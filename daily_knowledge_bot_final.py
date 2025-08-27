#!/usr/bin/env python3
"""
Daily Knowledge Bot

This script uses the Perplexity API to fetch an interesting fact about a rotating
topic each day. It can be scheduled to run daily using cron or Task Scheduler.

Usage:
  python daily_knowledge_bot_final.py
  python daily_knowledge_bot_final.py --linkedin
  python daily_knowledge_bot_final.py --post-to-linkedin
  python daily_knowledge_bot_final.py --post-to-linkedin --company

Requirements:
  - requests
  - python-dotenv
"""

import os
import json
import logging
import sys
import random
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("daily_knowledge_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("daily_knowledge_bot")


class ConfigurationError(Exception):
    """Exception raised for errors in the configuration."""
    pass


class LinkedInError(Exception):
    """Exception raised for errors posting to LinkedIn."""
    pass


class PerplexityClient:
    """Client for interacting with the Perplexity API."""
    
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ConfigurationError("Perplexity API key is required")
        
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_article_url(self, topic: str) -> Optional[str]:
        """Step 1: Find a single, relevant article URL for a given topic."""
        data = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a search assistant. Your sole purpose is to find a single, highly relevant, and verifiable online article for the given topic. Respond with ONLY the URL and nothing else."
                },
                {
                    "role": "user",
                    "content": f"Find one interesting article about {topic}."
                }
            ],
            "max_tokens": 150,
            "temperature": 0.2
        }
        response = requests.post(self.BASE_URL, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        url = response.json()["choices"][0]["message"]["content"].strip()
        
        if url.startswith("http") and " " not in url:
            return url
        return None

    def summarize_article(self, article_url: str) -> str:
        """Step 2: Summarize the content of a given article URL."""
        data = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a summarization assistant. Read the content of the provided URL and provide a concise, interesting summary of the key finding or main point. The summary should be under 100 words."
                },
                {
                    "role": "user",
                    "content": f"Please summarize this article: {article_url}"
                }
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }
        response = requests.post(self.BASE_URL, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


    def generate_linkedin_post(self, topic: str, fact: str, sources: List[str], max_tokens: int = 300, temperature: float = 0.7) -> str:
        data = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a social media expert specializing in LinkedIn content. Your tone is professional, engaging, and insightful. "
                        "Convert the user's fact into a compelling LinkedIn post under 150 words.\n\n"
                        "**Formatting Rules:**\n"
                        "- Use paragraphs for readability. Separate them with a blank line.\n"
                        "- Use bullet points (e.g., * or -) for lists or key points if it makes the content clearer.\n"
                        "- Start with a strong hook.\n"
                        "- Explain the fact clearly.\n"
                        "- End with a thought-provoking question or statement.\n"
                        "- Include 3-5 relevant hashtags.\n"
                        "- At the very end, under a 'Source:' heading, list ONLY the single source URL provided. Do not add any new sources or citations."
                    )
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}\nFact to summarize: {fact}\nSource to use: {sources[0]}"
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = requests.post(self.BASE_URL, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


class LinkedInPoster:
    """Client for posting updates to LinkedIn."""
    
    API_URL = "https://api.linkedin.com/v2/ugcPosts"
    
    def __init__(self, access_token: str):
        if not access_token or "YOUR_ACCESS_TOKEN_HERE" in access_token:
            raise ConfigurationError("LinkedIn Access Token is not configured. Please set it in your .env file.")
            
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def post_update(self, text: str, author_urn: str):
        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        try:
            response = requests.post(self.API_URL, headers=self.headers, json=post_data, timeout=30)
            response.raise_for_status()
            logger.info(f"Successfully posted update to LinkedIn as {author_urn}.")
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if e.response else str(e)
            logger.error(f"LinkedIn API Error: {error_text}")
            raise LinkedInError(f"Failed to post to LinkedIn: {error_text}") from e


class DailyFactService:
    """Service to manage retrieval and storage of daily facts."""
    
    def __init__(self, client: PerplexityClient, output_dir: Path):
        self.facts_dir = output_dir / "facts"
        self.linkedin_dir = output_dir / "linkedin_posts"
        self.facts_dir.mkdir(exist_ok=True, parents=True)
        self.linkedin_dir.mkdir(exist_ok=True, parents=True)
        self.client = client
        self.topics = [
            "astronomy", "history", "biology", "technology", "psychology",
            "ocean life", "ancient civilizations", "quantum physics",
            "art history", "culinary science"
        ]

    def load_topics_from_file(self, filepath: Union[str, Path]):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                loaded_topics = [line.strip() for line in f if line.strip()]
            if loaded_topics:
                self.topics = loaded_topics
                logger.info(f"Loaded {len(self.topics)} topics from {filepath}")
            else:
                logger.warning(f"Topics file {filepath} is empty, using defaults.")
        except FileNotFoundError:
            logger.warning(f"Topics file {filepath} not found, using defaults.")

    def get_daily_topic(self) -> str:
        day = datetime.now().day
        topic_index = (day - 1) % len(self.topics)
        return self.topics[topic_index]

    def get_and_save_daily_fact(self) -> Dict[str, str]:
        topic = self.get_daily_topic()
        logger.info(f"Step 1: Finding an article about: {topic}")
        article_url = self.client.get_article_url(topic)

        if not article_url:
            logger.error(f"Could not find a suitable article for {topic}. Exiting.")
            sys.exit(1)
        
        logger.info(f"Found article: {article_url}")
        logger.info("Step 2: Summarizing article...")
        fact_raw = self.client.summarize_article(article_url)
        
        # Standardize the citation number to [1] for consistency
        fact, num_replacements = re.subn(r'\s*\[\d+\]', ' [1]', fact_raw)
        if num_replacements == 0:
            fact += " [1]" # Add a citation if the model forgot one

        sources = [article_url]
        
        today = datetime.now().strftime("%Y-%m-%d")
        filename = self.facts_dir / f"daily_fact_{today}.txt"
        
        source_list_str = f"[1] {sources[0]}"
        file_content = f"DAILY FACT - {today}\nTopic: {topic}\n\n{fact.strip()}\n\nSource:\n{source_list_str}"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(file_content)
        logger.info(f"Fact saved to {filename}")
        
        return {"topic": topic, "fact": fact, "sources": sources, "filename": str(filename)}

    def generate_and_save_linkedin_post(self, topic: str, fact: str, sources: List[str]) -> Dict[str, str]:
        logger.info(f"Generating LinkedIn post for topic: {topic}")
        post_content = self.client.generate_linkedin_post(topic, fact, sources)
        
        today = datetime.now().strftime("%Y-%m-%d")
        filename = self.linkedin_dir / f"linkedin_post_{today}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(post_content)
        logger.info(f"LinkedIn post saved to {filename}")
        
        return {"post": post_content, "filepath": str(filename)}

def load_config() -> Dict[str, any]:
    script_dir = Path(__file__).parent
    dotenv_path = script_dir / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    topics_file = os.getenv("TOPICS_FILE", script_dir / "topics.txt")
    output_dir = os.getenv("OUTPUT_DIR", script_dir)
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    linkedin_id = os.getenv("LINKEDIN_PERSON_ID")
    linkedin_org_id = os.getenv("LINKEDIN_ORGANIZATION_ID")

    return {
        "api_key": api_key,
        "output_dir": Path(output_dir),
        "topics_file": Path(topics_file),
        "linkedin_token": linkedin_token,
        "linkedin_id": linkedin_id,
        "linkedin_org_id": linkedin_org_id
    }

def main():
    parser = argparse.ArgumentParser(description="Daily Knowledge Bot")
    parser.add_argument("--linkedin", action="store_true", help="Generate a LinkedIn post from the daily fact.")
    parser.add_argument("--post-to-linkedin", action="store_true", help="Automatically post the generated content to LinkedIn.")
    parser.add_argument("--company", action="store_true", help="Post to the configured LinkedIn Company Page instead of the personal profile.")
    args = parser.parse_args()

    try:
        config = load_config()
        if not config["api_key"]:
            raise ConfigurationError("Perplexity API key is not configured. Please set it in your .env file.")
        
        perplexity_client = PerplexityClient(api_key=config["api_key"])
        fact_service = DailyFactService(client=perplexity_client, output_dir=config["output_dir"])
        
        if config["topics_file"].exists():
            fact_service.load_topics_from_file(config["topics_file"])

        fact_info = fact_service.get_and_save_daily_fact()
        print(f"\nToday's {fact_info['topic']} fact: {fact_info['fact']}")
        print(f"Saved to: {fact_info['filename']}")

        if args.linkedin or args.post_to_linkedin:
            post_info = fact_service.generate_and_save_linkedin_post(fact_info['topic'], fact_info['fact'], fact_info['sources'])
            
            if not args.post_to_linkedin:
                print(f"\nLinkedIn post generated:\n{post_info['post']}")
                print(f"Saved to: {post_info['filepath']}")

            if args.post_to_linkedin:
                print("\n" + "="*50)
                print("The following post will be published to LinkedIn:")
                print("="*50)
                print(post_info['post'])
                print("="*50)
                
                confirm = input("Do you want to proceed with posting? (y/n): ")
                if confirm.lower() not in ['y', 'yes']:
                    logger.info("Posting cancelled by user.")
                    sys.exit(0)

                author_urn = None
                if args.company:
                    org_id = config.get("linkedin_org_id")
                    if not org_id or "YOUR_ORGANIZATION_ID_HERE" in org_id:
                        raise ConfigurationError("LinkedIn Organization ID is not configured for company post.")
                    author_urn = f"urn:li:organization:{org_id}"
                else:
                    if not config.get("linkedin_id") or "YOUR_PERSON_ID_HERE" in config.get("linkedin_id"):
                         raise ConfigurationError("LinkedIn Person ID is not configured for personal post.")
                    author_urn = f"urn:li:person:{config['linkedin_id']}"

                linkedin_poster = LinkedInPoster(access_token=config["linkedin_token"])
                linkedin_poster.post_update(post_info['post'], author_urn=author_urn)

    except (ConfigurationError, LinkedInError, requests.exceptions.RequestException) as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

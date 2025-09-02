#!/usr/bin/env python3
"""
Daily Knowledge Bot

This script uses the Perplexity API to fetch an interesting fact and the
Google Vertex AI API to generate a relevant image. It can post this content
to a LinkedIn personal profile or company page.

Usage:
  python daily_knowledge_bot_final.py
  python daily_knowledge_bot_final.py --post-to-linkedin
  python daily_knowledge_bot_final.py --post-to-linkedin --company

Requirements:
  - requests
  - python-dotenv
  - google-cloud-aiplatform
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
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("daily_knowledge_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("daily_knowledge_bot")

# --- Custom Exceptions ---
class ConfigurationError(Exception):
    """Exception raised for errors in the configuration."""
    pass

class LinkedInError(Exception):
    """Exception raised for errors posting to LinkedIn."""
    pass

# --- API Clients ---
class PerplexityClient:
    """Client for interacting with the Perplexity API."""
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, api_key: str):
        if not api_key or "YOUR_PERPLEXITY_API_KEY_HERE" in api_key:
            raise ConfigurationError("Perplexity API key is not configured.")
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
                {"role": "system", "content": "You are a search assistant. Your sole purpose is to find a single, highly relevant, and verifiable online article for the given topic. Respond with ONLY the URL and nothing else."},
                {"role": "user", "content": f"Find one interesting article about {topic}."}
            ],
            "max_tokens": 150, "temperature": 0.2
        }
        response = requests.post(self.BASE_URL, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        url = response.json()["choices"][0]["message"]["content"].strip()
        return url if url.startswith("http") and " " not in url else None

    def summarize_article(self, article_url: str) -> str:
        """Step 2: Summarize the content of a given article URL."""
        data = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": "You are a summarization assistant. Read the content of the provided URL and provide a concise, interesting summary of the key finding or main point. The summary should be under 100 words."},
                {"role": "user", "content": f"Please summarize this article: {article_url}"}
            ],
            "max_tokens": 200, "temperature": 0.7
        }
        response = requests.post(self.BASE_URL, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    def generate_linkedin_post_text(self, topic: str, fact: str, sources: List[str]) -> str:
        """Generates the text content for a LinkedIn post."""
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
                        "- Start with a strong hook.\n"
                        "- End with a thought-provoking question or statement.\n"
                        "- Include 3-5 relevant hashtags.\n"
                        "- At the very end, under a 'Source:' heading, list ONLY the single source URL provided. Do not add any new sources or citations."
                    )
                },
                {"role": "user", "content": f"Topic: {topic}\nFact to summarize: {fact}\nSource to use: {sources[0]}"}
            ],
            "max_tokens": 300, "temperature": 0.7
        }
        response = requests.post(self.BASE_URL, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

class GoogleImageClient:
    """Client for generating images using Google's Vertex AI."""
    def __init__(self, project_id: str, location: str):
        if not project_id or "YOUR_GOOGLE_PROJECT_ID" in project_id:
            raise ConfigurationError("Google Cloud project ID is not configured.")
        aiplatform.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")

    def generate_image(self, topic: str, output_dir: Path) -> Optional[Path]:
        """Generates an image based on a topic and saves it locally."""
        prompt = f"A visually appealing, professional, and abstract image representing the concept of '{topic}'. The style should be neutral, suitable for a corporate social media post. Avoid text and human figures."
        try:
            logger.info(f"Generating image for topic: {topic}...")
            response = self.model.generate_images(prompt=prompt, number_of_images=1)
            image = response[0]
            image_path = output_dir / f"{topic.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.png"
            image.save(location=str(image_path), include_generation_parameters=False)
            logger.info(f"Image saved to {image_path}")
            return image_path
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return None

class LinkedInClient:
    """Client for posting updates to LinkedIn."""
    API_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token: str, person_id: str, organization_id: str):
        if not access_token or "YOUR_ACCESS_TOKEN_HERE" in access_token:
            raise ConfigurationError("LinkedIn Access Token is not configured.")
        self.access_token = access_token
        self.person_id = person_id
        self.organization_id = organization_id
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def _get_author_urn(self, is_company: bool) -> str:
        """Determines the author URN based on the company flag."""
        if is_company:
            if not self.organization_id:
                raise ConfigurationError("LinkedIn Organization ID is required for company posts.")
            return f"urn:li:organization:{self.organization_id}"
        if not self.person_id:
            raise ConfigurationError("LinkedIn Person ID is required for personal posts.")
        return f"urn:li:person:{self.person_id}"

    def _register_image_upload(self, author_urn: str) -> Dict[str, any]:
        """Step 1: Register the image upload with LinkedIn to get an upload URL."""
        register_url = f"{self.API_URL}/assets?action=registerUpload"
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        response = requests.post(register_url, headers=self.headers, json=register_data)
        response.raise_for_status()
        return response.json()

    def _upload_image(self, upload_url: str, image_path: Path):
        """Step 2: Upload the image binary to the provided URL."""
        with open(image_path, "rb") as f:
            image_data = f.read()
        upload_headers = {"Content-Type": "application/octet-stream"}
        response = requests.put(upload_url, headers=upload_headers, data=image_data)
        response.raise_for_status()
        logger.info("Image binary successfully uploaded to LinkedIn.")

    def post_update(self, content: str, is_company: bool, image_path: Optional[Path] = None):
        """Posts an update to LinkedIn, with or without an image."""
        author_urn = self._get_author_urn(is_company)
        post_url = f"{self.API_URL}/ugcPosts"

        specific_content = {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE"
            }
        }

        if image_path:
            logger.info("Registering and uploading image to LinkedIn...")
            upload_info = self._register_image_upload(author_urn)
            upload_url = upload_info["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            image_asset_urn = upload_info["value"]["asset"]
            self._upload_image(upload_url, image_path)
            
            specific_content["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            specific_content["com.linkedin.ugc.ShareContent"]["media"] = [
                {"status": "READY", "media": image_asset_urn}
            ]

        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": specific_content,
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        
        response = requests.post(post_url, headers=self.headers, json=post_data)
        if response.status_code != 201:
            raise LinkedInError(f"Failed to post to LinkedIn: {response.status_code} {response.text}")
        
        media_type = "with image" if image_path else "(text-only)"
        logger.info(f"Successfully posted update {media_type} to LinkedIn as {author_urn.split(':')[-1]}.")

# --- Main Service --- 
class DailyKnowledgeService:
    """Service to manage the daily workflow."""
    def __init__(self, perplexity_client: PerplexityClient, image_client: GoogleImageClient, linkedin_client: Optional[LinkedInClient]):
        self.perplexity_client = perplexity_client
        self.image_client = image_client
        self.linkedin_client = linkedin_client
        self.facts_dir = Path("facts")
        self.linkedin_posts_dir = Path("linkedin_posts")
        self.images_dir = Path("images")
        self.facts_dir.mkdir(exist_ok=True)
        self.linkedin_posts_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.topics = []

    def load_topics_from_file(self, filepath: Path):
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                self.topics = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(self.topics)} topics from {filepath}")
        else:
            logger.warning(f"Topics file not found at {filepath}. Using default topics.")
            self.topics = ["Artificial Intelligence", "Climate Change", "Neuroscience"]

    def get_daily_topic(self) -> str:
        day = datetime.now().day
        return self.topics[(day - 1) % len(self.topics)]

    def get_and_save_daily_content(self) -> Dict[str, any]:
        """Generates and saves the daily fact, post, and image."""
        topic = self.get_daily_topic()
        
        # Step 1: Get sourced fact from Perplexity
        logger.info(f"Step 1: Finding an article about: {topic}")
        article_url = self.perplexity_client.get_article_url(topic)
        if not article_url:
            logger.error(f"Could not find a suitable article for {topic}. Exiting.")
            sys.exit(1)
        
        logger.info(f"Found article: {article_url}")
        logger.info("Step 2: Summarizing article...")
        fact_raw = self.perplexity_client.summarize_article(article_url)
        
        # Standardize citation to [1]
        fact, _ = re.subn(r'\s*\[\d+\]', ' [1]', fact_raw)
        if not fact.endswith(' [1]'):
            fact += " [1]"
        
        sources = [article_url]
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Save fact file
        fact_filename = self.facts_dir / f"daily_fact_{today}.txt"
        file_content = f"DAILY FACT - {today}\nTopic: {topic}\n\n{fact.strip()}\n\nSource:\n[1] {sources[0]}"
        with open(fact_filename, "w", encoding="utf-8") as f:
            f.write(file_content)
        logger.info(f"Fact saved to {fact_filename}")

        # Step 3: Generate LinkedIn post text
        logger.info(f"Step 3: Generating LinkedIn post text for topic: {topic}")
        post_text = self.perplexity_client.generate_linkedin_post_text(topic, fact, sources)
        post_filename = self.linkedin_posts_dir / f"linkedin_post_{today}.md"
        with open(post_filename, "w", encoding="utf-8") as f:
            f.write(post_text)
        logger.info(f"LinkedIn post text saved to {post_filename}")

        # Step 4: Generate image
        image_path = self.image_client.generate_image(topic, self.images_dir)

        return {
            "topic": topic, 
            "fact": fact, 
            "sources": sources, 
            "post_text": post_text,
            "image_path": image_path
        }

# --- Main Execution --- 
def main():
    parser = argparse.ArgumentParser(description="Daily Knowledge Bot for LinkedIn.")
    parser.add_argument("--post-to-linkedin", action="store_true", help="Post the generated content to LinkedIn.")
    parser.add_argument("--company", action="store_true", help="Post on behalf of a company (requires organization ID).")
    args = parser.parse_args()

    # Load configuration from .env file
    load_dotenv()
    linkedin_client = None
    try:
        perplexity_client = PerplexityClient(api_key=os.getenv("PERPLEXITY_API_KEY"))
        image_client = GoogleImageClient(
            project_id=os.getenv("GOOGLE_PROJECT_ID"),
            location=os.getenv("GOOGLE_LOCATION", "us-central1")
        )
        if args.post_to_linkedin:
            linkedin_client = LinkedInClient(
                access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
                person_id=os.getenv("LINKEDIN_PERSON_ID"),
                organization_id=os.getenv("LINKEDIN_ORGANIZATION_ID")
            )
        
        service = DailyKnowledgeService(perplexity_client, image_client, linkedin_client)
        service.load_topics_from_file(Path("topics.txt"))

    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)

    # Generate all content first
    content = service.get_and_save_daily_content()
    logger.info(f"Today's {content['topic']} fact: {content['fact']}")
    if content["image_path"]:
        logger.info(f"Image saved to: {content['image_path']}")

    # Post to LinkedIn if requested
    if args.post_to_linkedin:
        if not service.linkedin_client:
            logger.error("LinkedIn client not initialized. Cannot post.")
            return

        print("="*50)
        print("The following post will be published to LinkedIn:")
        print("="*50)
        print(content["post_text"])
        if content["image_path"]:
            print(f"\nImage to be uploaded: {content['image_path']}")
        print("="*50)
        
        # Manual confirmation step
        proceed = input("Do you want to proceed with posting? (y/n): ")
        if proceed.lower() == 'y':
            try:
                service.linkedin_client.post_update(
                    content=content["post_text"], 
                    is_company=args.company, 
                    image_path=content.get("image_path")
                )
            except LinkedInError as e:
                logger.error(f"LinkedIn Error: {e}")
        else:
            logger.info("Posting to LinkedIn aborted by user.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Daily Knowledge Bot

This script uses the Perplexity API to fetch an interesting fact and the
Google Vertex AI API to generate a relevant image. It can post this content
to a LinkedIn personal profile or company page.

Usage:
  python daily_knowledge_bot.py
  python daily_knowledge_bot.py --post-to-linkedin
  python daily_knowledge_bot.py --post-to-linkedin --company
  python daily_knowledge_bot.py --no-image
  python daily_knowledge_bot.py --no-logo

Requirements:
  - requests
  - python-dotenv
  - google-cloud-aiplatform
  - Pillow
"""

import os
import sys
import json
import random
import logging
import argparse
import re
from abc import ABC, abstractmethod
from datetime import datetime, date
from PIL import Image
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Optional, Union, Any

import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from vertexai.preview.vision_models import ImageGenerationModel
from google.cloud import aiplatform
from google import genai

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

class ImageGenerationClient(ABC):
    """Abstract base class for image generation clients."""
    
    @abstractmethod
    def generate_image(self, topic: str, output_dir: Path) -> Optional[Path]:
        """Generate an image for the given topic and save it to the output directory."""
        pass


class GeminiImageClient(ImageGenerationClient):
    """Client for generating images using Google's Gemini API."""

    def __init__(self, api_key: str):
        if not api_key or "YOUR_GOOGLE_API_KEY" in api_key:
            raise ConfigurationError("Google API key is not configured.")
        try:
            logger.info("Initializing Gemini API for image generation...")
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Gemini API: {e}")

    def generate_image(self, topic: str, output_dir: Path) -> Optional[Path]:
        """
        Generates a high-quality image based on a topic using Gemini API.
        """
        prompt = (
            f"Create a professional, high-detail image representing '{topic}'. "
            f"The style should be modern, clean, and visually striking, suitable for a LinkedIn post. "
            f"Focus on a composition that is both artistic and clearly communicates the subject. "
            f"Avoid text, watermarks, or distracting elements. The lighting should be bright and natural."
        )

        try:
            logger.info(f"Generating image for topic: {topic}...")
            logger.debug(f"Using prompt: {prompt}")

            # Generate the image
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[prompt],
            )
            
            # Process the response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    # Create output directory if it doesn't exist
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate a filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{topic.replace(' ', '_').lower()}_{timestamp}.png"
                    image_path = output_dir / filename
                    
                    # Save the image
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(image_path)
                    
                    logger.info(f"Image saved to {image_path}")
                    return image_path
            
            logger.warning("No image data found in the response")
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return None

# --- Helper Functions ---
def add_logo_to_image(base_image_path: Path, logo_path: Path, output_path: Path):
    """Overlays a logo onto the bottom-right corner of a base image."""
    try:
        logger.info(f"Opening base image: {base_image_path}")
        base_image = Image.open(base_image_path).convert("RGBA")
        
        logger.info(f"Opening logo image: {logo_path}")
        logo = Image.open(logo_path).convert("RGBA")

        base_width, base_height = base_image.size
        logo_width = int(base_width * 0.20)
        logo_ratio = logo_width / float(logo.size[0])
        logo_height = int(float(logo.size[1]) * float(logo_ratio))
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        padding_x = int(base_width * 0.02)
        padding_y = int(base_height * 0.02)
        position = (base_width - logo_width - padding_x, base_height - logo_height - padding_y)

        transparent_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        transparent_layer.paste(logo, position)

        watermarked_image = Image.alpha_composite(base_image, transparent_layer)
        watermarked_image.convert("RGB").save(output_path)
        logger.info(f"Successfully added logo and saved to: {output_path}")

    except FileNotFoundError:
        logger.warning(f"Logo file not found at '{logo_path}'. Skipping logo addition.")
    except Exception as e:
        logger.error(f"Could not add logo to image: {e}")

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
        }

    def upload_image(self, image_path: Path) -> str:
        """Uploads an image to LinkedIn and returns the asset URN."""
        # Step 1: Register the upload
        register_upload_url = f"{self.API_URL}/assets?action=registerUpload"
        register_body = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{self.person_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        response = requests.post(register_upload_url, headers=self.headers, json=register_body, timeout=30)
        if response.status_code != 200:
            raise LinkedInError(f"Failed to register image upload: {response.text}")
        upload_data = response.json()["value"]
        asset_urn = upload_data["asset"]
        upload_url = upload_data["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]

        # Step 2: Upload the image file
        image_headers = {'Authorization': f'Bearer {self.access_token}'}
        with open(image_path, 'rb') as f:
            upload_response = requests.put(upload_url, headers=image_headers, data=f, timeout=60)
        
        if upload_response.status_code not in [200, 201]:
            raise LinkedInError(f"Failed to upload image: {upload_response.text}")
        
        logger.info(f"Image uploaded successfully. Asset URN: {asset_urn}")
        return asset_urn

    def post_as_person(self, text: str, image_urn: Optional[str] = None):
        """Posts an update to a personal LinkedIn profile."""
        post_url = f"{self.API_URL}/ugcPosts"
        post_body = {
            "author": f"urn:li:person:{self.person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        if image_urn:
            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {"status": "READY", "media": image_urn}
            ]
        
        response = requests.post(post_url, headers=self.headers, json=post_body, timeout=30)
        if response.status_code != 201:
            raise LinkedInError(f"Failed to post to LinkedIn as person: {response.text}")
        logger.info("Successfully posted to LinkedIn personal profile.")

    def post_as_company(self, text: str, image_urn: Optional[str] = None):
        """Posts an update to a LinkedIn company page."""
        post_url = f"{self.API_URL}/ugcPosts"
        post_body = {
            "author": f"urn:li:organization:{self.organization_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        if image_urn:
            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {"status": "READY", "media": image_urn}
            ]
        
        response = requests.post(post_url, headers=self.headers, json=post_body, timeout=30)
        if response.status_code != 201:
            raise LinkedInError(f"Failed to post to LinkedIn as company: {response.text}")
        logger.info("Successfully posted to LinkedIn company page.")

# --- Main Service --- 
class DailyKnowledgeService:
    """Service to manage the daily workflow."""
    def __init__(self, perplexity_client: PerplexityClient, image_client: GeminiImageClient, linkedin_client: Optional[LinkedInClient]):
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
        try:
            with open(filepath, 'r') as f:
                self.topics = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(self.topics)} topics from {filepath}")
        except FileNotFoundError:
            logger.error(f"Topics file not found at {filepath}. Please create it.")
            self.topics = ["Artificial Intelligence"] # Default topic

    def get_daily_topic(self) -> str:
        """Selects a topic based on the day of the month."""
        if not self.topics:
            self.load_topics_from_file(Path("topics.txt"))
        day_of_month = datetime.now().day
        return self.topics[(day_of_month - 1) % len(self.topics)]

    def get_and_save_daily_content(self, generate_image: bool = True) -> Dict[str, Any]:
        """
        Generates and saves the daily fact, post, and optionally an image.
        
        Args:
            generate_image: If True, generates an image for the topic.
        
        Returns:
            A dictionary containing the generated content.
        """
        topic = self.get_daily_topic()
        logger.info(f"Step 1: Finding an article about: {topic}")
        article_url = self.perplexity_client.get_article_url(topic)
        if not article_url:
            logger.error("Could not find a valid article URL.")
            return {}
        logger.info(f"Found article: {article_url}")

        logger.info("Step 2: Summarizing article...")
        fact = self.perplexity_client.summarize_article(article_url)
        fact_file = self.facts_dir / f"daily_fact_{date.today().isoformat()}.txt"
        fact_file.write_text(fact, encoding='utf-8')
        logger.info(f"Fact saved to {fact_file}")

        logger.info(f"Step 3: Generating LinkedIn post text for topic: {topic}")
        post_text = self.perplexity_client.generate_linkedin_post_text(topic, fact, [article_url])
        post_file = self.linkedin_posts_dir / f"linkedin_post_{date.today().isoformat()}.md"
        post_file.write_text(post_text, encoding='utf-8')
        logger.info(f"LinkedIn post text saved to {post_file}")

        image_path = None
        if generate_image:
            image_path = self.image_client.generate_image(topic, self.images_dir)

        return {
            "topic": topic,
            "fact": fact,
            "post_text": post_text,
            "image_path": image_path
        }

# --- Helper Functions ---
def add_logo_to_image(base_image_path: Path, logo_path: Path, output_path: Path):
    """Overlays a logo onto the bottom-right corner of a base image."""
    try:
        logger.info(f"Opening base image: {base_image_path}")
        base_image = Image.open(base_image_path).convert("RGBA")
        
        logger.info(f"Opening logo image: {logo_path}")
        logo = Image.open(logo_path).convert("RGBA")

        # Resize logo to be 20% of the base image's width
        base_width, base_height = base_image.size
        logo_width = int(base_width * 0.20)
        logo_ratio = logo_width / float(logo.size[0])
        logo_height = int(float(logo.size[1]) * float(logo_ratio))
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # Position logo at the bottom-right with 2% padding
        padding_x = int(base_width * 0.02)
        padding_y = int(base_height * 0.02)
        position = (base_width - logo_width - padding_x, base_height - logo_height - padding_y)

        # Create a transparent layer to paste the logo on
        transparent_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        transparent_layer.paste(logo, position)

        # Composite the base image with the logo layer
        watermarked_image = Image.alpha_composite(base_image, transparent_layer)

        # Save the final image, replacing the original
        watermarked_image.convert("RGB").save(output_path)
        logger.info(f"Successfully added logo and saved to: {output_path}")

    except FileNotFoundError:
        logger.error(f"Error: Logo file not found at '{logo_path}'. Please ensure it exists.")
    except Exception as e:
        logger.error(f"Could not add logo to image: {e}")

def print_summary(topic: str, fact: str, post_text: str, image_path: Optional[Path] = None):
    """Prints a summary of the generated content to the console."""
    logger.info("--- Daily Knowledge Bot Summary ---")
    logger.info(f"Topic: {topic}")
    logger.info(f"Fact: {fact}")
    logger.info(f"LinkedIn Post:\n{post_text}")
    if image_path:
        logger.info(f"Image generated at: {image_path}")

# --- Main Execution --- 
def main():
    parser = argparse.ArgumentParser(description="Daily Knowledge Bot for LinkedIn.")
    parser.add_argument("--post-to-linkedin", action="store_true", help="Post the generated content to LinkedIn.")
    parser.add_argument("--company", action="store_true", help="Post on behalf of a company (requires organization ID).")
    parser.add_argument("--no-image", action="store_true", help="Skip generating an image for the post.")
    parser.add_argument("--no-logo", action="store_true", help="Skip adding the brand logo to the image.")
    args = parser.parse_args()

    # Load configuration from .env file
    load_dotenv()

    # Initialize clients
    try:
        perplexity_client = PerplexityClient(api_key=os.getenv("PERPLEXITY_API_KEY"))
        
        # Initialize Gemini image client
        image_client = GeminiImageClient(
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        logger.info("Using Google Gemini for image generation")
        
        linkedin_client = None
        if args.post_to_linkedin:
            linkedin_client = LinkedInClient(
                access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
                person_id=os.getenv("LINKEDIN_PERSON_ID"),
                organization_id=os.getenv("LINKEDIN_ORGANIZATION_ID")
            )

        service = DailyKnowledgeService(perplexity_client, image_client, linkedin_client)

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Generate content
    content = service.get_and_save_daily_content(generate_image=not args.no_image)
    if not content:
        logger.error("Failed to generate content. Exiting.")
        sys.exit(1)

    # Add logo to the image if it was generated and not disabled
    if content.get("image_path") and not args.no_logo:
        logo_path = Path("brand_logo.png")
        add_logo_to_image(content["image_path"], logo_path, content["image_path"]) # Overwrite original

    # Post to LinkedIn if requested
    if args.post_to_linkedin:
        if not service.linkedin_client:
            logger.error("LinkedIn client not initialized. Cannot post.")
            sys.exit(1)

        # Confirm before posting
        user_input = input("Do you want to post the generated content to LinkedIn? (y/n): ")
        if user_input.lower() == 'y':
            try:
                if args.company:
                    image_urn = service.linkedin_client.upload_image(content["image_path"])
                    service.linkedin_client.post_as_company(content["post_text"], image_urn)
                else:
                    image_urn = service.linkedin_client.upload_image(content["image_path"])
                    service.linkedin_client.post_as_person(content["post_text"], image_urn)
            except LinkedInError as e:
                logger.error(f"Failed to post to LinkedIn: {e}")
        else:
            logger.info("Posting to LinkedIn cancelled by user.")
    else:
        # Print summary if not posting
        print_summary(content["topic"], content["fact"], content["post_text"], content.get("image_path"))

if __name__ == "__main__":
    main()

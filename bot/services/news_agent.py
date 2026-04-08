import os
import time
import logging
import json
import random
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient
from services.firebase import add_content

logger = logging.getLogger(__name__)

class ModelRotator:
    """Handles Hugging Face model rotation to bypass rate limits."""
    def __init__(self, token):
        self.client = InferenceClient(token=token)
        self.models = [
            "mistralai/Mistral-7B-Instruct-v0.2",
            "google/gemma-1.1-7b-it",
            "HuggingFaceH4/zephyr-7b-beta"
        ]
        self.current_index = 0

    def get_current_model(self):
        return self.models[self.current_index]

    def rotate(self):
        self.current_index = (self.current_index + 1) % len(self.models)
        logger.info(f"🔄 Rotating to model: {self.get_current_model()}")

    def chat(self, prompt, system_message="You are a professional Surface Hub News Journalist."):
        """Attempts to chat with current model, rotates on failure."""
        attempts = len(self.models)
        while attempts > 0:
            try:
                model = self.get_current_model()
                response = self.client.text_generation(
                    prompt=f"<s>[INST] {system_message} {prompt} [/INST]</s>",
                    model=model,
                    max_new_tokens=1500,
                    temperature=0.7,
                )
                return response
            except Exception as e:
                logger.error(f"❌ Error with model {self.get_current_model()}: {e}")
                self.rotate()
                attempts -= 1
        return None

class AIAgent:
    """The core engine that searches for news and publishes to Surface Hub."""
    
    def __init__(self):
        token = os.getenv("HF_TOKEN")
        if not token:
            logger.error("🚫 HF_TOKEN not found in environment variables!")
            self.rotator = None
        else:
            self.rotator = ModelRotator(token)
            
    def run_update(self):
        """Main update loop: Search -> Summarize -> Publish"""
        if not self.rotator:
            return logger.error("AI Agent stopped: No Token.")

        logger.info("🌍 AI AGENT: Starting Global News Intelligence Sweep...")
        
        # 1. Broad Global Search
        search_queries = [
            "breaking world news technology today",
            "top financial market news live",
            "global entertainment and lifestyle headlines",
            "latest cryptocurrency and blockchain breakthroughs"
        ]
        
        query = random.choice(search_queries)
        results = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=5))
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return

        if not results:
            return logger.warning("No search results found.")

        # 2. Process each result
        for entry in results:
            url = entry.get('url')
            title_input = entry.get('title')
            snippet = entry.get('body')
            
            logger.info(f"📰 Processing: {title_input}")
            
            # Generate detailed article
            prompt = f"""
            Generate a detailed, professional news article based on this snippet:
            "{snippet}"
            
            REQUIREMENTS:
            1. Title: Catchy professional headline.
            2. Summary: 2-line high-impact summary.
            3. Content: 5-6 paragraphs of detailed analysis. 
            4. AD INJECTION: Place the exact marker [AD_SLOT] after the 2nd paragraph and after the 4th paragraph.
            5. Category: Choose one from [Blogs, Videos, Games, Records].
            
            OUTPUT FORMAT (JSON ONLY):
            {{
                "title": "Headline",
                "summary": "2-line summary",
                "content": "Full article with [AD_SLOT] placeholders",
                "category": "Chosen Category"
            }}
            """
            
            raw_response = self.rotator.chat(prompt)
            if not raw_response:
                continue
                
            try:
                # Clean response (sometimes models add chatter)
                json_str = raw_response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                data = json.loads(json_str)
                
                # 3. Publish to Firebase
                # For images, we try to use a placeholder or the snippet context
                image_tag = data.get("category", "tech").lower()
                image_url = f"https://source.unsplash.com/1200x800/?{image_tag}"
                
                content_id = add_content(
                    title=data["title"],
                    summary=data["summary"],
                    category=data["category"],
                    image=image_url,
                    url=url,
                    content=data["content"]
                )
                
                logger.info(f"✅ AI Published Content: {content_id}")
                
            except Exception as e:
                logger.error(f"JSON Parsing failed for response: {e}")
                continue
                
        logger.info("✨ AI Sweep Complete.")

# Background Job Hook
async def autonomous_news_job(context):
    """Bridge for Telegram Bot JobQueue"""
    agent = AIAgent()
    agent.run_update()

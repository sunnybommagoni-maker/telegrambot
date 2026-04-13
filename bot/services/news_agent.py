import os
import time
import logging
import json
import random
from huggingface_hub import InferenceClient
from services.firebase import add_content

logger = logging.getLogger(__name__)

class ModelRotator:
    """Handles Hugging Face model rotation to bypass rate limits."""
    def __init__(self, token):
        self.client = InferenceClient(token=token)
        self.models = [
            "mistralai/Mistral-7B-Instruct-v0.3",
            "Qwen/Qwen2.5-7B-Instruct",
            "microsoft/Phi-3-mini-4k-instruct"
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
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
                response = self.client.chat_completion(
                    messages=messages,
                    model=model,
                    max_tokens=1500,
                    temperature=0.7,
                )
                return response.choices[0].message.content
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
        
        import urllib.request
        import xml.etree.ElementTree as ET
        
        rss_feeds = [
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://feeds.bbci.co.uk/news/business/rss.xml"
        ]
        
        feed_url = random.choice(rss_feeds)
        results = []
        try:
            req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                # Find all items and pick the top 5
                items = root.findall('.//item')[:5]
                for item in items:
                    title = item.find('title')
                    desc = item.find('description')
                    link = item.find('link')
                    if title is not None and desc is not None:
                        results.append({
                            'title': title.text,
                            'body': desc.text,
                            'url': link.text if link is not None else ""
                        })
        except Exception as e:
            logger.error(f"RSS fetch failed: {e}")
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
                
                # 3. Ensure Ad Slots exist (Fail-Safe)
                data = json.loads(json_str)
                final_content = self.fix_ad_slots(data["content"])

                # 4. Publish to Firebase
                # For images, we try to use a placeholder or the snippet context
                image_tag = data.get("category", "tech").lower()
                image_url = f"https://source.unsplash.com/1200x800/?{image_tag}"
                
                content_id = add_content(
                    title=data["title"],
                    summary=data["summary"],
                    category=data["category"],
                    image=image_url,
                    url=url,
                    content=final_content
                )
                
                logger.info(f"✅ AI Published Content: {content_id}")
                
            except Exception as e:
                logger.error(f"JSON Parsing failed for response: {e}")
                continue
                
        logger.info("✨ AI Sweep Complete.")

    def fix_ad_slots(self, content):
        """Ensures [AD_SLOT] exists every few paragraphs if the LLM forgot."""
        if "[AD_SLOT]" in content:
            return content
            
        paragraphs = content.split('\n\n')
        if len(paragraphs) < 3:
            paragraphs = content.split('\n') # Fallback to single newlines
            
        new_content = []
        for i, p in enumerate(paragraphs):
            new_content.append(p.strip())
            if i == 1 or i == 3 or (i > 3 and i % 3 == 0):
                new_content.append("[AD_SLOT]")
        
        return "\n\n".join(new_content)

# Background Job Hook
async def autonomous_news_job(context):
    """Bridge for Telegram Bot JobQueue"""
    agent = AIAgent()
    agent.run_update()

import requests
import logging
from config import SHRINKEARN_API_KEY, SHORTLINK_PROVIDER

logger = logging.getLogger(__name__)

class ShortlinkService:
    """
    Utility to shorten URLs using ShrinkEarn API
    """
    API_URL = "https://shrinkearn.com/api"

    @staticmethod
    def get_short_url(long_url: str) -> str:
        """
        Shortens a URL using ShrinkEarn. Returns original URL if it fails.
        """
        if not SHRINKEARN_API_KEY:
            logger.warning("⚠️ SHRINKEARN_API_KEY not configured. Using original URL.")
            return long_url

        try:
            params = {
                "api": SHRINKEARN_API_KEY.strip(),
                "url": long_url
            }
            response = requests.get(ShortlinkService.API_URL, params=params, timeout=10)
            data = response.json()

            if data.get("status") == "success" and data.get("shortenedUrl"):
                logger.info(f"✅ URL Shortened: {data.get('shortenedUrl')}")
                return data.get("shortenedUrl")
            else:
                logger.warning(f"⚠️ ShrinkEarn Error: {data.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"❌ Shortlink Service Error: {e}")

        return long_url

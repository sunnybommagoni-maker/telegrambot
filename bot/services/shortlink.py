import httpx
import logging
from config import SHRINKEARN_API_KEY

logger = logging.getLogger(__name__)

async def shorten_link(tracking_url: str, user_id: int, ad_id: str = "") -> str:
    """
    Returns the tracking URL wrapped in a ShrinkEarn shortlink explicitly.
    Highest paying CPM network substitution.
    """
    if not SHRINKEARN_API_KEY or SHRINKEARN_API_KEY == "YOUR_SHRINKEARN_API_KEY":
        logger.warning("SHRINKEARN_API_KEY is missing! Returning raw URL.")
        return tracking_url

    api_url = "https://shrinkearn.com/api"
    params = {"api": SHRINKEARN_API_KEY, "url": tracking_url}
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(api_url, params=params)
            data = r.json()
            if data.get("status") == "success":
                return data["shortenedUrl"]
            else:
                logger.error(f"ShrinkEarn API error: {data.get('message')}")
    except Exception as e:
        logger.error(f"ShrinkEarn shortener failed: {e}")
    
    return tracking_url

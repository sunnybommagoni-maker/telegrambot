import logging
import random
import urllib.parse
from telegram.ext import ContextTypes
import services.firebase as db
import services.shortlink as shortlink
from config import WEBSITE_BASE_URL

logger = logging.getLogger(__name__)

async def feed_push_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Background job that runs every X hours to send a new shortlink to everyone.
    The shortlink points to the hub.html which keeps users for 5 mins to earn ₹50.
    """
    logger.info("Executing Autobroadcast Job: Pushing Hub Task to users...")

    # Fetch all registered users
    users = db.get_all_user_ids()
    if not users:
        logger.info("No users found to broadcast to.")
        return

    # Configuration for the broadcast task
    reward = 50.0  # Massive reward for 5 mins retention
    hub_id = str(random.randint(10000, 99999))
    base_url_template = f"{WEBSITE_BASE_URL}/hub.html?user_id={{user_id}}&hub_id={hub_id}&reward={reward}"

    successful = 0
    failed = 0

    for user_id in users:
        try:
            # Check if user is banned
            user_data = db.get_user(user_id)
            if not user_data or user_data.get("banned", False):
                continue

            # Generate shortlink for this specific user
            base_url = base_url_template.format(user_id=user_id)
            final_url = await shortlink.shorten_link(base_url, user_id, hub_id)

            text = (
                f"🚨 *HIGH PAYING ALERT!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"We just unlocked a new premium Content Hub!\n\n"
                f"🎮 Play viral games, get latest updates, and watch wild videos.\n\n"
                f"💰 *Reward:* ₹{reward}\n"
                f"⏱ *Requirement:* Stay and play for 5 minutes\n\n"
                f"👉 [ENTER PREMIUM HUB HERE]({final_url})\n\n"
                f"_Quick! This link expires soon._"
            )

            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            successful += 1
        except Exception as e:
            logger.warning(f"Failed to push message to {user_id}: {e}")
            failed += 1

    logger.info(f"Autobroadcast Complete. Success: {successful}, Failed: {failed}")

import os
from dotenv import load_dotenv

# ── Always load .env from project root (telegram bot/) regardless of CWD ──
_BOT_DIR = os.path.dirname(os.path.abspath(__file__))        # bot/
_PROJECT_ROOT = os.path.abspath(os.path.join(_BOT_DIR, "..")) # telegram bot/
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

# ── Bot ───────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ── Admin ────────────────────────────────────────────────────
ADMIN_TELEGRAM_ID = 5936922644
ADMIN_NAME = "Yaswanth"
_admin_raw = os.getenv("ADMIN_IDS", "5936922644")
ADMIN_IDS = [int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()] or [ADMIN_TELEGRAM_ID]

# ── Firebase ──────────────────────────────────────────────────
FIREBASE_URL = os.getenv("FIREBASE_URL", "https://chatting-app-ae637-default-rtdb.firebaseio.com")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

# ── Website ───────────────────────────────────────────────────
WEBSITE_BASE_URL = os.getenv("WEBSITE_BASE_URL", "https://chatting-app-ae637.web.app")
WEBSITE_ADMIN_URL = f"{WEBSITE_BASE_URL}/admin.html"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# ── UPI & Payment ─────────────────────────────────────────────
UPI_ID = os.getenv("UPI_ID", "7730846362@upi")
SHORTLINK_PROVIDER = os.getenv("SHORTLINK_PROVIDER", "shrinkearn")
LINKVERTISE_USER_ID = os.getenv("LINKVERTISE_USER_ID", "4840981")
EXEIO_API_KEY = os.getenv("EXEIO_API_KEY")
SHRINKEARN_API_KEY = os.getenv("SHRINKEARN_API_KEY")
LINKPAYS_API_KEY = os.getenv("LINKPAYS_API_KEY", "")

# ── Earning System Configuration ──────────────────────────────
# Task & Rewards
TASK_COMPLETION_REWARD = 10  # ₹10 per task

DEPOSIT_AMOUNT = 50  # User requested ₹50
MINIMUM_WITHDRAW_AMOUNT = 500  # User requested ₹500

# Referral System
REFERRAL_BONUS_REFERRER = 100  # ₹100 for friend's referrer when friend completes 25 tasks
REFERRAL_BONUS_REFERRED = 20  # ₹20 for friend when they complete 25 tasks
REFERRAL_TASK_THRESHOLD = 25  # Tasks to complete before bonus awarded (automatic)

# Withdrawal Processing
WITHDRAWAL_PROCESSING_HOURS_MIN = 24  # Min 24 hours
WITHDRAWAL_PROCESSING_HOURS_MAX = 48  # Max 48 hours

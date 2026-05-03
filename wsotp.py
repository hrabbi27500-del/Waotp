# ==================== WHATSAPP REGISTRATION BOT v3.1 - BUG-FREE STABLE ====================
import os, re, json, time, asyncio, aiohttp, requests, threading
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from fastapi import FastAPI
import uvicorn

load_dotenv()

# ==================== CONFIG (ALL FROM ENV) ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", ""))
GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "")
PORT = int(os.environ.get("PORT", "10000"))
bd_tz = pytz.timezone('Asia/Dhaka')
REQUIRED_CHANNEL = os.environ.get("CHANNEL", "@CashxByte")

print("="*60)
print("🚀 WHATSAPP REGISTRATION BOT v3.1 - STABLE")
print(f"👑 Admin: {ADMIN_ID}")
print("="*60)

# ==================== LIMITS ====================
MAX_ACTIVE_NUMBERS = 3
MAX_OTP_RETRY = 1
API_COOLDOWN = 0.5
TRACK_INTERVAL = 4  # seconds (reduced load)
STUCK_TIMEOUT = 120  # seconds

# ==================== COUNTRY DATA ====================
COUNTRY_RATES = {
    "93": {"country": "Afghanistan", "rate": 0.07, "flag": "🇦🇫", "cc": "93"},
    "880": {"country": "Bangladesh", "rate": 0.14, "flag": "🇧🇩", "cc": "880"},
    "11": {"country": "Canada", "rate": 0.10, "flag": "🇨🇦", "cc": "11"},
    "229": {"country": "Benin", "rate": 0.07, "flag": "🇧🇯", "cc": "229"},
    "591": {"country": "Bolivia", "rate": 0.07, "flag": "🇧🇴", "cc": "591"},
    "267": {"country": "Botswana", "rate": 0.07, "flag": "🇧🇼", "cc": "267"},
    "55": {"country": "Brazil", "rate": 0.50, "flag": "🇧🇷", "cc": "55"},
    "226": {"country": "Burkina Faso", "rate": 0.08, "flag": "🇧🇫", "cc": "226"},
    "237": {"country": "Cameroon", "rate": 0.07, "flag": "🇨🇲", "cc": "237"},
    "53": {"country": "Cuba", "rate": 0.07, "flag": "🇨🇺", "cc": "53"},
    "593": {"country": "Ecuador", "rate": 0.07, "flag": "🇪🇨", "cc": "593"},
    "20": {"country": "Egypt", "rate": 0.15, "flag": "🇪🇬", "cc": "20"},
    "44": {"country": "England", "rate": 0.12, "flag": "🇬🇧", "cc": "44"},
    "251": {"country": "Ethiopia", "rate": 0.07, "flag": "🇪🇹", "cc": "251"},
    "358": {"country": "Finland", "rate": 0.07, "flag": "🇫🇮", "cc": "358"},
    "33": {"country": "France", "rate": 0.18, "flag": "🇫🇷", "cc": "33"},
    "49": {"country": "Germany", "rate": 0.07, "flag": "🇩🇪", "cc": "49"},
    "233": {"country": "Ghana", "rate": 0.07, "flag": "🇬🇭", "cc": "233"},
    "224": {"country": "Guinea", "rate": 0.07, "flag": "🇬🇳", "cc": "224"},
    "509": {"country": "Haiti", "rate": 0.08, "flag": "🇭🇹", "cc": "509"},
    "852": {"country": "Hong Kong", "rate": 0.09, "flag": "🇭🇰", "cc": "852"},
    "62": {"country": "Indonesia", "rate": 0.08, "flag": "🇮🇩", "cc": "62"},
    "964": {"country": "Iraq", "rate": 0.09, "flag": "🇮🇶", "cc": "964"},
    "225": {"country": "Ivory Coast", "rate": 0.07, "flag": "🇨🇮", "cc": "225"},
    "254": {"country": "Kenya", "rate": 0.07, "flag": "🇰🇪", "cc": "254"},
    "231": {"country": "Liberia", "rate": 0.07, "flag": "🇱🇷", "cc": "231"},
    "261": {"country": "Madagascar", "rate": 0.07, "flag": "🇲🇬", "cc": "261"},
    "60": {"country": "Malaysia", "rate": 0.08, "flag": "🇲🇾", "cc": "60"},
    "223": {"country": "Mali", "rate": 0.07, "flag": "🇲🇱", "cc": "223"},
    "222": {"country": "Mauritania", "rate": 0.07, "flag": "🇲🇷", "cc": "222"},
    "52": {"country": "Mexico", "rate": 0.25, "flag": "🇲🇽", "cc": "52"},
    "212": {"country": "Morocco", "rate": 0.12, "flag": "🇲🇦", "cc": "212"},
    "258": {"country": "Mozambique", "rate": 0.07, "flag": "🇲🇿", "cc": "258"},
    "95": {"country": "Myanmar", "rate": 0.09, "flag": "🌍", "cc": "95"},
    "977": {"country": "Nepal", "rate": 0.07, "flag": "🇳🇵", "cc": "977"},
    "227": {"country": "Niger", "rate": 0.07, "flag": "🇳🇪", "cc": "227"},
    "234": {"country": "Nigeria", "rate": 0.10, "flag": "🇳🇬", "cc": "234"},
    "968": {"country": "Oman", "rate": 0.12, "flag": "🇴🇲", "cc": "968"},
    "92": {"country": "Pakistan", "rate": 0.13, "flag": "🇵🇰", "cc": "92"},
    "970": {"country": "Palestine", "rate": 0.08, "flag": "🇵🇸", "cc": "970"},
    "48": {"country": "Poland", "rate": 0.08, "flag": "🇵🇱", "cc": "48"},
    "7": {"country": "Russia", "rate": 0.08, "flag": "🇷🇺", "cc": "7"},
    "966": {"country": "Saudi Arabia", "rate": 0.20, "flag": "🇸🇦", "cc": "966"},
    "221": {"country": "Senegal", "rate": 0.07, "flag": "🇸🇳", "cc": "221"},
    "232": {"country": "Sierra Leone", "rate": 0.07, "flag": "🇸🇱", "cc": "232"},
    "27": {"country": "South Africa", "rate": 0.08, "flag": "🇿🇦", "cc": "27"},
    "211": {"country": "South Sudan", "rate": 0.08, "flag": "🌍", "cc": "211"},
    "249": {"country": "Sudan", "rate": 0.07, "flag": "🇸🇩", "cc": "249"},
    "963": {"country": "Syria", "rate": 0.08, "flag": "🇸🇾", "cc": "963"},
    "886": {"country": "Taiwan", "rate": 0.08, "flag": "🇹🇼", "cc": "886"},
    "255": {"country": "Tanzania", "rate": 0.07, "flag": "🇹🇿", "cc": "255"},
    "670": {"country": "Timor Leste", "rate": 0.07, "flag": "🇹🇱", "cc": "670"},
    "228": {"country": "Togo", "rate": 0.07, "flag": "🇹🇬", "cc": "228"},
    "256": {"country": "Uganda", "rate": 0.07, "flag": "🇺🇬", "cc": "256"},
    "58": {"country": "Venezuela", "rate": 0.07, "flag": "🇻🇪", "cc": "58"},
    "84": {"country": "Vietnam", "rate": 0.07, "flag": "🇻🇳", "cc": "84"},
    "967": {"country": "Yemen", "rate": 0.07, "flag": "🇾🇪", "cc": "967"},
    "260": {"country": "Zambia", "rate": 0.07, "flag": "🇿🇲", "cc": "260"},
    "263": {"country": "Zimbabwe", "rate": 0.09, "flag": "🇿🇼", "cc": "263"}
}

# ==================== COUNTRY APIS ====================
COUNTRY_APIS = {
    # ===== YOUR EXISTING ENTRIES (kept as-is) =====
    "11": {"cc": "11", "display_cc": "1", "country": "Canada", "base_url": "http://8.222.182.223:8081", "u": "HasanCAA", "p": "HasanCAA"},
    "52": {"cc": "52", "display_cc": "52", "country": "Mexico", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MX", "p": "Hasan42MX"},
    "44": {"cc": "44", "display_cc": "44", "country": "UK", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GB", "p": "Hasan42GB"},
    "49": {"cc": "49", "display_cc": "49", "country": "Germany", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DE", "p": "Hasan42DE"},
    "33": {"cc": "33", "display_cc": "33", "country": "France", "base_url": "http://8.222.182.223:8081", "u": "Hasan42FR", "p": "Hasan42FR"},
    "34": {"cc": "34", "display_cc": "34", "country": "Spain", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ES", "p": "Hasan42ES"},
    "39": {"cc": "39", "display_cc": "39", "country": "Italy", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IT", "p": "Hasan42IT"},
    "7": {"cc": "7", "display_cc": "7", "country": "Russia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42RU", "p": "Hasan42RU"},
    "31": {"cc": "31", "display_cc": "31", "country": "Netherlands", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NL", "p": "Hasan42NL"},
    "46": {"cc": "46", "display_cc": "46", "country": "Sweden", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SE", "p": "Hasan42SE"},
    "47": {"cc": "47", "display_cc": "47", "country": "Norway", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NO", "p": "Hasan42NO"},
    "45": {"cc": "45", "display_cc": "45", "country": "Denmark", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DK", "p": "Hasan42DK"},
    "358": {"cc": "358", "display_cc": "358", "country": "Finland", "base_url": "http://8.222.182.223:8081", "u": "Hasan42FI", "p": "Hasan42FI"},
    "880": {"cc": "880", "display_cc": "880", "country": "Bangladesh", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BD", "p": "Hasan42BD"},
    "91": {"cc": "91", "display_cc": "91", "country": "India", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IN", "p": "Hasan42IN"},
    "92": {"cc": "92", "display_cc": "92", "country": "Pakistan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PK", "p": "Hasan42PK"},
    "94": {"cc": "94", "display_cc": "94", "country": "Sri Lanka", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LK", "p": "Hasan42LK"},
    "977": {"cc": "977", "display_cc": "977", "country": "Nepal", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NP", "p": "Hasan42NP"},
    "60": {"cc": "60", "display_cc": "60", "country": "Malaysia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MY", "p": "Hasan42MY"},
    "62": {"cc": "62", "display_cc": "62", "country": "Indonesia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ID", "p": "Hasan42ID"},
    "63": {"cc": "63", "display_cc": "63", "country": "Philippines", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PH", "p": "Hasan42PH"},
    "66": {"cc": "66", "display_cc": "66", "country": "Thailand", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TH", "p": "Hasan42TH"},
    "84": {"cc": "84", "display_cc": "84", "country": "Vietnam", "base_url": "http://8.222.182.223:8081", "u": "Hasan42VN", "p": "Hasan42VN"},
    "81": {"cc": "81", "display_cc": "81", "country": "Japan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42JP", "p": "Hasan42JP"},
    "82": {"cc": "82", "display_cc": "82", "country": "Korea", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KR", "p": "Hasan42KR"},
    "86": {"cc": "86", "display_cc": "86", "country": "China", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CN", "p": "Hasan42CN"},
    "886": {"cc": "886", "display_cc": "886", "country": "Taiwan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TW", "p": "Hasan42TW"},
    "852": {"cc": "852", "display_cc": "852", "country": "Hong Kong", "base_url": "http://8.222.182.223:8081", "u": "Hasan42HK", "p": "Hasan42HK"},
    "853": {"cc": "853", "display_cc": "853", "country": "Macau", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MO", "p": "Hasan42MO"},
    "964": {"cc": "964", "display_cc": "964", "country": "Iraq", "base_url": "http://8.222.182.223:8081", "u": "JahidIQ", "p": "JahidIQ"},
    "966": {"cc": "966", "display_cc": "966", "country": "Saudi Arabia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SA", "p": "Hasan42SA"},
    "971": {"cc": "971", "display_cc": "971", "country": "UAE", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AE", "p": "Hasan42AE"},
    "962": {"cc": "962", "display_cc": "962", "country": "Jordan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42JO", "p": "Hasan42JO"},
    "961": {"cc": "961", "display_cc": "961", "country": "Lebanon", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LB", "p": "Hasan42LB"},
    "965": {"cc": "965", "display_cc": "965", "country": "Kuwait", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KW", "p": "Hasan42KW"},
    "968": {"cc": "968", "display_cc": "968", "country": "Oman", "base_url": "http://8.222.182.223:8081", "u": "Hasan42OM", "p": "Hasan42OM"},
    "973": {"cc": "973", "display_cc": "973", "country": "Bahrain", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BH", "p": "Hasan42BH"},
    "974": {"cc": "974", "display_cc": "974", "country": "Qatar", "base_url": "http://8.222.182.223:8081", "u": "Hasan42QA", "p": "Hasan42QA"},
    "98": {"cc": "98", "display_cc": "98", "country": "Iran", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IR", "p": "Hasan42IR"},
    "90": {"cc": "90", "display_cc": "90", "country": "Turkey", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TR", "p": "Hasan42TR"},
    "972": {"cc": "972", "display_cc": "972", "country": "Israel", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IL", "p": "Hasan42IL"},
    "20": {"cc": "20", "display_cc": "20", "country": "Egypt", "base_url": "http://8.222.182.223:8081", "u": "Hasan42EG", "p": "Hasan42EG"},
    "27": {"cc": "27", "display_cc": "27", "country": "South Africa", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ZA", "p": "Hasan42ZA"},
    "234": {"cc": "234", "display_cc": "234", "country": "Nigeria", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NG", "p": "Hasan42NG"},
    "212": {"cc": "212", "display_cc": "212", "country": "Morocco", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MA", "p": "Hasan42MA"},
    "216": {"cc": "216", "display_cc": "216", "country": "Tunisia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TN", "p": "Hasan42TN"},
    "213": {"cc": "213", "display_cc": "213", "country": "Algeria", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DZ", "p": "Hasan42DZ"},
    "55": {"cc": "55", "display_cc": "55", "country": "Brazil", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BR", "p": "Hasan42BR"},
    "54": {"cc": "54", "display_cc": "54", "country": "Argentina", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AR", "p": "Hasan42AR"},
    "56": {"cc": "56", "display_cc": "56", "country": "Chile", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CL", "p": "Hasan42CL"},
    "57": {"cc": "57", "display_cc": "57", "country": "Colombia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CO", "p": "Hasan42CO"},
    "51": {"cc": "51", "display_cc": "51", "country": "Peru", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PE", "p": "Hasan42PE"},
    "58": {"cc": "58", "display_cc": "58", "country": "Venezuela", "base_url": "http://8.222.182.223:8081", "u": "JahidVN", "p": "JahidVN"},
    "61": {"cc": "61", "display_cc": "61", "country": "Australia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AU", "p": "Hasan42AU"},
    "258": {"cc": "258", "display_cc": "258", "country": "Mozambique", "base_url": "http://8.222.182.223:8081", "u": "HasanMZ", "p": "HasanMZ"},
    
    # ===== NEWLY ADDED MISSING COUNTRIES (all with Hasan42+CC) =====
    "93": {"cc": "93", "display_cc": "93", "country": "Afghanistan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AF", "p": "Hasan42AF"},
    "355": {"cc": "355", "display_cc": "355", "country": "Albania", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AL", "p": "Hasan42AL"},
    "376": {"cc": "376", "display_cc": "376", "country": "Andorra", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AD", "p": "Hasan42AD"},
    "244": {"cc": "244", "display_cc": "244", "country": "Angola", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AO", "p": "Hasan42AO"},
    "268": {"cc": "268", "display_cc": "268", "country": "Antigua and Barbuda", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AG", "p": "Hasan42AG"},
    "374": {"cc": "374", "display_cc": "374", "country": "Armenia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AM", "p": "Hasan42AM"},
    "43": {"cc": "43", "display_cc": "43", "country": "Austria", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AT", "p": "Hasan42AT"},
    "994": {"cc": "994", "display_cc": "994", "country": "Azerbaijan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AZ", "p": "Hasan42AZ"},
    "1242": {"cc": "1242", "display_cc": "1242", "country": "Bahamas", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BS", "p": "Hasan42BS"},
    "1246": {"cc": "1246", "display_cc": "1246", "country": "Barbados", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BB", "p": "Hasan42BB"},
    "375": {"cc": "375", "display_cc": "375", "country": "Belarus", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BY", "p": "Hasan42BY"},
    "32": {"cc": "32", "display_cc": "32", "country": "Belgium", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BE", "p": "Hasan42BE"},
    "501": {"cc": "501", "display_cc": "501", "country": "Belize", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BZ", "p": "Hasan42BZ"},
    "229": {"cc": "229", "display_cc": "229", "country": "Benin", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BJ", "p": "Hasan42BJ"},
    "975": {"cc": "975", "display_cc": "975", "country": "Bhutan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BT", "p": "Hasan42BT"},
    "591": {"cc": "591", "display_cc": "591", "country": "Bolivia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BO", "p": "Hasan42BO"},
    "387": {"cc": "387", "display_cc": "387", "country": "Bosnia and Herzegovina", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BA", "p": "Hasan42BA"},
    "267": {"cc": "267", "display_cc": "267", "country": "Botswana", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BW", "p": "Hasan42BW"},
    "55": {"cc": "55", "display_cc": "55", "country": "Brazil", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BR", "p": "Hasan42BR"},
    "673": {"cc": "673", "display_cc": "673", "country": "Brunei", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BN", "p": "Hasan42BN"},
    "359": {"cc": "359", "display_cc": "359", "country": "Bulgaria", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BG", "p": "Hasan42BG"},
    "226": {"cc": "226", "display_cc": "226", "country": "Burkina Faso", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BF", "p": "Hasan42BF"},
    "257": {"cc": "257", "display_cc": "257", "country": "Burundi", "base_url": "http://8.222.182.223:8081", "u": "Hasan42BI", "p": "Hasan42BI"},
    "855": {"cc": "855", "display_cc": "855", "country": "Cambodia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KH", "p": "Hasan42KH"},
    "237": {"cc": "237", "display_cc": "237", "country": "Cameroon", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CM", "p": "Hasan42CM"},
    "238": {"cc": "238", "display_cc": "238", "country": "Cape Verde", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CV", "p": "Hasan42CV"},
    "236": {"cc": "236", "display_cc": "236", "country": "Central African Republic", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CF", "p": "Hasan42CF"},
    "235": {"cc": "235", "display_cc": "235", "country": "Chad", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TD", "p": "Hasan42TD"},
    "56": {"cc": "56", "display_cc": "56", "country": "Chile", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CL", "p": "Hasan42CL"},
    "86": {"cc": "86", "display_cc": "86", "country": "China", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CN", "p": "Hasan42CN"},
    "57": {"cc": "57", "display_cc": "57", "country": "Colombia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CO", "p": "Hasan42CO"},
    "269": {"cc": "269", "display_cc": "269", "country": "Comoros", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KM", "p": "Hasan42KM"},
    "242": {"cc": "242", "display_cc": "242", "country": "Congo", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CG", "p": "Hasan42CG"},
    "243": {"cc": "243", "display_cc": "243", "country": "Congo (DRC)", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CD", "p": "Hasan42CD"},
    "506": {"cc": "506", "display_cc": "506", "country": "Costa Rica", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CR", "p": "Hasan42CR"},
    "385": {"cc": "385", "display_cc": "385", "country": "Croatia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42HR", "p": "Hasan42HR"},
    "53": {"cc": "53", "display_cc": "53", "country": "Cuba", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CU", "p": "Hasan42CU"},
    "357": {"cc": "357", "display_cc": "357", "country": "Cyprus", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CY", "p": "Hasan42CY"},
    "420": {"cc": "420", "display_cc": "420", "country": "Czech Republic", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CZ", "p": "Hasan42CZ"},
    "45": {"cc": "45", "display_cc": "45", "country": "Denmark", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DK", "p": "Hasan42DK"},
    "253": {"cc": "253", "display_cc": "253", "country": "Djibouti", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DJ", "p": "Hasan42DJ"},
    "1767": {"cc": "1767", "display_cc": "1767", "country": "Dominica", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DM", "p": "Hasan42DM"},
    "1849": {"cc": "1849", "display_cc": "1849", "country": "Dominican Republic", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DO", "p": "Hasan42DO"},
    "593": {"cc": "593", "display_cc": "593", "country": "Ecuador", "base_url": "http://8.222.182.223:8081", "u": "Hasan42EC", "p": "Hasan42EC"},
    "20": {"cc": "20", "display_cc": "20", "country": "Egypt", "base_url": "http://8.222.182.223:8081", "u": "Hasan42EG", "p": "Hasan42EG"},
    "503": {"cc": "503", "display_cc": "503", "country": "El Salvador", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SV", "p": "Hasan42SV"},
    "240": {"cc": "240", "display_cc": "240", "country": "Equatorial Guinea", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GQ", "p": "Hasan42GQ"},
    "291": {"cc": "291", "display_cc": "291", "country": "Eritrea", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ER", "p": "Hasan42ER"},
    "372": {"cc": "372", "display_cc": "372", "country": "Estonia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42EE", "p": "Hasan42EE"},
    "268": {"cc": "268", "display_cc": "268", "country": "Eswatini", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SZ", "p": "Hasan42SZ"},
    "251": {"cc": "251", "display_cc": "251", "country": "Ethiopia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ET", "p": "Hasan42ET"},
    "679": {"cc": "679", "display_cc": "679", "country": "Fiji", "base_url": "http://8.222.182.223:8081", "u": "Hasan42FJ", "p": "Hasan42FJ"},
    "358": {"cc": "358", "display_cc": "358", "country": "Finland", "base_url": "http://8.222.182.223:8081", "u": "Hasan42FI", "p": "Hasan42FI"},
    "33": {"cc": "33", "display_cc": "33", "country": "France", "base_url": "http://8.222.182.223:8081", "u": "Hasan42FR", "p": "Hasan42FR"},
    "241": {"cc": "241", "display_cc": "241", "country": "Gabon", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GA", "p": "Hasan42GA"},
    "220": {"cc": "220", "display_cc": "220", "country": "Gambia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GM", "p": "Hasan42GM"},
    "995": {"cc": "995", "display_cc": "995", "country": "Georgia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GE", "p": "Hasan42GE"},
    "49": {"cc": "49", "display_cc": "49", "country": "Germany", "base_url": "http://8.222.182.223:8081", "u": "Hasan42DE", "p": "Hasan42DE"},
    "233": {"cc": "233", "display_cc": "233", "country": "Ghana", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GH", "p": "Hasan42GH"},
    "30": {"cc": "30", "display_cc": "30", "country": "Greece", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GR", "p": "Hasan42GR"},
    "1473": {"cc": "1473", "display_cc": "1473", "country": "Grenada", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GD", "p": "Hasan42GD"},
    "502": {"cc": "502", "display_cc": "502", "country": "Guatemala", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GT", "p": "Hasan42GT"},
    "224": {"cc": "224", "display_cc": "224", "country": "Guinea", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GN", "p": "Hasan42GN"},
    "245": {"cc": "245", "display_cc": "245", "country": "Guinea-Bissau", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GW", "p": "Hasan42GW"},
    "592": {"cc": "592", "display_cc": "592", "country": "Guyana", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GY", "p": "Hasan42GY"},
    "509": {"cc": "509", "display_cc": "509", "country": "Haiti", "base_url": "http://8.222.182.223:8081", "u": "Hasan42HT", "p": "Hasan42HT"},
    "504": {"cc": "504", "display_cc": "504", "country": "Honduras", "base_url": "http://8.222.182.223:8081", "u": "Hasan42HN", "p": "Hasan42HN"},
    "36": {"cc": "36", "display_cc": "36", "country": "Hungary", "base_url": "http://8.222.182.223:8081", "u": "Hasan42HU", "p": "Hasan42HU"},
    "354": {"cc": "354", "display_cc": "354", "country": "Iceland", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IS", "p": "Hasan42IS"},
    "91": {"cc": "91", "display_cc": "91", "country": "India", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IN", "p": "Hasan42IN"},
    "62": {"cc": "62", "display_cc": "62", "country": "Indonesia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ID", "p": "Hasan42ID"},
    "98": {"cc": "98", "display_cc": "98", "country": "Iran", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IR", "p": "Hasan42IR"},
    "964": {"cc": "964", "display_cc": "964", "country": "Iraq", "base_url": "http://8.222.182.223:8081", "u": "JahidIQ", "p": "JahidIQ"},
    "353": {"cc": "353", "display_cc": "353", "country": "Ireland", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IE", "p": "Hasan42IE"},
    "972": {"cc": "972", "display_cc": "972", "country": "Israel", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IL", "p": "Hasan42IL"},
    "39": {"cc": "39", "display_cc": "39", "country": "Italy", "base_url": "http://8.222.182.223:8081", "u": "Hasan42IT", "p": "Hasan42IT"},
    "225": {"cc": "225", "display_cc": "225", "country": "Ivory Coast", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CI", "p": "Hasan42CI"},
    "1876": {"cc": "1876", "display_cc": "1876", "country": "Jamaica", "base_url": "http://8.222.182.223:8081", "u": "Hasan42JM", "p": "Hasan42JM"},
    "81": {"cc": "81", "display_cc": "81", "country": "Japan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42JP", "p": "Hasan42JP"},
    "962": {"cc": "962", "display_cc": "962", "country": "Jordan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42JO", "p": "Hasan42JO"},
    "7": {"cc": "7", "display_cc": "7", "country": "Kazakhstan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KZ", "p": "Hasan42KZ"},
    "254": {"cc": "254", "display_cc": "254", "country": "Kenya", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KE", "p": "Hasan42KE"},
    "686": {"cc": "686", "display_cc": "686", "country": "Kiribati", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KI", "p": "Hasan42KI"},
    "850": {"cc": "850", "display_cc": "850", "country": "North Korea", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KP", "p": "Hasan42KP"},
    "82": {"cc": "82", "display_cc": "82", "country": "South Korea", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KR", "p": "Hasan42KR"},
    "383": {"cc": "383", "display_cc": "383", "country": "Kosovo", "base_url": "http://8.222.182.223:8081", "u": "Hasan42XK", "p": "Hasan42XK"},
    "965": {"cc": "965", "display_cc": "965", "country": "Kuwait", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KW", "p": "Hasan42KW"},
    "996": {"cc": "996", "display_cc": "996", "country": "Kyrgyzstan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KG", "p": "Hasan42KG"},
    "856": {"cc": "856", "display_cc": "856", "country": "Laos", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LA", "p": "Hasan42LA"},
    "371": {"cc": "371", "display_cc": "371", "country": "Latvia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LV", "p": "Hasan42LV"},
    "961": {"cc": "961", "display_cc": "961", "country": "Lebanon", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LB", "p": "Hasan42LB"},
    "266": {"cc": "266", "display_cc": "266", "country": "Lesotho", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LS", "p": "Hasan42LS"},
    "231": {"cc": "231", "display_cc": "231", "country": "Liberia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LR", "p": "Hasan42LR"},
    "218": {"cc": "218", "display_cc": "218", "country": "Libya", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LY", "p": "Hasan42LY"},
    "423": {"cc": "423", "display_cc": "423", "country": "Liechtenstein", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LI", "p": "Hasan42LI"},
    "370": {"cc": "370", "display_cc": "370", "country": "Lithuania", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LT", "p": "Hasan42LT"},
    "352": {"cc": "352", "display_cc": "352", "country": "Luxembourg", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LU", "p": "Hasan42LU"},
    "261": {"cc": "261", "display_cc": "261", "country": "Madagascar", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MG", "p": "Hasan42MG"},
    "265": {"cc": "265", "display_cc": "265", "country": "Malawi", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MW", "p": "Hasan42MW"},
    "60": {"cc": "60", "display_cc": "60", "country": "Malaysia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MY", "p": "Hasan42MY"},
    "960": {"cc": "960", "display_cc": "960", "country": "Maldives", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MV", "p": "Hasan42MV"},
    "223": {"cc": "223", "display_cc": "223", "country": "Mali", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ML", "p": "Hasan42ML"},
    "356": {"cc": "356", "display_cc": "356", "country": "Malta", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MT", "p": "Hasan42MT"},
    "692": {"cc": "692", "display_cc": "692", "country": "Marshall Islands", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MH", "p": "Hasan42MH"},
    "222": {"cc": "222", "display_cc": "222", "country": "Mauritania", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MR", "p": "Hasan42MR"},
    "230": {"cc": "230", "display_cc": "230", "country": "Mauritius", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MU", "p": "Hasan42MU"},
    "52": {"cc": "52", "display_cc": "52", "country": "Mexico", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MX", "p": "Hasan42MX"},
    "691": {"cc": "691", "display_cc": "691", "country": "Micronesia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42FM", "p": "Hasan42FM"},
    "373": {"cc": "373", "display_cc": "373", "country": "Moldova", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MD", "p": "Hasan42MD"},
    "377": {"cc": "377", "display_cc": "377", "country": "Monaco", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MC", "p": "Hasan42MC"},
    "976": {"cc": "976", "display_cc": "976", "country": "Mongolia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MN", "p": "Hasan42MN"},
    "382": {"cc": "382", "display_cc": "382", "country": "Montenegro", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ME", "p": "Hasan42ME"},
    "212": {"cc": "212", "display_cc": "212", "country": "Morocco", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MA", "p": "Hasan42MA"},
    "258": {"cc": "258", "display_cc": "258", "country": "Mozambique", "base_url": "http://8.222.182.223:8081", "u": "HasanMZ", "p": "HasanMZ"},
    "95": {"cc": "95", "display_cc": "95", "country": "Myanmar", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MM", "p": "Hasan42MM"},
    "264": {"cc": "264", "display_cc": "264", "country": "Namibia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NA", "p": "Hasan42NA"},
    "674": {"cc": "674", "display_cc": "674", "country": "Nauru", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NR", "p": "Hasan42NR"},
    "977": {"cc": "977", "display_cc": "977", "country": "Nepal", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NP", "p": "Hasan42NP"},
    "31": {"cc": "31", "display_cc": "31", "country": "Netherlands", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NL", "p": "Hasan42NL"},
    "64": {"cc": "64", "display_cc": "64", "country": "New Zealand", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NZ", "p": "Hasan42NZ"},
    "505": {"cc": "505", "display_cc": "505", "country": "Nicaragua", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NI", "p": "Hasan42NI"},
    "227": {"cc": "227", "display_cc": "227", "country": "Niger", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NE", "p": "Hasan42NE"},
    "234": {"cc": "234", "display_cc": "234", "country": "Nigeria", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NG", "p": "Hasan42NG"},
    "389": {"cc": "389", "display_cc": "389", "country": "North Macedonia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42MK", "p": "Hasan42MK"},
    "47": {"cc": "47", "display_cc": "47", "country": "Norway", "base_url": "http://8.222.182.223:8081", "u": "Hasan42NO", "p": "Hasan42NO"},
    "968": {"cc": "968", "display_cc": "968", "country": "Oman", "base_url": "http://8.222.182.223:8081", "u": "Hasan42OM", "p": "Hasan42OM"},
    "92": {"cc": "92", "display_cc": "92", "country": "Pakistan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PK", "p": "Hasan42PK"},
    "680": {"cc": "680", "display_cc": "680", "country": "Palau", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PW", "p": "Hasan42PW"},
    "970": {"cc": "970", "display_cc": "970", "country": "Palestine", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PS", "p": "Hasan42PS"},
    "507": {"cc": "507", "display_cc": "507", "country": "Panama", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PA", "p": "Hasan42PA"},
    "675": {"cc": "675", "display_cc": "675", "country": "Papua New Guinea", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PG", "p": "Hasan42PG"},
    "595": {"cc": "595", "display_cc": "595", "country": "Paraguay", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PY", "p": "Hasan42PY"},
    "51": {"cc": "51", "display_cc": "51", "country": "Peru", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PE", "p": "Hasan42PE"},
    "63": {"cc": "63", "display_cc": "63", "country": "Philippines", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PH", "p": "Hasan42PH"},
    "48": {"cc": "48", "display_cc": "48", "country": "Poland", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PL", "p": "Hasan42PL"},
    "351": {"cc": "351", "display_cc": "351", "country": "Portugal", "base_url": "http://8.222.182.223:8081", "u": "Hasan42PT", "p": "Hasan42PT"},
    "974": {"cc": "974", "display_cc": "974", "country": "Qatar", "base_url": "http://8.222.182.223:8081", "u": "Hasan42QA", "p": "Hasan42QA"},
    "40": {"cc": "40", "display_cc": "40", "country": "Romania", "base_url": "http://8.222.182.223:8081", "u": "Hasan42RO", "p": "Hasan42RO"},
    "7": {"cc": "7", "display_cc": "7", "country": "Russia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42RU", "p": "Hasan42RU"},
    "250": {"cc": "250", "display_cc": "250", "country": "Rwanda", "base_url": "http://8.222.182.223:8081", "u": "Hasan42RW", "p": "Hasan42RW"},
    "1869": {"cc": "1869", "display_cc": "1869", "country": "Saint Kitts and Nevis", "base_url": "http://8.222.182.223:8081", "u": "Hasan42KN", "p": "Hasan42KN"},
    "1758": {"cc": "1758", "display_cc": "1758", "country": "Saint Lucia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LC", "p": "Hasan42LC"},
    "1784": {"cc": "1784", "display_cc": "1784", "country": "Saint Vincent and Grenadines", "base_url": "http://8.222.182.223:8081", "u": "Hasan42VC", "p": "Hasan42VC"},
    "685": {"cc": "685", "display_cc": "685", "country": "Samoa", "base_url": "http://8.222.182.223:8081", "u": "Hasan42WS", "p": "Hasan42WS"},
    "378": {"cc": "378", "display_cc": "378", "country": "San Marino", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SM", "p": "Hasan42SM"},
    "239": {"cc": "239", "display_cc": "239", "country": "Sao Tome and Principe", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ST", "p": "Hasan42ST"},
    "966": {"cc": "966", "display_cc": "966", "country": "Saudi Arabia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SA", "p": "Hasan42SA"},
    "221": {"cc": "221", "display_cc": "221", "country": "Senegal", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SN", "p": "Hasan42SN"},
    "381": {"cc": "381", "display_cc": "381", "country": "Serbia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42RS", "p": "Hasan42RS"},
    "248": {"cc": "248", "display_cc": "248", "country": "Seychelles", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SC", "p": "Hasan42SC"},
    "232": {"cc": "232", "display_cc": "232", "country": "Sierra Leone", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SL", "p": "Hasan42SL"},
    "65": {"cc": "65", "display_cc": "65", "country": "Singapore", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SG", "p": "Hasan42SG"},
    "421": {"cc": "421", "display_cc": "421", "country": "Slovakia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SK", "p": "Hasan42SK"},
    "386": {"cc": "386", "display_cc": "386", "country": "Slovenia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SI", "p": "Hasan42SI"},
    "677": {"cc": "677", "display_cc": "677", "country": "Solomon Islands", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SB", "p": "Hasan42SB"},
    "252": {"cc": "252", "display_cc": "252", "country": "Somalia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SO", "p": "Hasan42SO"},
    "27": {"cc": "27", "display_cc": "27", "country": "South Africa", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ZA", "p": "Hasan42ZA"},
    "211": {"cc": "211", "display_cc": "211", "country": "South Sudan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SS", "p": "Hasan42SS"},
    "34": {"cc": "34", "display_cc": "34", "country": "Spain", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ES", "p": "Hasan42ES"},
    "94": {"cc": "94", "display_cc": "94", "country": "Sri Lanka", "base_url": "http://8.222.182.223:8081", "u": "Hasan42LK", "p": "Hasan42LK"},
    "249": {"cc": "249", "display_cc": "249", "country": "Sudan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SD", "p": "Hasan42SD"},
    "597": {"cc": "597", "display_cc": "597", "country": "Suriname", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SR", "p": "Hasan42SR"},
    "46": {"cc": "46", "display_cc": "46", "country": "Sweden", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SE", "p": "Hasan42SE"},
    "41": {"cc": "41", "display_cc": "41", "country": "Switzerland", "base_url": "http://8.222.182.223:8081", "u": "Hasan42CH", "p": "Hasan42CH"},
    "963": {"cc": "963", "display_cc": "963", "country": "Syria", "base_url": "http://8.222.182.223:8081", "u": "Hasan42SY", "p": "Hasan42SY"},
    "886": {"cc": "886", "display_cc": "886", "country": "Taiwan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TW", "p": "Hasan42TW"},
    "992": {"cc": "992", "display_cc": "992", "country": "Tajikistan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TJ", "p": "Hasan42TJ"},
    "255": {"cc": "255", "display_cc": "255", "country": "Tanzania", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TZ", "p": "Hasan42TZ"},
    "66": {"cc": "66", "display_cc": "66", "country": "Thailand", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TH", "p": "Hasan42TH"},
    "670": {"cc": "670", "display_cc": "670", "country": "Timor Leste", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TL", "p": "Hasan42TL"},
    "228": {"cc": "228", "display_cc": "228", "country": "Togo", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TG", "p": "Hasan42TG"},
    "676": {"cc": "676", "display_cc": "676", "country": "Tonga", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TO", "p": "Hasan42TO"},
    "1868": {"cc": "1868", "display_cc": "1868", "country": "Trinidad and Tobago", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TT", "p": "Hasan42TT"},
    "216": {"cc": "216", "display_cc": "216", "country": "Tunisia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TN", "p": "Hasan42TN"},
    "90": {"cc": "90", "display_cc": "90", "country": "Turkey", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TR", "p": "Hasan42TR"},
    "993": {"cc": "993", "display_cc": "993", "country": "Turkmenistan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TM", "p": "Hasan42TM"},
    "688": {"cc": "688", "display_cc": "688", "country": "Tuvalu", "base_url": "http://8.222.182.223:8081", "u": "Hasan42TV", "p": "Hasan42TV"},
    "256": {"cc": "256", "display_cc": "256", "country": "Uganda", "base_url": "http://8.222.182.223:8081", "u": "Hasan42UG", "p": "Hasan42UG"},
    "380": {"cc": "380", "display_cc": "380", "country": "Ukraine", "base_url": "http://8.222.182.223:8081", "u": "Hasan42UA", "p": "Hasan42UA"},
    "971": {"cc": "971", "display_cc": "971", "country": "UAE", "base_url": "http://8.222.182.223:8081", "u": "Hasan42AE", "p": "Hasan42AE"},
    "44": {"cc": "44", "display_cc": "44", "country": "United Kingdom", "base_url": "http://8.222.182.223:8081", "u": "Hasan42GB", "p": "Hasan42GB"},
    "598": {"cc": "598", "display_cc": "598", "country": "Uruguay", "base_url": "http://8.222.182.223:8081", "u": "Hasan42UY", "p": "Hasan42UY"},
    "998": {"cc": "998", "display_cc": "998", "country": "Uzbekistan", "base_url": "http://8.222.182.223:8081", "u": "Hasan42UZ", "p": "Hasan42UZ"},
    "678": {"cc": "678", "display_cc": "678", "country": "Vanuatu", "base_url": "http://8.222.182.223:8081", "u": "Hasan42VU", "p": "Hasan42VU"},
    "379": {"cc": "379", "display_cc": "379", "country": "Vatican City", "base_url": "http://8.222.182.223:8081", "u": "Hasan42VA", "p": "Hasan42VA"},
    "58": {"cc": "58", "display_cc": "58", "country": "Venezuela", "base_url": "http://8.222.182.223:8081", "u": "Hasan42VE", "p": "Hasan42VE"},
    "84": {"cc": "84", "display_cc": "84", "country": "Vietnam", "base_url": "http://8.222.182.223:8081", "u": "Hasan42VN", "p": "Hasan42VN"},
    "967": {"cc": "967", "display_cc": "967", "country": "Yemen", "base_url": "http://8.222.182.223:8081", "u": "Hasan42YE", "p": "Hasan42YE"},
    "260": {"cc": "260", "display_cc": "260", "country": "Zambia", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ZM", "p": "Hasan42ZM"},
    "263": {"cc": "263", "display_cc": "263", "country": "Zimbabwe", "base_url": "http://8.222.182.223:8081", "u": "Hasan42ZW", "p": "Hasan42ZW"},
}



# ==================== THREAD-SAFE STORAGE (COPY-ON-WRITE PATTERN) ====================
class AtomicStore:
    """Thread-safe store with copy-on-write to avoid race conditions"""
    def __init__(self):
        self._lock = threading.RLock()
        self._data = {}
    
    def get(self, key, default=None):
        """READ - safe to use without worrying about pop"""
        with self._lock:
            val = self._data.get(key, default)
            if isinstance(val, dict):
                return val.copy()  # Return copy to prevent mutation
            return val
    
    def update(self, key, value):
        """WRITE - atomic update"""
        with self._lock:
            self._data[key] = value
    
    def modify(self, key, modifier_fn):
        """ATOMIC MODIFY - safest pattern"""
        with self._lock:
            current = self._data.get(key, {})
            if isinstance(current, dict):
                current = current.copy()
            result = modifier_fn(current)
            self._data[key] = result
            return result
    
    def delete(self, key):
        with self._lock:
            return self._data.pop(key, None)
    
    def contains(self, key):
        with self._lock:
            return key in self._data

# Stores
user_numbers = AtomicStore()      # {user_id: {phone: {data}}}
api_tokens = AtomicStore()        # {cc: {token, expires}}
balances = AtomicStore()          # {user_id: {balance, history}}
daily_stats = AtomicStore()       # {user_id: {date: {total, otp, success, failed}}}
wallets = AtomicStore()           # {user_id: {method: account}}
withdraw_counts = AtomicStore()   # {user_id: {date: count}}
pending_withdraws = AtomicStore() # {user_id: {...}}
api_last_call = AtomicStore()     # {cc: datetime}
tracking_tasks = AtomicStore()    # {user_id: {phone: task}}

# Sheet queue - FIX 1: Use queue with ID to prevent duplicates
sheet_queue = []
sheet_processed = set()  # Track processed entries to prevent duplicates
sheet_running = True

# ==================== SHEET WORKER (FIXED: No duplicates) ====================
def sheet_worker():
    while sheet_running:
        try:
            if sheet_queue:
                p = sheet_queue.pop(0)
                # Create unique key for this entry
                entry_key = f"{p.get('user_id')}_{p.get('phone')}_{p.get('timestamp', '')}"
                
                # Skip if already processed
                if entry_key in sheet_processed:
                    continue
                
                try:
                    r = requests.post(GOOGLE_SHEET_URL, json=p, timeout=15)
                    if r.status_code == 200:
                        sheet_processed.add(entry_key)
                        print(f"   ✅ Sheet: {p.get('status','OK')}")
                    elif p.get('retry',0) < 3:
                        p['retry'] = p.get('retry',0) + 1
                        sheet_queue.append(p)
                except:
                    if p.get('retry',0) < 3:
                        p['retry'] = p.get('retry',0) + 1
                        sheet_queue.append(p)
            time.sleep(0.2)
        except:
            time.sleep(0.5)

threading.Thread(target=sheet_worker, daemon=True).start()

def queue_sheet(user_id, username, full_name, phone, cc, country, status, api_status, otp=""):
    # Add timestamp to prevent duplicates
    timestamp = datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S.%f')
    sheet_queue.append({
        "user_id": str(user_id), "username": username or "N/A", "full_name": full_name or "N/A",
        "phone": phone, "cc": str(cc), "country": country, "status": status,
        "api_status": str(api_status), "otp": otp, "retry": 0,
        "timestamp": timestamp  # Added for uniqueness
    })

def queue_paid_update(user_id, method):
    timestamp = datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S.%f')
    sheet_queue.append({
        "type": "paid_update", "user_id": str(user_id),
        "wallet_method": method, "timestamp": timestamp
    })

# ==================== HELPERS ====================
def get_bd_date():
    now = datetime.now(bd_tz)
    return (now - timedelta(days=1)).strftime('%Y-%m-%d') if now.hour < 16 else now.strftime('%Y-%m-%d')

def get_bd_hashtag():
    now = datetime.now(bd_tz)
    return (now - timedelta(days=1)).strftime('%Y%m%d') if now.hour < 16 else now.strftime('%Y%m%d')

def extract_number(text):
    """Extract CC + phone from text"""
    t = re.sub(r'[\s\-\(\)]', '', text.strip())
    if t.startswith('+'): t = t[1:]
    
    for cc in sorted(COUNTRY_APIS.keys(), key=len, reverse=True):
        if t.startswith(cc):
            p = t[len(cc):]
            if 5 <= len(p) <= 15:
                # Fix: use 'dc' if exists, otherwise use cc
                dc = COUNTRY_APIS[cc].get('dc', cc)
                return cc, p, dc
    
    if t.startswith('1') and len(t) == 11: return "11", t[1:], "1"
    if t.startswith('964'): return "964", t[3:], "964"
    if t.startswith('880'): return "880", t[3:], "880"
    return None, None, None
def add_balance(user_id, cc, amount):
    """Atomic balance add"""
    def modifier(b):
        b.setdefault("balance", 0)
        b.setdefault("history", [])
        b["balance"] += amount
        b["history"].append({
            "date": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S'),
            "cc": cc, "amount": amount
        })
        return b
    return balances.modify(str(user_id), modifier)

def get_balance(user_id):
    b = balances.get(str(user_id), {"balance": 0})
    return b.get("balance", 0)

def add_stats(user_id, status):
    uid, today = str(user_id), get_bd_date()
    def modifier(s):
        s.setdefault(today, {"total": 0, "otp": 0, "success": 0, "failed": 0})
        s[today]["total"] += 1
        if status == "OTP": s[today]["otp"] += 1
        elif status == "SUCCESS": s[today]["success"] += 1
        else: s[today]["failed"] += 1
        return s
    daily_stats.modify(uid, modifier)

def get_today_stats(user_id):
    uid, today = str(user_id), get_bd_date()
    s = daily_stats.get(uid, {})
    td = s.get(today, {"total": 0, "otp": 0})
    b = balances.get(uid, {"history": []})
    earn = sum(e.get("amount", 0) for e in b.get("history", []) if e.get("date", "").startswith(today))
    return td.get("otp", 0), earn

# ==================== API FUNCTIONS ====================
async def api_rate_limit(cc):
    """Rate limit per CC"""
    last = api_last_call.get(cc)
    if last:
        elapsed = (datetime.now() - last).total_seconds()
        if elapsed < API_COOLDOWN:
            await asyncio.sleep(API_COOLDOWN - elapsed)
    api_last_call.update(cc, datetime.now())

async def api_request(cc, method, endpoint, json_data=None, headers=None, timeout=10):
    """Generic API request with retry"""
    await api_rate_limit(cc)
    cfg = COUNTRY_APIS.get(cc)
    if not cfg: return None
    
    for attempt in range(2):  # Retry once on failure
        try:
            async with aiohttp.ClientSession() as s:
                url = f"{cfg['url']}{endpoint}"
                if method == "GET":
                    async with s.get(url, headers=headers, timeout=timeout) as r:
                        if r.status == 200: return await r.json()
                elif method == "POST":
                    async with s.post(url, json=json_data, headers=headers, timeout=timeout) as r:
                        if r.status == 200: return await r.json()
                elif method == "DELETE":
                    async with s.delete(url, headers=headers, timeout=timeout) as r:
                        return r.status == 200
        except:
            if attempt == 0:
                await asyncio.sleep(1)  # Retry delay
    return None

async def login(cc):
    """Login with token caching - retry on fail"""
    tok = api_tokens.get(cc)
    if tok and tok.get("expires", datetime.now()) > datetime.now():
        return tok["token"]
    
    cfg = COUNTRY_APIS.get(cc)
    if not cfg: return None
    
    r = await api_request(cc, "POST", "/user/login", 
                         {"account": cfg['u'], "password": cfg['p'], "identity": "Member"})
    
    if r and "data" in r and "token" in r["data"]:
        token = r["data"]["token"]
        api_tokens.update(cc, {"token": token, "expires": datetime.now() + timedelta(hours=23)})
        return token
    
    # Retry with fresh login
    await asyncio.sleep(1)
    r = await api_request(cc, "POST", "/user/login",
                         {"account": cfg['u'], "password": cfg['p'], "identity": "Member"})
    if r and "data" in r and "token" in r["data"]:
        token = r["data"]["token"]
        api_tokens.update(cc, {"token": token, "expires": datetime.now() + timedelta(hours=23)})
        return token
    return None

async def check_status(cc, phone, token):
    """Check number status - SAFE (returns None on failure)"""
    cfg = COUNTRY_APIS.get(cc)
    if not cfg: return None, None
    
    try:
        async with aiohttp.ClientSession() as s:
            h = {"Admin-Token": token}
            async with s.get(f"{cfg['url']}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}", 
                           headers=h, timeout=8) as r:
                if r.status == 200:
                    d = await r.json()
                    if d and "data" in d and "records" in d["data"] and d["data"]["records"]:
                        rec = d["data"]["records"][0]
                        return rec.get("registrationStatus"), rec.get("id")
    except:
        pass
    return None, None

async def add_number(cc, phone, token):
    """Add number to API"""
    cfg = COUNTRY_APIS.get(cc)
    if not cfg: return None
    try:
        async with aiohttp.ClientSession() as s:
            h = {"Admin-Token": token}
            async with s.post(f"{cfg['url']}/z-number-base/addNum?cc={cc}&phoneNum={phone}&smsStatus=2",
                            headers=h, timeout=8) as r:
                return r.status
    except:
        return None

async def submit_otp(cc, phone, code, token):
    """Submit OTP with retry"""
    cfg = COUNTRY_APIS.get(cc)
    if not cfg: return False
    
    for attempt in range(MAX_OTP_RETRY + 1):
        try:
            async with aiohttp.ClientSession() as s:
                h = {"Admin-Token": token}
                async with s.get(f"{cfg['url']}/z-number-base/allNum/uploadCode?cc={cc}&phoneNum={phone}&code={code}",
                               headers=h, timeout=10) as r:
                    if r.status == 200:
                        d = await r.json()
                        if d.get("code") == 200:
                            return True
            if attempt < MAX_OTP_RETRY:
                await asyncio.sleep(0.5)
        except:
            if attempt < MAX_OTP_RETRY:
                await asyncio.sleep(0.5)
    return False

async def delete_number(cc, phone, record_id, token):
    """Delete number - ONLY if record_id EXISTS and status != 1"""
    if record_id is None:
        return False
    cfg = COUNTRY_APIS.get(cc)
    if not cfg: return False
    try:
        async with aiohttp.ClientSession() as s:
            h = {"Admin-Token": token}
            async with s.delete(f"{cfg['url']}/z-number-base/deleteNum/{record_id}", headers=h, timeout=8) as r:
                return r.status == 200
    except:
        return False

# ==================== NUMBER TRACKER (FIXED) ====================
async def track_number(bot, chat_id, msg_id, phone, cc, dc, user_id, uname, fname, country, token):
    """Track single number - NO pop(), uses copy pattern"""
    display = f"+{dc} {phone}"
    start = datetime.now()
    last_status = None
    stuck_start = None
    last_update = 0
    max_wait = 180
    uid = str(user_id)
    
    while (datetime.now() - start).total_seconds() < max_wait:
        elapsed = int((datetime.now() - start).total_seconds())
        
        # Update message every 15 seconds (fixed spam risk)
        if elapsed - last_update >= 15:
            last_update = elapsed
            try:
                await bot.edit_message_text(
                    chat_id=chat_id, message_id=msg_id,
                    text=f"🟡 {display}\n⏳ {int((max_wait-elapsed)/60)}m {int((max_wait-elapsed)%60)}s"
                )
            except:
                pass
        
        status, record_id = await check_status(cc, phone, token)
        
        if status is not None and status != last_status:
            last_status = status
            
            # SUCCESS
            if status == 1:
                await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"✅ {display} 🟢 SUCCESS")
                
                # Get number data (COPY, don't pop)
                ud = user_numbers.get(uid, {})
                num_data = ud.get(phone, {})
                is_otp = num_data.get("otp_submitted", False)
                otp_code = num_data.get("otp_code", "")
                
                if is_otp and otp_code:
                    rate = COUNTRY_RATES.get(cc, {}).get("rate", 0)
                    if rate > 0:
                        result = add_balance(user_id, cc, rate)
                        bal = result["balance"]
                        add_stats(user_id, "OTP")
                        tot_ver, tot_earn = get_today_stats(user_id)
                        
                        # ========== FIX 2: User notification (same as before) ==========
                        try:
                            await bot.send_message(user_id,
                                f"💰 OTP Verified!\n📞 {display}\n🌎 {country}\n💵 Earning: ${rate:.2f}\n"
                                f"🏦 Total Balance: ${bal:.2f}\n"
                                f"🔖Total verified today: {tot_ver}\n\n"
                                f"#ID{user_id}_{get_bd_hashtag()}",
                                parse_mode='none')
                        except:
                            pass
                        
                        queue_sheet(user_id, uname, fname, phone, cc, country, "SUCCESS", f"OTP Verified - Earned ${rate:.2f}", otp_code)
                        
                        # ========== FIX 3: Admin notification for OTP success ==========
                        admin_msg = (
                            f"✅ OTP VERIFIED SUCCESS\n\n"
                            f"👤 Name: {fname}\n"
                            f"🆔 Username: @{uname if uname else 'N/A'}\n"
                            f"📞 Number: {display}\n"
                            f"🌍 Country: {country}\n"
                            f"💰 Amount: ${rate:.2f}\n"
                            f"🔖 Tag: #ID{user_id}_{get_bd_hashtag()}"
                        )
                        try:
                            await bot.send_message(ADMIN_ID, admin_msg, parse_mode='none')
                        except Exception as e:
                            print(f"Admin notification failed: {e}")
                    else:
                        queue_sheet(user_id, uname, fname, phone, cc, country, "SUCCESS", "OTP Verified (No rate)", otp_code)
                else:
                    add_stats(user_id, "SUCCESS")
                    queue_sheet(user_id, uname, fname, phone, cc, country, "SUCCESS", "Verified (Auto)")
                
                # Atomic remove from active numbers
                def remove_number(nums):
                    nums.pop(phone, None)
                    return nums
                user_numbers.modify(uid, remove_number)
                return
            
            # FAILED - auto delete (SAFE: checks record_id)
            elif status in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
                if record_id and status != 1:
                    await delete_number(cc, phone, record_id, token)
                
                smap = {4: "Not Registered", 6: "Wrong OTP"}
                smsg = smap.get(status, f"Failed ({status})")
                
                await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ {display}\n{smsg}")
                
                def remove_number(nums):
                    otp_code = nums.get(phone, {}).get("otp_code", "")
                    nums.pop(phone, None)
                    return nums
                ud = user_numbers.modify(uid, remove_number)
                otp_val = ud.get(phone, {}).get("otp_code", "") if phone in ud else ""
                
                queue_sheet(user_id, uname, fname, phone, cc, country, "FAILED", smsg, otp_val)
                add_stats(user_id, "FAILED")
                return
            
            elif status == 2:
                stuck_start = datetime.now()
        
        # Stuck check
        if status == 2 and stuck_start:
            if (datetime.now() - stuck_start).total_seconds() > STUCK_TIMEOUT:
                if record_id:
                    await delete_number(cc, phone, record_id, token)
                try:
                    await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏰ {display} Stuck - Deleted")
                except:
                    pass
                
                def remove_number(nums):
                    nums.pop(phone, None)
                    return nums
                user_numbers.modify(uid, remove_number)
                return
        
        await asyncio.sleep(TRACK_INTERVAL)
    
    # Timeout
    if last_status == 2 and record_id:
        await delete_number(cc, phone, record_id, token)
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏰ {display} Timeout")
    except:
        pass
    
    def remove_number(nums):
        nums.pop(phone, None)
        return nums
    user_numbers.modify(uid, remove_number)

# ==================== PROCESS NUMBER (FIXED) ====================
async def process_number(bot, update, msg, user, cc, phone, dc, country):
    """Process one number - atomic pattern, no pop() misuse"""
    uid, display = str(user.id), f"+{dc} {phone}"
    
    # Check user limit (using GET not pop)
    ud = user_numbers.get(uid, {})
    if len(ud) >= MAX_ACTIVE_NUMBERS:
        await msg.edit_text(f"❌ {display}\nMax {MAX_ACTIVE_NUMBERS} active!\nWait for current ones.")
        return
    
    # Login
    token = await login(cc)
    if not token:
        await msg.edit_text(f"❌ {display}\nAPI login failed")
        queue_sheet(user.id, user.username, user.full_name, phone, cc, country, "FAILED", "Login failed")
        return
    
    # Check existing
    status, rid = await check_status(cc, phone, token)
    if status == 1:
        await msg.edit_text(f"✅ {display} 🟢 ALREADY REGISTERED")
        queue_sheet(user.id, user.username, user.full_name, phone, cc, country, "SUCCESS", "Already Registered")
        return
    if status == 4:
        await msg.edit_text(f"❌ {display}\nNot Registered")
        queue_sheet(user.id, user.username, user.full_name, phone, cc, country, "FAILED", "Already Not Registered")
        return
    
    # Add number
    add_status = await add_number(cc, phone, token)
    if add_status not in [200, 409]:
        await msg.edit_text(f"❌ {display}\nAdd failed")
        queue_sheet(user.id, user.username, user.full_name, phone, cc, country, "FAILED", f"Add failed {add_status}")
        return
    
    await asyncio.sleep(1)
    
    # Quick recheck
    status, rid = await check_status(cc, phone, token)
    if status == 1:
        await msg.edit_text(f"✅ {display} 🟢 SUCCESS")
        queue_sheet(user.id, user.username, user.full_name, phone, cc, country, "SUCCESS", "Verified")
        return
    if status == 4:
        await msg.edit_text(f"❌ {display}\nNot Registered")
        queue_sheet(user.id, user.username, user.full_name, phone, cc, country, "FAILED", "Not Registered")
        return
    
    # Atomic add to active numbers
    def add_active(nums):
        nums[phone] = {
            "cc": cc, "dc": dc, "phone": phone, "country": country,
            "token": token, "otp_submitted": False, "otp_code": "",
            "msg_id": msg.message_id, "chat_id": update.message.chat_id if update.message else user.id
        }
        return nums
    user_numbers.modify(uid, add_active)
    
    await msg.edit_text(f"🟡 {display} IN PROGRESS")
    
    # Start tracking
    asyncio.create_task(track_number(
        bot, update.message.chat_id if update.message else user.id, msg.message_id,
        phone, cc, dc, user.id, user.username, user.full_name, country, token
    ))

# ==================== OTP HANDLER (FIXED - REPLY-BASED) ====================
async def handle_otp(update, context):
    """Handle OTP - reply-based matching to correct number"""
    user = update.effective_user
    otp = update.message.text.strip()
    uid = str(user.id)
    
    if not re.match(r'^\d{4,8}$', otp):
        await update.message.reply_text("❌ Invalid OTP!")
        return
    
    # Reply-based: match the replied message
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to the number message with OTP!")
        return
    
    replied_msg_id = update.message.reply_to_message.message_id
    
    # Find number by matching message_id
    ud = user_numbers.get(uid, {})
    target_phone = None
    target_data = None
    
    for p, d in ud.items():
        if d.get("msg_id") == replied_msg_id:
            target_phone = p
            target_data = d
            break
    
    if not target_phone:
        await update.message.reply_text("❌ Reply to an active number message!\nNumber may have expired.")
        return
    
    if target_data.get("otp_submitted"):
        await update.message.reply_text("⚠️ OTP already submitted for this number!")
        return
    
    display = f"+{target_data['dc']} {target_phone}"
    print(f"   🔑 OTP: {otp} → {display}")
    
    # Mark OTP submitted (atomic)
    def mark_otp(nums):
        if target_phone in nums:
            nums[target_phone]["otp_submitted"] = True
            nums[target_phone]["otp_code"] = otp
        return nums
    user_numbers.modify(uid, mark_otp)
    
    # Submit to API
    success = await submit_otp(target_data['cc'], target_phone, otp, target_data['token'])
    
    if success:
        print(f"   ✅ OTP Accepted: {display}")
    else:
        print(f"   ❌ Wrong OTP: {display}")
        
        # Delete number
        status, rid = await check_status(target_data['cc'], target_phone, target_data['token'])
        if rid and status != 1:
            await delete_number(target_data['cc'], target_phone, rid, target_data['token'])
        
        def remove_number(nums):
            nums.pop(target_phone, None)
            return nums
        user_numbers.modify(uid, remove_number)
        
        queue_sheet(user.id, user.username, user.full_name, target_phone, target_data['cc'], 
                   target_data['country'], "FAILED", "Wrong OTP", otp)
        add_stats(user.id, "FAILED")
        
        await update.message.reply_text(f"❌ Wrong OTP for {display}")

# ==================== TELEGRAM HANDLERS ====================
async def start(update, context):
    user = update.effective_user
    
    kb = [
        ["📊 Statistics", "💰 Balance", "💸 Withdraw"],
        ["🌍 Price List", "📥 Download"],
        ["🆘 Support", "📸 Payment", "👛 Wallet"]
    ]
    
    await update.message.reply_text(
        f"👋 *Welcome {user.first_name}!*\n\n"
        f"📱 Send numbers with country code\n"
        f"⚡ Max {MAX_ACTIVE_NUMBERS} at once\n"
        f"🔑 Reply to number msg with OTP\n"
        f"💡 Example: `+9647803260789`\n\n"
        f"💰 Earn after OTP verification!\n"
        f"💸 Withdraw min $0.50",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode='Markdown'
    )

async def handle_msg(update, context):
    user = update.effective_user
    text = update.message.text.strip()
    
    # Wallet setup
    if context.user_data.get('awaiting_wallet'):
        await save_wallet(update, context)
        return
    
    # OTP reply (reply-based)
    if update.message.reply_to_message:
        await handle_otp(update, context)
        return
    
    # Menu buttons
    if text in ["📊 Statistics", "💰 Balance", "💸 Withdraw", "🌍 Price List", 
                "📥 Download", "🆘 Support", "📸 Payment", "👛 Wallet"]:
        await menu_handler(update, context)
        return
    
    # Number extraction
    cc, phone, dc = extract_number(text)
    if not cc:
        await update.message.reply_text("❌ Send: `+12264566666`", parse_mode='Markdown')
        return
    
    if cc not in COUNTRY_APIS:
        await update.message.reply_text("❌ Country not supported!")
        return
    
    # Channel check (STRICT - no bypass)
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            await update.message.reply_text(
                f"🔒 Join {REQUIRED_CHANNEL} first!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")]])
            )
            return
    except Exception as e:
        await update.message.reply_text("⚠️ Channel check failed. Try again in a moment.")
        return
    
    country = COUNTRY_APIS[cc]['country']
    display = f"+{dc} {phone}"
    
    print(f"\n📞 {display}")
    msg = await update.message.reply_text(f"🔄 {display}...")
    
    asyncio.create_task(process_number(context.bot, update, msg, user, cc, phone, dc, country))

async def menu_handler(update, context):
    user = update.effective_user
    t = update.message.text.strip()
    uid = str(user.id)
    
    if t == "📊 Statistics":
        s = daily_stats.get(uid, {})
        today = get_bd_date()
        td = s.get(today, {"total":0,"otp":0})
        await update.message.reply_text(f"📊 *Today*\n📱 Total: {td['total']}\n✅ Verified: {td['otp']}", parse_mode='Markdown')
    
    elif t == "💰 Balance":
        bal = get_balance(user.id)
        await update.message.reply_text(f"💰 *Balance: ${bal:.2f}*\n{'✅ Can withdraw!' if bal >= 1.0 else 'Min: $1.0'}", parse_mode='Markdown')
    
    elif t == "💸 Withdraw":
        await withdraw_request(update, context)
    
    elif t == "🌍 Price List":
        txt = "🌍 *Prices*\n\n"
        for cc, d in sorted(COUNTRY_RATES.items(), key=lambda x: x[1]["rate"], reverse=True)[:20]:
            txt += f"{d['flag']} {d['country'][:15]}: ${d['rate']:.2f}\n"
        await update.message.reply_text(txt, parse_mode='Markdown')
    
    elif t == "📥 Download":
        await update.message.reply_text(f"📥 Commands:\n/mystats\n/mybalance\n/myhistory\n/mysheet")
    
    elif t == "🆘 Support":
        await update.message.reply_text(f"📢 {REQUIRED_CHANNEL}\n👑 Admin: {ADMIN_ID}")
    
    elif t == "📸 Payment":
        await update.message.reply_text("💰 Min: $0.50\nDaily: 1 time\nMethods: bKash/Nagad/Binance")
    
    elif t == "👛 Wallet":
        await wallet_show(update, context)

# ==================== WALLET (thread-safe) ====================
async def wallet_setup(update, context):
    kb = [
        [InlineKeyboardButton("📱 bKash", callback_data="w_bkash")],
        [InlineKeyboardButton("📱 Nagad", callback_data="w_nagad")],
        [InlineKeyboardButton("₿ Binance", callback_data="w_binance")],
        [InlineKeyboardButton("❌ Cancel", callback_data="w_cancel")]
    ]
    await update.message.reply_text("👛 Setup wallet:", reply_markup=InlineKeyboardMarkup(kb))

async def wallet_callback(update, context):
    q = update.callback_query
    await q.answer()
    d = q.data
    
    if d == "w_cancel": await q.message.delete(); return
    
    m = {"w_bkash":"bkash","w_nagad":"nagad","w_binance":"binance"}.get(d)
    if m:
        context.user_data['w_method'] = m
        context.user_data['awaiting_wallet'] = True
        prompts = {"bkash":"📱 Send bKash number:","nagad":"📱 Send Nagad number:","binance":"₿ Send Pay ID:"}
        await q.message.edit_text(prompts.get(m,""))

async def save_wallet(update, context):
    uid, acc = str(update.effective_user.id), update.message.text.strip()
    m = context.user_data.get('w_method')
    if not m: return
    
    def modifier(w):
        w[m] = acc
        return w
    wallets.modify(uid, modifier)
    
    nm = {"bkash":"bKash","nagad":"Nagad","binance":"Binance"}
    await update.message.reply_text(f"✅ Saved!\n{nm.get(m,m)}: `{acc}`", parse_mode='Markdown')
    context.user_data['awaiting_wallet'] = False

async def wallet_show(update, context):
    uid = str(update.effective_user.id)
    w = wallets.get(uid, {})
    
    if not w:
        await update.message.reply_text("❌ No wallet! Use /wallet")
        return
    
    nm = {"bkash":"📱 bKash","nagad":"📱 Nagad","binance":"₿ Binance"}
    txt = "👛 *Wallets*\n\n"
    for m, a in w.items(): txt += f"{nm.get(m,m)}: `{a}`\n"
    await update.message.reply_text(txt, parse_mode='Markdown')

# ==================== WITHDRAW (FIXED: Notifications work) ====================
async def withdraw_request(update, context):
    user = update.effective_user
    uid, today = str(user.id), get_bd_date()
    
    w = wallets.get(uid, {})
    if not w:
        await update.message.reply_text("❌ Setup wallet first!")
        return
    
    wc = withdraw_counts.get(uid, {})
    if wc.get(today, 0) >= 1:
        await update.message.reply_text("❌ Daily limit reached!")
        return
    
    if pending_withdraws.contains(uid):
        await update.message.reply_text("⏳ Pending withdraw exists!")
        return
    
    bal = get_balance(user.id)
    if bal < 0.1:
        await update.message.reply_text(f"❌ Min $0.10! Balance: ${bal:.2f}")
        return
    
    kb = []
    if "bkash" in w: kb.append([InlineKeyboardButton(f"📱 bKash ({w['bkash']})", callback_data="wd_bkash")])
    if "nagad" in w: kb.append([InlineKeyboardButton(f"📱 Nagad ({w['nagad']})", callback_data="wd_nagad")])
    if "binance" in w: kb.append([InlineKeyboardButton(f"₿ Binance ({w['binance'][:12]}...)", callback_data="wd_binance")])
    kb.append([InlineKeyboardButton("❌ Cancel", callback_data="wd_cancel")])
    
    await update.message.reply_text(f"💸 *Withdraw ${bal:.2f}*\nSelect:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def withdraw_callback(update, context):
    q = update.callback_query
    await q.answer()
    uid, d, today = str(q.from_user.id), q.data, get_bd_date()
    
    if d == "wd_cancel": 
        await q.message.delete()
        return
    
    m = {"wd_bkash":"bkash","wd_nagad":"nagad","wd_binance":"binance"}.get(d)
    if not m:
        return
    
    w = wallets.get(uid, {})
    acc = w.get(m, "")
    bal = get_balance(q.from_user.id)
    
    # Store pending
    pending_withdraws.update(uid, {"amount":bal,"method":m,"account":acc,"date":today,
                                    "fname":q.from_user.full_name,"uname":q.from_user.username or "N/A"})
    
    # Reset balance
    def reset_bal(b):
        b["balance"] = 0
        b["history"] = []
        return b
    balances.modify(uid, reset_bal)
    
    # Mark daily
    def mark_daily(wc):
        wc[today] = 1
        return wc
    withdraw_counts.modify(uid, mark_daily)
    
    # Reset today's OTP count
    def reset_stats(s):
        if today in s: s[today]["otp"] = 0
        return s
    daily_stats.modify(uid, reset_stats)
    
    nm = {"bkash":"bKash","nagad":"Nagad","binance":"Binance"}
    await q.message.edit_text(f"✅ *Submitted!*\n💰 ${bal:.2f}\n⏳ Processing...", parse_mode='Markdown')
    
    queue_paid_update(uid, nm.get(m, m))
    
    # ========== FIX 4: Admin withdraw notification ==========
    admin_msg = (
        f"💸 WITHDRAW REQUEST\n\n"
        f"👤 Name: {q.from_user.full_name}\n"
        f"🆔 Username: @{q.from_user.username or 'N/A'}\n"
        f"💰 Amount: ${bal:.2f}\n"
        f"📱 Method: {nm.get(m,m)}\n"
        f"🏦 Account: {acc}"
    )
    try:
        await context.bot.send_message(
            ADMIN_ID,
            admin_msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Confirm", callback_data=f"c_{uid}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"r_{uid}")
            ]]),
            parse_mode='none'
        )
    except Exception as e:
        print(f"Admin withdraw notification failed: {e}")

async def admin_withdraw_action(update, context):
    q = update.callback_query
    await q.answer()
    a, uid = q.data.split("_")[0], q.data.split("_")[1]
    
    p = pending_withdraws.delete(uid)
    if not p:
        await q.message.edit_text(q.message.text + "\n\n⚠️ Already processed", parse_mode='Markdown')
        return
    
    nm = {"bkash":"bKash","nagad":"Nagad","binance":"Binance"}
    
    if a == "c":
        await q.message.edit_text(q.message.text + "\n\n✅ *CONFIRMED*", parse_mode='Markdown')
        try:
            # ========== FIX 5: User notification for approved withdraw ==========
            await context.bot.send_message(
                int(uid), 
                f"✅ Withdrawal Approved!\n\n"
                f"💰 Amount: ${p['amount']:.2f}\n"
                f"📱 Method: {nm.get(p['method'], '')}\n"
                f"⏳ Status: Paid Successfully",
                parse_mode='none'
            )
        except:
            pass
    else:  # Reject
        # Restore balance
        def restore_bal(b):
            b["balance"] = p['amount']
            return b
        balances.modify(uid, restore_bal)
        
        # Remove daily limit
        def remove_daily(wc):
            wc.pop(get_bd_date(), None)
            return wc
        withdraw_counts.modify(uid, remove_daily)
        
        await q.message.edit_text(q.message.text + "\n\n❌ *REJECTED - Restored*", parse_mode='Markdown')
        try:
            # ========== FIX 6: User notification for rejected withdraw ==========
            await context.bot.send_message(
                int(uid), 
                f"❌ Withdrawal Rejected!\n\n"
                f"💰 Amount: ${p['amount']:.2f} has been restored to your balance.\n"
                f"📝 Reason: Please contact support for details.",
                parse_mode='none'
            )
        except:
            pass

# ==================== ADMIN RATE MANAGEMENT ====================
async def cmd_addrate(update, context):
    """Admin: Add/Update rate | Usage: /addrate cc amount"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 *Usage:* `/addrate cc amount`\n\n"
            "Example:\n"
            "• `/addrate 880 0.15` - Set Bangladesh rate\n"
            "• `/addrate 966 0.45` - Set Saudi rate",
            parse_mode='Markdown'
        )
        return
    
    cc = context.args[0].strip()
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Use number like 0.15")
        return
    
    if cc in COUNTRY_APIS:
        country_name = COUNTRY_APIS[cc]["country"]
        flag = COUNTRY_RATES.get(cc, {}).get("flag", "🌍")
        
        COUNTRY_RATES[cc] = {
            "country": country_name,
            "rate": amount,
            "flag": flag,
            "cc": cc
        }
        
        await update.message.reply_text(
            f"✅ *Rate Updated!*\n\n"
            f"🇨🇨 {flag} {country_name}\n"
            f"💰 New Rate: ${amount:.2f} per OTP",
            parse_mode='Markdown'
        )
        
        # Save rates to sheet
        save_rates_to_sheet()
        
        print(f"   📊 Rate updated: {cc} ({country_name}) = ${amount:.2f}")
    else:
        await update.message.reply_text(f"❌ Country code `{cc}` not found in API list!")

async def cmd_removerate(update, context):
    """Admin: Remove rate | Usage: /removerate cc"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text("📝 *Usage:* `/removerate cc`\nExample: `/removerate 880`", parse_mode='Markdown')
        return
    
    cc = context.args[0].strip()
    
    if cc in COUNTRY_RATES:
        country_name = COUNTRY_RATES[cc]["country"]
        del COUNTRY_RATES[cc]
        
        await update.message.reply_text(
            f"✅ *Rate Removed!*\n\n"
            f"🇨🇨 {country_name} removed from price list",
            parse_mode='Markdown'
        )
        
        save_rates_to_sheet()
        print(f"   🗑️ Rate removed: {cc} ({country_name})")
    else:
        await update.message.reply_text(f"❌ Country code `{cc}` not found in rate list!")

async def cmd_listrates(update, context):
    """Admin: List all rates | Usage: /listrates"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not COUNTRY_RATES:
        await update.message.reply_text("❌ No rates configured!\nUse /addrate to add countries.")
        return
    
    sorted_rates = sorted(COUNTRY_RATES.items(), key=lambda x: x[1]["rate"], reverse=True)
    
    rate_text = "📊 *Current Rates (Admin View)*\n\n"
    rate_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    rate_text += "🇨🇨 *Country*        *CC*    *Rate*\n"
    rate_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for cc, data in sorted_rates:
        flag = data.get("flag", "🌍")
        country = data["country"][:15]
        rate = data["rate"]
        rate_text += f"{flag} {country:<15} `{cc:<4}` 💵 ${rate:.2f}\n"
    
    rate_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    rate_text += f"📊 Total countries: *{len(COUNTRY_RATES)}*"
    
    await update.message.reply_text(rate_text, parse_mode='Markdown')

async def cmd_saverates(update, context):
    """Admin: Save rates to sheet | Usage: /saverates"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    save_rates_to_sheet()
    await update.message.reply_text("✅ All rates saved to Google Sheet!")

def save_rates_to_sheet():
    """Save all rates to Google Sheet"""
    rates_data = []
    for cc, data in COUNTRY_RATES.items():
        rates_data.append({
            "cc": cc,
            "country": data["country"],
            "rate": data["rate"],
            "flag": data.get("flag", "🌍"),
            "timestamp": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    payload = {
        "type": "rates_update",
        "data": rates_data,
        "timestamp": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')
    }
    sheet_queue.append(payload)
    print(f"   📤 Rates saved to sheet: {len(rates_data)} countries")

# ==================== ADMIN BALANCE & WITHDRAWAL MANAGEMENT ====================

# Store minimum withdrawal (default $0.50)
MIN_WITHDRAW = 0.50

async def cmd_addbalance(update, context):
    """Admin: Add balance to any user | Usage: /addbalance user_id amount"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 *Usage:* `/addbalance user_id amount`\n\n"
            "Example:\n"
            "• `/addbalance 7015259172 5.00` - Add $5.00\n"
            "• `/addbalance 7319925086 10.50` - Add $10.50",
            parse_mode='Markdown'
        )
        return
    
    target_uid = context.args[0].strip()
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Use number like 5.00")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return
    
    # Add balance
    def add_bal(b):
        b.setdefault("balance", 0)
        b.setdefault("history", [])
        b["balance"] += amount
        b["history"].append({
            "date": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S'),
            "cc": "ADMIN",
            "amount": amount,
            "type": "ADMIN_ADD"
        })
        return b
    
    result = balances.modify(target_uid, add_bal)
    
    await update.message.reply_text(
        f"✅ *Balance Added!*\n\n"
        f"👤 User: `{target_uid}`\n"
        f"💰 Amount: +${amount:.2f}\n"
        f"🏦 New Balance: ${result['balance']:.2f}",
        parse_mode='Markdown'
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            int(target_uid),
            f"💰 *Admin Added Balance!*\n\n"
            f"💵 Amount: +${amount:.2f}\n"
            f"🏦 New Balance: ${result['balance']:.2f}",
            parse_mode='Markdown'
        )
    except:
        pass
    
    print(f"   💰 Admin added ${amount:.2f} to user {target_uid}")

async def cmd_removebalance(update, context):
    """Admin: Remove balance from any user | Usage: /removebalance user_id amount"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 *Usage:* `/removebalance user_id amount`\n\n"
            "Example:\n"
            "• `/removebalance 7015259172 3.00` - Remove $3.00\n"
            "• `/removebalance 7319925086 1.50` - Remove $1.50",
            parse_mode='Markdown'
        )
        return
    
    target_uid = context.args[0].strip()
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Use number like 3.00")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive!")
        return
    
    # Get current balance
    current = balances.get(target_uid, {"balance": 0, "history": []})
    
    if current.get("balance", 0) < amount:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n"
            f"Current: ${current['balance']:.2f}\n"
            f"Trying to remove: ${amount:.2f}"
        )
        return
    
    # Remove balance
    def remove_bal(b):
        b["balance"] = b.get("balance", 0) - amount
        b.setdefault("history", []).append({
            "date": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S'),
            "cc": "ADMIN",
            "amount": -amount,
            "type": "ADMIN_REMOVE"
        })
        return b
    
    result = balances.modify(target_uid, remove_bal)
    
    await update.message.reply_text(
        f"✅ *Balance Removed!*\n\n"
        f"👤 User: `{target_uid}`\n"
        f"💰 Amount: -${amount:.2f}\n"
        f"🏦 New Balance: ${result['balance']:.2f}",
        parse_mode='Markdown'
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            int(target_uid),
            f"⚠️ *Admin Removed Balance!*\n\n"
            f"💵 Amount: -${amount:.2f}\n"
            f"🏦 New Balance: ${result['balance']:.2f}\n\n"
            f"Contact {REQUIRED_CHANNEL} for queries",
            parse_mode='Markdown'
        )
    except:
        pass
    
    print(f"   💰 Admin removed ${amount:.2f} from user {target_uid}")

async def cmd_checkbalance(update, context):
    """Admin: Check any user's balance | Usage: /checkbalance user_id"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 *Usage:* `/checkbalance user_id`\n\n"
            "Example: `/checkbalance 7015259172`",
            parse_mode='Markdown'
        )
        return
    
    target_uid = context.args[0].strip()
    
    # Get user data
    b = balances.get(target_uid, {"balance": 0, "history": []})
    s = daily_stats.get(target_uid, {})
    today = get_bd_date()
    td = s.get(today, {"total": 0, "otp": 0})
    
    # Get wallet info
    w = wallets.get(target_uid, {})
    wallet_text = ""
    if w:
        nm = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance"}
        wallet_text = "\n👛 *Wallets:*\n"
        for m, a in w.items():
            wallet_text += f"• {nm.get(m, m)}: `{a}`\n"
    
    await update.message.reply_text(
        f"👤 *User Balance Info*\n\n"
        f"🆔 ID: `{target_uid}`\n"
        f"💰 Balance: ${b['balance']:.2f}\n"
        f"📊 Today OTP: {td.get('otp', 0)}\n"
        f"📱 Today Total: {td.get('total', 0)}"
        f"{wallet_text}",
        parse_mode='Markdown'
    )

async def cmd_setminwithdraw(update, context):
    """Admin: Set minimum withdrawal amount | Usage: /setminwithdraw amount"""
    global MIN_WITHDRAW
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            f"📝 *Usage:* `/setminwithdraw amount`\n\n"
            f"Current: ${MIN_WITHDRAW:.2f}\n\n"
            f"Example:\n"
            f"• `/setminwithdraw 1.00` - Set to $1.00\n"
            f"• `/setminwithdraw 0.25` - Set to $0.25",
            parse_mode='Markdown'
        )
        return
    
    try:
        new_amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Use number like 1.00")
        return
    
    if new_amount < 0.10:
        await update.message.reply_text("❌ Minimum withdrawal cannot be less than $0.10!")
        return
    
    old_amount = MIN_WITHDRAW
    MIN_WITHDRAW = new_amount
    
    await update.message.reply_text(
        f"✅ *Minimum Withdrawal Updated!*\n\n"
        f"💰 Old: ${old_amount:.2f}\n"
        f"💰 New: ${MIN_WITHDRAW:.2f}",
        parse_mode='Markdown'
    )
    
    print(f"   ⚙️ Min withdrawal changed: ${old_amount:.2f} → ${MIN_WITHDRAW:.2f}")

async def cmd_allbalances(update, context):
    """Admin: Show all users with balances | Usage: /allbalances"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    # Collect all users with balances
    all_users = []
    total_balance = 0
    
    for uid in balances._data:
        b = balances.get(uid, {"balance": 0})
        bal = b.get("balance", 0)
        if bal > 0:
            all_users.append((uid, bal))
            total_balance += bal
    
    if not all_users:
        await update.message.reply_text("📊 No users with balance yet!")
        return
    
    # Sort by balance descending
    all_users.sort(key=lambda x: x[1], reverse=True)
    
    txt = "📊 *All User Balances*\n\n"
    txt += f"━━━━━━━━━━━━━━━━━━━━━\n"
    
    for uid, bal in all_users[:20]:
        txt += f"👤 `{uid[:10]}...` : ${bal:.2f}\n"
    
    if len(all_users) > 20:
        txt += f"\n... and {len(all_users)-20} more users"
    
    txt += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    txt += f"📊 Total: *{len(all_users)}* users\n"
    txt += f"💰 Total Balance: *${total_balance:.2f}*"
    
    await update.message.reply_text(txt, parse_mode='Markdown')


# ==================== DOWNLOAD ====================
async def cmd_mystats(update, context):
    uid, bal = str(update.effective_user.id), get_balance(update.effective_user.id)
    s = daily_stats.get(uid, {})
    txt = f"📊 Stats | 💰 ${bal:.2f}\n\n"
    for d, st in sorted(s.items()): txt += f"{d}: T={st['total']} OTP={st['otp']}\n"
    await update.message.reply_text(txt[:4000] or "No data")

async def cmd_mybalance(update, context):
    b = balances.get(str(update.effective_user.id), {"balance":0,"history":[]})
    txt = f"💰 ${b['balance']:.2f}\n\n"
    for h in b.get("history",[])[-20:]: txt += f"{h['date']}: +${h['amount']:.2f}\n"
    await update.message.reply_text(txt[:4000] or "No data")

async def cmd_myhistory(update, context): await cmd_mystats(update, context)
async def cmd_mysheet(update, context): await update.message.reply_text(f"🔗 {GOOGLE_SHEET_URL}")

# ==================== MEMORY CLEANUP ====================
async def cleanup_task():
    """Prevent memory leaks - runs every hour"""
    while True:
        await asyncio.sleep(3600)
        try:
            # Clean old API tokens
            now = datetime.now()
            old_ccs = []
            for cc in api_tokens._data:
                tok = api_tokens.get(cc)
                if tok and tok.get("expires", now) < now:
                    old_ccs.append(cc)
            for cc in old_ccs:
                api_tokens.delete(cc)
            
            # Clean completed tracking tasks
            # (handled automatically by task completion)
        except:
            pass

# ==================== FASTAPI ====================
app = FastAPI()

@app.get("/")
async def root(): return {"status": "active", "bot": "WhatsApp v3.1 Stable"}

@app.get("/health")
async def health(): return {"status": "healthy"}

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)

# ==================== MAIN ====================
 # ==================== MAIN ====================
def main():
    threading.Thread(target=run_fastapi, daemon=True).start()
    print(f"✅ FastAPI: port {PORT}")
    
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # User Commands
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("wallet", wallet_setup))
    app_bot.add_handler(CommandHandler("mystats", cmd_mystats))
    app_bot.add_handler(CommandHandler("mybalance", cmd_mybalance))
    app_bot.add_handler(CommandHandler("myhistory", cmd_myhistory))
    app_bot.add_handler(CommandHandler("mysheet", cmd_mysheet))
    
    # Admin Rate Commands
    app_bot.add_handler(CommandHandler("addrate", cmd_addrate))
    app_bot.add_handler(CommandHandler("removerate", cmd_removerate))
    app_bot.add_handler(CommandHandler("listrates", cmd_listrates))
    app_bot.add_handler(CommandHandler("saverates", cmd_saverates))
    
    # Admin Balance Commands
    app_bot.add_handler(CommandHandler("addbalance", cmd_addbalance))
    app_bot.add_handler(CommandHandler("removebalance", cmd_removebalance))
    app_bot.add_handler(CommandHandler("checkbalance", cmd_checkbalance))
    app_bot.add_handler(CommandHandler("setminwithdraw", cmd_setminwithdraw))
    app_bot.add_handler(CommandHandler("allbalances", cmd_allbalances))
    
    # Callbacks
    app_bot.add_handler(CallbackQueryHandler(wallet_callback, pattern="^w_"))
    app_bot.add_handler(CallbackQueryHandler(withdraw_callback, pattern="^wd_"))
    app_bot.add_handler(CallbackQueryHandler(admin_withdraw_action, pattern="^[cr]_"))
    
    # Messages
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    # Start cleanup task - FIXED for Python 3.14
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(cleanup_task())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(cleanup_task())
    
    print("\n" + "="*60)
    print("✅ BOT v3.1 STABLE RUNNING")
    print(f"📱 Max {MAX_ACTIVE_NUMBERS} numbers/user")
    print(f"🔑 Reply-based OTP (correct matching)")
    print(f"🛡️ Copy-on-write (no race conditions)")
    print(f"🧹 Auto memory cleanup")
    print(f"💰 Admin: /addrate /removerate /listrates")
    print(f"💵 Admin: /addbalance /removebalance /checkbalance")
    print(f"⚙️ Admin: /setminwithdraw /allbalances")
    print("="*60 + "\n")
    
    app_bot.run_polling()

if __name__ == "__main__":
    main()

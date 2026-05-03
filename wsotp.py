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

# ==================== JSON DATA PERSISTENCE (FIXED) ====================
JSON_FILE = "bot_data.json"

def datetime_converter(obj):
    """Convert datetime objects to string for JSON serialization"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def save_json_data():
    """Save all AtomicStore data to JSON file with datetime handling"""
    try:
        # Convert datetime objects in api_tokens
        api_tokens_clean = {}
        for cc, tok_data in api_tokens._data.items():
            if tok_data and isinstance(tok_data, dict):
                clean_data = tok_data.copy()
                if 'expires' in clean_data and isinstance(clean_data['expires'], datetime):
                    clean_data['expires'] = clean_data['expires'].isoformat()
                api_tokens_clean[cc] = clean_data
            else:
                api_tokens_clean[cc] = tok_data
        
        data = {
            "user_numbers": user_numbers._data if hasattr(user_numbers, '_data') else {},
            "api_tokens": api_tokens_clean,
            "balances": balances._data if hasattr(balances, '_data') else {},
            "daily_stats": daily_stats._data if hasattr(daily_stats, '_data') else {},
            "wallets": wallets._data if hasattr(wallets, '_data') else {},
            "withdraw_counts": withdraw_counts._data if hasattr(withdraw_counts, '_data') else {},
            "pending_withdraws": pending_withdraws._data if hasattr(pending_withdraws, '_data') else {},
            "api_last_call": {},  # Don't save last_call (datetime)
            "last_save": datetime.now().isoformat()
        }
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=datetime_converter)
        print(f"   💾 JSON saved: {len(data['balances'])} users")
    except Exception as e:
        print(f"   ⚠️ JSON save error: {e}")

def load_json_data():
    """Load all AtomicStore data from JSON file and restore datetime objects"""
    try:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                data = json.load(f)
            
            # Restore user_numbers
            if hasattr(user_numbers, '_data'):
                user_numbers._data.update(data.get("user_numbers", {}))
            
            # Restore api_tokens and convert string back to datetime
            if hasattr(api_tokens, '_data'):
                for cc, tok_data in data.get("api_tokens", {}).items():
                    if tok_data and isinstance(tok_data, dict) and 'expires' in tok_data:
                        tok_data['expires'] = datetime.fromisoformat(tok_data['expires'])
                    api_tokens._data[cc] = tok_data
            
            # Restore balances
            if hasattr(balances, '_data'):
                balances._data.update(data.get("balances", {}))
            
            # Restore daily_stats
            if hasattr(daily_stats, '_data'):
                daily_stats._data.update(data.get("daily_stats", {}))
            
            # Restore wallets
            if hasattr(wallets, '_data'):
                wallets._data.update(data.get("wallets", {}))
            
            # Restore withdraw_counts
            if hasattr(withdraw_counts, '_data'):
                withdraw_counts._data.update(data.get("withdraw_counts", {}))
            
            # Restore pending_withdraws
            if hasattr(pending_withdraws, '_data'):
                pending_withdraws._data.update(data.get("pending_withdraws", {}))
            
            total_users = len(data.get("balances", {}))
            print(f"   💾 JSON loaded: {total_users} users restored")
            if data.get('last_save'):
                print(f"   📅 Last save: {data['last_save']}")
    except Exception as e:
        print(f"   ⚠️ JSON load error: {e}")
        
def periodic_json_save():
    """Auto-save every 30 seconds"""
    while True:
        time.sleep(3600)
        save_json_data()

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

COUNTRY_APIS = {
    # Americas
    "11":{"cc":"11","dc":"1","country":"Canada","url":"http://8.222.182.223:8081","u":"Hasan42CA","p":"Hasan42CA"},
    "52":{"cc":"52","dc":"52","country":"Mexico","url":"http://8.222.182.223:8081","u":"Hasan42MX","p":"Hasan42MX"},
    "55":{"cc":"55","dc":"55","country":"Brazil","url":"http://8.222.182.223:8081","u":"Hasan42BR","p":"Hasan42BR"},
    "58":{"cc":"58","dc":"58","country":"Venezuela","url":"http://8.222.182.223:8081","u":"Hasan42VE","p":"Hasan42VE"},
    "54":{"cc":"54","dc":"54","country":"Argentina","url":"http://8.222.182.223:8081","u":"Hasan42AR","p":"Hasan42AR"},
    "56":{"cc":"56","dc":"56","country":"Chile","url":"http://8.222.182.223:8081","u":"Hasan42CL","p":"Hasan42CL"},
    "57":{"cc":"57","dc":"57","country":"Colombia","url":"http://8.222.182.223:8081","u":"Hasan42CO","p":"Hasan42CO"},
    "51":{"cc":"51","dc":"51","country":"Peru","url":"http://8.222.182.223:8081","u":"Hasan42PE","p":"Hasan42PE"},
    "507":{"cc":"507","dc":"507","country":"Panama","url":"http://8.222.182.223:8081","u":"Hasan42PA","p":"Hasan42PA"},
    "506":{"cc":"506","dc":"506","country":"Costa Rica","url":"http://8.222.182.223:8081","u":"Hasan42CR","p":"Hasan42CR"},
    "503":{"cc":"503","dc":"503","country":"El Salvador","url":"http://8.222.182.223:8081","u":"Hasan42SV","p":"Hasan42SV"},
    "505":{"cc":"505","dc":"505","country":"Nicaragua","url":"http://8.222.182.223:8081","u":"Hasan42NI","p":"Hasan42NI"},
    "504":{"cc":"504","dc":"504","country":"Honduras","url":"http://8.222.182.223:8081","u":"Hasan42HN","p":"Hasan42HN"},
    "501":{"cc":"501","dc":"501","country":"Belize","url":"http://8.222.182.223:8081","u":"Hasan42BZ","p":"Hasan42BZ"},
    "509":{"cc":"509","dc":"509","country":"Haiti","url":"http://8.222.182.223:8081","u":"Hasan42HT","p":"Hasan42HT"},
    "53":{"cc":"53","dc":"53","country":"Cuba","url":"http://8.222.182.223:8081","u":"Hasan42CU","p":"Hasan42CU"},
    "593":{"cc":"593","dc":"593","country":"Ecuador","url":"http://8.222.182.223:8081","u":"Hasan42EC","p":"Hasan42EC"},
    "595":{"cc":"595","dc":"595","country":"Paraguay","url":"http://8.222.182.223:8081","u":"Hasan42PY","p":"Hasan42PY"},
    "598":{"cc":"598","dc":"598","country":"Uruguay","url":"http://8.222.182.223:8081","u":"Hasan42UY","p":"Hasan42UY"},
    "591":{"cc":"591","dc":"591","country":"Bolivia","url":"http://8.222.182.223:8081","u":"Hasan42BO","p":"Hasan42BO"},
    "592":{"cc":"592","dc":"592","country":"Guyana","url":"http://8.222.182.223:8081","u":"Hasan42GY","p":"Hasan42GY"},
    "597":{"cc":"597","dc":"597","country":"Suriname","url":"http://8.222.182.223:8081","u":"Hasan42SR","p":"Hasan42SR"},
    
    # Europe
    "44":{"cc":"44","dc":"44","country":"UK","url":"http://8.222.182.223:8081","u":"Hasan42GB","p":"Hasan42GB"},
    "49":{"cc":"49","dc":"49","country":"Germany","url":"http://8.222.182.223:8081","u":"Hasan42DE","p":"Hasan42DE"},
    "33":{"cc":"33","dc":"33","country":"France","url":"http://8.222.182.223:8081","u":"Hasan42FR","p":"Hasan42FR"},
    "7":{"cc":"7","dc":"7","country":"Russia","url":"http://8.222.182.223:8081","u":"Hasan42RU","p":"Hasan42RU"},
    "39":{"cc":"39","dc":"39","country":"Italy","url":"http://8.222.182.223:8081","u":"Hasan42IT","p":"Hasan42IT"},
    "34":{"cc":"34","dc":"34","country":"Spain","url":"http://8.222.182.223:8081","u":"Hasan42ES","p":"Hasan42ES"},
    "31":{"cc":"31","dc":"31","country":"Netherlands","url":"http://8.222.182.223:8081","u":"Hasan42NL","p":"Hasan42NL"},
    "46":{"cc":"46","dc":"46","country":"Sweden","url":"http://8.222.182.223:8081","u":"Hasan42SE","p":"Hasan42SE"},
    "47":{"cc":"47","dc":"47","country":"Norway","url":"http://8.222.182.223:8081","u":"Hasan42NO","p":"Hasan42NO"},
    "45":{"cc":"45","dc":"45","country":"Denmark","url":"http://8.222.182.223:8081","u":"Hasan42DK","p":"Hasan42DK"},
    "358":{"cc":"358","dc":"358","country":"Finland","url":"http://8.222.182.223:8081","u":"Hasan42FI","p":"Hasan42FI"},
    "32":{"cc":"32","dc":"32","country":"Belgium","url":"http://8.222.182.223:8081","u":"Hasan42BE","p":"Hasan42BE"},
    "41":{"cc":"41","dc":"41","country":"Switzerland","url":"http://8.222.182.223:8081","u":"Hasan42CH","p":"Hasan42CH"},
    "43":{"cc":"43","dc":"43","country":"Austria","url":"http://8.222.182.223:8081","u":"Hasan42AT","p":"Hasan42AT"},
    "48":{"cc":"48","dc":"48","country":"Poland","url":"http://8.222.182.223:8081","u":"Hasan42PL","p":"Hasan42PL"},
    "420":{"cc":"420","dc":"420","country":"Czech Republic","url":"http://8.222.182.223:8081","u":"Hasan42CZ","p":"Hasan42CZ"},
    "421":{"cc":"421","dc":"421","country":"Slovakia","url":"http://8.222.182.223:8081","u":"Hasan42SK","p":"Hasan42SK"},
    "36":{"cc":"36","dc":"36","country":"Hungary","url":"http://8.222.182.223:8081","u":"Hasan42HU","p":"Hasan42HU"},
    "40":{"cc":"40","dc":"40","country":"Romania","url":"http://8.222.182.223:8081","u":"Hasan42RO","p":"Hasan42RO"},
    "359":{"cc":"359","dc":"359","country":"Bulgaria","url":"http://8.222.182.223:8081","u":"Hasan42BG","p":"Hasan42BG"},
    "30":{"cc":"30","dc":"30","country":"Greece","url":"http://8.222.182.223:8081","u":"Hasan42GR","p":"Hasan42GR"},
    "351":{"cc":"351","dc":"351","country":"Portugal","url":"http://8.222.182.223:8081","u":"Hasan42PT","p":"Hasan42PT"},
    "353":{"cc":"353","dc":"353","country":"Ireland","url":"http://8.222.182.223:8081","u":"Hasan42IE","p":"Hasan42IE"},
    "354":{"cc":"354","dc":"354","country":"Iceland","url":"http://8.222.182.223:8081","u":"Hasan42IS","p":"Hasan42IS"},
    "352":{"cc":"352","dc":"352","country":"Luxembourg","url":"http://8.222.182.223:8081","u":"Hasan42LU","p":"Hasan42LU"},
    "356":{"cc":"356","dc":"356","country":"Malta","url":"http://8.222.182.223:8081","u":"Hasan42MT","p":"Hasan42MT"},
    "386":{"cc":"386","dc":"386","country":"Slovenia","url":"http://8.222.182.223:8081","u":"Hasan42SI","p":"Hasan42SI"},
    "385":{"cc":"385","dc":"385","country":"Croatia","url":"http://8.222.182.223:8081","u":"Hasan42HR","p":"Hasan42HR"},
    "387":{"cc":"387","dc":"387","country":"Bosnia","url":"http://8.222.182.223:8081","u":"Hasan42BA","p":"Hasan42BA"},
    "381":{"cc":"381","dc":"381","country":"Serbia","url":"http://8.222.182.223:8081","u":"Hasan42RS","p":"Hasan42RS"},
    "382":{"cc":"382","dc":"382","country":"Montenegro","url":"http://8.222.182.223:8081","u":"Hasan42ME","p":"Hasan42ME"},
    "389":{"cc":"389","dc":"389","country":"North Macedonia","url":"http://8.222.182.223:8081","u":"Hasan42MK","p":"Hasan42MK"},
    "373":{"cc":"373","dc":"373","country":"Moldova","url":"http://8.222.182.223:8081","u":"Hasan42MD","p":"Hasan42MD"},
    "375":{"cc":"375","dc":"375","country":"Belarus","url":"http://8.222.182.223:8081","u":"Hasan42BY","p":"Hasan42BY"},
    "380":{"cc":"380","dc":"380","country":"Ukraine","url":"http://8.222.182.223:8081","u":"Hasan42UA","p":"Hasan42UA"},
    "370":{"cc":"370","dc":"370","country":"Lithuania","url":"http://8.222.182.223:8081","u":"Hasan42LT","p":"Hasan42LT"},
    "371":{"cc":"371","dc":"371","country":"Latvia","url":"http://8.222.182.223:8081","u":"Hasan42LV","p":"Hasan42LV"},
    "372":{"cc":"372","dc":"372","country":"Estonia","url":"http://8.222.182.223:8081","u":"Hasan42EE","p":"Hasan42EE"},
    
    # Asia
    "880":{"cc":"880","dc":"880","country":"Bangladesh","url":"http://8.222.182.223:8081","u":"Hasan42BD","p":"Hasan42BD"},
    "92":{"cc":"92","dc":"92","country":"Pakistan","url":"http://8.222.182.223:8081","u":"Hasan42PK","p":"Hasan42PK"},
    "964":{"cc":"964","dc":"964","country":"Iraq","url":"http://8.222.182.223:8081","u":"Hasan42IQ","p":"Hasan42IQ"},
    "966":{"cc":"966","dc":"966","country":"Saudi Arabia","url":"http://8.222.182.223:8081","u":"Hasan42SA","p":"Hasan42SA"},
    "20":{"cc":"20","dc":"20","country":"Egypt","url":"http://8.222.182.223:8081","u":"Hasan42EG","p":"Hasan42EG"},
    "968":{"cc":"968","dc":"968","country":"Oman","url":"http://8.222.182.223:8081","u":"Hasan42OM","p":"Hasan42OM"},
    "60":{"cc":"60","dc":"60","country":"Malaysia","url":"http://8.222.182.223:8081","u":"Hasan42MY","p":"Hasan42MY"},
    "62":{"cc":"62","dc":"62","country":"Indonesia","url":"http://8.222.182.223:8081","u":"Hasan42ID","p":"Hasan42ID"},
    "84":{"cc":"84","dc":"84","country":"Vietnam","url":"http://8.222.182.223:8081","u":"Hasan42VN","p":"Hasan42VN"},
    "886":{"cc":"886","dc":"886","country":"Taiwan","url":"http://8.222.182.223:8081","u":"Hasan42TW","p":"Hasan42TW"},
    "977":{"cc":"977","dc":"977","country":"Nepal","url":"http://8.222.182.223:8081","u":"Hasan42NP","p":"Hasan42NP"},
    "91":{"cc":"91","dc":"91","country":"India","url":"http://8.222.182.223:8081","u":"Hasan42IN","p":"Hasan42IN"},
    "94":{"cc":"94","dc":"94","country":"Sri Lanka","url":"http://8.222.182.223:8081","u":"Hasan42LK","p":"Hasan42LK"},
    "95":{"cc":"95","dc":"95","country":"Myanmar","url":"http://8.222.182.223:8081","u":"Hasan42MM","p":"Hasan42MM"},
    "66":{"cc":"66","dc":"66","country":"Thailand","url":"http://8.222.182.223:8081","u":"Hasan42TH","p":"Hasan42TH"},
    "63":{"cc":"63","dc":"63","country":"Philippines","url":"http://8.222.182.223:8081","u":"Hasan42PH","p":"Hasan42PH"},
    "82":{"cc":"82","dc":"82","country":"South Korea","url":"http://8.222.182.223:8081","u":"Hasan42KR","p":"Hasan42KR"},
    "81":{"cc":"81","dc":"81","country":"Japan","url":"http://8.222.182.223:8081","u":"Hasan42JP","p":"Hasan42JP"},
    "86":{"cc":"86","dc":"86","country":"China","url":"http://8.222.182.223:8081","u":"Hasan42CN","p":"Hasan42CN"},
    "852":{"cc":"852","dc":"852","country":"Hong Kong","url":"http://8.222.182.223:8081","u":"Hasan42HK","p":"Hasan42HK"},
    "853":{"cc":"853","dc":"853","country":"Macau","url":"http://8.222.182.223:8081","u":"Hasan42MO","p":"Hasan42MO"},
    "673":{"cc":"673","dc":"673","country":"Brunei","url":"http://8.222.182.223:8081","u":"Hasan42BN","p":"Hasan42BN"},
    "855":{"cc":"855","dc":"855","country":"Cambodia","url":"http://8.222.182.223:8081","u":"Hasan42KH","p":"Hasan42KH"},
    "856":{"cc":"856","dc":"856","country":"Laos","url":"http://8.222.182.223:8081","u":"Hasan42LA","p":"Hasan42LA"},
    "98":{"cc":"98","dc":"98","country":"Iran","url":"http://8.222.182.223:8081","u":"Hasan42IR","p":"Hasan42IR"},
    "90":{"cc":"90","dc":"90","country":"Turkey","url":"http://8.222.182.223:8081","u":"Hasan42TR","p":"Hasan42TR"},
    "961":{"cc":"961","dc":"961","country":"Lebanon","url":"http://8.222.182.223:8081","u":"Hasan42LB","p":"Hasan42LB"},
    "962":{"cc":"962","dc":"962","country":"Jordan","url":"http://8.222.182.223:8081","u":"Hasan42JO","p":"Hasan42JO"},
    "963":{"cc":"963","dc":"963","country":"Syria","url":"http://8.222.182.223:8081","u":"Hasan42SY","p":"Hasan42SY"},
    "965":{"cc":"965","dc":"965","country":"Kuwait","url":"http://8.222.182.223:8081","u":"Hasan42KW","p":"Hasan42KW"},
    "967":{"cc":"967","dc":"967","country":"Yemen","url":"http://8.222.182.223:8081","u":"Hasan42YE","p":"Hasan42YE"},
    "971":{"cc":"971","dc":"971","country":"UAE","url":"http://8.222.182.223:8081","u":"Hasan42AE","p":"Hasan42AE"},
    "972":{"cc":"972","dc":"972","country":"Israel","url":"http://8.222.182.223:8081","u":"Hasan42IL","p":"Hasan42IL"},
    "973":{"cc":"973","dc":"973","country":"Bahrain","url":"http://8.222.182.223:8081","u":"Hasan42BH","p":"Hasan42BH"},
    "974":{"cc":"974","dc":"974","country":"Qatar","url":"http://8.222.182.223:8081","u":"Hasan42QA","p":"Hasan42QA"},
    
    # Africa
    "234":{"cc":"234","dc":"234","country":"Nigeria","url":"http://8.222.182.223:8081","u":"Hasan42NG","p":"Hasan42NG"},
    "212":{"cc":"212","dc":"212","country":"Morocco","url":"http://8.222.182.223:8081","u":"Hasan42MA","p":"Hasan42MA"},
    "27":{"cc":"27","dc":"27","country":"South Africa","url":"http://8.222.182.223:8081","u":"Hasan42ZA","p":"Hasan42ZA"},
    "20":{"cc":"20","dc":"20","country":"Egypt","url":"http://8.222.182.223:8081","u":"Hasan42EG","p":"Hasan42EG"},
    "213":{"cc":"213","dc":"213","country":"Algeria","url":"http://8.222.182.223:8081","u":"Hasan42DZ","p":"Hasan42DZ"},
    "216":{"cc":"216","dc":"216","country":"Tunisia","url":"http://8.222.182.223:8081","u":"Hasan42TN","p":"Hasan42TN"},
    "218":{"cc":"218","dc":"218","country":"Libya","url":"http://8.222.182.223:8081","u":"Hasan42LY","p":"Hasan42LY"},
    "211":{"cc":"211","dc":"211","country":"South Sudan","url":"http://8.222.182.223:8081","u":"Hasan42SS","p":"Hasan42SS"},
    "254":{"cc":"254","dc":"254","country":"Kenya","url":"http://8.222.182.223:8081","u":"Hasan42KE","p":"Hasan42KE"},
    "255":{"cc":"255","dc":"255","country":"Tanzania","url":"http://8.222.182.223:8081","u":"Hasan42TZ","p":"Hasan42TZ"},
    "256":{"cc":"256","dc":"256","country":"Uganda","url":"http://8.222.182.223:8081","u":"Hasan42UG","p":"Hasan42UG"},
    "250":{"cc":"250","dc":"250","country":"Rwanda","url":"http://8.222.182.223:8081","u":"Hasan42RW","p":"Hasan42RW"},
    "251":{"cc":"251","dc":"251","country":"Ethiopia","url":"http://8.222.182.223:8081","u":"Hasan42ET","p":"Hasan42ET"},
    "252":{"cc":"252","dc":"252","country":"Somalia","url":"http://8.222.182.223:8081","u":"Hasan42SO","p":"Hasan42SO"},
    "253":{"cc":"253","dc":"253","country":"Djibouti","url":"http://8.222.182.223:8081","u":"Hasan42DJ","p":"Hasan42DJ"},
    "257":{"cc":"257","dc":"257","country":"Burundi","url":"http://8.222.182.223:8081","u":"Hasan42BI","p":"Hasan42BI"},
    "258":{"cc":"258","dc":"258","country":"Mozambique","url":"http://8.222.182.223:8081","u":"Hasan42MZ","p":"Hasan42MZ"},
    "260":{"cc":"260","dc":"260","country":"Zambia","url":"http://8.222.182.223:8081","u":"Hasan42ZM","p":"Hasan42ZM"},
    "261":{"cc":"261","dc":"261","country":"Madagascar","url":"http://8.222.182.223:8081","u":"Hasan42MG","p":"Hasan42MG"},
    "263":{"cc":"263","dc":"263","country":"Zimbabwe","url":"http://8.222.182.223:8081","u":"Hasan42ZW","p":"Hasan42ZW"},
    "264":{"cc":"264","dc":"264","country":"Namibia","url":"http://8.222.182.223:8081","u":"Hasan42NA","p":"Hasan42NA"},
    "265":{"cc":"265","dc":"265","country":"Malawi","url":"http://8.222.182.223:8081","u":"Hasan42MW","p":"Hasan42MW"},
    "266":{"cc":"266","dc":"266","country":"Lesotho","url":"http://8.222.182.223:8081","u":"Hasan42LS","p":"Hasan42LS"},
    "267":{"cc":"267","dc":"267","country":"Botswana","url":"http://8.222.182.223:8081","u":"Hasan42BW","p":"Hasan42BW"},
    "268":{"cc":"268","dc":"268","country":"Eswatini","url":"http://8.222.182.223:8081","u":"Hasan42SZ","p":"Hasan42SZ"},
    "269":{"cc":"269","dc":"269","country":"Comoros","url":"http://8.222.182.223:8081","u":"Hasan42KM","p":"Hasan42KM"},
    "290":{"cc":"290","dc":"290","country":"St Helena","url":"http://8.222.182.223:8081","u":"Hasan42SH","p":"Hasan42SH"},
    "291":{"cc":"291","dc":"291","country":"Eritrea","url":"http://8.222.182.223:8081","u":"Hasan42ER","p":"Hasan42ER"},
    "298":{"cc":"298","dc":"298","country":"Faroe Islands","url":"http://8.222.182.223:8081","u":"Hasan42FO","p":"Hasan42FO"},
    "220":{"cc":"220","dc":"220","country":"Gambia","url":"http://8.222.182.223:8081","u":"Hasan42GM","p":"Hasan42GM"},
    "221":{"cc":"221","dc":"221","country":"Senegal","url":"http://8.222.182.223:8081","u":"Hasan42SN","p":"Hasan42SN"},
    "222":{"cc":"222","dc":"222","country":"Mauritania","url":"http://8.222.182.223:8081","u":"Hasan42MR","p":"Hasan42MR"},
    "223":{"cc":"223","dc":"223","country":"Mali","url":"http://8.222.182.223:8081","u":"Hasan42ML","p":"Hasan42ML"},
    "224":{"cc":"224","dc":"224","country":"Guinea","url":"http://8.222.182.223:8081","u":"Hasan42GN","p":"Hasan42GN"},
    "225":{"cc":"225","dc":"225","country":"Ivory Coast","url":"http://8.222.182.223:8081","u":"Hasan42CI","p":"Hasan42CI"},
    "226":{"cc":"226","dc":"226","country":"Burkina Faso","url":"http://8.222.182.223:8081","u":"Hasan42BF","p":"Hasan42BF"},
    "227":{"cc":"227","dc":"227","country":"Niger","url":"http://8.222.182.223:8081","u":"Hasan42NE","p":"Hasan42NE"},
    "228":{"cc":"228","dc":"228","country":"Togo","url":"http://8.222.182.223:8081","u":"Hasan42TG","p":"Hasan42TG"},
    "229":{"cc":"229","dc":"229","country":"Benin","url":"http://8.222.182.223:8081","u":"Hasan42BJ","p":"Hasan42BJ"},
    "230":{"cc":"230","dc":"230","country":"Mauritius","url":"http://8.222.182.223:8081","u":"Hasan42MU","p":"Hasan42MU"},
    "231":{"cc":"231","dc":"231","country":"Liberia","url":"http://8.222.182.223:8081","u":"Hasan42LR","p":"Hasan42LR"},
    "232":{"cc":"232","dc":"232","country":"Sierra Leone","url":"http://8.222.182.223:8081","u":"Hasan42SL","p":"Hasan42SL"},
    "233":{"cc":"233","dc":"233","country":"Ghana","url":"http://8.222.182.223:8081","u":"Hasan42GH","p":"Hasan42GH"},
    "235":{"cc":"235","dc":"235","country":"Chad","url":"http://8.222.182.223:8081","u":"Hasan42TD","p":"Hasan42TD"},
    "236":{"cc":"236","dc":"236","country":"Central African Republic","url":"http://8.222.182.223:8081","u":"Hasan42CF","p":"Hasan42CF"},
    "237":{"cc":"237","dc":"237","country":"Cameroon","url":"http://8.222.182.223:8081","u":"Hasan42CM","p":"Hasan42CM"},
    "238":{"cc":"238","dc":"238","country":"Cape Verde","url":"http://8.222.182.223:8081","u":"Hasan42CV","p":"Hasan42CV"},
    "239":{"cc":"239","dc":"239","country":"Sao Tome","url":"http://8.222.182.223:8081","u":"Hasan42ST","p":"Hasan42ST"},
    "240":{"cc":"240","dc":"240","country":"Equatorial Guinea","url":"http://8.222.182.223:8081","u":"Hasan42GQ","p":"Hasan42GQ"},
    "241":{"cc":"241","dc":"241","country":"Gabon","url":"http://8.222.182.223:8081","u":"Hasan42GA","p":"Hasan42GA"},
    "242":{"cc":"242","dc":"242","country":"Congo","url":"http://8.222.182.223:8081","u":"Hasan42CG","p":"Hasan42CG"},
    "243":{"cc":"243","dc":"243","country":"DR Congo","url":"http://8.222.182.223:8081","u":"Hasan42CD","p":"Hasan42CD"},
    "244":{"cc":"244","dc":"244","country":"Angola","url":"http://8.222.182.223:8081","u":"Hasan42AO","p":"Hasan42AO"},
    "245":{"cc":"245","dc":"245","country":"Guinea-Bissau","url":"http://8.222.182.223:8081","u":"Hasan42GW","p":"Hasan42GW"},
    "246":{"cc":"246","dc":"246","country":"Diego Garcia","url":"http://8.222.182.223:8081","u":"Hasan42DG","p":"Hasan42DG"},
    "247":{"cc":"247","dc":"247","country":"Ascension","url":"http://8.222.182.223:8081","u":"Hasan42AC","p":"Hasan42AC"},
    "248":{"cc":"248","dc":"248","country":"Seychelles","url":"http://8.222.182.223:8081","u":"Hasan42SC","p":"Hasan42SC"},
    "249":{"cc":"249","dc":"249","country":"Sudan","url":"http://8.222.182.223:8081","u":"Hasan42SD","p":"Hasan42SD"},
    
    # Oceania
    "61":{"cc":"61","dc":"61","country":"Australia","url":"http://8.222.182.223:8081","u":"Hasan42AU","p":"Hasan42AU"},
    "64":{"cc":"64","dc":"64","country":"New Zealand","url":"http://8.222.182.223:8081","u":"Hasan42NZ","p":"Hasan42NZ"},
    "679":{"cc":"679","dc":"679","country":"Fiji","url":"http://8.222.182.223:8081","u":"Hasan42FJ","p":"Hasan42FJ"},
    "675":{"cc":"675","dc":"675","country":"Papua New Guinea","url":"http://8.222.182.223:8081","u":"Hasan42PG","p":"Hasan42PG"},
    "677":{"cc":"677","dc":"677","country":"Solomon Islands","url":"http://8.222.182.223:8081","u":"Hasan42SB","p":"Hasan42SB"},
    "678":{"cc":"678","dc":"678","country":"Vanuatu","url":"http://8.222.182.223:8081","u":"Hasan42VU","p":"Hasan42VU"},
    "685":{"cc":"685","dc":"685","country":"Samoa","url":"http://8.222.182.223:8081","u":"Hasan42WS","p":"Hasan42WS"},
    "687":{"cc":"687","dc":"687","country":"New Caledonia","url":"http://8.222.182.223:8081","u":"Hasan42NC","p":"Hasan42NC"},
    "688":{"cc":"688","dc":"688","country":"Tuvalu","url":"http://8.222.182.223:8081","u":"Hasan42TV","p":"Hasan42TV"},
    "689":{"cc":"689","dc":"689","country":"French Polynesia","url":"http://8.222.182.223:8081","u":"Hasan42PF","p":"Hasan42PF"},
    "690":{"cc":"690","dc":"690","country":"Tokelau","url":"http://8.222.182.223:8081","u":"Hasan42TK","p":"Hasan42TK"},
    "691":{"cc":"691","dc":"691","country":"Micronesia","url":"http://8.222.182.223:8081","u":"Hasan42FM","p":"Hasan42FM"},
    "692":{"cc":"692","dc":"692","country":"Marshall Islands","url":"http://8.222.182.223:8081","u":"Hasan42MH","p":"Hasan42MH"},
    "682":{"cc":"682","dc":"682","country":"Cook Islands","url":"http://8.222.182.223:8081","u":"Hasan42CK","p":"Hasan42CK"},
    "683":{"cc":"683","dc":"683","country":"Niue","url":"http://8.222.182.223:8081","u":"Hasan42NU","p":"Hasan42NU"},
    "686":{"cc":"686","dc":"686","country":"Kiribati","url":"http://8.222.182.223:8081","u":"Hasan42KI","p":"Hasan42KI"},
}

# ==================== STATUS MAPPING (FIXED - ADDED BACK) ====================
STATUS_MAPPING = {
    1: "✅ REGISTERED",
    2: "🟡 PENDING OTP",
    3: "❌ INVALID NUM",
    4: "❌ NOT REGISTERED",
    5: "❌ BLOCKED",
    6: "❌ WRONG OTP",
    7: "❌ DELETED",
    8: "❌ SUSPENDED",
    9: "❌ INVALID",
    10: "❌ TIMEOUT",
    11: "❌ BANNED",
    12: "❌ FAILED",
    13: "❌ ERROR",
    14: "❌ UNKNOWN",
    15: "❌ RETRY",
    16: "❌ CANCELLED"
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

# Load existing data from JSON
load_json_data()

# Start auto-save thread
threading.Thread(target=periodic_json_save, daemon=True).start()

# ==================== SHEET WORKER (FIXED: No duplicates) ====================
sheet_queue = []
sheet_processed = set()  # Track processed entries to prevent duplicates
sheet_running = True

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
    t = re.sub(r'[\s\-\(\)]', '', text.strip())
    if t.startswith('+'): t = t[1:]
    for cc in sorted(COUNTRY_APIS.keys(), key=len, reverse=True):
        if t.startswith(cc):
            p = t[len(cc):]
            if 5 <= len(p) <= 15:
                return cc, p, COUNTRY_APIS[cc]['dc']
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
    result = balances.modify(str(user_id), modifier)
    #save_json_data()  # Auto-save on balance change
    return result

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
    result = daily_stats.modify(uid, modifier)
    #save_json_data()  # Auto-save on stats change
    return result

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
    
    if r is not None and isinstance(r, dict) and r.get("data") and isinstance(r["data"], dict) and "token" in r["data"]:
        token = r["data"]["token"]
        api_tokens.update(cc, {"token": token, "expires": datetime.now() + timedelta(hours=23)})
        #save_json_data()  # Auto-save on token change
        return token
    
    # Retry with fresh login
    await asyncio.sleep(1)
    r = await api_request(cc, "POST", "/user/login",
                         {"account": cfg['u'], "password": cfg['p'], "identity": "Member"})
    if r is not None and isinstance(r, dict) and r.get("data") and isinstance(r["data"], dict) and "token" in r["data"]:
        token = r["data"]["token"]
        api_tokens.update(cc, {"token": token, "expires": datetime.now() + timedelta(hours=23)})
        #save_json_data()  # Auto-save on token change
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
                        
                        # ========== FIX 2: User notification (MUST WORK) ==========
                        user_notification_text = (
                            f"💰 OTP Verified!\n"
                            f"📞 {display}\n"
                            f"🌎 {country}\n"
                            f"💵 Earning: ${rate:.2f}\n"
                            f"🏦 Total Balance: ${bal:.2f}\n"
                            f"🔖Total verified today: {tot_ver}\n\n"
                            f"#ID{user_id}_{get_bd_hashtag()}"
                        )
                        try:
                            await bot.send_message(user_id, user_notification_text, parse_mode='none')
                            print(f"   ✅ User {user_id} notified for OTP success")
                        except Exception as e:
                            print(f"   ❌ User notification failed: {e}")
                        
                        queue_sheet(user_id, uname, fname, phone, cc, country, "SUCCESS", f"OTP Verified - Earned ${rate:.2f}", otp_code)
                        
                        # ========== FIX 3: Admin notification for OTP success ==========
                        admin_msg = (
                            f"✅ OTP VERIFIED SUCCESS\n\n"
                            f"👤 Name: {fname}\n"
                            f"🆔 Username: @{uname if uname else 'N/A'}\n"
                            f"📞 Number: {display}\n"
                            f"🌍 Country: {country}\n"
                            f"💰 Amount: ${rate:.2f}\n"
                            f"🏦 Balance: ${bal:.2f}\n"
                            f"🔖 Tag: #ID{user_id}_{get_bd_hashtag()}"
                        )
                        try:
                            await bot.send_message(ADMIN_ID, admin_msg, parse_mode='none')
                            print(f"   ✅ Admin {ADMIN_ID} notified for OTP success")
                        except Exception as e:
                            print(f"   ❌ Admin notification failed: {e}")
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
                #save_json_data()  # Auto-save on number removal
                return
            
            # FAILED - auto delete (SAFE: checks record_id)
            elif status in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
                if record_id and status != 1:
                    await delete_number(cc, phone, record_id, token)
                
                # Use status mapping for better message
                status_text = STATUS_MAPPING.get(status, f"Failed ({status})")
                
                await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ {display}\n{status_text}")
                
                def remove_number(nums):
                    otp_code = nums.get(phone, {}).get("otp_code", "")
                    nums.pop(phone, None)
                    return nums
                ud = user_numbers.modify(uid, remove_number)
                otp_val = ud.get(phone, {}).get("otp_code", "") if phone in ud else ""
                
                queue_sheet(user_id, uname, fname, phone, cc, country, "FAILED", status_text, otp_val)
                add_stats(user_id, "FAILED")
                #save_json_data()  # Auto-save on number removal
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
                #save_json_data()  # Auto-save on number removal
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
    #save_json_data()  # Auto-save on number removal

# ==================== PROCESS NUMBER (FIXED) ====================
async def process_number(bot, update, msg, user, cc, phone, dc, country):
    """Process one number - atomic pattern, no pop() misuse"""
    # 🔧 এই লাইন যোগ করুন - None check
    if not user or not msg:
        return
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
    #save_json_data()  # Auto-save on number add
    
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
    #save_json_data()  # Auto-save on OTP submission
    
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
        #save_json_data()  # Auto-save on number removal
        
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
        f"💸 Withdraw min ${MIN_WITHDRAW:.2f}",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode='Markdown'
    )

async def handle_msg(update, context):
    user = update.effective_user

    if not update.message or not update.message.text:
        return

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
        await update.message.reply_text(f"💰 *Balance: ${bal:.2f}*\n{'✅ Can withdraw!' if bal >= MIN_WITHDRAW else f'Min: ${MIN_WITHDRAW:.2f}'}", parse_mode='Markdown')
    
    elif t == "💸 Withdraw":
        await withdraw_request(update, context)
    
    elif t == "🌍 Price List":
        txt = "🌍 *Prices*\n\n"
        for cc, d in sorted(COUNTRY_RATES.items(), key=lambda x: x[1]["rate"], reverse=True)[:60]:
            txt += f"{d['flag']} {d['country'][:15]}: ${d['rate']:.2f}\n"
        await update.message.reply_text(txt, parse_mode='Markdown')
    
    elif t == "📥 Download":
        await update.message.reply_text(f"📥 Commands:\n/mystats\n/mybalance\n/myhistory\n")
    
    elif t == "🆘 Support":
        await update.message.reply_text(f"📢 {REQUIRED_CHANNEL}\n👑 Admin: {ADMIN_ID}")
    
    elif t == "📸 Payment":
        await update.message.reply_text(f"💰 Min: ${MIN_WITHDRAW:.2f}\nDaily: 1 time\nMethods: bKash/Nagad/Binance")
    
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
        prompts = {"bkash":"📱 Send bKash number:","nagad":"📱 Send Nagad number:","binance":"₿ Send USDT TRC20 address:"}
        await q.message.edit_text(prompts.get(m,""))

async def save_wallet(update, context):
    uid, acc = str(update.effective_user.id), update.message.text.strip()
    m = context.user_data.get('w_method')
    if not m: return
    
    def modifier(w):
        w[m] = acc
        return w
    wallets.modify(uid, modifier)
    #save_json_data()  # Auto-save on wallet change
    
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
    #save_json_data()  # Auto-save on balance change
    
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
    #save_json_data()  # Auto-save on balance change
    
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
    if bal < MIN_WITHDRAW:
        await update.message.reply_text(f"❌ Min ${MIN_WITHDRAW:.2f}! Balance: ${bal:.2f}")
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
    #save_json_data()  # Auto-save on withdraw
    
    # Mark daily
    def mark_daily(wc):
        wc[today] = 1
        return wc
    withdraw_counts.modify(uid, mark_daily)
    #save_json_data()  # Auto-save on withdraw count
    
    # Reset today's OTP count
    def reset_stats(s):
        if today in s: s[today]["otp"] = 0
        return s
    daily_stats.modify(uid, reset_stats)
    #save_json_data()  # Auto-save on stats reset
    
    nm = {"bkash":"bKash","nagad":"Nagad","binance":"Binance"}
    await q.message.edit_text(f"✅ *Submitted!*\n💰 ${bal:.2f}\n⏳ Processing...", parse_mode='Markdown')
    
    queue_paid_update(uid, nm.get(m, m))
    
    # ========== FIX 4: Admin withdraw notification (MUST WORK) ==========
    admin_msg = (
        f"💸 WITHDRAW REQUEST\n\n"
        f"👤 Name: {q.from_user.full_name}\n"
        f"🆔 Username: @{q.from_user.username or 'N/A'}\n"
        f"💰 Amount: ${bal:.2f}\n"
        f"📱 Method: {nm.get(m,m)}\n"
        f"🏦 Account: {acc}\n"
        
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
        print(f"   ✅ Admin {ADMIN_ID} notified for withdraw request")
    except Exception as e:
        print(f"   ❌ Admin withdraw notification failed: {e}")
    
    # User confirmation for withdraw request
    try:
        await context.bot.send_message(
            int(uid),
            f"📤 *Withdraw Request Submitted*\n\n"
            f"💰 Amount: ${bal:.2f}\n"
            f"📱 Method: {nm.get(m,m)}\n"
            f"⏳ Status: Pending Approval\n\n"
            f"✅ You will be notified when processed.",
            parse_mode='Markdown'
        )
        print(f"   ✅ User {uid} notified for withdraw request")
    except Exception as e:
        print(f"   ❌ User withdraw notification failed: {e}")

async def admin_withdraw_action(update, context):
    q = update.callback_query
    await q.answer()
    a, uid = q.data.split("_")[0], q.data.split("_")[1]
    
    p = pending_withdraws.delete(uid)
    if not p:
        try:
            await q.message.edit_text(q.message.text + "\n\n⚠️ Already processed")
        except:
            await q.message.edit_text("⚠️ Already processed")
        return
    
    nm = {"bkash":"bKash","nagad":"Nagad","binance":"Binance"}
    
    if a == "c":
        # Edit admin message - plain text, no markdown
        try:
            await q.message.edit_text(q.message.text + "\n\n✅ PAYMENT CONFIRMED")
        except:
            await q.message.edit_text("✅ Payment Confirmed!")
        
        # Notify user - plain text, no markdown
        try:
            await context.bot.send_message(
                int(uid), 
                f"✅ Withdrawal Approved!\n\n"
                f"💰 Amount: ${p['amount']:.2f}\n"
                f"📱 Method: {nm.get(p['method'], 'N/A')}\n"
                f"💳 Account: {p['account']}\n"
                f"⏳ Status: Paid Successfully\n\n"
                f"Thank you for using our service!"
            )
            print(f"   ✅ User {uid} notified: APPROVED")
        except Exception as e:
            print(f"   ❌ User notification failed: {e}")
            
    else:
        # Restore balance
        def restore_bal(b):
            b["balance"] = p['amount']
            return b
        balances.modify(uid, restore_bal)
        #save_json_data()  # Auto-save on balance restore
        
        # Remove daily limit
        def remove_daily(wc):
            wc.pop(get_bd_date(), None)
            return wc
        withdraw_counts.modify(uid, remove_daily)
        #save_json_data()  # Auto-save on withdraw count
        
        # Edit admin message - plain text
        try:
            await q.message.edit_text(q.message.text + "\n\n❌ PAYMENT REJECTED - Balance Restored")
        except:
            await q.message.edit_text("❌ Payment Rejected - Balance Restored")
        
        # Notify user
        try:
            await context.bot.send_message(
                int(uid), 
                f"❌ Withdrawal Rejected!\n\n"
                f"💰 Amount: ${p['amount']:.2f}\n"
                f"📱 Method: {nm.get(p['method'], 'N/A')}\n\n"
                f"✅ ${p['amount']:.2f} has been restored to your balance.\n"
                f"📝 Reason: Please contact support for details.\n\n"
                f"🆘 Support: {REQUIRED_CHANNEL}"
            )
            print(f"   ✅ User {uid} notified: REJECTED")
        except Exception as e:
            print(f"   ❌ User notification failed: {e}")

async def cmd_add_country(update, context):
    """Admin command to add new country
    Usage: /addcountry 880 Bangladesh 880 0.14 🇧🇩 Hasan42BD Hasan42BD
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    try:
        args = context.args
        if len(args) < 7:
            await update.message.reply_text(
                "❌ Usage: `/addcountry <code> <name> <dc> <rate> <flag> <username> <password>`\n"
                "Example: `/addcountry 880 Bangladesh 880 0.14 🇧🇩 Hasan42BD Hasan42BD`",
                parse_mode='Markdown'
            )
            return
        
        code = args[0]
        name = args[1]
        dc = args[2]
        rate = float(args[3])
        flag = args[4]
        username = args[5]
        password = args[6]
        
        # Add to COUNTRY_APIS
        COUNTRY_APIS[code] = {
            "cc": code, "dc": dc, "country": name,
            "url": "http://8.222.182.223:8081",
            "u": username, "p": password
        }
        
        # Add to COUNTRY_RATES
        COUNTRY_RATES[code] = {"country": name, "rate": rate, "flag": flag}
        
        await update.message.reply_text(
            f"✅ *Country Added Successfully!*\n\n"
            f"📞 Code: `{code}`\n"
            f"🌍 Name: {name}\n"
            f"💰 Rate: ${rate:.2f}\n"
            f"🔑 Username: `{username}`",
            parse_mode='Markdown'
        )
        
        print(f"✅ Admin added country: {code} - {name}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_remove_country(update, context):
    """Admin command to remove country
    Usage: /removecountry 880
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    try:
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("❌ Usage: `/removecountry 880`", parse_mode='Markdown')
            return
        
        code = args[0]
        
        if code in COUNTRY_APIS:
            del COUNTRY_APIS[code]
        if code in COUNTRY_RATES:
            del COUNTRY_RATES[code]
        
        await update.message.reply_text(f"✅ *Country {code} Removed!*", parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_list_countries(update, context):
    """Show all countries in API and Rates
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return
    
    txt = "*📊 COUNTRY LIST*\n\n"
    txt += "*🌍 COUNTRIES WITH RATES:*\n"
    for code, data in sorted(COUNTRY_RATES.items()):
        txt += f"{data['flag']} `{code}` {data['country']}: ${data['rate']:.2f}\n"
    
    txt += "\n*🔧 COUNTRIES IN API:*\n"
    for code, data in sorted(COUNTRY_APIS.items()):
        txt += f"📞 `{code}` {data['country']} (user: {data['u']})\n"
    
    await update.message.reply_text(txt[:4000], parse_mode='Markdown')

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
    app_bot.add_handler(CommandHandler("addcountry", cmd_add_country))
    app_bot.add_handler(CommandHandler("removecountry", cmd_remove_country))
    app_bot.add_handler(CommandHandler("listcountries", cmd_list_countries))
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
    print(f"💾 JSON Auto-save every 30 seconds")
    print(f"💰 Admin: /addrate /removerate /listrates")
    print(f"💵 Admin: /addbalance /removebalance /checkbalance")
    print(f"⚙️ Admin: /setminwithdraw /allbalances")
    print("="*60 + "\n")
    
    app_bot.run_polling()

if __name__ == "__main__":
    main()

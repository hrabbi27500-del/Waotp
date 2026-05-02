# ==================== WHATSAPP REGISTRATION BOT - FINAL WITH CONCURRENT FIX ====================
import os
import asyncio
import re
import json
import aiohttp
import requests
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import threading
import time
from collections import defaultdict
from queue import Queue

print("="*60)
print("🚀 WHATSAPP REGISTRATION BOT - FINAL")
print("="*60)

import os
from dotenv import load_dotenv

# ==================== LOAD ENVIRONMENT VARIABLES ====================
load_dotenv()

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5624278091"))
GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "")
PORT = int(os.environ.get("PORT", 10000))

print(f"📱 Bot Token: ✅")
print(f"👑 Admin ID: {ADMIN_ID}")

# ==================== THREAD-SAFE LOCKS ====================
api_lock = threading.Lock()
active_numbers_lock = threading.Lock()
balance_lock = threading.Lock()
stats_lock = threading.Lock()

# ==================== CONCURRENT PROCESSING QUEUES ====================
processing_queue = asyncio.Queue()  # Main processing queue
otp_processing_queue = asyncio.Queue()  # OTP processing queue

# Track active limits per user
user_active_requests = defaultdict(int)  # {user_id: active_count}
USER_MAX_CONCURRENT = 3  # Max concurrent requests per user
GLOBAL_MAX_CONCURRENT = 10  # Global max concurrent API calls

# Semaphore for rate limiting
api_semaphore = asyncio.Semaphore(GLOBAL_MAX_CONCURRENT)

# Track API last call time per CC
api_last_call = {}  # {cc: datetime}
API_MIN_INTERVAL = 0.5  # Min seconds between API calls per CC

# ==================== COUNTRY EARNING RATES ====================
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
    "11": {"cc": "11", "display_cc": "1", "country": "Canada", "base_url": "http://8.222.182.223:8081", "username": "HasanCAA", "password": "HasanCAA"},
    "52": {"cc": "52", "display_cc": "52", "country": "Mexico", "base_url": "http://8.222.182.223:8081", "username": "Hasan42MX", "password": "Hasan42MX"},
    "44": {"cc": "44", "display_cc": "44", "country": "UK", "base_url": "http://8.222.182.223:8081", "username": "Hasan42GB", "password": "Hasan42GB"},
    "49": {"cc": "49", "display_cc": "49", "country": "Germany", "base_url": "http://8.222.182.223:8081", "username": "Hasan42DE", "password": "Hasan42DE"},
    "33": {"cc": "33", "display_cc": "33", "country": "France", "base_url": "http://8.222.182.223:8081", "username": "Hasan42FR", "password": "Hasan42FR"},
    "7": {"cc": "7", "display_cc": "7", "country": "Russia", "base_url": "http://8.222.182.223:8081", "username": "Hasan42RU", "password": "Hasan42RU"},
    "880": {"cc": "880", "display_cc": "880", "country": "Bangladesh", "base_url": "http://8.222.182.223:8081", "username": "Hasan42BD", "password": "Hasan42BD"},
    "92": {"cc": "92", "display_cc": "92", "country": "Pakistan", "base_url": "http://8.222.182.223:8081", "username": "Hasan42PK", "password": "Hasan42PK"},
    "977": {"cc": "977", "display_cc": "977", "country": "Nepal", "base_url": "http://8.222.182.223:8081", "username": "Hasan42NP", "password": "Hasan42NP"},
    "60": {"cc": "60", "display_cc": "60", "country": "Malaysia", "base_url": "http://8.222.182.223:8081", "username": "Hasan42MY", "password": "Hasan42MY"},
    "62": {"cc": "62", "display_cc": "62", "country": "Indonesia", "base_url": "http://8.222.182.223:8081", "username": "Hasan42ID", "password": "Hasan42ID"},
    "84": {"cc": "84", "display_cc": "84", "country": "Vietnam", "base_url": "http://8.222.182.223:8081", "username": "Hasan42VN", "password": "Hasan42VN"},
    "886": {"cc": "886", "display_cc": "886", "country": "Taiwan", "base_url": "http://8.222.182.223:8081", "username": "Hasan42TW", "password": "Hasan42TW"},
    "852": {"cc": "852", "display_cc": "852", "country": "Hong Kong", "base_url": "http://8.222.182.223:8081", "username": "Hasan42HK", "password": "Hasan42HK"},
    "964": {"cc": "964", "display_cc": "964", "country": "Iraq", "base_url": "http://8.222.182.223:8081", "username": "JahidIQ", "password": "JahidIQ"},
    "966": {"cc": "966", "display_cc": "966", "country": "Saudi Arabia", "base_url": "http://8.222.182.223:8081", "username": "Hasan42SA", "password": "Hasan42SA"},
    "968": {"cc": "968", "display_cc": "968", "country": "Oman", "base_url": "http://8.222.182.223:8081", "username": "Hasan42OM", "password": "Hasan42OM"},
    "20": {"cc": "20", "display_cc": "20", "country": "Egypt", "base_url": "http://8.222.182.223:8081", "username": "Hasan42EG", "password": "Hasan42EG"},
    "27": {"cc": "27", "display_cc": "27", "country": "South Africa", "base_url": "http://8.222.182.223:8081", "username": "Hasan42ZA", "password": "Hasan42ZA"},
    "234": {"cc": "234", "display_cc": "234", "country": "Nigeria", "base_url": "http://8.222.182.223:8081", "username": "Hasan42NG", "password": "Hasan42NG"},
    "212": {"cc": "212", "display_cc": "212", "country": "Morocco", "base_url": "http://8.222.182.223:8081", "username": "Hasan42MA", "password": "Hasan42MA"},
    "55": {"cc": "55", "display_cc": "55", "country": "Brazil", "base_url": "http://8.222.182.223:8081", "username": "Hasan42BR", "password": "Hasan42BR"},
    "58": {"cc": "58", "display_cc": "58", "country": "Venezuela", "base_url": "http://8.222.182.223:8081", "username": "JahidVN", "password": "JahidVN"},
    "258": {"cc": "258", "display_cc": "258", "country": "Mozambique", "base_url": "http://8.222.182.223:8081", "username": "HasanMZ", "password": "HasanMZ"},
}

REQUIRED_CHANNEL = "@CashxByte"
bd_tz = pytz.timezone('Asia/Dhaka')

# ==================== DATA STORAGE ====================
active_numbers = {}
api_tokens = {}
daily_stats = {}
user_balances = {}
user_earnings_history = {}
last_reset_date = None

# New storage for wallet & withdraw
user_wallets = {}
withdraw_history = {}
daily_withdraw_count = {}
pending_withdraws = {}

# ==================== SHEET SAVE QUEUE ====================
sheet_queue = []
sheet_thread_running = True

async def keep_alive_enhanced():
    urls_to_ping = [
        "https://waotp-4v3w.onrender.com",
        "https://wschecker-wb1b.onrender.com"
    ]
    
    while True:
        for url in urls_to_ping:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.get(url, timeout=10)
            except:
                pass
            await asyncio.sleep(2)
        await asyncio.sleep(180)

def sheet_worker():
    while sheet_thread_running:
        try:
            if sheet_queue:
                payload = sheet_queue.pop(0)
                try:
                    response = requests.post(GOOGLE_SHEET_URL, json=payload, timeout=30)
                    if response.status_code == 200:
                        print(f"   ✅ Sheet saved: {payload.get('status', payload.get('type', 'N/A'))}")
                    else:
                        if payload.get('retry', 0) < 3:
                            payload['retry'] = payload.get('retry', 0) + 1
                            sheet_queue.append(payload)
                except:
                    if payload.get('retry', 0) < 3:
                        payload['retry'] = payload.get('retry', 0) + 1
                        sheet_queue.append(payload)
            time.sleep(0.5)
        except:
            time.sleep(1)

threading.Thread(target=sheet_worker, daemon=True).start()

def save_to_sheet(user_id, username, full_name, phone, cc, country, status, api_status, otp_code=None):
    final_statuses = ["SUCCESS", "FAILED", "OTP_FAILED"]
    if status not in final_statuses:
        return True
    
    payload = {
        "user_id": str(user_id),
        "username": username or "N/A",
        "full_name": full_name or "Unknown",
        "phone": phone,
        "cc": cc,
        "country": country,
        "status": status,
        "api_status": api_status,
        "otp": otp_code or "",
        "retry": 0
    }
    sheet_queue.append(payload)
    return True

def save_rate_to_sheet():
    rates_data = []
    for cc, data in COUNTRY_RATES.items():
        rates_data.append({
            "cc": cc,
            "country": data["country"],
            "rate": data["rate"],
            "flag": data["flag"],
            "timestamp": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    payload = {
        "type": "rates_update",
        "data": rates_data,
        "timestamp": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')
    }
    sheet_queue.append(payload)

def update_daily_stats(user_id, status, cc=None):
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    user_id_str = str(user_id)
    
    with stats_lock:
        if user_id_str not in daily_stats:
            daily_stats[user_id_str] = {}
        if today not in daily_stats[user_id_str]:
            daily_stats[user_id_str][today] = {"total": 0, "success": 0, "failed": 0, "otp_verified": 0}
        
        daily_stats[user_id_str][today]["total"] += 1
        if status == "SUCCESS":
            daily_stats[user_id_str][today]["success"] += 1
        elif status == "OTP_VERIFIED":
            daily_stats[user_id_str][today]["otp_verified"] += 1
        else:
            daily_stats[user_id_str][today]["failed"] += 1

def add_earning_to_balance(user_id, cc, amount):
    user_id_str = str(user_id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    
    with balance_lock:
        if user_id_str not in user_balances:
            user_balances[user_id_str] = {"balance": 0, "history": []}
        
        if "last_reset" not in user_balances[user_id_str]:
            user_balances[user_id_str]["last_reset"] = today
        
        user_balances[user_id_str]["balance"] += amount
        
        user_balances[user_id_str]["history"].append({
            "date": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S'),
            "cc": cc,
            "amount": amount,
            "type": "OTP_VERIFIED"
        })
        
        return user_balances[user_id_str]["balance"]

def check_and_reset_daily():
    # DAILY RESET IS NOW OFF
    return False

# ==================== RATE LIMITER FOR API ====================
async def rate_limit_api(cc):
    """Ensure minimum interval between API calls per country code"""
    now = datetime.now()
    if cc in api_last_call:
        elapsed = (now - api_last_call[cc]).total_seconds()
        if elapsed < API_MIN_INTERVAL:
            await asyncio.sleep(API_MIN_INTERVAL - elapsed)
    api_last_call[cc] = datetime.now()

# ==================== MAIN PROCESSING WORKER ====================
async def processing_worker():
    """Background worker that processes one number at a time per user"""
    while True:
        task = await processing_queue.get()
        try:
            update, context, user, api_cc, phone, display_cc, country, display_phone, msg = task
            user_id_str = str(user.id)
            
            # Wait if user has too many active requests
            while user_active_requests[user_id_str] >= USER_MAX_CONCURRENT:
                await asyncio.sleep(0.1)
            
            user_active_requests[user_id_str] += 1
            
            try:
                await process_single_number(update, context, user, api_cc, phone, display_cc, country, display_phone, msg)
            finally:
                user_active_requests[user_id_str] -= 1
                
            processing_queue.task_done()
            
        except Exception as e:
            print(f"   ⚠️ Worker error: {e}")
            processing_queue.task_done()

async def process_single_number(update, context, user, api_cc, phone, display_cc, country, display_phone, msg):
    """Process a single number with rate limiting"""
    
    # Rate limit per CC
    await rate_limit_api(api_cc)
    
    token = await login_api(api_cc)
    if not token:
        await msg.edit_text(f"❌ {display_phone}\nContact Admin")
        save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", "Login failed")
        return
    
    config = COUNTRY_APIS.get(api_cc)
    
    # Use semaphore for global rate limiting
    async with api_semaphore:
        try:
            # Check existing status
            async with aiohttp.ClientSession() as session:
                headers = {"Admin-Token": token}
                check_url = f"{config['base_url']}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
                
                await rate_limit_api(api_cc)
                async with session.get(check_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and "data" in data and "records" in data["data"] and data["data"]["records"]:
                            record = data["data"]["records"][0]
                            status_code = record.get("registrationStatus")
                            
                            if status_code == 1:
                                await msg.edit_text(f"✅ {display_phone} 🟢 ALREADY REGISTERED")
                                save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "SUCCESS", "Already Registered", None)
                                update_daily_stats(user.id, "SUCCESS")
                                return
                            
                            if status_code == 4:
                                await msg.edit_text(f"❌ {display_phone}\nAlready checked - Not Registered")
                                save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", "Already Not Registered", None)
                                update_daily_stats(user.id, "FAILED")
                                return
        except:
            pass
        
        # Add number
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Admin-Token": token}
                add_url = f"{config['base_url']}/z-number-base/addNum?cc={api_cc}&phoneNum={phone}&smsStatus=2"
                
                await rate_limit_api(api_cc)
                async with session.post(add_url, headers=headers, timeout=10) as response:
                    if response.status == 409:
                        # Already exists, check status
                        await rate_limit_api(api_cc)
                        async with session.get(check_url, headers=headers, timeout=10) as status_resp:
                            if status_resp.status == 200:
                                status_data = await status_resp.json()
                                if status_data and "data" in status_data and "records" in status_data["data"] and status_data["data"]["records"]:
                                    record = status_data["data"]["records"][0]
                                    current_status = record.get("registrationStatus")
                                    
                                    if current_status == 1:
                                        await msg.edit_text(f"✅ {display_phone} 🟢 ALREADY REGISTERED")
                                        save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "SUCCESS", "Already Registered", None)
                                        update_daily_stats(user.id, "SUCCESS")
                                        return
                                    elif current_status == 2:
                                        pass
                                    else:
                                        await msg.edit_text(f"❌ {display_phone}\nStatus: {current_status}")
                                        save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", f"Status {current_status}", None)
                                        update_daily_stats(user.id, "FAILED")
                                        return
                    elif response.status != 200:
                        await msg.edit_text(f"❌ {display_phone}\nAdd failed")
                        save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", f"Error {response.status}")
                        return
        except Exception as e:
            print(f"   ⚠️ Add error: {display_phone}: {e}")
            await msg.edit_text(f"❌ {display_phone}\nError adding")
            return
        
        # Wait and check initial status
        await asyncio.sleep(3)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Admin-Token": token}
                url = f"{config['base_url']}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
                
                await rate_limit_api(api_cc)
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and "data" in data and "records" in data["data"] and data["data"]["records"]:
                            record = data["data"]["records"][0]
                            status_code = record.get("registrationStatus")
                            
                            if status_code == 1:
                                await msg.edit_text(f"✅ {display_phone} 🟢 SUCCESS")
                                save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "SUCCESS", "Verified", None)
                                update_daily_stats(user.id, "SUCCESS")
                                return
                            
                            if status_code == 4:
                                await msg.edit_text(f"❌ {display_phone}\nNot Registered")
                                save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", "Not Registered", None)
                                update_daily_stats(user.id, "FAILED")
                                return
        except:
            pass
        
        # Start tracking
        with active_numbers_lock:
            # Remove old entries for this user
            for p in list(active_numbers.keys()):
                if active_numbers[p].get('user_id') == user.id:
                    old_entry = active_numbers[p]
                    if (datetime.now() - old_entry.get('start_time', datetime.now() - timedelta(hours=1))).total_seconds() > 600:
                        del active_numbers[p]
            
            active_numbers[phone] = {
                'user_id': user.id,
                'api_cc': api_cc,
                'display_cc': display_cc,
                'phone': phone,
                'username': user.username,
                'full_name': user.full_name,
                'country': country,
                'message_id': msg.message_id,
                'chat_id': update.message.chat_id if update.message else user.id,
                'token': token,
                'otp_submitted': False,
                'otp_code': None,
                'start_time': datetime.now()
            }
        
        await msg.edit_text(f"🟡 {display_phone} IN PROGRESS")
        
        asyncio.create_task(track_number_status(
            context, update.message.chat_id if update.message else user.id, msg.message_id,
            phone, api_cc, display_cc, user.id, user.username, user.full_name, country, token
        ))

# ==================== TRACKING FUNCTION (OPTIMIZED) ====================
async def track_number_status(context, chat_id, message_id, phone, api_cc, display_cc, user_id, username, full_name, country, token):
    display = f"+{display_cc} {phone}"
    start_time = datetime.now()
    max_duration = 180
    check_interval = 2  # Increased from 1 to reduce API calls
    
    config = COUNTRY_APIS.get(api_cc)
    check_count = 0
    last_status = None
    stuck_start_time = None
    last_update_time = 0
    
    auto_delete_statuses = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    
    while True:
        elapsed = (datetime.now() - start_time).total_seconds()
        remaining = max_duration - elapsed
        current_time = int(elapsed)
        
        # Update display every 5 seconds to reduce API calls
        if current_time > last_update_time and current_time % 5 == 0:
            last_update_time = current_time
            try:
                if last_status == 2 or last_status is None:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"🟡 {display} IN PROGRESS\n⏳ {int(remaining/60)}m {int(remaining%60)}s left"
                    )
            except:
                pass
        
        if elapsed >= max_duration:
            print(f"   ⏰ TIMEOUT: {display} (Status: {last_status})")
            
            if last_status == 2:
                await delete_number_from_api(api_cc, phone, token, 2)
            
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"⏰ {display} Timeout"
                )
            except:
                pass
            
            with active_numbers_lock:
                if phone in active_numbers:
                    del active_numbers[phone]
            break
        
        # Rate limit check
        await rate_limit_api(api_cc)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Admin-Token": token}
                url = f"{config['base_url']}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and "data" in data and "records" in data["data"] and data["data"]["records"]:
                            record = data["data"]["records"][0]
                            status_code = record.get("registrationStatus")
                            
                            if status_code == 1:
                                status_text = "✅ SUCCESS"
                            elif status_code == 2:
                                status_text = "🟡 IN PROGRESS"
                            elif status_code == 4:
                                status_text = "❌ NOT REGISTERED"
                            elif status_code == 6:
                                status_text = "🔴 WRONG OTP"
                            else:
                                status_text = f"❌ {status_code}"
                            
                            if status_code != last_status:
                                check_count += 1
                                print(f"   🔍 #{check_count}: {display} → {status_text}")
                                last_status = status_code
                            
                            # SUCCESS
                            if status_code == 1:
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    text=f"✅ {display} 🟢 SUCCESS"
                                )
                                
                                is_otp = False
                                otp_code = None
                                with active_numbers_lock:
                                    if phone in active_numbers:
                                        is_otp = active_numbers[phone].get('otp_submitted', False)
                                        otp_code = active_numbers[phone].get('otp_code')
                                
                                if is_otp and otp_code:
                                    rate = COUNTRY_RATES.get(api_cc, {}).get("rate", 0)
                                    if rate > 0:
                                        new_balance = add_earning_to_balance(user_id, api_cc, rate)
                                        save_msg = f"OTP Verified - Earned ${rate:.2f}"
                                        update_daily_stats(user_id, "OTP_VERIFIED", api_cc)
                                        
                                        try:
                                            await context.bot.send_message(
                                                chat_id=user_id,
                                                text=f"💰 OTP Verified!\n📞 {display}\n🌎 {country}\n💵 Earning: ${rate:.2f}\n🏦 Total Balance: ${new_balance:.2f}"
                                            )
                                        except:
                                            pass
                                    else:
                                        save_msg = "OTP Verified (No rate set)"
                                        update_daily_stats(user_id, "OTP_VERIFIED", api_cc)
                                else:
                                    save_msg = "Verified (No OTP)"
                                    update_daily_stats(user_id, "SUCCESS")
                                
                                save_to_sheet(user_id, username, full_name, phone, api_cc, country, "SUCCESS", save_msg, otp_code)
                                
                                with active_numbers_lock:
                                    if phone in active_numbers:
                                        del active_numbers[phone]
                                return
                            
                            # Auto-delete statuses
                            elif status_code in auto_delete_statuses:
                                await delete_number_from_api(api_cc, phone, token, status_code)
                                
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    text=f"❌ {display}\n{status_text}"
                                )
                                
                                if status_code == 4:
                                    save_msg = "Not Registered"
                                elif status_code == 6:
                                    save_msg = "Wrong OTP"
                                else:
                                    save_msg = status_text
                                
                                otp_val = None
                                with active_numbers_lock:
                                    if phone in active_numbers:
                                        otp_val = active_numbers[phone].get('otp_code')
                                        del active_numbers[phone]
                                
                                save_to_sheet(user_id, username, full_name, phone, api_cc, country, "FAILED", save_msg, otp_val)
                                update_daily_stats(user_id, "FAILED")
                                return
        
        except Exception as e:
            print(f"   ⚠️ Tracking error: {display}: {e}")
        
        await asyncio.sleep(check_interval)

# ==================== API FUNCTIONS ====================
async def login_api(cc):
    if cc in api_tokens and api_tokens[cc].get('expires_at', datetime.now()) > datetime.now():
        return api_tokens[cc]['token']
    
    config = COUNTRY_APIS.get(cc)
    if not config:
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"account": config['username'], "password": config['password'], "identity": "Member"}
            async with session.post(f"{config['base_url']}/user/login", json=payload, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and "data" in data and "token" in data["data"]:
                        token = data["data"]["token"]
                        with api_lock:
                            api_tokens[cc] = {
                                'token': token,
                                'expires_at': datetime.now() + timedelta(hours=23)
                            }
                        return token
        return None
    except:
        return None

async def delete_number_from_api(cc, phone, token, status_code):
    if status_code == 1:
        return False
    
    config = COUNTRY_APIS.get(cc)
    if not config:
        return False
    
    try:
        await rate_limit_api(cc)
        async with aiohttp.ClientSession() as session:
            headers = {"Admin-Token": token}
            url = f"{config['base_url']}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and "data" in data and "records" in data["data"] and data["data"]["records"]:
                        record = data["data"]["records"][0]
                        record_id = record.get("id")
                        current_status = record.get("registrationStatus")
                        
                        if current_status == 1:
                            return False
                        
                        if record_id and record_id > 0:
                            await rate_limit_api(cc)
                            delete_url = f"{config['base_url']}/z-number-base/deleteNum/{record_id}"
                            async with session.delete(delete_url, headers=headers, timeout=10) as del_response:
                                if del_response.status == 200:
                                    return True
        return False
    except:
        return False

# ==================== TELEGRAM HANDLERS ====================
def extract_number(text):
    cleaned = re.sub(r'[\s\-\(\)]', '', text.strip())
    
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    country_codes = sorted(COUNTRY_APIS.keys(), key=len, reverse=True)
    
    for cc in country_codes:
        if cleaned.startswith(cc):
            phone = cleaned[len(cc):]
            if 5 <= len(phone) <= 15:
                return cc, phone, COUNTRY_APIS[cc]['display_cc']
    
    if cleaned.startswith('1') and len(cleaned) == 11:
        return "11", cleaned[1:], "1"
    
    if cleaned.startswith('964') and len(cleaned) >= 13:
        return "964", cleaned[3:], "964"
    
    if cleaned.startswith('880') and len(cleaned) >= 13:
        return "880", cleaned[3:], "880"
    
    return None, None, None

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/CashxByte")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"🔒 Please join {REQUIRED_CHANNEL} first!", reply_markup=reply_markup)
            return
    except:
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/CashxByte")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"🔒 Please join {REQUIRED_CHANNEL} first!", reply_markup=reply_markup)
        return
    
    keyboard = [
        ["📊 Statistics", "💰 Check Balance", "💸 Withdraw"],
        ["🌍 Price List", "📥 Download Data"],
        ["🆘 Support", "📸 Payment Proof", "👛 My Wallet"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    countries_list = []
    for cc, cfg in list(COUNTRY_APIS.items())[:20]:
        if cc in COUNTRY_RATES:
            rate = COUNTRY_RATES[cc]["rate"]
            countries_list.append(f"• {COUNTRY_RATES[cc]['flag']} +{cfg['display_cc']} - {cfg['country']} (${rate:.2f})")
        else:
            countries_list.append(f"• +{cfg['display_cc']} - {cfg['country']}")
    
    countries_text = "\n".join(countries_list)
    
    welcome_msg = (
        f"👋 Welcome {user.first_name}!\n\n"
        f"🌍 *WhatsApp Registration Bot*\n\n"
        f"📱 Send any phone number with country code:\n\n"
        f"{countries_text}\n\n"
        f"💡 Examples:\n"
        f"• `+9647803260789` (Iraq)\n"
        f"• `+8801712345678` (Bangladesh)\n\n"
        f"⚡ Auto-detects country\n"
        f"⏱️ Max 3 minutes tracking\n"
        f"💰 Earnings only for OTP verification!\n\n"
        f"📅 *No daily reset - Balance accumulates*"
    )
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)

# ==================== ADD THESE BEFORE main() FUNCTION ====================

async def add_rate(update: Update, context: CallbackContext):
    """Admin command to add/update country rate"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 *Usage:* `/addrate cc amount`\n\n"
            "Example:\n"
            "• `/addrate 880 0.15` - Set Bangladesh rate to $0.15\n"
            "• `/addrate 966 0.45` - Set Saudi Arabia rate to $0.45",
            parse_mode='Markdown'
        )
        return
    
    cc = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount! Use number like 0.15")
        return
    
    if cc in COUNTRY_APIS:
        country_name = COUNTRY_APIS[cc]["country"]
        
        if cc in COUNTRY_RATES:
            COUNTRY_RATES[cc]["rate"] = amount
            await update.message.reply_text(
                f"✅ Rate updated!\n\n"
                f"🇨🇨 {country_name}\n"
                f"💰 New rate: ${amount:.2f} per OTP"
            )
        else:
            COUNTRY_RATES[cc] = {
                "country": country_name,
                "rate": amount,
                "flag": "🌍",
                "cc": cc
            }
            await update.message.reply_text(
                f"✅ New country added!\n\n"
                f"🇨🇨 {country_name}\n"
                f"💰 Rate: ${amount:.2f} per OTP"
            )
        
        save_rate_to_sheet()
    else:
        await update.message.reply_text(f"❌ Country code `{cc}` not found in API list!", parse_mode='Markdown')

async def remove_rate(update: Update, context: CallbackContext):
    """Admin command to remove country rate"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 *Usage:* `/removerate cc`\n\n"
            "Example: `/removerate 880`",
            parse_mode='Markdown'
        )
        return
    
    cc = context.args[0]
    
    if cc in COUNTRY_RATES:
        country_name = COUNTRY_RATES[cc]["country"]
        del COUNTRY_RATES[cc]
        await update.message.reply_text(f"✅ Rate removed for {country_name}!")
        save_rate_to_sheet()
    else:
        await update.message.reply_text(f"❌ Country code `{cc}` not found in rate list!", parse_mode='Markdown')

async def list_rates(update: Update, context: CallbackContext):
    """Admin command to list all rates"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not COUNTRY_RATES:
        await update.message.reply_text("No rates configured yet.")
        return
    
    sorted_rates = sorted(COUNTRY_RATES.items(), key=lambda x: x[1]["rate"], reverse=True)
    
    rate_text = "📊 *Current Rates*\n\n"
    for cc, data in sorted_rates:
        rate_text += f"{data['flag']} {data['country'][:15]} (CC: {cc}) - ${data['rate']:.2f}\n"
    
    rate_text += f"\n📊 Total: {len(COUNTRY_RATES)} countries"
    
    await update.message.reply_text(rate_text, parse_mode='Markdown')

async def save_rates(update: Update, context: CallbackContext):
    """Admin command to save rates to sheet"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    save_rate_to_sheet()
    await update.message.reply_text("✅ Rates saved to Google Sheet!")


async def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    # Handle wallet setup
    if 'awaiting_wallet' in context.user_data and context.user_data['awaiting_wallet']:
        await save_wallet_info(update, context)
        return
    
    if update.message.reply_to_message:
        await handle_otp(update, context)
        return
    
    api_cc, phone, display_cc = extract_number(text)
    
    if not api_cc:
        await update.message.reply_text("❌ Invalid! Send like: `+12264566666` or `+9647803260789`", parse_mode='Markdown')
        return
    
    if api_cc not in COUNTRY_APIS:
        await update.message.reply_text("❌ Country not supported!")
        return
    
    country = COUNTRY_APIS[api_cc]['country']
    display_phone = f"+{display_cc} {phone}"
    
    print(f"\n📞 Processing: {display_phone}")
    
    msg = await update.message.reply_text(f"🔄 {display_phone}...")
    
    # Add to processing queue instead of direct processing
    await processing_queue.put((update, context, user, api_cc, phone, display_cc, country, display_phone, msg))

async def handle_otp(update: Update, context: CallbackContext):
    user = update.effective_user
    otp = update.message.text.strip()
    
    if not re.match(r'^\d{6}$', otp):
        await update.message.reply_text("❌ Send 6-digit OTP code!")
        return
    
    phone = None
    data = None
    with active_numbers_lock:
        for p, d in active_numbers.items():
            if d['user_id'] == user.id:
                phone = p
                data = d
                break
    
    if not phone:
        await update.message.reply_text("❌ No active number! Send a new number first.")
        return
    
    display = f"+{data['display_cc']} {phone}"
    print(f"\n🔑 OTP {otp} for {display}")
    
    with active_numbers_lock:
        if phone in active_numbers:
            active_numbers[phone]['otp_submitted'] = True
            active_numbers[phone]['otp_code'] = otp
    
    config = COUNTRY_APIS.get(data['api_cc'])
    token = data.get('token')
    
    if not token:
        token = await login_api(data['api_cc'])
    
    try:
        await rate_limit_api(data['api_cc'])
        async with aiohttp.ClientSession() as session:
            headers = {"Admin-Token": token}
            url = f"{config['base_url']}/z-number-base/allNum/uploadCode?cc={data['api_cc']}&phoneNum={phone}&code={otp}"
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    resp_data = await response.json()
                    if resp_data.get('code') != 200:
                        await update.message.reply_text(f"❌ Wrong OTP! Try again.")
                        save_to_sheet(
                            data['user_id'], data['username'], data['full_name'],
                            phone, data['api_cc'], data['country'],
                            "FAILED", f"Wrong OTP", otp
                        )
                        update_daily_stats(data['user_id'], "FAILED")
                        
                        with active_numbers_lock:
                            if phone in active_numbers:
                                del active_numbers[phone]
                else:
                    await update.message.reply_text(f"❌ OTP submission failed! Try again.")
                    with active_numbers_lock:
                        if phone in active_numbers:
                            del active_numbers[phone]
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        with active_numbers_lock:
            if phone in active_numbers:
                del active_numbers[phone]

# ==================== MENU HANDLERS ====================
async def handle_menu_buttons(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text.strip()
    
    if text == "📊 Statistics":
        await show_statistics(update, context, user)
    elif text == "💰 Check Balance":
        await show_balance(update, context, user)
    elif text == "💸 Withdraw":
        await withdraw_request(update, context)
    elif text == "🌍 Price List":
        await show_price_list(update, context, user)
    elif text == "📥 Download Data":
        await download_my_sheet(update, context)
    elif text == "🆘 Support":
        await show_support(update, context, user)
    elif text == "📸 Payment Proof":
        await show_payment_proof(update, context, user)
    elif text == "👛 My Wallet":
        await show_my_wallet(update, context)
    else:
        await handle_message(update, context)

async def show_statistics(update: Update, context: CallbackContext, user):
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    yesterday = (datetime.now(bd_tz) - timedelta(days=1)).strftime('%Y-%m-%d')
    uid = str(user.id)
    
    is_admin = (user.id == ADMIN_ID)
    
    if is_admin:
        all_users_stats = []
        total_submissions = 0
        total_otp_verified = 0
        
        with stats_lock:
            for user_id, user_stats in daily_stats.items():
                user_total = 0
                user_otp = 0
                
                for date, stats in user_stats.items():
                    if date >= yesterday:
                        user_total += stats.get("total", 0)
                        user_otp += stats.get("otp_verified", 0)
                
                if user_total > 0 or user_otp > 0:
                    all_users_stats.append(f"👤 User {user_id[:8]}...: Total {user_total} | OTP {user_otp}")
                    total_submissions += user_total
                    total_otp_verified += user_otp
        
        stats_text = f"📊 *ADMIN STATISTICS (Last 24h)*\n\n"
        stats_text += f"📅 {datetime.now(bd_tz).strftime('%d %b %Y')}\n"
        stats_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        stats_text += f"📱 Total Submissions: *{total_submissions}*\n"
        stats_text += f"🔑 Total OTP Verified: *{total_otp_verified}*\n"
        stats_text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if all_users_stats:
            stats_text += "*Per User Breakdown:*\n"
            stats_text += "\n".join(all_users_stats[:15])
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    else:
        with stats_lock:
            user_stats = daily_stats.get(uid, {})
        
        total_24h = 0
        otp_verified_24h = 0
        
        for date, stats in user_stats.items():
            if date >= yesterday:
                total_24h += stats.get("total", 0)
                otp_verified_24h += stats.get("otp_verified", 0)
        
        stats_text = f"📊 *Your Statistics (Last 24h)*\n\n"
        stats_text += f"📅 {datetime.now(bd_tz).strftime('%d %b %Y')}\n"
        stats_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        stats_text += f"📱 Total Submissions: *{total_24h}*\n"
        stats_text += f"🔑 OTP Verified: *{otp_verified_24h}*\n"
        stats_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        
        if total_24h == 0:
            stats_text += "\n💡 Send phone numbers to start!"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

async def show_balance(update: Update, context: CallbackContext, user):
    uid = str(user.id)
    
    with balance_lock:
        if uid in user_balances:
            balance = user_balances[uid].get("balance", 0)
        else:
            balance = 0
    
    balance_text = f"💰 *Your Balance*\n\n"
    balance_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    balance_text += f"🏦 Total Balance: *${balance:.2f}*\n"
    balance_text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if balance >= 0.5:
        balance_text += f"✅ You can withdraw! Use 💸 Withdraw button\n"
    else:
        balance_text += f"💡 Minimum withdraw: $0.50\n"
        balance_text += f"Complete OTP verifications to earn!"
    
    await update.message.reply_text(balance_text, parse_mode='Markdown')

async def show_price_list(update: Update, context: CallbackContext, user):
    sorted_rates = sorted(COUNTRY_RATES.items(), key=lambda x: x[1]["rate"], reverse=True)
    
    price_text = f"🌍 *WhatsApp Service Price List*\n\n"
    price_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for cc, data in sorted_rates[:25]:
        flag = data["flag"]
        country = data["country"][:18]
        rate = data["rate"]
        price_text += f"{flag} {country:<18} 💵 ${rate:.2f}\n"
    
    price_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    price_text += f"💡 Earn the listed rate after OTP verification!"
    
    await update.message.reply_text(price_text, parse_mode='Markdown')

async def show_support(update: Update, context: CallbackContext, user):
    support_text = f"🆘 *Support Information*\n\n"
    support_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    support_text += f"📢 *Channel:* @CashxByte\n"
    support_text += f"👑 *Admin ID:* `{ADMIN_ID}`\n"
    support_text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    support_text += f"💬 For issues, contact admin or join channel"
    
    await update.message.reply_text(support_text, parse_mode='Markdown')

async def show_payment_proof(update: Update, context: CallbackContext, user):
    payment_text = f"📸 *Payment Proof*\n\n"
    payment_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    payment_text += f"💰 *Payment Information*\n\n"
    payment_text += f"• Minimum withdrawal: $0.50\n"
    payment_text += f"• Daily limit: 1 withdrawal\n"
    payment_text += f"• Payment method: bKash/Nagad/Binance\n"
    payment_text += f"• Processing time: 24-48 hours\n\n"
    payment_text += f"📢 *Channel:* @CashxByte"
    
    await update.message.reply_text(payment_text, parse_mode='Markdown')

# ==================== WALLET FUNCTIONS ====================
async def wallet_setup(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = str(user.id)
    
    keyboard = [
        [InlineKeyboardButton("📱 bKash", callback_data="wallet_bkash")],
        [InlineKeyboardButton("📱 Nagad", callback_data="wallet_nagad")],
        [InlineKeyboardButton("₿ Binance (USDT TRC20)", callback_data="wallet_binance")],
        [InlineKeyboardButton("❌ Cancel", callback_data="wallet_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user_id in user_wallets and user_wallets[user_id]:
        wallet_info = user_wallets[user_id]
        method_names = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance (USDT)"}
        wallet_text = "👛 *Your Current Wallet*\n\n"
        for method, account in wallet_info.items():
            wallet_text += f"• {method_names.get(method, method)}: `{account}`\n"
        wallet_text += "\nSelect method to update:"
    else:
        wallet_text = "👛 *Setup Your Payment Wallet*\n\nChoose payment method:"
    
    await update.message.reply_text(wallet_text, reply_markup=reply_markup, parse_mode='Markdown')

async def wallet_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "wallet_cancel":
        await query.message.delete()
        return
    
    method_map = {"wallet_bkash": "bkash", "wallet_nagad": "nagad", "wallet_binance": "binance"}
    method = method_map.get(data)
    
    if method:
        context.user_data['wallet_method'] = method
        context.user_data['awaiting_wallet'] = True
        
        prompts = {
            "bkash": "📱 *bKash Account Setup*\n\nSend your bKash account number:\nExample: `01XXXXXXXXX`",
            "nagad": "📱 *Nagad Account Setup*\n\nSend your Nagad account number:\nExample: `01XXXXXXXXX`",
            "binance": "₿ *Binance USDT (TRC20) Setup*\n\nSend your USDT TRC20 wallet address:"
        }
        
        await query.message.edit_text(prompts.get(method, ""), parse_mode='Markdown')

async def save_wallet_info(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    account = update.message.text.strip()
    
    if 'awaiting_wallet' not in context.user_data:
        return
    
    method = context.user_data.get('wallet_method')
    
    if not method:
        await update.message.reply_text("❌ Please setup wallet first with /wallet")
        return
    
    if user_id not in user_wallets:
        user_wallets[user_id] = {}
    
    user_wallets[user_id][method] = account
    
    method_names = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance (USDT)"}
    
    await update.message.reply_text(
        f"✅ *Wallet Saved!*\n\n"
        f"📱 Method: {method_names.get(method, method)}\n"
        f"💳 Account: `{account}`\n\n"
        f"Use /wallet to update anytime",
        parse_mode='Markdown'
    )
    
    context.user_data['awaiting_wallet'] = False
    context.user_data['wallet_method'] = None

async def show_my_wallet(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    
    if user_id not in user_wallets or not user_wallets[user_id]:
        await update.message.reply_text("❌ No wallet setup yet!\n\nUse /wallet to setup your payment method.")
        return
    
    wallet_info = user_wallets[user_id]
    method_names = {"bkash": "📱 bKash", "nagad": "📱 Nagad", "binance": "₿ Binance (USDT TRC20)"}
    
    wallet_text = "👛 *Your Saved Wallets*\n\n"
    wallet_text += "━━━━━━━━━━━━━━━━━━━━━\n"
    
    for method, account in wallet_info.items():
        wallet_text += f"{method_names.get(method, method)}\n"
        wallet_text += f"💳 `{account}`\n\n"
    
    wallet_text += "━━━━━━━━━━━━━━━━━━━━━\n"
    wallet_text += "Use /wallet to update"
    
    await update.message.reply_text(wallet_text, parse_mode='Markdown')

# ==================== WITHDRAW FUNCTIONS ====================
async def withdraw_request(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = str(user.id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    
    # Check wallet setup
    if user_id not in user_wallets or not user_wallets[user_id]:
        await update.message.reply_text(
            "❌ Please setup your wallet first!\n\n"
            "Use 👛 My Wallet button or /wallet to add payment method.\n"
            "Available: bKash, Nagad, Binance (USDT)"
        )
        return
    
    # Check daily limit
    if user_id in daily_withdraw_count and today in daily_withdraw_count[user_id]:
        if daily_withdraw_count[user_id][today] >= 1:
            await update.message.reply_text(
                "❌ Daily withdraw limit reached!\n\n"
                "You can withdraw only 1 time per day.\n"
                "Next withdraw available tomorrow."
            )
            return
    
    # Check pending withdraw
    if user_id in pending_withdraws:
        await update.message.reply_text(
            "⏳ You already have a pending withdraw request!\n\n"
            "Please wait for admin to process it."
        )
        return
    
    # Check balance
    balance = 0
    with balance_lock:
        if user_id in user_balances:
            balance = user_balances[user_id].get("balance", 0)
    
    if balance < 0.5:
        await update.message.reply_text(
            f"❌ Minimum withdraw is $0.50!\n\n"
            f"Your balance: ${balance:.2f}\n"
            f"Need: ${0.50 - balance:.2f} more\n\n"
            f"Complete more OTP verifications to earn!"
        )
        return
    
    # Show wallet selection for withdraw
    wallet_info = user_wallets[user_id]
    keyboard = []
    
    if "bkash" in wallet_info:
        keyboard.append([InlineKeyboardButton(f"📱 bKash ({wallet_info['bkash']})", callback_data="wd_bkash")])
    if "nagad" in wallet_info:
        keyboard.append([InlineKeyboardButton(f"📱 Nagad ({wallet_info['nagad']})", callback_data="wd_nagad")])
    if "binance" in wallet_info:
        keyboard.append([InlineKeyboardButton(f"₿ Binance ({wallet_info['binance'][:15]}...)", callback_data="wd_binance")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="wd_cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    withdraw_text = (
        f"💸 *Withdraw Request*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Available Balance: *${balance:.2f}*\n"
        f"💵 Withdraw Amount: *${balance:.2f}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Select payment method:"
    )
    
    await update.message.reply_text(withdraw_text, reply_markup=reply_markup, parse_mode='Markdown')

async def withdraw_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    
    if data == "wd_cancel":
        await query.message.delete()
        return
    
    method_map = {"wd_bkash": "bkash", "wd_nagad": "nagad", "wd_binance": "binance"}
    method = method_map.get(data)
    
    if not method or user_id not in user_wallets or method not in user_wallets[user_id]:
        await query.message.edit_text("❌ Wallet not found! Use /wallet to setup.")
        return
    
    balance = 0
    with balance_lock:
        if user_id in user_balances:
            balance = user_balances[user_id].get("balance", 0)
    
    account = user_wallets[user_id][method]
    
    method_names = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance (USDT TRC20)"}
    
    # Store pending withdraw
    pending_withdraws[user_id] = {
        "amount": balance,
        "wallet_method": method,
        "account": account,
        "date": today,
        "username": query.from_user.username or "N/A",
        "full_name": query.from_user.full_name,
        "message_id": query.message.message_id
    }
    
    # Set balance to 0 immediately
    with balance_lock:
        if user_id in user_balances:
            user_balances[user_id]["balance"] = 0
            user_balances[user_id]["history"] = []
    
    # Mark daily count
    if user_id not in daily_withdraw_count:
        daily_withdraw_count[user_id] = {}
    daily_withdraw_count[user_id][today] = 1
    
    # Save withdraw history
    if user_id not in withdraw_history:
        withdraw_history[user_id] = []
    
    withdraw_history[user_id].append({
        "date": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S'),
        "amount": balance,
        "method": method,
        "account": account,
        "status": "Pending"
    })
    
    await query.message.edit_text(
        f"✅ *Withdraw Request Submitted!*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Amount: *${balance:.2f}*\n"
        f"📱 Method: {method_names.get(method, method)}\n"
        f"💳 Account: `{account}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏳ Admin will process your payment soon.\n"
        f"📢 Join @CashxByte for updates!",
        parse_mode='Markdown'
    )
    
    # Paid mark update
    update_paid_status_in_sheet(user_id, method_names.get(method, method))
    
    # Send to admin
    await send_withdraw_to_admin(context, user_id, balance, method, account)

async def send_withdraw_to_admin(context, user_id, amount, method, account):
    method_names = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance (USDT TRC20)"}
    method_emoji = {"bkash": "📱", "nagad": "📱", "binance": "₿"}
    
    all_wallets = ""
    if user_id in user_wallets:
        for m, acc in user_wallets[user_id].items():
            all_wallets += f"\n{method_emoji.get(m, '💳')} {method_names.get(m, m)}: `{acc}`"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm Payment", callback_data=f"confirm_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_msg = (
        f"💸 *NEW WITHDRAW REQUEST*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User: [{pending_withdraws[user_id]['full_name']}](tg://user?id={user_id})\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Username: @{pending_withdraws[user_id]['username']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Amount: *${amount:.2f}*\n"
        f"📱 Pay via: {method_emoji.get(method, '')} {method_names.get(method, method)}\n"
        f"💳 Account: `{account}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👛 *All Saved Wallets:*{all_wallets}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date: {datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_confirm_withdraw(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    action = parts[0]
    user_id = parts[1]
    
    if user_id not in pending_withdraws:
        await query.message.edit_text(
            query.message.text + "\n\n⚠️ Request already processed!",
            parse_mode='Markdown'
        )
        return
    
    pending = pending_withdraws[user_id]
    method_names = {"bkash": "bKash", "nagad": "Nagad", "binance": "Binance (USDT TRC20)"}
    
    if action == "confirm":
        if user_id in withdraw_history and withdraw_history[user_id]:
            withdraw_history[user_id][-1]["status"] = "Confirmed"
        
        await query.message.edit_text(
            query.message.text + "\n\n✅ *PAYMENT CONFIRMED*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=(
                    f"✅ *Withdraw Confirmed!*\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Amount: *${pending['amount']:.2f}*\n"
                    f"📱 Method: {method_names.get(pending['wallet_method'], 'N/A')}\n"
                    f"💳 Account: `{pending['account']}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎉 Payment has been sent!\n"
                    f"📢 Join @CashxByte for more!"
                ),
                parse_mode='Markdown'
            )
        except:
            pass
        
        del pending_withdraws[user_id]
    
    elif action == "reject":
        with balance_lock:
            if user_id in user_balances:
                user_balances[user_id]["balance"] = pending['amount']
        
        if user_id in withdraw_history and withdraw_history[user_id]:
            withdraw_history[user_id][-1]["status"] = "Rejected"
        
        today = datetime.now(bd_tz).strftime('%Y-%m-%d')
        if user_id in daily_withdraw_count and today in daily_withdraw_count[user_id]:
            del daily_withdraw_count[user_id][today]
        
        await query.message.edit_text(
            query.message.text + "\n\n❌ *PAYMENT REJECTED - Balance Restored*",
            parse_mode='Markdown'
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=(
                    f"❌ *Withdraw Rejected*\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💰 Amount: *${pending['amount']:.2f}* restored to balance\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Please contact @CashxByte for support"
                ),
                parse_mode='Markdown'
            )
        except:
            pass
        
        del pending_withdraws[user_id]

def update_paid_status_in_sheet(user_id, wallet_method):
    payload = {
        "type": "paid_update",
        "user_id": user_id,
        "wallet_method": wallet_method,
        "timestamp": datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')
    }
    sheet_queue.append(payload)

# ==================== DOWNLOAD FUNCTIONS ====================
async def my_sheet_command(update: Update, context: CallbackContext):
    user = update.effective_user
    sheet_url = "https://script.google.com/macros/s/AKfycbwxrVX_8zbCkzsKwhx7u5OX9CUp2Y7RelJ_srzqp0CxrEmMMzG8xy9kvmSVmNFG4Zh_7A/edit"
    
    message = (
        f"🔗 YOUR GOOGLE SHEET LINK\n\n"
        f"User ID: {user.id}\n\n"
        f"Click to view your data:\n{sheet_url}"
    )
    
    await update.message.reply_text(message)

async def my_stats_command(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = str(user.id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    filename = f"user_stats_{user.id}_{today}.txt"
    
    content = []
    content.append("=" * 50)
    content.append("WHATSAPP REGISTRATION BOT - USER STATISTICS")
    content.append("=" * 50)
    content.append(f"Export Date: {datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"User ID: {user.id}")
    content.append(f"Username: {user.username or 'N/A'}")
    content.append("")
    
    with stats_lock:
        if user_id in daily_stats:
            for date, stats in sorted(daily_stats[user_id].items()):
                content.append(f"{date}: Total={stats.get('total',0)}, OTP={stats.get('otp_verified',0)}")
    
    with balance_lock:
        if user_id in user_balances:
            content.append(f"\nBalance: ${user_balances[user_id].get('balance', 0):.2f}")
    
    text_content = "\n".join(content)
    
    try:
        await context.bot.send_document(
            chat_id=user.id,
            document=text_content.encode('utf-8'),
            filename=filename,
            caption=f"📊 Your Statistics Report"
        )
    except:
        await update.message.reply_text(text_content[:4000])

async def my_balance_command(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = str(user.id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    filename = f"user_balance_{user.id}_{today}.txt"
    
    content = []
    content.append("=" * 50)
    content.append("BALANCE HISTORY")
    content.append("=" * 50)
    
    with balance_lock:
        if user_id in user_balances:
            content.append(f"Balance: ${user_balances[user_id].get('balance', 0):.2f}")
            for entry in user_balances[user_id].get("history", []):
                content.append(f"{entry.get('date')}: +${entry.get('amount', 0):.2f}")
    
    text_content = "\n".join(content)
    
    try:
        await context.bot.send_document(
            chat_id=user.id,
            document=text_content.encode('utf-8'),
            filename=filename,
            caption=f"💰 Your Balance History"
        )
    except:
        await update.message.reply_text(text_content[:4000])

async def my_history_command(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = str(user.id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    filename = f"user_full_history_{user.id}_{today}.txt"
    
    content = []
    content.append("=" * 50)
    content.append("FULL HISTORY")
    content.append("=" * 50)
    
    with stats_lock:
        if user_id in daily_stats:
            for date, stats in sorted(daily_stats[user_id].items()):
                content.append(f"{date}: Total={stats.get('total',0)}, OTP={stats.get('otp_verified',0)}")
    
    with balance_lock:
        if user_id in user_balances:
            content.append(f"\nBalance: ${user_balances[user_id].get('balance', 0):.2f}")
    
    text_content = "\n".join(content)
    
    try:
        await context.bot.send_document(
            chat_id=user.id,
            document=text_content.encode('utf-8'),
            filename=filename,
            caption=f"📋 Your Full History Report"
        )
    except:
        await update.message.reply_text(text_content[:4000])

async def download_my_sheet(update: Update, context: CallbackContext):
    user = update.effective_user
    
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/CashxByte")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"Please join {REQUIRED_CHANNEL} first!", reply_markup=reply_markup)
            return
    except:
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/CashxByte")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Please join {REQUIRED_CHANNEL} first!", reply_markup=reply_markup)
        return
    
    message = (
        f"📥 DOWNLOAD YOUR DATA\n\n"
        f"User: {user.first_name}\n"
        f"ID: {user.id}\n\n"
        f"Use these commands:\n\n"
        f"/mystats - Download statistics\n"
        f"/mybalance - Download balance\n"
        f"/myhistory - Download full history\n"
        f"/mysheet - Get Google Sheet link"
    )
    
    await update.message.reply_text(message)

# ==================== MAIN ====================
from fastapi import FastAPI
import uvicorn

app_fastapi = FastAPI()

@app_fastapi.get("/")
async def root():
    return {"status": "active", "message": "Bot is running"}

@app_fastapi.get("/health")
async def health():
    return {"status": "healthy"}

def run_fastapi():
    uvicorn.run(app_fastapi, host="0.0.0.0", port=PORT, access_log=False)

def main():
    # Start FastAPI
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    print(f"✅ FastAPI server started on port {PORT}")
    
    def reset_checker():
        while True:
            check_and_reset_daily()
            time.sleep(60)
    
    reset_thread = threading.Thread(target=reset_checker, daemon=True)
    reset_thread.start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", show_statistics))
    app.add_handler(CommandHandler("balance", show_balance))
    app.add_handler(CommandHandler("price", show_price_list))
    app.add_handler(CommandHandler("wallet", wallet_setup))
    app.add_handler(CommandHandler("mywallet", show_my_wallet))
    app.add_handler(CommandHandler("withdraw", withdraw_request))
    app.add_handler(CommandHandler("mystats", my_stats_command))
    app.add_handler(CommandHandler("mybalance", my_balance_command))
    app.add_handler(CommandHandler("myhistory", my_history_command))
    app.add_handler(CommandHandler("mysheet", my_sheet_command))
    app.add_handler(CommandHandler("download", download_my_sheet))
    app.add_handler(CommandHandler("addrate", add_rate))
    app.add_handler(CommandHandler("removerate", remove_rate))
    app.add_handler(CommandHandler("listrates", list_rates))
    app.add_handler(CommandHandler("saverates", save_rates))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(wallet_callback, pattern="^wallet_"))
    app.add_handler(CallbackQueryHandler(withdraw_callback, pattern="^wd_"))
    app.add_handler(CallbackQueryHandler(admin_confirm_withdraw, pattern="^(confirm|reject)_"))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
    
    # Start background worker
    asyncio.get_event_loop().create_task(processing_worker())
    
    print("\n✅ BOT RUNNING!")
    print("⏱️ Max tracking: 3 minutes per number")
    print("💰 Earnings only for OTP verified")
    print("📅 No daily reset - Balance accumulates")
    print("💸 Withdraw system: Min $0.50, Daily 1 time")
    print("👛 Wallet: bKash/Nagad/Binance")
    print(f"⚡ Concurrent support: Up to {GLOBAL_MAX_CONCURRENT} simultaneous requests")
    print(f"🚀 FastAPI on port: {PORT}")
    print("="*60 + "\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()

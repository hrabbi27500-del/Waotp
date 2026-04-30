# ==================== WHATSAPP REGISTRATION BOT - FINAL ====================
import os
import asyncio
import re
import json
import aiohttp
import requests
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, CallbackContext
import threading
import time





print("="*60)
print("🚀 WHATSAPP REGISTRATION BOT - FINAL")
print("="*60)

import os
from dotenv import load_dotenv

# ==================== LOAD ENVIRONMENT VARIABLES ====================
load_dotenv()  # .env ফাইল থেকে লোড করবে

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5624278091"))
GOOGLE_SHEET_URL = os.environ.get("GOOGLE_SHEET_URL", "")
PORT = int(os.environ.get("PORT", 10000))

print(f"📱 Bot Token: ✅")
print(f"👑 Admin ID: {ADMIN_ID}")

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
    "52": {"cc": "52", "display_cc": "52", "country": "Mexico", "base_url": "http://8.222.182.223:8081", "username": "your_mx_user", "password": "your_mx_pass"},
    "44": {"cc": "44", "display_cc": "44", "country": "UK", "base_url": "http://8.222.182.223:8081", "username": "your_uk_user", "password": "your_uk_pass"},
    "49": {"cc": "49", "display_cc": "49", "country": "Germany", "base_url": "http://8.222.182.223:8081", "username": "your_de_user", "password": "your_de_pass"},
    "33": {"cc": "33", "display_cc": "33", "country": "France", "base_url": "http://8.222.182.223:8081", "username": "your_fr_user", "password": "your_fr_pass"},
    "34": {"cc": "34", "display_cc": "34", "country": "Spain", "base_url": "http://8.222.182.223:8081", "username": "your_es_user", "password": "your_es_pass"},
    "39": {"cc": "39", "display_cc": "39", "country": "Italy", "base_url": "http://8.222.182.223:8081", "username": "your_it_user", "password": "your_it_pass"},
    "7": {"cc": "7", "display_cc": "7", "country": "Russia", "base_url": "http://8.222.182.223:8081", "username": "your_ru_user", "password": "your_ru_pass"},
    "31": {"cc": "31", "display_cc": "31", "country": "Netherlands", "base_url": "http://8.222.182.223:8081", "username": "your_nl_user", "password": "your_nl_pass"},
    "46": {"cc": "46", "display_cc": "46", "country": "Sweden", "base_url": "http://8.222.182.223:8081", "username": "your_se_user", "password": "your_se_pass"},
    "47": {"cc": "47", "display_cc": "47", "country": "Norway", "base_url": "http://8.222.182.223:8081", "username": "your_no_user", "password": "your_no_pass"},
    "45": {"cc": "45", "display_cc": "45", "country": "Denmark", "base_url": "http://8.222.182.223:8081", "username": "your_dk_user", "password": "your_dk_pass"},
    "358": {"cc": "358", "display_cc": "358", "country": "Finland", "base_url": "http://8.222.182.223:8081", "username": "your_fi_user", "password": "your_fi_pass"},
    "880": {"cc": "880", "display_cc": "880", "country": "Bangladesh", "base_url": "http://8.222.182.223:8081", "username": "your_bd_user", "password": "your_bd_pass"},
    "91": {"cc": "91", "display_cc": "91", "country": "India", "base_url": "http://8.222.182.223:8081", "username": "your_in_user", "password": "your_in_pass"},
    "92": {"cc": "92", "display_cc": "92", "country": "Pakistan", "base_url": "http://8.222.182.223:8081", "username": "your_pk_user", "password": "your_pk_pass"},
    "94": {"cc": "94", "display_cc": "94", "country": "Sri Lanka", "base_url": "http://8.222.182.223:8081", "username": "your_lk_user", "password": "your_lk_pass"},
    "977": {"cc": "977", "display_cc": "977", "country": "Nepal", "base_url": "http://8.222.182.223:8081", "username": "your_np_user", "password": "your_np_pass"},
    "60": {"cc": "60", "display_cc": "60", "country": "Malaysia", "base_url": "http://8.222.182.223:8081", "username": "your_my_user", "password": "your_my_pass"},
    "62": {"cc": "62", "display_cc": "62", "country": "Indonesia", "base_url": "http://8.222.182.223:8081", "username": "your_id_user", "password": "your_id_pass"},
    "63": {"cc": "63", "display_cc": "63", "country": "Philippines", "base_url": "http://8.222.182.223:8081", "username": "your_ph_user", "password": "your_ph_pass"},
    "66": {"cc": "66", "display_cc": "66", "country": "Thailand", "base_url": "http://8.222.182.223:8081", "username": "your_th_user", "password": "your_th_pass"},
    "84": {"cc": "84", "display_cc": "84", "country": "Vietnam", "base_url": "http://8.222.182.223:8081", "username": "your_vn_user", "password": "your_vn_pass"},
    "81": {"cc": "81", "display_cc": "81", "country": "Japan", "base_url": "http://8.222.182.223:8081", "username": "your_jp_user", "password": "your_jp_pass"},
    "82": {"cc": "82", "display_cc": "82", "country": "Korea", "base_url": "http://8.222.182.223:8081", "username": "your_kr_user", "password": "your_kr_pass"},
    "86": {"cc": "86", "display_cc": "86", "country": "China", "base_url": "http://8.222.182.223:8081", "username": "your_cn_user", "password": "your_cn_pass"},
    "886": {"cc": "886", "display_cc": "886", "country": "Taiwan", "base_url": "http://8.222.182.223:8081", "username": "your_tw_user", "password": "your_tw_pass"},
    "852": {"cc": "852", "display_cc": "852", "country": "Hong Kong", "base_url": "http://8.222.182.223:8081", "username": "your_hk_user", "password": "your_hk_pass"},
    "853": {"cc": "853", "display_cc": "853", "country": "Macau", "base_url": "http://8.222.182.223:8081", "username": "your_mo_user", "password": "your_mo_pass"},
    "964": {"cc": "964", "display_cc": "964", "country": "Iraq", "base_url": "http://8.222.182.223:8081", "username": "JahidIQ", "password": "JahidIQ"},
    "966": {"cc": "966", "display_cc": "966", "country": "Saudi Arabia", "base_url": "http://8.222.182.223:8081", "username": "your_sa_user", "password": "your_sa_pass"},
    "971": {"cc": "971", "display_cc": "971", "country": "UAE", "base_url": "http://8.222.182.223:8081", "username": "your_ae_user", "password": "your_ae_pass"},
    "962": {"cc": "962", "display_cc": "962", "country": "Jordan", "base_url": "http://8.222.182.223:8081", "username": "your_jo_user", "password": "your_jo_pass"},
    "961": {"cc": "961", "display_cc": "961", "country": "Lebanon", "base_url": "http://8.222.182.223:8081", "username": "your_lb_user", "password": "your_lb_pass"},
    "965": {"cc": "965", "display_cc": "965", "country": "Kuwait", "base_url": "http://8.222.182.223:8081", "username": "your_kw_user", "password": "your_kw_pass"},
    "968": {"cc": "968", "display_cc": "968", "country": "Oman", "base_url": "http://8.222.182.223:8081", "username": "your_om_user", "password": "your_om_pass"},
    "973": {"cc": "973", "display_cc": "973", "country": "Bahrain", "base_url": "http://8.222.182.223:8081", "username": "your_bh_user", "password": "your_bh_pass"},
    "974": {"cc": "974", "display_cc": "974", "country": "Qatar", "base_url": "http://8.222.182.223:8081", "username": "your_qa_user", "password": "your_qa_pass"},
    "98": {"cc": "98", "display_cc": "98", "country": "Iran", "base_url": "http://8.222.182.223:8081", "username": "your_ir_user", "password": "your_ir_pass"},
    "90": {"cc": "90", "display_cc": "90", "country": "Turkey", "base_url": "http://8.222.182.223:8081", "username": "your_tr_user", "password": "your_tr_pass"},
    "972": {"cc": "972", "display_cc": "972", "country": "Israel", "base_url": "http://8.222.182.223:8081", "username": "your_il_user", "password": "your_il_pass"},
    "20": {"cc": "20", "display_cc": "20", "country": "Egypt", "base_url": "http://8.222.182.223:8081", "username": "your_eg_user", "password": "your_eg_pass"},
    "27": {"cc": "27", "display_cc": "27", "country": "South Africa", "base_url": "http://8.222.182.223:8081", "username": "your_za_user", "password": "your_za_pass"},
    "234": {"cc": "234", "display_cc": "234", "country": "Nigeria", "base_url": "http://8.222.182.223:8081", "username": "your_ng_user", "password": "your_ng_pass"},
    "212": {"cc": "212", "display_cc": "212", "country": "Morocco", "base_url": "http://8.222.182.223:8081", "username": "your_ma_user", "password": "your_ma_pass"},
    "216": {"cc": "216", "display_cc": "216", "country": "Tunisia", "base_url": "http://8.222.182.223:8081", "username": "your_tn_user", "password": "your_tn_pass"},
    "213": {"cc": "213", "display_cc": "213", "country": "Algeria", "base_url": "http://8.222.182.223:8081", "username": "your_dz_user", "password": "your_dz_pass"},
    "55": {"cc": "55", "display_cc": "55", "country": "Brazil", "base_url": "http://8.222.182.223:8081", "username": "your_br_user", "password": "your_br_pass"},
    "54": {"cc": "54", "display_cc": "54", "country": "Argentina", "base_url": "http://8.222.182.223:8081", "username": "your_ar_user", "password": "your_ar_pass"},
    "56": {"cc": "56", "display_cc": "56", "country": "Chile", "base_url": "http://8.222.182.223:8081", "username": "your_cl_user", "password": "your_cl_pass"},
    "57": {"cc": "57", "display_cc": "57", "country": "Colombia", "base_url": "http://8.222.182.223:8081", "username": "your_co_user", "password": "your_co_pass"},
    "51": {"cc": "51", "display_cc": "51", "country": "Peru", "base_url": "http://8.222.182.223:8081", "username": "your_pe_user", "password": "your_pe_pass"},
    "58": {"cc": "58", "display_cc": "58", "country": "Venezuela", "base_url": "http://8.222.182.223:8081", "username": "JahidVN", "password": "JahidVN"},
    "61": {"cc": "61", "display_cc": "61", "country": "Australia", "base_url": "http://8.222.182.223:8081", "username": "your_au_user", "password": "your_au_pass"},
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

# ==================== SHEET SAVE QUEUE ====================
sheet_queue = []
sheet_thread_running = True

# আপনার ফাইলের শুরুতে যোগ করুন
import asyncio
import aiohttp

async def keep_alive_enhanced():
    # এখানে আপনার URL গুলো বসান
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
        await asyncio.sleep(180)  # 3 মিনিট

# আপনার main ফাংশনে কল করুন
# 

def sheet_worker():
    while sheet_thread_running:
        try:
            if sheet_queue:
                payload = sheet_queue.pop(0)
                try:
                    response = requests.post(GOOGLE_SHEET_URL, json=payload, timeout=30)
                    if response.status_code == 200:
                        print(f"   ✅ Sheet saved: {payload.get('status')}")
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
        print(f"   ⏭️ Skip sheet: {status}")
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
    print(f"   📤 Final saved: {status}")
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
    
    if user_id_str not in user_balances:
        user_balances[user_id_str] = {"balance": 0, "history": []}
    
    if "last_reset" not in user_balances[user_id_str]:
        user_balances[user_id_str]["last_reset"] = today
    
    if user_balances[user_id_str]["last_reset"] != today:
        user_balances[user_id_str]["balance"] = 0
        user_balances[user_id_str]["history"] = []
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
    global last_reset_date
    now = datetime.now(bd_tz)
    today_str = now.strftime('%Y-%m-%d')
    
    if now.hour >= 16 and last_reset_date != today_str:
        print(f"\n🔄 DAILY RESET at {now.strftime('%H:%M:%S')}")
        
        for user_id in list(daily_stats.keys()):
            if today_str not in daily_stats[user_id]:
                daily_stats[user_id][today_str] = {"total": 0, "success": 0, "failed": 0, "otp_verified": 0}
        
        for user_id in list(user_balances.keys()):
            if user_balances[user_id].get("last_reset") != today_str:
                user_balances[user_id]["balance"] = 0
                user_balances[user_id]["history"] = []
                user_balances[user_id]["last_reset"] = today_str
        
        last_reset_date = today_str
        print(f"✅ Reset completed for {today_str}")
    
    return False

# ==================== MAIN TRACKING FUNCTION ====================
async def track_number_status(context, chat_id, message_id, phone, api_cc, display_cc, user_id, username, full_name, country, token):
    """
    ট্র্যাকিং ফাংশন:
    - রিয়েল টাইম কাউন্টডাউন দেখাবে
    - ম্যাক্স ৩ মিনিট ট্র্যাকিং
    """
    display = f"+{display_cc} {phone}"
    start_time = datetime.now()
    max_duration = 180  # ৩ মিনিট
    check_interval = 1   # প্রতি ১ সেকেন্ডে চেক
    
    config = COUNTRY_APIS.get(api_cc)
    check_count = 0
    last_status = None
    stuck_start_time = None
    last_update_time = 0
    
    # যেসব স্ট্যাটাসে অটো ডিলিট হবে
    auto_delete_statuses = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    
    # Track OTP verified count for today
    today_otp_count = 0
    
    while True:
        elapsed = (datetime.now() - start_time).total_seconds()
        remaining = max_duration - elapsed
        remaining_min = int(remaining / 60)
        remaining_sec = int(remaining % 60)
        
        current_time = int(elapsed)
        if current_time > last_update_time:
            last_update_time = current_time
            
            # Only show countdown when IN PROGRESS
            if last_status == 2 or last_status is None:
                try:
                    # Check if OTP submitted and still verifying
                    if phone in active_numbers and active_numbers[phone].get('otp_submitted'):
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"🟡 {display} OTP submitted - verifying..."
                        )
                    else:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"🟡 {display} IN PROGRESS\n⏳ {remaining_min}m {remaining_sec}s left"
                        )
                except:
                    pass
        
        # ৩ মিনিট পার হলে
        if elapsed >= max_duration:
            if last_status == 2:
                print(f"   ⏰ STUCK DETECTED: {display}")
                await delete_number_from_api(api_cc, phone, token, 2)
                
                try:
                    stuck_msg = (
                        f"😕 আপনার নম্বরটি আটকে গেছে!\n\n"
                        f"📞 {display}\n"
                        f"⏰ ৩ মিনিট পার হয়েছে\n\n"
                        f"✅ নম্বরটি ডিলিট করা হয়েছে\n🔄 আবার চেষ্টা করুন"
                    )
                    await context.bot.send_message(chat_id=user_id, text=stuck_msg)
                except:
                    pass
                
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"🟡 {display} ⏰ 3 min timeout"
                    )
                except:
                    pass
            else:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"🟡 {display} ⏰ Timeout - Try again"
                    )
                except:
                    pass
            
            if phone in active_numbers:
                del active_numbers[phone]
            break
        
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
                            
                            # স্ট্যাটাস নেম
                            if status_code == 1:
                                status_text = "✅ SUCCESS"
                            elif status_code == 2:
                                status_text = "🟡 IN PROGRESS"
                            elif status_code == 0:
                                status_text = "🟡 PROCESSING"
                            elif status_code == 4:
                                status_text = "❌ NOT REGISTERED"
                            elif status_code == 6:
                                status_text = "🔴 WRONG OTP"
                            else:
                                status_text = f"❌ {status_code}"
                            
                            # স্ট্যাটাস চেঞ্জ হলে
                            if status_code != last_status:
                                check_count += 1
                                print(f"   🔍 #{check_count}: {display} → {status_text}")
                                
                                if status_code == 2:
                                    if stuck_start_time is None:
                                        stuck_start_time = datetime.now()
                                else:
                                    stuck_start_time = None
                                
                                last_status = status_code
                            
                            # চেক করো stuck হয়েছে কিনা
                            if status_code == 2 and stuck_start_time is not None:
                                stuck_duration = (datetime.now() - stuck_start_time).total_seconds()
                                if stuck_duration >= max_duration:
                                    print(f"   ⏰ STUCK: {display}")
                                    await delete_number_from_api(api_cc, phone, token, 2)
                                    
                                    try:
                                        await context.bot.send_message(
                                            chat_id=user_id,
                                            text=f"😕 {display} ⏰ 3 minutes without change\n✅ Number deleted\n🔄 Try again"
                                        )
                                    except:
                                        pass
                                    
                                    await context.bot.edit_message_text(
                                        chat_id=chat_id,
                                        message_id=message_id,
                                        text=f"🟡 {display} ⏰ Stuck"
                                    )
                                    
                                    if phone in active_numbers:
                                        del active_numbers[phone]
                                    break
                            
                            # ============ SUCCESS (WhatsApp registered) ============
                            if status_code == 1:
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    text=f"✅ {display} 🟢 SUCCESS"
                                )
                                
                                is_otp = False
                                otp_code = None
                                if phone in active_numbers:
                                    is_otp = active_numbers[phone].get('otp_submitted', False)
                                    otp_code = active_numbers[phone].get('otp_code')
                                
                                # Only count earnings if OTP was verified
                                if is_otp and otp_code:
                                    # Get rate for this country
                                    rate = COUNTRY_RATES.get(api_cc, {}).get("rate", 0)
                                    if rate > 0:
                                        new_balance = add_earning_to_balance(user_id, api_cc, rate)
                                        save_msg = f"OTP Verified - Earned ${rate:.2f}"
                                        update_daily_stats(user_id, "OTP_VERIFIED", api_cc)
                                        
                                        # Get today's OTP count
                                        today = datetime.now(bd_tz).strftime('%Y-%m-%d')
                                        uid = str(user_id)
                                        if uid in daily_stats and today in daily_stats[uid]:
                                            today_otp_count = daily_stats[uid][today].get("otp_verified", 0)
                                        
                                        # Send earning message without the extra texts
                                        try:
                                            await context.bot.send_message(
                                                chat_id=user_id,
                                                text=f"💰 OTP Verified!\n📞 {display}\n🌎 {country}\n💵 Earning: ${rate:.2f}\n🏦 Total Balance: ${new_balance:.2f}\n🔖Total verified today: {today_otp_count}"
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
                                
                                await context.bot.send_message(
                                    ADMIN_ID,
                                    f"✅ SUCCESS!\n👤 {full_name}\n📞 {display}"
                                )
                                
                                if phone in active_numbers:
                                    del active_numbers[phone]
                                break
                            
                            # ============ অটো ডিলিট (remove delete text) ============
                            elif status_code in auto_delete_statuses:
                                print(f"   🗑️ Auto-deleting: {display}")
                                await delete_number_from_api(api_cc, phone, token, status_code)
                                
                                # Remove delete text from message
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
                                
                                save_to_sheet(user_id, username, full_name, phone, api_cc, country, "FAILED", save_msg, 
                                             active_numbers[phone].get('otp_code') if phone in active_numbers else None)
                                update_daily_stats(user_id, "FAILED")
                                
                                if phone in active_numbers:
                                    del active_numbers[phone]
                                break
        
        except Exception as e:
            print(f"   ⚠️ Tracking error: {e}")
        
        await asyncio.sleep(check_interval)

# ==================== API FUNCTIONS ====================
async def login_api(cc):
    if cc in api_tokens and api_tokens[cc].get('expires_at', datetime.now()) > datetime.now():
        return api_tokens[cc]['token']
    
    config = COUNTRY_APIS.get(cc)
    if not config:
        print(f"   ❌ No config for CC: {cc}")
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"account": config['username'], "password": config['password'], "identity": "Member"}
            async with session.post(f"{config['base_url']}/user/login", json=payload, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and "data" in data and "token" in data["data"]:
                        token = data["data"]["token"]
                        api_tokens[cc] = {
                            'token': token,
                            'expires_at': datetime.now() + timedelta(hours=23)
                        }
                        print(f"   ✅ Login: {config['country']} (CC: {cc})")
                        return token
        print(f"   ❌ Login failed for {config['country']}")
        return None
    except Exception as e:
        print(f"   ❌ Login error for {cc}: {e}")
        return None

async def process_number(update, context, user, api_cc, phone, display_cc, country, display_phone, msg):
    token = await login_api(api_cc)
    if not token:
        await msg.edit_text(f"❌ {display_phone}\nLogin failed")
        save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", "Login failed")
        return
    
    config = COUNTRY_APIS.get(api_cc)
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Admin-Token": token}
            check_url = f"{config['base_url']}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
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
                            await context.bot.send_message(ADMIN_ID, f"✅ ALREADY REGISTERED!\n👤 {user.full_name}\n📞 {display_phone}")
                            return
                        
                        if status_code == 4:
                            await msg.edit_text(f"❌ {display_phone}\nAlready checked - Not Registered")
                            save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", "Already Not Registered", None)
                            update_daily_stats(user.id, "FAILED")
                            return
    except:
        pass
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Admin-Token": token}
            add_url = f"{config['base_url']}/z-number-base/addNum?cc={api_cc}&phoneNum={phone}&smsStatus=2"
            async with session.post(add_url, headers=headers, timeout=10) as response:
                if response.status == 409:
                    print(f"   ⚠️ Number already exists in API: {display_phone}")
                    async with session.get(check_url, headers=headers, timeout=10) as status_resp:
                        if status_resp.status == 200:
                            status_data = await status_resp.json()
                            if status_data and "data" in status_data and "records" in status_data["data"] and status_data["data"]["records"]:
                                record = status_data["data"]["records"][0]
                                status_code = record.get("registrationStatus")
                                
                                if status_code == 1:
                                    await msg.edit_text(f"✅ {display_phone} 🟢 ALREADY REGISTERED")
                                    save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "SUCCESS", "Already Registered", None)
                                    update_daily_stats(user.id, "SUCCESS")
                                    return
                                elif status_code == 2:
                                    pass
                                else:
                                    await msg.edit_text(f"❌ {display_phone}\nStatus: {status_code}")
                                    save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", f"Status {status_code}", None)
                                    update_daily_stats(user.id, "FAILED")
                                    return
                
                elif response.status != 200:
                    await msg.edit_text(f"❌ {display_phone}\nAdd failed")
                    save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", f"Error {response.status}")
                    return
    except Exception as e:
        print(f"   ⚠️ Add error: {e}")
        await msg.edit_text(f"❌ {display_phone}\nError adding")
        return
    
    await asyncio.sleep(3)
    
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
                            await msg.edit_text(f"✅ {display_phone} 🟢 SUCCESS")
                            save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "SUCCESS", "Verified", None)
                            update_daily_stats(user.id, "SUCCESS")
                            await context.bot.send_message(ADMIN_ID, f"✅ SUCCESS!\n👤 {user.full_name}\n📞 {display_phone}")
                            return
                        
                        if status_code == 4:
                            await msg.edit_text(f"❌ {display_phone}\nNot Registered")
                            save_to_sheet(user.id, user.username, user.full_name, phone, api_cc, country, "FAILED", "Not Registered", None)
                            update_daily_stats(user.id, "FAILED")
                            return
    except:
        pass
    
    active_numbers[phone] = {
        'user_id': user.id,
        'api_cc': api_cc,
        'display_cc': display_cc,
        'phone': phone,
        'username': user.username,
        'full_name': user.full_name,
        'country': country,
        'message_id': msg.message_id,
        'chat_id': update.message.chat_id,
        'token': token,
        'otp_submitted': False,
        'otp_code': None
    }
    
    await msg.edit_text(f"🟡 {display_phone} IN PROGRESS")
    
    asyncio.create_task(track_number_status(
        context, update.message.chat_id, msg.message_id,
        phone, api_cc, display_cc, user.id, user.username, user.full_name, country, token
    ))

async def delete_number_from_api(cc, phone, token, status_code):
    if status_code == 1:
        print(f"   🛡️ LAYER 1 PROTECTION: +{cc} {phone} is SUCCESS, will NOT delete")
        return False
    
    config = COUNTRY_APIS.get(cc)
    if not config:
        return False
    
    try:
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
                            print(f"   🛡️ LAYER 2 PROTECTION: Record {record_id} is SUCCESS")
                            return False
                        
                        if record_id and record_id > 0:
                            delete_url = f"{config['base_url']}/z-number-base/deleteNum/{record_id}"
                            async with session.delete(delete_url, headers=headers, timeout=10) as del_response:
                                if del_response.status == 200:
                                    print(f"   🗑️ Deleted: +{cc} {phone} (Status: {status_code})")
                                    return True
                                else:
                                    print(f"   ❌ Delete failed: {del_response.status}")
                                    return False
        return False
    except Exception as e:
        print(f"   ⚠️ Delete error: {e}")
        return False

# ==================== MENU COMMAND HANDLERS ====================

async def menu_keyboard(update: Update, context: CallbackContext):
    """Send the menu keyboard (only text buttons, no inline)"""
    user = update.effective_user
    
    keyboard = [
        [KeyboardButton("[Statistics]")],
        [KeyboardButton("[Check Balance]")],
        [KeyboardButton("[ws price list]")],
        [KeyboardButton("[Support]")],
        [KeyboardButton("[payment proof]")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "📱 *WhatsApp Registration Bot Menu*\n\nSelect an option from the keyboard below 👇",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_menu_buttons(update: Update, context: CallbackContext):
    """Handle menu button presses"""
    user = update.effective_user
    text = update.message.text.strip()
    
    if text == "📊 Statistics":
        await show_statistics(update, context, user)
    elif text == "💰 Check Balance":
        await show_balance(update, context, user)
    elif text == "🌍 Price List":
        await show_price_list(update, context, user)
    elif text == "📥 Download Data":
        await download_my_sheet(update, context)
    elif text == "🆘 Support":
        await show_support(update, context, user)
    elif text == "📸 Payment Proof":
        await show_payment_proof(update, context, user)
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
            if len(all_users_stats) > 15:
                stats_text += f"\n... and {len(all_users_stats) - 15} more users"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    else:
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
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    
    check_and_reset_daily()
    
    if uid in user_balances and user_balances[uid].get("last_reset") == today:
        balance = user_balances[uid].get("balance", 0)
        history = user_balances[uid].get("history", [])
        
        today_history = [h for h in history if h.get("date", "").startswith(today)]
        
        balance_text = f"💰 *Your Balance*\n\n"
        balance_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        balance_text += f"🏦 Total Balance: *${balance:.2f}*\n"
        balance_text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if today_history:
            balance_text += "*Today's Earnings:*\n"
            for h in today_history[-10:]:
                country_name = COUNTRY_RATES.get(h.get("cc", ""), {}).get("country", "Unknown")
                balance_text += f"• +${h['amount']:.2f} ({country_name})\n"
        
        if balance == 0:
            balance_text += "\n💡 Complete OTP verification to earn!\nEach country has different rates."
    else:
        balance_text = f"💰 *Your Balance*\n\n"
        balance_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        balance_text += f"🏦 Total Balance: *$0.00*\n"
        balance_text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        balance_text += "\n💡 Complete OTP verification to earn!\nEach country has different rates."
    
    await update.message.reply_text(balance_text, parse_mode='Markdown')

async def show_price_list(update: Update, context: CallbackContext, user):
    is_admin = (user.id == ADMIN_ID)
    
    sorted_rates = sorted(COUNTRY_RATES.items(), key=lambda x: x[1]["rate"], reverse=True)
    
    price_text = f"🌍 *WhatsApp Service Price List*\n\n"
    price_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    price_text += f"🇨🇨 *Country*                *Rate per OTP*\n"
    price_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for cc, data in sorted_rates:
        flag = data["flag"]
        country = data["country"]
        rate = data["rate"]
        price_text += f"{flag} {country:<20} 💵 ${rate:.2f}\n"
    
    price_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    price_text += f"💡 *How it works:*\n"
    price_text += f"1️⃣ Send phone number with country code\n"
    price_text += f"2️⃣ Receive OTP on WhatsApp\n"
    price_text += f"3️⃣ Send OTP to bot\n"
    price_text += f"4️⃣ Earn the listed rate!\n\n"
    price_text += f"⚠️ Earnings only count after *OTP verification*"
    
    if is_admin:
        price_text += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        price_text += f"👑 *Admin Commands:*\n"
        price_text += f"• `/addrate cc amount` - Add/Update rate\n"
        price_text += f"• `/removerate cc` - Remove country\n"
        price_text += f"• `/listrates` - Show all rates\n"
        price_text += f"• `/saverates` - Save rates to sheet"
    
    await update.message.reply_text(price_text, parse_mode='Markdown')

async def show_support(update: Update, context: CallbackContext, user):
    support_text = f"🆘 *Support Information*\n\n"
    support_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    support_text += f"📢 *Channel:* @CashxByte\n"
    support_text += f"👑 *Admin ID:* `{ADMIN_ID}`\n"
    support_text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    support_text += f"💬 *For support:*\n"
    support_text += f"• Join our channel for updates\n"
    support_text += f"• Contact admin for issues\n"
    support_text += f"• Report bugs to admin\n\n"
    support_text += f"⏰ *Reset Time:* Daily 4 PM (BD Time)\n"
    support_text += f"• Statistics reset\n"
    support_text += f"• Balance reset"
    
    await update.message.reply_text(support_text, parse_mode='Markdown')

async def show_payment_proof(update: Update, context: CallbackContext, user):
    payment_text = f"📸 *Payment Proof*\n\n"
    payment_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    payment_text += f"💰 *Payment Information*\n\n"
    payment_text += f"• Minimum withdrawal: $10\n"
    payment_text += f"• Payment method: USDT (TRC20)\n"
    payment_text += f"• Processing time: 24-48 hours\n\n"
    payment_text += f"📢 *Channel:* @CashxByte\n"
    payment_text += f"👑 *Admin:* Contact for payment requests\n\n"
    payment_text += f"📸 *Payment proofs are posted in channel*"
    
    await update.message.reply_text(payment_text, parse_mode='Markdown')

# ==================== ADMIN COMMANDS FOR RATE MANAGEMENT ====================

async def add_rate(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 *Usage:* `/addrate cc amount`\n\n"
            "Example:\n"
            "• `/addrate 880 0.15` - Set Bangladesh rate to $0.15\n"
            "• `/addrate 966 0.45` - Set Saudi Arabia rate to $0.45\n\n"
            "Use `/listrates` to see all current rates",
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
            flag = "🌍"
            COUNTRY_RATES[cc] = {
                "country": country_name,
                "rate": amount,
                "flag": flag,
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
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 *Usage:* `/removerate cc`\n\n"
            "Example:\n"
            "• `/removerate 880` - Remove Bangladesh from rate list\n\n"
            "Use `/listrates` to see all current rates",
            parse_mode='Markdown'
        )
        return
    
    cc = context.args[0]
    
    if cc in COUNTRY_RATES:
        country_name = COUNTRY_RATES[cc]["country"]
        del COUNTRY_RATES[cc]
        await update.message.reply_text(
            f"✅ Rate removed!\n\n"
            f"🇨🇨 {country_name} removed from price list"
        )
        save_rate_to_sheet()
    else:
        await update.message.reply_text(f"❌ Country code `{cc}` not found in rate list!", parse_mode='Markdown')

async def list_rates(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not COUNTRY_RATES:
        await update.message.reply_text("No rates configured yet. Use /addrate to add countries.")
        return
    
    sorted_rates = sorted(COUNTRY_RATES.items(), key=lambda x: x[1]["rate"], reverse=True)
    
    rate_text = "📊 *Current Rates (Admin View)*\n\n"
    rate_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    rate_text += "🇨🇨 *Country*        *CC*    *Rate*\n"
    rate_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for cc, data in sorted_rates:
        flag = data["flag"]
        country = data["country"][:15]
        rate = data["rate"]
        rate_text += f"{flag} {country:<15} `{cc:<4}` 💵 ${rate:.2f}\n"
    
    rate_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    rate_text += f"📊 Total countries: *{len(COUNTRY_RATES)}*"
    
    await update.message.reply_text(rate_text, parse_mode='Markdown')

async def save_rates(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    save_rate_to_sheet()
    await update.message.reply_text("✅ Rates saved to Google Sheet!")

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
                print(f"   ✅ Detected: {COUNTRY_APIS[cc]['country']} (CC: {cc})")
                return cc, phone, COUNTRY_APIS[cc]['display_cc']
    
    if cleaned.startswith('1') and len(cleaned) == 11:
        print(f"   ✅ Detected: Canada (CC: 11)")
        return "11", cleaned[1:], "1"
    
    if cleaned.startswith('964') and len(cleaned) >= 13:
        print(f"   ✅ Detected: Iraq (CC: 964)")
        return "964", cleaned[3:], "964"
    
    if cleaned.startswith('880') and len(cleaned) >= 13:
        print(f"   ✅ Detected: Bangladesh (CC: 880)")
        return "880", cleaned[3:], "880"
    
    print(f"   ❌ No match for: {cleaned[:20]}...")
    return None, None, None

# ==================== DOWNLOAD SHEET FUNCTION ====================
# ==================== DOWNLOAD SHEET FUNCTION (FIXED) ====================

async def my_sheet_command(update: Update, context: CallbackContext):
    """Send Google Sheet link to user"""
    user = update.effective_user
    
    # Create a simple link without Markdown
    sheet_url = "https://script.google.com/macros/s/AKfycbwxrVX_8zbCkzsKwhx7u5OX9CUp2Y7RelJ_srzqp0CxrEmMMzG8xy9kvmSVmNFG4Zh_7A/edit"
    
    message = (
        f"🔗 YOUR GOOGLE SHEET LINK\n\n"
        f"User ID: {user.id}\n\n"
        f"Click this link to view your data:\n{sheet_url}\n\n"
        f"NOTE: Search for your User ID in the 'All_Submissions' sheet or find your personal sheet named 'User_{user.id}'\n\n"
        f"You can also use these commands:\n"
        f"/mystats - Download statistics\n"
        f"/mybalance - Download balance\n"
        f"/myhistory - Download full history"
    )
    
    await update.message.reply_text(message)

async def my_stats_command(update: Update, context: CallbackContext):
    """Generate CSV with user's statistics"""
    user = update.effective_user
    user_id = str(user.id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    filename = f"user_stats_{user.id}_{today}.txt"
    
    # Create content without special characters
    content = []
    content.append("=" * 50)
    content.append("WHATSAPP REGISTRATION BOT - USER STATISTICS")
    content.append("=" * 50)
    content.append(f"Export Date: {datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"User ID: {user.id}")
    content.append(f"Username: {user.username or 'N/A'}")
    content.append(f"Full Name: {user.full_name or 'N/A'}")
    content.append("")
    content.append("=" * 50)
    content.append("DAILY STATISTICS")
    content.append("=" * 50)
    content.append("Date | Total | OTP Verified | Success | Failed | Earning USD | Earning BDT")
    content.append("-" * 70)
    
    total_submissions = 0
    total_otp = 0
    total_earnings = 0
    
    if user_id in daily_stats:
        for date, stats in sorted(daily_stats[user_id].items()):
            total = stats.get("total", 0)
            otp_verified = stats.get("otp_verified", 0)
            success = stats.get("success", 0)
            failed = stats.get("failed", 0)
            
            earning_usd = 0
            if user_id in user_balances:
                for entry in user_balances[user_id].get("history", []):
                    if entry.get("date", "").startswith(date):
                        earning_usd += entry.get("amount", 0)
            
            earning_bdt = earning_usd * 120
            total_submissions += total
            total_otp += otp_verified
            total_earnings += earning_usd
            
            content.append(f"{date} | {total} | {otp_verified} | {success} | {failed} | {earning_usd:.2f} USD | {earning_bdt:.2f} BDT")
    
    content.append("")
    content.append("=" * 50)
    content.append("SUMMARY")
    content.append("=" * 50)
    content.append(f"Total Submissions: {total_submissions}")
    content.append(f"Total OTP Verified: {total_otp}")
    content.append(f"Total Earnings: {total_earnings:.2f} USD / {total_earnings * 120:.2f} BDT")
    content.append("")
    content.append("=" * 50)
    content.append("END OF REPORT")
    
    text_content = "\n".join(content)
    
    try:
        await context.bot.send_document(
            chat_id=user.id,
            document=('utf-8', text_content.encode('utf-8')),
            filename=filename,
            caption=f"📊 Your Statistics Report"
        )
    except Exception as e:
        await update.message.reply_text(f"Error sending file. Sending as text instead...")
        # Split into multiple messages if too long
        for i in range(0, len(text_content), 4000):
            await update.message.reply_text(text_content[i:i+4000])

async def my_balance_command(update: Update, context: CallbackContext):
    """Generate CSV with user's balance history"""
    user = update.effective_user
    user_id = str(user.id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    filename = f"user_balance_{user.id}_{today}.txt"
    
    content = []
    content.append("=" * 50)
    content.append("WHATSAPP REGISTRATION BOT - BALANCE HISTORY")
    content.append("=" * 50)
    content.append(f"Export Date: {datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"User ID: {user.id}")
    content.append(f"Username: {user.username or 'N/A'}")
    content.append("")
    content.append("=" * 50)
    content.append("EARNINGS HISTORY")
    content.append("=" * 50)
    content.append("Date & Time | Country | Amount USD | Amount BDT")
    content.append("-" * 60)
    
    total_balance = 0
    
    if user_id in user_balances:
        history = user_balances[user_id].get("history", [])
        total_balance = user_balances[user_id].get("balance", 0)
        
        for entry in history:
            date_time = entry.get("date", "")
            cc = entry.get("cc", "")
            country = COUNTRY_RATES.get(cc, {}).get("country", "Unknown")
            amount_usd = entry.get("amount", 0)
            amount_bdt = amount_usd * 120
            
            content.append(f"{date_time} | {country} | {amount_usd:.2f} USD | {amount_bdt:.2f} BDT")
    
    content.append("")
    content.append("=" * 50)
    content.append("SUMMARY")
    content.append("=" * 50)
    content.append(f"Total Balance: {total_balance:.2f} USD / {total_balance * 120:.2f} BDT")
    content.append("")
    content.append("=" * 50)
    content.append("END OF REPORT")
    
    text_content = "\n".join(content)
    
    try:
        await context.bot.send_document(
            chat_id=user.id,
            document=('utf-8', text_content.encode('utf-8')),
            filename=filename,
            caption=f"💰 Your Balance History"
        )
    except Exception as e:
        await update.message.reply_text(f"Error sending file. Sending as text instead...")
        for i in range(0, len(text_content), 4000):
            await update.message.reply_text(text_content[i:i+4000])

async def my_history_command(update: Update, context: CallbackContext):
    """Generate full history text file"""
    user = update.effective_user
    user_id = str(user.id)
    today = datetime.now(bd_tz).strftime('%Y-%m-%d')
    filename = f"user_full_history_{user.id}_{today}.txt"
    
    content = []
    content.append("=" * 60)
    content.append("WHATSAPP REGISTRATION BOT - FULL HISTORY")
    content.append("=" * 60)
    content.append(f"Export Date: {datetime.now(bd_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"User ID: {user.id}")
    content.append(f"Username: {user.username or 'N/A'}")
    content.append(f"Full Name: {user.full_name or 'N/A'}")
    content.append("")
    
    # Statistics Summary
    content.append("=" * 50)
    content.append("STATISTICS SUMMARY")
    content.append("=" * 50)
    
    if user_id in daily_stats:
        for date, stats in sorted(daily_stats[user_id].items()):
            total = stats.get("total", 0)
            otp_verified = stats.get("otp_verified", 0)
            content.append(f"{date}: Total={total}, OTP Verified={otp_verified}")
    else:
        content.append("No statistics data found")
    
    # Balance Summary
    content.append("")
    content.append("=" * 50)
    content.append("BALANCE SUMMARY")
    content.append("=" * 50)
    
    if user_id in user_balances:
        total_balance = user_balances[user_id].get("balance", 0)
        content.append(f"Total Balance: {total_balance:.2f} USD")
        content.append("")
        content.append("Recent Earnings:")
        
        history = user_balances[user_id].get("history", [])
        if history:
            for entry in history[-10:]:
                date_time = entry.get("date", "")
                cc = entry.get("cc", "")
                country = COUNTRY_RATES.get(cc, {}).get("country", "Unknown")
                amount_usd = entry.get("amount", 0)
                content.append(f"  - {date_time}: {country} +{amount_usd:.2f} USD")
        else:
            content.append("  No earnings yet")
    else:
        content.append("No balance data found")
    
    content.append("")
    content.append("=" * 50)
    content.append("NOTE")
    content.append("=" * 50)
    content.append("For complete detailed history with OTP codes,")
    content.append("use /mysheet to get your Google Sheet link.")
    content.append("")
    content.append("=" * 50)
    content.append("END OF REPORT")
    
    text_content = "\n".join(content)
    
    try:
        await context.bot.send_document(
            chat_id=user.id,
            document=('utf-8', text_content.encode('utf-8')),
            filename=filename,
            caption=f"📋 Your Full History Report"
        )
    except Exception as e:
        await update.message.reply_text(f"Error sending file. Sending as text instead...")
        for i in range(0, len(text_content), 4000):
            await update.message.reply_text(text_content[i:i+4000])

async def download_my_sheet(update: Update, context: CallbackContext):
    """User can download their personal sheet data"""
    user = update.effective_user
    
    # Check channel join first
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/CashxByte")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"Please join {REQUIRED_CHANNEL} first to download your data!", reply_markup=reply_markup)
            return
    except:
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/CashxByte")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Please join {REQUIRED_CHANNEL} first to download your data!", reply_markup=reply_markup)
        return
    
    # Send download options as text with commands
    message = (
        f"📥 DOWNLOAD YOUR DATA\n\n"
        f"User: {user.first_name}\n"
        f"ID: {user.id}\n\n"
        f"Use these commands to download:\n\n"
        f"/mystats - Download my statistics\n"
        f"/mybalance - Download my balance history\n"
        f"/myhistory - Download full history\n"
        f"/mysheet - Get Google Sheet link"
    )
    
    await update.message.reply_text(message)

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
    
    # Menu keyboard
    keyboard = [
    ["📊 Statistics", "💰 Check Balance"],
    ["🌍 Price List", "📥 Download Data"],
    ["🆘 Support", "📸 Payment Proof"]
]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    # Supported countries list
    countries_list = []
    for cc, cfg in COUNTRY_APIS.items():
        if cc in COUNTRY_RATES:
            rate = COUNTRY_RATES[cc]["rate"]
            countries_list.append(f"• {COUNTRY_RATES[cc]['flag']} +{cfg['display_cc']} - {cfg['country']} (${rate:.2f})")
        else:
            countries_list.append(f"• +{cfg['display_cc']} - {cfg['country']}")
    
    countries_text = "\n".join(countries_list[:20])
    if len(countries_list) > 20:
        countries_text += f"\n... and {len(countries_list)-20} more countries"
    
    welcome_msg = (
        f"👋 Welcome {user.first_name}!\n\n"
        f"🌍 *WhatsApp Registration Bot*\n\n"
        f"📱 Send any phone number with country code:\n\n"
        f"{countries_text}\n\n"
        f"💡 Examples:\n"
        f"• `+9647803260789` (Iraq)\n"
        f"• `+8801712345678` (Bangladesh)\n\n"
        f"⚡ Bot auto-detects country\n"
        f"⏱️ Max 3 minutes tracking\n"
        f"💰 Earnings only for OTP verification!\n\n"
        f"📅 *Resets daily at 4 PM BD time*"
    )
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text.strip()
    
    if text.startswith('/'):
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
    
    asyncio.create_task(process_number(update, context, user, api_cc, phone, display_cc, country, display_phone, msg))

async def handle_otp(update: Update, context: CallbackContext):
    user = update.effective_user
    otp = update.message.text.strip()
    
    phone = None
    data = None
    for p, d in active_numbers.items():
        if d['user_id'] == user.id:
            phone = p
            data = d
            break
    
    if not phone:
        await update.message.reply_text("❌ No active number! Send a new number first.")
        return
    
    display = f"+{data['display_cc']} {phone}"
    
    if not re.match(r'^\d{6}$', otp):
        await update.message.reply_text("❌ Send 6-digit OTP code!")
        return
    
    print(f"\n🔑 OTP {otp} for {display}")
    
    # Mark OTP as submitted
    if phone in active_numbers:
        active_numbers[phone]['otp_submitted'] = True
        active_numbers[phone]['otp_code'] = otp
    
    # No message sent here - just process silently
    
    config = COUNTRY_APIS.get(data['api_cc'])
    token = data.get('token')
    
    if not token:
        token = await login_api(data['api_cc'])
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Admin-Token": token}
            url = f"{config['base_url']}/z-number-base/allNum/uploadCode?cc={data['api_cc']}&phoneNum={phone}&code={otp}"
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    resp_data = await response.json()
                    if resp_data.get('code') == 200:
                        # OTP accepted - no message, tracking will handle
                        pass
                    else:
                        await update.message.reply_text(f"❌ Wrong OTP! Try again.")
                        save_to_sheet(
                            data['user_id'], data['username'], data['full_name'],
                            phone, data['api_cc'], data['country'],
                            "FAILED", f"Wrong OTP", otp
                        )
                        update_daily_stats(data['user_id'], "FAILED")
                        
                        if phone in active_numbers:
                            del active_numbers[phone]
                else:
                    await update.message.reply_text(f"❌ OTP submission failed! Try again.")
                    if phone in active_numbers:
                        del active_numbers[phone]
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        if phone in active_numbers:
            del active_numbers[phone]

async def stats_command(update: Update, context: CallbackContext):
    user = update.effective_user
    await show_statistics(update, context, user)

async def balance_command(update: Update, context: CallbackContext):
    user = update.effective_user
    await show_balance(update, context, user)

async def price_list_command(update: Update, context: CallbackContext):
    user = update.effective_user
    await show_price_list(update, context, user)

# ==================== MAIN ====================
import threading
import asyncio
from fastapi import FastAPI
import uvicorn

# ==================== FASTAPI SETUP ====================
app_fastapi = FastAPI()

@app_fastapi.get("/")
async def root():
    return {"status": "active", "message": "Bot is running"}

@app_fastapi.get("/health")
async def health():
    return {"status": "healthy"}

def run_fastapi():
    """Run FastAPI on configured port"""
    uvicorn.run(app_fastapi, host="0.0.0.0", port=PORT, access_log=False)

# ==================== MAIN FUNCTION ====================
def main():
    # Start FastAPI in background thread
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
    
    # Add to main() function
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("price", price_list_command))
    app.add_handler(CommandHandler("menu", menu_keyboard))

    # Download commands
    app.add_handler(CommandHandler("mystats", my_stats_command))
    app.add_handler(CommandHandler("mybalance", my_balance_command))
    app.add_handler(CommandHandler("myhistory", my_history_command))
    app.add_handler(CommandHandler("mysheet", my_sheet_command))
    app.add_handler(CommandHandler("download", download_my_sheet))

    # Admin commands
    app.add_handler(CommandHandler("addrate", add_rate))
    app.add_handler(CommandHandler("removerate", remove_rate))
    app.add_handler(CommandHandler("listrates", list_rates))
    app.add_handler(CommandHandler("saverates", save_rates))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
    
    # Message handler - checks for menu buttons first
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
    
    print("\n✅ BOT RUNNING!")
    print("⏱️ Max tracking: 3 minutes per number")
    print("💰 Earnings only for OTP verified")
    print("📊 Statistics reset daily at 4 PM BD time")
    print("🌍 Dynamic country rates with admin commands")
    print("📱 Menu keyboard with 5 buttons")
    print(f"🚀 FastAPI on port: {PORT}")
    print("="*60 + "\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()

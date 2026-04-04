import os
import asyncio
import threading
import requests
import time
import json
import re
import logging
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from datetime import datetime, timedelta
from telegram.error import BadRequest
from fastapi import FastAPI
import uvicorn
import random
from typing import Dict, List, Optional, Tuple
import jwt

# Configure logging to focus on errors only
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "6329569356:AAEfPA03ZjZAByKhGhNUc8n_x5EATZpHDGw")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "5624278091"))
BASE_URL = os.environ.get("BASE_URL", "")

# Render-compatible port
RENDER_PORT = int(os.environ.get("PORT", 10000))

# Add these constants after your existing constants (around line 30-40)
# Payment group settings
PAYMENT_GROUP_ID = os.environ.get("PAYMENT_GROUP_ID", "-1003768366485")  # Replace with your group ID
PAYMENT_GROUP_LINK = os.environ.get("PAYMENT_GROUP_LINK", "https://t.me/livepaymentupdate")

# Fake payment settings
FAKE_PAYMENT_GROUP_ID = os.environ.get("FAKE_PAYMENT_GROUP_ID", PAYMENT_GROUP_ID)  # Can be same or different group
FAKE_PAYMENT_ENABLED = os.environ.get("FAKE_PAYMENT_ENABLED", "True").lower() == "true"

# Add these constants after your existing constants
REQUIRED_CHANNEL = "@CashxByte"  # Main channel
REQUIRED_PAYMENT_GROUP = os.environ.get("REQUIRED_PAYMENT_GROUP", "@livepaymentupdate")  # Payment group username
CHANNEL_INVITE_LINK = "https://t.me/CashxByte"  # Channel invite link
PAYMENT_GROUP_INVITE_LINK = os.environ.get("PAYMENT_GROUP_INVITE_LINK", "https://t.me/livepaymentupdate")  # Group invite link

# Random user data for fake payments
FAKE_USERNAMES = [
    "Rakib_Hasan", "Sakib_Khan", "Rafiq_Islam", "Sohel_Rana", "Nayeem_Chy",
    "Fahim_Ahmed", "Ridoy_Hossain", "Tanvir_Haque", "Saif_Uddin", "Shanto_Chy",
    "Mahmud_Hasan", "Habib_Rahman", "Shahin_Ahmed", "Rashed_Khan", "Mamun_Mia",
    "Asif_Iqbal", "Rony_Chy", "Shakil_Hossain", "Imran_Hasan", "Nurul_Islam"
]

FAKE_FIRST_NAMES = [
    "Rakib", "Sakib", "Rafiq", "Sohel", "Nayeem", "Fahim", "Ridoy", 
    "Tanvir", "Saif", "Shanto", "Mahmud", "Habib", "Shahin", "Rashed",
    "Mamun", "Asif", "Rony", "Shakil", "Imran", "Nurul"
]

FAKE_LAST_NAMES = [
    "Hasan", "Khan", "Islam", "Rana", "Chy", "Ahmed", "Hossain", "Haque",
    "Uddin", "Rahman", "Mia", "Iqbal", "Chowdhury", "Begum", "Ali", "Miah"
]

FAKE_COUNTRIES = [
    "Bangladesh", "India", "Pakistan", "USA", "Canada", "UK", "UAE", 
    "Saudi Arabia", "Malaysia", "Singapore", "Thailand", "Indonesia"
]


# File paths with Render.com compatibility
if 'RENDER' in os.environ:
    ACCOUNTS_FILE = "/tmp/accounts.json"
    STATS_FILE = "/tmp/stats.json"
    OTP_STATS_FILE = "/tmp/otp_stats.json"
    SETTINGS_FILE = "/tmp/settings.json"
else:
    ACCOUNTS_FILE = "accounts.json"
    STATS_FILE = "stats.json"
    OTP_STATS_FILE = "otp_stats.json"
    SETTINGS_FILE = "settings.json"

USD_TO_BDT = 125  # Exchange rate
MAX_PER_ACCOUNT = 10

# Status map
status_map = {
    0: "⚠️ Process Failed",
    1: "🟢 Success", 
    2: "🔵 In Progress",
    3: "⚠️ Try Again Later",
    4: "🚫 Not Register",
    7: "🚫 Ban Number",
    5: "⏳️ Recent Request",
    6: "🔴 Wrong OTP",
    8: "🟠 Limited",
    9: "🔶 Restricted", 
    10: "🟣 VIP Number",
    11: "⚠️ Add Again",
    12: "🟤 Temp Blocked",
    13: "⚠️ Bad Number",
    14: "🌀 Processing",
    15: "📞 Call Required",
    -1: "❌ Token Expired",
    -2: "❌ API Error",
    -3: "❌ No Data Found",
    16: "🚫 Already Exists"
}

# FastAPI for /ping endpoint
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "🤖 Python Number Checker Bot is Running!", "status": "active", "timestamp": datetime.now().isoformat()}

@app.get("/ping")
async def ping():
    return {"message": "Bot is alive!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "bot": "online"}

# Enhanced keep-alive system for Render
async def keep_alive_enhanced():
    keep_alive_urls = [
        "https://wsotpall-wdpk.onrender.com",
        "https://wschecker-f1ug.onrender.com"
    ]
    
    while True:
        try:
            for url in keep_alive_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            print(f"🔄 Keep-alive ping to {url}: Status {response.status}")
                            await asyncio.sleep(2)
                except Exception as e:
                    print(f"⚠️ Keep-alive ping failed for {url}: {e}")
            
            await asyncio.sleep(3 * 60)
            
        except Exception as e:
            print(f"❌ Keep-alive system error: {e}")
            await asyncio.sleep(3 * 60)

async def random_ping():
    while True:
        try:
            random_time = random.randint(2 * 60, 5 * 60)
            await asyncio.sleep(random_time)
            
            async with aiohttp.ClientSession() as session:
                async with session.get("https://webck-9utn.onrender.com", timeout=10) as response:
                    print(f"🎲 Random ping sent: Status {response.status}")
                    
        except Exception as e:
            print(f"⚠️ Random ping failed: {e}")

async def immediate_ping():
    await asyncio.sleep(30)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://webck-9utn.onrender.com", timeout=10) as response:
                print(f"🚀 Immediate startup ping: Status {response.status}")
    except Exception as e:
        print(f"⚠️ Immediate ping failed: {e}")

# tracking.json ফাইল অপারেশন
def load_tracking():
    try:
        with open("tracking.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "today_added" not in data or not isinstance(data["today_added"], dict):
                data["today_added"] = {}
            if "yesterday_added" not in data or not isinstance(data["yesterday_added"], dict):
                data["yesterday_added"] = {}
            if "today_success" not in data or not isinstance(data["today_success"], dict):
                data["today_success"] = {}
            if "yesterday_success" not in data or not isinstance(data["yesterday_success"], dict):
                data["yesterday_success"] = {}
            if "today_success_counts" not in data or not isinstance(data["today_success_counts"], dict):
                data["today_success_counts"] = {}
            if "daily_stats" not in data or not isinstance(data["daily_stats"], dict):
                data["daily_stats"] = {}
            return data
    except:
        return {
            "added_numbers": {},
            "success_numbers": {},
            "today_added": {},
            "yesterday_added": {},
            "today_success": {},
            "yesterday_success": {},
            "today_success_counts": {},
            "daily_stats": {},
            "last_reset": datetime.now().isoformat()
        }

def save_tracking(tracking):
    try:
        with open("tracking.json", 'w', encoding='utf-8') as f:
            json.dump(tracking, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error saving tracking: {e}")

async def reset_daily_stats(context: CallbackContext):
    stats = load_stats()
    otp_stats = load_otp_stats()
    tracking = load_tracking()
    
    today_date = datetime.now().date().isoformat()
    
    # Save yesterday's data
    tracking["yesterday_added"] = tracking.get("today_added", {}).copy()
    
    if "daily_stats" not in tracking:
        tracking["daily_stats"] = {}
    
    today_success_by_user = tracking.get("today_success_counts", {}).copy()
    tracking["daily_stats"][today_date] = today_success_by_user
    
    # Reset today's data
    tracking["today_added"] = {}
    tracking["yesterday_success"] = tracking.get("today_success_counts", {}).copy()
    tracking["today_success"] = {}
    tracking["today_success_counts"] = {}
    tracking["last_reset"] = datetime.now().isoformat()
    
    # Reset stats
    stats["yesterday_checked"] = stats["today_checked"]
    stats["today_checked"] = 0
    stats["yesterday_deleted"] = stats["today_deleted"]
    stats["today_deleted"] = 0
    
    # Reset OTP stats
    otp_stats["yesterday_success"] = otp_stats["today_success"]
    otp_stats["today_success"] = 0
    
    for user_id_str in otp_stats.get("user_stats", {}):
        otp_stats["user_stats"][user_id_str]["yesterday_success"] = otp_stats["user_stats"][user_id_str].get("today_success", 0)
        otp_stats["user_stats"][user_id_str]["today_success"] = 0
    
    save_stats(stats)
    save_otp_stats(otp_stats)
    save_tracking(tracking)
    
    # Send reset notification to admin
    reset_message = "🔄 Daily Statistics Reset 🔄\n\n"
    reset_message += f"📅 Date: {datetime.now().strftime('%d %B %Y')}\n"
    reset_message += f"⏰ Reset Time: 4:00 PM (Bangladesh Time)\n\n"
    reset_message += "📊 Yesterday's Final Stats:\n"
    reset_message += f"• 🔵 In Progress: {sum(tracking['yesterday_added'].values())}\n"
    reset_message += f"• 🟢 Success: {sum(tracking['yesterday_success'].values())}\n"
    reset_message += f"• ✅ OTP Success: {otp_stats['yesterday_success']}\n"
    reset_message += f"• 📊 Checked: {stats['yesterday_checked']}\n\n"
    reset_message += "✅ All statistics have been reset for the new day!"
    
    try:
        await context.bot.send_message(ADMIN_ID, reset_message, parse_mode='none')
    except:
        pass
    
    print(f"✅ Daily tracking reset (BD Time 4PM) - Date: {today_date}")
    
# Enhanced file operations with error handling
def load_accounts():
    try:
        possible_paths = [
            ACCOUNTS_FILE,
            "accounts.json",
            "/tmp/accounts.json",
            "./accounts.json"
        ]
        
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"✅ Loaded accounts from {file_path}")
                        return data
            except Exception as e:
                print(f"❌ Error loading from {file_path}: {e}")
                continue
        
        print("ℹ️ No accounts file found, starting fresh")
        initial_data = {
            str(ADMIN_ID): {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        }
        save_accounts(initial_data)
        return initial_data
        
    except Exception as e:
        print(f"❌ Critical error loading accounts: {e}")
        initial_data = {
            str(ADMIN_ID): {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        }
        return initial_data

def save_accounts(accounts):
    try:
        possible_paths = [
            ACCOUNTS_FILE,
            "accounts.json", 
            "/tmp/accounts.json"
        ]
        
        success = False
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(accounts, f, indent=4, ensure_ascii=False)
                print(f"✅ Saved accounts to {file_path}")
                success = True
                break
            except Exception as e:
                print(f"❌ Error saving to {file_path}: {e}")
                continue
        
        if not success:
            print("❌ Failed to save accounts to any location")
            
    except Exception as e:
        print(f"❌ Critical error saving accounts: {e}")

def load_stats():
    try:
        possible_paths = [STATS_FILE, "stats.json", "/tmp/stats.json", "./stats.json"]
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            # Ensure all required keys exist
                            required_keys = [
                                "total_checked", "total_deleted", 
                                "today_checked", "today_deleted",
                                "yesterday_checked", "yesterday_deleted",
                                "last_reset"
                            ]
                            
                            for key in required_keys:
                                if key not in data:
                                    if key in ["total_checked", "today_checked", "yesterday_checked"]:
                                        data[key] = 0
                                    elif key in ["total_deleted", "today_deleted", "yesterday_deleted"]:
                                        data[key] = 0
                                    elif key == "last_reset":
                                        data[key] = datetime.now().isoformat()
                            
                            return data
                        else:
                            print(f"⚠️ Stats file contains {type(data)}, returning default")
                            return create_default_stats()
            except Exception as e:
                print(f"❌ Error loading from {file_path}: {e}")
                continue
        
        # If no file found, create default
        return create_default_stats()
        
    except Exception as e:
        print(f"❌ Error loading stats: {e}")
        return create_default_stats()

def create_default_stats():
    """Create default stats dictionary with all required keys"""
    return {
        "total_checked": 0, 
        "total_deleted": 0, 
        "today_checked": 0, 
        "today_deleted": 0,
        "yesterday_checked": 0,
        "yesterday_deleted": 0,
        "last_reset": datetime.now().isoformat()
    }

def save_stats(stats):
    try:
        # Ensure all required keys exist before saving
        required_keys = [
            "total_checked", "total_deleted", 
            "today_checked", "today_deleted",
            "yesterday_checked", "yesterday_deleted",
            "last_reset"
        ]
        
        for key in required_keys:
            if key not in stats:
                if key in ["total_checked", "today_checked", "yesterday_checked"]:
                    stats[key] = 0
                elif key in ["total_deleted", "today_deleted", "yesterday_deleted"]:
                    stats[key] = 0
                elif key == "last_reset":
                    stats[key] = datetime.now().isoformat()
        
        possible_paths = [STATS_FILE, "stats.json", "/tmp/stats.json"]
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=4, ensure_ascii=False)
                print(f"✅ Stats saved to {file_path}")
                break
            except Exception as e:
                print(f"❌ Error saving to {file_path}: {e}")
                continue
    except Exception as e:
        print(f"❌ Error saving stats: {e}")

def load_otp_stats():
    try:
        possible_paths = [OTP_STATS_FILE, "otp_stats.json", "/tmp/otp_stats.json", "./otp_stats.json"]
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"✅ Loaded OTP stats from {file_path}")
                        return data
            except Exception as e:
                print(f"❌ Error loading from {file_path}: {e}")
                continue
        return {
            "total_success": 0,
            "today_success": 0,
            "yesterday_success": 0,
            "user_stats": {},
            "last_reset": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error loading OTP stats: {e}")
        return {
            "total_success": 0,
            "today_success": 0,
            "yesterday_success": 0,
            "user_stats": {},
            "last_reset": datetime.now().isoformat()
        }

def save_otp_stats(otp_stats):
    try:
        possible_paths = [OTP_STATS_FILE, "otp_stats.json", "/tmp/otp_stats.json"]
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(otp_stats, f, indent=4, ensure_ascii=False)
                break
            except:
                continue
    except Exception as e:
        print(f"❌ Error saving OTP stats: {e}")

def load_settings():
    try:
        possible_paths = [SETTINGS_FILE, "settings.json", "/tmp/settings.json", "./settings.json"]
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"✅ Loaded settings from {file_path}")
                        return data
            except Exception as e:
                print(f"❌ Error loading from {file_path}: {e}")
                continue
        default_settings = {
            "settlement_rate": 0.10,
            "last_updated": datetime.now().isoformat(),
            "updated_by": ADMIN_ID
        }
        save_settings(default_settings)
        return default_settings
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        default_settings = {
            "settlement_rate": 0.10,
            "last_updated": datetime.now().isoformat(),
            "updated_by": ADMIN_ID
        }
        return default_settings

def save_settings(settings):
    try:
        possible_paths = [SETTINGS_FILE, "settings.json", "/tmp/settings.json"]
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                break
            except:
                continue
    except Exception as e:
        print(f"❌ Error saving settings: {e}")

# Active OTP requests (in-memory only)
active_otp_requests = {}

# Async login - UPDATED VERSION
async def login_api_async(username, password):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"account": username, "password": password, "identity": "Member"}
            
            print(f"🔄 Attempting login for: {username}")
            
            async with session.post(f"{BASE_URL}/user/login", json=payload, timeout=30) as response:
                response_text = await response.text()
                print(f"📥 Response status: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                        
                        if data and isinstance(data, dict):
                            if "data" in data and "token" in data["data"]:
                                token = data["data"]["token"]
                                
                                try:
                                    decoded = jwt.decode(token, options={"verify_signature": False})
                                    api_user_id = decoded.get('id')
                                    nickname = decoded.get('nickname')
                                    
                                    print(f"✅ Login successful for {username}")
                                    print(f"📝 API User ID: {api_user_id}")
                                    print(f"👤 Nickname: {nickname}")
                                    
                                    return token, api_user_id, nickname
                                except Exception as jwt_error:
                                    print(f"⚠️ Could not decode token: {jwt_error}")
                                    return token, None, None
                            else:
                                print(f"❌ Token not found in response for {username}")
                                return None, None, None
                        else:
                            print(f"❌ Invalid response format for {username}")
                            return None, None, None
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error for {username}: {e}")
                        print(f"❌ Raw response: {response_text[:200]}...")
                        return None, None, None
                else:
                    print(f"❌ Login failed: {username} - Status: {response.status}")
                    return None, None, None
    except asyncio.TimeoutError:
        print(f"❌ Login timeout for {username}")
        return None, None, None
    except Exception as e:
        print(f"❌ Login error for {username}: {type(e).__name__}: {e}")
        return None, None, None

def calculate_daily_stats():
    """Calculate daily statistics from tracking data"""
    tracking = load_tracking()
    stats = load_stats()
    
    today_date = datetime.now().date().isoformat()
    
    # Calculate totals
    total_in_progress = 0
    total_success = 0
    
    # Get counts from tracking
    if "today_added" in tracking:
        for user_id, count in tracking["today_added"].items():
            if isinstance(count, (int, float)):
                total_in_progress += count
    
    if "today_success_counts" in tracking:
        for user_id, count in tracking["today_success_counts"].items():
            if isinstance(count, (int, float)):
                total_success += count
    
    # Get active in-progress numbers from active_numbers
    active_in_progress = len(active_numbers)
    
    return {
        "date": today_date,
        "total_in_progress": total_in_progress,
        "active_in_progress": active_in_progress,
        "total_success": total_success,
        "total_checked": stats.get("today_checked", 0),
        "total_deleted": stats.get("today_deleted", 0)
    }

async def show_user_statistics(update: Update, context: CallbackContext):
    """Show individual user statistics"""
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    tracking = load_tracking()
    stats = load_stats()  # This will now work with the fixed function
    otp_stats = load_otp_stats()
    
    today_date = datetime.now().date().isoformat()
    
    # Get user-specific stats with default values
    user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
    user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
    
    # Get OTP stats with default values
    user_otp_stats = otp_stats.get("user_stats", {}).get(user_id_str, {})
    today_otp_success = user_otp_stats.get("today_success", 0)
    yesterday_otp_success = user_otp_stats.get("yesterday_success", 0)
    
    # Get account info
    accounts = load_accounts()
    user_data = accounts.get(user_id_str, {})
    user_accounts = user_data.get("accounts", []) if isinstance(user_data, dict) else []
    active_accounts = account_manager.get_user_active_accounts_count(user_id)
    remaining_checks = account_manager.get_user_remaining_checks(user_id)
    
    message = "📊 Your Daily Statistics 📊\n\n"
    
    message += f"📅 Date: {datetime.now().strftime('%d %B %Y')}\n"
    message += f"⏰ Time: {datetime.now().strftime('%H:%M:%S')} (BD Time)\n"
    message += f"🔄 Next Reset: Today 4:00 PM (BD Time)\n\n"
    
    message += "👤 Account Information:\n"
    message += f"• 📱 Total Accounts: {len(user_accounts)}\n"
    message += f"• ✅ Active Login: {active_accounts}\n"
    message += f"• 🎯 Remaining Add: {remaining_checks}\n\n"
    
    message += "📈 Today's Performance:\n"
    message += f"• 📱Added Numbers: {user_in_progress}\n"
    message += f"• 🟢 Success Counts: {user_success}\n"
    message += f"• ✅ OTP Success: {today_otp_success}\n\n"
    
    
    message += "🔄 Auto Reset: Daily at 4:00 PM (Bangladesh Time)"
    
    await update.message.reply_text(message, parse_mode='none')

async def show_admin_statistics(update: Update, context: CallbackContext):
    """Show admin statistics with all users data"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    processing_msg = await update.message.reply_text("🔄 Generating statistics report...")
    
    tracking = load_tracking()
    stats = load_stats()
    otp_stats = load_otp_stats()
    accounts = load_accounts()
    
    today_date = datetime.now().date().isoformat()
    today_display = datetime.now().strftime('%d %B %Y')
    
    # Calculate totals
    total_in_progress = 0
    total_success = 0
    total_users = 0
    
    # User-wise calculations
    user_stats = []
    
    for user_id_str, user_data in accounts.items():
        if user_id_str == str(ADMIN_ID):
            continue
        
        if isinstance(user_data, dict):
            user_accounts = user_data.get("accounts", [])
        else:
            user_accounts = []
        
        if not user_accounts:
            continue
        
        total_users += 1
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        
        # Get user stats
        user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
        user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
        user_otp_success = otp_stats.get("user_stats", {}).get(user_id_str, {}).get("today_success", 0)
        
        total_in_progress += user_in_progress
        total_success += user_success
        
        user_stats.append({
            'user_id': user_id_str,
            'username': username,
            'in_progress': user_in_progress,
            'success': user_success,
            'otp_success': user_otp_success,
            'accounts': len(user_accounts)
        })
    
    # Sort users by success count (descending)
    user_stats.sort(key=lambda x: x['success'], reverse=True)
    
    # Send summary first
    summary_message = "👑 ADMIN STATISTICS SUMMARY 👑\n\n"
    
    summary_message += f"📅 Date: {today_display}\n"
    summary_message += f"⏰ Time: {datetime.now().strftime('%H:%M:%S')} (BD Time)\n"
    summary_message += f"🔄 Next Reset: Today 4:00 PM (BD Time)\n\n"
    
    summary_message += "📊 TODAY'S OVERVIEW:\n"
    summary_message += f"• 👥 Total Users: {total_users}\n"
    summary_message += f"• 🔵 Total In Progress: {total_in_progress}\n"
    summary_message += f"• 🟢 Total Success: {total_success}\n"
    summary_message += f"• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n"
    summary_message += f"• 📊 Total Checked: {stats.get('today_checked', 0)}\n"
    summary_message += f"• 🗑️ Total Deleted: {stats.get('today_deleted', 0)}\n\n"
    
    summary_message += "📈 YESTERDAY'S SUMMARY:\n"
    summary_message += f"• 🟢 Success Counts: {otp_stats.get('yesterday_success', 0)}\n"
    summary_message += f"• 📊 Checked: {stats.get('yesterday_checked', 0)}\n\n"
    
    summary_message += "📌 Note: In Progress counts all numbers added today.\n"
    summary_message += "Success counts only unique successful numbers.\n"
    
    await processing_msg.edit_text(summary_message, parse_mode='none')
    
    # Send user details in chunks of 10
    users_per_message = 10
    total_chunks = (len(user_stats) + users_per_message - 1) // users_per_message
    
    for chunk_index in range(total_chunks):
        start_idx = chunk_index * users_per_message
        end_idx = min(start_idx + users_per_message, len(user_stats))
        chunk = user_stats[start_idx:end_idx]
        
        details_message = f"📋 USER STATISTICS - PART {chunk_index + 1}/{total_chunks} 📋\n\n"
        details_message += f"📅 Date: {today_display}\n\n"
        
        for i, user in enumerate(chunk, start=start_idx + 1):
            details_message += f"{i}. {user['username']} (ID: {user['user_id']})\n"
            details_message += f"   ├─ 📱 Accounts: {user['accounts']}\n"
            details_message += f"   ├─ 🔵 In Progress: {user['in_progress']}\n"
            details_message += f"   ├─ 🟢 Success: {user['success']}\n"
            details_message += f"   ├─ ✅ OTP Success: {user['otp_success']}\n"
            
            # Calculate success rate
            if user['in_progress'] > 0:
                success_rate = (user['success'] / user['in_progress']) * 100
                details_message += f"   └─ 📈 Success Rate: {success_rate:.1f}%\n"
            else:
                details_message += f"   └─ 📈 Success Rate: 0%\n"
            
            details_message += "\n"
        
        # Add chunk totals
        chunk_in_progress = sum(u['in_progress'] for u in chunk)
        chunk_success = sum(u['success'] for u in chunk)
        
        details_message += f"📊 Chunk {chunk_index + 1} Summary:\n"
        details_message += f"• 👥 Users: {len(chunk)}\n"
        details_message += f"• 🔵 In Progress: {chunk_in_progress}\n"
        details_message += f"• 🟢 Success: {chunk_success}\n"
        
        if chunk_in_progress > 0:
            chunk_success_rate = (chunk_success / chunk_in_progress) * 100
            details_message += f"• 📈 Success Rate: {chunk_success_rate:.1f}%\n"
        
        if chunk_index < total_chunks - 1:
            details_message += "\n⬇️ More users in next message..."
        
        try:
            await context.bot.send_message(
                ADMIN_ID,
                details_message,
                parse_mode='none'
            )
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ Error sending statistics chunk {chunk_index + 1}: {e}")
    
    # Send final totals
    final_message = "🎯 FINAL DAILY SUMMARY 🎯\n\n"
    
    final_message += f"📅 Date: {today_display}\n"
    final_message += f"⏰ Report Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    final_message += "📊 TOTAL STATISTICS:\n"
    final_message += f"• 👥 Total Active Users: {total_users}\n"
    final_message += f"• 🔵 Total In Progress Numbers: {total_in_progress}\n"
    final_message += f"• 🟢 Total Success Counts: {total_success}\n"
    final_message += f"• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n\n"
    
    # Calculate overall success rate
    if total_in_progress > 0:
        overall_success_rate = (total_success / total_in_progress) * 100
        final_message += f"📈 OVERALL SUCCESS RATE: {overall_success_rate:.1f}%\n\n"
    
    # Top performers
    if len(user_stats) >= 3:
        final_message += "🏆 TOP 3 PERFORMERS TODAY:\n"
        for i in range(min(3, len(user_stats))):
            user = user_stats[i]
            final_message += f"{i+1}. {user['username']} - {user['success']} success\n"
        final_message += "\n"
    
    final_message += "🔄 Statistics will reset at 4:00 PM (Bangladesh Time)\n"
    final_message += "✅ Report generation complete!"
    
    await context.bot.send_message(ADMIN_ID, final_message, parse_mode='none')

async def statistics_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # ✅ চ্যানেল মেম্বারশিপ চেক
    if user_id != ADMIN_ID:
        REQUIRED_CHANNEL = "@CashxByte"
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if member.status not in allowed_status:
                await update.message.reply_text("❌ Please join @CashxByte first to use this feature.")
                return
        except:
            await update.message.reply_text("❌ Please join @CashxByte first to use this feature.")
            return
    
    if user_id == ADMIN_ID:
        # Admin sees two buttons: Top Performers and All Statistics
        keyboard = [
            [InlineKeyboardButton("🏆 Top Performers", callback_data="stats_top_performers")],
            [InlineKeyboardButton("📊 All Statistics", callback_data="stats_all")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 Admin Statistics Menu\n\n"
            "Choose what you want to see:",
            reply_markup=reply_markup
        )
    else:
        # Regular users see their own statistics
        await show_user_statistics(update, context)

async def handle_statistics_callback(update: Update, context: CallbackContext):
    """Handle statistics callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "stats_top_performers":
        await show_top_performers(query, context)
    elif data == "stats_all":
        await show_admin_statistics_from_callback(query, context)

async def show_top_performers(query, context):
    """Show only top performers summary - SPLIT VERSION"""
    await query.edit_message_text("🔄 Generating top performers report...")
    
    tracking = load_tracking()
    stats = load_stats()
    otp_stats = load_otp_stats()
    accounts = load_accounts()
    
    today_date = datetime.now().date().isoformat()
    today_display = datetime.now().strftime('%d %B %Y')
    
    # Calculate totals
    total_in_progress = 0
    total_success = 0
    total_users = 0
    
    # User-wise calculations
    user_stats = []
    
    for user_id_str, user_data in accounts.items():
        if user_id_str == str(ADMIN_ID):
            continue
        
        if isinstance(user_data, dict):
            user_accounts = user_data.get("accounts", [])
        else:
            user_accounts = []
        
        if not user_accounts:
            continue
        
        total_users += 1
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        
        # Get user stats
        user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
        user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
        user_otp_success = otp_stats.get("user_stats", {}).get(user_id_str, {}).get("today_success", 0)
        
        total_in_progress += user_in_progress
        total_success += user_success
        
        user_stats.append({
            'user_id': user_id_str,
            'username': username,
            'in_progress': user_in_progress,
            'success': user_success,
            'otp_success': user_otp_success,
            'accounts': len(user_accounts)
        })
    
    # Sort users by success count (descending)
    user_stats.sort(key=lambda x: x['success'], reverse=True)
    
    # =============== PART 1: HEADER AND SUMMARY ===============
    header_message = "🎯 TOP PERFORMERS SUMMARY 🎯\n\n"
    
    header_message += f"📅 Date: {today_display}\n"
    header_message += f"⏰ Report Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    header_message += "📊 TOTAL STATISTICS:\n"
    header_message += f"• 👥 Total Active Users: {total_users}\n"
    header_message += f"• 🔵 Total In Progress Numbers: {total_in_progress}\n"
    header_message += f"• 🟢 Total Success Counts: {total_success}\n"
    header_message += f"• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n\n"
    
    # Calculate overall success rate
    if total_in_progress > 0:
        overall_success_rate = (total_success / total_in_progress) * 100
        header_message += f"📈 OVERALL SUCCESS RATE: {overall_success_rate:.1f}%\n\n"
    
    # Show top performers header
    header_message += "🏆 TOP PERFORMERS TODAY:\n"
    
    await query.edit_message_text(header_message, parse_mode='none')
    
    # =============== PART 2: TOP PERFORMERS LIST ===============
    # Split users into chunks of 15-20 users per message
    users_per_chunk = 50
    total_chunks = (len(user_stats) + users_per_chunk - 1) // users_per_chunk
    
    # Send user stats in chunks
    for chunk_index in range(total_chunks):
        start_idx = chunk_index * users_per_chunk
        end_idx = min(start_idx + users_per_chunk, len(user_stats))
        chunk = user_stats[start_idx:end_idx]
        
        chunk_message = ""
        
        if total_chunks > 1:
            chunk_message += f"📋 Part {chunk_index + 1}/{total_chunks}\n\n"
        
        for i, user in enumerate(chunk, start=start_idx + 1):
            chunk_message += f"{i}. {user['username']} - {user['success']} success\n"
        
        # Add chunk summary
        chunk_in_progress = sum(u['in_progress'] for u in chunk)
        chunk_success = sum(u['success'] for u in chunk)
        
        chunk_message += f"\n📊 Chunk Summary:\n"
        chunk_message += f"• Users: {len(chunk)}\n"
        chunk_message += f"• Success: {chunk_success}\n"
        
        if chunk_in_progress > 0:
            chunk_success_rate = (chunk_success / chunk_in_progress) * 100
            chunk_message += f"• Success Rate: {chunk_success_rate:.1f}%\n"
        
        if chunk_index < total_chunks - 1:
            chunk_message += "\n⬇️ More users in next message..."
        
        try:
            await context.bot.send_message(
                ADMIN_ID,
                chunk_message,
                parse_mode='none'
            )
            await asyncio.sleep(0.5)  # Small delay between messages
        except Exception as e:
            print(f"❌ Error sending top performers chunk {chunk_index + 1}: {e}")
    
    # =============== PART 3: FOOTER ===============
    footer_message = "\n🔄 Statistics will reset at 4:00 PM (Bangladesh Time)"
    
    # Send footer as last message
    await context.bot.send_message(ADMIN_ID, footer_message, parse_mode='none')

async def show_user_statistics_from_callback(query, context):
    """Show user statistics from callback"""
    user_id = query.from_user.id
    
    tracking = load_tracking()
    stats = load_stats()
    otp_stats = load_otp_stats()
    
    user_id_str = str(user_id)
    today_date = datetime.now().date().isoformat()
    
    # Get user-specific stats
    user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
    user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
    
    # Get OTP stats
    user_otp_stats = otp_stats.get("user_stats", {}).get(user_id_str, {})
    today_otp_success = user_otp_stats.get("today_success", 0)
    yesterday_otp_success = user_otp_stats.get("yesterday_success", 0)
    
    # Get account info
    accounts = load_accounts()
    user_data = accounts.get(user_id_str, {})
    user_accounts = user_data.get("accounts", []) if isinstance(user_data, dict) else []
    active_accounts = account_manager.get_user_active_accounts_count(user_id)
    remaining_checks = account_manager.get_user_remaining_checks(user_id)
    
    message = "📊 Your Daily Statistics 📊\n\n"
    
    message += f"📅 Date: {datetime.now().strftime('%d %B %Y')}\n"
    message += f"⏰ Time: {datetime.now().strftime('%H:%M:%S')} (BD Time)\n"
    message += f"🔄 Next Reset: Today 4:00 PM (BD Time)\n\n"
    
    message += "👤 Account Information:\n"
    message += f"• 📱 Total Accounts: {len(user_accounts)}\n"
    message += f"• ✅ Active Login: {active_accounts}\n"
    message += f"• 🎯 Remaining Add: {remaining_checks}\n\n"
    
    message += "📈 Today's Performance:\n"
    message += f"• 📱 Added Numbers: {user_in_progress}\n"
    message += f"• 🟢 Success Counts: {user_success}\n"
    message += f"• ✅ OTP Success: {today_otp_success}\n\n"
    
    
    message += "🔄 Auto Reset: Daily at 4:00 PM (Bangladesh Time)"
    
    await query.edit_message_text(message, parse_mode='none')

async def show_admin_statistics_from_callback(query, context):
    """Show admin statistics from callback"""
    await query.edit_message_text("🔄 Generating all users statistics report...")
    await show_admin_statistics_from_message(query, context)

async def show_admin_statistics_from_message(message_obj, context):
    """Show admin statistics from message object"""
    tracking = load_tracking()
    stats = load_stats()
    otp_stats = load_otp_stats()
    accounts = load_accounts()
    
    today_date = datetime.now().date().isoformat()
    today_display = datetime.now().strftime('%d %B %Y')
    
    # Calculate totals
    total_in_progress = 0
    total_success = 0
    total_users = 0
    
    # User-wise calculations
    user_stats = []
    
    for user_id_str, user_data in accounts.items():
        if user_id_str == str(ADMIN_ID):
            continue
        
        if isinstance(user_data, dict):
            user_accounts = user_data.get("accounts", [])
        else:
            user_accounts = []
        
        if not user_accounts:
            continue
        
        total_users += 1
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        
        # Get user stats
        user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
        user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
        user_otp_success = otp_stats.get("user_stats", {}).get(user_id_str, {}).get("today_success", 0)
        
        total_in_progress += user_in_progress
        total_success += user_success
        
        user_stats.append({
            'user_id': user_id_str,
            'username': username,
            'in_progress': user_in_progress,
            'success': user_success,
            'otp_success': user_otp_success,
            'accounts': len(user_accounts)
        })
    
    # Sort users by success count (descending)
    user_stats.sort(key=lambda x: x['success'], reverse=True)
    
    # Send summary
    summary_message = "👑 ADMIN STATISTICS SUMMARY 👑\n\n"
    
    summary_message += f"📅 Date: {today_display}\n"
    summary_message += f"⏰ Time: {datetime.now().strftime('%H:%M:%S')} (BD Time)\n"
    summary_message += f"🔄 Next Reset: Today 4:00 PM (BD Time)\n\n"
    
    summary_message += "📊 TODAY'S OVERVIEW:\n"
    summary_message += f"• 👥 Total Users: {total_users}\n"
    summary_message += f"• 🔵 Total In Progress: {total_in_progress}\n"
    summary_message += f"• 🟢 Total Success: {total_success}\n"
    summary_message += f"• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n"
    summary_message += f"• 📊 Total Checked: {stats.get('today_checked', 0)}\n"
    summary_message += f"• 🗑️ Total Deleted: {stats.get('today_deleted', 0)}\n\n"
    
    await message_obj.edit_message_text(summary_message, parse_mode='none')
    
    # Send user details in chunks of 10
    users_per_message = 10
    total_chunks = (len(user_stats) + users_per_message - 1) // users_per_message
    
    for chunk_index in range(total_chunks):
        start_idx = chunk_index * users_per_message
        end_idx = min(start_idx + users_per_message, len(user_stats))
        chunk = user_stats[start_idx:end_idx]
        
        details_message = f"📋 USER STATISTICS - PART {chunk_index + 1}/{total_chunks} 📋\n\n"
        details_message += f"📅 Date: {today_display}\n\n"
        
        for i, user in enumerate(chunk, start=start_idx + 1):
            details_message += f"{i}. {user['username']} (ID: {user['user_id']})\n"
            details_message += f"   ├─ 📱 Accounts: {user['accounts']}\n"
            details_message += f"   ├─ 🔵 In Progress: {user['in_progress']}\n"
            details_message += f"   ├─ 🟢 Success: {user['success']}\n"
            details_message += f"   ├─ ✅ OTP Success: {user['otp_success']}\n"
            
            if user['in_progress'] > 0:
                success_rate = (user['success'] / user['in_progress']) * 100
                details_message += f"   └─ 📈 Success Rate: {success_rate:.1f}%\n"
            else:
                details_message += f"   └─ 📈 Success Rate: 0%\n"
            
            details_message += "\n"
        
        chunk_in_progress = sum(u['in_progress'] for u in chunk)
        chunk_success = sum(u['success'] for u in chunk)
        
        details_message += f"📊 Chunk {chunk_index + 1} Summary:\n"
        details_message += f"• 👥 Users: {len(chunk)}\n"
        details_message += f"• 🔵 In Progress: {chunk_in_progress}\n"
        details_message += f"• 🟢 Success: {chunk_success}\n"
        
        if chunk_index < total_chunks - 1:
            details_message += "\n⬇️ More users in next message..."
        
        try:
            await context.bot.send_message(
                ADMIN_ID,
                details_message,
                parse_mode='none'
            )
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ Error sending statistics chunk {chunk_index + 1}: {e}")
    
    # Send final totals
    final_message = "🎯 FINAL DAILY SUMMARY 🎯\n\n"
    
    final_message += f"📅 Date: {today_display}\n"
    final_message += f"⏰ Report Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    final_message += "📊 TOTAL STATISTICS:\n"
    final_message += f"• 👥 Total Active Users: {total_users}\n"
    final_message += f"• 🔵 Total In Progress Numbers: {total_in_progress}\n"
    final_message += f"• 🟢 Total Success Counts: {total_success}\n"
    final_message += f"• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n\n"
    
    if total_in_progress > 0:
        overall_success_rate = (total_success / total_in_progress) * 100
        final_message += f"📈 OVERALL SUCCESS RATE: {overall_success_rate:.1f}%\n\n"
    
    if len(user_stats) >= 3:
        final_message += "🏆 TOP 3 PERFORMERS TODAY:\n"
        for i in range(min(3, len(user_stats))):
            user = user_stats[i]
            final_message += f"{i+1}. {user['username']} - {user['success']} success\n"
        final_message += "\n"
    
    final_message += "🔄 Statistics will reset at 4:00 PM (Bangladesh Time)\n"
    final_message += "✅ Report generation complete!"
    
    await context.bot.send_message(ADMIN_ID, final_message, parse_mode='none')

def extract_phone_numbers(text: str) -> List[Dict[str, str]]:
    """
    Extract phone numbers with country codes from text
    Returns list of dictionaries with 'cc' and 'phone' keys
    """
    all_numbers = []
    
    # Define common country codes (expanded list)
    # IMPORTANT: For USA/Canada, API needs "11" instead of "1"
    country_codes = {
        '1': '11',  # USA/Canada - FIXED: API requires "11"
        '7': 'RU/KZ',
        '20': 'EG',
        '27': 'ZA',
        # ... rest of the country codes remain same
    }
    
    # ১. প্রথমে + সহ নম্বর এক্সট্র্যাক্ট করা
    pattern_plus = r'\+\s*(\d{1,4})\s*([\d\s\-\.\(\)]+)'
    matches_plus = re.finditer(pattern_plus, text, re.IGNORECASE)
    
    for match in matches_plus:
        cc = match.group(1).strip()
        phone_part = match.group(2).strip()
        
        # Clean phone part - remove all non-digits
        phone_digits = re.sub(r'\D', '', phone_part)
        
        # SPECIAL FIX: USA/Canada এর জন্য cc = "11"
        if cc == '1':
            cc = '11'  # API requires "11" for USA/Canada
            print(f"✅ Converted USA/Canada CC from 1 to 11 for phone: {phone_digits}")
        
        # Check if CC is valid
        if cc in ['11', '7', '20', '27', '30', '31', '32', '33', '34', '36', '39', '40', 
                  '41', '43', '44', '45', '46', '47', '48', '49', '51', '52', '53', '54', 
                  '55', '56', '57', '58', '60', '61', '62', '63', '64', '65', '66', '81', 
                  '82', '84', '86', '90', '91', '92', '93', '94', '95', '98', '212', '213', 
                  '216', '218', '220', '221', '222', '223', '224', '225', '226', '227', 
                  '228', '229', '230', '231', '232', '233', '234', '235', '236', '237', 
                  '238', '239', '240', '241', '242', '243', '244', '245', '246', '247', 
                  '248', '249', '250', '251', '252', '253', '254', '255', '256', '257', 
                  '258', '260', '261', '262', '263', '264', '265', '266', '267', '268', 
                  '269', '290', '291', '297', '298', '299', '350', '351', '352', '353', 
                  '354', '355', '356', '357', '358', '359', '370', '371', '372', '373', 
                  '374', '375', '376', '377', '378', '379', '380', '381', '382', '383', 
                  '385', '386', '387', '389', '420', '421', '423', '500', '501', '502', 
                  '503', '504', '505', '506', '507', '508', '509', '590', '591', '592', 
                  '593', '594', '595', '596', '597', '598', '599', '670', '672', '673', 
                  '674', '675', '676', '677', '678', '679', '680', '681', '682', '683', 
                  '685', '686', '687', '688', '689', '690', '691', '692', '850', '852', 
                  '853', '855', '856', '880', '886', '960', '961', '962', '963', '964', 
                  '965', '966', '967', '968', '970', '971', '972', '973', '974', '975', 
                  '976', '977', '992', '993', '994', '995', '996', '998']:
            # Phone should have reasonable length (7-15 digits)
            if 7 <= len(phone_digits) <= 15:
                all_numbers.append({
                    'cc': cc,
                    'phone': phone_digits,
                    'source': 'plus_format'
                })
                print(f"✅ Extracted from + format: CC={cc}, Phone={phone_digits}")
    
    # ২. যদি + না থাকে, শুধু ডিজিট থাকে
    if not all_numbers:
        # Find all sequences of digits
        all_digits = re.findall(r'\d+', text)
        
        for digits in all_digits:
            # Check if this looks like a phone number with country code
            if len(digits) >= 10:  # Minimum for country code + phone
                found_cc = None
                found_phone = None
                
                # SPECIAL HANDLING FOR USA/CANADA
                # Check for USA/Canada pattern: starts with 1 followed by 10 digits
                if digits.startswith('1') and len(digits) == 11:
                    # USA/Canada: 1 followed by 10-digit phone
                    found_cc = '11'  # API requires "11"
                    found_phone = digits[1:]  # Remove leading 1
                    print(f"✅ USA/Canada detected: CC={found_cc}, Phone={found_phone}")
                
                # Check for other country codes
                if not found_cc:
                    for cc_length in range(4, 0, -1):
                        if len(digits) > cc_length:
                            possible_cc = digits[:cc_length]
                            possible_phone = digits[cc_length:]
                            
                            # SPECIAL: If cc is "1", convert to "11" for API
                            if possible_cc == '1':
                                found_cc = '11'
                                found_phone = possible_phone
                                break
                            # Check other country codes
                            elif possible_cc in ['7', '20', '27', '30', '31', '32', '33', '34', 
                                               '36', '39', '40', '41', '43', '44', '45', '46', 
                                               '47', '48', '49', '51', '52', '53', '54', '55', 
                                               '56', '57', '58', '60', '61', '62', '63', '64', 
                                               '65', '66', '81', '82', '84', '86', '90', '91', 
                                               '92', '93', '94', '95', '98', '212', '213', '216', 
                                               '218', '220', '221', '222', '223', '224', '225', 
                                               '226', '227', '228', '229', '230', '231', '232', 
                                               '233', '234', '235', '236', '237', '238', '239', 
                                               '240', '241', '242', '243', '244', '245', '246', 
                                               '247', '248', '249', '250', '251', '252', '253', 
                                               '254', '255', '256', '257', '258', '260', '261', 
                                               '262', '263', '264', '265', '266', '267', '268', 
                                               '269', '290', '291', '297', '298', '299', '350', 
                                               '351', '352', '353', '354', '355', '356', '357', 
                                               '358', '359', '370', '371', '372', '373', '374', 
                                               '375', '376', '377', '378', '379', '380', '381', 
                                               '382', '383', '385', '386', '387', '389', '420', 
                                               '421', '423', '500', '501', '502', '503', '504', 
                                               '505', '506', '507', '508', '509', '590', '591', 
                                               '592', '593', '594', '595', '596', '597', '598', 
                                               '599', '670', '672', '673', '674', '675', '676', 
                                               '677', '678', '679', '680', '681', '682', '683', 
                                               '685', '686', '687', '688', '689', '690', '691', 
                                               '692', '850', '852', '853', '855', '856', '880', 
                                               '886', '960', '961', '962', '963', '964', '965', 
                                               '966', '967', '968', '970', '971', '972', '973', 
                                               '974', '975', '976', '977', '992', '993', '994', 
                                               '995', '996', '998'] and 7 <= len(possible_phone) <= 15:
                                found_cc = possible_cc
                                found_phone = possible_phone
                                break
                
                # If no country code found, try default logic
                if not found_cc:
                    # Check if it starts with 1 (USA/Canada)
                    if digits.startswith('1'):
                        found_cc = '11'
                        found_phone = digits[1:] if len(digits) > 1 else digits
                    elif len(digits) == 10:
                        # Assume USA/Canada without country code
                        found_cc = '11'
                        found_phone = digits
                    elif len(digits) >= 7:
                        # Generic fallback
                        found_cc = '11'  # Default to USA/Canada
                        found_phone = digits
                
                if found_cc and found_phone:
                    all_numbers.append({
                        'cc': found_cc,
                        'phone': found_phone,
                        'source': 'digits_only'
                    })
                    print(f"✅ Extracted from digits: CC={found_cc}, Phone={found_phone}")
    
    # ৩. Remove duplicates based on phone number
    unique_numbers = []
    seen_phones = set()
    
    for num in all_numbers:
        phone = num['phone']
        # Also check for similar numbers (like 7869817 vs 47869817)
        if phone not in seen_phones:
            is_substring = False
            for seen_phone in seen_phones:
                if phone in seen_phone or seen_phone in phone:
                    is_substring = True
                    if len(phone) > len(seen_phone):
                        unique_numbers = [n for n in unique_numbers if n['phone'] != seen_phone]
                        seen_phones.remove(seen_phone)
                        unique_numbers.append(num)
                        seen_phones.add(phone)
                    break
            
            if not is_substring:
                unique_numbers.append(num)
                seen_phones.add(phone)
    
    print(f"🔍 Text: {text}")
    print(f"📱 Final extracted numbers: {unique_numbers}")
    
    return unique_numbers
    
async def add_number_async(session, token, cc, phone, retry_count=2):
    for attempt in range(retry_count):
        try:
            headers = {"Admin-Token": token}
            add_url = f"{BASE_URL}/z-number-base/addNum?cc={cc}&phoneNum={phone}&smsStatus=2"
            async with session.post(add_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    print(f"✅ Number {phone} added successfully")
                    return True
                elif response.status == 401:
                    print(f"❌ Token expired during add for {phone}, attempt {attempt + 1}")
                    continue
                elif response.status in (400, 409):
                    print(f"❌ Number {phone} already exists or invalid, status {response.status}")
                    return False
                else:
                    print(f"❌ Add failed for {phone} with status {response.status}")
        except Exception as e:
            print(f"❌ Add number error for {phone} (attempt {attempt + 1}): {e}")
    return False

async def get_status_async(session, token, phone):
    try:
        headers = {"Admin-Token": token}
        status_url = f"{BASE_URL}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
        
        async with session.get(status_url, headers=headers, timeout=10) as response:
            response_text = await response.text()
            
            if response.status == 401:
                print(f"❌ Token expired for {phone}")
                return -1, "❌ Token Expired", None
            
            try:
                res = await response.json(content_type=None)
            except Exception as json_error:
                print(f"❌ JSON parse attempt 1 failed for {phone}: {json_error}")
                try:
                    cleaned_text = response_text.strip()
                    if cleaned_text.startswith('\ufeff'):
                        cleaned_text = cleaned_text[1:]
                    res = json.loads(cleaned_text)
                except Exception as e2:
                    print(f"❌ Manual JSON parse also failed for {phone}: {e2}")
                    print(f"❌ Raw response: {response_text[:500]}")
                    return -2, "❌ API Error", None
            
            if res.get('code') == 28004:
                print(f"❌ Login required for {phone}")
                return -1, "❌ Token Expired", None
            
            if res.get('msg') and any(keyword in str(res.get('msg')).lower() for keyword in ["already exists", "cannot register", "number exists"]):
                print(f"❌ Number {phone} already exists or cannot register")
                return 16, "🚫 Already Exists", None
            
            if res.get('code') in (400, 409):
                print(f"❌ Number {phone} already exists, code {res.get('code')}")
                return 16, "🚫 Already Exists", None
            
            if (res and "data" in res and "records" in res["data"] and 
                res["data"]["records"] and len(res["data"]["records"]) > 0):
                record = res["data"]["records"][0]
                status_code = record.get("registrationStatus")
                record_id = record.get("id")
                status_name = status_map.get(status_code, f"🔸 Status {status_code}")
                return status_code, status_name, record_id
            
            if res and "data" in res and "records" in res["data"]:
                return None, "🚫 Already Registered...", None
            
            return None, "🚫 Already Registered...", None
            
    except Exception as e:
        print(f"❌ Status error for {phone}: {type(e).__name__}: {e}")
        return -2, "🔄 Refresh Server", None

async def delete_single_number_async(session, token, record_id, username):
    try:
        headers = {"Admin-Token": token}
        delete_url = f"{BASE_URL}/z-number-base/deleteNum/{record_id}"
        async with session.delete(delete_url, headers=headers, timeout=10) as response:
            if response.status == 200:
                return True
            else:
                print(f"❌ Delete failed for {record_id}: Status {response.status}")
                return False
    except Exception as e:
        print(f"❌ Delete error for {record_id}: {e}")
        return False

async def submit_otp_async(session, token, phone, code, cc='1'):
    """
    Submit OTP with country code support
    """
    try:
        headers = {"Admin-Token": token}
        
        # Create URL with country code
        otp_url = f"{BASE_URL}/z-number-base/allNum/uploadCode?cc={cc}&phoneNum={phone}&code={code}"
        
        print(f"🔄 Submitting OTP for {phone} (CC:{cc}) with code {code}")
        print(f"📡 URL: {otp_url}")
        
        async with session.get(otp_url, headers=headers, timeout=15) as response:
            response_text = await response.text()
            print(f"📥 OTP Response: Status={response.status}, Body={response_text[:200]}")
            
            if response.status == 200:
                try:
                    result = await response.json(content_type=None)
                    if result.get('code') == 200:
                        print(f"✅ OTP submitted successfully for {phone}")
                        return True, "OTP verified successfully"
                    else:
                        error_msg = result.get('msg', 'Unknown error')
                        print(f"❌ OTP failed: {error_msg}")
                        return False, error_msg
                except json.JSONDecodeError:
                    if "success" in response_text.lower() or "200" in response_text:
                        print(f"✅ OTP submitted successfully for {phone} (text response)")
                        return True, "OTP verified successfully"
                    else:
                        print(f"❌ OTP failed: {response_text}")
                        return False, response_text
            elif response.status == 401:
                print(f"❌ Token expired for OTP submission")
                return False, "Token expired! Please refresh server."
            else:
                print(f"❌ HTTP Error {response.status} for OTP submission")
                return False, f"HTTP Error: {response.status}"
                
    except asyncio.TimeoutError:
        print(f"❌ OTP submission timeout for {phone}")
        return False, "Request timeout! Network issue."
    except Exception as e:
        print(f"❌ OTP submission error for {phone}: {type(e).__name__}: {e}")
        return False, str(e)

async def get_user_settlements(session, token, user_id, page=1, page_size=2):
    try:
        headers = {"Admin-Token": token}
        url = f"{BASE_URL}/m-settle-accounts/closingEntries?page={page}&pageSize={page_size}&userid={user_id}"
        
        print(f"🔍 Fetching settlements for user {user_id}")
        
        async with session.get(url, headers=headers, timeout=10) as response:
            response_text = await response.text()
            print(f"📥 Response status: {response.status}")
            
            if response.status == 200:
                try:
                    result = await response.json(content_type=None)
                    
                    if result.get('code') == 200:
                        data = result.get('data', {})
                        
                        if 'records' in data:
                            records = data.get('records', [])
                            total = data.get('total', len(records))
                            pages = data.get('pages', 1)
                            
                            return {
                                'records': records,
                                'total': total,
                                'pages': pages,
                                'page': page,
                                'size': page_size
                            }, None
                        else:
                            print(f"⚠️ No 'records' key in data: {data}")
                            return {
                                'records': [],
                                'total': 0,
                                'pages': 0,
                                'page': page,
                                'size': page_size
                            }, None
                    else:
                        error_msg = result.get('msg', 'Unknown error')
                        print(f"❌ API returned error: {error_msg}")
                        return None, f"API Error: {error_msg}"
                except Exception as e:
                    print(f"❌ JSON parse error in get_user_settlements: {e}")
                    return None, f"JSON parse error: {e}"
            else:
                print(f"❌ HTTP Error in get_user_settlements: {response.status}")
                return None, f"HTTP Error: {response.status}"
    except Exception as e:
        print(f"❌ Exception in get_user_settlements: {e}")
        return None, str(e)


# ============ FAKE PAYMENT FUNCTIONS ============

def generate_fake_payment_details():
    """Generate random fake payment details with realistic masked data"""
    import random
    
    # Generate random earnings between 2 and 10 USD
    total_usd = round(random.uniform(2.0, 10.0), 2)
    
    # Generate realistic personal counts (based on earnings)
    personal_count = random.randint(int(total_usd * 8), int(total_usd * 12))
    personal_earnings = round(personal_count * 0.10, 2)
    
    # Adjust to match total
    if personal_earnings > total_usd:
        personal_earnings = round(total_usd * 0.7, 2)
        personal_count = int(personal_earnings / 0.10)
    
    # Friend counts (realistic)
    friend_count = random.randint(5, int(total_usd * 5))
    friend_earnings = round(friend_count * 0.10, 2)
    commission = round(friend_count * 0.002, 2)
    
    # Calculate total
    calculated_total = personal_earnings + friend_earnings + commission
    if abs(calculated_total - total_usd) > 0.5:
        total_usd = round(calculated_total, 2)
    
    # Generate realistic user name (like real Telegram users)
    first_names = ["Rakib", "Sakib", "Rafiq", "Sohel", "Nayeem", "Fahim", "Ridoy", "Tanvir", "Saif", "Shanto"]
    last_names = ["Hasan", "Khan", "Islam", "Rana", "Ahmed", "Hossain", "Haque", "Uddin", "Rahman", "Mia"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    username = f"{first_name}_{last_name}"
    
    # Generate realistic user ID (7-10 digits like Telegram IDs)
    user_id = str(random.randint(1000000, 999999999))
    
    # Generate realistic telegram username
    telegram_username = f"{first_name.lower()}{random.randint(100, 999)}"
    
    # Generate realistic country
    countries = ["Bangladesh", "India", "Pakistan", "USA", "Canada", "UK", "UAE", "Saudi Arabia", "Malaysia"]
    country = random.choice(countries)
    
    # Generate realistic friends list
    num_friends = random.randint(1, 3)
    friends_details = []
    
    for i in range(num_friends):
        friend_first = random.choice(first_names)
        friend_last = random.choice(last_names)
        friend_name = f"{friend_first} {friend_last}"
        friend_telegram = f"{friend_first.lower()}{random.randint(10, 99)}"
        friend_amount = round(random.uniform(0.5, 3.0), 2)
        
        friends_details.append({
            'name': friend_name,
            'telegram': friend_telegram,
            'amount': friend_amount
        })
    
    return {
        'total_usd': total_usd,
        'total_bdt': round(total_usd * 125, 0),
        'personal_count': personal_count,
        'personal_earnings': personal_earnings,
        'friend_count': friend_count,
        'friend_earnings': friend_earnings,
        'commission': commission,
        'username': username,
        'user_id': user_id,
        'telegram_username': telegram_username,
        'country': country,
        'friends_details': friends_details
    }


async def send_fake_payment_confirmation(context: CallbackContext, count: int = 1):
    """
    Send fake payment confirmation messages to payment group
    Looks EXACTLY like real payment confirmations with proper masking
    """
    if not FAKE_PAYMENT_ENABLED:
        print("⚠️ Fake payment notifications are disabled")
        return 0
    
    sent_count = 0
    current_time = datetime.now()
    
    for i in range(count):
        try:
            # Generate random payment details
            payment = generate_fake_payment_details()
            
            # Add small delay between messages
            if i > 0:
                await asyncio.sleep(random.uniform(2, 5))
            
            # Current time with random offset
            msg_time = current_time - timedelta(seconds=random.randint(0, 300))
            time_str = msg_time.strftime('%d %B %Y, %H:%M:%S')
            
            # ============ MASK THE USER DETAILS ============
            # Mask user ID: first 3 + xxxx + last 3
            user_id = payment['user_id']
            if len(user_id) >= 6:
                first_three = user_id[:3]
                last_three = user_id[-3:]
                masked_user_id = f"{first_three}xxxx{last_three}"
            elif len(user_id) >= 4:
                masked_user_id = f"{user_id[:2]}xx{user_id[-2:]}"
            else:
                masked_user_id = "xxx"
            
            # Mask username: first 2 + xxx + last 2
            username = payment['username']
            if len(username) >= 4:
                first_two = username[:2]
                last_two = username[-2:]
                masked_username = f"{first_two}xxx{last_two}"
            elif len(username) >= 3:
                masked_username = f"{username[:1]}xx{username[-1:]}"
            else:
                masked_username = "xxx"
            
            # Mask telegram username
            telegram_username = payment['telegram_username']
            masked_telegram = ""
            if telegram_username:
                if len(telegram_username) >= 4:
                    first_two = telegram_username[:2]
                    last_two = telegram_username[-2:]
                    masked_telegram = f"{first_two}xxx{last_two}"
                elif len(telegram_username) >= 3:
                    masked_telegram = f"{telegram_username[:1]}xx{telegram_username[-1:]}"
                else:
                    masked_telegram = "xxx"
            
            # Create message - NO MARKDOWN
            message = f"💰 PAYMENT CONFIRMATION 💰\n\n"
            message += f"🕐 Time: {time_str}\n\n"
            
            message += f"👤 User: {masked_username}\n"
            message += f"🆔 User ID: {masked_user_id}\n"
            if masked_telegram:
                message += f"📱 Telegram: @{masked_telegram}\n"
            
            message += f"\n📊 Payment Details:\n"
            message += f"├─ 🔢 Personal Count: {payment['personal_count']}\n"
            message += f"├─ 💵 Personal Earnings: ${payment['personal_earnings']:.2f}\n"
            
            if payment['friend_count'] > 0:
                message += f"├─ 👥 Friend Count: {payment['friend_count']}\n"
                message += f"├─ 💰 Friends Earned: ${payment['friend_earnings']:.2f}\n"
            
            if payment['commission'] > 0:
                message += f"├─ 💸 Commission: ${payment['commission']:.2f}\n"
            
            message += f"├─ 📈 Total USD: ${payment['total_usd']:.2f}\n"
            message += f"└─ 🇧🇩 Total BDT: {payment['total_bdt']:.0f}\n\n"
            
            # Add masked friends info
            if payment['friends_details']:
                message += f"👥 Friends to Collect From ({len(payment['friends_details'])} friends):\n"
                for j, friend in enumerate(payment['friends_details'], 1):
                    friend_name = friend['name']
                    friend_telegram = friend.get('telegram', '')
                    friend_amount = friend.get('amount', 0)
                    
                    # Mask friend name
                    if len(friend_name) >= 4:
                        first_two = friend_name[:2]
                        last_two = friend_name[-2:]
                        masked_friend_name = f"{first_two}xxx{last_two}"
                    elif len(friend_name) >= 3:
                        masked_friend_name = f"{friend_name[:1]}xx{friend_name[-1:]}"
                    else:
                        masked_friend_name = "xxx"
                    
                    # Mask friend telegram
                    masked_friend_telegram = ""
                    if friend_telegram:
                        if len(friend_telegram) >= 4:
                            first_two = friend_telegram[:2]
                            last_two = friend_telegram[-2:]
                            masked_friend_telegram = f"{first_two}xxx{last_two}"
                        elif len(friend_telegram) >= 3:
                            masked_friend_telegram = f"{friend_telegram[:1]}xx{friend_telegram[-1:]}"
                        else:
                            masked_friend_telegram = "xxx"
                    
                    message += f"├─ {j}. {masked_friend_name}"
                    if masked_friend_telegram:
                        message += f" (@{masked_friend_telegram})"
                    message += f"\n├─   └─ ${friend_amount:.2f}\n"
            
            # Add random transaction ID
            tx_id = f"PAY-{msg_time.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            message += f"\n✅ Status: Payment Completed\n"
            message += f"🔒 Privacy: User details masked for security\n"
            message += f"📨 Transaction ID: {tx_id}\n\n"
            message += f"#PaymentConfirmation #{masked_user_id}"
            
            # Send to group - NO MARKDOWN
            await context.bot.send_message(
                chat_id=FAKE_PAYMENT_GROUP_ID,
                text=message,
                parse_mode='none'
            )
            sent_count += 1
            print(f"✅ Fake payment #{i+1} sent to group")
            
        except Exception as e:
            print(f"❌ Error sending fake payment #{i+1}: {e}")
    
    return sent_count


async def forward_payment_confirmation_to_group(context: CallbackContext, user_id: str, username: str, 
                                                telegram_username: str, total_usd: float, total_bdt: float,
                                                personal_count: int, personal_earnings: float,
                                                friend_count: int, friend_earnings: float,
                                                commission: float, friends_details: list, is_fake: bool = False):
    """
    Forward payment confirmation to a separate Telegram group with masked user info
    No Markdown - plain text only
    """
    try:
        # Mask user ID: first 3 digits + xxxx + last 3 digits
        masked_user_id = user_id
        if len(user_id) >= 6:
            first_three = user_id[:3]
            last_three = user_id[-3:]
            masked_user_id = f"{first_three}xxxx{last_three}"
        elif len(user_id) >= 4:
            masked_user_id = f"{user_id[:2]}xx{user_id[-2:]}"
        else:
            masked_user_id = "xxx"
        
        # Mask username: first 2 characters + xxx + last 2 characters
        masked_username = username
        if len(username) >= 4:
            first_two = username[:2]
            last_two = username[-2:]
            masked_username = f"{first_two}xxx{last_two}"
        elif len(username) >= 3:
            masked_username = f"{username[:1]}xx{username[-1:]}"
        else:
            masked_username = "xxx"
        
        # Mask telegram username if exists
        masked_telegram = ""
        if telegram_username:
            if len(telegram_username) >= 4:
                first_two = telegram_username[:2]
                last_two = telegram_username[-2:]
                masked_telegram = f"{first_two}xxx{last_two}"
            elif len(telegram_username) >= 3:
                masked_telegram = f"{telegram_username[:1]}xx{telegram_username[-1:]}"
            else:
                masked_telegram = "xxx"
        
        # Current time
        current_time = datetime.now().strftime('%d %B %Y, %H:%M:%S')
        
        # Calculate total counts from friends_details
        total_friend_counts = sum(f.get('counts', 0) for f in friends_details)
        
        # Create masked message - NO MARKDOWN, plain text
        message = f"💰 PAYMENT CONFIRMATION 💰\n\n"
        message += f"🕐 Time: {current_time}\n\n"
        
        message += f"👤 User: {masked_username}\n"
        message += f"🆔 User ID: {masked_user_id}\n"
        if masked_telegram:
            message += f"📱 Telegram: @{masked_telegram}\n"
        
        message += f"\n📊 Payment Details:\n"
        message += f"├─ 🔢 Personal Count: {personal_count}\n"
        message += f"├─ 💵 Personal Earnings: ${personal_earnings:.2f}\n"
        
        # Show friend details with both count and earnings
        if friends_details and len(friends_details) > 0:
            # Show total friend count and total earnings
            message += f"├─ 👥 Total Friends: {len(friends_details)}\n"
            message += f"├─ 🔢 Total Friend Counts: {total_friend_counts}\n"
            message += f"├─ 💰 Total Friends Earned: ${friend_earnings:.2f}\n"
        
        if commission > 0:
            message += f"├─ 💸 Commission: ${commission:.2f}\n"
        
        message += f"├─ 📈 Total USD: ${total_usd:.2f}\n"
        message += f"└─ 🇧🇩 Total BDT: {total_bdt:.0f}\n\n"
        
        # Add friends list with counts and earnings
        if friends_details and len(friends_details) > 0:
            message += f"👥 Friends Details ({len(friends_details)} friends):\n"
            for i, friend in enumerate(friends_details, 1):
                friend_name = friend.get('name', 'Unknown')
                friend_telegram = friend.get('telegram', '')
                friend_counts = friend.get('counts', 0)
                friend_amount = friend.get('amount', 0)
                
                # Mask friend name: first 2 + xxx + last 2
                masked_friend_name = friend_name
                if len(friend_name) >= 4:
                    first_two = friend_name[:2]
                    last_two = friend_name[-2:]
                    masked_friend_name = f"{first_two}xxx{last_two}"
                elif len(friend_name) >= 3:
                    masked_friend_name = f"{friend_name[:1]}xx{friend_name[-1:]}"
                else:
                    masked_friend_name = "xxx"
                
                # Mask friend telegram if exists
                masked_friend_telegram = ""
                if friend_telegram:
                    if len(friend_telegram) >= 4:
                        first_two = friend_telegram[:2]
                        last_two = friend_telegram[-2:]
                        masked_friend_telegram = f"{first_two}xxx{last_two}"
                    elif len(friend_telegram) >= 3:
                        masked_friend_telegram = f"{friend_telegram[:1]}xx{friend_telegram[-1:]}"
                    else:
                        masked_friend_telegram = "xxx"
                
                message += f"├─ {i}. {masked_friend_name}"
                if masked_friend_telegram:
                    message += f" (@{masked_friend_telegram})"
                message += f"\n├─   ├─ 🔢 Counts: {friend_counts}\n"
                message += f"├─   └─ 💰 Earned: ${friend_amount:.2f}\n"
        
        # Add fake indicator if it's a fake payment
        if is_fake:
            message += f"\n⚠️ Note: This is a simulated confirmation for testing\n"
        
        message += f"\n✅ Status: Payment Completed\n"
        message += f"🔒 Privacy: User details masked for security\n\n"
        message += f"#PaymentConfirmation #{masked_user_id}"
        
        # Send to group - NO MARKDOWN
        try:
            await context.bot.send_message(
                chat_id=PAYMENT_GROUP_ID,
                text=message,
                parse_mode='none'
            )
            print(f"✅ Payment confirmation forwarded to group for user {masked_user_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to send payment confirmation to group: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error in forward_payment_confirmation_to_group: {e}")
        return False


# ============ FAKE PAYMENT COMMAND HANDLERS ============

async def fake_payment_command(update: Update, context: CallbackContext):
    """
    Command to send fake payment confirmations
    Usage: /fakepay [count]
    Example: /fakepay 10 - sends 10 fake confirmations
             /fakepay - sends 1 fake confirmation
    """
    user_id = update.effective_user.id
    
    # Admin only command
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    # Parse count from command
    count = 1
    if context.args:
        try:
            count = int(context.args[0])
            if count < 1:
                count = 1
            if count > 100:  # Limit to 100 messages per command
                count = 100
                await update.message.reply_text("⚠️ Maximum 100 messages per command. Sending 100...")
        except ValueError:
            await update.message.reply_text("❌ Invalid count! Please provide a number.\nExample: `/fakepay 10`")
            return
    
    # Check if fake payments are enabled
    if not FAKE_PAYMENT_ENABLED:
        await update.message.reply_text(
            "❌ Fake payments are disabled!\n\n"
            "Enable them by setting `FAKE_PAYMENT_ENABLED=True` in environment variables."
        )
        return
    
    # Send initial message
    processing_msg = await update.message.reply_text(f"🔄 Sending {count} fake payment confirmation(s)...")
    
    try:
        sent_count = await send_fake_payment_confirmation(context, count)
        
        await processing_msg.edit_text(
            f"✅ Fake Payment Confirmation(s) Sent!\n\n"
            f"📊 Summary:\n"
            f"├─ 📨 Requested: {count}\n"
            f"├─ ✅ Sent: {sent_count}\n"
            f"└─ ❌ Failed: {count - sent_count}\n\n"
            f"📢 Target Group: {FAKE_PAYMENT_GROUP_ID}\n"
            f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}"
        )
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error sending fake payments: {e}")


async def fake_payment_toggle_command(update: Update, context: CallbackContext):
    """
    Command to enable/disable fake payments
    Usage: /fakeenable - enables fake payments
           /fakedisable - disables fake payments
    """
    user_id = update.effective_user.id
    
    # Admin only command
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    global FAKE_PAYMENT_ENABLED
    
    command = context.args[0].lower() if context.args else ""
    
    if command == "enable" or command == "on":
        FAKE_PAYMENT_ENABLED = True
        status = "ENABLED ✅"
    elif command == "disable" or command == "off":
        FAKE_PAYMENT_ENABLED = False
        status = "DISABLED ❌"
    else:
        await update.message.reply_text(
            "❌ Usage:\n"
            "`/fakeenable` - Enable fake payments\n"
            "`/fakedisable` - Disable fake payments\n\n"
            f"Current status: {'✅ ENABLED' if FAKE_PAYMENT_ENABLED else '❌ DISABLED'}"
        )
        return
    
    await update.message.reply_text(
        f"✅ Fake Payments {status}\n\n"
        f"📢 Status: {'✅ Active' if FAKE_PAYMENT_ENABLED else '❌ Inactive'}\n"
        f"📨 Target Group: {FAKE_PAYMENT_GROUP_ID}\n"
        f"🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"
    )


async def fake_payment_status_command(update: Update, context: CallbackContext):
    """
    Command to show fake payment settings
    Usage: /fakestatus
    """
    user_id = update.effective_user.id
    
    # Admin only command
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    # Generate a sample fake payment to show
    sample = generate_fake_payment_details()
    
    message = f"📊 Fake Payment Settings\n\n"
    message += f"✅ Status: {'ENABLED' if FAKE_PAYMENT_ENABLED else 'DISABLED'}\n"
    message += f"📨 Target Group: {FAKE_PAYMENT_GROUP_ID}\n"
    message += f"👥 Total Users in Database: {len(FAKE_USERNAMES)}\n"
    message += f"🌍 Countries Available: {len(FAKE_COUNTRIES)}\n\n"
    
    message += f"📝 Sample Fake Payment:\n"
    message += f"├─ 👤 Username: {sample['username']}\n"
    message += f"├─ 💰 Amount: ${sample['total_usd']:.2f}\n"
    message += f"├─ 🔢 Counts: {sample['personal_count']}\n"
    message += f"├─ 👥 Friends: {len(sample['friends_details'])}\n"
    message += f"└─ 🌍 Country: {sample['country']}\n\n"
    
    message += f"📋 Commands:\n"
    message += f"• `/fakepay [count]` - Send fake confirmations\n"
    message += f"• `/fakeenable` - Enable fake payments\n"
    message += f"• `/fakedisable` - Disable fake payments\n"
    message += f"• `/fakestatus` - Show this status\n\n"
    
    message += f"💡 Note: All user details in fake payments are randomly generated."
    
    await update.message.reply_text(message, parse_mode='none')


class AccountManager:
    def __init__(self):
        print("🔄 Initializing Account Manager...")
        self.accounts = self._load_accounts_compatible()
        print(f"📊 Loaded accounts for {len(self.accounts)} users")
        
        self.user_tokens = {}
        self.token_owners = {}
        self.token_info = {}
        self.user_selected_accounts = {}
        self.user_accounts_data = {}  # Store user accounts data
        
    def _load_accounts_compatible(self):
        """Load accounts with backward compatibility"""
        try:
            accounts_data = load_accounts()
            
            # Check if old format (list) or new format (dict with accounts)
            converted_accounts = {}
            
            for user_id_str, user_data in accounts_data.items():
                if isinstance(user_data, list):
                    # Old format - convert to new format
                    accounts_list = user_data
                    converted_accounts[user_id_str] = {
                        "accounts": [],
                        "selected_account_id": 1,
                        "telegram_username": "",
                        "last_active": datetime.now().isoformat()
                    }
                    
                    for i, acc in enumerate(accounts_list, 1):
                        new_account = {
                            'id': i,
                            'custom_name': acc.get('custom_name', f"Account {i}"),
                            'username': acc.get('username', ''),
                            'password': acc.get('password', ''),
                            'token': acc.get('token'),
                            'api_user_id': acc.get('api_user_id'),
                            'nickname': acc.get('nickname', acc.get('username', '')),
                            'last_login': acc.get('last_login', datetime.now().isoformat()),
                            'active': acc.get('active', True),
                            'default': (i == 1),
                            'added_by': acc.get('added_by', 'unknown'),
                            'added_at': acc.get('added_at', datetime.now().isoformat()),
                            'telegram_username': acc.get('telegram_username', ''),
                            'friends': acc.get('friends', [])  # Add friends field
                        }
                        converted_accounts[user_id_str]["accounts"].append(new_account)
                    
                    print(f"✅ Converted old format for user {user_id_str}")
                elif isinstance(user_data, dict):
                    # Already in new format
                    converted_accounts[user_id_str] = user_data
                else:
                    print(f"❌ Invalid format for user {user_id_str}, resetting")
                    converted_accounts[user_id_str] = {
                        "accounts": [],
                        "selected_account_id": 1,
                        "telegram_username": "",
                        "last_active": datetime.now().isoformat()
                    }
            
            # Save converted format
            if converted_accounts != accounts_data:
                save_accounts(converted_accounts)
                print("✅ Accounts converted to new format")
            
            return converted_accounts
            
        except Exception as e:
            print(f"❌ Error loading accounts: {e}")
            return {}
    
    async def initialize_user(self, user_id):
        """Initialize accounts for a specific user"""
        user_id_str = str(user_id)
        
        # Load fresh accounts data
        self.accounts = self._load_accounts_compatible()
        
        user_data = self.accounts.get(user_id_str, {})
        if not user_data or not user_data.get("accounts"):
            print(f"ℹ️ No accounts found for user {user_id}")
            self.user_selected_accounts[user_id_str] = None
            return 0
            
        user_accounts = user_data["accounts"]
        selected_id = user_data.get("selected_account_id", 1)
        
        print(f"🔄 Initializing {len(user_accounts)} accounts for user {user_id}")
        print(f"📱 Selected account ID: {selected_id}")
        
        valid_tokens = []
        
        # Try to login to selected account
        selected_account = None
        for acc in user_accounts:
            if acc['id'] == selected_id:
                selected_account = acc
                break
        
        if not selected_account:
            # If selected account not found, use first account
            selected_account = user_accounts[0] if user_accounts else None
            selected_id = selected_account['id'] if selected_account else 1
        
        if selected_account and selected_account.get('active', True):
            username = selected_account['username']
            password = selected_account['password']
            custom_name = selected_account.get('custom_name', username)
            
            print(f"🔄 Logging into selected account: {custom_name}")
            
            # Check if we have valid token
            if selected_account.get('token') and selected_account.get('api_user_id'):
                print(f"🔍 Validating existing token for {username}")
                is_valid = await self.validate_token(selected_account['token'])
                if is_valid:
                    print(f"✅ Token valid for {username}")
                    valid_tokens.append((
                        username, 
                        selected_account['token'], 
                        selected_account['api_user_id'], 
                        custom_name,
                        selected_id
                    ))
                else:
                    print(f"🔄 Token invalid, re-logging in for {username}")
                    new_token, api_user_id, nickname = await login_api_async(username, password)
                    if new_token:
                        selected_account['token'] = new_token
                        selected_account['api_user_id'] = api_user_id
                        selected_account['nickname'] = nickname
                        selected_account['last_login'] = datetime.now().isoformat()
                        valid_tokens.append((
                            username, 
                            new_token, 
                            api_user_id, 
                            custom_name,
                            selected_id
                        ))
                        print(f"✅ Re-login successful for {username}")
                    else:
                        print(f"❌ Re-login failed for {username}")
                        selected_account['active'] = False
            else:
                print(f"🔄 First time login for {username}")
                new_token, api_user_id, nickname = await login_api_async(username, password)
                if new_token:
                    selected_account['token'] = new_token
                    selected_account['api_user_id'] = api_user_id
                    selected_account['nickname'] = nickname
                    selected_account['last_login'] = datetime.now().isoformat()
                    valid_tokens.append((
                        username, 
                        new_token, 
                        api_user_id, 
                        custom_name,
                        selected_id
                    ))
                    print(f"✅ First login successful for {username}")
                else:
                    print(f"❌ First login failed for {username}")
                    selected_account['active'] = False
        
        # Save updated accounts
        save_accounts(self.accounts)
        
        # Initialize token tracking
        self.user_tokens[user_id_str] = []
        self.user_selected_accounts[user_id_str] = selected_id
        
        for username, token, api_user_id, custom_name, account_id in valid_tokens:
            self.user_tokens[user_id_str].append(token)
            self.token_owners[token] = (user_id_str, username, custom_name, account_id)
            self.token_info[token] = {
                'username': username,
                'custom_name': custom_name,
                'api_user_id': api_user_id,
                'usage': 0,
                'account_id': account_id,
                'user_id': user_id_str
            }
        
        print(f"✅ Initialized {len(valid_tokens)} accounts for user {user_id}")
        return len(valid_tokens)
    
    async def validate_token(self, token):
        """Validate if token is still working"""
        try:
            async with aiohttp.ClientSession() as session:
                status_code, _, _ = await get_status_async(session, token, "0000000000")
                if status_code is not None and status_code != -1:
                    return True
            return False
        except Exception as e:
            print(f"❌ Token validation error: {e}")
            return False
    
    def get_user_accounts_count(self, user_id):
        """Get total number of accounts for user"""
        user_id_str = str(user_id)
        if user_id_str in self.accounts:
            user_data = self.accounts[user_id_str]
            if isinstance(user_data, dict):
                accounts = user_data.get("accounts", [])
            else:
                accounts = []
            active_accounts = [acc for acc in accounts if acc.get('active', True)]
            return len(active_accounts)
        return 0
    
    def get_user_active_accounts_count(self, user_id):
        """Get number of actively logged in accounts"""
        user_id_str = str(user_id)
        if user_id_str in self.user_tokens:
            return len(self.user_tokens[user_id_str])
        return 0
    
    def get_user_remaining_checks(self, user_id):
        """Calculate remaining checks for user - FIXED VERSION"""
        user_id_str = str(user_id)
        
        # Check if user has tokens
        if user_id_str not in self.user_tokens:
            return 0
        
        total_slots = 0
        used_slots = 0
        
        # Calculate total slots from all logged-in accounts
        for token in self.user_tokens[user_id_str]:
            if token in self.token_info:
                # Each account can handle MAX_PER_ACCOUNT checks
                total_slots += MAX_PER_ACCOUNT
                # Current usage of this token
                usage = self.token_info[token].get('usage', 0)
                used_slots += usage
        
        # Also check if user has accounts but not logged in
        if user_id_str in self.accounts:
            user_data = self.accounts[user_id_str]
            if isinstance(user_data, dict):
                accounts_list = user_data.get("accounts", [])
                active_accounts = [acc for acc in accounts_list if acc.get('active', True)]
                total_accounts = len(active_accounts)
                
                # Add potential slots for non-logged accounts
                logged_accounts = len(self.user_tokens[user_id_str])
                non_logged_accounts = total_accounts - logged_accounts
                total_slots += non_logged_accounts * MAX_PER_ACCOUNT
        
        remaining = max(0, total_slots - used_slots)
        
        # Debug info
        print(f"📊 Remaining check calculation for user {user_id}:")
        print(f"  Total slots: {total_slots}")
        print(f"  Used slots: {used_slots}")
        print(f"  Remaining: {remaining}")
        
        return remaining
    
    def get_selected_account_name(self, user_id):
        """Get custom name of selected account"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.accounts:
            return "Unknown"
        
        user_data = self.accounts[user_id_str]
        if not isinstance(user_data, dict):
            return "Unknown"
            
        selected_id = user_data.get("selected_account_id", 1)
        
        for acc in user_data.get("accounts", []):
            if acc['id'] == selected_id:
                return acc.get('custom_name', acc.get('username', 'Unknown'))
        
        return "Unknown"
    
    def get_selected_account_id(self, user_id):
        """Get selected account ID"""
        user_id_str = str(user_id)
        return self.user_selected_accounts.get(user_id_str, 1)
    
    def get_user_accounts_info(self, user_id):
        """Get detailed accounts info for user"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.accounts:
            return []
        
        accounts_info = []
        user_data = self.accounts[user_id_str]
        if not isinstance(user_data, dict):
            return []
            
        selected_id = user_data.get("selected_account_id", 1)
        
        for acc in user_data.get("accounts", []):
            account_info = {
                'id': acc['id'],
                'custom_name': acc.get('custom_name', f"Account {acc['id']}"),
                'username': acc['username'],
                'api_user_id': acc.get('api_user_id'),
                'active': acc.get('active', True),
                'logged_in': bool(acc.get('token')),
                'selected': (acc['id'] == selected_id),
                'last_login': acc.get('last_login'),
                'default': acc.get('default', False)
            }
            accounts_info.append(account_info)
        
        return accounts_info
    
    def get_next_available_token(self, user_id):
        """Get next available token for processing - FIXED VERSION"""
        user_id_str = str(user_id)
        if user_id_str not in self.user_tokens or not self.user_tokens[user_id_str]:
            print(f"❌ No valid tokens available for user {user_id}")
            return None
        
        available_tokens = []
        for token in self.user_tokens[user_id_str]:
            info = self.token_info.get(token, {})
            usage = info.get('usage', 0)
            if usage < MAX_PER_ACCOUNT:
                custom_name = info.get('custom_name', 'Unknown')
                account_id = info.get('account_id', 0)
                available_tokens.append((token, usage, custom_name, account_id))
        
        if not available_tokens:
            print(f"❌ All accounts are at maximum usage for user {user_id}")
            return None
        
        # Get token with lowest usage
        best_token, best_usage, custom_name, account_id = min(available_tokens, key=lambda x: x[1])
        
        # Check if we can use this token
        if best_usage >= MAX_PER_ACCOUNT:
            print(f"❌ Token {custom_name} already at max usage {best_usage}/{MAX_PER_ACCOUNT}")
            return None
        
        # Increment usage
        self.token_info[best_token]['usage'] += 1
        
        current_usage = self.token_info[best_token]['usage']
        print(f"✅ Using token from {custom_name} (ID: {account_id}), usage: {current_usage}/{MAX_PER_ACCOUNT}")
        
        return best_token, custom_name
    
    def release_token(self, token):
        """Release token after processing - FIXED VERSION"""
        if token in self.token_info:
            current_usage = self.token_info[token]['usage']
            
            # Only decrement if usage is greater than 0
            if current_usage > 0:
                self.token_info[token]['usage'] = current_usage - 1
                
                custom_name = self.token_info[token].get('custom_name', 'Unknown')
                new_usage = self.token_info[token]['usage']
                print(f"✅ Released token from {custom_name}, usage: {new_usage}/{MAX_PER_ACCOUNT}")
            else:
                print(f"⚠️ Token {token} already at 0 usage, nothing to release")
    
    def get_api_user_id_for_token(self, token):
        """Get API user ID for a token"""
        info = self.token_info.get(token, {})
        return info.get('api_user_id')
    
    def get_account_info_for_token(self, token):
        """Get account info for a token"""
        if token in self.token_info:
            return self.token_info[token].copy()
        return {}
    
    def switch_user_account(self, user_id, account_id):
        """Switch user's selected account"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.accounts:
            return False
        
        user_data = self.accounts[user_id_str]
        if not isinstance(user_data, dict):
            return False
        
        # Check if account exists
        account_exists = False
        for acc in user_data.get("accounts", []):
            if acc['id'] == account_id:
                account_exists = True
                break
        
        if not account_exists:
            return False
        
        # Update selected account
        self.accounts[user_id_str]["selected_account_id"] = account_id
        self.accounts[user_id_str]["last_active"] = datetime.now().isoformat()
        self.user_selected_accounts[user_id_str] = account_id
        
        # Save changes
        save_accounts(self.accounts)
        
        print(f"✅ User {user_id} switched to account ID: {account_id}")
        return True
    
    async def refresh_user_account(self, user_id, account_id=None):
        """Refresh specific account or all accounts for user"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.accounts:
            return False
        
        user_data = self.accounts[user_id_str]
        if not isinstance(user_data, dict):
            return False
        
        updated_count = 0
        user_accounts = user_data.get("accounts", [])
        
        if account_id:
            # Refresh specific account
            for acc in user_accounts:
                if acc['id'] == account_id and acc.get('active', True):
                    token, api_user_id, nickname = await login_api_async(
                        acc['username'], 
                        acc['password']
                    )
                    if token:
                        acc['token'] = token
                        acc['api_user_id'] = api_user_id
                        acc['nickname'] = nickname
                        acc['last_login'] = datetime.now().isoformat()
                        updated_count += 1
                        print(f"✅ Refreshed account: {acc.get('custom_name', acc['username'])}")
                    break
        else:
            # Refresh all accounts
            for acc in user_accounts:
                if acc.get('active', True):
                    token, api_user_id, nickname = await login_api_async(
                        acc['username'], 
                        acc['password']
                    )
                    if token:
                        acc['token'] = token
                        acc['api_user_id'] = api_user_id
                        acc['nickname'] = nickname
                        acc['last_login'] = datetime.now().isoformat()
                        updated_count += 1
        
        self.accounts[user_id_str]["last_active"] = datetime.now().isoformat()
        save_accounts(self.accounts)
        
        # Re-initialize user
        await self.initialize_user(user_id)
        
        print(f"✅ Refreshed {updated_count} accounts for user {user_id}")
        return updated_count
    
    def get_all_users_accounts(self):
        """Get all users accounts for admin view"""
        all_users = {}
        
        for user_id_str, user_data in self.accounts.items():
            if user_id_str == str(ADMIN_ID):
                continue
            
            if not isinstance(user_data, dict):
                continue
                
            if user_data and "accounts" in user_data:
                user_info = {
                    'user_id': user_id_str,
                    'telegram_username': user_data.get('telegram_username', ''),
                    'last_active': user_data.get('last_active', ''),
                    'selected_account_id': user_data.get('selected_account_id', 1),
                    'accounts': []
                }
                
                for acc in user_data.get("accounts", []):
                    account_info = {
                        'id': acc['id'],
                        'custom_name': acc.get('custom_name', f"Account {acc['id']}"),
                        'username': acc['username'],
                        'api_user_id': acc.get('api_user_id'),
                        'active': acc.get('active', True),
                        'logged_in': bool(acc.get('token')),
                        'last_login': acc.get('last_login'),
                        'added_by': acc.get('added_by', 'unknown'),
                        'added_at': acc.get('added_at', '')
                    }
                    user_info['accounts'].append(account_info)
                
                all_users[user_id_str] = user_info
        
        return all_users

# Initialize AccountManager
account_manager = AccountManager()

active_numbers = {}

number_status_history = {}

async def handle_otp_submission(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a number message with OTP code.")
        return
    
    replied_message = update.message.reply_to_message.text
    print(f"🔍 Checking OTP submission - User: {user_id}, Text: {text}")
    print(f"📩 Replied message: {replied_message}")
    
    # Extract phone number from replied message
    phone = None
    cc = None
    
    # Pattern 1: +966 115103194
    match1 = re.search(r'\+\s*(\d+)\s+(\d+)', replied_message)
    if match1:
        cc = match1.group(1)
        phone = match1.group(2)
        print(f"📱 Found with CC: CC={cc}, Phone={phone}")
    
    # Pattern 2: Just phone number
    if not phone:
        match2 = re.search(r'(\d{9,15})', replied_message)
        if match2:
            phone = match2.group(1)
            print(f"📱 Found phone without CC: {phone}")
    
    if not phone:
        await update.message.reply_text("❌ Could not find phone number in replied message!")
        return
    
    print(f"📊 Active numbers in memory: {len(active_numbers)}")
    if active_numbers:
        for num, data in list(active_numbers.items())[:5]:
            print(f"  - {num}: user_id={data.get('user_id')}, cc={data.get('cc')}")
    
    # Find data in active_numbers
    otp_data = active_numbers.get(phone)
    
    if not otp_data:
        # Try to find by phone number in stored data
        for num, data in active_numbers.items():
            if data.get('phone') == phone:
                otp_data = data
                print(f"✅ Phone found with key: {num}")
                break
    
    if not otp_data:
        print(f"❌ Phone {phone} not found in active_numbers")
        await update.message.reply_text("❌ This number is not active or doesn't belong to you.")
        return
    
    token = otp_data['token']
    username = otp_data['username']
    message_id = otp_data['message_id']
    data_user_id = otp_data['user_id']
    data_cc = otp_data.get('cc', cc if cc else '1')
    
    print(f"   Token exists: {bool(token)}")
    print(f"   Message ID: {message_id}")
    print(f"   Data User ID: {data_user_id}")
    print(f"   Current User ID: {user_id}")
    print(f"   CC: {data_cc}")
    
    # Check if user matches
    if data_user_id != user_id:
        print(f"❌ User mismatch: data_user_id={data_user_id}, user_id={user_id}")
        await update.message.reply_text("❌ This number doesn't belong to you!")
        return
    
    # Validate OTP format based on country
    if data_cc == '1' or data_cc == '11':  # USA/Canada
        if not re.match(r'^\d{6}$', text):
            await update.message.reply_text("❌ USA/Canada requires 6-digit OTP!")
            return
    elif data_cc in ['44', '61', '64']:  # UK, Australia, New Zealand
        if not re.match(r'^\d{6}$', text):
            await update.message.reply_text("❌ This country requires 6-digit OTP!")
            return
    else:  # Other countries (Bangladesh, India, Saudi, etc)
        if not re.match(r'^\d{4,6}$', text):
            await update.message.reply_text("❌ Invalid OTP format. Please send 4-6 digit OTP code.")
            return
    
    processing_msg = await update.message.reply_text(f"🔄 Submitting OTP for {phone} (CC: {data_cc})...")
    
    # Submit OTP
    async with aiohttp.ClientSession() as session:
        success, message = await submit_otp_async(session, token, phone, text, data_cc)
    
    if success:
        await processing_msg.delete()
        
        # Check status after OTP submission
        async with aiohttp.ClientSession() as session:
            status_code, status_name, record_id = await get_status_async(session, token, phone)
        
        # Update the original message
        final_text = f"+{data_cc} {phone} {status_name}"
        
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                text=final_text
            )
            print(f"✅ Message updated to: {final_text}")
        except BadRequest as e:
            print(f"⚠️ Could not update message: {e}")
            
        # Remove from active_numbers
        if phone in active_numbers:
            del active_numbers[phone]
            print(f"🗑️ Removed {phone} from active_numbers")
        
        # Update OTP stats on success
        if status_code == 1:
            otp_stats = load_otp_stats()
            user_id_str = str(user_id)
            
            if user_id_str not in otp_stats["user_stats"]:
                otp_stats["user_stats"][user_id_str] = {
                    "total_success": 0,
                    "today_success": 0,
                    "yesterday_success": 0,
                    "username": username,
                    "full_name": ""
                }
            
            otp_stats["user_stats"][user_id_str]["total_success"] += 1
            otp_stats["user_stats"][user_id_str]["today_success"] += 1
            otp_stats["total_success"] = otp_stats.get("total_success", 0) + 1
            otp_stats["today_success"] = otp_stats.get("today_success", 0) + 1
            
            save_otp_stats(otp_stats)
            print(f"✅ OTP success stats updated for user {user_id_str}")
            
    else:
        await processing_msg.edit_text(f"❌ OTP submission failed for {phone}: {message}")

async def track_status_optimized(context: CallbackContext):
    data = context.job.data
    phone = data['phone']
    token = data['token']
    username = data['username']
    user_id = data['user_id']
    checks = data['checks']
    last_status = data.get('last_status', '🔵 Processing...')
    serial_number = data.get('serial_number')
    last_status_code = data.get('last_status_code')
    cc = data.get('cc', '1')
    
    try:
        async with aiohttp.ClientSession() as session:
            status_code, status_name, record_id, actual_phone = await get_status_with_actual_phone(session, token, phone)
        
        prefix = f"{serial_number}. " if serial_number else ""
        display_phone = actual_phone if actual_phone and actual_phone != phone else phone
        
        # Token expired check
        if status_code == -1:
            account_manager.release_token(token)
            error_text = f"{prefix}+{cc} {display_phone} ❌ Token Error (Auto-Retry)"
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=error_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Message update failed for {phone}: {e}")
            return
        
        # Final states - stop tracking
        final_states = [0, 1, 4, 7, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, -2]
        
        if status_code in final_states:
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
                print(f"🗑️ Number {phone} removed from active_numbers (final state: {status_code})")
            
            if status_code not in [1, 2]:
                deleted_count = await delete_number_from_all_accounts_optimized(phone, user_id)
            
            final_text = f"{prefix}+{cc} {display_phone} {status_name}"
            
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=final_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Final message update failed for {phone}: {e}")
            return
        
        # Success handling
        if status_code == 1 and last_status_code != 1:
            print(f"🎉 SUCCESS detected for {phone} by user {user_id}")
            
            tracking = load_tracking()
            user_id_str = str(user_id)
            
            if phone not in tracking.get("today_success", {}):
                otp_stats = load_otp_stats()
                otp_stats["total_success"] = otp_stats.get("total_success", 0) + 1
                otp_stats["today_success"] = otp_stats.get("today_success", 0) + 1
                
                if user_id_str not in otp_stats["user_stats"]:
                    otp_stats["user_stats"][user_id_str] = {
                        "total_success": 0,
                        "today_success": 0,
                        "yesterday_success": 0,
                        "username": username,
                        "full_name": ""
                    }
                otp_stats["user_stats"][user_id_str]["total_success"] += 1
                otp_stats["user_stats"][user_id_str]["today_success"] += 1
                
                tracking["today_success"][phone] = user_id_str
                
                if "today_success_counts" not in tracking:
                    tracking["today_success_counts"] = {}
                
                if user_id_str not in tracking["today_success_counts"]:
                    tracking["today_success_counts"][user_id_str] = 0
                tracking["today_success_counts"][user_id_str] += 1
                
                save_otp_stats(otp_stats)
                save_tracking(tracking)
                print(f"✅ Success count updated for user {user_id_str}")
        
        # In Progress handling - store in active_numbers
        if status_code == 2:
            if phone not in active_numbers:
                active_numbers[phone] = {
                    'token': token,
                    'username': username,
                    'message_id': data['message_id'],
                    'user_id': user_id,
                    'chat_id': data['chat_id'],
                    'cc': cc,
                    'phone': phone
                }
                print(f"✅ Number {phone} added to active_numbers for OTP submission")
                print(f"📱 Active numbers count: {len(active_numbers)}")
            else:
                print(f"ℹ️ Number {phone} already in active_numbers")
        
        # Update message if status changed
        if status_name != last_status:
            new_text = f"{prefix}+{cc} {display_phone} {status_name}"
            
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=new_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Message update failed for {phone}: {e}")
        
        # Timeout check
        if checks >= 100:
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
                print(f"⏰ Number {phone} removed from active_numbers (timeout)")
            
            if status_code not in [1, 2]:
                deleted_count = await delete_number_from_all_accounts_optimized(phone, user_id)
            
            timeout_text = f"{prefix}+{cc} {display_phone} 🟡 Try Later"
            
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=timeout_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Timeout message update failed for {phone}: {e}")
            return
        
        # Schedule next check
        if context.job_queue:
            context.job_queue.run_once(
                track_status_optimized, 
                5,  # Increased from 2 to 5 seconds
                data={
                    **data, 
                    'checks': checks + 1, 
                    'last_status': status_name,
                    'last_status_code': status_code,
                    'cc': cc
                }
            )
        else:
            print("❌ JobQueue not available")
            
    except Exception as e:
        print(f"❌ Tracking error for {phone}: {e}")
        account_manager.release_token(token)

async def delete_number_from_all_accounts_optimized(phone, user_id):
    """ডিলিট নাম্বার ইউজারের সব অ্যাকাউন্ট থেকে"""
    accounts = load_accounts()
    user_id_str = str(user_id)
    deleted_count = 0
    
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict):
        return 0
    
    # ইউজারের সব অ্যাকাউন্ট থেকে ডিলিট করার টাস্ক তৈরি করুন
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # ইউজারের প্রতিটি অ্যাকাউন্টের জন্য
        for account in user_data.get("accounts", []):
            if account.get("token"):
                # চেক করুন নাম্বারটি এই অ্যাকাউন্টে আছে কিনা
                task = asyncio.create_task(
                    check_and_delete_number(session, account["token"], phone, account['username'])
                )
                tasks.append(task)
        
        if tasks:
            # সব টাস্ক একসাথে রান করুন
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, bool) and result:
                    deleted_count += 1
        
        # স্ট্যাটিস্টিক্স আপডেট
        stats = load_stats()
        stats["total_deleted"] = stats.get("total_deleted", 0) + deleted_count
        stats["today_deleted"] = stats.get("today_deleted", 0) + deleted_count
        save_stats(stats)
        
        print(f"✅ Deleted {phone} from {deleted_count} accounts of user {user_id}")
        return deleted_count

async def check_and_delete_number(session, token, phone, username):
    """চেক করে নাম্বার ডিলিট করুন"""
    try:
        # প্রথমে স্ট্যাটাস চেক করুন
        status_code, status_name, record_id, _ = await get_status_with_actual_phone(session, token, phone)
        
        if record_id:
            # রেকর্ড আইডি থাকলে ডিলিট করুন
            deleted = await delete_single_number_async(session, token, record_id, username)
            if deleted:
                print(f"✅ Deleted {phone} from {username}'s account")
                return True
        else:
            # রেকর্ড না থাকলে শুধু ট্রু রিটার্ন করুন
            print(f"ℹ️ No record found for {phone} in {username}'s account")
            return True
            
    except Exception as e:
        print(f"❌ Error deleting {phone} from {username}: {e}")
    
    return False

async def delete_if_exists(session, token, phone, username):
    try:
        status_code, _, record_id = await get_status_async(session, token, phone)
        if record_id:
            return await delete_single_number_async(session, token, record_id, username)
        return True
    except Exception as e:
        print(f"❌ Delete check error for {phone} in {username}: {e}")
        return False

async def show_user_settlements(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    if user_id_str not in account_manager.user_tokens or not account_manager.user_tokens[user_id_str]:
        await update.message.reply_text("❌ No active accounts found!")
        return
    
    token = account_manager.user_tokens[user_id_str][0]
    
    api_user_id = account_manager.get_api_user_id_for_token(token)
    
    if not api_user_id:
        await update.message.reply_text(
            "❌ Could not find your API user ID.\n\n"
            "Please refresh your accounts by clicking '🚀 Refresh Server' button first."
        )
        return
    
    page = 1
    if context.args:
        try:
            page = int(context.args[0])
            if page < 1:
                page = 1
        except:
            pass
    
    processing_msg = await update.message.reply_text("🔄 Loading your settlement records...")
    
    async with aiohttp.ClientSession() as session:
        data, error = await get_user_settlements(session, token, str(api_user_id), page=page, page_size=5)
    
    if error:
        await processing_msg.edit_text(f"❌ Error loading settlements: {error}")
        return
    
    if not data or not data.get('records'):
        await processing_msg.edit_text("❌ No settlement records found for your account!")
        return
    
    records = data.get('records', [])
    total_records = data.get('total', 0)
    total_pages = data.get('pages', 1)
    
    total_count = 0
    total_amount = 0
    for record in records:
        count = record.get('count', 0)
        record_rate = record.get('receiptPrice', 0.10)
        total_count += count
        total_amount += count * record_rate
    
    message = f"📦 Your Settlement Records\n\n"
    message += f"📊 Total Records: {total_records}\n"
    message += f"🔢 Total Count: {total_count}\n"
    message += f"📄 Page: {page}/{total_pages}\n\n"
    
    for i, record in enumerate(records, 1):
        record_id = record.get('id', 'N/A')
        if record_id != 'N/A' and len(str(record_id)) > 8:
            record_id = str(record_id)[:8] + '...'
        
        count = record.get('count', 0)
        record_rate = record.get('receiptPrice', 0.10)
        amount = count * record_rate
        gmt_create = record.get('gmtCreate', 'N/A')
        country = record.get('countryName', 'N/A') or record.get('country', 'N/A')
        
        try:
            if gmt_create != 'N/A':
                if 'T' in gmt_create:
                    date_obj = datetime.fromisoformat(gmt_create.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%d %B %Y, %H:%M')
            else:
                formatted_date = 'N/A'
        except:
            formatted_date = gmt_create
        
        message += f"{i}. Settlement #{record_id}\n"
        message += f"📅 Date: {formatted_date}\n"
        message += f"🌍 Country: {country}\n"
        message += f"🔢 Count: {count}\n\n"
        
    
    keyboard = []
    row = []
    
    if page > 1:
        row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"settlement_{page-1}"))
    
    if page < total_pages:
        if not row:
            row = []
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"settlement_{page+1}"))
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"settlement_refresh_{page}")])
    
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await processing_msg.edit_text(message, reply_markup=reply_markup, parse_mode='none')
    else:
        await processing_msg.edit_text(message, parse_mode='none')

async def set_settlement_rate(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
        
    if not context.args:
        await update.message.reply_text(
            "✨ Set Settlement Rate ✨\n\n"
            "📝 Usage: `/setrate [country_rate_pairs] [date]`\n"
            "📢 Notice: `/setrate notice Your message here`\n\n"
            "📌 Examples:\n"
            "• `/setrate 0.08` (Today, all countries)\n"
            "• `/setrate 0.07 canada 0.04 benin 0.09 nigeria` (Different rates per country)\n"
            "• `/setrate 0.07 canada 0.04 benin 2/12` (2nd Dec, different rates)\n"
            "• `/setrate notice Payment will be sent tomorrow` (Send notice)\n\n"
            "💡 Note: Date format: DD/MM or YYYY-MM-DD"
        )
        return
        
    try:
        if context.args[0].lower() == 'notice':
            notice_message = ' '.join(context.args[1:])
            if not notice_message:
                await update.message.reply_text("❌ Please provide a notice message!")
                return
            
            accounts = load_accounts()
            sent_count = 0
            
            processing_msg = await update.message.reply_text(f"📢 Sending notice to all users...")
            
            for user_id_str, user_data in accounts.items():
                if user_id_str == str(ADMIN_ID):
                    continue
                
                try:
                    await context.bot.send_message(
                        int(user_id_str),
                        f"📢 Admin Notice 📢\n\n"
                        f"{notice_message}\n\n"
                        f"📅 Date: {datetime.now().strftime('%d %B %Y')}"
                    )
                    sent_count += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"❌ Could not send notice to user {user_id_str}: {e}")
            
            await processing_msg.edit_text(
                f"✅ Notice Sent Successfully!\n\n"
                f"📢 Message: {notice_message}\n"
                f"👥 Sent to: {sent_count} users\n"
                f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            return
        
        # Parse country-specific rates
        country_rates = {}
        target_date = datetime.now().date()
        date_provided = False
        
        args = context.args.copy()
        
        # Check if last argument is a date
        if len(args) >= 2 and ('/' in args[-1] or '-' in args[-1]):
            date_str = args[-1]
            args = args[:-1]  # Remove date from args
            
            try:
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 2:
                        day, month = parts
                        if len(day) == 1:
                            day = '0' + day
                        if len(month) == 1:
                            month = '0' + month
                        current_year = datetime.now().year
                        target_date = datetime.strptime(f"{day}/{month}/{current_year}", "%d/%m/%Y").date()
                elif '-' in date_str:
                    if len(date_str) == 5:
                        month, day = date_str.split('-')
                        current_year = datetime.now().year
                        target_date = datetime.strptime(f"{current_year}-{month}-{day}", "%Y-%m-%d").date()
                    else:
                        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                date_provided = True
                print(f"📅 Date parsed: {target_date}")
            except Exception as e:
                print(f"⚠️ Date parsing error: {e}")
                # If date parsing fails, treat it as part of country rates
                args.append(date_str)
        
        # Parse country rates
        i = 0
        default_rate = None
        
        while i < len(args):
            try:
                rate = float(args[i])
                
                # Check if next token is a country name
                if i + 1 < len(args) and not args[i+1].replace('.', '', 1).isdigit():
                    country_name = args[i+1].title()
                    # Clean country name - remove comma if present
                    country_name = country_name.rstrip(',')
                    country_rates[country_name] = rate
                    print(f"✅ Country rate: {country_name} = ${rate}")
                    i += 2
                else:
                    # Default rate for all countries
                    default_rate = rate
                    print(f"✅ Default rate: ${rate}")
                    i += 1
            except ValueError:
                # If not a number, might be a country name without rate
                print(f"⚠️ Skipping invalid rate: {args[i]}")
                i += 1
        
        if not default_rate and not country_rates:
            await update.message.reply_text("❌ Please provide at least one rate!")
            return
        
        # If no country rates specified, use default for all
        if not country_rates and default_rate:
            print(f"ℹ️ Using default rate for all countries: ${default_rate}")
        
        settings = load_settings()
        old_rate = settings.get('settlement_rate', 0.10)
        
        target_date_str = target_date.strftime('%Y-%m-%d')
        target_date_display = target_date.strftime('%d %B %Y')
        
        # Create filter message
        filter_message = ""
        if country_rates:
            if len(country_rates) == 1:
                country = list(country_rates.keys())[0]
                rate = country_rates[country]
                filter_message = f"🌍 Country: {country} only (${rate:.3f}/count)"
            else:
                filter_message = "🌍 Countries & Rates:\n"
                for country, rate in country_rates.items():
                    filter_message += f"• {country}: ${rate:.3f}/count\n"
        else:
            filter_message = f"🌍 All Countries (${default_rate:.3f}/count)"
        
        processing_msg = await update.message.reply_text(
            f"🔄 Processing Settlement Rate Update\n\n"
            f"📅 Date: {target_date_display}\n"
            f"{filter_message}\n"
            f"⏳ Status: Initializing users..."
        )
        
        accounts = load_accounts()
        all_users_summary = []
        total_users = 0
        total_usd = 0
        total_bdt = 0
        USD_TO_BDT = 125
        
        users_processed = 0
        users_token_refreshed = 0
        users_with_settlements = 0
        users_with_only_commission = 0
        users_failed = 0
        
        # Track users with earnings
        users_with_earnings = 0
        users_without_earnings = 0
        
        # টোটাল স্ট্যাটিসটিক্স
        total_friends_count = 0
        total_eligible_friends = 0
        total_personal_count = 0
        total_friend_counts = 0
        
        # প্রতিটি ইউজারের জন্য কে কার অধীনে কাজ করছে তা ট্র্যাক করা
        user_under_supervisors = {}
        
        # Track which users are in others' friends lists
        users_in_friends_lists = set()
        
        print(f"🔍 Total users in accounts: {len(accounts)}")
        print(f"📊 Settlement Rate Configuration:")
        print(f"  • Default rate: {default_rate}")
        print(f"  • Country rates: {country_rates}")
        print(f"  • Target date: {target_date}")
        
        # First pass: Find all users in friends lists
        for user_id_str, user_data in accounts.items():
            if user_id_str == str(ADMIN_ID):
                continue
            
            if not isinstance(user_data, dict):
                continue
                
            user_accounts = user_data.get("accounts", [])
            if not user_accounts:
                continue
            
            for acc in user_accounts:
                if 'friends' in acc and isinstance(acc['friends'], list):
                    for friend in acc['friends']:
                        friend_id = None
                        if isinstance(friend, dict) and 'user_id' in friend:
                            friend_id = str(friend['user_id'])
                        elif isinstance(friend, str):
                            friend_id = str(friend)
                        
                        if friend_id and friend_id in accounts:
                            users_in_friends_lists.add(friend_id)
                            print(f"🔍 User {friend_id} found in {user_id_str}'s friends list")
        
        print(f"👥 Users found in friends lists: {len(users_in_friends_lists)}")
        
        for user_id_str, user_data in accounts.items():
            if user_id_str == str(ADMIN_ID):
                continue
            
            if not isinstance(user_data, dict):
                continue
                
            user_accounts = user_data.get("accounts", [])
            if not user_accounts:
                continue
            
            users_processed += 1
            username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
            telegram_username = user_accounts[0].get('telegram_username', '') if user_accounts else ''
            
            if users_processed % 5 == 0:
                try:
                    await processing_msg.edit_text(
                        f"🔄 Processing Settlement Rate Update\n\n"
                        f"📅 Date: {target_date_display}\n"
                        f"{filter_message}\n"
                        f"⏳ Status: Processing {users_processed} users...\n"
                        f"✅ With Earnings: {users_with_earnings}\n"
                        f"👥 Without Earnings: {users_without_earnings}"
                    )
                except:
                    pass
            
            # ============ IMPORTANT CHANGE: Process ALL accounts for user ============
            user_total_count = 0
            user_total_usd = 0
            user_country_totals = {}
            user_accounts_with_settlements = []
            user_all_filtered_settlements = []
            
            # Process each account separately
            for acc_idx, account in enumerate(user_accounts):
                print(f"\n📊 Processing account {acc_idx + 1}/{len(user_accounts)} for user {username}")
                
                account_name = account.get('custom_name', account['username'])
                account_username = account['username']
                account_password = account['password']
                
                # Login to this specific account
                account_token = None
                account_api_user_id = None
                
                # Try existing token first
                if account.get('token'):
                    async with aiohttp.ClientSession() as session:
                        status_code, _, _ = await get_status_async(session, account['token'], "0000000000")
                    if status_code != -1:
                        account_token = account['token']
                        account_api_user_id = account.get('api_user_id')
                        print(f"✅ Using existing token for account {account_name}")
                
                # If no valid token, login fresh
                if not account_token:
                    print(f"🔄 Logging into account {account_name}")
                    token, api_user_id, nickname = await login_api_async(account_username, account_password)
                    if token:
                        account_token = token
                        account_api_user_id = api_user_id
                        
                        # Update account in database
                        account['token'] = token
                        account['api_user_id'] = api_user_id
                        account['nickname'] = nickname
                        account['last_login'] = datetime.now().isoformat()
                        
                        users_token_refreshed += 1
                        print(f"✅ Login successful for account {account_name}")
                    else:
                        print(f"❌ Login failed for account {account_name}")
                        continue
                
                # Get settlements for this account
                if account_token and account_api_user_id:
                    try:
                        async with aiohttp.ClientSession() as session:
                            settlement_data, error = await get_user_settlements(
                                session, account_token, str(account_api_user_id), page=1, page_size=100
                            )
                        
                        if error:
                            print(f"❌ Error fetching settlements for account {account_name}: {error}")
                            continue
                        
                        account_filtered_settlements = []
                        account_country_totals = {}
                        
                        if settlement_data and settlement_data.get('records'):
                            for record in settlement_data.get('records', []):
                                gmt_create = record.get('gmtCreate')
                                if not gmt_create:
                                    continue
                                
                                try:
                                    if 'T' in gmt_create:
                                        record_date = datetime.fromisoformat(gmt_create.replace('Z', '+00:00')).date()
                                    else:
                                        record_date = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S').date()
                                    
                                    if record_date != target_date:
                                        continue
                                    
                                    country = record.get('countryName') or record.get('country') or 'Unknown'
                                    # Clean country name
                                    country = country.strip(', ')
                                    
                                    # Check if this country is included in our rates
                                    if country_rates:
                                        country_matched = False
                                        matched_country = None
                                        matched_rate = default_rate if default_rate else 0.10
                                        
                                        for target_country, target_rate in country_rates.items():
                                            if target_country.lower() in country.lower() or country.lower() in target_country.lower():
                                                country_matched = True
                                                matched_country = target_country
                                                matched_rate = target_rate
                                                break
                                        
                                        if not country_matched:
                                            continue
                                    # If no country rates specified, use default rate
                                    else:
                                        if not default_rate:
                                            continue
                                        matched_rate = default_rate
                                    
                                    count_value = record.get('count', 0)
                                    account_filtered_settlements.append({
                                        'record': record,
                                        'date': record_date,
                                        'country': country,
                                        'count': count_value,
                                        'account_name': account_name,
                                        'rate': matched_rate  # Store the rate used
                                    })
                                    
                                except Exception as e:
                                    print(f"❌ Error processing record: {e}")
                                    continue
                        
                        if account_filtered_settlements:
                            print(f"✅ Account {account_name} has {len(account_filtered_settlements)} settlements")
                            
                            # Calculate account totals with correct rate
                            for item in account_filtered_settlements:
                                country = item['country']
                                count = item['count']
                                item_rate = item['rate']
                                
                                # Add to user totals
                                if country not in user_country_totals:
                                    user_country_totals[country] = {
                                        'count': 0,
                                        'rate': item_rate
                                    }
                                user_country_totals[country]['count'] += count
                                
                                user_total_count += count
                                user_total_usd += count * item_rate  # Use the correct rate
                                user_all_filtered_settlements.append(item)
                            
                            user_accounts_with_settlements.append({
                                'account_name': account_name,
                                'username': account_username,
                                'settlement_count': len(account_filtered_settlements),
                                'total_count': sum(item['count'] for item in account_filtered_settlements),
                                'total_usd': sum(item['count'] * item['rate'] for item in account_filtered_settlements)
                            })
                            
                    except Exception as e:
                        print(f"❌ Error processing account {account_name}: {type(e).__name__}: {e}")
                        continue
            
            # Calculate user's personal USD from all accounts (already calculated in loop)
            user_personal_usd = user_total_usd
            
            total_personal_count += user_total_count
            
            # Debug output for rate calculation
            print(f"💰 Rate calculation for {username}:")
            print(f"  • Total count: {user_total_count}")
            print(f"  • Total USD: ${user_personal_usd:.2f}")
            if user_total_count > 0:
                effective_rate = user_personal_usd / user_total_count
                print(f"  • Effective rate: ${effective_rate:.3f}/count")
            
            # ২. ফ্রেন্ডদের কমিশন যোগ করা (একই আগের লজিক)
            commission_rate = 0.002
            total_commission = 0
            friends_details = []
            
            # ফ্রেন্ড ডেটা চেক করা (প্রথম অ্যাকাউন্ট থেকে নেওয়া)
            friends_list = []
            for acc in user_accounts:
                if isinstance(acc, dict) and 'friends' in acc and isinstance(acc['friends'], list):
                    friends_list = acc['friends']
                    print(f"👥 Found {len(friends_list)} friends for {username}")
                    break
            
            total_friends_count += len(friends_list)
            
            # প্রতিটি ফ্রেন্ডের জন্য কমিশন ক্যালকুলেশন
            for friend_data in friends_list:
                friend_user_id = None
                
                if isinstance(friend_data, dict) and 'user_id' in friend_data:
                    friend_user_id = str(friend_data['user_id'])
                elif isinstance(friend_data, str):
                    friend_user_id = str(friend_data)
                else:
                    continue
                
                print(f"🔍 Processing friend: {friend_user_id}")
                
                friend_found = False
                actual_friend_id = None
                
                for acc_key in accounts.keys():
                    if str(acc_key) == str(friend_user_id):
                        actual_friend_id = acc_key
                        friend_found = True
                        break
                
                if not friend_found:
                    print(f"❌ Friend {friend_user_id} not found in accounts")
                    continue
                
                if actual_friend_id and actual_friend_id in accounts:
                    friend_accounts_data = accounts[actual_friend_id]
                    if not isinstance(friend_accounts_data, dict):
                        continue
                        
                    friend_accounts = friend_accounts_data.get("accounts", [])
                    if not friend_accounts:
                        continue
                        
                    friend_api_id = friend_accounts[0].get('api_user_id') if friend_accounts else None
                    friend_username = friend_accounts[0].get('username', 'Unknown') if friend_accounts else 'Unknown'
                    friend_telegram_username = friend_accounts[0].get('telegram_username', '') if friend_accounts else ''
                    
                    # ফ্রেন্ডের জন্য supervisor হিসেবে বর্তমান ইউজারকে সেট করা
                    user_under_supervisors[actual_friend_id] = {
                        'name': username,
                        'telegram_username': telegram_username,
                        'user_id': user_id_str
                    }
                    
                    print(f"✅ Processing friend: {friend_username} (API: {friend_api_id})")
                    
                    # ফ্রেন্ডের settlement ডেটা fetch করা (ফ্রেন্ডের সব অ্যাকাউন্ট থেকে)
                    friend_total_count = 0
                    friend_total_usd = 0
                    friend_countries = []
                    
                    # Process friend's all accounts
                    for friend_acc in friend_accounts:
                        friend_acc_token = None
                        friend_acc_api_id = friend_acc.get('api_user_id')
                        
                        if friend_acc.get('token'):
                            async with aiohttp.ClientSession() as token_session:
                                status_code, _, _ = await get_status_async(token_session, friend_acc['token'], "0000000000")
                            if status_code != -1:
                                friend_acc_token = friend_acc['token']
                        
                        if not friend_acc_token:
                            if friend_acc.get('active', True):
                                token, api_id, nickname = await login_api_async(friend_acc['username'], friend_acc['password'])
                                if token:
                                    friend_acc_token = token
                                    friend_acc['token'] = token
                                    if api_id:
                                        friend_acc['api_user_id'] = api_id
                                    friend_acc['nickname'] = nickname
                                    friend_acc['last_login'] = datetime.now().isoformat()
                        
                        if friend_acc_token and friend_acc_api_id:
                            try:
                                async with aiohttp.ClientSession() as friend_session:
                                    friend_settlement_data, error = await get_user_settlements(
                                        friend_session, friend_acc_token, str(friend_acc_api_id), page=1, page_size=100
                                    )
                                    
                                    if error:
                                        print(f"❌ Error fetching friend settlements: {error}")
                                        continue
                                    
                                    if friend_settlement_data and friend_settlement_data.get('records'):
                                        for record in friend_settlement_data.get('records', []):
                                            gmt_create = record.get('gmtCreate')
                                            if not gmt_create:
                                                continue
                                            
                                            try:
                                                if 'T' in gmt_create:
                                                    record_date = datetime.fromisoformat(gmt_create.replace('Z', '+00:00')).date()
                                                else:
                                                    record_date = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S').date()
                                                
                                                if record_date != target_date:
                                                    continue
                                                
                                                country = record.get('countryName') or record.get('country') or 'Unknown'
                                                # Clean country name
                                                country = country.strip(', ')
                                                
                                                # Check country filter and get rate
                                                item_rate = default_rate if default_rate else 0.10
                                                if country_rates:
                                                    country_matched = False
                                                    for target_country, target_rate in country_rates.items():
                                                        if target_country.lower() in country.lower() or country.lower() in target_country.lower():
                                                            country_matched = True
                                                            item_rate = target_rate
                                                            break
                                                    
                                                    if not country_matched:
                                                        continue
                                                
                                                count = record.get('count', 0)
                                                friend_total_count += count
                                                friend_total_usd += count * item_rate
                                                
                                                if country not in friend_countries:
                                                    friend_countries.append(country)
                                                    
                                            except Exception as e:
                                                continue
                            except Exception as e:
                                print(f"❌ Friend calculation error: {type(e).__name__}: {e}")
                                continue
                    
                    print(f"📈 Friend {friend_username} total filtered count: {friend_total_count}, USD: ${friend_total_usd:.2f}")
                    
                    if friend_total_count >= 1:
                        friend_commission = friend_total_count * commission_rate
                        total_commission += friend_commission
                        total_friend_counts += friend_total_count
                        total_eligible_friends += 1
                        
                        friend_name = "Unknown"
                        if isinstance(friend_data, dict) and 'name' in friend_data:
                            friend_name = friend_data['name']
                        elif friend_accounts and friend_accounts[0].get('nickname'):
                            friend_name = friend_accounts[0].get('nickname')
                        elif friend_accounts and friend_accounts[0].get('username'):
                            friend_name = friend_accounts[0].get('username')
                        
                        friends_details.append({
                            'name': friend_name,
                            'username': friend_username,
                            'telegram_username': friend_telegram_username,
                            'accounts': len(friend_accounts),
                            'counts': friend_total_count,
                            'commission': friend_commission,
                            'countries': friend_countries,
                            'earnings': friend_total_usd,  # Friend's actual earnings
                            'friend_user_id': actual_friend_id
                        })
                        
                        print(f"✅ Friend commission added: {friend_name} - ${friend_commission:.2f} from {friend_total_count} counts")
                    else:
                        print(f"⚠️ Friend {friend_username} has only {friend_total_count} counts in target countries")
                else:
                    print(f"⚠️ No settlement records found for friend {friend_username}")
            
            # ৩. টোটাল ক্যালকুলেশন করা
            total_usd_with_commission = user_personal_usd + total_commission
            total_bdt_user = total_usd_with_commission * USD_TO_BDT
            
            print(f"💰 Final calculation for {username} (ALL ACCOUNTS):")
            print(f"  Accounts with settlements: {len(user_accounts_with_settlements)}")
            print(f"  Personal counts: {user_total_count}")
            print(f"  Personal USD: ${user_personal_usd:.2f}")
            print(f"  Commission: ${total_commission:.2f}")
            print(f"  Total USD: ${total_usd_with_commission:.2f}")
            print(f"  Total BDT: {total_bdt_user:.2f}")
            
            if user_total_count > 0:
                users_with_settlements += 1
            
            if total_commission > 0 and user_total_count == 0:
                users_with_only_commission += 1
                print(f"👥 User {username} has only commission: ${total_commission:.2f}")
            
            # Check if user has any earnings
            has_earnings = user_personal_usd > 0 or total_commission > 0
            
            if has_earnings:
                users_with_earnings += 1
                
                # Convert country_totals to the expected format
                simplified_country_totals = {}
                for country, data in user_country_totals.items():
                    simplified_country_totals[country] = data['count']
                
                user_summary = {
                    'user_id': user_id_str,
                    'username': username,
                    'telegram_username': telegram_username,
                    'settlement_date': target_date_display,
                    'countries': list(simplified_country_totals.keys()),
                    'country_totals': simplified_country_totals,
                    'total_count': user_total_count,
                    'personal_usd': user_personal_usd,
                    'total_commission': total_commission,
                    'friends_details': friends_details,
                    'total_usd': total_usd_with_commission,
                    'total_bdt': total_bdt_user,
                    'num_records': len(user_all_filtered_settlements),
                    'token_refreshed': users_token_refreshed,
                    'has_personal_settlement': len(user_all_filtered_settlements) > 0,
                    'friend_counts': sum(f['counts'] for f in friends_details),
                    'total_counts': user_total_count + sum(f['counts'] for f in friends_details),
                    'has_earnings': has_earnings,
                    'in_friends_list': user_id_str in users_in_friends_lists,
                    'friends_list': friends_details,
                    'accounts_with_settlements': user_accounts_with_settlements,
                    'total_accounts': len(user_accounts),
                    'active_accounts': len([acc for acc in user_accounts if acc.get('active', True)])
                }
                
                all_users_summary.append(user_summary)
                total_users += 1
                total_usd += total_usd_with_commission
                total_bdt += total_bdt_user
                
                print(f"✅ User {username} added to summary (from {len(user_accounts_with_settlements)} accounts)")
                
            else:
                users_without_earnings += 1
                print(f"ℹ️ User {username} has no earnings, skipping from report")
        
        # Save updated accounts (with refreshed tokens)
        save_accounts(accounts)
        
        # Update settings with the correct rate
        if default_rate:
            settings['settlement_rate'] = default_rate
        elif country_rates:
            # Store first country rate as default
            first_country = list(country_rates.keys())[0]
            settings['settlement_rate'] = country_rates[first_country]
        else:
            settings['settlement_rate'] = 0.10  # Fallback
        
        settings['last_updated'] = datetime.now().isoformat()
        settings['updated_by'] = ADMIN_ID
        save_settings(settings)
        
        print(f"\n📈 Processing complete:")
        print(f"• Total users processed: {users_processed}")
        print(f"• Users with earnings: {users_with_earnings}")
        print(f"• Users without earnings: {users_without_earnings}")
        print(f"• Users with settlements: {users_with_settlements}")
        print(f"• Users with only commission: {users_with_only_commission}")
        print(f"• Total personal counts: {total_personal_count}")
        print(f"• Total personal USD: ${sum(u['personal_usd'] for u in all_users_summary):.2f}")
        print(f"• Commission rate used: ${commission_rate}/count")
        print(f"• Settlement rate used: ${default_rate if default_rate else 'country-specific'}")
        
        # আগের notification সিস্টেম - ইউপডেট করা (নিচের অংশ একই থাকে)
        # ... (নোটিফিকেশন অংশ একই থাকবে)
        
        # আগের notification সিস্টেম (original) - ইউপডেট করা
        notified_users = 0
        for user_summary in all_users_summary:
            try:
                # চেক করা যে এই ইউজার কারো অধীনে কাজ করছে কিনা
                supervisor_info = None
                if user_summary['user_id'] in user_under_supervisors:
                    supervisor_info = user_under_supervisors[user_summary['user_id']]
                
                # Get rate for this user (for display)
                display_rate = default_rate if default_rate else list(country_rates.values())[0]
                
                message = "✨ Settlement Rate Update ✨\n\n"
                message += "📢 Notification for Your Account\n\n"
                
                message += "📋 Details:\n"
                message += f"• 📅 Date: {user_summary['settlement_date']}\n"
                
                if country_rates:
                    if len(country_rates) == 1:
                        country = list(country_rates.keys())[0]
                        rate = country_rates[country]
                        message += f"• 🌍 Country: {country} only\n"
                        message += f"• 💰 Base Rate: ${rate:.3f} per count\n"
                    else:
                        message += f"• 🌍 Countries & Rates:\n"
                        for country, rate in country_rates.items():
                            message += f"  • {country}: ${rate:.3f}/count\n"
                else:
                    message += f"• 🌍 Countries: All countries\n"
                    message += f"• 💰 Base Rate: ${display_rate:.3f} per count\n"
                
                message += f"• 💱 Exchange Rate: 1 USD = {USD_TO_BDT} BDT\n\n"
                
                message += "📊 Your Performance (All Accounts):\n"
                
                # Show account breakdown
                if user_summary.get('accounts_with_settlements'):
                    message += f"• 📱 Active Accounts: {user_summary['active_accounts']}\n"
                    message += f"• ✅ Accounts with Settlements: {len(user_summary['accounts_with_settlements'])}\n\n"
                
                # Country breakdown for personal counts
                if user_summary['country_totals']:
                    if len(user_summary['country_totals']) == 1:
                        country = list(user_summary['country_totals'].keys())[0]
                        count = user_summary['country_totals'][country]
                        rate = country_rates.get(country, display_rate) if country_rates else display_rate
                        message += f"• Your Total Counts: {count} counts ({country})\n"
                        message += f"• Your USD: ${user_summary['personal_usd']:.2f} ({count} × ${rate:.3f})\n\n"
                    else:
                        message += f"• Your Total Counts: {user_summary['total_count']} counts\n"
                        for country, count in user_summary['country_totals'].items():
                            rate = country_rates.get(country, display_rate) if country_rates else display_rate
                            country_usd = count * rate
                            message += f"  └─ {country}: {count} counts (${country_usd:.2f})\n"
                        message += f"• Your USD: ${user_summary['personal_usd']:.2f}\n\n"
                else:
                    message += f"• Your Total Counts: {user_summary['total_count']} counts\n"
                    message += f"• Your USD: ${user_summary['personal_usd']:.2f} ({user_summary['total_count']} × ${display_rate:.3f})\n\n"
                
                # ফ্রেন্ড কমিশন থাকলে
                if user_summary['friends_details']:
                    # Count eligible friends (10+ counts)
                    eligible_friends = [f for f in user_summary['friends_details'] if f['counts'] >= 1]
                    ineligible_friends = [f for f in user_summary['friends_details'] if f['counts'] < 1]
                    
                    message += "👥 Your Friends Performance:\n"
                    
                    if eligible_friends:
                        message += f"• Eligible Friends (10+ counts): {len(eligible_friends)}\n"
                        message += f"• Ineligible Friends (<10 counts): {len(ineligible_friends)}\n\n"
                        
                        # Show commission rate
                        message += f"👥 Commission Rate: $0.002 per count (min 10 counts required)\n\n"
                        
                        # Split friends into chunks of 5
                        friends_chunks = [eligible_friends[i:i+5] for i in range(0, len(eligible_friends), 5)]
                        
                        for chunk_num, friends_chunk in enumerate(friends_chunks, 1):
                            if len(friends_chunks) > 1:
                                message += f"📋 Friends List (Part {chunk_num}):\n"
                            
                            for i, friend in enumerate(friends_chunk, start=(chunk_num-1)*5 + 1):
                                telegram_username_display = f" (@{friend['telegram_username']})" if friend['telegram_username'] else ""
                                friend_earned = friend['earnings']
                                friend_earned_bdt = friend_earned * USD_TO_BDT
                                
                                message += f"{i}. {friend['name']}{telegram_username_display}\n"
                                message += f"   • Accounts: {friend['accounts']}\n"
                                
                                if friend['countries']:
                                    if len(friend['countries']) == 1:
                                        message += f"   • Counts: {friend['counts']} ({friend['countries'][0]})\n"
                                    else:
                                        message += f"   • Counts: {friend['counts']} ({', '.join(friend['countries'])})\n"
                                else:
                                    message += f"   • Counts: {friend['counts']}\n"
                                
                                message += f"   • Earned: ${friend_earned:.2f}/{friend_earned_bdt:.0f} BDT\n"
                                message += f"   • Commission: ${friend['commission']:.2f} ({friend['counts']} × $0.002)\n\n"
                        
                        message += f"💸 Total Commission from Friends: ${user_summary['total_commission']:.2f}\n\n"
                    else:
                        message += "• No friends eligible for commission (need 10+ counts)\n"
                        if ineligible_friends:
                            message += f"• Friends with <10 counts: {len(ineligible_friends)}\n"
                        message += "\n"
                else:
                    message += "👥 Your Network:\n"
                    message += f"• Friends: 0 users\n\n"
                
                # Ineligible friends notification
                ineligible_friends_count = len([f for f in user_summary.get('friends_details', []) if f['counts'] < 1])
                if ineligible_friends_count > 0:
                    message += f"ℹ️ Note: {ineligible_friends_count} friends have less than 10 counts (minimum required for commission)\n\n"
                
                # Count summary
                if user_summary['friends_details']:
                    message += "📈 Count Summary:\n"
                    message += f"• Your Counts: {user_summary['total_count']}\n"
                    message += f"• Friends Counts: {user_summary['friend_counts']}\n"
                    message += f"• Total Counts: {user_summary['total_counts']}\n\n"
                
                # Calculate friend earnings (not commission)
                friend_earnings = sum(f['earnings'] for f in user_summary['friends_details'])

                # Total calculation summary
                message += "💰 Earnings Summary:\n"
                
                if user_summary['total_count'] > 0:
                    message += f"• Personal Earnings: ${user_summary['personal_usd']:.2f}\n"
                
                if friend_earnings > 0:
                    message += f"• All Friends Earned: ${friend_earnings:.2f}\n"
                
                if user_summary['total_commission'] > 0:
                    message += f"• Total Commission: ${user_summary['total_commission']:.2f}\n"
                
                # Calculate total
                total_all_earnings = user_summary['personal_usd'] + friend_earnings + user_summary['total_commission']
                total_all_bdt = total_all_earnings * USD_TO_BDT

                message += f"\n• Total USD: ${total_all_earnings:.2f}\n"
                message += f"• Total BDT: {total_all_bdt:.0f} BDT\n\n"
                
                # যদি এই ইউজার কারো অধীনে কাজ করে
                if supervisor_info:
                    supervisor_name = supervisor_info['name']
                    supervisor_telegram = supervisor_info['telegram_username']
                    supervisor_display = f" (@{supervisor_telegram})" if supervisor_telegram else ""
                    message += f"👤 Your Friend: {supervisor_name}{supervisor_display}\n\n"
                
                # Additional message based on earnings
                if total_all_earnings == 0:
                    message += "📈 Tips for next time:\n"
                    message += "• Add more accounts to increase counts\n"
                    message += "• Refer friends to earn commission\n"
                    message += "• Ensure counts meet minimum requirements\n\n"
                    message += "✅ Thank you for being part of our team!\n"
                    message += "🔄 Keep up the good work for future settlements"
                elif user_summary['total_count'] == 0 and user_summary['total_commission'] > 0:
                    message += "🎉 Great work managing your team!\n"
                    message += "✅ Thank you for your leadership!\n"
                    message += "🔄 Payments will be processed within 24 hours"
                else:
                    message += "✅ Thank you for your hard work!\n"
                    message += "🔄 Payments will be processed within 24 hours"
                
                await context.bot.send_message(
                    int(user_summary['user_id']),
                    message,
                    parse_mode='none'
                )
                notified_users += 1
                await asyncio.sleep(1)
                
                print(f"📨 Notification sent to {user_summary['username']}")
                
            except Exception as e:
                print(f"❌ Notification failed for {user_summary['user_id']}: {e}")
        
        # Track which friends are added by whom
        friend_added_by = {}
        for user_summary in all_users_summary:
            for friend in user_summary.get('friends_details', []):
                friend_id = friend['friend_user_id']
                if friend_id not in friend_added_by:
                    friend_added_by[friend_id] = []
                friend_added_by[friend_id].append({
                    'added_by': user_summary['username'],
                    'telegram': user_summary['telegram_username'],
                    'user_id': user_summary['user_id']
                })
        
        # Only send admin report if there are users with earnings
        if all_users_summary:
            # Calculate country-wise summary - PERSONAL COUNTS ONLY
            country_summary = {}
            actual_personal_counts = 0  # Track actual personal counts
            
            for user_summary in all_users_summary:
                # Add personal counts only
                for country, count in user_summary.get('country_totals', {}).items():
                    # Clean country name
                    clean_country = country.strip(', ')
                    if clean_country not in country_summary:
                        country_summary[clean_country] = 0
                    country_summary[clean_country] += count
                    actual_personal_counts += count
            
            # Calculate total friend earnings for all users
            total_friend_earnings = sum(
                sum(f['earnings'] for f in u['friends_details']) 
                for u in all_users_summary
            )

            # Calculate total personal USD from all users
            total_personal_usd = sum(u['personal_usd'] for u in all_users_summary)
            total_commissions = sum(u['total_commission'] for u in all_users_summary)
            
            # Total all earnings (Personal + All Friends + Commission)
            total_all_earnings = total_personal_usd + total_friend_earnings + total_commissions
            total_all_bdt = total_all_earnings * USD_TO_BDT
            
            # ডিটেইলড সামারি মেসেজ
            detailed_summary = "📊 DETAILED SETTLEMENT SUMMARY 📊\n\n"
            
            detailed_summary += "📅 Date: " + target_date_display + "\n"
            
            if country_rates:
                detailed_summary += f"💰 Rates by Country:\n"
                for country, rate in country_rates.items():
                    detailed_summary += f"• {country}: ${rate:.3f}/count\n"
            else:
                detailed_summary += f"💰 Rate: ${default_rate:.2f} per count (All countries)\n"
            
            detailed_summary += f"👥 Commission Rate: $0.002 per count (min 10 counts)\n"
            detailed_summary += f"💱 Exchange Rate: 1 USD = {USD_TO_BDT} BDT\n\n"
            
            detailed_summary += "📈 USER STATISTICS:\n"
            detailed_summary += f"• 👥 Total Users: {total_users} (with earnings)\n"
            detailed_summary += f"• 👥 Skipped Users: {users_without_earnings} (no earnings)\n"
            detailed_summary += f"• ✅ Users with Personal Settlements: {users_with_settlements}\n"
            detailed_summary += f"• 👥 Users with Only Commission: {users_with_only_commission}\n"
            detailed_summary += f"• 🔄 Auto-Refreshed Accounts: {users_token_refreshed}\n"
            detailed_summary += f"• ❌ Failed Users: {users_failed}\n"
            detailed_summary += f"• 📨 Notifications Sent: {notified_users}\n\n"
            
            detailed_summary += "📊 COUNT SUMMARY:\n"
            detailed_summary += f"• 🔢 Total Personal Counts: {actual_personal_counts}\n"
            detailed_summary += f"• 👥 Total Friend Counts: {total_friend_counts}\n"
            detailed_summary += f"• 📈 Grand Total Counts: {actual_personal_counts + total_friend_counts} ({actual_personal_counts} + {total_friend_counts})\n\n"
            
            detailed_summary += "🤝 FRIEND NETWORK:\n"
            detailed_summary += f"• 👥 Total Friends in System: {total_friends_count}\n"
            detailed_summary += f"• ✅ Eligible Friends (10+ counts): {total_eligible_friends}\n"
            detailed_summary += f"• 🔢 Total Eligible Friend Counts: {total_friend_counts}\n\n"
            
            detailed_summary += "💰 FINANCIAL SUMMARY:\n"
            # Calculate actual personal earnings based on country rates
            actual_personal_usd_calculated = 0
            if country_rates:
                for user_summary in all_users_summary:
                    for country, count in user_summary.get('country_totals', {}).items():
                        clean_country = country.strip(', ')
                        rate = default_rate
                        for target_country, target_rate in country_rates.items():
                            if target_country.lower() in clean_country.lower() or clean_country.lower() in target_country.lower():
                                rate = target_rate
                                break
                        actual_personal_usd_calculated += count * rate
            else:
                actual_personal_usd_calculated = actual_personal_counts * (default_rate if default_rate else 0.10)
            
            detailed_summary += f"• 💵 Personal Earnings: ${actual_personal_usd_calculated:.2f} ({actual_personal_counts} counts)\n"
            detailed_summary += f"• 👥 All Friends Earned: ${total_friend_earnings:.2f} ({total_friend_counts} counts)\n"
            detailed_summary += f"• 💸 Total Commission: ${total_commissions:.2f} ({total_friend_counts} × $0.002)\n"
            detailed_summary += f"• 📊 Total (Personal+Friends+Commission): ${total_all_earnings:.2f}\n"
            detailed_summary += f"• 🇧🇩 Total BDT: {total_all_bdt:.2f} (${total_all_earnings:.2f} × {USD_TO_BDT})\n"
            detailed_summary += f"• 📊 Total Records: {sum(u['num_records'] for u in all_users_summary)}\n\n"
            
            # 🌍 COUNTRY-WISE SUMMARY - PERSONAL COUNTS ONLY
            detailed_summary += "🌍 COUNTRY-WISE SUMMARY (Personal Counts Only) 🌍\n\n"
            detailed_summary += f"📅 Date: {target_date_display}\n\n"
            
            if country_rates:
                # Show only specified countries with PERSONAL counts
                for rate_country, rate in country_rates.items():
                    # Clean country name from rate key
                    clean_rate_country = rate_country.strip(',')
                    personal_country_count = 0
                    
                    # Find matching countries in PERSONAL counts only
                    for user_summary in all_users_summary:
                        for country, count in user_summary.get('country_totals', {}).items():
                            clean_country = country.strip(', ')
                            if (clean_rate_country.lower() == clean_country.lower() or
                                clean_rate_country.lower() in clean_country.lower() or 
                                clean_country.lower() in clean_rate_country.lower()):
                                personal_country_count += count  # Only personal counts
                    
                    country_usd = personal_country_count * rate
                    country_bdt = country_usd * USD_TO_BDT
                    
                    detailed_summary += f"{clean_rate_country}: ${rate:.2f}\n"
                    detailed_summary += f"• 🔢 Personal Count: {personal_country_count}\n"
                    detailed_summary += f"• 💵 USD: ${country_usd:.2f}\n"
                    detailed_summary += f"• 🇧🇩 BDT: {country_bdt:.2f}\n\n"
            else:
                # Show all countries with default rate (PERSONAL COUNTS ONLY)
                display_rate = default_rate if default_rate else 0.10
                detailed_summary += f"💰 Rate: ${display_rate:.2f}\n\n"
                
                # Collect PERSONAL counts by country only
                personal_country_counts = {}
                for user_summary in all_users_summary:
                    for country, count in user_summary.get('country_totals', {}).items():
                        clean_country = country.strip(', ')
                        if clean_country not in personal_country_counts:
                            personal_country_counts[clean_country] = 0
                        personal_country_counts[clean_country] += count
                
                for country, count in sorted(personal_country_counts.items()):
                    country_usd = count * display_rate
                    country_bdt = country_usd * USD_TO_BDT
                    
                    detailed_summary += f"{country}:\n"
                    detailed_summary += f"• 🔢 Personal Count: {count}\n"
                    detailed_summary += f"• 💵 USD: ${country_usd:.2f}\n"
                    detailed_summary += f"• 🇧🇩 BDT: {country_bdt:.2f}\n\n"
            
            detailed_summary += "✅ OPERATION SUCCESSFUL!\n"
            detailed_summary += "All payments have been calculated and notifications sent.\n\n"
            detailed_summary += f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}"
            
            await processing_msg.edit_text(detailed_summary, parse_mode='none')
            
            # প্রতিটি ইউজারের জন্য আলাদা বার্তা পাঠান (1 জন করে)
            for user_summary in all_users_summary:
                # Check if user is in someone's friend list
                added_by_list = friend_added_by.get(user_summary['user_id'], [])
                
                user_message = f"📋 USER DETAILS\n\n"
                
                telegram_display = f" (@{user_summary['telegram_username']})" if user_summary['telegram_username'] else ""
                refresh_icon = " 🔄" if user_summary['token_refreshed'] else ""
                settlement_icon = " ✅" if user_summary['has_personal_settlement'] else " 👥"
                
                user_message += f"👤 User: {user_summary['username']}{telegram_display}{refresh_icon}{settlement_icon}\n"
                
                user_data = accounts.get(user_summary['user_id'], {})
                user_accounts_count = len(user_data.get("accounts", [])) if isinstance(user_data, dict) else 0
                user_message += f"├─ 📱 Total Accounts: {user_accounts_count}\n"
                user_message += f"├─ ✅ Active Accounts: {user_summary['active_accounts']}\n"
                
                if user_summary.get('accounts_with_settlements'):
                    user_message += f"├─ 💰 Accounts with Settlements: {len(user_summary['accounts_with_settlements'])}\n"
                
                if len(user_summary['countries']) == 1:
                    user_message += f"├─ 🌍 Country: {user_summary['countries'][0]}\n"
                elif len(user_summary['countries']) > 1:
                    user_message += f"├─ 🌍 Countries: {', '.join(user_summary['countries'][:3])}"
                    if len(user_summary['countries']) > 3:
                        user_message += f" (+{len(user_summary['countries']) - 3} more)"
                    user_message += f"\n"
                else:
                    user_message += f"├─ 🌍 Countries: All\n"
                
                user_message += f"├─ 🔢 Personal Count: {user_summary['total_count']}\n"
                user_message += f"├─ 💰 Personal Earnings: ${user_summary['personal_usd']:.2f}\n"
                
                if user_summary['friends_details']:
                    eligible_friends = len([f for f in user_summary['friends_details'] if f['counts'] >= 1])
                    ineligible_friends = len([f for f in user_summary['friends_details'] if f['counts'] < 1])
                    user_message += f"├─ 🤝 Total Friends: {len(user_summary['friends_details'])} ({eligible_friends} eligible, {ineligible_friends} <10 counts)\n"
                    
                    # Add friend details
                    if user_summary['friends_details']:
                        user_message += f"├─ 📊 Friend Details:\n"
                        for j, friend in enumerate(user_summary['friends_details'], 1):
                            if friend['counts'] >= 1:
                                friend_telegram_display = f" (@{friend['telegram_username']})" if friend['telegram_username'] else ""
                                friend_earned = friend['earnings']
                                friend_earned_bdt = friend_earned * USD_TO_BDT
                                
                                user_message += f"├─ {j}. {friend['name']}{friend_telegram_display}\n"
                                user_message += f"├─   ├─ 📱 Accounts: {friend['accounts']}\n"
                                
                                if friend['countries']:
                                    if len(friend['countries']) == 1:
                                        user_message += f"├─   ├─ 🌍 Country: {friend['countries'][0]}\n"
                                    else:
                                        user_message += f"├─   ├─ 🌍 Countries: {', '.join(friend['countries'])}\n"
                                
                                user_message += f"├─   ├─ 🔢 Counts: {friend['counts']} ✅\n"
                                user_message += f"├─   ├─ 💰 Earned: ${friend_earned:.2f} ({friend_earned_bdt:.0f} BDT)\n"
                                user_message += f"├─   └─ 💸 Commission: ${friend['commission']:.2f}\n"
                            else:
                                user_message += f"├─ {j}. {friend['name']} ❌ <10 counts\n"
                else:
                    user_message += f"├─ 🤝 Total Friends: 0 (0 eligible)\n"
                
                # Calculate friend earnings for this user
                friend_earnings = sum(f['earnings'] for f in user_summary['friends_details'])
                total_all_earnings_user = user_summary['personal_usd'] + friend_earnings + user_summary['total_commission']
                total_all_bdt_user = total_all_earnings_user * USD_TO_BDT
                
                # কাউন্ট সামারি
                if user_summary['friends_details']:
                    user_message += f"├─ 📊 Count Summary:\n"
                    user_message += f"├─   ├─ 🔢 Your Counts: {user_summary['total_count']}\n"
                    user_message += f"├─   ├─ 👥 Friend Counts: {user_summary['friend_counts']}\n"
                    user_message += f"├─   └─ 📈 Total Counts: {user_summary['total_counts']}\n"
                
                user_message += f"├─ 💰 Total Earnings:\n"
                user_message += f"├─   ├─ Personal: ${user_summary['personal_usd']:.2f}\n"
                
                if friend_earnings > 0:
                    user_message += f"├─   ├─ Friends Earned: ${friend_earnings:.2f}\n"
                
                if user_summary['total_commission'] > 0:
                    user_message += f"├─   ├─ Commission: ${user_summary['total_commission']:.2f}\n"
                
                user_message += f"├─   └─ Total: ${total_all_earnings_user:.2f} ({total_all_bdt_user:.0f} BDT)\n"
                
                # Last active time
                last_active = user_data.get("last_active", "")
                if last_active:
                    try:
                        last_active_time = datetime.fromisoformat(last_active)
                        time_ago = datetime.now() - last_active_time
                        if time_ago.days > 0:
                            last_active_str = f"{time_ago.days} days ago"
                        elif time_ago.seconds > 3600:
                            last_active_str = f"{time_ago.seconds // 3600} hours ago"
                        elif time_ago.seconds > 60:
                            last_active_str = f"{time_ago.seconds // 60} minutes ago"
                        else:
                            last_active_str = "Just now"
                    except:
                        last_active_str = "Unknown"
                else:
                    last_active_str = "Unknown"
                
                user_message += f"└─ ⏰ Last Active: {last_active_str}\n\n"
                
                # If user is in someone's friends list, show warning
                if added_by_list:
                    names = []
                    for adder in added_by_list[:2]:  # Show max 2
                        if adder['telegram']:
                            names.append(f"{adder['added_by']} (@{adder['telegram']})")
                        else:
                            names.append(adder['added_by'])
                    
                    added_by_message = f"⚠️ Already Added by: {', '.join(names)}"
                    if len(added_by_list) > 2:
                        added_by_message += f" and {len(added_by_list) - 2} more"
                    
                    user_message += f"{added_by_message}\n\n"
                else:
                    user_message += f"[🔄 Payment Pending]\n\n"
                
                # Create keyboard buttons
                keyboard = []
                
                if not added_by_list and user_summary['has_earnings']:
                    # Only show payment button if user is not in friends list and has earnings
                    keyboard.append([
                        InlineKeyboardButton(
                            f"✅ Complete {user_summary['username']}", 
                            callback_data=f"payment_complete_{user_summary['user_id']}_{target_date_str}"
                        )
                    ])
                
                keyboard.append([
                    InlineKeyboardButton(
                        "📋 Details", 
                        callback_data=f"payment_details_{user_summary['user_id']}"
                    )
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send individual message for each user
                try:
                    await context.bot.send_message(
                        ADMIN_ID,
                        user_message,
                        reply_markup=reply_markup,
                        parse_mode='none'
                    )
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"❌ Error sending user message {user_summary['username']}: {e}")
            
            # Send final statistics
            final_stats = f"📊 Payment Statistics:\n\n"
            final_stats += f"• 📅 Settlement Date: {target_date_display}\n"
            final_stats += f"• 👥 Total Users: {total_users}\n"
            final_stats += f"• ✅ Direct Payment Required: {len([u for u in all_users_summary if not u['in_friends_list']])}\n"
            final_stats += f"• 👥 Payment via Friends: {len([u for u in all_users_summary if u['in_friends_list']])}\n"
            final_stats += f"• 💰 Total Amount: ${total_all_earnings:.2f}\n"
            final_stats += f"• 🇧🇩 Total BDT: {total_all_bdt:.0f}\n\n"
            final_stats += f"🔄 Payment completion rate: {len([u for u in all_users_summary if not u['in_friends_list']])}/{total_users} users\n"
            final_stats += f"⏰ Report generated at: {datetime.now().strftime('%H:%M:%S')}"
            
            await context.bot.send_message(ADMIN_ID, final_stats, parse_mode='none')
            
        else:
            # No users with earnings
            summary_message = "🎯 Settlement Rate Update Complete 🎯\n\n"
            
            summary_message += "📊 Operation Summary:\n"
            summary_message += f"• 📅 Target Date: {target_date_display}\n"
            
            if country_rates:
                if len(country_rates) == 1:
                    country = list(country_rates.keys())[0]
                    rate = country_rates[country]
                    summary_message += f"• 🌍 Country: {country} (${rate:.3f}/count)\n"
                else:
                    summary_message += f"• 🌍 Countries & Rates:\n"
                    for country, rate in country_rates.items():
                        summary_message += f"  • {country}: ${rate:.3f}/count\n"
            else:
                summary_message += f"• 🔄 Previous Rate: ${old_rate:.2f}\n"
                summary_message += f"• ✅ New Rate: ${default_rate:.2f}\n"
            
            summary_message += f"\n📈 Processing Statistics:\n"
            summary_message += f"• 👥 Total Users: {users_processed}\n"
            summary_message += f"• ✅ Users with Earnings: {users_with_earnings}\n"
            summary_message += f"• 👥 Users without Earnings: {users_without_earnings}\n"
            summary_message += f"• 🔄 Auto-Refreshed: {users_token_refreshed}\n"
            summary_message += f"• ❌ Failed: {users_failed}\n\n"
            
            summary_message += f"📭 No settlements found for {target_date_display} with the specified criteria\n"
            
            if default_rate:
                summary_message += f"ℹ️ Rate Updated: ${default_rate:.2f} (for future settlements)\n\n"
            
            summary_message += f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}"
            
            await processing_msg.edit_text(summary_message, parse_mode='none')
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid Command Format!\n\n"
            "📝 Usage: `/setrate [country_rate_pairs] [date]`\n"
            "📢 Notice: `/setrate notice Your message`\n\n"
            "✅ Examples:\n"
            "• `/setrate 0.08`\n"
            "• `/setrate 0.07 canada 0.04 benin 0.09 nigeria`\n"
            "• `/setrate 0.07 canada 0.04 benin 2/12`\n"
            "• `/setrate notice Payment tomorrow`"
        )

# এই কোডটি main() ফাংশনের আগে যুক্ত করুন
async def handle_payment_callback(update: Update, context: CallbackContext):
    """Handle payment completion callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('payment_complete_'):
        # Format: payment_complete_userID_date
        parts = data.split('_')
        if len(parts) >= 3:
            user_id = parts[2]
            date_str = parts[3] if len(parts) > 3 else datetime.now().strftime('%Y-%m-%d')
            
            await complete_user_payment(query, context, user_id, date_str)
    
    elif data.startswith('payment_details_'):
        user_id = data.split('_')[2]
        await show_user_payment_details(query, context, user_id)

async def complete_user_payment(query, context, user_id, date_str):
    """Complete payment for a specific user"""
    await query.edit_message_text(f"🔄 Completing payment for user {user_id}...")
    
    try:
        # Get user info
        accounts = load_accounts()
        user_data = accounts.get(user_id, {})
        
        if not user_data:
            await query.edit_message_text(f"❌ User {user_id} not found!")
            return
        
        user_accounts = user_data.get("accounts", [])
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        telegram_username = user_accounts[0].get('telegram_username', '') if user_accounts else ''
        
        # Get user's payment details from the message text
        original_text = query.message.text
        
        # Parse amounts from message
        import re
        
        # Extract values from the original message
        personal_earnings = 0
        friend_earnings = 0
        commission = 0
        total_usd = 0
        total_bdt = 0
        personal_count = 0
        friend_count = 0
        friends_details = []
        
        # ============ EXTRACT ALL VALUES ============
        
        # Extract personal earnings
        personal_match = re.search(r'Personal Earnings: \$([\d\.]+)', original_text)
        if personal_match:
            personal_earnings = float(personal_match.group(1))
        
        # Extract friend earnings
        friend_match = re.search(r'Friends Earned: \$([\d\.]+)', original_text)
        if friend_match:
            friend_earnings = float(friend_match.group(1))
        
        # Extract commission
        commission_match = re.search(r'Commission: \$([\d\.]+)', original_text)
        if commission_match:
            commission = float(commission_match.group(1))
        
        # Extract total USD
        total_match = re.search(r'Total USD: \$([\d\.]+)', original_text)
        if total_match:
            total_usd = float(total_match.group(1))
        else:
            total_match = re.search(r'Total: \$([\d\.]+)', original_text)
            if total_match:
                total_usd = float(total_match.group(1))
        
        # Extract total BDT
        bdt_match = re.search(r'Total BDT: (\d+)', original_text)
        if bdt_match:
            total_bdt = int(bdt_match.group(1))
        else:
            total_bdt = total_usd * 125
        
        # Extract personal count
        count_match = re.search(r'Personal Count: ([\d,\.]+)', original_text)
        if count_match:
            personal_count_str = count_match.group(1).replace(',', '')
            personal_count = int(float(personal_count_str))
        
        # Extract friend count
        friend_count_match = re.search(r'Friend Count: ([\d,\.]+)', original_text)
        if friend_count_match:
            friend_count_str = friend_count_match.group(1).replace(',', '')
            friend_count = int(float(friend_count_str))
        
        # ============ EXTRACT FRIENDS DETAILS FROM USER DETAILS SECTION ============
        # Find the USER DETAILS section
        user_details_section = original_text
        
        # Pattern to find all friends with their details
        # Format: ├─ 1. FriendName\n├─   ├─ 📱 Accounts: 1\n├─   ├─ 🌍 Country: Canada\n├─   ├─ 🔢 Counts: 11 ✅\n├─   ├─ 💰 Earned: $0.66 (82 BDT)\n├─   └─ 💸 Commission: $0.02
        friend_pattern = r'├─ (\d+)\. ([^\n]+)\n(.*?)(?=├─ \d+\.|├─ 📊 Count Summary|├─ 💰 Total Earnings|└─ ⏰ Last Active|$)'
        friend_matches = re.findall(friend_pattern, user_details_section, re.DOTALL)
        
        total_friend_counts = 0
        total_friend_earnings = 0
        total_friend_commission = 0
        
        for match in friend_matches:
            friend_num, friend_name, friend_section = match
            
            # Extract counts
            counts_match = re.search(r'🔢 Counts: (\d+)', friend_section)
            friend_counts = 0
            if counts_match:
                friend_counts = int(counts_match.group(1))
            
            # Extract earned amount
            earned_match = re.search(r'💰 Earned: \$([\d\.]+)', friend_section)
            friend_earned = 0
            if earned_match:
                friend_earned = float(earned_match.group(1))
            
            # Extract commission
            comm_match = re.search(r'💸 Commission: \$([\d\.]+)', friend_section)
            friend_commission = 0
            if comm_match:
                friend_commission = float(comm_match.group(1))
            
            # Extract telegram from name
            friend_telegram = ""
            if '@' in friend_name:
                name_parts = friend_name.split('@')
                friend_name = name_parts[0].strip()
                friend_telegram = name_parts[1].strip() if len(name_parts) > 1 else ""
            
            friends_details.append({
                'name': friend_name.strip(),
                'telegram': friend_telegram,
                'counts': friend_counts,
                'amount': friend_earned,
                'commission': friend_commission
            })
            
            total_friend_counts += friend_counts
            total_friend_earnings += friend_earned
            total_friend_commission += friend_commission
            
            print(f"📊 Friend: {friend_name} - Counts: {friend_counts}, Earned: ${friend_earned}, Commission: ${friend_commission}")
        
        # If we have friends_details, update friend_count and friend_earnings
        if friends_details:
            friend_count = len(friends_details)
            friend_earnings = total_friend_earnings
            commission = total_friend_commission  # Use the sum of individual friend commissions
            print(f"📊 Total: {friend_count} friends, {total_friend_counts} counts, ${friend_earnings:.2f} earned, ${commission:.2f} commission")
        
        # Calculate commission if still 0 but we have friend counts
        if commission == 0 and total_friend_counts > 0:
            # Commission is $0.002 per count (0.002 = 0.2 cents)
            commission = total_friend_counts * 0.002
            print(f"📊 Calculated commission from counts: ${commission:.2f} ({total_friend_counts} × 0.002)")
        
        # Recalculate total USD if needed
        if total_usd == 0:
            total_usd = personal_earnings + friend_earnings + commission
            total_bdt = total_usd * 125
            print(f"📊 Recalculated total USD: ${total_usd:.2f}")
        
        # Log extracted data for debugging
        print(f"📊 FINAL payment data for {username}:")
        print(f"  Personal: {personal_count} counts, ${personal_earnings:.2f}")
        print(f"  Friends: {friend_count} friends, {total_friend_counts} counts, ${friend_earnings:.2f}")
        print(f"  Commission: ${commission:.2f}")
        print(f"  Total: ${total_usd:.2f} / {total_bdt:.0f} BDT")
        
        # Get current date and time
        current_date = datetime.now().strftime('%d %B %Y')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # ============ 1. SEND NOTIFICATION TO THE USER ============
        user_notification = f"✨ Payment Complete Notification ✨\n\n"
        user_notification += f"✅ Your settlement payment has been processed!\n\n"
        user_notification += f"📅 Settlement Date: {current_date}\n"
        user_notification += f"👤 Username: {username}\n"
        if telegram_username:
            user_notification += f"📱 Telegram: @{telegram_username}\n"
        user_notification += f"💰 Total Amount: ${total_usd:.2f} USD\n"
        user_notification += f"🇧🇩 Converted: {total_bdt:.0f} BDT (${total_usd:.2f} × 125)\n\n"
        
        if personal_count > 0:
            user_notification += f"🔢 Your Counts: {personal_count}\n\n"
        
        user_notification += f"📊 Your Earnings Summary:\n"
        user_notification += f"├─ 💵 Personal Earnings: ${personal_earnings:.2f} ({personal_count} counts)\n"
        
        if friends_details:
            user_notification += f"├─ 👥 {len(friends_details)} Friends Performance:\n"
            for i, friend in enumerate(friends_details, 1):
                friend_display = friend['name']
                if friend.get('telegram'):
                    friend_display += f" (@{friend['telegram']})"
                user_notification += f"├─ {i}. {friend_display}: ${friend['amount']:.2f} ({friend.get('counts', 0)} counts)\n"
        
        if total_friend_counts > 0:
            user_notification += f"├─ 💸 Commission: ${commission:.2f} ({total_friend_counts} × $0.002)\n"
        
        user_notification += f"└─ 📈 Total: ${total_usd:.2f} ({total_bdt:.0f} BDT)\n\n"
        
        # Add friends to collect from
        if friends_details:
            user_notification += f"🤝 Friends to Collect From ({len(friends_details)} friends):\n"
            total_friends_amount = 0
            
            for i, friend in enumerate(friends_details, 1):
                friend_display = friend['name']
                if friend.get('telegram'):
                    friend_display += f" (@{friend['telegram']})"
                
                friend_bdt = friend['amount'] * 125
                total_friends_amount += friend['amount']
                user_notification += f"• {friend_display} - ${friend['amount']:.2f} ({friend_bdt:.0f} BDT) - {friend.get('counts', 0)} counts\n"
            
            total_friends_bdt = total_friends_amount * 125
            user_notification += f"\n💰 Total to collect from friends: ${total_friends_amount:.2f} ({total_friends_bdt:.0f} BDT)\n\n"
        
        user_notification += f"🏦 Payment Status: ✅ COMPLETED\n\n"
        user_notification += f"💡 Important Notes:\n"
        user_notification += f"• Your payment of ${total_usd:.2f} ({total_bdt:.0f} BDT) has been sent to your account\n"
        
        if friends_details:
            user_notification += f"• Please collect from your {len(friends_details)} friends as listed above\n"
        
        user_notification += f"• Contact admin if you face any issues\n\n"
        user_notification += f"⏰ Payment Time: {current_time}\n"
        user_notification += f"📨 Transaction ID: PAY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        user_notified = False
        try:
            await context.bot.send_message(
                int(user_id),
                user_notification,
                parse_mode='none'
            )
            user_notified = True
            print(f"✅ Notification sent to user {user_id}")
        except Exception as e:
            print(f"❌ Could not notify user {user_id}: {e}")
        
        # ============ 2. SEND NOTIFICATIONS TO ALL FRIENDS ============
        friends_notified = 0
        for friend in friends_details:
            # Find friend's user ID from accounts
            friend_user_id = None
            friend_name = friend['name']
            friend_telegram = friend.get('telegram', '')
            
            for acc_id, acc_data in accounts.items():
                if acc_id == str(ADMIN_ID):
                    continue
                
                acc_accounts = acc_data.get("accounts", [])
                if acc_accounts:
                    acc_username = acc_accounts[0].get('username', '')
                    acc_telegram = acc_accounts[0].get('telegram_username', '')
                    acc_nickname = acc_accounts[0].get('nickname', '')
                    
                    if (friend_name.lower() in acc_username.lower() or 
                        friend_name.lower() in acc_nickname.lower() or
                        (friend_telegram and friend_telegram.lower() == acc_telegram.lower())):
                        friend_user_id = acc_id
                        print(f"✅ Found friend: {acc_username} (ID: {friend_user_id})")
                        break
            
            if friend_user_id and friend['amount'] > 0:
                friend_notification = f"📢 Payment Notification from Your Friend ✨\n\n"
                friend_notification += f"👤 Your Friend: {username}"
                if telegram_username:
                    friend_notification += f" (@{telegram_username})"
                friend_notification += f"\n\n"
                
                friend_notification += f"💰 Your Settlement Details:\n"
                friend_notification += f"├─ 📅 Date: {current_date}\n"
                friend_notification += f"├─ 🔢 Your Counts: {friend.get('counts', 0)}\n"
                friend_notification += f"├─ 💰 Amount: ${friend['amount']:.2f} USD\n"
                friend_notification += f"├─ 🇧🇩 BDT: {friend['amount'] * 125:.0f}\n"
                friend_notification += f"└─ 🤝 Status: Ready for Collection\n\n"
                
                friend_notification += f"💡 Important Instructions:\n"
                friend_notification += f"• Your friend {username} has processed your settlement\n"
                friend_notification += f"• Please collect ${friend['amount']:.2f} ({friend['amount'] * 125:.0f} BDT) from them\n"
                friend_notification += f"• Contact them directly for payment collection\n\n"
                
                friend_notification += f"⏰ Notification Time: {current_time}\n"
                friend_notification += f"📨 Transaction ID: REF-{datetime.now().strftime('%Y%m%d-%H%M%S')}\n\n"
                friend_notification += f"✅ Your payment is ready! Contact your friend now."
                
                try:
                    await context.bot.send_message(
                        int(friend_user_id),
                        friend_notification,
                        parse_mode='none'
                    )
                    friends_notified += 1
                    print(f"✅ Notification sent to friend {friend_user_id}")
                except Exception as e:
                    print(f"❌ Could not notify friend {friend_user_id}: {e}")
        
        # ============ 3. UPDATE ADMIN MESSAGE ============
        if "[🔄 Payment Pending]" in original_text:
            updated_text = original_text.replace("[🔄 Payment Pending]", "[✅ Payment Completed]")
        else:
            updated_text = original_text + f"\n\n✅ Payment Completed\n⏰ Time: {current_time}"
        
        # Add notification status
        notification_status = f"\n📨 Notifications: "
        if user_notified:
            notification_status += f"✅ User"
            if friends_notified > 0:
                notification_status += f", 👥 {friends_notified} friends"
        else:
            notification_status += f"❌ Failed"
        
        updated_text += notification_status
        
        # Create new keyboard without payment button
        keyboard = []
        keyboard.append([
            InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_id}")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            updated_text,
            reply_markup=reply_markup,
            parse_mode='none'
        )
        
        # ============ 4. SEND CONFIRMATION TO ADMIN ============
        confirmation = f"✅ Payment Completed Successfully!\n\n"
        confirmation += f"👤 User: {username} (ID: {user_id})\n"
        
        if telegram_username:
            confirmation += f"📱 Telegram: @{telegram_username}\n"
        
        confirmation += f"📅 Date: {current_date}\n"
        confirmation += f"⏰ Time: {current_time}\n"
        confirmation += f"💰 Total Amount: ${total_usd:.2f} USD\n"
        confirmation += f"🇧🇩 BDT: {total_bdt:.0f} (${total_usd:.2f} × 125)\n\n"
        
        confirmation += f"📊 Breakdown:\n"
        confirmation += f"• Personal: ${personal_earnings:.2f} ({personal_count} counts)\n"
        if friend_earnings > 0:
            confirmation += f"• Friends Earned: ${friend_earnings:.2f} ({total_friend_counts} counts)\n"
        if commission > 0:
            confirmation += f"• Commission: ${commission:.2f}\n\n"
        
        # Show friends list in admin confirmation with correct commission
        if friends_details:
            confirmation += f"👥 Friends Details ({len(friends_details)} friends):\n"
            for i, friend in enumerate(friends_details, 1):
                friend_display = friend['name']
                if friend.get('telegram'):
                    friend_display += f" (@{friend['telegram']})"
                confirmation += f"  {i}. {friend_display} - Counts: {friend.get('counts', 0)}, Earned: ${friend['amount']:.2f}, Commission: ${friend.get('commission', friend.get('counts', 0) * 0.002):.2f}\n"
            confirmation += f"\n"
        
        confirmation += f"📨 Notifications Sent:\n"
        confirmation += f"• ✅ To User: {'✅ Yes' if user_notified else '❌ No'}\n"
        
        if friends_notified > 0:
            confirmation += f"• 👥 To Friends: {friends_notified} users\n"
        else:
            confirmation += f"• 👥 To Friends: No friends to notify\n"
        
        confirmation += f"\n✅ Payment marked as completed in system."
        
        await context.bot.send_message(ADMIN_ID, confirmation, parse_mode='none')
        
        # ============ 5. FORWARD PAYMENT CONFIRMATION TO GROUP ============
        await forward_payment_confirmation_to_group(
            context=context,
            user_id=user_id,
            username=username,
            telegram_username=telegram_username,
            total_usd=total_usd,
            total_bdt=total_bdt,
            personal_count=personal_count,
            personal_earnings=personal_earnings,
            friend_count=friend_count,
            friend_earnings=friend_earnings,
            commission=commission,
            friends_details=friends_details,
            is_fake=False
        )
        
    except Exception as e:
        print(f"❌ Error completing payment: {e}")
        import traceback
        traceback.print_exc()
        await query.edit_message_text(f"❌ Error completing payment: {e}")

async def show_user_payment_details(query, context, user_id):
    """Show detailed payment information for a user"""
    await query.answer("Fetching details...")
    
    # Get user details from accounts
    accounts = load_accounts()
    user_data = accounts.get(user_id, {})
    
    if not user_data:
        await query.edit_message_text(f"❌ User {user_id} not found!")
        return
    
    user_accounts = user_data.get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    telegram_username = user_accounts[0].get('telegram_username', '') if user_accounts else ''
    
    details = f"📋 Payment Details for {username}\n\n"
    details += f"🆔 User ID: {user_id}\n"
    details += f"👤 Telegram: @{telegram_username if telegram_username else 'N/A'}\n"
    details += f"📱 Accounts: {len(user_accounts)}\n"
    details += f"⏰ Last Active: {user_data.get('last_active', 'N/A')}\n\n"
    
    # Show account details
    details += "🔐 Account Information:\n"
    for i, acc in enumerate(user_accounts, 1):
        status = "✅" if acc.get('active', True) else "❌"
        login_status = "🔓" if acc.get('token') else "🔒"
        details += f"{i}. {status}{login_status} {acc.get('custom_name', acc['username'])}\n"
    
    # Add close button
    keyboard = [
        [InlineKeyboardButton("❌ Close", callback_data="close_details")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        details,
        reply_markup=reply_markup,
        parse_mode='none'
    )



async def admin_add_account(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
        
    if not context.args or len(context.args) < 3:
        await update.message.reply_text("❌ Usage: `/addacc user_id username password`\nExample: `/addacc 123456789 user1 pass1`")
        return
        
    try:
        target_user_id = context.args[0]
        username = context.args[1]
        password = context.args[2]
        
        processing_msg = await update.message.reply_text(f"🔄 Verifying account `{username}`...")
        token, api_user_id, nickname = await login_api_async(username, password)
        
        if not token:
            await processing_msg.edit_text(f"❌ Login failed for `{username}`! Please check credentials.")
            return
            
        accounts = load_accounts()
        user_id_str = str(target_user_id)
        
        if user_id_str not in accounts:
            accounts[user_id_str] = {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            user_data = {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        
        account_exists = False
        for acc in user_data.get("accounts", []):
            if acc['username'] == username:
                acc['password'] = password
                acc['token'] = token
                acc['api_user_id'] = api_user_id
                acc['nickname'] = nickname
                acc['last_login'] = datetime.now().isoformat()
                acc['active'] = True
                account_exists = True
                break
        
        if not account_exists:
            new_id = len(user_data.get("accounts", [])) + 1
            user_data["accounts"].append({
                'id': new_id,
                'custom_name': username,
                'username': username,
                'password': password,
                'token': token,
                'api_user_id': api_user_id,
                'nickname': nickname,
                'last_login': datetime.now().isoformat(),
                'active': True,
                'default': (new_id == 1),
                'added_by': update.effective_user.id,
                'added_at': datetime.now().isoformat(),
                'telegram_username': '',
                'friends': []  # Add friends field
            })
        
        accounts[user_id_str] = user_data
        save_accounts(accounts)
        
        if user_id_str in account_manager.user_tokens:
            await account_manager.initialize_user(int(target_user_id))
        
        await processing_msg.edit_text(
            f"✅ Account added successfully!\n\n"
            f"👤 User ID: `{target_user_id}`\n"
            f"📛 Username: `{username}`\n"
            f"🔑 Password: `{password}`\n"
            f"🆔 API User ID: `{api_user_id or 'N/A'}`\n"
            f"✅ Auto-login: Successful"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_start_bot_now(update: Update, context: CallbackContext):
    """Handle start bot button after membership verification"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_bot_now":
        try:
            # Delete the verification message first
            await query.delete_message()
            
            # Create a new message with start command simulation
            # Instead of simulating /start, just show the main menu directly
            user_id = query.from_user.id
            
            active_accounts = await account_manager.initialize_user(user_id)
            
            if user_id == ADMIN_ID:
                keyboard = [
                    [KeyboardButton("➕ Add Account"), KeyboardButton("📋 List Accounts")],
                    [KeyboardButton("🚀 Refresh Server"), KeyboardButton("💰 Set Rate")],
                    [KeyboardButton("📊 Statistics"), KeyboardButton("📱 Switch Account")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                remaining = account_manager.get_user_remaining_checks(user_id)
                active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
                selected_account = account_manager.get_selected_account_name(user_id)
                
                await query.message.reply_text(
                    f"🔥 WA OTP Bot 👑\n\n"
                    f"📱 Active Account: {selected_account}\n"
                    f"✅ Active Login: {active_accounts_count}\n"
                    f"🎯 Remaining Checks: {remaining}\n\n"
                    f"💡 OTP Tip: Reply to any 'In Progress' number with OTP code\n\n"
                    f"✨ Welcome Admin! ✨",
                    reply_markup=reply_markup,
                    parse_mode='none'
                )
                return
                
            keyboard = [
                [KeyboardButton("🚀 Refresh Server"), KeyboardButton("📱 Switch Account")],
                [KeyboardButton("📦 My Settlements"), KeyboardButton("📊 Statistics")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            remaining = account_manager.get_user_remaining_checks(user_id)
            active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
            selected_account = account_manager.get_selected_account_name(user_id)
            
            if active_accounts == 0:
                await query.message.reply_text(
                    f"❌ Access Denied!\n\n"
                    f"Please contact admin for access.\n"
                    f"👤 Admin: ",
                    reply_markup=reply_markup,
                    parse_mode='none'
                )
                return
            
            await query.message.reply_text(
                f"🔥 WA OTP Bot 🔥\n\n"
                f"📱 Active Account: {selected_account}\n"
                f"✅ Active Login: {active_accounts_count}\n"
                f"🎯 Remaining Checks: {remaining}\n\n"
                f"💡 OTP Tip: Reply to any 'In Progress' number with OTP code\n\n"
                f"✨ Welcome! Start checking numbers now! ✨",
                reply_markup=reply_markup,
                parse_mode='none'
            )
            
        except Exception as e:
            print(f"❌ Error in start_bot_now: {e}")
            await query.message.reply_text(
                "✅ Membership Verified!\n\n"
                "Please use /start command to access the bot.",
                parse_mode='none'
            )

async def admin_remove_account(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
        
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ Usage: `/removeacc user_id username`\nExample: `/removeacc 123456789 user1`")
        return
        
    try:
        target_user_id = context.args[0]
        username = context.args[1]
        
        accounts = load_accounts()
        user_id_str = str(target_user_id)
        
        user_data = accounts.get(user_id_str, {})
        if not isinstance(user_data, dict):
            await update.message.reply_text(f"❌ No accounts found for user `{target_user_id}`")
            return
        
        removed = False
        new_accounts = []
        for acc in user_data.get("accounts", []):
            if acc['username'] == username:
                removed = True
                if acc.get('token') and acc['token'] in account_manager.token_info:
                    del account_manager.token_info[acc['token']]
                if acc.get('token') and acc['token'] in account_manager.token_owners:
                    del account_manager.token_owners[acc['token']]
            else:
                new_accounts.append(acc)
        
        if removed:
            user_data["accounts"] = new_accounts
            accounts[user_id_str] = user_data
            save_accounts(accounts)
            
            if user_id_str in account_manager.user_tokens:
                account_manager.user_tokens[user_id_str] = [
                    token for token in account_manager.user_tokens[user_id_str] 
                    if token not in account_manager.token_info
                ]
            
            await update.message.reply_text(
                f"✅ Account removed successfully!\n\n"
                f"👤 User ID: `{target_user_id}`\n"
                f"📛 Username: `{username}`"
            )
        else:
            await update.message.reply_text(f"❌ Account `{username}` not found for user `{target_user_id}`")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def admin_list_accounts(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
        
    accounts = load_accounts()
    
    if not accounts:
        await update.message.reply_text("❌ No accounts in database!")
        return
    
    message = "📋 All User Accounts 👑\n\n"
    
    for user_id_str, user_data in accounts.items():
        if not isinstance(user_data, dict):
            continue
            
        user_accounts = user_data.get("accounts", [])
        message += f"👤 User ID: {user_id_str}\n"
        message += f"📊 Total Accounts: {len(user_accounts)}\n"
        
        active_accounts = len([acc for acc in user_accounts if acc.get('active', True)])
        logged_in_accounts = account_manager.get_user_active_accounts_count(int(user_id_str))
        
        message += f"✅ Active: {active_accounts} | 🔓 Logged In: {logged_in_accounts}\n"
        
        for i, acc in enumerate(user_accounts, 1):
            status = "✅" if acc.get('active', True) else "❌"
            login_status = "🔓" if acc.get('token') else "🔒"
            nickname = acc.get('nickname', 'N/A')
            api_user_id = acc.get('api_user_id', 'N/A')
            message += f"  {i}. {status}{login_status} {acc['username']} ({nickname}) [ID: {api_user_id[:8] if api_user_id != 'N/A' else 'N/A'}]\n"
        
        message += "───\n"
    
    await update.message.reply_text(message)

async def handle_settlement_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('settlement_'):
        if data.startswith('settlement_refresh_'):
            page = int(data.split('_')[2])
        else:
            page = int(data.split('_')[1])
        
        user_id = query.from_user.id
        user_id_str = str(user_id)
        
        if user_id_str not in account_manager.user_tokens or not account_manager.user_tokens[user_id_str]:
            await query.edit_message_text("❌ No active accounts found!")
            return
        
        token = account_manager.user_tokens[user_id_str][0]
        
        api_user_id = account_manager.get_api_user_id_for_token(token)
        
        if not api_user_id:
            await query.edit_message_text(
                "❌ Could not find your API user ID.\n\n"
                "Please refresh your accounts by clicking '🚀 Refresh Server' button first."
            )
            return
        
        async with aiohttp.ClientSession() as session:
            data_result, error = await get_user_settlements(session, token, str(api_user_id), page=page, page_size=5)
        
        if error:
            await query.edit_message_text(f"❌ Error loading settlements: {error}")
            return
        
        if not data_result or not data_result.get('records'):
            await query.edit_message_text("❌ No settlement records found for your account!")
            return
        
        records = data_result.get('records', [])
        total_records = data_result.get('total', 0)
        total_pages = data_result.get('pages', 1)
        
        total_count = 0
        total_amount = 0
        for record in records:
            count = record.get('count', 0)
            record_rate = record.get('receiptPrice', 0.10)
            total_count += count
            total_amount += count * record_rate
        
        message = f"📦 Your Settlement Records\n\n"
        message += f"📊 Total Records: {total_records}\n"
        message += f"🔢 Total Count: {total_count}\n"
        message += f"📄 Page: {page}/{total_pages}\n\n"
        
        for i, record in enumerate(records, 1):
            record_id = record.get('id', 'N/A')
            if record_id != 'N/A' and len(str(record_id)) > 8:
                record_id = str(record_id)[:8] + '...'
            
            count = record.get('count', 0)
            record_rate = record.get('receiptPrice', 0.10)
            amount = count * record_rate
            gmt_create = record.get('gmtCreate', 'N/A')
            country = record.get('countryName', 'N/A') or record.get('country', 'N/A')
            
            try:
                if gmt_create != 'N/A':
                    if 'T' in gmt_create:
                        date_obj = datetime.fromisoformat(gmt_create.replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S')
                    formatted_date = date_obj.strftime('%d %B %Y, %H:%M')
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = gmt_create
            
            message += f"{i}. Settlement #{record_id}\n"
            message += f"📅 Date: {formatted_date}\n"
            message += f"🌍 Country: {country}\n"
            message += f"🔢 Count: {count}\n"
            
        
        keyboard = []
        row = []
        
        if page > 1:
            row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"settlement_{page-1}"))
        
        if page < total_pages:
            if not row:
                row = []
            row.append(InlineKeyboardButton("Next ➡️", callback_data=f"settlement_{page+1}"))
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"settlement_refresh_{page}")])
        
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await query.edit_message_text(message, parse_mode='none')

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Check membership requirements
    channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
    
    if not (channel_joined and group_joined):
        # Create beautiful buttons for missing requirements
        keyboard = []
        
        if not channel_joined:
            keyboard.append([InlineKeyboardButton(
                "📢 Join Channel", 
                url=CHANNEL_INVITE_LINK
            )])
        
        if not group_joined:
            keyboard.append([InlineKeyboardButton(
                "💰 Join Payment Group", 
                url=PAYMENT_GROUP_INVITE_LINK
            )])
        
        keyboard.append([InlineKeyboardButton(
            "🔄 Check Membership", 
            callback_data="check_membership"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create status indicators
        channel_status = "❌ Not Joined" if not channel_joined else "✅ Joined"
        group_status = "❌ Not Joined" if not group_joined else "✅ Joined"
        
        missing_text = ", ".join(missing)
        
        await update.message.reply_text(
            f"🔒 Access Restricted 🔒\n\n"
            f"Welcome to WA OTP Bot! 🚀\n\n"
            f"To use this bot, you must join our official communities:\n\n"
            f"📢 Official Channel: {REQUIRED_CHANNEL}\n"
            f"└─ Status: {channel_status}\n\n"
            f"💰 Payment Group: {REQUIRED_PAYMENT_GROUP}\n"
            f"└─ Status: {group_status}\n\n"
            f"Missing: {missing_text}\n\n"
            f"👇 Please join using the buttons below 👇\n"
            f"Then click 'Check Membership' to verify.\n\n"
            f"✨ After verification, you'll get full access to the bot! ✨",
            reply_markup=reply_markup,
            parse_mode='none'
        )
        return
    
    # If membership requirements are satisfied, continue with normal flow
    try:
        user = update.effective_user
        user_info = f"""
🆕 New User Started Bot 🆕

👤 Full Name: {user.full_name or 'N/A'}
🆔 User ID: `{user.id}`
📛 Username: @{user.username if user.username else 'N/A'}
📅 Date: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}
✅ Channel: Joined
✅ Group: Joined
        """
        
        await context.bot.send_message(
            chat_id="@Wsalluser",
            text=user_info,
            parse_mode='none'
        )
    except Exception as e:
        print(f"⚠️ Failed to send user info to group: {e}")
    
    active_accounts = await account_manager.initialize_user(user_id)
    
    if user_id == ADMIN_ID:
        keyboard = [
            [KeyboardButton("➕ Add Account"), KeyboardButton("📋 List Accounts")],
            [KeyboardButton("🚀 Refresh Server"), KeyboardButton("💰 Set Rate")],
            [KeyboardButton("📊 Statistics"), KeyboardButton("📱 Switch Account")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        remaining = account_manager.get_user_remaining_checks(user_id)
        active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
        selected_account = account_manager.get_selected_account_name(user_id)
        
        await update.message.reply_text(
            f"🔥 WA OTP Bot 👑\n\n"
            f"📱 Active Account: {selected_account}\n"
            f"✅ Active Login: {active_accounts_count}\n"
            f"🎯 Remaining Checks: {remaining}\n\n"
            f"💡 OTP Tip: Reply to any 'In Progress' number with OTP code\n\n"
            f"✨ Welcome Admin! ✨",
            reply_markup=reply_markup,
            parse_mode='none'
        )
        return
        
    keyboard = [
        [KeyboardButton("🚀 Refresh Server"), KeyboardButton("📱 Switch Account")],
        [KeyboardButton("📦 My Settlements"), KeyboardButton("📊 Statistics")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    remaining = account_manager.get_user_remaining_checks(user_id)
    active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
    selected_account = account_manager.get_selected_account_name(user_id)
    
    if active_accounts == 0:
        await update.message.reply_text(
            f"❌ Access Denied!\n\n"
            f"Please contact admin for access.\n"
            f"👤 Admin: ",
            reply_markup=reply_markup,
            parse_mode='none'
        )
        return
    
    await update.message.reply_text(
        f"🔥 WA OTP Bot 🔥\n\n"
        f"📱 Active Account: {selected_account}\n"
        f"✅ Active Login: {active_accounts_count}\n"
        f"🎯 Remaining Checks: {remaining}\n\n"
        f"💡 OTP Tip: Reply to any 'In Progress' number with OTP code\n\n"
        f"✨ Welcome! Start checking numbers now! ✨",
        reply_markup=reply_markup,
        parse_mode='none'
    )

async def handle_membership_check(update: Update, context: CallbackContext):
    """Check membership again when user clicks 'Check Membership' button"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_membership":
        user_id = query.from_user.id
        
        channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
        
        if channel_joined and group_joined:
            # Both requirements satisfied
            new_text = (
                "✅ Membership Verified!\n\n"
                "🎉 Congratulations! You have successfully joined:\n"
                f"📢 {REQUIRED_CHANNEL}\n"
                f"💰 {REQUIRED_PAYMENT_GROUP}\n\n"
                "✨ Access Granted! ✨\n\n"
                "Now please use /start command again to access the bot.\n\n"
                "👇 Click below to start:"
            )
            
            new_reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Start Bot", callback_data="start_bot_now")
            ]])
            
            # Check if message needs to be updated
            current_text = query.message.text
            current_markup = query.message.reply_markup
            
            if current_text != new_text or current_markup != new_reply_markup:
                await query.edit_message_text(
                    new_text,
                    reply_markup=new_reply_markup,
                    parse_mode='none'
                )
            else:
                await query.answer("Already verified! Click Start Bot to continue.")
                
        else:
            # Create beautiful buttons for missing requirements
            keyboard = []
            
            if not channel_joined:
                keyboard.append([InlineKeyboardButton(
                    "📢 Join Channel", 
                    url=CHANNEL_INVITE_LINK
                )])
            
            if not group_joined:
                keyboard.append([InlineKeyboardButton(
                    "💰 Join Payment Group", 
                    url=PAYMENT_GROUP_INVITE_LINK
                )])
            
            keyboard.append([InlineKeyboardButton(
                "🔄 Check Again", 
                callback_data="check_membership"
            )])
            
            new_reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Create status indicators
            channel_status = "❌ Not Joined" if not channel_joined else "✅ Joined"
            group_status = "❌ Not Joined" if not group_joined else "✅ Joined"
            
            missing_text = ", ".join(missing)
            
            new_text = (
                f"🔒 Membership Required 🔒\n\n"
                f"To access this bot, please join both:\n\n"
                f"📢 Channel: {REQUIRED_CHANNEL}\n"
                f"└─ Status: {channel_status}\n\n"
                f"💰 Payment Group: {REQUIRED_PAYMENT_GROUP}\n"
                f"└─ Status: {group_status}\n\n"
                f"Missing: {missing_text}\n\n"
                f"👇 Click the buttons below to join 👇\n"
                f"Then click 'Check Again' to verify."
            )
            
            # Check if message needs to be updated
            current_text = query.message.text
            current_markup = query.message.reply_markup
            
            if current_text != new_text or current_markup != new_reply_markup:
                await query.edit_message_text(
                    new_text,
                    reply_markup=new_reply_markup,
                    parse_mode='none'
                )
            else:
                await query.answer("Please join the required channel/group first!")


async def check_membership_requirements(context: CallbackContext, user_id: int) -> tuple:
    return True, True, []
    """
    Check if user has joined both required channel and group
    Returns: (channel_joined, group_joined, missing_list)
    """
    channel_joined = False
    group_joined = False
    missing = []
    
    try:
        # Check channel membership
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if member.status in allowed_status:
                channel_joined = True
            else:
                missing.append("Channel")
        except Exception as e:
            print(f"⚠️ Channel check error: {e}")
            missing.append("Channel")
        
        # Check payment group membership
        try:
            group_member = await context.bot.get_chat_member(chat_id=REQUIRED_PAYMENT_GROUP, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if group_member.status in allowed_status:
                group_joined = True
            else:
                missing.append("Payment Group")
        except Exception as e:
            print(f"⚠️ Payment group check error: {e}")
            missing.append("Payment Group")
        
        return channel_joined, group_joined, missing
        
    except Exception as e:
        print(f"❌ Membership check error: {e}")
        return False, False, ["Channel", "Payment Group"]

async def show_accounts_menu(update: Update, context: CallbackContext):
    """Show accounts selection menu"""
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    accounts = load_accounts()
    
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict) or not user_data.get("accounts"):
        await update.message.reply_text(
            "❌ No accounts found!\n\n"
            "Please contact admin to add accounts for you.\n"
            "Admin: "
        )
        return
    
    user_accounts = user_data["accounts"]
    selected_id = user_data.get("selected_account_id", 1)
    
    message = "📱 Your Accounts 📱\n\n"
    message += "Select an account to use:\n\n"
    
    keyboard = []
    for acc in user_accounts:
        status = "✅" if acc.get('active', True) else "❌"
        login_status = "🔓" if acc.get('token') else "🔒"
        selected_mark = " 👑" if acc['id'] == selected_id else ""
        
        message += f"{status}{login_status} {acc['custom_name']}\n"
        message += f"   └─ 👤 Username: {acc['username']}\n"
        message += f"   └─ 🆔 ID: {acc.get('api_user_id', 'N/A')[:8]}...{selected_mark}\n\n"
        
        callback_data = f"select_account_{acc['id']}"
        keyboard.append([InlineKeyboardButton(
            f"{acc['custom_name']}{selected_mark}", 
            callback_data=callback_data
        )])
    
    keyboard.append([InlineKeyboardButton("🔄 Refresh All", callback_data="refresh_all_accounts")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_accounts_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='none')

async def handle_account_selection(update: Update, context: CallbackContext):
    """Handle account selection from menu"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    if data == "close_accounts_menu":
        await query.delete_message()
        return
    
    if data == "refresh_all_accounts":
        await query.edit_message_text("🔄 Refreshing all accounts...")
        await refresh_user_accounts(user_id)
        
        accounts = load_accounts()
        user_data = accounts.get(user_id_str, {})
        user_accounts = user_data.get("accounts", [])
        selected_id = user_data.get("selected_account_id", 1)
        
        message = "✅ Accounts Refreshed ✅\n\n"
        message += "Updated accounts:\n\n"
        
        for acc in user_accounts:
            status = "✅" if acc.get('active', True) else "❌"
            login_status = "🔓" if acc.get('token') else "🔒"
            selected_mark = " 👑" if acc['id'] == selected_id else ""
            
            message += f"{status}{login_status} {acc['custom_name']}\n"
            message += f"   └─ 👤 Username: {acc['username']}{selected_mark}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📱 Select Account", callback_data="back_to_accounts")],
            [InlineKeyboardButton("❌ Close", callback_data="close_accounts_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        return
    
    if data == "back_to_accounts":
        await show_accounts_menu_from_callback(query, context)
        return
    
    if data.startswith("select_account_"):
        account_id = int(data.split("_")[2])
        
        accounts = load_accounts()
        user_data = accounts.get(user_id_str, {})
        if not isinstance(user_data, dict):
            await query.edit_message_text("❌ No accounts found!")
            return
        
        # Find the account
        selected_account = None
        for acc in user_data.get("accounts", []):
            if acc["id"] == account_id:
                selected_account = acc
                break
        
        if not selected_account:
            await query.edit_message_text("❌ Account not found!")
            return
        
        # Try to login to selected account
        await query.edit_message_text(f"🔄 Logging into {selected_account['custom_name']}...")
        
        token, api_user_id, nickname = await login_api_async(
            selected_account['username'], 
            selected_account['password']
        )
        
        if token:
            # Update account info
            for acc in user_data["accounts"]:
                if acc["id"] == account_id:
                    acc['token'] = token
                    acc['api_user_id'] = api_user_id
                    acc['nickname'] = nickname
                    acc['last_login'] = datetime.now().isoformat()
                    acc['active'] = True
                    break
            
            # Set as selected
            user_data["selected_account_id"] = account_id
            user_data["last_active"] = datetime.now().isoformat()
            accounts[user_id_str] = user_data
            save_accounts(accounts)
            
            # Update AccountManager
            await account_manager.initialize_user(user_id)
            
            message = f"✅ Account Switched Successfully! ✅\n\n"
            message += f"📱 Active Account: {selected_account['custom_name']}\n"
            message += f"👤 Username: {selected_account['username']}\n"
            message += f"🆔 API ID: {api_user_id or 'N/A'}\n"
            message += f"👑 Default: {'Yes' if selected_account.get('default', False) else 'No'}\n\n"
            message += f"🔄 Remaining Checks: {account_manager.get_user_remaining_checks(user_id)}\n"
            message += f"✅ Active Login: {account_manager.get_user_active_accounts_count(user_id)}\n\n"
            message += "You can now start checking numbers!"
            
            keyboard = [
                [InlineKeyboardButton("📱 Switch Account", callback_data="back_to_accounts")],
                [InlineKeyboardButton("🚀 Start Checking", callback_data="start_checking")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await query.edit_message_text(
                f"❌ Failed to login to {selected_account['custom_name']}!\n\n"
                f"Please check credentials or contact admin."
            )

async def show_accounts_menu_from_callback(query, context):
    """Show accounts menu from callback"""
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    accounts = load_accounts()
    
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict) or not user_data.get("accounts"):
        await query.edit_message_text(
            "❌ No accounts found!\n\n"
            "Please contact admin to add accounts for you.\n"
            "Admin: "
        )
        return
    
    user_accounts = user_data["accounts"]
    selected_id = user_data.get("selected_account_id", 1)
    
    message = "📱 Your Accounts 📱\n\n"
    message += "Select an account to use:\n\n"
    
    keyboard = []
    for acc in user_accounts:
        status = "✅" if acc.get('active', True) else "❌"
        login_status = "🔓" if acc.get('token') else "🔒"
        selected_mark = " 👑" if acc['id'] == selected_id else ""
        
        message += f"{status}{login_status} {acc['custom_name']}\n"
        message += f"   └─ 👤 Username: {acc['username']}\n"
        message += f"   └─ 🆔 ID: {acc.get('api_user_id', 'N/A')[:8]}...{selected_mark}\n\n"
        
        callback_data = f"select_account_{acc['id']}"
        keyboard.append([InlineKeyboardButton(
            f"{acc['custom_name']}{selected_mark}", 
            callback_data=callback_data
        )])
    
    keyboard.append([InlineKeyboardButton("🔄 Refresh All", callback_data="refresh_all_accounts")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_accounts_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')

async def refresh_user_accounts(user_id):
    """Refresh all accounts for a user"""
    user_id_str = str(user_id)
    accounts = load_accounts()
    
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict):
        return False
    
    updated_count = 0
    for acc in user_data.get("accounts", []):
        if acc.get('active', True):
            token, api_user_id, nickname = await login_api_async(
                acc['username'], 
                acc['password']
            )
            if token:
                acc['token'] = token
                acc['api_user_id'] = api_user_id
                acc['nickname'] = nickname
                acc['last_login'] = datetime.now().isoformat()
                updated_count += 1
    
    user_data["last_active"] = datetime.now().isoformat()
    accounts[user_id_str] = user_data
    save_accounts(accounts)
    
    # Update AccountManager
    await account_manager.initialize_user(user_id)
    
    return updated_count

async def admin_add_account_custom(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
        
    if not context.args or len(context.args) < 4:
        await update.message.reply_text(
            "❌ Usage: `/addacc user_id custom_name username password`\n\n"
            "Example: `/addacc 7319925086 \"Main Account\" RakibulBN pass123`\n"
            "Example: `/addacc 7319925086 \"Backup Account\" RakibulBN2 pass456`\n\n"
            "Note: Use quotes for custom names with spaces"
        )
        return
        
    try:
        target_user_id = context.args[0]
        custom_name = context.args[1]
        username = context.args[2]
        password = context.args[3]
        
        processing_msg = await update.message.reply_text(f"🔄 Verifying account `{username}`...")
        token, api_user_id, nickname = await login_api_async(username, password)
        
        if not token:
            await processing_msg.edit_text(f"❌ Login failed for `{username}`! Please check credentials.")
            return
            
        accounts = load_accounts()
        user_id_str = str(target_user_id)
        
        # Initialize user structure if not exists
        if user_id_str not in accounts:
            accounts[user_id_str] = {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            user_data = {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        
        # Generate new account ID
        existing_ids = [acc['id'] for acc in user_data.get("accounts", [])]
        new_id = max(existing_ids) + 1 if existing_ids else 1
        
        # Check if account already exists
        account_exists = False
        for acc in user_data.get("accounts", []):
            if acc['username'] == username:
                # Update existing account
                acc['custom_name'] = custom_name
                acc['password'] = password
                acc['token'] = token
                acc['api_user_id'] = api_user_id
                acc['nickname'] = nickname
                acc['last_login'] = datetime.now().isoformat()
                acc['active'] = True
                account_exists = True
                break
        
        if not account_exists:
            # Add new account
            new_account = {
                'id': new_id,
                'custom_name': custom_name,
                'username': username,
                'password': password,
                'token': token,
                'api_user_id': api_user_id,
                'nickname': nickname,
                'last_login': datetime.now().isoformat(),
                'active': True,
                'default': (new_id == 1),  # First account is default
                'added_by': update.effective_user.id,
                'added_at': datetime.now().isoformat(),
                'telegram_username': "",
                'friends': []  # Add friends field
            }
            user_data["accounts"].append(new_account)
        
        # Set as selected if it's the first account
        if new_id == 1:
            user_data["selected_account_id"] = 1
        
        accounts[user_id_str] = user_data
        save_accounts(accounts)
        
        # Update AccountManager
        if user_id_str in account_manager.user_tokens:
            await account_manager.initialize_user(int(target_user_id))
        
        await processing_msg.edit_text(
            f"✅ Account Added Successfully! ✅\n\n"
            f"👤 User ID: `{target_user_id}`\n"
            f"📛 Custom Name: `{custom_name}`\n"
            f"👤 Username: `{username}`\n"
            f"🔑 Password: `{password}`\n"
            f"🆔 API User ID: `{api_user_id or 'N/A'}`\n"
            f"🎯 Account ID: `{new_id}`\n"
            f"👑 Default: `{'Yes' if new_id == 1 else 'No'}`\n"
            f"✅ Auto-login: Successful"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def refresh_server(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # ✅ চ্যানেল মেম্বারশিপ চেক
    if user_id != ADMIN_ID:
        REQUIRED_CHANNEL = "@CashxByte"
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if member.status not in allowed_status:
                await update.message.reply_text("❌ Please join @CashxByte first to use this feature.")
                return
        except:
            await update.message.reply_text("❌ Please join @CashxByte first to use this feature.")
            return
    
    processing_msg = await update.message.reply_text("🔄 Refreshing your accounts...")
    
    active_accounts = await account_manager.initialize_user(user_id)
    
    remaining = account_manager.get_user_remaining_checks(user_id)
    total_accounts = account_manager.get_user_accounts_count(user_id)
    
    if active_accounts == 0:
        await processing_msg.edit_text(
            f"❌ No accounts could be logged in!\n\n"
            f"Please contact admin to check your account credentials.\n"
            f"Admin: "
        )
        return
    
    await processing_msg.edit_text(
        f"✅ Accounts Refreshed Successfully!\n\n"
        f"📊 Result:\n"
        f"• Successfully Logged In: {active_accounts}\n"
        f"• Failed: {total_accounts - active_accounts}"
    )

async def async_add_number_optimized(token, phone, msg, username, serial_number=None, user_id=None, cc='1'):
    """
    Add number with specific country code - UPDATED with cc storage
    """
    try:
        async with aiohttp.ClientSession() as session:
            added = await add_number_async(session, token, cc, phone)
            prefix = f"{serial_number}. " if serial_number else ""
            
            if added:
                # Tracking update
                tracking = load_tracking()
                user_id_str = str(user_id)
                
                if user_id_str not in tracking["today_added"]:
                    tracking["today_added"][user_id_str] = 0
                
                tracking["today_added"][user_id_str] += 1
                save_tracking(tracking)
                
                stats = load_stats()
                stats["total_checked"] = stats.get("total_checked", 0) + 1
                stats["today_checked"] = stats.get("today_checked", 0) + 1
                save_stats(stats)
                
                await msg.edit_text(f"{prefix}+{cc} {phone} 🔵 In Progress")
                
                # IMPORTANT: Store number in active_numbers with cc
                active_numbers[phone] = {
                    'token': token,
                    'username': username,
                    'message_id': msg.message_id,
                    'user_id': user_id,
                    'chat_id': msg.chat_id,
                    'cc': cc,
                    'phone': phone
                }
                print(f"✅ Number {phone} added to active_numbers with CC={cc}")
                print(f"📱 Active numbers count: {len(active_numbers)}")
                
            else:
                # Get actual status
                status_code, status_name, record_id, actual_phone = await get_status_with_actual_phone(session, token, phone)
                
                if actual_phone and actual_phone != phone:
                    display_phone = actual_phone
                    status_name = f"{status_name} - Wrong Format"
                else:
                    display_phone = phone
                
                if status_code == 16:
                    await msg.edit_text(f"{prefix}+{cc} {display_phone} 🚫 Already Exists")
                    account_manager.release_token(token)
                    return
                
                await msg.edit_text(f"{prefix}+{cc} {display_phone} ❌ Add Failed")
                account_manager.release_token(token)
                
    except Exception as e:
        print(f"❌ Add error for {phone} (CC:{cc}): {e}")
        prefix = f"{serial_number}. " if serial_number else ""
        await msg.edit_text(f"{prefix}+{cc} {phone} ❌ Add Failed")
        account_manager.release_token(token)

async def get_status_with_actual_phone(session, token, phone):
    """
    Get status with actual phone number from API response
    Returns: (status_code, status_name, record_id, actual_phone)
    """
    try:
        headers = {"Admin-Token": token}
        status_url = f"{BASE_URL}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
        
        async with session.get(status_url, headers=headers, timeout=10) as response:
            response_text = await response.text()
            
            if response.status == 401:
                print(f"❌ Token expired for {phone}")
                return -1, "❌ Token Expired", None, phone
            
            try:
                res = await response.json(content_type=None)
            except Exception as json_error:
                print(f"❌ JSON parse attempt 1 failed for {phone}: {json_error}")
                try:
                    cleaned_text = response_text.strip()
                    if cleaned_text.startswith('\ufeff'):
                        cleaned_text = cleaned_text[1:]
                    res = json.loads(cleaned_text)
                except Exception as e2:
                    print(f"❌ Manual JSON parse also failed for {phone}: {e2}")
                    print(f"❌ Raw response: {response_text[:500]}")
                    return -2, "❌ API Error", None, phone
            
            # Check for specific error messages
            if res.get('code') == 28004:
                print(f"❌ Login required for {phone}")
                return -1, "❌ Token Expired", None, phone
            
            error_msg = res.get('msg', '').lower()
            if any(keyword in error_msg for keyword in ["already exists", "cannot register", "number exists", "invalid", "wrong format"]):
                print(f"❌ Number {phone} has issue: {error_msg}")
                return 16, f"🚫 {res.get('msg', 'Already Exists')}", None, phone
            
            if res.get('code') in (400, 409):
                error_msg = res.get('msg', f'Error {res.get("code")}')
                print(f"❌ Number {phone} has issue, code {res.get('code')}: {error_msg}")
                return 16, f"🚫 {error_msg}", None, phone
            
            if (res and "data" in res and "records" in res["data"] and 
                res["data"]["records"] and len(res["data"]["records"]) > 0):
                record = res["data"]["records"][0]
                status_code = record.get("registrationStatus")
                record_id = record.get("id")
                
                # Get actual phone number from API
                actual_phone = record.get("phoneNum")
                if not actual_phone:
                    # Try to extract from other fields
                    phone_fields = ["phone", "phoneNumber", "mobile", "number"]
                    for field in phone_fields:
                        if field in record:
                            actual_phone = record[field]
                            break
                
                status_name = status_map.get(status_code, f"🔸 Status {status_code}")
                return status_code, status_name, record_id, actual_phone or phone
            
            # If no records but successful response
            if res and "data" in res:
                return None, "🚫 Already register or wrong number", None, phone
            
            return None, "🚫 API Response Error", None, phone
            
    except Exception as e:
        print(f"❌ Status error for {phone}: {type(e).__name__}: {e}")
        return -2, "🔄 Refresh Server", None, phone

async def track_status_optimized(context: CallbackContext):
    data = context.job.data
    phone = data['phone']
    token = data['token']
    username = data['username']
    user_id = data['user_id']
    checks = data['checks']
    last_status = data.get('last_status', '🔵 Processing...')
    serial_number = data.get('serial_number')
    last_status_code = data.get('last_status_code')
    cc = data.get('cc', '1')  # Add country code
    
    try:
        async with aiohttp.ClientSession() as session:
            status_code, status_name, record_id, actual_phone = await get_status_with_actual_phone(session, token, phone)
        
        prefix = f"{serial_number}. " if serial_number else ""
        
        # Show actual phone if different
        display_phone = actual_phone if actual_phone and actual_phone != phone else phone
        
        if status_code == -1:
            account_manager.release_token(token)
            error_text = f"{prefix}+{cc} {display_phone} ❌ Token Error (Auto-Retry)"
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=error_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Message update failed for {phone}: {e}")
            return
        
        # IMPORTANT FIX: Stop tracking immediately for wrong/duplicate numbers
        immediate_stop_codes = []  # Not Register, Ban, Already Exists, API Error
        
        if status_code in immediate_stop_codes:
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
                print(f"🛑 Immediate stop for {phone} - Status: {status_name}")
            
            final_text = f"{prefix}+{cc} {display_phone} {status_name}"
            
            # Add extra info for wrong format
            if status_code == 16 and actual_phone != phone:
                final_text += f""
            
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=final_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Final message update failed for {phone}: {e}")
            return
        
        if status_code == 2:
            if phone not in active_numbers:
                active_numbers[phone] = {
                    'token': token,
                    'username': username,
                    'message_id': data['message_id'],
                    'user_id': user_id,
                    'chat_id': data['chat_id']
                }
                print(f"✅ Number {phone} added to active_numbers for OTP submission")
                print(f"📱 Active numbers count: {len(active_numbers)}")
            else:
                print(f"ℹ️ Number {phone} already in active_numbers")
        
        if status_code == 1 and last_status_code != 1:
            print(f"🎉 SUCCESS detected for {phone} by user {user_id}")
            
            tracking = load_tracking()
            user_id_str = str(user_id)
            
            if phone in tracking.get("today_success", {}):
                print(f"ℹ️ Number {phone} already had success today, skipping count")
            else:
                print(f"✅ First time SUCCESS today for {phone} by user {user_id_str}")
                
                otp_stats = load_otp_stats()
                otp_stats["total_success"] = otp_stats.get("total_success", 0) + 1
                otp_stats["today_success"] = otp_stats.get("today_success", 0) + 1
                
                if user_id_str not in otp_stats["user_stats"]:
                    otp_stats["user_stats"][user_id_str] = {
                        "total_success": 0,
                        "today_success": 0,
                        "yesterday_success": 0,
                        "username": username,
                        "full_name": ""
                    }
                otp_stats["user_stats"][user_id_str]["total_success"] = otp_stats["user_stats"][user_id_str].get("total_success", 0) + 1
                otp_stats["user_stats"][user_id_str]["today_success"] = otp_stats["user_stats"][user_id_str].get("today_success", 0) + 1
                
                tracking["today_success"][phone] = user_id_str
                
                if "today_success_counts" not in tracking:
                    tracking["today_success_counts"] = {}
                
                if user_id_str not in tracking["today_success_counts"]:
                    tracking["today_success_counts"][user_id_str] = 0
                tracking["today_success_counts"][user_id_str] = tracking["today_success_counts"][user_id_str] + 1
                
                save_otp_stats(otp_stats)
                save_tracking(tracking)
                print(f"✅ Success count updated for user {user_id_str} - Total: {tracking['today_success_counts'][user_id_str]}")
        
        if status_name != last_status:
            new_text = f"{prefix}+{cc} {display_phone} {status_name}"
            
            # Show actual phone if different
            if actual_phone and actual_phone != phone:
                new_text += f""
            
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=new_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Message update failed for {phone}: {e}")
        
        final_states = [0, 1, 4, 7, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, -2]
        if status_code in final_states:
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
                print(f"🗑️ Number {phone} removed from active_numbers (final state: {status_code})")
            
            if status_code not in [1, 2]:
                deleted_count = await delete_number_from_all_accounts_optimized(phone, user_id)
            
            final_text = f"{prefix}+{cc} {display_phone} {status_name}"
            
            # Show actual phone if different
            if actual_phone and actual_phone != phone:
                final_text += f""
            
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=final_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Final message update failed for {phone}: {e}")
            return
        
        if checks >= 200:  # Reduced from 150 to 100
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
                print(f"⏰ Number {phone} removed from active_numbers (timeout)")
            
            if status_code not in [1, 2]:
                deleted_count = await delete_number_from_all_accounts_optimized(phone, user_id)
            
            timeout_text = f"{prefix}+{cc} {display_phone} 🟡 Try Later"
            
            # Show actual phone if different
            if actual_phone and actual_phone != phone:
                timeout_text += f""
            
            try:
                await context.bot.edit_message_text(
                    chat_id=data['chat_id'], 
                    message_id=data['message_id'],
                    text=timeout_text
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    print(f"❌ Timeout message update failed for {phone}: {e}")
            return
        
        if context.job_queue:
            context.job_queue.run_once(
                track_status_optimized, 
                2,  # Start checking after 2 seconds
                data={
                    **data, 
                    'checks': checks + 1, 
                    'last_status': status_name,
                    'last_status_code': status_code,
                    'cc': cc  # Pass country code
                }
            )
        else:
            print("❌ JobQueue not available, cannot schedule status check")
    except Exception as e:
        print(f"❌ Tracking error for {phone}: {e}")
        account_manager.release_token(token)

async def process_multiple_numbers(update: Update, context: CallbackContext, text: str):
    numbers_data = extract_phone_numbers(text)  # Now returns dict with cc and phone
    
    if not numbers_data:
        await update.message.reply_text("❌ কোনো ভ্যালিড নম্বর পাওয়া যায়নি!")
        return
    
    user_id = update.effective_user.id
    
    for index, num_data in enumerate(numbers_data, 1):
        remaining = account_manager.get_user_remaining_checks(user_id)
        if remaining <= 0:
            active_accounts = account_manager.get_user_active_accounts_count(user_id)
            await update.message.reply_text(f"🚀 Refresh Server.. Processing  {active_accounts * MAX_PER_ACCOUNT}")
            break
            
        token_data = account_manager.get_next_available_token(user_id)
        if not token_data:
            await update.message.reply_text("❌ No available accounts! Please refresh server first.")
            break
            
        token, username = token_data
        
        # Extract phone and cc
        phone = num_data['phone']
        cc = num_data.get('cc', '1')  # Default to 1 if not found
        
        # Stats update
        stats = load_stats()
        stats["total_checked"] = stats.get("total_checked", 0) + 1
        stats["today_checked"] = stats.get("today_checked", 0) + 1
        save_stats(stats)
        
        msg = await update.message.reply_text(f"{index}. {phone} (CC:{cc}) 🔵 Processing...")
        asyncio.create_task(async_add_number_optimized(
            token, phone, msg, username, index, user_id, cc
        ))
        
        if context.job_queue:
            context.job_queue.run_once(
                track_status_optimized, 
                2,
                data={
                    'chat_id': update.message.chat_id,
                    'message_id': msg.message_id,
                    'phone': phone,
                    'token': token,
                    'username': username,
                    'checks': 0,
                    'last_status': '🔵 Processing...',
                    'serial_number': index,
                    'user_id': user_id,
                    'last_status_code': None
                }
            )
            
async def handle_message_optimized(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Check membership requirements for ALL non-admin users
    if user_id != ADMIN_ID:
        channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
        
        if not (channel_joined and group_joined):
            # ... membership check code (same as before)
            return
    
    # Check if user has accounts
    if account_manager.get_user_accounts_count(user_id) == 0 and user_id != ADMIN_ID:
        await update.message.reply_text(
            f"❌ No Accounts Found!\n\n"
            f"Please contact admin to add accounts for you.\n"
            f"👤 Admin: ",
            parse_mode='none'
        )
        return
    
    text = update.message.text.strip()
    
    # Handle OTP submission if replying to a message
    if update.message.reply_to_message:
        await handle_otp_submission(update, context)
        return
    
    # Handle button clicks
    if text == "🚀 Refresh Server":
        await refresh_server(update, context)
        return
    if text == "📦 My Settlements":
        await show_user_settlements(update, context)
        return
    if text == "📊 Statistics":
        await statistics_command(update, context)
        return
    if text == "📱 Switch Account":
        await show_accounts_menu(update, context)
        return
        
    # Admin menu options
    if user_id == ADMIN_ID:
        if text == "➕ Add Account":
            await update.message.reply_text("👤 Add Account\n\nUsage: `/addacc user_id custom_name username password`\n\nExample: `/addacc 123456789 \"Main Account\" user1 pass123`", parse_mode='none')
            return
        if text == "📋 List Accounts":
            await admin_list_accounts(update, context)
            return
        if text == "💰 Set Rate":
            await update.message.reply_text("💰 Set Settlement Rate\n\nUsage: `/setrate amount [date] [country...]`\n📢 Notice: `/setrate notice Your message`\n\nExample: `/setrate 0.08`\n`/setrate 0.07 canada 0.04 benin`", parse_mode='none')
            return
        if text == "📊 Statistics":
            await statistics_command(update, context)
            return
    
    # Extract phone numbers from text
    numbers_data = extract_phone_numbers(text)
    
    if numbers_data:
        # Take the first valid number
        if len(numbers_data) > 1:
            valid_numbers = []
            for num_data in numbers_data:
                phone = num_data['phone']
                cc = num_data.get('cc', '1')
                
                if cc == '229' and len(phone) == 8:
                    valid_numbers.append(num_data)
                elif 7 <= len(phone) <= 15:
                    valid_numbers.append(num_data)
            
            if valid_numbers:
                num_data = valid_numbers[0]
                await update.message.reply_text(
                    f"ℹ️ Found {len(numbers_data)} possible numbers.\n"
                    f"✅ Processing: +{num_data['cc']} {num_data['phone']}",
                    parse_mode='none'
                )
            else:
                num_data = numbers_data[0]
        else:
            num_data = numbers_data[0]
        
        phone = num_data['phone']
        cc = num_data.get('cc', '1')
        
        # Check remaining checks
        remaining = account_manager.get_user_remaining_checks(user_id)
        if remaining <= 0:
            active_accounts = account_manager.get_user_active_accounts_count(user_id)
            await update.message.reply_text(f"🚀 Refresh Server Required\n\nProcessing {active_accounts * MAX_PER_ACCOUNT} numbers. Please wait or refresh.", parse_mode='none')
            return
        
        # Get available token
        token_data = account_manager.get_next_available_token(user_id)
        if not token_data:
            await update.message.reply_text("❌ No Available Accounts!\n\nPlease refresh server first using the button.", parse_mode='none')
            return
        
        token, username = token_data
        
        # Update stats
        stats = load_stats()
        stats["total_checked"] = stats.get("total_checked", 0) + 1
        stats["today_checked"] = stats.get("today_checked", 0) + 1
        save_stats(stats)
        
        # Send processing message
        msg = await update.message.reply_text(f"+{cc} {phone} 🔵 Processing...")
        
        # Start async task to add number
        asyncio.create_task(async_add_number_optimized(
            token, phone, msg, username, user_id=user_id, cc=cc
        ))
        
        # Schedule status tracking
        if context.job_queue:
            context.job_queue.run_once(
                track_status_optimized, 
                2,
                data={
                    'chat_id': update.message.chat_id,
                    'message_id': msg.message_id,
                    'phone': phone,
                    'token': token,
                    'username': username,
                    'checks': 0,
                    'last_status': '🔵 Processing...',
                    'user_id': user_id,
                    'last_status_code': None,
                    'cc': cc
                }
            )
        
        return
    
    # If no phone numbers found
    await update.message.reply_text(
        "❌ No Valid Phone Numbers Found!\n\n"
        "📱 Supported Formats:\n"
        "• `+1 (234) 567-8900`\n"
        "• `+44 7911 123456`\n"
        "• `+229 47879817`\n"
        "• `(229) 47879817`\n"
        "• `22947879817`\n\n"
        "💡 Tip: Always include country code with + sign!",
        parse_mode='none'
    )

def run_fastapi():
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=RENDER_PORT,
        access_log=False
    )

def main():
    print(f"🚀 Starting Bot on Render (Port: {RENDER_PORT})...")

    # 🔹 FastAPI keep-alive
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    print(f"🌐 FastAPI server started on port {RENDER_PORT}")

    # 🔹 Async loop setup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def initialize_bot():
        await account_manager.initialize_user(ADMIN_ID)

        asyncio.create_task(keep_alive_enhanced())
        asyncio.create_task(random_ping())
        asyncio.create_task(immediate_ping())

        print("🤖 Bot initialized successfully with enhanced keep-alive!")

    loop.run_until_complete(initialize_bot())

    # 🔹 Telegram Application
    application = Application.builder().token(BOT_TOKEN).build()

    # ───────────────── COMMAND HANDLERS ─────────────────

    application.add_handler(CommandHandler("start", start))

    # ✅ Account system
    application.add_handler(CommandHandler("addacc", admin_add_account_custom))
    application.add_handler(CommandHandler("removeacc", admin_remove_account))
    application.add_handler(CommandHandler("accounts", show_accounts_menu))

    # 🔹 Admin / System
    application.add_handler(CommandHandler("refresh", refresh_server))
    application.add_handler(CommandHandler("setrate", set_settlement_rate))
    application.add_handler(CommandHandler("settlements", show_user_settlements))

    # 🔹 Statistics
    application.add_handler(CommandHandler("stats", statistics_command))
    application.add_handler(CommandHandler("statistics", statistics_command))

    # 🆕 Fake Payment (Admin Only)
    application.add_handler(CommandHandler("fakepay", fake_payment_command))
    application.add_handler(CommandHandler("fakeenable", fake_payment_toggle_command))
    application.add_handler(CommandHandler("fakedisable", fake_payment_toggle_command))
    application.add_handler(CommandHandler("fakestatus", fake_payment_status_command))

    # ───────────────── CALLBACK HANDLERS ─────────────────

    application.add_handler(
        CallbackQueryHandler(handle_statistics_callback, pattern=r"^stats_")
    )

    application.add_handler(
        CallbackQueryHandler(handle_settlement_callback, pattern=r"^settlement_")
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_account_selection,
            pattern=r"^(select_account_|refresh_all_accounts|close_accounts_menu|back_to_accounts|start_checking)"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_payment_callback,
            pattern=r"^(payment_complete_|payment_details_|close_details)"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_membership_check,
            pattern=r"^check_membership$"
        )
    )

    # ───────────────── MESSAGE HANDLER ─────────────────

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_optimized)
    )

    # ───────────────── JOB QUEUE ─────────────────

    if application.job_queue:
        application.job_queue.run_daily(
            reset_daily_stats,
            time=datetime.strptime("10:00", "%H:%M").time()
        )
    else:
        print("❌ JobQueue not available, daily stats reset not scheduled")

    # ───────────────── START BOT ─────────────────

    print("🚀 Bot starting polling with 24/7 keep-alive...")

    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        print(f"❌ Bot error: {e}")
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()

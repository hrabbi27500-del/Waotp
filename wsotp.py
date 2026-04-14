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
    level=logging.ERROR,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", ""))
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
        "https://waotp-fvx0.onrender.com"
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
            # NEW: Add in_progress_timestamp for tracking time
            if "in_progress_timestamp" not in data or not isinstance(data["in_progress_timestamp"], dict):
                data["in_progress_timestamp"] = {}
            if "pending_delete" not in data or not isinstance(data["pending_delete"], dict):
                data["pending_delete"] = {}
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
            "in_progress_timestamp": {},
            "pending_delete": {},
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
            "📊 Admin Menu\n\nChoose:",
            reply_markup=reply_markup
        )
    else:
        # Regular users see their own statistics
        await show_user_statistics(update, context)
        
        # Also send wallet button separately
        keyboard = [
            [InlineKeyboardButton("💳 My Wallet", callback_data="open_wallet")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💳 Manage your payment methods:",
            reply_markup=reply_markup
        )

async def wallet_command(update: Update, context: CallbackContext):
    """Show user's wallet with payment methods"""
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    # Check channel membership
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
    
    accounts = load_accounts()
    
    if user_id_str not in accounts:
        accounts[user_id_str] = {
            "accounts": [],
            "selected_account_id": 1,
            "telegram_username": "",
            "last_active": datetime.now().isoformat(),
            "payment_methods": {}
        }
        save_accounts(accounts)
    
    user_data = accounts[user_id_str]
    payment_methods = user_data.get("payment_methods", {})
    
    # Create message
    message = f"💳 YOUR WALLET\n\n"
    message += f"👤 {update.effective_user.first_name}\n"
    message += f"🆔 ID: `{user_id}`\n\n"
    
    if payment_methods:
        message += f"📋 Saved Payment Methods:\n"
        for method, data in payment_methods.items():
            payment_id = data.get('id', 'N/A')
            # Mask for display
            if len(payment_id) > 8:
                masked_id = payment_id[:4] + "****" + payment_id[-4:]
            else:
                masked_id = payment_id
            message += f"├─ {method.upper()}: `{masked_id}`\n"
            if data.get('details'):
                message += f"│  └─ {data['details'][:30]}\n"
        message += f"\n"
    else:
        message += f"❌ No payment methods added yet!\n\n"
    
    message += f"➕ Add Payment Method:\n"
    message += f"• BKash - Click below\n"
    message += f"• Nagad - Click below\n"
    message += f"• Binance - Click below\n\n"
    message += f"💡 Your payment info is secure and only visible to admin."
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("➕ BKash", callback_data="add_bkash"),
            InlineKeyboardButton("➕ Nagad", callback_data="add_nagad")
        ],
        [
            InlineKeyboardButton("➕ Binance", callback_data="add_binance")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close_wallet")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def handle_wallet_callback(update: Update, context: CallbackContext):
    """Handle wallet button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    if data == "close_wallet":
        await query.delete_message()
        return
    
    if data == "add_bkash":
        # Ask for BKash number
        context.user_data['pending_payment_method'] = 'bkash'
        await query.edit_message_text(
            f"💳 ADD BKASH NUMBER\n\n"
            f"Please send your BKash number.\n\n"
            f"Example: `017XXXXXXXX`\n\n"
            f"⚠️ While adding payment method, phone number checking is OFF.\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
    
    elif data == "add_nagad":
        # Ask for Nagad number
        context.user_data['pending_payment_method'] = 'nagad'
        await query.edit_message_text(
            f"💳 ADD NAGAD NUMBER\n\n"
            f"Please send your Nagad number.\n\n"
            f"Example: `018XXXXXXXX`\n\n"
            f"⚠️ While adding payment method, phone number checking is OFF.\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )
    
    elif data == "add_binance":
        # Ask for Binance Pay ID
        context.user_data['pending_payment_method'] = 'binance'
        await query.edit_message_text(
            f"💳 ADD BINANCE PAY ID\n\n"
            f"Please send your Binance Pay ID.\n\n"
            f"Example: `8277372966555`\n\n"
            f"⚠️ While adding payment method, phone number checking is OFF.\n"
            f"Type /cancel to cancel.",
            parse_mode='Markdown'
        )


async def handle_payment_method_input(update: Update, context: CallbackContext):
    """Handle user input for payment method details (OTP processing OFF during this time)"""
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    text = update.message.text.strip()
    
    # Check if user is in payment method adding mode
    if 'pending_payment_method' not in context.user_data:
        return
    
    # If user types /cancel, exit payment method mode
    if text.lower() == '/cancel':
        del context.user_data['pending_payment_method']
        await update.message.reply_text(
            "❌ Payment method addition cancelled.\n\n"
            "You can now send phone numbers normally.",
            parse_mode='none'
        )
        return
    
    method = context.user_data['pending_payment_method']
    
    # Validate input based on method
    if method in ['bkash', 'nagad']:
        # Validate phone number (Bangladeshi number)
        if not re.match(r'^01[3-9]\d{8}$', text):
            await update.message.reply_text(
                f"❌ Invalid {method.upper()} number!\n\n"
                f"Please send a valid Bangladeshi number.\n"
                f"Example: `017XXXXXXXX`\n\n"
                f"Type /cancel to cancel.",
                parse_mode='Markdown'
            )
            return
    
    elif method == 'binance':
        # Validate Binance Pay ID (should be numbers, at least 5 digits)
        if not re.match(r'^\d{5,}$', text):
            await update.message.reply_text(
                f"❌ Invalid Binance Pay ID!\n\n"
                f"Please send a valid Binance Pay ID.\n"
                f"Example: `8277372966555`\n\n"
                f"Type /cancel to cancel.",
                parse_mode='Markdown'
            )
            return
    
    # Save payment method
    accounts = load_accounts()
    
    if user_id_str not in accounts:
        accounts[user_id_str] = {
            "accounts": [],
            "selected_account_id": 1,
            "telegram_username": "",
            "last_active": datetime.now().isoformat(),
            "payment_methods": {}
        }
    
    if "payment_methods" not in accounts[user_id_str]:
        accounts[user_id_str]["payment_methods"] = {}
    
    # Add or update payment method
    accounts[user_id_str]["payment_methods"][method] = {
        "id": text,
        "details": "",
        "added_by": user_id,
        "added_at": datetime.now().isoformat()
    }
    
    save_accounts(accounts)
    
    # Clear pending state - IMPORTANT: Exit payment method mode
    del context.user_data['pending_payment_method']
    
    # Mask for display
    masked_id = text
    if len(text) > 8:
        masked_id = text[:4] + "****" + text[-4:]
    
    await update.message.reply_text(
        f"✅ {method.upper()} Added Successfully!\n\n"
        f"💰 Method: {method.upper()}\n"
        f"🔢 ID: `{text}`\n"
        f"🔒 Masked: `{masked_id}`\n\n"
        f"You can now send phone numbers normally.\n"
        f"Use /wallet to view all your payment methods.",
        parse_mode='Markdown'
    )
    
    # Notify admin
    username = update.effective_user.username or "No username"
    full_name = update.effective_user.full_name or "Unknown"
    
    admin_message = f"💳 NEW PAYMENT METHOD ADDED BY USER\n\n"
    admin_message += f"👤 User: {full_name}\n"
    admin_message += f"🆔 ID: `{user_id}`\n"
    admin_message += f"📛 Username: @{username}\n\n"
    admin_message += f"💰 Method: {method.upper()}\n"
    admin_message += f"🔢 ID: `{text}`\n"
    admin_message += f"🔒 Masked: `{masked_id}`\n\n"
    admin_message += f"📅 Added: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
    
    await context.bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')

async def cancel_payment_method(update: Update, context: CallbackContext):
    """Cancel adding payment method and re-enable phone number processing"""
    if 'pending_payment_method' in context.user_data:
        method = context.user_data['pending_payment_method']
        del context.user_data['pending_payment_method']
        await update.message.reply_text(
            f"❌ {method.upper()} payment method addition cancelled.\n\n"
            f"✅ Phone number checking is now back ON.\n"
            f"You can now send phone numbers normally.",
            parse_mode='none'
        )
    else:
        await update.message.reply_text(
            "ℹ️ No pending payment method addition.\n\n"
            "✅ Phone number checking is active.\n"
            "Send a phone number to check.",
            parse_mode='none'
        )

async def handle_wallet_open(update: Update, context: CallbackContext):
    """Handle open wallet from statistics"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "open_wallet":
        # Call wallet command
        await wallet_command(update, context)
        await query.delete_message()

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
                            
                            # Extract API rate from records - FIXED
                            api_rates = {}
                            for record in records:
                                country = record.get('countryName') or record.get('country') or 'Unknown'
                                country = country.strip(', ')
                                # Get receiptPrice from record (this is the API rate)
                                receipt_price = record.get('receiptPrice', 0)
                                if receipt_price > 0:
                                    api_rates[country] = receipt_price
                                    print(f"📊 API Rate for {country}: ${receipt_price}")
                            
                            return {
                                'records': records,
                                'total': total,
                                'pages': pages,
                                'page': page,
                                'size': page_size,
                                'api_rates': api_rates
                            }, None
                        else:
                            print(f"⚠️ No 'records' key in data: {data}")
                            return {
                                'records': [],
                                'total': 0,
                                'pages': 0,
                                'page': page,
                                'size': page_size,
                                'api_rates': {}
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
                                                commission: float, friends_details: list, 
                                                payment_method: str, payment_id: str, is_fake: bool = False):
    """
    Forward payment confirmation to a separate Telegram group with MASKED payment ID
    """
    try:
        # Mask user ID
        masked_user_id = user_id
        if len(user_id) >= 6:
            first_three = user_id[:3]
            last_three = user_id[-3:]
            masked_user_id = f"{first_three}xxxx{last_three}"
        elif len(user_id) >= 4:
            masked_user_id = f"{user_id[:2]}xx{user_id[-2:]}"
        else:
            masked_user_id = "xxx"
        
        # Mask username
        masked_username = username
        if len(username) >= 4:
            first_two = username[:2]
            last_two = username[-2:]
            masked_username = f"{first_two}xxx{last_two}"
        elif len(username) >= 3:
            masked_username = f"{username[:1]}xx{username[-1:]}"
        else:
            masked_username = "xxx"
        
        # Mask telegram username
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
        
        current_time = datetime.now().strftime('%d %B %Y, %H:%M:%S')
        
        # Payment ID is already masked when passed to this function
        message = f"💰 PAYMENT CONFIRMATION\n\n"
        message += f"🕐 {current_time}\n\n"
        
        message += f"👤 {masked_username}\n"
        message += f"🆔 {masked_user_id}\n"
        if masked_telegram:
            message += f"📱 @{masked_telegram}\n\n"
        
        message += "📊 DETAILS\n"
        message += f"├─ Personal: {personal_count} (${personal_earnings:.2f})\n"
        
        if friends_details and len(friends_details) > 0:
            message += f"├─ Friends: {len(friends_details)} (${friend_earnings:.2f})\n"
        
        if commission > 0:
            message += f"├─ Commission: ${commission:.2f}\n"
        
        message += f"└─ Total: ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
        
        message += f"💳 Payment Method: {payment_method.upper()}\n"
        message += f"🔢 Payment ID: `{payment_id}`\n\n"
        
        if is_fake:
            message += f"⚠️ Test Mode\n\n"
        
        message += f"✅ Status: Completed\n"
        message += f"🔒 Privacy: Masked\n\n"
        message += f"#PaymentConfirmation #{masked_user_id}"
        
        try:
            await context.bot.send_message(
                chat_id=PAYMENT_GROUP_ID,
                text=message,
                parse_mode='Markdown'
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
        
        # CRITICAL FIX: Remove from timeout tracking immediately after OTP submission
        phone_key = f"{data_cc}_{phone}_{user_id}"
        tracking = load_tracking()
        if phone_key in tracking.get("in_progress_timestamp", {}):
            del tracking["in_progress_timestamp"][phone_key]
            print(f"✅ Removed {phone_key} from in_progress_timestamp (OTP submitted)")
        if phone_key in tracking.get("pending_delete", {}):
            del tracking["pending_delete"][phone_key]
        save_tracking(tracking)
        
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
        phone_key = f"{cc}_{phone}_{user_id}"
        
        # Token expired check
        if status_code == -1:
            # Remove from timeout tracking
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
                print(f"🗑️ Removed {phone_key} from in_progress_timestamp (token expired)")
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            
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
        
        # CRITICAL FIX: Remove from timeout tracking IMMEDIATELY when status changes from 2
        if last_status_code == 2 and status_code != 2:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
                print(f"✅ Removed {phone_key} from in_progress_timestamp - Status changed from {last_status_code} to {status_code}")
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
        
        # Add to timeout tracker only when status becomes 2 and not already tracked
        if status_code == 2:
            tracking = load_tracking()
            if "in_progress_timestamp" not in tracking:
                tracking["in_progress_timestamp"] = {}
            
            # Only add if not already tracked
            if phone_key not in tracking["in_progress_timestamp"]:
                tracking["in_progress_timestamp"][phone_key] = datetime.now().isoformat()
                save_tracking(tracking)
                print(f"⏰ Started timeout timer for {phone} (Key: {phone_key})")
        
        # Success handling
        if status_code == 1 and last_status_code != 1:
            print(f"🎉 SUCCESS detected for {phone} by user {user_id}")
            
            # Immediately remove from timeout tracking on success
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
                print(f"✅ Removed {phone_key} from in_progress_timestamp (SUCCESS)")
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            
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
                print(f"✅ Success count updated for user {user_id_str} - Total: {tracking['today_success_counts'][user_id_str]}")
            else:
                save_tracking(tracking)
        
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
        
        # Final states - stop tracking
        final_states = [0, 1, 4, 7, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, -2]
        
        if status_code in final_states:
            # Remove from timeout tracking
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
                print(f"🗑️ Removed {phone_key} from in_progress_timestamp (final state: {status_code})")
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            
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
        
        # Timeout check
        if checks >= 100:
            # Remove from timeout tracking
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            
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
                5,
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

async def handle_force_payment_complete(update: Update, context: CallbackContext):
    """Force payment complete for users without payment method"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("force_payment_complete_"):
        parts = data.split("_")
        # force_payment_complete_userid_date
        if len(parts) >= 5:
            user_id = parts[3]
            date_str = parts[4]
        else:
            await query.edit_message_text("❌ Invalid request!")
            return
        
        await query.edit_message_text(f"🔄 Processing payment for user {user_id}...")
        
        try:  # <-- ADD THIS TRY BLOCK
            # Get user data
            accounts = load_accounts()
            user_data = accounts.get(user_id, {})
            
            if not user_data:
                await query.edit_message_text(f"❌ User {user_id} not found!")
                return
            
            user_accounts = user_data.get("accounts", [])
            username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
            telegram_username = user_data.get('telegram_username', '')
            payment_methods = user_data.get('payment_methods', {})
            
            # Extract payment details from original message
            original_text = query.message.text
            
            import re
            
            personal_earnings = 0
            friend_earnings = 0
            commission = 0
            total_usd = 0
            total_bdt = 0
            personal_count = 0
            friend_count = 0
            friends_details = []
            
            # Extract values from message
            personal_match = re.search(r'├─ 🔢 Personal: (\d+)', original_text)
            if not personal_match:
                personal_match = re.search(r'Personal: (\d+)', original_text)
            if personal_match:
                personal_count = int(personal_match.group(1))
            
            earnings_match = re.search(r'Personal: \d+ \(\$([\d\.]+)\)', original_text)
            if not earnings_match:
                earnings_match = re.search(r'Personal Earnings: \$([\d\.]+)', original_text)
            if earnings_match:
                personal_earnings = float(earnings_match.group(1))
            
            total_match = re.search(r'Total: \$([\d\.]+)', original_text)
            if total_match:
                total_usd = float(total_match.group(1))
            
            bdt_match = re.search(r'(\d+) BDT', original_text)
            if bdt_match:
                total_bdt = int(bdt_match.group(1))
            else:
                total_bdt = total_usd * 125
            
            commission_match = re.search(r'Commission: \$([\d\.]+)', original_text)
            if commission_match:
                commission = float(commission_match.group(1))
            
            # Extract friends details
            friend_section = re.search(r'FRIENDS DETAILS.*?(?=├─ 💰 Total|$)', original_text, re.DOTALL)
            if friend_section:
                friend_text = friend_section.group()
                friend_matches = re.findall(r'(\d+)\. ([^\n]+).*?Total Counts: (\d+)', friend_text, re.DOTALL)
                for match in friend_matches:
                    friend_num, friend_name, counts_str = match
                    friends_details.append({
                        'name': friend_name.strip(),
                        'counts': int(counts_str),
                        'amount': int(counts_str) * 0.10
                    })
                    friend_count += 1
                    friend_earnings += int(counts_str) * 0.10
            
            # Determine payment method
            selected_method = "bkash"
            payment_id = "No payment method added"
            
            if payment_methods:
                selected_method = list(payment_methods.keys())[0]
                payment_id = payment_methods[selected_method].get('id', 'N/A')
            
            current_date = datetime.now().strftime('%d %B %Y')
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Mask payment ID for group
            masked_payment_id = payment_id
            if len(payment_id) > 8 and payment_id != "No payment method added":
                masked_payment_id = payment_id[:4] + "****" + payment_id[-4:]
            
            # Send notification to user
            user_notification = f"✨ PAYMENT CONFIRMATION\n\n"
            user_notification += f"✅ Your payment has been processed!\n\n"
            user_notification += f"📅 {current_date}\n"
            user_notification += f"👤 {username}"
            if telegram_username:
                user_notification += f" (@{telegram_username})"
            user_notification += f"\n💰 ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
            
            if personal_count > 0:
                user_notification += f"📊 Your Counts: {personal_count}\n\n"
            
            user_notification += f"📈 EARNINGS\n"
            user_notification += f"├─ Personal: ${personal_earnings:.2f}\n"
            
            if friends_details:
                user_notification += f"├─ Friends: ${friend_earnings:.2f}\n"
            
            if commission > 0:
                user_notification += f"├─ Commission: ${commission:.2f}\n"
            
            user_notification += f"└─ Total: ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
            
            user_notification += f"💳 Payment Method Used:\n"
            user_notification += f"├─ Method: {selected_method.upper()}\n"
            user_notification += f"└─ ID: `{payment_id}`\n\n"
            
            if not payment_methods:
                user_notification += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n"
                user_notification += f"✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
            
            user_notification += f"✅ Status: COMPLETED\n"
            user_notification += f"📨 ID: PAY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            user_notified = False
            try:
                await context.bot.send_message(
                    int(user_id),
                    user_notification,
                    parse_mode='Markdown'
                )
                user_notified = True
                print(f"✅ Notification sent to user {user_id}")
            except Exception as e:
                print(f"❌ Could not notify user {user_id}: {e}")
            
            # Send notifications to friends
            friends_notified = 0
            for friend in friends_details:
                friend_user_id = None
                friend_name = friend['name']
                
                for acc_id, acc_data in accounts.items():
                    if acc_id == str(ADMIN_ID):
                        continue
                    
                    acc_accounts = acc_data.get("accounts", [])
                    if acc_accounts:
                        acc_username = acc_accounts[0].get('username', '')
                        acc_nickname = acc_accounts[0].get('nickname', '')
                        
                        if (friend_name.lower() in acc_username.lower() or 
                            friend_name.lower() in acc_nickname.lower()):
                            friend_user_id = acc_id
                            break
                
                if friend_user_id and friend['amount'] > 0:
                    friend_notification = f"📢 PAYMENT NOTIFICATION\n\n"
                    friend_notification += f"👤 Friend: {username}"
                    if telegram_username:
                        friend_notification += f" (@{telegram_username})"
                    friend_notification += f"\n\n"
                    
                    friend_notification += f"💰 Your Share\n"
                    friend_notification += f"├─ Counts: {friend.get('counts', 0)}\n"
                    friend_notification += f"├─ USD: ${friend['amount']:.2f}\n"
                    friend_notification += f"└─ BDT: {friend['amount'] * 125:.0f}\n\n"
                    
                    friend_notification += f"✅ Ready for collection!\n"
                    friend_notification += f"📨 Contact your friend"
                    
                    try:
                        await context.bot.send_message(
                            int(friend_user_id),
                            friend_notification,
                            parse_mode='none'
                        )
                        friends_notified += 1
                    except Exception as e:
                        print(f"❌ Could not notify friend {friend_user_id}: {e}")
            
            # Update admin message
            lines = original_text.split('\n')
            new_lines = []
            
            for line in lines:
                if '[🔄 Payment Pending]' in line:
                    new_lines.append(f"[✅ Payment Completed at {current_time}]")
                else:
                    new_lines.append(line)
            
            updated_text = '\n'.join(new_lines)
            
            if "✅ Payment Completed" not in updated_text:
                updated_text += f"\n\n✅ Payment Completed at {current_time}"
            
            notification_status = f"\n📨 Sent: "
            if user_notified:
                notification_status += f"User ✅"
                if friends_notified > 0:
                    notification_status += f", {friends_notified} friends"
            else:
                notification_status += f"Failed ❌"
            
            updated_text += notification_status
            
            # Keep only Details and Refresh buttons
            keyboard = [
                [InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_id}")],
                [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_user_card_{user_id}_{date_str}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                updated_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Send confirmation to admin
            confirmation = f"✅ PAYMENT COMPLETED\n\n"
            confirmation += f"👤 {username}"
            if telegram_username:
                confirmation += f" (@{telegram_username})"
            confirmation += f"\n🆔 `{user_id}`\n"
            confirmation += f"💰 ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
            
            confirmation += f"💳 Payment Method: {selected_method.upper()}\n"
            confirmation += f"🔢 ID: `{payment_id}`\n\n"
            
            confirmation += f"📊 Breakdown\n"
            confirmation += f"├─ Personal: ${personal_earnings:.2f}\n"
            if friend_earnings > 0:
                confirmation += f"├─ Friends: ${friend_earnings:.2f}\n"
            if commission > 0:
                confirmation += f"└─ Commission: ${commission:.2f}\n\n"
            
            confirmation += f"📨 Notifications\n"
            confirmation += f"├─ User: {'✅' if user_notified else '❌'}\n"
            confirmation += f"└─ Friends: {friends_notified}\n\n"
            confirmation += f"⏰ {current_time}"
            
            await context.bot.send_message(ADMIN_ID, confirmation, parse_mode='Markdown')
            
            # Forward to payment group with masked ID
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
                payment_method=selected_method,
                payment_id=masked_payment_id,
                is_fake=False
            )
            
        except Exception as e:
            print(f"❌ Force payment error: {e}")
            import traceback
            traceback.print_exc()
            await query.edit_message_text(f"❌ Error: {e}")


async def check_in_progress_timeout(context: CallbackContext):
    """Check numbers that are stuck in 'In Progress' state for more than 3 minutes - Only user gets message"""
    tracking = load_tracking()
    in_progress_timestamp = tracking.get("in_progress_timestamp", {})
    current_time = datetime.now()
    
    # Track which numbers to check for timeout
    numbers_to_check = []
    
    for phone_key, timestamp_str in list(in_progress_timestamp.items()):
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            time_diff = (current_time - timestamp).total_seconds()
            
            # If more than 3 minutes (180 seconds) and no pending delete
            if time_diff > 180 and phone_key not in tracking.get("pending_delete", {}):
                numbers_to_check.append(phone_key)
                # Mark as pending delete to avoid multiple notifications
                if "pending_delete" not in tracking:
                    tracking["pending_delete"] = {}
                tracking["pending_delete"][phone_key] = current_time.isoformat()
        except Exception as e:
            print(f"❌ Error checking timeout for {phone_key}: {e}")
    
    if numbers_to_check:
        save_tracking(tracking)
        
        # Send notifications to users only (not to admin)
        for phone_key in numbers_to_check:
            await notify_user_about_stuck_number(context, phone_key)
    
    # Schedule next check in 30 seconds
    if context.job_queue:
        context.job_queue.run_once(check_in_progress_timeout, 30)

async def notify_user_about_stuck_number(context: CallbackContext, phone_key: str):
    """Notify user about stuck number with delete button - Only user receives this"""
    try:
        # phone_key format: "cc_phone_userid"
        parts = phone_key.split("_")
        
        if len(parts) >= 3:
            cc = parts[0]
            phone = parts[1]
            user_id = int(parts[2])
        else:
            print(f"⚠️ Invalid phone_key format: {phone_key}")
            return
        
        # Create inline keyboard with delete button
        keyboard = [
            [InlineKeyboardButton("🗑️ নাম্বারটি ডিলিট করুন", callback_data=f"user_delete_stuck_{cc}_{phone}_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Bengali message for user
        message = f"⚠️ আপনার নম্বরটি আটকে গেছে (Stuck)!\n\n"
        message += f"📞 নম্বর: +{cc} {phone}\n"
        message += f"⏰ সময়: {datetime.now().strftime('%H:%M:%S')}\n\n"
        message += f"❌ এই নম্বরটি ৩ মিনিট ধরে 'In Progress' অবস্থায় আছে।\n\n"
        message += f"✅ অনুগ্রহ করে নিচের বাটনে ক্লিক করে নম্বরটি ডিলিট করুন।\n"
        message += f"ডিলিট করার পর আবার নতুন করে নম্বরটি সাবমিট করুন।\n\n"
        
        
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        print(f"📨 Stuck notification sent to user {user_id} for number +{cc}{phone}")
        
    except Exception as e:
        print(f"❌ Error sending stuck notification to user: {e}")

async def handle_user_delete_stuck_number(update: Update, context: CallbackContext):
    """Handle user's delete button click for stuck number"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("user_delete_stuck_"):
        parts = data.split("_")
        # user_delete_stuck_cc_phone_userid
        if len(parts) >= 6:
            cc = parts[3]
            phone = parts[4]
            user_id = int(parts[5])
        else:
            await query.edit_message_text("❌ ভুল ডিলিট রিকোয়েস্ট!")
            return
        
        # Check if the user is the same
        if query.from_user.id != user_id:
            await query.edit_message_text("❌ আপনি এই নম্বরটি ডিলিট করতে পারবেন না!")
            return
        
        # Show processing message in Bengali
        await query.edit_message_text(f"🔄 ডিলিট করা হচ্ছে +{cc} {phone}...")
        
        # Delete from all user accounts
        deleted_count = await delete_number_from_all_accounts_optimized(phone, user_id)
        
        if deleted_count > 0:
            # Remove from tracking
            tracking = load_tracking()
            phone_key = f"{cc}_{phone}_{user_id}"
            
            # Remove from in_progress_timestamp
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            
            # Remove from pending_delete
            if "pending_delete" in tracking and phone_key in tracking["pending_delete"]:
                del tracking["pending_delete"][phone_key]
            
            # Remove from today_added
            user_id_str = str(user_id)
            if user_id_str in tracking.get("today_added", {}):
                if isinstance(tracking["today_added"][user_id_str], dict):
                    if phone in tracking["today_added"][user_id_str]:
                        del tracking["today_added"][user_id_str][phone]
                elif isinstance(tracking["today_added"][user_id_str], (int, float)):
                    tracking["today_added"][user_id_str] = max(0, tracking["today_added"][user_id_str] - 1)
            
            save_tracking(tracking)
            
            # Remove from active_numbers
            if phone in active_numbers:
                del active_numbers[phone]
            
            # Bengali success message with re-submit instruction
            success_message = f"✅ নম্বরটি সফলভাবে ডিলিট করা হয়েছে!\n\n"
            success_message += f"📞 +{cc} {phone}\n"
            success_message += f"🗑️ {deleted_count} একাউন্ট থেকে ডিলিট হয়েছে\n\n"
            success_message += f"🔄 এখন আপনি আবার নতুন করে নম্বরটি সাবমিট করতে পারেন।\n"
            success_message += f"💡 টিপ: সরাসরি নম্বরটি টাইপ করে পাঠিয়ে দিন: `+{cc}{phone}`"
            
            await query.edit_message_text(success_message, parse_mode='Markdown')
            
        else:
            # Bengali error message
            error_message = f"⚠️ নম্বরটি পাওয়া যায়নি বা ইতিমধ্যে ডিলিট হয়ে গেছে!\n\n"
            error_message += f"📞 +{cc} {phone}\n\n"
            error_message += f"💡 আপনি সরাসরি নম্বরটি আবার সাবমিট করতে পারেন: `+{cc}{phone}`"
            
            await query.edit_message_text(error_message, parse_mode='Markdown')

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
            "💰 SET RATE\n\n"
            "Usage: `/setrate [rate] [country] [date]`\n"
            "Notice: `/setrate notice [message]`\n\n"
            "Examples:\n"
            "• `/setrate 0.08`\n"
            "• `/setrate 0.07 canada`\n"
            "• `/setrate 0.08 2026-04-01`\n"
            "• `/setrate 0.07 canada 2026-04-01`\n"
            "• `/setrate notice Payment tomorrow`"
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
            
            processing_msg = await update.message.reply_text(f"📢 Sending notice...")
            
            for user_id_str, user_data in accounts.items():
                if user_id_str == str(ADMIN_ID):
                    continue
                
                try:
                    await context.bot.send_message(
                        int(user_id_str),
                        f"📢 NOTICE\n\n{notice_message}\n\n📅 {datetime.now().strftime('%d %B %Y')}"
                    )
                    sent_count += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"❌ Could not send notice to user {user_id_str}: {e}")
            
            await processing_msg.edit_text(
                f"✅ Notice sent to {sent_count} users\n\n"
                f"📢 {notice_message[:50]}..."
            )
            return
        
        # Parse country rates and date
        country_rates = {}
        target_date = datetime.now().date()
        default_rate = None
        
        args = context.args.copy()
        
        # Find date in arguments
        date_index = -1
        for idx, arg in enumerate(args):
            if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', arg):
                date_index = idx
                break
            elif re.match(r'^\d{1,2}/\d{1,2}$', arg):
                date_index = idx
                break
        
        if date_index != -1:
            date_str = args.pop(date_index)
            try:
                if '-' in date_str:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                elif '/' in date_str:
                    parts = date_str.split('/')
                    day = parts[0].zfill(2)
                    month = parts[1].zfill(2)
                    current_year = datetime.now().year
                    target_date = datetime.strptime(f"{day}/{month}/{current_year}", "%d/%m/%Y").date()
                print(f"📅 Date parsed: {target_date}")
            except Exception as e:
                print(f"⚠️ Date parsing error: {e}")
                args.insert(date_index, date_str)
        
        # Parse country rates
        i = 0
        while i < len(args):
            try:
                rate = float(args[i])
                
                if i + 1 < len(args) and not args[i+1].replace('.', '', 1).isdigit() and not re.match(r'^\d', args[i+1]):
                    country_name = args[i+1].title()
                    country_name = country_name.rstrip(',')
                    country_rates[country_name] = rate
                    print(f"✅ Country rate: {country_name} = ${rate}")
                    i += 2
                else:
                    default_rate = rate
                    print(f"✅ Default rate: ${rate}")
                    i += 1
            except ValueError:
                print(f"⚠️ Skipping invalid: {args[i]}")
                i += 1
        
        if not default_rate and not country_rates:
            await update.message.reply_text("❌ Please provide at least one rate!")
            return
        
        if not country_rates and default_rate:
            print(f"ℹ️ Using default rate for all countries: ${default_rate}")
        
        settings = load_settings()
        old_rate = settings.get('settlement_rate', 0.10)
        
        target_date_str = target_date.strftime('%Y-%m-%d')
        target_date_display = target_date.strftime('%d %B %Y')
        
        filter_message = ""
        if country_rates:
            if len(country_rates) == 1:
                country = list(country_rates.keys())[0]
                rate = country_rates[country]
                filter_message = f"🌍 {country}: ${rate:.3f}"
            else:
                filter_message = "🌍 Multiple countries"
        else:
            filter_message = f"🌍 All: ${default_rate:.3f}"
        
        processing_msg = await update.message.reply_text(
            f"🔄 PROCESSING SETTLEMENT UPDATE\n"
            f"┌─────────────────────────\n"
            f"│ 📅 Date: {target_date_display}\n"
            f"│ {filter_message}\n"
            f"│ ⏳ Status: Initializing...\n"
            f"└─────────────────────────"
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
        
        users_with_earnings = 0
        users_without_earnings = 0
        
        total_friends_count = 0
        total_eligible_friends = 0
        total_personal_count = 0
        total_friend_counts = 0
        
        user_under_supervisors = {}
        users_in_friends_lists = set()
        
        # Dictionary to store API rates for each country
        api_rates_by_country = {}
        user_api_rates = {}
        
        # Dictionary for country-wise totals
        country_wise_totals = {}
        
        print(f"🔍 Total users in accounts: {len(accounts)}")
        
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
        
        total_users_to_process = len([u for u in accounts if u != str(ADMIN_ID)])
        
        for user_id_str, user_data in accounts.items():
            if user_id_str == str(ADMIN_ID):
                continue
            if not isinstance(user_data, dict):
                continue
            user_accounts = user_data.get("accounts", [])
            if not user_accounts:
                continue
            
            users_processed += 1
            
            if users_processed % 3 == 0 or users_processed == total_users_to_process:
                try:
                    progress_percent = int((users_processed / total_users_to_process) * 100)
                    progress_bar = "█" * (progress_percent // 5) + "░" * (20 - (progress_percent // 5))
                    await processing_msg.edit_text(
                        f"🔄 PROCESSING SETTLEMENT UPDATE\n"
                        f"┌─────────────────────────\n"
                        f"│ 📅 Date: {target_date_display}\n"
                        f"│ {filter_message}\n"
                        f"│ ├─ 📊 Progress: {progress_percent}% {progress_bar}\n"
                        f"│ ├─ 👥 Users: {users_processed}/{total_users_to_process}\n"
                        f"│ ├─ ✅ Found: {users_with_earnings}\n"
                        f"│ └─ ⏳ Status: Processing...\n"
                        f"└─────────────────────────"
                    )
                except:
                    pass
            
            username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
            telegram_username = user_data.get('telegram_username', '')
            
            payment_methods = user_data.get('payment_methods', {})
            
            # Country-wise totals for this user
            user_country_totals = {}
            user_total_count = 0
            user_total_usd = 0
            user_accounts_with_settlements = []
            user_all_filtered_settlements = []
            
            for acc_idx, account in enumerate(user_accounts):
                account_name = account.get('custom_name', account['username'])
                account_username = account['username']
                account_password = account['password']
                
                account_token = None
                account_api_user_id = None
                
                if account.get('token'):
                    async with aiohttp.ClientSession() as session:
                        status_code, _, _ = await get_status_async(session, account['token'], "0000000000")
                    if status_code != -1:
                        account_token = account['token']
                        account_api_user_id = account.get('api_user_id')
                
                if not account_token:
                    token, api_user_id, nickname = await login_api_async(account_username, account_password)
                    if token:
                        account_token = token
                        account_api_user_id = api_user_id
                        account['token'] = token
                        account['api_user_id'] = api_user_id
                        account['nickname'] = nickname
                        account['last_login'] = datetime.now().isoformat()
                        users_token_refreshed += 1
                    else:
                        continue
                
                if account_token and account_api_user_id:
                    try:
                        async with aiohttp.ClientSession() as session:
                            settlement_data, error = await get_user_settlements(
                                session, account_token, str(account_api_user_id), page=1, page_size=100
                            )
                        
                        if error:
                            continue
                        
                        # Store API rates from this user
                        if settlement_data and settlement_data.get('records'):
                            for record in settlement_data.get('records', []):
                                country = record.get('countryName') or record.get('country') or 'Unknown'
                                country = country.strip(', ')
                                receipt_price = record.get('receiptPrice', 0)
                                
                                if receipt_price > 0:
                                    if country not in api_rates_by_country:
                                        api_rates_by_country[country] = receipt_price
                                    if user_id_str not in user_api_rates:
                                        user_api_rates[user_id_str] = {}
                                    user_api_rates[user_id_str][country] = receipt_price
                        
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
                                    country = country.strip(', ')
                                    
                                    # Get API rate for this country
                                    api_rate_for_country = record.get('receiptPrice', 0)
                                    
                                    # Determine admin rate for this country
                                    if country_rates:
                                        matched_rate = default_rate if default_rate else 0.10
                                        for target_country, target_rate in country_rates.items():
                                            if target_country.lower() in country.lower() or country.lower() in target_country.lower():
                                                matched_rate = target_rate
                                                break
                                        if matched_rate == (default_rate if default_rate else 0.10) and default_rate is None:
                                            continue
                                    else:
                                        if not default_rate:
                                            continue
                                        matched_rate = default_rate
                                    
                                    count_value = record.get('count', 0)
                                    country_usd = count_value * matched_rate
                                    
                                    # Update user's country-wise totals
                                    if country not in user_country_totals:
                                        user_country_totals[country] = {
                                            'count': 0, 
                                            'usd': 0, 
                                            'rate': matched_rate
                                        }
                                    user_country_totals[country]['count'] += count_value
                                    user_country_totals[country]['usd'] += country_usd
                                    
                                    # Update global country-wise totals
                                    if country not in country_wise_totals:
                                        country_wise_totals[country] = {
                                            'count': 0, 
                                            'usd': 0, 
                                            'bdt': 0,
                                            'rate': matched_rate,
                                            'api_rate': api_rate_for_country
                                        }
                                    country_wise_totals[country]['count'] += count_value
                                    country_wise_totals[country]['usd'] += country_usd
                                    country_wise_totals[country]['bdt'] = country_wise_totals[country]['usd'] * USD_TO_BDT
                                    if api_rate_for_country > 0 and country_wise_totals[country].get('api_rate', 0) == 0:
                                        country_wise_totals[country]['api_rate'] = api_rate_for_country
                                    
                                    user_total_count += count_value
                                    user_total_usd += country_usd
                                    
                                    user_accounts_with_settlements.append({
                                        'account_name': account_name,
                                        'username': account_username,
                                        'settlement_count': 1,
                                        'total_count': count_value,
                                        'total_usd': country_usd,
                                        'country': country
                                    })
                                    
                                except Exception as e:
                                    continue
                    except Exception as e:
                        continue
            
            user_personal_usd = user_total_usd
            total_personal_count += user_total_count
            
            commission_rate = 0.002
            total_commission = 0
            friends_details = []
            
            friends_list = []
            for acc in user_accounts:
                if isinstance(acc, dict) and 'friends' in acc and isinstance(acc['friends'], list):
                    friends_list = acc['friends']
                    break
            
            total_friends_count += len(friends_list)
            
            for friend_data in friends_list:
                friend_user_id = None
                if isinstance(friend_data, dict) and 'user_id' in friend_data:
                    friend_user_id = str(friend_data['user_id'])
                elif isinstance(friend_data, str):
                    friend_user_id = str(friend_data)
                else:
                    continue
                
                friend_found = False
                actual_friend_id = None
                for acc_key in accounts.keys():
                    if str(acc_key) == str(friend_user_id):
                        actual_friend_id = acc_key
                        friend_found = True
                        break
                
                if not friend_found or not actual_friend_id:
                    continue
                
                if actual_friend_id in accounts:
                    friend_accounts_data = accounts[actual_friend_id]
                    if not isinstance(friend_accounts_data, dict):
                        continue
                    
                    friend_accounts = friend_accounts_data.get("accounts", [])
                    if not friend_accounts:
                        continue
                    
                    friend_username = friend_accounts[0].get('username', 'Unknown') if friend_accounts else 'Unknown'
                    friend_telegram_username = friend_accounts_data.get('telegram_username', '')
                    
                    user_under_supervisors[actual_friend_id] = {
                        'name': username,
                        'telegram_username': telegram_username,
                        'user_id': user_id_str
                    }
                    
                    # Friend's country-wise totals
                    friend_country_totals = {}
                    friend_total_count = 0
                    friend_total_usd = 0
                    
                    for friend_acc in friend_accounts:
                        friend_acc_token = None
                        friend_acc_api_id = friend_acc.get('api_user_id')
                        
                        if friend_acc.get('token'):
                            async with aiohttp.ClientSession() as token_session:
                                status_code, _, _ = await get_status_async(token_session, friend_acc['token'], "0000000000")
                            if status_code != -1:
                                friend_acc_token = friend_acc['token']
                        
                        if not friend_acc_token and friend_acc.get('active', True):
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
                                    
                                    if error or not friend_settlement_data:
                                        continue
                                    
                                    if friend_settlement_data.get('records'):
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
                                                country = country.strip(', ')
                                                
                                                # Determine rate
                                                if country_rates:
                                                    matched_rate = default_rate if default_rate else 0.10
                                                    for target_country, target_rate in country_rates.items():
                                                        if target_country.lower() in country.lower() or country.lower() in target_country.lower():
                                                            matched_rate = target_rate
                                                            break
                                                    if matched_rate == (default_rate if default_rate else 0.10) and default_rate is None:
                                                        continue
                                                else:
                                                    if not default_rate:
                                                        continue
                                                    matched_rate = default_rate
                                                
                                                count = record.get('count', 0)
                                                country_usd = count * matched_rate
                                                
                                                # Update friend's country-wise totals
                                                if country not in friend_country_totals:
                                                    friend_country_totals[country] = {
                                                        'count': 0,
                                                        'usd': 0,
                                                        'rate': matched_rate
                                                    }
                                                friend_country_totals[country]['count'] += count
                                                friend_country_totals[country]['usd'] += country_usd
                                                
                                                friend_total_count += count
                                                friend_total_usd += country_usd
                                                
                                            except:
                                                continue
                            except:
                                continue
                    
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
                            'earnings': friend_total_usd,
                            'friend_user_id': actual_friend_id,
                            'country_totals': friend_country_totals
                        })
            
            total_usd_with_commission = user_personal_usd + total_commission
            total_bdt_user = total_usd_with_commission * USD_TO_BDT
            
            if user_total_count > 0:
                users_with_settlements += 1
            
            if total_commission > 0 and user_total_count == 0:
                users_with_only_commission += 1
            
            has_earnings = user_personal_usd > 0 or total_commission > 0
            
            if has_earnings:
                users_with_earnings += 1
                
                user_summary = {
                    'user_id': user_id_str,
                    'username': username,
                    'telegram_username': telegram_username,
                    'settlement_date': target_date_display,
                    'country_totals': user_country_totals,
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
                    'active_accounts': len([acc for acc in user_accounts if acc.get('active', True)]),
                    'payment_methods': payment_methods
                }
                
                all_users_summary.append(user_summary)
                total_users += 1
                total_usd += total_usd_with_commission
                total_bdt += total_bdt_user
        
        save_accounts(accounts)
        
        if default_rate:
            settings['settlement_rate'] = default_rate
        elif country_rates:
            first_country = list(country_rates.keys())[0]
            settings['settlement_rate'] = country_rates[first_country]
        else:
            settings['settlement_rate'] = 0.10
        
        settings['last_updated'] = datetime.now().isoformat()
        settings['updated_by'] = ADMIN_ID
        save_settings(settings)
        
        # ============ SEND NOTIFICATIONS TO USERS (WITH AUTO CHUNK) ============
        
        for user_summary in all_users_summary:
            try:
                supervisor_info = user_under_supervisors.get(user_summary['user_id'])
                has_friends = len(user_summary.get('friends_details', [])) > 0
                is_friend = user_summary.get('in_friends_list', False)
                
                # Check if user has payment method
                payment_methods = user_summary.get('payment_methods', {})
                has_payment_method = len(payment_methods) > 0
                
                # Build country-wise breakdown message
                country_breakdown = ""
                if user_summary.get('country_totals'):
                    country_breakdown = "\n📊 COUNTRY-WISE BREAKDOWN:\n"
                    for country, data in user_summary['country_totals'].items():
                        country_breakdown += f"├─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                
                if has_friends:
                    message = f"✨ SETTLEMENT UPDATE\n\n"
                    message += f"📅 {user_summary['settlement_date']}\n\n"
                    
                    if country_rates:
                        message += f"💰 COUNTRY RATES:\n"
                        for country, rate in country_rates.items():
                            message += f"├─ {country}: ${rate:.3f}/account\n"
                        message += f"\n"
                    else:
                        message += f"💰 Rate: ${default_rate:.3f}/account\n\n"
                    
                    message += f"📊 YOUR EARNINGS\n"
                    if user_summary['country_totals']:
                        message += country_breakdown
                        message += f"\n📈 TOTAL: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    else:
                        message += f"├─ Personal: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    
                    if user_summary['friends_details']:
                        message += f"\n👥 YOUR NETWORK ({len(user_summary['friends_details'])} friends)\n"
                        
                        for i, friend in enumerate(user_summary['friends_details'], 1):
                            message += f"\n├─ {i}. {friend['name']}\n"
                            message += f"│  ├─ Total Accounts: {friend['counts']}\n"
                            message += f"│  ├─ Earned: ${friend['earnings']:.2f}\n"
                            
                            if friend.get('country_totals'):
                                message += f"│  └─ Country Breakdown:\n"
                                for country, data in friend['country_totals'].items():
                                    message += f"│     └─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                            else:
                                message += f"│  └─ Commission: ${friend['commission']:.2f}\n"
                        
                        total_friend_counts = sum(f['counts'] for f in user_summary['friends_details'])
                        message += f"\n💰 COMMISSION SUMMARY\n"
                        message += f"├─ Total Friend Accounts: {total_friend_counts}\n"
                        message += f"└─ Total Commission: ${user_summary['total_commission']:.2f}\n"
                    
                    message += f"\n💰 TOTAL EARNINGS\n"
                    message += f"├─ Personal + Commission: ${user_summary['total_usd']:.2f}\n"
                    message += f"└─ BDT: {user_summary['total_bdt']:.0f} BDT\n\n"
                    
                    if not has_payment_method:
                        message += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n"
                        message += f"✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
                
                elif is_friend:
                    message = f"✨ SETTLEMENT UPDATE\n\n"
                    message += f"📅 {user_summary['settlement_date']}\n\n"
                    
                    if country_rates:
                        message += f"💰 COUNTRY RATES:\n"
                        for country, rate in country_rates.items():
                            message += f"├─ {country}: ${rate:.3f}/account\n"
                        message += f"\n"
                    else:
                        message += f"💰 Rate: ${default_rate:.3f}/account\n\n"
                    
                    message += f"📊 YOUR EARNINGS\n"
                    if user_summary['country_totals']:
                        message += country_breakdown
                        message += f"\n📈 TOTAL: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    else:
                        message += f"├─ Accounts: {user_summary['total_count']}\n"
                        message += f"├─ USD: ${user_summary['personal_usd']:.2f}\n"
                        message += f"└─ BDT: {user_summary['total_bdt']:.0f} BDT\n\n"
                    
                    if supervisor_info:
                        message += f"👤 Added by: {supervisor_info['name']}"
                        if supervisor_info.get('telegram_username'):
                            message += f" (@{supervisor_info['telegram_username']})"
                        message += f"\n\n"
                    
                    if not has_payment_method:
                        message += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n"
                        message += f"✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
                    
                    message += f"ℹ️ Note: Your earnings will be collected by your friend.\n"
                    message += f"They will pay you directly.\n\n"
                
                else:
                    message = f"✨ SETTLEMENT UPDATE\n\n"
                    message += f"📅 {user_summary['settlement_date']}\n\n"
                    
                    if country_rates:
                        message += f"💰 COUNTRY RATES:\n"
                        for country, rate in country_rates.items():
                            message += f"├─ {country}: ${rate:.3f}/account\n"
                        message += f"\n"
                    else:
                        message += f"💰 Rate: ${default_rate:.3f}/account\n\n"
                    
                    message += f"📊 YOUR EARNINGS\n"
                    if user_summary['country_totals']:
                        message += country_breakdown
                        message += f"\n📈 TOTAL: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    else:
                        message += f"├─ Accounts: {user_summary['total_count']}\n"
                        message += f"├─ USD: ${user_summary['personal_usd']:.2f}\n"
                        message += f"└─ Total: ${user_summary['total_usd']:.2f} / {user_summary['total_bdt']:.0f} BDT\n\n"
                    
                    if supervisor_info:
                        message += f"👤 Added by: {supervisor_info['name']}\n\n"
                    
                    if not has_payment_method:
                        message += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n"
                        message += f"✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
                
                # AUTO CHUNK: Split message if too long
                if len(message) > 4000:
                    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                    for chunk in chunks:
                        await context.bot.send_message(
                            int(user_summary['user_id']),
                            chunk,
                            parse_mode='none'
                        )
                        await asyncio.sleep(0.5)
                else:
                    await context.bot.send_message(
                        int(user_summary['user_id']),
                        message,
                        parse_mode='none'
                    )
                
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"❌ Notification failed for {user_summary['user_id']}: {e}")
        
        # ============ ADMIN REPORT WITH COUNTRY-WISE SUMMARY ============
        
        if all_users_summary:
            # Calculate totals
            total_personal_counts_all = sum(u['total_count'] for u in all_users_summary)
            total_friend_counts_all = sum(u['friend_counts'] for u in all_users_summary)
            grand_total_counts = total_personal_counts_all + total_friend_counts_all
            
            total_personal_usd_all = sum(u['personal_usd'] for u in all_users_summary)
            total_friend_earnings_all = sum(sum(f['earnings'] for f in u['friends_details']) for u in all_users_summary)
            total_commissions_all = sum(u['total_commission'] for u in all_users_summary)
            total_all_earnings = total_personal_usd_all + total_friend_earnings_all + total_commissions_all
            total_all_bdt = total_all_earnings * USD_TO_BDT
            
            # Build country-wise summary with API rate comparison
            country_summary = ""
            if country_wise_totals:
                country_summary = "\n🌍 COUNTRY-WISE SUMMARY WITH PROFIT ANALYSIS:\n"
                sorted_countries = sorted(country_wise_totals.items(), key=lambda x: x[1]['count'], reverse=True)
                
                total_api_all = 0
                total_admin_all = 0
                total_profit_all = 0
                
                for country, data in sorted_countries:
                    count = data['count']
                    admin_rate = data.get('rate', default_rate or 0.10)
                    
                    # Get API rate
                    api_rate = data.get('api_rate', 0)
                    if api_rate == 0 and country in api_rates_by_country:
                        api_rate = api_rates_by_country[country]
                    
                    if api_rate > 0:
                        api_amount = count * api_rate
                        admin_amount = count * admin_rate
                        profit = admin_amount - api_amount
                        
                        total_api_all += api_amount
                        total_admin_all += admin_amount
                        total_profit_all += profit
                        
                        profit_symbol = "📈" if profit > 0 else "📉" if profit < 0 else "📊"
                        
                        country_summary += f"├─ {country}:\n"
                        country_summary += f"│  ├─ Accounts: {count}\n"
                        country_summary += f"│  ├─ API Rate: ${api_rate:.4f}\n"
                        country_summary += f"│  ├─ Admin Rate: ${admin_rate:.4f}\n"
                        country_summary += f"│  ├─ API Amount: ${api_amount:.2f}\n"
                        country_summary += f"│  ├─ Admin Amount: ${admin_amount:.2f}\n"
                        country_summary += f"│  └─ Profit: {profit_symbol} ${profit:.2f}\n"
                    else:
                        country_summary += f"├─ {country}:\n"
                        country_summary += f"│  ├─ Accounts: {count}\n"
                        country_summary += f"│  ├─ API Rate: ⚠️ Not Found\n"
                        country_summary += f"│  ├─ Admin Rate: ${admin_rate:.4f}\n"
                        country_summary += f"│  └─ Profit: ⚠️ Unknown\n"
                
                if total_api_all > 0:
                    country_summary += f"\n📊 GRAND TOTAL PROFIT ANALYSIS:\n"
                    country_summary += f"├─ Total API Amount: ${total_api_all:.2f}\n"
                    country_summary += f"├─ Total Admin Amount: ${total_admin_all:.2f}\n"
                    country_summary += f"└─ Total Profit: ${total_profit_all:.2f}\n"
                
                country_summary += f"\n📈 GRAND TOTAL ACCOUNTS: {grand_total_counts}\n"
                country_summary += f"   (Personal: {total_personal_counts_all} + Friend: {total_friend_counts_all})\n\n"
            
            detailed_summary = f"📊 SETTLEMENT SUMMARY\n\n"
            detailed_summary += f"📅 {target_date_display}\n"
            
            if country_rates:
                detailed_summary += "\n💰 RATES USED:\n"
                for country, rate in country_rates.items():
                    detailed_summary += f"├─ {country}: ${rate:.3f}\n"
                if default_rate:
                    detailed_summary += f"└─ Other: ${default_rate:.3f}\n"
                detailed_summary += "\n"
            
            detailed_summary += f"👥 USERS\n"
            detailed_summary += f"├─ With earnings: {users_with_earnings}\n"
            detailed_summary += f"├─ Without: {users_without_earnings}\n"
            detailed_summary += f"└─ Commission only: {users_with_only_commission}\n\n"
            
            detailed_summary += country_summary
            
            detailed_summary += f"💰 FINANCIAL SUMMARY\n"
            detailed_summary += f"├─ Personal Earnings: ${total_personal_usd_all:.2f}\n"
            detailed_summary += f"├─ Friends Earnings: ${total_friend_earnings_all:.2f}\n"
            detailed_summary += f"├─ Commission: ${total_commissions_all:.2f}\n"
            detailed_summary += f"└─ 📈 TOTAL: ${total_all_earnings:.2f} / {total_all_bdt:.0f} BDT\n\n"
            
            detailed_summary += f"✅ Operation complete!"
            
            # AUTO CHUNK
            if len(detailed_summary) > 4000:
                summary_chunks = [detailed_summary[i:i+4000] for i in range(0, len(detailed_summary), 4000)]
                for chunk in summary_chunks:
                    await processing_msg.edit_text(chunk, parse_mode='none')
                    await asyncio.sleep(0.5)
            else:
                await processing_msg.edit_text(detailed_summary, parse_mode='none')
            
            # ============ ADMIN CARDS ============
            
            for user_summary in all_users_summary:
                telegram_display = f" (@{user_summary['telegram_username']})" if user_summary['telegram_username'] else ""
                refresh_icon = " 🔄" if user_summary['token_refreshed'] else ""
                settlement_icon = " ✅" if user_summary['has_personal_settlement'] else " 👥"
                
                user_personal_counts = user_summary['total_count']
                user_friend_counts = user_summary['friend_counts']
                user_grand_total = user_personal_counts + user_friend_counts
                
                payment_methods = user_summary.get('payment_methods', {})
                has_payment_method = len(payment_methods) > 0
                
                user_message = f"👤 {user_summary['username']}{telegram_display}{refresh_icon}{settlement_icon}\n"
                user_message += f"├─ 📱 Accounts: {user_summary['active_accounts']}\n"
                
                if user_summary.get('accounts_with_settlements'):
                    user_message += f"├─ 💰 Active: {len(user_summary['accounts_with_settlements'])}\n"
                
                if user_summary.get('country_totals'):
                    user_message += f"├─ 📊 PERSONAL (Country-wise):\n"
                    for country, data in user_summary['country_totals'].items():
                        user_message += f"│  ├─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                    user_message += f"├─ 🔢 Total Personal: {user_personal_counts} accounts (${user_summary['personal_usd']:.2f})\n"
                else:
                    user_message += f"├─ 🔢 Personal: {user_personal_counts} accounts (${user_summary['personal_usd']:.2f})\n"
                
                if user_summary['friends_details']:
                    eligible_friends = len([f for f in user_summary['friends_details'] if f['counts'] >= 1])
                    user_message += f"├─ 👥 Friends: {eligible_friends} users\n"
                    user_message += f"├─ 🔢 Friend Accounts: {user_friend_counts}\n"
                    user_message += f"├─ 💰 Commission: ${user_summary['total_commission']:.2f}\n"
                    user_message += f"├─ 📊 GRAND TOTAL: {user_grand_total} accounts\n\n"
                    
                    user_message += f"├─ 📋 FRIENDS DETAILS (Country-wise):\n"
                    for i, friend in enumerate(user_summary['friends_details'], 1):
                        friend_name = friend.get('name', 'Unknown')
                        friend_username = friend.get('username', 'Unknown')
                        friend_counts = friend.get('counts', 0)
                        friend_earnings = friend.get('earnings', 0)
                        friend_commission = friend.get('commission', 0)
                        
                        user_message += f"│  ├─ {i}. {friend_name}"
                        if friend_username and friend_username != 'Unknown':
                            user_message += f" (@{friend_username})"
                        user_message += f"\n"
                        user_message += f"│  │  ├─ Total Accounts: {friend_counts}\n"
                        user_message += f"│  │  ├─ Earned: ${friend_earnings:.2f}\n"
                        
                        if friend.get('country_totals'):
                            user_message += f"│  │  └─ Country Breakdown:\n"
                            for country, data in friend['country_totals'].items():
                                user_message += f"│  │     └─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                        else:
                            user_message += f"│  │  └─ Commission: ${friend_commission:.2f}\n"
                else:
                    user_message += f"├─ 📊 Total: {user_grand_total} accounts\n"
                
                friend_earnings = sum(f['earnings'] for f in user_summary['friends_details'])
                total_all_earnings_user = user_summary['personal_usd'] + friend_earnings + user_summary['total_commission']
                total_all_bdt_user = total_all_earnings_user * USD_TO_BDT
                
                user_message += f"├─ 💰 Total: ${total_all_earnings_user:.2f} / {total_all_bdt_user:.0f} BDT\n"
                
                if payment_methods:
                    user_message += f"├─ 💳 Payment Methods:\n"
                    for method, data in payment_methods.items():
                        payment_id = data.get('id', 'N/A')
                        if len(payment_id) > 8:
                            masked_id = payment_id[:4] + "****" + payment_id[-4:]
                        else:
                            masked_id = payment_id
                        user_message += f"│  ├─ {method.upper()}: `{payment_id}`\n"
                        if data.get('details'):
                            user_message += f"│  │  └─ {data['details'][:30]}\n"
                else:
                    user_message += f"├─ 💳 Payment: ❌ Not Provided\n"
                
                user_message += f"└─ 📅 {target_date_display}\n\n"
                
                # Check if user is added by someone
                added_by_list = []
                for other_user in all_users_summary:
                    for friend in other_user.get('friends_details', []):
                        if friend.get('friend_user_id') == user_summary['user_id']:
                            added_by_list.append({
                                'added_by': other_user['username'],
                                'telegram': other_user['telegram_username']
                            })
                
                if added_by_list:
                    names = []
                    for adder in added_by_list[:2]:
                        if adder['telegram']:
                            names.append(f"{adder['added_by']} (@{adder['telegram']})")
                        else:
                            names.append(adder['added_by'])
                    added_by_message = f"⚠️ Added by: {', '.join(names)}"
                    if len(added_by_list) > 2:
                        added_by_message += f" +{len(added_by_list) - 2} more"
                    user_message += f"{added_by_message}\n\n"
                
                # Create keyboard
                keyboard = []
                
                if user_summary['has_earnings']:
                    if has_payment_method:
                        for method in payment_methods.keys():
                            keyboard.append([
                                InlineKeyboardButton(
                                    f"✅ {method.upper()} Payment Complete", 
                                    callback_data=f"payment_complete_{user_summary['user_id']}_{method}_{target_date_str}"
                                )
                            ])
                    else:
                        keyboard.append([
                            InlineKeyboardButton(
                                "✅ Payment Complete", 
                                callback_data=f"force_payment_complete_{user_summary['user_id']}_{target_date_str}"
                            )
                        ])
                
                keyboard.append([
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_user_card_{user_summary['user_id']}_{target_date_str}")
                ])
                
                keyboard.append([
                    InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_summary['user_id']}")
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if len(user_message) > 4000:
                    msg_chunks = [user_message[i:i+4000] for i in range(0, len(user_message), 4000)]
                    for j, chunk in enumerate(msg_chunks):
                        if j == len(msg_chunks) - 1:
                            await context.bot.send_message(ADMIN_ID, chunk, reply_markup=reply_markup, parse_mode='Markdown')
                        else:
                            await context.bot.send_message(ADMIN_ID, chunk, parse_mode='Markdown')
                        await asyncio.sleep(0.5)
                else:
                    await context.bot.send_message(ADMIN_ID, user_message, reply_markup=reply_markup, parse_mode='Markdown')
                
                await asyncio.sleep(0.5)
            
            # Final stats
            final_stats = f"📊 PAYMENT STATS\n\n📅 {target_date_display}\n👥 Users: {total_users}\n✅ Direct: {len([u for u in all_users_summary if not u['in_friends_list']])}\n👥 Via Friends: {len([u for u in all_users_summary if u['in_friends_list']])}\n💰 Total: ${total_all_earnings:.2f}\n📊 Grand Total Accounts: {grand_total_counts}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            if len(final_stats) > 4000:
                final_chunks = [final_stats[i:i+4000] for i in range(0, len(final_stats), 4000)]
                for chunk in final_chunks:
                    await context.bot.send_message(ADMIN_ID, chunk, parse_mode='none')
            else:
                await context.bot.send_message(ADMIN_ID, final_stats, parse_mode='none')
        else:
            summary_message = f"📊 SETTLEMENT UPDATE\n\n📅 {target_date_display}\n\n💰 No settlements found\n\n👥 Users: {users_processed}\n✅ With earnings: {users_with_earnings}\n👥 Without: {users_without_earnings}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            if len(summary_message) > 4000:
                summary_chunks = [summary_message[i:i+4000] for i in range(0, len(summary_message), 4000)]
                for chunk in summary_chunks:
                    await processing_msg.edit_text(chunk, parse_mode='none')
                    await asyncio.sleep(0.5)
            else:
                await processing_msg.edit_text(summary_message, parse_mode='none')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        print(f"❌ Set rate error: {e}")
        import traceback
        traceback.print_exc()

async def handle_refresh_user_card(update: Update, context: CallbackContext):
    """Refresh user card - check if payment method added and update buttons accordingly"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("refresh_user_card_"):
        parts = data.split("_")
        # refresh_user_card_userid_date
        if len(parts) >= 5:
            user_id = parts[3]
            date_str = parts[4]
        else:
            await query.answer("Invalid request!", show_alert=True)
            return
        
        await query.edit_message_text(f"🔄 Refreshing card for user {user_id}...")
        
        # Reload user data
        accounts = load_accounts()
        user_data = accounts.get(user_id, {})
        payment_methods = user_data.get('payment_methods', {})
        has_payment_method = len(payment_methods) > 0
        
        # Get the user summary from stored message
        original_text = query.message.text
        
        # Check if payment already completed
        payment_completed = "✅ Payment Completed" in original_text or "✅ পেমেন্ট সম্পূর্ণ" in original_text
        
        if payment_completed:
            await query.edit_message_text("✅ Payment already completed for this card!")
            return
        
        # Extract user info from message to check if has earnings
        has_earnings = "💰 Total:" in original_text or "মোট:" in original_text
        
        # Create new keyboard based on payment method status
        new_keyboard = []
        
        if has_earnings:
            if has_payment_method:
                # User HAS payment method - show individual payment method buttons
                for method in payment_methods.keys():
                    new_keyboard.append([
                        InlineKeyboardButton(
                            f"✅ {method.upper()} Payment Complete", 
                            callback_data=f"payment_complete_{user_id}_{method}_{date_str}"
                        )
                    ])
            else:
                # User has NO payment method - show single Payment Complete button
                new_keyboard.append([
                    InlineKeyboardButton(
                        "✅ Payment Complete", 
                        callback_data=f"force_payment_complete_{user_id}_{date_str}"
                    )
                ])
        
        # Refresh button for ALL users
        new_keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_user_card_{user_id}_{date_str}")
        ])
        
        # Details button for ALL users
        new_keyboard.append([
            InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_id}")
        ])
        
        reply_markup = InlineKeyboardMarkup(new_keyboard)
        
        # Update message
        updated_text = original_text
        if has_payment_method:
            updated_text += "\n\n✅ User has payment methods! You can now complete payment."
        else:
            updated_text += "\n\n⚠️ User still hasn't added any payment method."
        
        await query.edit_message_text(
            updated_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        print(f"✅ Card refreshed for user {user_id} - Payment methods: {list(payment_methods.keys()) if payment_methods else 'None'}")


# এই কোডটি main() ফাংশনের আগে যুক্ত করুন
async def handle_payment_callback(update: Update, context: CallbackContext):
    """Handle payment completion callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('payment_complete_'):
        # Format: payment_complete_userID_method_date
        parts = data.split('_')
        if len(parts) >= 4:
            user_id = parts[2]
            method = parts[3]
            date_str = parts[4] if len(parts) > 4 else datetime.now().strftime('%Y-%m-%d')
            
            await complete_user_payment_with_method(query, context, user_id, date_str, method)
    
    elif data.startswith('payment_details_'):
        user_id = data.split('_')[2]
        await show_user_payment_details(query, context, user_id)

async def complete_user_payment_with_method(query, context, user_id, date_str, selected_method):
    """Complete payment for a specific user with selected payment method"""
    await query.edit_message_text(f"🔄 Processing payment via {selected_method.upper()} for user {user_id}...")
    
    try:
        accounts = load_accounts()
        user_data = accounts.get(user_id, {})
        
        if not user_data:
            await query.edit_message_text(f"❌ User {user_id} not found!")
            return
        
        user_accounts = user_data.get("accounts", [])
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        telegram_username = user_data.get('telegram_username', '')
        payment_methods = user_data.get('payment_methods', {})
        
        # Get selected payment method details
        selected_payment = payment_methods.get(selected_method, {})
        if not selected_payment:
            await query.edit_message_text(f"❌ Payment method {selected_method.upper()} not found for this user!")
            return
        
        payment_id = selected_payment.get('id', 'N/A')
        
        original_text = query.message.text
        
        import re
        
        personal_earnings = 0
        friend_earnings = 0
        commission = 0
        total_usd = 0
        total_bdt = 0
        personal_count = 0
        friend_count = 0
        friends_details = []
        
        # Extract values
        personal_match = re.search(r'Personal: (\d+) \(\$([\d\.]+)\)', original_text)
        if not personal_match:
            personal_match = re.search(r'Personal Earnings: \$([\d\.]+)', original_text)
            if personal_match:
                personal_earnings = float(personal_match.group(1))
            personal_match = re.search(r'Personal Count: ([\d,\.]+)', original_text)
            if personal_match:
                personal_count_str = personal_match.group(1).replace(',', '')
                personal_count = int(float(personal_count_str))
        else:
            personal_count = int(personal_match.group(1))
            personal_earnings = float(personal_match.group(2))
        
        friend_match = re.search(r'Friends Earned: \$([\d\.]+)', original_text)
        if friend_match:
            friend_earnings = float(friend_match.group(1))
        
        commission_match = re.search(r'Commission: \$([\d\.]+)', original_text)
        if commission_match:
            commission = float(commission_match.group(1))
        
        total_match = re.search(r'Total: \$([\d\.]+)', original_text)
        if total_match:
            total_usd = float(total_match.group(1))
        
        bdt_match = re.search(r'Total: .*? (\d+) BDT', original_text)
        if not bdt_match:
            bdt_match = re.search(r'Total BDT: (\d+)', original_text)
        if bdt_match:
            total_bdt = int(bdt_match.group(1))
        else:
            total_bdt = total_usd * 125
        
        if personal_count == 0:
            count_match = re.search(r'Personal Count: ([\d,\.]+)', original_text)
            if count_match:
                personal_count_str = count_match.group(1).replace(',', '')
                personal_count = int(float(personal_count_str))
        
        # Extract friends details
        friends_section = re.search(r'👥 Friends Details \((\d+) friends\):\n(.*?)(?=\[🔄|$)', original_text, re.DOTALL)
        if friends_section:
            friends_text = friends_section.group(2)
            friend_pattern = r'(\d+)\. ([^\n]+)\n.*?Counts: (\d+) ✅.*?Earned: \$([\d\.]+)'
            friend_matches = re.findall(friend_pattern, friends_text, re.DOTALL)
            
            for match in friend_matches:
                friend_num, friend_name, counts_str, earned_str = match
                friends_details.append({
                    'name': friend_name.strip(),
                    'telegram': '',
                    'counts': int(counts_str),
                    'amount': float(earned_str),
                    'commission': float(earned_str) * 0.002
                })
                friend_count += 1
                friend_earnings += float(earned_str)
                commission += float(earned_str) * 0.002
        
        if commission == 0 and friend_count > 0:
            commission = friend_count * 0.002
        
        if total_usd == 0:
            total_usd = personal_earnings + friend_earnings + commission
            total_bdt = total_usd * 125
        
        current_date = datetime.now().strftime('%d %B %Y')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Mask payment ID for group (first 4 and last 4 digits only)
        masked_payment_id = payment_id
        if len(payment_id) > 8:
            masked_payment_id = payment_id[:4] + "****" + payment_id[-4:]
        else:
            masked_payment_id = payment_id
        
        # Send notification to user with payment method details (FULL ID)
        user_notification = f"✨ PAYMENT CONFIRMATION\n\n"
        user_notification += f"✅ Your payment has been processed!\n\n"
        user_notification += f"📅 {current_date}\n"
        user_notification += f"👤 {username}"
        if telegram_username:
            user_notification += f" (@{telegram_username})"
        user_notification += f"\n💰 ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
        
        if personal_count > 0:
            user_notification += f"📊 Your Counts: {personal_count}\n\n"
        
        user_notification += f"📈 EARNINGS\n"
        user_notification += f"├─ Personal: ${personal_earnings:.2f}\n"
        
        if friends_details:
            user_notification += f"├─ Friends: ${friend_earnings:.2f}\n"
        
        if commission > 0:
            user_notification += f"├─ Commission: ${commission:.2f}\n"
        
        user_notification += f"└─ Total: ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
        
        user_notification += f"💳 Payment Method Used:\n"
        user_notification += f"├─ Method: {selected_method.upper()}\n"
        user_notification += f"└─ ID: `{payment_id}`\n\n"
        
        user_notification += f"✅ Status: COMPLETED\n"
        user_notification += f"📨 ID: PAY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        user_notified = False
        try:
            await context.bot.send_message(
                int(user_id),
                user_notification,
                parse_mode='Markdown'
            )
            user_notified = True
            print(f"✅ Notification sent to user {user_id} via {selected_method}")
        except Exception as e:
            print(f"❌ Could not notify user {user_id}: {e}")
        
        # Send notifications to friends
        friends_notified = 0
        for friend in friends_details:
            friend_user_id = None
            friend_name = friend['name']
            
            for acc_id, acc_data in accounts.items():
                if acc_id == str(ADMIN_ID):
                    continue
                
                acc_accounts = acc_data.get("accounts", [])
                if acc_accounts:
                    acc_username = acc_accounts[0].get('username', '')
                    acc_nickname = acc_accounts[0].get('nickname', '')
                    
                    if (friend_name.lower() in acc_username.lower() or 
                        friend_name.lower() in acc_nickname.lower()):
                        friend_user_id = acc_id
                        print(f"✅ Found friend: {acc_username} (ID: {friend_user_id})")
                        break
            
            if friend_user_id and friend['amount'] > 0:
                friend_notification = f"📢 PAYMENT NOTIFICATION\n\n"
                friend_notification += f"👤 Friend: {username}"
                if telegram_username:
                    friend_notification += f" (@{telegram_username})"
                friend_notification += f"\n\n"
                
                friend_notification += f"💰 Your Share\n"
                friend_notification += f"├─ Counts: {friend.get('counts', 0)}\n"
                friend_notification += f"├─ USD: ${friend['amount']:.2f}\n"
                friend_notification += f"└─ BDT: {friend['amount'] * 125:.0f}\n\n"
                
                friend_notification += f"✅ Ready for collection!\n"
                friend_notification += f"📨 Contact your friend"
                
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
        
        # Update admin message - Remove payment buttons and mark as completed
        lines = original_text.split('\n')
        new_lines = []
        skip_payment_section = False
        payment_section_ended = False
        
        for line in lines:
            if '├─ 💳 Payment Methods:' in line:
                skip_payment_section = True
                new_lines.append(line)
                continue
            if skip_payment_section and not payment_section_ended:
                if line.startswith('└─') or line.startswith('├─ 💰 Total:') or line.startswith('└─ 💰 Total:') or line.startswith('['):
                    payment_section_ended = True
                    skip_payment_section = False
                else:
                    continue
            
            if '[🔄 Payment Pending]' in line:
                new_lines.append(f"[✅ Completed via {selected_method.upper()} at {current_time}]")
            else:
                new_lines.append(line)
        
        updated_text = '\n'.join(new_lines)
        
        # Add completion status
        if "✅ Completed" not in updated_text:
            updated_text += f"\n\n✅ Payment Completed via {selected_method.upper()}"
        
        notification_status = f"\n📨 Sent: "
        if user_notified:
            notification_status += f"User ✅"
            if friends_notified > 0:
                notification_status += f", {friends_notified} friends"
        else:
            notification_status += f"Failed ❌"
        
        updated_text += notification_status
        
        # Only keep Details button, remove payment buttons
        keyboard = [[InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            updated_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Send confirmation to admin
        confirmation = f"✅ PAYMENT COMPLETED\n\n"
        confirmation += f"👤 {username}"
        if telegram_username:
            confirmation += f" (@{telegram_username})"
        confirmation += f"\n🆔 `{user_id}`\n"
        confirmation += f"💰 ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
        
        confirmation += f"💳 Payment Method: {selected_method.upper()}\n"
        confirmation += f"🔢 ID: `{payment_id}`\n\n"
        
        confirmation += f"📊 Breakdown\n"
        confirmation += f"├─ Personal: ${personal_earnings:.2f}\n"
        if friend_earnings > 0:
            confirmation += f"├─ Friends: ${friend_earnings:.2f}\n"
        if commission > 0:
            confirmation += f"└─ Commission: ${commission:.2f}\n\n"
        
        confirmation += f"📨 Notifications\n"
        confirmation += f"├─ User: {'✅' if user_notified else '❌'}\n"
        confirmation += f"└─ Friends: {friends_notified}\n\n"
        confirmation += f"⏰ {current_time}"
        
        await context.bot.send_message(ADMIN_ID, confirmation, parse_mode='Markdown')
        
        # Forward to payment group with MASKED ID
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
            payment_method=selected_method,
            payment_id=masked_payment_id,
            is_fake=False
        )
        
    except Exception as e:
        print(f"❌ Error completing payment: {e}")
        import traceback
        traceback.print_exc()
        await query.edit_message_text(f"❌ Error: {e}")

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

# ============ ADMIN PAYMENT METHOD MANAGEMENT ============

async def add_payment_method(update: Update, context: CallbackContext):
    """Admin command to add payment method for a user"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "💳 ADD PAYMENT METHOD (Admin)\n\n"
            "Usage: `/addpayment [user_id] [method] [id] [details]`\n\n"
            "Methods: bkash, nagad, rocket, binance\n\n"
            "Examples:\n"
            "• `/addpayment 7319925086 bkash 01712345678`\n"
            "• `/addpayment 7319925086 nagad 01887654321`\n"
            "• `/addpayment 7319925086 binance 8277372966555`\n"
            "• `/addpayment 7319925086 rocket 01912345678`\n\n"
            "📝 Note: User will see masked ID, you will see full ID"
        )
        return
    
    target_user_id = context.args[0]
    method = context.args[1].lower()
    payment_id = context.args[2]
    details = ' '.join(context.args[3:]) if len(context.args) > 3 else ''
    
    valid_methods = ['bkash', 'nagad', 'rocket', 'binance']
    if method not in valid_methods:
        await update.message.reply_text(f"❌ Invalid method! Use: {', '.join(valid_methods)}")
        return
    
    accounts = load_accounts()
    
    if target_user_id not in accounts:
        accounts[target_user_id] = {
            "accounts": [],
            "selected_account_id": 1,
            "telegram_username": "",
            "last_active": datetime.now().isoformat(),
            "payment_methods": {}
        }
    
    if not isinstance(accounts[target_user_id], dict):
        accounts[target_user_id] = {
            "accounts": [],
            "selected_account_id": 1,
            "telegram_username": "",
            "last_active": datetime.now().isoformat(),
            "payment_methods": {}
        }
    
    if "payment_methods" not in accounts[target_user_id]:
        accounts[target_user_id]["payment_methods"] = {}
    
    # Add/Update payment method
    accounts[target_user_id]["payment_methods"][method] = {
        "id": payment_id,
        "details": details,
        "added_by": ADMIN_ID,
        "added_at": datetime.now().isoformat()
    }
    
    save_accounts(accounts)
    
    user_accounts = accounts[target_user_id].get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    
    # Mask for display in confirmation
    masked_id = payment_id
    if len(payment_id) > 8:
        masked_id = payment_id[:4] + "****" + payment_id[-4:]
    
    await update.message.reply_text(
        f"✅ PAYMENT METHOD ADDED\n\n"
        f"👤 User: {username}\n"
        f"🆔 ID: `{target_user_id}`\n\n"
        f"💰 Method: {method.upper()}\n"
        f"🔢 Full ID: `{payment_id}`\n"
        f"🔒 Masked: `{masked_id}`\n"
        f"{f'📝 Details: {details}' if details else ''}\n\n"
        f"📅 Added: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}",
        parse_mode='Markdown'
    )
    
    # Notify user that admin added payment method for them
    try:
        user_notification = f"💳 PAYMENT METHOD ADDED BY ADMIN\n\n"
        user_notification += f"💰 Method: {method.upper()}\n"
        user_notification += f"🔢 ID: `{masked_id}`\n"
        user_notification += f"{f'📝 Details: {details}' if details else ''}\n\n"
        user_notification += f"✅ Your payment method has been added successfully!"
        
        await context.bot.send_message(
            int(target_user_id),
            user_notification,
            parse_mode='Markdown'
        )
        print(f"✅ Notified user {target_user_id} about payment method addition")
    except Exception as e:
        print(f"❌ Could not notify user {target_user_id}: {e}")


async def remove_payment_method(update: Update, context: CallbackContext):
    """Admin command to remove a payment method from user"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ REMOVE PAYMENT METHOD (Admin)\n\n"
            "Usage: `/removepayment [user_id] [method]`\n\n"
            "Example: `/removepayment 7319925086 bkash`\n\n"
            "Use `/listpayment [user_id]` to see all methods"
        )
        return
    
    target_user_id = context.args[0]
    method = context.args[1].lower()
    
    accounts = load_accounts()
    
    if target_user_id not in accounts:
        await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
        return
    
    if "payment_methods" not in accounts[target_user_id]:
        await update.message.reply_text(f"❌ No payment methods found for this user!")
        return
    
    if method not in accounts[target_user_id]["payment_methods"]:
        available = ', '.join(accounts[target_user_id]["payment_methods"].keys())
        await update.message.reply_text(f"❌ Method '{method}' not found!\n\nAvailable: {available}")
        return
    
    removed_data = accounts[target_user_id]["payment_methods"].pop(method)
    save_accounts(accounts)
    
    user_accounts = accounts[target_user_id].get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    
    await update.message.reply_text(
        f"✅ PAYMENT METHOD REMOVED\n\n"
        f"👤 User: {username}\n"
        f"🆔 ID: `{target_user_id}`\n\n"
        f"💰 Removed: {method.upper()}\n"
        f"🔢 ID: `{removed_data.get('id', 'N/A')}`\n\n"
        f"📅 Removed: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}",
        parse_mode='Markdown'
    )
    
    # Notify user that admin removed payment method
    try:
        user_notification = f"💳 PAYMENT METHOD REMOVED BY ADMIN\n\n"
        user_notification += f"💰 Method: {method.upper()}\n"
        user_notification += f"🔢 ID: `{removed_data.get('id', 'N/A')[:4]}****{removed_data.get('id', 'N/A')[-4:] if len(removed_data.get('id', 'N/A')) > 8 else ''}`\n\n"
        user_notification += f"❌ This payment method has been removed from your account."
        
        await context.bot.send_message(
            int(target_user_id),
            user_notification,
            parse_mode='Markdown'
        )
        print(f"✅ Notified user {target_user_id} about payment method removal")
    except Exception as e:
        print(f"❌ Could not notify user {target_user_id}: {e}")


async def list_payment_methods(update: Update, context: CallbackContext):
    """Admin command to list all payment methods of a user"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📋 LIST PAYMENT METHODS (Admin)\n\n"
            "Usage: `/listpayment [user_id]`\n\n"
            "Example: `/listpayment 7319925086`"
        )
        return
    
    target_user_id = context.args[0]
    
    accounts = load_accounts()
    
    if target_user_id not in accounts:
        await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
        return
    
    user_data = accounts[target_user_id]
    user_accounts = user_data.get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    telegram_username = user_data.get('telegram_username', '')
    
    payment_methods = user_data.get("payment_methods", {})
    
    if not payment_methods:
        await update.message.reply_text(
            f"📋 PAYMENT METHODS\n\n"
            f"👤 User: {username}\n"
            f"🆔 ID: `{target_user_id}`\n"
            f"📱 Telegram: @{telegram_username if telegram_username else 'N/A'}\n\n"
            f"❌ No payment methods found!\n\n"
            f"Add using: `/addpayment {target_user_id} [method] [id]`",
            parse_mode='Markdown'
        )
        return
    
    # Admin sees FULL IDs (no masking)
    message = f"📋 PAYMENT METHODS (Full View - Admin Only)\n\n"
    message += f"👤 User: {username}\n"
    message += f"🆔 ID: `{target_user_id}`\n"
    message += f"📱 Telegram: @{telegram_username if telegram_username else 'N/A'}\n\n"
    message += f"💰 Available Methods ({len(payment_methods)}):\n"
    
    for i, (method, data) in enumerate(payment_methods.items(), 1):
        payment_id = data.get('id', 'N/A')
        
        message += f"\n{i}. {method.upper()}\n"
        message += f"   ├─ Full ID: `{payment_id}`\n"
        if data.get('details'):
            message += f"   ├─ Details: {data.get('details')}\n"
        message += f"   ├─ Added by: {'Admin' if data.get('added_by') == ADMIN_ID else 'User'}\n"
        message += f"   └─ Added: {data.get('added_at', 'N/A')[:10]}\n"
    
    message += f"\n📝 Commands:\n"
    message += f"• `/addpayment {target_user_id} [method] [id]`\n"
    message += f"• `/removepayment {target_user_id} [method]`\n"
    message += f"• `/clearpayment {target_user_id}`"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def clear_payment_methods(update: Update, context: CallbackContext):
    """Admin command to clear all payment methods of a user"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🗑️ CLEAR PAYMENT METHODS (Admin)\n\n"
            "Usage: `/clearpayment [user_id]`\n\n"
            "Example: `/clearpayment 7319925086`\n\n"
            "⚠️ This will remove ALL payment methods of the user!"
        )
        return
    
    target_user_id = context.args[0]
    
    accounts = load_accounts()
    
    if target_user_id not in accounts:
        await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
        return
    
    user_data = accounts[target_user_id]
    user_accounts = user_data.get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    
    old_methods = user_data.get("payment_methods", {})
    count = len(old_methods)
    
    if count == 0:
        await update.message.reply_text(f"❌ No payment methods to clear for user {username}!")
        return
    
    method_names = ', '.join(old_methods.keys())
    
    user_data["payment_methods"] = {}
    accounts[target_user_id] = user_data
    save_accounts(accounts)
    
    await update.message.reply_text(
        f"✅ ALL PAYMENT METHODS CLEARED\n\n"
        f"👤 User: {username}\n"
        f"🆔 ID: `{target_user_id}`\n\n"
        f"🗑️ Removed {count} method(s): {method_names.upper()}\n\n"
        f"📅 Cleared: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}",
        parse_mode='Markdown'
    )
    
    # Notify user that admin cleared all payment methods
    try:
        user_notification = f"💳 ALL PAYMENT METHODS CLEARED BY ADMIN\n\n"
        user_notification += f"🗑️ Removed {count} method(s): {method_names.upper()}\n\n"
        user_notification += f"❌ All your payment methods have been removed from your account.\n\n"
        user_notification += f"Please contact admin to add new payment methods."
        
        await context.bot.send_message(
            int(target_user_id),
            user_notification,
            parse_mode='Markdown'
        )
        print(f"✅ Notified user {target_user_id} about payment methods clearance")
    except Exception as e:
        print(f"❌ Could not notify user {target_user_id}: {e}")

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
                    f"👤 ",
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
    """Remove accounts - supports both interactive menu and old style command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    
    # Check if old style command with arguments
    if context.args and len(context.args) >= 2:
        # Old style: /removeacc user_id username
        target_user_id = context.args[0]
        username = context.args[1]
        
        accounts = load_accounts()
        user_id_str = str(target_user_id)
        
        if user_id_str not in accounts:
            await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
            return
        
        user_data = accounts.get(user_id_str, {})
        if not isinstance(user_data, dict):
            await update.message.reply_text(f"❌ No accounts found for user `{target_user_id}`", parse_mode='Markdown')
            return
        
        removed = False
        new_accounts = []
        removed_account_name = None
        
        for acc in user_data.get("accounts", []):
            if acc['username'] == username:
                removed = True
                removed_account_name = acc.get('custom_name', acc['username'])
                # Remove from account_manager
                if acc.get('token') and acc['token'] in account_manager.token_info:
                    del account_manager.token_info[acc['token']]
                if acc.get('token') and acc['token'] in account_manager.token_owners:
                    del account_manager.token_owners[acc['token']]
            else:
                new_accounts.append(acc)
        
        if removed:
            user_data["accounts"] = new_accounts
            
            # If no accounts left, remove user completely
            if len(new_accounts) == 0:
                # Remove from account_manager
                if user_id_str in account_manager.user_tokens:
                    del account_manager.user_tokens[user_id_str]
                if user_id_str in account_manager.user_selected_accounts:
                    del account_manager.user_selected_accounts[user_id_str]
                
                # Remove user
                del accounts[user_id_str]
                save_accounts(accounts)
                
                await update.message.reply_text(
                    f"✅ User removed successfully!\n\n"
                    f"👤 User ID: `{target_user_id}`\n"
                    f"📛 Username: `{username}`\n"
                    f"🗑️ All accounts removed!"
                )
            else:
                # Update selected account if needed
                selected_id = user_data.get("selected_account_id", 1)
                if selected_id and removed:
                    user_data["selected_account_id"] = new_accounts[0]['id']
                
                accounts[user_id_str] = user_data
                save_accounts(accounts)
                
                # Re-initialize user tokens
                if user_id_str in account_manager.user_tokens:
                    await account_manager.initialize_user(int(target_user_id))
                
                await update.message.reply_text(
                    f"✅ Account removed successfully!\n\n"
                    f"👤 User ID: `{target_user_id}`\n"
                    f"📛 Username: `{username}`\n"
                    f"🗑️ Removed: {removed_account_name}\n"
                    f"📊 Remaining accounts: {len(new_accounts)}"
                )
        else:
            await update.message.reply_text(f"❌ Account `{username}` not found for user `{target_user_id}`", parse_mode='Markdown')
        
        return
    
    # New style: Show interactive menu (all users at once, chunked)
    await show_all_users_with_accounts(update, context)


async def show_all_users_with_accounts(update: Update, context: CallbackContext, page: int = 0):
    """Show all users with accounts - chunked by message limit (max 100 buttons per message)"""
    
    # Load fresh accounts
    accounts = load_accounts()
    
    # Collect users who have accounts (excluding admin)
    users_list = []
    
    for user_id_str, user_data in accounts.items():
        if user_id_str == str(ADMIN_ID):
            continue
        
        if not isinstance(user_data, dict):
            continue
        
        user_accounts = user_data.get("accounts", [])
        if not user_accounts:
            continue
        
        # Get user info
        first_account = user_accounts[0] if user_accounts else {}
        api_username = first_account.get('username', 'Unknown')
        
        # Try to get Telegram full name (avoid 400 error by catching exception)
        full_name = ""
        try:
            # Don't call get_chat for every user - use stored data
            full_name = user_data.get('full_name', '')
            if not full_name:
                full_name = f"User {user_id_str[-6:]}"
        except:
            full_name = f"User {user_id_str[-6:]}"
        
        display_name = full_name if full_name else f"User {user_id_str[-6:]}"
        
        users_list.append({
            'user_id': user_id_str,
            'display_name': display_name,
            'api_username': api_username,
            'account_count': len(user_accounts),
            'accounts': user_accounts  # Store accounts for direct access
        })
    
    if not users_list:
        if isinstance(update, Update) and hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text("✅ No users with accounts found!")
        else:
            await update.message.reply_text("✅ No users with accounts found!")
        return
    
    # Sort by display name
    users_list.sort(key=lambda x: x['display_name'])
    
    # Telegram limit: Max 100 buttons per message
    # We'll put each user in a separate button (without pagination within users)
    # If more than 100 users, we need to chunk into multiple messages
    items_per_chunk = 90  # Leave room for navigation buttons
    
    total_chunks = (len(users_list) + items_per_chunk - 1) // items_per_chunk
    
    if total_chunks > 1:
        # Store in context for chunk navigation
        context.user_data['remove_users_list'] = users_list
        context.user_data['remove_total_chunks'] = total_chunks
        context.user_data['remove_current_chunk'] = page
        
        start_idx = page * items_per_chunk
        end_idx = min(start_idx + items_per_chunk, len(users_list))
        chunk = users_list[start_idx:end_idx]
        
        # Create message
        message = f"🗑️ REMOVE USER ACCOUNTS\n\n"
        message += f"📊 Total users: {len(users_list)}\n"
        message += f"📄 Message {page + 1}/{total_chunks}\n"
        message += f"📋 Showing: {start_idx + 1} - {end_idx}\n\n"
        message += f"⚠️ Click on a user to see their accounts\n\n"
        
        # Create inline keyboard
        keyboard = []
        
        for user in chunk:
            button_text = f"👤 {user['display_name']}"
            if user['api_username'] != 'Unknown':
                button_text += f" (@{user['api_username']})"
            if user['account_count'] > 1:
                button_text += f" [{user['account_count']}]"
            
            callback_data = f"view_user_acc_{user['user_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Navigation buttons for chunks
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"remove_chunk_{page - 1}"))
        if page < total_chunks - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"remove_chunk_{page + 1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_remove_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send or edit message
        if isinstance(update, Update) and hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='none')
    
    else:
        # Single message (less than 100 users)
        message = f"🗑️ REMOVE USER ACCOUNTS\n\n"
        message += f"📊 Total users: {len(users_list)}\n\n"
        message += f"⚠️ Click on a user to see their accounts\n\n"
        
        # Create inline keyboard
        keyboard = []
        
        for user in users_list:
            button_text = f"👤 {user['display_name']}"
            if user['api_username'] != 'Unknown':
                button_text += f" (@{user['api_username']})"
            if user['account_count'] > 1:
                button_text += f" [{user['account_count']}]"
            
            callback_data = f"view_user_acc_{user['user_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_remove_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(update, Update) and hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='none')


async def handle_remove_chunk(update: Update, context: CallbackContext):
    """Handle chunk navigation for remove users list"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("remove_chunk_"):
        page = int(data.split("_")[2])
        await show_all_users_with_accounts(update, context, page)


async def view_user_accounts(update: Update, context: CallbackContext):
    """Show all accounts of a specific user with remove buttons"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("view_user_acc_"):
        user_id_str = data.replace("view_user_acc_", "")
        
        # Load fresh accounts
        accounts = load_accounts()
        
        if user_id_str not in accounts:
            await query.edit_message_text(f"❌ User not found!")
            return
        
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            await query.edit_message_text(f"❌ Invalid user data!")
            return
        
        user_accounts = user_data.get("accounts", [])
        account_count = len(user_accounts)
        
        # Get user info
        first_account = user_accounts[0] if user_accounts else {}
        api_username = first_account.get('username', 'Unknown')
        
        # Get display name
        display_name = user_data.get('full_name', f"User {user_id_str[-6:]}")
        
        # Build account list message
        message = f"👤 USER: {display_name}\n"
        message += f"🆔 ID: `{user_id_str}`\n"
        message += f"📛 API: {api_username}\n"
        message += f"📊 Total: {account_count} account(s)\n\n"
        
        if account_count == 0:
            message += f"❌ No accounts found!\n"
            keyboard = [[InlineKeyboardButton("🔙 Back to Users", callback_data="back_to_users_list")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        message += f"📋 ACCOUNTS:\n\n"
        
        # Create keyboard with each account
        keyboard = []
        
        for i, acc in enumerate(user_accounts, 1):
            account_id = acc.get('id', i)
            account_name = acc.get('custom_name', f"Account {account_id}")
            account_username = acc.get('username', 'Unknown')
            account_status = "✅" if acc.get('active', True) else "❌"
            token_status = "🔓" if acc.get('token') else "🔒"
            
            message += f"{i}. {account_status}{token_status} {account_name}\n"
            message += f"   └─ @{account_username}\n\n"
            
            # Button for each account
            button_text = f"🗑️ Remove {account_name}"
            callback_data = f"remove_single_acc_{user_id_str}_{account_id}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add special buttons
        if account_count > 1:
            keyboard.append([InlineKeyboardButton("🗑️ Remove ALL Accounts", callback_data=f"remove_all_accs_{user_id_str}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Users", callback_data="back_to_users_list")])
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_remove_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store current user in context
        context.user_data['current_user_id'] = user_id_str
        
        # Send or edit message
        if len(message) > 3500:
            await query.edit_message_text(message[:3500], reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def remove_single_account_from_list(update: Update, context: CallbackContext):
    """Remove a single account and refresh the account list"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("remove_single_acc_"):
        parts = data.split("_")
        # remove_single_acc_userid_accountid
        user_id_str = parts[3]
        account_id = int(parts[4])
        
        # Load fresh accounts
        accounts = load_accounts()
        
        if user_id_str not in accounts:
            await query.answer("User not found!", show_alert=True)
            return
        
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            await query.answer("Invalid user data!", show_alert=True)
            return
        
        user_accounts = user_data.get("accounts", [])
        
        # Find and remove the account
        account_removed = None
        new_accounts = []
        
        for acc in user_accounts:
            if acc.get('id') == account_id:
                account_removed = acc
                # Remove token from account_manager
                if acc.get('token') and acc['token'] in account_manager.token_info:
                    del account_manager.token_info[acc['token']]
                if acc.get('token') and acc['token'] in account_manager.token_owners:
                    del account_manager.token_owners[acc['token']]
            else:
                new_accounts.append(acc)
        
        if not account_removed:
            await query.answer("Account not found!", show_alert=True)
            return
        
        account_name = account_removed.get('custom_name', f"Account {account_id}")
        
        # Update accounts
        user_data["accounts"] = new_accounts
        
        # Update selected account if needed
        selected_id = user_data.get("selected_account_id", 1)
        if selected_id == account_id and new_accounts:
            user_data["selected_account_id"] = new_accounts[0]['id']
        
        # If no accounts left, remove user completely
        if len(new_accounts) == 0:
            # Remove from account_manager
            if user_id_str in account_manager.user_tokens:
                del account_manager.user_tokens[user_id_str]
            if user_id_str in account_manager.user_selected_accounts:
                del account_manager.user_selected_accounts[user_id_str]
            
            # Remove user
            del accounts[user_id_str]
            save_accounts(accounts)
            
            await query.answer(f"✅ {account_name} removed! User has no more accounts.", show_alert=True)
            
            # Go back to users list
            await show_all_users_with_accounts(update, context, 0)
            return
        else:
            accounts[user_id_str] = user_data
            save_accounts(accounts)
            
            # Re-initialize user tokens
            if user_id_str in account_manager.user_tokens:
                await account_manager.initialize_user(int(user_id_str))
            
            await query.answer(f"✅ {account_name} removed successfully!", show_alert=True)
        
        # Refresh the account list (stay on same user)
        await view_user_accounts(update, context)


async def remove_all_accounts_from_user(update: Update, context: CallbackContext):
    """Remove all accounts of a user and go back to users list"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("remove_all_accs_"):
        user_id_str = data.replace("remove_all_accs_", "")
        
        # Load fresh accounts
        accounts = load_accounts()
        
        if user_id_str not in accounts:
            await query.answer("User not found!", show_alert=True)
            return
        
        user_data = accounts[user_id_str]
        user_accounts = user_data.get("accounts", [])
        account_count = len(user_accounts)
        
        # Get user info for message
        first_account = user_accounts[0] if user_accounts else {}
        api_username = first_account.get('username', 'Unknown')
        
        # Remove all tokens from account_manager
        if user_id_str in account_manager.user_tokens:
            for token in account_manager.user_tokens[user_id_str]:
                if token in account_manager.token_info:
                    del account_manager.token_info[token]
                if token in account_manager.token_owners:
                    del account_manager.token_owners[token]
            del account_manager.user_tokens[user_id_str]
        
        if user_id_str in account_manager.user_selected_accounts:
            del account_manager.user_selected_accounts[user_id_str]
        
        # Remove user from accounts
        del accounts[user_id_str]
        save_accounts(accounts)
        
        await query.answer(f"✅ All {account_count} accounts removed!", show_alert=True)
        
        # Go back to users list
        await show_all_users_with_accounts(update, context, 0)


async def back_to_users_list(update: Update, context: CallbackContext):
    """Go back to users list"""
    query = update.callback_query
    await query.answer()
    
    # Clear cache and go back to users list
    await show_all_users_with_accounts(update, context, 0)


async def close_remove_menu(update: Update, context: CallbackContext):
    """Close the remove menu"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Menu closed!")

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
    
    # ALWAYS send user info to group (whether they joined channel/group or not)
    try:
        user = update.effective_user
        current_time = datetime.now().strftime('%d %B %Y, %H:%M:%S')
        
        # Check membership status for report only
        channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
        
        channel_status = "✅ Joined" if channel_joined else "❌ Not Joined"
        group_status = "✅ Joined" if group_joined else "❌ Not Joined"
        
        user_info = f"""
🆕 USER STARTED BOT 🆕

👤 Name: {user.full_name or 'N/A'}
🆔 ID: `{user.id}`
📛 Username: @{user.username if user.username else 'N/A'}
📅 Time: {current_time}

🔓 MEMBERSHIP STATUS:
📢 Channel: {channel_status}
💰 Group: {group_status}

📍 Status: {'✅ Full Access' if (channel_joined and group_joined) else '⚠️ Restricted Access'}
        """
        
        await context.bot.send_message(
            chat_id="@Wsalluser",  # Your group username/channel ID
            text=user_info,
            parse_mode='Markdown'
        )
        print(f"✅ User {user_id} info sent to group")
    except Exception as e:
        print(f"⚠️ Failed to send user info to group: {e}")
    
    # Now check membership requirements for bot access
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
        
        # UPDATED: Clean membership message
        await update.message.reply_text(
            f"🔒 ACCESS RESTRICTED\n\n"
            f"To use this bot, join:\n\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"└─ {channel_status}\n\n"
            f"💰 Payment Group: {REQUIRED_PAYMENT_GROUP}\n"
            f"└─ {group_status}\n\n"
            f"Missing: {missing_text}\n\n"
            f"👇 Join then click 'Check Membership'",
            reply_markup=reply_markup,
            parse_mode='none'
        )
        return
    
    # If membership requirements are satisfied, continue with normal flow
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
        
        # UPDATED: Clean start message
        await update.message.reply_text(
            f"🔥 WA OTP BOT\n\n"
            f"📱 {selected_account}\n"
            f"✅ {active_accounts_count} active\n"
            f"🎯 {remaining} remaining\n\n"
            f"💡 Reply to 'In Progress' with OTP\n\n"
            f"👑 Admin Mode",
            reply_markup=reply_markup,
            parse_mode='none'
        )
        return
        
    keyboard = [
        [KeyboardButton("🚀 Refresh Server"), KeyboardButton("📱 Switch Account")],
        [KeyboardButton("📦 My Settlements"), KeyboardButton("📊 Statistics")],
        [KeyboardButton("💳 Wallet")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    remaining = account_manager.get_user_remaining_checks(user_id)
    active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
    selected_account = account_manager.get_selected_account_name(user_id)
    
    if active_accounts == 0:
        await update.message.reply_text(
            f"❌ Access Denied!\n\n"
            f"Contact ",
            reply_markup=reply_markup,
            parse_mode='none'
        )
        return
    
    # UPDATED: Clean start message
    await update.message.reply_text(
        f"🔥 WA OTP BOT\n\n"
        f"📱 {selected_account}\n"
        f"✅ {active_accounts_count} active\n"
        f"🎯 {remaining} remaining\n\n"
        f"💡 Reply to 'In Progress' with OTP\n\n"
        f"✨ Welcome!",
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
            ""
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
            ""
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
            f""
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
                
                # NEW: Add to timeout tracker immediately
                phone_key = f"{cc}_{phone}_{user_id}"
                tracking = load_tracking()
                if "in_progress_timestamp" not in tracking:
                    tracking["in_progress_timestamp"] = {}
                tracking["in_progress_timestamp"][phone_key] = datetime.now().isoformat()
                save_tracking(tracking)
                print(f"⏰ Timer started for {phone} (Key: {phone_key})")
                
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
    text = update.message.text.strip()
    
    # ============ FIRST: Check for button clicks ============
    if text == "💳 Wallet":
        await wallet_command(update, context)
        return
    
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
    
    # ============ Admin menu options ============
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
    
    # ============ Check membership for non-admin ============
    if user_id != ADMIN_ID:
        channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
        
        if not (channel_joined and group_joined):
            keyboard = []
            if not channel_joined:
                keyboard.append([InlineKeyboardButton("📢 Join Channel", url=CHANNEL_INVITE_LINK)])
            if not group_joined:
                keyboard.append([InlineKeyboardButton("💰 Join Payment Group", url=PAYMENT_GROUP_INVITE_LINK)])
            keyboard.append([InlineKeyboardButton("🔄 Check Membership", callback_data="check_membership")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            channel_status = "❌ Not Joined" if not channel_joined else "✅ Joined"
            group_status = "❌ Not Joined" if not group_joined else "✅ Joined"
            missing_text = ", ".join(missing)
            await update.message.reply_text(
                f"🔒 ACCESS RESTRICTED\n\nTo use this bot, join:\n\n📢 Channel: {REQUIRED_CHANNEL}\n└─ {channel_status}\n\n💰 Payment Group: {REQUIRED_PAYMENT_GROUP}\n└─ {group_status}\n\nMissing: {missing_text}\n\n👇 Join then click 'Check Membership'",
                reply_markup=reply_markup,
                parse_mode='none'
            )
            return
    
    # ============ Check if user has accounts ============
    if account_manager.get_user_accounts_count(user_id) == 0 and user_id != ADMIN_ID:
        await update.message.reply_text(
            f"❌ No Accounts Found!\n\nPlease contact admin to add accounts for you.\n👤 ",
            parse_mode='none'
        )
        return
    
    # ============ Handle OTP submission if replying ============
    if update.message.reply_to_message:
        await handle_otp_submission(update, context)
        return
    
    # ============ Check if user is adding payment method ============
    if 'pending_payment_method' in context.user_data:
        await handle_payment_method_input(update, context)
        return
    
    # ============ Extract phone numbers ============
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
    
    # ============ If no phone numbers found ============
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

    # 🆕 Fake Payment
    application.add_handler(CommandHandler("fakepay", fake_payment_command))
    application.add_handler(CommandHandler("fakeenable", fake_payment_toggle_command))
    application.add_handler(CommandHandler("fakedisable", fake_payment_toggle_command))
    application.add_handler(CommandHandler("fakestatus", fake_payment_status_command))

    # 🆕 Wallet
    application.add_handler(CommandHandler("wallet", wallet_command))
    application.add_handler(CommandHandler("cancel", cancel_payment_method))

    # 🆕 Payment Admin
    application.add_handler(CommandHandler("addpayment", add_payment_method))
    application.add_handler(CommandHandler("removepayment", remove_payment_method))
    application.add_handler(CommandHandler("listpayment", list_payment_methods))
    application.add_handler(CommandHandler("clearpayment", clear_payment_methods))

    # ───────────────── CALLBACK HANDLERS ─────────────────
    application.add_handler(CallbackQueryHandler(handle_statistics_callback, pattern=r"^stats_"))
    application.add_handler(CallbackQueryHandler(handle_settlement_callback, pattern=r"^settlement_"))

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

    # 🆕 Extra callbacks (ONLY ONCE)
    application.add_handler(CallbackQueryHandler(handle_force_payment_complete, pattern=r"^force_payment_complete_"))
    application.add_handler(CallbackQueryHandler(handle_refresh_user_card, pattern=r"^refresh_user_card_"))
    application.add_handler(CallbackQueryHandler(handle_membership_check, pattern=r"^check_membership$"))

    # Wallet callbacks
    application.add_handler(
        CallbackQueryHandler(handle_wallet_callback, pattern=r"^(add_bkash|add_nagad|add_binance|close_wallet)$")
    )
    application.add_handler(CallbackQueryHandler(handle_wallet_open, pattern=r"^open_wallet$"))

    # Remove account callbacks
    application.add_handler(CallbackQueryHandler(handle_remove_chunk, pattern=r"^remove_chunk_"))
    application.add_handler(CallbackQueryHandler(back_to_users_list, pattern=r"^back_to_users_list$"))
    application.add_handler(CallbackQueryHandler(close_remove_menu, pattern=r"^close_remove_menu$"))
    application.add_handler(CallbackQueryHandler(view_user_accounts, pattern=r"^view_user_acc_"))
    application.add_handler(CallbackQueryHandler(remove_single_account_from_list, pattern=r"^remove_single_acc_"))
    application.add_handler(CallbackQueryHandler(remove_all_accounts_from_user, pattern=r"^remove_all_accs_"))

    # 🆕 User delete stuck number
    application.add_handler(CallbackQueryHandler(handle_user_delete_stuck_number, pattern=r"^user_delete_stuck_"))

    # ───────────────── MESSAGE HANDLERS ─────────────────
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_optimized))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment_method_input))

    # ───────────────── JOB QUEUE ─────────────────
    if application.job_queue:
        application.job_queue.run_daily(
            reset_daily_stats,
            time=datetime.strptime("10:00", "%H:%M").time()
        )

        application.job_queue.run_repeating(
            check_in_progress_timeout,
            interval=30,
            first=10
        )
    else:
        print("❌ JobQueue not available")

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

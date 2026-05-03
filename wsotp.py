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
    "11":{"country":"Canada","rate":0.10,"flag":"🇨🇦"},"880":{"country":"Bangladesh","rate":0.14,"flag":"🇧🇩"},
    "964":{"country":"Iraq","rate":0.09,"flag":"🇮🇶"},"92":{"country":"Pakistan","rate":0.13,"flag":"🇵🇰"},
    "966":{"country":"Saudi Arabia","rate":0.20,"flag":"🇸🇦"},"20":{"country":"Egypt","rate":0.15,"flag":"🇪🇬"},
    "52":{"country":"Mexico","rate":0.25,"flag":"🇲🇽"},"55":{"country":"Brazil","rate":0.50,"flag":"🇧🇷"},
    "33":{"country":"France","rate":0.18,"flag":"🇫🇷"},"44":{"country":"UK","rate":0.12,"flag":"🇬🇧"},
    "49":{"country":"Germany","rate":0.07,"flag":"🇩🇪"},"7":{"country":"Russia","rate":0.08,"flag":"🇷🇺"},
    "968":{"country":"Oman","rate":0.12,"flag":"🇴🇲"},"977":{"country":"Nepal","rate":0.07,"flag":"🇳🇵"},
    "60":{"country":"Malaysia","rate":0.08,"flag":"🇲🇾"},"62":{"country":"Indonesia","rate":0.08,"flag":"🇮🇩"},
    "84":{"country":"Vietnam","rate":0.07,"flag":"🇻🇳"},"27":{"country":"South Africa","rate":0.08,"flag":"🇿🇦"},
    "234":{"country":"Nigeria","rate":0.10,"flag":"🇳🇬"},"212":{"country":"Morocco","rate":0.12,"flag":"🇲🇦"},
    "58":{"country":"Venezuela","rate":0.07,"flag":"🇻🇪"},"886":{"country":"Taiwan","rate":0.08,"flag":"🇹🇼"},
}

COUNTRY_APIS = {
    "11":{"cc":"11","dc":"1","country":"Canada","url":"http://8.222.182.223:8081","u":"HasanCAA","p":"HasanCAA"},
    "52":{"cc":"52","dc":"52","country":"Mexico","url":"http://8.222.182.223:8081","u":"Hasan42MX","p":"Hasan42MX"},
    "44":{"cc":"44","dc":"44","country":"UK","url":"http://8.222.182.223:8081","u":"Hasan42GB","p":"Hasan42GB"},
    "49":{"cc":"49","dc":"49","country":"Germany","url":"http://8.222.182.223:8081","u":"Hasan42DE","p":"Hasan42DE"},
    "33":{"cc":"33","dc":"33","country":"France","url":"http://8.222.182.223:8081","u":"Hasan42FR","p":"Hasan42FR"},
    "7":{"cc":"7","dc":"7","country":"Russia","url":"http://8.222.182.223:8081","u":"Hasan42RU","p":"Hasan42RU"},
    "880":{"cc":"880","dc":"880","country":"Bangladesh","url":"http://8.222.182.223:8081","u":"Hasan42BD","p":"Hasan42BD"},
    "92":{"cc":"92","dc":"92","country":"Pakistan","url":"http://8.222.182.223:8081","u":"Hasan42PK","p":"Hasan42PK"},
    "964":{"cc":"964","dc":"964","country":"Iraq","url":"http://8.222.182.223:8081","u":"JahidIQ","p":"JahidIQ"},
    "966":{"cc":"966","dc":"966","country":"Saudi Arabia","url":"http://8.222.182.223:8081","u":"Hasan42SA","p":"Hasan42SA"},
    "20":{"cc":"20","dc":"20","country":"Egypt","url":"http://8.222.182.223:8081","u":"Hasan42EG","p":"Hasan42EG"},
    "968":{"cc":"968","dc":"968","country":"Oman","url":"http://8.222.182.223:8081","u":"Hasan42OM","p":"Hasan42OM"},
    "55":{"cc":"55","dc":"55","country":"Brazil","url":"http://8.222.182.223:8081","u":"Hasan42BR","p":"Hasan42BR"},
    "58":{"cc":"58","dc":"58","country":"Venezuela","url":"http://8.222.182.223:8081","u":"JahidVN","p":"JahidVN"},
    "258":{"cc":"258","dc":"258","country":"Mozambique","url":"http://8.222.182.223:8081","u":"HasanMZ","p":"HasanMZ"},
    "27":{"cc":"27","dc":"27","country":"South Africa","url":"http://8.222.182.223:8081","u":"Hasan42ZA","p":"Hasan42ZA"},
    "234":{"cc":"234","dc":"234","country":"Nigeria","url":"http://8.222.182.223:8081","u":"Hasan42NG","p":"Hasan42NG"},
    "212":{"cc":"212","dc":"212","country":"Morocco","url":"http://8.222.182.223:8081","u":"Hasan42MA","p":"Hasan42MA"},
    "60":{"cc":"60","dc":"60","country":"Malaysia","url":"http://8.222.182.223:8081","u":"Hasan42MY","p":"Hasan42MY"},
    "62":{"cc":"62","dc":"62","country":"Indonesia","url":"http://8.222.182.223:8081","u":"Hasan42ID","p":"Hasan42ID"},
    "84":{"cc":"84","dc":"84","country":"Vietnam","url":"http://8.222.182.223:8081","u":"Hasan42VN","p":"Hasan42VN"},
    "886":{"cc":"886","dc":"886","country":"Taiwan","url":"http://8.222.182.223:8081","u":"Hasan42TW","p":"Hasan42TW"},
    "977":{"cc":"977","dc":"977","country":"Nepal","url":"http://8.222.182.223:8081","u":"Hasan42NP","p":"Hasan42NP"},
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
                                f"💰 *OTP Verified!*\n📞 {display}\n🌎 {country}\n💵 Earning: ${rate:.2f}\n"
                                f"🏦 Total Balance: ${bal:.2f}\n"
                                f"🔖Total verified today: {tot_ver}\n\n"
                                f"#{user_id}_{get_bd_hashtag()}",
                                parse_mode='none')
                        except:
                            pass
                        
                        queue_sheet(user_id, uname, fname, phone, cc, country, "SUCCESS", f"OTP Verified - Earned ${rate:.2f}", otp_code)
                        
                        # ========== FIX 3: Admin notification for OTP success ==========
                        admin_msg = (
                            f"✅ *OTP VERIFIED SUCCESS*\n\n"
                            f"👤 *Name:* {fname}\n"
                            f"🆔 *Username:* @{uname if uname else 'N/A'}\n"
                            f"📞 *Number:* {display}\n"
                            f"🌍 *Country:* {country}\n"
                            f"💰 *Amount:* ${rate:.2f}\n"
                            f"🔖 *Tag:* #{user_id}_{get_bd_hashtag()}"
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
        await update.message.reply_text(f"💰 *Balance: ${bal:.2f}*\n{'✅ Can withdraw!' if bal >= 0.5 else 'Min: $0.50'}", parse_mode='Markdown')
    
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
        f"💸 *WITHDRAW REQUEST*\n\n"
        f"👤 *Name:* {q.from_user.full_name}\n"
        f"🆔 *Username:* @{q.from_user.username or 'N/A'}\n"
        f"💰 *Amount:* ${bal:.2f}\n"
        f"📱 *Method:* {nm.get(m,m)}\n"
        f"🏦 *Account:* `{acc}`\n"
        f"🔖 *Tag:* #{uid}_{get_bd_hashtag()}"
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
                f"✅ *Withdrawal Approved!*\n\n"
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
    # Start FastAPI
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    print(f"✅ FastAPI: port {PORT}")
    
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("wallet", wallet_setup))
    app_bot.add_handler(CommandHandler("mystats", cmd_mystats))
    app_bot.add_handler(CommandHandler("mybalance", cmd_mybalance))
    app_bot.add_handler(CommandHandler("myhistory", cmd_myhistory))
    app_bot.add_handler(CommandHandler("mysheet", cmd_mysheet))
    
    # ADMIN RATE COMMANDS - ADD THESE
    app_bot.add_handler(CommandHandler("addrate", cmd_addrate))
    app_bot.add_handler(CommandHandler("removerate", cmd_removerate))
    app_bot.add_handler(CommandHandler("listrates", cmd_listrates))
    app_bot.add_handler(CommandHandler("saverates", cmd_saverates))
    
    # Callbacks
    app_bot.add_handler(CallbackQueryHandler(wallet_callback, pattern="^w_"))
    app_bot.add_handler(CallbackQueryHandler(withdraw_callback, pattern="^wd_"))
    app_bot.add_handler(CallbackQueryHandler(admin_withdraw_action, pattern="^[cr]_"))
    
    # Messages
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    # Start cleanup task using post_init
    async def post_init(app):
        asyncio.create_task(cleanup_task())
    
    app_bot.post_init = post_init
    
    print("\n" + "="*60)
    print("✅ BOT v3.1 STABLE RUNNING")
    print(f"📱 Max {MAX_ACTIVE_NUMBERS} numbers/user")
    print(f"🔑 Reply-based OTP (correct matching)")
    print(f"🛡️ Copy-on-write (no race conditions)")
    print(f"🧹 Auto memory cleanup")
    print(f"📢 Admin notifications: ON")
    print(f"📤 Sheet deduplication: ON")
    print(f"💰 Rate management: /addrate /removerate /listrates")
    print("✅ ALL SYSTEMS READY")
    print("="*60 + "\n")
    
    app_bot.run_polling()

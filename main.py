import re
import os
import asyncio
import datetime
import jdatetime
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# --- تنظیمات ربات دوم (این مقادیر را دقیق تغییر دهید) ---
API_ID = 35673437            # همان ای‌آی‌دی قبلی شما
API_HASH = '0ef1cecd58655cb567c0bf6567bbdb98'  # همان ای‌پ‌آی هش قبلی شما
BOT_TOKEN = '303518559:AAEHaWu6bPyirGk9wEEeggpa6j3ze85KtMo'  # توکن ربات جدید (دوم) شما

SOURCE_GROUP_ID = -1002201375304  # آیدی عددی گروه مبدا جدید
TARGET_CHANNEL_ID = -1001441969577  # آیدی عددی کانال مقصد جدید
TARGET_TOPIC_ID = 234
# ---------------------------------------------
app = Flask('')
@app.route('/')
def home():
    return "Bot 2 is running perfectly!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

import re
import os
import asyncio
import datetime
import jdatetime
import sys
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from quart import Quart
from hypercorn.config import Config
from hypercorn.asyncio import serve

# پیکربندی لایه بافر خروجی جهت ثبت آنی وقایع در کنسول سرور ابری Render
sys.stdout.reconfigure(line_buffering=True)

# --- تنظیمات احراز هویت امن ---
API_ID = 36850805         
API_HASH = 'f3e90cffb1a5ca214883a0b886ad62b4'  
BOT_TOKEN = '303518559:AAEHaWu6bPyirGk9wEEeggpa6j3ze85KtMo'  

SOURCE_GROUP_ID = -1002201375304  
TARGET_CHANNEL_ID = -1001441969577  
TARGET_TOPIC_ID = 234

# --- انبارهای ذخیره موقت وضعیت ---
album_cache = {}     # ذخیره‌سازی پیام‌های مربوط به هر آلبوم (grouped_id -> [Message])
album_tasks = {}     # رهگیری تسک‌های فعال دی‌بانس برای جلوگیری از ارسال تکراری
last_text_cache = {} # ذخیره آخرین متن ارسال شده به تفکیک تاپیک

# --- تنظیمات وب‌سرور ناهمگام Quart ---
app = Quart(__name__)

@app.route('/')
async def home():
    return "Bot is running perfectly on a single-thread asynchronous loop!"

# --- توابع کمکی مبدل تاریخ و پاک‌سازی محتوا ---
def format_to_persian_date(num_str: str) -> str:
    """تبدیل اعداد انگلیسی تاریخ به فارسی و جایگذاری ممیز با کاراکتر استاندارد فارسی"""
    translation_table = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
    return num_str.translate(translation_table)

def clean_caption(text: str) -> str:
    """پاک‌سازی متون تبلیغاتی، لینک‌ها و شناسه‌های کاربری مزاحم"""
    if not text:
        return ""
    lines = text.split('\n')
    cleaned_lines = [
        line for line in lines 
        if not re.search(r'(@\w+|https?://[^\s]+|t\.me/[^\s]+)', line)
    ]
    
    # حذف خط آخر در صورتی که امضای کوتاه تبلیغاتی یا نام کانال باشد
    if cleaned_lines:
        last_line_words = cleaned_lines[-1].strip().split()
        if 0 < len(last_line_words) < 5:
            cleaned_lines.pop()
            
    return '\n'.join(cleaned_lines).strip()

def generate_date_payload(utc_date) -> str:
    """محاسبه دقیق زمان به وقت رسمی ایران و استخراج تاریخ شمسی و میلادی متناظر"""
    if utc_date.tzinfo is not None:
        utc_date = utc_date.replace(tzinfo=None)
        
    iran_offset = datetime.timedelta(hours=3, minutes=30)
    iran_date = utc_date + iran_offset
    
    gregorian_date = iran_date.strftime("%Y/%m/%d").replace("/", "٫") 
    
    jalali_raw = jdatetime.datetime.fromgregorian(datetime=iran_date).strftime("%Y/%m/%d")
    jalali_date = format_to_persian_date(jalali_raw)
    
    return f"\n\n🗓️ تاریخ انتشار : {jalali_date} - {gregorian_date}\n\n🆔 @rash_kham"

# --- نمونه‌سازی هوشمند کلاینت تلگرام ---
SESSION_DATA = os.environ.get("TELETHON_SESSION_STRING", "second_caption_bot_session")

bot = TelegramClient(
    SESSION_DATA, 
    API_ID, 
    API_HASH,
    device_model="Samsung SM-G998B",   
    system_version="SDK 31",           
    app_version="8.4.1 (2522)",        
    system_lang_code="en-US",
    lang_code="en"
)

# --- تسک ناهمگام دی‌بانس (مخصوص تجمیع و پردازش پایدار آلبوم‌ها) ---
async def process_delayed_album(grouped_id: int):
    """منتظر ماندن برای دریافت تمام اجزای آلبوم و سپس ارسال یکباره با کپشن اصلاح‌شده"""
    try:
        await asyncio.sleep(3.0)
        
        messages = album_cache.pop(grouped_id, None)
        album_tasks.pop(grouped_id, None)
        
        if not messages:
            return
            
        messages.sort(key=lambda msg: msg.id)
        
        raw_caption = next((msg.text for msg in messages if msg.text), "")
        
        if not raw_caption and TARGET_TOPIC_ID in last_text_cache:
            raw_caption = last_text_cache.pop(TARGET_TOPIC_ID)
            
        cleaned_text = clean_caption(raw_caption)
        # اصلاح ارور متادیتای تاریخ آلبوم بر اساس اولین قطعه رسانه
        date_signature = generate_date_payload(messages[0].date)
        final_caption = cleaned_text + date_signature if cleaned_text else date_signature
        
        media_payload = [msg.media for msg in messages]
        captions = [final_caption] + [""] * (len(media_payload) - 1)
        
        await bot.send_file(TARGET_CHANNEL_ID, media_payload, caption=captions)
        print(f"[🟢 OK] Album forwarded with memory text capture configuration.", flush=True)
        
    except asyncio.CancelledError:
        pass
    except Exception as error:
        print(f"Error occurred during album transmission: {error}", flush=True)

# --- گیرنده رویدادهای پیام جدید در گروه مبدا ---
@bot.on(events.NewMessage(chats=SOURCE_GROUP_ID))
async def incoming_message_handler(event):
    global last_text_cache
    
    if event.message.reply_to_msg_id != TARGET_TOPIC_ID:
        return

    # اصلاح خطای انتساب مستقیم متغیر محلی در کش متون خالص
    if event.message.text and not event.message.media:
        last_text_cache[TARGET_TOPIC_ID] = event.message.text
        return

    has_valid_media = (
        event.message.photo or
        event.message.video or 
        event.message.document or 
        event.message.audio or 
        event.message.voice
    )
    if not has_valid_media:
        return

    if event.message.grouped_id:
        gid = event.message.grouped_id
        if gid not in album_cache:
            album_cache[gid] = [] # اصلاح خطای خالی رها شدن آرایه
        album_cache[gid].append(event.message)
        
        if gid in album_tasks:
            album_tasks[gid].cancel()
            
        album_tasks[gid] = asyncio.create_task(process_delayed_album(gid))
        
    else:
        raw_caption = event.message.text or ""
        
        if not raw_caption and TARGET_TOPIC_ID in last_text_cache:
            raw_caption = last_text_cache.pop(TARGET_TOPIC_ID)
            
        cleaned_text = clean_caption(raw_caption)
        date_signature = generate_date_payload(event.message.date)
        final_caption = cleaned_text + date_signature if cleaned_text else date_signature
        
        try:
            await bot.send_file(TARGET_CHANNEL_ID, event.message.media, caption=final_caption)
            print(f"[🟢 OK] Single media forwarded with memory text capture configuration.", flush=True)
        except Exception as error:
            print(f"Error occurred during single media transmission: {error}", flush=True)

# --- اجرای یکپارچه سیستم همگرا بر روی لوپ رویداد ناهمگام ---
async def start_application():
    print("Initializing Client Session with anti-suspicion configurations...", flush=True)
    await bot.start(bot_token=BOT_TOKEN)
    print("Telegram client connected successfully.", flush=True)

    web_config = Config()
    # اختصاص پورت پیش‌فرض ۱۰اندازی ابری رندر با استاندارد هاستینگ
    web_config.bind = [f"0.0.0.0:{os.environ.get('PORT', '10000')}"]

    await asyncio.gather(
        serve(app, web_config),
        bot.run_until_disconnected()
    )

if __name__ == '__main__':
    try:
        asyncio.run(start_application())
    except KeyboardInterrupt:
        print("\n[🛑] Process terminated by administrator signal.", flush=True)

import re
import os
import asyncio
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# --- تنظیمات ربات دوم (این مقادیر را دقیق تغییر دهید) ---
API_ID = 36850805            # همان ای‌آی‌دی قبلی شما
API_HASH = 'f3e90cffb1a5ca214883a0b886ad62b4'  # همان ای‌پ‌آی هش قبلی شما
BOT_TOKEN = '303518559:AAEHaWu6bPyirGk9wEEeggpa6j3ze85KtMo'  # توکن ربات جدید (دوم) شما

SOURCE_GROUP_ID = -1002201375304  # آیدی عددی گروه مبدا جدید
TARGET_CHANNEL_ID = -1001441969577  # آیدی عددی کانال مقصد جدید
# ---------------------------------------------
TARGET_TOPIC_ID = 234

import datetime
import jdatetime

app = Flask('')
@app.route('/')
def home():
    return "Bot 2 is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

bot = TelegramClient('second_caption_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# انبار موقت برای جمع‌آوری آلبوم‌ها
album_cache = {}

# تابع کمکی برای تبدیل اعداد انگلیسی به فارسی (مخصوص تاریخ شمسی)
def en_to_fa(num_str):
    translation_table = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return num_str.translate(translation_table)

@bot.on(events.NewMessage(chats=SOURCE_GROUP_ID))
async def handler(event):
    # ۱. بررسی اینکه پیام حتماً در تاپیک مورد نظر باشد
    current_topic = event.message.reply_to_msg_id
    if current_topic != TARGET_TOPIC_ID:
        return

    # ۲. فیلتر کردن انواع رسانه‌ها
    has_media = (
        event.message.video or 
        event.message.document or 
        event.message.audio or 
        event.message.voice
    )
    
    if not has_media:
        return

    # ۳. محاسبات تاریخ میلادی (انگلیسی) و شمسی (فارسی) پیام
    msg_date = event.message.date
    gregorian_date = msg_date.strftime("%Y.%m.%d") # اعداد انگلیسی
    
    jalali_raw = jdatetime.datetime.fromgregorian(datetime=msg_date).strftime("%Y.%m.%d")
    jalali_date = en_to_fa(jalali_raw) # تبدیل به اعداد فارسی
    
    date_text = f"\n\n📅 تاریخ انتشار : {jalali_date} - {gregorian_date}"

    # ۴. مدیریت پیام‌های آلبومی (گروهی)
    if event.message.grouped_id:
        gid = event.message.grouped_id
        if gid not in album_cache:
            album_cache[gid] = []
        
        album_cache[gid].append(event.message)
        
        # ۲ ثانیه منتظر بمان تا تمام فایل‌های آلبوم برسند
        await asyncio.sleep(2)
        
        if album_cache[gid][0].id == event.message.id:
            messages_to_send = album_cache[gid]
            
            caption = ""
            for msg in messages_to_send:
                if msg.text:
                    caption = msg.text
                    break
            
            if caption:
                lines = caption.split('\n')
                cleaned_lines = [l for l in lines if not re.search(r'(@\w+|https?://[^\s]+|t\.me/[^\s]+)', l)]
                caption = '\n'.join(cleaned_lines).strip()
                
                caption_lines = caption.split('\n')
                if caption_lines and 0 < len(caption_lines[-1].strip().split()) < 5:
                    caption_lines.pop()
                    caption = '\n'.join(caption_lines).strip()

            signature = "\n\n🆔 @rash_kham"
            final_caption = caption + date_text + signature if caption else date_text + signature
            
            try:
                media_list = [msg.media for msg in messages_to_send]
                # ارسال فایل‌ها به صورت آلبوم یکجا (کپشن فقط روی فایل اول اعمال می‌شود)
                await bot.send_file(TARGET_CHANNEL_ID, media_list, caption=[final_caption] + [""] * (len(media_list) - 1))
            except Exception as e:
                print(f"Error sending album: {e}")
            
            del album_cache[gid]
            
    else:
        # ۵. مدیریت پیام‌های تکی
        caption = event.message.text or ""
        if caption:
            lines = caption.split('\n')
            cleaned_lines = [l for l in lines if not re.search(r'(@\w+|https?://[^\s]+|t\.me/[^\s]+)', l)]
            caption = '\n'.join(cleaned_lines).strip()
            
            caption_lines = caption.split('\n')
            if caption_lines and 0 < len(caption_lines[-1].strip().split()) < 5:
                caption_lines.pop()
                caption = '\n'.join(caption_lines).strip()

        signature = "\n\n🆔 @rash_kham"
        final_caption = caption + date_text + signature if caption else date_text + signature
        
        try:
            file_size_mb = event.message.file.size / (1024 * 1024) if event.message.file else 0
            
            if file_size_mb > 400: # فایل‌های سنگین بالای ۴۰۰ مگابایت
                # فوروارد بدون نقل‌قول و کاملاً مخفی
                await event.message.forward_to(TARGET_CHANNEL_ID, drop_author=True)
                # ارسال کپشن و تاریخ به عنوان پیام متنی مستقل زیر فایل
                await bot.send_message(TARGET_CHANNEL_ID, final_caption)
            else:
                # فایل‌های معمولی
                await bot.send_file(TARGET_CHANNEL_ID, event.message.media, caption=final_caption)
        except Exception as e:
            print(f"Error sending single file: {e}")

print("ربات دوم با فرمت تاریخ اختصاصی و رفع مشکل آلبوم‌ها آنلاین شد!")
bot.run_until_disconnected()

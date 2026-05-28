import re
import os
import asyncio
import datetime
import jdatetime
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# --- تنظیمات ربات دوم (این مقادیر را دقیق تغییر دهید) ---
API_ID = 36850805            # همان ای‌آی‌دی قبلی شما
API_HASH = 'f3e90cffb1a5ca214883a0b886ad62b4'  # همان ای‌پ‌آی هش قبلی شما
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

Thread(target=run).start()

bot = TelegramClient('second_caption_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# انبار موقت برای جمع‌آوری آلبوم‌ها
album_cache = {}

# تابع کمکی برای تبدیل اعداد انگلیسی به فارسی و قرار دادن ممیز
def format_to_persian_date(num_str):
    translation_table = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
    return num_str.translate(translation_table)

@bot.on(events.NewMessage(chats=SOURCE_GROUP_ID))
async def handler(event):
    # ۱. بررسی آیدی تاپیک
    if event.message.reply_to_msg_id != TARGET_TOPIC_ID:
        return

    # ۲. فیلتر کردن رسانه‌ها
    has_media = (
        event.message.photo or
        event.message.video or 
        event.message.document or 
        event.message.audio or 
        event.message.voice
    )
    if not has_media:
        return

    # ۳. محاسبات دقیق تاریخ با فرمت ممیز (٫)
    msg_date = event.message.date
    gregorian_date = msg_date.strftime("%Y/%m/%d").replace("/", "٫") 
    jalali_raw = jdatetime.datetime.fromgregorian(datetime=msg_date).strftime("%Y/%m/%d")
    jalali_date = format_to_persian_date(jalali_raw)
    
    date_text = f"\n\n📅 تاریخ انتشار : {jalali_date} - {gregorian_date}"
    signature = "\n\n🆔 @rash_kham"

    # ۴. بخش مدیریت آلبوم‌ها (رسانه‌های گروهی) + جفت‌سازی با متن قبل
    if event.message.grouped_id:
        gid = event.message.grouped_id
        if gid not in album_cache:
            album_cache[gid] = []
        album_cache[gid].append(event.message)
        
        # ۳ ثانیه مهلت برای جمع‌آوری تمام قطعات آلبوم
        await asyncio.sleep(3)
        
        # فقط اولین قطعه دریافت شده، عملیات ارسال را مدیریت می‌کند
        if album_cache[gid][0].id == event.message.id:
            messages_to_send = album_cache[gid]
            
            # مرتب‌سازی پیام‌های آلبوم بر اساس آیدی برای پیدا کردن اولین قطعه واقعی
            messages_to_send.sort(key=lambda m: m.id)
            first_media_id = messages_to_send[0].id
            
            # بررسی اینکه آیا خود آلبوم متنی دارد یا خیر
            extracted_caption = next((msg.text for msg in messages_to_send if msg.text), "")
            
            # اگر آلبوم اصلاً متن نداشت، پیام متنیِ قبل از کل آلبوم را شکار کن
            if not extracted_caption:
                try:
                    # گرفتن پیام‌های قبل از شروع اولین قطعه آلبوم
                    history = await bot.get_messages(SOURCE_GROUP_ID, limit=1, max_id=first_media_id)
                    if history and history[0].text and not history[0].media:
                        # مطمئن می‌شویم پیام متنی قبلی در همین تاپیک باشد
                        if history[0].reply_to_msg_id == TARGET_TOPIC_ID:
                            extracted_caption = history[0].text
                except Exception as e:
                    print(f"Error fetching past message for album: {e}")
            
            # پاک‌سازی متن (حذف لینک‌ها و آیدی‌های تبلیغاتی)
            if extracted_caption:
                lines = extracted_caption.split('\n')
                cleaned_lines = [l for l in lines if not re.search(r'(@\w+|https?://[^\s]+|t\.me/[^\s]+)', l)]
                extracted_caption = '\n'.join(cleaned_lines).strip()
                
                caption_lines = extracted_caption.split('\n')
                if caption_lines and 0 < len(caption_lines[-1].strip().split()) < 5:
                    caption_lines.pop()
                    extracted_caption = '\n'.join(caption_lines).strip()

            final_caption = extracted_caption + date_text + signature if extracted_caption else date_text + signature
            
            try:
                media_list = [msg.media for msg in messages_to_send]
                # ارسال کل آلبوم به همراه متن شکار شده از پیام قبل
                await bot.send_file(TARGET_CHANNEL_ID, media_list, caption=[final_caption] + [""] * (len(media_list) - 1))
            except Exception as e:
                print(f"Error sending album: {e}")
            
            # خالی کردن انبار آلبوم
            del album_cache[gid]
            
    # ۵. بخش مدیریت فایل‌های تکی + جفت‌سازی با متن قبل
    else:
        extracted_caption = event.message.text or ""
        
        # اگر فایل تکی متن نداشت، پیام متنیِ یک ثانیه قبل را بردار
        if not extracted_caption:
            try:
                history = await bot.get_messages(SOURCE_GROUP_ID, limit=1, max_id=event.message.id)
                if history and history[0].text and not history[0].media:
                    if history[0].reply_to_msg_id == TARGET_TOPIC_ID:
                        extracted_caption = history[0].text
            except Exception as e:
                print(f"Error fetching past message for single file: {e}")
        
        # پاک‌سازی متن فایل تکی
        if extracted_caption:
            lines = extracted_caption.split('\n')
            cleaned_lines = [l for l in lines if not re.search(r'(@\w+|https?://[^\s]+|t\.me/[^\s]+)', l)]
            extracted_caption = '\n'.join(cleaned_lines).strip()
            
            caption_lines = caption.split('\n')
            if caption_lines and 0 < len(caption_lines[-1].strip().split()) < 5:
                caption_lines.pop()
                extracted_caption = '\n'.join(caption_lines).strip()

        final_caption = extracted_caption + date_text + signature if extracted_caption else date_text + signature
        
        try:
            await bot.send_file(TARGET_CHANNEL_ID, event.message.media, caption=final_caption)
        except Exception as e:
            print(f"Error sending single file: {e}")

print("ربات دوم (نسخه هوشمند جفت‌سازی آلبوم و رسانه تکی با متن قبل) فعال شد!")
bot.run_until_disconnected()

import re
import os
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread
import asyncio
from deep_translator import GoogleTranslator

# --- تنظیمات ربات دوم (این مقادیر را دقیق تغییر دهید) ---
API_ID = 36850805            # همان ای‌آی‌دی قبلی شما
API_HASH = 'f3e90cffb1a5ca214883a0b886ad62b4'  # همان ای‌پ‌آی هش قبلی شما
BOT_TOKEN = '303518559:AAEHaWu6bPyirGk9wEEeggpa6j3ze85KtMo'  # توکن ربات جدید (دوم) شما

SOURCE_GROUP_ID = -1002201375304  # آیدی عددی گروه مبدا جدید
TARGET_CHANNEL_ID = -1001441969577  # آیدی عددی کانال مقصد جدید
# ---------------------------------------------

app = Flask('')
@app.route('/')
def home():
    return "Bot 2 is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

bot = TelegramClient('second_caption_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# لیست موقت ضد تکرار پیام
processed_messages = set()

# تابع کمکی ترجمه مجهز به تایم‌اوت ۵ ثانیه‌ای
async def translate_with_timeout(text, timeout_seconds=5):
    try:
        loop = asyncio.get_event_loop()
        translated = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: GoogleTranslator(source='auto', target='fa').translate(text)),
            timeout=timeout_seconds
        )
        return translated
    except Exception as e:
        print(f"Translation timeout or error: {e}")
        return text

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
    
    if has_media:
        # جلوگیری از ارسال پیام تکراری
        if event.message.id in processed_messages:
            return
        processed_messages.add(event.message.id)
        if len(processed_messages) > 100:
            processed_messages.clear()

        caption = event.message.text or ""
        
        if caption:
            # ۳. ترجمه متن با امنیت بالا
            if any(c.isalnum() for c in caption):
                caption = await translate_with_timeout(caption, timeout_seconds=5)

            # ۴. پاک کردن خطوط حاوی آیدی یا لینک
            lines = caption.split('\n')
            cleaned_lines = []
            for line in lines:
                if not re.search(r'(@\w+|https?://[^\s]+|t\.me/[^\s]+)', line):
                    cleaned_lines.append(line)
            caption = '\n'.join(cleaned_lines).strip()
            
            # ۵. حذف تبلیغات انتهای کپشن
            caption_lines = caption.split('\n')
            if caption_lines:
                last_line = caption_lines[-1].strip()
                if 0 < len(last_line.split()) < 5:
                    caption_lines.pop()
                    caption = '\n'.join(caption_lines).strip()

        # ۶. اضافه کردن امضا
        signature = "\n\n🆔 @rash_kham"
        final_caption = caption + signature if caption else "🆔 @rash_kham"
        
        try:
            media_to_send = (
                event.message.video or 
                event.message.document or 
                event.message.audio or 
                event.message.voice
            )
            await bot.send_file(TARGET_CHANNEL_ID, media_to_send, caption=final_caption)
        except Exception as e:
            print(f"Error sending file: {e}")

print("ربات دوم اصلاح شد و آنلاین است!")
bot.run_until_disconnected()

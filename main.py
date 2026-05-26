import re
import os
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

app = Flask('')
@app.route('/')
def home():
    return "Bot 2 is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

# تغییر نام سشن برای اینکه با ربات اول تداخل پیدا نکند
bot = TelegramClient('second_caption_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# لیست موقت ضد تکرار پیام
processed_messages = set()

# لیست موقت ضد تکرار پیام
processed_messages = set()

# عدد آیدی موضوع "در صف انتشار" را اینجا وارد کنید (مثلاً 45)
TARGET_TOPIC_ID = 234 

@bot.on(events.NewMessage(chats=SOURCE_GROUP_ID))
async def handler(event):
    # ۱. بررسی اینکه پیام حتماً متعلق به موضوع (Topic) مورد نظر باشد
    # در تلگرام پیام‌های تاپیک‌ها به عنوان ریپلای به آیدی آن تاپیک شناخته می‌شوند
    current_topic = event.message.reply_to_msg_id
    
    if current_topic != TARGET_TOPIC_ID:
        return # اگر پیام در این موضوع نبود، ربات بی‌خیال می‌شود و ادامه نمی‌دهد

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
            # ۳. پاک کردن خطوط حاوی آیدی یا لینک
            lines = caption.split('\n')
            cleaned_lines = []
            for line in lines:
                if not re.search(r'(@\w+|https?://[^\s]+|t\.me/[^\s]+)', line):
                    cleaned_lines.append(line)
            
            caption = '\n'.join(cleaned_lines).strip()
            
            # ۴. حذف کردن نوشته‌های تبلیغاتی انتهای کپشن
            caption_lines = caption.split('\n')
            if caption_lines:
                last_line = caption_lines[-1].strip()
                if 0 < len(last_line.split()) < 5:
                    caption_lines.pop()
                    caption = '\n'.join(caption_lines).strip()

        # ۵. اضافه کردن امضای جدید با یک خط فاصله
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
            print(f"Error: {e}")

print("ربات دوم (مخصوص تاپیک در صف انتشار) روشن شد!")
bot.run_until_disconnected()

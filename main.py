import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pytesseract
from PIL import Image
import io
import re

# ==================== التكوين الخاص بالذكاء الاصطناعي (CONFIG) ====================
TOKEN = 'YOUR_BOT_TOKEN_HERE'  # ضع توكن البوت الخاص بك هنا
AI_API_KEY = 'YOUR_AI_API_KEY_HERE'  # مفتاح الـ API الخاص بالذكاء الاصطناعي
AI_API_URL = 'https://api.openai.com/v1'  # الأي بي / الرابط الخاص بالخدمة (عدله حسب شركتك)
# ==============================================================================

bot = telebot.TeleBot(TOKEN)

# 2. مسار Tesseract (مهم جداً للويندوز: احذف علامة # من بداية السطر التالي وعدل المسار إذا لزم الأمر)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def clean_and_extract_numbers(image_bytes):
    # تحويل الصورة للأبيض والأسود لتسريع وتسهيل القراءة
    image = Image.open(io.BytesIO(image_bytes)).convert('L')
    
    # القراءة السريعة للبيانات
    text = pytesseract.image_to_string(image, config='--psm 6')
    
    # تحويل الأرقام العربية إلى إنجليزية
    arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    text = text.translate(arabic_to_english)
    
    # استخراج الأرقام التي تبدأ بـ 07 وتتكون من 11 رقم حصراً
    numbers = re.findall(r'07\d{9}', text)
    
    # إزالة التكرار مع الحفاظ على الترتيب
    return list(dict.fromkeys(numbers))

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⚡ جاري المسح والاستخراج...")
    
    try:
        # تحميل الصورة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # استخراج الأرقام
        extracted_numbers = clean_and_extract_numbers(downloaded_file)
        
        if len(extracted_numbers) >= 2:
            client_num = extracted_numbers[0]
            customer_num = extracted_numbers[1]
            
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("🏢 اتصال بالعميل", url=f"whatsapp://send?phone=964{client_num[1:]}"),
                InlineKeyboardButton("📞 اتصال بالزبون", url=f"whatsapp://send?phone=964{customer_num[1:]}")
            )
            bot.edit_message_text(f"✅ تمت القراءة بنجاح:\n\nالعميل: `{client_num}`\nالزبون: `{customer_num}`", 
                                  chat_id, msg.message_id, reply_markup=markup, parse_mode="Markdown")
            
        elif len(extracted_numbers) == 1:
            num = extracted_numbers[0]
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📞 اتصال بالرقم", url=f"whatsapp://send?phone=964{num[1:]}"))
            bot.edit_message_text(f"⚠️ تم العثور على رقم واحد فقط:\n`{num}`", chat_id, msg.message_id, reply_markup=markup, parse_mode="Markdown")
            
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✍️ إدخال يدوي", callback_data="manual_entry"))
            bot.edit_message_text("❌ لم يتم العثور على أرقام واضحة.", chat_id, msg.message_id, reply_markup=markup)
            
    except Exception as e:
        bot.edit_message_text("⚠️ حدث خطأ، تأكد من وضوح الصورة.", chat_id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "manual_entry")
def manual_entry(call):
    msg = bot.send_message(call.message.chat.id, "يرجى كتابة رقم الهاتف يدوياً (11 رقم تبدأ بـ 07):")
    bot.register_next_step_handler(msg, process_manual_number)

def process_manual_number(message):
    chat_id = message.chat.id
    phone_number = message.text.strip()
    
    # تحويل الأرقام العربية إلى إنجليزية إن وجدت
    arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    phone_number = phone_number.translate(arabic_to_english)

    if re.fullmatch(r'07\d{9}', phone_number):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📞 اتصال بالرقم", url=f"whatsapp://send?phone=964{phone_number[1:]}"))
        bot.send_message(chat_id, f"✅ تم الإدخال:\n`{phone_number}`", reply_markup=markup, parse_mode="Markdown")
    else:
        msg = bot.send_message(chat_id, "⚠️ رقم غير صالح. يرجى إدخال 11 رقماً تبدأ بـ 07:")
        bot.register_next_step_handler(msg, process_manual_number)

if __name__ == '__main__':
    print("🤖 البوت يعمل الآن...")
    bot.infinity_polling()
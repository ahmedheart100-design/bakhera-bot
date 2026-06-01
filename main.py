import os
import re
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv

# تحميل المتغيرات السرية والبيئية من ملف .env تلقائياً
load_dotenv()

# قراءة التوكن والمفتاح بأمان كامل لحماية الشفرة على GitHub
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# تهيئة عميل الذكاء الاصطناعي بنظام جوجل الحديث السريع
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# تحديد هيكل البيانات مسبقاً لسرعة المعالجة (Structured Output)
class ReceiptData(BaseModel):
    customer_phone: str
    client_name: str
    customer_name: str
    receipt_no: str
    final_report: str

async def analyze_receipt_ultra_fast(image_bytes, additional_text=""):
    """ دالة معالجة الصورة بأقصى سرعة ممكنة عبر الـ RAM """
    try:
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg"
        )
        
        prompt = f"""
        أنت نظام أتمتة لشركة "الباخرة". استخرج بدقة فورية:
        1. customer_phone: هاتف الزبون.
        2. client_name: اسم البيج/المتجر.
        3. customer_name: اسم الزبون.
        4. receipt_no: رقم الوصل.
        5. final_report: التبليغ النهائي لسبب الرفض أو التأجيل بناءً على تحديث المندوب التالي: ({additional_text}). لا تكتب أبداً تم التوصيل بنجاح.
        """
        
        # استدعاء غير متزامن واستخدام نظام الـ Pydantic لوقف أي تأخير في معالجة الجيسون
        response = await asyncio.to_thread(
            ai_client.models.generate_content,
            model='gemini-2.5-flash',
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReceiptData,
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"🛑 خطأ في المعالجة فائقة السرعة: {e}")
        return None

async def process_delivery_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.photo: return
        
    # سحب الصورة كبايتات فوراً وبدون تخزين على القرص الصلب
    photo_file = await message.photo[-1].get_file()
    image_bytes = await photo_file.download_as_bytearray()
    
    additional_text = message.caption if message.caption else ""
    
    # معالجة فورية نفاثة بالذكاء الاصطناعي
    ai_results = await analyze_receipt_ultra_fast(bytes(image_bytes), additional_text)
    
    if not ai_results:
        await message.reply_text("❌ حدث خطأ غير متوقع في النظام الفوري.")
        return

    # تنظيف النصوص البرمجية لسرعة العرض والتأمين وضمان استقرار الشات
    receipt_id = str(ai_results.get("receipt_no", "")).strip()
    phone = str(ai_results.get("customer_phone", "")).strip()
    client = str(ai_results.get("client_name", "")).strip()
    customer = str(ai_results.get("customer_name", "")).strip()
    report_text = str(ai_results.get("final_report", "")).strip()

    keyboard = []
    if phone and phone not in ["null", "غير محدد", ""]:
        clean_phone = re.sub(r'\D', '', phone)
        if clean_phone.startswith('0'): 
            clean_phone = '964' + clean_phone[1:]
        elif clean_phone.startswith('+'):
            clean_phone = clean_phone[1:]
        elif not clean_phone.startswith('964'):
            clean_phone = '964' + clean_phone
            
        whatsapp_url = f"https://wa.me/{clean_phone}"
        keyboard.append([InlineKeyboardButton(f"🟢 فتح واتساب والاتصال | {customer}", url=whatsapp_url)])
    
    # نص التبليغ الاحترافي المنسق للعميل عند الضغط على زر النسخ الفوري
    full_forward_text = (
        f"🚨 تبليغ شحنة - شركة الباخرة 🚨\n\n"
        f"🏪 العميل: {client}\n"
        f"🧾 رقم الوصل: {receipt_id}\n"
        f"👤 الزبون: {customer}\n"
        f"📝 التبليغ: {report_text}"
    )
    keyboard.append([InlineKeyboardButton("📋 نسخ التبليغ الجاهز للعميل", switch_inline_query_current_chat=full_forward_text)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # تصميم لوحة تحكم داخلية فخمة ومريحة للعين للموظف الاحترافي
    dashboard_message = (
        f"📋 لـوحـة مـعـالـجـة الـتـبـلـيـغـات 📋\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 رقم الوصل  │ {receipt_id}\n"
        f"🏪 العميل     │ {client}\n"
        f"👤 الزبون     │ {customer}\n"
        f"📱 رقم الهاتف │ {phone}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚙️ الإجراءات الفورية المتوفرة:"
    )

    await message.reply_text(text=dashboard_message, reply_markup=reply_markup)

def main():
    # بناء البوت مع تفعيل الاتصالات المتوازية المباشرة لسرعة استجابة قصوى
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, process_delivery_report))
    
    print("🚀 محرك الباخرة النفاث يعمل الآن بأعلى معايير الأتمتة الاحترافية وسرعة الضوء...")
    app.run_polling()

if __name__ == "__main__":
    main()
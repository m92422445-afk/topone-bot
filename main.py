import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from flask import Flask
from threading import Thread

# سيرفر وهمي لتشغيل البوت مجاناً على Render وتخطي نظامهم
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive"
def run(): app.run(host='0.0.0.0', port=8080)

# ===== إعدادات البيانات الأساسية والربط التلقائي للبوت الجديد لمحمد =====
BOT_TOKEN = "8866415092:AAEWZ0wkV2BRWv1dpZRvengbg0i3G1M4mYk"
ADMIN_CHAT_ID = 8890068169  # معرف حساب محمد لتصله إشعارات الحوالات واللوحة

NEMER_CARD_TOKEN = "eB-x5a-OlQgfmb_p5E2Ggp--mitrxjFSDgKuZO-cl"

# حسابات كاش محمد الحقيقية والمعدلة
SHAM_CASH_ACCOUNT = "d1f48dff44e504323052c3b6533cd296"
SYRIATEL_CASH_ACCOUNT = "78682855"

PRICES = {"60": "180 ل.س", "325": "800 ل.س", "660": "1600 ل.س", "1800": "4000 ل.س"}
PRODUCT_IDS = {"60": "60", "325": "325", "660": "660", "1800": "1800"}

bot = telebot.TeleBot(BOT_TOKEN)
user_orders = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_orders[chat_id] = {}
    
    # إجبار البوت على إلغاء أي خطوة معلقة وتصفير النظام فوراً عند الضغط على ستارت
    bot.clear_step_handler_by_chat_id(chat_id=chat_id)
    
    text = "أهلاً بك في متجر توب ون ستور لشحن شدات ببجي في سوريا فِنا\n\nالرجاء اختيار الباقة المطلوبة لبدء الشحن:"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💎 60 شدة", callback_data="pack_60"))
    markup.row(InlineKeyboardButton("💎 325 شدة", callback_data="pack_325"))
    markup.row(InlineKeyboardButton("💎 660 شدة", callback_data="pack_660"))
    markup.row(InlineKeyboardButton("💎 1800 شدة", callback_data="pack_1800"))
    
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pack_'))
def handle_pack_selection(call):
    chat_id = call.message.chat.id
    pack = call.data.split('_')[1]
    user_orders[chat_id]['pack'] = pack
    user_orders[chat_id]['price'] = PRICES[pack]
    
    text = f"📦 باقة: {pack} شدة\n💰 السعر الحالي: {PRICES[pack]}\n\nهل أنت موافق وتريد المتابعة؟"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✅ موافقة", callback_data="agree_id"))
    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "agree_id")
def ask_for_id(call):
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "🎯 يرجى كتابة الـ ID الخاص بك في لعبة ببجي بدقة:")
    bot.register_next_step_handler(msg, get_player_id)

def get_player_id(message):
    chat_id = message.chat.id
    if message.text == '/start':
        send_welcome(message)
        return
        
    user_orders[chat_id]['player_id'] = message.text
    
    text = "💳 الرجاء اختيار طريقة الدفع المناسبة لك لعملية التحويل:"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🚀 سيريتل كاش", callback_data="pay_syriatel"))
    markup.row(InlineKeyboardButton("💎 شام كاش", callback_data="pay_sham"))
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment_method(call):
    chat_id = call.message.chat.id
    method = call.data.split('_')[1]
    price = user_orders[chat_id]['price']
    
    if method == "syriatel":
        text = f"📌 تم اختيار سيريتل كاش\n💰 المبلغ المطلوب تحويله: {price}\n📱 رقم الحساب للتحويل: `{SYRIATEL_CASH_ACCOUNT}`\n\nالرجاء إرسال إشعار الحوالة كـ (صورة واضحة) هنا في البوت بعد التحويل:"
        bot.edit_message_text(text, chat_id, call.message.message_id)
    else:
        text = f"📌 تم اختيار شام كاش\n💰 المبلغ المطلوب تحويله: {price}\n📱 حساب التحويل: `{SHAM_CASH_ACCOUNT}`\n\nالرجاء مسح الـ QR كود المرفق بالأسفل لإتمام الدفع، ثم أرسل إشعار الحوالة كـ (صورة واضحة) هنا:"
        bot.edit_message_text(text, chat_id, call.message.message_id)
        try: bot.send_photo(chat_id, "AgACAgQAAxkBAAIB6mccS7_M0T4HjXv0V9K6j8vB5z9AAALvuxcxG6BUP9b9E2Ggp--mitrxjFSDgKuZO-cl")
        except: pass
        
    bot.register_next_step_handler(call.message, get_payment_screenshot)

def get_payment_screenshot(message):
    chat_id = message.chat.id
    if message.text == '/start':
        send_welcome(message)
        return
        
    if message.content_type != 'photo':
        msg = bot.send_message(chat_id, "⚠️ يرجى إرسال الإشعار كـ (صورة) حصراً:")
        bot.register_next_step_handler(msg, get_payment_screenshot)
        return
    photo_id = message.photo[-1].file_id
    pack = user_orders[chat_id]['pack']
    player_id = user_orders[chat_id]['player_id']
    price = user_orders[chat_id]['price']
    bot.send_message(chat_id, "⏳ جاري مراجعة طلبك وإشعار الحوالة من قبل الإدارة...")
    admin_markup = InlineKeyboardMarkup()
    admin_markup.row(InlineKeyboardButton("✅ قبول وتمرير تلقائي للطلب", callback_data=f"adm_accept_{chat_id}"), InlineKeyboardButton("❌ رفض الطلب", callback_data=f"adm_reject_{chat_id}"))
    admin_text = f"🚨 **طلب شحن جديد يا محمد**\n\n👤 العميل: `{chat_id}`\n📦 الباقة: {pack} شدة\n💰 القيمة: {price}\n🆔 معرف اللاعب: `{player_id}`"
    bot.send_photo(ADMIN_CHAT_ID, photo_id, caption=admin_text, reply_markup=admin_markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def handle_admin_decision(call):
    data_parts = call.data.split('_')
    action = data_parts[1]
    client_chat_id = int(data_parts[2])
    if client_chat_id not in user_orders: return
    pack = user_orders[client_chat_id].get('pack')
    player_id = user_orders[client_chat_id].get('player_id')
    if action == "accept":
        api_url = "https://nemer-card.com"
        headers = {"Authorization": f"Bearer {NEMER_CARD_TOKEN}", "Content-Type": "application/json", "Accept": "application/json"}
        payload = {"product_id": PRODUCT_IDS.get(pack), "player_id": player_id, "quantity": 1}
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                bot.edit_message_caption("✅ تم قبول الطلب وتمريره لمتجر نمر كارد بنجاح.", call.message.chat.id, call.message.message_id)
                bot.send_message(client_chat_id, f"🎉 تم تأكيد الحوالة! وجاري شحن {pack} شدة لحسابك (ID: {player_id}) تلقائياً. شكراً لتعاملك معنا!")
            else:
                bot.send_message(ADMIN_CHAT_ID, f"⚠️ خطأ من سيرفر المتجر رقم {response.status_code}: {response.text}")
        except Exception as e:
            bot.send_message(ADMIN_CHAT_ID, f"❌ فشل الاتصال بالمتجر بسبب: {e}")
    elif action == "reject":
        bot.edit_message_caption("❌ تم رفض هذا الطلب وإرسال التنبيه للمستخدم.", call.message.chat.id, call.message.message_id)
        bot.send_message(client_chat_id, "❌ نعتذر منك، لقد تم رفض طلب الشحن الخاص بك. يرجى التأكد من صحة بيانات الحوالة أو التواصل مع الدعم الفني.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()

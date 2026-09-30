import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# سيرفر وهمي لتشغيل البوت مجاناً على Render وتخطي نظامهم الجديد
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive"
def run(): app.run(host='0.0.0.0', port=8080)

# ===== إعدادات البوت والبيانات الأساسية المستخرجة لبوت محمد =====
BOT_TOKEN = "8980983661:AAGkuCbXphFg-XXpwpXcw52GTQahgQBi3nM"
ADMIN_CHAT_ID = 8890068169  # معرف حساب محمد لتصله إشعارات الحوالات

NEMER_CARD_TOKEN = "eB-x5a-OlQgfmb_p5E2Ggp--mitrxjFSDgKuZO-cl"

PRICES = {"60": "180 ل.س", "325": "800 ل.س", "660": "1600 ل.س", "1800": "4000 ل.س"}
PRODUCT_IDS = {"60": "60", "325": "325", "660": "660", "1800": "1800"}

bot = telebot.TeleBot(BOT_TOKEN)
user_orders = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_orders[chat_id] = {}
    text = "أهلاً بك في متجر توب ون ستور لشحن شدات ببجي في سوريا فِنا\n\nأسعار شحن الشدات الحالية:\n"
    for pack, price in PRICES.items(): text += f"🔹 {pack} شدة = {price}\n"
    text += "\nالرجاء اختيار الباقة المطلوبة لبدء الشحن:"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💎 1800 شدة", callback_data="buy_1800"))
    markup.row(InlineKeyboardButton("💎 60 شدة", callback_data="buy_60"))
    markup.row(InlineKeyboardButton("💎 325 شدة", callback_data="buy_325"))
    markup.row(InlineKeyboardButton("💎 660 شدة", callback_data="buy_660"))
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_pack_selection(call):
    chat_id = call.message.chat.id
    selected_pack = call.data.split('_')[1]
    user_orders[chat_id]['pack'] = selected_pack
    user_orders[chat_id]['price'] = PRICES[selected_pack]
    msg = bot.send_message(chat_id, "🎯 يرجى كتابة الـ ID الخاص بك في لعبة ببجي بدقة:")
    bot.register_next_step_handler(msg, get_player_id)

def get_player_id(message):
    chat_id = message.chat.id
    user_orders[chat_id]['player_id'] = message.text
    price = user_orders[chat_id]['price']
    text = f"💰 السعر المطلوب لتحويله هو: {price}\n\nالرجاء إرسال إشعار الحوالة كـ (صورة واضحة) هنا في البوت:"
    msg = bot.send_message(chat_id, text)
    bot.register_next_step_handler(msg, get_payment_screenshot)

def get_payment_screenshot(message):
    chat_id = message.chat.id
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
            if response.status_code in:
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

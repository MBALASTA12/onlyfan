from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ContextTypes, MessageHandler, filters
import os
from flask import Flask, request, jsonify, redirect
import requests
import logging
from threading import Thread

# Replace this with your PayPal LIVE business email
PAYPAL_EMAIL = "sb-jvljd40101210@business.example.com"  # <-- UPDATE THIS
PAYPAL_IPN_URL = "https://onlyfan-6cc5a61b58dd.herokuapp.com/ipn"

models = [
    {
        "name": "Agustina Alexia",
        "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/Profile.PNG",
        "price": 20.00,
        "channel_link": "https://t.me/+k2pqjOfYlBA3YTA9",
        "description": """
Hey babe 😘 It’s Agustina Alexia.

I’ve got something special just for you – my exclusive private channel where I share only the most intimate and exclusive content.

If you want to see photos and videos you won’t find anywhere else, then this is your chance to get up close and personal with me. 💋
This is a private space for my true fans, where I get to share everything – raw, real, and totally uncensored.

Trust me, you don’t want to miss this.
So, are you ready for a closer connection?
Hit that subscribe button and get instant access to all the content waiting for you. 🔥

🔞 18+ ONLY | No reposting | Respect is a must
"""
    },
    {
        "name": "Pia",
        "photo": "https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/profile.jpg",
        "price": 20.00,
        "channel_link": "https://t.me/+PiaPrivateChannel",
        "description": "👠 Glamour shots • 🎥 Weekly video drops • ✨ VIP fan-only livestreams"
    },
]



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

bot = Bot(token=os.environ["BOT_API_TOKEN"])

# Temp storage for user subscriptions (in-memory)
user_subscriptions = {}

@app.route("/ipn", methods=["POST"])
def ipn():
    ipn_data = request.form.to_dict()
    verification_url = "https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_xclick..."  # LIVE endpoint
    verification_data = {
        "cmd": "_notify-validate",
        **ipn_data
    }
    response = requests.post(verification_url, data=verification_data)
    
    if response.text == "VERIFIED":
        logger.info(f"Payment VERIFIED: {ipn_data}")

        # Expecting custom format: "<user_id>:<model_name>"
        custom_data = ipn_data.get("custom", "")
        if ":" in custom_data:
            user_id_str, model_name = custom_data.split(":", 1)
            try:
                user_id = int(user_id_str.strip())
            except ValueError:
                logger.error("Invalid user ID format.")
                return jsonify({"message": "Invalid user ID format."})
        else:
            logger.error("Custom data missing or invalid format.")
            return jsonify({"message": "Missing or invalid custom data."})

        # Find the model info
        selected_model = next((m for m in models if m["name"].lower() == model_name.strip().lower()), None)
        if selected_model:
            try:
                message = (
                    f"Hi babe! 💖 Your payment was successful!\n\n"
                    f"Here’s your exclusive access to *{selected_model['name']}*'s private channel:\n"
                    f"{selected_model['channel_link']}\n\n"
                    f"Enjoy the content – and welcome to the private side. 🔥"
                )
                bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")

                # Store for success redirect
                user_subscriptions[user_id] = selected_model["name"]

            except Exception as e:
                logger.error(f"Error sending message to user: {e}")
        else:
            logger.error(f"Model not found: {model_name}")

        return jsonify({"message": "Payment verified and processed."})
    else:
        logger.error(f"Payment verification FAILED: {ipn_data}")
        return jsonify({"message": "Payment verification failed."})



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    # Handle /start success (after redirect from browser)
    if args and args[0] == "success":
        user_id = update.effective_user.id
        model_name = user_subscriptions.get(user_id)

        if model_name:
            selected_model = next((m for m in models if m["name"].lower() == model_name.lower()), None)
            if selected_model:
                await update.message.reply_text(
                    f"✅ Payment successful!\n\n"
                    f"Here’s your exclusive access to *{selected_model['name']}*’s private channel:\n"
                    f"{selected_model['channel_link']}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("✅ Payment successful, but model info not found.")
        else:
            await update.message.reply_text(
                "✅ Payment confirmed, but no subscription record found.\n"
                "If you didn’t receive the link, please message us."
            )
        # Optionally clear after use
        user_subscriptions.pop(user_id, None)
        return

    # Default: show available models
    for model in models:
        button = InlineKeyboardButton(
            text=f"Subscribe to {model['name']}",
            callback_data=f"subscribe_{model['name']}"
        )
        keyboard = [[button]]
        try:
            await update.message.reply_photo(
                photo=model['photo'],
                caption=f"{model['name']}\n\n{model['description']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error sending model message: {e}")

    # At the end of your function after showing models:
reply_markup = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("💬 Contact Support")],
        [KeyboardButton("💸 Earn Money")]
    ],
    resize_keyboard=True
)

await update.message.reply_text(
    "Choose an option below 👇",
    reply_markup=reply_markup
)


async def contact_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Need help? Just message @OnlyFansSupportTeam and we’ll take care of you. 💁‍♂️")

async def earn_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can earn by sharing your referral link!\nUse /referral to get your unique invite. 💰")




@app.route("/success", methods=["GET"])
def payment_success():
    return '''
        <html>
            <head>
                <title>Payment Successful</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        margin-top: 50px; 
                        background-color: #f4f4f9;
                        color: #333;
                    }
                    h2 {
                        font-size: 32px;
                        color: #4CAF50;
                    }
                    p.instruction {
                        font-size: 24px;
                        font-weight: bold;
                        color: #333;
                    }
                    a.button {
                        display: inline-block;
                        padding: 15px 25px;
                        font-size: 18px;
                        color: white;
                        background-color: #4CAF50;
                        border-radius: 8px;
                        text-decoration: none;
                        margin-top: 30px;
                    }
                    .arrow {
                        font-size: 40px;
                        color: #4CAF50;
                        margin-top: 30px;
                    }
                    .arrow-container {
                        margin-top: 20px;
                    }
                    .note {
                        font-size: 20px;
                        color: #777;
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <h2>✅ Payment Successful!</h2>
                <p>Click below to return to Telegram:</p>
                <p class="instruction">Please make sure to click or tap the button to access your exclusive content before closing this page!</p>
                
                <div class="arrow-container">
                    <span class="arrow">⬇️</span>
                </div>
                
                <a class="button" href="tg://resolve?domain=OnlyFanAgencyBot&start=success">Open Telegram</a>
                
                <p class="note">If you do not tap the button, you may miss the exclusive content.</p>
            </body>
        </html>
    '''



async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    model_name = query.data.split("_")[1]  # Extract model name from callback data
    user_id = query.from_user.id

    # Find the model data (including price) for the selected model
    selected_model = next((model for model in models if model["name"] == model_name), None)
    if selected_model:
        model_price = selected_model["price"]
    else:
        model_price = 1.00  # Default price if model not found (can be updated)

    # Create the PayPal payment link with dynamic pricing
    payment_url = (
    f"https://www.sandbox.paypal.com/cgi-bin/webscr"
    f"?cmd=_xclick&business={PAYPAL_EMAIL}"
    f"&item_name=Subscription+to+{model_name}"
    f"&amount={model_price:.2f}&currency_code=USD"
    f"&notify_url={PAYPAL_IPN_URL}"
    f"&custom={user_id}:{model_name}"
    f"&return=https://onlyfan-6cc5a61b58dd.herokuapp.com/success"
)

    # Create an inline button that links directly to the PayPal payment page
    payment_button = InlineKeyboardButton(text=f"Pay {model_price:.2f} USD", url=payment_url)
    keyboard = InlineKeyboardMarkup([[payment_button]])

    try:
        message = f"You've subscribed to {model_name}!\n\nClick below to proceed with payment."

        # Check if the message contains text or caption and edit accordingly
        if query.message.text:
            await query.edit_message_text(text=message, reply_markup=keyboard)
        elif query.message.caption:
            await query.edit_message_caption(caption=message, reply_markup=keyboard)
        else:
            # Fallback message if neither text nor caption exists
            await query.message.reply_text(message, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error editing message: {e}")


def start_telegram_bot():
    application = Application.builder().token(os.environ["BOT_API_TOKEN"]).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💬 Contact Support$"), contact_support))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^💸 Earn Money$"), earn_money))
    application.run_polling()

def main():
    port = int(os.environ.get("PORT", 5000))
    thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': port})
    thread.start()
    start_telegram_bot()

if __name__ == '__main__':
    main()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import os
from flask import Flask, request, jsonify
import requests
import logging
from threading import Thread

# List of model photos (local file paths) and names
models = [
    {"name": "Agustina Alexia", "photo": r"https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/Profile.PNG"},
    {"name": "Pia", "photo": r"https://raw.githubusercontent.com/MBALASTA12/onlyfan/main/photo/profile.jpg"},
    # Add more models here with their respective file paths
]

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Flask
app = Flask(__name__)

# PayPal IPN URL (this will be set to the Heroku app's URL)
PAYPAL_IPN_URL = "https://onlyfan-6cc5a61b58dd.herokuapp.com/ipn"  # Change this with your Heroku URL

# PayPal IPN endpoint to verify payment
@app.route("/ipn", methods=["POST"])
def ipn():
    ipn_data = request.form.to_dict()

    # You need to send the received IPN message to PayPal for verification
    verification_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"
    verification_data = {
        "cmd": "_notify-validate",
        **ipn_data
    }
    response = requests.post(verification_url, data=verification_data)

    if response.text == "VERIFIED":
        # Payment verified, process the subscription
        logger.info("Payment verified")
        # Handle subscription logic (e.g., activate subscription, update user record, etc.)
        return jsonify({"message": "Payment verified and processed."})
    else:
        logger.error("Payment verification failed")
        return jsonify({"message": "Payment verification failed."})

# Set up the Telegram bot
async def start(update: Update, context: CallbackContext) -> None:
    # Prepare buttons for each model
    for model in models:
        # Add an inline button for each model to subscribe
        button = InlineKeyboardButton(
            text=f"Subscribe to {model['name']}",
            callback_data=f"subscribe_{model['name']}"
        )
        
        # Wrap the button in a list to match the expected structure
        keyboard = [[button]]  # Correct structure for InlineKeyboardMarkup
        
        # Send each model's photo with the subscribe button and caption
        try:
            await update.message.reply_photo(
                photo=model['photo'],
                caption=f"{model['name']}",  # Include the model's name in the caption
                reply_markup=InlineKeyboardMarkup(keyboard)  # Inline button for each model
            )
        except FileNotFoundError:
            await update.message.reply_text(f"Sorry, the image for {model['name']} could not be found.")

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Handle the subscription logic based on the button pressed
    if query.data.startswith("subscribe_"):
        model_name = query.data.split('_')[1]
        await query.edit_message_text(text=f"You've subscribed to {model_name}!")
        # Add additional subscription logic (e.g., database update, payment, etc.)

def start_telegram_bot():
    # Set up the bot with your token
    application = Application.builder().token("7848323018:AAHxtPX3huG4_4ZuNQamUvp7IIrY135bPaw").build()

    # Add command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Add callback handler for button presses
    application.add_handler(CallbackQueryHandler(button))

    # Start the bot
    application.run_polling()

def main():
    # Start the Flask server (on a separate thread)
    thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000})
    thread.start()

    # Start the Telegram bot
    start_telegram_bot()

if __name__ == '__main__':
    main()

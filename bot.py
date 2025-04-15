from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import os

# List of model photos (local file paths) and names
models = [
    {"name": "Agustina Alexia", "photo": r"D:\Project\OnlyfansBot\photo\Profile.png"},
    {"name": "Pia", "photo": r"D:\Project\OnlyfansBot\photo\profile.jpg"},
    # Add more models here with their respective file paths
]

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
            with open(model['photo'], 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
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

def main() -> None:
    # Set up the bot with your token
    application = Application.builder().token("7848323018:AAHxtPX3huG4_4ZuNQamUvp7IIrY135bPaw").build()
    
    # Add command handler for /start
    application.add_handler(CommandHandler("start", start))
    
    # Add callback handler for button presses
    application.add_handler(CallbackQueryHandler(button))
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()

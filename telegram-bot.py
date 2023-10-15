import telegram
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import threading
import time
from generate_image import generate_image  # Assuming this is your image generation script

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')


# Function to send the .jpg file
async def send_image(update, context):
    # Determine the chat ID
    if update.message:
        chat_id = update.message.chat_id
    else:
        chat_id = update.callback_query.message.chat_id

    # Create the InlineKeyboardButton for the START button
    start_button = InlineKeyboardButton("START", callback_data='start')
    # Create the InlineKeyboardMarkup with the START button
    keyboard = InlineKeyboardMarkup([[start_button]])

    try:
        with open("parking_lots.jpg", "rb") as image_file:
            # Send the photo along with the START button
            await context.bot.send_photo(chat_id=chat_id, photo=image_file, reply_markup=keyboard)
    except FileNotFoundError:
        await context.bot.send_message(chat_id=chat_id, text="The image file is not available.", reply_markup=keyboard)

# Function to schedule the code every two minutes
def schedule_code():
    while True:
        generate_image()  # Generate the .jpg file
        time.sleep(60)  # Sleep for 2 minutes before generating again

# Define the callback query handler for the START button
async def start_button_callback(update, context):
    await send_image(update, context)  # Call send_image when the START button is pressed

# Create an Application instance
app = Application.builder().token(BOT_TOKEN).build()

# Add your handlers to the application
app.add_handler(CommandHandler('start', send_image))
app.add_handler(CallbackQueryHandler(start_button_callback, pattern='^start$'))

# Create a separate thread for scheduling the code
schedule_thread = threading.Thread(target=schedule_code)
schedule_thread.daemon = True
schedule_thread.start()

if __name__ == '__main__':
    # Start the bot
    app.run_polling(1.0)
    # Run the scheduling thread in the background
    schedule_thread.join()

import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from generate_image import generate_image  # Assuming this is your image generation script
import asyncio
import websockets
import nest_asyncio
import threading

load_dotenv()
nest_asyncio.apply()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_TOKEN = os.getenv("ACCESS_TOKEN_SECRET")

async def listen_for_updates():
    async with websockets.connect(f'ws://localhost:3000?token={API_TOKEN}') as ws:
        while True:
            generate_image(await ws.recv())  # Generate the .jpg file

def start_socket_listener():
    asyncio.run(listen_for_updates())

# Create a new thread for the socket listener
socket_listener_thread = threading.Thread(target=start_socket_listener)

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



# Define the callback query handler for the START button
async def start_button_callback(update, context):
    await send_image(update, context)  # Call send_image when the START button is pressed

# Create an Application instance
app = Application.builder().token(BOT_TOKEN).build()

# Add your handlers to the application
app.add_handler(CommandHandler('start', send_image))
app.add_handler(CallbackQueryHandler(start_button_callback, pattern='^start$'))




if __name__ == '__main__':
    # Start the socket listener thread
    socket_listener_thread.start()

    # Start the bot polling in the main thread's event loop
    app.run_polling(1.0)

    # Optionally, wait for the socket listener thread to finish
    socket_listener_thread.join()

    
    
  
   
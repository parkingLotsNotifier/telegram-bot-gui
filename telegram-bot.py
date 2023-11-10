import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from ui import generate_image  # Assuming this is your image generation script
import asyncio
import websockets
import nest_asyncio
import threading

load_dotenv()
nest_asyncio.apply()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_TOKEN = os.getenv("ACCESS_TOKEN_SECRET")
USERS_IDS = os.getenv("ALLOWED_USER_IDS", "")

# Get the allowed user IDs from the environment variable and convert them to a set of integers
ALLOWED_USER_IDS = set(int(uid) for uid in USERS_IDS.split(","))


# Define a function to check if a user is allowed to use the bot
def is_user_allowed(user_id):
    return user_id in ALLOWED_USER_IDS


async def listen_for_updates():
    async with websockets.connect(f"ws://localhost:3000?token={API_TOKEN}") as ws:
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
    start_button = InlineKeyboardButton("START", callback_data="start")
    # Create the InlineKeyboardMarkup with the START button
    keyboard = InlineKeyboardMarkup([[start_button]])

    try:
        with open("background_image.png", "rb") as image_file:
            # Send the photo along with the START button
            await context.bot.send_photo(
                chat_id=chat_id, photo=image_file, reply_markup=keyboard
            )
    except FileNotFoundError:
        await context.bot.send_message(
            chat_id=chat_id,
            text="The image file is not available.",
            reply_markup=keyboard,
        )


# Define a function that replies only if the user is allowed
async def start(update, context):
    print("someone enteterd start")
    user_id = update.effective_user.id
    chat_id = (
        update.effective_chat.id
        if update.effective_chat
        else update.callback_query.message.chat_id
    )
    if not is_user_allowed(user_id):
        # If it's a callback query, you need to send a message instead of using reply_text
        if update.callback_query:
            await context.bot.send_message(
                chat_id=chat_id, text="You are not authorized to use this bot."
            )
        return
    # The user is allowed; implement your bot's functionality here
    await send_image(update, context)


# Define the callback query handler for the START button
async def start_button_callback(update, context):
    await start(update, context)  # Call send_image when the START button is pressed


# Define a function for handling the /start command
async def start_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    if not is_user_allowed(user_id):
        await context.bot.send_message(
            chat_id=chat_id, text="You are not authorized to use this bot."
        )
        return
    await start(update, context)


# Create an Application instance
app = Application.builder().token(BOT_TOKEN).build()

# Add your handlers to the application
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(start_button_callback, pattern="^start$"))


if __name__ == "__main__":
    # Start the socket listener thread
    socket_listener_thread.start()

    # Start the bot polling in the main thread's event loop
    app.run_polling(1.0)

    # Optionally, wait for the socket listener thread to finish
    socket_listener_thread.join()

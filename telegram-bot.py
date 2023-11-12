import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from ui import generate_image  # Assuming this is your image generation script
import asyncio
import websockets
import nest_asyncio
import threading
from datetime import datetime
import json
import logging

# for email sending
import smtplib
from email.mime.text import MIMEText


load_dotenv()
nest_asyncio.apply()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_TOKEN = os.getenv("ACCESS_TOKEN_SECRET")
USERS_IDS = os.getenv("ALLOWED_USER_IDS", "")

# Get the allowed user IDs from the environment variable and convert them to a set of integers
ALLOWED_USER_IDS = set(int(uid) for uid in USERS_IDS.split(","))


# Configure the logging module for user access logs
user_access_logger = logging.getLogger("user_access")
user_access_logger.setLevel(logging.INFO)

user_access_handler = logging.FileHandler("users_access.log")
user_access_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
user_access_handler.setFormatter(user_access_formatter)

user_access_logger.addHandler(user_access_handler)

# Configure the logging for the telegram library
telegram_logger = logging.getLogger("telegram")
telegram_logger.setLevel(logging.INFO)

# Create a handler that captures all messages from the telegram logger
telegram_handler = logging.FileHandler("telegram_logs.log")
telegram_handler.setLevel(logging.INFO)  # Adjust the level as needed

# Create a formatter that includes the entire log message
telegram_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
telegram_handler.setFormatter(telegram_formatter)

# Add the handler to the logger
telegram_logger.addHandler(telegram_handler)


# ---------------------------------------------------------------------------


# Define a function to check if a user is allowed to use the bot
def is_user_allowed(user_id):
    return user_id in ALLOWED_USER_IDS


async def listen_for_updates():
    async with websockets.connect(f"ws://localhost:3000?token={API_TOKEN}") as ws:
        while True:
            generate_image(await ws.recv())  # Generate the .jpg file


def start_socket_listener():
    asyncio.run(listen_for_updates())


# Thread Safety:

# Be cautious when using asyncio.run in a threaded environment.
# In your start_socket_listener function, you're calling asyncio.run(listen_for_updates()) in a separate thread.
# This could potentially lead to issues because asyncio.run is intended to be used in the main thread.
# Consider using asyncio.create_task instead.


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
    start_button = InlineKeyboardButton("▶️ START", callback_data="start")
    # Create the InlineKeyboardButton for the FEEDBACK button
    feedback_button = InlineKeyboardButton("📣 FEEDBACK", callback_data="feedback")
    # Create the InlineKeyboardMarkup with both buttons
    keyboard = InlineKeyboardMarkup([[start_button, feedback_button]])

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


user_logs = []


# Function to add user logs
def add_user_log(update, context, isUserAllowed):
    user = update.effective_user
    log = {}
    log["first_name"] = user.first_name
    log["last_name"] = user.last_name if hasattr(user, "last_name") else None
    log["username"] = user.username if hasattr(user, "username") else None
    log["user_id"] = get_attribute(update, context, "user_id")
    log["permission"] = isUserAllowed

    log_message = json.dumps(log, indent=2)  # Add indent for readability

    # Log the information to the user access logger
    if isUserAllowed:
        user_access_logger.info(log_message)
    else:
        user_access_logger.warning(log_message)


def get_attribute(update, context, attribute_name):
    # Retrieves the specified attribute (e.g., user_id, chat_id) from the update object, handling different cases.

    # Dictionary to map attribute names to corresponding retrieval methods
    attribute_mapping = {
        "user_id": lambda u: u.effective_user.id
        if u.effective_user
        else u.callback_query.from_user.id,
        "chat_id": lambda u: u.effective_chat.id
        if u.effective_chat
        else u.callback_query.message.chat_id,
        # Add more attributes as needed
    }

    retrieval_method = attribute_mapping.get(attribute_name)

    if retrieval_method:
        return retrieval_method(update)
    else:
        # Handle the case where the attribute_name is not supported
        raise ValueError(f"Unsupported attribute: {attribute_name}")


# Define a function that replies only if the user is allowed
async def start(update, context):
    # get user_id and chat_id
    user_id = get_attribute(update, context, "user_id")
    chat_id = get_attribute(update, context, "chat_id")
    isUserAllowed = is_user_allowed(user_id)

    add_user_log(update, context, isUserAllowed)
    print(f"{user_id}, Pressed: /start")

    if isUserAllowed:
        # The user is allowed; implement your bot's functionality here
        await send_image(update, context)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="You are not authorized to use this bot.",
        )


# Define the callback query handler for the START button
async def start_button_callback(update, context):
    await start(update, context)  # Call send_image when the START button is pressed


# Define a function for handling the /start command
async def start_command(update, context):
    await start(update, context)


# Define a function to handle the /feedback command
async def feedback_command(update, context):
    user_id = get_attribute(update, context, "user_id")
    chat_id = get_attribute(update, context, "chat_id")

    if not is_user_allowed(user_id):
        await context.bot.send_message(
            chat_id=chat_id, text="You are not authorized to use this bot."
        )
        return

    # Send a message prompting the user for feedback
    await context.bot.send_message(
        chat_id=chat_id,
        text="Please type your feedback below. Your message will be sent to the admin.",
    )

    # Set a new state to track feedback messages
    context.user_data["feedback_in_progress"] = True


# Define a function to handle the /feedback button
async def feedback_button(update, context):
    await feedback_command(update, context)


# Define a function to handle user feedback
async def handle_feedback(update, context):
    user_id = get_attribute(update, context, "user_id")
    chat_id = get_attribute(update, context, "chat_id")

    # Check if the user is allowed and if feedback is in progress
    if not is_user_allowed(user_id) or not context.user_data.get(
        "feedback_in_progress"
    ):
        return

    # Get the user's feedback message
    feedback_message = update.message.text

    # You can implement the logic to send the feedback to your email here
    # For simplicity, let's print it to the console
    print(f"Received feedback from user {user_id}: {feedback_message}")

    # Send feedback via email (modify this section)
    send_feedback_email(feedback_message, user_id)

    # Provide a confirmation to the user
    await context.bot.send_message(
        chat_id=chat_id, text="Thank you for your feedback! It has been submitted."
    )

    # Reset the feedback state
    del context.user_data["feedback_in_progress"]


# Function to send feedback via email
def send_feedback_email(feedback_message, userID):
    # Replace the following variables with your email and SMTP server details
    sender_email = os.getenv("GMAIL_USERNAME")
    app_password = os.getenv("TELEGRAM_BOT_GMAIL_PASSWORD")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Get recipient emails from environment variables
    recipient_emails = [
        # os.getenv("MAIL_DEST1"), # Co-founder E-mail
        os.getenv("MAIL_DEST2"),
    ]

    # Create the email message
    message_body = f"Feedback from Telegram Bot\n\nUser ID: {userID}\nFeedback Message:\n{feedback_message}"
    message = MIMEText(message_body)
    message["Subject"] = "Feedback from Telegram Bot"
    message["From"] = sender_email
    message["To"] = ", ".join(recipient_emails)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_emails, message.as_string())


# Create an Application instance
app = Application.builder().token(BOT_TOKEN).build()

# Add your handlers to the application
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CallbackQueryHandler(start_button_callback, pattern="^start$"))
# Add the handler for the /feedback command
app.add_handler(CommandHandler("feedback", feedback_command))
# Add a new handler for the /feedback button
app.add_handler(CallbackQueryHandler(feedback_button, pattern="^feedback$"))
# Add a message handler to handle feedback messages
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_feedback))


if __name__ == "__main__":
    # Start the socket listener thread
    socket_listener_thread.start()

    # Start the bot polling in the main thread's event loop
    app.run_polling(1.0)

    # Optionally, wait for the socket listener thread to finish
    socket_listener_thread.join()

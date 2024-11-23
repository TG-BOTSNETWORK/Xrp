#!/usr/bin/python3

import json
import requests
import time
from pyromod import Client, Message
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from rich import print
from pyrogram.errors import BadMsgNotification
import asyncio

# Initialize Pyrogram client
bot = Client(
    "xrpminerbot",
    api_id=22363963,
    api_hash="5c096f7e8fd4c38c035d53dc5a85d768",
    bot_token="7261854045:AAGv8_bgcspRJ_LAMJjwaX_AAe8dSGMXEo4"
)

# User data storage
user_data = {}


# Mining logic
def start_mining_with_cookies(cookies, xrp_address, destination_tag):
    session = requests.Session()
    session.headers.update({
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Host': 'faucetearner.org',
        'Origin': 'https://faucetearner.org',
    })
    session.cookies.update(cookies)

    try:
        # Mining process
        r2 = session.post('https://faucetearner.org/api.php?act=faucet', data={})

        if 'congratulations' in r2.text.lower():
            return {"success": ["Mining successful!"], "failed": []}
        elif 'you have already' in r2.text.lower():
            return {"success": [], "failed": ["Mining failed: Already claimed."]}
        else:
            return {"success": [], "failed": ["Mining failed: Unknown error."]}
    except Exception as e:
        return {"error": f"Exception occurred: {e}"}


# Start command handler
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    chat_id = message.chat.id

    # Check if user already started
    if chat_id in user_data:
        await message.reply_text(
            f"Welcome back, {message.from_user.first_name}! 👋\n\n"
            "You already provided your cookies. Type /reset to start over or /mine to begin mining."
        )
    else:
        # New user: start asking for cookies and details
        user_data[chat_id] = {}
        await message.reply_text(
            "Welcome to the **XRP Miner Bot**! 🚀\n\n"
            "Please send your **cookies** in JSON format (e.g., `{\"cookie_name\": \"cookie_value\"}`).\n\n"
            "_Note: You can copy cookies from your browser using tools like EditThisCookie._"
        )
        user_data[chat_id]["cookies"] = json.loads(await client.listen(chat_id))
        await message.reply_text("Great! Now send your XRP address:")
        user_data[chat_id]["xrp_address"] = await client.listen(chat_id)
        await message.reply_text("Finally, send your destination tag:")
        user_data[chat_id]["destination_tag"] = await client.listen(chat_id)

        await message.reply_text(
            "Thank you! Your details have been saved. You can now start mining by typing /mine."
        )


# Mine command handler
@bot.on_message(filters.command("mine") & filters.private)
async def mine(client, message):
    chat_id = message.chat.id

    if chat_id not in user_data or not all(key in user_data[chat_id] for key in ["cookies", "xrp_address", "destination_tag"]):
        await message.reply_text("You need to provide cookies, XRP address, and destination tag first. Type /start to begin.")
        return

    user = user_data[chat_id]
    cookies = user["cookies"]
    xrp_address = user["xrp_address"]
    destination_tag = user["destination_tag"]

    await message.reply_text("Mining started! Please wait...")
    result = start_mining_with_cookies(cookies, xrp_address, destination_tag)

    if "error" in result:
        await message.reply_text(f"Mining failed: {result['error']}")
    else:
        success = "\n".join(result["success"])
        failed = "\n".join(result["failed"])
        await message.reply_text(
            f"Mining Summary:\n\n"
            f"Success: {success}\n"
            f"Failed: {failed}"
        )


# Reset command handler
@bot.on_message(filters.command("reset") & filters.private)
async def reset(client, message):
    chat_id = message.chat.id

    if chat_id in user_data:
        del user_data[chat_id]
        await message.reply_text("Your data has been reset. Type /start to set up again.")
    else:
        await message.reply_text("No data found to reset. Type /start to set up.")


async def main():
    try:
        await bot.start()
        print("Bot Started!") 
    except BadMsgNotification as e:
        print(f"Error: {e}. Retrying...")
        await asyncio.sleep(2)  # Short delay before retry
        await bot.start()

bot.run(main)

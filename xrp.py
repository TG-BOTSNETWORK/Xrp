#!/usr/bin/python3

import json
import requests
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from rich.console import Console
from rich.panel import Panel
from rich import print
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from random import choice


proxy_list = []
user_data = {}

# Initialize Pyrogram client
bot = Client(
    "xrpminerbot",
    api_id=22363963,
    api_hash="5c096f7e8fd4c38c035d53dc5a85d768",
    bot_token="7261854045:AAGv8_bgcspRJ_LAMJjwaX_AAe8dSGMXEo4"
)


# Helper function to update proxies
def update_proxies():
    global proxy_list
    with open('proxy.json') as file:
        datahttp = json.load(file)
    for dhttp in datahttp:
        response = requests.get(dhttp)
        proxies = response.text.split('\n')
        proxy_list = [proxy.strip() for proxy in proxies if proxy.strip()]


# Helper function to select a random proxy
def get_proxy():
    if proxy_list:
        proxy = choice(proxy_list).replace('http://', '')
        return {"http": f"http://{proxy}"}
    return None


# Mining logic
def start_mining(email, password, xrp_address, destination_tag):
    session = requests.Session()
    session.headers.update({
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Host': 'faucetearner.org',
        'Origin': 'https://faucetearner.org',
        'User-Agent': UserAgent().random
    })

    # Login to the platform
    response = session.post("https://faucetearner.org/api.php?act=login", json={
        "email": email,
        "password": password
    }, proxies=get_proxy())

    if response.status_code == 200:
        cookies = response.cookies.get_dict()
        if cookies.get("login"):
            success = []
            failed = []

            # Mining process
            r = session.get('https://faucetearner.org/faucet.php', proxies=get_proxy())
            r.headers.update({
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Host': 'faucetearner.org',
                'Origin': 'https://faucetearner.org',
            })
            r2 = session.post('https://faucetearner.org/api.php?act=faucet', data={}, proxies=get_proxy())

            if 'congratulations' in r2.text.lower():
                success.append("Mining successful!")
            elif 'you have already' in r2.text.lower():
                failed.append("Mining failed: Already claimed.")
            else:
                failed.append("Mining failed: Unknown error.")

            return {"success": success, "failed": failed}
        else:
            return {"error": "Login failed: Invalid credentials"}
    else:
        return {"error": "Failed to connect to the platform"}


@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "Welcome to XRP Miner Bot! Please send your email to login:"
    )
    user_data[message.chat.id] = {}


@bot.on_message(filters.private & ~filters.command("start"))
async def collect_user_data(client, message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        await message.reply("Please start with /start.")
        return

    user = user_data[chat_id]

    if "email" not in user:
        user["email"] = message.text
        await message.reply("Great! Now send your password:")
    elif "password" not in user:
        user["password"] = message.text
        await message.reply("Now send your XRP address:")
    elif "xrp_address" not in user:
        user["xrp_address"] = message.text
        await message.reply("Finally, send your destination tag:")
    elif "destination_tag" not in user:
        user["destination_tag"] = message.text
        await message.reply(
            f"Here are your details:\n\n"
            f"Email: {user['email']}\n"
            f"Password: {user['password'][:3]}**{user['password'][-2:]}\n"
            f"XRP Address: {user['xrp_address']}\n"
            f"Destination Tag: {user['destination_tag']}\n\n"
            "Click the button below to start mining!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✨ Start Mine ✨", callback_data="start_mining")]
            ])
        )


@bot.on_callback_query(filters.regex("start_mining"))
async def start_mining_handler(client, callback_query):
    chat_id = callback_query.message.chat.id
    if chat_id not in user_data:
        await callback_query.answer("No user data found. Please restart with /start.")
        return

    user = user_data[chat_id]
    email = user["email"]
    password = user["password"]
    xrp_address = user["xrp_address"]
    destination_tag = user["destination_tag"]

    await callback_query.answer("Mining started! Please wait...")
    result = start_mining(email, password, xrp_address, destination_tag)

    if "error" in result:
        await bot.send_message(chat_id, f"Mining failed: {result['error']}")
    else:
        success = "\n".join(result["success"])
        failed = "\n".join(result["failed"])
        await bot.send_message(
            chat_id,
            f"Mining Summary:\n\n"
            f"Success: {success}\n"
            f"Failed: {failed}"
        )


if __name__ == "__main__":
    update_proxies()
    bot.run()

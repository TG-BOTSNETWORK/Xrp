import json
import requests
import asyncio
from pyromod import Client, Message
from pyrogram import filters
from pyrogram.errors import BadMsgNotification

bot = Client(
    "xrpminerbot",
    api_id=22363963,
    api_hash="5c096f7e8fd4c38c035d53dc5a85d768",
    bot_token="7261854045:AAGv8_bgcspRJ_LAMJjwaX_AAe8dSGMXEo4"
)

user_data = {}

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
        r2 = session.post('https://faucetearner.org/api.php?act=faucet', data={})
        if 'congratulations' in r2.text.lower():
            return {"success": ["Mining successful!"], "failed": []}
        elif 'you have already' in r2.text.lower():
            return {"success": [], "failed": ["Mining failed: Already claimed."]}
        else:
            return {"success": [], "failed": ["Mining failed: Unknown error."]}
    except Exception as e:
        return {"error": f"Exception occurred: {e}"}

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    chat_id = message.chat.id
    if chat_id in user_data:
        await message.reply_text(
            f"Welcome back, {message.from_user.first_name}!\n"
            "You already provided your cookies. Type /reset to start over or /mine to begin mining."
        )
    else:
        user_data[chat_id] = {}
        await message.reply_text("Send your cookies in JSON format (e.g., `{\"cookie_name\": \"cookie_value\"}`).")
        cookies = await client.listen(chat_id)
        user_data[chat_id]["cookies"] = json.loads(cookies.text)
        await message.reply_text("Now send your XRP address:")
        xrp_address = await client.listen(chat_id)
        user_data[chat_id]["xrp_address"] = xrp_address.text
        await message.reply_text("Finally, send your destination tag:")
        destination_tag = await client.listen(chat_id)
        user_data[chat_id]["destination_tag"] = destination_tag.text
        await message.reply_text("Details saved. You can start mining with /mine.")

@bot.on_message(filters.command("mine") & filters.private)
async def mine(client, message):
    chat_id = message.chat.id
    if chat_id not in user_data or not all(key in user_data[chat_id] for key in ["cookies", "xrp_address", "destination_tag"]):
        await message.reply_text("Provide cookies, XRP address, and destination tag first. Type /start to begin.")
        return

    user = user_data[chat_id]
    result = start_mining_with_cookies(user["cookies"], user["xrp_address"], user["destination_tag"])

    if "error" in result:
        await message.reply_text(f"Mining failed: {result['error']}")
    else:
        success = "\n".join(result["success"]) if result["success"] else "None"
        failed = "\n".join(result["failed"]) if result["failed"] else "None"
        await message.reply_text(f"Mining Summary:\nSuccess: {success}\nFailed: {failed}")

@bot.on_message(filters.command("reset") & filters.private)
async def reset(client, message):
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
        await message.reply_text("Your data has been reset. Type /start to set up again.")
    else:
        await message.reply_text("No data to reset. Type /start to set up.")

if __name__ == "__main__":
    asyncio.run(bot.start())

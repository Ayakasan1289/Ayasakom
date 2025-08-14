import asyncio
import random

async def charge_resp(result):
    try:
        if (
            '{"status":"SUCCESS",' in result or
            '"status":"success"' in result
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
        response = f"{str(e)} ❌"
        return response

async def authenticate(json, pk, session):
    try:
        three_d_secure_2_source = json["next_action"]["use_stripe_sdk"][
            "three_d_secure_2_source"
        ]
        url = "https://api.stripe.com/v1/3ds2/authenticate"
        data = {
            "source": three_d_secure_2_source,
            "browser": '{"fingerprintAttempted":false,"fingerprintData":null,"challengeWindowSize":null,"threeDSCompInd":"Y","browserJavaEnabled":false,"browserJavascriptEnabled":true,"browserLanguage":"en-US","browserColorDepth":"24","browserScreenHeight":"864","browserScreenWidth":"1536","browserTZ":"-360","browserUserAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
            + str(random.randint(115, 116))
            + '.0.0.0 Safari/537.36"}',
            "one_click_authn_device_support[hosted]": "false",
            "one_click_authn_device_support[same_origin_frame]": "false",
            "one_click_authn_device_support[spc_eligible]": "true",
            "one_click_authn_device_support[webauthn_eligible]": "true",
            "one_click_authn_device_support[publickey_credentials_get_allowed]": "true",
            "key": pk,
        }
        result = await session.post(url, data=data)

        try:
            return result.json()["state"]
        except:
            try:
                return result.json()["error"]["message"]
            except:
                return result.text

    except Exception as e:
        return e


async def one_click_3d_check(json, session):
    try:
        three_ds_method_url = json["next_action"]["use_stripe_sdk"][
            "three_ds_method_url"
        ]
        await session.get(three_ds_method_url)
    except Exception:
        pass

# app/services/utils/phone_utils.py
import phonenumbers

def normalize_phone(number: str, region: str = "IN") -> str:
    try:
        parsed = phonenumbers.parse(number, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    return number


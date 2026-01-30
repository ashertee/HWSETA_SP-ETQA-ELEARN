#from snoop import snoop
import datetime
import re


VALIDATIONS = {
    "gender": {
        0: "female",
        1: "female",
        2: "female",
        3: "female",
        4: "female",
        5: "male",
        6: "male",
        7: "male",
        8: "male",
        9: "male",
    },
    "citizenship": {
        0: "sa",
        1: "other",
    },
    "length": 13,
}

# -------------------------------------------------
# SA ID VALIDATIONS
# -------------------------------------------------

def check_length(id_num):
    return len(id_num) == VALIDATIONS["length"]


def check_gender(id_num):
    try:
        return VALIDATIONS["gender"][int(id_num[6])]
    except Exception:
        return "Invalid gender"


def check_citizenship(id_num):
    try:
        return VALIDATIONS["citizenship"][int(id_num[10])]
    except Exception:
        return "Invalid citizenship status"


def check_date(id_num):
    id_num = str(id_num)

    year = int(id_num[:2])
    month = int(id_num[2:4])
    day = int(id_num[4:6])

    prefix = 2000 if year <= 20 else 1900

    try:
        return datetime.date(prefix + year, month, day)
    except Exception:
        return "Invalid birth date"


def check_control_bit(id_num):
    id_num = str(id_num)

    odds = [int(id_num[i]) for i in range(0, 12, 2)]
    evens = [id_num[i] for i in range(1, 12, 2)]

    sum_odds = sum(odds)
    even_number = int("".join(evens)) * 2
    sum_evens = sum(map(int, str(even_number)))

    total = sum_odds + sum_evens
    control = (10 - (total % 10)) % 10

    return "Passable" if control == int(id_num[-1]) else "Invalid control bit"


def said_check(id_num):
    """Full SA ID validation (Odoo safe)"""

    if not check_length(id_num):
        return {"valid": False, "reason": "Invalid length"}

    birth_date = check_date(id_num)
    if isinstance(birth_date, str):
        return {"valid": False, "reason": birth_date}

    gender = check_gender(id_num)
    if gender == "Invalid gender":
        return {"valid": False, "reason": gender}

    citizenship = check_citizenship(id_num)
    if citizenship == "Invalid citizenship status":
        return {"valid": False, "reason": citizenship}

    control = check_control_bit(id_num)
    if control != "Passable":
        return {"valid": False, "reason": control}

    return {
        "valid": True,
        "birth_date": birth_date,
        "gender": gender,
        "citizenship": citizenship,
    }


# -------------------------------------------------
# STRING VALIDATIONS
# -------------------------------------------------

def name_checker(name):
    return bool(re.fullmatch(r"[A-Za-z]+", name))


def email_checker(email):
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))


def mobile_num_checker(contact_num):
    return bool(re.fullmatch(r"((\+27|27)|0)(72|82|73|83|74|84|79|61)\d{7}", contact_num))


def phone_num_checker(contact_num):
    return bool(re.fullmatch(r"((\+27|27)|0)(11|12|10)\d{7}", contact_num))


def passport_checker(passport):
    return bool(re.fullmatch(r"(?!^0+$)[A-Za-z0-9]{3,20}", passport))


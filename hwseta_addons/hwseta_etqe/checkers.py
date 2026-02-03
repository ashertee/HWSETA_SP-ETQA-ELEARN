import datetime
import re

# --------------------------------------------------------- DEBUG LOGGER ---------------------------------------------------------

def dbg(msg):
    pass


# --------------------------------------------------------- ID CHECKER ---------------------------------------------------------

VALIDATIONS = {
    "gender": {
        0: "female", 1: "female", 2: "female", 3: "female", 4: "female",
        5: "male", 6: "male", 7: "male", 8: "male", 9: "male",
    },
    "citizenship": {
        0: "sa",
        1: "other",
    },
    "length": 13,
}


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
    try:
        year_prefix = "20" if int(id_num[0:2]) < 20 else "19"
        date_string = f"{year_prefix}{id_num[0:2]}-{id_num[2:4]}-{id_num[4:6]}"
        return datetime.datetime.strptime(date_string, "%Y-%m-%d")
    except Exception:
        return "Invalid birth date"


def check_control_bit(id_num):
    id_num = str(id_num)
    evens = [id_num[i] for i in range(len(id_num)) if (i + 1) % 2 == 0]
    odds = [id_num[i] for i in range(len(id_num)) if (i + 1) % 2 != 0][:-1]

    sum_odds = sum(int(o) for o in odds)
    even_number = int("".join(evens)) * 2
    even_sum = sum(int(x) for x in str(even_number))

    total = sum_odds + even_sum
    control = 10 - int(str(total)[-1])
    return "Passable" if control == int(id_num[-1]) else "Invalid control bit"


def old_said_check(id_num):
    return [
        check_citizenship(id_num),
        check_date(id_num),
        check_gender(id_num),
    ]


def said_check(id_num):
    result = {
        "valid": True,
        "citizenship": check_citizenship(id_num),
        "gender": check_gender(id_num),
        "date": check_date(id_num),
    }

    if not check_length(id_num):
        result["valid"] = False

    if "Invalid" in str(result["citizenship"]) or "Invalid" in str(result["gender"]) or "Invalid" in str(result["date"]):
        result["valid"] = False

    return result


# --------------------------------------------------------- NAME CHECKER ---------------------------------------------------------

def name_checker(name):
    return "Passable" if re.fullmatch(r"[A-Za-z]+", name or "") else "Invalid first/last name"


# --------------------------------------------------------- EMAIL CHECKER ---------------------------------------------------------

def email_checker(email):
    return "Passable" if re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email or "") else "Invalid email"


# --------------------------------------------------------- MOBILE NUMBER CHECKER ---------------------------------------------------------

def mobile_num_checker(contact_num):
    return (
        "Passable"
        if re.fullmatch(r"((\+27|27)|0)(72|82|73|83|74|84|79|61)\d{7}", contact_num or "")
        else "Invalid Mobile Number"
    )


# --------------------------------------------------------- PHONE NUMBER CHECKER ---------------------------------------------------------

def phone_num_checker(contact_num):
    return (
        "Passable"
        if re.fullmatch(r"((\+27|27)|0)(11|12|10)\d{7}", contact_num or "")
        else "Invalid Phone Number"
    )


# --------------------------------------------------------- PASSPORT CHECKER ---------------------------------------------------------

def check_passport_number(passport):
    return (
        "Passable"
        if re.fullmatch(r"(?!^0+$)[a-zA-Z0-9]{3,20}", passport or "")
        else "Invalid passport"
    )


passport_check = check_passport_number
from pickle import FALSE
from telnetlib import STATUS
# from compose.cli.errors import UserError
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime
import logging
import datetime
from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError, UserError
import re
from datetime import date
from odoo import api, fields, models, _
import datetime
from odoo.exceptions import ValidationError

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(msg):
        pass


def validate_certain_chars(chars, value, field_name):
    def split(word):
        return [char for char in word]

    sublist = split(value)
    complist = split(chars)
    dbg(sublist)

    for s in sublist:
        dbg(s)
        if s not in complist:
            return False, "Please only use " + str(chars) + " in " + str(field_name)
    return True, "Fine"


# person title


def validate_person_title(value):
    def split(word):
        return [char for char in word]

    sublist = split(value)
    complist = split("ABCDEFGHIJKLMNOPQRTSUVWXYZ`'")
    dbg(sublist)

    for s in sublist:
        dbg(s)
        if s not in complist:
            return (
                False,
                "Please only use  ABCDEFGHIJKLMNOPQRTSUVWXYZ`' in Person Title",
            )
    return True, "Fine"


### non nqf interventions

# non nqf credit
def validate_non_nqf_credit(value):
    try:
        int(value)
        return True, "Fine"
    except:
        return False, "NON NQF Credit can only contain whole numbers"


# learning programme type id
def validate_learning_programme_type_id(value):
    try:
        int(value)
        return True, "Fine"
    except:
        return False, "Learning Programme Type ID can only contain whole numbers"


# non nqf interv code
def validate_non_nqf_intervention_code(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-",
        value,
        "NON NQF Intervention Code",
    )


# non nqf interv name
def validate_non_nqf_intervention_name(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-",
        value,
        "NON NQF Intervention Name",
    )


### seta qualifications stu

# certificate number


def validate_certificate_number(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-", value, "Certificate Number"
    )


# practical_provider


def validate_practical_provider(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-", value, "Practical Provider"
    )


# cumulative_spend


def validate_cumulative_spend(value):
    try:
        int(value)
    except:
        return False, "Cumulative Spend must be a number"
    return True, "Fine"


# assessor_registration_number


def validate_assessor_registration_number(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-",
        value,
        "Assessor Registration Number",
    )


# practical_etqe_id


def validate_practical_etqe_id(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-", value, "Practical ETQE ID"
    )


### seta qualifications stu end


### employer stu validations

# employer_registration_number


def validate_employer_registration_number(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-",
        value,
        "Employer Registration Number",
    )


# employer_site_no


def validate_employer_site_number(value):
    return validate_certain_chars(
        "ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-", value, "Site Number"
    )


# phone


def validate_phone_fax_number(value):
    try:
        int(value)
        if len(value) == 10:
            return True, "Fine"
        else:
            pass
    except Exception as e:
        pass
    return False, "Please enter valid phone/fax/mobile number"


# fax

# mobile

# website


def validate_website(value):

    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        # domain...
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if re.match(regex, "http://www.example.com"):
        return True, "Fine"  # True
    else:
        return False, "Please enter valid website address"


# name

## use nageens

# employer_trading_name

## use nageens

# person_home_address_1

## use nageens

# person_home_address_2

## use nageens

# person_home_address_3

## use nageens

# person_home_suburb

## use nageens

# person_home_city

## use nageens

# person_home_province_code

## use nageens

# person_home_zip

## use nageens

# person_postal_address_1

## use nageens

# person_postal_address_2

## use nageens

# person_postal_address_3

## use nageens

# person_postal_suburb

# person_postal_city

## use nageens

# person_postal_province_code

# person_postal_zip


### employer stu validations

# email


def validate_email(email):

    regex = re.compile(
        r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
    )
    try:
        if re.fullmatch(regex, email):
            return True, "Fine"
        else:
            return False, "Invalid Email Address"
    except TypeError:
        pass


# national id


def validate_national_id_passport(value):
    def split(word):
        return [char for char in word]

    sublist = split(value)
    complist = split("ABCDEFGHIJKLMNOPQRTSUVWXYZ-1234567890@_")
    dbg(sublist)

    for s in sublist:
        dbg(s)
        if s not in complist:
            return (
                False,
                "Please only use  ABCDEFGHIJKLMNOPQRTSUVWXYZ-1234567890@_ in Passport Number",
            )
    return True, "Fine"


def validate_national_id(value):
    if re.match(
        "(^[0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])([0-9]{4})([0-1]{1})([0-9]{2})",
        value,
    ):
        return True, "Fine"
    else:
        return False, "please enter a valid id number"


# designation class
def validate_person_alternate_id(value):
    # dbg(value)
    if not re.match(r"(?=.*[ ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@_`])", value):
        return (
            False,
            "%s should contain  ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@_" % value,
        )
    else:
        return True, "Fine"


def validate_designation_registration_number(value):
    # ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-
    dbg(value)
    dbg(re.match(r"(?=.*[ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\\:._-])", value))
    if not re.match(
        r"(?=.*[ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\\:._-])", value
    ):
        return (
            False,
            "%s should contain  ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-"
            % value,
        )
    else:
        return True, "Fine"


"""
placeholder funcs for designation testing by dyl
"""


def id_check(value):
    if re.match(
        "(^[0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])([0-9]{4})([0-1]{1})([0-9]{2})",
        value,
    ):
        return True, "Fine"
    else:
        return False, "please enter a valid id number"


def validate_names_1(value):

    boolman = bool(re.findall(r"[^\w\s`'-]|\d", value))
    if not boolman:
        return True, "Fine"
    else:
        return False, "No special characters allowed in Name fields"


def validate_names_2(value):

    check1 = r"[^A-Za-z-1234567890`' -]"
    check2 = r"\bUNKNOWN\b|\bAS\b|\bABOVE\b|\bSOOS\b|\bBO\b|\bDELETE\b|\bN[/]A\b|\bNA\b|\bU\b|\bNONE\b|\bGEEN\b|\b0\b|\bTEST\b|\bONTBREEK\b|\bNIL\b|^[-]$|[–]"

    if bool(re.findall(check2, value)) == True:
        return False
    if bool(re.findall(check1, value)) == True:
        return False
    else:
        return True


def validate_letters_special(value):
    if not re.match(
        r"(?=.*[ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890#&\(\)\/:\._`])", value
    ):
        raise ValidationError(
            _(
                "%(value)s should contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890#&()/\:._`"
            ),
            params={"value": value},
        )


def validate_sixteen(value):
    sixteen_years = datetime.datetime.now() - datetime.timedelta(days=16 * 365)
    if value > sixteen_years.date():
        raise ValidationError(
            _("%(value)s - person is younger than 16!"),
            params={"value": value},
        )


def validate_eighteen_fifty(value):
    if datetime.date(1850, 1, 1) > value:
        raise ValidationError(
            _("%(value)s is less than 1850!"),
            params={"value": value},
        )


def nineteen_hundred(value):
    if datetime.date(1900, 1, 1) > value:
        raise ValidationError(
            _("%(value)s is less than 1900!"),
            params={"value": value},
        )


# def validate_names(value):
# 	if not re.match(r"(?=.*[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRTSUVWXYZ`'\-])",value):
# 		raise ValidationError(
# 			_("%(value)s should contain ABCDEFGHIJKLMNOPQRTSUVWXYZ`'\-"),
# 			params={'value': value},
# 		)


def validate_na_geen(value):
    illegal_partials = [
        "UNKNOWN",
        " AS",
        "ABOVE ",
        " SOOS",
        "BO ",
        " DELETE ",
        " ONTBREEK ",
    ]

    illegal_full = ["N / A", "NA", "U", "NONE", "GEEN", "0", "TEST", "NIL", "-", "–"]

    def split(word):
        return [char for char in word]

    # check fulls
    if value.upper() in illegal_full:
        return (
            False,
            "Please do not use any of the following values: " + str(illegal_full),
        )
    # check partials
    sublist = split(value)
    for s in sublist:
        if s.upper() in illegal_partials:
            return (
                False,
                "Please do not use any of the following in your values:"
                + str(illegal_partials),
            )
    return True, "Fine"


def validate_postcode(value):
    if not re.match(r"\d{4}", value):
        return False, "Please enter valid postcode"
    return True, "Fine"


def validate_phone_fax(value):
    try:
        int(value)
        return True, "Fine"
    except:
        return False, "Please enter a valid number"
    # if not re.match(r"(?<!\d)\d{20,20}(?!\d)", value):
    #    raise ValidationError(
    #            _('%(value)s is not a valid postcode'),
    #            params={'value': value},
    #        )


def validate_uppercase_letters_numbers_special(value):
    p = re.compile("[A-Z_0-9]")
    a = p.match(value)
    if a == None:
        raise ValidationError(
            _(
                "%(value)s is not valid - only use the characters: ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._- "
            ),
            params={"value": value},
        )


def validateID(IDNum):
    def informinvalid():
        raise ValidationError(
            _("%(IDNum)s is not an ID"),
            params={"IDNum": IDNum},
        )

    xv = True
    if len(IDNum) != 13:
        informinvalid()
    if int(IDNum[10]) > 1:
        informinvalid()
    d = -1
    a = 0
    for i in range(0, 6):
        a += int(IDNum[2 * i])
    b = 0
    for i in range(0, 6):
        b = b * 10 + int(IDNum[2 * i + 1])
        b *= 2
    c = 0
    while b > 0:
        c += b % 10
        b = b / 10
        c += a
        d = 10 - (c % 10)
        if d == 10:
            d = 0
        xc = str(d) == IDNum[12]
    if xv == False:
        informinvalid()


def validate_even(value):
    value = int(value)
    if value % 2 != 0:
        raise ValidationError(
            _("%(value)s is not an even number"),
            params={"value": value},
        )


def validate_provider_start_end_date(value):
    if Provider.provider_start_date == Provider.provider_end_date or 1 == 1:
        raise ValidationError(
            # _('%(value)s is time travel'),
            _("%(Provider.provider_start_date)s is time travel"),
            params={"value": value},
        )


# QMR lookups

# Learnership Enrolment validations
##Tested working


def provider_etqe_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


def learnership_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


def assessor_etqe_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


# def non_nqf_interv_etqe_id(value):

#     if bool(re.match(r" +", value)) == True:
#         return False
#     if bool(re.match(r"^\d{0,10}$", value)) == False:
#         return False
#     else:
#         return True


def assessor_registration_number(value):

    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._-]", value)) == False:
        return True
    else:
        return False


##Tested working
def certificate_number(value):

    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._-]", value)) == False:
        return True
    else:
        return False


##Tested working
def cumulative_spend(value):

    if bool(re.findall(r"[^1234567890]", value)) == False:
        return True
    else:
        return False


def enrolment_status_date(value):
    today = date.today()
    value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
    # value = value.date()
    # print(value)
    if value > today:
        return False
    elif value < datetime.date(1900, 1, 1):
        return False
    else:
        return True, "Fine"


# def most_recent_registration_date(value):
#     today = date.today()
#     value = datetime.datetime.strptime(value,'%Y-%m-%d').date()
#     #value = value.date()
#     print(value)
#     if value > today:
#         return False
#     elif value < datetime.date(1900,1,1):
#         return False
#     else:
#         return True,"Fine"

##############################
##** Provider validations **##
##############################

# Provider validations
##Tested working
def provider_code(value):

    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._-]", value)) == False:
        return True
    else:
        return False


##Tested working
def provider_name(value):

    check1 = r"[^A-Za-z-1234567890@#&+() /\\:._,'`-]"
    check2 = r"\bUNKNOWN\b|\bAS\b|\bABOVE\b|\bSOOS\b|\bBO\b|\bDELETE\b|\bN[/]A\b|\bNA\b|\bU\b|\bNONE\b|\bGEEN\b|\b0\b|\bTEST\b|\bONTBREEK\b|\bNIL\b|^[-]$|[–]"

    if bool(re.findall(check2, value)) == True:
        return False
    if bool(re.findall(check1, value)) == True:
        return False
    else:
        return True


def SIC_code(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._,'`]", value)) == False:
        return True
    else:
        return False


##Tested working
def provider_phone_number(value):

    if bool(re.findall(r"[^\d ()/-]", value)) == False:
        return True
    else:
        return False


##Tested working
def provider_fax_number(value):

    if bool(re.findall(r"[^\d ()/-]", value)) == False:
        return True
    else:
        return False


##Tested working
def provider_contact_cell_number(value):

    if bool(re.findall(r"[^\d ()-]", value)) == False:
        return True
    else:
        return False


##Tested working
def provider_sars_number(value):

    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._-]", value)) == False:
        return True
    else:
        return False


##Tested working
def provider_contact_email_address(value):

    if (
        bool(
            re.fullmatch(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", value)
        )
        == True
    ):
        return True
    else:
        return False


##Tested working
def provider_accreditation_num(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._]", value)) == False:
        return True
    else:
        return False


def province_code(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._,'`]", value)) == False:
        return True
    else:
        return False


def country_code(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._,'`]", value)) == False:
        return True
    else:
        return False


def provider_website_address(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&() /\\:._,'`]", value)) == False:
        return True
    else:
        return False


def SDL_no(value):
    if bool(re.match(r"\b[L][0-9]{9}\b|\b[N][0-9]{9}\b", value)) == True:
        return True
    else:
        return False


##Tested working


def start_date(startdate):
    today = date.today()

    startdate = datetime.datetime.strptime(startdate, "%Y-%m-%d %H:%M:%S").date()
    if startdate > today:
        return False
    if startdate < datetime.date(1900, 1, 1):
        return False
    else:
        return True


def end_date(enddate):
    today = date.today()
    enddate = datetime.datetime.strptime(enddate, "%Y-%m-%d %H:%M:%S").date()
    if enddate > today:
        return False
    if enddate < datetime.date(1900, 1, 1):
        return False
    else:
        return True


def provider_address(value):

    check1 = r"[^A-Za-z-1234567890#&() /\\:._,'`-]"
    check2 = r"\bUNKNOWN\b|\bAS\b|\bABOVE\b|\bSOOS\b|\bBO\b|\bDELETE\b|\bN[/]A\b|\bNA\b|\bU\b|\bNONE\b|\bGEEN\b|\b0\b|\bTEST\b|\bONTBREEK\b|\bNIL\b|\bZZZ\b|\bXXX\b|\bADDRES\b|^[-]$|[–]"

    if bool(re.findall(check2, value)) == True:
        return False
    if bool(re.findall(check1, value)) == True:
        return False
    else:
        return True


def provider_address_code(value):
    if bool(re.match(r"\b\d{4}\b", value)) == True:
        return True
    else:
        return False


def etqe_decision_number(value):

    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._]", value)) == True:
        return False
    else:
        return True


def provider_contact_name(value):

    check1 = r"[^A-Za-z-1234567890#&() '`]"
    check2 = r"\bUNKNOWN\b|\bAS\b|\bABOVE\b|\bSOOS\b|\bBO\b|\bDELETE\b|\bN[/]A\b|\bNA\b|\bU\b|\bNONE\b|\bGEEN\b|\b0\b|\bTEST\b|\bONTBREEK\b|\bNIL\b|^[-]$|[–]"

    if bool(re.findall(check2, value)) == True:
        return False
    if bool(re.findall(check1, value)) == True:
        return False
    else:
        return True


def longitude_seconds(value):
    if (
        bool(
            re.match(
                r"^(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])\.([0-9]){3}$", value
            )
        )
        == False
    ):
        return False
    else:
        return True


def longitude_minutes(value):
    if bool(re.match(r"^(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])$", value)) == False:
        return False
    else:
        return True


def longitude_degree(value):
    ## has to run more checks in the provider file
    if bool(re.match(r"^(1[6-9]|2[0-9]|3[0-3])$", value)) == False:
        return False
    else:
        return True


def latitude_seconds(value):

    if (
        bool(
            re.match(
                r"^(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])\.([0-9]){3}$", value
            )
        )
        == True
    ):
        return True
    else:
        return False


def latitude_minutes(value):
    if bool(re.match(r"^(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])$", value)) == False:
        return False
    else:
        return True


def latitude_degree(value):
    ## has to run more checks in the provider file
    if bool(re.match(r"^-(2[2-9]|3[0-5])$", value)) == False:
        return False
    else:
        return True


########################################
##**Internship placement validations**##
########################################


def qualification_achievement_date(value):
    today = date.today()
    value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
    if value > today:
        return False
    elif value < datetime.date(1900, 1, 1):
        return False
    else:
        return True


## Start_Date same validation in provider

## end_Date same validation in provider

## SDL_no same validation in provider


def site_no(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._]", value)) == True:
        return False
    else:
        return True


##Provider_code same validation in provider

##Cumulative_Spend same validation in Learnership Enrolment

#########################################
##**  Person Designation validations **##
#########################################


def designation_registration_number(value):

    check1 = r"[^A-Za-z-1234567890#&() /\\:._,'`-]"
    check2 = r"\bUNKNOWN\b|\bAS\b|\bABOVE\b|\bSOOS\b|\bBO\b|\bDELETE\b|\bN[/]A\b|\bNA\b|\bU\b|\bNONE\b|\bGEEN\b|\b0\b|\bTEST\b|\bONTBREEK\b|\bNIL\b|^[-]$|[–]"

    if bool(re.findall(check2, value)) == True:
        return False
    if bool(re.findall(check1, value)) == True:
        return False
    else:
        return True


## Start_Date same validation in provider


def designation_end_date(enddate):
    enddate = datetime.datetime.strptime(enddate, "%Y-%m-%d").date()
    if enddate < datetime.date(1900, 1, 1):
        return False
    else:
        return True


##Provider_Code same validation in provider


def date_stamp(value):
    today = date.today()
    value = datetime.datetime.strptime(value, "%Y-%m-%d").date()
    if value > today:
        return False
    if value < datetime.date(1900, 1, 1):
        return False
    else:
        return True


def etqe_decision_number_designation(value):

    if bool(re.search(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,20}$", value)) == False:
        return False
    else:
        return True


def designation_etqe_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


def chk_national_id(value):
    dbg(value)
    dbg(re.match(
                r"(^[0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])([0-9]{4})([0-1]{1})([0-9]{2})",
                value,
            ))
    if (
        bool(
            re.match(
                r"(^[0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])([0-9]{4})([0-1]{1})([0-9]{2})",
                value,
            )
        )
        == True
    ):
        dbg('if bool')
        return True
    else:
        return False


def chk_person_alternate_id(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@_]", value)) == True:
        return False
    else:
        return True


#########################################
##** Non NQF Intervention Enrolments **##
#########################################


def non_nqf_intervention_code(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._]", value)) == True:
        return False
    else:
        return True


def assessor_registration_number(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._]", value)) == True:
        return False
    else:
        return True


def qualification_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


def learnership_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


def non_nqf_intervention_etqe_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


def learnership_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


############################
##** Partner validations**##
############################


def person_alternate_id(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@_]", value)) == True:
        return False
    else:
        return True


def work_phone(value):

    if bool(re.findall(r"[^\d ()/-]", value)) == False:
        return True
    else:
        return False


##############################
##** Employer validations **##
##############################

# SDL No same as in provider
# main SDL No as in provider


def employer_registration_number(value):

    if bool(re.findall(r"[^A-Za-z-1234567890@#&+() /\\:._-]", value)) == False:
        return True
    else:
        return False


##Tested working
def employer_name(value):
    dbg(value)

    check1 = r"[^A-Za-z-1234567890@#&+() /\\:._,'`-]"
    check2 = r"\bUNKNOWN\b|\bAS\b|\bABOVE\b|\bSOOS\b|\bBO\b|\bDELETE\b|\bN[/]A\b|\bNA\b|\bU\b|\bNONE\b|\bGEEN\b|\b0\b|\bTEST\b|\bONTBREEK\b|\bNIL\b|^[-]$|[–]"

    dbg(bool(re.findall(check2, value)) == True)
    if bool(re.findall(check2, value)) == True:
        return False
    dbg(bool(re.findall(check1, value)) == True)
    if bool(re.findall(check1, value)) == True:
        return False
    else:
        return True


def unit_standard_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,10}$", value)) == False:
        return False
    else:
        return True


def part_of_id(value):

    if bool(re.match(r" +", value)) == True:
        return False
    if bool(re.match(r"^\d{0,2}$", value)) == False:
        return False
    else:
        return True


def employer_approval_end_date(value):
    # today = date.today()
    value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
    # value = value.date()
    # print(value)
    if value < datetime.date(1900, 1, 1):
        return False
    else:
        return True, "Fine"


def non_nqf_credit(value):
    if (
        bool(re.match(r"^([1-9]|[1-9][0-9]|[0-3][0-9][0-9]|4[0-7][0-9]|480)$", value))
        == False
    ):
        return False
    else:
        return True


def non_nqf_intervention_name(value):
    if bool(re.findall(r"[^A-Za-z-1234567890@#&() /\\:._,'`]", value)) == False:
        return True
    else:
        return False


def designation_end_date(value):
    today = date.today()
    value = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
    # value = value.date()
    # print(value)
    if value < datetime.date(1900, 1, 1):
        return False
    else:
        return True, "Fine"


#### PARTNER ###########


def person_name(value):
    dbg('person_name:::::',value)

    check1 = r"[^A-Za-z-'` ]"
    check2 = r"\bUNKNOWN\b|\bAS\b|\bABOVE\b|\bSOOS\b|\bBO\b|\bDELETE\b|\bN[/]A\b|\bNA\b|\bU\b|\bNONE\b|\bGEEN\b|\b0\b|\bTEST\b|\bONTBREEK\b|\bNIL\b|^[-]$|[–]"

    if bool(re.findall(check2, value)) == True:
        dbg('if bool(re.findall(check2, value)) == True:')
        return False
    if bool(re.findall(check1, value)) == True:
        dbg('if bool(re.findall(check1, value)) == True: vds')
        return False
    else:
        return True


def birth_date(startdate):
    startdate = startdate.strip()
    today = date.today()

    try:
        startdate = datetime.datetime.strptime(startdate, "%Y-%m-%d %H:%M:%S").date()
    except:
        startdate = datetime.datetime.strptime(startdate, "%Y-%m-%d").date()
    age = (
        today.year
        - startdate.year
        - ((today.month, today.day) < (startdate.month, startdate.day))
    )
    print(age)
    if age < 16:
        return False
    if startdate < datetime.date(1850, 1, 1):
        return False
    else:
        return True


def popi_act_status_date(startdate):
    today = date.today()

    startdate = datetime.datetime.strptime(startdate, "%Y-%m-%d %H:%M:%S").date()
    if startdate > today:
        return False
    else:
        return True


def person_previous_alternate_id_type_id(value):

    if bool(re.findall(r"[^\d]", value)) == False:
        return True
    else:
        return False


# def last_school_year(value):
#     # dbg(value)
#     if  re.match(r"^(19|20)\d{2}$",value):
#         return True
#     else:
#         return False
def last_school_year(value):
    try:
        value = datetime.datetime.strptime(value, "%Y").date()
        return True
    except:
        return False


"""
this is the provider file aka seta.provider aka (nlrd) aka 100(setmis)
"""
# Tested and Working
def check_provider_name(provider_name):
    broken = False
    valid = []
    msg = ""
    if provider_name == "False":
        msg = "provider_name field may not be left blank\n"
        broken = True
    if provider_name:
        valid = provider_name(provider_name)
    if valid == False:
        broken = True
        msg = "provider_name should ony contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


# Tested and Working
def check_provider_code(provider_code):
    broken = False
    valid = []
    msg = ""

    if provider_code == "False":
        msg = "provider_code field may not be left blank\n"
        broken = True
    if provider_code:
        valid = provider_code(provider_code)
    if valid == False:
        broken = True
        msg = "provider_code should ony contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


# Tested and Working
def check_provider_postal_address_1(provider_postal_address_1):
    broken = False
    valid = []
    msg = ""
    if provider_postal_address_1 == "False":
        msg = "provider_postal_address_1 field may not be left blank \n"
        broken = True
    if provider_postal_address_1:
        valid = provider_address(provider_postal_address_1)
    if valid == False:
        broken = True
        msg = "provider_postal_address_1 should ony contain a valid address \n"
    return broken, msg


# Tested and Working
def check_provider_postal_address_2(provider_postal_address_2):
    broken = False
    valid = []
    msg = ""
    if provider_postal_address_2 == "False":
        msg = "provider_postal_address_2 field may not be left blank \n"
        broken = True
    if provider_postal_address_2:
        valid = provider_address(provider_postal_address_2)
    if valid == False:
        broken = True
        msg = "provider_postal_address_2 should ony contain a valid address \n"
    return broken, msg


# Tested and Working
def check_provider_postal_address_3(provider_postal_address_3):
    broken = False
    valid = []
    msg = ""
    if provider_postal_address_3:
        valid = provider_address(provider_postal_address_3)
    if valid == False:
        broken = True
        msg = "provider_postal_address_3 should ony contain a valid address\n"
    return broken, msg


# Tested and Working
def check_provider_postal_address_code(provider_postal_address_code):
    broken = False
    valid = []
    msg = ""
    if provider_postal_address_code == "False":
        msg = "provider_postal_address_code field may not be left blank\n"
        provider_postal_address_code = ""
        broken = True
    if provider_postal_address_code:
        valid = provider_address_code(provider_postal_address_code)
    if valid == False:
        broken = True
        msg = "provider_postal_address_code should ony contain a valid address code\n"
    return broken, msg


# Tested and Working
def check_provider_phone_number(provider_phone_number):
    broken = False
    valid = []
    msg = ""
    if provider_phone_number:
        valid = provider_phone_number(provider_phone_number)
    if valid == False:
        broken = True
        msg = "provider_phone_number should ony contain 1234567890 ()/-\n"
    return broken, msg


# Tested and Working
def check_provider_fax_number(provider_fax_number):
    broken = False
    valid = []
    msg = ""
    if provider_fax_number == "False":
        provider_fax_number = ""
    if provider_fax_number:
        valid = provider_fax_number(provider_fax_number)
    if valid == False:
        broken = True
        msg = "provider_fax_number should ony contain 1234567890 ()/-\n"
    return broken, msg


# Tested and Working
def check_provider_sars_number(provider_sars_number):
    broken = False
    valid = []
    msg = ""
    if provider_sars_number:
        valid = provider_sars_number(provider_sars_number)
    if valid == False:
        broken = True
        msg = "provider_sars_number should ony contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


# Tested and Working
def check_provider_contact_name(provider_contact_name):
    broken = False
    valid = []
    msg = ""
    if provider_contact_name:
        valid = provider_contact_name(provider_contact_name)
    if valid == False:
        broken = True
        msg = "Provider phone name should ony contain a valid contact name\n"
    return broken, msg


# Tested and Working
def check_provider_contact_email_address(provider_contact_email_address):
    broken = False
    valid = []
    msg = ""
    if provider_contact_email_address == "False":
        provider_contact_email_address = ""
    if provider_contact_email_address:
        valid = provider_contact_email_address(provider_contact_email_address)
    if valid == False:
        broken = True
        msg = "Provider contact email address should contain a valid email\n"
    return broken, msg


# Tested and Working
def check_provider_contact_phone_number(provider_contact_phone_number):
    broken = False
    valid = []
    msg = ""
    if provider_contact_phone_number == "False":
        provider_contact_phone_number = ""
    if provider_contact_phone_number:
        valid = provider_phone_number(provider_contact_phone_number)
    if valid == False:
        broken = True
        msg = "Provider contact phone number should ony contain 1234567890 ()/-\n"
    return broken, msg


# Tested and Working
def check_provider_contact_cell_number(provider_contact_cell_number):
    broken = False
    valid = []
    msg = ""
    if provider_contact_cell_number == "False":
        provider_contact_cell_number = ""
    if provider_contact_cell_number:
        valid = provider_contact_cell_number(provider_contact_cell_number)
    if valid == False:
        broken = True
        msg = "Provider phone cell number  should ony contain 1234567890 ()/-\n"
    return broken, msg


# Tested and Working
def check_provider_accreditation_num(provider_accreditation_num):
    broken = False
    valid = []
    msg = ""
    if provider_accreditation_num:
        valid = provider_accreditation_num(provider_accreditation_num)
    if valid == False:
        broken = True
        msg = "Provider Accreditation Num should ony contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


# Tested and Working
def check_provider_physical_address_1(provider_physical_address_1):
    broken = False
    valid = []
    msg = ""
    if provider_physical_address_1 == "False":
        msg = "Provider Physical address 1 Field may not be left blank\n"
        broken = True
    if provider_physical_address_1:
        valid = provider_address(provider_physical_address_1)
    if valid == False:
        broken = True
        msg = "Provider Physical address 1  should ony contain a valid address\n"
    return broken, msg


# Tested and Working
def check_provider_physical_address_2(provider_physical_address_2):
    broken = False
    valid = []
    msg = ""
    if provider_physical_address_2 == "False":
        msg = "Provider Physical address 2 Field may not be left blank\n"
        broken = True
    if provider_physical_address_2:
        valid = provider_address(provider_physical_address_2)
    if valid == False:
        broken = True
        msg = "Provider Physical address 2  should ony contain a valid address\n"
    return broken, msg


# Tested and Working
def check_provider_physical_address_3(provider_physical_address_3):
    broken = False
    valid = []
    msg = ""
    if provider_physical_address_3:
        valid = provider_address(provider_physical_address_3)
    if valid == False:
        broken = True
        msg = "Provider Physical address 3 should ony contain a valid address\n"
    return broken, msg


# Tested and Working
def check_provider_physical_address_code(provider_physical_address_code):
    broken = False
    valid = []
    msg = ""
    if provider_physical_address_code == "False":
        msg = "Provider Physical address code  Field may not be left blank\n"
        provider_physical_address_code = ""
        broken = True
    if provider_physical_address_code:
        valid = provider_address_code(provider_physical_address_code)
    if valid == False:
        broken = True
        msg = (
            "Provider Physical address code  should ony contain a valid address code\n"
        )
    return broken, msg


# Tested and Working
def check_etqe_decision_number(etqe_decision_number):
    broken = False
    valid = []
    msg = ""
    if etqe_decision_number:
        valid = etqe_decision_number(etqe_decision_number)
    if valid == False:
        broken = True
        msg = "Etqe Decision Number should ony contain only ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


# Tested and Working
def check_latitude_degree(latitude_degree):
    broken = False
    valid = []
    msg = ""
    if latitude_degree == "False":
        latitude_degree = ""
    if latitude_degree:
        valid = latitude_degree(latitude_degree)
    if valid == False:
        broken = True
        msg = "Latitude Degree may only contain whole numbers and may not be greater than -22 and may not have a value less than -35\n"
    return broken, msg


# Tested and Working
def check_latitude_minutes(latitude_minutes):
    broken = False
    valid = []
    msg = ""
    if latitude_minutes == "False":
        latitude_minutes = ""
    if latitude_minutes:
        valid = latitude_minutes(latitude_minutes)
    if valid == False:
        broken = True
        msg = "Latitude Minutes may not be greater than 59\n"
    return broken, msg


# Tested and Working
def check_latitude_seconds(latitude_seconds):
    broken = False
    valid = []
    msg = ""
    if latitude_seconds == "False":
        latitude_seconds = ""
    if latitude_seconds:
        valid = latitude_seconds(latitude_seconds)
    if valid == False:
        broken = True
        msg += "Latitude Seconds may only contain 1234567890 and must have a length of exactly 6 (nn.nnn) and may not be greater than 59.999.\n"
    return broken, msg


# Tested and Working
def check_longitude_degree(longitude_degree):
    broken = False
    valid = []
    msg = ""
    if longitude_degree == "False":
        longitude_degree = ""
    if longitude_degree:
        valid = longitude_degree(longitude_degree)
    if valid == False:
        broken = True
        msg = "longitude degree may only contain whole numbers and may not be greater than 33 and may not have a value less than 16\n"
    return broken, msg


# Tested and Working
def check_longitude_minutes(longitude_minutes):
    broken = False
    valid = []
    msg = ""
    if longitude_minutes == "False":
        longitude_minutes = ""
    if longitude_minutes:
        valid = longitude_minutes(longitude_minutes)
    if valid == False:
        broken = True
        msg = "longitude minutes may not be greater than 59\n"
    return broken, msg


# Tested and Working
def check_longitude_seconds(longitude_seconds):
    broken = False
    valid = []
    msg = ""
    if longitude_seconds == "False":
        longitude_seconds = ""
    if longitude_seconds:
        valid = longitude_seconds(longitude_seconds)
    if valid == False:
        broken = True
        msg += "longitude seconds may only contain 1234567890 and must have a length of exactly 6 (nn.nnn) and may not be greater than 59.999.\n"
    return broken, msg


# Tested and Working
def check_provider_website_address(provider_website_address):
    broken = False
    valid = []
    msg = ""
    if provider_website_address:
        valid = provider_website_address(provider_website_address)
    if valid == False:
        broken = True
        msg += "provider website address should be a valid website address\n"
    return broken, msg


# Tested and Working
def check_sdl_no(sdl_no):
    broken = False
    valid = []
    msg = ""
    if sdl_no:
        valid = SDL_no(sdl_no)
    if valid == False:
        broken = True
        msg += "SDL No must start with 'L' followed by 9 digits or 'N' followed by 9 digits\n"
    return broken, msg


# Tested and Working
def check_date_stamp(date_stamp):
    broken = False
    valid = []
    msg = ""
    if date_stamp == "False":
        msg = "Date Stamp Field may not be left blank\n"
        broken = True
    return broken, msg


# Tested and Working
def check_provider_start_date(provider_start_date):
    broken = False
    valid = []
    msg = ""

    try:

        if provider_start_date == "False":
            msg = "Field may not be left blank\n"
            broken = True
            provider_start_date = ""
        if provider_start_date:
            valid = start_date(provider_start_date)
        if valid == False:
            broken = True
            msg = "should contain a valid date and not greater than today's date\n"
    except:
        broken = True
        msg = "Enrolment status date should contain a valid date"

    return broken, msg


# Tested and Working
def check_provider_end_date(provider_end_date):
    broken = False
    valid = []
    msg = ""
    if provider_end_date == "False":
        msg = "provider end date Field may not be left blank\n"
        provider_end_date = ""
    try:
        (datetime.datetime.strptime(provider_end_date, "%Y-%m-%d %H:%M:%S").date())

    except:
        broken = True
        msg = "should contain a valid end date\n"
    return broken, msg


# class SetmisProvider(models.Model):
# 	_name = "setmis.provider"
# 	_rec_name = "Provider_Code"

# 	#Checking


# #Tested and Working
# 	@api.multi
# 	def check_all(self):
# 		msg = ''
# 		broken = False

# 		if self.check_Provider_Code(self.Provider_Code)[0]:
# 			broken = True
# 			msg += self.check_Provider_Code(self.Provider_Code)[1]

# 		if self.check_provider_name(self.provider_name)[0]:
# 			broken = True
# 			msg += self.check_provider_name(self.provider_name)[1]

# 		if self.check_Provider_Postal_Address_1(self.Provider_Postal_Address_1)[0]:
# 			broken = True
# 			msg += self.check_Provider_Postal_Address_1(self.Provider_Postal_Address_1)[1]

# 		if self.check_Provider_Postal_Address_2(self.Provider_Postal_Address_2)[0]:
# 			broken = True
# 			msg += self.check_Provider_Postal_Address_2(self.Provider_Postal_Address_2)[1]

# 		if self.check_Provider_Postal_Address_3(self.Provider_Postal_Address_3)[0]:
# 			broken = True
# 			msg += self.check_Provider_Postal_Address_3(self.Provider_Postal_Address_3)[1]

# 		if self.check_Provider_Postal_Address_Code(self.Provider_Postal_Address_Code)[0]:
# 			broken = True
# 			msg += self.check_Provider_Postal_Address_Code(self.Provider_Postal_Address_Code)[1]

# 		if self.check_provider_phone_number(self.provider_phone_number)[0]:
# 			broken = True
# 			msg += self.check_provider_phone_number(self.provider_phone_number)[1]

# 		if self.check_provider_fax_number(self.provider_fax_number)[0]:
# 			broken = True
# 			msg += self.check_provider_fax_number(self.provider_fax_number)[1]

# 		if self.check_provider_contact_name(self.provider_contact_name)[0]:
# 			broken = True
# 			msg += self.check_provider_contact_name(self.provider_contact_name)[1]

# 		if self.check_provider_contact_email_address(self.provider_contact_email_address)[0]:
# 			broken = True
# 			msg += self.check_provider_contact_email_address(self.provider_contact_email_address)[1]

# 		if self.check_provider_contact_cell_number(self.provider_contact_cell_number)[0]:
# 			broken = True
# 			msg += self.check_provider_contact_cell_number(self.provider_contact_cell_number)[1]

# 		if self.check_provider_accreditation_num(self.provider_accreditation_num)[0]:
# 			broken = True
# 			msg += self.check_provider_accreditation_num(self.provider_accreditation_num)[1]

# 		if self.check_provider_physical_address_1(self.provider_physical_address_1)[0]:
# 			broken = True
# 			msg += self.check_provider_physical_address_1(self.provider_physical_address_1)[1]

# 		if self.check_provider_physical_address_2(self.provider_physical_address_2)[0]:
# 			broken = True
# 			msg += self.check_provider_physical_address_2(self.provider_physical_address_2)[1]

# 		if self.check_provider_physical_address_3(self.provider_physical_address_3)[0]:
# 			broken = True
# 			msg += self.check_provider_physical_address_3(self.provider_physical_address_3)[1]

# 		if self.check_provider_physical_address_code(self.provider_physical_address_code)[0]:
# 			broken = True
# 			msg += self.check_provider_physical_address_code(self.provider_physical_address_code)[1]

# 		if self.check_provider_sars_number(self.provider_sars_number)[0]:
# 			broken = True
# 			msg += self.check_Provider_provider_sars_number(self.provider_sars_number)[1]

# 		if self.check_etqe_decision_number(self.etqe_decision_number)[0]:
# 			broken = True
# 			msg += self.check_etqe_decision_number(self.etqe_decision_number)[1]

# 		if self.check_latitude_degree(self.latitude_degree)[0]:
# 			broken = True
# 			msg += self.check_latitude_degree(self.latitude_degree)[1]

# 		if self.check_latitude_minutes(self.latitude_minutes)[0]:
# 			broken = True
# 			msg += self.check_latitude_minutes(self.latitude_minutes)[1]

# 		if self.check_latitude_seconds(self.latitude_seconds)[0]:
# 			broken = True
# 			msg += self.check_latitude_seconds(self.latitude_seconds)[1]

# 		if self.check_longitude_degree(self.longitude_degree)[0]:
# 			broken = True
# 			msg += self.check_longitude_degree(self.longitude_degree)[1]

# 		if self.check_longitude_minutes(self.longitude_minutes)[0]:
# 			broken = True
# 			msg += self.check_longitude_minutes(self.longitude_minutes)[1]

# 		if self.check_longitude_seconds(self.longitude_seconds)[0]:
# 			broken = True
# 			msg += self.check_longitude_seconds(self.longitude_seconds)[1]

# 		if self.check_provider_website_address(self.provider_website_address)[0]:
# 			broken = True
# 			msg += self.check_provider_website_address(self.provider_website_address)[1]

# 		if self.check_provider_website_address(self.provider_website_address)[0]:
# 			broken = True
# 			msg += self.check_provider_website_address(self.provider_website_address)[1]

# 		if self.check_SDL_No(self.SDL_No)[0]:
# 			broken = True
# 			msg += self.check_SDL_No(self.SDL_No)[1]

# 		if self.check_date_stamp(self.date_stamp)[0]:
# 			broken = True
# 			msg += self.check_date_stamp(self.date_stamp)[1]

# 		if self.check_provider_start_date(self.provider_start_date)[0]:
# 			broken = True
# 			msg += self.check_provider_start_date(self.provider_start_date)[1]

# 		if self.check_provider_end_date(self.provider_end_date)[0]:
# 			broken = True
# 			msg += self.check_provider_end_date(self.provider_end_date)[1]


# 		self.broken = broken
# 		self.msg = msg
# 		#create Report random unique ID
# 		uuidFour = uuid.uuid4().hex
# 		self.Report_ID = uuidFour


# 	broken = fields.Text()
# 	msg = fields.Text()
# 	#checked fields as per SETMIS File
# 	Provider_Code = fields.Char()
# 	#provider_etqe_m2o = fields.Many2one("etqe.id")
# 	# #sic_code_m2o = fields.Many2one("sic.code")
# 	#sic_code_id = fields.Char()  # Many2one('sic.code')
# 	provider_name = fields.Char(size=70)
# 	#provider_type_m2o = fields.Many2one("provider.type.id")
# 	#provider_type_id_id = fields.Char()  # Many2one('provider.type.id')
# 	Provider_Postal_Address_1 = fields.Char(size=50)  # validate_na_geen
# 	Provider_Postal_Address_2 = fields.Char(size=50)
# 	Provider_Postal_Address_3 = fields.Char(size=50)
# 	Provider_Postal_Address_Code = fields.Char(size=4)
# 	provider_phone_number = fields.Char(size=20)
# 	provider_fax_number = fields.Char(size=20)
# 	provider_sars_number = fields.Char(size=20)
# 	provider_contact_name = fields.Char(size=20)
# 	provider_contact_email_address = fields.Char(size=50)
# 	provider_contact_phone_number = fields.Char(size=20)
# 	provider_contact_cell_number = fields.Char(size=20)
# 	provider_accreditation_num = fields.Char(size=20)
# 	provider_physical_address_1 = fields.Char(size=50)
# 	provider_physical_address_2 = fields.Char(size=50)
# 	provider_physical_address_3 = fields.Char(size=50)
# 	provider_physical_address_code = fields.Char(size=4)
# 	etqe_decision_number = fields.Char(size=20)
# 	# provider_class_m2o = fields.Many2one("provider.class.id")
# 	# provider_class_id_id = fields.Char()  # Many2one('provider.class.id')
# 	# provider_status_m2o = fields.Many2one("provider.status.id")
# 	# provider_status_id_id = fields.Char()  # Many2one('provider.status.id')
# 	# province_code_m2o = fields.Many2one("res.country.state")  # add the nlrd and setmis lookup fields in this model to be used correctly
# 	# country_code_m2o = fields.Many2one("res.country")  # add the nlrd and setmis lookup fields in this model to be used correctly
# 	# country_code_id = (fields.Char())  # Many2one('res.country')  # add the nlrd and setmis lookup fields in this model to be used correctly
# 	# province_code_id = (fields.Char())  # Many2one('res.country.state')  # add the nlrd and setmis lookup fields in this model to be used correctly
# 	latitude_degree = fields.Char(size=3)
# 	latitude_minutes = fields.Char(size=2)
# 	latitude_seconds = fields.Char(size=6)
# 	longitude_degree = fields.Char(size=2)
# 	longitude_minutes = fields.Char(size=2)
# 	longitude_seconds = fields.Char(size=6)
# 	provider_website_address = fields.Char()
# 	SDL_No = fields.Char(size=10)
# 	date_stamp = fields.Datetime(default=datetime.datetime.now())
# 	provider_start_date = fields.Char()
# 	provider_end_date = fields.Char()
# 	# provider_start_date = fields.Datetime(validators=[validate_provider_start_end_date])
# 	django_id = fields.Char()
# 	Report_ID = fields.Text()

"""
this is the employer file aka seta.employer aka (nlrd) aka 200(setmis)
"""


# Tested and Working
def check_sdl_no(sdl_no):
    broken = False
    valid = []
    msg = ""
    if sdl_no == "False":
        msg = "SDL No may not be left blank"
        broken = True
        sdl_no = ""
    if sdl_no:
        valid = SDL_no(sdl_no)
    if valid == False:
        broken = True
        msg = "SDL No must start with 'L' followed by 9 digits or 'N' followed by 9 digits\n"
    return broken, msg


# Tested and Working
def check_site_no(site_no):
    broken = False
    valid = []
    msg = ""
    if site_no == "False":
        msg = "Site No may not be left blank"
        broken = True
        site_no = ""
    if site_no:
        valid = site_no(site_no)
    if valid == False:
        broken = True
        msg = "Site No should only contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


# Tested and Working
def check_employer_postal_address_1(employer_postal_address_1):
    broken = False
    valid = []
    msg = ""
    if employer_postal_address_1 == "False":
        msg = "employer postal address_1 field may not be left blank \n"
        broken = True
    if employer_postal_address_1:
        valid = provider_address(employer_postal_address_1)
    if valid == False:
        broken = True
        msg = "employer postal address 1 should only contain a valid address \n"
    return broken, msg


# Tested and Working
def check_employer_postal_address_2(employer_postal_address_2):
    broken = False
    valid = []
    msg = ""
    if employer_postal_address_2 == "False":
        msg = "employer_postal_address_2 field may not be left blank \n"
        broken = True
    if employer_postal_address_2:
        valid = provider_address(employer_postal_address_2)
    if valid == False:
        broken = True
        msg = "employer_postal_address_2 should only contain a valid address \n"
    return broken, msg


# Tested and Working
def check_employer_postal_address_3(employer_postal_address_3):
    broken = False
    valid = []
    msg = ""
    if employer_postal_address_3:
        valid = provider_address(employer_postal_address_3)
    if valid == False:
        broken = True
        msg = "employer postal address 3 should only contain a valid address\n"
    return broken, msg


# Tested and Working
def check_employer_postal_address_code(employer_postal_address_code):
    broken = False
    valid = []
    msg = ""
    if employer_postal_address_code == "False":
        msg = "employer postal address code field may not be left blank\n"
        employer_postal_address_code = ""
        broken = True
    if employer_postal_address_code:
        valid = provider_address_code(employer_postal_address_code)
    if valid == False:
        broken = True
        msg = "employer postal address code should only contain a valid address code\n"
    return broken, msg


# Tested and Working
def check_employer_physical_address_1(employer_physical_address_1):
    broken = False
    valid = []
    msg = ""
    if employer_physical_address_1 == "False":
        msg = "employer Physical address 1 Field may not be left blank\n"
        broken = True
    if employer_physical_address_1:
        valid = provider_address(employer_physical_address_1)
    if valid == False:
        broken = True
        msg = "employer Physical address 1 should only contain a valid address\n"
    return broken, msg


# Tested and Working
def check_employer_physical_address_2(employer_physical_address_2):
    broken = False
    valid = []
    msg = ""
    if employer_physical_address_2 == "False":
        msg = "employer Physical address 2 Field may not be left blank\n"
        broken = True
    if employer_physical_address_2:
        valid = provider_address(employer_physical_address_2)
    if valid == False:
        broken = True
        msg = "employer Physical address 2 should only contain a valid address\n"
    return broken, msg


# Tested and Working
def check_employer_physical_address_3(employer_physical_address_3):
    broken = False
    valid = []
    msg = ""
    if employer_physical_address_3:
        valid = provider_address(employer_physical_address_3)
    if valid == False:
        broken = True
        msg = "Employer Physical address 3 should only contain a valid address\n"
    return broken, msg


# Tested and Working
def check_employer_physical_address_code(employer_physical_address_code):
    broken = False
    valid = []
    msg = ""
    if employer_physical_address_code == "False":
        msg = "Employer Physical address code  Field may not be left blank\n"
        broken = True
        employer_physical_address_code = ""
        broken = True
    if employer_physical_address_code:
        valid = provider_address_code(employer_physical_address_code)
    if valid == False:
        broken = True
        msg = (
            "Employer Physical address code should only contain a valid address code\n"
        )
    return broken, msg


# Tested and Working
def check_latitude_degree(latitude_degree):
    broken = False
    valid = []
    msg = ""
    if latitude_degree == "False":
        latitude_degree = ""
    if latitude_degree:
        valid = latitude_degree(latitude_degree)
    if valid == False:
        broken = True
        msg = "Latitude Degree may only contain whole numbers and may not be greater than -22 and may not have a value less than -35\n"
    return broken, msg


# Tested and Working
def check_latitude_minutes(latitude_minutes):
    broken = False
    valid = []
    msg = ""
    if latitude_minutes == "False":
        latitude_minutes = ""
    if latitude_minutes:
        valid = latitude_minutes(latitude_minutes)
    if valid == False:
        broken = True
        msg = "Latitude Minutes may not be greater than 59\n"
    return broken, msg


# Tested and Working
def check_latitude_seconds(latitude_seconds):
    broken = False
    valid = []
    msg = ""
    if latitude_seconds == "False":
        latitude_seconds = ""
    if latitude_seconds:
        valid = latitude_seconds(latitude_seconds)
    if valid == False:
        broken = True
        msg += "Latitude Seconds may only contain 1234567890 and must have a length of exactly 6 (nn.nnn) and may not be greater than 59.999.\n"
    return broken, msg


# Tested and Working
def check_longitude_degree(longitude_degree):
    broken = False
    valid = []
    msg = ""
    if longitude_degree == "False":
        longitude_degree = ""
    if longitude_degree:
        valid = longitude_degree(longitude_degree)
    if valid == False:
        broken = True
        msg = "longitude degree may only contain whole numbers and may not be greater than 33 and may not have a value less than 16\n"
    return broken, msg


# Tested and Working
def check_longitude_minutes(longitude_minutes):
    broken = False
    valid = []
    msg = ""
    if longitude_minutes == "False":
        longitude_minutes = ""
    if longitude_minutes:
        valid = longitude_minutes(longitude_minutes)
    if valid == False:
        broken = True
        msg = "longitude minutes may not be greater than 59\n"
    return broken, msg


# Tested and Working
def check_longitude_seconds(longitude_seconds):
    broken = False
    valid = []
    msg = ""
    if longitude_seconds == "False":
        longitude_seconds = ""
    if longitude_seconds:
        valid = longitude_seconds(longitude_seconds)
    if valid == False:
        broken = True
        msg += "longitude seconds may only contain 1234567890 and must have a length of exactly 6 (nn.nnn) and may not be greater than 59.999.\n"
    return broken, msg


# Tested and Working
def check_employer_registration_number(emp_registration_number):
    broken = False
    valid = []
    msg = ""
    if emp_registration_number:
        valid = employer_registration_number(emp_registration_number)
    if valid == False:
        broken = True
        msg = "employer registration number should only contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-"
    return broken, msg


def check_employer_company_name(employer_company_name):
    broken = False
    valid = []
    msg = ""
    if employer_company_name:
        valid = employer_name(employer_company_name)
    if valid == False:
        broken = True
        msg = "should only contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    dbg(broken, msg)
    return broken, msg


def check_employer_trading_name(employer_trading_name):
    broken = False
    valid = []
    msg = ""
    if employer_trading_name == "False":
        msg = "employer company name may not be left blank"
        employer_trading_name = ""
        broken = True
    if employer_trading_name:
        valid = employer_name(employer_trading_name)
    if valid == False:
        broken = True
        msg = " should only contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-"
    return broken, msg


# Tested and Working
def check_employer_phone_number(employer_phone_number):
    broken = False
    valid = []
    msg = ""
    if employer_phone_number == "False":
        # msg = "Employer Physical address code  Field may not be left blank\n"
        employer_phone_number = ""

    if employer_phone_number:
        valid = provider_phone_number(employer_phone_number)
    if valid == False:
        broken = True
        msg = "employer phone number should ony contain 1234567890 ()/-\n"
    return broken, msg


# Tested and Working
def check_employer_fax_number(employer_fax_number):
    broken = False
    valid = []
    msg = ""
    if employer_fax_number == "False":
        # msg = "Employer Physical address code  Field may not be left blank\n"
        employer_fax_number = ""

    if employer_fax_number:
        valid = provider_fax_number(employer_fax_number)
    if valid == False:
        broken = True
        msg = "employer fax number should ony contain 1234567890 ()/-\n"
    return broken, msg


def check_main_sdl_no(main_sdl_no):
    broken = False
    valid = []
    msg = ""
    if main_sdl_no == "False":
        msg = "Main SDL No may not be left blank"
        main_sdl_no = ""
        broken = True
    if main_sdl_no:
        valid = SDL_no(main_sdl_no)
    if valid == False:
        broken = True
        msg = "Main SDL No must start with 'L' followed by 9 digits or 'N' followed by 9 digits\n"
    return broken, msg


def check_employer_contact_name(employer_contact_name):
    broken = False
    valid = []
    msg = ""
    if employer_contact_name == "False":
        msg = "employer contact name may not be left blank"
        employer_contact_name = ""
        broken = True
    if employer_contact_name:
        valid = provider_contact_name(employer_contact_name)
    if valid == False:
        broken = True
        msg = "employer contact name  should ony contain a valid contact name\n"
    return broken, msg


def check_employer_contact_email_address(employer_contact_email_address):
    broken = False
    valid = []
    msg = ""
    if employer_contact_email_address == "False":
        employer_contact_email_address = ""
    if employer_contact_email_address:
        valid = provider_contact_email_address(employer_contact_email_address)
    if valid == False:
        broken = True
        msg = "employer contact email should contain a valid email\n"
    return broken, msg


def check_employer_contact_phone_number(employer_contact_phone_number):
    broken = False
    valid = []
    msg = ""
    if employer_contact_phone_number == "False":
        msg = "employer contact phone number may not be left blank"
        employer_contact_phone_number = ""
        broken = True
    if employer_contact_phone_number:
        valid = provider_phone_number(employer_contact_phone_number)
    if valid == False:
        broken = True
        msg = "employer contact phone number should ony contain 1234567890 ()/-\n"
    return broken, msg


def check_employer_contact_cell_number(employer_contact_cell_number):
    broken = False
    valid = []
    msg = ""
    if employer_contact_cell_number == "False":
        employer_contact_cell_number = ""
    if employer_contact_cell_number:
        valid = provider_contact_cell_number(employer_contact_cell_number)
    if valid == False:
        broken = True
        msg = "employer contact cell number should ony contain 1234567890 ()/-\n"
    return broken, msg


# Tested and Working
def check_employer_approval_start_date(employer_approval_start_date):
    broken = False
    valid = []
    msg = ""

    try:

        if employer_approval_start_date == "False":
            msg = "Field may not be left blank\n"
            broken = True
            employer_approval_start_date = ""
        if employer_approval_start_date:
            valid = start_date(employer_approval_start_date)
        if valid == False:
            broken = True
            msg = "employer approval start date should contain a valid date and not greater than today's date\n"
    except:
        broken = True
        msg = "employer approval start date should contain a valid date"

    return broken, msg


def check_employer_approval_end_date(employer_approval_end_date):
    broken = False
    valid = []
    msg = ""

    try:

        if employer_approval_end_date == "False":
            employer_approval_end_date = ""
        if employer_approval_end_date:
            valid = employer_approval_end_date(employer_approval_end_date)
        if valid == False:
            broken = True
            msg = "employer approval end date should contain a valid date\n"
    except:
        broken = True
        msg = "employer approval end date should contain a valid date"

    return broken, msg


"""
this is the person file aka res.partner aka 29(nlrd) aka 400(setmis)
"""
# Tested and Working
# def check_national_id(national_id):
#     broken = False
#     valid = []
#     msg = ""
#     if national_id == "False":
#         national_id = ""
#     if national_id:
#         valid = chk_national_id(national_id)
#     if valid == False:
#         broken = True
#         msg = "National id not valid\n"
#     return broken, msg


# Tested and Working
def check_person_postal_address_1(person_postal_address_1):
    broken = False
    valid = []
    msg = ""
    if person_postal_address_1 == "False":
        # msg = "person_postal_address_1 field may not be left blank \n"
        # broken = True
        person_postal_address_1 = ""
    if person_postal_address_1:
        valid = provider_address(person_postal_address_1)
    if valid == False:
        broken = True
        msg = "Postal Address 1 should only contain a valid address."
    return broken, msg


# Tested and Working
def check_person_postal_address_2(person_postal_address_2):
    broken = False
    valid = []
    msg = ""
    if person_postal_address_2 == "False":
        person_postal_address_2 = ""
    if person_postal_address_2:
        valid = provider_address(person_postal_address_2)
    if valid == False:
        broken = True
        msg = "Postal Address 2 should only contain a valid address."
    return broken, msg


# Tested and Working
def check_person_postal_address_3(person_postal_address_3):
    broken = False
    valid = []
    msg = ""
    if person_postal_address_3 == "False":
        person_postal_address_3 = ""
    if person_postal_address_3:
        valid = provider_address(person_postal_address_3)
    if valid == False:
        broken = True
        msg = "Postal Address 3 should only contain a valid address."
    return broken, msg


# Tested and Working
def check_person_postal_address_code(person_postal_address_code):
    broken = False
    valid = []
    msg = ""
    if person_postal_address_code == "False":
        person_postal_address_code = ""
    if person_postal_address_code:
        valid = provider_address_code(person_postal_address_code)
    if valid == False:
        broken = True
        msg = " Postal Code should only contain a valid address code."
    return broken, msg


# Tested and Working
def check_person_home_address_1(person_home_address_1):
    broken = False
    valid = []
    msg = ""
    if person_home_address_1 == "False":
        person_home_address_1 = ""
    if person_home_address_1:
        valid = provider_address(person_home_address_1)
    if valid == False:
        broken = True
        msg = "Physical Address 1 should only contain a valid address."
    return broken, msg


# Tested and Working
def check_person_home_address_2(person_home_address_2):
    broken = False
    valid = []
    msg = ""
    if person_home_address_2 == "False":
        person_home_address_2 = ""
    if person_home_address_2:
        valid = provider_address(person_home_address_2)
    if valid == False:
        broken = True
        msg = "Physical Address 2 should only contain a valid address."
    return broken, msg


# Tested and Working
def check_person_home_address_3(person_home_address_3):
    broken = False
    valid = []
    msg = ""
    if person_home_address_3 == "False":
        person_home_address_3 = ""
    if person_home_address_3:
        valid = provider_address(person_home_address_3)
    if valid == False:
        broken = True
        msg = "Physical Address 3 should only contain a valid address."
    return broken, msg


def check_person_address_code(person_address_code):
    broken = False
    valid = []
    msg = ""
    if person_address_code == "False":
        person_address_code = ""
    if person_address_code:
        valid = provider_address_code(person_address_code)
    if valid == False:
        broken = True
        msg = "Physical Postal Code should only contain a valid address code."
    return broken, msg

def check_work_email(work_email):
    broken = False
    valid = []
    msg = ""
    if work_email == "False":
        work_email = ""
    if work_email:
        valid = provider_contact_email_address(work_email)
    if valid == False:
        broken = True
        msg = "Work Email should contain a valid email."
    return broken, msg

# Tested and Working
def check_work_address_1(work_address_1):
    broken = False
    valid = []
    msg = ""
    if work_address_1 == "False":
        work_address_1 = ""
    if work_address_1:
        valid = provider_address(work_address_1)
    if valid == False:
        broken = True
        msg = "Work Address 1 should only contain a valid address."
    return broken, msg


# Tested and Working
def check_work_address_2(work_address_2):
    broken = False
    valid = []
    msg = ""
    if work_address_2 == "False":
        work_address_2 = ""
    if work_address_2:
        valid = provider_address(work_address_2)
    if valid == False:
        broken = True
        msg = "Work Address 2 should only contain a valid address\n"
    return broken, msg


# Tested and Working
def check_work_address_3(work_address_3):
    broken = False
    valid = []
    msg = ""
    if work_address_3 == "False":
        work_address_3 = ""
    if work_address_3:
        valid = provider_address(work_address_3)
    if valid == False:
        broken = True
        msg = "Work Address 3 should only contain a valid address\n"
    return broken, msg


def check_work_address_code(work_address_code):
    broken = False
    valid = []
    msg = ""
    if work_address_code == "False":
        work_address_code = ""
    if work_address_code:
        valid = provider_address_code(work_address_code)
    if valid == False:
        broken = True
        msg = "Work Address code should only contain a valid address code\n"
    return broken, msg

# Tested and Working
def check_person_cell_phone_number(person_cell_phone_number):
    broken = False
    valid = []
    msg = ""
    if person_cell_phone_number == "False":
        person_cell_phone_number = ""
    if person_cell_phone_number:
        valid = provider_contact_cell_number(person_cell_phone_number)
    if valid == False:
        broken = True
        msg = "Mobile No should ony contain 1234567890 ()/-"
    return broken, msg


# Tested and Working
def check_person_phone_number(person_phone_number):
    broken = False
    valid = []
    msg = ""
    if person_phone_number == "False":
        person_phone_number = ""
    if person_phone_number:
        valid = provider_phone_number(person_phone_number)
    if valid == False:
        broken = True
        msg = "Phone No should ony contain 1234567890 ()/-"
    return broken, msg


def check_person_alternate_id(person_alternate_id):
    broken = False
    valid = []
    msg = ""
    if person_alternate_id == "False":
        person_alternate_id = ""
    if person_alternate_id:
        valid = chk_person_alternate_id(person_alternate_id)
    if valid == False:
        broken = True
        msg = "Alternate ID may only contain characters ABCDEFGHIJKLMNOPQRTSUVWXYZ-1234567890@_"
    return broken, msg


# Tested and Working
def check_person_fax_number(person_fax_number):
    broken = False
    valid = []
    msg = ""
    if person_fax_number == "False":
        # msg = "Employer Physical address code  Field may not be left blank\n"
        person_fax_number = ""

    if person_fax_number:
        valid = provider_fax_number(person_fax_number)
    if valid == False:
        broken = True
        msg = "Fax No should ony contain 1234567890 ()/-\n"
    return broken, msg


def check_person_email_address(person_email_address):
    broken = False
    valid = []
    msg = ""
    if person_email_address == "False":
        person_email_address = ""
    if person_email_address:
        valid = provider_contact_email_address(person_email_address)
    if valid == False:
        broken = True
        msg = "person_email_address should contain a valid email\n"
    return broken, msg


def check_person_last_name(person_last_name):
    broken = False
    valid = []
    msg = ""
    if person_last_name == "False":
        person_last_name = ""
    if person_last_name:
        valid = person_name(person_last_name)
    if valid == False:
        broken = True
        msg = "\nLast Name should contain a valid name."
    return broken, msg


def check_person_first_name(person_first_name):
    broken = False
    valid = []
    msg = ""
    if person_first_name == "False":
        person_first_name = ""
    if person_first_name:
        valid = person_name(person_first_name)
    if valid == False:
        broken = True
        msg = "\nFirst Name should contain a valid name."
    return broken, msg


def check_person_middle_name(person_middle_name):
    broken = False
    valid = []
    msg = ""
    if person_middle_name == "False":
        person_middle_name = ""
    if person_middle_name:
        valid = person_name(person_middle_name)
    if valid == False:
        broken = True
        msg = "\n Middle Name should contain a valid name."
    return broken, msg

def check_person_title(check_person_title):
    broken = False
    valid = []
    msg = ""
    if check_person_title == "False":
        check_person_title = ""
    if check_person_title:
        valid = person_name(check_person_title)
    if valid == False:
        broken = True
        msg = "field should contain a valid Title\n"
    return broken, msg

# Tested and Working
def check_person_birth_date(person_birth_date):
    if type(person_birth_date) == date:
        startdate = person_birth_date
    elif type(person_birth_date) == datetime.datetime:
        startdate = person_birth_date.date()
    else:
        raise UserError(type(person_birth_date))
    # person_birth_date = str(person_birth_date)
    broken = False
    msg = ""
    if person_birth_date == "False":
        msg += "person_birth_date field may not be left blank\n"
        broken = True
        person_birth_date = ""
    if person_birth_date:
        # startdate = person_birth_date.strip()
        today = date.today()
        age = (
                today.year
                - startdate.year
                - ((today.month, today.day) < (startdate.month, startdate.day))
        )
        print(age)
        if age < 16:
            broken = True
            msg += "age may not be less than 16 years"
        if startdate < datetime.date(1850, 1, 1):
            broken = True
            msg += "person_birth_date must be greater than 1850"

    return broken, msg


def check_person_previous_last_name(person_previous_last_name):
    broken = False
    valid = []
    msg = ""
    if person_previous_last_name == "False":
        person_previous_last_name = ""
    if person_previous_last_name:
        valid = person_name(person_previous_last_name)
    if valid == False:
        broken = True
        msg = "person_previous_last_name should contain a valid name\n"
    return broken, msg


def check_person_previous_alternate_id(person_previous_alternate_id):
    broken = False
    valid = []
    msg = ""
    if person_previous_alternate_id == "False":
        person_previous_alternate_id = ""
    if person_previous_alternate_id:
        valid = chk_person_alternate_id(person_previous_alternate_id)
    if valid == False:
        broken = True
        msg = "person_previous_alternate_id may only contain characters ABCDEFGHIJKLMNOPQRTSUVWXYZ-1234567890@_\n"
    return broken, msg


# Tested and Working
def check_person_previous_provider_code(person_previous_provider_code):
    broken = False
    valid = []
    msg = ""

    if person_previous_provider_code == "False":
        person_previous_provider_code = ""
    if person_previous_provider_code:
        valid = provider_code(person_previous_provider_code)
    if valid == False:
        broken = True
        msg = "person_previous_provider_code should ony contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


# Tested and Working
def check_popi_act_status_date(popi_act_status_date_value):
    broken = False
    valid = []
    msg = ""

    try:

        if popi_act_status_date_value == "False":
            popi_act_status_date_value = ""
        if popi_act_status_date_value:
            valid = popi_act_status_date(popi_act_status_date_value)
        if valid == False:
            broken = True
            msg = "popi_act_status_date may not be greater than todays date\n"
    except:
        broken = True
        msg = "popi_act_status_date should contain a valid date"

    return broken, msg


# Tested and Working
def check_person_previous_alternate_id_type_id(person_previous_alternate_id_type_id_value):
    broken = False
    valid = []
    msg = ""

    # if person_previous_alternate_id_type_id_value == "False":
    #     person_previous_alternate_id_type_id_value = ""
    if person_previous_alternate_id_type_id_value:
        valid = person_previous_alternate_id_type_id(
            person_previous_alternate_id_type_id_value
        )
    if valid == False:
        broken = True
        msg = "person_previous_alternate_id_type_id may only contain whole numbers\n"
    return broken, msg


# Tested and Working
def check_person_previous_provider_etqe_id(person_previous_provider_etqe_id):
    broken = False
    valid = []
    msg = ""

    if person_previous_provider_etqe_id == "False":
        person_previous_provider_etqe_id = ""
    if person_previous_provider_etqe_id:
        valid = person_previous_alternate_id_type_id(person_previous_provider_etqe_id)
    if valid == False:
        broken = True
        msg = "person_previous_provider_etqe_id may only contain whole numbers\n"
    return broken, msg


# Tested and Working
def check_last_school_emis_number(last_school_emis_number):
    broken = False
    valid = []
    msg = ""

    if last_school_emis_number == "False":
        last_school_emis_number = ""
    if last_school_emis_number:
        valid = person_previous_alternate_id_type_id(last_school_emis_number)
    if valid == False:
        broken = True
        msg = "last_school_emis_number may only contain whole numbers\n"
    return broken, msg


# Tested and Working
def check_last_school_year(last_school_year_value):
    broken = False
    valid = []
    msg = ""

    # if last_school_year == "False":
    #     last_school_year = ""
    if last_school_year_value:
        valid = last_school_year(last_school_year_value)
    if valid == False:
        broken = True
        msg = "last_school_year may only contain year in format YYYY\n"
    return broken, msg


"""
this is the employer file aka seta.designation aka (nlrd) aka 401(setmis)
"""
# Tested and Working
def check_date_stamp(date_stamp):
    broken = False
    valid = []
    msg = ""
    if date_stamp == "False":
        msg = "Date Stamp Field may not be left blank\n"
        broken = True
    return broken, msg


# Tested and Working
def check_designation_etqe_id(designation_etqe_id):
    broken = False
    valid = []
    msg = ""
    if designation_etqe_id == "False":
        msg = "designation_etqe_id may not be left blank"
        brokent = True
        designation_etqe_id = ""

    if designation_etqe_id:
        valid = designation_etqe_id(designation_etqe_id)
    if valid == False:
        broken = True
        msg = "designation_etqe_id may only contain whole numbers\n"
    return broken, msg


# Tested and Working
def check_designation_start_date(designation_start_date):
    broken = False
    valid = []
    msg = ""
    try:
        if designation_start_date == "False":
            msg = "designation start date Field may not be left blank\n"
            broken = True
            designation_start_date = ""
        if designation_start_date:
            valid = start_date(designation_start_date)
        if valid == False:
            broken = True
            msg = "designation start date should contain a valid date and not greater than today's date\n"
    except:
        broken = True
        msg = "designation start date should contain a valid date"

    return broken, msg


# Tested and Working
def check_national_id(national_id):
    broken = False
    valid = []
    msg = ""
    if national_id == "False":
        national_id = ""
    if national_id:
        valid = chk_national_id(national_id)
        dbg('validz',valid)
    if valid == False:
        broken = True
        msg = "National id not valid\n"
    return broken, msg


def check_person_alternate_id(person_alternate_id):
    broken = False
    valid = []
    msg = ""
    if person_alternate_id == "False":
        person_alternate_id = ""
    if person_alternate_id:
        valid = chk_person_alternate_id(person_alternate_id)
    if valid == False:
        broken = True
        msg = "person_alternate_id may only contain characters ABCDEFGHIJKLMNOPQRTSUVWXYZ-1234567890@_\n"
    return broken, msg


def check_designation_registration_number(designation_registration_number):
    broken = False
    valid = []
    msg = ""
    if designation_registration_number == "False":
        msg = "designation_registration_number should not be blank"
        broken = True
        designation_registration_number = ""
    if designation_registration_number:
        valid = designation_registration_number(designation_registration_number)
    if valid == False:
        broken = True
        msg = "designation_registration_number should ony contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-\n"
    return broken, msg


def check_etqe_decision_number(etqe_decision_number):
    broken = False
    valid = []
    msg = ""
    if etqe_decision_number == "False":
        etqe_decision_number = ""

    if etqe_decision_number:
        valid = etqe_decision_number(etqe_decision_number)
    if valid == False:
        broken = True
        msg = "etqe_decision_number may only contain whole numbers\n"
    return broken, msg


# Tested and Working
def check_designation_end_date(designation_end_date):
    broken = False
    valid = []
    msg = ""
    try:
        if designation_end_date == "False":
            designation_end_date = ""
        if designation_end_date:
            valid = designation_end_date(designation_end_date)
        if valid == False:
            broken = True
            msg = "designation_end_date should not less be than 1900\n"
    except:
        broken = True
        msg = "designation_end_date should contain a valid date"

    return broken, msg

def check_name_all(name_check):
    broken = False
    valid = []
    msg = ""
    if name_check == "False":
        msg = "may not be left blank"
        name_check = ""
        broken = True
    if name_check:
        valid = employer_name(name_check)
    if valid == False:
        broken = True
        msg = " should only contain ABCDEFGHIJKLMNOPQRTSUVWXYZ1234567890@#&+() /\:._-"
    return broken, msg



# class SetaDesignation(models.Model):
# 	_name = "seta.designation"
# 	django_id = fields.Integer()

# 	person = fields.Many2one("res.partner")
# 	# person = fields.Char()
# 	person_id = fields.Char()

# 	national_id = fields.Char(size=15)
# 	# national_id = fields.Char(size=15, validators=[validateID])
# 	person_alternate_id = fields.Char(size=20)

# 	alternate_id_type_id_id_m2o = fields.Many2one(
# 		"alternate.id.type.id"
# 	)  # , default='533', to_field='lookup',on_delete=models.CASCADE
# 	alternate_id_type_id_id_id = fields.Char()

# 	designation_id_m2o = fields.Many2one(
# 		"designation.id"
# 	)  # , to_field='lookup', on_delete=models.CASCADE
# 	designation_id_id = fields.Char()

# 	designation_registration_number = fields.Char(size=20)
# 	designation_etqe_id = fields.Char(size=10)
# 	designation_start_date = fields.Datetime()
# 	designation_end_date = fields.Datetime()  # , blank=True

# 	designation_structure_status_id_m2o = fields.Many2one(
# 		"designation.structure.status.id"
# 	)  # , to_field='lookup',on_delete=models.CASCADE
# 	designation_structure_status_id_id = fields.Char()
# 	etqe_decision_number = fields.Char(size=20)  # , blank=True

# 	provider_code_m2o = fields.Many2one("seta.provider")  # , on_delete=models.CASCADE
# 	provider_code_id = fields.Char()

# 	# provider_etqe_id = fields.Char(size=10)
# 	provider_etqe_id_m2o = fields.Char(size=10)
# 	date_stamp = fields.Datetime(default=datetime.datetime.now())


# 	@api.onchange("designation_end_date")
# 	def onchange_designation_end_date(self):
# 		valid = []
# 		strmessage = "Designation end date"
# 		if (
# 			self.designation_start_date
# 			and self.designation_start_date.date() > self.designation_end_date.date()
# 		):
# 			raise ValidationError(strmessage + " should not be less than start date")


# class ResPartner(models.Model):
# 	_inherit = "res.partner"

# 	designation_ids = fields.One2many("seta.designation", "person")


# class SetmisSubDesignation(models.Model):
# 	_name = "setmis.sub.designation"
# 	django_id = fields.Integer()

# 	person = fields.Many2one("res.partner")
# 	# person = fields.Char()
# 	person_id = fields.Char()

# 	national_id = fields.Char(size=15)
# 	# national_id = fields.Char(size=15, validators=[validateID])
# 	person_alternate_id = fields.Char(size=20)

# 	alternate_id_type_id_id_m2o = fields.Many2one(
# 		"alternate.id.type.id"
# 	)  # , default='533', to_field='lookup',on_delete=models.CASCADE
# 	alternate_id_type_id_id_id = fields.Char()

# 	designation_id_m2o = fields.Many2one(
# 		"designation.id"
# 	)  # , to_field='lookup', on_delete=models.CASCADE
# 	designation_id_id = fields.Char()

# 	designation_registration_number = fields.Char(size=20)
# 	designation_etqe_id = fields.Char(size=10)
# 	designation_start_date = fields.Datetime()
# 	designation_end_date = fields.Datetime()  # , blank=True

# 	designation_structure_status_id_m2o = fields.Many2one(
# 		"designation.structure.status.id"
# 	)  # , to_field='lookup',on_delete=models.CASCADE
# 	designation_structure_status_id_id = fields.Char()
# 	etqe_decision_number = fields.Char(size=20)  # , blank=True

# 	provider_code_m2o = fields.Many2one("seta.provider")  # , on_delete=models.CASCADE
# 	provider_code_id = fields.Char()

# 	# provider_etqe_id = fields.Char(size=10)
# 	provider_etqe_id_m2o = fields.Char(size=10)
# 	date_stamp = fields.Datetime(default=datetime.datetime.now())

# 	broken = fields.Boolean()
# 	msg = fields.Text()

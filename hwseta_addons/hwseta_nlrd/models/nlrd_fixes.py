# coding=utf-8
import re
import random
import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# --- IDENTITY & STRINGS ---

def normalize_alt_id(alt_id):
    """ Replaces slashes with dashes in IDs for file compatibility. """
    if not alt_id:
        return ''
    return str(alt_id).replace('/', '-')


def dual_name_removal(text):
    """ Extracts only the first part of a multi-part name string. """
    if not text:
        return ''
    # In Python 3, strings are unicode by default
    return str(text).split(" ")[0]


def sanitize_addrs(addr):
    """ Cleans addresses of semi-colons and quotes for CSV/DAT export. """
    if not addr:
        return ''
    addr = str(addr).replace(";", " ").replace('"', '')
    return addr.strip()


# --- DATE HANDLING (Modernized for Odoo 18) ---

def fix_dates(val):
    """
    Converts Odoo Date/Datetime fields to NLRD string format (YYYYMMDD).
    In Odoo 18, date fields are native Python date objects.
    """
    if not val:
        return '19890413'  # Default NLRD fallback

    try:
        if isinstance(val, (date, datetime)):
            return val.strftime('%Y%m%d')
        elif isinstance(val, str):
            # Handle string dates if coming from older raw SQL or manual input
            clean_str = val.split(' ')[0].replace('-', '')
            return clean_str[:8]
    except Exception:
        _logger.warning(f"Date fix failed for: {val}")
        return '19890413'


def year_gap(start, end, years, prov=None):
    """
    Ensures that a start date is at least X years before the end date.
    Returns a native date object for Odoo 18 field compatibility.
    """
    if not start or not end:
        return start

    # Ensure we are working with date objects
    d_start = start if isinstance(start, date) else datetime.strptime(str(start)[:10], '%Y-%m-%d').date()
    d_end = end if isinstance(end, date) else datetime.strptime(str(end)[:10], '%Y-%m-%d').date()

    if d_start >= d_end - relativedelta(years=years):
        return d_end - relativedelta(years=years)
    return d_start


# --- SAQA / NLRD MAPPINGS ---

def gender_to_code(gen):
    # Odoo 18 selection fields usually return 'male' or 'female'
    return {"female": "F", "male": "M"}.get(gen, "F")


def equity_to_code(eq):
    equity_map = {
        "black_african": "BA", "black_coloured": "BC", "black_indian": "BI",
        "white": "Wh", "other": "Oth", "unknown": "U", False: "U"
    }
    return equity_map.get(eq, "U")


def province_to_code(prov_id):
    """ Map Odoo State IDs to NLRD Province Codes. """
    # Update these IDs to match your Odoo 18 State/Province DB IDs
    prov_map = {
        68: "1", 60: "2", 67: "3", 61: "4", 63: "5",
        66: "6", 62: "7", 65: "8", 64: "9"
    }
    return prov_map.get(prov_id, "N")


def lang_to_code(lang_name):
    langs = {
        'English': 'Eng', 'isiZulu': 'Zul', 'Afrikaans': 'Afr',
        'seSotho': 'Ses', 'isiXhosa': 'Xho', 'Other': 'Oth'
    }
    return langs.get(lang_name, 'U')
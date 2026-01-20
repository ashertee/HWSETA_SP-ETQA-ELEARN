# coding=utf-8
from collections import OrderedDict as OD
import logging
import os

_logger = logging.getLogger(__name__)


def dbg(msg):
    _logger.info(msg)

def replace_unicode_with_normal(text):
    if not text:
        return text

    result = str(text)

    for x, repl in unimap.items():
        if x in result:
            result = result.replace(x, repl)

    return result


def gendat(vald, lens, fields_list, datfile_name):
    """
    Generates a fixed-width DAT file compatible with NLRD specifications.
    Optimized for Odoo 18 / Python 3.
    """
    # Define the output directory (Ensure Odoo has write permissions here)
    # For Odoo.sh or Docker, use /tmp/ or a configured filestore path
    base_path = "/var/log/odoo/nlrd_dat_files/"
    if not os.path.exists(base_path):
        try:
            os.makedirs(base_path)
        except OSError:
            # Fallback to tmp if log dir is restricted
            base_path = "/tmp/nlrd_dat_files/"
            if not os.path.exists(base_path):
                os.makedirs(base_path)

    full_path = os.path.join(base_path, datfile_name)

    line_parts = []

    for i, field_name in enumerate(fields_list):
        width = lens[i]
        # Get value and handle None/False
        raw_val = vald.get(field_name, "")
        if raw_val is False or raw_val is None:
            raw_val = ""

        # Ensure string type for formatting
        str_val = str(raw_val)

        # Python 3 Unicode to ASCII conversion for NLRD
        # We encode to ascii and 'ignore' errors to strip non-ascii chars,
        # then decode back to string for the format operator.
        clean_val = str_val.encode("ascii", errors="ignore").decode("ascii")

        # Fixed-width padding: %-*s pads to the right (left-aligned)
        # We also truncate the string if it exceeds the allowed width
        formatted_part = "{:<{width}}".format(clean_val[:width], width=width)
        line_parts.append(formatted_part)

    # Join parts and ensure DOS line endings (\r\n) as per SAQA/NLRD requirements
    line_to_write = "".join(line_parts) + "\r\n"

    try:
        # 'a' mode creates file if not exists or appends if it does
        with open(full_path, 'a', encoding='ascii') as f:
            f.write(line_to_write)
    except Exception as e:
        _logger.error(f"Failed to write to DAT file {datfile_name}: {str(e)}")
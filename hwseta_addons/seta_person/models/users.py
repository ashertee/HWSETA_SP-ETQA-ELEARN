import datetime

from odoo import api, fields, models, _
import re

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)


    def dbg(msg):
        logger.info(msg)

else:

    def dbg(msg):
        pass


class ResUsers(models.Model):
    _inherit = "res.users"

    person_id = fields.Many2one("seta.person")

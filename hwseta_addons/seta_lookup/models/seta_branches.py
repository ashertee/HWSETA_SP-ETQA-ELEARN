from odoo import fields, models, api, _
from .create_record_mixin import CreateRecordMixin

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class SetaBranches(models.Model):
    _name = "seta.branches"

    name = fields.Char(string="Branch Code")
    branch_address = fields.Char()
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    v8_id = fields.Integer(string="V8 ID", copy=False, index=True)
    v8_value = fields.Char(string="V8 Value", copy=False)
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


class TradeTestResultReasonId(models.Model, CreateRecordMixin):
    _name = "trade.test.result.reason.id"

    name = fields.Char()
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()

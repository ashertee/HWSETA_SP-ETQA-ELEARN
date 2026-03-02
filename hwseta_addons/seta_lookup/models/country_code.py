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


class CountryCode(models.Model):
    _name = "country.code"

    code = fields.Char(string="Country Code")
    image = fields.Binary(string="Flag")
    country_id = fields.Many2one("res.country", string="Res Country")
    address_format = fields.Text(string="Address Format")
    name = fields.Char()
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    province_ids = fields.One2many('province.code', 'country_id', string="Provinces")

    # migration fields
    v8_id = fields.Integer(string='V8 ID')
    v8_value = fields.Char(string='V8 Value')
 

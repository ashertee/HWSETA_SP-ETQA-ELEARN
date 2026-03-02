from odoo import fields, models, api, _
from odoo.exceptions import UserError
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


class ResDistrict(models.Model):
    _name = 'res.district'
    _description = "District"

    name = fields.Char(string='Name')
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    code = fields.Char(string='Code')
    municipality_ids = fields.One2many(
        comodel_name='res.municipality', inverse_name='district_id', string='Municipalities')
    province_code = fields.Many2one('province.code', string='Province Code')
    province_id = fields.Many2one('res.country.state',related='province_code.province_id', string='Res Country State',store=True)
    country_code = fields.Many2one('country.code', string='Country')
    country_id = fields.Many2one('res.country', related='country_code.country_id', string='Res Country',store=True)
    urban_rural = fields.Selection([('urban','Urban'),('rural','Rural'),('unknown','Unknown')], string='Urban/Rural')

        # migration fields
    v8_id = fields.Integer(string='V8 ID')
    v8_value = fields.Char(string='V8 Value')
    v8_province_id = fields.Integer(string='V8 Province ID')
    v8_country_id = fields.Integer(string='V8 Country ID')
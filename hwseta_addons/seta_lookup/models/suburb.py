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


class ResSuburb(models.Model):
    _name = 'res.suburb'
    _description = "Suburb"

    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    name = fields.Char(string='Name')
    postal_code = fields.Char(string='Postal Code')
    municipality_id = fields.Many2one('res.municipality', string='Municipality')
    city_id = fields.Many2one('res.city', string='City')
    district_id = fields.Many2one('res.district', string='District')
    # province = fields.Char(string='Province', related='city_id.province_code.name', store=True)
    province_code = fields.Many2one('province.code', string='Province Code')
    province_id = fields.Many2one('res.country.state',related='province_code.province_id', string='Res Country State',store=True)
    country_id = fields.Many2one('res.country', related="country_code.country_id", string="Res Country",store=True)
    country_code = fields.Many2one('country.code',  string='Country Code')
    urban_rural = fields.Selection([('urban', 'Urban'), ('rural', 'Rural'), ('unknown', 'Unknown')],
                                   string='Urban/Rural')
    statssa_area_code = fields.Char(string='StatsSA Area Code')

        # migration fields
    v8_id = fields.Integer(string='V8 ID')
    v8_value = fields.Char(string='V8 Value')
    v8_city_id = fields.Integer(string='V8 City ID')
    v8_district_id = fields.Integer(string='V8 District ID')
    v8_province_id = fields.Integer(string='V8 Province ID')
    v8_country_id = fields.Integer(string='V8 Country ID')
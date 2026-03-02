from odoo import fields, models, api, _
from odoo.exceptions import UserError

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)


    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class ResCity(models.Model):
    _name = 'res.city'
    _description = "City"

    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    municipality_id = fields.Many2one('res.municipality', string='Municipality')
    district_id = fields.Many2one('res.district',related='municipality_id.district_id', string='District',store=True)
    country_id = fields.Many2one('res.country', related="country_code.country_id", string='Res Country',store=True)
    country_code = fields.Many2one('country.code', string="Country Code")
    # province = fields.Char(string='Res Country State', related='province_code.name', store=True)
    province_code = fields.Many2one('province.code', string='Province Code')
    province_id = fields.Many2one('res.country.state', related="province_code.province_id", string='Res Country State',store=True)
    urban_rural = fields.Selection([('urban', 'Urban'), ('rural', 'Rural'), ('unknown', 'Unknown')],string='Urban/Rural')
    latitude = fields.Char(string='Latitude')
    longitude = fields.Char(string='Longitude')
    suburb_ids = fields.One2many('res.suburb', 'city_id', string='Suburbs')
    active = fields.Boolean(string='Active', default=True)

        # migration fields
    v8_id = fields.Integer(string='V8 ID')
    v8_value = fields.Char(string='V8 Value')
    v8_province_id = fields.Integer(string='V8 Province ID')
    v8_country_id = fields.Integer(string='V8 Country ID')
    v8_district_id = fields.Integer(string='V8 District ID')

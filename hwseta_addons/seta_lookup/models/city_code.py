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


class ResCity(models.Model, CreateRecordMixin):
    _name = 'res.city'
    _description = "City"

    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    name = fields.Char(string='Name')
    district_id = fields.Many2one('res.district', string='District')
    province_id = fields.Many2one('res.country.state', string='Province')
    province_code = fields.Many2one('province.code', string='Province')
    country_id = fields.Many2one('res.country', string='Country')
    urban_rural = fields.Selection([('urban', 'Urban'), ('rural', 'Rural'), ('unknown', 'Unknown')],
                                   string='Urban/Rural')
    latitude = fields.Char(string='Latitude')
    longitude = fields.Char(string='Longitude')

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


class ResMunicipality(models.Model,CreateRecordMixin):
    _name = 'res.municipality'
    _description = "Municipality"

    name = fields.Char(string='Name')
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    city_id = fields.Many2one('res.city', string='City')
    district_id = fields.Many2one('res.district', string='District')
#     code = fields.Char(string='Code') 
    province_id = fields.Many2one('res.country.state', string='Province')
    country_id = fields.Many2one('res.country', string='Country')
    urban_rural = fields.Selection([('urban','Urban'),('rural','Rural'),('unknown','Unknown')], string='Urban/Rural')






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


class ResMunicipality(models.Model,CreateRecordMixin):
    _name = 'res.municipality'
    _description = "Municipality"

    types = [
        ('metropolitan', 'Metropolitan'),
        ('district', 'District'),
        ('local', 'Local'),
    ]

    municipality_type = fields.Selection(types, string='Municipality Type')
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    city_id = fields.Many2one('res.city', string='City')
    city_ids = fields.One2many('res.city', 'municipality_id', string='Cities')
    # province = fields.Char(string='Province', related='province_code.name', store=True)
    district_id = fields.Many2one('res.district', string='District')
    province_code = fields.Many2one('province.code', string='Province Code')
    province_id = fields.Many2one('res.country.state',related='province_code.province_id', string='Res Country State',store=True)
    country_code = fields.Many2one('country.code', string='Country')
    country_id = fields.Many2one('res.country',related='country_code.country_id', string='Res Country',store=True)
    urban_rural = fields.Selection([('urban','Urban'),('rural','Rural'),('unknown','Unknown')], string='Urban/Rural')


        # migration fields
    v8_id = fields.Integer(string='V8 ID')
    v8_value = fields.Char(string='V8 Value')



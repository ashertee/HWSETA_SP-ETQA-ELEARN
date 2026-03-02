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


class ProvinceCode(models.Model):
    _name = "province.code"

    name = fields.Char()
    code = fields.Char(string="Province Code")
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    province_id = fields.Many2one("res.country.state", string="New Province ID")
    country_code = fields.Many2one(
        comodel_name="country.code", string="Country", readonly=True)
    country_id = fields.Many2one("res.country",related="country_code.country_id" , string="Res Country",store=True)
    city_ids = fields.One2many(
        comodel_name="res.city", inverse_name="province_code", string="Cities")
    district_ids = fields.One2many(comodel_name="res.district",
                                   inverse_name="province_code", string="Districts")
    municipality_ids = fields.One2many(comodel_name="res.municipality",
                                      inverse_name="province_code", string="Municipalities")
    suburb_ids = fields.One2many(
        comodel_name="res.suburb", inverse_name="province_code", string="Suburbs")
    
        # migration fields
    v8_id = fields.Integer(string='V8 ID')
    v8_value = fields.Char(string='V8 Value')
    v8_country_id = fields.Integer(string='V8 Country ID')
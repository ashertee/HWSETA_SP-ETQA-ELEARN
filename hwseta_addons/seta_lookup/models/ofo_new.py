from odoo import fields, models, api, _

class OfoCodeLookupNew(models.Model):
    _name = "ofo.code.lookup.new"
    _rec_name = "ofo_code"

    name = fields.Char()
    ofo_code = fields.Char()
    ofo_year = fields.Char()
    occupation = fields.Char()
    trade = fields.Boolean()
    green_skill = fields.Boolean()
    green_occupation = fields.Boolean()
    specialisation = fields.One2many('ofo.code.specialisation.lookup.new', 'occ_id')
    specialisation_2 = fields.Many2many('ofo.code.specialisation.lookup.new')

class OfoCodeSpecialisationsLookupNew(models.Model):
    _name = "ofo.code.specialisation.lookup.new"

    name = fields.Char()
    occ_id = fields.Many2one('ofo.code.lookup.new')

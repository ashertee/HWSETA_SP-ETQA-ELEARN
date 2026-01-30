from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HwsetaSicMaster(models.Model):
    _name = 'hwseta.sic.master'
    _description = 'HWSETA SIC Master'
    _rec_name = 'name'

    seta_id = fields.Many2one('seta.branches', string='SETA ID')
    code = fields.Char(string="Code")
    name = fields.Char(string="Description", required=True)

    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.code:
                name += f'[{record.code}] '
            if record.name:
                name += record.name
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += ['|', ('name', operator, name), ('code', operator, name)]
        records = self.search(args, limit=limit)
        return records.name_get()


class HwsetaOrganisationLegalStatus(models.Model):
    _name = 'hwseta.organisation.legal.status'
    _description = 'HWSETA Organisation Legal Status'

    name = fields.Char(string="Name", required=True)


class HwsetaProviderFocusMaster(models.Model):
    _name = 'hwseta.provider.focus.master'
    _description = 'HWSETA Provider Focus Master'

    name = fields.Char(string="Name", required=True)


class HwsetaChamberMaster(models.Model):
    _name = 'hwseta.chamber.master'
    _description = 'HWSETA Chamber Master'

    name = fields.Char(string="Name", required=True)


class HwsetaRelationToProviderStatus(models.Model):
    _name = 'hwseta.relation.to.provider.status'
    _description = 'HWSETA Relation to Provider Status'

    name = fields.Char(string="Name", required=True)


class HwsetaMaster(models.Model):
    _name = 'hwseta.master'
    _description = 'HWSETA Master'

    name = fields.Char(string="Name", required=True)

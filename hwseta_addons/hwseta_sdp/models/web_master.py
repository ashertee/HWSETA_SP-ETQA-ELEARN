from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HwsetaSicMaster(models.Model):
    _name = 'hwseta.sic.master'
    _description = 'HWSETA SIC Master'

    name = fields.Char(
        string="Name",
        required=True
    )


class HwsetaOrganisationLegalStatus(models.Model):
    _name = 'hwseta.organisation.legal.status'
    _description = 'HWSETA Organisation Legal Status'

    name = fields.Char(
        string="Name",
        required=True
    )


class HwsetaProviderFocusMaster(models.Model):
    _name = 'hwseta.provider.focus.master'
    _description = 'HWSETA Provider Focus Master'

    name = fields.Char(
        string="Name",
        required=True
    )


class HwsetaChamberMaster(models.Model):
    _name = 'hwseta.chamber.master'
    _description = 'HWSETA Chamber Master'

    name = fields.Char(
        string="Name",
        required=True
    )


class HwsetaRelationToProviderStatus(models.Model):
    _name = 'hwseta.relation.to.provider.status'
    _description = 'HWSETA Relation to Provider Status'

    name = fields.Char(
        string="Name",
        required=True
    )


class HwsetaMaster(models.Model):
    _name = 'hwseta.master'
    _description = 'HWSETA Generic Master'

    name = fields.Char(
        string="Name",
        required=True
    )

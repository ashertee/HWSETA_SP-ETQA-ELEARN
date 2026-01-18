# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

DEBUG = True


def dbg(msg):
    if DEBUG:
        _logger.info(msg)


class LearnerRegQualFixWizard(models.TransientModel):
    _name = 'learner.reg.qual.fix.wiz'
    _description = 'Learner Registration Qualification Fix Wizard'

    lrq_id = fields.Many2one('learner.registration.qualification', string="Learner Qualification")
    learner_id = fields.Many2one('hr.employee', string="Learner")

    missing_learner = fields.Boolean(
        string="Missing Learner",
        compute="_compute_missing_learner",
        store=False
    )

    # --------------------------------------------------

    @api.depends('lrq_id')
    def _compute_missing_learner(self):
        for wiz in self:
            wiz.missing_learner = not bool(wiz.lrq_id and wiz.lrq_id.learner_id)

    # --------------------------------------------------

    def fix_lrq(self):
        for wiz in self:
            if wiz.lrq_id:
                raise UserError(_('Found LRQ record: %s') % wiz.lrq_id.display_name)
            else:
                raise UserError(_('No LRQ selected.'))

    # --------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        lrq_id = self.env.context.get('lrq_id')
        if lrq_id:
            res['lrq_id'] = lrq_id
        return res

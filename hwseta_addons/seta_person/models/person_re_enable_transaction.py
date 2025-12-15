from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import datetime
from ... import toolz

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)


    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class SetaPersonReEnableTransaction(models.Model):
    _name = "seta.person.re.enable.transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "ref"

    person_id = fields.Many2one('seta.person')
    ref = fields.Char(string='Reference Number')
    status = fields.Selection([
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('auto_approved', 'Auto Approved'),
        ('rejected', 'Rejected')
    ], string="Status", default='submitted', track_visibility='onchange')
    reason = fields.Char()
    auto_approve = fields.Boolean(default=False)
    display = fields.Text()
    person_links = fields.Text(string='Person Links')
    user_id = fields.Many2one('res.users', string='User Id')



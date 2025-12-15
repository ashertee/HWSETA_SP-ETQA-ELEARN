from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class SetaApplicationRequirements(models.Model):
    _name = "seta.application.requirements"
    # _inherit = ["mail.thread", "mail.activity.mixin"]

    active = fields.Boolean(default=True)
    name = fields.Char()
    code = fields.Char()
    display = fields.Text()

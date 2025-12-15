from odoo import fields, models, api, _

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class OfoCodeOccupationLookup(models.Model):
    _name = "ofo.code.occupation.lookup"

    name = fields.Char()

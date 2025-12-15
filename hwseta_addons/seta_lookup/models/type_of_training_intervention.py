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


class TypeOfTrainingIntervention(models.Model, CreateRecordMixin):
    _name = "type.of.training.intervention"

    name = fields.Char()
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    training_type_id = fields.Many2one(
        comodel_name="training.type")

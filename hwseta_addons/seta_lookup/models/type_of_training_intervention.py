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


class TypeOfTrainingIntervention(models.Model):
    _name = "type.of.training.intervention"

    name = fields.Char()
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()
    training_type_id = fields.Many2one(
        comodel_name="training.type")
    
    pivotal = fields.Boolean(string="Pivotal")

    # Migration fields

    v8_id = fields.Integer(string="V8 ID")
    v8_value = fields.Char(string="V8 Value")
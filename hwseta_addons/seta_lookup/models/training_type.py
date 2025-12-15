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


class TrainingType(models.Model, CreateRecordMixin):
    _name = "training.type"
    _rec_name = "name"
    

    name = fields.Char(string = "Training Type")
    setmis_lookup = fields.Char()
    nlrd_lookup = fields.Char()

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


class SetaUpdateMessage(models.TransientModel):
    _name = "seta.update.message"

    message = fields.Text(string='Comment')

    def action_submit(self):
        ctx = self._context
        errors = ''
        if "active_id" in ctx and "active_model" in ctx:
            model = ctx.get("active_model")
            rec = self.env[model].browse(ctx.get("active_id"))
            dbg(">>>>>>>>>>" + str(ctx))
            if "method" in ctx:
                method = ctx.get("method")
                if hasattr(rec,method):
                    try:
                        dbg("getting attr")
                        operation = getattr(rec, method)
                        res = operation('Comment: ' + self.message)
                    except Exception as e:
                        errors += str(e)
                    if errors != "":
                        raise Warning(errors)
                else:
                    dbg("The method _run_%s doesn't exist on the model" % method)
            else:
                raise Warning("never got a method to use")
        else:
            raise Warning("never got active id or active model")

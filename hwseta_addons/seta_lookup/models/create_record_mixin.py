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

    

class CreateRecordMixin(models.AbstractModel):
    _name = 'create.record.mixin'
    _description = 'Mixin to create new records'

    @api.model
    def create_record(self):#, vals):
        
        """Method to open a form for creating a new record of the calling model."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Record',
            'res_model': self._name,  
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    @api.model
    def edit_record(self):#, vals):
            """Method to edit an existing record."""
            # Open a form view in edit mode for the current record
            return {
                'type': 'ir.actions.act_window',
                'name': 'Edit record',
                'res_model': self._name,
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': dict(self.env.context, show_buttons=False),
            }

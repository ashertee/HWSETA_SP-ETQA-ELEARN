from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

# Standard Odoo 18 logging replaces the legacy DEBUG/dbg block
_logger = logging.getLogger(__name__)

class SdfEmailWizard(models.TransientModel):
    _name = 'sdf.email.wizard'
    _description = 'SDF Email Update Wizard'

    sdf_id = fields.Many2one('hr.employee', string="SDF")
    identification = fields.Char(string="Identification")
    ticket_num = fields.Char(string="Ticket #")
    search_by = fields.Selection([
        ('id', 'Identification Number')
    ], string="Search by", default='id')
    
    work_email = fields.Char(string="New Work Email")

    def get_sdf(self, identification):
        """Find the SDF record using sudo for elevated access."""
        self.ensure_one()
        if identification:
            # Modern sudo() syntax
            sdf_obj = self.env['hr.employee'].sudo().search([
                ('identification_id', '=', identification)
            ], limit=1)
            return sdf_obj
        raise UserError(_('You need an Identification Number!'))

    @api.onchange('identification')
    def onchange_get_sdf(self):
        """Automatically fetch SDF record on ID change."""
        if self.identification:
            sdf_obj = self.get_sdf(self.identification)
            if sdf_obj:
                self.sdf_id = sdf_obj.id
                # Optionally pre-fill the email to show current state
                self.work_email = sdf_obj.work_email

    def fix_email(self):
        """Updates Email across Employee, User, and Partner records."""
        # Replacement for @api.one is ensure_one()
        self.ensure_one()
        
        if not self.identification:
            raise UserError(_("Identification is required."))
            
        sdf_obj = self.get_sdf(self.identification)
        if not sdf_obj:
            raise UserError(_("Could not find the SDF record."))
            
        if not self.work_email:
            raise UserError(_("Please ensure the new email is filled!"))

        old_email = sdf_obj.work_email
        
        # 1. Update Employee
        sdf_obj.sudo().write({'work_email': self.work_email})

        # 2. Update User Login
        user_obj = self.env['res.users'].sudo().search([
            ('sdf_id', '=', sdf_obj.id)
        ], limit=1)
        
        if user_obj:
            user_obj.write({'login': self.work_email})
            # 3. Update Partner Email
            if user_obj.partner_id:
                user_obj.partner_id.write({'email': self.work_email})

        # Log the change
        msg = f"ticket#:{self.ticket_num or 'N/A'}-{self.identification}-sdf email changed: {old_email} > {self.work_email}"
        _logger.info(msg)

        # 4. Handle Notification Email
        template = self.env.ref('hwseta_etqe.email_template_master_data_edit_notification', raise_if_not_found=False)
        if template:
            # Sudo is needed to write to the template body temporarily
            template.sudo().write({
                'body_html': f"<p>{msg}</p>",
                'email_from': self.env.user.email
            })
            template.send_mail(sdf_obj.id, force_send=True)

        return {'type': 'ir.actions.act_window_close'}


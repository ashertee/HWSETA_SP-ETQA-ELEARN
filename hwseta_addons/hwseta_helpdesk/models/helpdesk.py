from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import re
from lxml import etree

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)


    def dbg(msg):
        logger.info(msg)
else:
    def dbg(msg):
        pass


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def _get_assigned_user_field(self):
        users_search = self.env['res.users'].search([])
        users = []
        if self.team_id:
            return [('id', 'in', self.user_ids.ids)]
        for user in users_search:
            if user.has_group('seta_base.seta_internal'):
                users.append(user.id)
        return [('id', 'in', users)]

    @api.onchange("contact_number")
    def onchange_contact_number(self):
        if self.contact_number:
            if not self.contact_number.isnumeric() or len(self.contact_number) < 10:
                return {'warning': {'title': 'Invalid Contact Number',
                                    'message': 'Please re-enter a valid Contact Number'},
                        'value': {'contact_number': False, }}

    def _get_default_note(self):
        result = """
	    <div>
	        <p class="terms">Please provide a comprehensive explanation of the problem or error you are encountering. If feasible, attach a relevant screenshot depicting the error:</p>
	    </div>"""
        return result

    number = fields.Char(string="Ticket number", default="", readonly=True)
    description = fields.Html(required=True, sanitize_style=True, default=_get_default_note)
    user_id = fields.Many2one(
        'res.users',
        string='Assigned user',
        track_visibility="onchange",
        index=True,
        domain="[('id', 'in', allowed_value_ids)]",
    )
    province_id = fields.Many2one("res.country.state")
    stakeholder_type = fields.Selection([
        ('assessor', 'Assessor'),
        ('moderator', 'Moderator'),
        ('provider', 'Provider'),
        ('employer', 'Employer/Organisation'),
        ('learner', 'Learner'),
        ('sdf', 'SDF'),
        ('other', 'Other')
    ])
    stakeholder_type_id = fields.Char()
    contact_number = fields.Char(size=10)
    email_address = fields.Char(default=lambda self: self.env.user.login)
    is_cancelled = fields.Boolean(default=False)
    is_closed = fields.Boolean(default=False)
    is_clickable = fields.Boolean(compute="_compute_clickable")
    is_done = fields.Boolean(compute="_compute_done")
    is_new = fields.Boolean(compute="_compute_new")
    partner_id = fields.Many2one('res.partner', default=lambda self: self.env.user.partner_id.id,
                                 track_visibility='always')
    allowed_value_ids = fields.Many2many(comodel_name="res.users", compute="_compute_allowed_value_ids")
    it_helpdesk_id = fields.Many2one("seta.it.helpdesk")
    is_transfered_to_it = fields.Boolean()
    is_transfered_to_erp = fields.Boolean()

    is_in_transferred_stage = fields.Boolean(compute="_compute_transferred")

    @api.model
    def get_provinces_tickets_ids(self, user):
        province_groups = {
            'EC': "hwseta_helpdesk.group_province_ec",
            'FS': "hwseta_helpdesk.group_province_fs",
            'GP': "hwseta_helpdesk.group_province_gp",
            'KZN': "hwseta_helpdesk.group_province_kzn",
            'LP': "hwseta_helpdesk.group_province_lp",
            'MP': "hwseta_helpdesk.group_province_mp",
            'NC': "hwseta_helpdesk.group_province_nc",
            'NW': "hwseta_helpdesk.group_province_nw",
            'WC': "hwseta_helpdesk.group_province_wc",
        }

        user_province_codes = [code for code, xml_id in province_groups.items() if user.has_group(xml_id)]
        if user_province_codes:
            provinces = self.env['res.country.state'].search([
                ('code', 'in', user_province_codes)
            ])
            tickets = self.env['helpdesk.ticket'].search([
                ('province_id', 'in', provinces.ids)
            ])
            return tickets.ids
        else:
            return []

    @api.depends("team_id")
    def _compute_allowed_value_ids(self):
        users_search = self.env['res.users'].search([])
        users_ids = []
        for user in users_search:
            if user.has_group('seta_base.seta_internal'):
                users_ids.append(user.id)
        filtered_users = []
        if self.team_id:
            filtered_users = self.user_ids.ids
        else:
            filtered_users = users_ids
        for record in self:
            record.allowed_value_ids = self.env["res.users"].search([('id', 'in', filtered_users)])

    @api.depends("stage_id")
    def _compute_clickable(self):
        if self.stage_id.name == 'Done':
            self.is_clickable = False
        elif self.stage_id.name == 'Cancelled':
            self.is_clickable = False
        else:
            self.is_clickable = True

    @api.depends("stage_id")
    def _compute_done(self):
        if self.stage_id.name == 'Done':
            self.is_done = True
        else:
            self.is_done = False

    @api.depends("stage_id")
    def _compute_transferred(self):
        if self.stage_id.name == 'Transferred':
            self.is_in_transferred_stage = True
        else:
            self.is_in_transferred_stage = False

    @api.depends("stage_id")
    def _compute_new(self):
        if self.stage_id.name == 'New':
            self.is_new = True
        else:
            self.is_new = False

    @api.onchange("contact_number")
    def onchange_contact_number(self):
        if self.contact_number:
            if not self.contact_number.isnumeric() or len(self.contact_number) < 10:
                return {'warning': {'title': 'Invalid Contact Number',
                                    'message': 'Please re-enter a valid Contact Number'},
                        'value': {'contact_number': False, }}

    @api.onchange("email_address")
    def onchange_email_address(self):
        is_valid = False
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if self.email_address:
            if not (re.fullmatch(regex, self.email_address)):
                return {'warning': {'title': 'Invalid Email Address',
                                    'message': 'Please re-enter a valid Email Address'},
                        'value': {'email_address': False, }}

    @api.model
    @api.onchange('team_id', 'user_id')
    def _onchange_dominion_user_id(self):
        if self.team_id:
            if self.user_id and self.user_id.id not in self.user_ids.ids:
                self.update({
                    'user_id': False
                })

    def cancel_ticket(self):
        find_cancel_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Cancelled')]).id
        find_done_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Done')]).id
        ir_model_data = self.env['ir.model.data']
        # close_template_it_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.closed_ticket_template_it')[1]
        # close_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.closed_ticket_template')[1]
        context = self.env.context
        if self.stage_id:
            if self.stage_id.id != find_done_id:
                find_cancel = self.env['helpdesk.ticket.stage'].sudo().search([('name', '=', 'Cancelled')])
                # find_cancel.update({'mail_template_id': close_template_id})
                # self._track_template(self)
                self.stage_id = find_cancel_id
                self.is_cancelled = True
                self.send_user_mail_closed()
            if self.stage_id.id == find_done_id:
                raise UserError("You can not Cancel a ticket that is Done")

    def close_ticket(self):
        find_cancel_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Cancelled')]).id
        find_done_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Done')]).id
        ir_model_data = self.env['ir.model.data']
        # close_template_it_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.closed_ticket_template_it')[1]
        # close_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.closed_ticket_template')[1]
        context = self.env.context
        if self.stage_id:
            if self.stage_id.id != find_cancel_id:
                find_done = self.env['helpdesk.ticket.stage'].sudo().search([('name', '=', 'Done')])
                # find_done.update({'mail_template_id': close_template_id})
                # self._track_template(self)
                self.stage_id = find_done_id
                self.is_closed = True
                self.send_user_mail_closed()
            if self.stage_id.id == find_cancel_id:
                raise UserError("You can not Close a ticket that is Cancel")

    def reopen_ticket(self):
        find_cancel_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Cancelled')]).id
        find_done_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Done')]).id
        find_new_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'New')]).id
        if self.stage_id:
            if self.stage_id.id == find_done_id:
                self.stage_id = find_new_id
                self.is_closed = False
                self.is_cancelled = False
                if self.user_id and self._name == 'helpdesk.ticket':
                    self.send_user_mail()
                self.send_user_mail_reopen()
            if self.stage_id.id == find_cancel_id:
                raise UserError("You can not Re-open a ticket that is Cancel")

# @api.model
# def return_tree_view(self):
# 	return {
# 		'name': _('test'),
# 		'view_type': 'tree',
# 		'view_mode': 'tree,form',
# 		# 'view_id': self.env.ref('hwseta_helpdesk.ticket_ext_view_tree').id,
# 		'view_id': False,
# 		'views': [(self.env.ref('hwseta_helpdesk.ticket_ext_view_tree').id,'tree')],
# 		'res_model': 'helpdesk.ticket',
# 		# 'context': "{'type':'out_invoice'}",
# 		'type': 'ir.actions.act_window',
# 		'target': 'current',
# 	}


class HelpdeskTicketTeam(models.Model):
    _inherit = 'helpdesk.ticket.team'

    @api.model
    def _get_assigned_user_field(self):
        users_search = self.env['res.users'].search([])
        users = []
        for user in users_search:
            if user.has_group('seta_base.seta_internal'):
                users.append(user.id)
        return [('id', 'in', users)]

    user_ids = fields.Many2many(comodel_name='res.users', string='Members', domain=_get_assigned_user_field)

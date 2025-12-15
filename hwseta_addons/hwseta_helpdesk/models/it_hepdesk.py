from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import re
from lxml import etree
import random
import datetime
# import wdb
DEBUG = True

if DEBUG:
	import logging

	logger = logging.getLogger(__name__)


	def dbg(msg):
		logger.info(msg)
else:
	def dbg(msg):
		pass

class Category(models.Model):
	_name = 'helpdesk.it.category'
	name = fields.Char()
	# setmis_lookup = fields.Char()
	# nlrd_lookup = fields.Char()
	# django_id = fields.Char()

class RequestType(models.Model):
	_name = 'helpdesk.it.request.type'
	name = fields.Char()
	# setmis_lookup = fields.Char()
	# nlrd_lookup = fields.Char()
	# django_id = fields.Char()

class Location(models.Model):
	_name = 'helpdesk.it.location'
	name = fields.Char()

class Location(models.Model):
	_name = 'helpdesk.it.department'
	name = fields.Char()


class ItHelpdeskTicket(models.Model):

	_name = 'seta.it.helpdesk'
	_inherit = ["helpdesk.ticket", "mail.thread.cc", "mail.activity.mixin", "portal.mixin"]
	_mail_post_access = "read"

	it_team_id = fields.Many2one(
		comodel_name="it.helpdesk.ticket.team",
		string="Team",
	)
	is_it_helpdesk = fields.Boolean()
	is_transfered_to_it = fields.Boolean()
	is_transfered_to_erp = fields.Boolean()
	# related_to = fields.Char()
	due_date = fields.Datetime()
	it_category_id = fields.Many2one('helpdesk.it.category')
	request_type_id = fields.Many2one('helpdesk.it.request.type')
	location_id = fields.Many2one('helpdesk.it.location')
	department_id = fields.Many2one('helpdesk.it.department')
	urgency = fields.Selection(selection=[("0", "Low"),("1", "Medium"),("2", "High"), ("3", "Very High"),],default="1",)
	impact = fields.Selection(selection=[("0", "Low"),("1", "Medium"),("2", "High"), ("3", "Very High"),],default="1",)
	user_id = fields.Many2one(
		'res.users',
		string='Assigned user',
		track_visibility="onchange",
		index=True,
		domain="[('id', 'in', allowed_value_ids)]",
	)
	user_ids = fields.Many2many(
		comodel_name="res.users", related="it_team_id.user_ids", string="Users"
	)
	allowed_value_ids = fields.Many2many(comodel_name="res.users", compute="_compute_allowed_value_ids")
	is_transfered_to_erp = fields.Boolean()
	erp_helpdesk_id = fields.Many2one("helpdesk.ticket")
	is_in_transferred_stage = fields.Boolean(compute="_compute_transferred")
	partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")
	# number = fields.Char(string="Ticket number", default="/", readonly=True)
	is_done_it = fields.Boolean(default=False)

	# @api.depends('stage_id')
	# def _compute_is_done_it(self):

	def send_user_mail_query_it(self):
		template = self.env.ref("hwseta_helpdesk.in_query_ticket_template_it")
		template.send_mail(self.id, force_send=True)

	def send_user_mail_progress_it(self):
		template = self.env.ref("hwseta_helpdesk.in_progress_ticket_template_it")
		template.send_mail(self.id, force_send=True)

	def send_user_mail_closed_it(self):
		template = self.env.ref("hwseta_helpdesk.closed_ticket_template_it")
		template.send_mail(self.id, force_send=True)

	@api.onchange('stage_id')
	def stage_id_template(self):
		# res = super()._track_template(tracking)
		ticket = self[0]
		ir_model_data = self.env['ir.model.data']
		# close_template_it_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.closed_ticket_template_it')[1]
		# close_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.closed_ticket_template')[1]
		# in_progress_template_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.in_progress_ticket_template_it')[1]
		# in_query_template_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.in_query_ticket_template_it')[1]
		# in_new_template_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.in_new_ticket_template_it')[1]
		# in_transferred_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.in_transferred_ticket_to_erp_template_it')[1]

		context = self.env.context
		ctx = self.env.context
		# params = ctx.get('params')
		# active_model = params['model']
		active_model = ctx.get('active_model')
		model = ctx.get('params', {}).get('model', False)
		if self._name == 'seta.it.helpdesk' and not active_model:
			if self.stage_id.name in ['Done', 'Cancelled']:
				# wdb.set_trace()
				# self.stage_id.mail_template_id = close_template_it_id
				# ticket.stage_id.mail_template_id = close_template_it_id
				# self._track_template(self)
				self.send_user_mail_closed_it()

			if self.stage_id.name in ['In Progress']:
				# self.stage_id.mail_template_id = in_progress_template_id
				# self._track_template(self)
				self.send_user_mail_progress_it()

			if self.stage_id.name in ['Query']:
				# self.stage_id.mail_template_id = in_query_template_id
				# self._track_template(self)
				self.send_user_mail_query_it()

			# if self.stage_id.name in ['Transferred']:
			# 	self.stage_id.mail_template_id = in_transferred_id
			# 	self._track_template(self)

			# if self.id:
			#
			# 	if self.stage_id.name in ['New']:
			# 		self.stage_id.mail_template_id = in_new_template_id
			# 		self._track_template(self)

		# wdb.set_trace()
		# if context.get('params', {}).get('model', False) == 'seta.it.helpdesk':
		# 	#close and done it tickets
		# 	if self.stage_id.name in ['Done', 'Cancelled']:
		# 		# wdb.set_trace()
		# 		self.stage_id.mail_template_id = close_template_it_id
		# 		ticket.stage_id.mail_template_id = close_template_it_id
		# 		self._track_template(self)

	def cancel_ticket_it(self):
		find_cancel_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Cancelled')]).id
		find_done_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Done')]).id
		ticket = self[0]
		ir_model_data = self.env['ir.model.data']
		# close_template_it_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.closed_ticket_template_it')[1]
		# close_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.closed_ticket_template')[1]
		context = self.env.context
		if self.stage_id:
			if self.stage_id.id != find_done_id:
				find_cancel = self.env['helpdesk.ticket.stage'].sudo().search([('name', '=', 'Cancelled')])
				# find_cancel.update({'mail_template_id': close_template_it_id})
				# self._track_template(self)
				self.stage_id = find_cancel_id
				self.is_cancelled = True
				self.send_user_mail_closed_it()
			if self.stage_id.id == find_done_id:
				raise UserError("You can not Cancel a ticket that is Done")


	def close_ticket_it(self):
		find_cancel_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Cancelled')]).id
		find_done_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Done')]).id
		ticket = self[0]
		ir_model_data = self.env['ir.model.data']
		# close_template_it_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.closed_ticket_template_it')[1]
		if self.stage_id:
			if self.stage_id.id != find_cancel_id:
				find_done = self.env['helpdesk.ticket.stage'].sudo().search([('name', '=', 'Done')])
				# find_done.update({'mail_template_id': close_template_it_id})
				# self._track_template(self)
				self.stage_id = find_done_id
				self.is_closed = True
				self.send_user_mail_closed_it()
			if self.stage_id.id == find_cancel_id:
				raise UserError("You can not Close a ticket that is Cancel")


	# @api.model
	# def _track_template(self, tracking):
	# 	res = super()._track_template(tracking)
	# 	ticket = self[0]
	# 	ir_model_data = self.env['ir.model.data']
	# 	close_template_it_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.closed_ticket_template_it')[1]
	# 	close_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.closed_ticket_template')[1]
	# 	context = self.env.context
	# 	if context.get('params', {}).get('model', False) == 'seta.it.helpdesk':
	# 		if self.stage_id.name in ['Done', 'Cancelled']:
	# 			# wdb.set_trace()
	# 			ticket.stage_id.mail_template_id = close_template_it_id
	# 			if "stage_id" in tracking and ticket.stage_id.mail_template_id:
	# 				res["stage_id"] = (
	# 					ticket.stage_id.mail_template_id,
	# 					{
	# 						# Need to set mass_mail so that the email will always be sent
	# 						"composition_mode": "mass_mail",
	# 						# "auto_delete_message": True,
	# 						"subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
	# 							"mail.mt_note"
	# 						),
	# 						"email_layout_xmlid": "mail.mail_notification_light",
	# 					},
	# 				)
	# 			if self.stage_id.name in ['Done', 'Cancelled']:
	# 				ticket.stage_id.mail_template_id = close_template_id
	# 			else:
	# 				ticket.stage_id.mail_template_id = False
		# else:
		# 	wdb.set_trace()
		# 	if "stage_id" in tracking and ticket.stage_id.mail_template_id:
		# 		res["stage_id"] = (
		# 			ticket.stage_id.mail_template_id,
		# 			{
		# 				# Need to set mass_mail so that the email will always be sent
		# 				"composition_mode": "mass_mail",
		# 				# "auto_delete_message": True,
		# 				"subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
		# 					"mail.mt_note"
		# 				),
		# 				"email_layout_xmlid": "mail.mail_notification_light",
		# 			},
		# 		)
		# return res

	@api.depends("stage_id")
	def _compute_transferred(self):
		if self.stage_id.name == 'Transferred':
			self.is_in_transferred_stage = True
		else:
			self.is_in_transferred_stage = False



	@api.onchange('due_date')
	def onchange_due_date(self):
		if self.due_date:
			today_date = datetime.datetime.now()
			next_date = today_date + datetime.timedelta(days=1)
			if self.due_date < today_date or self.due_date < next_date:
				return {'warning': {'title': 'Invalid Due Date',
									'message': "The due date should be set to a date after today and should include an additional day to allow for investigation." + '\nPlease re-enter a valid due date'},
						'value': {'due_date': False}}
			else:
				pass


	@api.depends("it_team_id")
	def _compute_allowed_value_ids(self):
		users_search = self.env['res.users'].search([])
		users_ids = []
		for user in users_search:
			if user.has_group('hwseta_helpdesk.group_it_helpdesk_Admin'):
				users_ids.append(user.id)
		filtered_users = []
		if self.it_team_id:
			filtered_users = self.user_ids.ids
		else:
			filtered_users = users_ids
		for record in self:
			record.allowed_value_ids = self.env["res.users"].search([('id', 'in', filtered_users)])
		# wdb.set_trace()

	def send_user_mail_it(self):
		template = self.env.ref("hwseta_helpdesk.assignment_email_template_it")
		template.send_mail(self.id, force_send=True)

	def send_user_mail_it_transferred(self):
		template = self.env.ref("hwseta_helpdesk.in_transferred_ticket_to_erp_template_it")
		template.send_mail(self.id, force_send=True)

	def send_user_mail_create_it(self):
		template = self.env.ref("hwseta_helpdesk.create_ticket_template_it")
		template.send_mail(self.id, force_send=True)

	def send_user_mail_reopen_it(self):
		template = self.env.ref("hwseta_helpdesk.reopen_ticket_template_it")
		template.send_mail(self.id, force_send=True)

	def reopen_ticket_it(self):
		find_cancel_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Cancelled')]).id
		find_done_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Done')]).id
		find_new_id = self.env['helpdesk.ticket.stage'].search([('name', '=', 'New')]).id
		if self.stage_id:
			if self.stage_id.id == find_done_id:
				self.stage_id = find_new_id
				self.is_closed = False
				self.is_cancelled = False
				if self.user_id and self._name == 'seta.it.helpdesk':
					self.send_user_mail_it()
				self.send_user_mail_reopen_it()
			if self.stage_id.id == find_cancel_id:
				raise UserError("You can not Re-open a ticket that is Cancel")

	@api.model_create_multi
	def create(self, vals_list):
		user = self.env.user
		users_search = self.env['res.users'].search([])
		users_ids = []
		if user.has_group('hwseta_helpdesk.group_it_helpdesk_internal_user') and not user.has_group('hwseta_helpdesk.group_it_helpdesk_Admin'):
			for user in users_search:
				if user.has_group('hwseta_helpdesk.group_it_helpdesk_Admin'):
					users_ids.append(user.id)
			try:
				random_user_id = random.choice(users_ids)
				vals_list[0]['user_id'] = random_user_id
			except Exception:
				pass
		for vals in vals_list:
			if vals.get("number", "/") == "/":
				vals["number"] = self._prepare_ticket_number(vals)
			if vals.get("user_id") and not vals.get("assigned_date"):
				vals["assigned_date"] = fields.Datetime.now()
		res_it = super().create(vals_list)
		ctx = self._context
		# wdb.set_trace()
		# params = ctx.get('params')
		# model = params['model']
		model = ctx.get('params', {}).get('model', False)
		active_model = ctx.get('active_model')
		if self._name == 'seta.it.helpdesk' and not active_model:
		# Check if mail to the user has to be sent
			for vals in vals_list:
				if vals.get("user_id") and res_it:
					res_it.send_user_mail_it()
			res_it.send_user_mail_create_it()
		return res_it


	def write(self, vals):
		for _ticket in self:
			now = fields.Datetime.now()
			if vals.get("stage_id"):
				stage = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
				vals["last_stage_update"] = now
				if stage.closed:
					vals["closed_date"] = now
			if vals.get("user_id"):
				vals["assigned_date"] = now

		ctx = self._context
		# params = ctx.get('params')
		# model = params['model']
		model = ctx.get('params', {}).get('model', False)
		active_model = ctx.get('active_model')
		mail_user_id = []
		if self._name == 'seta.it.helpdesk' and not active_model:
			rec = self.env["seta.it.helpdesk"].browse(self.id)
			mail_user_id = rec.user_id.id
			# wdb.set_trace()
			if 'stage_id' in vals:
				stage_name = self.env['helpdesk.ticket.stage'].browse(vals["stage_id"]).name
				if stage_name in ['Done', 'Cancelled']:
					vals.update({'is_done_it': True})
				else:
					vals.update({'is_done_it': False})
				if self.stage_id.name in ['Query', 'In Progress']:
					if stage_name in ['New']:
						raise UserError("Operation Not Allowed")
		res_it = super().write(vals)
		if self._name == 'seta.it.helpdesk' and not active_model:
			if mail_user_id != self.user_id.id:
				self.send_user_mail_it()

		return res_it



class ITHelpdeskTicketTeam(models.Model):

	_inherit = 'it.helpdesk.ticket.team'

	@api.model
	def _get_assigned_user_field(self):
		users_search = self.env['res.users'].search([])
		users = []
		for user in users_search:
			if user.has_group('hwseta_helpdesk.group_it_helpdesk_Admin'):
				users.append(user.id)
		return [('id', 'in', users)]

	user_ids = fields.Many2many(comodel_name='res.users', string='Members', domain=_get_assigned_user_field)

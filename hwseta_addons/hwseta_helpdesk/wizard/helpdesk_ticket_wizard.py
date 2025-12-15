from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import datetime
import re
from ... import toolz
import logging
# import wdb
import random

_logger = logging.getLogger(__name__)
DEBUG = True
if DEBUG:
	import logging

	logger = logging.getLogger(__name__)


	def dbg(msg):
		logger.info(msg)
else:
	def dbg(msg):
		pass



bad_fields = ["mail_followers",
		              "create_uid",
		              "create_date",
		              "write_uid",
		              "write_date",
		              'id',
		              'message_follower_ids',
		              'message_has_error',
		              'message_unread_counter',
		              'message_is_follower',
		              'message_attachment_count',
		              'message_ids',
		              'message_needaction',
		              'message_has_error_counter',
		              'message_channel_ids',
		              'website_message_ids',
		              'message_partner_ids',
		              'message_unread',
		              'message_needaction_counter',
		              ]

# class ItHelpdeskTicketTransfer(models.TransientModel):
# 	_name = 'it.helpdesk.ticket.transfer'


class ItHelpdeskTicketTransfer(models.TransientModel):
	_name = 'it.helpdesk.ticket.transfer.wizard'
	_description = 'Ticket Transfer Wizard'
	_inherit = ['seta.it.helpdesk']

	is_transfered_to_it = fields.Boolean()
	default_is_it_helpdesk = fields.Boolean()
	it_helpdesk_id = fields.Many2one("seta.it.helpdesk")
	erp_helpdesk_id = fields.Many2one("helpdesk.ticket")

	@api.onchange("it_team_id")
	def _onchange_it_team_id(self):
		if self.it_team_id:
			return {'value': {'user_id': False}}
	# it_team_id = fields.Many2one(
	# 	comodel_name="it.helpdesk.ticket.team",
	# 	string="Team",
	# )
	# is_it_helpdesk = fields.Boolean()
	# # related_to = fields.Char()
	# due_date = fields.Datetime()
	# it_category_id = fields.Many2one('helpdesk.it.category')
	# request_type_id = fields.Many2one('helpdesk.it.request.type')
	# location_id = fields.Many2one('helpdesk.it.location')
	# department_id = fields.Many2one('helpdesk.it.location')
	# urgency = fields.Selection(selection=[("0", "Low"), ("1", "Medium"), ("2", "High"), ("3", "Very High"), ],
	#                            default="1", )
	# impact = fields.Selection(selection=[("0", "Low"), ("1", "Medium"), ("2", "High"), ("3", "Very High"), ],
	#                           default="1", )
	# user_id = fields.Many2one(
	# 	'res.users',
	# 	string='Assigned user',
	# 	track_visibility="onchange",
	# 	index=True,
	# 	domain="[('id', 'in', allowed_value_ids)]",
	# )
	# user_ids = fields.Many2many(
	# 	comodel_name="res.users", related="it_team_id.user_ids", string="Users"
	# )
	# allowed_value_ids = fields.Many2many(comodel_name="res.users", compute="_compute_allowed_value_ids")


	# @api.depends("it_team_id")
	# def _compute_allowed_value_ids(self):
	# 	users_search = self.env['res.users'].search([])
	# 	users_ids = []
	# 	for user in users_search:
	# 		if user.has_group('hwseta_helpdesk.group_it_helpdesk_Admin'):
	# 			users_ids.append(user.id)
	# 	filtered_users = []
	# 	if self.it_team_id:
	# 		filtered_users = self.user_ids.ids
	# 	else:
	# 		filtered_users = users_ids
	# 	for record in self:
	# 		record.allowed_value_ids = self.env["res.users"].search([('id', 'in', filtered_users)])

	# wdb.set_trace()

	def default_get(self, fields):
		these_fields = self.fields_get().keys()
		rec = super(ItHelpdeskTicketTransfer, self).default_get(fields)
		user = self.env.user
		ctx = self._context
		# wdb.set_trace()
		if "active_id" in ctx:
			active_id = ctx.get("active_id")
			ticket = self.env["helpdesk.ticket"].browse(active_id)
			ticket_tup = toolz.tuple_fixer(ticket.read()[0])
			new_stage = self.env['helpdesk.ticket.stage'].search([('name', '=', 'New')], limit=1)
			for field in ticket_tup.keys():
				if field in these_fields and field not in bad_fields:
					rec.update({field: ticket_tup[field]})
			rec.update(
				{
					"erp_helpdesk_id": ticket.id,
					"is_transfered_to_it": True,
					"user_id": False,
					'stage_id': new_stage.id,

				})

		# wdb.set_trace()
		# if org:
		# 	org_tup = toolz.tuple_fixer(org.read()[0])
		# 	for field in org_tup.keys():
		# 		if field in these_fields:
		# 			rec.update({field: org_tup[field]})
		# 	# partner = lnr.partner_id
		# 	rec.update(
		# 		{
		# 			"organisation_id": org.id,
		# 			# "person_id": lnr.id,
		# 			# 'designation_id':des_id,
		# 		}
		# 	)
		else:
			rec = rec
		return rec

	# def send_user_mail_it(self):
	# 	template = self.env.ref("hwseta_helpdesk.in_transferred_ticket_to_erp_template_it")
	# 	template.send_mail(self.id, force_send=True)

	# def send_user_mail_it(self):
	# 	template = self.env.ref("hwseta_helpdesk.assignment_email_template_it")
	# 	template.send_mail(self.id, force_send=True)

	def action_transfer_to_it(self):
		vals = self.read()[0]
		vals = toolz.tuple_fixer(vals)
		dbg(vals)
		# here we remove helper fields from vals because they don't belong in the transaction.
		# vals.update({'ref': self.env['ir.sequence'].sudo().next_by_code('organisation.transaction')})
		heldesk_it_fields = self.env["seta.it.helpdesk"]._fields
		new_vals = {}

		for key, value in vals.items():
			if key in list(heldesk_it_fields.keys()) and key not in bad_fields:
				new_vals.update({key: value})
		# del vals[key]
		# wdb.set_trace()
		transferred = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Transferred')])
		ctx = self._context
		active_id = ctx.get("active_id")
		ticket = self.env["helpdesk.ticket"].browse(active_id)
		ticket.update({'stage_id': transferred.id})
		# wdb.set_trace()
		create_ticket = self.env['seta.it.helpdesk'].create(new_vals)
		if create_ticket.user_id:
			create_ticket.send_user_mail_it()
		# create_orgs.update({'state': 'submitted'})
		ticket.update({'it_helpdesk_id': create_ticket.id})
		# wdb.set_trace()
		#
		try:
			ticket.send_user_mail_it_transferred()
		except:
			pass
		return create_ticket





class HelpdeskTicketTransfer(models.TransientModel):
	_name = 'helpdesk.ticket.transfer.wizard'
	_description = 'Ticket Transfer Wizard'

	_inherit = ['seta.it.helpdesk', 'helpdesk.ticket']


	is_transfered_to_erp = fields.Boolean()
	allowed_value_ids = fields.Many2many(comodel_name="res.users", compute="_compute_allowed_value_ids")
	user_ids = fields.Many2many(
		comodel_name="res.users", related="team_id.user_ids", string="Users"
	)

	it_helpdesk_id = fields.Many2one("seta.it.helpdesk")
	erp_helpdesk_id = fields.Many2one("helpdesk.ticket")

	@api.onchange("team_id")
	def _onchange_team_id(self):
		if self.it_team_id:
			return {'value': {'user_id': False}}
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

	def default_get(self, fields):
		these_fields = self.fields_get().keys()
		rec = super(HelpdeskTicketTransfer, self).default_get(fields)
		user = self.env.user
		ctx = self._context
		# wdb.set_trace()
		if "active_id" in ctx:
			active_id = ctx.get("active_id")
			ticket = self.env["seta.it.helpdesk"].browse(active_id)
			ticket_tup = toolz.tuple_fixer(ticket.read()[0])
			new_stage = self.env['helpdesk.ticket.stage'].search([('name', '=', 'New')], limit=1)
			for field in ticket_tup.keys():
				if field in these_fields and field not in bad_fields:
					rec.update({field: ticket_tup[field]})
			rec.update(
					{
						"it_helpdesk_id": ticket.id,
						"is_transfered_to_erp": True,
						"stage_id": new_stage.id,
					})

			# wdb.set_trace()
			# if org:
			# 	org_tup = toolz.tuple_fixer(org.read()[0])
			# 	for field in org_tup.keys():
			# 		if field in these_fields:
			# 			rec.update({field: org_tup[field]})
			# 	# partner = lnr.partner_id
			# 	rec.update(
			# 		{
			# 			"organisation_id": org.id,
			# 			# "person_id": lnr.id,
			# 			# 'designation_id':des_id,
			# 		}
			# 	)
		else:
			rec = rec
		return rec


	def action_transfer_to_erp(self):
		vals = self.read()[0]
		vals = toolz.tuple_fixer(vals)
		# wdb.set_trace()
		dbg(vals)
		# here we remove helper fields from vals because they don't belong in the transaction.
		# vals.update({'ref': self.env['ir.sequence'].sudo().next_by_code('organisation.transaction')})
		heldesk_erp_fields = self.env["helpdesk.ticket"]._fields
		new_vals = {}

		for key, value in vals.items():
			if key in list(heldesk_erp_fields.keys()) and key not in bad_fields:
				new_vals.update({key:value})
		transferred = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Transferred')])
		ctx = self._context
		active_id = ctx.get("active_id")
		ticket = self.env["seta.it.helpdesk"].browse(active_id)
		ticket.update({'stage_id': transferred.id})
		create_ticket = self.env['helpdesk.ticket'].create(new_vals)
		if create_ticket.user_id:
			create_ticket.send_user_mail()
		# create_orgs.update({'state': 'submitted'})
		ticket.update({'erp_helpdesk_id': create_ticket.id})
		try:
			ticket.send_user_mail_it_transferred()
		except:
			pass
		return create_ticket

# class OrganisationWizard(models.TransientModel):
# 	_name = 'organisation.wizard'
# 	_description = "Non Levy Paying Organisation Wizard"
#
# 	# _inherit = ['mail.thread', 'mail.activity.mixin']
#
# 	@api.model
# 	def default_get(self, fields):
# 		record_ids = self._context.get('active_ids')
# 		result = super(OrganisationWizard, self).default_get(fields)
#
# 		# if record_ids:
# 		# 	if 'opportunity_ids' in fields:
# 		# 		opp_ids = self.env['crm.lead'].browse(record_ids).filtered(lambda opp: opp.probability < 100).ids
# 		# 		result['opportunity_ids'] = [(6, 0, opp_ids)]
#
# 		return result
#
# 	def _partnerID(self):
# 		context = dict(self._context or {})
# 		active_ids = context.get('active_ids', []) or []
# 		return active_ids[0]
#
# 	# verified required field Mohavia
# 	state = fields.Selection([
# 		('draft', 'Draft'),
# 		('sdp_submitted', 'SDP Submitted'),
# 		('sdp_approved', 'SDP Approved'),
# 		('submitted', 'Finance Submitted'),
# 		('approved', 'Approved'),
# 		('rejected', 'Rejected'),
# 	], readonly=True, default='draft', string='State')
# 	ref = fields.Char()
# 	alt_sdl_prefix = fields.Selection([('prefix_N', 'N'), ('prefix_g', 'G'), ('prefix_T', 'T'),],
# 	                                  size=10,
# 	                                  string='SDL number prefix')
# 	is_employer = fields.Boolean(string="organisation")
# 	employer_sdl_no = fields.Char(size=10, string='SDL No.')
# 	employer_site_no = fields.Char(size=10, string='Site No.')
# 	employer_company_name = fields.Char(string="Name")
# 	employer_trading_name = fields.Char(string='Trading Name', track_visibility='onchange')
# 	employer_registration_number = fields.Char(string="Registration Number")
# 	employer_seta_id = fields.Many2one('seta.id', string='SETA ID')
# 	empl_sic_code = fields.Many2one('sic.code', string='SIC Code', track_visibility='onchange')
# 	# empl_sic_code_id = fields.Char('SIC Description', track_visibility='onchange')
#
# 	# new fields
# 	employer_approval_status_id = fields.Many2one("employer.approval.status.id")
# 	employer_approval_status_start_date = fields.Date()
# 	employer_approval_status_end_date = fields.Date()
# 	employer_approval_status_num = fields.Char()
# 	# datestamp = fields.Date(default=datetime.datetime.now())
# 	main_sdl_no = fields.Char(size=10, string='SDL No.')
#
# 	# employer contact detail
# 	website = fields.Char()
# 	employer_phone_number = fields.Char(size=10, string='Phone Number')
# 	employer_fax_number = fields.Char(size=10, string='Fax Number')
#
# 	# employer contact person detail
# 	title = fields.Selection([('mr', 'Mr'), ('mrs', 'Mrs'), ('ms', 'Ms'), ('miss', 'Miss'),('dr', 'Dr'), ('prof', 'Prof')],)
# 	function = fields.Char(string='Job Position')
# 	employer_contact_name = fields.Char(string='')
# 	employer_contact_email_address = fields.Char()
# 	employer_contact_phone_number = fields.Char(size=10, string='Phone Number')
# 	employer_contact_cell_number = fields.Char(string='Mobile', size=10)
#
# 	# employer Physical address
# 	employer_physical_address_1 = fields.Char(string='Physical Address 1')
# 	employer_physical_address_2 = fields.Char(string='Physical Address 2')
# 	employer_physical_address_3 = fields.Char(string='Physical Address 3')
# 	employer_physical_address_code = fields.Char(string='Physical Address Code')
# 	province_code = fields.Many2one('res.country.state', string='Physical Province Code',
# 	                                track_visibility='onchange')
# 	country_code = fields.Many2one('res.country', string='Physical Country Code', track_visibility='onchange')
# 	latitude_degree = fields.Char(size=3)
# 	latitude_minutes = fields.Char(size=2)
# 	latitude_seconds = fields.Char(size=6)
# 	longitude_degree = fields.Char(size=2)
# 	longitude_minutes = fields.Char(size=2)
# 	longitude_seconds = fields.Char(size=6)
# 	# not sure if needeed
# 	suburb_id = fields.Many2one('res.suburb')
# 	# state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
# 	#                            domain="[('country_id', '=?', country_id)]")
#
# 	# country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
#
# 	# employer Postal address
# 	same_as_physical = fields.Boolean(string='Same As Physical Address')
# 	employer_postal_address_1 = fields.Char(string='Postal Address 1')
# 	employer_postal_address_2 = fields.Char(string='Postal Address 2')
# 	employer_postal_address_3 = fields.Char(string='Postal Address 3')
# 	employer_postal_address_code = fields.Char(string='Postal Address Code')
#
# 	# needed fields
#
# 	emp_government = fields.Boolean('Government')
# 	emp_levy_paying = fields.Boolean('Levy Paying')
# 	emp_university = fields.Boolean('University (CHE)')
# 	emp_non_levy_paying = fields.Boolean('Non Levy Paying')
# 	emp_tvet_college = fields.Boolean('TVET College (DHET)')
# 	emp_exempt = fields.Boolean('Levy Exempt')
# 	emp_other_group = fields.Boolean('Other')
# 	emp_ngo_npo = fields.Boolean('NGO/NPO')
# 	emp_cbo = fields.Boolean('CBO')
# 	emp_fbo = fields.Boolean('FBO')
# 	emp_section = fields.Boolean('Section 21')
# 	emp_other_group_info = fields.Char(size=70)
# 	emp_health = fields.Boolean('Health')
# 	emp_walfare = fields.Boolean('Welfare')
# 	emp_other = fields.Boolean('Other')
# 	emp_other_info = fields.Char(size=70)
# 	total_annual_payroll = fields.Float('Total Anual Payroll')
# 	organisation_size = fields.Selection(
# 		[('small', 'Small (0-49)'), ('medium', 'Medium (50-149)'), ('large', 'Large (150+)')],
# 		string='Organisation Size')
# 	partnership = fields.Selection([('private', 'Private'), ('public', 'Public'), ('private_public', 'Private Public')],
# 	                               string='Partnership')
# 	employees_count = fields.Integer(string='Employees as per Employment Profile')
# 	# organisation_document_file = fields.Many2one('ir.attachment', string='Organization Document File')
# 	doc_upload_ids = fields.Many2many('document.upload', string='Document Uploads')
# 	# organisation_document_file = fields.Many2one('ir.attachment', string='Organization Document File *')
# 	# doc_upload_id = fields.One2many('document.upload', string='Document Uploads')
# 	levy_exempt_certificate = fields.Many2one('ir.attachment', string='Levy Exempt Certificate')
# 	npo_certificate = fields.Many2one('ir.attachment', string='NPO Certificate ')
# 	bbee_certificate = fields.Many2one('ir.attachment', string='B-BEE Certificate')
#
# 	# not sure fields
#
# 	# imported_updated_flg = fields.Boolean()
# 	# record_updated_flg = fields.Boolean(default=True)
#
# 	# emp_reg_number_type = fields.Char()
# 	emp_reg_number_type = fields.Selection(
# 		[('cipro_number', 'Cipro Number'), ('comp_reg_no', 'Company Registration Number')],
# 		string='Registration Number Type')
#
#
# 	vendor = fields.Char(string="Vendor")
# 	# employer_registration_number = fields.Char(string="Registration Number", default=records_init)
#
# 	employer_vat_number = fields.Char(string="Vat Number")
# 	# site_no = fields.Char()
# 	# mobile_phone = fields.Char()
# 	mandatory_account = fields.Many2one('organisation.bank.account')
# 	discretionary_account = fields.Many2one('organisation.bank.account')
# 	comments = fields.Text(string='Comments', track_visibility='onchange')
# 	type_of_employer = fields.Many2one('employer.type', string='Type of Employer')
# 	mand_grant_banking_details = fields.Many2one('ir.attachment', 'Mandatory Grant Banking Details')
# 	disc_grant_banking_details = fields.Many2one('ir.attachment', 'Discretionary Grant Banking Details')
#
# 	suburb = fields.Char(size=70, string='Suburb')
#
# 	# employees_count = fields.Integer(string='Employees as per Employment Profile')
#
# 	parent_employer_id = fields.Many2one('organisation.master', string='Parent Employer',
# 	                                     domain=[('employer', '=', True)])
# 	child_employer_ids = fields.One2many('organisation.child', 'parent_id', string='Child Organisations')
# 	# todo: below is redundant?
# 	# child_emp_ids = fields.One2many('res.partner', 'parent_employer_id', string='Child Organisations')
# 	# not needed
# 	# django_id = fields.Char()
# 	# todo: add back when going in with finance
# 	# property_account_payable_id = fields.Many2one('account.account',
# 	#                                               string="Account Payable")
# 	# property_account_receivable_id = fields.Many2one('account.account',
# 	#                                                  string="Account Recevable",
# 	#                                                  )
#
# 	# bank_ids = fields.Many2many('organisation.bank.account','bank_partner_rel','partner_id','bank_id', string='Banks')
# 	# bank_ids = fields.Many2many('organisation.bank.account', string='Banks')
# 	bank_id = fields.Many2one('res.bank', string='Bank')
# 	# todo: below redundant
# 	# partner_id = fields.Many2one('res.partner', index=True,
# 	#                              domain=['|', ('is_employer', '=', True)], default=_partnerID, required=False)
# 	# todo: add back when doing wsp
# 	# wsp_submission_ids = fields.One2many('wsp.submission.track', 'employer_id', string='WSP Submissions')
# 	# todo: add back later when we find teh cats we need
# 	# category_id = fields.Many2many('res.partner.category', column1='partner_id',
# 	#                                column2='category_id', string='Tags')
# 	currency_id = fields.Char()
#
# 	lang = fields.Char()
# 	# todo: find out what needs doing here (are we gonna use better sdf linking?)
# 	# sdf_tracking_ids = fields.One2many('sdf.tracking', 'partner_id', string='SDF tracking')
#
# 	city = fields.Char(string='City')
#
# 	# todo: check if redundant
# 	# partner_user_rel_ids = fields.One2many('partner.user.rel', 'rel_id', string='Rel')
#
# 	# fields not needed
#
# 	# same_as_home = fields.Boolean(string='Same As Home Address')
# 	# person_home_suburb = fields.Many2one('res.suburb', string='Home Suburb')
# 	# person_home_city = fields.Many2one('res.city', string='Home City', track_visibility='onchange')
# 	#
# 	# person_suburb = fields.Many2one('res.suburb', string='Suburb')
# 	# person_postal_suburb = fields.Many2one('res.suburb', string='Postal Suburb')
# 	# person_home_address_1 = fields.Char(string='Home Address 1', track_visibility='onchange', size=50)
# 	# person_home_address_2 = fields.Char(string='Home Address 2', track_visibility='onchange', size=50)
# 	# person_home_address_3 = fields.Char(string='Home Address 3', track_visibility='onchange', size=50)
# 	# person_postal_address_1 = fields.Char(string='Postal Address 1', track_visibility='onchange', size=50)
# 	# person_postal_address_2 = fields.Char(string='Postal Address 2', track_visibility='onchange', size=50)
# 	# person_postal_city = fields.Many2one('res.city', string='Postal City', track_visibility='onchange')
# 	# person_postal_zip = fields.Char(string='Postal Zip', track_visibility='onchange')
# 	# person_home_zip = fields.Char(string='Home Zip', track_visibility='onchange')
# 	# person_cell_phone_number = fields.Char(string='Cell Phone Number', track_visibility='onchange', size=10)
# 	# person_postal_address_3 = fields.Char(string='Postal Address 3', track_visibility='onchange', size=50)
# 	# person_postal_province_code = fields.Many2one('res.country.state', string='Postal Province Code',
# 	#                                               track_visibility='onchange')
# 	# person_home_province_code = fields.Many2one('res.country.state', string='Home Province Code',
# 	#                                             track_visibility='onchange')
# 	# postal_municipality = fields.Many2one('res.municipality', string='Postal Municipality')
# 	#
# 	# physical_municipality = fields.Many2one('res.municipality', string='Physical Municipality')
# 	# country_postal = fields.Many2one('res.country', string='Postal Country', track_visibility='onchange')
# 	# country_code_physical = fields.Many2one('res.country', string='Physical Country Code', track_visibility='onchange')
# 	#
# 	# country_home = fields.Many2one('res.country', string='Home Country', track_visibility='onchange')
# 	vat = fields.Char(string='VAT No.')
# 	def action_submit(self):
# 		vals = self.read()[0]
# 		vals = toolz.tuple_fixer(vals)
# 		dbg(vals)
# 		# here we remove helper fields from vals because they don't belong in the transaction.
# 		vals.update({'ref': self.env['ir.sequence'].sudo().next_by_code('organisation.transaction')})
# 		# raise Warning(vals)
# 		# if "organisation_ids" in vals:
# 		# 	organisation_vals = []
# 		# 	for org in self.organisation_ids:
# 		# 		org_val = org.read()[0]
# 		# 		org_val = toolz.tuple_fixer(org_val)
# 		# 		del org_val["wiz_id"]
# 		# 		del org_val["wiz_id"]
# 		# 		dbg(org_val)
# 		# 		organisation_vals.append((0, 0, org_val))
# 		# 	del vals["organisation_ids"]
# 		# 	vals.update({"organisation_ids": organisation_vals})
# 		create_orgs = self.env['organisation.transaction'].create(vals)
# 		create_orgs.update({'state': 'submitted'})
# 		return create_orgs

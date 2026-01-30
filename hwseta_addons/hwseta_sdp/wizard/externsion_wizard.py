from openerp import models, fields, api, _
from datetime import datetime
from openerp.exceptions import Warning
import calendar
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import base64
import cStringIO
from openerp import tools
from openerp.tools.translate import _
import xlrd
import xlsxwriter
import re
import unicodedata
import xlwt

class WspExtensionRequest(models.TransientModel):
	_name = 'wsp.extension.request'
	_description = 'Wsp Extension Request'

	extension_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	extension_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	extension_reason_comment = fields.Text(string='Comments / Reasons')
	extension_verify_reason_comment = fields.Text(string='Comments / Reasons')
	extension_approve_reason_comment = fields.Text(string='Comments / Reasons')
	extension_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_extension = fields.Boolean(string='Allow Extension')
	sdf_id = fields.Many2one(
		'hr.employee', string='SDF', domain="[('is_sdf','=',True)]")
	user_id = fields.Many2one(
		'res.users', string='Current User', default=lambda self: self.env.user)
	current_user_forbidden = fields.Boolean()
	employer_id = fields.Many2one(
		'res.partner', string='Employer', domain="[('employer','=',True)]")
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	wsp_start_period = fields.Date(
		string='WSP Start Period')
	scheme_year_id = fields.Many2one('scheme.year','Scheme Year')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	start_period = fields.Date(
		string='WSP Submission Start Date')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	allow_extension = fields.Boolean(string='Allow Extension')
	show_extension_date = fields.Boolean(string='Show Extension')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	request_extension_date = fields.Date(string='Request Extension Date')
	approve_extension_date = fields.Date(string='Approve Extension Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	extension_date = fields.Date(string='WSP Extension Date')
	wsp_id =  fields.Many2one('wsp.plan')


	@api.one
	def extension_validate(self):
		if self.wsp_id and self.extension_reason_comment:
			self.wsp_id.extension_doc_statement = self.extension_doc_statement			
			self.wsp_id.extension_reason_comment = self.extension_reason_comment
			self.wsp_id.allow_resubmit_extension = False
			self.wsp_id.action_request_for_extension()

	_defaults = {'wsp_id': lambda self, cr, uid, context: context.get('wsp_id', False), }
	
class WspExtensionRequest(models.TransientModel):
	_name = 'wsp.extension.resubmit'
	_description = 'Wsp Extension Re-Submit'

	extension_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	extension_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	extension_reason_comment = fields.Text(string='Comments / Reasons')
	extension_verify_reason_comment = fields.Text(string='Comments / Reasons')
	extension_approve_reason_comment = fields.Text(string='Comments / Reasons')
	extension_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_extension = fields.Boolean(string='Allow Extension')
	sdf_id = fields.Many2one(
		'hr.employee', string='SDF', domain="[('is_sdf','=',True)]")
	user_id = fields.Many2one(
		'res.users', string='Current User', default=lambda self: self.env.user)
	current_user_forbidden = fields.Boolean()
	employer_id = fields.Many2one(
		'res.partner', string='Employer', domain="[('employer','=',True)]")
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	wsp_start_period = fields.Date(
		string='WSP Start Period')
	scheme_year_id = fields.Many2one('scheme.year','Scheme Year')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	start_period = fields.Date(
		string='WSP Submission Start Date')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	allow_extension = fields.Boolean(string='Allow Extension')
	show_extension_date = fields.Boolean(string='Show Extension')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	request_extension_date = fields.Date(string='Request Extension Date')
	approve_extension_date = fields.Date(string='Approve Extension Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	extension_date = fields.Date(string='WSP Extension Date')	
	wsp_ext_id =  fields.Many2one('wsp.extension')
	wsp_id = fields.Many2one(related="wsp_ext_id.wsp_plan_id", string='WSP Plan')
    
	


	@api.one
	def extension_validate(self):
		if self.wsp_id and self.extension_reason_comment:
			self.wsp_ext_id.extension_doc_statement = self.extension_doc_statement			
			self.wsp_ext_id.extension_reason_comment = self.extension_reason_comment			
			self.wsp_ext_id.extension_state = 'requested'	
			self.wsp_id.extension_doc_statement = self.extension_doc_statement			
			self.wsp_id.extension_reason_comment = self.extension_reason_comment
			self.wsp_id.allow_resubmit_extension = False
			self.wsp_id.action_resubmit_for_extension()

	_defaults = {'wsp_ext_id': lambda self, cr, uid, context: context.get('wsp_ext_id', False), }
	

class WspExtensionVerify(models.TransientModel):
	_name = 'wsp.extension.verify'
	_description = 'Wsp Extension Verificacation'

	extension_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	extension_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	extension_reason_comment = fields.Text(string='Comments / Reasons')
	extension_verify_reason_comment = fields.Text(string='Comments / Reasons')
	extension_approve_reason_comment = fields.Text(string='Comments / Reasons')
	extension_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_extension = fields.Boolean(string='Allow Extension')
	sdf_id = fields.Many2one(
		'hr.employee', string='SDF', domain="[('is_sdf','=',True)]")
	user_id = fields.Many2one(
		'res.users', string='Current User', default=lambda self: self.env.user)
	current_user_forbidden = fields.Boolean()
	employer_id = fields.Many2one(
		'res.partner', string='Employer', domain="[('employer','=',True)]")
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	wsp_start_period = fields.Date(
		string='WSP Start Period')
	scheme_year_id = fields.Many2one('scheme.year','Scheme Year')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	start_period = fields.Date(
		string='WSP Submission Start Date')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	allow_extension = fields.Boolean(string='Allow Extension')
	show_extension_date = fields.Boolean(string='Show Extension')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	request_extension_date = fields.Date(string='Request Extension Date')
	approve_extension_date = fields.Date(string='Approve Extension Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	extension_date = fields.Date(string='WSP Extension Date')	
	wsp_ext_id =  fields.Many2one('wsp.extension')
	wsp_id = fields.Many2one(related="wsp_ext_id.wsp_plan_id", string='WSP Plan')
    
	


	@api.one
	def extension_validate(self):
		if self.wsp_id and self.extension_verify_reason_comment:
			# self.wsp_ext_id.extension_doc_statement = self.extension_doc_statement			
			self.wsp_ext_id.extension_verify_reason_comment = self.extension_verify_reason_comment
			self.wsp_ext_id.extension_verified_by = self.user_id 
			self.wsp_ext_id.extension_state = 'verified' 
			self.wsp_id.extension_verify_reason_comment = self.extension_verify_reason_comment
			self.wsp_id.extension_verified_by = self.user_id
			self.wsp_id.allow_resubmit_extension = False
			self.wsp_id.action_verify_for_extension()

	_defaults = {'wsp_ext_id': lambda self, cr, uid, context: context.get('wsp_ext_id', False), }
	

class WspExtensionApproval(models.TransientModel):
	_name = 'wsp.extension.approval'
	_description = 'Wsp Extension Approval'

	extension_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	extension_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	extension_reason_comment = fields.Text(string='Comments / Reasons')
	extension_verify_reason_comment = fields.Text(string='Comments / Reasons')
	extension_approve_reason_comment = fields.Text(string='Comments / Reasons')
	extension_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_extension = fields.Boolean(string='Allow Extension')
	sdf_id = fields.Many2one(
		'hr.employee', string='SDF', domain="[('is_sdf','=',True)]")
	user_id = fields.Many2one(
		'res.users', string='Current User', default=lambda self: self.env.user)
	current_user_forbidden = fields.Boolean()
	employer_id = fields.Many2one(
		'res.partner', string='Employer', domain="[('employer','=',True)]")
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	wsp_start_period = fields.Date(
		string='WSP Start Period')
	scheme_year_id = fields.Many2one('scheme.year','Scheme Year')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	start_period = fields.Date(
		string='WSP Submission Start Date')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	allow_extension = fields.Boolean(string='Allow Extension')
	show_extension_date = fields.Boolean(string='Show Extension')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	request_extension_date = fields.Date(string='Request Extension Date')
	approve_extension_date = fields.Date(string='Approve Extension Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	extension_date = fields.Date(string='WSP Extension Date')		
	wsp_ext_id =  fields.Many2one('wsp.extension')
	wsp_id = fields.Many2one(related="wsp_ext_id.wsp_plan_id", string='WSP Plan')
    
	


	@api.one
	def extension_validate(self):
		if self.wsp_id and self.extension_approve_reason_comment:
			# self.wsp_ext_id.extension_doc_statement = self.extension_doc_statement			
			self.wsp_ext_id.extension_approve_reason_comment = self.extension_approve_reason_comment
			self.wsp_ext_id.extension_approved_by = self.user_id 
			self.wsp_ext_id.extension_state = 'approved' 
			self.wsp_id.extension_approve_reason_comment = self.extension_approve_reason_comment
			self.wsp_id.extension_approved_by = self.user_id
			self.wsp_id.allow_resubmit_extension = False
			self.wsp_id.action_approve_for_extension()

	_defaults = {'wsp_ext_id': lambda self, cr, uid, context: context.get('wsp_ext_id', False), }
	
	

class WspExtensionReject(models.TransientModel):
	_name = 'wsp.extension.reject'
	_description = 'Wsp Extension Rejection'

	extension_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	extension_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	extension_reason_comment = fields.Text(string='Comments / Reasons')
	extension_verify_reason_comment = fields.Text(string='Comments / Reasons')
	extension_approve_reason_comment = fields.Text(string='Comments / Reasons')
	extension_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_extension = fields.Boolean(string='Allow Extension')
	sdf_id = fields.Many2one(
		'hr.employee', string='SDF', domain="[('is_sdf','=',True)]")
	user_id = fields.Many2one(
		'res.users', string='Current User', default=lambda self: self.env.user)
	current_user_forbidden = fields.Boolean()
	employer_id = fields.Many2one(
		'res.partner', string='Employer', domain="[('employer','=',True)]")
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	fiscal_year = fields.Many2one(
		'account.fiscalyear', string='Financial Year')
	wsp_start_period = fields.Date(
		string='WSP Start Period')
	scheme_year_id = fields.Many2one('scheme.year','Scheme Year')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	start_period = fields.Date(
		string='WSP Submission Start Date')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	allow_extension = fields.Boolean(string='Allow Extension')
	show_extension_date = fields.Boolean(string='Show Extension')
	extension_allowed = fields.Boolean(string='Extension Allowed')
	request_extension_date = fields.Date(string='Request Extension Date')
	approve_extension_date = fields.Date(string='Approve Extension Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	extension_date = fields.Date(string='WSP Extension Date')		
	wsp_ext_id =  fields.Many2one('wsp.extension')
	wsp_id = fields.Many2one(related="wsp_ext_id.wsp_plan_id", string='WSP Plan')
    
	


	@api.one
	def extension_validate(self):
		if self.wsp_id and self.extension_reject_reason_comment:
			# self.wsp_ext_id.extension_doc_statement = self.extension_doc_statement			
			self.wsp_ext_id.extension_reject_reason_comment = self.extension_approve_reason_comment
			self.wsp_ext_id.extension_rejected_by = self.user_id 
			self.wsp_ext_id.extension_state = 'rejected' 
			self.wsp_id.extension_approve_reason_comment = self.extension_approve_reason_comment
			self.wsp_id.extension_approved_by = self.user_id
			self.wsp_id.allow_resubmit_extension = False
			self.wsp_id.action_reject_for_extension()

	_defaults = {'wsp_ext_id': lambda self, cr, uid, context: context.get('wsp_ext_id', False), }
	
	@api.one
	def extension_validate_resubmit(self):
		if self.wsp_id and self.extension_reject_reason_comment:
			self.wsp_ext_id.extension_reject_reason_comment = self.extension_approve_reason_comment
			self.wsp_ext_id.extension_rejected_by = self.user_id
			self.wsp_ext_id.extension_state = 'resubmit'
			self.wsp_ext_id.allow_resubmit_extension = True				
			self.wsp_id.extension_doc_statement = self.extension_doc_statement			
			self.wsp_id.extension_reject_reason_comment = self.extension_reject_reason_comment
			self.wsp_id.extension_rejected_by = self.user_id
			self.wsp_id.allow_resubmit_extension = True			
			self.wsp_id.action_reject_resubmit_for_extension()

	_defaults = {'wsp_ext_id': lambda self, cr, uid, context: context.get('wsp_ext_id', False), }
	
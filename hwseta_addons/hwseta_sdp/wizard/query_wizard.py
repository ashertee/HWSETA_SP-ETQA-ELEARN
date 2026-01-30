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
# import wdb as wdb

DEBUG = True

if DEBUG:
	import logging

	logger = logging.getLogger(__name__)


	def dbg(msg):
		logger.info(msg)
else:
	def dbg(msg):
		pass

class WspQueryRequest(models.TransientModel):
	_name = 'wsp.query.request'
	_description = 'Wsp Query Request'

	query_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	query_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	query_reason_comment = fields.Text(string='Comments / Reasons')
	query_verify_reason_comment = fields.Text(string='Comments / Reasons')
	query_approve_reason_comment = fields.Text(string='Comments / Reasons')
	query_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	query_allowed = fields.Boolean(string='Query Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_query = fields.Boolean(string='Allow Query')
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
	allow_query = fields.Boolean(string='Allow Query')
	show_query_date = fields.Boolean(string='Show Query')
	query_allowed = fields.Boolean(string='Query Allowed')
	request_query_date = fields.Date(string='Request Query Date')
	approve_query_date = fields.Date(string='Approve Query Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	query_date = fields.Date(string='WSP Query Date')
	wsp_id =  fields.Many2one('wsp.plan')


	@api.one
	def query_validate(self):
		# dbg('wsp id '+str(self.wsp_id))
		
		if self.wsp_id :
			# dbg('state '+str(self.state))
			self.wsp_id.query_doc_statement = self.query_doc_statement			
			self.wsp_id.query_reason_comment = self.query_reason_comment
			self.wsp_id.query_comments = self.query_reason_comment
			self.wsp_id.allow_resubmit_query = False
			# self.wsp_id.before_query_state = self.wsp_id.state
			# self.wsp_id.wsp_query_id = self.wsp_query_id
			self.wsp_id.send_query_email()
			self.wsp_id.action_request_for_query()
			
			# self.wsp_id.write({'before_query_state':self.state})


	_defaults = {'wsp_id': lambda self, cr, uid, context: context.get('wsp_id', False), }
	
class WspQueryRequest(models.TransientModel):
	_name = 'wsp.query.resubmit'
	_description = 'Wsp Query Re-Submit'

	query_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	query_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	query_reason_comment = fields.Text(string='Comments / Reasons')
	query_verify_reason_comment = fields.Text(string='Comments / Reasons')
	query_approve_reason_comment = fields.Text(string='Comments / Reasons')
	query_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	query_allowed = fields.Boolean(string='Query Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_query = fields.Boolean(string='Allow Query')
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
	allow_query = fields.Boolean(string='Allow Query')
	show_query_date = fields.Boolean(string='Show Query')
	query_allowed = fields.Boolean(string='Query Allowed')
	request_query_date = fields.Date(string='Request Query Date')
	approve_query_date = fields.Date(string='Approve Query Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	query_date = fields.Date(string='WSP Query Date')	
	wsp_query_id =  fields.Many2one('wsp.query')
	wsp_id = fields.Many2one(related="wsp_query_id.wsp_plan_id", string='WSP Plan')
	
	


	@api.one
	def query_validate(self):
		if self.wsp_id :
			self.wsp_query_id.query_doc_statement = self.query_doc_statement			
			self.wsp_query_id.query_reason_comment = self.query_reason_comment			
			self.wsp_query_id.query_state = 'requested'	
			self.wsp_id.wsp_query_id = self.wsp_query_id
			self.wsp_id.query_doc_statement = self.query_doc_statement			
			self.wsp_id.query_reason_comment = self.query_reason_comment
			self.wsp_id.allow_resubmit_query = False
			self.wsp_id.action_resubmit_for_query()

	_defaults = {'wsp_query_id': lambda self, cr, uid, context: context.get('wsp_query_id', False), }
	

class WspQueryVerify(models.TransientModel):
	_name = 'wsp.query.verify'
	_description = 'Wsp Query Verificacation'

	query_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	query_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	query_reason_comment = fields.Text(string='Comments / Reasons')
	query_verify_reason_comment = fields.Text(string='Comments / Reasons')
	query_approve_reason_comment = fields.Text(string='Comments / Reasons')
	query_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	query_allowed = fields.Boolean(string='Query Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_query = fields.Boolean(string='Allow Query')
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
	allow_query = fields.Boolean(string='Allow Query')
	show_query_date = fields.Boolean(string='Show Query')
	query_allowed = fields.Boolean(string='Query Allowed')
	request_query_date = fields.Date(string='Request Query Date')
	approve_query_date = fields.Date(string='Approve Query Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	query_date = fields.Date(string='WSP Query Date')	
	wsp_query_id =  fields.Many2one('wsp.query')
	wsp_id = fields.Many2one(related="wsp_query_id.wsp_plan_id", string='WSP Plan')
	
	


	@api.one
	def query_validate(self):
		if self.wsp_id and self.query_verify_reason_comment:
			# self.wsp_query_id.query_doc_statement = self.query_doc_statement			
			self.wsp_query_id.query_verify_reason_comment = self.query_verify_reason_comment
			self.wsp_query_id.query_verified_by = self.user_id 
			self.wsp_query_id.query_state = 'verified' 
			self.wsp_id.wsp_query_id = self.wsp_query_id
			self.wsp_id.query_verify_reason_comment = self.query_verify_reason_comment
			self.wsp_id.query_verified_by = self.user_id
			self.wsp_id.allow_resubmit_query = False
			self.wsp_id.action_verify_for_query()

	_defaults = {'wsp_query_id': lambda self, cr, uid, context: context.get('wsp_query_id', False), }

class WspQueryUpdate(models.TransientModel):
	_name = 'wsp.query.update'
	_description = 'Wsp Query Verificacation'

	query_docs_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	query_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	query_reason_comment = fields.Text(string='Comments / Reasons')
	query_update_reason_comment = fields.Text(string='Comments / Reasons')
	query_approve_reason_comment = fields.Text(string='Comments / Reasons')
	query_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')
	submittable = fields.Boolean(string='Can be submitted')
	query_allowed = fields.Boolean(string='Query Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_query = fields.Boolean(string='Allow Query')
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
	allow_query = fields.Boolean(string='Allow Query')
	show_query_date = fields.Boolean(string='Show Query')
	query_allowed = fields.Boolean(string='Query Allowed')
	request_query_date = fields.Date(string='Request Query Date')
	approve_query_date = fields.Date(string='Approve Query Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	query_date = fields.Date(string='WSP Query Date')	
	wsp_query_id =  fields.Many2one('wsp.query')
	wsp_id = fields.Many2one(related="wsp_query_id.wsp_plan_id", string='WSP Plan')
	
	


	@api.one
	def query_validate(self):
		if self.wsp_id :
			# wdb.set_trace()
			self.wsp_query_id.query_docs_statement = self.query_docs_statement			
			self.wsp_query_id.query_update_reason_comment = self.query_update_reason_comment
			self.wsp_id.query_comments = self.query_update_reason_comment
			self.wsp_id.wsp_query_id = self.wsp_query_id
			self.wsp_id.query_docs_statement = self.query_docs_statement
			self.wsp_id.action_update_for_query()		

			res_doc = {
					'query_docs_statement': self.query_docs_statement.id,
					'comments': self.query_reason_comment,
					'wsp_plan_id': self.wsp_id,
				}
			self.write({'wsp_query_docs_ids': [(0, 0, res_doc)], 'comments': ''})

	_defaults = {'wsp_query_id': lambda self, cr, uid, context: context.get('wsp_query_id', False), } 
	

class WspQueryApproval(models.TransientModel):
	_name = 'wsp.query.approval'
	_description = 'Wsp Query Approval'

	query_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	query_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	query_reason_comment = fields.Text(string='Comments / Reasons')
	query_verify_reason_comment = fields.Text(string='Comments / Reasons')
	query_approve_reason_comment = fields.Text(string='Comments / Reasons')
	query_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	query_allowed = fields.Boolean(string='Query Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_query = fields.Boolean(string='Allow Query')
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
	allow_query = fields.Boolean(string='Allow Query')
	show_query_date = fields.Boolean(string='Show Query')
	query_allowed = fields.Boolean(string='Query Allowed')
	request_query_date = fields.Date(string='Request Query Date')
	approve_query_date = fields.Date(string='Approve Query Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	query_date = fields.Date(string='WSP Query Date')		
	wsp_query_id =  fields.Many2one('wsp.query')
	wsp_id = fields.Many2one(related="wsp_query_id.wsp_plan_id", string='WSP Plan')
	
	

#  = fields.Many2one(
# 		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')    
# 	comments = fields.Text(string='Comments')
# 	wsp_plan_id = fields.Many2one('wsp.plan', string='Related WSP')


	@api.one
	def query_validate(self):
		if self.wsp_id :
			# self.wsp_query_id.query_doc_statement = self.query_doc_statement			
			self.wsp_query_id.query_approve_reason_comment = self.query_approve_reason_comment
			self.wsp_query_id.query_approved_by = self.user_id 
			self.wsp_query_id.query_state = 'approved' 
			self.wsp_id.wsp_query_id = self.wsp_query_id
			self.wsp_id.query_approve_reason_comment = self.query_approve_reason_comment
			self.wsp_id.query_approved_by = self.user_id
			self.wsp_id.allow_resubmit_query = False 
			self.wsp_id.action_approve_for_query()
			self.wsp_id.before_query_stage()
			
   
	_defaults = {'wsp_query_id': lambda self, cr, uid, context: context.get('wsp_query_id', False), }
	
	

class WspQueryReject(models.TransientModel):
	_name = 'wsp.query.reject'
	_description = 'Wsp Query Rejection'

	query_doc_statement = fields.Many2one(
		'ir.attachment', string="Extenstion of WSP Reason Statement/Letter", help='Upload Document')
	query_state = fields.Selection([('requested', 'Requested'), ('resubmit', 'Re-submit'), ('verified', 'Verified'), ('approved', 'Approved'), ('rejected', 'Rejected')], string="State" )
	query_reason_comment = fields.Text(string='Comments / Reasons')
	query_verify_reason_comment = fields.Text(string='Comments / Reasons')
	query_approve_reason_comment = fields.Text(string='Comments / Reasons')
	query_reject_reason_comment = fields.Text(string='Comments / Reasons')
	state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('evaluated', 'Assessment'), ('evaluated2',
																											'Evaluated'), ('approved', 'Accepted'), ('query', 'Query'), ('rejected', 'Rejected')], string="State", default='draft')

	submittable = fields.Boolean(string='Can be submitted')
	query_allowed = fields.Boolean(string='Query Allowed')
	is_tep_loaded = fields.Boolean("TEP Loaded", default=False)
	is_tep_to_planned_loaded = fields.Boolean(
		"TEP to Planned Loaded", default=False)
	is_prev_wsp_loaded = fields.Boolean("Previous WSP Loaded", default=False)
	allow_query = fields.Boolean(string='Allow Query')
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
	allow_query = fields.Boolean(string='Allow Query')
	show_query_date = fields.Boolean(string='Show Query')
	query_allowed = fields.Boolean(string='Query Allowed')
	request_query_date = fields.Date(string='Request Query Date')
	approve_query_date = fields.Date(string='Approve Query Date')
	sdl_no = fields.Char(string='SDL No.', size=10)
	wsp_submission_date = fields.Date(string='Date Submitted')
	wsp_end_period = fields.Date(
		string='WSP End Period')
	end_period = fields.Date(
		string='WSP Submission Due Date')
	duplicate_total_mf_tep = fields.Integer(
		string='Total Employees')
	query_date = fields.Date(string='WSP Query Date')		
	wsp_query_id =  fields.Many2one('wsp.query')
	wsp_id = fields.Many2one(related="wsp_query_id.wsp_plan_id", string='WSP Plan')
	
	


	@api.one
	def query_validate(self):
		if self.wsp_id :
			# self.wsp_query_id.query_doc_statement = self.query_doc_statement			
			self.wsp_query_id.query_reject_reason_comment = self.query_reject_reason_comment
			self.wsp_query_id.query_rejected_by = self.user_id 
			self.wsp_query_id.query_state = 'rejected' 
			self.wsp_id.wsp_query_id = self.wsp_query_id
			self.wsp_id.query_reject_reason_comment = self.query_reject_reason_comment
			self.wsp_id.query_approved_by = self.user_id
			self.wsp_id.allow_resubmit_query = False
			self.wsp_id.action_reject_for_query()

	_defaults = {'wsp_query_id': lambda self, cr, uid, context: context.get('wsp_query_id', False), }
	
	@api.one
	def query_validate_resubmit(self):
		if self.wsp_id :
			self.wsp_query_id.query_reject_reason_comment = self.query_reject_reason_comment
			self.wsp_query_id.query_rejected_by = self.user_id
			self.wsp_query_id.query_state = 'resubmit'
			self.wsp_id.wsp_query_id = self.wsp_query_id
			self.wsp_query_id.allow_resubmit_query = True				
			self.wsp_id.query_doc_statement = self.query_doc_statement			
			self.wsp_id.query_reject_reason_comment = self.query_reject_reason_comment
			self.wsp_id.query_rejected_by = self.user_id
			self.wsp_id.allow_resubmit_query = True			
			self.wsp_id.action_reject_resubmit_for_query()

	_defaults = {'wsp_query_id': lambda self, cr, uid, context: context.get('wsp_query_id', False), }
	
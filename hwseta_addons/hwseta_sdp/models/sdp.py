from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import os
import base64
import calendar
import random

DEBUG = True

if DEBUG:
    import logging
    logger = logging.getLogger(__name__)

    def dbg(msg):
        logger.info(msg)
else:
    def dbg(msg):
        pass


class SkillPlan(models.Model):
    _name = 'skill.plan'
    _description = "Skill Plan"

    name = fields.Char(string='Skills')


def validate_phone_mobile(phone_no):
    return True


class ProjectIndicator(models.Model):
    _name = 'project.indicator'
    _description = "Project Indicator"

    name = fields.Char(string="Name")

    _sql_constraints = [
        ('project_indicator_uniq', 'unique(name)', 'Project Indicator must be unique!')
    ]


class HwsetaProjectCategory(models.Model):
    _name = 'hwseta.project.category'
    _description = "HWSETA Project Category"
    _rec_name = 'category_name'

    category_type = fields.Selection(
        [
            ('18.1', 'Employed Learners (18.1)'),
            ('18.2', 'Unemployed Learners (18.2)')
        ],
        string="Category Type"
    )

    category_name = fields.Char(string="Category Name")

    @api.model
    def create(self, vals):
        res = super(HwsetaProjectCategory, self).create(vals)

        project_category_lst = self.env['hwseta.project.category'].search([
            ('category_name', '=', res.category_name),
            ('category_type', '=', res.category_type)
        ])

        if len(project_category_lst) > 1:
            raise UserError(_('You cannot create duplicate category name for same category type!'))

        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_project_type = fields.Boolean("Project Type")


class HwsetaProjectTypes(models.Model):
    _name = 'hwseta.project.types'
    _description = "HWSETA Project Types"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ------------------ FIELDS ------------------

    code = fields.Char(string="Code", tracking=True)

    name = fields.Many2one(
        'account.account',
        string="Name",
        tracking=True
    )

    budget = fields.Float(
        string='Available Discretionary budget',
        default=lambda self: self._default_budget()
    )

    rem_budget = fields.Float(string='Rem Budget')

    applied_budget = fields.Float(string='Project Type Budget')

    fees_employed = fields.Many2many(
        'fees.structure',
        'project_type_fees_emp_rel',
        'project_type_id',
        'fees_id',
        string='Funding Structure 18.1'
    )

    fees_unemployed = fields.Many2many(
        'fees.structure',
        'project_type_fees_unemp_rel',
        'project_type_id',
        'fees_id',
        string='Funding Structure 18.2'
    )

    project_ids = fields.One2many(
        'hwseta.project',
        'project_type_id',
        string="Projects"
    )

    project_document_ids = fields.One2many(
        'hwseta.project.document',
        'project_type_id',
        string="Project Documents"
    )

    # ⚠ Fiscalyear removed in Odoo 18 – replaced by configuration link
    seta_funding_year = fields.Many2one(
        'account.fiscal.year',
        string='Funding Year'
    )

    app_target_employed = fields.Integer(string="App Target 18.1")
    app_target_unemployed = fields.Integer(string="App Target 18.2")

    app_target_employed_unemployed = fields.Integer(
        string="Total App Target",
        compute='_compute_total_app_target',
        store=True
    )

    app_target_achieved_employed = fields.Integer(
        string="App Target Achieved 18.1",
        compute='_compute_app_target_achieved_employed',
        store=True
    )

    app_target_achieved_unemployed = fields.Integer(
        string="App Target Achieved 18.2",
        compute='_compute_app_target_achieved_unemployed',
        store=True
    )

    app_target_achieved_employed_unemployed = fields.Integer(
        string="Total App Target Achieved",
        compute='_compute_total_app_target_achieved',
        store=True
    )

    variance = fields.Float(
        string="Variance",
        compute='_compute_variance',
        store=True
    )

    project_indicator_id = fields.Many2one(
        'project.indicator',
        string="Indicator"
    )

    project_type_description = fields.Html("Description")

    project_type_terms_condition = fields.Many2one(
        'ir.attachment',
        string="Terms and Conditions"
    )

    # ------------------ ONCHANGE (NEW STYLE) ------------------

    @api.onchange('name')
    def _onchange_default_project_type(self):
        accounts = self.env['account.account'].search([
            ('is_project_type', '=', True)
        ])

        domain = {'name': [('id', 'in', accounts.ids)]}

        if self.name:
            self.code = self.name.code

        return {'domain': domain}

    # ------------------ DEFAULT BUDGET ------------------

    @api.model
    def _default_budget(self):
        config = self.env['leavy.income.config'].search([], limit=1)

        if not config or not config.project_budget_acc:
            return 0

        total_balance = abs(config.project_budget_acc.balance)

        total_applied_budget = sum(
            self.search([]).mapped('applied_budget')
        )

        available_budget = total_balance - total_applied_budget

        return max(available_budget, 0)

    # ------------------ COMPUTE METHODS ------------------

    @api.depends('app_target_employed', 'app_target_unemployed')
    def _compute_total_app_target(self):
        for rec in self:
            rec.app_target_employed_unemployed = (
                rec.app_target_employed + rec.app_target_unemployed
            )

    @api.depends(
        'app_target_achieved_employed',
        'app_target_achieved_unemployed'
    )
    def _compute_total_app_target_achieved(self):
        for rec in self:
            rec.app_target_achieved_employed_unemployed = (
                rec.app_target_achieved_employed +
                rec.app_target_achieved_unemployed
            )

    @api.depends()
    def _compute_app_target_achieved_employed(self):
        for rec in self:
            enroll_projects = self.env['enrollment.projects'].search([
                ('project_types', '=', rec.id),
                ('state', '=', 'approved')
            ])

            rec.app_target_achieved_employed = sum(
                enroll_projects.mapped('employed')
            )

    @api.depends()
    def _compute_app_target_achieved_unemployed(self):
        for rec in self:
            enroll_projects = self.env['enrollment.projects'].search([
                ('project_types', '=', rec.id),
                ('state', '=', 'approved')
            ])

            rec.app_target_achieved_unemployed = sum(
                enroll_projects.mapped('non_employed')
            )

    @api.depends(
        'app_target_employed_unemployed',
        'app_target_achieved_employed_unemployed'
    )
    def _compute_variance(self):
        for rec in self:
            if rec.app_target_employed_unemployed:
                achieved = rec.app_target_achieved_employed_unemployed
                target = rec.app_target_employed_unemployed

                percentage = (float(achieved) / float(target)) * 100
                rec.variance = 100 - percentage
            else:
                rec.variance = 0

    @api.model
    def create(self, vals):
        res = super(HwsetaProjectTypes, self).create(vals)

        # Check duplicate project type for same year
        project_types = self.search([
            ('name', '=', res.name.id),
            ('seta_funding_year', '=', res.seta_funding_year.id)
        ])

        if len(project_types) > 1:
            raise UserError(
                _('You can not create multiple Project type for the Financial year %s !') %
                (res.seta_funding_year.name)
            )

        # Budget validations
        if res.budget == 0 and res.applied_budget:
            raise UserError(_('You dont have more budget to allocate!'))

        if res.applied_budget > res.budget:
            raise UserError(_('You can not apply more budget than exists!'))

        # Validate linked projects
        if res.project_ids:
            total_budget = 0.0
            total_employed = 0
            total_unemployed = 0

            for project in res.project_ids:

                if project.target_employed == 0 and project.target_unemployed == 0:
                    raise UserError(
                        _('Please add Target 18.1 or Target 18.2 for %s') % project.name.name
                    )

                total_budget += project.budget_applied
                total_employed += project.target_employed
                total_unemployed += project.target_unemployed

            if total_budget > res.applied_budget:
                raise UserError(
                    _('You can not apply more budget than Project type budget exists!')
                )

            if total_employed > res.app_target_employed:
                raise UserError(
                    _('You can not apply more Employed than App target Employed exists!')
                )

            if total_unemployed > res.app_target_unemployed:
                raise UserError(
                    _('You can not apply more Unemployed than App Target Unemployed exists!')
                )

        return res

        # ---------------- WRITE -----------------

    def write(self, vals):
        res = super(HwsetaProjectTypes, self).write(vals)

        for rec in self:

            applied_budget = vals.get('applied_budget', rec.applied_budget)

            if rec.budget == 0 and vals.get('applied_budget'):
                raise UserError(_('You dont have more budget to allocate!'))

            if applied_budget > rec.budget:
                raise UserError(_('You can not apply more budget than exists!'))

            if rec.project_ids:
                total_budget = 0.0
                total_employed = 0
                total_unemployed = 0

                for project in rec.project_ids:

                    if project.target_employed == 0 and project.target_unemployed == 0:
                        raise UserError(
                            _('Please add Target 18.1 or Target 18.2 for %s') %
                            project.name.name
                        )

                    total_budget += project.budget_applied
                    total_employed += project.target_employed
                    total_unemployed += project.target_unemployed

                if total_budget > rec.applied_budget:
                    raise UserError(
                        _('You can not apply more budget than Project type budget exists!')
                    )

                if total_employed > rec.app_target_employed:
                    raise UserError(
                        _('You can not apply more Employed than App target Employed exists!')
                    )

                if total_unemployed > rec.app_target_unemployed:
                    raise UserError(
                        _('You can not apply more Unemployed than App Target Unemployed exists!')
                    )

        return res


class HwsetaProject(models.Model):
    _name = 'hwseta.project'
    _description = 'HWSETA Project'

    name = fields.Many2one(
        "account.account",
        string="Projects",
        tracking=True
    )

    project_type_id = fields.Many2one(
        'hwseta.project.types',
        string="Project Type"
    )

    budget_applied = fields.Float("Budget Allocated")

    target_employed = fields.Integer("Target 18.1")
    target_unemployed = fields.Integer("Target 18.2")

    project_approval = fields.Many2one(
        'ir.attachment',
        string="Project Approval"
    )

    # ---------- ONCHANGE PROJECT NAME ----------

    @api.onchange('name')
    def onchange_project(self):
        if not self.project_type_id:
            raise UserError(_('Please Select Project Type!'))

        project_type_id = self.project_type_id.name

        project_accounts = self.env['account.account'].search([
            ('parent_id', '=', project_type_id.id)
        ])

        return {
            'domain': {
                'name': [('id', 'in', project_accounts.ids)]
            }
        }

    # ---------- TARGET LOGIC ----------

    @api.onchange('target_employed')
    def onchange_target_employed(self):
        if self.target_employed > 0:
            self.target_unemployed = 0

    @api.onchange('target_unemployed')
    def onchange_target_unemployed(self):
        if self.target_unemployed > 0:
            self.target_employed = 0


# --------------------------------------------------


class HwsetaProjectDocument(models.Model):
    _name = 'hwseta.project.document'
    _description = 'HWSETA Project Document'

    name = fields.Many2one(
        'project.document',
        string="Document Name"
    )

    required = fields.Boolean("Document Required")

    project_type_id = fields.Many2one(
        'hwseta.project.types',
        string="Project Type"
    )


class DocumentLibrary(models.Model):
    _name = 'document.library'
    _description = 'Document Library'

    name = fields.Char(string='Document')

    ofo_file = fields.Binary(string='OFO Codes')
    ofo_file_name = fields.Char(string='OFO File Name')

    auth_page_less_fifty = fields.Binary(string='Authorisation Page (less than 50 Employees)')
    auth_page_name1 = fields.Char(string='Auth Page Name1')

    auth_page_more_fifty = fields.Binary(string='Authorisation Page (more than 50 Employees)')
    auth_page_name2 = fields.Char(string='Auth Page Name2')

    training_guide = fields.Binary(string='Training Guide')
    training_guide_name = fields.Char(string='Training Guide Name')

    wsp_template = fields.Binary(string='WSP Template')
    wsp_template_name = fields.Char(string='WSP Template Name')

    atr_template = fields.Binary(string='ATR Template')
    atr_template_name = fields.Char(string='ATR Template Name')

    # ---------------------------------------------------

    @api.model
    def default_get(self, fields):
        """
        This method will set the documents by default within document library.
        """
        res = super(DocumentLibrary, self).default_get(fields)

        res.update({
            'name': 'Documents',

            'ofo_file_name': 'ofo.pdf',

            'auth_page_name1': 'auth_page_less_fifty.pdf',

            'auth_page_name2': 'auth_page_more_fifty.pdf',

            'training_guide_name': 'train_guide.pdf',

            'wsp_template_name': 'Planned.xlsx',

            'atr_template_name': 'Actual.xlsx'
        })

        return res

    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        return super(DocumentLibrary, self).create(vals)


class LearnerAgree(models.Model):
    _name = 'learner.agree'
    _description = 'Learner Agreement'

    seq_no = fields.Char(string='Agreement No')

    learner_reg_no = fields.Char(string='Learner Reg No')

    attached_report = fields.Binary(string="Agreement File")

    identity_number = fields.Char(string='Identity Number')

    learner_id = fields.Many2one(
        'hr.employee',
        string='Learner'
    )

    state = fields.Selection(
        [('new', 'New'), ('done', 'Done')],
        string="Status",
        default='new'
    )


class LearnerProjectRel(models.Model):
    _name = 'learner.project.rel'
    _description = 'Learner Project Relationship'

    project_id = fields.Many2one(
        'project.project',
        string='Project Details'
    )

    learner_id = fields.Many2one(
        'hr.employee',
        string='Learner',
        domain=[('is_learner', '=', True)]
    )

    project_type_id = fields.Many2one(
        'hwseta.project.types',
        string="Project Type"
    )

    project_budget = fields.Float(string='Budget')

    qualification_ids = fields.Many2many(
        'provider.qualification',
        'learner_qualification_rel',
        'learner_id',
        'qualification_id',
        string='Qualifications'
    )


## SDF Related fields will be accessible here from hwseta_person module.
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employer_ids = fields.One2many(
        'sdf.employer.rel',
        'sdf_prof_id',
        string='Employers'
    )

    sdf_reg_id = fields.Many2one(
        'sdf.register',
        string='SDF Register ID'
    )

    sdf_popi_accept = fields.Boolean()

    sdf_pre_popi_date = fields.Boolean()

    latest_employer = fields.Many2one(
        'res.partner',
        string="Latest Employer"
    )

    agreement_ids = fields.One2many(
        'learner.agree',
        'learner_id',
        string='Agreement'
    )

    learning_programme_id = fields.Many2one(
        'learning.programme',
        string='Learning Programme'
    )

    project_ids = fields.One2many(
        'learner.project.rel',
        'learner_id',
        string='Projects'
    )

    # -----------------------------------------------------------
    # DEFAULT GET
    # -----------------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        res = super(HrEmployee, self).default_get(fields_list)

        context = dict(self.env.context)

        if context.get('is_learner_from_assessment'):
            res.update({
                'is_learner_from_assessment': True,
                'seta_elements': True,
                'is_learner': True
            })

        return res

    # -----------------------------------------------------------
    # ONCHANGE METHODS (NEW API)
    # -----------------------------------------------------------

    def _get_country_for_province(self, province_id):
        state = self.env['res.country.state'].browse(province_id)
        return state.country_id.id if state else False

    @api.onchange('work_state_id')
    def onchange_work_province(self):
        if self.work_state_id:
            self.work_country = self._get_country_for_province(self.work_state_id.id)

    @api.onchange('home_state_id')
    def onchange_home_province(self):
        if self.home_state_id:
            self.country_home = self._get_country_for_province(self.home_state_id.id)

    @api.onchange('postal_state_id')
    def onchange_postal_province(self):
        if self.postal_state_id:
            self.country_postal = self._get_country_for_province(self.postal_state_id.id)

    # -----------------------------------------------------------
    # CREATE METHOD - MIGRATED LOGIC
    # -----------------------------------------------------------

    @api.model
    def create(self, vals):
        user = self.env.user
        res = super(HrEmployee, self).create(vals)

        # ---- LEARNER CREATION LOGIC ----
        if res.is_learner:
            seq_no = self.env['ir.sequence'].next_by_code('learner.registration.sequence')
            res.write({
                'learner_reg_no': seq_no,
                'seta_elements': True
            })

        # ---- USER CREATION FOR ASSESSORS ----
        if not res.is_learner and not vals.get('already_registered') and not res.is_sdf:

            group_obj = self.env['res.groups']

            login = res.work_email or f"{res.name}@gmail.com"

            duplicate_match = self.env['res.users'].search([
                ('login', '=', login)
            ], limit=1)

            if duplicate_match:
                if duplicate_match.assessor_moderator_id:
                    raise UserError(
                        _('Sorry! Assessor/Moderator already registered with email %s') % login
                    )

                groups = group_obj.search([
                    '|',
                    ('name', '=', 'Portal'),
                    ('name', '=', 'Assessors')
                ])

                res.write({'user_id': duplicate_match.id})

                duplicate_match.write({
                    'assessor_moderator_id': res.id,
                    'groups_id': [(4, g.id) for g in groups]
                })

                return res

            # Create new user
            related_user = self.env['res.users'].create({
                'name': res.name,
                'login': login,
                'password': res.password,
                'assessor_moderator_id': res.id,
                'internal_external_users': 'Assessors',
            })

            groups = group_obj.search([
                '|',
                ('name', '=', 'Portal'),
                ('name', '=', 'Assessors')
            ])

            related_user.write({
                'groups_id': [(4, g.id) for g in groups]
            })

            related_user.partner_id.write({
                'email': login
            })

            res.write({'user_id': related_user.id})

        # ---- SDF USER CREATION LOGIC ----
        if res.is_sdf:

            group_obj = self.env['res.groups']

            groups = group_obj.search([
                '|',
                ('name', '=', 'Portal'),
                ('name', '=', 'SDF')
            ])

            rem_groups = group_obj.search([
                '|',
                ('name', '=', 'Contact Creation'),
                ('name', '=', 'Employee')
            ])

            group_list = [(4, g.id) for g in groups] + [(3, g.id) for g in rem_groups]

            related_user = self.env['res.users'].create({
                'name': res.name,
                'login': res.work_email,
                'password': res.password,
                'internal_external_users': 'SDF',
            })

            related_user.write({
                'groups_id': group_list,
                'sdf_id': res.id
            })

            related_user.partner_id.write({
                'email': res.work_email
            })

            res.write({'user_id': related_user.id})

            partner = user.partner_id

            if partner.employer:
                tracking_obj = self.env['sdf.tracking']

                register_data = res.sdf_reg_id

                track_data = tracking_obj.search([
                    ('sdf_register_id', '=', register_data.id)
                ])

                if not track_data:
                    tracking_obj.create({
                        'sdf_id': res.id,
                        'status': 'approved',
                        'partner_id': partner.id,
                        'sdf_approved_denied': True,
                    })

                self.env['sdf.employer.rel'].create({
                    'employer_id': partner.id,
                    'sdf_prof_id': res.id
                })

        return res


class ResUsers(models.Model):
    _inherit = 'res.users'

    sdf_id = fields.Many2one(
        'hr.employee',
        string='SDF'
    )

    assessor_moderator_id = fields.Many2one(
        'hr.employee',
        string='Assessor Moderator'
    )

    internal_external_users = fields.Selection(
        [
            ('SDF', 'SDF'),
            ('Providers', 'Providers'),
            ('Assessors', 'Assessors'),
            ('Moderators', 'Moderators'),
            ('Employer', 'Employer'),
            ('Administrator', 'Administrator'),
            ('Internal', 'Internal'),
            ('Unknown', 'Unknown')
        ],
        string='User Type',
        default="Internal"
    )


class FeesStructure(models.Model):
    _name = 'fees.structure'
    _description = "Fees Structure"

    name = fields.Char(
        string='Name',
        required=True
    )

    related_product = fields.Many2one(
        'product.product',
        string='Related Product'
    )

    project_emp_id = fields.Many2one(
        'project.project',
        string='Related Project (Employed)'
    )

    project_unemp_id = fields.Many2one(
        'project.project',
        string='Related Project (Unemployed)'
    )


# class ir_attachment(models.Model):
# 	_inherit = 'ir.attachment'
#
# 	@api.model
# 	def default_get(self, fields_list):
# 		res = super(ir_attachment, self).default_get(fields_list)
# 		context = self._context.copy()
# 		if context and context.get('model', False) == 'sdf.register':
# 			res.update({'name': 'ID Document/Passport Upload'})
# 		return res
#
# 	@api.model
# 	def create(self, vals):
# 		context = self._context.copy()
# 		if context and context.get('model', False) == 'sdf.register':
# 			vals.update({'name': vals.get('datas_fname', False)})
# 		return super(ir_attachment, self).create(vals)
#
# 	@api.v7
# 	def check(self, cr, uid, ids, mode, context=None, values=None):
# 		"""Restricts the access to an ir.attachment, according to referred model
# 		In the 'document' module, it is overriden to relax this hard rule, since
# 		more complex ones apply there.
# 		"""
# 		res_ids = {}
# 		require_employee = False
# 		if ids:
# 			if isinstance(ids, (int, long)):
# 				ids = [ids]
# 			cr.execute('SELECT DISTINCT res_model, res_id, create_uid FROM ir_attachment WHERE id = ANY (%s)', (ids,))
# 			for rmod, rid, create_uid in cr.fetchall():
# 				if not (rmod and rid):
# 					if create_uid != uid:
# 						require_employee = True
# 					continue
# 				res_ids.setdefault(rmod, set()).add(rid)
# 		if values:
# 			if values.get('res_model') and values.get('res_id'):
# 				res_ids.setdefault(values['res_model'], set()).add(values['res_id'])
#
# 		ima = self.pool.get('ir.model.access')
# 		for model, mids in res_ids.items():
# 			# ignore attachments that are not attached to a resource anymore when checking access rights
# 			# (resource was deleted but attachment was not)
# 			if not self.pool.get(model):
# 				require_employee = True
# 				continue
# 			existing_ids = self.pool[model].exists(cr, uid, mids)
# 			if len(existing_ids) != len(mids):
# 				require_employee = True
# 			ima.check(cr, uid, model, mode)
# 			self.pool[model].check_access_rule(cr, uid, existing_ids, mode, context=context)
#
#
# ir_attachment()


class SdfRegister(models.Model):
    _name = 'sdf.register'

    # ---------------------------------------------------------
    # DEFAULTS
    # ---------------------------------------------------------

    @api.model
    def _default_work_province(self):
        user = self.env.user
        if user.has_group('hwseta.group_provincial_manager') or \
           user.has_group('hwseta.group_provincial_officer'):
            return user.province_ids[:1].id
        return False

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    image_medium = fields.Binary(string='Medium Photo')

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True
    )

    work_email = fields.Char(string='Work Place Email', tracking=True)
    work_phone = fields.Char(string='Work Place Phone')
    work_address2 = fields.Char(string='Work Place Address 2')
    work_address3 = fields.Char(string='Work Place Address 3')

    work_city = fields.Many2one('res.city', string='Work City', tracking=True)

    work_province = fields.Many2one(
        'res.country.state',
        string='Work Place Province',
        default=_default_work_province,
        tracking=True
    )

    work_zip = fields.Char(string='Work Place Zip')
    work_country = fields.Many2one('res.country', string='Work Place Country')

    work_address = fields.Char(string='Work Place Address')
    work_location = fields.Char(string='Work Place Location')
    department = fields.Char(string='Department')
    job_title = fields.Char(string='Job Title')

    coach_id = fields.Many2one('hr.employee', string='Coach')
    user_id = fields.Many2one('res.users', string='Related User')
    company_id = fields.Many2one('res.company', string='Company')

    person_home_city = fields.Many2one('res.city', string='Home City')
    person_postal_city = fields.Many2one('res.city', string='Postal City')

    person_home_zip = fields.Char(string='Home Zip')
    person_postal_zip = fields.Char(string='Postal Zip')

    person_home_province_code = fields.Many2one(
        'res.country.state',
        string='Home Province Code'
    )

    person_postal_province_code = fields.Many2one(
        'res.country.state',
        string='Postal Province Code'
    )

    country_home = fields.Many2one('res.country', string='Home Country')
    country_postal = fields.Many2one('res.country', string='Postal Country')

    country_id = fields.Many2one('res.country', string='Nationality')

    identification_id = fields.Char(
        string='Identification No',
        size=13,
        tracking=True
    )

    passport_id = fields.Char(string='Passport No')
    bank_account_number = fields.Char(string='Bank Account Number')

    home_language_code = fields.Many2one('res.lang', string='Home Language')

    citizen_resident_status_code = fields.Selection(
        [
            ('dual', 'Dual (SA plus other)'),
            ('other', 'Other'),
            ('sa', 'South Africa'),
            ('unknown', 'Unknown')
        ],
        string='Citizen Status'
    )

    person_last_name = fields.Char(string='Last Name')
    person_birth_date = fields.Date(string='Birth Date')

    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female')],
        string='Gender'
    )

    marital = fields.Selection(
        [
            ('single', 'Single'),
            ('married', 'Married'),
            ('widower', 'Widower'),
            ('widow', 'Widow'),
            ('divorced', 'Divorced')
        ],
        string='Marital Status'
    )

    employer_ids = fields.One2many(
        'sdf.employer.rel',
        'sdf_id',
        string='Employers',
        copy=True
    )

    state = fields.Selection(
        [
            ('general_info', 'General Information'),
            ('public_info', 'Public Information'),
            ('personal_info', 'Personal Information'),
            ('address_info', 'Address Information'),
            ('employer_info', 'Employer'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('denied', 'Rejected'),
        ],
        default='general_info',
        tracking=True,
        index=True
    )

    submitted = fields.Boolean()
    approved = fields.Boolean()
    denied = fields.Boolean()

    related_sdf = fields.Many2one('hr.employee', string='Related SDF')

    population_group = fields.Selection(
        [
            ('African', 'African'),
            ('Coloured', 'Coloured'),
            ('Indian', 'Indian'),
            ('White', 'White')
        ],
        string='Population Group'
    )

    disabled = fields.Boolean(string='Disabled')

    cell_phone_number = fields.Char(string='Cell Phone Number')

    person_suburb = fields.Many2one('res.suburb', string='Suburb')
    person_home_suburb = fields.Many2one('res.suburb', string='Home Suburb')
    person_postal_suburb = fields.Many2one('res.suburb', string='Postal Suburb')

    id_document = fields.Many2one('ir.attachment', string='ID Document')

    sdf_reference_no = fields.Char(string='Reference No')

    sdf_type = fields.Selection(
        [('internal', 'Internal'), ('consultant', 'Consultant')],
        string='SDF Type'
    )

    sdf_approval_date = fields.Date(string='SDF Approval Date')
    sdf_register_date = fields.Date(string='SDF Registration Date')

    waiting_approval = fields.Boolean(string='Waiting Approval')

    sdf_letter_from_employer = fields.Many2one(
        'ir.attachment',
        string='Letter of SDF appointment'
    )

    primary_secondary = fields.Selection(
        [('primary', 'Primary'), ('secondary', 'Secondary')],
        string='Internal Type'
    )
    check_sdf_type = fields.Boolean(string="Check SDF Type", default=False)
    manager = fields.Char(string='Manager', track_visibility='onchange')
    person_title = fields.Selection(
        [('adv', 'Adv.'), ('dr', 'Dr.'), ('mr', 'Mr.'), ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('prof', 'Prof.')],
        string='Job Title', track_visibility='onchange')
    person_name = fields.Char(string='Name', track_visibility='onchange', size=50)
    cont_number_home = fields.Char(string='Contact Number Home', track_visibility='onchange', size=20)
    cont_number_office = fields.Char(string='Contact Number Office', track_visibility='onchange', size=20)
    person_home_address_1 = fields.Char(string='Home Address 1', track_visibility='onchange', size=50)
    person_home_address_2 = fields.Char(string='Home Address 2', track_visibility='onchange', size=50)
    person_home_address_3 = fields.Char(string='Home Address 3', track_visibility='onchange', size=50)
    person_postal_address_1 = fields.Char(string='Postal Address 1', track_visibility='onchange', size=50)
    person_postal_address_2 = fields.Char(string='Postal Address 2', track_visibility='onchange', size=50)
    person_postal_address_3 = fields.Char(string='Postal Address 3', track_visibility='onchange', size=50)
    person_home_addr_postal_code = fields.Char(string='Home Address Postal Code', track_visibility='onchange', size=4)
    person_home_addr_post_code = fields.Char(string='Home Address Post Code', track_visibility='onchange', size=4)
    same_as_home = fields.Boolean(string='Same As Home Address')
    final_state = fields.Char(string='Status')

    @api.model
    def create(self, vals):
        context = self.env.context

        # Backend creation
        if not context.get('from_website'):
            vals['sdf_reference_no'] = self.env['ir.sequence'].next_by_code(
                'sdf.register.reference'
            )
            vals['final_state'] = 'Draft'

        record = super().create(vals)

        # Website submission emails
        if context.get('from_website'):
            template_1 = self.env.ref(
                'hwseta_sdp.email_template_sdf_register_submit',
                raise_if_not_found=False
            )
            if template_1:
                template_1.send_mail(record.id, force_send=True)

            template_2 = self.env.ref(
                'hwseta_sdp.email_template_sdf_register_brian_submit',
                raise_if_not_found=False
            )
            if template_2:
                template_2.send_mail(record.id, force_send=True)

        # Phone validation
        if vals.get('work_phone'):
            validate_phone_mobile(vals['work_phone'])

        return record

    @api.onchange('sdf_type')
    def _onchange_sdf_type(self):
        if not self.sdf_type:
            self.check_sdf_type = False
            return

        if self.sdf_type == 'internal':
            self.check_sdf_type = True

        if self.sdf_type == 'consultant':
            self.check_sdf_type = False
            self.primary_secondary = False

    @api.onchange('person_suburb')
    def _onchange_person_suburb(self):
        if not self.person_suburb:
            return

        suburb = self.person_suburb
        self.work_zip = suburb.postal_code
        self.work_city = suburb.city_id
        self.work_province = suburb.province_id

    @api.onchange('person_home_suburb')
    def _onchange_person_home_suburb(self):
        if not self.person_home_suburb:
            return

        suburb = self.person_home_suburb
        self.person_home_zip = suburb.postal_code
        self.person_home_city = suburb.city_id
        self.person_home_province_code = suburb.province_id

	#
	# def onchange_person_postal_suburb(self, person_postal_suburb):
	# 	res = {}
	# 	if not person_postal_suburb:
	# 		return res
	# 	if person_postal_suburb:
	# 		sub_res = self.env['res.suburb'].browse(person_postal_suburb)
	# 		res.update({'value': {'person_postal_zip': sub_res.postal_code, 'person_postal_city': sub_res.city_id,
	# 							  'person_postal_province_code': sub_res.province_id}})
	# 	return res

    @api.onchange('citizen_resident_status_code')
    def _onchange_citizen_resident_status_code(self):
        if not self.citizen_resident_status_code:
            return

        if self.citizen_resident_status_code == 'sa':
            country = self.env['res.country'].search(
                [('code', '=', 'ZA')], limit=1
            )
            self.country_id = country

            return {
                'domain': {
                    'country_id': [('id', '=', country.id)]
                }
            }

        return {
            'domain': {
                'country_id': []
            }
        }

    @api.onchange('citizen_resident_status_code')
    def _onchange_citizen_resident_status_code(self):
        if not self.citizen_resident_status_code:
            return

        if self.citizen_resident_status_code == 'sa':
            country = self.env['res.country'].search(
                [('code', '=', 'ZA')], limit=1
            )
            self.country_id = country

            return {
                'domain': {
                    'country_id': [('id', '=', country.id)]
                }
            }

        return {
            'domain': {
                'country_id': []
            }
        }

    def _country_from_province(self, province):
        return province.country_id if province else False

    @api.onchange('work_province')
    def _onchange_work_province(self):
        if self.work_province:
            self.work_country = self.work_province.country_id

    @api.onchange('person_home_province_code')
    def _onchange_home_province(self):
        if self.person_home_province_code:
            self.country_home = self.person_home_province_code.country_id

    @api.onchange('person_postal_province_code')
    def _onchange_postal_province(self):
        if self.person_postal_province_code:
            self.country_postal = self.person_postal_province_code.country_id

    def _get_provincial_email(self):
        """Centralised province → email mapping"""
        return {
            63: "lungilen@hwseta.org.za",
            61: "zamod@hwseta.org.za",
            62: "richardm1@hwseta.org.za",
            64: "nomvuzor@hwseta.org.za",
            65: "mokhulum@hwseta.org.za",
            68: "juanitam@hwseta.org.za",
            67: "mbongisenig@hwseta.org.za",
            60: "welekazim@hwseta.org.za",
            66: "thabom2@hwseta.org.za",
        }

    def action_submit_button(self):
        self.ensure_one()

        # ----------------------------
        # VALIDATIONS
        # ----------------------------
        if not self.work_province:
            raise UserError(_('Please fill Work Province in Public Information.'))

        if not self.work_address:
            raise UserError(_('Please fill Work Address in Public Information.'))

        if not self.person_home_address_1:
            raise UserError(_('Please fill Home Address in Address Information.'))

        if not self.person_postal_address_1:
            raise UserError(_('Please fill Postal Address in Address Information.'))

        if not self.citizen_resident_status_code:
            raise UserError(_('Please Select Citizen Status in Personal Information.'))

        if not self.id_document:
            raise UserError(_('Please upload ID Document in Personal Information.'))

        if not self.employer_ids:
            raise UserError(_('Please Select Employers Information.'))

        # ----------------------------
        # UPDATE STATE
        # ----------------------------
        self.with_context(submit=True).write({
            'state': 'pending',
            'submitted': True,
            'final_state': 'Submitted',
            'waiting_approval': True,
        })

        # ----------------------------
        # SDF TYPE
        # ----------------------------
        sdf_type = self.primary_secondary if self.sdf_type == 'internal' else self.sdf_type

        # ----------------------------
        # EMAIL SETUP
        # ----------------------------
        template_external = self.env.ref(
            'hwseta_sdp.email_template_sdf_individual_register_submit', raise_if_not_found=False
        )
        template_internal = self.env.ref(
            'hwseta_sdp.email_template_sdf_individual_register_submit_internal', raise_if_not_found=False
        )

        province_email_map = self._get_provincial_email()
        province_id = self.work_province.id
        internal_email = province_email_map.get(province_id)

        internal_user = self.env['res.users'].search(
            [('login', '=', internal_email)], limit=1
        ) if internal_email else False

        # ----------------------------
        # LOOP EMPLOYERS
        # ----------------------------
        for employer_rel in self.employer_ids:
            employer = employer_rel.employer_id

            employer_rel.write({
                'status': 'waiting_approval',
                'employer_status': 'Pending'
            })

            # ----------------------------
            # INTERNAL NOTIFICATION
            # ----------------------------
            if template_internal and internal_user:
                template_internal.sudo().send_mail(
                    self.id,
                    email_values={'email_to': internal_user.login},
                    force_send=True
                )

            # ----------------------------
            # EMPLOYER NOTIFICATION
            # ----------------------------
            if template_external and employer.email:
                body = f"""
                    <p><b>SDF Name:</b> {self.name}</p>
                    <p><b>Organisation:</b> {employer.name}</p>
                    <p><b>SDL Number:</b> {employer.employer_sdl_no}</p>
                    <p><b>Application Ref:</b> {self.sdf_reference_no}</p>
                    <br/>
                    <p>
                        This email confirms your application to register as the
                        Skills Development Facilitator for <b>{employer.name}</b>.
                    </p>
                    <p>
                        Please submit confirmation to
                        <a href="mailto:daphneym1@hwseta.org.za">daphneym1@hwseta.org.za</a>
                    </p>
                    <br/>
                    <p>Regards<br/>HWSETA</p>
                """

                template_external.sudo().send_mail(
                    self.id,
                    email_values={
                        'email_to': employer.email,
                        'body_html': body
                    },
                    force_send=True
                )

            # ----------------------------
            # TRACKING RECORD
            # ----------------------------
            self.env['sdf.tracking'].create({
                'sdf_register_id': self.id,
                'partner_id': employer.id,
                'status': 'requested_approval',
                'sdf_approved_denied': True,
                'sdf_type': sdf_type,
            })

        return True

    def action_deny_button(self):
        self.ensure_one()

        for employer_rel in self.employer_ids:
            employer = employer_rel.employer_id

            tracking = self.env['sdf.tracking'].search([
                ('partner_id', '=', employer.id),
                ('sdf_register_id', '=', self.id)
            ])

            tracking.write({'status': 'denied'})
            employer_rel.write({
                'status': 'rejected',
                'employer_status': 'Rejected'
            })

        self.write({
            'state': 'denied',
            'denied': True,
            'final_state': 'Denied'
        })

        return True

    def action_approve_button(self):
        self.ensure_one()

        if self.approved:
            return True

        HrEmployee = self.env['hr.employee']
        Tracking = self.env['sdf.tracking']

        # ----------------------------
        # SDF TYPE
        # ----------------------------
        sdf_type = (
            self.primary_secondary
            if self.sdf_type == 'internal'
            else self.sdf_type
        )

        employer_values = []

        # ----------------------------
        # PROCESS EMPLOYERS
        # ----------------------------
        for employer_rel in self.employer_ids:
            employer = employer_rel.employer_id

            approved_trackings = Tracking.search([
                ('partner_id', '=', employer.id),
                ('status', '=', 'approved')
            ])

            # Handle existing SDFs → set dormant
            for existing in approved_trackings:
                if existing.status == 'approved':
                    existing.write({'status': 'dormant'})

            sdf_tracking = Tracking.search([
                ('sdf_register_id', '=', self.id),
                ('partner_id', '=', employer.id)
            ], limit=1)

            if employer_rel.status == 'waiting_approval' and sdf_tracking:
                employer_rel.write({'employer_status': 'Approved'})

                employer_values.append((0, 0, {
                    'employer_id': employer.id,
                    'employer_trading_name': employer.employer_trading_name,
                    'sdl_no': employer.sdl_no,
                    'seta_id': employer.seta_id.id if employer.seta_id else False,
                    'registration_number': employer.registration_number,
                    'status': 'approved',
                    'confirm_sdf_appointment_letter_from_employer':
                        employer.confirm_sdf_appointment_letter_from_employer.id
                        if employer.confirm_sdf_appointment_letter_from_employer else False,
                }))

                sdf_tracking.write({
                    'status': 'approved',
                    'employer_status': 'Approved',
                    'sdf_approved_denied': True,
                    'sdf_type': sdf_type,
                })

        # ----------------------------
        # PASSWORD
        # ----------------------------
        password = ''.join(random.choice('abcdef123456') for _ in range(10))
        self.write({'sdf_password': password})

        # ----------------------------
        # CREATE SDF (hr.employee)
        # ----------------------------
        sdf = HrEmployee.create({
            'name': self.name,
            'work_email': self.work_email,
            'work_phone': self.work_phone,
            'sdf_type': self.sdf_type,
            'work_address': self.work_address,
            'work_address2': self.work_address2,
            'work_address3': self.work_address3,
            'work_city': self.work_city.id if self.work_city else False,
            'work_zip': self.work_zip,
            'work_province': self.work_province.id if self.work_province else False,
            'work_country': self.work_country.id if self.work_country else False,
            'department': self.department,
            'job_title': self.job_title,
            'manager': self.manager,
            'notes': self.notes,
            'person_title': self.person_title,
            'person_name': self.person_name,
            'person_last_name': self.person_last_name,
            'person_birth_date': self.person_birth_date,
            'gender': self.gender,
            'marital': self.marital,
            'dissability': self.dissability,
            'identification_id': self.identification_id,
            'passport_id': self.passport_id,
            'citizen_resident_status_code': self.citizen_resident_status_code,
            'national_id': self.national_id,
            'home_language_code': self.home_language_code.id if self.home_language_code else False,
            'id_document': self.id_document.id if self.id_document else False,
            'is_sdf': True,
            'seta_elements': True,
            'sdf_reg_id': self.id,
            'employer_ids': employer_values,
            'password': password,
            'primary_secondary': self.primary_secondary,
        })

        # ----------------------------
        # UPDATE REGISTER
        # ----------------------------
        self.write({
            'related_sdf': sdf.id,
            'state': 'approved',
            'approved': True,
            'final_state': 'Approved',
            'sdf_approval_date': date.today(),
        })

        # ----------------------------
        # LINK TRACKING → SDF
        # ----------------------------
        Tracking.search([
            ('sdf_register_id', '=', self.id)
        ]).write({'sdf_id': sdf.id})

        # ----------------------------
        # EMAILS
        # ----------------------------
        template_admin = self.env.ref(
            'hwseta_sdp.email_template_sdf_register_approve',
            raise_if_not_found=False
        )
        template_employer = self.env.ref(
            'hwseta_sdp.email_template_individual_sdf_register_approve',
            raise_if_not_found=False
        )

        if template_admin:
            template_admin.sudo().send_mail(self.id, force_send=True)

        for employer_rel in self.employer_ids:
            employer = employer_rel.employer_id
            if template_employer and employer.email:
                template_employer.sudo().send_mail(
                    self.id,
                    email_values={'email_to': employer.email},
                    force_send=True
                )

        return True

    def check_alpha(self, field_string, msg):
        """
        Raise error if the string contains alphabetic characters.
        """
        if field_string:
            for ch in field_string:
                if ch.isalpha():
                    raise UserError(_(msg))
        return True

    def write(self, vals):
        res = super().write(vals)

        for record in self:
            # ------------------------------------
            # DUPLICATE SDL NUMBER CHECK
            # ------------------------------------
            sdl_numbers = set()
            for employer in record.employer_ids:
                if employer.sdl_no:
                    if employer.sdl_no in sdl_numbers:
                        raise UserError(
                            _('You cannot add the same employer multiple times.')
                        )
                    sdl_numbers.add(employer.sdl_no)

            ctx = record.env.context

            # ------------------------------------
            # STATE VALIDATIONS
            # ------------------------------------
            if record.state == "pending" and not record.submitted:
                raise UserError(
                    _('You cannot move to Pending before submitting the application.')
                )

            if record.state == "approved" and not record.approved:
                raise UserError(
                    _('You cannot manually change status to Approved.')
                )

            if record.state == "denied" and not record.denied:
                raise UserError(
                    _('You cannot manually change status to Rejected.')
                )

            if record.state == "pending" and record.approved:
                raise UserError(
                    _('This application is already Approved and cannot be set back to Pending.')
                )

            if record.state == "pending" and record.denied:
                raise UserError(
                    _('This application is already Rejected and cannot be set back to Pending.')
                )

        return res



    @api.onchange('identification_id')
    def onchange_id_no(self):
        if not self.identification_id:
            return

        id_no = str(self.identification_id)

        # ------------------------------------
        # BASIC VALIDATION
        # ------------------------------------
        if len(id_no) != 13 or not id_no.isdigit():
            self.identification_id = False
            return {
                'warning': {
                    'title': 'Invalid Identification Number',
                    'message': 'Identification Number should be 13 numeric digits!'
                }
            }

        # ------------------------------------
        # SA ID CHECK
        # ------------------------------------
        check = checkers.said_check(id_no)
        old_check = checkers.old_said_check(id_no)

        year = check.get('year')
        month = check.get('month')
        day = check.get('day')

        dbg(check)
        dbg(old_check)

        if not check.get('valid'):
            if "Invalid gender" in old_check:
                return {
                    'warning': {
                        'title': 'Invalid Identification Number',
                        'message': 'Invalid Gender!'
                    }
                }

            if "Invalid citizenship status" in old_check:
                return {
                    'warning': {
                        'title': 'Invalid Identification Number',
                        'message': 'Invalid citizenship status!'
                    }
                }

            # ------------------------------------
            # DATE VALIDATION
            # ------------------------------------
            if not (1 <= int(month) <= 12):
                return {
                    'warning': {
                        'title': 'Invalid Identification Number',
                        'message': 'Incorrect Month in Identification Number!'
                    }
                }

            # Determine century
            yr = int(year)
            full_year = 2000 + yr if yr <= 20 else 1900 + yr

            last_day = calendar.monthrange(full_year, int(month))[1]

            if not (1 <= int(day) <= last_day):
                return {
                    'warning': {
                        'title': 'Invalid Identification Number',
                        'message': 'Incorrect Day in Identification Number!'
                    }
                }

            # If everything else passed → checksum issue
            self.identification_id = False
            return {
                'warning': {
                    'title': 'Invalid Identification Number',
                    'message': 'Incorrect checksum!'
                }
            }

        # ------------------------------------
        # BIRTH DATE CALCULATION
        # ------------------------------------
        yr = int(year)
        full_year = 2000 + yr if yr <= 20 else 1900 + yr

        birth_date = datetime.strptime(
            f"{full_year}-{month}-{day}",
            "%Y-%m-%d"
        ).date()

        self.person_birth_date = birth_date


class SdfEmployerRel(models.Model):
    _name = 'sdf.employer.rel'
    _description = 'SDF Employer Relation'

    employer_id = fields.Many2one(
        'res.partner',
        string="Employer",
        domain="[('employer', '=', True)]"
    )
    employer_trading_name = fields.Char(string='Trading Name')
    sdl_no = fields.Char(string='SDL No.', size=10)
    seta_id = fields.Char(string='SETA Id.', size=3)
    registration_number = fields.Char(string='Registration Number', size=20)

    sdf_id = fields.Many2one(
        'sdf.register',
        string="SDF",
        ondelete='cascade'
    )
    sdf_prof_id = fields.Many2one(
        'hr.employee',
        string="SDF Profile",
        ondelete='cascade'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('assessment_done', 'Assessment Done'),
            ('transche_payment', 'TP Done')
        ],
        string="State"
    )

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting_approval', 'Waiting Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        string="Status",
        default='draft'
    )

    emp_add = fields.Boolean(string='Add Organization', default=True)
    request_send = fields.Boolean(string='Send Request', default=False)

    confirm_sdf_appointment_letter_from_employer = fields.Many2one(
        'ir.attachment',
        string="SDF Appointment Letter"
    )

    employer_status = fields.Char(string="Status")

    # --------------------------------------------------
    # ONCHANGE: EMPLOYER
    # --------------------------------------------------
    @api.onchange('employer_id')
    def _onchange_employer_id(self):
        if not self.employer_id:
            return

        employer = self.employer_id
        self.sdl_no = employer.employer_sdl_no
        self.employer_trading_name = employer.employer_trading_name
        self.seta_id = employer.employer_seta_id
        self.registration_number = employer.employer_registration_number

    # --------------------------------------------------
    # ONCHANGE: SDL NUMBER
    # --------------------------------------------------
    @api.onchange('sdl_no')
    def _onchange_sdl_no(self):
        if not self.sdl_no:
            return

        employer = self.env['res.partner'].search(
            [('employer_sdl_no', '=', self.sdl_no)],
            limit=1
        )

        if not employer:
            raise UserError(_('Enter a valid SDL Number!'))

        self.employer_id = employer
        self.employer_trading_name = employer.employer_trading_name
        self.seta_id = employer.employer_seta_id
        self.registration_number = employer.employer_registration_number

    # --------------------------------------------------
    # ACTION: SEND REQUEST
    # --------------------------------------------------
    def action_send_request(self):
        for rec in self:
            if not rec.employer_id or not rec.sdf_prof_id:
                raise UserError(_('Employer and SDF Profile are required.'))

            rec.write({
                'status': 'waiting_approval',
                'request_send': True,
            })

            # Create tracking entry
            tracking_vals = {
                'sdf_register_id': rec.sdf_prof_id.sdf_reg_id.id,
                'status': 'requested_approval',
                'sdf_id': rec.sdf_prof_id.id,
                'partner_id': rec.employer_id.id,
                'sdf_employer_rel_id': rec.id,
            }

            rec.employer_id.write({
                'sdf_tracking_ids': [(0, 0, tracking_vals)]
            })

            # ------------------------------------
            # EMAIL: ORGANISATION
            # ------------------------------------
            template_org = self.env.ref(
                'hwseta_sdp.email_template_sdf_register_organisation_post_submit',
                raise_if_not_found=False
            )
            if template_org:
                template_org.send_mail(rec.id, force_send=True)

            # ------------------------------------
            # EMAIL: SDP MANAGERS
            # ------------------------------------
            template_mgr = self.env.ref(
                'hwseta_sdp.email_template_sdf_register_sdp_managers_post_submit',
                raise_if_not_found=False
            )
            if template_mgr:
                template_mgr.send_mail(rec.id, force_send=True)

        return True


class SdfTracking(models.Model):
    _name = 'sdf.tracking'
    _description = 'SDF Tracking'

    sdf_id = fields.Many2one(
        'hr.employee',
        string="SDF",
        ondelete='cascade'
    )

    sdf_register_id = fields.Many2one(
        'sdf.register',
        string="SDF Registering",
        ondelete='cascade'
    )

    status = fields.Selection(
        [
            ('requested_approval', 'Requested Approval'),
            ('approved', 'Approved'),
            ('denied', 'Denied'),
            ('dormant', 'Dormant'),
            ('pending', 'Pending'),
        ],
        string='State',
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
        domain="[('employer', '=', True)]"
    )

    sdf_approved_denied = fields.Boolean(string='SDF Approved / Denied')
    sdf_employer_rel_id = fields.Many2one(
        'sdf.employer.rel',
        string="SDF Employer Relation"
    )

    sdf_type = fields.Selection(
        [
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('consultant', 'Consultant')
        ],
        string='SDF Type'
    )

    sdf_dormant = fields.Boolean(
        string="SDF Dormant",
        default=False
    )

    # ---------------------------------------------------------
    # ACTION: APPROVE SDF
    # ---------------------------------------------------------
    def action_approve_sdf(self):
        for rec in self:
            sdf_register = rec.sdf_register_id
            employer = rec.partner_id

            # ----------------------------------------
            # Case 1: Approval via sdf.employer.rel
            # ----------------------------------------
            if rec.sdf_employer_rel_id:
                emp_rel = rec.sdf_employer_rel_id
                emp_rel.write({'status': 'approved'})
                rec.write({'status': 'approved', 'sdf_approved_denied': True})

                # Email: Employer Approved
                template_emp = self.env.ref(
                    'hwseta_sdp.email_template_sdf_register_post_approve',
                    raise_if_not_found=False
                )
                if template_emp:
                    template_emp.send_mail(rec.id, force_send=True)

                # Email: Manager Approved
                template_mgr = self.env.ref(
                    'hwseta_sdp.email_template_sdf_register_post_approve_manager',
                    raise_if_not_found=False
                )
                if template_mgr:
                    template_mgr.send_mail(rec.id, force_send=True)

            # ---------------------------------------------------
            # Case 2: Registration already approved → add employer
            # ---------------------------------------------------
            if sdf_register and sdf_register.final_state == 'Approved':
                sdf_employee = self.env['hr.employee'].search(
                    [('sdf_reg_id', '=', sdf_register.id)],
                    limit=1
                )

                registration_number = ''
                if not rec.sdf_employer_rel_id:
                    for emp in sdf_register.employer_ids:
                        if emp.employer_id.id == employer.id:
                            registration_number = emp.registration_number

                    self.env['sdf.employer.rel'].create({
                        'sdf_prof_id': sdf_employee.id,
                        'employer_id': employer.id,
                        'sdl_no': employer.employer_sdl_no,
                        'registration_number': registration_number,
                        'emp_add': False,
                        'status': 'approved',
                    })

                    rec.write({'status': 'approved', 'sdf_approved_denied': True})

            # ---------------------------------------------------
            # Case 3: Normal approval flow
            # ---------------------------------------------------
            else:
                if sdf_register and employer:
                    for emp in sdf_register.employer_ids:
                        if emp.employer_id.id == employer.id:
                            emp.write({'status': 'approved'})

                    sdf_register.write({'waiting_approval': True})
                    rec.write({'status': 'approved', 'sdf_approved_denied': True})

        return True

    # ---------------------------------------------------------
    # ACTION: DENY
    # ---------------------------------------------------------
    def action_deny_sdf(self):
        self.write({
            'status': 'denied',
            'sdf_approved_denied': True
        })
        return True

    # ---------------------------------------------------------
    # ACTION: DORMANT
    # ---------------------------------------------------------
    def action_dormant_sdf(self):
        self.write({
            'status': 'dormant',
            'sdf_dormant': True
        })
        return True

    # ---------------------------------------------------------
    # ACTION: UNDORMANT
    # ---------------------------------------------------------
    def action_undormant_sdf(self):
        self.write({
            'status': 'approved',
            'sdf_dormant': False
        })
        return True


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sdf_tracking_ids = fields.One2many(
        'sdf.tracking',
        'partner_id',
        string='SDF Tracking'
    )

    # Employer approval fields (ported from legacy)
    employer_approval_status_id = fields.Char(size=10)
    employer_approval_status_m2o = fields.Many2one(
        'employer.approval.status.id',
        string="Employer Approval Status"
    )
    employer_approval_status_num = fields.Char(size=20)

    employer_approval_start_date = fields.Datetime()
    employer_approval_end_date = fields.Datetime()

    employer_contact_name = fields.Char(size=20)
    employer_contact_phone_number = fields.Char(size=20)

    organization_document_file = fields.Many2one(
        'ir.attachment',
        string='Organization Document File'
    )


class ProviderAssessment(models.Model):
    _name = 'provider.assessment'
    _inherit = 'mail.thread'
    _description = 'Provider Assessment'

    assessed = fields.Boolean(
        string='Assessed',
        tracking=True
    )


class EoiIdConfiguration(models.Model):
    _name = 'eoi_id.configuration'
    _inherit = 'mail.thread'
    _description = 'EOI ID Configuration'
    _rec_name = 'eoi_id'

    eoi_id = fields.Char(
        string='EOI ID',
        tracking=True,
        readonly=True,
        copy=False
    )

    eoi_description = fields.Char(
        string='EOI Description',
        tracking=True
    )

    @api.model
    def create(self, vals):
        vals['eoi_id'] = self.env['ir.sequence'].next_by_code(
            'eoi_id.configuration'
        )
        return super().create(vals)
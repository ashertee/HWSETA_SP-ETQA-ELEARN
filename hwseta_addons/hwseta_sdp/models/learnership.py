from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import calendar

DIFFICULTY_RATINGS = [
            ('1', 'No difficulty'),
            ('2', 'Some difficulty'),
            ('3', 'A lot of difficulty'),
            ('4', 'Cannot do at all'),
            ('6', 'Cannot yet be determined'),
            ('60', 'May be part of multiple difficulties (TBC)'),
            ('70', 'May have difficulty (TBC)'),
            ('80', 'Former difficulty - none now')
        ]

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # 1. Identity & SDF Fields
    # track_visibility='onchange' becomes tracking=True
    # size attribute is generally ignored by modern Odoo ORM (handled at DB level if needed)
    national_id = fields.Char(string='National Id', tracking=True)
    person_alternate_id = fields.Char(string='Person Alternate Id', tracking=True)
    alternate_id_type_id = fields.Char(string='Alternate Type Id', tracking=True)
    alternate_id_type = fields.Selection([
        ('saqa_member', '521 - SAQA Member ID'),
        ('passport_number', '527 - Passport Number'),
        ('drivers_license', '529 - Drivers License'),
        ('temporary_id_number', '531 - Temporary ID number'),
        ('none', '533 - None'),
        ('unknown', '535 - Unknown'),
        ('student_number', '537 - Student number'),
        ('work_permit_number', '538 - Work Permit Number'),
        ('employee_number', '539 - Employee Number'),
        ('birth_certificate_number', '540 - Birth Certificate Number'),
        ('hsrc_register_number', ' 541 - HSRC Register Number'),
        ('etqe_record_number', '561 - ETQA Record Number'),
        ('refugee_number', '565 - Refugee Number')
    ], string='Alternate ID Type')

    # 2. Language & Nationality
    home_language_code = fields.Many2one('res.lang', string='Home Language Code', tracking=True)
    home_lang_saqa_code = fields.Selection([
        ('eng', 'Eng'), ('afr', 'Afr'), ('xho', 'Xho'), ('set', 'Set'), ('zul', 'Zul'),
        ('sep', 'Sep'), ('tsh', 'Tsh'), ('ses', 'Ses'), ('xit', 'Xit'), ('swa', 'Swa'),
        ('nde', 'Nde'), ('u', 'U'), ('oth', 'Oth')
    ], string='Home Language SAQA Code')
    nationality_saqa_code = fields.Selection([('sa', 'SA')], string='Nationality SAQA Code')

    citizen_resident_status_code = fields.Selection([
        ('sa', 'SA - South Africa'), ('dual', 'D - Dual (SA plus other)'),
        ('other', 'O - Other'), ('PR', 'PR - Permanent Resident'), ('unknown', 'U - Unknown')
    ], string='Citizen Status')
    citizen_status_saqa_code = fields.Selection([
        ('sa', 'SA'), ('d', 'D'), ('o', 'O'), ('pr', 'PR'), ('u', 'U')
    ], string='Citizen Status SAQA Code')

    # 3. Personal Details
    person_last_name = fields.Char(string='Last Name', tracking=True)
    person_middle_name = fields.Char(string='Middle Name', tracking=True)
    person_title = fields.Selection([
        ('adv', 'Adv.'), ('dr', 'Dr'), ('mr', 'Mr'), ('mrs', 'Mrs'), ('ms', 'Ms'), ('prof', 'Prof')
    ], string='Title', tracking=True)
    person_name = fields.Char(string='First Name', tracking=True)
    person_birth_date = fields.Date(string='Birth Date', tracking=True)

    # 4. Address Hierarchy (Linked to your previously migrated models)
    person_suburb = fields.Many2one('res.suburb', string='Suburb')
    person_home_suburb = fields.Many2one('res.suburb', string='Home Suburb')
    person_postal_suburb = fields.Many2one('res.suburb', string='Postal Suburb')

    person_home_city = fields.Many2one('res.city', string='Home City', tracking=True)
    person_postal_city = fields.Many2one('res.city', string='Postal City', tracking=True)

    person_home_province_code = fields.Many2one('res.country.state', string='Home Province Code', tracking=True)
    person_postal_province_code = fields.Many2one('res.country.state', string='Postal Province Code', tracking=True)

    # 5. Work Address Extensions
    work_address2 = fields.Char(string='Work Address 2', tracking=True)
    work_address3 = fields.Char(string='Work Address 3', tracking=True)
    work_city = fields.Many2one('res.city', string='Work City', tracking=True)
    work_province = fields.Many2one('res.country.state', string='Work Province', tracking=True)
    work_zip = fields.Char(string='Work Zip', tracking=True)
    work_country = fields.Many2one('res.country', string='Work Country', tracking=True)

    # 6. Default values in Odoo 18 style
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today)


        # --- Ratings Section ---
    seeing_rating_id = fields.Selection(DIFFICULTY_RATINGS, string='Seeing Rating Id', tracking=True)
    hearing_rating_id = fields.Selection(DIFFICULTY_RATINGS, string='Hearing Rating Id', tracking=True)
    walking_rating_id = fields.Selection(DIFFICULTY_RATINGS, string='Walking Rating Id', tracking=True)
    remembering_rating_id = fields.Selection(DIFFICULTY_RATINGS, string='Remembering Rating Id', tracking=True)
    communicating_rating_id = fields.Selection(DIFFICULTY_RATINGS, string='Communicating Rating Id', tracking=True)
    self_care_rating_id = fields.Selection(DIFFICULTY_RATINGS, string='Self Care Rating Id', tracking=True)

    # --- SETA & Learner Status ---
    last_school_emis_no = fields.Char(string='Last School EMIS No', tracking=True)
    last_school_year = fields.Integer(string='Last School Year', tracking=True)
    statssa_area_code = fields.Integer(string='STATSSA Area Code', tracking=True)
    popi_act_status_id = fields.Integer(string='POPI Act Status Id', tracking=True)
    popi_act_status_date = fields.Date(string='POPI Act Status Date', tracking=True)

    is_sdf = fields.Boolean(string='SDF', tracking=True)
    is_learner = fields.Boolean(string='Learner', tracking=True)
    is_learner_from_assessment = fields.Boolean(string='Learner (from Assessment)', default=False, tracking=True)
    seta_elements = fields.Boolean(string='Seta Elements', tracking=True)

    # --- Professional IDs ---
    rsa_identity_no = fields.Char(string='RSA Identity No', tracking=True)
    learner_reg_no = fields.Char(string='Learner Reg No', tracking=True)
    assessor_seq_no = fields.Char(string='Assessor ID')
    moderator_seq_no = fields.Char(string='Moderator ID')

    # --- Document Attachments ---
    # In Odoo 18, using Many2one to ir.attachment is the preferred way to manage files without bloating the DB
    id_document = fields.Many2one('ir.attachment', string='ID Document')
    registrationdoc = fields.Many2one('ir.attachment', string='Assessor Registration Documents')
    cv_document = fields.Many2one('ir.attachment', string="CV Document")
    sdf_letter_from_employer = fields.Many2one("ir.attachment", string="Letter of SDF Appointment")

    # --- Equity & Socio-Economic ---
    equity = fields.Selection([
        ('black_african', 'Black: African'),
        ('black_indian', 'Black: Indian / Asian'),
        ('black_coloured', 'Black: Coloured'),
        ('other', 'Other'),
        ('white', 'White')
    ], string='Equity', tracking=True)

    socio_economic_status = fields.Selection([
        ('employed', 'Employed'),
        ('unemployed', 'Unemployed, seeking work'),
        ('unspecified', 'Unspecified')
    ], string='Socio Economic Status')

    # --- Address & Municipality (Linked to previous migrations) ---
    work_municipality = fields.Many2one('res.municipality', string='Working Municipality')
    physical_municipality = fields.Many2one('res.municipality', string='Physical Municipality')
    postal_municipality = fields.Many2one('res.municipality', string='Postal Municipality')

    # Update marital selection in Odoo 18
    # marital = fields.Selection(selection_add=[('widow', 'Widow')], ondelete={'widow': 'set default'})

    # Password field should usually be handled with 'password=True' in XML for masking
    password = fields.Char("Portal Password")
    provider_learner = fields.Boolean(
        string='Is Provider Learner',
        default=False,
        help="Technical field to control view visibility"
    )
    certificate_no = fields.Char(string='Qualification & Certificate No')
    bank_account_number = fields.Char(string='Bank Account Number')
    person_home_address_1 = fields.Char(string='Home Address 1',track_visibility='onchange', size=50)
    person_home_address_2 = fields.Char(string='Home Address 2', track_visibility='onchange', size=50)
    person_home_address_3 = fields.Char(string='Home Address 3', track_visibility='onchange', size=50)
    person_postal_address_1 = fields.Char(string='Postal Address 1', track_visibility='onchange', size=50)
    person_postal_address_2 = fields.Char(string='Postal Address 2', track_visibility='onchange', size=50)
    person_postal_address_3 = fields.Char(string='Postal Address 3', track_visibility='onchange', size=50)
    country_home = fields.Many2one('res.country', string='Home Country', track_visibility='onchange')
    country_postal = fields.Many2one('res.country', string='Postal Country', track_visibility='onchange')
    person_previous_alternate_id = fields.Char(string='Previous Alternate Id',track_visibility='onchange', size=20)
    person_previous_alternate_id_type_id = fields.Char(string='Previous Alternate Id Type Id',track_visibility='onchange', size=3)
    person_previous_provider_code = fields.Char(string='Previous Provider Code', track_visibility='onchange', size=20)
    person_previous_provider_etqe_id = fields.Integer(string='Previous Provider ETQE Id', track_visibility='onchange',
                                                  size=10)


class ProjectFees(models.Model):
    _name = 'project.fees'
    _description = 'Project Fees'

    name = fields.Char(string='Fees Name')

    project_emp_id = fields.Many2one(
        'project.project',
        string='Related Project (Employee)'
    )

    project_unemp_id = fields.Many2one(
        'project.project',
        string='Related Project (Unemployee)'
    )

    course_id = fields.Many2one(
        'fees.structure',
        string='Fees Name'
    )

    course_amount = fields.Float(string='Course Amount')

    

## Added for EOI Configuration ( Masters for  EOI Approval Criteria )
class EoiApprovalCriteria(models.Model):
    _name = 'eoi.approval.criteria'
    _description = 'EOI Approval Criteria'
    _rec_name = 'project_id'

    project_type = fields.Many2one(
        'hwseta.project.types',
        string='Project Type',
        tracking=True
    )

    project_id = fields.Many2one(
        'project.project',
        string='Project'
    )

    allocation_ids = fields.One2many(
        'allocation.data',
        'eoi_approval_id',
        string='Allocation'
    )

    funding_year = fields.Many2one(
        'account.fiscalyear',
        string='Funding Year'
    )

    category = fields.Many2one(
        'hwseta.project.category',
        string='Project Category'
    )

    category_type = fields.Selection(
        [
            ('18.1', 'Employed Learners (18.1)'),
            ('18.2', 'Unemployed Learners (18.2)')
        ],
        string="Category Type"
    )

    # ---------- ONCHANGE METHODS (ODOO 18 STYLE) ----------

    @api.onchange('funding_year')
    def onchange_funding_year(self):
        if not self.funding_year:
            return {'domain': {'project_type': [('id', 'in', [])]}}

        project_types = self.env['hwseta.project.types'].search([
            ('seta_funding_year', '=', self.funding_year.id)
        ])

        return {'domain': {'project_type': [('id', 'in', project_types.ids)]}}

    @api.onchange('project_type')
    def onchange_project_type(self):
        if not self.project_type:
            return {'domain': {'project_id': [('id', 'in', [])]}}

        projects = self.env['project.project'].search([
            ('project_types', '=', self.project_type.id)
        ])

        return {'domain': {'project_id': [('id', 'in', projects.ids)]}}

    @api.onchange('project_id')
    def onchange_project(self):
        if self.project_id:
            project = self.project_id

            if project.category_type == '18.1':
                self.category_type = '18.1'
            else:
                self.category_type = '18.2'

            if project.category:
                self.category = project.category.id

    @api.onchange('category_type')
    def onchange_category_type(self):
        """Filter project category based on category type"""

        if not self.category_type:
            self.category = False
            return {'domain': {'category': [('id', 'in', [])]}}

        category_values = self.env['hwseta.project.category'].search([
            ('category_type', '=', self.category_type)
        ])

        category_lst = category_values.ids

        if category_lst:
            return {'domain': {'category': [('id', 'in', category_lst)]}}

        return {'domain': {'category': [('id', 'in', [])]}}

    # ---------- CREATE OVERRIDE ----------

    @api.model
    def create(self, vals):
        res = super(EoiApprovalCriteria, self).create(vals)

        eoi_criteria = self.search([
            ('project_id', '=', res.project_id.id),
            ('funding_year', '=', res.funding_year.id)
        ])

        if len(eoi_criteria) > 1:
            raise UserError(
                _('You can not create multiple EOI criteria for the Financial year %s !')
                % (res.funding_year.name)
            )

        for line in res.allocation_ids:
            if res.category_type == '18.1' and line.learner_status == 'unemployed':
                raise UserError(_('You can not add unemployed learner status!'))

            if res.category_type == '18.2' and line.learner_status == 'employed':
                raise UserError(_('You can not add employed learner status'))

        return res

    # ---------- WRITE OVERRIDE ----------

    def write(self, vals):
        res = super(EoiApprovalCriteria, self).write(vals)

        for record in self:
            eoi_criteria = self.search([
                ('project_id', '=', record.project_id.id),
                ('funding_year', '=', record.funding_year.id)
            ])

            if len(eoi_criteria) > 1:
                raise UserError(
                    _('You can not create multiple EOI criteria for the Financial year %s !')
                    % (record.funding_year.name)
                )

            for line in record.allocation_ids:
                if record.category_type == '18.1' and line.learner_status == 'unemployed':
                    raise UserError(_('You can not add unemployed learner status!'))

                if record.category_type == '18.2' and line.learner_status == 'employed':
                    raise UserError(_('You can not add employed learner status'))

        return res

class EmployerType(models.Model):
    _inherit = 'employer.type'

    allocation_id = fields.Many2one(
        'allocation.data',
        string='Related Allocations'
    )


class AllocationData(models.Model):
    _name = 'allocation.data'
    _description = 'Allocation Data'

    learner_status = fields.Selection(
        [
            ('employed', 'Employed'),
            ('unemployed', 'Un-employed')
        ],
        string='Learner Status'
    )

    emp_type_id = fields.Many2many(
        'employer.type',
        'allocation_employer_type_rel',
        'allocation_id',
        'emp_type_id',
        string='Type Of Employer'
    )

    min_learner = fields.Integer(string='Min no. Learner')

    max_learner = fields.Integer(string='Max no. Learner')

    percentage_allocate = fields.Integer(string='Percentage(%)')

    eoi_approval_id = fields.Many2one(
        'eoi.approval.criteria',
        string='Related EOI Approval'
    )

    # ---------- ONCHANGE VALIDATION ----------

    @api.onchange('learner_status')
    def onchange_learner_status(self):
        """Restrict learner status based on EOI category type"""

        if not self.eoi_approval_id:
            return

        if self.eoi_approval_id.category_type == '18.2' and self.learner_status == 'employed':
            return {
                'warning': {
                    'title': _('Invalid Learner Status'),
                    'message': _('Sorry! You can not add employed learner status')
                }
            }

        if self.eoi_approval_id.category_type == '18.1' and self.learner_status == 'unemployed':
            return {
                'warning': {
                    'title': _('Invalid Learner Status'),
                    'message': _('Sorry! You can not add unemployed learner status')
                }
            }

class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_types = fields.Many2one(
        'hwseta.project.types',
        string="Project Type"
    )

    fees_employed = fields.One2many(
        'project.fees',
        'project_emp_id',
        string='Fees 18.1'
    )

    fees_unemployed = fields.One2many(
        'project.fees',
        'project_unemp_id',
        string='Fees 18.2'
    )

    employer_request_ids = fields.One2many(
        'employer.requests',
        'project_id',
        string='Employer Requests Employed/Unemployed'
    )

    fees_defined = fields.Boolean("Fees define", default=False)

    update_toeoi = fields.Boolean("Update to EOI", default=False)

    eoi_id = fields.Many2one(
        'eoi_id.configuration',
        string="EOI ID"
    )

    eoi_id_reference_invisible = fields.Char(
        related='eoi_id.eoi_id',
        string="EOI ID",
        store=True,
        readonly=True
    )

    state = fields.Selection(
        [
            ('template', 'Template'),
            ('draft', 'New'),
            ('open', 'In Progress'),
            ('publish', 'Publish'),
            ('cancelled', 'Cancelled'),
            ('pending', 'Pending'),
            ('close', 'Closed')
        ],
        string='Status',
        required=True,
        copy=False
    )

    # ---------- ACTION METHODS ----------

    def set_publish(self):
        self.write({'state': 'publish'})
        return True

    # ---------- ONCHANGE METHODS ----------

    @api.onchange('project_types')
    def onchange_project_type(self):
        if not self.project_types:
            return

        project_type_data = self.project_types
        project_type_budget = project_type_data.applied_budget or 0

        allocated_budget = sum(
            self.search([
                ('project_types', '=', project_type_data.id)
            ]).mapped('budget_applied')
        )

        available_budget = project_type_budget - allocated_budget

        if available_budget < 0:
            available_budget = 0

        return {
            'domain': {
                'project_id': [('id', 'in', project_type_data.project_ids.ids)]
            }
        }

    # ---------- FEES STRUCTURE ACTION ----------

    def action_fees_structure(self):

        project_type_data = self.project_types

        fees_employed = project_type_data.fees_employed.ids
        fees_unemployed = project_type_data.fees_unemployed.ids

        if self.fees_employed:
            self.with_context(from_get_fees=True).write({
                'fees_employed': [(2, f.id) for f in self.fees_employed]
            })

        if self.fees_unemployed:
            self.with_context(from_get_fees=True).write({
                'fees_unemployed': [(2, f.id) for f in self.fees_unemployed]
            })

        if fees_employed or fees_unemployed:

            self.with_context(from_get_fees=True).write({
                'fees_employed': [
                    (0, 0, {'course_id': fees_id, 'project_emp_id': self.id})
                    for fees_id in fees_employed
                ],
                'fees_unemployed': [
                    (0, 0, {'course_id': fees_id, 'project_unemp_id': self.id})
                    for fees_id in fees_unemployed
                ]
            })

        else:
            raise UserError(
                _('Fees structure not defined for %s') % project_type_data.name
            )

        self.write({'fees_defined': True})

        return True

    # ---------- CREATE OVERRIDE ----------

    @api.model
    def create(self, vals):

        res = super(ProjectProject, self).create(vals)

        project_type_data = res.project_types

        if res.budget == 0 and res.budget_applied:
            raise UserError(
                _('You dont have more budget to allocate for %s!')
                % project_type_data.name.name
            )

        if res.budget_applied > res.budget:
            raise UserError(_('You can not apply more budget than exists!'))

        # DATE VALIDATIONS

        if res.start_date and res.end_date:

            if res.start_date > res.end_date:
                raise UserError(
                    _("Project End Date should be greater than Start Date")
                )

            if res.eoi_start_date and res.eoi_end_date:

                if res.eoi_start_date > res.eoi_end_date:
                    raise UserError(
                        _("EOI End Date should be greater than Start Date")
                    )

        return res

    # ---------- WRITE OVERRIDE ----------

    def write(self, vals):

        res = super(ProjectProject, self).write(vals)

        for record in self:

            project_type_data = record.project_types

            if record.budget == 0 and vals.get('budget_applied'):
                raise UserError(
                    _('You dont have more budget to allocate for %s!')
                    % project_type_data.name
                )

            if record.budget_applied > record.budget:
                raise UserError(
                    _('You can not apply more budget than exists!')
                )

            # FEES VALIDATION

            total_fees_employed = sum(
                record.fees_employed.mapped('course_amount')
            ) * record.target_employed_learner

            total_fees_unemployed = sum(
                record.fees_unemployed.mapped('course_amount')
            ) * record.target_unemployed_learner

            total_fees = total_fees_employed + total_fees_unemployed

            if record.budget_applied < total_fees:
                raise UserError(
                    _('Your fees according to targeted learner is more than Budget Applied!')
                )

        return res

    # ---------- UPDATE TO EOI ----------

    def update_to_eoi(self):

        for employer_approval in self.employer_request_ids:

            enrollment_projects = employer_approval.enroll_project_id

            enrollment_projects.write({
                'employed': employer_approval.app_employed,
                'non_employed': employer_approval.app_unemployed,
                'state': 'approved'
            })

        return True

    # ---------- HELPER METHOD ----------

    def get_calculated_emp(self, req_learners, min_range, max_range, percentage_allocated):

        no_of_learners = float(percentage_allocated) / 100 * req_learners

        if round(no_of_learners % 1, 1) >= 0.5:
            return int(no_of_learners) + 1

        return int(no_of_learners)

    # ---------- COMPUTE ALLOCATION ----------

    def compute_allocation(self):

        eoi_approval_data = self.env['eoi.approval.criteria'].search([
            ('project_id', '=', self.id),
            ('funding_year', '=', self.seta_funding_year.id)
        ], limit=1)

        if not eoi_approval_data:
            raise UserError(
                _('Please define EOI Approval Criteria for project %s!')
                % self.name
            )

        total_request_employed = sum(
            int(x.req_employed) for x in self.employer_request_ids
        )

        total_request_unemployed = sum(
            int(x.req_unemployed) for x in self.employer_request_ids
        )

        for emp_req in self.employer_request_ids:

            emp_req.write({
                'ratio_req_employed': emp_req.req_employed,
                'ratio_req_unemployed': emp_req.req_unemployed
            })

        self.write({'update_toeoi': True})

        return True


class EmployerRequests(models.Model):
    _name = 'employer.requests'
    _description = 'Employer Requests'

    employer_id = fields.Many2one(
        'res.partner',
        string='Employer',
        domain=[('employer', '=', True)]
    )

    req_employed = fields.Integer(string='Requested Employed')
    req_unemployed = fields.Integer(string='Requested Unemployed')

    ratio_req_employed = fields.Integer(string='Ratio Requested Employed')
    ratio_req_unemployed = fields.Integer(string='Ratio Requested Unemployed')

    app_employed = fields.Integer(string='Approved Employed')
    app_unemployed = fields.Integer(string='Approved Unemployed')

    cost_required = fields.Float(
        string='Cost Reqd',
        compute='_get_total_cost',
        store=True
    )

    enroll_project_id = fields.Many2one(
        'enrollment.projects',
        string='Project Enrollment in EOI'
    )

    project_id = fields.Many2one(
        'project.project',
        string='Project'
    )

    eoi_id = fields.Many2one(
        'learning.programme',
        string='Related EOI'
    )

    # ---------- COMPUTE METHODS ----------

    @api.depends('app_employed', 'app_unemployed', 'project_id')
    def _get_total_cost(self):

        for record in self:

            total = 0

            if (record.app_employed or record.app_unemployed) and record.project_id:

                project_data = record.project_id

                total_employed = sum(
                    project_data.fees_employed.mapped('course_amount')
                ) * record.app_employed

                total_unemployed = sum(
                    project_data.fees_unemployed.mapped('course_amount')
                ) * record.app_unemployed

                total = total_employed + total_unemployed

            record.cost_required = total

class EnrollmentProjects(models.Model):
    _name = 'enrollment.projects'
    _description = 'Enrollment Projects'

    employer_id = fields.Many2one(
        'res.partner',
        string='Employer',
        domain=[('employer', '=', True)]
    )

    project_types = fields.Many2one(
        'hwseta.project.types',
        string="Project"
    )

    project_id = fields.Many2one(
        'project.project',
        string='Project'
    )

    black = fields.Integer(string="Black")
    coloured = fields.Integer(string="Coloured")
    indian = fields.Integer(string="Indian")

    req_employed = fields.Integer(string="No of Employed (18.1)")
    req_unemployed = fields.Integer(string="No of Unemployed (18.2)")

    employed = fields.Integer(string="Employed")
    non_employed = fields.Integer(string="Non Employed")

    no_of_persons = fields.Integer(
        string='Total Number of Learners Approved',
        compute='_compute_total_persons',
        store=True
    )

    persons_approved = fields.Integer(string='Persons Granted')

    learnership_id = fields.Many2one(
        'learning.programme',
        string='Learnership'
    )

    status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('evaluation', 'Evaluation'),
            ('approved', 'Approved'),
            ('final_approval', 'Final Approval'),
        ],
        string="State",
        default='pending'
    )

    provider_id = fields.Many2one(
        'res.partner',
        string="HWSETA Training Provider",
        tracking=True,
        domain=[('provider', '=', True)]
    )

    provider = fields.Char("Other Provider")

    provider_campus_id = fields.Many2one(
        'res.partner',
        string='Training Provider Campus'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pending_approval', 'Pending Approval'),
            ('approved', 'Approved')
        ],
        string='Status',
        default='draft'
    )

    qualifications = fields.Many2many(
        'provider.qualification',
        'learning_programme_qualification_rel',
        'learning_programme_id',
        'qualification_id',
        string='Qualifications'
    )

    # ---------- COMPUTE METHODS ----------

    @api.depends('employed', 'non_employed')
    def _compute_total_persons(self):

        for record in self:
            record.no_of_persons = record.employed + record.non_employed

    # ---------- ONCHANGE METHODS ----------

    @api.onchange('req_employed')
    def onchange_req_employed(self):
        if self.req_employed > 0:
            self.req_unemployed = 0

    @api.onchange('req_unemployed')
    def onchange_req_unemployed(self):
        if self.req_unemployed > 0:
            self.req_employed = 0

    @api.onchange('project_id')
    def onchange_project_id(self):

        if not self.project_id:
            return

        provider_ids = self.env['partner.project.rel'].search([
            ('pro_project_id', '=', self.project_id.id)
        ]).filtered(lambda r: r.provider_id and r.select_pro)

        return {
            'domain': {
                'provider_id': [('id', 'in', provider_ids.mapped('provider_id').ids)]
            }
        }

class SdpLearnerAttachment(models.Model):
    _name = "sdp.learner.attachment"
    _description = "SDP Learner Attachment"

    name = fields.Char('Document Name', required=True)

    data = fields.Binary('File', required=True)

    learner_attach_id = fields.Many2one(
        'sdp.learner',
        string='Document Upload',
        ondelete='cascade'
    )

class ProjectEnrolled(models.Model):
    _name = 'project.enrolled'
    _description = 'Project Enrolled'

    project_id = fields.Many2one(
        'project.project',
        string="Project"
    )

    project_type = fields.Many2one(
        'hwseta.project.types',
        string="Project Types"
    )

    provider_id = fields.Many2one(
        'res.partner',
        string="Provider",
        domain=[('provider', '=', True)]
    )

    sdp_learner_id = fields.Many2one(
        'sdp.learner',
        string="SDP Learner"
    )

class SdpLearner(models.Model):
    _name = 'sdp.learner'
    _description = 'Sdp Learner'

    select_learner_info = fields.Boolean(
        string='Please select to include this learner while loading learners'
    )

    seq_no = fields.Char(string='Agreement No')

    learner_id = fields.Many2one(
        'learning.programme',
        string='Learning Programme',
        ondelete='cascade'
    )

    learner_attachment_ids = fields.One2many(
        'sdp.learner.attachment',
        'learner_attach_id',
        string='Document Upload'
    )

    surname = fields.Char(string='Surname')
    middle_name = fields.Char(string='Middle Name')

    work_email = fields.Char(string='Email', tracking=True)
    work_phone = fields.Char(string='Phone', tracking=True)

    financial_year = fields.Datetime(string='Enrollment Year', tracking=True)

    initials = fields.Char(string='Initials', tracking=True)

    passport_id = fields.Char(string='Passport No', tracking=True)

    id_document = fields.Many2one(
        'ir.attachment',
        string='ID Document'
    )

    identity_number = fields.Char(string='Identity Number')

    cell = fields.Char(string='Mobile Number')

    date_of_birth = fields.Date(string='Date of Birth')

    project_id = fields.Many2one(
        'project.project',
        string='Projects'
    )

    proj_enrolled_ids = fields.One2many(
        'project.enrolled',
        'sdp_learner_id',
        string="Projects for EOI"
    )

    created = fields.Boolean(string='Created', default=True)

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user
    )

    req_for_approve = fields.Boolean(
        "Request for Approval",
        default=False
    )

    state = fields.Selection([
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('dropout', 'Drop Out'),
        ('replacement', 'Replacement'),
        ('suspended', ' Suspended'),
        ('inactive', 'In Active'),
    ], string='Status', default='pending', tracking=True)

    current_status = fields.Selection([
        ('req_active', 'Request For Active'),
        ('req_in_active', 'Request For In Active'),
        ('req_drop_out', 'Request For Drop Out'),
        ('req_replacement', 'Request For Replacement'),
        ('req_suspend', 'Request For Suspended'),
        ('wait_active', 'Waiting For Active'),
        ('wait_in_active', 'Waiting For In Active'),
        ('wait_drop_out', 'Waiting For Drop Out'),
        ('wait_replacement', 'Waiting For Replacement'),
        ('wait_suspend', 'Waiting For Suspended'),
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('in_active', 'In Active'),
        ('drop_out', 'Drop Out'),
        ('replacement', 'Replacement'),
        ('suspend', 'Suspended'),
    ], string='Current Status', default='req_active')
    employee_type = fields.Selection([('employed','Employed'),('unemployed','Unemployed')])
    name = fields.Char(string='Name')
    attached_report = fields.Binary(string="Agreement")
    learner_reg_no = fields.Char(string='Learner Reg No')
    loaded = fields.Boolean(string='Loaded')
    person_title = fields.Selection([('adv', 'Adv.'), ('dr', 'Dr.'),('mr', 'Mr.'),('mrs', 'Mrs.'), ('ms', 'Ms.'), ('prof', 'Prof.')], string='Title', track_visibility='onchange')
    maiden_name = fields.Char(string='Maiden Name')
    certificate_no = fields.Char(string='Certificate No')
    african = fields.Boolean(string='African')
    business_tel_no = fields.Char(string='Business Tel No')
    fax_no = fields.Char(string='Fax No')
    method_of_communication = fields.Selection([('cell_phone','Cell Phone'),('email','Email')],string='Method of Communication')
    nationality_id = fields.Many2one('res.country', string='Nationality')
    learner_status = fields.Selection([('achieved', 'Achieved')], 'Learner Status')
    status_effective_date = fields.Date(string='Status Effective Date')
    status_reason = fields.Selection([('workplace_learning', '500 - Workplace learning')], 'Learner Status Reason')
    sponsorship = fields.Selection([('funded', 'Funded'), ('nonfunded', 'Non-Funded')], 'Sponsorship')
    wsp_year = fields.Selection([('2015', '2015'), ('2016', '2016')], 'WSP Year')
    status_comments = fields.Text('Status Comments')
    record_last_updated = fields.Datetime('Record Last Updated')
    last_updated_operator = fields.Char(string='Last Updated Operator')

    equity = fields.Selection([('black_african', 'Black: African'), ('black_indian', 'Black: Indian / Asian'),
                               ('black_coloured', 'Black: Coloured'), ('other', 'Other'), ('unknown', 'Unknown'),
                               ('white', 'White')], string='Equity')
    marital = fields.Selection(
        [('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'), ('widow', 'Widow'),
         ('divorced', 'Divorced')], 'Marital Status', track_visibility='onchange')
    socio_economic_saqa_code = fields.Selection(
        [('1', '01'), ('2', '02'), ('3', '03'), ('4', '04'), ('6', '06'), ('7', '07'), ('8', '08'), ('9', '09'),
         ('10', '10'), ('97', '97'), ('98', '98'), ('U', 'U')], string='Socio Economic Status SAQA Code')
    disability_status = fields.Selection([
        ('sight', 'Sight ( even with glasses )'),
        ('hearing', 'Hearing ( even with h.aid )'),
        ('communication', 'Communication ( talk/listen)'),
        ('physical', 'Physical ( move/stand, etc)'),
        ('intellectual', 'Intellectual ( learn,etc)'),
        ('emotional', 'Emotional ( behav/psych)'),
        ('multiple', 'Multiple'),
        ('disabled', 'Disabled but unspecified'),
        ('none', 'None'), ], string='Disability Status')
    alternate_identity_no = fields.Char(string='Alternate identity No')

    title = fields.Char(string='Title')
    detials_surname = fields.Char(string='Surname')
    rsa_identity_no = fields.Char(string='RSA Identity No', size=13)
    citizen_residential_status = fields.Selection(
        [('dual', 'D - Dual (SA plus other)'), ('other', 'O - Other'), ('sa', 'SA - South Africa'),
         ('unknown', 'U - Unknown')], string='Citizen Status')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    dissability = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Dissability')
    home_language = fields.Many2one('res.lang', string='Home Language Code', track_visibility='onchange', size=6)
    highest_education = fields.Selection(
        [('abet_level_1', 'Abet Level 1'), ('abet_level_2', 'Abet Level 2'), ('abet_level_3', 'Abet Level 3'),
         ('abet_level_4', 'Abet Level 4'), ('nqf123', 'NQF 1,2,3'), ('nqf45', 'NQF 4,5'), ('nqf67', 'NQF 6,7'),
         ('nqf8910', 'NQF 8,9,10')], string='Highest Education')
    email = fields.Char(string='Email')

    learner_home_address_1 = fields.Char(string='Home Address 1', track_visibility='onchange', size=50)
    learner_home_address_2 = fields.Char(string='Home Address 2', track_visibility='onchange', size=50)
    learner_home_address_3 = fields.Char(string='Home Address 3', track_visibility='onchange', size=50)
    learner_postal_address_1 = fields.Char(string='Postal Address 1', track_visibility='onchange', size=50)
    learner_postal_address_2 = fields.Char(string='Postal Address 2', track_visibility='onchange', size=50)
    learner_postal_address_3 = fields.Char(string='Postal Address 3', track_visibility='onchange', size=50)
    learner_home_suburb = fields.Many2one('res.suburb', string='Home Suburb')
    learner_home_municipality = fields.Many2one('res.municipality', string='Municipality')
    learner_postal_suburb = fields.Many2one('res.suburb', string='Postal Suburb')
    learner_postal_municipality = fields.Many2one('res.municipality', string='Municipality')
    learner_home_city = fields.Many2one('res.city', string='Home City', track_visibility='onchange')
    learner_postal_city = fields.Many2one('res.city', string='Postal City', track_visibility='onchange')
    learner_home_zip = fields.Char(string='Home Zip', track_visibility='onchange')
    learner_postal_zip = fields.Char(string='Postal Zip', track_visibility='onchange')
    learner_country_home = fields.Many2one('res.country', string='Home Country', track_visibility='onchange')
    learner_country_postal = fields.Many2one('res.country', string='Postal Country', track_visibility='onchange')
    learner_home_province_code = fields.Many2one('res.country.state', string='Home Province Code',
                                                 track_visibility='onchange')
    learner_postal_province_code = fields.Many2one('res.country.state', string='Postal Province Code',
                                                   track_visibility='onchange')
    same_as_home = fields.Boolean(string='Same As Home Address')
    # Rating

    seeing_rating_id = fields.Selection(
        [('1', 'No difficulty'), ('2', 'Some difficulty'), ('3', 'A lot of difficulty'), ('4', 'Cannot do at all'),
         ('6', 'Cannot yet be determined'), ('60', 'May be part of multiple difficulties (TBC)'),
         ('70', 'May have difficulty (TBC)'), ('80', 'Former difficulty - none now')], string='Seeing Rating Id',
        track_visibility='onchange')
    hearing_rating_id = fields.Selection(
        [('1', 'No difficulty'), ('2', 'Some difficulty'), ('3', 'A lot of difficulty'), ('4', 'Cannot do at all'),
         ('6', 'Cannot yet be determined'), ('60', 'May be part of multiple difficulties (TBC)'),
         ('70', 'May have difficulty (TBC)'), ('80', 'Former difficulty - none now')], string='Hearing Rating Id',
        track_visibility='onchange')
    walking_rating_id = fields.Selection(
        [('1', 'No difficulty'), ('2', 'Some difficulty'), ('3', 'A lot of difficulty'), ('4', 'Cannot do at all'),
         ('6', 'Cannot yet be determined'), ('60', 'May be part of multiple difficulties (TBC)'),
         ('70', 'May have difficulty (TBC)'), ('80', 'Former difficulty - none now')], string='Walking Rating Id',
        track_visibility='onchange')
    remembering_rating_id = fields.Selection(
        [('1', 'No difficulty'), ('2', 'Some difficulty'), ('3', 'A lot of difficulty'), ('4', 'Cannot do at all'),
         ('6', 'Cannot yet be determined'), ('60', 'May be part of multiple difficulties (TBC)'),
         ('70', 'May have difficulty (TBC)'), ('80', 'Former difficulty - none now')], string='Remembering Rating Id',
        track_visibility='onchange')
    statssa_area_code = fields.Integer(string='STATSSA Area Code', track_visibility='onchange', size=20)
    popi_act_status_date = fields.Date(string='POPI Act Status Date', track_visibility='onchange')
    communicating_rating_id = fields.Selection(
        [('1', 'No difficulty'), ('2', 'Some difficulty'), ('3', 'A lot of difficulty'), ('4', 'Cannot do at all'),
         ('6', 'Cannot yet be determined'), ('60', 'May be part of multiple difficulties (TBC)'),
         ('70', 'May have difficulty (TBC)'), ('80', 'Former difficulty - none now')], string='Communicating Rating Id',
        track_visibility='onchange')
    self_care_rating_id = fields.Selection(
        [('1', 'No difficulty'), ('2', 'Some difficulty'), ('3', 'A lot of difficulty'), ('4', 'Cannot do at all'),
         ('6', 'Cannot yet be determined'), ('60', 'May be part of multiple difficulties (TBC)'),
         ('70', 'May have difficulty (TBC)'), ('80', 'Former difficulty - none now')], string='Self Care Rating Id',
        track_visibility='onchange')
    last_school_emis_no = fields.Char(string='Last School EMIS No', track_visibility='onchange', size=20)
    last_school_year = fields.Integer(string='Last School Year', track_visibility='onchange', size=4)
    popi_act_status_id = fields.Integer(string='POPI Act Status Id', track_visibility='onchange', size=2)
    date_stamp = fields.Date(string='Date Stamp', track_visibility='onchange')

    # ---------- BUTTON ACTIONS ----------

    def action_active_button(self):
        self.write({'current_status': 'req_active', 'req_for_approve': False})

    def action_dropout_button(self):
        self.write({'current_status': 'req_drop_out', 'req_for_approve': False})

    def action_replacement_button(self):
        self.write({'current_status': 'req_replacement', 'req_for_approve': False})

    def action_suspend_button(self):
        self.write({'current_status': 'req_suspend', 'req_for_approve': False})

    def action_inactive_button(self):
        self.write({'current_status': 'req_in_active', 'req_for_approve': False})

    # ---------- VALIDATIONS ----------

    @api.onchange('work_phone', 'cell', 'fax_no', 'work_email', 'business_tel_no')
    def onchange_validate_number(self):

        if self.work_email and '@' not in self.work_email:
            self.work_email = False
            return {'warning': {
                'title': 'Invalid input',
                'message': 'Please enter valid email address'
            }}

        for field in ['work_phone', 'cell', 'business_tel_no']:
            value = getattr(self, field)

            if value and (not value.isdigit() or len(value) != 10):
                setattr(self, field, False)
                return {'warning': {
                    'title': 'Invalid input',
                    'message': 'Please enter 10 digits number'
                }}

    # ---------- APPROVAL LOGIC ----------

    def action_approve_button(self):

        if self.current_status == 'wait_active':
            self.write({'current_status': 'active', 'state': 'active'})

        elif self.current_status == 'wait_in_active':
            self.write({'current_status': 'in_active', 'state': 'inactive'})

        elif self.current_status == 'wait_drop_out':
            self.write({'current_status': 'drop_out', 'state': 'dropout'})

        elif self.current_status == 'wait_replacement':
            self.write({'current_status': 'replacement', 'state': 'replacement'})

        elif self.current_status == 'wait_suspend':
            self.write({'current_status': 'suspend', 'state': 'suspended'})

        return True

    def action_reject_button(self):
        self.write({'current_status': self.state})
        return True

    def action_request_for_approve(self):

        self.write({'req_for_approve': True})

        mapping = {
            'req_active': 'wait_active',
            'req_in_active': 'wait_in_active',
            'req_drop_out': 'wait_drop_out',
            'req_replacement': 'wait_replacement',
            'req_suspend': 'wait_suspend'
        }

        if self.current_status in mapping:
            self.write({'current_status': mapping[self.current_status]})

        return True

    # ---------- CREATE OVERRIDE ----------

    @api.model
    def create(self, vals):

        if not vals.get('seq_no'):
            vals['seq_no'] = self.env['ir.sequence'].next_by_code('sdp.learner')

        return super(SdpLearner, self).create(vals)

class EoiMoa(models.Model):
    _name = 'eoi.moa'
    _description = 'EOI MOA'

    name = fields.Char(string='Name')

    learning_programme_id = fields.Many2one(
        'learning.programme',
        string='Name'
    )

    attach_moa = fields.Many2one(
        'ir.attachment',
        string='MOA'
    )

    status = fields.Selection(
        [
            ('pending', 'Pending For Acceptance'),
            ('accepted', 'Accepted'),
        ],
        string="State",
        default='pending'
    )

class EoiDocument(models.Model):
    _name = 'eoi.document'
    _description = 'EOI Document'

    name = fields.Many2one(
        'project.document',
        string="Document Name"
    )

    learning_programme_id = fields.Many2one(
        'learning.programme',
        string='Name'
    )

    attached = fields.Binary(string='attach')

    attach_doc = fields.Many2one(
        'ir.attachment',
        string='Attach Document'
    )

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def default_get(self, fields_list):

        res = super(IrAttachment, self).default_get(fields_list)

        if self._context.get('moa'):
            res.update({'name': 'MOA'})

        return res

class TrancheGeneration(models.Model):
    _name = 'tranche.generation'
    _description = 'Tranche Generation'

    name = fields.Char("Name")

    tranche_id = fields.Integer("Tranche id")

    number = fields.Integer("Tranche Number")

    employed_unemployed = fields.Char("18.1/18.2")

    approve_transche = fields.Boolean(
        "Tranche generated",
        default=False
    )

    reject_transche = fields.Boolean(
        "Reject Tranche",
        default=False
    )

    recommend_transche = fields.Boolean(
        "Recommend Tranche",
        default=False
    )

    learning_program_id = fields.Many2one(
        'learning.programme',
        string="Learning Program"
    )

    monitor_and_evaluate_id = fields.Many2one(
        'monitor.and.evaluate',
        string="Monitor and Evaluate"
    )

    status = fields.Char("Status")

    # ---------- RECOMMEND TRANCHE ----------

    def action_recommend_transche(self):

        transche = self.env['transche.payment'].browse(self.tranche_id)

        transche_document_ids = [
            document.name.id
            for document in transche.tranche_document_ids
            if document.required
        ]

        if self.learning_program_id and not self.monitor_and_evaluate_id:

            learning_program = self.learning_program_id

            for document in learning_program.document_ids:

                if document.name.id in transche_document_ids and not document.attach_doc:
                    raise UserError(
                        _('Please upload the %s document!')
                        % document.name.name
                    )

        if self.monitor_and_evaluate_id and not self.learning_program_id:

            monitor_and_evaluate = self.monitor_and_evaluate_id

            for documents in monitor_and_evaluate.monitor_and_evaluate_document_ids:

                if documents.name.id in transche_document_ids and not documents.attach_doc:
                    raise UserError(
                        _('Please upload the %s document!')
                        % documents.name.name
                    )

        self.write({
            'recommend_transche': True,
            'status': 'Recommended'
        })

        return True

    # ---------- APPROVE TRANCHE ----------

    def action_approve_transche(self):

        if self.learning_program_id and not self.monitor_and_evaluate_id:

            learning_program = self.learning_program_id
            employer_data = learning_program.employer_id

            for project_data in learning_program.enroll_project_ids:

                project_info = project_data.project_id

                model_data = self.env['ir.model'].search([
                    ('model', '=', 'learning.programme')
                ], limit=1)

                transche_payment_data = self.env['transche.payment'].search([
                    ('project_id', '=', project_info.id),
                    ('trigger_jv', '=', model_data.id),
                    ('id', '=', self.tranche_id)
                ])

                if not transche_payment_data:
                    raise UserError(
                        _('No Tranche Payment Configuration defined for project %s for EOI!')
                        % project_info.name
                    )

                category_type = learning_program.learning_project_id.category_type

                if category_type == '18.1':
                    self.env['transche.payment'].transche_payment_jv(
                        project_data,
                        employer_data,
                        '- Tranche Payment for EOI ' + learning_program.name,
                        transche_payment_data,
                        'employed'
                    )

                if category_type == '18.2':
                    self.env['transche.payment'].transche_payment_jv(
                        project_data,
                        employer_data,
                        '- Tranche Payment for EOI ' + learning_program.name,
                        transche_payment_data,
                        'unemployed'
                    )

        if self.monitor_and_evaluate_id and not self.learning_program_id:

            monitor_and_evaluate = self.monitor_and_evaluate_id
            employer_data = monitor_and_evaluate.employer_id

            for project_data in monitor_and_evaluate.project_info_ids:

                project_info = project_data.project_id

                model_data = self.env['ir.model'].search([
                    ('model', '=', 'monitor.and.evaluate')
                ], limit=1)

                transche_payment_data = self.env['transche.payment'].search([
                    ('project_id', '=', project_info.id),
                    ('trigger_jv', '=', model_data.id),
                    ('id', '=', self.tranche_id)
                ])

                if not transche_payment_data:
                    raise UserError(
                        _('No Tranche Payment Configuration defined for project %s for Monitoring and Evaluation!')
                        % project_info.name
                    )

                category_type = monitor_and_evaluate.project_id.category_type

                if category_type == '18.1':
                    self.env['transche.payment'].transche_payment_jv(
                        project_data,
                        employer_data,
                        '- Tranche Payment for Monitoring and Evaluation ' + monitor_and_evaluate.name,
                        transche_payment_data,
                        'employed'
                    )

                if category_type == '18.2':
                    self.env['transche.payment'].transche_payment_jv(
                        project_data,
                        employer_data,
                        '- Tranche Payment for Monitoring and Evaluation ' + monitor_and_evaluate.name,
                        transche_payment_data,
                        'unemployed'
                    )

        self.write({
            'approve_transche': True,
            'status': 'Approved'
        })

        return True

    # ---------- REJECT TRANCHE ----------

    def action_reject_transche(self):

        self.write({
            'reject_transche': True,
            'status': 'Rejected'
        })

        return True

class LearningProgramme(models.Model):
    _name = 'learning.programme'
    _inherit = ['mail.thread']
    _description = 'Learning Programme'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        result = super(LearningProgramme, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

        for rec in result:
            if 'eoi_id_reference' in rec:

                records = self.search([
                    ('eoi_id_reference', '=', rec['eoi_id_reference'])
                ])

                rec['eoi_id_reference_count'] = len(records)

        return result


    @api.model
    def _default_employer(self):

        user = self.env.user

        if user.partner_id and user.partner_id.employer:
            return user.partner_id.id

        return False

    
    name = fields.Char(
        string='Leanership name',
        tracking=True,
        default='/'
    )

    employer_id = fields.Many2one(
        'res.partner',
        string="Employer",
        domain=[('employer', '=', True)],
        default=_default_employer,
        tracking=True
    )

    category = fields.Many2one(
        'hwseta.project.category',
        string='Project Category'
    )

    category_type = fields.Selection(
        [('18.1', 'Employed Learners (18.1)'),
         ('18.2', 'Unemployed Learners (18.2)')],
        string="Category Type"
    )

    enroll_project_ids = fields.One2many(
        'enrollment.projects',
        'learnership_id',
        string='Project Enrollments'
    )

    state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('submitted', 'Submitted'),
            ('evaluation', 'Evaluation'),
            ('recommended', 'Recommended'),
            ('conditional_approval', 'Conditional Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('final_approval', 'Completed'),
        ],
        string="State",
        default='pending',
        tracking=True
    )

    submitted = fields.Boolean(string='Submitted')
    approved = fields.Boolean(string='Approved')
    evaluate = fields.Boolean(string='Evaluated')
    recommend = fields.Boolean(string='Recomended')
    cond_approved = fields.Boolean(string='Conditional Approved')

    learner_ids = fields.One2many(
        'sdp.learner',
        'learner_id',
        string='Learner'
    )

    moa_ids = fields.One2many(
        'eoi.moa',
        'learning_programme_id',
        string='MOA'
    )

    document_ids = fields.One2many(
        'eoi.document',
        'learning_programme_id',
        string='Documents'
    )

    learning_program_tranche_ids = fields.One2many(
        'tranche.generation',
        'learning_program_id',
        string="Tranche Generation"
    )

    learning_project_type_id = fields.Many2one(
        'hwseta.project.types',
        string="Project Type"
    )

    learning_project_id = fields.Many2one(
        'project.project',
        string="Project"
    )

    eoi_id_reference = fields.Char(
        related='learning_project_id.eoi_id.eoi_id',
        store=True,
        readonly=True
    )
    rejected1 = fields.Boolean(string='Rejected1')
    learner_loaded = fields.Boolean(string='Learner Loaded')
    is_moa_attached = fields.Boolean(string='MOA Attached')
    accept_moa = fields.Boolean(string='MOA Accepted')
    conditional_approval = fields.Boolean("Conditional Approval", default=False)
    employer_sdl_no = fields.Char(string='SDL No.',track_visibility='onchange', size=10)
    empl_sic_code = fields.Many2one('hwseta.sic.master', string='SIC Code')
    employer_site_no = fields.Char(string='Site No.',track_visibility='onchange', size=10)
    employer_seta_id = fields.Many2one('seta.branches', string='SETA Id',track_visibility='onchange')
    employer_registration_number = fields.Char(string='Registration Number',track_visibility='onchange', size=20)
    employer_trading_name = fields.Char(string='Employer Trading Name',track_visibility='onchange', size=70)
    date_of_enroll = fields.Date(string='Date', default=datetime.now())
    eoi_status_ids = fields.One2many('eoi.status', 'eoi_id', string='EOI Status')

    attach_moa = fields.Binary(string='Attach MOA', nodrop=True)
    attach_moa2 = fields.Binary(string='Attach MOA', nodrop=True)
    requested_empl = fields.Char(string="Requested 18.1")
    requested_non_empl = fields.Char(string="Requested 18.2")
    approved_empl = fields.Char(string="Approved 18.1")
    approved_non_empl = fields.Char(string="Approved 18.2")
    accepted_empl = fields.Char(string="Accepted 18.1")
    accepted_non_empl = fields.Char(string="Accepted 18.2")
    granted_total_req = fields.Integer(string="Granted Req")
    granted_total_app = fields.Char(string="Granted App")
    granted_total_acc = fields.Char(string="Granted Acc")
    ## for final approval
    final_empl = fields.Char(string="Final 18.1")
    final_non_empl = fields.Char(string="Final 18.2")
    granted_total_final = fields.Char(string="Granted Final")
    enroll_status = fields.Char(string='Status', default='Pending')
    show_moa = fields.Boolean(string='Show MOA')
    comment = fields.Text(string='Reason')
    rejected2 = fields.Boolean(string='Rejected2')

    @api.onchange('learning_project_type_id')
    def onchange_default_project_type(self):

        if self.learning_project_type_id:

            projects = self.env['project.project'].search([
                ('project_types', '=', self.learning_project_type_id.id)
            ])

            return {
                'domain': {
                    'learning_project_id': [('id', 'in', projects.ids)]
                }
            }
    
    @api.onchange('attach_moa')
    def onchange_attach_moa(self):
        """Copying MOA attached by SDP Manager to Employer MOA"""
        if self.attach_moa:
            self.attach_moa2 = self.attach_moa
        
    @api.onchange('employer_id')
    def onchange_employer_id(self):
        if not self.employer_id:
            return

        employer = self.employer_id

        self.employer_sdl_no = employer.employer_sdl_no
        self.employer_site_no = employer.employer_site_no
        self.employer_seta_id = employer.employer_seta_id.id if employer.employer_seta_id else False
        self.empl_sic_code = employer.empl_sic_code.id if employer.empl_sic_code else False
        self.employer_registration_number = employer.employer_registration_number
        self.employer_trading_name = employer.employer_registration_number

    def action_calculate_moa(self):

        record = self[:1]

        return {
            'name': 'Attach',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'moa.attachment',
            'target': 'new',
            'context': {
                **self.env.context,
                'eoi_id': record.id
            },
        }

    def compute_total_learners(self):

        for record in self:

            learner_obj = self.env['sdp.learner']

            # Remove existing learners linked to this record
            existing_learners = learner_obj.search([('learner_id', '=', record.id)])
            if existing_learners:
                existing_learners.unlink()

            learner_lines = []

            for project_data in record.enroll_project_ids:

                project_dict = {
                    'project_id': project_data.project_id.id if project_data.project_id else False,
                    'project_type': project_data.project_types.id if project_data.project_types else False,
                    'provider_id': project_data.provider_id.id if project_data.provider_id else False
                }

                # Create employed learners
                for i in range(project_data.employed):
                    learner_lines.append((0, 0, {
                        'learner_id': record.id,
                        'employee_type': 'employed',
                        'proj_enrolled_ids': [(0, 0, project_dict)]
                    }))

                # Create unemployed learners
                for i in range(project_data.non_employed):
                    learner_lines.append((0, 0, {
                        'learner_id': record.id,
                        'employee_type': 'unemployed',
                        'proj_enrolled_ids': [(0, 0, project_dict)]
                    }))

            if learner_lines:
                record.write({'learner_ids': learner_lines})

        return True

    def get_list(self, list_val):
        ret_list = []
        for req_em in list_val:
            if req_em:
                ret_list.append(req_em)
        return ret_list

    def write(self, vals):

        res = super(learning_programme, self).write(vals)

        for record in self:

            status = ''
            context = self.env.context

            if vals.get('state') == "evaluation":
                status = 'evaluation'
            elif vals.get('state') == 'approved':
                status = 'approved'
            elif vals.get('state') == 'final_approval':
                status = 'final_approval'

            count = 0

            for project_data in record.enroll_project_ids:

                req_empl = []
                req_non_empl = []
                app_empl = []
                app_non_empl = []
                fin_empl = []
                fin_non_empl = []

                if record.requested_empl and record.requested_non_empl and \
                        record.approved_empl and record.approved_non_empl and \
                        record.final_empl and record.final_non_empl:

                    req_empl = record.get_list(record.requested_empl.split(','))
                    req_non_empl = record.get_list(record.requested_non_empl.split(','))
                    app_empl = record.get_list(record.approved_empl.split(','))
                    app_non_empl = record.get_list(record.approved_non_empl.split(','))
                    fin_empl = record.get_list(record.final_empl.split(','))
                    fin_non_empl = record.get_list(record.final_non_empl.split(','))

                    if status == 'evaluation' and int(req_empl[count]) != 0 and int(req_non_empl[count]) != 0:
                        project_data.write({
                            'employed': int(req_empl[count]),
                            'non_employed': int(req_non_empl[count])
                        })

                    if status == 'approved' and int(app_empl[count]) != 0 and int(app_non_empl[count]) != 0:
                        project_data.write({
                            'employed': int(app_empl[count]),
                            'non_employed': int(app_non_empl[count])
                        })

                    if status == 'final_approval' and int(fin_empl[count]) != 0 and int(fin_non_empl[count]) != 0:
                        project_data.write({
                            'employed': int(fin_empl[count]),
                            'non_employed': int(fin_non_empl[count])
                        })

                project_data.write({'status': status})
                count += 1

                if not project_data.project_id.fees_employed and project_data.req_employed > 0:
                    raise UserError(_('Sorry! Employed learner can not apply for this project!'))

                if not project_data.project_id.fees_unemployed and project_data.req_unemployed > 0:
                    raise UserError(_('Sorry! Unemployed learner can not apply for this project!'))

            # Auto create proj_enrolled_ids if missing
            for learner in record.learner_ids:

                if not learner.proj_enrolled_ids:

                    for project_data in record.enroll_project_ids:
                        project_dict = {
                            'project_id': project_data.project_id.id if project_data.project_id else False,
                            'project_type': project_data.project_types.id if project_data.project_types else False,
                            'provider_id': project_data.provider_id.id if project_data.provider_id else False
                        }

                        learner.write({
                            'proj_enrolled_ids': [(0, 0, project_dict)]
                        })

            # State transition protections
            if context.get('submit'):
                pass

            if record.state == "evaluation" and not record.submitted:
                raise UserError(_('Sorry! You can not change the status to evaluation.'))

            if record.state == "approved" and not record.approved:
                raise UserError(_('Sorry! You can not change the status to approved.'))

            if record.state == "rejected" and not (record.rejected1 or record.rejected2):
                raise UserError(_('Sorry! You can not change the status to rejected.'))

            if record.state == "final_approval" and (record.rejected1 or record.rejected2):
                raise UserError(_('Sorry! You can not change the status to done.'))

            if record.state == "final_approval" and not record.learner_loaded:
                raise UserError(_('Sorry! You can not change the status to done.'))

            if record.state == "approved" and (record.rejected1 or record.rejected2):
                raise UserError(_('Sorry! You can not change the status to approve.'))

        return res

    @api.model
    def create(self, vals):

        if not vals.get('name') or vals.get('name') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('learning.programme') or '/'

        return super(LearningProgramme, self).create(vals)

    
    def action_submit_learnership(self):

        if self.submitted:
            raise UserError(_('Information Already Submitted!'))

        if not self.enroll_project_ids:
            raise UserError(_('Please enter project related information!.'))

        self.write({
            'submitted': True,
            'state': 'submitted'
        })

        self.env['eoi.status'].create({
            'user_id': self.env.uid,
            'state': 'submitted',
            'eoi_id': self.id,
            'status': 'Submitted'
        })

        return True

    def action_evaluate(self):

        for record in self:
            record.with_context(evaluate=True).write({
                'evaluate': True,
                'state': 'evaluation',
                'enroll_status': 'Evaluated'
            })

            self.env['eoi.status'].create({
                'user_id': self.env.uid,
                'state': 'evaluated',
                'eoi_id': record.id,
                'comment': record.comment,
                'status': 'Evaluated',
            })

        return True

    def action_recommend(self):

        for record in self:
            record.with_context(evaluate=True).write({
                'recommend': True,
                'state': 'recommended',
                'enroll_status': 'Recommended'
            })

            self.env['eoi.status'].create({
                'user_id': self.env.uid,
                'state': 'recommended',
                'eoi_id': record.id,
                'comment': record.comment,
                'status': 'Recommended',
            })

        return True
    
    def action_cond_approve(self):

        for project in self.enroll_project_ids:
            if project.state != 'approved':
                raise UserError(
                    _('Please approve all projects first!')
                )

        self.write({
            'cond_approved': True,
            'state': 'conditional_approval'
        })

        return True

    def action_conditional_approval(self):
        """
        Send conditional approval email with MOA template attachments
        """

        template = self.env.ref(
            'hwseta_sdp.email_template_conditional_approval',
            raise_if_not_found=False
        )

        for record in self:

            if not record.learning_project_id:
                continue

            attachment_ids = []

            # Collect attachments safely
            if record.learning_project_id.moa_template:
                attachment_ids.append(record.learning_project_id.moa_template.id)

            if record.learning_project_id.conditional_approval_details:
                attachment_ids.append(record.learning_project_id.conditional_approval_details.id)

            if not template:
                raise UserError(_('Conditional Approval email template not found.'))

            # Attach files to template
            template.write({
                'attachment_ids': [(6, 0, attachment_ids)]
            })

            # Send email
            template.send_mail(record.id, force_send=True)

            # Update record status
            record.write({'conditional_approval': True})

            # Log EOI status
            self.env['eoi.status'].create({
                'user_id': self.env.uid,
                'state': 'conditional_approval',
                'eoi_id': record.id,
                'comment': record.comment,
                'status': 'Conditional Approval',
            })

        return True

    def action_approve_learnership(self):

        if not self.submitted:
            raise UserError(_('Information Not Submitted!'))

        if not self.moa_ids:
            raise UserError(_('Please attach MOA before Approval!'))

        self.write({
            'approved': True,
            'state': 'approved'
        })

        self.env['eoi.status'].create({
            'user_id': self.env.uid,
            'state': 'approved',
            'eoi_id': self.id,
            'status': 'Approved'
        })

        return True

    ## This method deny the learnership process.
    def action_deny_learnership(self):

        template = self.env.ref(
            'hwseta_sdp.email_template_eoi_rejection',
            raise_if_not_found=False
        )

        for record in self:

            # Send rejection email if template exists
            if template:
                template.send_mail(record.id, force_send=True)

            # Update learnership status
            record.write({
                'state': 'rejected',
                'enroll_status': 'Rejected',
                'rejected1': True
            })

            # Create status tracking entry
            self.env['eoi.status'].create({
                'user_id': self.env.uid,
                'state': 'rejected',
                'eoi_id': record.id,
                'comment': record.comment,
                'status': 'Rejected',
            })

        return True

    def action_deny_learnership2(self):

        template = self.env.ref(
            'hwseta_sdp.email_template_eoi_rejection',
            raise_if_not_found=False
        )

        for record in self:

            if template:
                template.send_mail(record.id, force_send=True)

            record.write({
                'state': 'rejected',
                'enroll_status': 'Rejected',
                'rejected2': True
            })

        return True

    def action_accept_moa(self):

        for record in self:

            eoi_moa_records = self.env['eoi.moa'].search([
                ('learning_programme_id', '=', record.id)
            ])

            if not eoi_moa_records:
                raise UserError(_('No MOA records found for this Learnership.'))

            for moa in eoi_moa_records:
                if not moa.attach_moa:
                    raise UserError(_('Please attach MOA before Approval!'))

            eoi_moa_records.write({'status': 'accepted'})

            record.write({'accept_moa': True})

        return True

    def action_load_learners(self):

        current_date = datetime.now()
        app_learner_count = 0

        # --------- VALIDATE PROJECT EXTENSION RULES ---------
        for enroll_data in self.enroll_project_ids:

            app_learner_count += enroll_data.no_of_persons

            if enroll_data.project_id:

                project_obj = enroll_data.project_id

                learner_extension = self.env['partner.project.rel'].search([
                    ('emp_project_id', '=', project_obj.id),
                    ('load_learner_ext_request', '=', True),
                    ('employer_id', '=', self.employer_id.id)
                ])

                if not learner_extension:
                    if project_obj.load_learner_end_date and current_date.date() > project_obj.load_learner_end_date:
                        raise UserError(
                            _('Please apply to load learner extension for project %s !') % (project_obj.name)
                        )

                if learner_extension and not learner_extension.load_learner_ext_date:
                    raise UserError(
                        _('Please contact HWSETA to load learner extension date for project %s !') % (project_obj.name)
                    )

        # --------- BASIC VALIDATIONS ---------
        if not self.learner_ids:
            raise UserError(_('Please enter Learners!'))

        learner_count = 0

        for learner_data in self.learner_ids:

            learner_count += 1

            if not (
                    learner_data.name or learner_data.surname or learner_data.identity_number or learner_data.citizen_residential_status):
                raise UserError(_('Please enter mandatory informations for learners before loading!'))

        if learner_count > app_learner_count:
            raise UserError(_('Sorry! You cant load more learners than approved'))

        # --------- PROCESS LEARNERS ---------
        learner_obj = self.env['hr.employee']

        for learner_data in self.learner_ids:

            if learner_data.select_learner_info and not learner_data.loaded and learner_data.current_status == 'active':

                # ----- MULTIPLE PROJECT TYPE CHECK -----
                project_types_ids = [
                    enrolled_proj.project_type.id
                    for enrolled_proj in learner_data.proj_enrolled_ids
                ]

                if len(set(project_types_ids)) > 1:
                    raise UserError(
                        _('Learner %s %s can not enroll for more than one Project Type!')
                        % (learner_data.name, learner_data.surname)
                    )

                # ----- CHECK EXISTING LEARNER -----
                learner_exist = learner_obj.search([
                    ('rsa_identity_no', '=', learner_data.identity_number),
                    ('is_learner', '=', True)
                ], limit=1)

                employer_list = [(0, 0, {
                    'employer_id': self.employer_id.id,
                    'sdl_no': self.employer_id.employer_sdl_no,
                    'seta_id': self.employer_id.employer_seta_id.id if self.employer_id.employer_seta_id else False,
                    'registration_number': self.employer_id.employer_registration_number,
                    'state': 'draft'
                })]

                if learner_exist:

                    employer_done = any(emp.state != 'draft' for emp in learner_exist.employer_ids)
                    agreement_done = any(agree.state != 'new' for agree in learner_exist.agreement_ids)

                    if employer_done and agreement_done:

                        learner_exist.write({
                            'latest_employer': self.employer_id.id,
                            'employer_ids': employer_list,
                        })

                    else:
                        raise UserError(_('Please complete assessment for learner %s') % learner_exist.name)

                else:

                    # --------- CREATE NEW LEARNER ---------
                    seq_no = self.env['ir.sequence'].next_by_code('learner.registration.sequence')

                    attachments = [
                        (0, 0, {
                            'name': attachment.name,
                            'data': attachment.data
                        })
                        for attachment in learner_data.learner_attachment_ids
                    ]

                    project_list = [
                        (0, 0, {
                            'project_id': p.project_id.id,
                            'project_type_id': p.project_id.project_types.id if p.project_id.project_types else False,
                            'project_budget': p.project_id.budget_applied,
                        })
                        for p in learner_data.proj_enrolled_ids
                    ]

                    learner_dict = {
                        'name': learner_data.name,
                        'work_email': learner_data.work_email,
                        'work_phone': learner_data.work_phone,
                        'equity': learner_data.equity,
                        'marital': learner_data.marital,
                        'disability_status': learner_data.disability_status,
                        'passport_id': learner_data.passport_id,
                        'initials': learner_data.initials,
                        'rsa_identity_no': learner_data.identity_number,
                        'learner_reg_no': seq_no,
                        'gender': learner_data.gender,
                        'highest_education': learner_data.highest_education,
                        'cell': learner_data.cell,
                        'learner_attachment_ids': attachments,
                        'is_learner': True,
                        'employer_ids': employer_list,
                        'latest_employer': self.employer_id.id,
                        'learning_programme_id': self.id,
                        'project_ids': project_list,
                        'socio_economic_status': learner_data.employee_type
                    }

                    learner_data.write({'learner_reg_no': seq_no})

                    hr_obj = learner_obj.create(learner_dict)

                    # ----- UPDATE FINAL EMP / UNEMP COUNTS -----
                    for project_data in self.enroll_project_ids:
                        fin_empl = self.final_empl or ','
                        fin_non_empl = self.final_non_empl or ','

                        self.write({
                            'final_empl': fin_empl + ',' + str(project_data.employed),
                            'final_non_empl': fin_non_empl + ',' + str(project_data.non_employed)
                        })

                    # ----- PROVIDER LINKING -----
                    provider_done = False

                    if learner_exist:
                        for provider in learner_exist.learner_pro_ids:
                            if provider.state != 'new':
                                provider_done = True

                    provider_list = [
                        (0, 0, {
                            'name': p.provider_id.name,
                            'provider_id': p.provider_id.id,
                            'state': 'new'
                        })
                        for p in learner_data.proj_enrolled_ids
                    ]

                    learner_data.write({'learner_pro_ids': provider_list})

                    # ----- PDF GENERATION -----
                    report = self.env.ref('hwseta_sdp.report_learner_agreement')

                    pdf_content, _ = report._render_qweb_pdf([hr_obj.id])

                    learner_data.write({
                        'attached_report': base64.b64encode(pdf_content),
                        'loaded': True
                    })

        # --------- FINAL STATUS UPDATE ---------
        loaded_learners = len(self.learner_ids.filtered(lambda l: l.loaded))

        if loaded_learners == len(self.learner_ids):
            self.env['eoi.status'].create({
                'user_id': self.env.uid,
                'state': 'final_approval',
                'eoi_id': self.id,
                'status': 'Completed',
            })

            self.write({
                'learner_loaded': True,
                'state': 'final_approval',
                'enroll_status': 'Completed'
            })

        return True
    

class PartnerProjectRel(models.Model):
    _inherit = 'partner.project.rel'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Override read_group to filter record count based on logged SDF user"""

        user = self.env.user

        if user.id != 1 and user.sdf_id:
            user_records = self.search([('create_uid', '=', user.id)])
            domain.append(('id', 'in', user_records.ids))

        return super(PartnerProjectRel, self).read_group(
            domain, fields, groupby,
            offset=offset, limit=limit,
            orderby=orderby, lazy=lazy
        )

    eoi_id_reference_new = fields.Char(
        related='emp_project_id.eoi_id_reference_invisible',
        store=True,
        readonly=True,
        copy=False
    )

class EoiStatus(models.Model):
    _name = 'eoi.status'
    _description = 'EOI Status Tracking'
    _order = 's_date desc'

    user_id = fields.Many2one(
        'res.users',
        string='Name'
    )

    state = fields.Selection([
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('evaluated', 'Evaluated'),
        ('recommended', 'Recommended'),
        ('conditional_approval', 'Conditional Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('final_approval', 'Completed'),
    ],
        string='State',
        index=True,
        readonly=True,
        default='pending',
        copy=False
    )

    status = fields.Char("Status")

    s_date = fields.Datetime(
        string='Date',
        default=lambda self: fields.Datetime.now()
    )

    update_date = fields.Datetime(
        string='Update Date',
        default=lambda self: fields.Datetime.now()
    )

    comment = fields.Char(string='Comment')

    eoi_id = fields.Many2one(
        'learning.programme',
        string='Learnership'
    )
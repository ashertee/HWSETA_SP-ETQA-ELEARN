from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MaeDocument(models.Model):
    _name = 'mae.document'
    _inherit = ['mail.thread']
    _description = 'Monitor and Evaluate Documents'

    name = fields.Many2one(
        'project.document',
        string="Document Name"
    )

    monitor_and_evalaute_id = fields.Many2one(
        'monitor.and.evaluate',
        string='Name'
    )

    attached = fields.Binary(
        string='Attach'
    )

    attach_doc = fields.Many2one(
        'ir.attachment',
        string='Attach Document'
    )


class MonitorAndEvaluate(models.Model):
    _name = 'monitor.and.evaluate'
    _inherit = ['mail.thread']
    _description = 'Monitor and Evaluate'

    project_id = fields.Many2one('project.project', string="Project")
    employer_id = fields.Many2one('res.partner', string="Employer")

    amount_approved = fields.Float(
        string="Amount Approved",
        compute="_compute_amount_approved",
        store=True
    )

    def get_related_employee(self):
        """Return the employee linked to current user"""
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id)
        ], limit=1)

        return employee.id if employee else False

    @api.depends('project_id', 'employer_id')
    def _compute_amount_approved(self):
        for record in self:
            amount_approved = 0.0

            if record.project_id and record.employer_id:
                employer_projects = self.env['employer.requests'].search([
                    ('project_id', '=', record.project_id.id),
                    ('employer_id', '=', record.employer_id.id)
                ])

                for employer_project in employer_projects:
                    amount_approved += employer_project.cost_required

            record.amount_approved = amount_approved

    @api.depends('project_id', 'employer_id', 'amount_approved')
    def _compute_amount_disbursed(self):
        for record in self:
            amount_disbursed = 0.0

            if record.project_id and record.employer_id:
                account_move_lines = self.env['account.move.line'].search([
                    ('project_id', '=', record.project_id.id),
                    ('partner_id', '=', record.employer_id.id)
                ])

                debits = sum(account_move_lines.mapped('debit'))
                credits = sum(account_move_lines.mapped('credit'))

                if debits == credits:
                    amount_disbursed = record.amount_approved - debits

            record.amount_disbursed = amount_disbursed

    @api.depends('amount_approved', 'amount_disbursed')
    def _compute_amount_outstanding(self):
        for record in self:
            if record.amount_approved and record.amount_disbursed:
                record.amount_outstanding = record.amount_approved - record.amount_disbursed
            else:
                record.amount_outstanding = 0.0

    @api.depends('project_id', 'employer_id')
    def _compute_employed(self):
        for record in self:
            employed = 0

            if record.project_id and record.employer_id:
                employer_projects = self.env['employer.requests'].search([
                    ('project_id', '=', record.project_id.id),
                    ('employer_id', '=', record.employer_id.id)
                ])

                for employer_project in employer_projects:
                    employed += employer_project.app_employed

            record.no_of_employed = employed

    @api.depends('project_id', 'employer_id')
    def _compute_unemployed(self):
        for record in self:
            unemployed = 0

            if record.project_id and record.employer_id:
                employer_projects = self.env['employer.requests'].search([
                    ('project_id', '=', record.project_id.id),
                    ('employer_id', '=', record.employer_id.id)
                ])

                for employer_project in employer_projects:
                    unemployed += employer_project.app_unemployed

            record.no_of_unemployed = unemployed

    @api.depends('no_of_employed', 'no_of_unemployed')
    def _compute_total_employed_unemployed(self):
        for record in self:
            record.total_employed_unemployed = (
                    record.no_of_employed + record.no_of_unemployed
            )

    name = fields.Char(string='Name')

    state = fields.Selection([
        ('org_and_proj', 'Organisation and Project Info'),
        ('quality', 'Quality Assurance'),
        ('administer', 'Administration'),
        ('finance', 'Finance Audit Programme'),
        ('learner_report', 'Learner Report'),
        ('project_evaluation', 'Project Evaluation'),
        ('overall_assess', 'Overall Assessment'),
        ('submitted', 'Submitted'),
        ('recommended', 'Recommended'),
        ('approved', 'Approved'),
    ], string="State", default='org_and_proj', tracking=True)

    # SECTION A : Organisational Details
    employer_id = fields.Many2one('res.partner', string='Name of Organisation')

    sdl_number = fields.Char(string='SDL No.', tracking=True)

    date_visit = fields.Date(string='Date Of Visit')

    me_conducted_by = fields.Char('M&E Conducted By')

    amount_approved = fields.Float(
        string='Amount Approved',
        compute='_compute_amount_approved',
        tracking=True,
        store=True
    )

    amount_disbursed = fields.Float(
        string='Amount Disbursed',
        compute='_compute_amount_disbursed',
        tracking=True,
        store=True
    )

    amount_outstanding = fields.Float(
        string='Amount Outstanding',
        compute='_compute_amount_outstanding',
        tracking=True,
        store=True
    )

    # SECTION B : DISCRETIONARY GRANT PROJECT INFORMATION
    project_info_ids = fields.One2many(
        'grant.project.info',
        'monitor_evaluate_id',
        string='Project Info'
    )

    commencement_date = fields.Date(string='Commencement Date', tracking=True)
    completion_date = fields.Date(string='Completion Date', tracking=True)

    dropouts_emplyed = fields.Integer(string='Employed 18.1')
    dropouts_unemplyed = fields.Integer(string='Unemployed 18.2')

    # SECTION C : Quality Assurance
    report_prepared = fields.Boolean(string='Report Prepared')
    regular_meeting = fields.Boolean(string='Regular Meeting')
    learner_dispute = fields.Boolean(string='Learner Dispute')
    project_reviewed = fields.Boolean(string='Project Reviewed')
    outcome_reviewed = fields.Boolean(string='Outcome Reviewed')

    comment_report_prepared = fields.Text(string='Comment Report Prepared')
    comment_regular_meeting = fields.Text(string='Comment Regular Meeting')
    comment_learner_dispute = fields.Text(string='Comment Learner Dispute')
    comment_project_reviewed = fields.Text(string='Comment Project Reviewed')
    comment_outcome_reviewed = fields.Text(string='Comment Outcome Reviewed')

    # SECTION D : Administration
    req_main_met = fields.Boolean(string='Req and Maintenance')
    req_main_not_met = fields.Boolean(string='Not Req and Maintenance')

    data_main_met = fields.Boolean(string='Database Maintenance')
    data_main_not_met = fields.Boolean(string='Not Database Maintenance')

    confi_rec_met = fields.Boolean(string='Confidentiality Rec')
    confi_rec_not_met = fields.Boolean(string='Not Confidentiality Rec')

    rep_adm_capmet = fields.Boolean(string='Reporting Capacity MET')
    rep_adm_not_capmet = fields.Boolean(string='Reporting Capacity not MET')

    assessor_avail_met = fields.Boolean(string='Assessor Availability MET')
    assessor_avail_not_met = fields.Boolean(string='Assessor Availability Not MET')

    moderator_avail_met = fields.Boolean(string='Moderator Availability MET')
    moderator_avail_not_met = fields.Boolean(string='Moderator Availability not MET')

    coach_met = fields.Boolean(string='Coaches MET')
    coach_not_met = fields.Boolean(string='Coaches not MET')

    role_player_met = fields.Boolean(string='Role Players MET')
    role_player_not_met = fields.Boolean(string='Role Players not MET')

    access_resource_met = fields.Boolean(string='Access Resource MET')
    access_resource_not_met = fields.Boolean(string='Access Resource not MET')

    train_met = fields.Boolean(string='Training MET')
    train_not_met = fields.Boolean(string='Training not MET')

    comment_learner = fields.Text(string='Comment Learner', tracking=True)
    comment_database = fields.Text(string='Comment Database', tracking=True)
    comment_access = fields.Text(string='Comment Access', tracking=True)
    comment_reporting = fields.Text(string='Comment Reporting', tracking=True)

    # SECTION E : Finance Audit Programme
    insti_have_moa = fields.Boolean(string='Have a Copy of MOA')
    signature_appear = fields.Boolean(string='Signature Appear')
    signatory_authority = fields.Boolean(string='Signatory Authority')
    read_content_moa = fields.Boolean(string='Read the Contents in the MOA')

    bank_sole_purpose = fields.Boolean(string='Bank Sole Purpose')
    bank_secure_stmt = fields.Boolean(string='Secure Bank Statement')

    list_receipt_bank_stmt = fields.Boolean(string='Receipts on Bank Statement')
    list_payment_bank_stmt = fields.Boolean(string='Payments on Bank Statement')

    # SECTION G
    indicator_no_of_learner = fields.Text(string='Number of Learners')
    indicator_no_of_dropouts = fields.Text(string='Number of Dropouts')

    area_of_concern = fields.Text(string='Areas of Concerns')
    professional_opinion = fields.Text(string='Professional Opinion')
    next_payment_process = fields.Text(string='Next Payment Process')

    compiled_by = fields.Many2one(
        'res.users',
        string='Compiled By',
        default=lambda self: self.env.user
    )

    compiled_date = fields.Date(
        string='Date',
        default=fields.Date.today
    )

    provincial_manager_name = fields.Many2one(
        'res.users',
        string='Name',
        default=lambda self: self.env.user,
        tracking=True
    )

    prov_man_date = fields.Date(
        string='Date',
        default=fields.Date.today
    )

    project_man_date = fields.Date(
        string='Date',
        default=fields.Date.today
    )

    approved_learn = fields.Integer(string='Approved', tracking=True)
    not_approved_learn = fields.Integer(string='Not Approved')

    monitor_and_evaluate_ids = fields.One2many(
        'tranche.generation',
        'monitor_and_evaluate_id',
        string="Monitoring Tranche",
        tracking=True
    )

    attach_transche = fields.Boolean("Attach Tranche", default=False)
    attach_document = fields.Boolean("Document")

    monitor_and_evaluate_document_ids = fields.One2many(
        'mae.document',
        'monitor_and_evalaute_id',
        string="ME Document"
    )

    funding_year = fields.Many2one(
        'account.fiscal.year',
        string='Funding Year'
    )

    project_type_id = fields.Many2one('hwseta.project.types', string="Project Type")

    project_id = fields.Many2one('project.project', string="Project")

    no_of_employed = fields.Integer(
        "Employed 18.1",
        compute='_compute_employed',
        store=True
    )

    no_of_unemployed = fields.Integer(
        "Unemployed 18.2",
        compute='_compute_unemployed',
        store=True
    )

    total_employed_unemployed = fields.Integer(
        "Total",
        compute='_compute_total_employed_unemployed',
        store=True
    )

    submit = fields.Boolean("Submit", tracking=True)
    recommend = fields.Boolean("Recommend", tracking=True)
    approve = fields.Boolean("Approve", tracking=True)

    comment_assessor = fields.Text(string='Comment Assessor', track_visibility='onchange')
    comment_moderator = fields.Text(string='Comment Moderator', track_visibility='onchange')
    comment_coaches = fields.Text(string='Comment Coaches', track_visibility='onchange')
    comment_role = fields.Text(string='Comment Role', track_visibility='onchange')
    comment_resource = fields.Text(string='Comment Resource', track_visibility='onchange')
    comment_training = fields.Text(string='Comment Training', track_visibility='onchange')

    comment_insti_have_moa = fields.Text(string='Have a Copy of MOA')
    comment_signature_appear = fields.Text(string='Signature Appear')
    comment_signatory_authority = fields.Text(string='Signatory Authority')
    comment_read_content_moa = fields.Text(string='Read the Contents in the MOA')
    comment_bank_sole_purpose = fields.Text(string='Bank Sole Purpose')
    comment_bank_secure_stmt = fields.Text(string='Secure Bank Statement')
    comment_list_receipt_bank_stmt = fields.Text(string='List reseipt reflected on the bank statement')
    comment_list_payment_bank_stmt = fields.Text(string='List payment reflected on the bank statement')

    comment_abt_hwseta_prog = fields.Text(string='About HWSETA Programmes')
    comment_abt_satisfy_info = fields.Text(string='About HWSETA Satisfy Info')
    comment_abt_sign_contract = fields.Text(string='About Signed Contract')
    comment_abt_contract_about = fields.Text(string='What the Contract About')
    comment_abt_improve_recruit = fields.Text(string='About Improvement in Recruitment and Selection')
    comment_abt_theoretical_comp = fields.Text(string='About where theoretical training takes place')
    comment_abt_training_lang = fields.Text(string='About where training language')
    comment_abt_week_month_allowance = fields.Text(string='About Weekly or Monthly Allowance')
    comment_abt_supervisor_advice = fields.Text(string='About Supervisor advice during Training')
    comment_abt_overtime = fields.Text(string='About Overtime')
    comment_abt_received_uniforms = fields.Text(string='About Received Uniforms')
    comment_abt_received_books = fields.Text(string='About Received Books')
    comment_abt_remark = fields.Text(string='About Remark')

    indicator_factors_success = fields.Text(string='Factors Success/Failure')
    indicator_financial_performance = fields.Text(string='Financial Performance')
    action_evaluate_success = fields.Text(string='Financial Performance')
    action_no_of_learner = fields.Text(string='Number of Learners')
    action_no_of_dropouts = fields.Text(string='Number of Dropouts')
    action_factors_success = fields.Text(string='Factors Success/Failure')
    action_financial_performance = fields.Text(string='Financial Performance')

    related_employee1 = fields.Many2one('hr.employee', string='Employee',
                                        default=lambda self: self.get_related_employee())

    related_emplyee = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    #     prov_man_sign = fields.Binary(string='Signature')
    related_employee2 = fields.Many2one('hr.employee', string='Employee2',
                                        default=lambda self: self.get_related_employee())
    project_man_sign = fields.Binary(string='Signature')


    @api.onchange('funding_year')
    def onchange_funding_year(self):
        if not self.funding_year:
            return {
                'domain': {
                    'project_type_id': [('id', 'in', [])]
                }
            }

        project_types = self.env['hwseta.project.types'].search([
            ('seta_funding_year', '=', self.funding_year.id)
        ])

        return {
            'domain': {
                'project_type_id': [('id', 'in', project_types.ids)]
            }
        }

    @api.onchange('project_type_id')
    def onchange_project_type(self):
        if not self.project_type_id:
            return {
                'domain': {
                    'project_id': [('id', 'in', [])]
                }
            }

        projects = self.env['project.project'].search([
            ('project_types', '=', self.project_type_id.id)
        ])

        return {
            'domain': {
                'project_id': [('id', 'in', projects.ids)]
            }
        }

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('monitor.and.evaluate.ref') or '/'

        return super().create(vals)

    def write(self, vals):
        for record in self:
            if not self._context.get('button', False):

                if not record.submit and vals.get('state') in ['submitted', 'recommended', 'approved']:
                    raise Warning(_('Sorry! First Submit the Monitoring and Evaluation!!!!'))

                if not record.recommend and vals.get('state') in ['recommended', 'approved']:
                    raise Warning(_('Sorry! First Recommend the Monitoring and Evaluation!!!!'))

        return super().write(vals)

    def action_submit_mae(self):
        self = self.with_context(button=True)
        self.write({
            'submit': True,
            'state': 'submitted'
        })
        return True

    def action_recommend_mae(self):
        self = self.with_context(button=True)
        self.write({
            'recommend': True,
            'state': 'recommended'
        })
        return True

    def action_approve_mae(self):
        self = self.with_context(button=True)
        self.write({
            'approve': True,
            'state': 'approved'
        })
        return True

    def action_get_transche(self):
        for record in self:

            if not record.project_id:
                raise Warning(_('Please select project for Monitor and Evaluate!'))

            project = record.project_id

            tranche_domain = [
                ('project_id', '=', project.id),
                ('trigger_jv', '=', 'monitor.and.evaluate'),
                ('funding_year', '=', project.seta_funding_year.id)
            ]

            tranche_ids = self.env['transche.payment'].search(tranche_domain)

            # Clear existing lines
            if record.monitor_and_evaluate_ids:
                record.write({
                    'monitor_and_evaluate_ids': [(5, 0, 0)]
                })

            if not tranche_ids:
                raise Warning(_('Please configure tranche for project %s!') % (project.name))

            tranche_list = []

            for tranche in tranche_ids:

                if project.category_type == '18.1':
                    number = tranche.no_of_tranche

                elif project.category_type == '18.2':
                    number = tranche.no_of_tranche_18_2

                else:
                    continue

                tranche_list.append((0, 0, {
                    'name': tranche.name,
                    'number': number,
                    'monitor_and_evaluate_id': record.id,
                    'tranche_id': tranche.id
                }))

            record.write({
                'monitor_and_evaluate_ids': tranche_list,
                'attach_transche': True
            })

        return True

    def action_get_document(self):
        for record in self:

            if not record.project_id:
                raise Warning(_('Please select project for Monitor and Evaluate!'))

            project = record.project_id

            tranche_domain = [
                ('project_id', '=', project.id),
                ('trigger_jv', '=', 'monitor.and.evaluate'),
                ('funding_year', '=', project.seta_funding_year.id)
            ]

            tranche_ids = self.env['transche.payment'].search(tranche_domain)

            document_ids = set()

            for tranche in tranche_ids:
                for document in tranche.tranche_document_ids:
                    document_ids.add(document.name.id)

            # Remove old documents
            if record.monitor_and_evaluate_document_ids:
                record.write({
                    'monitor_and_evaluate_document_ids': [(5, 0, 0)]
                })

            # Create new document lines
            document_list = [
                (0, 0, {
                    'name': doc_id,
                    'monitor_and_evaluate_id': record.id
                }) for doc_id in document_ids
            ]

            record.write({
                'monitor_and_evaluate_document_ids': document_list,
                'attach_document': True
            })

        return True

    @api.onchange('employer_id')
    def _onchange_employer_id(self):
        if self.employer_id:
            self.sdl_number = self.employer_id.employer_sdl_no
        else:
            self.sdl_number = False
    

class GrantProjectInfo(models.Model):
    _name = 'grant.project.info'
    _description = 'Grant Project Information'

    type_of_project = fields.Selection([
        ('learnership', 'Learnerships'),
        ('bursaries', 'Bursaries'),
        ('skills_programmes', 'Skills Programmes'),
        ('artisans', 'Artisans'),
        ('levy_exempt', 'Levy Exempt'),
    ], string='Project Type')

    type_of_projects = fields.Many2one(
        'hwseta.project.types',
        string='Project Type'
    )

    project_id = fields.Many2one(
        'project.project',
        string='Discretionary Grant Name'
    )

    mark_x = fields.Boolean(string='Mark X')

    funding_year = fields.Char(string='Funding Year')

    employed = fields.Integer(string='Employed 18.1')

    unemployed = fields.Integer(string='Unemployed 18.2')

    total = fields.Integer(
        string='Total',
        compute='_compute_total_persons',
        store=True
    )

    monitor_evaluate_id = fields.Many2one(
        'monitor.and.evaluate',
        string='Monitor and Evaluate'
    )

    @api.depends('employed', 'unemployed')
    def _compute_total_persons(self):
        for record in self:
            record.total = (record.employed or 0) + (record.unemployed or 0)
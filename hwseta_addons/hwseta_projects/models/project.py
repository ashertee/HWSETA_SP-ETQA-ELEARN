from odoo import models, fields, api, _


class ProjectProject(models.Model):
    _inherit = 'project.project'
    

    total_targeted_learner = fields.Integer(
        string='Total Targeted Learners',
        compute='_compute_total_targeted_learner',
        store=True
    )

    @api.depends('target_employed_learner', 'target_unemployed_learner')
    def _compute_total_targeted_learner(self):
        """Calculate total number of targeted learners for the project"""
        for record in self:
            record.total_targeted_learner = (
                record.target_employed_learner + record.target_unemployed_learner
            )

    decommitted_fund = fields.Float(
        string='Decommitted Fund',
        compute='_compute_decommitted_fund',
        store=False
    )

    budget_committed = fields.Float(
        string='Budget Committed',
        compute='_compute_budget_committed',
        store=False
    )
    
    @api.depends('budget_applied')
    def _compute_decommitted_fund(self):
        for record in self:
            decommitted = 0.0

            if record.budget_applied:
                move_lines = self.env['account.move.line'].search([
                    ('project_id', '=', record.id),
                    ('move_id.state', '=', 'posted')
                ])

                debit = sum(move_lines.mapped('debit'))
                credit = sum(move_lines.mapped('credit'))

                if debit == credit:
                    decommitted = record.budget_applied - debit

            record.decommitted_fund = decommitted


    def _compute_budget_committed(self):
        for record in self:
            record.budget_committed = sum(
                record.employer_request_ids.mapped('cost_required')
            ) if record.employer_request_ids else 0.0
 
        
    def _compute_balance_due(self):
        """Calculate balance due for the project"""
        for record in self:
            balance_due = 0.0

            if record.budget_committed and record.analytic_account_id:
                lines = self.env['account.move.line'].search([
                    ('analytic_account_id', '=', record.analytic_account_id.id),
                    ('move_id.state', '=', 'posted'),
                ])

                debit = sum(lines.mapped('debit'))
                credit = sum(lines.mapped('credit'))

                if debit == credit:
                    balance_due = record.budget_committed - debit

            record.balance_due = balance_due


    def _compute_invoice_to_date(self):
        """Calculate invoice to date for the project"""
        for record in self:
            invoice_to_date = 0.0

            if record.analytic_account_id:
                lines = self.env['account.move.line'].search([
                    ('analytic_account_id', '=', record.analytic_account_id.id),
                    ('move_id.state', '=', 'posted'),
                ])

                debit = sum(lines.mapped('debit'))
                credit = sum(lines.mapped('credit'))

                if debit == credit:
                    invoice_to_date = debit

            record.invoice_to_date = invoice_to_date      
        

    @api.depends('budget_applied', 'budget_committed')
    def _compute_project_balance(self):
        """Calculate project budget balance"""
        for record in self:
            record.project_balance = (
                record.budget_applied - record.budget_committed
                if record.budget_applied
                else 0.0
            )
    number = fields.Char(string='Number')
    funding = fields.Float(string='Funding Value')
    milestones = fields.Float(string='Milestones')

    
    invoice_to_date = fields.Float(
    string='Invoice To Date',
    compute='_compute_invoice_to_date',
    store=False
    )
    
    def _compute_invoice_to_date(self):
        for record in self:
            total = 0.0

            if record.id:
                move_lines = self.env['account.move.line'].search([
                    ('project_id', '=', record.id),
                    ('move_id.state', '=', 'posted')
                ])

                debit = sum(move_lines.mapped('debit'))
                credit = sum(move_lines.mapped('credit'))

                if debit == credit:
                    total = debit

            record.invoice_to_date = total
            
    seta_funding_year = fields.Char(string='Funding Year')

    project_balance = fields.Float(
        string='Budget Balance',
        compute='_compute_project_balance',
        store=True
    )

    comment = fields.Text(string='Executive Summary')

    project_parent_id = fields.Many2one(
        'project.project',
        string='Parent Project',
        ondelete='cascade'
    )

    sub_project_ids = fields.One2many(
        'project.project',
        'project_parent_id',
        string='Sub Projects'
    )

    course_fee = fields.Float(string='Course Fee')
    allowance = fields.Float(string='Allowance')
    uniform = fields.Float(string='Uniform')

    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    project_description = fields.Html(string='Description')
    
    project_id = fields.Many2one(
        'hwseta.project',
        string='Project Name'
    )

    budget = fields.Float(string='Budget Available')
    budget_applied = fields.Float(string='Budget Allocated')
    approved_amount = fields.Float(string="Approved Amount")

    eoi_start_date = fields.Datetime(string='EOI Start Date')
    eoi_end_date = fields.Datetime(string='EOI End Date')

    load_learner_start_date = fields.Datetime(string='Load Learner Start Date')
    load_learner_end_date = fields.Datetime(string='Load Learner End Date')

    no_of_tranche = fields.Integer(string='Number of Tranche (18.1)')
    no_of_tranche_18_2 = fields.Integer(string='Number of Tranche (18.2)')

    target_employed_learner = fields.Integer(string='Target Learner (18.1)')
    target_unemployed_learner = fields.Integer(string='Target Learner (18.2)')

    total_targeted_learner = fields.Integer(
        string='Total Targeted Learners',
        compute='_compute_total_targeted_learner',
        store=True
    )

    decommitted_fund = fields.Float(
        string='Decommitted Fund',
        compute='_compute_decommitted_fund',
        store=True
    )

    project_terms_and_condition = fields.Many2one(
        'ir.attachment',
        string='Guideline to Application'
    )

    budget_committed = fields.Float(
        string='Budget Committed',
        compute='_compute_budget_committed',
        store=True
    )

    training_provider_applicable = fields.Boolean(
        string='Training Provider Applicable'
    )

    moa_template = fields.Many2one(
        'ir.attachment',
        string='MOA Template'
    )

    conditional_approval_details = fields.Many2one(
        'ir.attachment',
        string='Conditional Approval Details'
    )

    balance_due = fields.Float(
        string='Balance Due',
        compute='_compute_balance_due',
        store=True
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
        string='Category Type'
    )

    # Provider Groups
    provider_hwseta_group = fields.Boolean(string='HWSETA')
    provider_dhet_group = fields.Boolean(string='DHET')
    provider_hpcsa_group = fields.Boolean(string='HPCSA')
    provider_otherseta_group = fields.Boolean(string='Other SETA')
    provider_che_group = fields.Boolean(string='CHE')
    provider_sanc_group = fields.Boolean(string='SANC')
    provider_sapc_group = fields.Boolean(string='SAPC')
    

    def _onchange_provider_group(self):
        """
        Filter and auto-populate providers based on selected provider groups
        """
        for record in self:
            domain = []

            if record.provider_hwseta_group:
                domain.append(('provider_hwseta_group', '=', True))
            if record.provider_dhet_group:
                domain.append(('provider_dhet_group', '=', True))
            if record.provider_hpcsa_group:
                domain.append(('provider_hpcsa_group', '=', True))
            if record.provider_otherseta_group:
                domain.append(('provider_otherseta_group', '=', True))
            if record.provider_che_group:
                domain.append(('provider_che_group', '=', True))
            if record.provider_sanc_group:
                domain.append(('provider_sanc_group', '=', True))
            if record.provider_sapc_group:
                domain.append(('provider_sapc_group', '=', True))

            if not domain:
                record.pro_ids = False
                return

            providers = self.env['res.partner'].search(domain)

            record.pro_ids = [
                (0, 0, {
                    'provider_id': provider.id,
                    'provider_accreditation_num': provider.provider_accreditation_num,
                    'project_description': record.project_description,
                })
                for provider in providers
            ]
    @api.onchange('category_type')
    def _onchange_category_type(self):
        """
        Filter project categories based on category type
        """
        if not self.category_type:
            self.category = False
            return {
                'domain': {'category': []}
            }

        categories = self.env['hwseta.project.category'].search([
            ('category_type', '=', self.category_type)
        ])

        return {
            'domain': {
                'category': [('id', 'in', categories.ids)]
            }
        }
            
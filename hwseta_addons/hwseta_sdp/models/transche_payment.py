from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from calendar import monthrange


# ---------------------------------------------------------
# Object State
# ---------------------------------------------------------
class ObjectState(models.Model):
    _name = 'object.state'
    _description = 'Object State'

    state_key = fields.Char(string='State Key')
    name = fields.Char(string='State Value')
    model_id = fields.Many2one(
        'ir.model',
        string='Model'
    )


# ---------------------------------------------------------
# Tranche Fees
# ---------------------------------------------------------
class TrancheFees(models.Model):
    _name = 'tranche.fees'
    _description = 'Tranche Fees'

    fees_id = fields.Many2one(
        'fees.structure',
        string='Fees Name'
    )
    percentage = fields.Float(
        string='Percentage (%)'
    )
    tranche_payment_id = fields.Many2one(
        'transche.payment',
        string='Related Tranche'
    )

    # Type of tranche
    tranche_type = fields.Selection(
        [
            ('percent', 'Percentage (%)'),
            ('month', 'Months')
        ],
        string="Tranche Type"
    )

    # Employee type
    employee_type = fields.Selection(
        [
            ('employed', 'Employed'),
            ('unemployed', 'Unemployed')
        ],
        string="18.1 / 18.2"
    )


# ---------------------------------------------------------
# Tranche Documents
# ---------------------------------------------------------
class HwsetaTrancheDocument(models.Model):
    _name = 'hwseta.tranche.document'
    _description = 'HWSETA Tranche Document'

    name = fields.Many2one(
        'project.document',
        string="Document Name"
    )
    required = fields.Boolean(
        string="Document Required"
    )
    tranche_payment_id = fields.Many2one(
        'transche.payment',
        string='Related Tranche'
    )

    trigger_jv = fields.Boolean(
        string="Trigger JV"
    )

    @api.model
    def default_get(self, fields_list):
        """Set trigger_jv from context"""
        res = super().default_get(fields_list)
        res['trigger_jv'] = self.env.context.get('trigger_jv', False)
        return res


class TranschePayment(models.Model):
    _name = 'transche.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Tranche Payment'

    # --------------------------------------------------
    # Basic Info
    # --------------------------------------------------
    name = fields.Char(
        string='Tranche Payment Number',
        tracking=True
    )
    active = fields.Boolean(default=True, help="Set to false to hide the record without deleting it.")

    trigger_jv = fields.Many2one(
        'ir.model',
        string='Trigger JV Action',
        tracking=True
    )

    object_state_id = fields.Many2one(
        'object.state',
        string='State',
        tracking=True
    )

    project_type = fields.Many2one(
        'hwseta.project.types',
        string='Project Type',
        tracking=True
    )

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True
    )

    # --------------------------------------------------
    # Fees & Accounting
    # --------------------------------------------------
    tranche_fees_ids = fields.One2many(
        'tranche.fees',
        'tranche_payment_id',
        string='Fees Structure'
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        tracking=True
    )

    emp_sdlno_cr_account_id = fields.Many2one(
        'account.account',
        string='Credit Account',
        tracking=True
    )

    disc_grant_dr_account_id = fields.Many2one(
        'account.account',
        string='Debit Account',
        tracking=True
    )

    disc_expense_acc = fields.Many2one(
        'account.account',
        string='Project Expense Account',
        tracking=True
    )

    # --------------------------------------------------
    # Category / Type
    # --------------------------------------------------
    employed_unemployed = fields.Selection(
        [
            ('employed', 'Employed'),
            ('unemployed', 'Unemployed')
        ],
        string='18.1 / 18.2'
    )

    get_fees = fields.Boolean(
        string="Get Fees",
        default=False
    )

    tranche_document_ids = fields.One2many(
        'hwseta.tranche.document',
        'tranche_payment_id',
        string='Tranche Documents'
    )

    no_of_tranche = fields.Integer(
        string="Tranche Number (18.1)"
    )

    no_of_tranche_18_2 = fields.Integer(
        string="Tranche Number (18.2)"
    )

    funding_year = fields.Many2one(
        'account.fiscalyear',
        string='Funding Year'
    )

    category_type = fields.Selection(
        [
            ('18.1', 'Employed Learners (18.1)'),
            ('18.2', 'Unemployed Learners (18.2)')
        ],
        string="Category Type"
    )

    category = fields.Many2one(
        'hwseta.project.category',
        string='Project Category'
    )

    # --------------------------------------------------
    # Business Logic
    # --------------------------------------------------
    def action_tranche_fees_structure(self):
        """
        Load fees structure based on Project
        """
        self.ensure_one()

        project = self.project_id
        if not project:
            raise UserError(_("Please select a Project first."))

        # Clear existing fees
        self.tranche_fees_ids.unlink()

        fees_employed = project.fees_employed.mapped('course_id').ids
        fees_unemployed = project.fees_unemployed.mapped('course_id').ids

        if not fees_employed and not fees_unemployed:
            raise UserError(
                _("Fees structure not defined for project %s") % project.name
            )

        vals = []

        for fee_id in fees_employed:
            vals.append({
                'fees_id': fee_id,
                'employee_type': 'employed',
            })

        for fee_id in fees_unemployed:
            vals.append({
                'fees_id': fee_id,
                'employee_type': 'unemployed',
            })

        self.write({
            'tranche_fees_ids': [(0, 0, v) for v in vals],
            'get_fees': True
        })

        return True

    # --------------------------------------------------
    # Onchange
    # --------------------------------------------------
    @api.onchange('funding_year')
    def _onchange_funding_year(self):
        if not self.funding_year:
            return {
                'domain': {
                    'project_type': []
                }
            }

        project_types = self.env['hwseta.project.types'].search([
            ('seta_funding_year', '=', self.funding_year.id)
        ])

        return {
            'domain': {
                'project_type': [('id', 'in', project_types.ids)]
            }
        }
        
    # 
    # def onchange_project_type(self, project_type) :
    #     res = {}
    #     if not project_type :
    #         res.update({'domain':{'project_id':[('id','in',[])]}})
    #         return res
    #     ##Onchange of project type filled projects in tranche
    #     project=[project.id for project in self.env['project.project'].search([('project_types','=',project_type)])]
    #     res.update({'domain':{'project_id':[('id','in',project)]},'value':{'get_fees':False}})
    #     ## Onchange of project type filled document required for tranche
    #     self.write({'tranche_document_ids' : [(2,tranche_data.id) for tranche_data in self.tranche_document_ids]})
    #     document_vals = [(0,0,{'name':document.name,'required':document.required}) for document in self.env['hwseta.project.document'].search([('project_type_id','=',project_type)]) ]
    #     res.update({'value':{ 'tranche_document_ids' : document_vals }})
    #     return res

    @api.onchange('project_type')
    def _onchange_project_type(self):
        if not self.project_type:
            self.project_id = False
            self.get_fees = False
            return {
                'domain': {
                    'project_id': []
                }
            }

        # ----------------------------------
        # Filter projects by project type
        # ----------------------------------
        projects = self.env['project.project'].search([
            ('project_types', '=', self.project_type.id)
        ])

        self.get_fees = False

        # ----------------------------------
        # Reset tranche documents
        # ----------------------------------
        self.tranche_document_ids = [(5, 0, 0)]

        documents = self.env['hwseta.project.document'].search([
            ('project_type_id', '=', self.project_type.id)
        ])

        self.tranche_document_ids = [
            (0, 0, {
                'name': doc.name.id,
                'required': doc.required,
            }) for doc in documents
        ]

        return {
            'domain': {
                'project_id': [('id', 'in', projects.ids)]
            }
        }

    @api.onchange('project_id')
    def _onchange_project(self):
        if not self.project_id:
            return

        project = self.project_id

        # ----------------------------------
        # Set category type & category
        # ----------------------------------
        self.category_type = project.category_type
        self.category = project.category.id if project.category else False

        # ----------------------------------
        # Calculate tranche number
        # ----------------------------------
        tranche_count = self.env['transche.payment'].search_count([
            ('project_id', '=', project.id)
        ])

        if project.category_type == '18.1':
            self.no_of_tranche = tranche_count + 1
            self.no_of_tranche_18_2 = False

        elif project.category_type == '18.2':
            self.no_of_tranche_18_2 = tranche_count + 1
            self.no_of_tranche = False

    @api.onchange('trigger_jv')
    def _onchange_trigger_jv(self):
        if not self.trigger_jv:
            return

        model = self.trigger_jv.model
        object_state_obj = self.env['object.state']

        # Get all fields of the target model
        model_fields = self.env[model].fields_get()

        # Check if model has a state field
        if 'state' not in model_fields:
            return

        # Get selection values of state field
        state_selection = model_fields['state'].get('selection', [])

        # Check existing object states
        existing_states = object_state_obj.search([
            ('model_id', '=', self.trigger_jv.id)
        ])

        if not existing_states:
            for key, value in state_selection:
                object_state_obj.create({
                    'state_key': key,
                    'name': value,
                    'model_id': self.trigger_jv.id,
                })

    @api.model
    def create(self, vals):
        # ----------------------------------
        # Generate Tranche Sequence
        # ----------------------------------
        vals['name'] = self.env['ir.sequence'].next_by_code('transche.payment')

        project = self.env['project.project'].browse(vals.get('project_id'))
        funding_year = vals.get('funding_year')

        if not project:
            return super().create(vals)

        # ----------------------------------
        # Validation for 18.1
        # ----------------------------------
        if vals.get('category_type') == '18.1':
            tranche_no = vals.get('no_of_tranche')
            if tranche_no:
                if tranche_no > project.no_of_tranche:
                    raise Warning(_(
                        "You can not create more than %s tranche for %s project!"
                    ) % (project.no_of_tranche, project.name))

        # ----------------------------------
        # Validation for 18.2
        # ----------------------------------
        if vals.get('category_type') == '18.2':
            tranche_no_18_2 = vals.get('no_of_tranche_18_2')
            if tranche_no_18_2:
                if tranche_no_18_2 > project.no_of_tranche_18_2:
                    raise Warning(_(
                        "You can not create more than %s tranche for %s project!"
                    ) % (project.no_of_tranche_18_2, project.name))

        return super().create(vals)

    def _get_move_line_vals(
        self,
        name,
        debit,
        credit,
        account_id,
        partner_id,
        ref_name,
        tranche_info
    ):
        """Prepare account.move.line values"""

        return {
            'name': name,
            'ref': ref_name,
            'debit': debit,
            'credit': credit,
            'date': fields.Date.today(),
            'partner_id': partner_id,
            'account_id': account_id,
            'project_id': tranche_info.project_id.id if tranche_info.project_id else False,
        }

    def _get_move_lines(
            self,
            credit_account,
            debit_account,
            fees_structure,
            total_fee,
            partner_id,
            ref_name,
            journal_item_name,
            tranche_info
    ):
        """
        Build move line commands for account.move
        """
        move_lines = []

        if fees_structure:
            for fee_name, fee_amount in fees_structure.items():
                line_vals = self._get_move_line_vals(
                    name=f"{journal_item_name} - {fee_name}",
                    debit=fee_amount,
                    credit=0.0,
                    account_id=debit_account,
                    partner_id=partner_id,
                    ref_name=ref_name,
                    tranche_info=tranche_info,
                )
                move_lines.append((0, 0, line_vals))

        # Credit total line
        credit_line_vals = self._get_move_line_vals(
            name='/',
            debit=0.0,
            credit=total_fee,
            account_id=credit_account,
            partner_id=partner_id,
            ref_name=ref_name,
            tranche_info=tranche_info,
        )
        move_lines.append((0, 0, credit_line_vals))

        return move_lines


    
    def transche_payment_invoice(
        self,
        projects_dict,
        employer_data,
        line_name,
        module_name=None,
    ):
        """
        Create Supplier Invoice for Tranche Payment
        """

        if not projects_dict:
            raise UserError(_("No project fee data found."))

        if not employer_data:
            raise UserError(_("Employer not found."))

        # -----------------------------------------
        # Get Purchase Journal
        # -----------------------------------------
        journal = self.env['account.journal'].search(
            [('journal_type', '=', 'purchase')],
            limit=1
        )

        if not journal:
            raise UserError(_("Purchase journal not found."))

        # -----------------------------------------
        # Prepare Invoice Lines
        # projects_dict format:
        # {
        #   'Project A': [{'product_id': 1, 'Fee1': 1000}],
        #   'Project B': [{'product_id': 2, 'Fee2': 2000}]
        # }
        # -----------------------------------------
        invoice_lines = []

        for project_name, fee_lines in projects_dict.items():
            for fee_dict in fee_lines:
                product_id = fee_dict.get('product_id')
                if not product_id:
                    continue

                for key, price in fee_dict.items():
                    if key == 'product_id':
                        continue

                    invoice_lines.append((
                        0, 0, {
                            'product_id': product_id,
                            'name': f"{line_name} for {key} (Project: {project_name})",
                            'quantity': 1.0,
                            'price_unit': price,
                        }
                    ))

        if not invoice_lines:
            raise UserError(_("No invoice lines generated."))

        # -----------------------------------------
        # Create Supplier Invoice
        # -----------------------------------------
        invoice_vals = {
            'move_type': 'in_invoice',
            'partner_id': employer_data.id,
            'journal_id': journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # -----------------------------------------
        # Post Invoice
        # -----------------------------------------
        invoice.action_post()

        return invoice

    def transche_payment_jv(self, project, employer_data, name, tranche_info, emp_status):
        """
        Create Journal Entries for Tranche Payment (Employed / Unemployed)
        """

        final_dict = tranche_info.calculate_tranche(
            project, employer_data, emp_status
        )

        if not final_dict:
            raise UserError(_("No tranche calculation found."))

        # ---------------------------------------------------
        # Get Purchase Journal
        # ---------------------------------------------------
        journal = self.env['account.journal'].search(
            [('journal_type', '=', 'purchase')],
            limit=1
        )
        if not journal:
            raise UserError(_("Purchase journal not found."))

        # ---------------------------------------------------
        # Get Levy / Provision Accounts
        # ---------------------------------------------------
        admin_config = self.env['leavy.income.config'].search([], limit=1)
        if not admin_config:
            raise UserError(_("Levy Income Configuration not found."))

        debit_account = tranche_info.disc_expense_acc
        credit_account = admin_config.disc_provision_acc

        if not debit_account or not credit_account:
            raise UserError(_("Debit or Credit account not configured."))

        # ---------------------------------------------------
        # Helper: Create Journal Entry
        # ---------------------------------------------------
        def _create_move(lines, ref):
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': journal.id,
                'date': fields.Date.today(),
                'ref': ref,
                'line_ids': lines,
            })
            move.action_post()
            return move

        # ---------------------------------------------------
        # EMPLOYED (18.1)
        # ---------------------------------------------------
        if final_dict.get('employed'):
            fees = final_dict['employed']
            total = reduce(lambda x, y: float(x) + float(y), fees.values())

            move_lines = []

            # Debit lines (expense)
            for fee_name, amount in fees.items():
                move_lines.append((0, 0, {
                    'name': f"{name} - {fee_name}",
                    'debit': amount,
                    'credit': 0.0,
                    'account_id': debit_account.id,
                    'partner_id': employer_data.id,
                    'project_id': tranche_info.project_id.id,
                }))

            # Credit line (provision)
            move_lines.append((0, 0, {
                'name': f"{name} - Employed",
                'debit': 0.0,
                'credit': total,
                'account_id': credit_account.id,
                'partner_id': employer_data.id,
                'project_id': tranche_info.project_id.id,
            }))

            _create_move(move_lines, f"{name} for Employed")

        # ---------------------------------------------------
        # UNEMPLOYED (18.2)
        # ---------------------------------------------------
        if final_dict.get('unemployed'):
            fees = final_dict['unemployed']
            total = reduce(lambda x, y: float(x) + float(y), fees.values())

            move_lines = []

            for fee_name, amount in fees.items():
                move_lines.append((0, 0, {
                    'name': f"{name} - {fee_name}",
                    'debit': amount,
                    'credit': 0.0,
                    'account_id': debit_account.id,
                    'partner_id': employer_data.id,
                    'project_id': tranche_info.project_id.id,
                }))

            move_lines.append((0, 0, {
                'name': f"{name} - Unemployed",
                'debit': 0.0,
                'credit': total,
                'account_id': credit_account.id,
                'partner_id': employer_data.id,
                'project_id': tranche_info.project_id.id,
            }))

            _create_move(move_lines, f"{name} for Unemployed")

        return True

    def date_difference_month(self, start_date, end_date):
        """Return number of full months between two dates"""
        if not start_date or not end_date:
            return 0
        if start_date > end_date:
            return 0

        diff = relativedelta(end_date, start_date)
        return diff.years * 12 + diff.months or 1

    def calculate_tranche(self, project_datas, employer_data, emp_status):
        """
        Calculate tranche cost for employed (18.1) and unemployed (18.2)
        """

        project = project_datas.project_id
        if not project:
            raise UserError(_("Project not found."))

        # ----------------------------------------------------
        # Dates
        # ----------------------------------------------------
        if not project.start_date or not project.end_date:
            raise UserError(_("Project start/end date missing."))

        project_start = fields.Date.to_date(project.start_date)
        project_end = fields.Date.to_date(project.end_date)
        project_duration = self.date_difference_month(project_start, project_end)

        # ----------------------------------------------------
        # Employer Request
        # ----------------------------------------------------
        emp_request = self.env['employer.requests'].search([
            ('employer_id', '=', employer_data.id),
            ('project_id', '=', project.id)
        ], limit=1)

        if not emp_request:
            raise UserError(_("Employer request not found for project %s") % project.name)

        employed_learner = emp_request.app_employed or 0
        unemployed_learner = emp_request.app_unemployed or 0

        employed_cost = {}
        unemployed_cost = {}

        # ----------------------------------------------------
        # EMPLOYED (18.1)
        # ----------------------------------------------------
        if project.category_type == '18.1':

            if not project.fees_employed:
                raise UserError(_("Please configure employed fees for project %s") % project.name)

            if employed_learner <= 0:
                raise UserError(_("No approved employed learners found."))

            for fee in project.fees_employed:
                if fee.course_amount <= 0:
                    raise UserError(
                        _("Invalid course amount for %s") % fee.course_id.name
                    )

                base_amount = fee.course_amount * employed_learner

                for tranche_fee in self.tranche_fees_ids.filtered(
                        lambda x: x.employee_type == 'employed' and x.fees_id.name == fee.course_id.name
                ):
                    if tranche_fee.tranche_type == 'percent':
                        amount = (tranche_fee.percentage / 100) * base_amount
                    else:
                        amount = (base_amount / project_duration) * tranche_fee.percentage

                    employed_cost[fee.course_id.name] = amount

        # ----------------------------------------------------
        # UNEMPLOYED (18.2)
        # ----------------------------------------------------
        if project.category_type == '18.2':

            if not project.fees_unemployed:
                raise UserError(_("Please configure unemployed fees for project %s") % project.name)

            if unemployed_learner <= 0:
                raise UserError(_("No approved unemployed learners found."))

            for fee in project.fees_unemployed:
                if fee.course_amount <= 0:
                    raise UserError(
                        _("Invalid course amount for %s") % fee.course_id.name
                    )

                base_amount = fee.course_amount * unemployed_learner

                for tranche_fee in self.tranche_fees_ids.filtered(
                        lambda x: x.employee_type == 'unemployed' and x.fees_id.name == fee.course_id.name
                ):
                    if tranche_fee.tranche_type == 'percent':
                        amount = (tranche_fee.percentage / 100) * base_amount
                    else:
                        amount = (base_amount / project_duration) * tranche_fee.percentage

                    unemployed_cost[fee.course_id.name] = amount

        return {
            'employed': employed_cost,
            'unemployed': unemployed_cost,
        }

## Inheriting Class for Generating 1st Transche Payment.


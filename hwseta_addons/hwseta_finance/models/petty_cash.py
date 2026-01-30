from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    # hr.department is often used for branches in HWSETA/DHET contexts
    branch_id = fields.Many2one(
        'hr.department',
        string='Branch',
        domain=[('is_branch', '=', True)],
        tracking=True
    )
    province_id = fields.Many2one(
        'res.country.state',
        string='Province',
        tracking=True
    )

    # Overriding selection to include the multi-level approval workflow
    # Note: 'ondelete' is required in Odoo 18 when extending selections
    # state = fields.Selection(selection_add=[
    #     ('approve1', 'Approve by Accountant'),
    #     ('approve2', 'Approve by Financial Manager'),
    #     ('approve3', 'Approve by CFO'),
    # ], ondelete={
    #     'approve1': 'cascade',
    #     'approve2': 'cascade',
    #     'approve3': 'cascade'
    # })

    def approve_by_accountant(self):
        self.write({'state': 'approve1'})

    def approve_by_manager(self):
        self.write({'state': 'approve2'})

    def approve_by_cfo(self):
        self.write({'state': 'approve3'})


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    # Linking attachments directly to statement lines for audit trails
    docs = fields.Many2one('ir.attachment', string='Documents')


# class CrossoveredBudgetLines(models.Model):
#     _inherit = "crossovered.budget.lines"
#
#     # Odoo 18 uses 'digits' attribute referring to the decimal precision name
#     approved_amount = fields.Float(
#         string='Planned Amount',
#         required=True,
#         digits='Account'
#     )
#     commited_amount = fields.Float(
#         string='Commited Amount',
#         required=True,
#         digits='Account'
#     )
#     # Corrected 'recomited' to 'recompiled' based on your string or kept spelling for DB consistency
#     recomited_amount = fields.Float(
#         string='Recompiled Amount',
#         required=True,
#         digits='Account'
#     )


class PettyCash(models.Model):
    _name = 'petty.cash'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Petty Cash'
    _order = 'date desc, id desc'

    # Sequence generation in Odoo 18
    name = fields.Char(
        string='Request No.',
        required=True, copy=False, readonly=True,
        default=lambda self: _('New')
    )
    branch_id = fields.Many2one('hr.department', string='Branch Name', domain=[('is_branch', '=', True)], tracking=True)
    province_id = fields.Many2one('res.country.state', string='Province', tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, tracking=True)
    amount_requested = fields.Float(string='Requested Amount', tracking=True)
    acc_number = fields.Char(string='Account Number', tracking=True)

    requested_by = fields.Many2one('hr.employee', string='Requested By', tracking=True)
    description_need = fields.Text(string='Description', tracking=True)

    # Signatures and Approvals
    approve_by = fields.Many2one('hr.employee', string='Approved By', readonly=True)
    receive_by = fields.Many2one('hr.employee', string='Received By', readonly=True)
    signature_approved_by = fields.Binary(string='Approver Signature', readonly=True)
    signature_received_by = fields.Binary(string='Receiver Signature', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('recommend', 'Recommended'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('deny', 'Denied'),
    ], string='State', default='draft', tracking=True)

    user_id = fields.Many2one('res.users', string='Related User')
    branch_chk = fields.Boolean(string="Branch")
    province_chk = fields.Boolean(string="Province")

    # ---------------------------------------------------------
    # Constraints and Sequences
    # ---------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('petty.cash') or _('New')
        return super().create(vals_list)

    # ---------------------------------------------------------
    # Onchanges (Modern Syntax)
    # ---------------------------------------------------------
    @api.onchange('requested_by')
    def _onchange_requested_by(self):
        if self.requested_by:
            # received_by was a res.users in your old code; ensure logic matches use case
            pass

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.branch_id:
            self.province_id = False

    @api.onchange('province_id')
    def _onchange_province_id(self):
        if self.province_id:
            self.branch_id = False

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------
    def action_request_petty_cash(self):
        admin_config = self.env['leavy.income.config'].search([], limit=1)
        limit = admin_config.petty_limit if admin_config else 500.0

        if self.amount_requested > limit:
            raise UserError(_('You can request a maximum of %sR per transaction!') % limit)

        self.write({'state': 'requested'})

    def action_recommend_petty_cash(self):
        self.write({'state': 'recommend'})

    def action_approve_petty_cash(self):
        """ Creates the cash journal entry in the open Cash Box. """
        self.ensure_one()

        # Determine Domain for the Cash Register
        domain = [('state', '=', 'open')]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))
        elif self.province_id:
            domain.append(('province_id', '=', self.province_id.id))
        else:
            raise UserError(_("Please specify a Branch or Province."))

        cash_register = self.env['account.bank.statement'].search(domain, limit=1)

        if not cash_register:
            location = self.branch_id.name if self.branch_id else self.province_id.name
            raise UserError(_('Cash Box for %s must be open to approve this request!') % location)

        if not self.requested_by.user_id:
            raise UserError(_('The requesting employee must be linked to a system user/partner.'))

        # Create the line in the cash register
        # Note: amount is negative as it is an outflow
        cash_register.write({
            'line_ids': [Command.create({
                'payment_ref': self.name,
                'partner_id': self.requested_by.user_id.partner_id.id,
                'amount': -self.amount_requested,
                'date': date.today(),
            })]
        })

        # Signature logic
        employee = self.env.user.employee_id
        self.write({
            'state': 'approved',
            'approve_by': employee.id if employee else False,
            'signature_approved_by': employee.signature if employee else False
        })

    def action_deny_petty_cash(self):
        self.write({'state': 'deny'})

    def action_receive_petty_cash(self):
        employee = self.env.user.employee_id
        self.write({
            'state': 'received',
            'receive_by': employee.id if employee else False,
            'signature_received_by': employee.signature if employee else False
        })
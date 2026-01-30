from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime


class AccountAccount(models.Model):
    _inherit = 'account.account'

    # In Odoo 18, we use standard Python naming conventions (CamelCase)
    # The 'account.account' model already has fields like 'code' and 'name'

    business_unit = fields.Char(string='Business Unit')
    account_ref = fields.Char(string='Account')  # Renamed to avoid confusion with model name
    subsidiary = fields.Char(string='Subsidiary')
    company_ref = fields.Char(string='Company')  # Renamed to avoid confusion with company_id
    l_d = fields.Integer(string='L D')
    p_e = fields.Char(string='P E')
    currency_code = fields.Char(string='Currency Code')


class SchemeYear(models.Model):
    _name = 'scheme.year'
    _description = 'Scheme Year'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed')
    ], string="Status", default='open', tracking=True)

    # In Odoo 18, @api.multi is removed. self is a recordset.
    def set_to_close(self):
        self.write({'state': 'closed'})
        return True


class GrantConfig(models.Model):
    _name = 'grant.config'
    _description = 'Legacy Grant Configuration'

    scheme_yr = fields.Many2one('scheme.year', string='Scheme Year')
    # Changed to Float for better calculation support in Odoo 18
    mandatory = fields.Float(string='Mandatory Grant (%)')
    admin_grant = fields.Float(string='Admin Grant (%)')
    discretionary = fields.Float(string='Discretionary Grant (%)')
    hwseta_rec = fields.Float(string='HWSETA Received (%)')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('executed', 'Executed')
    ], string="Status", default='draft')


class GrantNew(models.Model):
    _name = 'grant.new'
    _description = 'Grant Type'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')


class GrantConfigNew(models.Model):
    _name = 'grant.config.new'
    _description = 'Grant Configuration'

    scheme_yr = fields.Many2one('scheme.year', string='Scheme Year')
    grant_assign_ids = fields.One2many('grant.config.assign', 'grant_ass_id', string='Grants')
    hwseta_rec = fields.Float(string='HWSETA Received (%)')


class GrantConfigAssign(models.Model):
    _name = 'grant.config.assign'
    _description = 'Grant Configuration Assignment'

    grant_ass_id = fields.Many2one('grant.config.new', string='Grant Config')
    grant_id = fields.Many2one('grant.new', string='Grant Type')
    value = fields.Float(string='Grant Percent')


class GrantAccount(models.Model):
    _name = 'grant.account'
    _description = 'Grant Account Mapping'

    # Ensure 'leavy.income.config' is updated to 'levy.income.config' if intended
    grant1 = fields.Many2one('leavy.income.config', string='Levy Config')
    grant_id = fields.Many2one('grant.new', string='Grant')
    account_id = fields.Many2one('account.account', string='Account')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # In Odoo 18, 'proforma_voucher' usually maps to the 'action_post'
    # or a custom validation step in the payment lifecycle.
    def action_post(self):
        # Call the original post method (replaces action_move_line_create)
        res = super(AccountPayment, self).action_post()

        # Modern way to get a template and send mail
        template = self.env.ref('hwseta_finance.email_template_mgrant_payment_notification', raise_if_not_found=False)

        if template:
            # In Python 3 / Odoo 18, we don't use self.pool.
            # The template object has its own send_mail method.
            template.send_mail(self.id, force_send=True)

        return res


# class AccountFiscalYear(models.Model):
#     # Note: Ensure you have 'account_accountant' installed,
#     # otherwise you may need to define this model from scratch.
#     _inherit = 'account.fiscal.year'
#
#     scheme_year_id = fields.Many2one('scheme.year', string='Scheme Year')
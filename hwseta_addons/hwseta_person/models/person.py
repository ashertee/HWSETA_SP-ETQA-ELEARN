from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from urllib.parse import quote_plus
from datetime import date, datetime
import calendar
import logging

_logger = logging.getLogger(__name__)


class SetaBranches(models.Model):
    _name = 'seta.branches'
    _description = 'SETA Branches'

    name = fields.Char(string='Branch Code', required=True)
    branch_address = fields.Char(string='Branch Address')

    _sql_constraints = [
        ('branch_uniq', 'unique(name)', 'Branch Code must be unique!')
    ]

class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Employers
    emp_ids = fields.One2many(
        'partner.project.rel',
        'emp_project_id',
        string='Employers'
    )

    # ✅ Providers
    pro_ids = fields.One2many(
        'partner.project.rel',
        'pro_project_id',
        string='Providers'
    )

    select_all_employer = fields.Boolean(string='Select All Employer')
    select_all_provider = fields.Boolean(string='Select All Provider')

    emp_ids = fields.One2many(
        'partner.project.rel',
        'emp_project_id',
        string='Employers'
    )

    selected_emp_ids = fields.One2many(
        'partner.project.rel.one',
        'selected_emp_project_id',
        string='Employers'
    )

    pro_ids = fields.One2many(
        'partner.project.rel',
        'pro_project_id',
        string='Providers'
    )

    selected_pro_ids = fields.One2many(
        'partner.project.rel.one',
        'selected_pro_project_id',
        string='Providers'
    )
    # Employer Groups
    emp_levy_paying = fields.Boolean(string='Levy Paying')
    emp_non_levy_paying = fields.Boolean(string='Non Levy Paying')
    emp_exempt = fields.Boolean(string='Levy Exempt')
    emp_government = fields.Boolean(string='Government')
    emp_university = fields.Boolean(string='University (CHE)')
    emp_tvet_college = fields.Boolean(string='TVET College (DHET)')
    emp_other_group = fields.Boolean(string='Other')
    emp_wsp_status = fields.Boolean(string='WSP Status')
    emp_sanc = fields.Boolean(string='SANC')
    emp_hpsca = fields.Boolean(string='HPSCA')
    emp_sapc = fields.Boolean(string='SAPC')
    emp_ngo_npo = fields.Boolean(string='NGO/NPO')
    emp_cbo = fields.Boolean(string='CBO')
    emp_fbo = fields.Boolean(string='FBO')
    emp_section = fields.Boolean(string='Section 21')
    emp_other_group_info = fields.Char(string='Other', size=70)

    


    def add_partners(self):
        self.ensure_one()
        context = self.env.context

        # --------------------
        # Employers
        # --------------------
        if context.get('employer'):
            emp_proj_data = self.env['partner.project.rel'].search([
                ('select_emp', '=', True),
                ('emp_project_id', '=', self.id)
            ])

            employers = emp_proj_data.mapped('employer_id')

            # Clear selected employers
            self.write({'selected_emp_ids': [(5, 0, 0)]})

            vals_list = []
            for employer in employers:
                employer.write({
                    'project_terms_and_condition': self.project_terms_and_condition.id
                })
                vals_list.append((0, 0, {
                    'select_emp': True,
                    'employer_id': employer.id,
                    'employer_sdl_no': employer.employer_sdl_no,
                }))

            if vals_list:
                self.write({'selected_emp_ids': vals_list})

        # --------------------
        # Providers
        # --------------------
        if context.get('provider'):
            pro_proj_data = self.env['partner.project.rel'].search([
                ('select_pro', '=', True),
                ('pro_project_id', '=', self.id)
            ])

            providers = pro_proj_data.mapped('provider_id')

            # Clear selected providers
            self.write({'selected_pro_ids': [(5, 0, 0)]})

            vals_list = []
            for provider in providers:
                provider.write({
                    'project_terms_and_condition': self.project_terms_and_condition.id
                })
                vals_list.append((0, 0, {
                    'select_pro': True,
                    'provider_id': provider.id,
                    'provider_acc_no': provider.provider_accreditation_num,
                }))

            if vals_list:
                self.write({'selected_pro_ids': vals_list})

        return True


    def add_all_partners(self):
        self.ensure_one()
        context = self.env.context

        # --------------------
        # Employers
        # --------------------
        if context.get('employer'):
            emp_proj_data = self.env['partner.project.rel'].search([
                ('emp_project_id', '=', self.id)
            ])

            employers = emp_proj_data.mapped('employer_id')

            # Clear selected employers
            self.write({'selected_emp_ids': [(5, 0, 0)]})

            vals_list = []
            for employer in employers:
                employer.write({
                    'project_terms_and_condition': self.project_terms_and_condition.id
                })
                vals_list.append((0, 0, {
                    'select_emp': True,
                    'employer_id': employer.id,
                    'employer_sdl_no': employer.employer_sdl_no,
                }))

            if vals_list:
                self.write({'selected_emp_ids': vals_list})

        # --------------------
        # Providers
        # --------------------
        if context.get('provider'):
            pro_proj_data = self.env['partner.project.rel'].search([
                ('pro_project_id', '=', self.id)
            ])

            providers = pro_proj_data.mapped('provider_id')

            # Clear selected providers
            self.write({'selected_pro_ids': [(5, 0, 0)]})

            vals_list = []
            for provider in providers:
                provider.write({
                    'project_terms_and_condition': self.project_terms_and_condition.id
                })
                vals_list.append((0, 0, {
                    'select_pro': True,
                    'provider_id': provider.id,
                    'provider_acc_no': provider.provider_accreditation_num,
                }))

            if vals_list:
                self.write({'selected_pro_ids': vals_list})

        return True


    def clear_partners(self):
        self.ensure_one()
        context = self.env.context

        # --------------------
        # Employers
        # --------------------
        if context.get('employer'):
            emp_proj_data = self.env['partner.project.rel.one'].search([
                ('select_emp', '=', True),
                ('selected_emp_project_id', '=', self.id)
            ])
            # Direct unlink is enough; no need to write select_emp=False
            emp_proj_data.unlink()

        # --------------------
        # Providers
        # --------------------
        if context.get('provider'):
            pro_proj_data = self.env['partner.project.rel.one'].search([
                ('select_pro', '=', True),
                ('selected_pro_project_id', '=', self.id)
            ])
            pro_proj_data.unlink()

        return True


    def onchange_category(self):
        for record in self:
            domain_val = []

            if record.emp_levy_paying:
                domain_val.append(('emp_levy_paying', '=', True))
            if record.emp_non_levy_paying:
                domain_val.append(('emp_non_levy_paying', '=', True))
            if record.emp_exempt:
                domain_val.append(('emp_exempt', '=', True))
            if record.emp_ngo_npo:
                domain_val.append(('emp_ngo_npo', '=', True))
            if record.emp_cbo:
                domain_val.append(('emp_cbo', '=', True))
            if record.emp_fbo:
                domain_val.append(('emp_fbo', '=', True))
            if record.emp_section:
                domain_val.append(('emp_section', '=', True))
            if record.emp_government:
                domain_val.append(('emp_government', '=', True))
            if record.emp_university:
                domain_val.append(('emp_university', '=', True))
            if record.emp_tvet_college:
                domain_val.append(('emp_tvet_college', '=', True))
            if record.emp_other_group:
                domain_val.append(('emp_other_group', '=', True))
            if record.emp_wsp_status:
                domain_val.append(('emp_wsp_status', '=', True))
            if record.emp_sanc:
                domain_val.append(('emp_sanc', '=', True))
            if record.emp_hpsca:
                domain_val.append(('emp_hpsca', '=', True))
            if record.emp_sapc:
                domain_val.append(('emp_sapc', '=', True))

            # Clear employers if nothing selected
            if not domain_val:
                record.emp_ids = [(5, 0, 0)]
                return

            employers = record.env['res.partner'].search(domain_val)

            record.emp_ids = [
                (0, 0, {
                    'employer_id': employer.id,
                    'employer_sdl_no': employer.employer_sdl_no,
                    'project_description': record.project_description,
                    'category': record.category.id,
                    'category_type': record.category_type,
                })
                for employer in employers
            ]

class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    user_id = fields.Many2one(
        'res.users',
        string='Related Users'
    )
    province_code_id = fields.Char(
        string='Province Code Id'
    )

class ResUsers(models.Model):
    _inherit = 'res.users'

    province_ids = fields.One2many(
        'res.country.state',
        'user_id',
        string='Provinces'
    )

    def has_hwseta_group(self, group_ext_id):
        """
        Backward-compatible helper for old code that used
        non-qualified group XML IDs.

        Example:
            'group_dc_stakeholder_data'
        becomes:
            'hwseta_etqe.group_dc_stakeholder_data'
        """
        if not group_ext_id:
            return False

        # Convert short group name to fully-qualified XML ID
        if '.' not in group_ext_id:
            group_ext_id = f'hwseta_etqe.{group_ext_id}'

        return self.has_group(group_ext_id)

class PartnerProjectRel(models.Model):
    _name = 'partner.project.rel'
    _inherit = ['mail.thread']
    _rec_name = 'employer_id'

    @api.model
    def read_group(
        self, domain, fields, groupby,
        offset=0, limit=None, orderby=False, lazy=True
    ):
        """
        Override read_group to show correct group count
        and default EOI ID group in SDF Portal
        """

        # Always restrict to selected employers
        domain = [('select_emp', '=', True)]

        result = super().read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )

        if not result:
            return result

        for group in result:
            eoi_value = group.get('eoi_id_reference_new')
            if not eoi_value:
                continue

            records = self.search([
                ('eoi_id_reference_new', '=', eoi_value),
                ('select_emp', '=', True),
            ])

            group['eoi_id_reference_new_count'] = len(records)

        return result

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, count=False):
        user = self.env.user

        # Groups that can see everything
        full_access_groups = [
            'hwseta_etqe.group_wsp_manager',
            'hwseta_etqe.group_sdp_manager',
            'hwseta_etqe.group_provincial_manager',
            'hwseta_etqe.group_wsp_officer',
            'hwseta_etqe.group_provincial_officer',
            'hwseta_etqe.group_wsp_administrator',
            'hwseta_etqe.group_general_access',
            'hwseta_etqe.group_auditor_access',
        ]

        # If user has any full-access group → no restriction
        if any(user.has_group(g) for g in full_access_groups):
            return super()._search(domain, offset=offset, limit=limit, order=order, count=count)

        # Superuser → no restriction
        if user.id == self.env.ref('base.user_admin').id:
            return super()._search(domain, offset=offset, limit=limit, order=order, count=count)

        domain = list(domain or [])

        # Employer access
        if user.has_group('hwseta_etqe.group_employer'):
            domain.append(('employer_id', '=', user.partner_id.id))

        # SDF access
        if user.has_group('hwseta_etqe.group_sdf'):
            sdf_records = self.env['sdf.tracking'].search([
                ('status', '=', 'approved'),
                ('sdf_id', '=', user.sdf_id.id),
            ])
            employer_ids = sdf_records.mapped('partner_id').ids
            domain.append(('employer_id', 'in', employer_ids))

        return super()._search(domain, offset=offset, limit=limit, order=order, count=count)

    # --------------------------------------------------
    # Fields
    # --------------------------------------------------
    select_emp = fields.Boolean(string='Select Employer')
    select_pro = fields.Boolean(string='Select Provider')

    employer_id = fields.Many2one(
        'res.partner',
        string='Employer',
        domain=[('employer', '=', True)],
        tracking=True,
    )

    provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        domain=[('provider', '=', True)],
        tracking=True,
    )

    emp_project_id = fields.Many2one(
        'project.project',
        string="Emp Project",
        tracking=True,
    )

    pro_project_id = fields.Many2one(
        'project.project',
        string="Pro Project",
    )

    category = fields.Many2one(
        'hwseta.project.category',
        string='Project Category',
    )

    category_type = fields.Selection(
        [
            ('18.1', 'Employed Learners (18.1)'),
            ('18.2', 'Unemployed Learners (18.2)'),
        ],
        string="Category Type",
    )

    project_description = fields.Text("Description")

    employer_sdl_no = fields.Char(string='SDL No.', tracking=True)
    provider_accreditation_num = fields.Char(string='Accreditation No.', tracking=True)

    eoi_apply = fields.Boolean("Apply For EOI", default=False, tracking=True)
    eoi_apply_date = fields.Datetime("Apply Date")
    eoi_ext_date = fields.Datetime("EOI Extension Date")
    eoi_ext_request = fields.Boolean("EOI Extension Request", default=False, tracking=True)

    load_learner_ext_date = fields.Datetime("Load Learner Extension Date", tracking=True)
    load_learner_ext_request = fields.Boolean("Learner Extension Request", default=False)

    is_extension = fields.Boolean("Is Extension", default=False)

    project_terms_and_condition = fields.Many2one(
        'ir.attachment',
        string='Project Terms and Conditions',
        tracking=True,
    )

    agree_terms = fields.Boolean(
        string='Agree',
        default=False,
        tracking=True,
    )


    def action_eoi_apply(self):
        self.ensure_one()

        if not self.agree_terms:
            raise UserError(_("Please agree to the project terms and conditions!"))

        if not self.emp_project_id:
            return True

        # -------------------------------------------------
        # Collect qualification IDs
        # -------------------------------------------------
        qualification_ids = self.emp_project_id.qualification_ids.mapped(
            'qualification_id'
        ).ids

        # -------------------------------------------------
        # Enrolled project values
        # -------------------------------------------------
        project_vals = {
            'project_types': self.emp_project_id.project_types.id,
            'project_id': self.emp_project_id.id,
            'state': 'draft',
        }

        if qualification_ids:
            project_vals['qualifications'] = [(6, 0, qualification_ids)]

        # -------------------------------------------------
        # EOI values
        # -------------------------------------------------
        eoi_vals = {
            'employer_id': self.employer_id.id,
            'enroll_project_ids': [(0, 0, project_vals)],
            'learning_project_type_id': self.emp_project_id.project_types.id,
            'learning_project_id': self.emp_project_id.id,
            'category': self.category.id,
            'category_type': self.category_type,
            'employer_sdl_no': self.employer_id.employer_sdl_no,
            'empl_sic_code': self.employer_id.empl_sic_code.id if self.employer_id.empl_sic_code else False,
            'employer_registration_number': self.employer_id.employer_registration_number,
            'employer_site_no': self.employer_id.employer_site_no,
            'employer_trading_name': self.employer_id.employer_trading_name,
            'employer_seta_id': self.employer_id.employer_seta_id.id if self.employer_id.employer_seta_id else False,
        }

        self.env['learning.programme'].create(eoi_vals)

        # -------------------------------------------------
        # Update flags
        # -------------------------------------------------
        self.write({
            'eoi_apply': True,
            'eoi_apply_date': fields.Datetime.now(),
            'agree_terms': True,
        })

        return True
    
    def action_request_eoi_extension(self):
        self.ensure_one()

        if not self.eoi_apply:
            raise UserError(_("Sorry! Please apply for EOI first."))

        # Mark extension request
        self.write({'eoi_ext_request': True})

        # -------------------------------------------------
        # Send email notification to HWSETA Team
        # -------------------------------------------------
        template = self.env.ref(
            'hwseta_person.email_template_eoi_extension',
            raise_if_not_found=False
        )

        if template:
            template.send_mail(self.id, force_send=True)

        return True
    
    def action_request_learner_extension(self):
        self.ensure_one()

        if not self.eoi_apply:
            raise UserError(_("Sorry! Please apply for EOI first."))

        # Mark learner extension request
        self.write({'load_learner_ext_request': True})

        # -------------------------------------------------
        # Send email notification to HWSETA Team
        # -------------------------------------------------
        template = self.env.ref(
            'hwseta_person.email_template_load_learner_extension',
            raise_if_not_found=False
        )

        if template:
            template.send_mail(self.id, force_send=True)

        return True    
    
    def action_check_eoi_date(self):
        """
        Check EOI and Load Learner end dates
        and mark records as extension if overdue
        """
        current_date = fields.Datetime.now()

        # Get all selected employers
        employers = self.env['partner.project.rel'].search([
            ('select_emp', '=', True)
        ])

        for employer in employers:
            project = employer.emp_project_id
            if not project:
                continue

            # Compare datetimes safely
            if project.eoi_end_date and current_date > project.eoi_end_date:
                employer.write({
                    'eoi_apply_date': current_date,
                    'is_extension': True,
                })

            if project.load_learner_end_date and current_date > project.load_learner_end_date:
                employer.write({
                    'eoi_apply_date': current_date,
                    'is_extension': True,
                })

        return True
       
class PartnerProjectRel(models.Model):
    _name = 'partner.project.rel'
    _description = 'Partner Project Relation'

    # Employer side
    emp_project_id = fields.Many2one(
        'project.project',
        string='Employer Project',
        ondelete='cascade'
    )

    # ✅ Provider side (THIS WAS MISSING)
    pro_project_id = fields.Many2one(
        'project.project',
        string='Provider Project',
        ondelete='cascade'
    )

    employer_id = fields.Many2one(
        'res.partner',
        string='Employer'
    )

    provider_id = fields.Many2one(
        'res.partner',
        string='Provider'
    )

    select_emp = fields.Boolean(string='Select Employer')
    select_pro = fields.Boolean(string='Select Provider')
    
    @api.constrains('eoi_ext_date', 'load_learner_ext_date', 'emp_project_id')
    def _check_extension_dates(self):
        for record in self:
            project = record.emp_project_id
            if not project:
                continue

            if record.eoi_ext_date:
                if (
                    project.start_date
                    and project.end_date
                    and not (project.start_date <= record.eoi_ext_date <= project.end_date)
                ):
                    raise ValidationError(_(
                        "EOI Extension Date must be between the Project Start Date "
                        "and Project End Date."
                    ))

            if record.load_learner_ext_date:
                if record.eoi_ext_date:
                    if (
                        project.eoi_start_date
                        and not (project.eoi_start_date <= record.load_learner_ext_date <= record.eoi_ext_date)
                    ):
                        raise ValidationError(_(
                            "Load Learner Extension Date must be between "
                            "EOI Start Date and EOI Extension Date."
                        ))
                else:
                    if (
                        project.eoi_start_date
                        and project.eoi_end_date
                        and not (project.eoi_start_date <= record.load_learner_ext_date <= project.eoi_end_date)
                    ):
                        raise ValidationError(_(
                            "Load Learner Extension Date must be between "
                            "EOI Start Date and EOI End Date."
                        ))


class PartnerProjectRelOne(models.Model):
    _name = 'partner.project.rel.one'
    _description = 'Selected Employer / Provider Project Relation'

    # -------------------------
    # Employer
    # -------------------------
    select_emp = fields.Boolean(string='Select Employer')

    employer_id = fields.Many2one(
        'res.partner',
        string='Employer',
        domain=[('employer', '=', True)]
    )

    employer_sdl_no = fields.Char(
        string='SDL No.'
    )

    selected_emp_project_id = fields.Many2one(
        'project.project',
        string='Emp Project'
    )

    # -------------------------
    # Provider
    # -------------------------
    select_pro = fields.Boolean(string='Select Provider')

    provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        domain=[('provider', '=', True)]
    )

    provider_acc_no = fields.Char(
        string='Accreditation No.'
    )

    selected_pro_project_id = fields.Many2one(
        'project.project',
        string='Pro Project'
    )

class EmployerType(models.Model):
    _name = 'employer.type'
    _description = 'Employer Type'

    name = fields.Char(string='Name', required=True)

## Adding Banking related fields in partner bank details
class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    grant_type = fields.Selection(
        [
            ('mandatory', 'Mandatory'),
            ('discretionary', 'Discretionary'),
            ('both', 'Both'),
        ],
        string='Grant Account Type'
    )

    branch_name = fields.Char(string='Branch Name')
    branch_code = fields.Char(string='Branch Code')
    ifsc_code = fields.Char(string='IFSC Code')
    other = fields.Text(string='Other')

    city_id = fields.Many2one(
        'res.city',
        string='City'
    ) 
    
class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def create(self, vals):
        account_number = vals.get('acc_number')

        if account_number:
            # Fast and safe duplicate check
            if self.search_count([('acc_number', '=', account_number)]):
                raise UserError(_("Account number already exists!"))

        return super().create(vals)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_default_seta(self):
        seta = self.env['seta.branches'].search(
            [('name', '=', '11')],
            limit=1
        )
        return seta.id if seta else False
    
     # -------------------------------------------------
    # Compute Organisation Size
    # -------------------------------------------------
    @api.depends('employees_count')
    def _compute_organisation_size(self):
        for record in self:
            if record.employees_count <= 49:
                record.organisation_size = 'small'
            elif 50 <= record.employees_count <= 149:
                record.organisation_size = 'medium'
            else:
                record.organisation_size = 'large'

    # -------------------------------------------------
    # Employer Fields
    # -------------------------------------------------
    employer = fields.Boolean(string='Employer')
    employer_department = fields.Boolean(string='Department')

    employer_sdl_no = fields.Char(
        string='SDL No.',
        size=10,
        tracking=True
    )

    employer_site_no = fields.Char(
        string='Site No.',
        size=10,
        tracking=True
    )

    employer_seta_id = fields.Many2one(
        'seta.branches',
        string='Employer SETA',
        default=lambda self: self._get_default_seta(),
        tracking=True
    )

    emp_reg_number_type = fields.Selection(
        [
            ('cipro_number', 'Cipro Number'),
            ('comp_reg_no', 'Company Registration Number'),
        ],
        string='Registration Number Type'
    )

    employer_registration_number = fields.Char(
        string='Registration Number',
        size=20,
        tracking=True
    )

    employer_vat_number = fields.Char(
        string='VAT Number',
        size=20,
        tracking=True
    )

    employer_trading_name = fields.Char(
        string='Trading Name',
        tracking=True
    )

    partnership = fields.Selection(
        [
            ('private', 'Private'),
            ('public', 'Public'),
            ('private_public', 'Private Public'),
        ],
        string='Partnership'
    )

    total_annual_payroll = fields.Float(string='Total Annual Payroll')

    organisation_size = fields.Selection(
        [
            ('small', 'Small (0–49)'),
            ('medium', 'Medium (50–149)'),
            ('large', 'Large (150+)'),
        ],
        compute='_compute_organisation_size',
        store=True,
        readonly=True,
        string='Organisation Size'
    )

    # -------------------------------------------------
    # Employer Approval / Address Info
    # -------------------------------------------------
    employer_approval_status_id = fields.Char(
        string='Approval Status Id',
        size=10,
        tracking=True
    )

    employer_approval_status_start_date = fields.Date(
        string='Approval Status Start Date',
        tracking=True
    )

    employer_approval_status_end_date = fields.Date(
        string='Approval Status End Date',
        tracking=True
    )

    employer_approval_status_num = fields.Char(
        string='Approval Status Number',
        size=20,
        tracking=True
    )

    # -------------------------------------------------
    # Location (Legacy – consider replacing later)
    # -------------------------------------------------
    employer_latitude_degree = fields.Char(string='Latitude Degree', size=3, tracking=True)
    employer_latitude_minutes = fields.Char(string='Latitude Minutes', size=2, tracking=True)
    employer_latitude_seconds = fields.Char(string='Latitude Seconds', size=6, tracking=True)

    employer_longitude_degree = fields.Char(string='Longitude Degree', size=2, tracking=True)
    employer_longitude_minutes = fields.Char(string='Longitude Minutes', size=2, tracking=True)
    employer_longitude_seconds = fields.Char(string='Longitude Seconds', size=6, tracking=True)

    # -------------------------------------------------
    # Misc
    # -------------------------------------------------
    employer_main_sdl_no = fields.Char(string='Main SDL No.', size=10, tracking=True)
    employer_filler01 = fields.Char(string='Filler01', size=20, tracking=True)
    employer_filler02 = fields.Char(string='Filler02', size=4, tracking=True)
    employer_date_stamp = fields.Date(string='Date Stamp', tracking=True)

    dormant = fields.Boolean(string='Dormant')
    university = fields.Boolean(string='University')
    college = fields.Boolean(string='College')
    nsfas = fields.Boolean(string='NSFAS')
    
# -------------------------------------------------
    # Organisation Sector (UAT requirement)
    # -------------------------------------------------
    emp_health = fields.Boolean(string='Health')
    emp_welfare = fields.Boolean(string='Welfare')
    emp_other = fields.Boolean(string='Other')
    emp_other_info = fields.Char(string='Other', size=70, tracking=True)

    # -------------------------------------------------
    # Employer Groups
    # -------------------------------------------------
    emp_levy_paying = fields.Boolean(string='Levy Paying')
    emp_non_levy_paying = fields.Boolean(string='Non Levy Paying')
    emp_exempt = fields.Boolean(string='Levy Exempt')
    emp_government = fields.Boolean(string='Government')
    emp_university = fields.Boolean(string='University (CHE)')
    emp_tvet_college = fields.Boolean(string='TVET College (DHET)')
    emp_other_group = fields.Boolean(string='Other')
    emp_wsp_status = fields.Boolean(string='WSP Status')
    emp_sanc = fields.Boolean(string='SANC')
    emp_hpsca = fields.Boolean(string='HPSCA')
    emp_sapc = fields.Boolean(string='SAPC')
    emp_other_group_info = fields.Char(string='Other', size=70)
    emp_ngo_npo = fields.Boolean(string='NGO/NPO')
    emp_cbo = fields.Boolean(string='CBO')
    emp_fbo = fields.Boolean(string='FBO')
    emp_section = fields.Boolean(string='Section 21')

    employees_count = fields.Integer(
        string='Employees as per Employment Profile',
        readonly=True
    )

    type_of_employer = fields.Many2one(
        'employer.type',
        string='Employer Type'
    )

    # -------------------------------------------------
    # Provider Fields
    # -------------------------------------------------
    provider = fields.Boolean(string='Provider')

    provider_trading_name = fields.Char(
        string='Trading Name',
        size=70,
        tracking=True
    )

    provider_suburb = fields.Char(string='Suburb')

    provider_physical_suburb_id = fields.Many2one(
        'res.suburb',
        string='Physical Suburb'
    )

    provider_postal_suburb_id = fields.Many2one(
        'res.suburb',
        string='Postal Suburb'
    )

    provider_code = fields.Char(
        string='Code',
        help="Provider Code",
        size=50,
        tracking=True
    )

    provider_etqe_id = fields.Char(
        string='ETQE Id',
        size=10,
        tracking=True
    )

    provider_sars_number = fields.Char(
        string='SDL No.',
        size=50,
        tracking=True
    )

    provider_contact_name = fields.Char(
        string='Contact Name',
        size=50,
        tracking=True
    )

    provider_accreditation_num = fields.Char(
        string='Accreditation No.',
        size=50,
        tracking=True
    )

    provider_etqa_decision_number = fields.Char(
        string='Decision No.',
        size=20,
        tracking=True
    )

    provider_type_id = fields.Char(
        string='Provider Type',
        size=50,
        tracking=True
    )

    provider_start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today,
        tracking=True
    )

    provider_end_date = fields.Date(
        string='End Date',
        tracking=True
    )

    provider_class_id = fields.Char(
        string='Provider Class',
        size=50,
        tracking=True
    )

    provider_status_id = fields.Char(
        string='Provider Status',
        size=50,
        tracking=True
    )

    provider_sdl_no = fields.Char(
        string='SDL No',
        size=50,
        tracking=True
    )

    provider_date_stamp = fields.Datetime(
        string='Date Stamp',
        tracking=True
    )

    is_qdm_provider = fields.Boolean(string='QDM')

    # -------------------------------------------------
    # Provider Location (Legacy – consider geo fields)
    # -------------------------------------------------
    provider_latitude_degree = fields.Char(string='Latitude (Degree)', size=50, tracking=True)
    provider_latitude_minutes = fields.Char(string='Latitude (Minutes)', size=50, tracking=True)
    provider_latitude_seconds = fields.Char(string='Latitude (Seconds)', size=50, tracking=True)

    provider_longitude_degree = fields.Char(string='Longitude (Degree)', size=50, tracking=True)
    provider_longitude_minutes = fields.Char(string='Longitude (Minutes)', size=50, tracking=True)
    provider_longitude_seconds = fields.Char(string='Longitude (Seconds)', size=50, tracking=True)

    provider_latitude_degree_p = fields.Char(string='Latitude (Degree)', size=50, tracking=True)
    provider_latitude_minutes_p = fields.Char(string='Latitude (Minutes)', size=50, tracking=True)
    provider_latitude_seconds_p = fields.Char(string='Latitude (Seconds)', size=50, tracking=True)

    provider_longitude_degree_p = fields.Char(string='Longitude (Degree)', size=50, tracking=True)
    provider_longitude_minutes_p = fields.Char(string='Longitude (Minutes)', size=50, tracking=True)
    provider_longitude_seconds_p = fields.Char(string='Longitude (Seconds)', size=50, tracking=True)

    provider_website_address = fields.Char(
        string='Website Address',
        size=50,
        tracking=True
    )

    accreditation = fields.Boolean(string='Accreditation')
    
    # -------------------------------------------------
    # Provider Physical Address
    # -------------------------------------------------
    physical_address_1 = fields.Char(
        string='Physical Address 1',
        size=50,
        tracking=True
    )
    physical_address_2 = fields.Char(
        string='Physical Address 2',
        size=50,
        tracking=True
    )
    physical_address_3 = fields.Char(
        string='Physical Address 3',
        size=50,
        tracking=True
    )

    city_id = fields.Many2one(
        'res.city',
        string='Work City',
        tracking=True
    )

    street3 = fields.Char(string='Street 3', size=50)

    suburb_id = fields.Many2one(
        'res.suburb',
        string='Suburb',
        tracking=True
    )

    postal_address_1 = fields.Char(
        string='Postal Address 1',
        size=50,
        tracking=True
    )
    postal_address_2 = fields.Char(
        string='Postal Address 2',
        size=50,
        tracking=True
    )
    postal_address_3 = fields.Char(
        string='Postal Address 3',
        size=50,
        tracking=True
    )

    postal_address_code = fields.Char(
        string='Postal Address Code',
        size=4,
        tracking=True
    )

    physical_address_code = fields.Char(
        string='Physical Address Code',
        size=4,
        tracking=True
    )

    city_physical_id = fields.Many2one(
        'res.city',
        string='Provider Physical City',
        tracking=True
    )

    city_postal_id = fields.Many2one(
        'res.city',
        string='Provider Postal City',
        tracking=True
    )

    zip_physical = fields.Char(
        string='Provider Physical Zip',
        tracking=True
    )

    zip_postal = fields.Char(
        string='Provider Postal Zip',
        tracking=True
    )

    country_code_physical_id = fields.Many2one(
        'res.country',
        string='Provider Physical Country',
        tracking=True
    )

    country_code_postal_id = fields.Many2one(
        'res.country',
        string='Provider Postal Country',
        tracking=True
    )

    province_code_physical_id = fields.Many2one(
        'res.country.state',
        string='Physical Province',
        tracking=True
    )

    province_code_postal_id = fields.Many2one(
        'res.country.state',
        string='Postal Province',
        tracking=True
    )

    # -------------------------------------------------
    # Employer Physical Address
    # -------------------------------------------------
    emp_physical_address_1 = fields.Char(
        string='Employer Physical Address 1',
        size=50,
        tracking=True
    )
    emp_physical_address_2 = fields.Char(
        string='Employer Physical Address 2',
        size=50,
        tracking=True
    )
    emp_physical_address_3 = fields.Char(
        string='Employer Physical Address 3',
        size=50,
        tracking=True
    )

    emp_physical_suburb_id = fields.Many2one(
        'res.suburb',
        string='Employer Physical Suburb'
    )

    emp_postal_address_1 = fields.Char(
        string='Employer Postal Address 1',
        size=50,
        tracking=True
    )
    emp_postal_address_2 = fields.Char(
        string='Employer Postal Address 2',
        size=50,
        tracking=True
    )
    emp_postal_address_3 = fields.Char(
        string='Employer Postal Address 3',
        size=50,
        tracking=True
    )

    emp_postal_suburb_id = fields.Many2one(
        'res.suburb',
        string='Employer Postal Suburb'
    )

    emp_postal_address_code = fields.Char(
        string='Employer Postal Address Code',
        size=4,
        tracking=True
    )

    emp_physical_address_code = fields.Char(
        string='Employer Physical Address Code',
        size=4,
        tracking=True
    )

    emp_city_physical_id = fields.Many2one(
        'res.city',
        string='Employer Physical City',
        tracking=True
    )

    emp_city_postal_id = fields.Many2one(
        'res.city',
        string='Employer Postal City',
        tracking=True
    )

    emp_zip_physical = fields.Char(
        string='Employer Physical Zip',
        tracking=True
    )

    emp_zip_postal = fields.Char(
        string='Employer Postal Zip',
        tracking=True
    )

    emp_country_code_physical_id = fields.Many2one(
        'res.country',
        string='Employer Physical Country',
        tracking=True
    )

    emp_country_code_postal_id = fields.Many2one(
        'res.country',
        string='Employer Postal Country',
        tracking=True
    )

    emp_province_code_physical_id = fields.Many2one(
        'res.country.state',
        string='Employer Physical Province',
        tracking=True
    )

    emp_province_code_postal_id = fields.Many2one(
        'res.country.state',
        string='Employer Postal Province',
        tracking=True
    )

    # -------------------------------------------------
    # Extra Documents
    # -------------------------------------------------
    levy_exempt_certificate_id = fields.Many2one(
        'ir.attachment',
        string='Levy Exempt Certificate'
    )

    npo_certificate_id = fields.Many2one(
        'ir.attachment',
        string='NPO Certificate'
    )

    mand_grant_banking_details_id = fields.Many2one(
        'ir.attachment',
        string='Mandatory Grant Banking Details'
    )

    disc_grant_banking_details_id = fields.Many2one(
        'ir.attachment',
        string='Discretionary Grant Banking Details'
    )

    bbee_certificate_id = fields.Many2one(
        'ir.attachment',
        string='B-BEE Certificate'
    )
    
    # -------------------------------------------------
    # Organisation Contact Fields
    # -------------------------------------------------
    surname = fields.Char(string='Surname')
    initials = fields.Char(string='Initials')
    urban_rural = fields.Char(string='Urban / Rural')





    # -------------------------------------------------
    # SQL Constraints
    # -------------------------------------------------
    _sql_constraints = [
        (
            'vat_no_uniq',
            'unique(employer_vat_number)',
            'VAT number must be unique!'
        ),
    ]

    # -------------------------------------------------
    # Open Address in Google Maps
    # -------------------------------------------------
    def open_map_addr(self):
        """
        Opens the partner address in Google Maps.
        """
        self.ensure_one()

        parts = []

        if self.street:
            parts.append(self.street)
        if self.city_id:
            parts.append(self.city_id.name)
        if self.state_id:
            parts.append(self.state_id.name)
        if self.country_id:
            parts.append(self.country_id.name)
        if self.zip:
            parts.append(self.zip)

        address = quote_plus(" ".join(parts))
        url = f"https://www.google.com/maps/search/?api=1&query={address}"

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
        
    @api.onchange('provider_postal_suburb_id')
    def _onchange_provider_postal_suburb(self):
        for record in self:
            if record.provider_postal_suburb_id:
                record.zip_postal = record.provider_postal_suburb_id.postal_code
            else:
                record.zip_postal = False
    
    @api.onchange('provider_physical_suburb_id')
    def _onchange_provider_physical_suburb(self):
        for record in self:
            if record.provider_physical_suburb_id:
                record.zip_physical = record.provider_physical_suburb_id.postal_code
            else:
                record.zip_physical = False
    
    
    
    # -------------------------------------------------
    # Get country from province/state
    # -------------------------------------------------
    @api.model
    def country_for_province(self, province_id):
        state = self.env['res.country.state'].browse(province_id)
        return state.country_id.id if state and state.country_id else False

    # -------------------------------------------------
    # Open Physical Address on Map
    # -------------------------------------------------
    def physical_addr_map(self):
        self.ensure_one()

        return self.open_map_addr(
            street=self.physical_address_1,
            city=self.city_physical_id,
            state=self.province_code_physical_id,
            country=self.country_code_physical_id,
            zip_code=self.zip_physical,
        )

    # -------------------------------------------------
    # Open Postal Address on Map
    # -------------------------------------------------
    def postal_addr_map(self):
        self.ensure_one()

        return self.open_map_addr(
            street=self.postal_address_1,
            city=self.city_postal_id,
            state=self.province_code_postal_id,
            country=self.country_code_postal_id,
            zip_code=self.zip_postal,
        )


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_marital_status_selection(self):
        selection = super()._get_marital_status_selection()

        if ('widow', 'Widow') not in selection:
            selection.append(('widow', 'Widow'))

        return selection

    # -------------------------------------------------
    # SDF / Identity
    # -------------------------------------------------
    national_id = fields.Char(string='National ID', size=20, tracking=True)
    person_alternate_id = fields.Char(string='Person Alternate ID', size=20, tracking=True)
    alternate_id_type_id = fields.Char(string='Alternate Type ID', size=3, tracking=True)

    alternate_id_type = fields.Selection(
        [
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
            ('hsrc_register_number', '541 - HSRC Register Number'),
            ('etqe_record_number', '561 - ETQA Record Number'),
            ('refugee_number', '565 - Refugee Number'),
        ],
        string='Alternate ID Type',
    )

    # -------------------------------------------------
    # Language & Nationality
    # -------------------------------------------------
    home_language_code = fields.Many2one(
        'res.lang',
        string='Home Language',
        tracking=True
    )

    home_lang_saqa_code = fields.Selection(
        [
            ('eng', 'Eng'), ('afr', 'Afr'), ('xho', 'Xho'), ('set', 'Set'),
            ('zul', 'Zul'), ('sep', 'Sep'), ('tsh', 'Tsh'), ('ses', 'Ses'),
            ('xit', 'Xit'), ('swa', 'Swa'), ('nde', 'Nde'), ('u', 'U'),
            ('oth', 'Oth'),
        ],
        string='Home Language SAQA Code',
    )

    nationality_saqa_code = fields.Selection(
        [('sa', 'SA')],
        string='Nationality SAQA Code'
    )

    citizen_resident_status_code = fields.Selection(
        [
            ('sa', 'SA - South Africa'),
            ('dual', 'D - Dual (SA plus other)'),
            ('other', 'O - Other'),
            ('PR', 'PR - Permanent Resident'),
            ('unknown', 'U - Unknown'),
        ],
        string='Citizen Status'
    )

    citizen_status_saqa_code = fields.Selection(
        [('sa', 'SA'), ('d', 'D'), ('o', 'O'), ('pr', 'PR'), ('u', 'U')],
        string='Citizen Status SAQA Code'
    )

    # -------------------------------------------------
    # Personal Details
    # -------------------------------------------------
    person_title = fields.Selection(
        [('adv', 'Adv.'), ('dr', 'Dr'), ('mr', 'Mr'), ('mrs', 'Mrs'), ('ms', 'Ms'), ('prof', 'Prof')],
        string='Title',
        tracking=True
    )

    person_name = fields.Char(string='First Name', size=50, tracking=True)
    person_middle_name = fields.Char(string='Middle Name', size=50, tracking=True)
    person_last_name = fields.Char(string='Last Name', size=45, tracking=True)
    person_previous_lastname = fields.Char(string='Previous Last Name', size=45, tracking=True)
    maiden_name = fields.Char(string='Maiden Name', tracking=True)

    person_birth_date = fields.Date(string='Birth Date', tracking=True)

    # -------------------------------------------------
    # Contact & Address
    # -------------------------------------------------
    person_cell_phone_number = fields.Char(string='Cell Phone Number', size=10, tracking=True)
    person_fax_number = fields.Char(string='Fax Number', size=10, tracking=True)

    person_suburb_id = fields.Many2one('res.suburb', string='Suburb')
    person_home_suburb_id = fields.Many2one('res.suburb', string='Home Suburb')
    person_postal_suburb_id = fields.Many2one('res.suburb', string='Postal Suburb')

    person_home_city_id = fields.Many2one('res.city', string='Home City', tracking=True)
    person_postal_city_id = fields.Many2one('res.city', string='Postal City', tracking=True)

    person_home_zip = fields.Char(string='Home Zip', tracking=True)
    person_postal_zip = fields.Char(string='Postal Zip', tracking=True)

    country_home_id = fields.Many2one('res.country', string='Home Country', tracking=True)
    country_postal_id = fields.Many2one('res.country', string='Postal Country', tracking=True)

    person_home_province_code_id = fields.Many2one('res.country.state', string='Home Province', tracking=True)
    person_postal_province_code_id = fields.Many2one('res.country.state', string='Postal Province', tracking=True)

    # -------------------------------------------------
    # Work Details
    # -------------------------------------------------
    department = fields.Char(string='Department', tracking=True)
    job_title = fields.Char(string='Job Title', tracking=True)
    manager = fields.Char(string='Manager', tracking=True)

    work_address = fields.Char(string='Work Address', tracking=True)
    work_address2 = fields.Char(string='Work Address 2', tracking=True)
    work_address3 = fields.Char(string='Work Address 3', tracking=True)

    work_city_id = fields.Many2one('res.city', string='Work City', tracking=True)
    work_province_id = fields.Many2one('res.country.state', string='Work Province', tracking=True)
    work_country_id = fields.Many2one('res.country', string='Work Country', tracking=True)
    work_zip = fields.Char(string='Work Zip', tracking=True)

    # -------------------------------------------------
    # Provider / Learner
    # -------------------------------------------------
    provider_code = fields.Char(string='Provider Code', size=20, tracking=True)
    provider_etqe_id = fields.Integer(string='Provider ETQE ID', tracking=True)

    is_sdf = fields.Boolean(string='SDF', tracking=True)
    is_learner = fields.Boolean(string='Learner', tracking=True)
    is_learner_from_assessment = fields.Boolean(string='Learner (Assessment)', default=False, tracking=True)

    learner_reg_no = fields.Char(string='Learner Reg No', tracking=True)
    learner_status = fields.Char(string='Learner Status', tracking=True)

    method_of_communication = fields.Selection(
        [('cell_phone', 'Cell Phone'), ('email', 'Email')],
        string='Method of Communication'
    )

    # -------------------------------------------------
    # Disability & Ratings
    # -------------------------------------------------
    disability_status = fields.Selection(
        [
            ('sight', 'Sight (even with glasses)'),
            ('hearing', 'Hearing (even with hearing aid)'),
            ('communication', 'Communication'),
            ('physical', 'Physical'),
            ('intellectual', 'Intellectual'),
            ('emotional', 'Emotional'),
            ('multiple', 'Multiple'),
            ('disabled', 'Disabled but unspecified'),
            ('none', 'None'),
        ],
        string='Disability Status'
    )

    disability_status_saqa = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'),
         ('5', '5'), ('6', '6'), ('7', '7'), ('9', '9'), ('n', 'N')],
        string='Disability SAQA Code'
    )

    dissability = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Disability'
    )

    # -------------------------------------------------
    # Audit
    # -------------------------------------------------
    record_last_update = fields.Date(string='Record Last Updated', tracking=True)
    date_stamp = fields.Date(string='Date Stamp', tracking=True)
    status_comments = fields.Char(string='Status Comment', tracking=True)
    highest_education_level = fields.Selection(
        [
            ('abet_level_1', 'Abet Level 1'),
            ('abet_level_2', 'Abet Level 2'),
            ('abet_level_3', 'Abet Level 3'),
            ('abet_level_4', 'Abet Level 4'),
            ('nqf123', 'NQF 1,2,3'),
            ('nqf45', 'NQF 4,5'),
            ('nqf67', 'NQF 6,7'),
            ('nqf8910', 'NQF 8,9,10'),
        ],
        string='Highest Education Level'
    )

    cell = fields.Char(string='Mobile Number', tracking=True)

    status_reason = fields.Selection(
        [('workplace_learning', '500 - Workplace learning')],
        string='Learner Status Reason',
        tracking=True
    )

    wsp_year = fields.Selection(
        [('2015', '2015'), ('2016', '2016')],
        string='WSP Year',
        tracking=True
    )

    status_effective_date = fields.Date(string='Status Effective Date', tracking=True)
    last_updated_operator = fields.Char(string='Last Updated Operator', tracking=True)

    branch_id = fields.Many2one(
        'hr.department',
        string='Branch',
        domain=[('is_branch', '=', True)],
        tracking=True
    )

    # -------------------------------------------------
    # Assessor / Moderator
    # -------------------------------------------------
    is_assessors = fields.Boolean(string='Assessors')
    is_moderators = fields.Boolean(string='Moderators')

    assessor_seq_no = fields.Char(string='Assessor ID')
    moderator_seq_no = fields.Char(string='Moderator ID')

    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.today
    )

    end_date = fields.Date(
        string='End Date',
        default=lambda self: date(2018, 3, 31)
    )

    signature = fields.Binary(string='Signature')

    # -------------------------------------------------
    # Provider Details
    # -------------------------------------------------
    provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        domain=[('provider', '=', True)],
        tracking=True
    )

    provider_accreditation_num = fields.Char(
        string='Provider Identity Number',
        size=50,
        tracking=True
    )

    cont_number_home = fields.Char(string='Home Number', size=10, tracking=True)
    cont_number_office = fields.Char(string='Office Number', size=10, tracking=True)

    id_document_id = fields.Many2one(
        'ir.attachment',
        string='ID Document'
    )

    # -------------------------------------------------
    # Banking & SDF
    # -------------------------------------------------
    bank_name = fields.Char(string='Bank Name')
    branch_code = fields.Char(string='Branch Code')

    same_as_home = fields.Boolean(string='Same As Home Address')

    sdf_type = fields.Selection(
        [('internal', 'Internal'), ('consultant', 'Consultant')],
        string='SDF Type'
    )

    # -------------------------------------------------
    # Assessor / Moderator Documents
    # -------------------------------------------------
    registrationdoc_id = fields.Many2one('ir.attachment', string='Registration Documents')
    professionalbodydoc_id = fields.Many2one('ir.attachment', string='Professional Body')
    sram_doc_id = fields.Many2one('ir.attachment', string='Statement')
    cv_document_id = fields.Many2one('ir.attachment', string='CV Document')

    moderator_registrationdoc_id = fields.Many2one('ir.attachment', string='Registration Documents')
    moderator_professionalbodydoc_id = fields.Many2one('ir.attachment', string='Professional Body')
    moderator_sram_doc_id = fields.Many2one('ir.attachment', string='Statement')
    moderator_cv_document_id = fields.Many2one('ir.attachment', string='CV Document')
    moderator_unknown_type_document_id = fields.Many2one('ir.attachment', string='Type Document')

    # -------------------------------------------------
    # Equity & Demographics
    # -------------------------------------------------
    african = fields.Boolean(string='Is African')

    gender_saqa_code = fields.Selection(
        [('m', 'M'), ('f', 'F')],
        string='Gender SAQA Code'
    )

    equity = fields.Selection(
        [
            ('black_african', 'Black: African'),
            ('black_indian', 'Black: Indian / Asian'),
            ('black_coloured', 'Black: Coloured'),
            ('white', 'White'),
            ('other', 'Other'),
            ('unknown', 'Unknown'),
        ],
        string='Equity'
    )

    equity_saqa_code = fields.Selection(
        [('ba', 'BA'), ('bi', 'BI'), ('bc', 'BC'), ('oth', 'Oth'), ('u', 'U'), ('wh', 'Wh')],
        string='Equity SAQA Code'
    )

    socio_economic_status = fields.Selection(
        [
            ('employed', 'Employed'),
            ('unemployed', 'Unemployed, seeking work'),
            ('not_working', 'Not working, not looking'),
            ('home_maker', 'Home-maker'),
            ('student', 'Scholar/student'),
            ('retired', 'Pensioner/retired'),
            ('disabled', 'Not working - disabled'),
            ('no_wish', 'Not working - no wish to work'),
            ('nec', 'Not working - N.E.C.'),
            ('under_15', 'N/A: aged <15'),
            ('institution', 'N/A: Institution'),
            ('unspecified', 'Unspecified'),
        ],
        string='Socio Economic Status'
    )

    socio_economic_saqa_code = fields.Selection(
        [('1', '01'), ('2', '02'), ('3', '03'), ('4', '04'),
         ('6', '06'), ('7', '07'), ('8', '08'),
         ('9', '09'), ('10', '10'), ('97', '97'),
         ('98', '98'), ('u', 'U')],
        string='Socio Economic Status SAQA Code'
    )

    highest_education = fields.Char(string='Highest Education')
    current_occupation = fields.Char(string='Current Occupation')
    years_in_occupation = fields.Char(string='Years in Occupation')

    initials = fields.Char(string='Initials')

    work_municipality_id = fields.Many2one('res.municipality', string='Working Municipality')
    physical_municipality_id = fields.Many2one('res.municipality', string='Physical Municipality')
    postal_municipality_id = fields.Many2one('res.municipality', string='Postal Municipality')


    sdf_letter_from_employer_id = fields.Many2one(
        'ir.attachment',
        string='Letter of SDF appointment from employer'
    )

    unknown_type = fields.Selection(
        [('political_asylum', 'Political Asylum'), ('refugee', 'Refugee')],
        string='Type',
        copy=False
    )

    unknown_type_document_id = fields.Many2one(
        'ir.attachment',
        string='Type Document'
    )

    password = fields.Char(string='Password')

    primary_secondary = fields.Selection(
        [('primary', 'Primary'), ('secondary', 'Secondary')],
        string='Internal Type'
    )
    
    #  adding validation 
    @api.onchange('work_phone', 'cell', 'person_fax_number', 'work_email')
    def _onchange_validate_contact_details(self):
        for record in self:
            if record.work_email and '@' not in record.work_email:
                record.work_email = False
                return {
                    'warning': {
                        'title': _('Invalid Input'),
                        'message': _('Please enter a valid email address.'),
                    }
                }

            if record.work_phone and (not record.work_phone.isdigit() or len(record.work_phone) != 10):
                record.work_phone = False
                return {
                    'warning': {
                        'title': _('Invalid Input'),
                        'message': _('Please enter a 10-digit Phone number.'),
                    }
                }

            if record.cell and (not record.cell.isdigit() or len(record.cell) != 10):
                record.cell = False
                return {
                    'warning': {
                        'title': _('Invalid Input'),
                        'message': _('Please enter a 10-digit Mobile number.'),
                    }
                }

            if record.person_fax_number and (
                not record.person_fax_number.isdigit()
                or len(record.person_fax_number) != 10
            ):
                record.person_fax_number = False
                return {
                    'warning': {
                        'title': _('Invalid Input'),
                        'message': _('Please enter a 10-digit Fax number.'),
                    }
                }
       
    @api.onchange('citizen_resident_status_code')
    def _onchange_citizen_resident_status_code(self):
        for record in self:
            # Reset by default
            record.citizen_status_saqa_code = False

            if not record.citizen_resident_status_code:
                return

            if record.citizen_resident_status_code == 'sa':
                country = self.env['res.country'].search(
                    ['|', ('code', '=', 'ZA'), ('name', '=', 'South Africa')],
                    limit=1
                )
                record.citizen_status_saqa_code = 'sa'
                record.country_id = country

                return {
                    'domain': {
                        'country_id': [('id', '=', country.id)] if country else []
                    }
                }

            elif record.citizen_resident_status_code == 'dual':
                record.citizen_status_saqa_code = 'd'

            elif record.citizen_resident_status_code == 'other':
                record.citizen_status_saqa_code = 'o'

            elif record.citizen_resident_status_code == 'PR':
                record.citizen_status_saqa_code = 'pr'

            elif record.citizen_resident_status_code == 'unknown':
                record.citizen_status_saqa_code = 'u'

            else:
                return {
                    'domain': {
                        'country_id': []
                    }
                }

    @api.onchange('citizen_status_saqa_code')
    def _onchange_citizen_status_saqa_code(self):
        for record in self:
            if not record.citizen_status_saqa_code:
                record.citizen_resident_status_code = False
                return

            if record.citizen_status_saqa_code == 'sa':
                record.citizen_resident_status_code = 'sa'

            elif record.citizen_status_saqa_code == 'd':
                record.citizen_resident_status_code = 'dual'

            elif record.citizen_status_saqa_code == 'o':
                record.citizen_resident_status_code = 'other'

            elif record.citizen_status_saqa_code == 'pr':
                record.citizen_resident_status_code = 'PR'

            elif record.citizen_status_saqa_code == 'u':
                record.citizen_resident_status_code = 'unknown'
    
    @api.onchange('person_postal_suburb_id')
    def _onchange_person_postal_suburb(self):
        for record in self:
            suburb = record.person_postal_suburb_id
            if suburb:
                record.person_postal_zip = suburb.postal_code
                record.postal_municipality_id = suburb.municipality_id
                record.person_postal_city_id = suburb.city_id
                record.person_postal_province_code_id = suburb.province_id
            else:
                record.person_postal_zip = False
                record.postal_municipality_id = False
                record.person_postal_city_id = False
                record.person_postal_province_code_id = False
    
    @api.onchange('person_home_suburb_id')
    def _onchange_person_home_suburb(self):
        for record in self:
            suburb = record.person_home_suburb_id
            if suburb:
                record.person_home_zip = suburb.postal_code
                record.physical_municipality_id = suburb.municipality_id
                record.person_home_city_id = suburb.city_id
                record.person_home_province_code_id = suburb.province_id
            else:
                record.person_home_zip = False
                record.physical_municipality_id = False
                record.person_home_city_id = False
                record.person_home_province_code_id = False
                
    @api.onchange('person_suburb_id')
    def _onchange_person_suburb(self):
        for record in self:
            suburb = record.person_suburb_id
            if suburb:
                record.work_zip = suburb.postal_code
                record.work_municipality_id = suburb.municipality_id
                record.work_city_id = suburb.city_id
                record.work_province_id = suburb.province_id
            else:
                record.work_zip = False
                record.work_municipality_id = False
                record.work_city_id = False
                record.work_province_id = False
    
    @api.onchange('identification_id', 'citizen_resident_status_code')
    def _onchange_identification_id(self):
        for record in self:
            id_no = record.identification_id

            if not id_no:
                return

            # ----------------------------------------
            # Duplicate check (SA & Dual only)
            # ----------------------------------------
            if record.citizen_resident_status_code in ('sa', 'dual'):
                duplicate = self.search([
                    ('identification_id', '=', id_no),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    record.identification_id = False
                    return {
                        'warning': {
                            'title': _('Duplicate Identification Number'),
                            'message': _('This Identification Number already exists.'),
                        }
                    }

            # ----------------------------------------
            # Validate SA ID format
            # ----------------------------------------
            if not (id_no.isdigit() and len(id_no) == 13):
                record.identification_id = False
                return {
                    'warning': {
                        'title': _('Invalid Identification Number'),
                        'message': _('Identification Number must be 13 numeric digits.'),
                    }
                }

            year = int(id_no[:2])
            month = int(id_no[2:4])
            day = int(id_no[4:6])

            if month < 1 or month > 12:
                record.identification_id = False
                return {
                    'warning': {
                        'title': _('Invalid Identification Number'),
                        'message': _('Invalid month in Identification Number.'),
                    }
                }

            # Resolve century
            full_year = 2000 + year if year <= 20 else 1900 + year

            last_day = calendar.monthrange(full_year, month)[1]
            if day < 1 or day > last_day:
                record.identification_id = False
                return {
                    'warning': {
                        'title': _('Invalid Identification Number'),
                        'message': _('Invalid day in Identification Number.'),
                    }
                }

            # ----------------------------------------
            # Set birth date
            # ----------------------------------------
            record.person_birth_date = datetime(
                full_year, month, day
            ).date()
    
    @api.onchange('same_as_home')
    def _onchange_same_as_home(self):
        for record in self:
            if not record.same_as_home:
                return

            record.person_postal_address_1 = record.person_home_address_1
            record.person_postal_address_2 = record.person_home_address_2
            record.person_postal_address_3 = record.person_home_address_3
            record.person_postal_suburb_id = record.person_home_suburb_id
            record.person_postal_city_id = record.person_home_city_id
            record.person_postal_province_code_id = record.person_home_province_code_id
            record.person_postal_zip = record.person_home_zip
            record.country_postal_id = record.country_home_id
    
    
    def open_map(self, street=None, city=None, state=None, country=None, zip_code=None):
        self.ensure_one()

        parts = []

        if street:
            parts.append(street)
        if city:
            parts.append(city.name)
        if state:
            parts.append(state.name)
        if country:
            parts.append(country.name)
        if zip_code:
            parts.append(zip_code)

        address = quote_plus(" ".join(parts))

        url = f"https://www.google.com/maps/search/?api=1&query={address}"

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
        
    
    # -------------------------------------------------
    # Work Address Map
    # -------------------------------------------------
    def work_addr_map(self):
        self.ensure_one()
        return self.open_map(
            street=self.work_address,
            city=self.work_city_id,
            state=self.work_province_id,
            country=self.work_country_id,
            zip_code=self.work_zip,
        )

    # -------------------------------------------------
    # Home Address Map
    # -------------------------------------------------
    def home_addr_map(self):
        self.ensure_one()
        return self.open_map(
            street=self.person_home_address_1,
            city=self.person_home_city_id,
            state=self.person_home_province_code_id,
            country=self.country_home_id,
            zip_code=self.person_home_zip,
        )

    # -------------------------------------------------
    # Postal Address Map
    # -------------------------------------------------
    def postal_addr_map(self):
        self.ensure_one()
        return self.open_map(
            street=self.person_postal_address_1,
            city=self.person_postal_city_id,
            state=self.person_postal_province_code_id,
            country=self.country_postal_id,
            zip_code=self.person_postal_zip,
        )  

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        model = vals.get('model')
        res_id = vals.get('res_id')
        body = vals.get('body', '') or ''

        # -------------------------------------------------
        # HR Employee Messages
        # -------------------------------------------------
        if model == 'hr.employee' and res_id:
            employee = self.env['hr.employee'].browse(res_id)
            if employee.exists() and 'created' in body.lower():

                if employee.is_sdf:
                    vals['body'] = '<p>SDF Created</p>'

                elif employee.is_learner:
                    vals['body'] = '<p>Learner Created</p>'

                elif employee.is_assessors:
                    vals['body'] = '<p>Assessor Created</p>'

                elif employee.is_moderators:
                    vals['body'] = '<p>Moderator Created</p>'

        # -------------------------------------------------
        # Partner Messages
        # -------------------------------------------------
        elif model == 'res.partner' and res_id:
            partner = self.env['res.partner'].browse(res_id)
            if partner.exists() and 'created' in body.lower():

                if partner.employer:
                    vals['body'] = '<p>Employer Created</p>'

                elif partner.provider:
                    vals['body'] = '<p>Provider Created</p>'

        return super().create(vals)

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    is_branch = fields.Boolean(string='Branch')
    parent_branch_id = fields.Many2one('hr.department', string='Parent Branch')
    code = fields.Char(string='Code')
    branch_address1 = fields.Char(string='Address 1')
    branch_address2 = fields.Char(string='Address 2')
    branch_address3 = fields.Char(string='Address 3')
    branch_city = fields.Char(string='City')
    branch_province_id = fields.Many2one('res.country.state', string='Province')
    branch_zip = fields.Char(string='Zip')
    branch_country_id = fields.Many2one('res.country', string='Country')
    dept_branch_id = fields.Many2one('hr.department', string='Branch')

    @api.onchange('branch_province_id')
    def _onchange_branch_province(self):
        for record in self:
            if record.branch_province_id:
                record.branch_country_id = record.branch_province_id.country_id
            else:
                record.branch_country_id = False


## For Locality in South Africa
class ResDistrict(models.Model):
    _name = 'res.district'
    _description = 'District'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    province_id = fields.Many2one('res.country.state', string='Province')
    country_id = fields.Many2one('res.country', string='Country')
    urban_rural = fields.Selection(
        [('urban', 'Urban'), ('rural', 'Rural'), ('unknown', 'Unknown')],
        string='Urban/Rural'
    )

class ResCity(models.Model):
    _name = 'res.city'
    _description = 'City'

    name = fields.Char(string='Name', required=True)
    district_id = fields.Many2one('res.district', string='District')
    province_id = fields.Many2one('res.country.state', string='Province')
    country_id = fields.Many2one('res.country', string='Country')
    urban_rural = fields.Selection(
        [('urban', 'Urban'), ('rural', 'Rural'), ('unknown', 'Unknown')],
        string='Urban/Rural'
    )
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")

class ResMunicipality(models.Model):
    _name = 'res.municipality'
    _description = 'Municipality'

    name = fields.Char(string='Name', required=True)
    city_id = fields.Many2one('res.city', string='City')
    district_id = fields.Many2one('res.district', string='District')
    province_id = fields.Many2one('res.country.state', string='Province')
    country_id = fields.Many2one('res.country', string='Country')
    urban_rural = fields.Selection(
        [('urban', 'Urban'), ('rural', 'Rural'), ('unknown', 'Unknown')],
        string='Urban/Rural'
    )

class ResSuburb(models.Model):
    _name = 'res.suburb'
    _description = 'Suburb'

    name = fields.Char(string='Name', required=True)
    postal_code = fields.Char(string='Postal Code')
    municipality_id = fields.Many2one('res.municipality', string='Municipality')
    city_id = fields.Many2one('res.city', string='City')
    district_id = fields.Many2one('res.district', string='District')
    province_id = fields.Many2one('res.country.state', string='Province')
    country_id = fields.Many2one('res.country', string='Country')
    urban_rural = fields.Selection(
        [('urban', 'Urban'), ('rural', 'Rural'), ('unknown', 'Unknown')],
        string='Urban/Rural'
    )
    statssa_area_code = fields.Char(string='StatsSA Area Code')

class ProjectDocument(models.Model):
    _name = 'project.document'
    _description = 'Project Document'

    name = fields.Char(string='Name', required=True)

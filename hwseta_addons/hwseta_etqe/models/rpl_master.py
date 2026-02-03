import base64
import calendar
import random
import logging
from datetime import datetime
import datetime as dt

from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# -------------------- DEBUG LOGGER --------------------
DEBUG = True

_logger = logging.getLogger(__name__)

def dbg(msg):
    if DEBUG:
        _logger.info(msg)


class RplMaster(models.Model):
    _name = 'rpl.master'
    _description = 'RPL Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # -------------------- VIEW OVERRIDE --------------------
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and res.get('arch'):
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in list(sheet):
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    # -------------------- COMPUTE --------------------
    @api.depends('state', 'final_state', 'approved')
    def compute_reject_button_visibility(self):
        compare_dict = {
            'general_info': ['hwseta_etqe.group_seta_administrator'],
            'public_info': ['hwseta_etqe.group_seta_administrator'],
            'personal_info': ['hwseta_etqe.group_seta_administrator'],
            'address_info': ['hwseta_etqe.group_seta_administrator'],
            'qualification_info': ['hwseta_etqe.group_seta_administrator'],
            'verification': ['hwseta_etqe.group_seta_administrator', 'hwseta_etqe.group_etqe_provincial_administrator'],
            'evaluation': ['hwseta_etqe.group_seta_administrator', 'hwseta_etqe.group_etqe_provincial_officer',
                           'hwseta_etqe.group_etqe_provincial_manager'],
            'approved': ['hwseta_etqe.group_seta_administrator'],
            'denied': ['hwseta_etqe.group_seta_administrator'],
        }

        final_states = {
            'Draft': ['hwseta_etqe.group_seta_administrator'],
            'Submitted': ['hwseta_etqe.group_seta_administrator', 'hwseta_etqe.group_etqe_provincial_administrator'],
            'Evaluated': ['hwseta_etqe.group_seta_administrator', 'hwseta_etqe.group_etqe_provincial_officer'],
            'Recommended': ['hwseta_etqe.group_seta_administrator', 'hwseta_etqe.group_etqe_provincial_manager'],
            'Approved': ['hwseta_etqe.group_seta_administrator'],
            'Rejected': ['hwseta_etqe.group_seta_administrator'],
        }

        for rec in self:
            rec.reject_button_is_visible = False
            current_groups = compare_dict.get(rec.state, [])
            final_groups = final_states.get(rec.final_state, [])
            if not rec.approved and any(self.env.user.has_group(g) for g in current_groups) and any(
                    self.env.user.has_group(g) for g in final_groups):
                rec.reject_button_is_visible = True

    # -------------------- BASIC INFO --------------------
    name = fields.Char(string="Name")
    current_occupation = fields.Char()
    highest_education = fields.Char()
    years_in_occupation = fields.Char()

    work_email = fields.Char()
    work_phone = fields.Char(size=10)
    mobile_phone = fields.Char(size=10)
    work_location = fields.Char()

    user_id = fields.Many2one('res.users')
    company_id = fields.Many2one('res.company')

    identification_id = fields.Char(size=13)
    passport_id = fields.Char()
    national_id = fields.Char(size=20)

    person_last_name = fields.Char(size=45)
    person_initials = fields.Char(size=10)
    person_middle_name = fields.Char(size=50)

    person_birth_date = fields.Date()
    gender = fields.Selection([('M', 'Male'), ('F', 'Female')])
    marital = fields.Selection([
        ('single', 'Single'), ('married', 'Married'),
        ('widower', 'Widower'), ('divorced', 'Divorced')
    ])

    # -------------------- STATUS --------------------
    state = fields.Selection([
        ('general_info', 'General Information'),
        ('public_info', 'Public Information'),
        ('personal_info', 'Personal Information'),
        ('address_info', 'Address Information'),
        ('verification', 'Verification'),
        ('evaluation', 'Evaluation'),
        ('approved', 'Approved'),
        ('denied', 'Rejected'),
    ], default='general_info', tracking=True)

    submitted = fields.Boolean()
    verify = fields.Boolean()
    evaluate = fields.Boolean()
    approved = fields.Boolean()
    denied = fields.Boolean()

    # -------------------- RPL --------------------
    is_rpl = fields.Boolean()
    rpl_ref = fields.Char(readonly=True)
    rpl_state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted')
    ], default='draft', readonly=True, tracking=True)

    rpl_approval_date = fields.Date()
    rpl_register_date = fields.Date()

    final_state = fields.Char()
    reject_button_is_visible = fields.Boolean(compute='compute_reject_button_visibility')

    # -------------------- DOCUMENTS --------------------
    id_document = fields.Many2one('ir.attachment')
    rpl_certificate = fields.Many2one('ir.attachment')
    sram_doc = fields.Many2one('ir.attachment')
    cv_document = fields.Many2one('ir.attachment')

    id_document_bool = fields.Boolean()
    rpl_certificate_bool = fields.Boolean()
    sram_doc_bool = fields.Boolean()
    cv_document_bool = fields.Boolean()

    # -------------------- MISC --------------------
    comment_line = fields.Text()
    popi_accept = fields.Boolean()
    pre_popi_date = fields.Boolean(default=False)

    equity = fields.Selection([
        ('BA', 'Black: African'), ('BI', 'Indian / Asian'),
        ('BC', 'Coloured'), ('Wh', 'White'), ('Oth', 'Other'), ('U', 'Unknown')
    ])

    socio_economic_status = fields.Selection([
        ('01', 'Employed'),
        ('02', 'Unemployed, seeking work'),
        ('03', 'Not working, not looking'),
        ('04', 'Home-maker'),
        ('06', 'Scholar/student'),
        ('07', 'Pensioner'),
        ('08', 'Disabled'),
        ('09', 'No wish to work'),
        ('10', 'N.E.C.'),
        ('97', 'Under 15'),
        ('98', 'Institution'),
        ('U', 'Unspecified')
    ])

    rpl_seq_no = fields.Char()
    update_disclaimer = fields.Boolean()
    reg_start = fields.Date(string='Registration Start Date')
    person_cell_phone_number = fields.Char(string='Cell Phone Number', size=10)
    work_address = fields.Char(string='Work Address')
    work_address2 = fields.Char(string='Street2')
    work_address3 = fields.Char(string='Street3')
    person_suburb = fields.Many2one('res.suburb', string='Suburb')
    person_home_suburb = fields.Many2one('res.suburb', string='Home Suburb')
    person_postal_suburb = fields.Many2one('res.suburb', string='Postal Suburb')
    person_name = fields.Char(string='Name', track_visibility='onchange', size=50)
    cont_number_home = fields.Char(string='Home Number', track_visibility='onchange', size=10)
    cont_number_office = fields.Char(string='Office Number', track_visibility='onchange', size=10)
    duplicate_checkbox = fields.Boolean(string='Duplicate Transaction Checkbox')
    duplicate_note = fields.Text(string='Duplication Notes', track_visibility='onchange')
    # professionalbodydoc_bool = fields.Boolean(string='Verify')
    same_as_home = fields.Boolean(string='Same As Home Address')
    disability = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Disability")
    rpl_id = fields.Char(string='RPL ID')

    unknown_type = fields.Selection([
        ('political_asylum', 'Political Asylum'),
        ('refugee', 'Refugee'),
    ], string='Type',
        track_visibility='onchange', copy=False)
    unknown_type_document = fields.Many2one('ir.attachment', string="Type Document")
    password = fields.Char("Password")
    work_city = fields.Many2one('res.city', string='Work City', track_visibility='onchange')
    work_zip = fields.Char(string='Zip')
    work_country = fields.Many2one('res.country', string='Country')
    country_id = fields.Many2one('res.country', string='Nationality')
    bank_account_number = fields.Char(string='Bank Account Number')
    otherid = fields.Char(string='Other Id')
    home_language_code = fields.Many2one('res.lang', string='Home Language Code', track_visibility='onchange', size=6)
    citizen_resident_status_code = fields.Selection(
        [('D', 'D - Dual (SA plus other)'), ('O', 'O - Other'), ('PR', 'PR - Permanent Resident'),
         ('SA', 'SA - South Africa'), ('U', 'U - Unknown')], string='Citizen Status')
    address_home_id = fields.Many2one('res.partner', string='Home Address')
    person_alternate_id = fields.Char(string='Person Alternate Id', size=20)
    alternate_id_type_id = fields.Char(string='Alternate Type Id', size=3)

    person_title = fields.Selection(
        [('adv', 'Adv.'), ('dr', 'Dr.'), ('mr', 'Mr.'), ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('prof', 'Prof.')],
        string='Title', track_visibility='onchange')

    birthday = fields.Date(string='Date of Birth')
    address_home = fields.Char(string='Home Address')
    person_home_address_1 = fields.Char(string='Home Address 1', size=50)
    person_home_address_2 = fields.Char(string='Home Address 2', size=50)
    person_home_address_3 = fields.Char(string='Home Address 3', size=50)
    person_postal_address_1 = fields.Char(string='Postal Address 1', size=50)
    person_postal_address_2 = fields.Char(string='Postal Address 2', size=50)
    person_postal_address_3 = fields.Char(string='Postal Address 3', size=50)
    person_home_addr_postal_code = fields.Char(string='Home Addr Postal Code', size=4)
    person_home_addr_post_code = fields.Char(string='Home Addr Post Code', size=4)
    person_fax_number = fields.Char(string='Fax Number', size=10)
    person_home_province_code = fields.Many2one('res.country.state', string='Province Code')
    person_postal_province_code = fields.Many2one('res.country.state', string='Province Code')
    provider_code = fields.Char(string='Provider Code', size=20)
    country_home = fields.Many2one('res.country', string='Country')
    country_postal = fields.Many2one('res.country', string='Country')
    person_home_city = fields.Many2one('res.city', string='Home City', track_visibility='onchange')
    person_postal_city = fields.Many2one('res.city', string='Postal City', track_visibility='onchange')
    person_home_zip = fields.Char(string='Zip')
    person_postal_zip = fields.Char(string='Zip')

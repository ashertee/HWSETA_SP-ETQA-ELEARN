import base64, calendar, random, logging
from datetime import datetime
import datetime as dt
import calendar
from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo import models, fields, api, _, Command, tools
from odoo.exceptions import UserError, ValidationError

DEBUG = True
logger = logging.getLogger(__name__)

def dbg(msg):
    logger.info(msg) if DEBUG else None

class RplStatus(models.Model):
    _name = 'rpl.status'
    _description = 'RPL Practitioner Status'

    rpl_status_id = fields.Many2one('rpl.register', string='RPL Practitioner Status Reference')
    rpl_name = fields.Char(string='Name')
    rpl_status = fields.Char(string='Status')
    rpl_comment = fields.Char(string='Comment')
    rpl_date = fields.Datetime(string='Date')
    rpl_update_date = fields.Datetime(string='Update Date')



class RplRegister(models.Model):
    _name = 'rpl.register'
    # _inherit = 'mail.thread'
    _description = 'RPL Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu
        )
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

    @api.depends('state', 'final_state', 'approved')
    def compute_reject_button_visibility(self):
        for rec in self:
            rec.reject_button_is_visible = False

            compare_dict = {
                'general_info': ['hwseta_etqe.group_seta_administrator'],
                'public_info': ['hwseta_etqe.group_seta_administrator'],
                'personal_info': ['hwseta_etqe.group_seta_administrator'],
                'address_info': ['hwseta_etqe.group_seta_administrator'],
                'qualification_info': ['hwseta_etqe.group_seta_administrator'],
                'verification': [
                    'hwseta_etqe.group_seta_administrator',
                    'hwseta_etqe.group_etqe_officer'
                ],
                'evaluation': [
                    'hwseta_etqe.group_seta_administrator',
                    'hwseta_etqe.group_etqe_manager',
                    'hwseta_etqe.group_etqe_executive_manager'
                ],
                'approved': [
                    'hwseta_etqe.group_seta_administrator',
                    'hwseta_etqe.group_etqe_executive_manager'
                ],
                'denied': ['hwseta_etqe.group_seta_administrator'],
            }

            final_states = {
                'Draft': ['hwseta_etqe.group_seta_administrator'],
                'Submitted': [
                    'hwseta_etqe.group_seta_administrator',
                    'hwseta_etqe.group_etqe_officer'
                ],
                'Evaluated': [
                    'hwseta_etqe.group_seta_administrator',
                    'hwseta_etqe.group_etqe_manager'
                ],
                'Recommended': [
                    'hwseta_etqe.group_seta_administrator',
                    'hwseta_etqe.group_etqe_executive_manager'
                ],
                'Approved': ['hwseta_etqe.group_seta_administrator'],
                'Rejected': ['hwseta_etqe.group_seta_administrator'],
            }

            current_groups = compare_dict.get(rec.state)
            final_groups = final_states.get(rec.final_state)

            if not current_groups or not final_groups or rec.approved:
                continue

            user = rec.env.user
            if (
                any(user.has_group(g) for g in current_groups)
                and any(user.has_group(g) for g in final_groups)
            ):
                rec.reject_button_is_visible = True

    # -----------------------------
    # Fields (only related ones)
    # -----------------------------
    final_state = fields.Char(string='Final State')
    approved = fields.Boolean(string='Approved')
    reject_button_is_visible = fields.Boolean(
        compute='compute_reject_button_visibility',
        default=False
    )


    # temp_rpl_seq_no = fields.Char("RPL ID")
    # temp_rpl_seq_no = fields.Char("Moderator ID")
    # already_registered = fields.Boolean("Re-registration", default=False)
    # search_by = fields.Selection([('id', 'Identification No'), ('number', 'Assessor/Moderator Number')],
    #                              string="Search by")
    name = fields.Char(string="Name")
    current_occupation = fields.Char(string="Current Occupation")
    highest_education = fields.Char(string="Highest Education")
    years_in_occupation = fields.Char(string="Years In Occupation")

    work_email = fields.Char(string='Work Email')
    work_phone = fields.Char(string='Work Phone', size=10)
    mobile_phone = fields.Char(string='Work Mobile', size=10)
    work_location = fields.Char(string='Office Location')
    user_id = fields.Many2one('res.users', string='Related User')
    company_id = fields.Many2one('res.company', string='Company')
    work_address = fields.Char(string='Work Address')
    work_address2 = fields.Char(string='Street2')
    work_address3 = fields.Char(string='Street3')
    work_city = fields.Many2one('res.city', string='Work City')
    work_province = fields.Many2one('res.country.state', string='Province')
    work_zip = fields.Char(string='Zip')
    work_country = fields.Many2one('res.country', string='Country')
    country_id = fields.Many2one('res.country', string='Nationality')

    identification_id = fields.Char(string='Identification No', size=13)
    passport_id = fields.Char(string='Passport No')
    bank_account_number = fields.Char(string='Bank Account Number')
    otherid = fields.Char(string='Other Id')
    national_id = fields.Char(string='National Id', size=20)

    home_language_code = fields.Many2one('res.lang', string='Home Language Code')
    citizen_resident_status_code = fields.Selection([
        ('D', 'D - Dual (SA plus other)'),
        ('O', 'O - Other'),
        ('PR', 'PR - Permanent Resident'),
        ('SA', 'SA - South Africa'),
        ('U', 'U - Unknown')
    ], string='Citizen Status')

    address_home_id = fields.Many2one('res.partner', string='Home Address')
    person_alternate_id = fields.Char(string='Person Alternate Id', size=20)
    alternate_id_type_id = fields.Char(string='Alternate Type Id', size=3)
    person_last_name = fields.Char(string='Surname', size=45)
    person_initials = fields.Char(string='Initials', size=10)
    person_middle_name = fields.Char(string='Middle Name', size=50)

    person_title = fields.Selection([
        ('adv', 'Adv.'),
        ('dr', 'Dr.'),
        ('mr', 'Mr.'),
        ('mrs', 'Mrs.'),
        ('ms', 'Ms.'),
        ('prof', 'Prof.')
    ], string='Title')

    person_birth_date = fields.Date(string='Birth Date')
    gender = fields.Selection([('M', 'Male'), ('F', 'Female')], string='Gender')
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status')

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

    person_cell_phone_number = fields.Char(string='Cell Phone Number', size=10)
    person_fax_number = fields.Char(string='Fax Number', size=10)

    person_home_province_code = fields.Many2one('res.country.state', string='Province Code')
    person_postal_province_code = fields.Many2one('res.country.state', string='Province Code')

    provider_code = fields.Char(string='Provider Code', size=20)
    country_home = fields.Many2one('res.country', string='Country')
    country_postal = fields.Many2one('res.country', string='Country')

    person_home_city = fields.Many2one('res.city', string='Home City')
    person_postal_city = fields.Many2one('res.city', string='Postal City')

    person_home_zip = fields.Char(string='Zip')
    person_postal_zip = fields.Char(string='Zip')

    state = fields.Selection([
        ('general_info', 'General Information'),
        ('public_info', 'Public Information'),
        ('personal_info', 'Personal Information'),
        ('address_info', 'Address Information'),
        ('verification', 'Verification'),
        ('evaluation', 'Evaluation'),
        ('approved', 'Approved'),
        ('denied', 'Rejected'),
    ], string='Status', default='general_info', index=True, copy=False)

    submitted = fields.Boolean(string='Submitted')
    verify = fields.Boolean(string='Verify')
    evaluate = fields.Boolean(string='Evaluate')
    denied = fields.Boolean(string='Denied')

    is_rpl = fields.Boolean(string='RPL')
    rpl_ref = fields.Char(string='Reference Number', size=50, readonly=True)

    person_suburb = fields.Many2one('res.suburb', string='Suburb')
    person_home_suburb = fields.Many2one('res.suburb', string='Home Suburb')
    person_postal_suburb = fields.Many2one('res.suburb', string='Postal Suburb')

    person_name = fields.Char(string='Name', size=50)
    cont_number_home = fields.Char(string='Home Number', size=10)
    cont_number_office = fields.Char(string='Office Number', size=10)

    duplicate_checkbox = fields.Boolean(string='Duplicate Transaction Checkbox')
    duplicate_note = fields.Text(string='Duplication Notes')

    id_document = fields.Many2one('ir.attachment', string='ID Document')
    rpl_certificate = fields.Many2one('ir.attachment', string='RPL Practitioner Certificate')
    sram_doc = fields.Many2one('ir.attachment', string='Statement of Results')

    id_document_bool = fields.Boolean(string='Verify')
    rpl_certificate_bool = fields.Boolean(string='Verify')
    sram_doc_bool = fields.Boolean(string='Verify')

    same_as_home = fields.Boolean(string='Same As Home Address')
    disability = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Disability')

    rpl_id = fields.Char(string='RPL ID')
    comment_line = fields.Text(string='Status Comment')

    rpl_state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted')
    ], string='Status', default='draft', readonly=True)

    rpl_approval_date = fields.Date(string='RPL Approval Date')
    rpl_register_date = fields.Date(string='RPL Application Date')
    reg_start = fields.Date(string='Registration Start Date')

    unknown_type = fields.Selection([
        ('political_asylum', 'Political Asylum'),
        ('refugee', 'Refugee')
    ], string='Type')

    unknown_type_document = fields.Many2one('ir.attachment', string='Type Document')

    password = fields.Char(string='Password')

    cv_document = fields.Many2one('ir.attachment', string='CV Document')
    cv_document_bool = fields.Boolean(string='Verify')



    popi_accept = fields.Boolean()
    pre_popi_date = fields.Boolean(default=False)

    equity = fields.Selection([
        ('BA', 'Black: African'),
        ('BI', 'Indian / Asian'),
        ('BC', 'Coloured'),
        ('Oth', 'Other'),
        ('U', 'Unknown'),
        ('Wh', 'White')
    ], string='Equity')


    socio_economic_status = fields.Selection([
    ('01', 'Employed'),
    ('02', 'Unemployed, seeking work'),
    ('03', 'Not working, not looking'),
    ('04', 'Home-maker (not working)'),
    ('06', 'Scholar/student (not w.)'),
    ('07', 'Pensioner/retired (not w.)'),
    ('08', 'Not working - disabled'),
    ('09', 'Not working - no wish to w'),
    ('10', 'Not working - N.E.C.'),
    ('97', 'N/A: aged <15'),
    ('98', 'N/A: Institution'),
    ('U', 'Unspecified'),
    
    ], string='Socio Economic Status')

    rpl_seq_no = fields.Char(string='RPL ID')

    rpl_status_ids = fields.One2many(
        'rpl.status',
        'rpl_status_id',
        string='Status Line'
    )

    # assessors_moderators_status_ids = fields.One2many('assessors.moderators.status',
    #                                                   'assessors_moderators_status_mo_id', 'Status Line')
    # socio_economic_saqa_code = fields.Selection(
    #     [('1', '01'), ('2', '02'), ('3', '03'), ('4', '04'), ('6', '6'), ('7', '07'), ('8', '08'), ('9', '09'),
    #      ('10', '10'), ('97', '97'), ('98', '98'), ('U', 'U')], string='Socio Economic Status SAQA Code')



    @api.onchange('search_by', 'existing_assessor_moderator')
    def on_change_search_by(self):
        if not self.search_by:
            self.existing_assessor_id = False
            self.existing_assessor_number = False
            self.existing_moderator_id = False
            self.existing_moderator_number = False
        elif self.search_by == 'number' and self.existing_assessor_moderator == 'ex_assessor':
            self.existing_assessor_number = (
                self.env.user.assessor_moderator_id.assessor_seq_no
                if self.env.user.assessor_moderator_id else False
            )
        elif self.search_by == 'number' and self.existing_assessor_moderator == 'ex_moderator':
            am = self.env.user.assessor_moderator_id
            self.existing_assessor_number = am.assessor_seq_no if am else False
            self.existing_moderator_number = am.moderator_seq_no if am else False

    @api.onchange('citizen_resident_status_code')
    def onchange_crc(self):
        if self.citizen_resident_status_code == 'sa':
            country = self.env['res.country'].search(
                ['|', ('code', '=', 'ZA'), ('name', '=', 'South Africa')], limit=1
            )
            self.country_id = country.id if country else False
        else:
            self.country_id = False

    @api.onchange('person_postal_suburb')
    def onchange_person_postal_suburb(self):
        if self.person_postal_suburb:
            suburb = self.person_postal_suburb
            self.person_postal_zip = suburb.postal_code
            self.person_postal_city = suburb.city_id
            self.person_postal_province_code = suburb.province_id

    @api.onchange('person_home_suburb')
    def onchange_person_home_suburb(self):
        if self.person_home_suburb:
            suburb = self.person_home_suburb
            self.person_home_zip = suburb.postal_code
            self.person_home_city = suburb.city_id
            self.physical_municipality = suburb.municipality_id
            self.person_home_province_code = suburb.province_id

    @api.onchange('person_suburb')
    def onchange_person_suburb(self):
        if self.person_suburb:
            suburb = self.person_suburb
            self.work_zip = suburb.postal_code
            self.work_city = suburb.city_id
            self.work_province = suburb.province_id

    @api.onchange('identification_id')
    def onchange_id_no(self):
        if not self.identification_id:
            return

        check = checkers.said_check(self.identification_id)
        year, month, day = check['year'], check['month'], check['day']

        if not check.get('valid'):
            old_check = checkers.old_said_check(self.identification_id)

            if "Invalid gender" in old_check:
                self.identification_id = False
                raise UserError(_("Invalid Gender in Identification Number"))

            if "Invalid citizenship status" in old_check:
                self.identification_id = False
                raise UserError(_("Invalid Citizenship Status in Identification Number"))

            if not (1 <= int(day) <= 31):
                self.identification_id = False
                raise UserError(_("Incorrect Day in Identification Number"))

            if not (1 <= int(month) <= 12):
                self.identification_id = False
                raise UserError(_("Incorrect Month in Identification Number"))

            x_year = int(year) or 2000
            last_day = calendar.monthrange(x_year, int(month))[1]
            if int(day) > last_day:
                self.identification_id = False
                raise UserError(_("Incorrect last day of month in Identification Number"))

            self.identification_id = False
            raise UserError(_("Incorrect checksum in Identification Number"))

    # 	if "Invalid control bit" in checkers.said_check(identification_id):
    # 		return {
    # 			'value': {'identification_id': ''},
    # 			'warning': {'title': 'Invalid Identification Number',
    # 						'message': 'this Id Number is invalid!'}}
    # if len(identification_id) == 13 and str(identification_id).isdigit():
    # 	if not self.already_registered and not self.is_extension_of_scope and self.assessor_moderator == 'assessor':
    # 		exist_assr = self.env['hr.employee'].search(
    # 			[('is_assessors', '=', True), ('assessor_moderator_identification_id', '=', identification_id)])
    # 		exist_ass_mod = self.env['assessors.moderators.register'].search(
    # 			[('final_state', '!=', 'Rejected'), ('identification_id', '=', identification_id)])
    # 		if exist_assr or exist_ass_mod:
    # 			return {'value': {'identification_id': ''},
    # 					'warning': {'title': 'Duplicate Entry (Aleady Exist In the Master)',
    # 								'message': 'Please enter unique Identification Number!'}}
    # 	gender_digit = str(identification_id)[6:10]
    # 	citizenship = str(identification_id)[10:11]
    # 	if gender_digit:
    # 		if int(gender_digit) <= 4999:
    # 			val.update({'gender': 'female'})
    # 		elif int(gender_digit) >= 5000:
    # 			val.update({'gender': 'male'})
    # 	if citizenship:
    # 		if int(citizenship) == 0:
    # 			val.update({'citizen_resident_status_code': 'sa'})
    # 		elif int(citizenship) == 1:
    # 			val.update({'citizen_resident_status_code': 'PR'})
    # 	year = identification_id[:2]
    # 	identification_id = identification_id[2:]
    # 	month = identification_id[:2]
    # 	identification_id = identification_id[2:]
    # 	day = identification_id[:2]
    # 	if int(month) > 12 or int(month) < 1 or int(day) > 31 or int(day) < 1:
    # 		return {'value': {'identification_id': ''}, 'warning': {'title': 'Invalid Identification Number',
    # 																'message': 'Incorrect Identification Number!'}}
    # 	else:
    # 		# # Calculating last day of month.
    # 		x_year = int(year)
    # 		if x_year == 00:
    # 			x_year = 2000
    # 		last_day = calendar.monthrange(int(x_year), int(month))[1]
    # 		if int(day) > last_day:
    # 			return {'value': {'identification_id': ''}, 'warning': {'title': 'Invalid Identification Number',
    # 																	'message': 'Incorrect Identification Number!'}}
    # 	if int(year) == 00 or int(year) >= 01 and int(year) <= 20:
    # 		birth_date = datetime.strptime('20' + year + '-' + month + '-' + day, '%Y-%m-%d').date()
    # 	else:
    # 		birth_date = datetime.strptime('19' + year + '-' + month + '-' + day, '%Y-%m-%d').date()
    #
    # 	val.update({'person_birth_date': birth_date})
    # 	res.update({'value': val})
    # 	return res
    # else:
    # 	return {'value': {'identification_id': ''}, 'warning': {'title': 'Invalid Identification Number',
    # 															'message': 'Identification Number should be numeric!'}}

    # @api.multi
    # def onchange_assessor_moderator(self, assessor_moderator):
    #     res = {}
    #     if not assessor_moderator:
    #         return res
    #     if assessor_moderator == 'assessor':
    #         res.update({'value': {'is_assessors': True}})
    #         res.update({'value': {'is_moderators': False}})
    #     if assessor_moderator == 'moderator':
    #         res.update({'value': {'is_moderators': True}})
    #         res.update({'value': {'is_assessors': False}})
    #     return res

    # @api.multi
    # def onchange_assessor_id(self, assessor_id):
    #     res = {}
    #     if not assessor_id:
    #         return res
    #     assessors_objects = self.env['hr.employee'].search([('assessor_seq_no', '=', assessor_id)])
    #     ase_lst = []
    #     for ase_obj in assessors_objects:
    #         ase_lst.append(ase_obj.id)
    #     assessors_ids = []
    #     if ase_lst:
    #         assessors_ids = self.env['hr.employee'].search([('id', '=', max(ase_lst))])
    #     if assessors_ids:
    #         for assessor_data in assessors_ids:
    #             if assessor_data.end_date:
    #                 if assessor_data.end_date < str(datetime.now().date()):
    #                     #                         raise Warning(_("Sorry! %s Assessor is currently In-Active") % (assessor_id))
    #                     return {'value': {'assessor_id': ''}, 'warning': {'title': 'In-Active Assessor ID',
    #                                                                       'message': 'Sorry! Assessor is currently In-Active'}}
    #
    #             q_vals_line = []
    #             if assessor_data.qualification_ids:
    #                 for q_lines in assessor_data.qualification_ids:
    #                     if q_lines.qualification_status == 'approved':
    #                         qual_master_obj = self.env['provider.qualification'].search(
    #                             [('id', '=', q_lines.qualification_hr_id.id), ('seta_branch_id', '=', '11')])
    #                         if qual_master_obj:
    #                             accreditation_qualification_line = []
    #                             for lines in q_lines.qualification_line_hr:
    #                                 for data in lines:
    #                                     val = {
    #                                         'name': data.name,
    #                                         'type': data.type,
    #                                         'id_no': data.id_no,
    #                                         'title': data.title,
    #                                         'level1': data.level1,
    #                                         'level2': data.level2,
    #                                         'level3': data.level3,
    #                                         'selection': data.selection,
    #                                     }
    #                                     accreditation_qualification_line.append((0, 0, val))
    #                             q_vals = {
    #                                 'qual_unit_type': q_lines.qual_unit_type,
    #                                 'qualification_id': qual_master_obj.id,
    #                                 'saqa_qual_id': qual_master_obj.saqa_qual_id,
    #                                 'minimum_credits': qual_master_obj.m_credits,
    #                                 'qualification_line': accreditation_qualification_line,
    #                             }
    #                             q_vals_line.append((0, 0, q_vals))
    #             vals = {
    #                 'name': assessor_data.name,
    #                 'seq_no': assessor_data.assessor_seq_no,
    #                 'type': assessor_data.type,
    #                 'work_email': assessor_data.work_email,
    #                 'work_phone': assessor_data.work_phone,
    #                 'work_address': assessor_data.work_address or False,
    #                 'work_address2': assessor_data.work_address2,
    #                 'work_address3': assessor_data.work_address3,
    #                 'work_location': assessor_data.work_location,
    #                 'person_suburb': assessor_data.person_suburb and assessor_data.person_suburb.id,
    #                 'work_city': assessor_data.work_city and assessor_data.work_city.id,
    #                 'work_province': assessor_data.work_province and assessor_data.work_province.id,
    #                 'work_zip': assessor_data.work_zip,
    #                 'work_country': assessor_data.work_country and assessor_data.work_country.id,
    #                 'department': assessor_data.department or False,
    #                 'job_title': assessor_data.job_title or False,
    #                 'manager': assessor_data.manager or False,
    #                 'notes': assessor_data.notes,
    #                 'person_title': assessor_data.person_title,
    #                 'person_name': assessor_data.person_name,
    #                 'dissability': assessor_data.dissability,
    #                 'person_last_name': assessor_data.person_last_name,
    #                 'cont_number_home': assessor_data.cont_number_home,
    #                 'cont_number_office': assessor_data.cont_number_office,
    #                 'person_cell_phone_number': assessor_data.person_cell_phone_number,
    #                 'citizen_resident_status_code': assessor_data.citizen_resident_status_code,
    #                 'country_id': assessor_data.country_id and assessor_data.country_id.id or False,
    #                 'identification_id': assessor_data.assessor_moderator_identification_id,
    #                 'person_birth_date': assessor_data.person_birth_date,
    #                 'passport_id': assessor_data.passport_id,
    #                 'national_id': assessor_data.national_id,
    #                 'home_language_code': assessor_data.home_language_code and assessor_data.home_language_code.id,
    #                 'gender': assessor_data.gender,
    #                 'marital': assessor_data.marital,
    #                 'id_document': assessor_data.id_document,
    #                 'rpl_certificate': assessor_data.rpl_certificate,
    #                 'professionalbodydoc': assessor_data.professionalbodydoc,
    #                 'sram_doc': assessor_data.sram_doc,
    #                 'cv_document': assessor_data.cv_document,
    #                 'person_home_address_1': assessor_data.person_home_address_1,
    #                 'person_home_address_2': assessor_data.person_home_address_2,
    #                 'person_home_address_3': assessor_data.person_home_address_3,
    #                 'person_home_province_code': assessor_data.person_home_province_code and assessor_data.person_home_province_code.id,
    #                 'person_home_city': assessor_data.person_home_city and assessor_data.person_home_city.id,
    #                 'person_home_suburb': assessor_data.person_home_suburb and assessor_data.person_home_suburb.id,
    #                 'person_home_zip': assessor_data.person_home_zip,
    #                 'country_home': assessor_data.country_home and assessor_data.country_home.id,
    #                 'person_postal_address_1': assessor_data.person_postal_address_1,
    #                 'person_postal_address_2': assessor_data.person_postal_address_2,
    #                 'person_postal_address_3': assessor_data.person_postal_address_3,
    #                 'person_postal_suburb': assessor_data.person_postal_suburb and assessor_data.person_postal_suburb.id,
    #                 'person_postal_city': assessor_data.person_postal_city and assessor_data.person_postal_city.id,
    #                 'person_postal_province_code': assessor_data.person_postal_province_code and assessor_data.person_postal_province_code.id,
    #                 'person_postal_zip': assessor_data.person_postal_zip,
    #                 'country_postal': assessor_data.country_postal and assessor_data.country_postal.id,
    #                 'dissability': assessor_data.dissability,
    #                 #                  'is_assessors':assessor_data.is_assessors,
    #                 'is_moderators': True,
    #                 'seta_elements': True,
    #                 'same_as_home': assessor_data.same_as_home,
    #                 'qualification_ids': q_vals_line,
    #
    #                 'unknown_type': assessor_data.unknown_type,
    #                 'unknown_type_document': assessor_data.unknown_type_document and assessor_data.unknown_type_document.id
    #             }
    #
    #         res.update({'value': vals, })
    #     else:
    #         return {'value': {'assessor_id': ''}, \
    #                 'warning': {'title': 'Invalid Asssessor ID', 'message': 'Assessor does not exits in the system!'}}
    #     return res

    # @api.multi
    # def onchange_sameas_home(self, same_as_home):
    #     res = {}
    #     if not same_as_home:
    #         return res
    #     result = {
    #         'person_postal_address_1': self.person_home_address_1,
    #         'person_postal_address_2': self.person_home_address_2,
    #         'person_postal_address_3': self.person_home_address_3,
    #         'person_postal_suburb': self.person_home_suburb,
    #         'person_postal_city': self.person_home_city,
    #         'person_postal_province_code': self.person_home_province_code and self.person_home_province_code.id,
    #         'person_postal_zip': self.person_home_zip,
    #         'country_postal': self.country_home and self.country_home.id
    #     }
    #     res.update({'value': result})
    #     return res
    #
    # @api.multi
    # def open_map(self, street, city, state, country, zip):
    #     url = "http://maps.google.com/maps?oi=map&q="
    #     if street:
    #         url += street.replace(' ', '+')
    #     if city:
    #         url += '+' + city.replace(' ', '+')
    #     if state:
    #         url += '+' + state.name.replace(' ', '+')
    #     if country:
    #         url += '+' + country.name.replace(' ', '+')
    #     if zip:
    #         url += '+' + zip.replace(' ', '+')
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': url,
    #         'target': 'new'
    #     }
    #
    def work_addr_map(self):
        return self.open_map(
            self.work_address,
            self.work_city,
            self.work_province,
            self.work_country,
            self.work_zip
        )

    def home_addr_map(self):
        return self.open_map(
            self.person_home_address_1,
            self.person_home_city,
            self.person_home_province_code,
            self.country_home,
            self.person_home_zip
        )

    def postal_addr_map(self):
        return self.open_map(
            self.person_postal_address_1,
            self.person_postal_city,
            self.person_postal_province_code,
            self.country_postal,
            self.person_postal_zip
        )

    def action_verify_button(self):
        self.ensure_one()
        # Add context for logic downstream if necessary
        self = self.with_context(verify=True)

        # 1. Validation Logic: Using UserError instead of Warning
        if self.rpl_certificate and not self.rpl_certificate_bool:
            raise UserError(_("Please check RPL Practitioner Certificate before Evaluate!"))

        if self.sram_doc and not self.sram_doc_bool:
            raise UserError(_("Please check Statement before Evaluate"))

        if self.cv_document and not self.cv_document_bool:
            raise UserError(_("Please check CV Document before Evaluate"))

        # 2. Audit Log (One2many update)
        # self.env.user.name is the standard way to get current user name
        log_entry = {
            'rpl_name': self.env.user.name,
            'rpl_date': fields.Datetime.now(),
            'rpl_status': 'Evaluated',
            'rpl_update_date': self.write_date or fields.Datetime.now(),
            'rpl_comment': self.comment_line or '',
        }

        # 3. Perform updates in a single write call for performance
        self.write({
            'state': 'evaluation',
            'verify': True,
            'ass_mod_state': 'submit',
            'final_state': 'Evaluated',
            'comment_line': '',
            'rpl_status_ids': [fields.Command.create(log_entry)]
        })

        # 4. Email Template Logic
        # Odoo 18 uses self.env.ref and the .send_mail() method on the template record
        template = self.env.ref('hwseta_etqe.email_template_rpl_verified', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        return True

    def action_submit_button(self):
        self = self.with_context(submit=True)

        if not self.work_address or not self.work_address2 or not self.work_province or not self.work_country:
            raise UserError(_("Please fill work address in Public Information!!"))

        if not self.citizen_resident_status_code:
            raise UserError(_("Please select citizen status in Personal Information!!"))

        if self.identification_id and len(self.identification_id) > 13:
            raise UserError(_("You can enter maximum 13 digits Identification No. only!!"))

        if not self.person_cell_phone_number:
            raise UserError(_("Please enter mobile number in General Information"))

        if not self.id_document:
            pass  # kept same behavior as original code

        # Send submission email
        template = self.env.ref(
            'hwseta_etqe.email_template_rpl_submit',
            raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=True)

        self.write({'comment_line': ''})
        return self.write({
            'state': 'verification',
            'submitted': True,
            'final_state': 'Submitted'
        })

    # For Mail Server notification
    #         user_pool = self.env['res.users']
    #         group_pool = self.env['res.groups']
    #         email_to_string=""
    #
    #         group_obj = group_pool.search([('name', '=', 'ETQE Manager')])
    #         for group_data in group_obj:
    #             print "group_id====",group_data.id
    #             user_obj = user_pool.search([('groups_id', '=', group_data.id)])
    #             for user_data in user_obj:
    #                 print "user email===",user_data.partner_id.email
    #                 if email_to_string:
    #                     email_to_string=email_to_string + ',' + user_data.partner_id.email
    #                 else:
    #                     email_to_string=user_data.partner_id.email
    #
    #         print "email_to_string===",email_to_string
    #         email_template_obj = self.env['email.template']
    #         ir_model_data_obj = self.env['ir.model.data']
    #         mail_template_id = ir_model_data_obj.get_object_reference('hwseta_etqe', 'email_template_edi_etq11')
    #         print "mail_template_id====",mail_template_id
    #         if mail_template_id:
    #             temp_obj = email_template_obj.browse(mail_template_id[1])
    #             current_user_obj = user_pool.browse(self._uid)
    #             print "login user =",current_user_obj.partner_id.email
    #             if email_to_string:
    #                 if temp_obj.write({'email_to' : email_to_string, 'email_from' : current_user_obj.partner_id.email}):
    #                     print "done="
    #                     self.pool['email.template'].send_mail(self.env.cr, self.env.uid, mail_template_id[1], self.id, force_send=True,context=self.env.context)
    #         return True


    def action_evaluate_button(self):
        # 1. Validation: Use UserError instead of Warning
        if not self.comment_line:
            raise UserError(_("Please enter status comment"))

        # 2. Context handling (Modern style)
        this = self.with_context(evaluate=True)

        # 3. Email Template (Modern API)
        # Using env.ref is safer and cleaner than get_object_reference
        template = self.env.ref('hwseta_etqe.email_template_rpl_evaluated', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        # 4. Prepare the log entry for the status history
        # (0, 0, {values}) is still valid, but we use self.env.user for the name
        status_log = {
            'rpl_name': self.env.user.name,
            'rpl_date': fields.Datetime.now(),
            'rpl_status': 'Recommended',
            'rpl_update_date': self.write_date,
            'rpl_comment': self.comment_line,
        }

        # 5. Final Write (Combined for performance)
        # In Odoo 18, it's best practice to update all fields in one database hit
        self.write({
            'rpl_status_ids': [(0, 0, status_log)],
            'state': 'evaluation',
            'evaluate': True,
            'final_state': 'Recommended',
            'comment_line': ''  # Clear the comment after logging it
        })

        return True

    def action_denied_button(self):
        # 1. Validation
        if not self.comment_line:
            raise UserError(_("Please enter status comment"))

        # 2. Context & Email (Odoo 18 uses mail.template)
        template = self.env.ref('hwseta_etqe.email_template_rpl_rejected', raise_if_not_found=False)
        if template:
            # Simplified send_mail - no need for cr, uid, or manual context
            template.send_mail(self.id, force_send=True)

        # 3. Combined Write using the modern Command namespace
        return self.write({
            'rpl_status_ids': [Command.create({
                'rpl_name': self.env.user.name,
                'rpl_date': fields.Datetime.now(),
                'rpl_status': 'Rejected',
                'rpl_update_date': self.write_date,
                'rpl_comment': self.comment_line,
            })],
            'state': 'denied',
            'denied': True,
            'final_state': 'Rejected',
            'comment_line': ''
        })


    @api.model_create_multi
    def create(self, vals_list):
        # Odoo 18 uses @api.model_create_multi for performance. 
        # vals_list is a list of dictionaries.
        for vals in vals_list:
            vals['final_state'] = 'Draft'
            
            # Use next_by_code instead of get
            if not vals.get('rpl_ref') or vals.get('rpl_ref') == '/':
                vals['rpl_ref'] = self.env['ir.sequence'].next_by_code('rpl.register') or '/'

        # Call super with the list
        records = super(RplRegister, self).create(vals_list)

        # Logic after creation (if you decide to uncomment it)
        for record in records:
            if not self._context.get('from_website3'):
                if record.work_email and '@' not in record.work_email:
                    raise UserError(_('Please enter a valid email address'))
                if not record.person_cell_phone_number:
                    raise UserError(_('Please enter a mobile number'))
            
            # EXAMPLE: How to handle that commented-out notification logic modernly
            # template = self.env.ref('hwseta_etqe.email_template_edi_etq11', raise_if_not_found=False)
            # if template:
            #     # Instead of manual email_to strings, Odoo 18 handles this 
            #     # better via Subtypes or Followers, but if you must:
            #     template.send_mail(record.id, force_send=True)

        return records

    def action_approve_button(self):
        # 1. Validation & Context
        if not self.comment_line:
            raise UserError(_("Please enter status comment"))
        
        this = self.with_context(submit=True, from_registration_process=True)
        
        # 2. Sequence Generation
        rpl_seq_no = self.env['ir.sequence'].next_by_code('rpl.master') or '/'

        # 3. Create the Master Record
        # We map the fields directly. Odoo 18 handles recordset-to-id conversion automatically.
        master_data = {
            'user_id': False,
            'name': self.name,
            'rpl_seq_no': rpl_seq_no,
            'work_email': self.work_email,
            'work_phone': self.work_phone,
            'work_address': self.work_address,
            'work_address2': self.work_address2,
            'work_address3': self.work_address3,
            'work_location': self.work_location,
            'person_suburb': self.person_suburb.id,
            'work_city': self.work_city.id,
            'work_province': self.work_province.id,
            'work_zip': self.work_zip,
            'work_country': self.work_country.id,
            'person_title': self.person_title,
            'person_name': self.person_name,
            'disability': self.disability,
            'person_last_name': self.person_last_name,
            'cont_number_home': self.cont_number_home,
            'cont_number_office': self.cont_number_office,
            'person_cell_phone_number': self.person_cell_phone_number,
            'citizen_resident_status_code': self.citizen_resident_status_code,
            'id_document': self.id_document.id,
            'country_id': self.country_id.id,
            'assessor_moderator_identification_id': self.identification_id,
            'person_birth_date': self.person_birth_date,
            'passport_id': self.passport_id,
            'national_id': self.national_id,
            'home_language_code': self.home_language_code.id,
            'gender': self.gender,
            'marital': self.marital,
            'person_home_address_1': self.person_home_address_1,
            'person_home_address_2': self.person_home_address_2,
            'person_home_address_3': self.person_home_address_3,
            'person_home_province_code': self.person_home_province_code.id,
            'person_home_city': self.person_home_city.id,
            'person_home_suburb': self.person_home_suburb.id,
            'person_home_zip': self.person_home_zip,
            'country_home': self.country_home.id,
            'person_postal_address_1': self.person_postal_address_1,
            'person_postal_address_2': self.person_postal_address_2,
            'person_postal_address_3': self.person_postal_address_3,
            'person_postal_suburb': self.person_postal_suburb.id,
            'person_postal_city': self.person_postal_city.id,
            'person_postal_province_code': self.person_postal_province_code.id,
            'person_postal_zip': self.person_postal_zip,
            'country_postal': self.country_postal.id,
            'is_rpl': self.is_rpl,
            'seta_elements': True,
            'same_as_home': self.same_as_home,
            'unknown_type': self.unknown_type,
            'cv_document': self.cv_document.id,
            'unknown_type_document': self.unknown_type_document.id,
            'rpl_certificate': self.rpl_certificate.id,
            'sram_doc': self.sram_doc.id,
            'password': self.password,
            'current_occupation': self.current_occupation,
            'highest_education': self.highest_education,
            'years_in_occupation': self.years_in_occupation,
            'socio_economic_status': self.socio_economic_status,
            'equity': self.equity,
            'reg_start': fields.Date.today(),
            'update_disclaimer': True,
            'identification_id': self.identification_id,
            'person_fax_number': self.person_fax_number,
            'person_initials': self.person_initials,
        }

        if self.is_rpl:
            employee_record = self.env['rpl.master'].create(master_data)

            # 4. History Logging and Registration Update
            status_log = {
                'rpl_name': self.env.user.name,
                'rpl_date': fields.Datetime.now(),
                'rpl_status': 'Approved',
                'rpl_update_date': fields.Datetime.now(),
                'rpl_comment': self.comment_line,
            }

            self.write({
                'rpl_seq_no': rpl_seq_no,
                'state': 'approved',
                'approved': True,
                'rpl_approval_date': fields.Date.today(),
                'final_state': 'Approved',
                'comment_line': '',
                'rpl_status_ids': [Command.create(status_log)]
            })

            # 5. Send Email
            template = self.env.ref('hwseta_etqe.email_template_rpl_approved', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)

        return True

    def write(self, vals):
        # 1. Data Integrity: Identification ID check
        # Better handled via @api.constrains, but if keeping in write:
        if 'identification_id' in vals and vals['identification_id']:
            if len(vals['identification_id']) < 13:
                raise ValidationError(_("Please enter 13 digits Identification No.!!"))

        # 2. State Transition Validation
        # In Odoo 18, 'self' can be multiple records. We loop to ensure 
        # the logic applies to every record being updated.
        if 'state' in vals:
            new_state = vals['state']
            for rec in self:
                if new_state == "verification" and not rec.submitted:
                    raise UserError(_('Sorry! You cannot change status to verification without submitting the application.'))

                if new_state == "evaluation" and not rec.verify:
                    raise UserError(_('Sorry! You cannot change status to evaluation without verifying the application.'))

                if new_state == "approved":
                    if not rec.evaluate:
                        raise UserError(_('Sorry! You cannot change status to Approved without evaluating the application.'))
                    if rec.denied:
                        raise UserError(_('Sorry! You cannot change status to Approved as it is already Rejected.'))
                    if not vals.get('approved') and not rec.approved:
                        raise UserError(_('Sorry! You cannot change status to Approved without using the Approve button.'))

                if new_state == "denied":
                    if rec.approved:
                        raise UserError(_('Sorry! You cannot change status to Rejected as it is already Approved.'))
                    if not vals.get('denied') and not rec.denied:
                        raise UserError(_('Sorry! You cannot change status to Rejected without using the Reject button.'))

        # 3. Execute the write
        return super(RplRegister, self).write(vals)

    def copy(self, default=None):
        ''' Inherited to avoid duplicating records '''
        raise UserError(_('Sorry! You cannot create duplicate records for this model.'))
        return super(RplRegister, self).copy(default=default)

    def unlink(self):
        ''' Inherited to restrict deleting records '''
        # Standard Odoo 18 exception for blocking actions
        raise UserError(_('Sorry! You cannot delete records in this system. Please archive them instead.'))
        return super(RplRegister, self).unlink()

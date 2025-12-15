from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
# import wdb
import datetime
DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


"""
this is the person file aka res.partner aka 29(nlrd) aka 400(setmis)
"""


class SetaPerson(models.Model):
    _name = "seta.person"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "person_first_name"
    _description = "Person Profile"

    active = fields.Boolean(default=True)
    user_id = fields.Many2one("res.users")
    is_person = fields.Boolean(default=True)

    city = fields.Many2one("res.city")
    suburb = fields.Many2one("res.suburb")
    country = fields.Many2one("res.country")
    age = fields.Char(size=3)
    district_id = fields.Many2one('res.district')
    municipality_id = fields.Many2one('res.municipality')
    provincial_office_m2o = fields.Many2one("res.country.state",)
    is_sdf = fields.Boolean()
    PERSON_TITLES = [
        ("Mr", "Mr"),
        ("Mrs", "Mrs"),
        ("Ms", "Ms"),
        ("Miss", "Miss"),
        ("Dr", "Dr"),
        ("Prof", "Prof"),
    ]

    image = fields.Many2one('ir.attachment')
    django_id = fields.Integer()
    is_learner = fields.Boolean()
    is_moderator = fields.Boolean()
    is_assessor = fields.Boolean()
    is_provider = fields.Boolean()
    partner_id = fields.Many2one("res.partner")
    # seta_id = fields.Many2one("seta.branches")
    # provider_seta_id = fields.Many2one("seta.branches")
    # employer_contact_email_address = fields.Char(related='employer_m2o.employer_contact_email_address')
    fax = fields.Char()
    national_id = fields.Char(size=13)
    previous_national_id = fields.Char(size=13)
    sic_code = fields.Many2one("sic.code")
    person_alternate_id = fields.Char(size=20)
    alternate_id_type_id_m2o = fields.Many2one(
        "alternate.id.type.id"
    )  # , default='533'
    alternate_id_type_id_id = fields.Char()
    equity_code_m2o = fields.Many2one("equity.code")
    economic_status_id_m2o = fields.Many2one("economic.status.id")
    # equity_code_id = fields.Char()
    nationality_code_m2o = fields.Many2one("nationality.code")
    nationality_code_id = fields.Char()
    home_language_code_m2o = fields.Many2one(
        "res.lang"
    )  # Many2one('home.language.code')
    home_language_code_id = fields.Char()
    gender_code_m2o = fields.Many2one("gender.code")
    gender_code_id = fields.Char()
    citizen_resident_status_code_m2o = fields.Many2one("citizen.resident.status.code")
    citizen_resident_status_code_id = fields.Char()
    person_last_name = fields.Char(size=45, string="Last Name")
    person_first_name = fields.Char(size=26, string="First Name")
    name = fields.Char(size=60)
    person_middle_name = fields.Char(size=50, string="Middle Name")
    same_as_home = fields.Boolean()
    # person_title = fields.Selection(selection=PERSON_TITLES)  # size=10,
    # qual_ids = fields.One2many(
    #     "seta.qualifications",
    #     "learner_id",
    #     string="Qualifications Learners Masters Link",
    # )
    # learnership_ids = fields.One2many(
    #     "seta.learnership",
    #     "person_m2o",
    #     string="Qualifications Learners Masters Link",
    # )
    # unit_standard_ids = fields.One2many(
    #     "seta.unit.standard", "person_m2o", string="Unit Standard Learners Masters Link"
    # )
    # learner_ids = fields.One2many('hwseta.project.learner', 'task_id', string='Learners')

    person_title = fields.Selection(selection=PERSON_TITLES)
    person_birth_date = fields.Date(size=8)
    person_home_address_1 = fields.Char(size=50)
    person_home_address_2 = fields.Char(size=50)
    person_home_address_3 = fields.Char(size=50)
    person_address_code = fields.Char(size=4)
    person_postal_address_1 = fields.Char(size=50)
    person_postal_address_2 = fields.Char(size=50)
    person_postal_address_3 = fields.Char(size=50)
    address_rural_urban = fields.Selection([('rural', 'Rural'), ('urban', 'Urban')])
    is_disabled = fields.Boolean(string="Disabled")
    person_postal_address_code = fields.Char(size=4)
    person_phone_number = fields.Char(size=10)
    person_cell_phone_number = fields.Char(size=10, string="Mobile No")
    person_fax_number = fields.Char(size=10)
    person_email_address = fields.Char(size=50)
    province_code_m2o = fields.Many2one("res.country.state", domain="[('country_id', '=', 247)]")
    postal_province_code_m2o = fields.Many2one("res.country.state", domain="[('country_id', '=', 247)]")
    # id_document_upload = fields.Many2one('ir.attachment', string='Upload ID document')
    id_document_upload = fields.Many2one('ir.attachment',string='ID Document')
    # id_document_upload_name = fields.Char(string='ID Document')
    # person_age = fields.Char(string='Age')
    person_youth = fields.Boolean()
    # person_youth = fields.Selection([('no', 'No'), ('yes', 'Yes')])
    province_code_id = fields.Char()
    # provider_code_m2o = fields.Many2one("seta.provider")
    provider_code_id = fields.Char()
    # employer_m2o = fields.Many2one("seta.employer")
    employer_id = fields.Char()
    provider_etqe_m2o = fields.Many2one("etqe.id")
    person_previous_last_name = fields.Char(size=45)
    person_previous_alternate_id = fields.Char(size=20)
    # person_previous_alternate_id_type_id = fields.Char(size=3)
    person_previous_alternate_id_type_id = fields.Many2one(
        "alternate.id.type.id"
    )  # , default='533'
    person_previous_provider_code = fields.Char(size=20)
    person_previous_provider_etqe_id = fields.Char(size=10)
    seeing_rating_id_m2o = fields.Many2one("seeing.rating.id")
    seeing_rating_id_id = fields.Char()
    hearing_rating_id_m2o = fields.Many2one("hearing.rating.id")
    hearing_rating_id_id = fields.Char()
    walking_rating_id_m2o = fields.Many2one("walking.rating.id")
    walking_rating_id_id = fields.Char()
    remembering_rating_id_m2o = fields.Many2one("remembering.rating.id")
    remembering_rating_id_id = fields.Char()
    communicating_rating_id_m2o = fields.Many2one("communicating.rating.id")
    communicating_rating_id_id = fields.Char()
    self_care_rating_id_m2o = fields.Many2one("self.care.rating.id")
    self_care_rating_id_id = fields.Char()
    last_school_emis_number = fields.Char(size=10)
    # last_school_year = fields.Date()
    last_school_year = fields.Many2one("last.school.year")
    statssa_area_code_m2o = fields.Many2one("statssa.area.code")
    statssa_area_code_id = fields.Char()
    popi_act_status_id_m2o = fields.Many2one("popi.act.status.id")
    popi_act_status_id_m2o_name = fields.Char(
        string="POPI Act Status", related="popi_act_status_id_m2o.name"
    )
    popi_act_status_id_id = fields.Char()
    popi_act_status_date = fields.Date()
    date_stamp = fields.Date(default=datetime.datetime.now().date())
    status_selections = [
        ("achieved", "Achieved"),
        ("certificated", "Certificated"),
        ("completed", "Completed - To Be Assessed"),
        ("discontinued", "Discontinued"),
        ("enrolled", "Enrolled"),
        ("non_endorsed_achieved", "Non-Endorsed Achievement"),
        ("waiting_for_wil", "Waiting for WIL"),
        ("wil_in_progress", "WIL In Progress"),
    ]
    citizen_resident_status_code_m2o_name = fields.Char(
        related="citizen_resident_status_code_m2o.name"
    )
    person_id = fields.Many2one("seta.person", string="person")

    postal_city = fields.Many2one("res.city")
    postal_suburb = fields.Many2one("res.suburb")
    postal_country = fields.Many2one("res.country")
    national_nd_alternate_id = fields.Char(string='Identification Number')
    #state = fields.Selection(status_selections, required=True, string="Learner Status")

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )


    def chatter(self, author, msg):
        self.message_post(
            body=_(msg), subtype_xmlid='mail.mt_comment', author_id=author.partner_id.id
        )

    @api.depends('name', 'person_first_name', 'person_last_name')
    def _compute_display_name(self):
        for rec in self:
            id_no = ''
            if rec.national_id:
                id_no = str(rec.national_id)
            else:
                id_no = str(rec.person_alternate_id)

            rec.display_name = f"{rec.person_first_name} {rec.person_last_name} ({id_no})"


    @api.model
    @api.depends('national_id')
    @api.onchange('national_id')
    def _compute_age(self):
        for record in self:
            if record.national_id:
                birthdate = record.national_id[:6]
                today = datetime.date.today()
                # b_date = fields.Datetime.from_string(birthdate)
                current_date = str(today).replace('-', '')[2:]
                dbg(current_date)
                # dbg(current_date-birthdate)
                if record.national_id[:2] > str(today).replace('-', '')[2:4]:
                    dt_str = '19' + birthdate
                else:
                    dt_str = '20' + birthdate
                dbg(dt_str)
                dbg(today)
                date_format = '%Y%m%d'
                date_obj = datetime.datetime.strptime(dt_str, date_format)
                dbg('b_date' + str(date_obj.date()))
                age_days = today - (date_obj.date())
                dbg((age_days))
                youth_days_min = datetime.timedelta(days=6570)
                youth_days_max = datetime.timedelta(days=12775)
                if age_days < youth_days_min:
                    state = False
                elif age_days >= youth_days_min and age_days < youth_days_max:
                    state = True
                else:
                    state = False

                record.person_youth = state

    def send_user_mail_create_person(self):
        template = self.env.ref("seta_person.create_person_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_update_person(self):
        template = self.env.ref("seta_person.update_person_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_deactivate_person(self):
        template = self.env.ref("seta_person.deactivate_person_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_reactivate_person(self):
        template = self.env.ref("seta_person.reactivate_person_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_disable_approver_person(self):
        template = self.env.ref("seta_person.person_disable_approver_template")
        template.send_mail(self.id, force_send=True)

    @api.model
    def get_email_to(self):
        # wdb.set_trace()
        user_group = self.env.ref("seta_person.group_person_disable_approve")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        return ",".join(email_list)

    def open_person_wiz(self):
        act = {
            "name": _("Person Details"),
            "res_model": "person.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "seta_person.person_wizard_form_view"
            ).id,
            "context": {
                "active_model": "seta.person",
                "active_id": self.id,
                # "default_user_id": ,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
        dbg(act["context"])
        return act


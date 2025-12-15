from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import datetime
from ... import toolz
DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class SetaPersonTransaction(models.Model):
    _name = "seta.person.transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "person_first_name"

    # helper stuff
    ref = fields.Char(string='Reference Number')
    display_name = fields.Char(compute='_compute_display_name')

    def _compute_display_name(self):
        for this in self:
            if this.national_id:
                dn = f"[{this.national_id}] {this.person_first_name} {this.person_last_name}"
            elif this.person_alternate_id:
                dn = f"[{this.person_alternate_id}] {this.person_first_name} {this.person_last_name}"
            else:
                dn = f"[] {this.person_first_name} {this.person_last_name}"
            this.display_name = dn
    # end of helper stuff

    city = fields.Many2one("res.city")
    suburb = fields.Many2one("res.suburb")
    country = fields.Many2one("res.country")
    age = fields.Char(size=3)
    last_signature_date = fields.Date()
    district_id = fields.Many2one('res.district')
    municipality_id = fields.Many2one('res.municipality')
    provincial_office_m2o = fields.Many2one("res.country.state",)

    # sdf_id_m2o = fields.Many2one('sdf.master')
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
    national_id = fields.Char(size=15)
    previous_national_id = fields.Char(size=15)
    sic_code = fields.Many2one("sic.code")
    person_alternate_id = fields.Char(size=20)
    alternate_id_type_id_m2o = fields.Many2one(
        "alternate.id.type.id"
    )  # , default='533'
    alternate_id_type_id_id = fields.Char()
    equity_code_m2o = fields.Many2one("equity.code")
    economic_status_id_m2o = fields.Many2one("economic.status.id")
    equity_code_id = fields.Char()
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
    person_last_name = fields.Char(size=45)
    person_first_name = fields.Char(size=26)
    name = fields.Char(size=60)
    person_middle_name = fields.Char(size=50)
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

    person_title = fields.Char(size=10)
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
    person_phone_number = fields.Char(size=20)
    person_cell_phone_number = fields.Char(size=20)
    person_fax_number = fields.Char(size=20)
    person_email_address = fields.Char(size=50)
    province_code_m2o = fields.Many2one("res.country.state", domain="[('country_id', '=', 247)]")
    postal_province_code_m2o = fields.Many2one("res.country.state", domain="[('country_id', '=', 247)]")
    # id_document_upload = fields.Many2one('ir.attachment', string='Upload ID document')
    id_document_upload = fields.Many2one('ir.attachment',string='Upload ID document')
    # id_document_upload_name = fields.Char(string='Upload ID document')
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
    #state = fields.Selection(status_selections, required=True, string="Learner Status")
    status = fields.Selection([
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string="Status", default='submitted')

    user_id = fields.Many2one("res.users")
    postal_city = fields.Many2one("res.city")
    postal_suburb = fields.Many2one("res.suburb")
    postal_country = fields.Many2one("res.country")
    national_nd_alternate_id = fields.Char(string='Identification Number')

    def review_confirmed(self,message):
        self.action_approve(message=message)

    def review(self):
        user = self.env.user
        act = {
            "name": _("User Details"),
            "res_model": "seta.update.message",
            "view_mode": "form",
            "view_id": self.env.ref(
                "seta_base.seta_update_message_form_view"
            ).id,
            "context": {
                "active_model": self._name,
                "active_id": self.id,
                "method": "review_confirmed",
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
        dbg(act["context"])
        return act

    def action_approve(self, message=None):
        vals = self.read()[0]
        vals = toolz.tuple_fixer(vals)
        del vals['message_ids']
        del vals['message_follower_ids']
        del vals['activity_ids']
        del vals['message_partner_ids']
        del vals['status']
        del vals['ref']
        # message_ids
        dbg(vals)
        vals.update({'active':True})
        rec = self.env['seta.person'].create(vals)
        toolz.link_attachments_to_record(rec)
        msg = f'approved the creation of this record.'
        if message:
            msg += f"with the following comments: {message}"
        rec.message_post(body=_(msg), subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id)
        self.status = 'approved'
        return rec

    #
    # @api.constrains(
    #     "national_id",
    #     "person_postal_address_1",
    #     "person_postal_address_2",
    #     "person_postal_address_3",
    #     "person_postal_address_code",
    #     "person_home_address_1",
    #     "person_home_address_2",
    #     "person_home_address_3",
    #     "person_address_code",
    #     "person_cell_phone_number",
    #     "person_phone_number",
    #     "person_alternate_id",
    #     "person_fax_number",
    #     "person_email_address",
    #     "person_last_name",
    #     "person_first_name",
    #     "person_middle_name",
    #     "person_birth_date",
    #     "person_previous_last_name",
    #     "person_previous_alternate_id",
    #     "person_previous_provider_code",
    #     "popi_act_status_date",
    #     "person_previous_alternate_id_type_id",
    #     "person_previous_provider_etqe_id",
    #     "last_school_emis_number",
    #     "last_school_year",
    # )
    # def constrain_person_validations(self):
    #     dbg("def constrain_person_validations(self):")
    #     any_broken = False
    #     final_msg = ""
    #     if self.national_id:
    #         broken, msg = vd.check_national_id(self.national_id)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_postal_address_1:
    #         broken, msg = vd.check_person_postal_address_1(self.person_postal_address_1)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_postal_address_2:
    #         broken, msg = vd.check_person_postal_address_2(self.person_postal_address_2)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_postal_address_3:
    #         broken, msg = vd.check_person_postal_address_3(self.person_postal_address_3)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_postal_address_code:
    #         broken, msg = vd.check_person_postal_address_code(
    #             self.person_postal_address_code
    #         )
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_home_address_1:
    #         broken, msg = vd.check_person_home_address_1(self.person_home_address_1)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_home_address_2:
    #         broken, msg = vd.check_person_home_address_2(self.person_home_address_2)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_home_address_3:
    #         broken, msg = vd.check_person_home_address_3(self.person_home_address_3)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_address_code:
    #         broken, msg = vd.check_person_address_code(self.person_address_code)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_cell_phone_number:
    #         broken, msg = vd.check_person_cell_phone_number(
    #             self.person_cell_phone_number
    #         )
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_phone_number:
    #         broken, msg = vd.check_person_phone_number(self.person_phone_number)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_alternate_id:
    #         broken, msg = vd.check_person_alternate_id(self.person_alternate_id)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_fax_number:
    #         broken, msg = vd.check_person_fax_number(self.person_fax_number)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_email_address:
    #         broken, msg = vd.check_person_email_address(self.person_email_address)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_last_name:
    #         broken, msg = vd.check_person_last_name(self.person_last_name)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_first_name:
    #         broken, msg = vd.check_person_first_name(self.person_first_name)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_middle_name:
    #         broken, msg = vd.check_person_middle_name(self.person_middle_name)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     # if self.person_birth_date:
    #     #     broken, msg = vd.check_person_birth_date(self.person_birth_date)
    #     #     if broken:
    #     #         any_broken = True
    #     #         final_msg += msg + "\n"
    #     if self.person_previous_last_name:
    #         broken, msg = vd.check_person_previous_last_name(
    #             self.person_previous_last_name
    #         )
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_previous_alternate_id:
    #         broken, msg = vd.check_person_previous_alternate_id(
    #             self.person_previous_alternate_id
    #         )
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.person_previous_provider_code:
    #         broken, msg = vd.check_person_previous_provider_code(
    #             self.person_previous_provider_code
    #         )
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     # if self.popi_act_status_date:
    #     #     broken, msg = vd.check_popi_act_status_date(self.popi_act_status_date)
    #     #     if broken:
    #     #         any_broken = True
    #     #         final_msg += msg + "\n"
    #     # if self.person_previous_alternate_id_type_id:
    #     #     broken, msg = vd.check_person_previous_alternate_id_type_id(
    #     #         self.person_previous_alternate_id_type_id
    #     #     )
    #     #     if broken:
    #     #         any_broken = True
    #     #         final_msg += msg + "\n"
    #     if self.person_previous_provider_etqe_id:
    #         broken, msg = vd.check_person_previous_provider_etqe_id(
    #             self.person_previous_provider_etqe_id
    #         )
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     if self.last_school_emis_number:
    #         broken, msg = vd.check_last_school_emis_number(self.last_school_emis_number)
    #         if broken:
    #             any_broken = True
    #             final_msg += msg + "\n"
    #     # if self.last_school_year:
    #     #     broken, msg = vd.check_last_school_year(self.last_school_year)
    #     #     if broken:
    #     #         any_broken = True
    #     #         final_msg += msg + "\n"
    #     if any_broken:
    #         dbg("any_broken")
    #         raise ValidationError(_(final_msg))
    #
    #
    # # national_id
    # @api.onchange("national_id")
    # def onchange_national_id_validations(self):
    #     dbg("def onchange_national_id_validations(self):")
    #     if self.national_id:
    #         broken, msg = vd.check_national_id(self.national_id)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_postal_address_1
    # @api.onchange("person_postal_address_1")
    # def onchange_person_postal_address_1_validations(self):
    #     dbg("def onchange_person_postal_address_1_validations(self):")
    #     if self.person_postal_address_1:
    #         broken, msg = vd.check_person_postal_address_1(self.person_postal_address_1)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_postal_address_2
    # @api.onchange("person_postal_address_2")
    # def onchange_person_postal_address_2_validations(self):
    #     dbg("def onchange_person_postal_address_2_validations(self):")
    #     if self.person_postal_address_2:
    #         broken, msg = vd.check_person_postal_address_2(self.person_postal_address_2)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_postal_address_3
    # @api.onchange("person_postal_address_3")
    # def onchange_person_postal_address_3_validations(self):
    #     dbg("def onchange_person_postal_address_3_validations(self):")
    #     if self.person_postal_address_3:
    #         broken, msg = vd.check_person_postal_address_3(self.person_postal_address_3)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_postal_address_code
    # @api.onchange("person_postal_address_code")
    # def onchange_person_postal_address_code_validations(self):
    #     dbg("def onchange_person_postal_address_code_validations(self):")
    #     if self.person_postal_address_code:
    #         broken, msg = vd.check_person_postal_address_code(
    #             self.person_postal_address_code
    #         )
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_home_address_1
    # @api.onchange("person_home_address_1")
    # def onchange_person_home_address_1_validations(self):
    #     dbg("def onchange_person_home_address_1_validations(self):")
    #     if self.person_home_address_1:
    #         broken, msg = vd.check_person_home_address_1(self.person_home_address_1)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_home_address_2
    # @api.onchange("person_home_address_2")
    # def onchange_person_home_address_2_validations(self):
    #     dbg("def onchange_person_home_address_2_validations(self):")
    #     if self.person_home_address_2:
    #         broken, msg = vd.check_person_home_address_2(self.person_home_address_2)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_home_address_3
    # @api.onchange("person_home_address_3")
    # def onchange_person_home_address_3_validations(self):
    #     dbg("def onchange_person_home_address_3_validations(self):")
    #     if self.person_home_address_3:
    #         broken, msg = vd.check_person_home_address_3(self.person_home_address_3)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_address_code
    # @api.onchange("person_address_code")
    # def onchange_person_address_code_validations(self):
    #     dbg("def onchange_person_address_code_validations(self):")
    #     if self.person_address_code:
    #         broken, msg = vd.check_person_address_code(self.person_address_code)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_cell_phone_number
    # @api.onchange("person_cell_phone_number")
    # def onchange_person_cell_phone_number_validations(self):
    #     dbg("def onchange_person_cell_phone_number_validations(self):")
    #     if self.person_cell_phone_number:
    #         broken, msg = vd.check_person_cell_phone_number(
    #             self.person_cell_phone_number
    #         )
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_phone_number
    # @api.onchange("person_phone_number")
    # def onchange_person_phone_number_validations(self):
    #     dbg("def onchange_person_phone_number_validations(self):")
    #     if self.person_phone_number:
    #         broken, msg = vd.check_person_phone_number(self.person_phone_number)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_alternate_id
    # @api.onchange("person_alternate_id")
    # def onchange_person_alternate_id_validations(self):
    #     dbg("def onchange_person_alternate_id_validations(self):")
    #     if self.person_alternate_id:
    #         broken, msg = vd.check_person_alternate_id(self.person_alternate_id)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_fax_number
    # @api.onchange("person_fax_number")
    # def onchange_person_fax_number_validations(self):
    #     dbg("def onchange_person_fax_number_validations(self):")
    #     if self.person_fax_number:
    #         broken, msg = vd.check_person_fax_number(self.person_fax_number)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_email_address
    # @api.onchange("person_email_address")
    # def onchange_person_email_address_validations(self):
    #     dbg("def onchange_person_email_address_validations(self):")
    #     if self.person_email_address:
    #         broken, msg = vd.check_person_email_address(self.person_email_address)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_last_name
    # @api.onchange("person_last_name")
    # def onchange_person_last_name_validations(self):
    #     dbg("def onchange_person_last_name_validations(self):")
    #     if self.person_last_name:
    #         broken, msg = vd.check_person_last_name(self.person_last_name)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_first_name
    # @api.onchange("person_first_name")
    # def onchange_person_first_name_validations(self):
    #     dbg("def onchange_person_first_name_validations(self):")
    #     if self.person_first_name:
    #         broken, msg = vd.check_person_first_name(self.person_first_name)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_middle_name
    # @api.onchange("person_middle_name")
    # def onchange_person_middle_name_validations(self):
    #     dbg("def onchange_person_middle_name_validations(self):")
    #     if self.person_middle_name:
    #         broken, msg = vd.check_person_middle_name(self.person_middle_name)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_birth_date
    # @api.onchange("person_birth_date")
    # def onchange_person_birth_date_validations(self):
    #     dbg("def onchange_person_birth_date_validations(self):")
    #     if self.person_birth_date:
    #         broken, msg = vd.check_person_birth_date(self.person_birth_date)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_previous_last_name
    # @api.onchange("person_previous_last_name")
    # def onchange_person_previous_last_name_validations(self):
    #     dbg("def onchange_person_previous_last_name_validations(self):")
    #     if self.person_previous_last_name:
    #         broken, msg = vd.check_person_previous_last_name(
    #             self.person_previous_last_name
    #         )
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_previous_alternate_id
    # @api.onchange("person_previous_alternate_id")
    # def onchange_person_previous_alternate_id_validations(self):
    #     dbg("def onchange_person_previous_alternate_id_validations(self):")
    #     if self.person_previous_alternate_id:
    #         broken, msg = vd.check_person_previous_alternate_id(
    #             self.person_previous_alternate_id
    #         )
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_previous_provider_code
    # @api.onchange("person_previous_provider_code")
    # def onchange_person_previous_provider_code_validations(self):
    #     dbg("def onchange_person_previous_provider_code_validations(self):")
    #     if self.person_previous_provider_code:
    #         broken, msg = vd.check_person_previous_provider_code(
    #             self.person_previous_provider_code
    #         )
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # popi_act_status_date
    # @api.onchange("popi_act_status_date")
    # def onchange_popi_act_status_date_validations(self):
    #     dbg("def onchange_popi_act_status_date_validations(self):")
    #     if self.popi_act_status_date:
    #         broken, msg = vd.check_popi_act_status_date(self.popi_act_status_date)
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_previous_alternate_id_type_id
    # @api.onchange("person_previous_alternate_id_type_id")
    # def onchange_person_previous_alternate_id_type_id_validations(self):
    #     dbg("def onchange_person_previous_alternate_id_type_id_validations(self):")
    #     if self.person_previous_alternate_id_type_id:
    #         broken, msg = vd.check_person_previous_alternate_id_type_id(
    #             self.person_previous_alternate_id_type_id
    #         )
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # person_previous_provider_etqe_id
    # @api.onchange("person_previous_provider_etqe_id")
    # def onchange_person_previous_provider_etqe_id_validations(self):
    #     dbg("def onchange_person_previous_provider_etqe_id_validations(self):")
    #     if self.person_previous_provider_etqe_id:
    #         broken, msg = vd.check_person_previous_provider_etqe_id(
    #             self.person_previous_provider_etqe_id
    #         )
    #         if broken:
    #             raise ValidationError(_(msg))
    #
    # # last_school_emis_number
    # @api.onchange("last_school_emis_number")
    # def onchange_last_school_emis_number_validations(self):
    #     dbg("def onchange_last_school_emis_number_validations(self):")
    #     if self.last_school_emis_number:
    #         broken, msg = vd.check_last_school_emis_number(self.last_school_emis_number)
    #         if broken:
    #             raise ValidationError(_(msg))

    # last_school_year
    # @api.onchange("last_school_year")
    # def onchange_last_school_year_validations(self):
    #     dbg("def onchange_last_school_year_validations(self):")
    #     if self.last_school_year:
    #         broken, msg = vd.check_last_school_year(self.last_school_year)
    #         if broken:
    #             raise ValidationError(_(msg))

    # @api.onchange('national_id')
    # def onchange(self):
    #     flist = ['django_id', 'seta_id', 'provider_seta_id', 'fax', 'national_id', 'sic_code', 'person_alternate_id', 'alternate_id_type_id_m2o', 'alternate_id_type_id_id', 'equity_code_m2o', 'equity_code_id', 'nationality_code_m2o', 'nationality_code_id', 'home_language_code_m2o', 'home_language_code_id', 'gender_code_m2o', 'gender_code_id', 'citizen_resident_status_code_m2o', 'citizen_resident_status_code_id', 'person_last_name', 'person_first_name', 'person_middle_name', 'person_title', 'person_birth_date', 'person_home_address_1', 'person_home_address_2', 'person_home_address_3', 'person_address_code', 'person_postal_address_1', 'person_postal_address_2', 'person_postal_address_3', 'person_postal_address_code', 'person_phone_number', 'person_cell_phone_number', 'person_fax_number', 'person_email_address', 'province_code_m2o', 'province_code_id', 'provider_code_m2o', 'provider_code_id', 'employer_m2o', 'employer_id', 'provider_etqe_m2o', 'person_previous_last_name', 'person_previous_alternate_id', 'person_previous_alternate_id_type_id', 'person_previous_provider_code', 'person_previous_provider_etqe_id', 'seeing_rating_id_m2o', 'seeing_rating_id_id', 'hearing_rating_id_m2o', 'hearing_rating_id_id', 'walking_rating_id_m2o', 'walking_rating_id_id', 'remembering_rating_id_m2o', 'remembering_rating_id_id', 'communicating_rating_id_m2o', 'communicating_rating_id_id', 'self_care_rating_id_m2o', 'self_care_rating_id_id', 'last_school_emis_number', 'last_school_year', 'statssa_area_code_m2o', 'statssa_area_code_id', 'popi_act_status_id_m2o', 'popi_act_status_id_id', 'popi_act_status_date', 'date_stamp', 'learner_learnership_ids', 'id', 'display_name', 'create_uid', 'create_date', 'write_uid', 'write_date', '__last_update']

    # def setmis_pull(self):
    #     # raise Warning(_("You are trying to do a SETMIS PULL"))
    #     # employer pull
    #     x = requests.get("http://192.168.15.110/db/setmis3_employer.json")
    #     raise Warning(_(x.content['columns']))

    # @api.model
    # @api.depends('national_id')
    # @api.onchange('national_id')
    # def _compute_age(self):
    #     for record in self:
    #         if record.national_id:
    #             birthdate = record.national_id[:6]
    #             today = datetime.date.today()
    #             # b_date = fields.Datetime.from_string(birthdate)
    #             current_date = str(today).replace('-', '')[2:]
    #             dbg(current_date)
    #             # dbg(current_date-birthdate)
    #             if record.national_id[:2] > str(today).replace('-', '')[2:4]:
    #                 dt_str = '19' + birthdate
    #             else:
    #                 dt_str = '20' + birthdate
    #             dbg(dt_str)
    #             dbg(today)
    #
    #
    #             date_format = '%Y%m%d'
    #             date_obj = datetime.datetime.strptime(dt_str, date_format)
    #             dbg('b_date' + str(date_obj.date()))
    #             age_days = today - (date_obj.date())
    #             dbg((age_days))
    #             youth_days_min = datetime.timedelta(days=6570)
    #             youth_days_max = datetime.timedelta(days=12775)
    #             if age_days < youth_days_min:
    #                 state = False
    #             elif age_days >= youth_days_min and age_days < youth_days_max:
    #                 state = True
    #             else:
    #                 state = False
    #
    #             record.person_youth = state

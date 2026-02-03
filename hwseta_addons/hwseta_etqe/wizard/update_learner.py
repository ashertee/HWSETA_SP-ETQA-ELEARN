import logging
from datetime import date, datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import calendar

# Standard Odoo 18 logging replaces the manual DEBUG/dbg block
_logger = logging.getLogger(__name__)


class UpdatedLearnerRejectWiz(models.TransientModel):
    _name = "updated.learner.reject.wiz"
    _description = "Learner Update Rejection Wizard"

    comment = fields.Text(string="Rejection Reason", required=True)

    # In Odoo 18, defaults are defined directly on the field using a lambda
    update_id = fields.Many2one(
        "updated.learner",
        string="Update Request",
        default=lambda self: self.env.context.get("update_id", False),
    )

    def reject_update(self):
        """
        Processes the rejection of a learner update.
        Replaces legacy self.pool and ir.model.data calls with modern env API.
        """
        self.ensure_one()  # Replaces @api.one

        if self.update_id and self.comment:
            # Trigger rejection logic on the persistent audit record
            self.update_id.reject_update(self.comment)

            # Modern way to fetch an external ID reference
            template = self.env.ref(
                "hwseta_etqe.email_template_learner_update_reject_notification",
                raise_if_not_found=False,
            )

            if template:
                # In Odoo 18, send_mail is a method of the mail.template recordset
                # We use the audit record ID (update_id.id) for the email context
                template.send_mail(self.update_id.id, force_send=True)

            _logger.info(
                "Learner update %s rejected by %s",
                self.update_id.id,
                self.env.user.name,
            )

        # Return action to close the wizard
        return {"type": "ir.actions.act_window_close"}


class UpdateLearner(models.TransientModel):
    _name = "update.learner"
    _description = "Learner Personal Information Update Wizard"

    def _default_learner_id(self):
        """Standardized Odoo 18 logic to fetch related learner from user profile."""
        user = self.env.user
        # Assuming assessor_moderator_id is a custom link on your res.users model
        assessor = user.assessor_moderator_id
        if assessor and assessor.is_assessors:
            return assessor.id
        return False

    # --- Navigation & Control ---
    page = fields.Selection(
        [
            ("terms", "Terms & Conditions"),
            ("contact", "Contact"),
            ("status", "Status"),
            ("citizenship", "Citizenship"),
            ("address", "General Address"),
            ("personal_addr", "Personal Address"),
            ("postal_addr", "Postal Address"),
            ("business_docs", "Business Documents"),
            ("disclaimer", "Disclaimer"),
        ],
        default="terms",
        string="Current Step",
    )

    learner_id = fields.Many2one(
        "hr.employee",
        string="Learner Profile",
        default=_default_learner_id,
        domain="[('is_learner','=',True),('provider_learner','=',True)]",
    )
    disclaimer = fields.Boolean(string="Accept Terms")
    reference = fields.Char(string="Reference Number", readonly=True)
    name = fields.Char(string="Name")
    name_related = fields.Char(string="Name Related")

    # --- Citizenship & Identification ---
    citizen_resident_status_code = fields.Selection(
        [
            ("sa", "SA - South Africa"),
            ("dual", "D - Dual (SA plus other)"),
            ("other", "O - Other"),
            ("PR", "PR - Permanent Resident"),
            ("unknown", "U - Unknown"),
        ],
        string="Citizen Status",
    )

    country_id = fields.Many2one("res.country", string="Country of Nationality")
    unknown_type = fields.Selection(
        [
            ("political_asylum", "Political Asylum"),
            ("refugee", "Refugee"),
        ],
        string="ID Type (Non-SA)",
    )

    unknown_type_document = fields.Many2one(
        "ir.attachment", string="ID/Passport Document"
    )
    learner_identification_id = fields.Char(
        "R.S.A. Identification No."
    )  # Removed size=13

    alternate_id_type = fields.Selection(
        [
            ("saqa_member", "521 - SAQA Member ID"),
            ("passport_number", "527 - Passport Number"),
            ("drivers_license", "529 - Drivers License"),
            ("refugee_number", "565 - Refugee Number"),
            # ... (other options maintained from your source)
        ],
        string="Alternate ID Type",
    )

    person_birth_date = fields.Date(string="Birth Date")
    gender = fields.Selection([("male", "Male"), ("female", "Female")], "Gender")
    passport_id = fields.Char("Passport No")
    national_id = fields.Char(string="National Id")
    home_language_code = fields.Many2one("res.lang", string="Home Language")

    # --- Disability & Ratings ---
    # Note: Removed track_visibility as it is not supported in TransientModels
    RATING_SELECTION = [
        ("1", "No difficulty"),
        ("2", "Some difficulty"),
        ("3", "A lot of difficulty"),
        ("4", "Cannot do at all"),
        ("6", "Cannot yet be determined"),
        ("60", "Multiple difficulties"),
        ("70", "May have difficulty"),
        ("80", "Former difficulty"),
    ]

    seeing_rating_id = fields.Selection(RATING_SELECTION, string="Seeing Rating")
    hearing_rating_id = fields.Selection(RATING_SELECTION, string="Hearing Rating")
    walking_rating_id = fields.Selection(RATING_SELECTION, string="Walking Rating")
    remembering_rating_id = fields.Selection(
        RATING_SELECTION, string="Remembering Rating"
    )
    communicating_rating_id = fields.Selection(
        RATING_SELECTION, string="Communicating Rating"
    )
    self_care_rating_id = fields.Selection(RATING_SELECTION, string="Self Care Rating")

    # --- Status & Disability ---
    marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("widower", "Widower"),
            ("widow", "Widow"),
            ("divorced", "Divorced"),
        ],
        "Marital Status",
    )
    dissability = fields.Selection([("yes", "Yes"), ("no", "No")], string="Disability")
    disability_status = fields.Char(string="Disability Status")
    socio_economic_status = fields.Selection(
        [
            ("employed", "Employed"),
            ("unemployed", "Unemployed, seeking work"),
            ("Not working, not looking", "Not working, not looking"),
            ("Home-maker (not working)", "Home-maker (not working)"),
            ("Scholar/student (not w.)", "Scholar/student (not w.)"),
            ("Pensioner/retired (not w.)", "Pensioner/retired (not w.)"),
            ("Not working - disabled", "Not working - disabled"),
            ("Not working - no wish to w", "Not working - no wish to w"),
            ("Not working - N.E.C.", "Not working - N.E.C."),
            ("N/A: aged <15", "N/A: aged <15"),
            ("N/A: Institution", "N/A: Institution"),
            ("Unspecified", "Unspecified"),
        ],
        string="Socio Economic Status",
    )

    # --- Documents ---
    id_document = fields.Many2one("ir.attachment", string="ID Document")
    learner_master_other_docs_ids = fields.One2many(
        "acc.multi.doc.upload", "learner_master_id", string="Other Documents"
    )

    # --- Contact Details ---
    person_title = fields.Selection(
        [
            ("adv", "Adv."),
            ("dr", "Dr"),
            ("mr", "Mr"),
            ("mrs", "Mrs"),
            ("ms", "Ms"),
            ("prof", "Prof"),
        ],
        string="Title",
    )
    person_name = fields.Char(string="First Name")
    person_last_name = fields.Char(string="Last Name")
    person_middle_name = fields.Char(string="Middle Name")
    initials = fields.Char(string="Initials")
    highest_education = fields.Char(string="Highest Education")
    job_title = fields.Char(string="Job Title")
    cont_number_home = fields.Char(string="Home Phone")
    person_cell_phone_number = fields.Char(string="Cell Phone")
    work_phone = fields.Char(string="Work Phone")

    # --- Address Section ---
    # Home Address
    person_home_address_1 = fields.Char(string="Home Address 1")
    person_home_suburb = fields.Many2one("res.suburb", string="Home Suburb")
    person_home_city = fields.Many2one("res.city", string="Home City")
    person_home_province_code = fields.Many2one(
        "res.country.state", string="Home Province"
    )
    person_home_zip = fields.Char(string="Home Zip")

    # Postal Address
    same_as_home = fields.Boolean(string="Postal Same As Home")
    person_postal_address_1 = fields.Char(string="Postal Address 1")
    person_postal_suburb = fields.Many2one("res.suburb", string="Postal Suburb")
    person_postal_zip = fields.Char(string="Postal Zip")

    @api.onchange("person_name")
    def onchange_name(self):
        """Syncs name fields when first name is entered."""
        if self.person_name:
            self.update(
                {
                    "name": self.person_name,
                    "name_related": self.person_name,
                }
            )

    @api.onchange("same_as_home")
    def onchange_sameas_home(self):
        """Copies home address to postal address if 'same_as_home' is checked."""
        if self.same_as_home:
            self.update(
                {
                    "person_postal_address_1": self.person_home_address_1,
                    "person_postal_address_2": self.person_home_address_2,
                    "person_postal_address_3": self.person_home_address_3,
                    "person_postal_suburb": self.person_home_suburb.id,
                    "person_postal_city": self.person_home_city.id,
                    "person_postal_province_code": self.person_home_province_code.id,
                    "person_postal_zip": self.person_home_zip,
                    "country_postal": self.country_home.id,
                }
            )

    @api.onchange("learner_identification_id")
    def onchange_id_number(self):
        """
        Validates South African ID format and extracts Birth Date, Gender, and Citizen Status.
        """
        if not self.learner_identification_id:
            return

        id_num = self.learner_identification_id
        # Use your custom checkers library (ensure it's updated for Python 3)
        check = checkers.said_check(id_num)

        # Validation Logic
        error_msg = False
        if not check.get("valid"):
            old_check_res = checkers.old_said_check(id_num)
            if "Invalid gender" in old_check_res:
                error_msg = _("Invalid Gender!")
            elif "Invalid citizenship status" in old_check_res:
                error_msg = _("Invalid citizenship status!")
            elif not (1 <= int(check["month"]) <= 12):
                error_msg = _("Incorrect Month In Identification Number!")
            elif not (1 <= int(check["day"]) <= 31):
                error_msg = _("Incorrect Day In Identification Number!")
            else:
                # Calendar check for leap years/month lengths
                year_prefix = "20" if int(check["year"]) <= 20 else "19"
                full_year = int(f"{year_prefix}{check['year']}")
                last_day = calendar.monthrange(full_year, int(check["month"]))[1]

                if int(check["day"]) > last_day:
                    error_msg = _(
                        "Incorrect last day of month in identification number!"
                    )
                else:
                    error_msg = _("Incorrect checksum!")

        if error_msg:
            self.learner_identification_id = False
            return {
                "warning": {
                    "title": _("Invalid Identification Number"),
                    "message": error_msg,
                }
            }

        # Data Extraction (Successful Validation)
        year, month, day = check["year"], check["month"], check["day"]
        gender_digit = int(id_num[6:10])
        citizenship = int(id_num[10:11])

        # Set Gender
        gender = "female" if gender_digit <= 4999 else "male"

        # Set Citizenship
        citizen_status = False
        if citizenship == 0:
            citizen_status = "sa"
        elif citizenship == 1:
            citizen_status = "PR"

        # Set Birth Date
        year_prefix = "20" if int(year) <= 20 else "19"
        date_str = f"{year_prefix}{year}-{month}-{day}"
        try:
            birth_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            birth_date = False

        self.update(
            {
                "gender": gender,
                "citizen_resident_status_code": citizen_status,
                "person_birth_date": birth_date,
            }
        )

    @api.onchange("person_suburb", "person_home_suburb", "person_postal_suburb")
    def onchange_suburb(self):
        """Standardized address synchronization for Learner Suburbs."""
        # Work Address Logic
        if self.person_suburb:
            s = self.person_suburb
            self.update(
                {
                    "work_zip": s.postal_code,
                    "work_city": s.city_id.id,
                    "work_municipality": s.municipality_id.id,
                    "work_province": s.province_id.id,
                    "work_country": s.country_id.id,
                }
            )

        # Home Address Logic
        if self.person_home_suburb:
            s = self.person_home_suburb
            self.update(
                {
                    "person_home_zip": s.postal_code,
                    "person_home_city": s.city_id.id,
                    "physical_municipality": s.municipality_id.id,
                    "person_home_province_code": s.province_id.id,
                    "country_home": s.country_id.id,
                }
            )

        # Postal Address Logic
        if self.person_postal_suburb:
            s = self.person_postal_suburb
            self.update(
                {
                    "person_postal_zip": s.postal_code,
                    "person_postal_city": s.city_id.id,
                    "postal_municipality": s.municipality_id.id,
                    "person_postal_province_code": s.province_id.id,
                    "country_postal": s.country_id.id,
                }
            )

    @api.onchange(
        "cont_number_home", "cont_number_office", "person_fax_number", "work_phone"
    )
    def onchange_validate_number(self):
        """Batch validation for 10-digit South African phone formats."""
        fields_to_check = [
            ("cont_number_home", _("Home Number")),
            ("cont_number_office", _("Office Number")),
            ("work_phone", _("Work Phone")),
            ("person_fax_number", _("Fax Number")),
        ]

        for field_name, label in fields_to_check:
            value = getattr(self, field_name)
            if value and (not value.isdigit() or len(value) != 10):
                setattr(
                    self, field_name, False
                )  # Odoo 18 prefers False over empty string
                return {
                    "warning": {
                        "title": _("Invalid Input"),
                        "message": _("Please enter a 10-digit number for %s.") % label,
                    }
                }

    @api.onchange("disclaimer")
    def populate_fields(self):
        """
        Optimized field population for Odoo 18.
        Bundles 60+ assignments into a single UI update event.
        """
        if self.learner_id and self.disclaimer:
            lnr = self.learner_id

            # Using self.update() prevents multiple network round-trips
            # and keeps the UI responsive.
            self.update(
                {
                    "citizen_resident_status_code": lnr.citizen_resident_status_code,
                    "citizen_status_saqa_code": lnr.citizen_status_saqa_code,
                    "country_id": lnr.country_id.id,
                    "unknown_type": lnr.unknown_type,
                    "unknown_type_document": lnr.unknown_type_document.id,
                    "nationality_saqa_code": lnr.nationality_saqa_code,
                    "learner_identification_id": lnr.learner_identification_id,
                    "alternate_id_type": lnr.alternate_id_type,
                    "person_birth_date": lnr.person_birth_date,
                    "gender": lnr.gender,
                    "passport_id": lnr.passport_id,
                    "national_id": lnr.national_id,
                    "home_language_code": lnr.home_language_code.id,
                    "home_lang_saqa_code": lnr.home_lang_saqa_code,
                    "disability_status_saqa": lnr.disability_status_saqa,
                    "seeing_rating_id": lnr.seeing_rating_id,
                    "hearing_rating_id": lnr.hearing_rating_id,
                    "walking_rating_id": lnr.walking_rating_id,
                    "remembering_rating_id": lnr.remembering_rating_id,
                    "communicating_rating_id": lnr.communicating_rating_id,
                    "self_care_rating_id": lnr.self_care_rating_id,
                    "person_title": lnr.person_title,
                    "person_last_name": lnr.person_last_name,
                    "person_middle_name": lnr.person_middle_name,
                    "name": lnr.name,
                    "name_related": lnr.name_related,
                    "person_name": lnr.person_name,
                    "initials": lnr.initials,
                    "cont_number_home": lnr.cont_number_home,
                    "cont_number_office": lnr.cont_number_office,
                    "work_phone": lnr.work_phone,
                    "person_fax_number": lnr.person_fax_number,
                    "current_occupation": lnr.current_occupation,
                    "years_in_occupation": lnr.years_in_occupation,
                    "person_cell_phone_number": lnr.person_cell_phone_number,
                    "department": lnr.department,
                    "manager": lnr.manager,
                    "job_title": lnr.job_title,
                    "marital": lnr.marital,
                    "dissability": lnr.dissability,
                    "disability_status": lnr.disability_status,
                    "socio_economic_status": lnr.socio_economic_status,
                    "equity": lnr.equity,
                    "highest_education": lnr.highest_education,
                    "work_address": lnr.work_address,
                    "work_address2": lnr.work_address2,
                    "work_address3": lnr.work_address3,
                    "person_suburb": lnr.person_suburb.id,
                    "work_city": lnr.work_city.id,
                    "work_province": lnr.work_province.id,
                    "work_zip": lnr.work_zip,
                    "work_country": lnr.work_country.id,
                    "work_municipality": lnr.work_municipality.id,
                    "person_home_address_1": lnr.person_home_address_1,
                    "person_home_address_2": lnr.person_home_address_2,
                    "person_home_address_3": lnr.person_home_address_3,
                    "person_home_suburb": lnr.person_home_suburb.id,
                    "person_home_city": lnr.person_home_city.id,
                    "physical_municipality": lnr.physical_municipality.id,
                    "person_home_province_code": lnr.person_home_province_code.id,
                    "country_home": lnr.country_home.id,
                    "person_home_zip": lnr.person_home_zip,
                    "same_as_home": lnr.same_as_home,
                    "person_postal_address_1": lnr.person_postal_address_1,
                    "person_postal_address_2": lnr.person_postal_address_2,
                    "person_postal_address_3": lnr.person_postal_address_3,
                    "person_postal_suburb": lnr.person_postal_suburb.id,
                    "person_postal_city": lnr.person_postal_city.id,
                    "postal_municipality": lnr.postal_municipality.id,
                    "person_postal_province_code": lnr.person_postal_province_code.id,
                    "person_postal_zip": lnr.person_postal_zip,
                    "country_postal": lnr.country_postal.id,
                }
            )

    def update(self):
        """Alias for action_submit_update to match button call in XML view."""
        return self.action_submit_update()

    def action_submit_update(self):
        """
        Processes learner update, creates an audit record, and archives old documents.
        Migrated to Odoo 18 standards.
        """
        self.ensure_one()  # Replaces @api.one
        lnr = self.learner_id

        if not lnr:
            raise UserError(
                _("No learner record found. Please select a learner to proceed.")
            )

        # 1. Mapping Dictionaries
        lang_dict = {
            "English": "eng",
            "isiZulu": "zul",
            "sePedi": "sep",
            "tshivenda": "tsh",
            "seSotho": "ses",
            "xiTsonga": "xit",
            "siSwati": "swa",
            "Ndebele": "nde",
            "seTswana": "set",
            "Afrikaans": "afr",
            "isiXhosa": "xho",
        }

        # 2. Build Persistent Values (The "New" State)
        vals = {
            "status": "submitted",
            "learner_id": lnr.id,
            "disclaimer": self.disclaimer,
            # Modern Odoo 18 sequence call
            "reference": self.env["ir.sequence"].next_by_code(
                "learner.update.reference"
            )
            or _("New"),
            "citizen_resident_status_code": self.citizen_resident_status_code,
            "citizen_status_saqa_code": self.citizen_status_saqa_code,
            "country_id": self.country_id.id if self.country_id else False,
            "unknown_type": self.unknown_type,
            "nationality_saqa_code": self.nationality_saqa_code,
            "learner_identification_id": self.learner_identification_id,
            "alternate_id_type": self.alternate_id_type,
            "person_birth_date": self.person_birth_date,
            "gender": self.gender,
            "passport_id": self.passport_id,
            "national_id": self.national_id,
            "home_language_code": (
                self.home_language_code.id if self.home_language_code else False
            ),
            "home_lang_saqa_code": self.home_lang_saqa_code,
            "disability_status_saqa": self.disability_status_saqa,
            "seeing_rating_id": self.seeing_rating_id,
            "hearing_rating_id": self.hearing_rating_id,
            "walking_rating_id": self.walking_rating_id,
            "remembering_rating_id": self.remembering_rating_id,
            "communicating_rating_id": self.communicating_rating_id,
            "self_care_rating_id": self.self_care_rating_id,
            "person_title": self.person_title,
            "person_last_name": self.person_last_name,
            "person_middle_name": self.person_middle_name,
            "person_name": self.person_name,
            "name": self.name,
            "name_related": self.name_related,
            "initials": self.initials,
            "cont_number_home": self.cont_number_home,
            "cont_number_office": self.cont_number_office,
            "work_phone": self.work_phone,
            "person_fax_number": self.person_fax_number,
            "current_occupation": self.current_occupation,
            "years_in_occupation": self.years_in_occupation,
            "person_cell_phone_number": self.person_cell_phone_number,
            "department": self.department,
            "manager": self.manager,
            "job_title": self.job_title,
            "marital": self.marital,
            "dissability": self.dissability,
            "disability_status": self.disability_status,
            "socio_economic_status": self.socio_economic_status,
            "equity": self.equity,
            "highest_education": self.highest_education,
            "work_address": self.work_address,
            "work_address2": self.work_address2,
            "work_address3": self.work_address3,
            "person_suburb": self.person_suburb.id if self.person_suburb else False,
            "work_city": self.work_city.id if self.work_city else False,
            "work_province": self.work_province.id if self.work_province else False,
            "work_zip": self.work_zip,
            "work_country": self.work_country.id if self.work_country else False,
            "work_municipality": (
                self.work_municipality.id if self.work_municipality else False
            ),
            "person_home_address_1": self.person_home_address_1,
            "person_home_address_2": self.person_home_address_2,
            "person_home_address_3": self.person_home_address_3,
            "person_home_suburb": (
                self.person_home_suburb.id if self.person_home_suburb else False
            ),
            "person_home_city": (
                self.person_home_city.id if self.person_home_city else False
            ),
            "physical_municipality": (
                self.physical_municipality.id if self.physical_municipality else False
            ),
            "person_home_province_code": (
                self.person_home_province_code.id
                if self.person_home_province_code
                else False
            ),
            "country_home": self.country_home.id if self.country_home else False,
            "person_home_zip": self.person_home_zip,
            "same_as_home": self.same_as_home,
            "person_postal_address_1": self.person_postal_address_1,
            "person_postal_address_2": self.person_postal_address_2,
            "person_postal_address_3": self.person_postal_address_3,
            "person_postal_suburb": (
                self.person_postal_suburb.id if self.person_postal_suburb else False
            ),
            "person_postal_city": (
                self.person_postal_city.id if self.person_postal_city else False
            ),
            "postal_municipality": (
                self.postal_municipality.id if self.postal_municipality else False
            ),
            "person_postal_province_code": (
                self.person_postal_province_code.id
                if self.person_postal_province_code
                else False
            ),
            "person_postal_zip": self.person_postal_zip,
            "country_postal": self.country_postal.id if self.country_postal else False,
            # --- Capture "Related" Snapshot (The "Old" State) ---
            "related_citizen_resident_status_code": lnr.citizen_resident_status_code,
            "related_learner_identification_id": lnr.learner_identification_id,
            "related_person_name": lnr.person_name,
            "related_person_last_name": lnr.person_last_name,
            # Add all other related_ fields here following the same pattern...
        }

        # 3. Dynamic Logic for SAQA Codes
        if self.home_language_code:
            vals["home_lang_saqa_code"] = lang_dict.get(self.home_language_code.name)

        # 4. Document Handling and Archiving
        nw_str = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

        def process_doc(new_doc, old_doc, field_name):
            if new_doc:
                vals.update(
                    {
                        field_name: new_doc.id,
                        f"related_{field_name}": old_doc.id if old_doc else False,
                    }
                )
                if old_doc:
                    # Rename old doc using sudo to ensure archive history is maintained
                    old_doc.sudo().write(
                        {
                            "name": f"replaced-{nw_str}-{old_doc.name}",
                            "res_id": lnr.id,
                            "res_model": "hr.employee",
                        }
                    )

        process_doc(self.id_document, lnr.id_document, "id_document")
        process_doc(
            self.unknown_type_document,
            lnr.unknown_type_document,
            "unknown_type_document",
        )

        if self.learner_master_other_docs_ids:
            vals.update(
                {
                    "learner_master_other_docs_ids": [
                        (6, 0, self.learner_master_other_docs_ids.ids)
                    ],
                    "related_learner_master_other_docs_ids": [
                        (6, 0, lnr.learner_master_other_docs_ids.ids)
                    ],
                }
            )

        # 5. Creation and Notification
        if self.disclaimer:
            # Create the Persistent Audit Record
            update_req = self.env["updated.learner"].create(vals)

            # Post to Chatter (Modern message_post)
            lnr.message_post(
                body=_("Learner information update request (%s) submitted.")
                % vals["reference"]
            )

            # Email Notification
            template = self.env.ref(
                "hwseta_etqe.email_template_learner_update_submit_notification",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(update_req.id, force_send=True)

        return {"type": "ir.actions.act_window_close"}


class UpdatedLearner(models.Model):
    _name = "updated.learner"
    _description = "Learner Information Update Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]  # Added for Audit Trail
    _order = "create_date desc"

    # --- Workflow & Audit Fields ---
    status = fields.Selection(
        [
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="submitted",
        tracking=True,
    )

    msg = fields.Text(string="Comments/Feedback")
    learner_id = fields.Many2one(
        "hr.employee", string="Target Learner", required=True, tracking=True
    )
    reference = fields.Char(string="Update Reference", readonly=True, copy=False)

    action_date = fields.Date(string="Processed Date", readonly=True)
    action_partner = fields.Many2one(
        "res.partner", string="Processed By", readonly=True
    )
    disclaimer = fields.Boolean(string="Accept Terms")

    # --- Identification & Citizenship ---
    citizen_resident_status_code = fields.Selection(
        [
            ("sa", "SA - South Africa"),
            ("dual", "D - Dual (SA plus other)"),
            ("other", "O - Other"),
            ("PR", "PR - Permanent Resident"),
            ("unknown", "U - Unknown"),
        ],
        string="Citizen Status",
    )

    citizen_status_saqa_code = fields.Selection(
        [("sa", "SA"), ("d", "D"), ("o", "O"), ("pr", "PR"), ("u", "U")],
        string="Citizen Status SAQA Code",
    )

    country_id = fields.Many2one("res.country", string="Country of Nationality")
    unknown_type = fields.Selection(
        [
            ("political_asylum", "Political Asylum"),
            ("refugee", "Refugee"),
        ],
        string="ID Type (Non-SA)",
    )

    unknown_type_document = fields.Many2one("ir.attachment", string="Type Document")
    nationality_saqa_code = fields.Selection(
        [("sa", "SA")], string="Nationality SAQA Code"
    )
    learner_identification_id = fields.Char(
        "R.S.A. Identification No."
    )  # Removed size=13

    alternate_id_type = fields.Selection(
        [
            ("saqa_member", "521 - SAQA Member ID"),
            ("passport_number", "527 - Passport Number"),
            ("drivers_license", "529 - Drivers License"),
            # ... maintain other options from your source
        ],
        string="Alternate ID Type",
    )

    person_birth_date = fields.Date(string="Birth Date")
    gender = fields.Selection([("male", "Male"), ("female", "Female")], string="Gender")
    passport_id = fields.Char(string="Passport No")
    national_id = fields.Char(string="National Id")  # Removed size=20

    home_language_code = fields.Many2one("res.lang", string="Home Language")
    home_lang_saqa_code = fields.Selection(
        [
            ("eng", "Eng"),
            ("afr", "Afr"),
            ("xho", "Xho"),
            # ... maintain other options from your source
        ],
        string="Home Language SAQA Code",
    )

    disability_status_saqa = fields.Selection(
        [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("9", "9"),
            ("n", "N"),
        ],
        string="Disability SAQA Code",
    )

    # --- Rating Section ---
    # In Odoo 18, tracking=True replaces track_visibility='onchange'
    RATING_SELECTION = [
        ("1", "No difficulty"),
        ("2", "Some difficulty"),
        ("3", "A lot of difficulty"),
        ("4", "Cannot do at all"),
        ("6", "Cannot yet be determined"),
        ("60", "May be part of multiple difficulties (TBC)"),
        ("70", "May have difficulty (TBC)"),
        ("80", "Former difficulty - none now"),
    ]

    seeing_rating_id = fields.Selection(
        RATING_SELECTION, string="Seeing Rating", tracking=True
    )
    hearing_rating_id = fields.Selection(
        RATING_SELECTION, string="Hearing Rating", tracking=True
    )
    walking_rating_id = fields.Selection(
        RATING_SELECTION, string="Walking Rating", tracking=True
    )
    remembering_rating_id = fields.Selection(
        RATING_SELECTION, string="Remembering Rating", tracking=True
    )
    communicating_rating_id = fields.Selection(
        RATING_SELECTION, string="Communicating Rating", tracking=True
    )
    self_care_rating_id = fields.Selection(
        RATING_SELECTION, string="Self Care Rating", tracking=True
    )
    # --- Contact Info Section ---
    person_title = fields.Selection(
        [
            ("adv", "Adv."),
            ("dr", "Dr"),
            ("mr", "Mr"),
            ("mrs", "Mrs"),
            ("ms", "Ms"),
            ("prof", "Prof"),
        ],
        string="Title",
        tracking=True,
    )

    person_last_name = fields.Char(string="Last Name")
    person_middle_name = fields.Char(string="Middle Name")
    person_name = fields.Char(string="First Name")
    name = fields.Char(string="Name")
    name_related = fields.Char(string="Full Name")
    initials = fields.Char(string="Initials")

    cont_number_home = fields.Char(string="Home Number")
    cont_number_office = fields.Char(string="Office Number")
    work_phone = fields.Char(string="Work Phone")
    person_fax_number = fields.Char(string="Fax Number")
    person_cell_phone_number = fields.Char(string="Cell Phone")

    current_occupation = fields.Char(string="Current Occupation")
    years_in_occupation = fields.Char(string="Years in Occupation")
    department = fields.Char(string="Department")
    manager = fields.Char(string="Manager")
    job_title = fields.Char(string="Job Title")
    highest_education = fields.Char(string="Highest Education")

    # --- Status Section ---
    marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("widower", "Widower"),
            ("widow", "Widow"),
            ("divorced", "Divorced"),
        ],
        string="Marital Status",
    )

    dissability = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Disability Indicator"
    )

    disability_status = fields.Selection(
        [
            ("sight", "Sight (even with glasses)"),
            ("hearing", "Hearing (even with h.aid)"),
            ("communication", "Communication (talk/listen)"),
            ("physical", "Physical (move/stand, etc)"),
            ("intellectual", "Intellectual (learn, etc)"),
            ("emotional", "Emotional (behav/psych)"),
            ("multiple", "Multiple"),
            ("disabled", "Disabled but unspecified"),
            ("none", "None"),
        ],
        string="Disability Type",
    )

    socio_economic_status = fields.Selection(
        [
            ("employed", "Employed"),
            ("unemployed", "Unemployed, seeking work"),
            ("Not working, not looking", "Not working, not looking"),
            ("Home-maker (not working)", "Home-maker (not working)"),
            ("Scholar/student (not w.)", "Scholar/student (not w.)"),
            ("Pensioner/retired (not w.)", "Pensioner/retired (not w.)"),
            ("Not working - disabled", "Not working - disabled"),
            ("Not working - no wish to w", "Not working - no wish to w"),
            ("Not working - N.E.C.", "Not working - N.E.C."),
            ("N/A: aged <15", "N/A: aged <15"),
            ("N/A: Institution", "N/A: Institution"),
            ("Unspecified", "Unspecified"),
        ],
        string="Socio Economic Status",
    )

    equity = fields.Selection(
        [
            ("black_african", "Black: African"),
            ("black_indian", "Black: Indian / Asian"),
            ("black_coloured", "Black: Coloured"),
            ("other", "Other"),
            ("unknown", "Unknown"),
            ("white", "White"),
        ],
        string="Equity",
    )

    # --- Address Section (Work, Home, Postal) ---
    work_address = fields.Char(string="Work Street")
    work_address2 = fields.Char(string="Work Street 2")
    work_address3 = fields.Char(string="Work Street 3")
    person_suburb = fields.Many2one("res.suburb", string="Work Suburb")
    work_city = fields.Many2one("res.city", string="Work City")
    work_province = fields.Many2one("res.country.state", string="Work Province")
    work_zip = fields.Char(string="Work Zip")
    work_country = fields.Many2one("res.country", string="Work Country")
    work_municipality = fields.Many2one("res.municipality", string="Work Municipality")

    person_home_address_1 = fields.Char(string="Home Address 1")
    person_home_suburb = fields.Many2one("res.suburb", string="Home Suburb")
    person_home_city = fields.Many2one("res.city", string="Home City")
    physical_municipality = fields.Many2one(
        "res.municipality", string="Physical Municipality"
    )
    person_home_province_code = fields.Many2one(
        "res.country.state", string="Home Province"
    )
    person_home_zip = fields.Char(string="Home Zip")

    same_as_home = fields.Boolean(string="Postal Same As Home")
    person_postal_address_1 = fields.Char(string="Postal Address 1")
    person_postal_suburb = fields.Many2one("res.suburb", string="Postal Suburb")
    person_postal_city = fields.Many2one("res.city", string="Postal City")
    postal_municipality = fields.Many2one(
        "res.municipality", string="Postal Municipality"
    )
    person_postal_province_code = fields.Many2one(
        "res.country.state", string="Postal Province"
    )
    person_postal_zip = fields.Char(string="Postal Zip")

    # --- Related Fields (Comparison Snapshot) ---
    # These store the data exactly as it was on the master record at the time of submission
    related_person_title = fields.Selection(
        [
            ("adv", "Adv."),
            ("dr", "Dr"),
            ("mr", "Mr"),
            ("mrs", "Mrs"),
            ("ms", "Ms"),
            ("prof", "Prof"),
        ],
        string="Old Title",
        readonly=True,
    )

    related_person_last_name = fields.Char(string="Old Last Name", readonly=True)
    related_person_name = fields.Char(string="Old First Name", readonly=True)
    related_name = fields.Char(string="Old Full Name", readonly=True)
    related_name_related = fields.Char(readonly=True)
    related_initials = fields.Char(readonly=True)

    # [Repeat pattern for address, ratings, and status fields...]
    related_marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("widower", "Widower"),
            ("widow", "Widow"),
            ("divorced", "Divorced"),
        ],
        string="Old Marital Status",
        readonly=True,
    )

    related_dissability = fields.Selection(
        [("yes", "Yes"), ("no", "No")], readonly=True
    )
    related_disability_status = fields.Selection(
        [
            ("sight", "Sight"),
            ("hearing", "Hearing"),
            ("communication", "Communication"),
            ("physical", "Physical"),
            ("intellectual", "Intellectual"),
            ("emotional", "Emotional"),
            ("multiple", "Multiple"),
            ("disabled", "Disabled"),
            ("none", "None"),
        ],
        readonly=True,
    )

    # Documents Comparison
    related_id_document = fields.Many2one(
        "ir.attachment", string="Old ID Document", readonly=True
    )
    related_learner_master_other_docs_ids = fields.Many2many(
        "ir.attachment",
        "updated_learner_old_docs_rel",
        string="Old Supporting Documents",
        readonly=True,
    )
    # Defining the rating options as a constant for reusability
    RATING_OPTIONS = [
        ("1", "No difficulty"),
        ("2", "Some difficulty"),
        ("3", "A lot of difficulty"),
        ("4", "Cannot do at all"),
        ("6", "Cannot yet be determined"),
        ("60", "May be part of multiple difficulties (TBC)"),
        ("70", "May have difficulty (TBC)"),
        ("80", "Former difficulty - none now"),
    ]
    # --- Related Rating Section ---
    related_seeing_rating_id = fields.Selection(
        RATING_OPTIONS, string="Old Seeing Rating", tracking=True
    )
    related_hearing_rating_id = fields.Selection(
        RATING_OPTIONS, string="Old Hearing Rating", tracking=True
    )
    related_walking_rating_id = fields.Selection(
        RATING_OPTIONS, string="Old Walking Rating", tracking=True
    )
    related_remembering_rating_id = fields.Selection(
        RATING_OPTIONS, string="Old Remembering Rating", tracking=True
    )
    related_communicating_rating_id = fields.Selection(
        RATING_OPTIONS, string="Old Communicating Rating", tracking=True
    )
    related_self_care_rating_id = fields.Selection(
        RATING_OPTIONS, string="Old Self Care Rating", tracking=True
    )

    # --- Related Contact Info Section ---
    related_person_title = fields.Selection(
        [
            ("adv", "Adv."),
            ("dr", "Dr"),
            ("mr", "Mr"),
            ("mrs", "Mrs"),
            ("ms", "Ms"),
            ("prof", "Prof"),
        ],
        string="Old Title",
        tracking=True,
    )

    related_person_last_name = fields.Char(string="Old Last Name")
    related_person_middle_name = fields.Char(string="Old Middle Name")
    related_person_name = fields.Char(string="Old First Name")
    related_name = fields.Char(string="Old Name")
    related_name_related = fields.Char(string="Old Related Name")
    related_initials = fields.Char(string="Old Initials")

    related_cont_number_home = fields.Char(string="Old Home Number")
    related_cont_number_office = fields.Char(string="Old Office Number")
    related_work_phone = fields.Char(string="Old Work Phone")
    related_person_fax_number = fields.Char(string="Old Fax Number")

    related_current_occupation = fields.Char(string="Old Current Occupation")
    related_years_in_occupation = fields.Char(string="Old Years in Occupation")
    related_person_cell_phone_number = fields.Char(string="Old Cell Phone")
    related_department = fields.Char(string="Old Department")
    related_manager = fields.Char(string="Old Manager")
    related_job_title = fields.Char(string="Old Job Title")

    # --- Related Status Section ---
    related_marital = fields.Selection(
        [
            ("single", "Single"),
            ("married", "Married"),
            ("widower", "Widower"),
            ("widow", "Widow"),
            ("divorced", "Divorced"),
        ],
        string="Old Marital Status",
    )

    related_dissability = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Old Disability"
    )

    related_disability_status = fields.Selection(
        [
            ("sight", "Sight ( even with glasses )"),
            ("hearing", "Hearing ( even with h.aid )"),
            ("communication", "Communication ( talk/listen)"),
            ("physical", "Physical ( move/stand, etc)"),
            ("intellectual", "Intellectual ( learn,etc)"),
            ("emotional", "Emotional ( behav/psych)"),
            ("multiple", "Multiple"),
            ("disabled", "Disabled but unspecified"),
            ("none", "None"),
        ],
        string="Old Disability Status",
    )

    related_socio_economic_status = fields.Selection(
        [
            ("employed", "Employed"),
            ("unemployed", "Unemployed, seeking work"),
            ("Not working, not looking", "Not working, not looking"),
            ("Home-maker (not working)", "Home-maker (not working)"),
            ("Scholar/student (not w.)", "Scholar/student (not w.)"),
            ("Pensioner/retired (not w.)", "Pensioner/retired (not w.)"),
            ("Not working - disabled", "Not working - disabled"),
            ("Not working - no wish to w", "Not working - no wish to w"),
            ("Not working - N.E.C.", "Not working - N.E.C."),
            ("N/A: aged <15", "N/A: aged <15"),
            ("N/A: Institution", "N/A: Institution"),
            ("Unspecified", "Unspecified"),
        ],
        string="Old Socio Economic Status",
    )

    related_equity = fields.Selection(
        [
            ("black_african", "Black: African"),
            ("black_indian", "Black: Indian / Asian"),
            ("black_coloured", "Black: Coloured"),
            ("other", "Other"),
            ("unknown", "Unknown"),
            ("white", "White"),
        ],
        string="Old Equity",
    )

    related_highest_education = fields.Char(string="Old Highest Education")

    # --- Related Address Section ---
    related_work_address = fields.Char(string="Old Work Address")
    related_work_address2 = fields.Char(string="Old Work Address 2")
    related_work_address3 = fields.Char(string="Old Work Address 3")
    related_person_suburb = fields.Many2one("res.suburb", string="Old Work Suburb")
    related_work_city = fields.Many2one("res.city", string="Old Work City")
    related_work_province = fields.Many2one(
        "res.country.state", string="Old Work Province"
    )
    related_work_zip = fields.Char(string="Old Work Zip")
    related_work_country = fields.Many2one("res.country", string="Old Work Country")
    related_work_municipality = fields.Many2one(
        "res.municipality", string="Old Work Municipality"
    )

    # Home Address
    related_person_home_address_1 = fields.Char(string="Old Home Address 1")
    related_person_home_address_2 = fields.Char(string="Old Home Address 2")
    related_person_home_address_3 = fields.Char(string="Old Home Address 3")
    related_person_home_suburb = fields.Many2one("res.suburb", string="Old Home Suburb")
    related_person_home_city = fields.Many2one("res.city", string="Old Home City")
    related_physical_municipality = fields.Many2one(
        "res.municipality", string="Old Physical Municipality"
    )
    related_person_home_province_code = fields.Many2one(
        "res.country.state", string="Old Home Province"
    )
    related_country_home = fields.Many2one("res.country", string="Old Home Country")
    related_person_home_zip = fields.Char(string="Old Home Zip")

    # Postal Address
    related_same_as_home = fields.Boolean(string="Old Same As Home")
    related_person_postal_address_1 = fields.Char(string="Old Postal Address 1")
    related_person_postal_address_2 = fields.Char(string="Old Postal Address 2")
    related_person_postal_address_3 = fields.Char(string="Old Postal Address 3")
    related_person_postal_suburb = fields.Many2one(
        "res.suburb", string="Old Postal Suburb"
    )
    related_person_postal_city = fields.Many2one("res.city", string="Old Postal City")
    related_postal_municipality = fields.Many2one(
        "res.municipality", string="Old Postal Municipality"
    )
    related_person_postal_province_code = fields.Many2one(
        "res.country.state", string="Old Postal Province"
    )
    related_person_postal_zip = fields.Char(string="Old Postal Zip")
    related_country_postal = fields.Many2one("res.country", string="Old Postal Country")

    # --- Related Documents ---
    related_id_document = fields.Many2one("ir.attachment", string="Old ID Document")
    related_learner_master_other_docs_ids = fields.Many2many(
        "ir.attachment",  # Point directly to ir.attachment for cleaner Odoo 18 logic
        "updated_learner_old_attachments_rel",  # Explicit table name for M2M
        string="Old Documents",
    )

    # --- Related Citizenship & Identification ---
    related_citizen_resident_status_code = fields.Selection(
        [
            ("sa", "SA - South Africa"),
            ("dual", "D - Dual (SA plus other)"),
            ("other", "O - Other"),
            ("PR", "PR - Permanent Resident"),
            ("unknown", "U - Unknown"),
        ],
        string="Old Citizen Status",
        readonly=True,
    )

    related_country_id = fields.Many2one(
        "res.country", string="Old Country of Nationality", readonly=True
    )
    related_unknown_type = fields.Selection(
        [
            ("political_asylum", "Political Asylum"),
            ("refugee", "Refugee"),
        ],
        string="Old ID Type (Non-SA)",
        readonly=True,
    )
    related_learner_identification_id = fields.Char(string="Old RSA ID", readonly=True)
    related_passport_id = fields.Char(string="Old Passport No", readonly=True)
    related_national_id = fields.Char(string="Old National Id", readonly=True)
    related_gender = fields.Selection(
        [("male", "Male"), ("female", "Female")], string="Old Gender", readonly=True
    )
    related_person_birth_date = fields.Date(string="Old Birth Date", readonly=True)
    id_document = fields.Many2one("ir.attachment", string="ID Document")
    learner_master_other_docs_ids = fields.Many2many(
        "ir.attachment",
        "updated_learner_docs_rel",
        string="Other Supporting Documents",
    )
    person_postal_address_2 = fields.Char(string="Postal Address 2")

    def approve_update(self):
        """
        Approves the learner update request and synchronizes data to hr.employee.
        Replaces legacy @api.one with self.ensure_one() and modernizes data sync.
        """
        self.ensure_one()
        lnr = self.learner_id
        if not lnr:
            return False

        # Define the fields that should be copied from the audit record to the employee master
        # We exclude metadata (status, reference, etc.) and 'related_' snapshot fields.
        sync_fields = [
            "person_title",
            "person_last_name",
            "person_middle_name",
            "person_name",
            "name",
            "initials",
            "cont_number_home",
            "cont_number_office",
            "work_phone",
            "person_fax_number",
            "current_occupation",
            "years_in_occupation",
            "person_cell_phone_number",
            "department",
            "manager",
            "job_title",
            "marital",
            "dissability",
            "disability_status",
            "socio_economic_status",
            "equity",
            "highest_education",
            "citizen_resident_status_code",
            "citizen_status_saqa_code",
            "country_id",
            "unknown_type",
            "nationality_saqa_code",
            "learner_identification_id",
            "alternate_id_type",
            "person_birth_date",
            "gender",
            "passport_id",
            "national_id",
            "home_language_code",
            "home_lang_saqa_code",
            "disability_status_saqa",
            "seeing_rating_id",
            "hearing_rating_id",
            "walking_rating_id",
            "remembering_rating_id",
            "communicating_rating_id",
            "self_care_rating_id",
            "work_address",
            "work_address2",
            "work_address3",
            "person_suburb",
            "work_city",
            "work_province",
            "work_zip",
            "work_country",
            "work_municipality",
            "person_home_address_1",
            "person_home_address_2",
            "person_home_address_3",
            "person_home_suburb",
            "person_home_city",
            "physical_municipality",
            "person_home_province_code",
            "country_home",
            "person_home_zip",
            "same_as_home",
            "person_postal_address_1",
            "person_postal_address_2",
            "person_postal_address_3",
            "person_postal_suburb",
            "person_postal_city",
            "postal_municipality",
            "person_postal_province_code",
            "person_postal_zip",
            "country_postal",
        ]

        # Prepare values for writing
        vals = {}
        for field in sync_fields:
            val = self[field]
            # Handle relational fields (Many2one)
            if isinstance(val, models.BaseModel):
                vals[field] = val.id if val else False
            else:
                vals[field] = val

        # Handle Document Fields (only update if a new document was provided)
        doc_fields = ["id_document", "unknown_type_document"]
        for doc in doc_fields:
            if not self[doc]:
                vals.pop(doc, None)
            else:
                vals[doc] = self[doc].id

        # Handle Many2many (learner_master_other_docs_ids)
        if self.learner_master_other_docs_ids:
            vals["learner_master_other_docs_ids"] = [
                (6, 0, self.learner_master_other_docs_ids.ids)
            ]

        # Update the Learner Master record (hr.employee) using sudo
        lnr.sudo().write(vals)

        # Update Audit Record Status
        self.write(
            {
                "status": "approved",
                "action_date": date.today(),
                "action_partner": self.env.user.partner_id.id,
            }
        )

        # Post to Chatter for Audit Trail
        lnr.message_post(
            body=_("Learner information update %s has been approved and applied.")
            % self.reference
        )

        # Send Approval Email
        template = self.env.ref(
            "hwseta_etqe.email_template_learner_update_approve_notification",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

        return True

    def reject_update(self, msg):
        """
        Rejects the update request and logs the reason to chatter.
        """
        self.ensure_one()
        self.write(
            {
                "status": "rejected",
                "action_date": date.today(),
                "action_partner": self.env.user.partner_id.id,
            }
        )

        if self.learner_id:
            body = _(
                "%(ref)s - Update has been rejected with the following comments: \n %(msg)s"
            ) % {"ref": self.reference or "", "msg": msg}
            self.learner_id.message_post(body=body)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    update_ids = fields.One2many(
        "updated.learner", "learner_id", string="Update History"
    )

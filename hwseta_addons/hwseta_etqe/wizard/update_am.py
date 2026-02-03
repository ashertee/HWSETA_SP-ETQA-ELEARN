# -*- coding: utf-8 -*-
import logging
from datetime import date, datetime
import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Standard Odoo 18 logging.
# This allows logs to be controlled via the --log-level server flag.
_logger = logging.getLogger(__name__)


# If you still need the dbg helper for easier typing during migration:
def dbg(msg):
    _logger.info(msg)


class UpdatedAssessorsRejectWiz(models.TransientModel):
    _name = "updated.assessors.reject.wiz"
    _description = "Reject Assessor Update Wizard"

    comment = fields.Text(string="Rejection Comment", required=True)

    # In Odoo 18, defaults are cleaner using the recordset-based context
    update_id = fields.Many2one(
        "updated.assessors",
        string="Update Reference",
        default=lambda self: self.env.context.get("update_id", False),
    )

    def reject_update(self):
        """Logic to reject the update and send notification."""
        self.ensure_one()
        _logger.info(
            "Rejecting update %s with comment: %s", self.update_id.id, self.comment
        )

        if not self.comment:
            raise UserError(_("Please provide a comment for the rejection."))

        if self.update_id:
            # Call rejection logic on parent record
            self.update_id.reject_update(self.comment)

            # Use self.env.ref() - the modern Odoo 18 standard
            template = self.env.ref(
                "hwseta_etqe.email_template_ass_update_reject_notification",
                raise_if_not_found=False,
            )

            if template:
                # Odoo 18 send_mail method expects the record ID to render against
                # Ensure you pass the correct ID (the main update record, not the wizard)
                template.send_mail(self.update_id.id, force_send=True)

        # Returns a client action to close the wizard window
        return {"type": "ir.actions.act_window_close"}


class UpdateAssessor(models.TransientModel):
    _name = "update.assessor"
    _description = "Assessor Profile Update Wizard"

    def _default_assessor(self):
        """Standardized default assessor logic for Odoo 18"""
        user = self.env.user
        # Assuming the relation is defined on res.users
        assessor = user.assessor_moderator_id
        if assessor and assessor.is_assessors:
            return assessor.id

        # Fallback to context
        return self.env.context.get("assessor_id", False)

    # Multi-step wizard page selection
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
        string="Wizard Page",
        default="terms",
    )

    assessor_id = fields.Many2one(
        "hr.employee", string="Assessor", default=_default_assessor
    )
    disclaimer = fields.Boolean(string="Disclaimer Accepted")
    update_disclaimer = fields.Boolean(string="Update Disclaimer Accepted")
    reference = fields.Char(string="Reference")

    # Citizenship Section
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
        [("political_asylum", "Political Asylum"), ("refugee", "Refugee")],
        string="Nationality Type",
    )
    unknown_type_document = fields.Many2one("ir.attachment", string="Type Document")
    nationality_saqa_code = fields.Selection(
        [("sa", "SA")], string="Nationality SAQA Code"
    )

    assessor_moderator_identification_id = fields.Char(
        "R.S.A. Identification No.", size=13
    )
    alternate_id_type = fields.Selection(
        [
            ("saqa_member", "521 - SAQA Member ID"),
            ("passport_number", "527 - Passport Number"),
            ("drivers_license", "529 - Drivers License"),
            ("temporary_id_number", "531 - Temporary ID number"),
            ("none", "533 - None"),
            ("unknown", "535 - Unknown"),
            ("student_number", "537 - Student number"),
            ("work_permit_number", "538 - Work Permit Number"),
            ("employee_number", "539 - Employee Number"),
            ("birth_certificate_number", "540 - Birth Certificate Number"),
            ("hsrc_register_number", " 541 - HSRC Register Number"),
            ("etqe_record_number", "561 - ETQA Record Number"),
            ("refugee_number", "565 - Refugee Number"),
        ],
        string="Alternate ID Type",
    )

    person_birth_date = fields.Date(string="Birth Date")
    gender = fields.Selection([("male", "Male"), ("female", "Female")], string="Gender")
    passport_id = fields.Char(string="Passport No")
    national_id = fields.Char(string="National Id", size=20)
    home_language_code = fields.Many2one("res.lang", string="Home Language Code")

    home_lang_saqa_code = fields.Selection(
        [
            ("eng", "Eng"),
            ("afr", "Afr"),
            ("xho", "Xho"),
            ("set", "Set"),
            ("zul", "Zul"),
            ("sep", "Sep"),
            ("tsh", "Tsh"),
            ("ses", "Ses"),
            ("xit", "Xit"),
            ("swa", "Swa"),
            ("nde", "Nde"),
            ("u", "U"),
            ("oth", "Oth"),
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

    # Contact Info Section
    # Removed track_visibility as it is not used in TransientModels
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

    person_last_name = fields.Char(string="Last Name", size=45)
    person_name = fields.Char(string="First Name", size=50)
    initials = fields.Char(string="Initials")
    cont_number_home = fields.Char(string="Home Number", size=10)
    cont_number_office = fields.Char(string="Office Number", size=10)
    work_phone = fields.Char(string="Work Phone")
    person_fax_number = fields.Char(string="Tele Fax Number ", size=10)
    highest_education = fields.Char(string="Highest Education")
    current_occupation = fields.Char(string="Current Occupation")
    years_in_occupation = fields.Char(string="Years in Occupation")
    person_cell_phone_number = fields.Char(string="Cell Phone Number")
    department = fields.Char(string="Department")
    manager = fields.Char(string="Manager")
    job_title = fields.Char(string="Job Title")

    # Status Section
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

    dissability = fields.Selection([("yes", "Yes"), ("no", "No")], string="Disability")
    disability_status = fields.Selection(
        [
            ("sight", "Sight (even with glasses)"),
            ("hearing", "Hearing (even with h.aid)"),
            ("communication", "Communication (talk/listen)"),
            ("physical", "Physical (move/stand, etc)"),
            ("intellectual", "Intellectual (learn,etc)"),
            ("emotional", "Emotional (behav/psych)"),
            ("multiple", "Multiple"),
            ("disabled", "Disabled but unspecified"),
            ("none", "None"),
        ],
        string="Disability Status",
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

    # Address Section (Physical & Work)
    work_address = fields.Char(string="Work Address")
    work_address2 = fields.Char(string="Work Address 2")
    work_address3 = fields.Char(string="Work Address 3")
    person_suburb = fields.Many2one("res.suburb", string="Suburb")
    work_city = fields.Many2one("res.city", string="City")
    work_province = fields.Many2one("res.country.state", string="Province")
    work_zip = fields.Char(string="Zip Code")
    work_country = fields.Many2one("res.country", string="Country")
    work_municipality = fields.Many2one("res.municipality", string="Municipality")

    # Home Address
    person_home_address_1 = fields.Char(string="Home Address 1", size=50)
    person_home_address_2 = fields.Char(string="Home Address 2", size=50)
    person_home_address_3 = fields.Char(string="Home Address 3", size=50)
    person_home_suburb = fields.Many2one("res.suburb", string="Home Suburb")
    person_home_city = fields.Many2one("res.city", string="Home City")
    physical_municipality = fields.Many2one(
        "res.municipality", string="Physical Municipality"
    )
    person_home_province_code = fields.Many2one(
        "res.country.state", string="Home Province Code"
    )
    country_home = fields.Many2one("res.country", string="Home Country")
    person_home_zip = fields.Char(string="Home Zip")

    same_as_home = fields.Boolean(string="Same As Home Address")

    # Postal Address
    person_postal_address_1 = fields.Char(string="Postal Address 1", size=50)
    person_postal_address_2 = fields.Char(string="Postal Address 2", size=50)
    person_postal_address_3 = fields.Char(string="Postal Address 3", size=50)
    person_postal_suburb = fields.Many2one("res.suburb", string="Postal Suburb")
    person_postal_city = fields.Many2one("res.city", string="Postal City")
    postal_municipality = fields.Many2one(
        "res.municipality", string="Postal Municipality"
    )
    person_postal_province_code = fields.Many2one(
        "res.country.state", string="Postal Province Code"
    )
    person_postal_zip = fields.Char(string="Postal Zip")
    country_postal = fields.Many2one("res.country", string="Postal Country")

    # Documents Section
    id_document = fields.Many2one("ir.attachment", string="ID Document")
    registrationdoc = fields.Many2one("ir.attachment", string="Registration Documents")
    professionalbodydoc = fields.Many2one(
        "ir.attachment", string="Professional Body Document"
    )
    sram_doc = fields.Many2one("ir.attachment", string="Statement Document")
    cv_document = fields.Many2one("ir.attachment", string="CV Document")

    @api.onchange("same_as_home")
    def onchange_sameas_home(self):
        """Copies home address to postal address in Odoo 18."""
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

    @api.onchange("citizen_resident_status_code")
    def onchange_citizenship(self):
        """Syncs identification data from the linked assessor record in Odoo 18."""
        if self.citizen_resident_status_code and self.assessor_id:
            ass = self.assessor_id

            # Use dictionary comprehension or explicit dict to keep the UI snappy
            vals = {
                "national_id": ass.national_id,
                "alternate_id_type": ass.alternate_id_type,
                "passport_id": ass.passport_id,
                "gender": ass.gender,
                "person_birth_date": ass.person_birth_date,
                "home_language_code": (
                    ass.home_language_code.id if ass.home_language_code else False
                ),
            }

            # Logic for South African IDs vs Foreign IDs
            if self.citizen_resident_status_code not in ["unknown", "other"]:
                vals["assessor_moderator_identification_id"] = (
                    ass.assessor_moderator_identification_id
                )

            # Update all fields in one single UI refresh cycle
            self.update(vals)

    @api.onchange("assessor_moderator_identification_id")
    def onchange_id_number(self):
        """Validates South African ID number and extracts metadata."""
        if not self.assessor_moderator_identification_id:
            return

        ident_id = self.assessor_moderator_identification_id
        # Assuming 'checkers' utility is available in the environment
        check = checkers.said_check(ident_id)

        if not check or not check.get("valid"):
            # Clear invalid ID
            self.assessor_moderator_identification_id = False

            # Check specific error types from legacy checker
            err_msg = checkers.old_said_check(ident_id)
            if "Invalid gender" in err_msg:
                raise UserError(_("Invalid Gender!"))
            if "Invalid citizenship status" in err_msg:
                raise UserError(_("Invalid citizenship status!"))

            # Date validation
            day = int(check.get("day", 0))
            month = int(check.get("month", 0))
            year_val = int(check.get("year", 0))

            if not (1 <= day <= 31):
                raise UserError(_("Incorrect Day In Identification Number!"))
            if not (1 <= month <= 12):
                raise UserError(_("Incorrect Month In Identification Number!"))

            # Calculate leap year/days in month
            full_year = 2000 + year_val if year_val < 50 else 1900 + year_val
            last_day = calendar.monthrange(full_year, month)[1]
            if day > last_day:
                raise UserError(
                    _("Incorrect last day of month in identification number!")
                )

            raise UserError(_("Incorrect checksum or invalid ID!"))

        # Extract Gender (Digits 7-10)
        gender_digit = int(ident_id[6:10])
        self.gender = "female" if gender_digit <= 4999 else "male"

        # Extract Citizenship (Digit 11)
        cit_digit = int(ident_id[10:11])
        self.citizen_resident_status_code = "sa" if cit_digit == 0 else "PR"

        # Extract Birth Date
        year_val = int(check["year"])
        month_val = int(check["month"])
        day_val = int(check["day"])

        # Determine century
        century = 2000 if year_val < 50 else 1900
        try:
            self.person_birth_date = date(century + year_val, month_val, day_val)
        except ValueError:
            raise UserError(
                _("Calculated birth date is invalid for the ID number provided.")
            )

    @api.onchange("person_suburb", "person_home_suburb", "person_postal_suburb")
    def onchange_suburb(self):
        """Automatically populates address hierarchy based on suburb selection."""
        _logger.info("Onchange triggered for suburbs")

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
        """Validates that phone numbers are exactly 10 digits."""
        # Define the fields to check in a list for cleaner iteration
        phone_fields = [
            "cont_number_home",
            "cont_number_office",
            "person_fax_number",
            "work_phone",
        ]

        for field in phone_fields:
            val = getattr(self, field)
            if val:
                # Odoo 18 logic: strip whitespace if any, then check
                cleaned_val = val.strip()
                if not cleaned_val.isdigit() or len(cleaned_val) != 10:
                    setattr(
                        self, field, False
                    )  # Using False/None is better than empty string
                    raise UserError(
                        _("Invalid input: '%s' must be exactly 10 digits.")
                        % self._fields[field].string
                    )

    @api.onchange("disclaimer")
    def populate_fields(self):
        """Batch populates wizard fields from the linked Assessor record."""
        if self.assessor_id and self.disclaimer:
            ass = self.assessor_id
            _logger.info("Populating wizard fields for Assessor ID: %s", ass.id)

            # Using update() with a dictionary for modern Odoo 18 performance
            self.update(
                {
                    "person_title": ass.person_title,
                    "national_id": ass.national_id,
                    "alternate_id_type": ass.alternate_id_type,
                    "person_last_name": ass.person_last_name,
                    "person_name": ass.person_name,
                    "home_language_code": ass.home_language_code.id,
                    "initials": ass.initials,
                    "citizen_resident_status_code": ass.citizen_resident_status_code,
                    "cont_number_home": ass.cont_number_home,
                    "cont_number_office": ass.cont_number_office,
                    "work_phone": ass.work_phone,
                    "person_fax_number": ass.person_fax_number,
                    "highest_education": ass.highest_education,
                    "current_occupation": ass.current_occupation,
                    "years_in_occupation": ass.years_in_occupation,
                    "person_cell_phone_number": ass.person_cell_phone_number,
                    "department": ass.department,
                    "job_title": ass.job_title,
                    "manager": ass.manager,
                    "marital": ass.marital,
                    "dissability": ass.dissability,
                    "disability_status": ass.disability_status,
                    "socio_economic_status": ass.socio_economic_status,
                    "equity": ass.equity,
                    "country_id": ass.country_id.id,
                    "work_address": ass.work_address,
                    "work_address2": ass.work_address2,
                    "work_address3": ass.work_address3,
                    "person_suburb": ass.person_suburb.id,
                    "work_city": ass.work_city.id,
                    "work_province": ass.work_province.id,
                    "work_zip": ass.work_zip,
                    "work_country": ass.work_country.id,
                    "work_municipality": ass.work_municipality.id,
                    "person_home_address_1": ass.person_home_address_1,
                    "person_home_address_2": ass.person_home_address_2,
                    "person_home_address_3": ass.person_home_address_3,
                    "person_home_suburb": ass.person_home_suburb.id,
                    "person_home_city": ass.person_home_city.id,
                    "physical_municipality": ass.physical_municipality.id,
                    "person_home_province_code": ass.person_home_province_code.id,
                    "country_home": ass.country_home.id,
                    "person_home_zip": ass.person_home_zip,
                    "same_as_home": ass.same_as_home,
                    "person_postal_address_1": ass.person_postal_address_1,
                    "person_postal_address_2": ass.person_postal_address_2,
                    "person_postal_address_3": ass.person_postal_address_3,
                    "person_postal_suburb": ass.person_postal_suburb.id,
                    "person_postal_city": ass.person_postal_city.id,
                    "postal_municipality": ass.postal_municipality.id,
                    "person_postal_province_code": ass.person_postal_province_code.id,
                    "person_postal_zip": ass.person_postal_zip,
                    "country_postal": (
                        ass.country_postal.id if ass.country_postal else False
                    ),
                }
            )

    def update_record(self):  # Renamed to avoid confusion with ORM update()
        """Finalizes the wizard and creates an update request record."""
        self.ensure_one()
        ass = self.assessor_id

        if not ass:
            raise UserError(_("No assessor found to update."))
        if not self.disclaimer:
            raise UserError(_("You must accept the disclaimer to proceed."))

        # Modern Odoo Mapping Tables
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
        disability_dict = {
            "sight": "1",
            "hearing": "2",
            "communication": "3",
            "physical": "4",
            "intellectual": "5",
            "emotional": "6",
            "multiple": "7",
            "disabled": "9",
            "none": "n",
        }

        # Build the values dictionary for the permanent 'updated.assessors' model
        vals = {
            "status": "submitted",
            "assessor_id": ass.id,
            "update_disclaimer": self.update_disclaimer,
            "disclaimer": self.disclaimer,
            "reference": self.env["ir.sequence"].next_by_code(
                "personal.update.reference"
            ),
            "person_title": self.person_title,
            "person_last_name": self.person_last_name,
            "person_name": self.person_name,
            "name": f"{self.person_name} {self.person_last_name}",
            "person_birth_date": self.person_birth_date,
            "gender": self.gender,
            "citizen_resident_status_code": self.citizen_resident_status_code,
            "assessor_moderator_identification_id": self.assessor_moderator_identification_id,
            "national_id": self.national_id,
            "alternate_id_type": self.alternate_id_type,
            "unknown_type": self.unknown_type,
            "home_language_code": (
                self.home_language_code.id if self.home_language_code else False
            ),
            "initials": self.initials,
            "cont_number_home": self.cont_number_home,
            "cont_number_office": self.cont_number_office,
            "work_phone": self.work_phone,
            "person_fax_number": self.person_fax_number,
            "highest_education": self.highest_education,
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
            "country_id": self.country_id.id if self.country_id else False,
            # --- Address Fields ---
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
        }

        # Handling SAQA specific codes
        if self.home_language_code:
            vals["home_lang_saqa_code"] = lang_dict.get(self.home_language_code.name)
        if self.disability_status:
            vals["disability_status_saqa"] = disability_dict.get(self.disability_status)

        # Document Replacement Helper
        nw_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        def process_doc(new_doc, old_doc, field_name):
            if new_doc:
                vals[field_name] = new_doc.id
                # Track the original document for reference
                vals[f"related_{field_name}"] = old_doc.id if old_doc else False
                if old_doc:
                    # Mark old doc as replaced and link to employee for archive
                    old_doc.sudo().write(
                        {
                            "name": f"replaced_{nw_str}_{old_doc.name}",
                            "res_model": "hr.employee",
                            "res_id": ass.id,
                        }
                    )

        # Execute Document Processing for all defined attachments
        process_doc(self.id_document, ass.id_document, "id_document")
        process_doc(self.registrationdoc, ass.registrationdoc, "registrationdoc")
        process_doc(
            self.professionalbodydoc, ass.professionalbodydoc, "professionalbodydoc"
        )
        process_doc(self.sram_doc, ass.sram_doc, "sram_doc")
        process_doc(self.cv_document, ass.cv_document, "cv_document")
        process_doc(
            self.unknown_type_document,
            ass.unknown_type_document,
            "unknown_type_document",
        )

        # Create the Record and Notify
        ud = self.env["updated.assessors"].create(vals)
        ass.message_post(
            body=_("Information update request has been submitted. Reference: %s")
            % vals["reference"]
        )

        # Trigger Email
        template = self.env.ref(
            "hwseta_etqe.email_template_ass_update_submit_notification",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(ud.id, force_send=True)

        return {"type": "ir.actions.act_window_close"}


class UpdatedAssessors(models.Model):
    _name = "updated.assessors"
    _description = "Assessor Information Update Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]  # Added for chatter support
    _order = "create_date desc"

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

    msg = fields.Text(string="Internal Comments")
    assessor_id = fields.Many2one("hr.employee", string="Assessor", required=True)
    reference = fields.Char(string="Update Reference", readonly=True)
    action_date = fields.Date(string="Approval/Rejection Date")
    action_partner = fields.Many2one("res.partner", string="Action Performed By")

    # --- New Values Section ---
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
    person_last_name = fields.Char(string="Last Name")
    person_name = fields.Char(string="First Name")
    name = fields.Char(string="Full Name")
    initials = fields.Char(string="Initials")

    # Contact Details
    work_phone = fields.Char(string="Work Phone")
    person_cell_phone_number = fields.Char(string="Cell Phone")
    cont_number_home = fields.Char(string="Home Number")
    cont_number_office = fields.Char(string="Office Number")
    person_fax_number = fields.Char(string="Fax Number")

    # Occupation & Education
    highest_education = fields.Char(string="Highest Education")
    current_occupation = fields.Char(string="Current Occupation")
    years_in_occupation = fields.Char(string="Years in Occupation")
    department = fields.Char(string="Department")
    job_title = fields.Char(string="Job Title")
    manager = fields.Char(string="Manager")

    # Legal & Demographic
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

    dissability = fields.Selection([("yes", "Yes"), ("no", "No")], string="Disability")
    disability_status = fields.Selection(
        [
            ("sight", "Sight (even with glasses)"),
            ("hearing", "Hearing (even with h.aid)"),
            ("communication", "Communication (talk/listen)"),
            ("physical", "Physical (move/stand, etc)"),
            ("intellectual", "Intellectual (learn,etc)"),
            ("emotional", "Emotional (behav/psych)"),
            ("multiple", "Multiple"),
            ("disabled", "Disabled but unspecified"),
            ("none", "None"),
        ],
        string="Disability Status",
    )

    # SAQA Mappings
    socio_economic_status = fields.Selection(
        [
            ("employed", "Employed"),
            ("unemployed", "Unemployed"),
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

    # Address Data (Physical, Home, Postal)
    # [Fields remain consistent with your original structure, Many2ones used for relation integrity]
    work_zip = fields.Char(string="Zip Code")
    person_suburb = fields.Many2one("res.suburb", string="Suburb")
    work_city = fields.Many2one("res.city", string="City")
    work_province = fields.Many2one("res.country.state", string="Province")
    work_country = fields.Many2one("res.country", string="Country")

    # Document Section
    id_document = fields.Many2one("ir.attachment", string="ID Document")
    cv_document = fields.Many2one("ir.attachment", string="CV Document")
    registrationdoc = fields.Many2one("ir.attachment", string="Registration Documents")

    # --- Related (Old) Values Section ---
    # These store the values before the update for comparison
    related_person_last_name = fields.Char(string="Old Last Name", readonly=True)
    related_person_name = fields.Char(string="Old First Name", readonly=True)
    related_work_phone = fields.Char(string="Old Work Phone", readonly=True)
    related_id_document = fields.Many2one(
        "ir.attachment", string="Old ID Document", readonly=True
    )

    # Personal Info
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
    related_initials = fields.Char(string="Old Initials", readonly=True)
    related_job_title = fields.Char(string="Old Job Title", readonly=True)

    # Status Info
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
        [("yes", "Yes"), ("no", "No")], string="Old Disability", readonly=True
    )
    related_disability_status = fields.Selection(
        [
            ("sight", "Sight (even with glasses)"),
            ("hearing", "Hearing (even with h.aid)"),
            ("communication", "Communication (talk/listen)"),
            ("physical", "Physical (move/stand, etc)"),
            ("intellectual", "Intellectual (learn,etc)"),
            ("emotional", "Emotional (behav/psych)"),
            ("multiple", "Multiple"),
            ("disabled", "Disabled but unspecified"),
            ("none", "None"),
        ],
        string="Old Disability Status",
        readonly=True,
    )
    related_socio_economic_status = fields.Selection(
        [
            ("employed", "Employed"),
            ("unemployed", "Unemployed"),
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
        readonly=True,
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
        readonly=True,
    )
    related_equity_saqa_code = fields.Char(string="Old Equity SAQA Code", readonly=True)

    # Citizenship Info
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
        "res.country", string="Old Country", readonly=True
    )
    related_unknown_type = fields.Selection(
        [("political_asylum", "Political Asylum"), ("refugee", "Refugee")],
        string="Old Nationality Type",
        readonly=True,
    )
    related_assessor_moderator_identification_id = fields.Char(
        string="Old RSA ID No.", readonly=True
    )
    related_passport_id = fields.Char(string="Old Passport No", readonly=True)
    related_national_id = fields.Char(string="Old National Id", readonly=True)
    related_gender = fields.Selection(
        [("male", "Male"), ("female", "Female")], string="Old Gender", readonly=True
    )
    related_person_birth_date = fields.Date(string="Old Birth Date", readonly=True)
    related_home_language_code = fields.Many2one(
        "res.lang", string="Old Home Language Code", readonly=True
    )

    # Work Address
    related_work_address = fields.Char(string="Old Work Address", readonly=True)
    related_work_address2 = fields.Char(string="Old Work Address 2", readonly=True)
    related_person_suburb = fields.Many2one(
        "res.suburb", string="Old Suburb", readonly=True
    )
    related_work_city = fields.Many2one("res.city", string="Old City", readonly=True)
    related_work_province = fields.Many2one(
        "res.country.state", string="Old Province", readonly=True
    )
    related_work_zip = fields.Char(string="Old Zip Code", readonly=True)
    related_work_country = fields.Many2one(
        "res.country", string="Old Country", readonly=True
    )

    # Home Address
    related_person_home_address_1 = fields.Char(
        string="Old Home Address 1", readonly=True
    )
    related_person_home_suburb = fields.Many2one(
        "res.suburb", string="Old Home Suburb", readonly=True
    )
    related_person_home_city = fields.Many2one(
        "res.city", string="Old Home City", readonly=True
    )
    related_person_home_province_code = fields.Many2one(
        "res.country.state", string="Old Home Province Code", readonly=True
    )
    related_person_home_zip = fields.Char(string="Old Home Zip", readonly=True)
    related_country_home = fields.Many2one(
        "res.country", string="Old Home Country", readonly=True
    )

    # Postal Address
    related_same_as_home = fields.Boolean(
        string="Old Same As Home Address", readonly=True
    )
    related_person_postal_address_1 = fields.Char(
        string="Old Postal Address 1", readonly=True
    )
    related_person_postal_suburb = fields.Many2one(
        "res.suburb", string="Old Postal Suburb", readonly=True
    )
    related_person_postal_city = fields.Many2one(
        "res.city", string="Old Postal City", readonly=True
    )
    related_person_postal_province_code = fields.Many2one(
        "res.country.state", string="Old Postal Province Code", readonly=True
    )
    related_person_postal_zip = fields.Char(string="Old Postal Zip", readonly=True)

    # Documents
    related_registrationdoc = fields.Many2one(
        "ir.attachment", string="Old Registration Documents", readonly=True
    )
    related_professionalbodydoc = fields.Many2one(
        "ir.attachment", string="Old Professional Body Document", readonly=True
    )
    related_sram_doc = fields.Many2one(
        "ir.attachment", string="Old Statement Document", readonly=True
    )
    related_cv_document = fields.Many2one(
        "ir.attachment", string="Old CV Document", readonly=True
    )

    # Additional fields needed by views
    equity_saqa_code = fields.Char(string="Equity SAQA Code", readonly=True)
    gender = fields.Selection([("male", "Male"), ("female", "Female")], string="Gender")
    person_birth_date = fields.Date(string="Birth Date")
    home_language_code = fields.Many2one("res.lang", string="Home Language Code")
    work_address = fields.Char(string="Work Address")
    work_address2 = fields.Char(string="Work Address 2")
    person_home_address_1 = fields.Char(string="Home Address 1")
    person_home_suburb = fields.Many2one("res.suburb", string="Home Suburb")
    person_home_city = fields.Many2one("res.city", string="Home City")
    person_home_province_code = fields.Many2one(
        "res.country.state", string="Home Province Code"
    )
    country_home = fields.Many2one("res.country", string="Home Country")
    person_home_zip = fields.Char(string="Home Zip")
    same_as_home = fields.Boolean(string="Same As Home Address")
    person_postal_address_1 = fields.Char(string="Postal Address 1")
    person_postal_suburb = fields.Many2one("res.suburb", string="Postal Suburb")
    person_postal_city = fields.Many2one("res.city", string="Postal City")
    person_postal_province_code = fields.Many2one(
        "res.country.state", string="Postal Province Code"
    )
    person_postal_zip = fields.Char(string="Postal Zip")
    country_postal = fields.Many2one("res.country", string="Postal Country")
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
        [("political_asylum", "Political Asylum"), ("refugee", "Refugee")],
        string="Nationality Type",
    )
    assessor_moderator_identification_id = fields.Char("R.S.A. Identification No.")
    passport_id = fields.Char(string="Passport No")
    national_id = fields.Char(string="National Id")
    professionalbodydoc = fields.Many2one(
        "ir.attachment", string="Professional Body Document"
    )
    sram_doc = fields.Many2one("ir.attachment", string="Statement Document")
    create_date = fields.Datetime(string="Created On", readonly=True)

    def approve_update(self):
        """Processes and applies the approved changes to the hr.employee record."""
        self.ensure_one()

        # Fields to skip (technical/meta fields that shouldn't overwrite employee data)
        skip_fields = [
            "id",
            "create_uid",
            "create_date",
            "write_uid",
            "write_date",
            "display_name",
            "status",
            "msg",
            "assessor_id",
            "disclaimer",
            "update_disclaimer",
            "reference",
            "action_date",
            "action_partner",
        ]

        # Identify all 'related_' fields so we can skip them too
        related_fields = [f for f in self._fields if f.startswith("related_")]
        skip_fields.extend(related_fields)

        # Get all valid field names for the employee update
        field_list = [f for f in self._fields if f not in skip_fields]

        # Standard Odoo 18 logic: Use read() then clean Many2one tuples
        vals = self.read(field_list)[0]

        # Process values: convert (id, name) tuples to just IDs and remove empty entries
        clean_vals = {}
        for key, value in vals.items():
            if isinstance(value, tuple):
                clean_vals[key] = value[0]
            elif value:
                clean_vals[key] = value

        # Update Employee
        if self.assessor_id:
            self.assessor_id.write(clean_vals)

            # Post to chatter using standard Odoo 18 message_post
            self.assessor_id.message_post(
                body=_("Personal Information update request (%s) has been approved.")
                % self.reference,
                subtype_xmlid="mail.mt_comment",
            )

        # Update request status
        self.write(
            {
                "status": "approved",
                "action_date": date.today(),
                "action_partner": self.env.user.partner_id.id,
            }
        )

        # Trigger Notification Email
        template = self.env.ref(
            "hwseta_etqe.email_template_ass_update_approve_notification",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def reject_update(self, msg):
        """Rejects the update request with feedback."""
        self.ensure_one()
        self.write(
            {
                "status": "rejected",
                "action_date": date.today(),
                "action_partner": self.env.user.partner_id.id,
                "msg": msg,
            }
        )

        if self.assessor_id:
            body = _("Update request %s rejected. Comments: %s") % (self.reference, msg)
            self.assessor_id.message_post(body=body)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ass_mod_update_ids = fields.One2many(
        "updated.assessors", "assessor_id", string="Update History"
    )

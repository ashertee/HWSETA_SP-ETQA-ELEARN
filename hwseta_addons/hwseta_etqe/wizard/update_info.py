from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class UpdateInfo(models.TransientModel):
    _name = "update.info"
    _description = "Partner Information Update Selection"

    partner_type = fields.Selection(
        [
            ("provider", "Provider"),
            ("moderator", "Moderator"),
            ("assessor", "Assessor"),
        ],
        string="Update Type",
        required=True,
    )

    def _default_provider_id(self):
        """Standardized Odoo 18 default logic."""
        user = self.env.user
        partner = user.partner_id

        # Checking custom 'internal_external_users' field from your specific module logic
        if (
            hasattr(user, "internal_external_users")
            and user.internal_external_users == "Internal"
        ):
            # Return a search recordset (limited to 1 or filtered in view)
            return (
                self.env["res.partner"]
                .search(
                    [
                        ("is_active_provider", "=", True),
                        ("active", "=", True),
                        ("provider_accreditation_num", "!=", False),
                    ],
                    limit=1,
                )
                .id
            )
        elif partner.provider:
            return partner.id
        else:
            raise UserError(_("You do not have access to this document."))

    def select_partner(self):
        """
        Processes selection and redirects to the specific update wizard.
        """
        self.ensure_one()

        if self.partner_type == "provider":
            view = self.env.ref(
                "hwseta_etqe.update_provider_info_form", raise_if_not_found=False
            )

            # Odoo 18: Actions are returned as dictionaries
            return {
                "type": "ir.actions.act_window",
                "name": _("Update Provider Information"),
                "res_model": "update.provider",
                "view_mode": "form",
                "view_id": view.id if view else False,
                "target": "current",
                "context": self.env.context,
            }

        # Placeholder for Moderator/Assessor logic if needed
        return {"type": "ir.actions.act_window_close"}


class UpdatedProvidersRejectWiz(models.TransientModel):
    _name = "updated.providers.reject.wiz"
    _description = "Provider Update Rejection Wizard"

    comment = fields.Text(string="Rejection Reason", required=True)
    update_id = fields.Many2one("updated.providers", string="Related Update")

    def reject_update(self):
        """Finalizes rejection and notifies the provider."""
        self.ensure_one()

        if self.update_id:
            # Audit trail log
            _logger.info(
                "Rejecting Provider Update %s: %s", self.update_id.id, self.comment
            )

            # Execute logic on persistence model
            self.update_id.reject_update(self.comment)

            # Email Notification
            template = self.env.ref(
                "hwseta_etqe.email_template_prov_update_reject_notification",
                raise_if_not_found=False,
            )
            if template:
                # In Odoo 18, we pass the ID of the record the template should use for rendering
                template.send_mail(self.update_id.id, force_send=True)

        return {"type": "ir.actions.act_window_close"}


class UpdateProvider(models.TransientModel):
    _name = "update.provider"
    _description = "Provider Information Update Wizard"

    def generate_msg(self, partner):
        """Standardized HTML message generation using f-strings and False-safe handling."""
        msg = []
        # Use a list and join for better memory performance in 18,000+ line projects
        msg.append(f"<p>Phone: {partner.phone or ''}</p>")
        msg.append(f"<p>Mobile: {partner.mobile or ''}</p>")
        msg.append(f"<p>Fax: {partner.fax or ''}</p>")
        msg.append(f"<p>Website: {partner.website or ''}</p>")

        msg.append("<p>---Work Address---</p>")
        msg.append(f"<p>Street: {partner.street or ''}</p>")
        msg.append(f"<p>Street2: {partner.street2 or ''}</p>")
        msg.append(f"<p>Suburb: {partner.suburb.name or ''}</p>")
        msg.append(f"<p>Province: {partner.state_id.name or ''}</p>")
        msg.append(f"<p>Zip: {partner.zip or ''}</p>")

        msg.append("<p>---Physical Address---</p>")
        msg.append(f"<p>Address 1: {partner.physical_address_1 or ''}</p>")
        msg.append(f"<p>City: {partner.city_physical.name or ''}</p>")
        msg.append(f"<p>Province Code: {partner.province_code_physical.name or ''}</p>")

        msg.append("<p>---Postal Address---</p>")
        msg.append(f"<p>Postal 1: {partner.postal_address_1 or ''}</p>")
        msg.append(f"<p>City: {partner.city_postal.name or ''}</p>")

        msg.append("<p>---Business Info---</p>")
        msg.append(f"<p>Reg No: {partner.txtCompanyRegNo or ''}</p>")
        msg.append(f"<p>VAT No: {partner.txtVATRegNo or ''}</p>")
        msg.append(f"<p>Focus: {partner.cboProviderFocus.name or ''}</p>")

        return "".join(msg)

    def _default_provider(self):
        partner = self.env.user.partner_id
        if partner.provider:
            return partner.id
        return self.env.context.get("provider_id", False)

    # --- Navigation & Reference ---
    page = fields.Selection(
        [
            ("terms", "Terms & Conditions"),
            ("contact", "Contact"),
            ("address", "General Address"),
            ("personal_addr", "Personal Address"),
            ("postal_addr", "Postal Address"),
            ("business_info", "Business Info"),
            ("business_docs", "Business Documents"),
            ("admin", "Internal Administration"),
            ("disclaimer", "Disclaimer"),
        ],
        default="terms",
        string="Wizard Step",
    )

    provider_id = fields.Many2one(
        "res.partner", string="Provider", default=_default_provider
    )
    disclaimer = fields.Boolean(string="Accept Terms")
    update_disclaimer = fields.Boolean(string="Accept POPIA")
    reference = fields.Char(string="Reference", readonly=True)

    # --- Contact Details ---
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    fax = fields.Char(string="Fax")
    website = fields.Char(string="Website")

    # --- General/Work Address ---
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    street3 = fields.Char(string="Street 3")
    suburb = fields.Many2one("res.suburb", string="Suburb")
    city = fields.Many2one("res.city", string="City")
    state_id = fields.Many2one("res.country.state", string="Province")
    zip = fields.Char(string="Zip")
    country_id = fields.Many2one("res.country", string="Country")

    # --- Physical Address ---
    physical_address_1 = fields.Char(string="Physical Address 1")
    physical_address_2 = fields.Char(string="Physical Address 2")
    physical_address_3 = fields.Char(string="Physical Address 3")
    provider_physical_suburb = fields.Many2one("res.suburb", string="Physical Suburb")
    city_physical = fields.Many2one("res.city", string="Physical City")
    province_code_physical = fields.Many2one(
        "res.country.state", string="Physical Province"
    )
    zip_physical = fields.Char(string="Physical Zip")
    country_code_physical = fields.Many2one("res.country", string="Physical Country")

    # --- Postal Address ---
    postal_address_1 = fields.Char(string="Postal Address 1")
    postal_address_2 = fields.Char(string="Postal Address 2")
    postal_address_3 = fields.Char(string="Postal Address 3")
    provider_postal_suburb = fields.Many2one("res.suburb", string="Postal Suburb")
    city_postal = fields.Many2one("res.city", string="Postal City")
    province_code_postal = fields.Many2one(
        "res.country.state", string="Postal Province"
    )
    zip_postal = fields.Char(string="Postal Zip")
    country_code_postal = fields.Many2one("res.country", string="Postal Country")

    # --- Business Info ---
    txtCompanyRegNo = fields.Char(string="Company Registration Number")
    txtVATRegNo = fields.Char(string="VAT Number")
    cboProviderFocus = fields.Many2one(
        "hwseta.provider.focus.master", string="Provider Focus"
    )
    txtNumYearsCurrentBusiness = fields.Selection(
        [
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("10+", "10+"),
        ],
        string="Years in Business",
    )
    txtNumStaffMembers = fields.Char(string="Number of Staff")

    # --- Attachments ---
    cipro_documents = fields.Many2one("ir.attachment", string="Cipro Documents")
    tax_clearance = fields.Many2one("ir.attachment", string="Tax Clearance")
    director_cv = fields.Many2one("ir.attachment", string="Director C.V")
    certified_copies_of_qualifications = fields.Many2one(
        "ir.attachment", string="Certified Qualifications"
    )
    professional_body_registration = fields.Many2one(
        "ir.attachment", string="Professional Body Registration"
    )
    workplace_agreement = fields.Many2one("ir.attachment", string="Workplace Agreement")
    business_residence_proof = fields.Many2one(
        "ir.attachment", string="Visa/Residence Proof"
    )
    provider_learning_material = fields.Many2one(
        "ir.attachment", string="Learning Programme Report"
    )
    skills_programme_registration_letter = fields.Many2one(
        "ir.attachment", string="Skills Reg Letter"
    )
    company_profile_and_organogram = fields.Many2one(
        "ir.attachment", string="Profile & Organogram"
    )
    quality_management_system = fields.Many2one("ir.attachment", string="QMS")
    lease_agreement_document = fields.Many2one("ir.attachment", string="Lease Document")

    # --- Internal Admin ---
    provider_type_id = fields.Char(
        string="Provider Type", help="NLRD classification: 2, 3, 4, 5, or 500"
    )
    provider_class_Id = fields.Char(string="Provider Class")
    provider_start_date = fields.Date(string="Start Date")
    provider_end_date = fields.Date(string="End Date")
    name = fields.Char(string="Provider Name")
    related_name = fields.Char(string="Current Master Name", readonly=True)
    name_change = fields.Boolean(string="Require Name Change")

    @api.onchange("provider_physical_suburb", "suburb", "provider_postal_suburb")
    def onchange_suburb(self):
        """Syncs address fields based on the selected suburb."""
        # Physical Address Sync
        if self.provider_physical_suburb:
            s = self.provider_physical_suburb
            self.update(
                {
                    "zip_physical": s.postal_code,
                    "city_physical": s.city_id.id,
                    "province_code_physical": s.province_id.id,
                    "country_code_physical": s.country_id.id,
                }
            )

        # Work Address Sync
        if self.suburb:
            s = self.suburb
            self.update(
                {
                    "zip": s.postal_code,
                    "city": s.city_id.id,
                    "state_id": s.province_id.id,
                    "country_id": s.country_id.id,
                }
            )

        # Postal Address Sync
        if self.provider_postal_suburb:
            s = self.provider_postal_suburb
            self.update(
                {
                    "zip_postal": s.postal_code,
                    "city_postal": s.city_id.id,
                    "province_code_postal": s.province_id.id,
                    "country_code_postal": s.country_id.id,
                }
            )

    @api.onchange("phone", "mobile", "fax")
    def onchange_validate_number(self):
        """Validates South African 10-digit number format."""

        # Helper to validate 10 digit strings
        def is_invalid(val):
            return val and (not val.isdigit() or len(val) != 10)

        if is_invalid(self.phone):
            self.phone = (
                False  # Odoo 18 prefers False over empty string for Char fields
            )
            return {
                "warning": {
                    "title": _("Invalid Phone"),
                    "message": _("Please enter a 10-digit Phone number."),
                }
            }

        if is_invalid(self.mobile):
            self.mobile = False
            return {
                "warning": {
                    "title": _("Invalid Mobile"),
                    "message": _("Please enter a 10-digit Mobile number."),
                }
            }

        if is_invalid(self.fax):
            self.fax = False
            return {
                "warning": {
                    "title": _("Invalid Fax"),
                    "message": _("Please enter a 10-digit Fax number."),
                }
            }

    @api.onchange("disclaimer")
    def populate_fields(self):
        """Mass populates wizard from the Master Provider record."""
        if self.provider_id and self.disclaimer:
            p = self.provider_id
            # Using self.update() is best practice in Odoo 18 to trigger
            # a single re-render of the web client form.
            self.update(
                {
                    "phone": p.phone,
                    "mobile": p.mobile,
                    "fax": p.fax,
                    "website": p.website,
                    "street": p.street,
                    "street2": p.street2,
                    "street3": p.street3,
                    "suburb": p.suburb.id,
                    "city": p.city.id,
                    "state_id": p.state_id.id,
                    "zip": p.zip,
                    "country_id": p.country_id.id,
                    "physical_address_1": p.physical_address_1,
                    "physical_address_2": p.physical_address_2,
                    "physical_address_3": p.physical_address_3,
                    "provider_physical_suburb": p.provider_physical_suburb.id,
                    "city_physical": p.city_physical.id,
                    "province_code_physical": p.province_code_physical.id,
                    "zip_physical": p.zip_physical,
                    "country_code_physical": p.country_code_physical.id,
                    "postal_address_1": p.postal_address_1,
                    "postal_address_2": p.postal_address_2,
                    "postal_address_3": p.postal_address_3,
                    "provider_postal_suburb": p.provider_postal_suburb.id,
                    "city_postal": p.city_postal.id,
                    "province_code_postal": p.province_code_postal.id,
                    "zip_postal": p.zip_postal,
                    "country_code_postal": p.country_code_postal.id,
                    "txtCompanyRegNo": p.txtCompanyRegNo,
                    "txtVATRegNo": p.txtVATRegNo,
                    "cboProviderFocus": p.cboProviderFocus.id,
                    "txtNumYearsCurrentBusiness": p.txtNumYearsCurrentBusiness,
                    "txtNumStaffMembers": p.txtNumStaffMembers,
                    "provider_type_id": p.provider_type_id,
                    "provider_class_Id": p.provider_class_Id,
                    "provider_start_date": p.provider_start_date,
                    "provider_end_date": p.provider_end_date,
                }
            )


class UpdateProviderWizard(models.TransientModel):
    _inherit = "update.provider"

    def action_submit_update(self):  # Renamed to avoid ORM update() conflict
        """
        Processes the wizard and creates a persistent 'updated.providers' record.
        Includes a side-by-side snapshot of Old vs New data for administrator review.
        """
        self.ensure_one()
        prov = self.provider_id

        if not prov:
            raise UserError(_("No provider linked to this update request."))
        if not self.disclaimer:
            raise UserError(_("You must accept the terms and conditions to proceed."))

        # Fetch sequence reference
        sequence_number = self.env["ir.sequence"].next_by_code(
            "provider.update.reference"
        ) or _("New")

        # Build basic values from Wizard input
        vals = {
            "status": "submitted",
            "name": self.name,
            "provider_id": prov.id,
            "update_disclaimer": self.update_disclaimer,
            "popi_update_disclaimer": self.update_disclaimer,
            "disclaimer": self.disclaimer,
            "reference": sequence_number,
            "phone": self.phone,
            "mobile": self.mobile,
            "fax": self.fax,
            "website": self.website,
            "street": self.street,
            "street2": self.street2,
            "street3": self.street3,
            "suburb": self.suburb.id if self.suburb else False,
            "city": self.city.id if self.city else False,
            "state_id": self.state_id.id if self.state_id else False,
            "zip": self.zip,
            "country_id": self.country_id.id if self.country_id else False,
            "physical_address_1": self.physical_address_1,
            "physical_address_2": self.physical_address_2,
            "physical_address_3": self.physical_address_3,
            "provider_physical_suburb": (
                self.provider_physical_suburb.id
                if self.provider_physical_suburb
                else False
            ),
            "city_physical": self.city_physical.id if self.city_physical else False,
            "province_code_physical": (
                self.province_code_physical.id if self.province_code_physical else False
            ),
            "zip_physical": self.zip_physical,
            "country_code_physical": (
                self.country_code_physical.id if self.country_code_physical else False
            ),
            "postal_address_1": self.postal_address_1,
            "postal_address_2": self.postal_address_2,
            "postal_address_3": self.postal_address_3,
            "provider_postal_suburb": (
                self.provider_postal_suburb.id if self.provider_postal_suburb else False
            ),
            "city_postal": self.city_postal.id if self.city_postal else False,
            "province_code_postal": (
                self.province_code_postal.id if self.province_code_postal else False
            ),
            "zip_postal": self.zip_postal,
            "country_code_postal": (
                self.country_code_postal.id if self.country_code_postal else False
            ),
            "txtCompanyRegNo": self.txtCompanyRegNo,
            "txtVATRegNo": self.txtVATRegNo,
            "cboProviderFocus": (
                self.cboProviderFocus.id if self.cboProviderFocus else False
            ),
            "txtNumYearsCurrentBusiness": self.txtNumYearsCurrentBusiness,
            "txtNumStaffMembers": self.txtNumStaffMembers,
            "provider_type_id": self.provider_type_id or prov.provider_type_id,
            "provider_class_Id": self.provider_class_Id or prov.provider_class_Id,
            "provider_start_date": self.provider_start_date or prov.provider_start_date,
            "provider_end_date": self.provider_end_date or prov.provider_end_date,
            # --- "Related" Snapshot (Current Partner Data) ---
            "related_name": prov.name,
            "related_phone": prov.phone,
            "related_mobile": prov.mobile,
            "related_fax": prov.fax,
            "related_website": prov.website,
            "related_street": prov.street,
            "related_suburb": prov.suburb.id if prov.suburb else False,
            "related_city": prov.city.id if prov.city else False,
            "related_state_id": prov.state_id.id if prov.state_id else False,
            "related_zip": prov.zip,
            "related_country_id": prov.country_id.id if prov.country_id else False,
            # Related Physical Address
            "related_physical_address_1": prov.physical_address_1,
            "related_city_physical": (
                prov.city_physical.id if prov.city_physical else False
            ),
            # Related Document fields
            "related_txtCompanyRegNo": prov.txtCompanyRegNo,
            "related_cipro_documents": (
                prov.cipro_documents.id if prov.cipro_documents else False
            ),
            "related_tax_clearance": (
                prov.tax_clearance.id if prov.tax_clearance else False
            ),
            "related_director_cv": prov.director_cv.id if prov.director_cv else False,
            "related_quality_management_system": (
                prov.quality_management_system.id
                if prov.quality_management_system
                else False
            ),
            # Related Admin Fields
            "related_provider_type_id": prov.provider_type_id,
            "related_provider_class_Id": prov.provider_class_Id,
            "related_provider_start_date": prov.provider_start_date,
        }

        # Document Snapshot Logic
        nw_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_fields = [
            "cipro_documents",
            "tax_clearance",
            "director_cv",
            "certified_copies_of_qualifications",
            "professional_body_registration",
            "workplace_agreement",
            "business_residence_proof",
            "provider_learning_material",
            "skills_programme_registration_letter",
            "company_profile_and_organogram",
            "quality_management_system",
            "lease_agreement_document",
        ]

        for field in doc_fields:
            new_doc = getattr(self, field)
            old_doc = getattr(prov, field)
            if new_doc:
                vals.update(
                    {
                        field: new_doc.id,
                        f"related_{field}": old_doc.id if old_doc else False,
                    }
                )
                # Archive the old document in the Partner chatter context
                if old_doc:
                    old_doc.sudo().write(
                        {
                            "name": f"replaced_{nw_str}_{old_doc.name}",
                            "res_id": prov.id,
                            "res_model": "res.partner",
                        }
                    )

        # Create persistent request and notify
        ud = self.env["updated.providers"].create(vals)
        prov.message_post(
            body=_("Update request %s submitted for approval.") % sequence_number
        )

        # Trigger email notification using Odoo 18 standard env.ref
        template = self.env.ref(
            "hwseta_etqe.email_template_prov_update_submit_notification",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(ud.id, force_send=True)

        return {"type": "ir.actions.act_window_close"}


class UpdatedProviders(models.Model):
    _name = "updated.providers"
    _description = "Provider Information Update Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # --- Workflow & Audit ---
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
    provider_id = fields.Many2one(
        "res.partner", string="Provider", required=True, tracking=True
    )
    reference = fields.Char(string="Update Reference", readonly=True, copy=False)

    action_date = fields.Date(string="Processed Date", readonly=True)
    action_partner = fields.Many2one(
        "res.partner", string="Processed By", readonly=True
    )

    disclaimer = fields.Boolean(string="Terms Accepted")
    update_disclaimer = fields.Boolean(string="POPIA Accepted")
    name_change = fields.Boolean(string="Require Name Change")

    # --- New Values Section ---
    name = fields.Char(string="Provider Name")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    fax = fields.Char(string="Fax")
    website = fields.Char(string="Website")

    # Work Address
    street = fields.Char()
    street2 = fields.Char()
    street3 = fields.Char()
    suburb = fields.Many2one("res.suburb")
    city = fields.Many2one("res.city")
    state_id = fields.Many2one("res.country.state", string="Province")
    zip = fields.Char()
    country_id = fields.Many2one("res.country")

    # Physical Address
    physical_address_1 = fields.Char()
    physical_address_2 = fields.Char()
    physical_address_3 = fields.Char()
    provider_physical_suburb = fields.Many2one("res.suburb")
    city_physical = fields.Many2one("res.city")
    province_code_physical = fields.Many2one("res.country.state")
    zip_physical = fields.Char()
    country_code_physical = fields.Many2one("res.country")

    # Postal Address
    postal_address_1 = fields.Char()
    postal_address_2 = fields.Char()
    postal_address_3 = fields.Char()
    provider_postal_suburb = fields.Many2one("res.suburb")
    city_postal = fields.Many2one("res.city")
    province_code_postal = fields.Many2one("res.country.state")
    zip_postal = fields.Char()
    country_code_postal = fields.Many2one("res.country")

    # Business Info
    txtCompanyRegNo = fields.Char(string="Company Registration Number")
    txtVATRegNo = fields.Char(string="VAT Number")
    cboProviderFocus = fields.Many2one(
        "hwseta.provider.focus.master", string="Provider Focus"
    )
    txtNumYearsCurrentBusiness = fields.Selection(
        [(str(i), str(i)) for i in range(11)] + [("10+", "10+")],
        string="Years in Business",
    )
    txtNumStaffMembers = fields.Char(string="Number of Staff")

    # Attachments (New)
    cipro_documents = fields.Many2one("ir.attachment", string="Cipro Documents")
    tax_clearance = fields.Many2one("ir.attachment", string="Tax Clearance")
    director_cv = fields.Many2one("ir.attachment", string="Director C.V")
    certified_copies_of_qualifications = fields.Many2one(
        "ir.attachment", string="Qualifications"
    )
    professional_body_registration = fields.Many2one(
        "ir.attachment", string="Professional Body"
    )
    workplace_agreement = fields.Many2one("ir.attachment", string="Workplace Agreement")
    business_residence_proof = fields.Many2one(
        "ir.attachment", string="Visa/Residence Proof"
    )
    provider_learning_material = fields.Many2one(
        "ir.attachment", string="Learning Programme Report"
    )
    skills_programme_registration_letter = fields.Many2one(
        "ir.attachment", string="Skills Reg Letter"
    )
    company_profile_and_organogram = fields.Many2one(
        "ir.attachment", string="Profile & Organogram"
    )
    quality_management_system = fields.Many2one("ir.attachment", string="QMS")
    lease_agreement_document = fields.Many2one("ir.attachment", string="Lease Document")

    # Admin Fields
    provider_type_id = fields.Char(string="Provider Type")
    provider_class_Id = fields.Char(string="Provider Class")
    provider_start_date = fields.Date(string="Start Date")
    provider_end_date = fields.Date(string="End Date")

    # --- Related (Old) Values for History Comparison ---
    # These store the "Before" state for the side-by-side audit view
    related_name = fields.Char(string="Old Provider Name", readonly=True)
    related_phone = fields.Char(string="Old Phone", readonly=True)
    related_mobile = fields.Char(string="Old Mobile", readonly=True)
    related_fax = fields.Char(string="Old Fax", readonly=True)
    related_website = fields.Char(string="Old Website", readonly=True)
    related_street = fields.Char(readonly=True)
    related_suburb = fields.Many2one("res.suburb", readonly=True)
    related_city = fields.Many2one("res.city", readonly=True)
    related_state_id = fields.Many2one("res.country.state", readonly=True)
    related_zip = fields.Char(readonly=True)
    related_country_id = fields.Many2one("res.country", readonly=True)

    # Related Physical Address
    related_physical_address_1 = fields.Char(
        string="Old Physical Address 1", readonly=True
    )
    related_city_physical = fields.Many2one(
        "res.city", string="Old Physical City", readonly=True
    )

    # Related Document fields
    related_txtCompanyRegNo = fields.Char(readonly=True)
    related_cipro_documents = fields.Many2one("ir.attachment", readonly=True)
    related_tax_clearance = fields.Many2one("ir.attachment", readonly=True)
    related_director_cv = fields.Many2one(
        "ir.attachment", string="Old Director CV", readonly=True
    )
    related_quality_management_system = fields.Many2one("ir.attachment", readonly=True)

    # Related Admin Fields
    related_provider_type_id = fields.Char(string="Old Provider Type", readonly=True)
    related_provider_class_Id = fields.Char(string="Old Provider Class", readonly=True)
    related_provider_start_date = fields.Date(
        string="Old Provider Start Date", readonly=True
    )

    def approve_update(self):
        """
        Approves the request and synchronizes validated data to res.partner.
        """
        # Document fields that require careful handling (don't overwrite if empty)
        doc_list = [
            "cipro_documents",
            "tax_clearance",
            "director_cv",
            "certified_copies_of_qualifications",
            "professional_body_registration",
            "workplace_agreement",
            "business_residence_proof",
            "provider_learning_material",
            "skills_programme_registration_letter",
            "company_profile_and_organogram",
            "quality_management_system",
            "lease_agreement_document",
        ]

        # All fields to be synced from the audit record to the master record
        sync_fields = [
            "phone",
            "mobile",
            "fax",
            "website",
            "street",
            "street2",
            "street3",
            "suburb",
            "city",
            "state_id",
            "zip",
            "country_id",
            "physical_address_1",
            "physical_address_2",
            "physical_address_3",
            "provider_physical_suburb",
            "city_physical",
            "province_code_physical",
            "zip_physical",
            "country_code_physical",
            "postal_address_1",
            "postal_address_2",
            "postal_address_3",
            "provider_postal_suburb",
            "city_postal",
            "province_code_postal",
            "zip_postal",
            "country_code_postal",
            "txtCompanyRegNo",
            "txtVATRegNo",
            "cboProviderFocus",
            "txtNumYearsCurrentBusiness",
            "txtNumStaffMembers",
            "provider_type_id",
            "provider_class_Id",
            "provider_start_date",
            "provider_end_date",
        ] + doc_list

        for record in self:
            provider = record.provider_id
            if not provider:
                _logger.warning(
                    "No provider linked to update request %s", record.reference
                )
                continue

            vals = {}
            for field_name in sync_fields:
                # Use Odoo's native mapped logic for cleaner value extraction
                val = record[field_name]

                # Handle Many2one (extract ID) vs simple fields
                if isinstance(val, models.BaseModel):
                    vals[field_name] = val.id if val else False
                else:
                    vals[field_name] = val

            # Sync name only if specifically provided in the update
            if record.name:
                vals["name"] = record.name

            # Clean up document fields: don't overwrite master with False if no new doc uploaded
            for doc in doc_list:
                if not vals.get(doc):
                    vals.pop(doc, None)

            # Update the Master Partner record. Use sudo() to bypass potential
            # ACL restrictions during the administrative approval process.
            provider.sudo().write(vals)

            # Mark audit record as approved
            record.write(
                {
                    "status": "approved",
                    "action_date": fields.Date.today(),
                    "action_partner": self.env.user.partner_id.id,
                }
            )

            # Post to Provider chatter for audit trail
            provider.message_post(
                body=_("Information update %s has been approved and applied.")
                % record.reference
            )

            # Notification
            template = self.env.ref(
                "hwseta_etqe.email_template_prov_update_approve_notification",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(record.id, force_send=True)

        return True

    def reject_update(self, msg):
        """
        Rejects the request and notifies the provider.
        """
        for record in self:
            record.write(
                {
                    "status": "rejected",
                    "msg": msg,  # Store reason on the record
                    "action_date": fields.Date.today(),
                    "action_partner": self.env.user.partner_id.id,
                }
            )

            if record.provider_id:
                body = _(
                    "%(ref)s - Your update request has been rejected. \n\n Reason: %(msg)s"
                ) % {"ref": record.reference or _("Update Request"), "msg": msg}
                record.provider_id.message_post(body=body)


class ResPartner(models.Model):
    _inherit = "res.partner"

    update_ids = fields.One2many(
        "updated.providers", "provider_id", string="Update History"
    )

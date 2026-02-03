import logging
from datetime import date, datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def dbg(msg):
    """Log info messages; visible in console with --log-level=info or debug."""
    _logger.info(msg)


class UpdatedCampusesRejectWiz(models.TransientModel):
    _name = "updated.campuses.reject.wiz"
    _description = "Reject Campus Update Wizard"

    comment = fields.Text(string="Reason for Rejection", required=True)

    update_id = fields.Many2one(
        "updated.campuses",
        string="Update Request",
        default=lambda self: self.env.context.get("update_id", False),
    )

    def reject_update(self):
        """Finalizes the rejection of the campus update request."""
        self.ensure_one()

        # Log the rejection for debugging purposes (Odoo 18 standard)
        _logger.info(
            "Rejecting Campus Update ID %s with comment: %s",
            self.update_id.id,
            self.comment,
        )

        if self.update_id:
            # Using sudo() here ensures that even if the user has restricted
            # write access, the system logic can finalize the rejection.
            self.update_id.sudo().reject_update(self.comment)

        # Odoo 18 closing action
        return {"type": "ir.actions.act_window_close"}


class UpdatedCampusesApproveWiz(models.TransientModel):
    _name = "updated.campuses.approve.wiz"
    _description = "Approve Campus Update Wizard"

    comment = fields.Text(string="Approval Notes", required=True)

    update_id = fields.Many2one(
        "updated.campuses",
        string="Update Request",
        default=lambda self: self.env.context.get("update_id", False),
    )

    def approve_update(self):
        """Logic to approve a campus update and finalize the data migration."""
        self.ensure_one()

        # Standard Odoo 18 logging for the audit trail
        _logger.info(
            "Approving Campus Update ID %s. Notes: %s", self.update_id.id, self.comment
        )

        if self.update_id:
            # We call sudo() to ensure the backend logic (writing to the campus)
            # succeeds even if the approving clerk has limited record-level access.
            self.update_id.sudo().approve_update(self.comment)

        # Returns an action to close the wizard window
        return {"type": "ir.actions.act_window_close"}


class UpdateCampus(models.TransientModel):
    _name = "update.campus"
    _description = "Campus Information Update Wizard"

    def generate_msg(self, partner):
        """Standardized HTML message generation using f-strings."""
        return f"<p>Phone: {partner.phone or ''}</p>"

    def _default_provider(self):
        # In Odoo 18, self.env.user.partner_id is the standard way to get the related partner
        partner = self.env.user.partner_id
        if partner.provider:
            return partner.id
        return self.env.context.get("provider_id", False)

    def _default_accreditation(self):
        partner = self.env.user.partner_id
        provider_id = (
            partner.id
            if partner.provider
            else self.env.context.get("provider_id", False)
        )

        if provider_id:
            # .search() returns a recordset; using .last() or slicing is more efficient
            accred_ids = self.env["provider.accreditation"].search(
                [("related_provider", "=", provider_id)], order="id desc", limit=1
            )
            return accred_ids.id if accred_ids else False
        return False

    sequence_number = fields.Char(string="Reference Number", readonly=True)
    provider_id = fields.Many2one(
        "res.partner", string="Provider", default=_default_provider
    )
    accreditation_id = fields.Many2one(
        "provider.accreditation", string="Accreditation", default=_default_accreditation
    )
    campus_id = fields.Many2one("provider.accreditation.campus", string="Target Campus")

    disclaimer = fields.Boolean(string="Terms & Conditions")
    update_disclaimer = fields.Boolean(string="POPIA Disclaimer")

    action = fields.Selection(
        [
            ("create", "Create"),
            ("update", "Update"),
            ("delete", "Delete"),
        ],
        string="Action Type",
        required=True,
    )

    # Physical Address Fields
    name = fields.Char(string="Campus Name", required=True)
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    street3 = fields.Char(string="Street 3")
    zip = fields.Char(string="Zip Code")
    suburb = fields.Many2one("res.suburb", string="Suburb")
    city = fields.Many2one("res.city", string="City")
    state_id = fields.Many2one(
        "res.country.state", string="Province", ondelete="restrict"
    )
    country_id = fields.Many2one("res.country", string="Country", ondelete="restrict")

    # Contact Fields
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    status = fields.Char(string="Status")
    fax = fields.Char(string="Fax")
    designation = fields.Char(string="Designation")
    campus_evaluat = fields.Boolean(string="Evaluate Campus")

    @api.onchange("accreditation_id")
    def onchange_lookups(self):
        """Sync provider based on selected accreditation."""
        if self.accreditation_id:
            self.provider_id = self.accreditation_id.related_provider.id

    @api.onchange("disclaimer", "campus_id")
    def populate_fields(self):
        """Populates wizard fields from existing campus record if updating/deleting."""
        if self.campus_id and self.disclaimer:
            c = self.campus_id
            # Batch update using update() for better performance
            self.update(
                {
                    "name": c.name,
                    "street": c.street,
                    "street2": c.street2,
                    "street3": c.street3,
                    "zip": c.zip,
                    "suburb": c.suburb.id,
                    "city": c.city.id,
                    "state_id": c.state_id.id,
                    "country_id": c.country_id.id,
                    "email": c.email,
                    "phone": c.phone,
                    "mobile": c.mobile,
                    "fax": c.fax,
                    "designation": c.designation,
                    "campus_evaluat": c.campus_evaluat,
                }
            )

    def action_submit(self):
        """
        Migrated to Odoo 18. Processes the wizard data and creates
        an audit record in updated.campuses.
        """
        self.ensure_one()
        prov = self.provider_id
        campus = self.campus_id

        # Odoo 18 sequence fetching
        sequence_number = (
            self.env["ir.sequence"].next_by_code("update.campus.reference.sequence")
            or "New"
        )

        # Logic to ensure phone/mobile are populated from provider if empty
        if self.action in ["create", "update"]:
            if not self.phone:
                self.phone = prov.phone
            if not self.mobile:
                self.mobile = prov.mobile

        # Base dictionary for the new request
        vals = {
            "sequence_number": sequence_number,
            "phone": self.phone,
            "mobile": self.mobile,
            "name": self.name,
            "street": self.street,
            "street2": self.street2,
            "street3": self.street3,
            "zip": self.zip,
            "suburb": self.suburb.id,
            "city": self.city.id,
            "state_id": self.state_id.id,
            "country_id": self.country_id.id,
            "email": self.email,
            "fax": self.fax,
            "designation": self.designation,
            "transaction_status": "submitted",
            "provider_id": prov.id,
            "campus_id": campus.id if campus else False,
            "campus_evaluat": self.campus_evaluat,
            "disclaimer": self.disclaimer,
            "update_disclaimer": self.update_disclaimer,
            "accreditation_id": self.accreditation_id.id,
            "action": self.action,
        }

        # Handling 'Related' fields for Audit Comparison (Old vs New)
        if self.action == "create":
            # For creation, 'Related' (Old) is the same as 'New'
            vals.update(
                {
                    "related_phone": self.phone,
                    "related_mobile": self.mobile,
                    "related_name": self.name,
                    "related_street": self.street,
                    "related_zip": self.zip,
                    "related_suburb": self.suburb.id,
                    "related_city": self.city.id,
                    "related_state_id": self.state_id.id,
                    "related_country_id": self.country_id.id,
                    "related_email": self.email,
                    "related_fax": self.fax,
                    "related_designation": self.designation,
                    "related_campus_evaluat": self.campus_evaluat,
                }
            )

        elif self.action in ["update", "delete"] and campus:
            # Map existing campus data to 'Related' fields for comparison
            vals.update(
                {
                    "msg": "Deletion request" if self.action == "delete" else "",
                    "related_phone": campus.phone,
                    "related_mobile": campus.mobile,
                    "related_name": campus.name,
                    "related_street": campus.street,
                    "related_zip": campus.zip,
                    "related_suburb": campus.suburb.id,
                    "related_city": campus.city.id,
                    "related_state_id": campus.state_id.id,
                    "related_country_id": campus.country_id.id,
                    "related_email": campus.email,
                    "related_fax": campus.fax,
                    "related_designation": campus.designation,
                    "related_campus_evaluat": campus.campus_evaluat,
                }
            )
        elif self.action in ["update", "delete"] and not campus:
            raise UserError(_("Please select a Campus to %s.") % self.action)
        else:
            raise UserError(_("Please select a valid action before proceeding."))

        # Create audit record
        update_request = self.env["updated.campuses"].create(vals)

        # Modern Chatter log on the Provider (res.partner)
        prov.message_post(
            body=_("Information update request for campus (%s) has been submitted.")
            % sequence_number,
            subtype_xmlid="mail.mt_note",
        )

        # Email Notification
        template = self.env.ref(
            "hwseta_etqe.email_template_prov_update_submit_notification",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(update_request.id, force_send=True)

        _logger.info(
            "Campus update request %s created by %s",
            sequence_number,
            self.env.user.name,
        )

        return {"type": "ir.actions.act_window_close"}


class MasterCampuses(models.Model):
    _name = "master.campuses"
    _description = "Master Campus Records"
    _inherit = ["mail.thread", "mail.activity.mixin"]  # Added for audit trail/chatter
    _order = "name asc"

    # Reference Fields
    provider_id = fields.Many2one(
        "res.partner", string="Provider", tracking=True, index=True
    )
    disclaimer = fields.Boolean(string="Disclaimer Accepted")
    update_disclaimer = fields.Boolean(string="POPIA Accepted")

    # Identification
    name = fields.Char(string="Campus Name", required=True, tracking=True)
    designation = fields.Char(string="Designation")
    status = fields.Char(string="Status", tracking=True)

    # Physical Address
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    street3 = fields.Char(string="Street 3")
    suburb = fields.Many2one("res.suburb", string="Suburb")
    city = fields.Many2one("res.city", string="City", tracking=True)
    state_id = fields.Many2one(
        "res.country.state", string="Province", ondelete="restrict"
    )
    country_id = fields.Many2one("res.country", string="Country", ondelete="restrict")
    zip = fields.Char(string="Zip Code", change_default=True)

    # Contact Info
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    fax = fields.Char(string="Fax")


class UpdatedCampuses(models.Model):
    _name = "updated.campuses"
    _description = "Campus Update Audit Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    transaction_status = fields.Selection(
        [
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Transaction Status",
        default="submitted",
        tracking=True,
    )

    sequence_number = fields.Char(string="Reference Number", copy=False, readonly=True)
    provider_id = fields.Many2one("res.partner", string="Provider", tracking=True)
    accreditation_id = fields.Many2one("provider.accreditation", string="Accreditation")
    campus_id = fields.Many2one("provider.accreditation.campus", string="Source Campus")

    action = fields.Selection(
        [
            ("create", "Create"),
            ("update", "Update"),
            ("delete", "Delete"),
        ],
        string="Action",
    )

    disclaimer = fields.Boolean(string="Disclaimer")
    update_disclaimer = fields.Boolean(string="POPIA Disclaimer")
    comment = fields.Text(string="Notes")

    # --- New Values ---
    name = fields.Char(string="Name", required=True)
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    street3 = fields.Char(string="Street 3")
    zip = fields.Char(string="Zip")
    suburb = fields.Many2one("res.suburb", string="Suburb")
    city = fields.Many2one("res.city", string="City")
    state_id = fields.Many2one("res.country.state", "Province")
    country_id = fields.Many2one("res.country", "Country")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    status = fields.Char(string="Status")
    fax = fields.Char(string="Fax")
    designation = fields.Char(string="Designation")
    campus_evaluat = fields.Boolean(string="Evaluate")

    # --- Related (Old) Values for Comparison ---
    related_name = fields.Char(string="Old Name")
    related_street = fields.Char(string="Old Street")
    related_street2 = fields.Char(string="Old Street 2")
    related_street3 = fields.Char(string="Old Street 3")
    related_zip = fields.Char(string="Old Zip")
    related_suburb = fields.Many2one("res.suburb", string="Old Suburb")
    related_city = fields.Many2one("res.city", string="Old City")
    related_state_id = fields.Many2one("res.country.state", "Old Province")
    related_country_id = fields.Many2one("res.country", "Old Country")
    related_email = fields.Char(string="Old Email")
    related_phone = fields.Char(string="Old Phone")
    related_mobile = fields.Char(string="Old Mobile")
    related_status = fields.Char(string="Old Status")
    related_fax = fields.Char(string="Old Fax")
    related_designation = fields.Char(string="Old Designation")
    related_campus_evaluat = fields.Boolean(string="Old Evaluate")

    @api.model_create_multi
    def create(self, vals_list):
        """Modern Odoo 18 create method handling multiple records and sequences."""
        for vals in vals_list:
            if not vals.get("sequence_number") or vals.get("sequence_number") == "New":
                vals["sequence_number"] = (
                    self.env["ir.sequence"].next_by_code(
                        "update.campus.reference.sequence"
                    )
                    or "New"
                )
        return super().create(vals_list)

    def approve_update(self, comment):
        """Applies changes to Master Campuses and updates record status."""
        self.ensure_one()
        # Filter technical/audit fields to get clean master data
        skip_fields = [
            "transaction_status",
            "sequence_number",
            "accreditation_id",
            "campus_id",
            "action",
            "disclaimer",
            "update_disclaimer",
            "comment",
        ]

        # Build dictionary for master record
        master_vals = {
            k: (
                getattr(self, k).id
                if isinstance(getattr(self, k), models.BaseModel)
                else getattr(self, k)
            )
            for k in self._fields
            if not k.startswith("related_") and k not in skip_fields
        }

        if self.action == "delete":
            self.delete_master_campuses(master_vals)
        else:
            self.create_or_update_master_campuses(master_vals)

        self.write({"transaction_status": "approved", "comment": comment})

    @api.model
    def delete_master_campuses(self, vals):
        """Standardized deletion from master."""
        matcher = self.env["master.campuses"].search(
            [
                ("provider_id", "=", vals.get("provider_id")),
                ("name", "=", vals.get("name")),
            ]
        )
        if matcher:
            matcher.unlink()
        else:
            _logger.warning(
                "Attempted to delete non-existent master campus: %s", vals.get("name")
            )

    @api.model
    def create_or_update_master_campuses(self, vals):
        """Standardized create/update in master."""
        matcher = self.env["master.campuses"].search(
            [
                ("provider_id", "=", vals.get("provider_id")),
                ("name", "=", vals.get("name")),
            ]
        )
        if matcher:
            matcher.write(vals)
        else:
            self.env["master.campuses"].create(vals)

    def approve_update(self):
        """
        Migrated to Odoo 18. Processes approval for campus create, update, or delete.
        Synchronizes operational data with the Master Campus audit model.
        """
        # Batch processing is the default in Odoo 18, but ensure_one if logic is record-specific
        for record in self:
            prov = record.provider_id
            campus = record.campus_id
            accred = record.accreditation_id

            # Fallback for contact details
            phone = record.phone or prov.phone
            mobile = record.mobile or prov.mobile

            # Common values for operational campus and master campus
            vals = {
                "phone": phone,
                "mobile": mobile,
                "name": record.name,
                "street": record.street,
                "street2": record.street2,
                "street3": record.street3,
                "zip": record.zip,
                "suburb": record.suburb.id,
                "city": record.city.id,
                "state_id": record.state_id.id,
                "country_id": record.country_id.id,
                "email": record.email,
                "fax": record.fax,
                "designation": record.designation,
                "campus_evaluat": record.campus_evaluat,
                "state": "approved",  # Operational state
            }

            if record.action == "create":
                # Add operational-specific fields for creation
                create_vals = vals.copy()
                create_vals.update(
                    {
                        "provider_accreditation_campus_id": accred.id,
                        "provider_id": prov.id,
                    }
                )
                # 1. Create the operational campus
                self.env["provider.accreditation.campus"].sudo().create(create_vals)

                # 2. Sync to Master
                master_vals = vals.copy()
                master_vals.update(
                    {
                        "provider_id": prov.id,
                        "update_disclaimer": record.update_disclaimer,
                        "disclaimer": record.disclaimer,
                    }
                )
                record.create_or_update_master_campuses(master_vals)

            elif record.action == "update":
                if not campus:
                    _logger.warning(
                        "Update skipped: No campus linked to request %s",
                        record.sequence_number,
                    )
                    continue

                # 1. Update operational campus
                campus.sudo().write(vals)

                # 2. Sync to Master
                master_vals = vals.copy()
                master_vals.update(
                    {
                        "provider_id": prov.id,
                        "update_disclaimer": record.update_disclaimer,
                        "disclaimer": record.disclaimer,
                    }
                )
                record.create_or_update_master_campuses(master_vals)

            elif record.action == "delete":
                if campus:
                    # 1. Logic-specific sync to master before unlink
                    delete_vals = {
                        "provider_id": prov.id,
                        "name": record.name,
                    }
                    record.delete_master_campuses(delete_vals)

                    # 2. Unlink operational record
                    campus.sudo().unlink()

            # Finalize the transaction status
            record.write(
                {
                    "transaction_status": "approved",
                    "action_date": fields.Date.today(),
                    "action_partner": self.env.user.partner_id.id,
                }
            )

            # Post to Provider Chatter
            prov.message_post(
                body=_("Campus update request %s has been approved.")
                % record.sequence_number
            )

        return True

    def reject_update(self, msg):
        """
        Migrated to Odoo 18.
        Rejects the request and logs the feedback in the Provider's chatter.
        """
        # Batch processing is the default; self is a recordset
        for record in self:
            if not msg:
                raise UserError(_("Please provide a rejection comment."))

            # Modern write operation
            record.write(
                {
                    "transaction_status": "rejected",
                    "action_date": fields.Date.today(),
                    "action_partner": self.env.user.partner_id.id,
                    "comment": msg,  # Storing the rejection reason on the record
                }
            )

            # Construct log message using f-strings (standard in Odoo 18 / Python 3.10+)
            log_message = _(
                "%(seq)s - Update has been rejected with the following comments:\n%(msg)s"
            ) % {"seq": record.sequence_number or _("New Request"), "msg": msg}

            # Standard Odoo message_post
            if record.provider_id:
                record.provider_id.message_post(
                    body=log_message,
                    subtype_xmlid="mail.mt_note",  # Logs as an internal note
                )

        _logger.info("Campus update request(s) rejected by %s", self.env.user.name)
        return True


class ResPartner(models.Model):
    _inherit = "res.partner"

    # One2many relation to track all campus update attempts for this provider
    update_campus_ids = fields.One2many(
        "updated.campuses", "provider_id", string="Campus Update Requests"
    )

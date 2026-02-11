from odoo import fields, models, api, _
from odoo.exceptions import UserError
import calendar
import logging


_logger = logging.getLogger(__name__)


class LinkStakeholder(models.TransientModel):
    _name = "link.stakeholder"
    _description = "Wizard to Link Stakeholders"

    # Default Methods (Modernized)
    def _default_provider(self):
        # self.env.user is already optimized in Odoo 18
        partner = self.env.user.partner_id
        if partner.provider:
            return partner
        return False

    def _default_assessor(self):
        user = self.env.user
        # Direct search is standard; limit=1 for efficiency
        ass = self.env["hr.employee"].search(
            [
                ("user_id", "=", user.id),
                ("is_assessors", "=", True),
                ("is_active_assessor", "=", True),
            ],
            limit=1,
        )
        return ass

    def _default_moderator(self):
        user = self.env.user
        mod = self.env["hr.employee"].search(
            [
                ("user_id", "=", user.id),
                ("is_moderators", "=", True),
                ("is_active_moderator", "=", True),
            ],
            limit=1,
        )
        return mod

    def _default_assessor_or_moderator(self):
        partner = self.env.user.partner_id
        if not partner.provider:
            return "provider"
        return False

    # Field Definitions
    popi_accept = fields.Boolean(string="POPI Accept")

    provider_id = fields.Many2one(
        "res.partner", string="Provider", default=_default_provider, ondelete="cascade"
    )

    assessor_id = fields.Many2one(
        "hr.employee", string="Assessor", default=_default_assessor
    )

    moderator_id = fields.Many2one(
        "hr.employee", string="Moderator", default=_default_moderator
    )

    assessor_or_moderator = fields.Selection(
        [
            ("assessor", "Assessor"),
            ("moderator", "Moderator"),
            ("provider", "Provider"),
        ],
        string="Type",
        default=_default_assessor_or_moderator,
    )

    work_phone = fields.Char("Work Phone", size=10)
    work_email = fields.Char("Work Email", size=240)

    sla_document = fields.Many2one("ir.attachment", string="SLA Document")
    notification_letter = fields.Many2one("ir.attachment", string="Notification Letter")

    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting_approval", "Waiting Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="draft",
    )

    search_by = fields.Selection(
        [
            ("id", "Identification No"),
            ("number", "Assessor/Moderator Number"),
            ("sdl", "Provider SDL Number"),
            ("prov_acc", "Provider Accreditation Number"),
        ],
        string="Search by",
    )

    identification_id = fields.Char(string="Identification ID")

    @api.onchange("identification_id", "search_by", "assessor_or_moderator")
    def onchange_identification_id(self):
        """Validates identification and automatically populates stakeholder details."""
        if not self.identification_id:
            return

        if self.search_by == "id":
            identification_id = self.identification_id
            # Assuming 'checkers' is imported in the main file
            check = checkers.said_check(identification_id)

            if not check.get("valid"):
                old_check_msg = checkers.old_said_check(identification_id)

                if "Invalid gender" in old_check_msg:
                    raise UserError(_("Invalid Gender!"))
                if "Invalid citizenship status" in old_check_msg:
                    raise UserError(_("Invalid citizenship status!"))

                day = int(check.get("day", 0))
                month = int(check.get("month", 0))
                year = int(check.get("year", 0))

                if day > 31 or day < 1:
                    raise UserError(_("Incorrect Day In Identification Number!"))
                if month > 12 or month < 1:
                    raise UserError(_("Incorrect Month In Identification Number!"))

                # Handling Y2K year logic
                x_year = 2000 + year if year < 50 else 1900 + year
                last_day = calendar.monthrange(x_year, month)[1]

                if day > last_day:
                    raise UserError(
                        _("Incorrect last day of month in identification number!")
                    )

                # If checksum is the only remaining failure
                self.identification_id = ""
                raise UserError(_("Incorrect checksum!"))

            # Search logic for ID
            Employee = self.env["hr.employee"].sudo()
            domain = [
                ("assessor_moderator_identification_id", "=", self.identification_id)
            ]

            if self.assessor_or_moderator == "assessor":
                res = Employee.search(
                    domain + [("is_active_assessor", "=", True)], limit=1
                )
                if res:
                    self.assessor_id = res.id
                    self.work_email = res.work_email
                    self.work_phone = res.person_cell_phone_number
            elif self.assessor_or_moderator == "moderator":
                res = Employee.search(
                    domain + [("is_active_moderator", "=", True)], limit=1
                )
                if res:
                    self.moderator_id = res.id
                    self.work_email = res.work_email
                    self.work_phone = res.person_cell_phone_number
            else:
                raise UserError(
                    _("Please select which partner to search (Assessor or Moderator).")
                )

        elif self.search_by == "number":
            Employee = self.env["hr.employee"].sudo()
            if self.assessor_or_moderator == "assessor":
                res = Employee.search(
                    [
                        ("is_active_assessor", "=", True),
                        ("assessor_seq_no", "=", self.identification_id),
                        ("is_assessors", "=", True),
                    ],
                    limit=1,
                )
                if res:
                    self.assessor_id = res.id
                    self.work_email = res.work_email
                    self.work_phone = res.person_cell_phone_number
            elif self.assessor_or_moderator == "moderator":
                res = Employee.search(
                    [
                        ("is_active_moderator", "=", True),
                        ("moderator_seq_no", "=", self.identification_id),
                        ("is_moderators", "=", True),
                    ],
                    limit=1,
                )
                if res:
                    self.moderator_id = res.id
                    self.work_email = res.work_email
                    self.work_phone = res.person_cell_phone_number

        elif self.search_by in ["sdl", "prov_acc"]:
            Partner = self.env["res.partner"].sudo()
            domain = [("provider", "=", True)]

            if self.search_by == "sdl":
                domain.append(("provider_sars_number", "=", self.identification_id))
            else:
                domain.append(
                    ("provider_accreditation_num", "=", self.identification_id)
                )

            if self.assessor_or_moderator == "provider":
                res = Partner.search(domain, limit=1)
                if res:
                    self.provider_id = res.id
                    self.work_email = res.email
                    self.work_phone = res.mobile
            else:
                raise UserError(
                    _(
                        "Please select 'Provider' as the Stakeholder Type to search by SDL/Accreditation."
                    )
                )

        _logger.info("Stakeholder search completed for ID: %s", self.identification_id)

    def link_assessor_moderator(self):
        """Migrated to Odoo 18: Links an Assessor or Moderator to a Provider."""
        self.ensure_one()
        _logger.info(
            "Executing link_assessor_moderator for stakeholder type: %s",
            self.assessor_or_moderator,
        )

        user = self.env.user
        partner = self.provider_id

        if not partner:
            raise UserError(_("No provider selected to link with."))

        # Use sudo() on the environment model directly
        Employee = self.env["hr.employee"].sudo()

        if self.assessor_or_moderator == "assessor":
            ass_obj = False
            if self.search_by == "id":
                ass_obj = Employee.search(
                    [
                        ("is_active_assessor", "=", True),
                        (
                            "assessor_moderator_identification_id",
                            "=",
                            self.identification_id,
                        ),
                    ],
                    limit=1,
                )
            elif self.search_by == "number":
                ass_obj = Employee.search(
                    [
                        ("is_active_assessor", "=", True),
                        ("assessor_seq_no", "=", self.identification_id),
                        ("is_assessors", "=", True),
                    ],
                    limit=1,
                )
            elif self.assessor_id:
                ass_obj = self.assessor_id

            if not ass_obj:
                raise UserError(
                    _(
                        "Cannot find an Assessor under this context. Please contact the administrator."
                    )
                )

            # Modern Odoo 'Command' syntax for X2many relations
            partner.write(
                {
                    "assessors_ids": [
                        Command.create(
                            {
                                "assessors_id": ass_obj.id,
                                "search_by": self.search_by,
                                "identification_id": self.identification_id,
                                "awork_email": self.work_email,
                                "awork_phone": self.work_phone,
                                "assessor_sla_document": self.sla_document.id,
                                "assessor_notification_letter": self.notification_letter.id,
                                "creator": user.id,
                                "status": "requested",
                            }
                        )
                    ]
                }
            )

            ass_obj.write(
                {
                    "as_provider_rel_id": [
                        Command.create(
                            {
                                "provider_id": partner.id,
                                "provider_accreditation_num": partner.provider_accreditation_num,
                                "employer_sdl_no": partner.provider_sars_number,
                            }
                        )
                    ]
                }
            )

        elif self.assessor_or_moderator == "moderator":
            mod_obj = False
            if self.search_by == "id":
                mod_obj = Employee.search(
                    [
                        ("is_active_moderator", "=", True),
                        (
                            "assessor_moderator_identification_id",
                            "=",
                            self.identification_id,
                        ),
                    ],
                    limit=1,
                )
            elif self.search_by == "number":
                mod_obj = Employee.search(
                    [
                        ("is_active_moderator", "=", True),
                        ("moderator_seq_no", "=", self.identification_id),
                        ("is_moderators", "=", True),
                    ],
                    limit=1,
                )
            elif self.moderator_id:
                mod_obj = self.moderator_id

            if not mod_obj:
                raise UserError(
                    _(
                        "Cannot find a Moderator under this context. Please contact the administrator."
                    )
                )

            partner.write(
                {
                    "moderators_ids": [
                        Command.create(
                            {
                                "moderators_id": mod_obj.id,
                                "identification_id": self.identification_id,
                                "search_by": self.search_by,
                                "mwork_email": self.work_email,
                                "mwork_phone": self.work_phone,
                                "moderator_sla_document": self.sla_document.id,
                                "moderator_notification_letter": self.notification_letter.id,
                                "creator": user.id,
                                "status": "requested",
                            }
                        )
                    ]
                }
            )

            mod_obj.write(
                {
                    "mo_provider_rel_id": [
                        Command.create(
                            {
                                "provider_id": partner.id,
                                "provider_accreditation_num": partner.provider_accreditation_num,
                                "employer_sdl_no": partner.provider_sars_number,
                            }
                        )
                    ]
                }
            )
        else:
            raise UserError(
                _("You need to select a valid search by option before continuing.")
            )

        return True

    def link_provider(self):
        """Migrated to Odoo 18: Links a Provider to an Assessor or Moderator."""
        self.ensure_one()
        _logger.info("Executing link_provider for search_by: %s", self.search_by)

        user = self.env.user
        prov_obj = self.env["res.partner"]

        # 1. Determine the Provider Object
        if not self.provider_id:
            # Sudo is called directly on the model reference in Odoo 18
            Partner = self.env["res.partner"].sudo()
            domain = [("provider", "=", True)]

            if self.search_by == "sdl":
                domain.append(("provider_sars_number", "=", self.identification_id))
            elif self.search_by == "prov_acc":
                domain.append(
                    ("provider_accreditation_num", "=", self.identification_id)
                )
            else:
                raise UserError(
                    _(
                        "Cannot retrieve provider info. Please contact the system administrator."
                    )
                )

            # Using limit=1 as we expect a single unique provider
            prov_obj = Partner.search(domain, limit=1)
        else:
            prov_obj = self.provider_id

        if not prov_obj:
            raise UserError(_("No provider found matching the criteria."))

        # 2. Link Assessor if present
        if self.assessor_id:
            _logger.info(
                "Linking Assessor: %s to Provider: %s",
                self.assessor_id.name,
                prov_obj.name,
            )

            # Using Command.create (0, 0, {values}) for cleaner Odoo 18 syntax
            prov_obj.write(
                {
                    "assessors_ids": [
                        Command.create(
                            {
                                "assessors_id": self.assessor_id.id,
                                "identification_id": self.identification_id,
                                "awork_email": self.work_email,
                                "awork_phone": self.work_phone,
                                "assessor_sla_document": self.sla_document.id,
                                "assessor_notification_letter": self.notification_letter.id,
                                "creator": user.id,
                                "status": "requested",
                            }
                        )
                    ]
                }
            )

            self.assessor_id.write(
                {
                    "as_provider_rel_id": [
                        Command.create(
                            {
                                "provider_id": prov_obj.id,
                                "provider_accreditation_num": prov_obj.provider_accreditation_num,
                                "employer_sdl_no": prov_obj.provider_sars_number,
                                "create_uid": user.id,
                            }
                        )
                    ]
                }
            )

        # 3. Link Moderator if present
        if self.moderator_id:
            _logger.info(
                "Linking Moderator: %s to Provider: %s",
                self.moderator_id.name,
                prov_obj.name,
            )

            prov_obj.write(
                {
                    "moderators_ids": [
                        Command.create(
                            {
                                "moderators_id": self.moderator_id.id,
                                "identification_id": self.identification_id,
                                "mwork_email": self.work_email,
                                "mwork_phone": self.work_phone,
                                "moderator_sla_document": self.sla_document.id,
                                "moderator_notification_letter": self.notification_letter.id,
                                "creator": user.id,
                                "status": "requested",
                            }
                        )
                    ]
                }
            )

            self.moderator_id.write(
                {
                    "mo_provider_rel_id": [
                        Command.create(
                            {
                                "provider_id": prov_obj.id,
                                "provider_accreditation_num": prov_obj.provider_accreditation_num,
                                "employer_sdl_no": prov_obj.provider_sars_number,
                                "create_uid": user.id,
                            }
                        )
                    ]
                }
            )

        return True


class AssessorModeratorAmeWizard(models.TransientModel):
    _name = "assessor.moderator.ame.wizard"
    _description = "Assessor and Moderator Email Management Wizard"

    assessor_id = fields.Many2one("hr.employee", string="Assessor")
    moderator_id = fields.Many2one("hr.employee", string="Moderator")
    assessor_or_moderator = fields.Selection(
        [("a", "Assessor"), ("m", "Moderator")], string="Type", required=True
    )

    identification = fields.Char(string="Identification / Reg No")
    ticket_num = fields.Char(string="Ticket #")
    search_by = fields.Selection(
        [("id", "Identification Number"), ("number", "Registration Number")],
        string="Search by",
        required=True,
    )

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    work_email = fields.Char(string="New Work Email")

    def get_am(self, identification):
        """Helper to find the Assessor or Moderator record."""
        self.ensure_one()
        if not identification:
            return False

        # In Odoo 18, use .sudo() on the environment model directly
        Employee = self.env["hr.employee"].sudo()
        domain = []

        if self.assessor_or_moderator == "a":
            if self.search_by == "id":
                domain = [("assessor_moderator_identification_id", "=", identification)]
            else:
                domain = [
                    ("assessor_seq_no", "=", identification),
                    ("is_assessors", "=", True),
                ]

        elif self.assessor_or_moderator == "m":
            if self.search_by == "id":
                domain = [("assessor_moderator_identification_id", "=", identification)]
            else:
                domain = [
                    ("moderator_seq_no", "=", identification),
                    ("is_moderators", "=", True),
                ]

        res = Employee.search(domain, order="id desc", limit=1)
        if not res:
            raise UserError(
                _("Couldn't find the requested record. Please check the ID/Number.")
            )

        return self.assessor_or_moderator, res

    @api.onchange("identification", "assessor_or_moderator", "search_by")
    def onchange_get_am(self):
        """Fetch A/M record automatically when identification is entered."""
        if self.identification and self.assessor_or_moderator and self.search_by:
            try:
                a_or_m, am_obj = self.get_am(self.identification)
                if a_or_m == "a":
                    self.assessor_id = am_obj.id
                else:
                    self.moderator_id = am_obj.id
            except UserError:
                pass

    def fix_email(self):
        """Synchronizes the email update across Employee, User, and Partner records."""
        self.ensure_one()
        if not self.work_email:
            raise UserError(_("Please provide the new work email."))

        type_code, am_obj = self.get_am(self.identification)
        old_email = am_obj.work_email

        # 1. Update Employee
        am_obj.write({"work_email": self.work_email})

        # 2. Update User Login
        user = (
            self.env["res.users"]
            .sudo()
            .search([("assessor_moderator_id", "=", am_obj.id)], limit=1)
        )
        if user:
            user.write({"login": self.work_email})
            # 3. Update Partner Email
            if user.partner_id:
                user.partner_id.write({"email": self.work_email})

        # Formatting log message with f-strings
        msg = f"Ticket#:{self.ticket_num or 'N/A'} - ID:{self.identification} - Email changed: {old_email} > {self.work_email}"

        # Handle Notification
        template = self.env.ref(
            "hwseta_etqe.email_template_master_data_edit_notification",
            raise_if_not_found=False,
        )
        if template:
            template.sudo().write(
                {"body_html": f"<p>{msg}</p>", "email_from": self.env.user.email}
            )
            template.send_mail(am_obj.id, force_send=True)

        _logger.info(msg)
        return {"type": "ir.actions.act_window_close"}

class EtqeAssessorsProviderRel(models.Model):
    _inherit = 'etqe.assessors.provider.rel'

    # Use default=lambda self: self.env.user to automatically set the creator
    creator = fields.Many2one('res.users', string='Creator', default=lambda self: self.env.user)

    def assessor_approved_request(self):
        """Standard Odoo 18 method (no decorator needed for multi-record support)"""
        user = self.env.user
        for record in self:
            if record.creator == user:
                raise UserError(_("You cannot approve a request created by yourself. "
                                  "Please ask the provider to approve."))
            record.write({'status': 'waiting_approval', 'request_send': True})

    def provider_approved_request(self):
        user = self.env.user
        for record in self:
            if record.creator == user:
                raise UserError(_("You cannot approve a request created by yourself. "
                                  "Please ask the assessor to approve."))
            record.write({'status': 'waiting_approval', 'request_send': True})

    def assessor_rejected_request(self):
        self.write({'status': 'rejected', 'reject_request': True})


class EtqeModeratorsProviderRel(models.Model):
    _inherit = "etqe.moderators.provider.rel"

    # Captures the user who created the record
    creator = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        readonly=True,
    )
    popi_accept = fields.Boolean(string="POPI Accepted")

    def moderator_approved_request(self):
        """Moderator approving a request they didn't create"""
        user = self.env.user
        for record in self:
            if record.creator == user:
                raise UserError(
                    _(
                        "You cannot approve a request created by yourself. Please ask the provider to approve."
                    )
                )
            record.write({"status": "waiting_approval", "request_send": True})

    def provider_approved_request(self):
        """Provider approving a request they didn't create"""
        user = self.env.user
        for record in self:
            if record.creator == user:
                raise UserError(
                    _(
                        "You cannot approve a request created by yourself. Please ask the moderator to approve."
                    )
                )
            record.write({"status": "waiting_approval", "request_send": True})

    def moderator_rejected_request(self):
        """Reject the request and update status"""
        self.write({"status": "rejected", "reject_request": True})

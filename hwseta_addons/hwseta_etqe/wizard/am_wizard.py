from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AssessorModeratorWizard(models.TransientModel):
    _name = "assessor.moderator.wizard"
    _description = "Wizard to Manage Assessor and Moderator Details"

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

    # Date fields for assessor
    start_date = fields.Date(string="Assessor Start Date")
    end_date = fields.Date(string="Assessor End Date")

    # Date fields for moderator
    moderator_start_date = fields.Date(string="Moderator Start Date")
    moderator_end_date = fields.Date(string="Moderator End Date")

    def get_am(self, identification):
        """Helper to find the Assessor or Moderator record with optimized search."""
        self.ensure_one()
        _logger.info(
            "Searching for %s with ID: %s", self.assessor_or_moderator, identification
        )

        if not identification:
            return False

        # Accessing the model via sudo() directly on the environment
        Employee = self.env["hr.employee"].sudo()
        domain = []

        if self.assessor_or_moderator == "a":
            if self.search_by == "id":
                domain = [("assessor_moderator_identification_id", "=", identification)]
            elif self.search_by == "number":
                domain = [
                    ("assessor_seq_no", "=", identification),
                    ("is_assessors", "=", True),
                ]

            ass_mod_obj = Employee.search(domain, limit=1)
            if not ass_mod_obj:
                raise UserError(
                    _("Couldn't find an Assessor with that Identification/Number.")
                )
            return "a", ass_mod_obj

        elif self.assessor_or_moderator == "m":
            if self.search_by == "id":
                domain = [("assessor_moderator_identification_id", "=", identification)]
            elif self.search_by == "number":
                domain = [
                    ("moderator_seq_no", "=", identification),
                    ("is_moderators", "=", True),
                ]

            ass_mod_obj = Employee.search(domain, limit=1)
            if not ass_mod_obj:
                raise UserError(
                    _("Couldn't find a Moderator with that Identification/Number.")
                )
            return "m", ass_mod_obj

        raise UserError(_('Please choose "Assessor" or "Moderator" to proceed.'))

    @api.onchange("identification", "assessor_or_moderator", "search_by")
    def onchange_get_am(self):
        """Automatically fetch and populate the A/M details on the wizard."""
        if self.identification and self.assessor_or_moderator and self.search_by:
            try:
                a_or_m, am_obj = self.get_am(self.identification)
                if a_or_m == "a":
                    self.assessor_id = am_obj.id
                    self.start_date = am_obj.start_date
                    self.end_date = am_obj.end_date
                elif a_or_m == "m":
                    self.moderator_id = am_obj.id
                    self.moderator_start_date = am_obj.moderator_start_date
                    self.moderator_end_date = am_obj.moderator_end_date
            except UserError:
                # We typically don't block the user with popups during onchange
                # unless absolutely necessary.
                pass

    def fix_dates(self):
        """Validates and updates registration dates for Assessors or Moderators."""
        self.ensure_one()
        if not self.identification:
            raise UserError(_("Please provide an identification number first."))

        a_or_m, am_obj = self.get_am(self.identification)
        today = fields.Date.today()
        vals = {}
        msg_parts = [f"ticket#:{self.ticket_num or 'N/A'}", f"ID:{self.identification}"]

        if a_or_m == "a":
            if not (self.start_date and self.end_date):
                raise UserError(_("Please ensure both Assessor dates are filled!"))

            msg_parts.append(
                f"Assessor dates changed: {am_obj.start_date} > {self.start_date} | {am_obj.end_date} > {self.end_date}"
            )

            # Update values and determine activation status
            is_active = self.end_date >= today
            vals.update(
                {
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "is_active_assessor": is_active,
                }
            )
            msg_parts.append(f"Status: {'Active' if is_active else 'Inactive'}")

        elif a_or_m == "m":
            if not (self.moderator_start_date and self.moderator_end_date):
                raise UserError(_("Please ensure both Moderator dates are filled!"))

            msg_parts.append(
                f"Moderator dates changed: {am_obj.moderator_start_date} > {self.moderator_start_date} | {am_obj.moderator_end_date} > {self.moderator_end_date}"
            )

            is_active = self.moderator_end_date >= today
            vals.update(
                {
                    "moderator_start_date": self.moderator_start_date,
                    "moderator_end_date": self.moderator_end_date,
                    "is_active_moderator": is_active,
                }
            )
            msg_parts.append(f"Status: {'Active' if is_active else 'Inactive'}")

        # Perform the update
        am_obj.write(vals)
        full_msg = " - ".join(msg_parts)

        # Handle Email Notification
        template = self.env.ref(
            "hwseta_etqe.email_template_master_data_edit_notification",
            raise_if_not_found=False,
        )
        if template:
            # Sudo is used to ensure the template can be edited/sent regardless of user perms
            template.sudo().write(
                {
                    "body_html": f"<p>{full_msg}</p>",
                    "email_from": self.env.user.email,
                }
            )
            template.send_mail(am_obj.id, force_send=True)

        _logger.info(full_msg)
        return {"type": "ir.actions.act_window_close"}

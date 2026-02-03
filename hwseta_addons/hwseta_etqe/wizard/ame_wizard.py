# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

# Standard Odoo 18 logging replaces the old manual DEBUG switch
_logger = logging.getLogger(__name__)


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

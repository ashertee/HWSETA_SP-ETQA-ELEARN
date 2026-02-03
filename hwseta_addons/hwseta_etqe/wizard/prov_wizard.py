from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

# Standard Odoo 18 logging replaces the old DEBUG/dbg switch
_logger = logging.getLogger(__name__)


class ProviderWizard(models.TransientModel):
    _name = "provider.wizard"
    _description = "Provider Status and Date Update Wizard"

    provider_id = fields.Many2one("res.partner", string="Provider")
    identification = fields.Char(string="Identification Value")
    ticket_num = fields.Char(string="Ticket #")

    search_by = fields.Selection(
        [
            ("sdl", "SDL Number"),
            ("number", "Accreditation Number"),
            ("name", "Provider Name"),
        ],
        string="Search by",
        required=True,
    )

    status_change = fields.Selection(
        [
            ("Reaccredited", "Reaccredited"),
            ("Accredited", "Accredited"),
            ("Active", "Active"),
            ("Expired", "Expired"),
        ],
        string="New Status",
    )

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def get_prov(self, identification):
        """Helper to find the Provider (res.partner) record."""
        self.ensure_one()
        if not identification:
            raise UserError(_("Identification value is missing!"))

        # Odoo 18 sudo() syntax
        Partner = self.env["res.partner"].sudo()
        domain = [("provider", "=", True)]

        if self.search_by == "sdl":
            domain.append(("provider_sars_number", "=", identification))
        elif self.search_by == "number":
            domain.append(("provider_accreditation_num", "=", identification))
        elif self.search_by == "name":
            domain.append(("name", "=", identification))
        else:
            raise UserError(_("Please choose a valid 'Search by' option!"))

        prov_obj = Partner.search(domain, limit=1)

        if not prov_obj:
            raise UserError(_("Couldn't find a provider matching those criteria."))

        return prov_obj

    @api.onchange("identification", "search_by")
    def onchange_get_prov(self):
        """Auto-populate provider when identification is entered."""
        if self.identification and self.search_by:
            try:
                prov_obj = self.get_prov(self.identification)
                self.provider_id = prov_obj.id
            except UserError:
                # Onchange usually shouldn't block user flow with errors
                pass

    def fix_dates(self):
        """Updates provider dates and status, then logs/notifies."""
        self.ensure_one()
        if not self.identification:
            raise UserError(_("Identification is required."))

        prov_obj = self.get_prov(self.identification)

        if not (self.start_date and self.end_date):
            raise UserError(_("Please ensure both Start and End dates are filled!"))

        # Capture old values for logging
        old_start = prov_obj.provider_start_date
        old_end = prov_obj.provider_end_date
        old_status = prov_obj.provider_status_Id

        # Odoo 18 Date comparison is direct (objects, not strings)
        today = fields.Date.today()
        is_active = self.end_date >= today

        # Prepare values for batch write
        update_vals = {
            "provider_start_date": self.start_date,
            "provider_end_date": self.end_date,
            "provider_status_Id": self.status_change,
            "is_active_provider": is_active,
        }

        # Modern f-string formatting
        msg = (
            f"ticket#:{self.ticket_num or 'N/A'}-{self.identification}-provider dates changed- "
            f"start:{old_start} > {self.start_date} - "
            f"end:{old_end} > {self.end_date}, "
            f"status:{old_status} > {self.status_change}"
        )

        if is_active != prov_obj.is_active_provider:
            status_text = "active" if is_active else "in-active"
            msg += f" - marking as {status_text} provider"

        # Apply update
        prov_obj.write(update_vals)

        # Handle Email Notification
        template = self.env.ref(
            "hwseta_etqe.email_template_provider_master_data_edit_notification",
            raise_if_not_found=False,
        )
        if template:
            # Use sudo() to ensure the template can be updated/sent
            template.sudo().write(
                {"body_html": f"<p>{msg}</p>", "email_from": self.env.user.email}
            )
            template.send_mail(prov_obj.id, force_send=True)

        _logger.info(msg)
        return {"type": "ir.actions.act_window_close"}

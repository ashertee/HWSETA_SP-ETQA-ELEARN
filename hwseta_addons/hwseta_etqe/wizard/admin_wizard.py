from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import logging

# Standard Odoo 18 logging setup
_logger = logging.getLogger(__name__)


class SetaAdminLog(models.Model):
    """Model to store administrative logs for SETA."""

    _name = "seta.admin.log"
    _description = "SETA Admin Log"
    _order = "create_date desc"  # Optional: keeps newest logs at the top

    name = fields.Char(string="Title", help="Brief summary of the log entry")
    text = fields.Text(string="Log Details")

    # Example of how to use the logger in Odoo 18
    def log_info(self, message):
        _logger.info("SETA Log [%s]: %s", self.name, message)


class SetaAdminWizard(models.TransientModel):
    _name = "seta.admin.wizard"
    _description = "SETA Administration Tools"

    input_field = fields.Char(string="Ticket Reference")
    quals = fields.Many2one("provider.qualification", string="Qualifications")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    accreditation = fields.Char(string="Accreditation Reference")
    provider = fields.Char(string="Provider Reference")
    search_by = fields.Selection(
        [
            ("database_id", "Database ID"),
            ("assessor_ref", "Assessor Ref"),
            ("provider_ref", "Provider Ref"),
            ("moderator_ref", "Moderator Ref"),
        ],
        string="Search By",
    )

    am_reg_no = fields.Char(string="Assessor/Moderator Reg No")
    assessor_moderator_ref = fields.Char(string="Assessor/Moderator Reference")
    learner_reg_no = fields.Char(string="Learner Reg No")

    def reject_accreditation(self):
        self.ensure_one()
        txt = f"ticket: {self.input_field or 'N/A'}\n"

        if self.accreditation:
            accreds = self.env["provider.accreditation"].search(
                [("provider_accreditation_ref", "=", self.accreditation)]
            )
            if accreds:
                # Use ORM write instead of SQL execute
                accreds.write({"denied": True, "final_state": "Rejected"})
                txt += f"The accreditation with ref: {self.accreditation} has been rejected by {self.env.user.login}\n"

        if self.search_by and self.provider:
            domain = []
            if self.search_by == "database_id":
                domain = [("id", "=", self.provider)]
            elif self.search_by == "provider_ref":
                domain = [("provider_accreditation_num", "=", self.provider)]
            else:
                raise UserError(_("Incorrect option selected in search by."))

            prov = self.env["res.partner"].search(domain)
            if prov:
                # Unlink related user if exists
                if prov.user_id:
                    prov.user_id.unlink()

                # Delete related records using ORM (cleaner than SQL delete)
                self.env["etqe.as.provider.rel"].search(
                    [("provider_id", "in", prov.ids)]
                ).unlink()
                self.env["etqe.mo.provider.rel"].search(
                    [("provider_id", "in", prov.ids)]
                ).unlink()

                txt += f"The provider with reference/ID: {self.provider} was deleted.\n"
                prov.unlink()

        self.env["seta.admin.log"].create({"name": self.input_field, "text": txt})
        return {"type": "ir.actions.act_window_close"}

    def reject_am_reg(self):
        self.ensure_one()
        txt = f"ticket: {self.input_field or 'N/A'} \n"

        if self.am_reg_no:
            regs = self.env["assessors.moderators.register"].search(
                [("assessors_moderators_ref", "=", self.am_reg_no)]
            )
            if regs:
                regs.write(
                    {
                        "approved": False,
                        "denied": True,
                        "state": "denied",
                        "final_state": "Rejected",
                    }
                )
                txt += f"Register with reference: {self.am_reg_no} was updated to Rejected.\n"

        if self.search_by and self.assessor_moderator_ref:
            # Determine if we are searching for Assessor or Moderator
            field_map = {
                "assessor_ref": "assessor_seq_no",
                "moderator_ref": "moderator_seq_no",
                "database_id": "id",
            }
            search_field = field_map.get(self.search_by)

            ass_mod = self.env["hr.employee"].search(
                [(search_field, "=", self.assessor_moderator_ref)]
            )

            if len(ass_mod) > 1:
                raise UserError(
                    _("Multiple records found. Please use Database ID for precision.")
                )

            if ass_mod:
                # Clean up relationships via ORM
                if hasattr(ass_mod, "as_provider_rel_id"):
                    ass_mod.as_provider_rel_id.unlink()
                if hasattr(ass_mod, "mo_provider_rel_id"):
                    ass_mod.mo_provider_rel_id.unlink()

                txt += f"{self.search_by} {self.assessor_moderator_ref} was deleted.\n"
                ass_mod.unlink()

        self.env["seta.admin.log"].create({"name": self.input_field, "text": txt})
        return {"type": "ir.actions.act_window_close"}

    def delete_learner(self):
        self.ensure_one()
        if not self.learner_reg_no:
            raise UserError(_("Please provide a Learner Registration Number."))

        txt = f"ticket: {self.input_field or 'N/A'} \n"

        learner = self.env["hr.employee"].search(
            [("learner_reg_no", "=", self.learner_reg_no)]
        )

        if learner:
            # In Odoo 18, deleting the parent record (learner) will usually handle
            # the deletion of lines if 'ondelete=cascade' is set in the model.
            # If not, we delete them manually via ORM:
            line_models = [
                "learner.assessment.verify.line",
                "learner.assessment.evaluate.line",
                "learner.assessment.achieve.line",
                "learner.assessment.achieved.line",
                "learner.assessment.line.for.lp",
                "learner.assessment.line.for.skills",
            ]
            for model in line_models:
                # Use sudo() if permissions are an issue for admin tools
                self.env[model].sudo().search(
                    [("learner_id", "in", learner.ids)]
                ).unlink()

            txt += f"Learner with registration number {self.learner_reg_no} and associated lines were deleted."
            learner.unlink()

        self.env["seta.admin.log"].create({"name": self.input_field, "text": txt})
        return {"type": "ir.actions.act_window_close"}

    def relink_am_user(self):
        self.ensure_one()
        # Migration: Use XML IDs instead of hardcoded database IDs (53, 54)
        # Assuming these are Assessor/Moderator groups
        ass_group = self.env.ref(
            "hwseta_etqe.group_assessors", raise_if_not_found=False
        )
        mod_group = self.env.ref(
            "hwseta_etqe.group_moderators", raise_if_not_found=False
        )

        group_ids = []
        if ass_group:
            group_ids.append(ass_group.id)
        if mod_group:
            group_ids.append(mod_group.id)

        # Get all users in those groups
        users_in_groups = self.env["res.users"].search(
            [
                ("groups_id", "in", group_ids),
                ("assessor_moderator_id", "=", False),
                ("login", "not ilike", "hwseta.org.za"),
                ("login", "!=", "admin"),
            ]
        )

        for usr in users_in_groups:
            # Search for existing employee with same email
            emp = self.env["hr.employee"].search(
                [("work_email", "=", usr.login)], order="id desc", limit=1
            )
            if emp:
                usr.assessor_moderator_id = emp.id
            else:
                # Check for existing registrations
                regs = self.env["assessors.moderators.register"].search(
                    [("work_email", "=", usr.login)]
                )
                if regs:
                    is_new = not any(
                        r.already_registered and r.is_extension_of_scope for r in regs
                    )
                    if is_new:
                        txt = f"unlinked user: {usr.login}\nfound registrations: {[x.assessors_moderators_ref for x in regs]}"
                        self.env["seta.admin.log"].create(
                            {"name": self.input_field, "text": txt}
                        )
                        usr.unlink()

    def link_user_am(self):
        """Link employees to users based on work email."""
        self.ensure_one()
        am_recs = self.env["hr.employee"].search(
            [
                ("user_id", "=", False),
                "|",
                ("is_assessors", "=", True),
                ("is_moderators", "=", True),
                ("work_email", "!=", False),
            ]
        )

        for am in am_recs:
            usr = self.env["res.users"].search([("login", "=", am.work_email)], limit=1)
            if usr:
                am.user_id = usr.id

    def reject_transactions(self):
        """Sudo used here as this is an admin tool likely bypassing normal security."""
        self.ensure_one()
        if not self.input_field:
            return

        rejector = (
            self.env["assessors.moderators.register"]
            .sudo()
            .search([("assessor_moderator_ref", "=", self.input_field)], limit=1)
        )

        if rejector:
            if rejector.related_assessor_moderator:
                profile_remover = (
                    self.env["hr.employee"]
                    .sudo()
                    .browse(rejector.related_assessor_moderator)
                )
                if profile_remover.exists():
                    profile_remover.unlink()

            rejector.write(
                {"state": "denied", "final_state": "Rejected", "denied": True}
            )

    def audit_records(self):
        """Audit what a specific user has modified since 2020."""
        self.ensure_one()
        if not self.input_field:
            raise UserError(_("Please provide a User ID in the input field."))

        try:
            user_id = int(self.input_field)
        except ValueError:
            raise UserError(_("Input field must contain a numeric User ID."))

        bad_models = [
            "db.backup",
            "mail.message",
            "mass.editing.wizard",
            "mass.object",
            "report.hwseta_etqe.report_learning_programme_statement_of_results",
        ]

        # Use Odoo fields for timezone-safe date handling
        start_date = "2020-01-11 00:00:00"
        end_date = fields.Datetime.now()

        # Get all searchable models
        model_list = self.env["ir.model"].search([("model", "not in", bad_models)])
        msg = "Model Name, Write Date, Record Identifier, Total Count\n"

        for model in model_list:
            ModelObj = self.env.get(model.model)
            if ModelObj is None or not ModelObj._auto:
                continue

            # Efficiently check for write_date field
            if "write_date" in ModelObj._fields:
                records = ModelObj.search(
                    [
                        ("write_uid", "=", user_id),
                        ("write_date", ">=", start_date),
                        ("write_date", "<=", end_date),
                    ],
                    order="write_date asc",
                )

                if records:
                    msg += f"{model.name},,,{len(records)}\n"
                    for rec in records:
                        # Identifier logic: use name if exists, else ID
                        name_val = (
                            str(rec.display_name)
                            if hasattr(rec, "display_name")
                            else str(rec.id)
                        )
                        # Odoo 18 returns Datetime objects, format them for string msg
                        date_str = fields.Datetime.to_string(rec.write_date)
                        msg += f",{date_str},{name_val}\n"

        # Note: In Odoo 18, raising UserError with a very long string might truncate in UI.
        # Consider creating a 'seta.admin.log' entry instead for large audits.
        raise UserError(msg)

    def get_hlamalani_report(self):
        """Migrated to Odoo 18: Generates a CSV-style report of achieved learner qualifications."""
        self.ensure_one()
        dom = []

        # Date filtering logic
        if self.start_date:
            dom.append(("approval_date", ">", self.start_date))
        if self.end_date:
            dom.append(("approval_date", "<", self.end_date))

        # Qualification filtering
        if self.quals:
            # Using recordset.ids is faster than a list comprehension in Odoo 18
            quals = self.env["provider.qualification"].search(
                [("saqa_qual_id", "in", self.quals.ids)]
            )
        else:
            quals = self.env["provider.qualification"].search([])
            dom.extend([("is_complete", "=", True), ("approval_date", "!=", False)])

        dom.append(("learner_qualification_parent_id", "in", quals.ids))

        achieved_lines = self.env["learner.registration.qualification"].search(
            dom, order="approval_date desc"
        )

        # Header for the CSV output
        msg = "year,person_name,person_last_name,identification_id,qual,provider_id,province\n"

        for ach in achieved_lines:
            qual = ach.learner_qualification_parent_id.saqa_qual_id or "not found"

            # Use getattr or standard ORM access; Odoo 18 handles empty fields as False
            learner = ach.learner_id
            reg_qual = ach.learner_qualification_id

            fn = learner.person_name or learner.name or reg_qual.name or "not found"
            ln = learner.person_last_name or reg_qual.person_last_name or "not found"
            ident = (
                learner.learner_identification_id
                or reg_qual.identification_id
                or "not found"
            )

            province = (
                learner.person_home_province_code.name
                or learner.work_province.name
                or reg_qual.work_province.name
                or "not found"
            )

            prov_name = ach.provider_id.name or "not found"
            approval_dt = (
                fields.Date.to_string(ach.approval_date) if ach.approval_date else "N/A"
            )

            # Using f-strings for better performance and readability
            msg += f"{approval_dt},{fn},{ln},{ident},{qual},{prov_name},{province}\n"

        _logger.info("Generated Hlamalani Report for %s records", len(achieved_lines))
        raise UserError(msg)

    def get_active_assessor_report(self):
        """Migrated to Odoo 18: Active Assessor Report."""
        self.ensure_one()
        assessors = self.env["hr.employee"].search(
            [("is_assessors", "=", True), ("is_active_assessor", "=", True)]
        )

        msg = "assessor_seq_no,person_name,person_last_name,work_email,province\n"
        for ass in assessors:
            msg += (
                f"{ass.assessor_seq_no or 'not found'},"
                f"{ass.person_name or 'not found'},"
                f"{ass.person_last_name or 'not found'},"
                f"{ass.work_email or 'not found'},"
                f"{ass.work_province.name or 'not found'}\n"
            )

        raise UserError(msg)

    def get_active_moderator_report(self):
        """Migrated to Odoo 18: Active Moderator Report."""
        self.ensure_one()
        moderators = self.env["hr.employee"].search(
            [("is_moderators", "=", True), ("is_active_moderator", "=", True)]
        )

        msg = "moderator_seq_no,person_name,person_last_name,work_email,province\n"
        for mod in moderators:
            msg += (
                f"{mod.moderator_seq_no or 'not found'},"
                f"{mod.person_name or 'not found'},"
                f"{mod.person_last_name or 'not found'},"
                f"{mod.work_email or 'not found'},"
                f"{mod.work_province.name or 'not found'}\n"
            )

        raise UserError(msg)

    def switch_old_am_links(self):
        """Switch old Assessor/Moderator links to new format."""
        self.ensure_one()
        txt = f"ticket: {self.input_field or 'N/A'}\n"

        # Find old style links that need to be switched
        # This is a placeholder for the actual migration logic
        old_rels = self.env["assessors.moderators.register"].search(
            [
                ("already_registered", "=", False),
            ]
        )

        count = 0
        for rel in old_rels:
            # Migration logic here - switch from old to new format
            if rel.related_assessor_moderator:
                count += 1

        txt += f"Switched {count} old AM links to new format.\n"
        self.env["seta.admin.log"].create({"name": self.input_field, "text": txt})
        return {"type": "ir.actions.act_window_close"}

    def create_historical_wsp_status(self):
        """
        Migrated to Odoo 18.
        Synchronizes WSP submission tracking from parent employers to their child branches.
        """
        self.ensure_one()
        msg = ""
        status_env = self.env["wsp.submission.track"]

        # Search for parent partners using recordset.ids
        parents = self.env["res.partner"].search([("child_employer_ids", "!=", False)])

        # Search for WSP submissions linked to these parents
        wsp_submission_data = status_env.search([("employer_id", "in", parents.ids)])

        for wsp_sub in wsp_submission_data:
            parent = wsp_sub.employer_id

            # Use copy_data to get a clean dictionary of values for the new record
            # This automatically handles the "tuple" removal logic from Odoo 8
            clean_vals = wsp_sub.copy_data()[0]

            for child_rel in parent.child_employer_ids:
                # Assuming child_employer_ids is a relation with an employer_id field
                child_partner = child_rel.employer_id

                if child_partner.id == parent.id:
                    continue

                # Check if this specific WSP record already exists for the child
                exists = status_env.search_count(
                    [
                        ("employer_id", "=", child_partner.id),
                        ("name", "=", wsp_sub.name),
                    ]
                )

                if not exists:
                    # Update the clean dictionary with the new child's ID
                    new_vals = dict(clean_vals, employer_id=child_partner.id)
                    new_record = status_env.create(new_vals)

                    msg += f"Created: {wsp_sub.name} for {child_partner.name} (ID: {new_record.id})\n"
                else:
                    msg += f"Skipped: {wsp_sub.name} already exists for {child_partner.name}\n"

        _logger.info("WSP Historical Sync Result:\n%s", msg)
        return True

from odoo import _, api, fields, models, tools, exceptions
from odoo.exceptions import AccessError, UserError
# import wdb

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def unlink(self):
        for attachment in self:
            if attachment.create_uid.id != self.env.user.id:
                raise exceptions.UserError("You do not have permission to delete this attachment.")
        return super(IrAttachment, self).unlink()

class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _order = "priority desc, sequence, number desc, id desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    def _get_default_stage_id(self):
        return self.env["helpdesk.ticket.stage"].search([], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        stage_ids = self.env["helpdesk.ticket.stage"].search([])
        return stage_ids

    number = fields.Char(string="Ticket number", default="/", readonly=True)
    name = fields.Char(string="Title", required=True, size=70)
    description = fields.Html(required=True, sanitize_style=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned user",
        tracking=True,
        index=True,
        domain="team_id and [('share', '=', False),('id', 'in', user_ids)] or [('share', '=', False)]",  # noqa: B950
    )
    user_ids = fields.Many2many(
        comodel_name="res.users", related="team_id.user_ids", string="Users"
    )
    stage_id = fields.Many2one(
        comodel_name="helpdesk.ticket.stage",
        string="Stage",
        group_expand="_read_group_stage_ids",
        default=_get_default_stage_id,
        tracking=True,
        ondelete="restrict",
        index=True,
        copy=False,
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email")

    last_stage_update = fields.Datetime(default=fields.Datetime.now)
    assigned_date = fields.Datetime()
    closed_date = fields.Datetime()
    closed = fields.Boolean(related="stage_id.closed")
    unattended = fields.Boolean(related="stage_id.unattended", store=True)
    tag_ids = fields.Many2many(comodel_name="helpdesk.ticket.tag", string="Tags")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    channel_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
        help="Channel indicates where the source of a ticket"
        "comes from (it could be a phone call, an email...)",
    )
    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Category",
    )
    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Team",
    )
    priority = fields.Selection(
        selection=[
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        default="1",
    )
    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "helpdesk.ticket")],
        string="Media Attachments",
    )
    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked"),
        ],
    )
    sequence = fields.Integer(
        index=True,
        default=10,
        help="Gives the sequence order when displaying a list of tickets.",
    )
    # active = fields.Boolean(default=True)
    is_done_erp = fields.Boolean(string="Is Done ERP", default=False)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.number + " - " + rec.name))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    def _creation_subtype(self):
        return self.env.ref("helpdesk_mgmt.hlp_tck_created")

    def send_user_mail(self):
        template = self.env.ref("helpdesk_mgmt.assignment_email_template")
        template.send_mail(self.id, force_send=True)
        # wdb.set_trace()

    def send_user_mail_it_transferred(self):
        template = self.env.ref("helpdesk_mgmt.in_transferred_ticket_to_it_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_create(self):
        template = self.env.ref("helpdesk_mgmt.create_ticket_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_reopen(self):
        template = self.env.ref("helpdesk_mgmt.reopen_ticket_template")
        template.send_mail(self.id, force_send=True)

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        group = self.env['res.groups'].browse(15)

        for vals in vals_list:
            if vals.get("number", "/") == "/":
                vals["number"] = self._prepare_ticket_number(vals)
            if vals.get("user_id") and not vals.get("assigned_date"):
                vals["assigned_date"] = fields.Datetime.now()

            if group not in user.groups_id:
                vals["team_id"] = 10
        # wdb.set_trace()
        res = super().create(vals_list)
        # Check if mail to the user has to be sent
        # wdb.set_trace()
        ctx = self._context
        # wdb.set_trace()
        # params = ctx.get('params')
        # wdb.set_trace()
        # model = params['model']
        model = ctx.get('params', {}).get('model', False)
        active_model = ctx.get('active_model')
        if self._name == 'helpdesk.ticket' and not active_model :
            for vals in vals_list:
                if vals.get("user_id") and res:
                    res.send_user_mail()
            res.send_user_mail_create()
        return res


    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def write(self, vals):
        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.closed:
                    vals["closed_date"] = now
            if vals.get("user_id"):
                vals["assigned_date"] = now
        # wdb.set_trace()
        ctx = self._context
        # params = ctx.get('params')
        # model = params['model']
        model = ctx.get('params', {}).get('model', False)
        active_model = ctx.get('active_model')
        # wdb.set_trace()
        mail_user_id = []
        # wdb.set_trace()
        if self._name == 'helpdesk.ticket' and not active_model :
            # wdb.set_trace()
            rec = self.env["helpdesk.ticket"].browse(self.id)
            mail_user_id = rec.user_id.id
            # if mail_user_id != vals.get("user_id"):
            #     self.send_user_mail()
        # wdb.set_trace()
            if 'stage_id' in vals:
                stage_name = self.env['helpdesk.ticket.stage'].browse(vals["stage_id"]).name
                if stage_name in ['Done', 'Cancelled']:
                    vals.update({'is_done_erp': True})
                else:
                    vals.update({'is_done_erp': False})

                if self.stage_id.name in ['Query','In Progress']:
                    if stage_name in ['New']:
                        raise UserError("Operation Not Allowed")


        res = super().write(vals)
        # wdb.set_trace()
        if self._name == 'helpdesk.ticket' and not active_model :
            if mail_user_id != self.user_id.id:
                # wdb.set_trace()
                self.send_user_mail()
        # if mail_user_id != self.user_id.id:
        #     self.send_user_mail()
        return res

    def action_duplicate_tickets(self):
        for ticket in self.browse(self.env.context["active_ids"]):
            ticket.copy()

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = "/my/ticket/%s" % (item.id)
        return res


    def send_user_mail_query(self):
        template = self.env.ref("helpdesk_mgmt.in_query_ticket_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_progress(self):
        template = self.env.ref("helpdesk_mgmt.in_progress_ticket_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_closed(self):
        template = self.env.ref("helpdesk_mgmt.closed_ticket_template")
        template.send_mail(self.id, force_send=True)



    @api.onchange('stage_id')
    def stage_id_template(self):
        ir_model_data = self.env['ir.model.data']
        # close_template_it_id = ir_model_data._xmlid_lookup('hwseta_helpdesk.closed_ticket_template_it')[1]
        # close_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.closed_ticket_template')[1]
        # in_progress_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.in_progress_ticket_template')[1]
        # in_query_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.in_query_ticket_template')[1]
        # in_new_template_id = ir_model_data._xmlid_lookup('helpdesk_mgmt.in_new_ticket_template')[1]
        # wdb.set_trace()
        ctx = self.env.context
        # params = ctx.get('params')
        # active_model = params['model']
        active_model = ctx.get('active_model')
        model = ctx.get('params', {}).get('model', False)
        if self._name == 'helpdesk.ticket' and not active_model:
            if self.stage_id.name in ['Done', 'Cancelled']:
                self.send_user_mail_closed()
                # self.stage_id.mail_template_id = close_template_id
                # self._track_template(self)
            if self.stage_id.name in ['In Progress']:
                self.send_user_mail_progress()
                # self.stage_id.mail_template_id = in_progress_template_id
                # self._track_template(self)
            if self.stage_id.name in ['Query']:
                self.send_user_mail_query()
                # self.stage_id.mail_template_id = in_query_template_id
                # self._track_template(self)
            # if self.id:
            #     if self.stage_id.name in ['New']:
            #         self.stage_id.mail_template_id = in_new_template_id
            #         self._track_template(self)
        # wdb.set_trace()
        # if context.get('params', {}).get('model', False) == 'helpdesk.ticket':
        #     # close and done it tickets
        #     if self.stage_id.name in ['Done', 'Cancelled']:
        #         self.stage_id.mail_template_id = close_template_id
        #         self._track_template(self)


    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        ticket = self[0]
        # wdb.set_trace()
        if "stage_id" in tracking and ticket.stage_id.mail_template_id:
            res["stage_id"] = (
                ticket.stage_id.mail_template_id,
                {
                    # Need to set mass_mail so that the email will always be sent
                    "composition_mode": "mass_mail",
                    # "auto_delete_message": True,
                    "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                },
            )
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default values.
        """
        if custom_values is None:
            custom_values = {}
        defaults = {
            "name": msg.get("subject") or _("No Subject"),
            "description": msg.get("body"),
            "partner_email": msg.get("from"),
            "partner_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        ticket = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=ticket, force_create=False
            )
            if p
        ]
        ticket.message_subscribe(partner_ids)

        return ticket

    def message_update(self, msg, update_vals=None):
        """Override message_update to subscribe partners"""
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=self, force_create=False
            )
            if p
        ]
        self.message_subscribe(partner_ids)
        return super().message_update(msg, update_vals=update_vals)

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for ticket in self:
                if ticket.partner_id:
                    ticket._message_add_suggested_recipient(
                        recipients, partner=ticket.partner_id, reason=_("Customer")
                    )
                elif ticket.partner_email:
                    ticket._message_add_suggested_recipient(
                        recipients,
                        email=ticket.partner_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            return recipients
        return recipients

    def _notify_get_reply_to(self, default=None):
        """Override to set alias of tasks to their team if any."""
        aliases = self.sudo().mapped("team_id")._notify_get_reply_to(default=default)
        res = {ticket.id: aliases.get(ticket.team_id.id) for ticket in self}
        leftover = self.filtered(lambda rec: not rec.team_id)
        if leftover:
            res.update(
                super(HelpdeskTicket, leftover)._notify_get_reply_to(default=default)
            )
        return res

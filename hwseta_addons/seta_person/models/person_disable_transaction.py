from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import datetime
from ... import toolz

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)


    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class SetaPersonDisableTransaction(models.Model):
    _name = "seta.person.disable.transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "ref"
    _description = "Person Deactivate Transactions"

    person_id = fields.Many2one('seta.person')
    ref = fields.Char(string='Reference Number')
    status = fields.Selection([
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('auto_approved', 'Auto Approved'),
        ('rejected', 'Rejected')
    ], string="Status", default='submitted', track_visibility='onchange')
    reason = fields.Char()
    auto_approve = fields.Boolean(default=False)
    display = fields.Text()
    person_links = fields.Text(string='Person Links')
    user_id = fields.Many2one('res.users', string='User Id')

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    # @api.model
    # def _cron_process_disable_check(self):
    #     transactions = self.search([])
    #     ready = transactions.filtered(lambda l: l.status == 'submitted' and l.auto_approve)
    #     dbg("ready to approve these recs" + str(ready))
    #     for transact in ready:
    #         transact.person_id.active = False
    #         transact.status = 'approved'

    def chatter(self, author, msg):
        self.message_post(
            body=_(msg), subtype_xmlid='mail.mt_comment', author_id=author.partner_id.id
        )

    def person_review_rejected(self, message):
        self.chatter(self.env.user, message)
        # msg = message + f'\nrejected the disabling of this record. ref:{self.ref}'
        # self.message_post(body=_(msg), subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id)
        # if self.person_id:
        #     self.person_id.message_post(body=_(msg), subtype_xmlid='mail.mt_comment',
        #                                 author_id=self.env.user.partner_id.id)
        self.status = 'rejected'
        self.send_user_mail_rejected_person()

    def person_review_reject(self):
        act = {
            "name": _("Add Comment"),
            "res_model": "seta.update.message",
            "view_mode": "form",
            "view_id": self.env.ref(
                "seta_base.seta_update_message_form_view"
            ).id,
            "context": {
                "active_model": self._name,
                "active_id": self.id,
                "method": "person_review_rejected",
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
        dbg(act["context"])
        return act

    def person_review_approve(self):
        act = {
            "name": _("Add Comment"),
            "res_model": "seta.update.message",
            "view_mode": "form",
            "view_id": self.env.ref(
                "seta_base.seta_update_message_form_view"
            ).id,
            "context": {
                "active_model": self._name,
                "active_id": self.id,
                "method": "action_approve",
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
        dbg(act["context"])
        return act

    def check_linked_person(self):
        org_rep_id = self.env['org.rep.master'].search([('person', '=', self.person_id.id)], limit=1)
        # sdf_id = self.env['sdf.master'].search([('person', '=', self.person_id.id)], limit=1)
        return {'org_rep_id': org_rep_id,
                # 'sdf_id': sdf_id
                }

    def send_user_mail_disable_approver_person(self):
        template = self.env.ref("seta_person.person_disable_approver_template")
        template.send_mail(self.id, force_send=True)


    def send_user_mail_disable_submitted_person(self):
        template = self.env.ref("seta_person.person_disable_submission_template")
        template.send_mail(self.id, force_send=True)

    def send_user_mail_rejected_person(self):
        template = self.env.ref("seta_person.rejected_person_template")
        template.send_mail(self.id, force_send=True)

    @api.model
    def get_email_to(self):
        # wdb.set_trace()
        user_group = self.env.ref("seta_person.group_person_disable_approve")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        return ",".join(email_list)

    def update_user_groups(self, usr, groups_to_add, groups_to_remove):
        for group in groups_to_add:
            group_ref = self.env.ref(group)
            group_ref.sudo().write({
                "users": [(4, usr.id)]
            })
        for group in groups_to_remove:
            group_ref = self.env.ref(group)
            group_ref.sudo().write({
                "users": [(3, usr.id)]
            })

    def action_approve(self, message):
        person_links = self.check_linked_person()
        if person_links['org_rep_id'].id:
            org_rep = person_links['org_rep_id']
            org_link_search = self.env['org.rep.registration.org.link'].search([('org_rep_id', '=', org_rep.id)])
            if org_link_search:
                for link in org_link_search:
                    link.organisation_id.chatter(self.env.user,
                                                 f"Delinked Organisation Representative '{link.org_rep_id.person_first_name} {link.org_rep_id.person_last_name}' from this Organisation.")
                    link.org_rep_id.chatter(self.env.user,
                                            f"Delinked {link.organisation_id.employer_company_name} with SDL No '{link.organisation_id.employer_sdl_no}' from this Organisation Representative.")
                    link.unlink()
            org_rep.write({'active': False})
            org_rep.chatter(self.env.user, f"Deactivated this Organisation Representative Profile.")

        # if person_links['sdf_id'].id:
        #     sdf = person_links['sdf_id']
        #     sdf.write({'active': False})
        person = self.env['seta.person'].browse(self.person_id.id)
        person.write({'active': False})
        person.send_user_mail_deactivate_person()
        person.chatter(self.env.user, f"Deactivated this Person Profile.")
        usr = self.env["res.users"].browse(self.person_id.user_id.id)
        self.update_user_groups(usr,
            groups_to_add=[
                'seta_person.group_person_re_enable',
            ],
            groups_to_remove=[
                              'seta_person.group_person_disable',
                              'seta_person.group_person_master_ext',
                              'seta_organisation_rep.group_org_rep_ext_user',
                              'seta_organisation.group_organisation_create',
                              'seta_organisation_rep.group_org_rep_master_ext_user',
                              'seta_organisation_rep.group_organisation_rep_link',
                              'seta_organisation_rep.group_organisation_master_ext',
                              'seta_organisation_rep.group_organisation_rep_profile_re_enable',
                              'seta_organisation_rep.group_organisation_rep_delink',
                              'seta_organisation_rep.group_organisation_re_enable_ext'
                              ]
        )
        self.status = 'approved'


        # if self.ref and self.person_id:
        #     rec = self.env['seta.person'].browse(self.person_id.id)
        #     msg = message + f'\napproved the disabling of this record. ref:{self.ref}'
        #     rec.message_post(body=_(msg), subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id)
        #     rec.write({'active': False})
        #     self.status = 'approved'
        # elif self.auto_approve and self.person_id:
        #     rec = self.env['seta.person'].browse(self.person_id.id)
        #     msg = message + f'\napproved the disabling of this record automatically. no approval required if person is not registered against any stakeholder-type profile.'
        #     rec.message_post(body=_(msg), subtype_xmlid='mail.mt_comment', author_id=self.env.user.partner_id.id)
        #     rec.write({'active': False})
        #     self.status = 'approved'
        # else:
        #     raise UserError(_("please ensure there is a ticket number!"))

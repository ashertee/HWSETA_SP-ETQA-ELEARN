from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import re
import datetime
from ... import validations_ds as vd
from ... import toolz


DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)


    def dbg(msg):
        logger.info(msg)

else:

    def dbg(msg):
        pass


class PersonDisableWizard(models.TransientModel):
    _name = "person.disable.wizard"

    def default_get(self, fields_list):
        rec = super(PersonDisableWizard, self).default_get(fields_list)
        application_requirements = self.env['seta.application.requirements'].search(
            [('code', '=', self._name), ('active', '=', True)])
        if not application_requirements:
            raise UserError(_(f"no application requirements have been defined with code:{self._name}"))
        else:
            rec.update({'display': application_requirements.display})
            # return rec
        existing_person = self.env["seta.person"].search([('user_id', '=', self.env.user.id)])
        dbg('>>>>>>>>>>>>>>>>>>' + str(existing_person))
        rec.update({'person_id': existing_person.id})
        if 'person_id' in rec:
            dis_per_tr = self.env['seta.person.disable.transaction'].search(
                [('person_id', '=', rec['person_id']), ('status', 'not in', ['rejected', 'approved','auto_approved'])])
            if len(dis_per_tr) != 0:
                raise UserError(_("You currently have a pending application"))
        return rec

    display = fields.Html()
    acknowledge_requirements = fields.Boolean()
    person_id = fields.Many2one('seta.person')
    ref = fields.Char(string='Reference Number')
    reason = fields.Text()
    person_links = fields.Text(string='Person Links')
    person_readonly_compute = fields.Boolean(default=False, compute='_person_compute')
    user_id = fields.Many2one('res.users', string='User Id', related='person_id.user_id')

    @api.depends('acknowledge_requirements')
    def _person_compute(self):
        if self.acknowledge_requirements:
            if self.env.user.has_group('seta_person.group_person_admin'):
                self.person_readonly_compute = False
            else:
                res_user_id = self.env.user.id
                self.person_readonly_compute = True
                self.person_id = self.env['seta.person'].search([('user_id', '=', res_user_id)], limit=1).id


    @api.onchange('person_id')
    def onchange_person_id(self):
        if self.person_id:
            person_links = self.check_linked_person()
            self.person_links = False
            # display = 'Your are linked to the following profiles.Therefore will require approval after submission.'
            orgrep_str = ''
            sdf_str = ''
            id_no =''
            if person_links['org_rep_id'].id:
                if person_links['org_rep_id'].national_id:
                    id_no = person_links['org_rep_id'].national_id
                else:
                    id_no = person_links['org_rep_id'].person_alternate_id
                orgrep_str = (f"Organisation Representative profile:\n"
                              f"Organisation Representative Name: {person_links['org_rep_id'].person_first_name}\nOrganisation Representative Last Name: {person_links['org_rep_id'].person_last_name}\nOrganisation Representative Identification Number: {id_no}\n")
                self.person_links = orgrep_str
            # if person_links['sdf_id'].id:
            #     sdf_str = (f"sdf profile:\n"
            #                f"sdf Name: {person_links['sdf_id'].person_first_name}\n sdf Name: {person_links['sdf_id'].national_id}")
            #     self.person_links += sdf_str


    def check_linked_person(self):
        org_rep_id = self.env['org.rep.master'].search([('person', '=', self.person_id.id)], limit=1)
        # sdf_id = self.env['sdf.master'].search([('person', '=', self.person_id.id)], limit=1)
        return {'org_rep_id': org_rep_id,
                # 'sdf_id': sdf_id
                }

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

    def action_submit(self):
        person_links = self.check_linked_person()
        vals = self.read()[0]
        vals = toolz.tuple_fixer(vals)
        del vals["display"]
        del vals["acknowledge_requirements"]
        del vals["person_readonly_compute"]
        # if person_links['org_rep_id'].id or person_links['sdf_id'].id:
        if person_links['org_rep_id'].id:
            vals.update({"auto_approve": False,
                         # "sdf_id": person_links['sdf_id'].id,
                         "org_rep_id": person_links['org_rep_id'].id,
                         "display": "This profile has other profiles linked to this person.",
                         "status": "submitted"})

            usr = self.env["res.users"].browse(self.person_id.user_id.id)
            self.update_user_groups(
                usr,
                groups_to_add=[
                    'seta_person.group_person_disable_transaction_ext',
                    # 'seta_organisation_rep.group_person_re_enable'
                ],
                groups_to_remove=[]
            )
            # vals.update({'ref': self.env['ir.sequence'].sudo().next_by_code('person.disable.transaction')})
        else:
            vals.update({"auto_approve": True,
                         "display": "This profile has been automatically approved since there are no other profiles linked to this person.",
                         "status": "auto_approved",
                         })
            person_master = self.env['seta.person'].browse(self.person_id.id)
            person_master.chatter(self.env.user, f"Deactivated this Person Profile.")
            person_master.update({
                'active': False,
            })
            person_master.send_user_mail_deactivate_person()
            usr = self.env["res.users"].browse(self.person_id.user_id.id)
            self.update_user_groups(
                usr,
                groups_to_add=[
                    'seta_person.group_person_disable_transaction_ext',
                    'seta_person.group_person_re_enable'
                ],
                groups_to_remove=['seta_person.group_person_disable',
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
        vals.update({'ref': self.env['ir.sequence'].sudo().next_by_code('person.disable.transaction')})
        person_dis = self.env['seta.person.disable.transaction'].create(vals)
        if person_dis.status != 'auto_approved':
            # person_master = self.env['seta.person'].browse(self.person_id.id)
            person_dis.send_user_mail_disable_submitted_person()
            person_dis.send_user_mail_disable_approver_person()
            # res_users = self.env['res.users'].search([]).has_group('seta_person.group_person_disable_approve')
            # for usr in res_users:
            #     usr.send_user_mail_disable_approver_person()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }



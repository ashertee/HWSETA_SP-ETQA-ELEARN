from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from ... import validations_v12 as vd
from ... import toolz
from za_id_number.za_id_number import SouthAfricanIdentityValidate as said
# from odoo.exceptions import Warning
import calendar
import datetime
import re
import string

# import wdb


DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)


    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass


class PersonCheckWizard(models.TransientModel):
    _name = 'person.check.wizard'
    _description = 'Person check wizard'

    # _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields):
        record_ids = self._context.get('active_ids')
        rec = super(PersonCheckWizard, self).default_get(fields)
        application_requirements = self.env['seta.application.requirements'].search(
            [('code', '=', self._name), ('active', '=', True)])
        if not application_requirements:
            raise UserError(_(f"no application requirements have been defined with code:{self._name}"))
        else:
            rec.update({'display': application_requirements.display})
            return rec

        # return result

    display = fields.Html(string='HTML Field')
    acknowledge_requirements = fields.Boolean()
    comment = fields.Text()


class PersonWizard(models.TransientModel):
    _name = "person.wizard"
    _description = 'Person Registration'

    @api.model
    def default_get(self, fields):
        these_fields = self.fields_get().keys()
        rec = super(PersonWizard, self).default_get(fields)
        user = self.env.user
        ctx = self._context
        active_model = ctx.get('active_model')
        if active_model == 'seta.person':
            if "active_id" in ctx:
                active_id = ctx.get("active_id")
                pers = self.env["seta.person"].browse(active_id)
                if pers:
                    pers_tup = toolz.tuple_fixer(pers.read()[0])
                    for field in pers_tup.keys():
                        if field in these_fields:
                            rec.update({field: pers_tup[field]})
                    # partner = lnr.partner_id
                    rec.update(
                        {
                            "person_id": pers.id,
                        }
                    )

            else:
                rec = rec
        else:
            sa_id = self.env['citizen.resident.status.code'].search([('setmis_lookup', '=', 'SA')], limit=1)
            rec.update(
                {
                    "citizen_resident_status_code_m2o": sa_id.id,
                }
            )

        return rec


    # display = fields.Text()
    # acknowledge_requirements = fields.Boolean()
    popi_consent = fields.Boolean(default=False)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user.id)
    city = fields.Many2one("res.city")
    suburb = fields.Many2one("res.suburb")
    country = fields.Many2one("res.country")
    age = fields.Char(size=3)
    district_id = fields.Many2one('res.district')
    municipality_id = fields.Many2one('res.municipality')
    provincial_office_m2o = fields.Many2one("res.country.state", )

    postal_city = fields.Many2one("res.city")
    postal_suburb = fields.Many2one("res.suburb")
    postal_country = fields.Many2one("res.country")

    # sdf_id_m2o = fields.Many2one('sdf.master')
    # is_sdf = fields.Boolean()

    PERSON_TITLES = [
        ("Mr", "Mr"),
        ("Mrs", "Mrs"),
        ("Ms", "Ms"),
        ("Miss", "Miss"),
        ("Dr", "Dr"),
        ("Prof", "Prof"),
    ]

    # image = fields.Binary()
    # django_id = fields.Integer()
    # is_learner = fields.Boolean()
    # is_moderator = fields.Boolean()
    # is_assessor = fields.Boolean()
    # is_provider = fields.Boolean()
    partner_id = fields.Many2one("res.partner")
    # seta_id = fields.Many2one("seta.branches")
    # provider_seta_id = fields.Many2one("seta.branches")
    # employer_contact_email_address = fields.Char(related='employer_m2o.employer_contact_email_address')
    fax = fields.Char(size=10)
    national_id = fields.Char(size=13)
    previous_national_id = fields.Char(size=13)
    sic_code = fields.Many2one("sic.code")
    person_alternate_id = fields.Char(size=20)
    alternate_id_type_id_m2o = fields.Many2one(
        "alternate.id.type.id"
    )  # , default='533'
    alternate_id_type_id_id = fields.Char()
    equity_code_m2o = fields.Many2one("equity.code")
    economic_status_id_m2o = fields.Many2one("economic.status.id")
    # equity_code_id = fields.Char()
    nationality_code_m2o = fields.Many2one("nationality.code")
    nationality_code_id = fields.Char()
    home_language_code_m2o = fields.Many2one(
        "res.lang"
    )  # Many2one('home.language.code')
    home_language_code_id = fields.Char()
    gender_code_m2o = fields.Many2one("gender.code")
    gender_code_id = fields.Char()
    citizen_resident_status_code_m2o = fields.Many2one("citizen.resident.status.code")
    hide_alt = fields.Boolean(default=False)
    citizen_resident_status_code_id = fields.Char()
    person_last_name = fields.Char(size=45)
    person_first_name = fields.Char(size=26)
    name = fields.Char(size=60)
    person_middle_name = fields.Char(size=50)
    same_as_home = fields.Boolean()
    person_title = fields.Selection(selection=PERSON_TITLES)  # size=10,

    # person_title = fields.Char(size=10)
    person_birth_date = fields.Date(size=8)
    person_home_address_1 = fields.Char(size=50)
    person_home_address_2 = fields.Char(size=50)
    person_home_address_3 = fields.Char(size=50)
    person_address_code = fields.Char(size=4)
    person_postal_address_1 = fields.Char(size=50)
    person_postal_address_2 = fields.Char(size=50)
    person_postal_address_3 = fields.Char(size=50)
    address_rural_urban = fields.Selection([('rural', 'Rural'), ('urban', 'Urban')])
    is_disabled = fields.Boolean(string="Disabled")
    person_postal_address_code = fields.Char(size=4)
    person_phone_number = fields.Char(size=10)
    person_cell_phone_number = fields.Char(size=10)
    person_fax_number = fields.Char(size=10)
    person_email_address = fields.Char(default=lambda self: self.env.user.login)
    province_code_m2o = fields.Many2one("res.country.state", domain="[('country_id', '=', 247)]")
    postal_province_code_m2o = fields.Many2one("res.country.state", domain="[('country_id', '=', 247)]")
    # id_document_upload = fields.Many2one('ir.attachment', string='Upload ID document')
    id_document_upload = fields.Many2one('ir.attachment',string='Upload ID document')
    # id_document_upload_name = fields.Char(string='Upload ID document')
    # person_age = fields.Char(string='Age')
    person_youth = fields.Boolean()
    province_code_id = fields.Char()
    # provider_code_m2o = fields.Many2one("seta.provider")
    provider_code_id = fields.Char()
    # employer_m2o = fields.Many2one("seta.employer")
    employer_id = fields.Char()
    provider_etqe_m2o = fields.Many2one("etqe.id")
    person_previous_last_name = fields.Char(size=45)
    person_previous_alternate_id = fields.Char(size=20)
    # person_previous_alternate_id_type_id = fields.Char(size=3)
    person_previous_alternate_id_type_id = fields.Many2one(
        "alternate.id.type.id"
    )  # , default='533'
    person_previous_provider_code = fields.Char(size=20)
    person_previous_provider_etqe_id = fields.Char(size=10)
    seeing_rating_id_m2o = fields.Many2one("seeing.rating.id")
    seeing_rating_id_id = fields.Char()
    hearing_rating_id_m2o = fields.Many2one("hearing.rating.id")
    hearing_rating_id_id = fields.Char()
    walking_rating_id_m2o = fields.Many2one("walking.rating.id")
    walking_rating_id_id = fields.Char()
    remembering_rating_id_m2o = fields.Many2one("remembering.rating.id")
    remembering_rating_id_id = fields.Char()
    communicating_rating_id_m2o = fields.Many2one("communicating.rating.id")
    communicating_rating_id_id = fields.Char()
    self_care_rating_id_m2o = fields.Many2one("self.care.rating.id")
    self_care_rating_id_id = fields.Char()
    # last_school_emis_number = fields.Char(size=10)
    # last_school_year = fields.Date()
    # last_school_year = fields.Many2one("last.school.year")
    statssa_area_code_m2o = fields.Many2one("statssa.area.code")
    statssa_area_code_id = fields.Char()
    popi_act_status_id_m2o = fields.Many2one("popi.act.status.id")
    popi_act_status_id_id = fields.Char()
    popi_act_status_date = fields.Date(default=datetime.datetime.now().date())
    date_stamp = fields.Date(default=datetime.datetime.now().date())
    status_selections = [
        ("achieved", "Achieved"),
        ("certificated", "Certificated"),
        ("completed", "Completed - To Be Assessed"),
        ("discontinued", "Discontinued"),
        ("enrolled", "Enrolled"),
        ("non_endorsed_achieved", "Non-Endorsed Achievement"),
        ("waiting_for_wil", "Waiting for WIL"),
        ("wil_in_progress", "WIL In Progress"),
    ]
    person_id = fields.Many2one("seta.person", string="person")
    national_nd_alternate_id = fields.Char(string='Identification Number')



#global validations
    @api.onchange('person_alternate_id', 'person_last_name', 'person_first_name', 'person_middle_name',
                  'person_home_address_1', 'person_home_address_2', 'person_home_address_3', 'person_postal_address_1',
                  'person_postal_address_2','person_postal_address_3', 'person_address_code', 'person_postal_address_code', 'person_phone_number',
                  'person_cell_phone_number', 'person_fax_number', 'person_email_address')
    def _onchange_field_validation(self):
        seta_map_line_data = toolz.get_seta_map_line_data(self=self, model_name='seta.person')
        validate = self.env['seta.map.line.validation']
        for k, v in seta_map_line_data.items():
            if self[k]:
                seta_map_line_validation_data = toolz.get_seta_map_line_validation_data(self=self, seta_map_line_id=v)
                broken, msg, validation_name = validate.validation_call(seta_map_line_validation_data[v], self[k])
                seta_map_line = self.env['seta.map.line'].browse(v)
                other_compliance_validations, val_error = toolz.other_compliance_validations(self=self,k=k,odoo_label=seta_map_line.odoo_label)
                if other_compliance_validations:
                    self[k]= other_compliance_validations
                if val_error:
                    return val_error
                if broken:
                    return {'warning': {'title': 'Invalid ' + seta_map_line.odoo_label,
                                        'message': f' \n{seta_map_line.odoo_label} {msg}\nPlease re-enter a valid ' + seta_map_line.odoo_label + '.'},
                            'value': {k : False}}


    @api.onchange('same_as_home','person_home_address_1',
        'person_home_address_2',
        'person_home_address_3',
        'person_address_code',
        'suburb',
        'country',
        'province_code_m2o',
        'city',
)
    def onchange_same_as_home(self):
        if self.same_as_home:
            self.person_postal_address_1, self.person_postal_address_2, self.person_postal_address_3, self.person_postal_address_code, self.postal_suburb, self.postal_country, self.postal_province_code_m2o, self.postal_city = (
                self.person_home_address_1, self.person_home_address_2, self.person_home_address_3, self.person_address_code,
                self.suburb, self.country, self.province_code_m2o, self.city)
        else:
            return {'value': {'person_postal_address_1': False,
                              'person_postal_address_2': False,
                              'person_postal_address_3': False,
                              'person_postal_address_code': False,
                              'postal_suburb': False,
                              'postal_country': False,
                              'postal_province_code_m2o': False,
                              'postal_city': False,
                              }}

    @api.onchange("province_code_m2o", "suburb", "district_id", "municipality_id", "city")
    def onchange_province_code_m2o_filler(self):
        """
        district:province_id,country_id,urban_rural
        city:district,province_id,country_id,urban_rural
        suburb:city_id,district_id,province_id,country_id,urban_rural,municipality_id
        """
        if self.suburb:
            self.province_code_m2o = self.suburb.province_id
            self.city = self.suburb.city_id
            self.country = self.suburb.country_id
            self.municipality_id = self.suburb.municipality_id
            self.district_id = self.suburb.district_id
            self.address_rural_urban = self.suburb.urban_rural
            self.person_address_code = self.suburb.postal_code



    def invoke_wiz(self):
        act = {
            "name": _("User Details"),
            "res_model": "person.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "seta_person.person_wizard_form_view"
            ).id,
            "context": {
                "active_model": "seta.person",
                "active_id": self.id,
                # "default_user_id": ,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
        dbg(act["context"])
        return act


    def action_create(self):
        agreed_popi_status = self.env.ref("seta_lookup.popi_act_status_id_1")
        if self.popi_act_status_id_m2o != agreed_popi_status:
            dbg(agreed_popi_status)
            dbg(self.popi_act_status_id_m2o)
            raise UserError(_("You may not register person profile without agreeing to POPI."))
        if self.env["seta.person"].search([('user_id', '=', self.env.user.id)]) and not self.person_id:
            raise UserError(_("You may not register more than one person profile."))

        # CHECKING FOR DUPLICATE id OR ALTERNATE id
        # for National id
        if self.national_id:
            persons = self.env["seta.person"].search([("national_id", "=", self.national_id)])
            if not self.person_id:
                if len(persons) != 0:
                    raise UserError("The person you are trying to register already exists in the system."
                                    "\nYou have the following options :"
                                    "\n 1. You can update the existing person."
                                    "\n 2. If you feel this is an error, please raise a ticket on the helpdesk system")
            if self.person_id:
                if self.national_id != self.person_id.national_id:
                    if len(persons) != 0:
                        raise UserError("The person you are trying to register already exists in the system."
                                        "\nYou have the following options :"
                                        "\n 1. You can update the existing person by raising a ticket on the helpdesk with the old and new ID numbers.\n   Please attach a copy of both IDs to the ticket."
                                        "\n 2. If you feel this is an error, please raise a ticket on the helpdesk system.")

        # for alternate id
        if self.person_alternate_id and self.alternate_id_type_id_m2o and self.nationality_code_m2o:
            person1 = self.env["seta.person"].search([
                ("person_alternate_id", "=", self.person_alternate_id),
                ("alternate_id_type_id_m2o", "=", self.alternate_id_type_id_m2o.id),
                ("nationality_code_m2o", "=", self.nationality_code_m2o.id)
            ])
            dbg("person1111" + str(person1))
            if not self.person_id:
                if len(person1) != 0:
                    raise UserError("The person you are trying to register already exists in the system."
                                    "\nYou have the following options :"
                                    "\n 1. You can update the existing person."
                                    "\n 2. If you feel this is an error, please raise a ticket on the helpdesk system")

            if self.person_id:
                # if self.person_alternate_id != self.person_id.person_alternate_id and self.alternate_id_type_id_m2o != self.person_id.alternate_id_type_id_m2o and self.nationality_code_m2o != self.person_id.nationality_code_m2o:
                if self.person_alternate_id != self.person_id.person_alternate_id:
                    if len(person1) != 0:
                        raise UserError("The person you are trying to register already exists in the system."
                                        "\nYou have the following options :"
                                        "\n 1. You can update the existing person by raising a ticket on the helpdesk with the old and new ID numbers.\n   Please attach a copy of both IDs to the ticket."
                                        "\n 2. If you feel this is an error, please raise a ticket on the helpdesk system")

        vals = self.read()[0]
        vals = toolz.tuple_fixer(vals)
        if not vals.get('is_disabled', True):  # Default to True if not present
            vals.update({
                'seeing_rating_id_m2o': False,
                'hearing_rating_id_m2o': False,
                'walking_rating_id_m2o': False,
                'remembering_rating_id_m2o': False,
                'communicating_rating_id_m2o': False,
                'self_care_rating_id_m2o': False,
            })
        # del vals["display"]
        # del vals["acknowledge_requirements"]
        del vals["hide_alt"]
        del vals["popi_consent"]
        vals["popi_act_status_date"] = datetime.date.today()
        validz = {}
        dbg('mo1',vals)
        for field, val in vals.items():
            field_grab = self._fields.get(field)
            fieldz = {}
            if field_grab:
                field_string = field_grab.get_description(self.env)['string']
                field_type = field_grab.type
                fieldz.update({"field_type": field_type, "field_string": field_string})
                if field_type in ["many2one"]:
                    field_comodel = field_grab.comodel_name
                    fieldz.update({"field_comodel": field_comodel})
                    # dbg(field,field_grab,field_type,val)
                elif field_type == "one2many":
                    field_comodel = field_grab.comodel_name
                    values = []
                    for x in val:
                        o2m_vals = self.env[field_comodel].browse(x).read()[0]
                        o2m_vals = toolz.tuple_fixer(o2m_vals)
                        del o2m_vals["id"]
                        values.append(o2m_vals)
                    val = values
            # if field == 'same_as_home':
            #     validz.update({field: [val, fieldz]})
            if val or fieldz['field_type'] == 'boolean':
                validz.update({field: [val, fieldz]})

        act = {
            "name": _("Person Details Confirmation"),
            "res_model": "confirm.application.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "seta_base.confirm_application_wizard_form_view"
            ).id,
            "context": {
                "active_model": self._name,
                "active_id": self.id,
                "vals": validz,
                "header": "You are about to create person profile. Do you want to proceed?",
                "method": "action_confirmed_create",
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
        return act

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


    def action_confirmed_create(self, vals=None):
        values = {f: v[0] for f, v in vals.items() if v[1]["field_type"] != "one2many"}
        for f, v in vals.items():
            if v[1]["field_type"] == "one2many":
                o2m_list = []
                for o2m_vals in v[0]:
                    if "wiz_id" in o2m_vals:
                        del o2m_vals['wiz_id']
                    o2m_list.append((0, 0, o2m_vals))
                values.update({f: o2m_list})

        if 'person_id' in values:
            del values['id']
            rec = self.env['seta.person'].browse(values['person_id'])

            if rec.national_id and 'national_id' not in values:
                values['previous_national_id'] = rec.national_id
                values['national_id'] = False
            if 'person_last_name' in values:
                if rec.person_last_name != values['person_last_name']:
                    values['person_previous_last_name'] = rec.person_last_name
            if rec.person_alternate_id and 'person_alternate_id' not in values:
                values['person_previous_alternate_id'] = rec.person_alternate_id
                values['person_alternate_id'] = False
            if rec.alternate_id_type_id_m2o and 'alternate_id_type_id_m2o' not in values:
                values['person_previous_alternate_id_type_id'] = rec.alternate_id_type_id_m2o
                values['alternate_id_type_id_m2o'] = False

            if rec.national_id and 'national_id' in values:
                if rec.national_id != values['national_id']:
                    values['previous_national_id'] = rec.national_id
            if rec.person_alternate_id and 'person_alternate_id' in values:
                if rec.person_alternate_id != values['person_alternate_id']:
                    values['person_previous_alternate_id'] = rec.person_alternate_id
            if rec.alternate_id_type_id_m2o and 'alternate_id_type_id_m2o' in values:
                if rec.alternate_id_type_id_m2o != values['alternate_id_type_id_m2o']:
                    values['person_previous_alternate_id_type_id'] = rec.alternate_id_type_id_m2o

            if not values.get('is_disabled', True):  # Default to True if not present
                values.update({
                    'seeing_rating_id_m2o': False,
                    'hearing_rating_id_m2o': False,
                    'walking_rating_id_m2o': False,
                    'remembering_rating_id_m2o': False,
                    'communicating_rating_id_m2o': False,
                    'self_care_rating_id_m2o': False,
                })
            keys_to_check = [
                'seeing_rating_id_m2o',
                'hearing_rating_id_m2o',
                'walking_rating_id_m2o',
                'remembering_rating_id_m2o',
                'communicating_rating_id_m2o',
                'self_care_rating_id_m2o',
            ]

            for key in keys_to_check:
                if key not in values:
                    values[key] = False
                # values['alternate_id_type_id_m2o'] = False
            # values['national_id'] = False
            # if 'previous_national_id' in values and :
            # if 'person_alternate_id' in values and 'national_id' in values:
            #     if rec.national_id and not rec.person_alternate_id:
            #         values['national_id'] = False
            #     if not rec.national_id and rec.person_alternate_id:
            #         values['person_alternate_id'] = False
            #         values['alternate_id_type_id_m2o'] = False
            rec.update(values)
            toolz.link_attachments_to_record(rec)
            rec.send_user_mail_update_person()
            rec.chatter(self.env.user, f"Updated this Person Profile.")

            if rec.national_id:
                rec.update({'national_nd_alternate_id': rec.national_id})
            if rec.person_alternate_id:
                rec.update({'national_nd_alternate_id': rec.person_alternate_id})

        else:
            if 'national_id' in values:
                values.update({'national_nd_alternate_id': values['national_id']})
            if 'person_alternate_id' in values:
                values.update({'national_nd_alternate_id': values['person_alternate_id']})

            rec = self.env["seta.person"].sudo().create(values)
            toolz.link_attachments_to_record(rec)
            rec.send_user_mail_create_person()
            usr = self.env.user
            usr.sudo().write({"person_id": rec.id})
            self.update_user_groups(
                usr,
                groups_to_add=[
                    'seta_person.group_person_master_ext',
                    'seta_person.group_person_disable',
                    'seta_organisation_rep.group_org_rep_ext_user',
                ],
                groups_to_remove=[
                    'seta_person.group_person_ext_user'
                ]
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            return rec



    @api.onchange("popi_act_status_id_m2o")
    def onchange_popi_act_status_id_m2o(self):
        dbg("def popi_act_status_id_m2o(self):")
        if self.popi_act_status_id_m2o:
            self.popi_act_status_date = datetime.date.today()

    @api.onchange("citizen_resident_status_code_m2o")
    def onchange_citizen_hide_alt(self):
        dbg("def onchange_citizen_hide_alt(self):")
        sa_id = self.env["nationality.code"].search([("setmis_lookup", "=", "SA")]).id
        if self.citizen_resident_status_code_m2o:
            if self.citizen_resident_status_code_m2o.setmis_lookup == "SA":
                self.nationality_code_m2o = sa_id
                self.hide_alt = True

            elif self.citizen_resident_status_code_m2o.setmis_lookup == "D":
                self.nationality_code_m2o = sa_id
                self.hide_alt = True

            elif self.citizen_resident_status_code_m2o.setmis_lookup == "PR":
                self.nationality_code_m2o = False
                self.hide_alt = True
            else:
                self.hide_alt = False
                # if self.nationality_code_m2o = sa_id:
                #     self.nationality_code_m2o = False
        if not self.person_id:
            if self.citizen_resident_status_code_m2o.setmis_lookup in ["U",'O']:
                return {'value': {'national_id': False,
                                  'nationality_code_m2o': False
                                  }}

            else:
                return {'value': {'alternate_id_type_id_m2o': False,
                                  'person_alternate_id': False,
                                  }}

    @api.onchange("nationality_code_m2o")
    def onchange_nationality(self):
        dbg("def onchange_nationality(self):")
        if self.nationality_code_m2o:
            if self.nationality_code_m2o.setmis_lookup == "SA":
                self.citizen_resident_status_code_m2o = self.env["citizen.resident.status.code"].search(
                    [("setmis_lookup", "=", "SA")]).id
            # else:
            #     self.citizen_resident_status_code_m2o = False


    # national_id
    @api.onchange("national_id")
    def onchange_national_id_validations(self):
        dbg("def onchange_national_id_validations(self):")
        if self.national_id:
            valid_id = said(self.national_id)
            if not valid_id.valid:
                return {'warning': {'title': 'Invalid ID Number',
                                    'message': '\nYou have entered an invalid ID Number.Please re-enter a valid ID Number. \nIf you feel this is an error, please raise a ticket on the helpdesk system.'},
                        'value': {'national_id': False, }}
            broken, msg = vd.check_national_id(self.national_id)
            gender_id = self.env['gender.code'].search([('name','=',valid_id.gender)],limit=1)
            self.gender_code_m2o = gender_id.id
            if broken:
                raise ValidationError(_(msg))

    # national_id


    @api.onchange("postal_province_code_m2o", "postal_suburb", "postal_city")
    def onchange_postal_province_code_m2o_filler(self):

        if self.postal_suburb and self.same_as_home == False:
            self.postal_province_code_m2o = self.postal_suburb.province_id
            self.postal_city = self.postal_suburb.city_id
            self.postal_country = self.postal_suburb.country_id
            self.person_postal_address_code = self.postal_suburb.postal_code

    @api.onchange("popi_consent")
    def onchange_popi_consent(self):
        agreed_popi_status = self.env.ref("seta_lookup.popi_act_status_id_1")
        desagreed_popi_status = self.env.ref("seta_lookup.popi_act_status_id_2")
        if self.popi_consent:
            self.popi_act_status_id_m2o = agreed_popi_status
        else:
            self.popi_act_status_id_m2o = desagreed_popi_status




    # person_birth_date
    @api.onchange("person_birth_date")
    def onchange_person_birth_date_validations(self):
        dbg("def onchange_person_birth_date_validations(self):")
        if self.person_birth_date:
            broken, msg = vd.check_person_birth_date(self.person_birth_date)
            if broken:
                raise ValidationError(_(msg))
            if self.person_alternate_id:

                age = relativedelta(datetime.date.today(), self.person_birth_date)
                age_days = datetime.date.today() - self.person_birth_date
                dbg(age_days)
                self.age = age.years
                youth_days_min = datetime.timedelta(days=6570)
                youth_days_max = datetime.timedelta(days=12775)
                if age_days < youth_days_min:
                    state = False
                elif age_days >= youth_days_min and age_days < youth_days_max:
                    state = True
                else:
                    state = False

                self.person_youth = state


    @api.model
    @api.depends('national_id')
    @api.onchange('national_id')
    def _compute_age(self):
        for record in self:
            if record.national_id:
                try:
                    birthdate = record.national_id[:6]
                    today = datetime.date.today()
                    # b_date = fields.Datetime.from_string(birthdate)
                    current_date = str(today).replace('-', '')[2:]
                    dbg(current_date)
                    # dbg(current_date-birthdate)
                    if record.national_id[:2] > str(today).replace('-', '')[2:4]:
                        dt_str = '19' + birthdate
                    else:
                        dt_str = '20' + birthdate
                    dbg(dt_str)
                    dbg(today)

                    date_format = '%Y%m%d'
                    date_obj = datetime.datetime.strptime(dt_str, date_format)
                    dbg('b_date' + str(date_obj.date()))
                    age_days = today - (date_obj.date())
                    dbg((age_days))
                    self.age = relativedelta(datetime.date.today(), date_obj).years
                    self.person_birth_date = date_obj
                    youth_days_min = datetime.timedelta(days=6570)
                    youth_days_max = datetime.timedelta(days=12775)
                    if age_days < youth_days_min:
                        state = False
                    elif age_days >= youth_days_min and age_days < youth_days_max:
                        state = True
                    else:
                        state = False

                    record.person_youth = state

                except:
                    raise ValidationError(_('\nID Number should be 13 digits'))

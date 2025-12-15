from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from ast import literal_eval
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


class ConfirmApplicationWizard(models.TransientModel):
    _name = "confirm.application.wizard"

    message = fields.Text()
    ref = fields.Char()
    fields_mapping={
#Person
'City':'City',
'Suburb':'Suburb',
'Country':'Country',
'Age':'Age',
'Postal City':'Postal Address City',
'Postal Suburb':'Postal Address Suburb',
'Postal Country':'Postal Address Country',
'National':'ID Number',
'Equity Code':'Race',
'Nationality Code':'Nationality',
'Home Language Code':'Home Language',
'Gender Code':'Gender',
'Citizen Resident Status Code' : 'Citizenship',
'Person Last Name' :'Last Name',
'Person First Name': 'First Name',
'Person Middle Name': 'Middle Name',
'Same As Home': 'Same As Home Address',
'Person Title' : 'Title',
'Person Birth Date' : 'Date of Birth',
'Person Home Address 1' : 'Home Address 1',
'Person Home Address 2' : 'Home Address 2',
'Person Address Code': 'Postal Code',
'Person Postal Address 1' : 'Postal Address 1',
'Person Postal Address 2' : 'Postal Address 2',
'Disabled' : 'I have a disability',
'Person Postal Address Code': 'Postal Address Postal Code',
'Person Phone Number': 'Phone Number',
'Person Cell Phone Number' : 'Cell Number',
'Person Email Address': 'Email Address',
'Province Code': 'Province',
'Postal Province Code' : 'Postal Address Province',
'Person Youth': 'Youth',
'Popi Act Status Id': 'POPI Act Status',
'Popi Act Status Date': 'POPI Act Status Date',
'Seeing Rating Id':'Seeing Rating',
'Hearing Rating Id':'Hearing Rating',
'Walking Rating Id':'Walking Rating',
'Remembering Rating Id':'Remembering Rating',
'Communicating Rating Id':'Communicating Rating',
'Self Care Rating Id':'Self Care Rating',
'Alternate Id Type Id':'Alternate Id Type',

# Org_rep
'person_first_name': 'First Name',
'person_last_name': 'Last Name',
'person_middle_name': 'Middle Name',
'person_email_address': 'Email Address',
'person_title': 'Title',
'initials': 'Initials',
'citizen_resident_status_id': 'Citizenship',
'national_id': 'ID Number',
'alternate_id_type_id': 'Alternate ID Type',
'person_alternate_id': 'Alternate ID',
'id_document_upload_name': 'ID Document',
'nationality_id': 'Nationality',
'department':'Department',
'age':'Age',
'person_postal_address_1' : 'Postal Address 1',
'person_postal_address_2' : 'Postal Address 2',
'person_postal_address_3' : 'Postal Address 3',
'person_postal_address_code' : 'Postal Address Code',
'country_id': 'Physical Country',
'postal_code': 'Postal Code',
'postal_province_code_m2o': 'Postal Province Code',
'postal_city': 'Postal City',
'postal_suburb': 'Postal Suburb',
'postal_country': 'Postal Country',
'work_address_1': 'Work Address 1',
'work_address_2': 'Work Address 2',
'work_address_3': 'Work Address 3',
'work_suburb_id': 'Work Suburb',
'physical_address_1': 'Physical Address 1',
'physical_address_2': 'Physical Address 2',
'physical_address_3': 'Physical Address 3',
'suburb_id': 'Physical Suburb',
'city_id': 'Physical City',
'province_id': 'Physical Province',
'work_city_id': 'Work City',
'work_province_id': 'Work Province',
'work_country_id': 'Work Country',
'work_postal_code': 'Work Postal Code',
'same_as_home': 'Same as Home Address',
'same_as_physical': 'Same as Physical Address',
'is_disabled': 'I have a disability',
               'seeing_rating_id': 'Seeing Rating',
'hearing_rating_id': 'Hearing Rating',
'walking_rating_id': 'Walking Rating',
'remembering_rating_id': 'Remembering Rating',
'communicating_rating_id': 'Communication Rating',
'self_care_rating_id': 'Self Care Rating',
'job_title': 'Job Title',
'manager': 'Manager',
'date_of_birth' : 'Date of Birth',
'home_language_id' : 'Home Language',
'equity_id' : 'Race',
'marital_status' : 'Marital Status',
'current_occupation': 'Current Occupation',
'years_in_occupation': 'Years in occupation',
'popi_status_date': 'POPI Status Date',
# 'popi_act_status_date': 'POPI Act Status Date',
'popi_status_id': 'POPI Status',
'marketing_consent': 'Marketing Consent',
'person_phone_number': 'Phone Number',
'work_email': 'Work Email',
'person_cell_phone_number': 'Cellphone Number',
'work_contact_number': 'Work Contact Number',
'fax_number': 'Fax Number',
'gender_id':'Gender',
'socio_economic_status_id' : 'Socio Economic Status',
'national_nd_alternate_id':'Identification Number',

#SDF

  "Attachment Name"	: "Attachment",  
  "Work Email *" : "Work Email",
  "Person Home Address 3" : "Home Address 3",
  "Person Postal Address 3": "Postal Address 3",
  "Work Email *" : "Work Email",

#supplier
        'black_woman_ownership' : 'Black Women Ownership',
    'people_with_disability_ownership' : 'People with Disability Ownership',
    'black_youth_ownership' : 'Black Youth Ownership',
    'qse_eme' : 'QSE/EME',
    'black_owned_ownership' : 'Black Owned Ownership',
    'supplier_name': 'Company Name',
    'trading_name': 'Trading Name',
    'registration_number': 'Registration Number',
    'csd_ref_no': 'CSD Reference No',
    'phone_number': 'Telephone Number',
    'Work Email': 'Work Email Address',
    'Function': 'Job Position',
    'contact_name': 'Name',
    'contact_email_address': 'Email Address',
    'contact_phone_number': 'Telephone Number',
    'contact_cell_number': 'Cellphone Number',
    'physical_address_code': 'Physical Address Code',
    'postal_address_3': 'Postal Address 3',
    'province_code': 'Province',
    'country_code': 'Country',
    'city': 'City',
    'title': 'Title',
    'function': 'Job Position',
    'postal_address_1': 'Postal Address 1',
    'postal_address_2': 'Postal Address 2',
    'postal_address_code': 'Postal Address Code',
    'tax_certificate': 'Tax Certificate',
    'csd_certificate': 'CSD Certificate',
    'levy_exempt_certificate': 'Levy Exempt Certificate',
    'bbee_certificate': 'B-BBEE Certificate',
    'emp_reg_number_type': 'Registration Number Type',
    'comp_reg_no': 'Registration Number',
    'vat_number': 'VAT No',
    'latitude_degree': 'Latitude Degree',
    'latitude_minutes': 'Latitude Minutes',
    'latitude_seconds': 'Latitude Seconds',
    'longitude_degree': 'Longitude Degree',
    'longitude_minutes': 'Longitude Minutes',
    'longitude_seconds': 'Longitude Seconds',
    'company_reg_certificate': 'Company Registration Certificate',
    'website': 'Website',
    'is_agent' : 'Is Agent',
    'sars_registered': 'SARS Registered',
    'income_tax_number': 'Income Tax Number',
    'overall_tax_status': 'Overall Tax Status',
    'commissioner_of_oath': 'Commissioner of Oath',
    'affidavit_signed_date': 'Affidavit Signed Date',
    'affidavit_expiry_date': 'Affidavit Expiry Date',
        'director_ids':'Directors',
        'categories' : 'Supplier Categories',
#Requisition
        "deviation_doc": "Deviation Document",
        "room_setup_ids" : "Room Setup(s)",
        "requirements_ids" : "Requirements",
        "dietary_requirement_ids" : "Dietary Requirements",
#Goods and Services
        "requisition_date": "Requisition Date",
        "requesting_division": "Requesting Division",
        "goods_services_details": "Goods Services Details",
        "procurement_type": "Procurement Type",
        "goods_services_type": "Goods Services Type",
        "requesting_user": "Requesting User",
        "manager": "Manager",
        "executive_manager": "Executive Manager",
        "is_deviation": "Is It A Deviation?",
        "supporting_doc": "Supporting Documents",
#Events
        "event_details": "Event Details",
        "event_type": "Event Type",
        "is_catering": "Catering",
        "is_venue": "Venue",
        "event_date" : "Event Date",
        "number_of_delegates" : "Number Of Delegates",
        "arrival_time" : "Start Time",
        "end_time" : "End Time",
        "all_day" : "All Day",
        "breakfast" : "Breakfast",
        "lunch" : "Lunch",
        "afternoon_tea" : "Afternoon Tea",
        "breakfast_time" : "Breakfast Time",
        "lunch_time" : "Lunch Time",
        "afternoon_tea_time" : "Afternoon Tea Time",

 # Catering
        "catering_details": "Catering Details",
        "location" : "Location",
        "province" : "Province",
        "catering_date" : "Catering Date",

#Travel
        "travel_details": "Travel Details",
        "travel_type": "Travel Type",
        "is_car_hire" : "Car Hire",
        "is_flight" : "Flight",
        "is_accommodation" : "Accommodation",
        "is_shuttle" : "Shuttle",
        "car_hire_start_date" : "Car Pickup",
        "car_hire_end_date" : "Car Drop Off",
        "flight_start_date" : "Flight Departure",
        "flight_end_date" : "Flight Return",
        "shuttle_start_date" : "Shuttle Pickup",
        "shuttle_end_date" : "Shuttle Drop Off",
        "accommodation_start_date" : "Accommodation Check-In",
        "accommodation_end_date" : "Accommodation Check-Out",
        "traveler_name" : "Traveler Name(s)",
        "traveler_surname" : "Traveler Surname",
        "traveler_email" : "Traveler Email",
        "traveler_contact_number" : "Traveler Contact Number",
        "deviation_reason": "Deviation Reason",
        "traveller_details" : "Travel Type and Traveller's Details",

  }
    hide_fields=['ID',
                 'id',
                 'popi_act_status_date',
                 'Organisation',
                 'popi_consent',
                 'ref','user_id',
                 'Disabled',
                 'display_name',
                 'org_rep_id',
                 'organisation_id',
                 'id_document_upload',
                 'id_document_upload_name',
                 'Identity Number',
                 'ID Document',
                 'ID Document',
                 'Attachment',
                 'Attachment Name',
                 'Name',
                 'Same As Home Address',
                 'Same As Home',
                 'Gender',
                 'create_uid',
                 'previous_last_name',
                 'previous_alternate_id',
                 'previous_alternate_id_type',
                 'previous_national_id',
                 'create_date',
                 'write_uid',
                 'write_date',
                 'Person',
                 'User',
                 'Upload ID document',
                 'Date Stamp',
                 'Created by',
                 'Created on',
                 'Last Updated by',
                 'Last Updated on',
                 'Appointment Letter *',
                 'Popi Status',
                 'Popi Status Date',
                 'Current User',
                 'Display Name',
                 'Popi Consent',
                 'Sdf',
                 'person',
                 'national_nd_alternate_id',
                 'Identification Number'
                 'allowed_managers_ids',
                 # 'gs_transaction_id',
                 # 'event_transaction_id',
                 # 'travel_transaction_id',
                 'tax_certificate_expiry_date',
                 'csd_certificate_expiry_date',
                 'bbee_certificate_expiry_date',
                 # 'categories',
                 # 'director_ids',
                 'supplier_id',
                 # 'traveller_details',
                 # 'room_setup_ids',
                 # 'requirements_ids',
                 # 'dietary_requirement_ids',
                'event_transaction_id',
                'event_deviation_transaction_id',
                 'catering_transaction_id',
                 'catering_deviation_transaction_id',
                 'travel_transaction_id',
                 'travel_deviation_transaction_id',
                 'gs_transaction_id',
                 'gs_deviation_transaction_id',
                 'is_tax_certificate_expired',
                 'is_csd_certificate_expired',
                'is_bbee_certificate_expired',
                 'requisition_number',
                 ]
    selection_fields_map = {"services": "Services",
                            "goods": "Goods",
                            "goods_services": "Goods and Services",
                            "events": "Events",
                            "travel": "Travel",
                            "catering": "Catering",
                            "courier": "Courier",
                            "accommodation": "Accommodation",
                            "ceo": "Office of the CEO",
                            "finance": "Finance",
                            "corporate_services": "Corporate Services",
                            "sdp": "SDP",
                            "etqa": "ETQA",
                            "rime": "RIME",
                            "provinces": "Provinces",
                            "cipro_number": "Cipro Number",
                            "comp_reg_no": "Company Registration Number",
                            'emergency': 'Emergency',
                            'sole_supplier': 'Single Provider',
                            'art_object': 'Special Works of Art or Historical Objects',
                            'exceptional_case': 'Other Exceptional Case',
                            }

    M2M_FIELD_MODEL_MAP = {
        "room_setup_ids": "event.room.setup",
        "requirements_ids": "event.requirement",
        "dietary_requirement_ids": "event.dietary.requirement",
        "traveller_details": "requisition.travel.details",
        "director_ids" : "supplier.directors",
    "categories" : "supplier.categories",

    }
    def default_get(self, fields_list):
        rec = super(ConfirmApplicationWizard, self).default_get(fields_list)
        ctx = self._context
        if "header" in ctx:
            header = ctx.get("header")
        else:
            header = ""
        msg = """<style>
table {
  font-family: arial, sans-serif;
  border-collapse: collapse;
  width: 100%;
}

td, th {
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}

tr:nth-child(even) {
  background-color: #dddddd;
}
</style>"""
        msg += f"<h4>{header}</h4>\n<table><tr><th>Field Name</th><th>Field Value</th></tr>"


        if "vals" in ctx:
            vals = ctx.get("vals")
            for field, val in vals.items():
                value = val[0]
                field_grab = val[1]
                if "field_string" in field_grab:
                    field_string = field_grab['field_string'].replace("M2O", "")
                else:
                    field_string = field
                if field_grab['field_type'] in ["many2one"]:
                    field_rec = self.env[field_grab["field_comodel"]].browse(value)
                    value = field_rec.display_name
                elif field_grab['field_type'] in ["selection"]:
                    if value in self.selection_fields_map:
                        value = self.selection_fields_map[value]
                elif field_grab['field_type'] in ["boolean"]:
                    dbg('mohavia3',value)
                    if value == True:
                        value = "Yes"
                elif field_grab['field_type'] in ["many2many"]:
                    ids = value if isinstance(value, list) else [value]
                    comodel_m2m = self.M2M_FIELD_MODEL_MAP.get(field, None)
                    if comodel_m2m and ids:
                        recs = self.env[comodel_m2m].browse(ids)
                        dbg('mohavia22',recs.read())
                        value = ", ".join(recs.mapped("display_name"))
                    else:
                        value = False

                else:
                    value = value
                    dbg("This is the fields "+str(field_string))
                if field_string not in self.hide_fields and value != False:
                    if field_string.strip() in self.fields_mapping:
                        msg += f"<tr><td>{self.fields_mapping[field_string.strip()]}</td><td>{value}</td></tr>\n"
                    else:
                        msg += f"<tr><td>{field_string}</td><td>{value}</td></tr>\n"
            msg += "</table>"
            rec.update({'message': msg})
            if "ref" in ctx:
                ref = ctx.get("ref")
                rec.update({'ref': ref})
            return rec
        else:
            raise UserError(_(f"no application requirements have been defined with code:{self._name}"))



    # def diff_lists(self, line):
    #     """
    #     compare an update line containing 2 lists
    #     the old values and new values compared to give back 2 types of diffs in html format
    #     shows the removed ids and shows the added ids, colour coded red and green respectively
    #     """
    #     field_grab = self.env[line.model_id]._fields.get(line.field_name)
    #     field_comodel = field_grab.comodel_name
    #     dbg(line.field_name, line.old_field_value, line.new_field_value)
    #     if line.old_field_value:
    #         oldies = literal_eval(line.old_field_value)
    #     else:
    #         oldies = []
    #     if line.new_field_value:
    #         newies = literal_eval(line.new_field_value)
    #     else:
    #         newies = []
    #     added = [x for x in newies if x not in oldies]
    #     removed = [x for x in oldies if x not in newies]
    #     if len(added) or len(removed) > 0:
    #         # line_html = f'<tr><td>{line.field_name}</td><td>....</td><td>....</td></tr>\n'
    #         line_html = '<tr><td>{}</td><td>....</td><td>....</td></tr>\n'.format(line.field_name)
    #         for fline in removed:
    #             dbg(fline)
    #             rec = self.env[field_comodel].browse(fline)
    #             line_html += '<tr><td></td><td style="color:red;">{}</td><td></td></tr>\n'.format(rec.display_name)
    #         for fline in added:
    #             dbg(fline)
    #             rec = self.env[field_comodel].browse(fline)
    #             line_html += '<tr><td></td><td></td><td style="color:green;">{}</td></tr>\n'.format(rec.display_name)
    #     else:
    #         line_html = ''
    #     return line_html

    # @api.depends('update_ids')
    # def _compute_popup_content(self):
    #     """
    #     builds popup content to give a semi dynamic form feel off of the table that holds updates.
    #     balances the need for a human-readable form and the need to keep the database small
    #     by only keeping the diff per line
    #     """
    # for this in self:
    #     # ctx = self._context
    #     # tab = ''
    #     update_id = this
    #     lines = ''
    #     dbg(this)
    #     title = 'generic update'
    #     for line in update_id.update_ids:
    #         dbg(line)
    #         line_html = ''
    #         if line.field_type in ['many2many', 'one2many'] and line.model_id:
    #             line_html += self.diff_lists(line)
    #         elif line.field_type == 'many2one' and line.model_id:
    #             dbg(line.model_id, line.field_name)
    #             field_grab = self.env[line.model_id]._fields.get(line.field_name)
    #             field_comodel = field_grab.comodel_name
    #             old_rec = self.env[field_comodel].browse(int(line.old_field_value))
    #             new_rec = self.env[field_comodel].browse(int(line.new_field_value))
    #             line_html = "<tr><td>{}</td><td>{}</td><td>{}</td></tr>\n".format(line.field_name,old_rec.display_name or '',new_rec.display_name or '')
    #         else:
    #             line_html = "<tr><td>{}</td><td>{}</td><td>{}</td></tr>\n".format(line.field_name,line.old_field_value or '',line.new_field_value or '')
    #         lines += line_html
    #     tab = """<table>
    #                   <tr>
    #                     <th>field</th>
    #                     <th>old</th>
    #                     <th>new</th>
    #                   </tr>
    #                   {}
    #                 </table>""".format(lines)
    #     gg = """<html>
    #                 <head>
    #                     <link class="origin" rel="stylesheet" href="/web/static/lib/bootstrap/css/bootstrap.css">
    #                 </head>
    #                 <body>
    #                     <div class="modal-header text-center">
    #                         <h3 class="modal-title mt8">{}</h3>
    #                     </div>
    #                     <div class="o_popup_message">
    #                         <font>7</font>
    #                         <strong>{}</strong>
    #                     </div>
    #                     <div class="container text-center">
    #                         <div class="row">
    #                             <div class="col">col</div>
    #                             <div class="col">col</div>
    #                             <div class="col">col</div>
    #                         <div class="col">col</div>
    #                       </div>
    #                       <div class="row">
    #                             <div class="col-8">col-8</div>
    #                             <div class="col-4">col-4</div>
    #                       </div>
    #                     </div>
    #                 <body>
    #             <html>
    # """.format(title,tab)
    #     this.html_content = gg

    def action_confirm(self):
        ctx = self._context
        errors = ''
        # raise Warning(ctx)
        if "active_id" in ctx and "active_model" in ctx and "vals" in ctx:
            vals = ctx.get("vals")

            model = ctx.get("active_model")
            rec_model = self.env[model]
            rec = rec_model.browse(ctx.get("active_id"))
            if "method" in ctx:
                method = ctx.get("method")
                if hasattr(rec_model, method):
                    try:
                        dbg("getting attr")
                        operation = getattr(rec_model, method)
                        res = operation(vals=vals)
                        return res
                    except Exception as e:
                        errors += str(e)
                    if errors != "":
                        raise Warning(errors)
                else:
                    dbg("The method _run_%s doesn't exist on the model" % method)
            else:
                raise Warning("never got a method to use")
        else:
            raise Warning("never got active id or active model")

    # def action_submit(self):
    #     ctx = self._context
    #     errors = ''
    #     if "active_id" in ctx and "active_model" in ctx:
    #         model = ctx.get("active_model")
    #         rec = self.env[model].browse(ctx.get("active_id"))
    #         if "method" in ctx:
    #             method = ctx.get("method")
    #             if hasattr(rec,method):
    #                 try:
    #                     dbg("getting attr")
    #                     operation = getattr(rec, method)
    #                     res = operation(self.message)
    #                 except Exception as e:
    #                     errors += str(e)
    #             else:
    #                 dbg("The method _run_%s doesn't exist on the model" % method)
    #         else:
    #             raise Warning("never got a method to use")
    #     else:
    #         raise Warning("never got active id or active model")
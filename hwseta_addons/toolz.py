import string
import re
# import wdb


def tuple_fixer(vals):
    for val in vals.keys():
        if type(vals.get(val)) == tuple:
            vals.update({val: vals.get(val)[0]})
    return vals


def mail_activity_strip(vals):
    new_vals = {}
    bad_list = [
        "activity_ids",
        "activity_state",
        "activity_type_id",
        "activity_type_icon",
        "activity_date_deadline",
        "my_activity_date_deadline",
        "activity_summary",
        "activity_exception_decoration",
        "activity_exception_icon",
        "activity_calendar_event_id",
        "activity_user_id",
        "message_is_follower",
        "message_follower_ids",
        "message_partner_ids",
        "message_ids",
        "has_message",
        "message_needaction",
        "message_needaction_counter",
        "message_has_error",
        "message_has_error_counter",
        "message_attachment_count",
        "message_main_attachment_id",
        "website_message_ids",
        "message_has_sms_error",
    ]
    for val in vals.keys():
        if val not in bad_list:
            new_vals.update({val: vals.get(val)})
        else:
            pass
    return new_vals


def get_seta_map_line_data(self, model_name):
    # model_name = 'seta.person'
    # Get the cursor for raw SQL query execution

    cr = self.env.cr

    # Define the SQL query
    query = """
               SELECT odoo_field, id
               FROM seta_map_line
               WHERE map_id IN (SELECT id FROM seta_map WHERE odoo_model = '%s')
               AND id IN (SELECT seta_map_line_id FROM seta_map_line_seta_map_line_validation_rel);
           """ % (model_name)

    # Execute the query
    cr.execute(query)

    # Fetch all results
    results = cr.fetchall()
    r_dict = {}
    for result in results:
        odoo_field, id = result
        r_dict.update({odoo_field: id})

    return r_dict


def get_seta_map_line_validation_data(self, seta_map_line_id):
    cr = self.env.cr

    # Define the SQL query
    query = """
                                     SELECT * FROM seta_map_line_seta_map_line_validation_rel WHERE seta_map_line_id = %s;
                                 """ % (seta_map_line_id)
    cr = self.env.cr
    cr.execute(query)
    # Fetch all results
    results = cr.fetchall()
    r_dict = {}
    for result in results:
        seta_map_line, seta_map_line_validation = result
        r_dict.update({seta_map_line: seta_map_line_validation})
    return r_dict



def other_compliance_validations(self, k, odoo_label):
    val_error = None
    address_keys = ['person_postal_address_1', 'person_postal_address_2', 'person_postal_address_3',
                    'person_home_address_1', 'person_home_address_2', 'person_home_address_3','work_address_1',
    'work_address_2',
    'work_address_3','postal_address_1', 'postal_address_2', 'postal_address_3','physical_address_1',
'physical_address_2',
'physical_address_3'
]
    name_keys = ['person_first_name', 'person_last_name', 'person_middle_name']
    code_keys = ['person_address_code', 'person_address_postal_code','work_postal_code','postal_address_code','physical_address_code']
    emails = ['work_email']

    if k in name_keys + address_keys + code_keys:
        self[k] = string.capwords(self[k].strip())

        if k in address_keys:
            value = self[k].replace(" ", "")
            is_numeric = value.isnumeric()
            check = r"(0123|1234|2345|3456|4567|5678|6789|3210|4321|5432|6543|7654|8765|9876|0000|1111|2222|3333|4444|5555|6666|7777|8888|9999)"
            is_consecutive = bool(re.findall(check, self[k]))

            if is_numeric:
                val_error = {'warning': {'title': f'Invalid {odoo_label}',
                                         'message': f'{odoo_label} may not contain only numbers. Please re-enter a valid {odoo_label}.'},
                             'value': {k: False}}

            if k in ['person_postal_address_3', 'person_home_address_3','postal_address_3','physical_address_3'] and is_consecutive:
                val_error = {'warning': {'title': f'Invalid {odoo_label}',
                                         'message': f'{odoo_label} may not contain 4 consecutive numbers. Please re-enter a valid {odoo_label}.'},
                             'value': {k: False}}

        if k == 'person_first_name' and " " in self[k]:
            val_error = {'warning': {'title': f'Invalid {odoo_label}',
                                     'message': 'First Name should not contain a space. Please re-enter a valid {odoo_label}.'},
                         'value': {k: False}}
    if k in emails:
        self[k] = self[k].strip().lower()

    return self[k], val_error

def fomart_value(self, field, classification):
    if field:
        field_value = getattr(self, field, False)
        if field_value:
            if classification == "title":
                setattr(self, field, field_value.title())
            else:
                setattr(self, field, field_value.strip())


# def _link_attachments_to_record(self, rec):
#     """
#     Link all ir.attachment fields (many2one, one2many, many2many)
#     to the given record by setting res_model and res_id.
#
#     :param rec: The record to which attachments must be linked
#     """
#     for field_name, field in rec._fields.items():
#         if field.comodel_name == "ir.attachment":
#             if field.type in ["one2many", "many2many"]:
#                 attachments = getattr(rec, field_name)
#                 attachments.write({
#                     'res_model': rec._name,
#                     'res_id': rec.id,
#                 })
#             elif field.type == "many2one":
#                 attachment = getattr(rec, field_name)
#                 if attachment:
#                     attachment.write({
#                         'res_model': rec._name,
#                         'res_id': rec.id,
#                     })

def link_attachments_to_record(rec):
    """
    Link all ir.attachment fields (many2one, one2many, many2many)
    to the given record by setting res_model and res_id.

    :param rec: Record (single browse record) to link attachments to
    """
    for field_name, field in rec._fields.items():
        if not field.related:
            if field.comodel_name == "ir.attachment":
                if field.type in ["one2many", "many2many"]:
                    attachments = getattr(rec, field_name)
                    attachments.write({
                        'res_model': rec._name,
                        'res_id': rec.id,
                    })
                elif field.type == "many2one":
                    attachment = getattr(rec, field_name)
                    if attachment:
                        attachment.write({
                            'res_model': rec._name,
                            'res_id': rec.id,
                        })

        else:
            continue


def generate_time_intervals_15_min():
    intervals = []
    for h in range(24):  # hours 0 - 23
        for m in range(0, 60, 15):  # minutes 0, 15, 30, 45
            intervals.append((
                f"{h:02d}:{m:02d}",  # value stored in DB
                f"{h:02d}:{m:02d}",  # label shown to user
            ))
    return intervals
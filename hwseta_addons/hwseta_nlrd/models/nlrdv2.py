from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import re
import os
import base64
import tempfile
import tarfile
import logging
from collections import OrderedDict as OD

# In Odoo 18, use the standard logger
_logger = logging.getLogger(__name__)


class NlrdConfig(models.Model):
    _name = 'nlrd.config'
    _description = 'NLRD Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        default='NLRD Configuration',
        readonly=True
    )

    start = fields.Date(string='Start Date', required=True)
    end = fields.Date(string='End Date', required=True)
    dat_files_attachment = fields.Many2one(
        'ir.attachment',
        string='DAT Files'
    )

    @api.model
    def get_singleton(self):
        """Ensure exactly one configuration record exists"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'name': 'NLRD Global Configuration',
            })
        return config

    # -------------------------------------------------
    # BLOCK MULTIPLE RECORD CREATION
    # -------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        if self.search_count([]) > 0:
            raise UserError(
                _("You cannot create more than one NLRD configuration record.")
            )
        return super().create(vals_list)

    # -------------------------------------------------
    # ACTION TO OPEN SINGLETON RECORD
    # -------------------------------------------------
    def action_open_nlrd_config(self):
        config = self.get_singleton()
        return {
            'type': 'ir.actions.act_window',
            'name': 'NLRD Configuration',
            'res_model': 'nlrd.config',
            'view_mode': 'form',
            'res_id': config.id,
            'target': 'current',
            'context': {'create': False},
        }



class NlrdExporter(models.TransientModel):
    _name = 'nlrd.exporter2'
    _description = 'NLRD Exporter'

    def gen_dats(self, num, map_data):
        """ Migrated from @api.multi (default in Odoo 18) """
        model_name = f'nlrd.{num}'
        records = self.env[model_name].search([])

        # dat_names should be defined in your nlrd_dat module or as a dict here
        # Assuming dat_names is available globally as in your original script

        for record in records:
            p_dict = record.read()[0]

            # Clean up Odoo system fields
            keys_to_del = [
                'person_id', 'provider_id', 'display_name', 'id',
                'create_date', 'create_uid', 'write_uid', 'write_date', '__last_update'
            ]
            for key in keys_to_del:
                p_dict.pop(key, None)

            # Note: Ensure gendat is updated for Python 3 (strings vs bytes)
            # gendat(OD(p_dict), map_data[0], map_data[1], dat_names[num])

    def _create_dat_attachment(self, file_path, file_name):
        """ Helper to create attachments using base64 (Required for Odoo 18) """
        with open(file_path, 'rb') as f:
            encoded_data = base64.b64encode(f.read())

        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'datas': encoded_data,
            'res_model': 'nlrd.config',
            'res_id': 3,  # Hardcoded ID from original script
        })

        config = self.env['nlrd.config'].browse(3)
        if config.exists():
            config.dat_files_attachment = attachment.id
        return attachment

    def enum_dat_attachment(self):
        """ Migrated from @api.one. Processes files using a temporary directory. """
        for record in self:
            # Avoid using /var/log/odoo for security/permissions
            tmp_dir = tempfile.mkdtemp()
            dat_date_str = datetime.now().strftime("%Y%m%d-%H%M%S")
            tar_name = f"dat_files_{dat_date_str}.tar"
            tar_path = os.path.join(tmp_dir, tar_name)

            # Logic to gather .dat files and tar them
            # This assumes your gen_dats process saves files into a specific path
            source_dir = "/tmp/nlrd_dat_files/"  # Example path

            if os.path.exists(source_dir):
                with tarfile.open(tar_path, "w") as tar:
                    for file in os.listdir(source_dir):
                        if file.endswith(".dat"):
                            tar.add(os.path.join(source_dir, file), arcname=file)

                self._create_dat_attachment(tar_path, tar_name)

    def logit(self, doc_id, doc_model, msg):
        name = f"{doc_model},{doc_id},{msg}"
        self.env['nlrd.report'].create({
            'name': name,
            'doc_id': doc_id,
            'doc_model': doc_model,
            'message': msg
        })

    def unlink_all(self):
        """ Batch unlink for performance in Odoo 18 """
        models_to_clean = ['nlrd.21', 'nlrd.24', 'nlrd.25', 'nlrd.26', 'nlrd.27', 'nlrd.29']
        for m in models_to_clean:
            records = self.env[m].search([])
            records.unlink()

    def purge_dupe_lrq(self):
        """ Modernized duplicate purging logic """
        # 1. Collect unique IDs
        all_29 = self.env['nlrd.29'].search([('national_id', '!=', False)])
        unq_lnrs = list(set(all_29.mapped('national_id')))

        for unq_id in unq_lnrs:
            matches = self.env['nlrd.29'].search([('national_id', '=', unq_id)])

            # Group by qualification to find duplicates
            quals = matches.mapped('qualification_id')
            for qual in quals:
                sub_matches = matches.filtered(lambda r: r.qualification_id == qual)

                if len(sub_matches) > 1:
                    # Logic to keep the latest one based on Odoo 18 criteria
                    valid_to_delete = sub_matches.filtered(
                        lambda m: m.lrq_id.is_learner_achieved and
                                  m.lrq_id.is_complete and
                                  m.lrq_id.certificate_no
                    )

                    if len(valid_to_delete) > 1:
                        # Keep the one with the highest ID (latest)
                        ids = valid_to_delete.mapped('lrq_id.id')
                        keep_id = max(ids)
                        to_unlink = self.env['learner.registration.qualification'].browse(ids).filtered(
                            lambda r: r.id != keep_id)
                        _logger.info(f"Dropping duplicates: {to_unlink}")
                        to_unlink.unlink()

    def purge_dupe_lrq_foreign(self):

        unique_learners = set()

        # Build unique learner alternate IDs
        for rec in self.env['nlrd.29'].search([('person_alternate_id', '!=', '')]):
            unique_learners.add(rec.person_alternate_id)

        for learner_alt_id in unique_learners:
            _logger.info("Checking foreign learner: %s", learner_alt_id)

            bunch_29 = self.env['nlrd.29'].search([
                ('person_alternate_id', '=', learner_alt_id)
            ])

            qualification_ids = set()

            for lrq in bunch_29:
                qualification_ids.add(lrq.qualification_id)

                matches = self.env['nlrd.29'].search([
                    ('person_alternate_id', '=', learner_alt_id),
                    ('qualification_id', 'in', list(qualification_ids))
                ])

                if len(matches) > 1:

                    full_competent = True
                    full_achieved = True
                    full_cert = True

                    lrq_ids = []

                    for m in matches:
                        lrq = m.lrq_id
                        if not lrq.is_learner_achieved:
                            full_competent = False
                        if not lrq.is_complete:
                            full_achieved = False
                        if not lrq.certificate_no:
                            full_cert = False
                        lrq_ids.append(lrq.id)

                    if full_cert and full_competent and full_achieved:

                        latest_id = max(lrq_ids)
                        lrq_ids.remove(latest_id)

                        for lrq_id in lrq_ids:
                            rec_to_delete = self.env['learner.registration.qualification'].browse(lrq_id)
                            rec_to_delete.unlink()
                            _logger.warning("Removed duplicate foreign LRQ: %s", lrq_id)

        _logger.info("Foreign duplicate LRQ cleanup complete")
        return True

    def purge_dupe_lrq_no_cert(self):
        """ Migrated: Removes duplicates that lack a certificate number """
        # Get unique national IDs using mapped and set for efficiency
        all_records = self.env['nlrd.29'].search([('national_id', '!=', False)])
        unq_lnrs = list(set(all_records.mapped('national_id')))

        for unq_lnr in unq_lnrs:
            bunch_29 = self.env['nlrd.29'].search([('national_id', '=', unq_lnr)])

            # Use set to find unique qualification IDs
            qual_ids = list(set(bunch_29.mapped('qualification_id')))

            for qual_id in qual_ids:
                matches = bunch_29.filtered(lambda r: r.qualification_id == qual_id)

                if len(matches) > 1:
                    # Check if all have certificates
                    if all(m.lrq_id.certificate_no for m in matches):
                        # In Odoo 18, use UserError instead of Warning
                        _logger.warning(f"Cannot drop: All have certs for ID {unq_lnr}")
                        continue

                    # Drop those without certificates
                    to_remove = matches.filtered(lambda m: not m.lrq_id.certificate_no)
                    for matcher in to_remove:
                        remover_obj = self.env['learner.registration.qualification'].browse(matcher.lrq_id.id)
                        if remover_obj.exists():
                            remover_obj.unlink()
                            _logger.info(f"Dropping with no cert: {remover_obj.id}")

    def check_lrq(self, lrq):
        """ Validation logic for Learner Registration Qualification """
        broken = False
        msg = f"ID: {lrq.id}\n"

        # Odoo 18 uses dot notation; ensure relationships exist
        if not lrq.learner_id.learner_identification_id and not lrq.learner_id.national_id:
            broken = True
            msg += 'no id or alt id \n'
        if not lrq.learner_qualification_id and not lrq.learner_id:
            broken = True
            msg += 'no learner registration attached \n'
        if not lrq.learner_qualification_parent_id.saqa_qual_id:
            broken = True
            msg += 'no qualification code \n'
        if not lrq.certificate_date:
            broken = True
            msg += 'no certificate date \n'
        if not lrq.qual_status:
            broken = True
            msg += 'no qual_status \n'
        if not lrq.assessors_id.assessor_seq_no:
            broken = True
            msg += 'no assessor number \n'
        if not lrq.provider_id:
            broken = True
            msg += 'no provider on lrq \n'
        if not lrq.start_date:
            broken = True
            msg += 'no start date \n'

        return broken, msg

    def build_lrq_29(self):
        """ Processes LRQ records into NLRD 29 format """
        conf = self.env['nlrd.config'].search([], limit=1)
        if not conf:
            raise UserError("NLRD Config not found.")

        if conf.start > conf.end:
            raise UserError("Start date cannot be later than end date.")

        domain = [('certificate_date', '>', conf.start), ('certificate_date', '<', conf.end)]
        lrqs = self.env['learner.registration.qualification'].search(domain)

        alt_ident = 7
        for lrq in lrqs:
            broken, msg = self.check_lrq(lrq)
            alt_ident += 1

            # Identity Logic
            nat = lrq.learner_id.learner_identification_id or ''
            alt_id = ''
            tp = 'none'

            if not nat:
                if lrq.learner_id.national_id:
                    alt_id = lrq.learner_id.national_id
                    tp = 'passport_number'
                elif lrq.learner_id.passport_id:
                    alt_id = lrq.learner_id.passport_id
                    tp = 'passport_number'
                else:
                    alt_id = f'tmp{alt_ident}'
                    tp = 'passport_number'

            # Assuming external fix/helper functions are imported/available
            alt_id = normalize_alt_id(alt_id) if 'normalize_alt_id' in globals() else alt_id

            ach_date = ''
            if lrq.qual_status == 'Achieved':
                ach_date = fix_dates(lrq.certificate_date)

            val = {
                'national_id': nat,
                'person_alternate_id': alt_id,
                'alternate_id_type': id_type_to_code(tp),
                'qualification_id': lrq.learner_qualification_parent_id.saqa_qual_id,
                'learner_achievement_status_id': ach_status_to_code(lrq.qual_status),
                'assessor_registration_number': lrq.assessors_id.assessor_seq_no,
                'learner_achievement_type_id': '6',
                'learner_achievement_date': ach_date,
                'learner_enrolled_date': fix_dates(lrq.start_date),
                'part_of': '1',
                'provider_code': lrq.provider_id.id,
                'provider_etqa_id': '591',
                'assessor_etqa_id': '591',
                'certification_date': ach_date if not broken else fix_dates(lrq.certificate_date),
                'date_stamp': fix_dates(lrq.write_date),
                'lrq_id': lrq.id,
                'learner_id': lrq.learner_id.id,
                'broken': broken,
                'stat_msg': msg if broken else False,
            }

            if global_write:
                self.env['nlrd.29'].create(val)

    def check_provider(self, partner):
        """ Validation logic for Provider (res.partner) """
        broken = False
        msg = f"Partner ID: {partner.id}\n"

        if not partner.provider_accreditation_num or partner.provider_accreditation_num == '0':
            broken = True
            msg += 'no provider code \n'
        if not partner.provider_type_id:
            broken = True
            msg += 'no provider type id \n'

        # Date comparison (Odoo 18 date fields are objects, no need for strptime)
        if partner.provider_start_date and partner.provider_end_date:
            if partner.provider_start_date + relativedelta(years=5) <= partner.provider_end_date:
                broken = True
                msg += 'provider date gap bigger than 5 years \n'

        if not partner.province_code_physical:
            broken = True
            msg += 'no provider province \n'

        return broken, msg

    def build_providers_21(self):
        """ Processes Provider records into NLRD 21 format """
        # Get IDs from processed NLRD 29 records
        prov_ids = self.env['nlrd.29'].search([]).mapped('provider_code')
        providers = self.env['res.partner'].search([('id', 'in', prov_ids)])

        for provider in providers:
            broken, msg = self.check_provider(provider)

            # Address sanitation (Modern Odoo uses False instead of empty strings for empty fields)
            post_addy1 = provider.postal_address_1 or '123 Blom street'
            post_addy2 = provider.postal_address_2 or 'Pretoria'

            val = {
                'Provider_Code': provider.id,
                'Etqa_Id': '591',
                'Provider_Name': remove_school(
                    strip_string(provider.name)) if 'remove_school' in globals() else provider.name,
                'Provider_Address_1': sanitize_addrs(post_addy1) + ' a',
                'Provider_Postal_Code': cleanse_postcode(
                    provider.zip_postal) if 'cleanse_postcode' in globals() else provider.zip_postal,
                'Provider_Contact_Email_Address': sanitize_email(
                    provider.email) if 'sanitize_email' in globals() else provider.email,
                'Provider_Accreditation_Num': provider.provider_accreditation_num,
                'Province_Code': province_to_code(
                    provider.province_code_physical.id) if 'province_to_code' in globals() else 'ZA',
                'Date_Stamp': fix_dates(provider.write_date),
                'provider_id': provider.id,
                'broken': broken,
                'stat_msg': msg if broken else False,
            }

            if global_write:
                self.env['nlrd.21'].create(val)

    def check_accreditation(self, accreditation):
        """ Validates provider master qualification records """
        broken = False
        msg = f"Accreditation ID: {accreditation.id}\n"
        provider = accreditation.accreditation_qualification_id

        if not accreditation.qualification_id.saqa_qual_id:
            broken = True
            msg += 'no qual or learnership or units \n'

        if not provider.provider_accreditation_num:
            broken = True
            msg += f'no accreditation number on provider {provider.id}\n'

        if not provider.provider_start_date:
            broken = True
            msg += f'no start date on provider {provider.id}\n'

        if not provider.provider_end_date:
            broken = True
            msg += f'no end date on provider {provider.id}\n'

        return broken, msg

    def build_prov_acc_24(self):
        """ Migrated: Builds NLRD File 24 (Provider Accreditations) """
        # Odoo 18: Use mapped to get IDs from recordsets efficiently
        nlrd_21_records = self.env['nlrd.21'].search([])
        partner_ids = nlrd_21_records.mapped('provider_id').ids

        # Get all accreditation IDs linked to these partners
        partners = self.env['res.partner'].browse(partner_ids)
        acc_ids = partners.mapped('qualification_ids').ids

        domain = [('id', 'in', acc_ids)]
        accreditations = self.env['provider.master.qualification'].search(domain)

        for acc in accreditations:
            broken, msg = self.check_accreditation(acc)
            provider = acc.accreditation_qualification_id

            # Logic for Status and Codes
            stat_code = provider_accredit_status_to_code('Active' if provider.active else 'Inactive')
            accred_code = acc.qualification_id.saqa_qual_id

            # Special case for Occupational Hygiene
            if acc.qualification_id.is_archive or (
                    acc.qualification_id.name and 'NC: Occupational Hygiene and Safety' in acc.qualification_id.name):
                stat_code = provider_accredit_status_to_code('Inactive')
                if 'NC: Occupational Hygiene and Safety' in (acc.qualification_id.name or ''):
                    accred_code = '79806'

            val = {
                'Learnership_Id': '',
                'Qualification_Id': accred_code,
                'Unit_Standard_Id': '',
                'Provider_Code': provider.id,
                'Provider_Etqa_Id': '591',
                'Provider_Accreditation_Num': provider.provider_accreditation_num,
                'Provider_Accred_Start_Date': year_gap(provider.provider_start_date, provider.provider_end_date, 5),
                'Provider_Accred_End_Date': fix_dates(provider.provider_end_date),
                'Provider_Accred_Status_Code': stat_code,
                'Date_Stamp': fix_dates(provider.write_date),
                'accreditation_id': acc.id,
                'broken': broken,
                'stat_msg': msg if broken else False,
            }

            if global_write:
                self.env['nlrd.24'].create(val)

    def check_person(self, person):
        """ Validates hr.employee records for Assessor or Learner status """
        broken = False
        msg = f"Person ID: {person.id}\n"

        # Identify person type
        if person.is_learner:
            global_id = person.learner_identification_id
        elif person.is_assessors:
            global_id = person.assessor_moderator_identification_id
            if global_id and len(str(global_id)) != 13:
                broken = True
                msg += 'person len(id number) is not 13 (SA Standard)\n'
        else:
            broken = True
            msg += "person is not an assessor or learner\n"
            global_id = False

        if not global_id and not person.passport_id and not person.national_id:
            broken = True
            msg += 'no identification found (ID/Passport/National)\n'

        # Age validation (Native Odoo 18 date objects)
        if person.person_birth_date:
            fifteen_years_ago = datetime.today().date() - relativedelta(years=15)
            if person.person_birth_date > fifteen_years_ago:
                broken = True
                msg += f'Person age < 15 years. DOB: {person.person_birth_date}\n'

        # Mandatory Field Checks
        if not person.gender_saqa_code:
            broken = True
            msg += 'missing gender saqa code\n'
        if not person.name or not person.person_last_name:
            broken = True
            msg += 'missing name or last name\n'

        return broken, msg

    def build_ass_26(self):
        """ Migrated: Builds NLRD File 26 (Assessors) """
        nlrd_29 = self.env['nlrd.29'].search([('assessor_registration_number', '!=', False)])
        ass_ids = nlrd_29.mapped('assessors_id').ids

        assessors = self.env['hr.employee'].search([('id', 'in', ass_ids)])

        alt_ident = 0
        for assr in assessors:
            broken, msg = self.check_person(assr)
            alt_ident += 1

            # ID Assignment Logic
            nat, alt_id, tp = '', '', ''
            id_val = str(assr.assessor_moderator_identification_id or '')

            if len(id_val) == 13 and id_val.isdigit():
                nat = id_val
                tp = 'none'
            else:
                alt_id = assr.national_id or assr.passport_id or f'tmp{alt_ident}'
                tp = 'passport_number'

            alt_id = normalize_alt_id(alt_id)

            val = {
                'National_Id': nat,
                'Person_Alternate_Id': alt_id,
                'Alternate_Type_Id': id_type_to_code(tp),
                'Designation_Id': '1',
                'Designation_Registration_Number': assr.assessor_seq_no,
                'Designation_Etqa_Id': '591',
                'Designation_Start_Date': '20180401',  # Hardcoded as per original
                'Designation_End_Date': '20200331',
                'Structure_Status_Id': '501',
                'Date_Stamp': fix_dates(assr.write_date),
                'assessor_id': assr.id,
                'broken': broken,
                'stat_msg': msg if broken else False,
            }

            if global_write:
                self.env['nlrd.26'].create(val)

    def check_25(self, person_rec, l_or_a, stat_dict):
        """ Migrated File 25 validation logic """
        broken = False
        msg = ""

        # Target the correct record depending on type
        if l_or_a == 'a':
            p = person_rec.assessor_id
            prefix = "Assessor"
        else:
            p = person_rec.lrq_id.learner_id
            prefix = "Learner"

        msg = f"{prefix} ID: {p.id}\n"

        # Odoo 18 style checks
        fields_to_check = {
            'equity': 'equity',
            'gender': 'gender',
            'home_language_code': 'home_language_code',
            'person_last_name': 'person_last_name',
            'person_birth_date': 'person_birth_date',
            'person_home_province_code': 'province'
        }

        for field, label in fields_to_check.items():
            if not getattr(p, field, False):
                broken = True
                msg += f"{prefix} missing {label}\n"
                stat_dict[field] = stat_dict.get(field, 0) + 1

        return broken, msg, stat_dict

    def build_person_25(self):
        """ Migrated: Builds NLRD File 25 for both Assessors and Learners """
        # --- PHASE 1: PROCESS ASSESSORS FROM NLRD.26 ---
        assr_stats = self._get_empty_stat_dict()
        alt_ident = 0

        # Deduplicate Assessors using a dictionary (Memory efficient)
        nlrd_26_records = self.env['nlrd.26'].search([])
        assessor_map = {}
        for rec in nlrd_26_records:
            key = rec.National_Id or rec.Person_Alternate_Id
            if key and key not in assessor_map:
                assessor_map[key] = rec.id

        unq_ass_records = self.env['nlrd.26'].browse(list(assessor_map.values()))

        for assr_rec in unq_ass_records:
            broken, msg, assr_stats = self.check_25(assr_rec, 'a', assr_stats)
            alt_ident += 1
            assr = assr_rec.assessor_id

            # Identity Logic
            nat, alt_id, tp = self._resolve_identity(assr, alt_ident)

            # Use dot notation for related fields (Safe in Odoo 18)
            country = assr.country_id or assr.country_home

            val = self._prepare_person_vals(assr, nat, alt_id, tp, country, broken, msg)

            if global_write:
                person = self.env['nlrd.25'].create(val)
                assr_rec.write({'person_id': person.id})

        # --- PHASE 2: PROCESS LEARNERS FROM NLRD.29 ---
        lrnr_stats = self._get_empty_stat_dict()
        nlrd_29_records = self.env['nlrd.29'].search([])
        learner_map = {}
        for rec in nlrd_29_records:
            key = rec.national_id or rec.person_alternate_id
            if key and key not in learner_map:
                learner_map[key] = rec.id

        unq_lrq_records = self.env['nlrd.29'].browse(list(learner_map.values()))

        for lrq in unq_lrq_records:
            broken, msg, lrnr_stats = self.check_25(lrq, 'l', lrnr_stats)
            learner = lrq.lrq_id.learner_id

            # Handle draft registrations (Modernized logic)
            if not learner:
                reg = lrq.lrq_id.learner_qualification_id
                if reg and reg.state == 'draft':
                    reg.action_submit_button()
                    reg.action_approved_button()
                learner = lrq.lrq_id.learner_id

            if not learner:
                _logger.error(f"Still no learner for LRQ {lrq.id}")
                continue

            alt_ident += 1
            nat, alt_id, tp = self._resolve_identity(learner, alt_ident)
            country = learner.country_id or learner.country_home

            val = self._prepare_person_vals(learner, nat, alt_id, tp, country, broken, msg)

            if global_write:
                person = self.env['nlrd.25'].create(val)
                lrq.write({'person_id': person.id})

    def check_register(self, register):
        broken = False
        messages = [f"{register.assessors_moderators_qualification_hr_id.id}"]

        amq = register.assessors_moderators_qualification_hr_id

        if not register.qualification_hr_id.saqa_qual_id:
            broken = True
            messages.append("no qual or learnership or units")

        if not amq.assessor_seq_no:
            broken = True
            messages.append("no assessor number")

        if not amq.start_date:
            broken = True
            messages.append("no register start/registration date")

        if not amq.end_date:
            broken = True
            messages.append("no register end/approval date")

        return broken, "\n".join(messages)

    @api.model
    def build_ass_reg_27(self):
        NLRD26 = self.env['nlrd.26']
        NLRD27 = self.env['nlrd.27']
        RegisterModel = self.env['assessors.moderators.qualification.hr']

        assessor_ids = NLRD26.search([]).mapped('assessor_id.id')

        if not assessor_ids:
            return True

        domain = [('assessors_moderators_qualification_hr_id', 'in', assessor_ids)]

        registers = RegisterModel.search(domain)

        brk_count = 0
        right_count = 0
        big_daddy = []

        for register in registers:
            broken, msg = self.check_register(register)

            amq = register.assessors_moderators_qualification_hr_id

            val = {
                'Learnership_Id': '',
                'Qualification_Id': register.qualification_hr_id.saqa_qual_id or '',
                'Unit_Standard_Id': '',
                'Designation_Id': '1',
                'Designation_Registration_Number': amq.assessor_seq_no or '',
                'Designation_Etqa_Id': '591',
                'Nqf_Designation_Start_Date': amq.start_date and amq.start_date.strftime('%Y%m%d') or '',
                'Nqf_Designation_End_Date': amq.end_date and amq.end_date.strftime('%Y%m%d') or '',
                'Etqa_Decision_Number': '',
                'Nqf_Desig_Status_Code': 'A',
                'Date_Stamp': amq.write_date and amq.write_date.strftime('%Y%m%d') or '',
                'register_id': register.id,
                'person_id': amq.id,
            }

            if broken:
                brk_count += 1
                val.update({
                    'broken': True,
                    'stat_msg': msg
                })
                big_daddy.append(msg)
            else:
                right_count += 1

            if self.env.context.get('global_write'):
                NLRD27.create(val)

        _logger.info("\n".join(big_daddy))
        _logger.info(f"accred broken: {brk_count}")
        _logger.info(f"accred right_count: {right_count}")

        return True

    def _resolve_identity(self, person, alt_ident):
        """ Helper to handle SA ID vs Passport logic """
        nat, alt_id, tp = '', '', 'none'
        # Check different identification fields based on model type
        id_val = getattr(person, 'assessor_moderator_identification_id', False) or \
                 getattr(person, 'learner_identification_id', False)

        if id_val and len(str(id_val)) == 13:
            nat = str(id_val)
        else:
            alt_id = person.national_id or person.passport_id or f'tmp{alt_ident}'
            tp = 'passport_number'

        return nat, normalize_alt_id(alt_id), tp

    def _prepare_person_vals(self, p, nat, alt_id, tp, country, broken, msg):
        """ Mapping Odoo fields to NLRD 25 dictionary """
        return {
            'National_Id': nat,
            'Person_Alternate_Id': alt_id,
            'Alternate_Id_Type': id_type_to_code(tp),
            'Equity_Code': equity_to_code(p.equity),
            'Nationality_Code': nationality_to_code(country.name) if country else 'ZA',
            'Home_Language_Code': lang_to_code(p.home_language_code.name) if p.home_language_code else '',
            'Gender_Code': gender_to_code(p.gender),
            'Citizen_Resident_Status_Code': citizen_map(p.citizen_resident_status_code),
            'Socioeconomic_Status_Code': socio_to_code(p.socio_economic_status),
            'Disability_Status_Code': disability_status_code(p.disability_status),
            'Person_First_Name': dual_name_removal(p.name or ''),
            'Person_Last_Name': dual_name_removal(p.person_last_name or ''),
            'Person_Birth_Date': fix_dates(p.person_birth_date),
            'Province_Code': province_to_code(p.person_home_province_code.id) if p.person_home_province_code else '',
            'Provider_Etqa_Id': '591',
            'Date_Stamp': fix_dates(p.write_date),
            'person_id': p.id,
            'broken': broken,
            'stat_msg': msg if broken else False,
        }

    def report_link_issues(self):
        # Search only for the fields you actually need to reduce memory usage
        nlrd29 = self.env['nlrd.29'].search([])

        # In Odoo 18, mapped() on IDs is fast, but set() is still great for primitives
        lrq_ids = nlrd29.ids
        lrq_prov_set = set(nlrd29.mapped('provider_code'))
        lrq_ass_set = set(nlrd29.mapped('assessors_id.id'))
        lrq_lnr_set = set(nlrd29.mapped('lrq_id.learner_id.id'))

        msg = [
            f"lrq count (29): {len(lrq_ids)}",
            f"unique providers in lrq (29): {len(lrq_prov_set)}",
            f"unique assessors in lrq (29): {len(lrq_ass_set)}",
            f"unique learners in lrq (29): {len(lrq_lnr_set)}"
        ]

        # Compare with 21 (Providers)
        nlrd21 = self.env['nlrd.21'].search([])
        act_prov_set = set(nlrd21.mapped('Provider_Code'))
        # Use set subtraction for much faster comparisons
        diff_prov = act_prov_set - lrq_prov_set

        msg.append(f"provider count in 21: {len(act_prov_set)}")
        msg.append(f"provider diff in 21 vs 29: {list(diff_prov)}")

        # Compare with 26 (Assessors)
        nlrd26 = self.env['nlrd.26'].search([])
        act_ass_set = set(nlrd26.mapped('assessor_id.id'))
        diff_ass = act_ass_set - lrq_ass_set

        msg.append(f"assessor count in 26: {len(act_ass_set)}")
        msg.append(f"assessor diff in 26 vs 29: {list(diff_ass)}")

        # ... continue for 24 and 27 ...

        final_msg = "\n".join(msg)
        _logger.info(final_msg)

        # Note: UserError is fine for debugging, but in Odoo 18,
        # a proper Notification or a multi-line message in a Wizard is preferred.
        raise UserError(final_msg)


    def do_all_v2(self):
        """ Sequential Execution of all build methods """
        self.build_lrq_29()
        self.build_providers_21()
        self.build_prov_acc_24()
        self.build_ass_26()
        self.build_ass_reg_27()
        self.build_person_25()

    def gen_all_dats(self):
        """ Migrated: Secure file handling instead of os.system """
        # Odoo 18: Never use os.system("rm -f ...") on a server path
        # Files should be managed in a temporary directory or via ir.attachment
        _logger.info("Generating all DAT files...")

        num_dict = {
            '21': dat21, '24': dat24, '26': dat26,
            '27': dat27, '29': dat29, '25': dat25
        }
        for code, mapping in num_dict.items():
            self.gen_dats(code, mapping)

        self.enum_dat_attachment()

    def _get_empty_stat_dict(self):
        return {k: 0 for k in [
            'identification_id', 'alternate_id_type', 'equity', 'country_id',
            'home_language_code', 'gender', 'citizen_resident_status_code',
            'socio_economic_status', 'disability_status', 'name',
            'person_last_name', 'person_birth_date', 'person_home_province_code'
        ]}

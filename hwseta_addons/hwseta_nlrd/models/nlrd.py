from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from .nlrd_dat import gendat, dat21, dat24, dat25, dat26, dat27, dat29

_logger = logging.getLogger(__name__)


class NlrdExporter(models.TransientModel):
    _name = 'nlrd.exporter'
    _description = 'NLRD Data Exporter'

    # --- VALIDATION LOGIC ---

    def check_lrq(self, lrq):
        """ Checks Learner Registration Qualifications for missing NLRD fields """
        broken = False
        msg = f"LRQ ID: {lrq.id}\n"

        # In Odoo 18, check related fields via dot notation
        if not lrq.learner_id.learner_identification_id and not lrq.learner_id.national_id:
            broken = True
            msg += '- Missing Identification (ID or Passport)\n'
        if not lrq.learner_qualification_parent_id.saqa_qual_id:
            broken = True
            msg += '- Missing SAQA Qualification Code\n'
        if not lrq.certificate_date:
            broken = True
            msg += '- Missing Certification Date\n'
        if not lrq.provider_id:
            broken = True
            msg += '- No Provider linked to LRQ\n'

        return broken, msg


    def check_person(self, person):
        """ Checks Employees (Assessors/Learners) for NLRD File 25/26 requirements """
        broken = False
        msg = f"Person ID: {person.id}\n"

        # Check if the person is an Assessor or Learner
        if not (person.is_learner or person.is_assessors):
            return True, f"{msg}- Person is neither a learner nor an assessor.\n"

        if not person.name or not person.person_last_name:
            broken = True
            msg += "- Missing First or Last Name\n"

        if not person.gender_saqa_code:
            broken = True
            msg += "- Missing Gender SAQA Code\n"

        return broken, msg

    # --- EXTRACTION LOGIC ---

    def fetch_nlrd_29(self):
        """ Extract Learner Enrollments (NLRD File 29) """
        # Updated domain for Odoo 18 date filtering
        domain = [('certificate_date', '>', '2020-02-01')]
        brk_count = 0
        right_count = 0

        lrqs = self.env['learner.registration.qualification'].search(domain)
        for lrq in lrqs:
            broken, msg = self.check_lrq(lrq)
            if not broken:
                right_count += 1
                val = {
                    'national_id': lrq.learner_id.learner_identification_id,
                    'person_alternate_id': lrq.learner_id.national_id,
                    'alternate_id_type': id_type_to_code(lrq.learner_id.alternate_id_type or 'none'),
                    'qualification_id': lrq.learner_qualification_parent_id.saqa_qual_id,
                    'learner_achievement_status_id': lrq.qual_status,
                    'assessor_registration_number': lrq.assessors_id.assessor_seq_no,
                    'learner_achievement_type_id': '6',
                    'learner_enrolled_date': fix_dates(lrq.start_date),
                    'provider_code': lrq.provider_id.id,
                    'provider_etqa_id': '591',
                    'certification_date': fix_dates(lrq.certificate_date),
                    'date_stamp': fix_dates(lrq.certificate_date),
                    'lrq_id': lrq.id,
                    'learner_id': lrq.learner_id.id,
                }
                self.env['nlrd.29'].create(val)
            else:
                brk_count += 1
                _logger.warning(msg)

    def fetch_nlrd_21(self):
        """ Extract Providers (NLRD File 21) """
        domain = [('provider', '=', True)]
        partners = self.env['res.partner'].search(domain)

        for provider in partners:
            broken, msg = self.check_provider(provider)
            if not broken:
                # Handle addresses with Odoo 18 defaults
                post_addy1 = provider.postal_address_1 or '123 Blom street'
                eddy = fix_dates(make_up_date(provider.provider_end_date, provider))

                val = {
                    'Provider_Code': provider.id,
                    'Etqa_Id': '591',
                    'Provider_Name': remove_school(provider.name.strip()),
                    'Provider_Address_1': sanitize_addrs(post_addy1),
                    'Provider_Postal_Code': cleanse_postcode(provider.zip_postal),
                    'Provider_Accreditation_Num': provider.provider_accreditation_num,
                    'Provider_Accredit_Start_Date': fix_dates(filth_date_gap(provider.provider_start_date, eddy)),
                    'Provider_Accredit_End_Date': eddy,
                    'Province_Code': province_to_code(provider.province_code_physical.id),
                    'Country_Code': 'ZA',
                    'Date_Stamp': fix_dates(provider.write_date),
                    'provider_id': provider.id,
                }
                self.env['nlrd.21'].create(val)

    def fetch_nlrd_26(self):
        """ Extract Assessor Registrations (NLRD File 26) """
        assessors = self.env['hr.employee'].search([('is_assessors', '=', True)])

        for assessor in assessors:
            broken, msg = self.check_person(assessor)
            if not broken:
                val = {
                    'National_Id': assessor.assessor_moderator_identification_id,
                    'Person_Alternate_Id': assessor.national_id,
                    'Alternate_Type_Id': id_type_to_code(assessor.alternate_id_type or 'none'),
                    'Designation_Registration_Number': assessor.assessor_seq_no,
                    'Designation_Etqa_Id': '591',
                    'Designation_Start_Date': fix_dates(assessor.start_date),
                    'Designation_End_Date': fix_dates(assessor.end_date),
                    'Date_Stamp': fix_dates(assessor.write_date),
                    'assessor_id': assessor.id,
                }
                self.env['nlrd.26'].create(val)

    def check_accreditation(self, accreditation):
        """ Checks if the Provider-Qualification link is valid for NLRD 24 """
        broken = False
        msg = f"Accreditation ID: {accreditation.id}\n"

        # Accessing related objects safely in Odoo 18
        parent = accreditation.accreditation_qualification_id
        provider = parent.related_provider

        if not accreditation.qualification_id.saqa_qual_id:
            broken = True
            msg += "- Missing SAQA Qualification ID\n"

        if not parent.accreditation_number:
            broken = True
            msg += f"- Missing accreditation number on parent {parent.id}\n"

        if not provider:
            broken = True
            msg += "- No related provider found\n"
        elif not provider.provider_start_date or not provider.provider_end_date:
            broken = True
            msg += f"- Provider {provider.id} missing start or end dates\n"

        return broken, msg

    def check_provider(self, partner):
        if not partner:
            return True, "No partner provided\n"

        broken = False
        messages = [f"{partner.id}\n"]

        if not partner.provider_accreditation_num or partner.provider_accreditation_num == '0':
            broken = True
            messages.append('no provider code')

        if not partner.name:
            broken = True
            messages.append('no provider name')

        if not partner.zip_postal:
            broken = True
            messages.append('no provider zip_postal')

        return broken, "\n".join(messages)

    def fetch_nlrd_24(self):
        """ Extracts Provider-Qualification scope into staging table 24 """
        # domain updated for modern field string consistency
        domain = [('accreditation_qualification_id.final_state', '=', 'Approved')]
        brk_count = 0
        right_count = 0

        accreditations = self.env['accreditation.qualification'].search(domain)

        for acc in accreditations:
            broken, msg = self.check_accreditation(acc)

            # Resolve status code
            prov = acc.accreditation_qualification_id.related_provider
            stat_code = provider_accredit_status_to_code('Active' if prov.active else 'Inactive')

            if not broken:
                right_count += 1
                val = {
                    'Learnership_Id': '',
                    'Qualification_Id': acc.qualification_id.saqa_qual_id,
                    'Unit_Standard_Id': '',
                    'Provider_Code': prov.id,
                    'Provider_Etqa_Id': '591',
                    'Provider_Accreditation_Num': acc.accreditation_qualification_id.accreditation_number,
                    'Provider_Accredit_Assessor_Ind': '',
                    'Provider_Accred_Start_Date': fix_dates(prov.provider_start_date),
                    'Provider_Accred_End_Date': fix_dates(prov.provider_end_date),
                    'Etqa_Decision_Number': '',
                    'Provider_Accred_Status_Code': stat_code,
                    'Date_Stamp': fix_dates(acc.accreditation_qualification_id.write_date),
                    'accreditation_id': acc.id,
                }
                if global_write:
                    self.env['nlrd.24'].create(val)
            else:
                brk_count += 1
                _logger.warning(msg)

    # --- ASSESSOR REGISTER (FILE 27) ---

    def check_register(self, register):
        """ Validates Assessor Qualification Scope for NLRD 27 """
        broken = False
        parent = register.assessors_moderators_qualification_id
        msg = f"Assessor Register ID: {parent.id}\n"

        if not register.qualification_id.saqa_qual_id:
            broken = True
            msg += "- Missing Qualification SAQA ID\n"

        # Check for assessor identity using exists check
        has_id = any([
            parent.existing_assessor_number,
            parent.temp_assessor_seq_no,
            parent.existing_assessor_id
        ])
        if not has_id:
            broken = True
            msg += "- No assessor sequence or ID number found\n"

        if not parent.assessor_moderator_register_date or not parent.assessor_moderator_approval_date:
            broken = True
            msg += "- Missing registration or approval dates\n"

        return broken, msg

    def attach_assessor(self, register):
        """
        Links a registration record to the HR Employee (Assessor) object.
        Optimized Odoo 18 search.
        """
        msg = ''
        search_domain = [
            '|',
            ('assessor_moderator_identification_id', '=', register.temp_assessor_seq_no),
            ('assessor_moderator_identification_id', '=', register.existing_assessor_id),
            ('assessor_moderator_identification_id', '!=', False)
        ]

        assessor_objs = self.env['hr.employee'].search(search_domain)

        if len(assessor_objs) > 1:
            return False, True, 'Multiple assessor records found for this ID.'

        if not assessor_objs:
            return False, True, 'Assessor not found in employee records.'

        assessor = assessor_objs[0]
        status_msg = 'Assessor linked (Inactive)' if not assessor.is_active_assessor else 'Assessor linked'

        return assessor, False, status_msg

    def check_25(self, person_obj, role_type, stat_dict):
        """
        Validates person data.
        role_type: 'a' for Assessor, 'l' for Learner
        """
        broken = False
        msg_parts = []

        # Determine which Odoo record to look at
        # In Odoo 18, we use dot notation to reach the actual Employee or Learner record
        person = person_obj.assessor_id if role_type == 'a' else person_obj.lrq_id.learner_id

        if not person:
            return True, "No linked person record found", stat_dict

        # Core Validation checks
        checks = [
            ('identification_id',
             person.learner_identification_id or person.national_id or person.assessor_moderator_identification_id),
            ('equity', person.equity),
            ('country_id', person.country_id),
            ('home_language_code', person.home_language_code),
            ('gender', person.gender),
            ('name', person.name),
            ('person_last_name', person.person_last_name),
            ('person_birth_date', person.person_birth_date),
            ('person_home_province_code', person.person_home_province_code),
        ]

        for field_key, value in checks:
            if not value:
                broken = True
                msg_parts.append(f"Missing {field_key}")
                if field_key in stat_dict:
                    stat_dict[field_key] += 1

        msg = f"{person.id}: " + ", ".join(msg_parts) if broken else ""
        return broken, msg, stat_dict

    def fetch_nlrd_25(self):
        """
        Aggregates Assessors and unique Learners into the nlrd.25 staging table.
        """
        # 1. Process Assessors (from staging table nlrd.26)
        assessor_stats = self._init_stat_dict()
        assessors = self.env['nlrd.26'].search([])

        for acc_record in assessors:
            broken, msg, assessor_stats = self.check_25(acc_record, 'a', assessor_stats)
            if not broken:
                val = self._prepare_person_val(acc_record.assessor_id, acc_record)
                if global_write:
                    new_person = self.env['nlrd.25'].create(val)
                    acc_record.write({'person_id': new_person.id})

        # 2. Process Unique Learners (from staging table nlrd.29)
        learner_stats = self._init_stat_dict()
        all_learner_records = self.env['nlrd.29'].search([])

        # Odoo 18 Deduplication: Get unique learner IDs using mapped and set
        unique_learner_ids = set(all_learner_records.mapped('lrq_id.learner_id.id'))

        for l_id in unique_learner_ids:
            # Get the first occurrence of this learner to extract their details
            lrq_record = all_learner_records.filtered(lambda r: r.lrq_id.learner_id.id == l_id)[0]
            learner = lrq_record.lrq_id.learner_id

            broken, msg, learner_stats = self.check_25(lrq_record, 'l', learner_stats)
            if not broken:
                val = self._prepare_person_val(learner, lrq_record)
                if global_write:
                    new_person = self.env['nlrd.25'].create(val)
                    # Link all lrq records for this learner to the one staging person
                    related_lrqs = all_learner_records.filtered(lambda r: r.lrq_id.learner_id.id == l_id)
                    related_lrqs.write({'person_id': new_person.id})

    def _prepare_person_val(self, person, staging_rec):
        """ Helper to map Odoo fields to NLRD 25 dictionary format """
        return {
            'National_Id': getattr(person, 'identification_id', False) or getattr(person,
                                                                                  'assessor_moderator_identification_id',
                                                                                  False) or staging_rec.National_Id,
            'Person_Alternate_Id': person.national_id,
            'Alternate_Id_Type': id_type_to_code(person.alternate_id_type or 'none'),
            'Equity_Code': equity_to_code(person.equity),
            'Nationality_Code': nationality_to_code(person.country_id.name),
            'Home_Language_Code': lang_to_code(person.home_language_code.name),
            'Gender_Code': gender_to_code(person.gender),
            'Citizen_Resident_Status_Code': person.citizen_resident_status_code,
            'Socioeconomic_Status_Code': socio_to_code(person.socio_economic_status),
            'Disability_Status_Code': disability_status_code(person.disability_status),
            'Person_First_Name': person.name,
            'Person_Last_Name': person.person_last_name,
            'Person_Birth_Date': fix_dates(person.person_birth_date),
            'Province_Code': province_to_code(person.person_home_province_code.id),
            'Provider_Etqa_Id': '591',
            'Date_Stamp': fix_dates(person.write_date),
            'person_id': person.id,
        }

    def _init_stat_dict(self):
        return {k: 0 for k in ['identification_id', 'equity', 'country_id', 'home_language_code',
                               'gender', 'name', 'person_last_name', 'person_birth_date',
                               'person_home_province_code']}

    def unlink_all(self):
        """ Clears all staging tables in one go. Optimized for Odoo 18. """
        models_to_clean = ['nlrd.21', 'nlrd.24', 'nlrd.25', 'nlrd.26', 'nlrd.27', 'nlrd.29']
        for m in models_to_clean:
            records = self.env[m].search([])
            if records:
                records.unlink()
        _logger.info("NLRD Staging Tables Cleared.")

    def inverse_check(self):
        """
        Removes staging records that successfully linked to a Person record.
        This leaves only the 'broken' records for debugging in the staging UI.
        """
        # Batch search and batch unlink is much faster in Odoo 18
        lrqs = self.env['nlrd.29'].search([('person_id', '!=', False)])
        lrq_count = len(lrqs)
        lrqs.unlink()

        assessors = self.env['nlrd.26'].search([('person_id', '!=', False)])
        ass_count = len(assessors)
        assessors.unlink()

        _logger.info(f"Cleanup: Removed {lrq_count} LRQs and {ass_count} Assessors with valid links.")

    # --- DAT FILE GENERATION ---

    def gen_dats(self, num, mapping):
        """
        Generic DAT generator.
        mapping[0] = lengths, mapping[1] = field_names
        """
        model_name = f'nlrd.{num}'
        records = self.env[model_name].search([])

        # Fields to exclude from the fixed-width DAT file
        internal_fields = {
            'display_name', 'id', 'create_date', 'create_uid',
            'write_uid', 'write_date', '__last_update',
            'person_id', 'provider_id', 'lrq_id', 'stat_msg', 'link_broken'
        }

        for rec in records:
            # Get raw data dict
            # In Python 3.12, read() returns a list of dicts with modern types
            raw_data = rec.read()[0]

            # Create a cleaned dictionary for the generator
            p_dict = OD()
            # Ensure fields are added in the order defined in your mapping
            for field in mapping[1]:
                val = raw_data.get(field, "")
                p_dict[field] = val if val is not False and val is not None else ""

            # Call the migrated gendat from nlrd_utils
            gendat(p_dict, mapping[0], mapping[1], dat_names[num])

    def gen_all_dats(self):
        """
        Odoo 18 version of gen_all_dats.
        @api.multi is removed as it is default behavior.
        """
        num_dict = {
            '21': dat21,
            '24': dat24,
            '26': dat26,
            '27': dat27,
            '29': dat29,
            '25': dat25
        }
        for file_num, spec in num_dict.items():
            self.gen_dats(file_num, spec)


    def fetch_nlrd_27(self):

        domain = [
            ('assessors_moderators_qualification_id.final_state', '=', 'Approved'),
            ('assessors_moderators_qualification_id.assessor_moderator', '=', 'assessor')
        ]

        brk_count = 0
        right_count = 0
        big_daddy = ''

        registers = self.env['assessors.moderators.qualification'].search(domain)

        for register in registers:

            broken, msg = self.check_register(register)

            reg_num = (
                    register.assessors_moderators_qualification_id.temp_assessor_seq_no
                    or register.assessors_moderators_qualification_id.existing_assessor_number
                    or register.assessors_moderators_qualification_id.existing_assessor_id
                    or ''
            )

            registration = register.assessors_moderators_qualification_id

            assessor_obj, link_broken, assessor_msg = self.attach_assessor(registration)

            assessor_id = assessor_obj.id if assessor_obj else False

            if not broken:
                right_count += 1

                vals = {
                    'Learnership_Id': '',
                    'Qualification_Id': register.qualification_id.saqa_qual_id,
                    'Unit_Standard_Id': '',
                    'Designation_Id': '501',
                    'Designation_Registration_Number': reg_num,
                    'Designation_Etqa_Id': '591',
                    'Nqf_Designation_Start_Date': self.fix_dates(
                        registration.assessor_moderator_register_date
                    ),
                    'Nqf_Designation_End_Date': self.fix_dates(
                        registration.assessor_moderator_approval_date
                    ),
                    'Etqa_Decision_Number': '',
                    'Nqf_Desig_Status_Code': 'A',
                    'Date_Stamp': self.fix_dates(register.write_date),
                    'register_id': register.id,
                    'person_id': assessor_id,
                    'stat_msg': assessor_msg,
                    'link_broken': link_broken,
                    'broken': False,
                }

                _logger.info("NLRD27 OK: %s", assessor_msg)

                self.env['nlrd.27'].create(vals)

            else:
                brk_count += 1
                big_daddy += f"\n\n{msg}"
                _logger.warning("NLRD27 BROKEN: %s", register.id)

        _logger.info("NLRD27 Broken: %s", brk_count)
        _logger.info("NLRD27 Correct: %s", right_count)

        return True

    def gen_21(self):
        records = self.env['nlrd.21'].search([])

        for rec in records:
            data = rec.read()[0]

            # Remove Odoo system fields
            for field in [
                'provider_id', 'display_name', 'id',
                'create_date', 'create_uid',
                'write_uid', 'write_date', '__last_update'
            ]:
                data.pop(field, None)

            ordered_data = OD(data)

            gendat(
                ordered_data,
                dat21[0],
                dat21[1],
                "21_nlrd.dat"
            )

        _logger.info("NLRD21 DAT file generated successfully")
        return True

    def gen_25(self):

        records = self.env['nlrd.25'].search([])

        for rec in records:
            data = rec.read()[0]

            # Remove Odoo technical fields
            for field in [
                'person_id', 'display_name', 'id',
                'create_date', 'create_uid',
                'write_uid', 'write_date', '__last_update'
            ]:
                data.pop(field, None)

            _logger.debug("NLRD25 DATA: %s", data)

            ordered_data = OD(data)

            gendat(
                ordered_data,
                dat25[0],
                dat25[1],
                "25_nlrd.dat"
            )

        _logger.info("NLRD25 DAT diff_29_pidfile generated successfully")
        return True
    # --- MASTER EXECUTION ---

    def diff_29_pid(self):
        prov_nums = set()
        del_nums = []
        diff = []

        # Collect unique provider codes from nlrd.29
        nlrd29_records = self.env['nlrd.29'].search([])
        for lrq in nlrd29_records:
            if lrq.provider_code:
                prov_nums.add(lrq.provider_code)

        prov_del_count = 0
        prov_keep = 0

        nlrd21_records = self.env['nlrd.21'].search([])
        original_prov_count = len(nlrd21_records)

        for prov in nlrd21_records:
            if prov.Provider_Code not in prov_nums:
                del_nums.append(prov.Provider_Code)
                prov_del_count += 1
            else:
                diff.append(prov.Provider_Code)
                prov_keep += 1

        msg = (
            f"keep providers count: {prov_keep}\n"
            f"original providers count: {original_prov_count}\n"
            f"unique providers in nlrd.29: {len(prov_nums)}\n"
            f"deleted provs count: {prov_del_count}\n"
            f"del providers: {del_nums}\n"
            f"diff providers count: {len(del_nums)}\n"
            f"diff providers list: {del_nums}\n"
        )

        raise UserError(msg)

    def do_all(self):
        """ The 'Big Red Button' logic for the NLRD Export. """
        self.unlink_all()  # Start fresh
        self.fetch_nlrd_21()  # Providers
        self.fetch_nlrd_24()  # Provider-Qual links
        self.fetch_nlrd_26()  # Assessors
        self.fetch_nlrd_27()  # Assessor Scopes
        self.fetch_nlrd_29()  # Learner Enrollments
        self.fetch_nlrd_25()  # Person Master (Aggregated)

        # self.inverse_check() # Optional: Uncomment to delete 'good' records from UI
        self.gen_all_dats()  # Write to File System

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Export Complete'),
                'message': _('NLRD DAT files have been generated in /tmp/nlrd_dat_files/'),
                'sticky': False,
            }
        }

    def del_extra_provs(self):
        """
        Removes providers from staging table 21 if they aren't
        referenced by any learners in staging table 29.
        """
        # 1. Use mapped() to get all provider codes from the Enrollment staging table
        # Using set() instantly deduplicates the list for a faster 'in' check
        active_lrq_prov_codes = set(self.env['nlrd.29'].search([]).mapped('provider_code'))

        # 2. Get all provider records currently in the Provider staging table
        all_staging_providers = self.env['nlrd.21'].search([])

        # 3. Filter the recordset to find providers NOT in the active set
        # This happens in memory, which is much faster than individual SQL searches
        to_delete = all_staging_providers.filtered(
            lambda p: p.Provider_Code not in active_lrq_prov_codes
        )

        # 4. Perform a batch unlink (One single SQL DELETE command)
        del_count = len(to_delete)
        if to_delete:
            to_delete.unlink()

        _logger.info(f"NLRD Cleanup: Pruned {del_count} redundant providers from File 21.")


class NlrdReport(models.Model):
    _name = 'nlrd.report'
    _description = 'NLRD Export Validation Report'

    name = fields.Char(string="Name")
    # Link to whichever staging record caused the error
    nlrd_21_id = fields.Many2one('nlrd.21', string="NLRD 21 ID")
    nlrd_24_id = fields.Many2one('nlrd.24', string="NLRD 24 ID")
    nlrd_25_id = fields.Many2one('nlrd.25', string="NRLD 25 ID")
    nlrd_26_id = fields.Many2one('nlrd.26', string="NLRD 26 ID")
    nlrd_27_id = fields.Many2one('nlrd.27', string="NLRD 27 ID")
    nlrd_29_id = fields.Many2one('nlrd.29', string="NLRD 29 ID")

    # Generic link back to the actual Odoo record (Source)
    doc_model = fields.Char(string="Doc Model")
    doc_id = fields.Integer(string="Doc ID")  # Changed to Integer for performance
    message = fields.Text(string="Message")


class Nlrd29(models.Model):
    _name = 'nlrd.29'
    _description = 'NLRD Staging: Learner Achievements (File 29)'

    # Identification (Indexed for performance)
    national_id = fields.Char(index=True)
    person_alternate_id = fields.Char(index=True)
    alternate_id_type = fields.Char()
    qualification_id = fields.Char(index=True)

    # Status & Dates
    learner_achievement_status_id = fields.Char()
    learner_achievement_type_id = fields.Char()
    learner_achievement_date = fields.Char()
    learner_enrolled_date = fields.Char()
    certification_date = fields.Char()
    date_stamp = fields.Char()

    # Scope & Codes
    assessor_registration_number = fields.Char()
    honours_classification = fields.Char()
    part_of = fields.Char()
    learnership_id = fields.Char()
    provider_code = fields.Char()
    provider_etqa_id = fields.Char()
    assessor_etqa_id = fields.Char()

    # Odoo Relations (Source Tracking)
    learner_id = fields.Many2one('hr.employee', string="Source Learner")
    assessors_id = fields.Many2one('hr.employee', string="Source Assessor")
    lrq_id = fields.Many2one('learner.registration.qualification', string="LRQ ID")
    person_id = fields.Many2one('nlrd.25', string="Linked Person Record")

    # Validation Tracking
    link_broken = fields.Boolean(string="Link Broken", default=False)
    broken = fields.Boolean(string="Broken", default=False)
    # stat_msg = fields.Text(string="System Message")


class Nlrd21(models.Model):
    _name = 'nlrd.21'
    _description = 'NLRD Staging: Provider Information (File 21)'
    _rec_name = 'Provider_Name'

    # Core Identifiers
    Provider_Code = fields.Char(index=True, help="Unique code assigned by the ETQA")
    Etqa_Id = fields.Char(help="ETQA Identifier (e.g., 591)")

    # Organization Details
    Std_Industry_Class_Code = fields.Char()
    Provider_Name = fields.Char()
    Provider_Type_Id = fields.Char()
    Provider_Sars_Number = fields.Char()
    Provider_Class_Id = fields.Char()
    Provider_Contact_Name = fields.Char()

    # Contact & Postal Info
    Provider_Address_1 = fields.Char()
    Provider_Address_2 = fields.Char()
    Provider_Address_3 = fields.Char()
    Provider_Postal_Code = fields.Char()
    Provider_Phone_Number = fields.Char()
    Provider_Fax_Number = fields.Char()

    # Accreditation Details
    Provider_Accreditation_Num = fields.Char()
    Provider_Accredit_Start_Date = fields.Char()
    Provider_Accredit_End_Date = fields.Char()
    Etqa_Decision_Number = fields.Char()

    # Physical Location (NLRD Requirement)
    Province_Code = fields.Char()
    Country_Code = fields.Char()
    Latitude_Degree = fields.Char()
    Latitude_Minutes = fields.Char()
    Latitude_Seconds = fields.Char()
    Longitude_Degree = fields.Char()
    Longitude_Minutes = fields.Char()
    Longitude_Seconds = fields.Char()

    Provider_Physical_Address_1 = fields.Char()
    Provider_Physical_Address_2 = fields.Char()
    Provider_Physical_Address_Town = fields.Char()
    Provider_Phys_Address_Postcode = fields.Char()
    Provider_Web_Address = fields.Char()

    # Audit & Tracking
    Date_Stamp = fields.Char()
    provider_id = fields.Many2one('res.partner', string="Source Partner", index=True)

    # Staging Validation Flags
    link_broken = fields.Boolean(string="Link Missing", default=False)
    broken = fields.Boolean(string="Data Error", default=False, index=True)
    stat_msg = fields.Text(string="Validation Message")

    Provider_Contact_Email_Address = fields.Char()
    Provider_Contact_Phone_Number = fields.Char()
    Provider_Contact_Cell_Number = fields.Char()
    Structure_Status_Id = fields.Char()


class Nlrd24(models.Model):
    """
    NLRD File 24: Provider Accreditation Scope
    Defines what a provider is accredited to train (Quals/Unit Standards).
    """
    _name = 'nlrd.24'
    _description = 'NLRD Staging: Provider Accreditation'
    _rec_name = 'Qualification_Id'

    # Fixed-width Data Fields
    Learnership_Id = fields.Char(string="Learnership ID")
    Qualification_Id = fields.Char(string="Qualification ID")
    Unit_Standard_Id = fields.Char(string="Unit Standard ID")
    Provider_Code = fields.Char(string="Provider Code")
    Provider_Etqa_Id = fields.Char(string="Provider ETQA ID")
    Provider_Accreditation_Num = fields.Char(string="Accreditation Number")
    Provider_Accredit_Assessor_Ind = fields.Char(string="Assessor Indicator")
    Provider_Accred_Start_Date = fields.Char(string="Accreditation Start Date")
    Provider_Accred_End_Date = fields.Char(string="Accreditation End Date")
    Etqa_Decision_Number = fields.Char(string="ETQA Decision Number")
    Provider_Accred_Status_Code = fields.Char(string="Status Code")
    Date_Stamp = fields.Char(string="Date Stamp")

    # Odoo Relations & Internal Logic
    accreditation_id = fields.Many2one(
        'provider.master.qualification',
        string="Source Accreditation Record"
    )
    link_broken = fields.Boolean(string="Link Broken", default=False)
    broken = fields.Boolean(string="Data Error", default=False)
    stat_msg = fields.Text(string="Validation Message")


class Nlrd25(models.Model):
    """
    NLRD File 25: Person Information
    The Master file for all Learners and Assessors.
    """
    _name = 'nlrd.25'
    _description = 'NLRD Staging: Person Information'
    _rec_name = 'National_Id'

    # Identification
    National_Id = fields.Char(string="National ID", index=True)
    Person_Alternate_Id = fields.Char(string="Person Alternate ID")
    Alternate_Id_Type = fields.Char(string="Alternate ID Type")

    # Demographic Codes
    Equity_Code = fields.Char(string="Equity Code")
    Nationality_Code = fields.Char(string="Nationality Code")
    Home_Language_Code = fields.Char(string="Home Language Code")
    Gender_Code = fields.Char(string="Gender Code")
    Citizen_Resident_Status_Code = fields.Char(string="Resident Status Code")
    Socioeconomic_Status_Code = fields.Char(string="Socioeconomic Status Code")
    Disability_Status_Code = fields.Char(string="Disability Status Code")

    # Names & Personal Details
    Person_First_Name = fields.Char(string="First Name")
    Person_Last_Name = fields.Char(string="Last Name")
    Person_Middle_Name = fields.Char(string="Middle Name")
    Person_Title = fields.Char(string="Title")
    Person_Birth_Date = fields.Char(string="Birth Date")

    # Address & Contact
    Person_Home_Address_1 = fields.Char(string="Home Address 1")
    Person_Home_Address_2 = fields.Char(string="Home Address 2")
    Person_Home_Address_3 = fields.Char(string="Home Address 3")
    Person_Postal_Address_1 = fields.Char(string="Postal Address 1")
    Person_Postal_Address_2 = fields.Char(string="Postal Address 2")
    Person_Postal_Address_3 = fields.Char(string="Postal Address 3")
    Person_Home_Addr_Postal_Code = fields.Char(string="Home Postal Code")
    Person_Postal_Addr_Post_Code = fields.Char(string="Postal Addr Post Code")
    Person_Phone_Number = fields.Char(string="Phone Number")
    Person_Cell_Phone_Number = fields.Char(string="Cell Phone Number")
    Person_Fax_Number = fields.Char(string="Fax Number")
    Person_Email_Address = fields.Char(string="Email Address")

    # Regional & Provider Info
    Province_Code = fields.Char(string="Province Code")
    Provider_Code = fields.Char(string="Provider Code")
    Provider_Etqa_Id = fields.Char(string="Provider ETQA ID")

    # Legacy / Previous Info
    Person_Previous_Provider_Lastname = fields.Char(string="Prev Provider Lastname")
    Person_Previous_Alternate_Id = fields.Char(string="Prev Alternate ID")
    Person_Previous_Alternate_Id_Type = fields.Char(string="Prev Alternate ID Type")
    Person_Previous_Provider_Code = fields.Char(string="Prev Provider Code")
    Person_Previous_Provider_Etqe_Id = fields.Char(string="Prev Provider ETQA ID")

    # Disability Ratings
    Seeing_Rating_Id = fields.Char(string="Seeing Rating")
    Hearing_Rating_Id = fields.Char(string="Hearing Rating")
    Communicating_Rating_Id = fields.Char(string="Communicating Rating")
    Walking_Rating_Id = fields.Char(string="Walking Rating")
    Remembering_Rating_Id = fields.Char(string="Remembering Rating")
    Self_Care_Rating_Id = fields.Char(string="Self Care Rating")

    # Odoo Relations & Audit
    Date_Stamp = fields.Char(string="Date Stamp")
    person_id = fields.Many2one(
        'hr.employee',
        string="Source Employee/Learner"
    )
    broken = fields.Boolean(string="Broken", default=False)
    link_broken = fields.Boolean(string="Link Broken", default=False)
    stat_msg = fields.Text(string="Validation Message")

class Nlrd26(models.Model):
    _name = 'nlrd.26'
    _description = 'NLRD 26 Assessor Record'
    _order = 'id desc'

    National_Id = fields.Char(string="National ID")
    Person_Alternate_Id = fields.Char(string="Alternate ID")
    Alternate_Type_Id = fields.Char(string="Alternate Type")
    Designation_Id = fields.Char(string="Designation ID")
    Designation_Registration_Number = fields.Char(string="Designation Registration Number")
    Designation_Etqa_Id = fields.Char(string="Designation ETQA ID")
    Designation_Start_Date = fields.Char(string="Designation Start Date")
    Designation_End_Date = fields.Char(string="Designation End Date")
    Structure_Status_Id = fields.Char(string="Structure Status ID")
    Etqa_Decision_Number = fields.Char(string="ETQA Decision Number")
    Provider_Code = fields.Char(string="Provider Code")
    Provider_Etqa_Id = fields.Char(string="Provider ETQA ID")
    Date_Stamp = fields.Char(string="Date Stamp")

    assessor_id = fields.Many2one(
        'hr.employee',
        string="Assessor",
        ondelete='set null'
    )

    person_id = fields.Many2one(
        'nlrd.25',
        string="Person",
        ondelete='set null'
    )

    link_broken = fields.Boolean(string="Link Broken", default=False)
    broken = fields.Boolean(string="Broken", default=False)
    stat_msg = fields.Text(string="Status Message")

class Nlrd27(models.Model):
    _name = 'nlrd.27'
    _description = 'NLRD 27 Assessor Registration'
    _order = 'id desc'

    Learnership_Id = fields.Char(string="Learnership ID")
    Qualification_Id = fields.Char(string="Qualification ID")
    Unit_Standard_Id = fields.Char(string="Unit Standard ID")
    Designation_Id = fields.Char(string="Designation ID")
    Designation_Registration_Number = fields.Char(string="Designation Registration Number")
    Designation_Etqa_Id = fields.Char(string="Designation ETQA ID")
    Nqf_Designation_Start_Date = fields.Char(string="NQF Designation Start Date")
    Nqf_Designation_End_Date = fields.Char(string="NQF Designation End Date")
    Etqa_Decision_Number = fields.Char(string="ETQA Decision Number")
    Nqf_Desig_Status_Code = fields.Char(string="NQF Designation Status Code")
    Date_Stamp = fields.Char(string="Date Stamp")

    register_id = fields.Many2one(
        'assessors.moderators.qualification.hr',
        string="Assessor Qualification",
        ondelete='set null'
    )

    person_id = fields.Many2one(
        'hr.employee',
        string="Person",
        ondelete='set null'
    )

    broken = fields.Boolean(string="Broken", default=False)
    link_broken = fields.Boolean(string="Link Broken", default=False)
    stat_msg = fields.Text(string="Status Message")

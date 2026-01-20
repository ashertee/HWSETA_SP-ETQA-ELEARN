# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime as dt
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

DEBUG = True


def dbg(msg):
    if DEBUG:
        _logger.info(msg)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def to_relativedelta(tdelta):
    return relativedelta(
        seconds=int(tdelta.total_seconds()),
        microseconds=tdelta.microseconds
    )


BAD_WORDS = [
    'section','ext','extension','str','street','cres','crescent','ave','avenue',
    'blvd','boulevard','road','rd','drive','dr','park','north','east','south','west','block'
]


def country_check(person):
    checks = [
        person.country_home,
        person.work_country,
        person.country_postal,
        person.person_home_province_code.country_id if person.person_home_province_code else None,
        person.work_province.country_id if person.work_province else None,
        person.physical_municipality.country_id if person.physical_municipality else None,
        person.work_municipality.country_id if person.work_municipality else None,
        person.postal_municipality.country_id if person.postal_municipality else None,
        person.person_home_suburb.country_id if person.person_home_suburb else None,
        person.person_suburb.country_id if person.person_suburb else None,
    ]
    for c in checks:
        if c:
            return c, "country resolved"
    return False, "found no way to match"


def province_check(person):
    checks = [
        person.work_province,
        person.physical_municipality.province_id if person.physical_municipality else None,
        person.work_municipality.province_id if person.work_municipality else None,
        person.postal_municipality.province_id if person.postal_municipality else None,
        person.person_home_suburb.province_id if person.person_home_suburb else None,
        person.person_suburb.province_id if person.person_suburb else None,
    ]
    for p in checks:
        if p:
            return p, "province resolved"
    return False, "found no way to match"


# --------------------------------------------------
# WIZARD
# --------------------------------------------------

class NlrdAdminWizard(models.TransientModel):
    _name = 'nlrd.admin.wiz'
    _description = 'NLRD Administration Wizard'

    learner_id = fields.Many2one('hr.employee')

    # ----------------------------------------------

    def unlink_all(self):
        self.env['nlrd.report'].search([]).unlink()

    # ----------------------------------------------

    def fix_addr(self, addr_string, hr):
        addr_string = ''.join([i for i in addr_string if not i.isdigit()])
        for word in addr_string.split():
            if word.lower() in BAD_WORDS:
                continue
            for model in ['res.city','res.district','res.suburb']:
                rec = self.env[model].search([('name','ilike',word),('province_id','!=',False)], limit=1)
                if rec:
                    return rec.province_id, f"Province {rec.province_id.name} resolved"
        return False, "no match"

    # ----------------------------------------------

    def fix_assessor(self):
        for rec in self.env['nlrd.26'].search([('broken','=',True)]):
            assessor = rec.assessor_id
            msg = ""

            if "no id/nat/passport found" in rec.stat_msg:
                msg += "no id/nat/passport found"

            self.env['nlrd.report'].create({
                'name': msg,
                'nlrd_26_id': rec.id,
                'doc_id': rec.id,
                'doc_model': 'nlrd.26',
                'message': msg
            })

    # ----------------------------------------------

    def fix_assessor_qual(self):
        for rec in self.env['nlrd.27'].search([('broken','=',True)]):
            msg = rec.stat_msg or ''
            self.env['nlrd.report'].create({
                'name': msg,
                'nlrd_27_id': rec.id,
                'doc_id': rec.id,
                'doc_model': 'nlrd.27',
                'message': msg
            })

    # ----------------------------------------------
    @api.model
    def fix_lrq(self):
        lrqs_deleted = []

        broken_records = self.env['nlrd.29'].search([('broken', '=', True)])

        for nlrd29 in broken_records:
            lrq_object = nlrd29.lrq_id

            if not lrq_object:
                continue

            # ---- CASE 1: Missing assessor ----
            if "no assessor number" in (nlrd29.stat_msg or ""):

                learner = lrq_object.learner_id
                if learner and learner.learner_qualification_ids:

                    for lrq in learner.learner_qualification_ids:

                        if lrq == lrq_object:
                            continue

                        # try find a healthy replacement
                        if (
                            lrq_object.learner_qualification_parent_id == lrq.learner_qualification_parent_id
                            and lrq.assessors_id
                            and lrq.moderators_id
                            and lrq.batch_id
                            and lrq.start_date
                            and lrq.end_date
                            and lrq.certificate_no
                        ):

                            lrqs_deleted.append({
                                'nlrd29': nlrd29,
                                'status': "clean replace",
                                'replacer': lrq,
                                'record_data': lrq_object.id
                            })
                            break

            # ---- CASE 2: No ID or alternate ID ----
            if "no id or alt id" in (nlrd29.stat_msg or "") or \
               "no learner regsitration attached" in (nlrd29.stat_msg or ""):

                if lrq_object.certificate_no:

                    matches = self.env['learner.registration.qualification'].search([
                        ('certificate_no', '=', lrq_object.certificate_no),
                        ('id', '!=', lrq_object.id)
                    ])

                    if matches:
                        lrqs_deleted.append({
                            'nlrd29': nlrd29,
                            'status': "straight delete on matched cert num",
                            'replacer': matches[0],
                            'record_data': lrq_object.id
                        })
                        continue

                # ---- Match by batch ----
                if lrq_object.batch_id:

                    non_draft = self.env['provider.assessment'].search([
                        ('batch_id', '=', lrq_object.batch_id.id),
                        ('state', '!=', 'draft')
                    ])

                    if not non_draft:
                        lrqs_deleted.append({
                            'nlrd29': nlrd29,
                            'status': "straight delete, no non-draft assessment",
                            'replacer': "N/A",
                            'record_data': lrq_object.id
                        })

        # ---- PROCESS DELETIONS ----
        _logger.info("LRQ delete candidates: %s", lrqs_deleted)

        for item in lrqs_deleted:

            nlrd29 = item['nlrd29']
            lrq = nlrd29.lrq_id

            values = {
                'name': f"LRQ Fix - {nlrd29.id}",
                'nlrd_29_id': nlrd29.id,
                'doc_id': nlrd29.id,
                'doc_model': 'nlrd.29',
                'message': str(item)
            }

            self.env['nlrd.report'].create(values)

            # Safety check before unlink
            if lrq and lrq.exists():
                lrq.unlink()

        return True

    # ----------------------------------------------

    @api.model
    def fix_person(self):

        fixed_people = []

        unknown_lang = self.env['res.lang'].search([('name', '=', 'Unknown')], limit=1)

        broken_records = self.env['nlrd.25'].search([('broken', '=', True)])

        for nlrd25 in broken_records:

            person = nlrd25.person_id
            msg = ""

            if not person:
                continue

            stat_msg = nlrd25.stat_msg or ""

            # ---- AGE FIX ----
            if "Person age is less than 15 years" in stat_msg:

                try:
                    dob = datetime.strptime(person.person_birth_date, '%Y-%m-%d')
                    now = datetime.today()

                    if (now - dob) >= relativedelta(years=15):
                        new_date = now - relativedelta(years=15)
                    else:
                        new_date = dob

                    person.write({
                        'person_birth_date': new_date.strftime('%Y-%m-%d')
                    })

                    msg += "Setting dob to 15 years behind today. "

                except Exception as e:
                    msg += f"Failed to fix DOB: {str(e)} "

            # ---- MISSING DOB ----
            if "learner has no person_birth_date" in stat_msg:
                msg += "learner has no person_birth_date. "

            # ---- EQUITY FIX ----
            if "learner has no equity" in stat_msg:
                person.write({'equity': 'unknown'})
                msg += "Blanket set equity to unknown. "

            # ---- HOME LANGUAGE FIX ----
            if "learner has no home_language_code" in stat_msg:
                person.write({'home_language_code': unknown_lang.id})
                msg += "Set home language to Unknown. "

            # ---- PROVINCE FIX (LEARNER) ----
            if "learner has no person_home_province_code" in stat_msg:
                msg += self._fix_province(person)

            # ---- PROVINCE FIX (ASSESSOR) ----
            if "assessor has no person_home_province_code" in stat_msg:
                msg += self._fix_province(person)

            # ---- COUNTRY FIX ----
            if "assessor has no country" in stat_msg or "learner has no country" in stat_msg:
                country, mesg = country_check(person)
                if country:
                    person.write({'country_id': country.id})
                msg += mesg

            # ---- ASSESSOR EQUITY ----
            if "assessor has no equity" in stat_msg:
                person.write({'equity': 'unknown'})
                msg += "Blanket set assessor equity to unknown. "

            # ---- SOCIO ECONOMIC STATUS ----
            if "assessor has no socio_economic_status" in stat_msg:
                person.write({'socio_economic_status': 'Unspecified'})
                msg += "Blanket set socio economic status as Unspecified. "

            # ---- DISABILITY STATUS ----
            if "assessor has no disability_status" in stat_msg:
                person.write({'disability_status': 'none'})
                msg += "Blanket set disability status as none. "

            fixed_people.append({
                'nlrd25': nlrd25,
                'message': msg
            })

        # ---- CREATE FIX REPORT ----
        for fix in fixed_people:

            nlrd25 = fix['nlrd25']
            message = fix['message'] or nlrd25.stat_msg

            values = {
                'name': f"Person Fix - {nlrd25.id}",
                'nlrd_25_id': nlrd25.id,
                'doc_id': nlrd25.id,
                'doc_model': 'nlrd.25',
                'message': message
            }

            self.env['nlrd.report'].create(values)

        return True


    # ---- Helper Function ----
    def _fix_province(self, person):

        msg = "Fixing province: "
        province = False

        search_fields = [
            person.person_home_zip,
            person.work_zip,
            person.person_postal_zip
        ]

        for zip_code in search_fields:
            if zip_code:
                suburb = self.env['res.suburb'].search([
                    ('postal_code', '=', zip_code)
                ], limit=1)

                if suburb:
                    province = suburb.province_id
                    msg += f"Set based on zip {zip_code}. "
                    break

        if not province:
            msg += "Could not determine province. "

        else:
            person.write({
                'person_home_province_code': province.id
            })

        return msg

    # ----------------------------------------------

    @api.model
    def fix_provider(self):

        fixed_providers = []

        broken_providers = self.env['nlrd.21'].search([('broken', '=', True)])

        for nlrd21 in broken_providers:

            provider = nlrd21.provider_id
            msg = ""

            if not provider:
                continue

            stat_msg = nlrd21.stat_msg or ""

            # ---- FIX DATE GAP ----
            if "provider date gap bigger than 5 years" in stat_msg:

                try:
                    start = datetime.strptime(provider.provider_start_date, '%Y-%m-%d')
                    end = datetime.strptime(provider.provider_end_date, '%Y-%m-%d')

                    diff = end - start

                    if diff >= relativedelta(years=5):
                        new_date = end - relativedelta(years=5)
                    else:
                        new_date = start

                    provider.write({
                        'provider_start_date': new_date.strftime('%Y-%m-%d')
                    })

                    msg += f"Setting provider start date to {new_date}. "

                except Exception as e:
                    msg += f"Failed to fix provider date: {str(e)}. "

            # ---- FIX CLASS ID ----
            if "no provider provider_class_id" in stat_msg:

                if not provider.provider_class_Id:

                    # Try to find "Unknown" class record
                    class_rec = self.env['provider.class'].search(
                        [('name', '=', 'Unknown')], limit=1
                    )

                    if class_rec:
                        provider.write({
                            'provider_class_Id': class_rec.id
                        })
                        msg += "Setting class id to Unknown. "
                    else:
                        msg += "Could not find class 'Unknown'. "

            # ---- FIX TYPE ID ----
            if "no provider type id" in stat_msg:

                if not provider.provider_type_id:

                    type_rec = self.env['provider.type'].search(
                        [('name', '=', 'Education and Training')], limit=1
                    )

                    if type_rec:
                        provider.write({
                            'provider_type_id': type_rec.id
                        })
                        msg += "Setting type id to Education and Training. "
                    else:
                        msg += "Could not find type 'Education and Training'. "

            fixed_providers.append({
                'nlrd21': nlrd21,
                'message': msg
            })

        # ---- CREATE REPORT RECORDS ----
        for fix in fixed_providers:

            nlrd21 = fix['nlrd21']
            message = fix['message'] or nlrd21.stat_msg

            values = {
                'name': f"Provider Fix - {nlrd21.id}",
                'nlrd_21_id': nlrd21.id,
                'doc_id': nlrd21.id,
                'doc_model': 'nlrd.21',
                'message': message
            }

            self.env['nlrd.report'].create(values)

        return True

    # ----------------------------------------------

    @api.model
    def purge_dupe_amr(self):

        deleted_reports = []

        assessors = self.env['hr.employee'].search([('is_assessors', '=', True)])

        for assessor in assessors:

            seen_quals = set()

            for amr in assessor.qualification_ids:

                qual_id = amr.saqa_qual_id

                if qual_id in seen_quals:

                    _logger.info("Deleting duplicate AMR %s for assessor %s", amr.id, assessor.name)

                    deleted_reports.append({
                        'assessor': assessor,
                        'amr': amr
                    })

                    amr.unlink()

                else:
                    seen_quals.add(qual_id)

        # Create report records
        for record in deleted_reports:

            assessor = record['assessor']
            amr = record['amr']

            message = f"Duplicate AMR removed for Assessor {assessor.name} (AMR ID: {amr.id})"

            self.env['nlrd.report'].create({
                'name': f"AMR Purge - Assessor {assessor.name}",
                'doc_id': assessor.id,
                'doc_model': 'amr',
                'message': message
            })

        return True
    # ----------------------------------------------

    def do_all_admin(self):
        self.purge_dupe_amr()
        self.fix_lrq()
        self.fix_assessor_qual()
        self.fix_assessor()
        self.fix_provider()
        self.fix_person()

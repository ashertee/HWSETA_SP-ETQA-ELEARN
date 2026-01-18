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

    def fix_lrq(self):
        for rec in self.env['nlrd.29'].search([('broken','=',True)]):
            msg = rec.stat_msg or ''
            self.env['nlrd.report'].create({
                'name': msg,
                'nlrd_29_id': rec.id,
                'doc_id': rec.id,
                'doc_model': 'nlrd.29',
                'message': msg
            })
            if rec.lrq_id:
                rec.lrq_id.unlink()

    # ----------------------------------------------

    def fix_person(self):
        unknown_lang = self.env['res.lang'].search([('name','=','Unknown')], limit=1)

        for rec in self.env['nlrd.25'].search([('broken','=',True)]):
            person = rec.person_id
            msg = ""

            if "no equity" in rec.stat_msg:
                person.equity = "unknown"
                msg += "equity fixed "

            if "no home_language_code" in rec.stat_msg:
                person.home_language_code = unknown_lang
                msg += "language fixed "

            if "no country" in rec.stat_msg:
                country, _ = country_check(person)
                person.country_id = country

            self.env['nlrd.report'].create({
                'name': msg,
                'nlrd_25_id': rec.id,
                'doc_id': rec.id,
                'doc_model': 'nlrd.25',
                'message': msg
            })

    # ----------------------------------------------

    def fix_provider(self):
        for rec in self.env['nlrd.21'].search([('broken','=',True)]):
            provider = rec.provider_id
            msg = ""

            if "provider date gap" in rec.stat_msg:
                start = dt.datetime.strptime(provider.provider_start_date, '%Y-%m-%d')
                end = dt.datetime.strptime(provider.provider_end_date, '%Y-%m-%d')
                if end - start > relativedelta(years=5):
                    provider.provider_start_date = (end - relativedelta(years=5)).strftime('%Y-%m-%d')
                msg += "provider date fixed "

            self.env['nlrd.report'].create({
                'name': msg,
                'nlrd_21_id': rec.id,
                'doc_id': rec.id,
                'doc_model': 'nlrd.21',
                'message': msg
            })

    # ----------------------------------------------

    def purge_dupe_amr(self):
        for emp in self.env['hr.employee'].search([('is_assessors','=',True)]):
            seen = []
            for amr in emp.qualification_ids:
                if amr.saqa_qual_id in seen:
                    amr.unlink()
                else:
                    seen.append(amr.saqa_qual_id)

    # ----------------------------------------------

    def do_all_admin(self):
        self.purge_dupe_amr()
        self.fix_lrq()
        self.fix_assessor_qual()
        self.fix_assessor()
        self.fix_provider()
        self.fix_person()

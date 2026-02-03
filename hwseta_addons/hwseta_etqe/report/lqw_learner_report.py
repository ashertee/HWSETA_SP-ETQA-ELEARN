import logging
from odoo import api, models


_logger = logging.getLogger(__name__)


class LearnerAchievementCertificateReportView(models.AbstractModel):
    # The name must follow the pattern: report.module_name.template_id
    _name = 'report.hwseta_etqe.lqw_report_achievement_certificate'
    _description = 'Learner Achievement Certificate Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        In Odoo 18, this method acts as the bridge between the database 
        and the QWeb template.
        """
        # Fetch the records (docs) being printed
        docs = self.env['learner.assessment.achieved.line'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'learner.assessment.achieved.line',
            'docs': docs,
            # Helper functions to be used in the XML template
            'get_qualification': self._get_qualification,
            'get_unit_standard': self._get_unit_standard,
            'get_status': self._get_status,
            'get_saqa_qual_id': self._get_saqa_qual_id,
            'get_certificate_no': self._get_certificate_no,
            'get_qual_nqf_level': self._get_qual_nqf_level,
            'get_qual_credits_value': self._get_qual_credits_value,
        }

    def _get_qualification(self, achieved_record):
        # achieved_record is now a recordset, no need for manual SQL
        names = achieved_record.qualification_ids.mapped('name')
        return ', '.join(names) if names else ''

    def _get_saqa_qual_id(self, achieved_record):
        saq-ids = achieved_record.qualification_ids.mapped('saqa_qual_id')
        return ', '.join(map(str, saq-ids)) if saq-ids else ''

    def _get_qual_nqf_level(self, achieved_record):
        levels = achieved_record.qualification_ids.mapped('n_level')
        return ', '.join(map(str, levels)) if levels else ''

    def _get_qual_credits_value(self, achieved_record):
        credits = achieved_record.qualification_ids.mapped('m_credits')
        return ', '.join(map(str, credits)) if credits else ''

    def _get_unit_standard(self, achieved_record):
        """
        Refactored logic for unit standards grouping and calculation
        """
        res = []
        # Assuming qualification_line_ids is the O2M/M2M field on your model
        lines = achieved_record.qualification_line_ids
        
        # Get unique types
        u_types = list(set(lines.mapped('type')))
        total_nqf_sum = sum(float(l.level2 or 0) for l in lines)
        
        if total_nqf_sum == 0:
            total_nqf_sum = 1

        for u_type in u_types:
            type_lines = lines.filtered(lambda l: l.type == u_type)
            val_lst = []
            type_credits = 0
            type_nqf = 0
            
            for line in type_lines:
                val_lst.append({
                    'name': line.title,
                    'credit': line.level3,
                    'nqf_level': line.level2,
                    'nlrd_number': line.id_no,
                })
                type_nqf += float(line.level2 or 0)
                type_credits += float(line.level3 or 0)

            res.append({
                'type': u_type,
                'value': val_lst[::-1], # Keep your original reverse logic
                't_credits': type_credits,
                'percentage': (type_nqf * 100) / total_nqf_sum,
                'counter': len(u_types)
            })
            
        return sorted(res, key=lambda k: k['type'])

    def _get_status(self, achieved_record):
        # Ported logic to check learner status
        match = achieved_record.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id == achieved_record.qual_learner_assessment_achieved_line_id
        )
        return {'achieve': match[:1].is_learner_achieved or False}


    def _get_certificate_no(self, achieved_record):
        match = achieved_record.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id == achieved_record.qual_learner_assessment_achieved_line_id
        )
        return {'certificate_no': match[:1].certificate_no or False}

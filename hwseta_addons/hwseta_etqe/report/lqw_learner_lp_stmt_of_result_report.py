import logging
from odoo import models, api


_logger = logging.getLogger(__name__)


class LpStatementOfResultReportView(models.AbstractModel):
    # This name MUST match: report.[module_name].[template_id]
    # In your case: report.hwseta_etqe.lqw_report_learning_programme_statement_of_result
    _name = 'report.hwseta_etqe.lqw_report_learning_programme_statement_of_result'
    _description = 'Learning Programme Statement of Result Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Main entry point for Odoo 18 reports.
        Replaces the old localcontext.update logic.
        """
        docs = self.env['learner.assessment.achieved.line'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'learner.assessment.achieved.line',
            'docs': docs,
            # Mapping helper methods for the QWeb template
            'get_lp': self._get_lp,
            'get_unit_standard': self._get_unit_standard,
            'get_status': self._get_status,
            'get_saqa_qual_id': self._get_saqa_qual_id,
            'get_certificate_no': self._get_certificate_no,
            'get_lp_nqf_level': self._get_lp_nqf_level,
            'get_lp_credits_value': self._get_lp_credits_value,
            'get_lp_saqa_qual_id': self._get_lp_saqa_qual_id,
        }

    def _get_lp(self, achieved_id):
        _logger.info("get_lp")
        return ','.join(achieved_id.learning_programme_ids.mapped('name'))

    def _get_saqa_qual_id(self, achieved_id):
        _logger.info("get_saqa_qual_id")
        return ','.join(achieved_id.learning_programme_ids.mapped('code'))

    def _get_lp_saqa_qual_id(self, achieved_id):
        _logger.info("get_lp_saqa_qual_id")
        lp_recs = achieved_id.learning_programme_ids
        qual_details = []
        
        if lp_recs:
            lp = lp_recs[0]  # Get first record as per legacy logic
            # Search for provider qualification based on SAQA ID
            qual = self.env['provider.qualification'].search([
                ('saqa_qual_id', '=', str(lp.saqa_qual_id))
            ], limit=1)
            
            if qual:
                qual_details.append({
                    'value': [{
                        'saqa_qual_id': qual.saqa_qual_id,
                        'name': qual.name,
                        'lp_id': lp.code,
                        'n_level': qual.n_level,
                        'm_credits': qual.m_credits,
                    }]
                })
        return qual_details

    def _get_lp_nqf_level(self, achieved_id):
        return ','.join(achieved_id.learning_programme_ids.mapped('n_level'))

    def _get_lp_credits_value(self, achieved_id):
        return ','.join([str(val) for val in achieved_id.learning_programme_ids.mapped('total_credit')])

    def _get_unit_standard(self, achieved_id):
        """
        Retrieves and groups Unit Standards. 
        Note: Ensure 'selection' and 'learning_programme_id' are actual field names.
        """
        _logger.info("get_unit_standard")
        
        # Filter related unit standards where selection is true
        us_lines = self.env['learning.programme.unit.standards.learner.rel'].search([
            ('learning_programme_id', '=', achieved_id.id),
            ('selection', '=', True)
        ])
        
        # Get unique types and prepare grouping
        unit_standard_list = []
        types = sorted(list(set(us_lines.mapped('type'))))
        
        # Fetch actual standard records from master table
        etqe_standards = self.env['etqe.learning.programme.unit.standards'].search([
            ('id_no', 'in', us_lines.mapped('id_no')),
            ('type', 'in', types)
        ])

        total_global_nfq = sum(int(s.level2 or 0) for s in etqe_standards) or 1

        for u_type in types:
            type_lines = etqe_standards.filtered(lambda x: x.type == u_type)
            if not type_lines:
                continue

            val_lst = [{
                'name': s.title,
                'credit': s.level3,
                'nqf_level': s.level2,
                'saqa_us_id': s.id_no,
            } for s in type_lines]

            type_nfq = sum(int(s.level2 or 0) for s in type_lines)
            
            unit_standard_list.append({
                'type_key': type_lines[0].type_key,
                'type': u_type,
                'value': val_lst[::-1],
                't_credits': sum(int(s.level3 or 0) for s in type_lines),
                'percentage': (type_nfq * 100) / total_global_nfq,
                'counter': len(types)
            })

        return sorted(unit_standard_list, key=lambda k: k['type_key'])

    def _get_status(self, achieved_id):
        # Filtering learner registration lines to find matching LP achievement
        match = achieved_id.learner_id.learning_programme_ids.filtered(
            lambda s: s.learning_programme_id.id == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {'achieve': match[:1].is_learner_achieved or False}

    def _get_certificate_no(self, achieved_id):
        match = achieved_id.learner_id.learning_programme_ids.filtered(
            lambda s: s.learning_programme_id.id == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {'certificate_no': match[:1].certificate_no or False}

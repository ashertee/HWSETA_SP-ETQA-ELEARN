import logging
from odoo import models, api


_logger = logging.getLogger(__name__)


class LearnerQualificationSorReportView(models.AbstractModel):
    # This name must match: report.[module_name].[template_id]
    _name = 'report.hwseta_etqe.lqw_qualification_stmt_of_result_report'
    _description = 'Qualification Statement of Result Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        In Odoo 18, this method replaces the old 'wrapped_report_class'.
        It prepares the data dictionary for the QWeb template.
        """
        # Fetch the records being printed
        docs = self.env['learner.assessment.achieved.line'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'learner.assessment.achieved.line',
            'docs': docs,
            # Map helper methods from your logic class here:
            'get_qualification': self._get_qualification,
            'get_unit_standard': self._get_unit_standard,
            'get_status': self._get_status,
            'get_saqa_qual_id': self._get_saqa_qual_id,
            'get_certificate_no': self._get_certificate_no,
            'get_qual_nqf_level': self._get_qual_nqf_level,
            'get_qual_credits_value': self._get_qual_credits_value,
        }

    def _get_qualification(self, achieved_id):
        # Accessing many-to-many or related fields via ORM
        return ', '.join(achieved_id.learner_qualification_parent_ids.mapped('name'))

    def _get_saqa_qual_id(self, achieved_id):
        return ', '.join(achieved_id.learner_qualification_parent_ids.mapped('saqa_qual_id'))

    def _get_qual_nqf_level(self, achieved_id):
        return ', '.join([str(val) for val in achieved_id.learner_qualification_parent_ids.mapped('n_level')])

    def _get_qual_credits_value(self, achieved_id):
        return ', '.join([str(val) for val in achieved_id.learner_qualification_parent_ids.mapped('m_credits')])

    def _get_unit_standard(self, achieved_id):
        """
        Refactored grouping logic using Odoo 18 ORM search and filtered.
        """
        # Find related registration lines that are selected
        reg_lines = self.env['learner.registration.qualification.line'].search([
            ('learner_reg_id', '=', achieved_id.id),
            ('selection', '=', True)
        ])

        # Get corresponding provider lines efficiently
        # id_data is used as the link to provider.qualification.line id_no
        provider_line_model = self.env['provider.qualification.line']
        provider_lines = provider_line_model.browse()

        unit_standard_type = []
        for reg in reg_lines:
            match = provider_line_model.search([
                ('id_no', '=', reg.id_data),
                ('type', '=', reg.type)
            ], limit=1)
            if match:
                provider_lines |= match
                unit_standard_type.append(reg.type)

        results = []
        unique_types = list(set(unit_standard_type))
        total_global_nfq = sum(int(line.level2 or 0) for line in provider_lines) or 1

        for u_type in unique_types:
            type_lines = provider_lines.filtered(lambda x: x.type == u_type)

            val_lst = []
            type_nfq_sum = 0
            type_credit_sum = 0

            for line in type_lines:
                val_lst.append({
                    'name': line.title,
                    'credit': line.level3,
                    'nqf_level': line.level2,
                    'nlrd_number': int(line.id_no or 0),
                })
                type_nfq_sum += int(line.level2 or 0)
                type_credit_sum += int(line.level3 or 0)

            # Sort by NLRD Number as per legacy logic
            val_lst = sorted(val_lst, key=lambda k: k['nlrd_number'], reverse=True)

            results.append({
                'type_key': type_lines[0].type_key if type_lines else 0,
                'type': u_type,
                'value': val_lst[::-1], # Keep legacy reverse logic
                't_credits': type_credit_sum,
                'percentage': (type_nfq_sum * 100) / total_global_nfq,
                'counter': len(unique_types)
            })

        return sorted(results, key=lambda k: k['type_key'])

    def _get_status(self, achieved_id):
        # Filtering records via ORM instead of manual loops
        match = achieved_id.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id.id == achieved_id.qual_learner_assessment_achieved_line_id.id
        )
        return {'achieve': match[:1].is_learner_achieved or False}

    def _get_certificate_no(self, achieved_id):
        match = achieved_id.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id.id == achieved_id.qual_learner_assessment_achieved_line_id.id
        )
        return {'certificate_no': match[:1].certificate_no or False}

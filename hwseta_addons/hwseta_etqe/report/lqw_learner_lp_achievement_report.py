from odoo import models, api


class LpCertificateReportView(models.AbstractModel):
    # This name must match: report.[module_name].[template_id]
    # It links the Python logic directly to your QWeb XML template.
    _name = 'report.hwseta_etqe.lqw_report_learning_programme_achievement_certificate'
    _description = 'Learning Programme Achievement Certificate Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Provides data and helper functions to the QWeb template.
        """
        # Load the records being printed
        docs = self.env['learner.assessment.achieved.line'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'learner.assessment.achieved.line',
            'docs': docs,
            # Map the helper methods from your logic class here
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
        # Uses ORM mapped() to join learning programme names
        return ','.join(achieved_id.learning_programme_ids.mapped('name'))

    def _get_saqa_qual_id(self, achieved_id):
        # Maps the 'code' field as per legacy logic
        return ','.join(achieved_id.learning_programme_ids.mapped('code'))

    def _get_lp_saqa_qual_id(self, achieved_id):
        """Retrieves Provider Qualification details based on LP's SAQA ID"""
        qual_details = []
        lp_saq-ids = achieved_id.learning_programme_ids.mapped('saqa_qual_id')

        if lp_saq-ids:
            saq-id = lp_saq-ids[0]
            qual = self.env['provider.qualification'].search([
                ('saqa_qual_id', '=', str(saq-id))
            ], limit=1)

            if qual:
                qual_details.append({
                    'value': [{
                        'saqa_qual_id': qual.saqa_qual_id,
                        'name': qual.name,
                        'n_level': qual.n_level,
                        'm_credits': qual.m_credits,
                    }]
                })
        return qual_details

    def _get_lp_nqf_level(self, achieved_id):
        return ','.join(achieved_id.learning_programme_ids.mapped('seta_branch_id.name'))

    def _get_lp_credits_value(self, achieved_id):
        return ','.join([str(c) for c in achieved_id.learning_programme_ids.mapped('total_credit')])

    def _get_unit_standard(self, achieved_id):
        """Groups Unit Standards by type and calculates NFQ percentages"""
        lines = achieved_id.lp_unit_standard_line_ids
        unit_standard_data = []

        types = sorted(list(set(lines.mapped('type'))))
        total_nfq_level = sum(int(l.level2 or 0) for l in lines) or 1

        for u_type in types:
            type_lines = lines.filtered(lambda l: l.type == u_type)
            val_lst = [{
                'name': l.title,
                'credit': l.level3,
                'nqf_level': l.level2,
                'saqa_us_id': l.id_no,
            } for l in type_lines]

            type_nfq = sum(int(l.level2 or 0) for l in type_lines)

            unit_standard_data.append({
                'type': u_type,
                'value': val_lst[::-1],
                't_credits': sum(int(l.level3 or 0) for l in type_lines),
                'percentage': (type_nfq * 100) / total_nfq_level,
                'counter': len(types)
            })
        return unit_standard_data

    def _get_status(self, achieved_id):
        """Finds matching achievement line for the learner"""
        match = achieved_id.learner_id.learning_programme_ids.filtered(
            lambda s: s.learning_programme_id.id == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {'achieve': match[:1].is_learner_achieved or False}

    def _get_certificate_no(self, achieved_id):
        match = achieved_id.learner_id.learning_programme_ids.filtered(
            lambda s: s.learning_programme_id.id == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {'certificate_no': match[:1].certificate_no or False}

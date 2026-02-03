from odoo import models, api, _

class ReportLpStatementOfResult(models.AbstractModel):
    # This must match: report.[module_name].[report_id_in_xml]
    _name = 'report.hwseta_etqe.report_learning_programme_statement_of_result'
    _description = 'Learning Programme Statement of Result Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Equivalent to the old localcontext.update.
        Everything returned here is directly accessible in the QWeb XML.
        """
        docs = self.env['provider.assessment'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'provider.assessment',
            'docs': docs,
            # Function mappings for the template
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
        # Uses ORM mapped() to get name from related Learning Programmes
        return ','.join(achieved_id.lp_assessment_ids.mapped('name'))

    def _get_saqa_qual_id(self, achieved_id):
        # Replaces raw SQL to fetch LP code
        return ','.join(achieved_id.lp_assessment_ids.mapped('code'))

    def _get_lp_saqa_qual_id(self, achieved_id):
        # Modern search for qualification details
        lps = achieved_id.lp_assessment_ids
        qual_details = []
        if lps:
            lp = lps[0] # Get first related LP
            qual = self.env['provider.qualification'].search([
                ('saqa_qual_id', '=', lp.saqa_qual_id)
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
        return ','.join(achieved_id.lp_assessment_ids.mapped('n_level'))

    def _get_lp_credits_value(self, achieved_id):
        return ','.join([str(c) for c in achieved_id.lp_assessment_ids.mapped('total_credit')])

    def _get_unit_standard(self, achieved_id):
        """Groups Unit Standards by type using modern logic"""
        lines = achieved_id.unit_standard_line_ids
        unit_standard = []
        
        # Determine unique types and total NFQ level for percentage calculation
        types = list(set(lines.mapped('type')))
        total_nfq_level = sum(int(l.level2 or 0) for l in lines) or 1
        
        for u_type in types:
            type_lines = lines.filtered(lambda l: l.type == u_type)
            # Replaces the old loop with ORM aggregation
            val_lst = [{
                'name': l.title,
                'credit': l.level3,
                'nqf_level': l.level2,
                'saqa_us_id': l.id_no,
            } for l in type_lines]

            unit_standard.append({
                'type_key': type_lines[0].type_key if type_lines else 0,
                'type': u_type,
                'value': val_lst[::-1],
                't_credits': sum(int(l.level3 or 0) for l in type_lines),
                'percentage': (sum(int(l.level2 or 0) for l in type_lines) * 100) / total_nfq_level,
                'counter': len(types)
            })
        return sorted(unit_standard, key=lambda k: k['type_key'])

    def _get_status(self, achieved_id):
        # Filtering records via ORM instead of nested Python loops
        match = achieved_id.learner_id.learning_programme_ids.filtered(
            lambda s: s.learning_programme_id.id == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {'achieve': match[:1].is_learner_achieved or False}

    def _get_certificate_no(self, achieved_id):
        match = achieved_id.learner_id.learning_programme_ids.filtered(
            lambda s: s.learning_programme_id.id == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {'certificate_no': match[:1].certificate_no or False}


class LpStatementOfResultReportView(models.AbstractModel):
    # The name must match: report.[module_name].[template_id]
    # This automatically links the Python logic to the QWeb XML template
    _name = 'report.hwseta_etqe.report_learning_programme_statement_of_result'
    _description = 'Learning Programme Statement of Result Report View'

    # You move the methods from the old 'learner_lp_statement_of_result' 
    # directly into this class and call them via _get_report_values.
    def _get_report_values(self, docids, data=None):
        docs = self.env['provider.assessment'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'provider.assessment',
            'docs': docs,
            # Map your helper functions here
            'get_lp': self._get_lp,
            'get_unit_standard': self._get_unit_standard,
            'get_status': self._get_status,
            'get_saqa_qual_id': self._get_saqa_qual_id,
            'get_certificate_no': self._get_certificate_no,
            'get_lp_nqf_level': self._get_lp_nqf_level,
            'get_lp_credits_value': self._get_lp_credits_value,
            'get_lp_saqa_qual_id': self._get_lp_saqa_qual_id,
        }

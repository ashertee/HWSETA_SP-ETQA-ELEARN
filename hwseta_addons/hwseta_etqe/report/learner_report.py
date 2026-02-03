from odoo import models, api


class ReportLearnerAchievementCertificate(models.AbstractModel):
    # The name must follow the pattern: report.[module_name].[report_id]
    _name = "report.hwseta_etqe.report_learner_achievement_certificate"
    _description = "Learner Achievement Certificate Report Logic"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        In Odoo 18, this method replaces the old localcontext and __init__.
        It prepares the data passed to the QWeb template.
        """
        docs = self.env["learner.assessment.achieved.line"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "learner.assessment.achieved.line",
            "docs": docs,
            # Function mappings for the template
            "get_qualification": self._get_qualification,
            "get_saqa_qual_id": self._get_saqa_qual_id,
            "get_qual_nqf_level": self._get_qual_nqf_level,
            "get_qual_credits_value": self._get_qual_credits_value,
            "get_unit_standard": self._get_unit_standard,
            "get_status": self._get_status,
            "get_certificate_no": self._get_certificate_no,
        }

    def _get_qualification(self, achieved_id):
        """Replaces SQL select with ORM mapped() for qualification names"""
        return ",".join(achieved_id.qualification_ids.mapped("name"))

    def _get_saqa_qual_id(self, achieved_id):
        return ",".join(achieved_id.qualification_ids.mapped("saqa_qual_id"))

    def _get_qual_nqf_level(self, achieved_id):
        return ",".join(achieved_id.qualification_ids.mapped("n_level"))

    def _get_qual_credits_value(self, achieved_id):
        return ",".join(
            [str(c) for c in achieved_id.qualification_ids.mapped("m_credits")]
        )

    def _get_unit_standard(self, achieved_id):
        """Groups unit standards by type using Odoo 18 ORM filtered()"""
        lines = achieved_id.unit_standard_line_ids
        unit_standard_data = []

        # Get unique types and total NFQ sum for percentage calculation
        types = list(set(lines.mapped("type")))
        total_nfq_sum = sum(int(l.level2 or 0) for l in lines) or 1

        for u_type in types:
            type_lines = lines.filtered(lambda l: l.type == u_type)
            val_lst = [
                {
                    "name": l.title,
                    "credit": l.level3,
                    "nqf_level": l.level2,
                    "nlrd_number": l.id_no,
                }
                for l in type_lines
            ]

            type_credits = sum(int(l.level3 or 0) for l in type_lines)
            type_nfq = sum(int(l.level2 or 0) for l in type_lines)

            unit_standard_data.append(
                {
                    "type": u_type,
                    "value": val_lst[::-1],
                    "t_credits": type_credits,
                    "percentage": (type_nfq * 100) / total_nfq_sum,
                    "counter": len(types),
                }
            )
        return sorted(unit_standard_data, key=lambda k: k["type"])

    def _get_status(self, achieved_id):
        """Replaces nested loops with ORM filtering"""
        match = achieved_id.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id.id
            == achieved_id.qual_learner_assessment_achieved_line_id.id
        )
        return {"achieve": match[:1].is_learner_achieved or False}

    def _get_certificate_no(self, achieved_id):
        match = achieved_id.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id.id
            == achieved_id.qual_learner_assessment_achieved_line_id.id
        )
        return {"certificate_no": match[:1].certificate_no or False}


class AchievementCertificateReportView(models.AbstractModel):
    # The name must match: report.[module_name].[template_id]
    # This automatically connects the logic to your QWeb XML template
    _name = "report.hwseta_etqe.report_achievement_certificate"
    _description = "Learner Achievement Certificate Report View"

    def _get_report_values(self, docids, data=None):
        """
        Main method to provide data to the QWeb template.
        """
        docs = self.env["learner.assessment.achieved.line"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "learner.assessment.achieved.line",
            "docs": docs,
            # Pass your helper methods here so they are callable in the template
            "get_qualification": self._get_qualification,
            "get_unit_standard": self._get_unit_standard,
            "get_status": self._get_status,
            "get_saqa_qual_id": self._get_saqa_qual_id,
            "get_certificate_no": self._get_certificate_no,
            "get_qual_nqf_level": self._get_qual_nqf_level,
            "get_qual_credits_value": self._get_qual_credits_value,
        }

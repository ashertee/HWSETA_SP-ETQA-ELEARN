from odoo import models, api


class QualificationSorReportView(models.AbstractModel):
    _name = "report.hwseta_etqe.qualification_stmt_of_result_report"
    _description = "Learner Qualification Statement of Result Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Main entry point for QWeb reports.
        The 'docs' and helper methods are passed here to the template.
        """
        docs = self.env["learner.assessment.achieved.line"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "learner.assessment.achieved.line",
            "docs": docs,
            "get_qualification": self._get_qualification,
            "get_saqa_qual_id": self._get_saqa_qual_id,
            "get_qual_nqf_level": self._get_qual_nqf_level,
            "get_qual_credits_value": self._get_qual_credits_value,
            "get_unit_standard": self._get_unit_standard,
            "get_status": self._get_status,
            "get_certificate_no": self._get_certificate_no,
        }

    def _get_qualification(self, achieved_id):
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
        lines = achieved_id.unit_standard_line_ids
        unit_standard_data = []
        types = sorted(list(set(lines.mapped("type"))))
        total_nfq_sum = sum(int(l.level2 or 0) for l in lines) or 1

        for u_type in types:
            type_lines = lines.filtered(lambda l: l.type == u_type)
            val_lst = []
            type_credits = 0
            type_nfq = 0
            for line in type_lines:
                val_lst.append(
                    {
                        "name": line.title,
                        "credit": line.level3,
                        "nqf_level": line.level2,
                        "nlrd_number": int(line.id_no or 0),
                    }
                )
                type_credits += int(line.level3 or 0)
                type_nfq += int(line.level2 or 0)

            unit_standard_data.append(
                {
                    "type_key": type_lines[0].type_key if type_lines else 0,
                    "type": u_type,
                    "value": sorted(val_lst, key=lambda k: k["nlrd_number"]),
                    "t_credits": type_credits,
                    "percentage": (type_nfq * 100) / total_nfq_sum,
                    "counter": len(types),
                }
            )
        return sorted(unit_standard_data, key=lambda k: k["type_key"])

    def _get_status(self, achieved_id):
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

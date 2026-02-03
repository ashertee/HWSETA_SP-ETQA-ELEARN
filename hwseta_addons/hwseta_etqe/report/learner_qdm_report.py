from odoo import models, api, _


class QualificationSorReportView(models.AbstractModel):
    _name = "report.hwseta_etqe.qualification_stmt_of_result_report"
    _description = "Learner Qualification Statement of Result Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Equivalent to old localcontext.update.
        Everything returned here is accessible in the QWeb XML template.
        """
        docs = self.env["learner.assessment.achieved.line"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "learner.assessment.achieved.line",
            "docs": docs,
            # Helper functions
            "get_qualification": self._get_qualification,
            "get_saqa_qual_id": self._get_saqa_qual_id,
            "get_unit_standard": self._get_unit_standard,
            "get_status": self._get_status,
            "get_name": self._get_name,
            "get_certificate_no": self._get_certificate_no,
            "get_qual_nqf_level": self._get_qual_nqf_level,
            "get_qual_credits_value": self._get_qual_credits_value,
        }

    def _get_qualification(self, achieved_id):
        # Uses ORM mapped() to replace SQL select on M2M relation
        return ", ".join(achieved_id.qualification_ids.mapped("name"))

    def _get_saqa_qual_id(self, achieved_id):
        return ", ".join(achieved_id.qualification_ids.mapped("saqa_qual_id"))

    def _get_unit_standard(self, achieved_id):
        """Groups Unit Standards by type using modern ORM and Python logic"""
        # Dynamically fetch unit standards related to the achieved_id
        lines = achieved_id.unit_standard_line_ids or self.env["provider.qualification.line"]

        unit_standard = []
        types = sorted(list(set(lines.mapped("type"))))

        # Calculate total credits for percentage calculation if needed, otherwise use a default
        total_all_credits = sum(float(l.level3 or 0) for l in lines) or 1

        for u_type in types:
            type_lines = lines.filtered(lambda l: l.type == u_type)
            val_lst = [
                {
                    "name": l.title,
                    "credit": l.level3,
                    "nqf_level": l.level2,
                    "nlrd_number": l.level1,
                }
                for l in type_lines
            ]

            total_credits_for_type = sum(float(l.level3 or 0) for l in type_lines)

            unit_standard.append(
                {
                    "type": u_type,
                    "value": val_lst[::-1],
                    "t_credits": total_credits_for_type,
                    "percentage": round((total_credits_for_type * 100) / total_all_credits, 1),
                    "counter": len(types),
                }
            )
        return sorted(unit_standard, key=lambda k: k["type"])

    def _get_status(self, achieved_id):
        """ORM logic for learner achievement status"""
        # achieved_id is a single record in QWeb context
        match = achieved_id.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id.id
            == achieved_id.qual_learner_assessment_achieved_line_id.id
        )
        return {"achieve": match[:1].is_learner_achieved or False}

    def _get_name(self, achieved_id):
        """Replaces multiple SQL queries with a single ORM call to hr.employee"""
        employee = achieved_id.learner_id
        if not employee:
            return ""

        parts = [
            (employee.name or "").title(),
            (employee.person_middle_name or "").title(),
            (employee.person_last_name or "").title(),
        ]
        # Filter out empty strings and join
        return " ".join([p for p in parts if p])

    def _get_certificate_no(self, achieved_id):
        match = achieved_id.learner_id.learner_qualification_ids.filtered(
            lambda q: q.learner_qualification_parent_id.id
            == achieved_id.qual_learner_assessment_achieved_line_id.id
        )
        return {"certificate_no": match[:1].certificate_no or False}

    def _get_qual_nqf_level(self, achieved_id):
        return ", ".join(achieved_id.qualification_ids.mapped("n_level"))

    def _get_qual_credits_value(self, achieved_id):
        return ", ".join(
            [str(c) for c in achieved_id.qualification_ids.mapped("m_credits")]
        )

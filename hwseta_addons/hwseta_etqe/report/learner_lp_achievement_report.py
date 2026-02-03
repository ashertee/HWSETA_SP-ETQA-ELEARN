from odoo import models, api, _


class LpCertificateReportView(models.AbstractModel):
    # This name must EXACTLY match: report.[module_name].[template_id]
    # In your case, it links the logic to the XML template with id 'report_learning_programme_achievement_certificate'
    _name = "report.hwseta_etqe.report_learning_programme_achievement_certificate"
    _description = "Learning Programme Achievement Certificate Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Replaces __init__ and localcontext.update.
        Everything returned in this dictionary is accessible in the QWeb XML.
        """
        docs = self.env["provider.assessment"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "provider.assessment",
            "docs": docs,
            # Functions
            "get_lp": self._get_lp,
            "get_unit_standard": self._get_unit_standard,
            "get_status": self._get_status,
            "get_saqa_qual_id": self._get_saqa_qual_id,
            "get_certificate_no": self._get_certificate_no,
            "get_lp_nqf_level": self._get_lp_nqf_level,
            "get_lp_credits_value": self._get_lp_credits_value,
            "get_lp_saqa_qual_id": self._get_lp_saqa_qual_id,
        }

    def _get_lp(self, achieved_id):
        """Replaces SQL query with ORM mapped()"""
        # Assuming lp_assessment_ids is the many2many relation field
        return ", ".join(achieved_id.lp_assessment_ids.mapped("name"))

    def _get_saqa_qual_id(self, achieved_id):
        return ", ".join(achieved_id.lp_assessment_ids.mapped("code"))

    def _get_lp_saqa_qual_id(self, achieved_id):
        """Replaces raw SQL for qualification details"""
        lp_saqa_qual_ids = achieved_id.lp_assessment_ids.mapped("saqa_qual_id")
        qual_details = []
        if lp_saqa_qual_ids:
            # Modern search instead of raw select
            qual = self.env["provider.qualification"].search(
                [("saqa_qual_id", "=", str(lp_saqa_qual_ids[0]))], limit=1
            )
            if qual:
                qual_details.append(
                    {
                        "value": [
                            {
                                "saqa_qual_id": qual.saqa_qual_id,
                                "name": qual.name,
                                "n_level": qual.n_level,
                                "m_credits": qual.m_credits,
                            }
                        ]
                    }
                )
        return qual_details

    def _get_unit_standard(self, achieved_id):
        """Groups Unit Standards by type using modern logic"""
        # Assuming unit_assessment_line_ids is your relation field
        lines = achieved_id.unit_assessment_line_ids
        unit_standard = []

        # Get unique types
        types = sorted(list(set(lines.mapped("type"))))
        total_nfq_level = sum(int(l.level2 or 0) for l in lines) or 1

        for u_type in types:
            val_lst = []
            type_lines = lines.filtered(lambda l: l.type == u_type)

            total_credits = sum(int(l.level3 or 0) for l in type_lines)
            nfq_level = sum(int(l.level2 or 0) for l in type_lines)

            for line in type_lines:
                val_lst.append(
                    {
                        "name": line.title,
                        "credit": line.level3,
                        "nqf_level": line.level2,
                        "saqa_us_id": line.id_no,
                    }
                )

            unit_standard.append(
                {
                    "type": u_type,
                    "value": val_lst[::-1],
                    "t_credits": total_credits,
                    "percentage": (nfq_level * 100) / total_nfq_level,
                    "counter": len(types),
                }
            )
        return sorted(unit_standard, key=lambda k: k["type"])

    def _get_status(self, achieved_id):
        """ORM logic for learner achievement status"""
        # Note: In Odoo 18 achieved_id is a single record here
        learner_lines = achieved_id.learner_id.learning_programme_ids
        match = learner_lines.filtered(
            lambda s: s.learning_programme_id.id
            == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {"achieve": match[:1].is_learner_achieved or False}

    def _get_certificate_no(self, achieved_id):
        learner_lines = achieved_id.learner_id.learning_programme_ids
        match = learner_lines.filtered(
            lambda s: s.learning_programme_id.id
            == achieved_id.lp_learner_assessment_achieved_line_id.id
        )
        return {"certificate_no": match[:1].certificate_no or False}

    def _get_lp_nqf_level(self, achieved_id):
        return ", ".join(achieved_id.lp_assessment_ids.mapped("seta_branch_id.name"))

    def _get_lp_credits_value(self, achieved_id):
        return ", ".join(
            [str(v) for v in achieved_id.lp_assessment_ids.mapped("total_credit")]
        )

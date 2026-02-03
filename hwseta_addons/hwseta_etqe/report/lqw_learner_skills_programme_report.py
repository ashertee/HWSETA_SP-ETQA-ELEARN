import logging
from odoo import models, api


_logger = logging.getLogger(__name__)


class SkillReportView(models.AbstractModel):
    # This name MUST match the pattern: report.module_name.template_name
    _name = "report.hwseta_etqe.lqw_report_skills_programme_statement_of_results"
    _description = "Skills Programme Statement of Results Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        In Odoo 18, this method handles what the old _wrapped_report_class did.
        It prepares the data and functions for the QWeb engine.
        """
        # Fetch the records being printed
        # Ensure 'skills.programme.learner.rel' is the correct technical name of your model
        docs = self.env["skills.programme.learner.rel"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "skills.programme.learner.rel",
            "docs": docs,
            # Mapping the helper methods from the logic class
            "get_skill": self._get_skill,
            "get_unit_standard": self._get_unit_standard,
            "get_status": self._get_status,
            "get_saqa_qual_id": self._get_saqa_qual_id,
            "get_certificate_no": self._get_certificate_no,
            "get_qual_nqf_level": self._get_qual_nqf_level,
            "get_qual_credits_value": self._get_qual_credits_value,
            "get_skills_saqa_qual_id": self._get_skills_saqa_qual_id,
        }

    def _get_skill(self, record):
        # Accessing the skills_programme_id Many2one directly
        return record.skills_programme_id.name or ""

    def _get_saqa_qual_id(self, record):
        return record.skills_programme_id.code or ""

    def _get_skills_saqa_qual_id(self, record):
        """
        Retrieves qualification details based on the skill's saqa_qual_id.
        Logic: Search provider.qualification first, then etqe.learning.programme.
        """
        qual_details = []
        saq-id = record.skills_programme_id.saqa_qual_id

        if not saq-id:
            return qual_details

        # Use ORM search instead of execute()
        qual = self.env["provider.qualification"].search(
            [("seta_branch_id", "=", 1), ("saqa_qual_id", "=", str(saq-id))], limit=1
        )

        if qual:
            qual_details.append(
                {
                    "value": [
                        {
                            "saqa_qual_id": qual.saqa_qual_id,
                            "lp_id": False,
                            "name": qual.name,
                            "n_level": qual.n_level,
                            "m_credits": qual.m_credits,
                        }
                    ]
                }
            )
            return qual_details

        # If not found, check learning programme
        lp = self.env["etqe.learning.programme"].search(
            [("seta_branch_id", "=", 1), ("code", "=", str(saq-id))], limit=1
        )

        if lp:
            qual_v2 = self.env["provider.qualification"].search(
                [
                    ("seta_branch_id", "=", 1),
                    ("saqa_qual_id", "=", str(lp.saqa_qual_id)),
                ],
                limit=1,
            )

            if qual_v2:
                qual_details.append(
                    {
                        "value": [
                            {
                                "saqa_qual_id": qual_v2.saqa_qual_id,
                                "lp_id": lp.code,
                                "name": qual_v2.name,
                                "n_level": qual_v2.n_level,
                                "m_credits": qual_v2.m_credits,
                            }
                        ]
                    }
                )
        return qual_details

    def _get_qual_nqf_level(self, record):
        return record.skills_programme_id.seta_branch_id.name or ""

    def _get_qual_credits_value(self, record):
        return str(record.skills_programme_id.total_credit or 0)

    def _get_unit_standard(self, record):
        """
        Retrieves Unit standards. Replaces complex SQL logic with filtered recordsets.
        """
        # Search for learner standards where selection is True
        learner_standards = self.env[
            "skills.programme.unit.standards.learner.rel"
        ].search([("selection", "=", True), ("skills_programme_id", "=", record.id)])

        unit_standard_type = learner_standards.mapped("type")
        res = []

        for u_type in set(unit_standard_type):
            val_lst = []
            total_credits = 0

            # Find the actual provider skill lines related to these learner lines
            for l_std in learner_standards.filtered(lambda r: r.type == u_type):
                # Matching logic based on your original search
                provider_line = self.env["skills.programme.unit.standards"].search(
                    [("id_no", "=", l_std.id_no), ("type", "=", l_std.type)], limit=1
                )

                if provider_line:
                    val_lst.append(
                        {
                            "name": provider_line.title,
                            "credit": provider_line.level3,
                            "nqf_level": provider_line.level2,
                            "saqa_us_id": provider_line.id_no,
                        }
                    )
                    total_credits += int(provider_line.level3 or 0)

            res.append(
                {
                    "value": val_lst[::-1],
                    "t_credits": total_credits,
                    "counter": len(set(unit_standard_type)),
                }
            )

        return sorted(res, key=lambda x: x.get("t_credits", 0))

    def _get_status(self, record):
        # Ported logic: currently returns False per your static update note
        return {"achieve": False}

    def _get_certificate_no(self, record):
        """ORM filter to find the specific skill programme line for the learner"""
        match = record.learner_id.skills_programme_ids.filtered(
            lambda s: s.skills_programme_id.id
            == record.skill_learner_assessment_achieved_line_id.id
        )
        return {"certificate_no": match[:1].certificate_no or False}

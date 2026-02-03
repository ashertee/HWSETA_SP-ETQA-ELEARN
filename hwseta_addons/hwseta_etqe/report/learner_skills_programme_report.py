import logging
from odoo import models, api


_logger = logging.getLogger(__name__)


class SkillReportView(models.AbstractModel):
    # This name must match: report.[module_name].[template_id]
    # In Odoo 18, this automatically links the logic to the XML template
    _name = "report.hwseta_etqe.report_skills_programme_statement_of_results"
    _description = "Skills Programme Statement of Results Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Main entry point for QWeb reports.
        Everything returned in this dictionary is available in the XML template.
        """
        docs = self.env["learner.assessment.achieved.line"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "learner.assessment.achieved.line",
            "docs": docs,
            # Link your helper methods from the logic class here:
            "get_skill": self._get_skill,
            "get_unit_standard": self._get_unit_standard,
            "get_status": self._get_status,
            "get_saqa_qual_id": self._get_saqa_qual_id,
            "get_certificate_no": self._get_certificate_no,
            "get_qual_nqf_level": self._get_qual_nqf_level,
            "get_qual_credits_value": self._get_qual_credits_value,
            "get_skills_saqa_qual_id": self._get_skills_saqa_qual_id,
        }

    def _get_skill(self, achieved_id):
        # Uses ORM to get skill names from the many-to-many relationship
        return ",".join(achieved_id.skill_programme_ids.mapped("name"))

    def _get_saqa_qual_id(self, achieved_id):
        # Maps the 'code' field as per your legacy logic
        return ",".join(achieved_id.skill_programme_ids.mapped("code"))

    def _get_skills_saqa_qual_id(self, achieved_id):
        """Logic to fetch Qualification details based on Skill SAQA ID"""
        qual_details = []
        # Get the SAQA ID from the skills programme related to this line
        skill_saq-ids = achieved_id.skill_programme_ids.mapped("saqa_qual_id")

        if skill_saq-ids:
            saq-id = skill_saq-ids[0]
            # Search for the provider qualification (Seta Branch ID 1)
            qual = self.env["provider.qualification"].search(
                [("seta_branch_id", "=", 1), ("saqa_qual_id", "=", saq-id)], limit=1
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
            else:
                # Fallback to learning programme if not found in provider qualification
                lp = self.env["etqe.learning.programme"].search(
                    [("seta_branch_id", "=", 1), ("code", "=", saq-id)], limit=1
                )

                if lp:
                    qual = self.env["provider.qualification"].search(
                        [
                            ("seta_branch_id", "=", 1),
                            ("saqa_qual_id", "=", lp.saqa_qual_id),
                        ],
                        limit=1,
                    )

                    if qual:
                        qual_details.append(
                            {
                                "value": [
                                    {
                                        "saqa_qual_id": qual.saqa_qual_id,
                                        "lp_id": lp.code,
                                        "name": qual.name,
                                        "n_level": qual.n_level,
                                        "m_credits": qual.m_credits,
                                    }
                                ]
                            }
                        )
        return qual_details

    def _get_qual_nqf_level(self, achieved_id):
        return ",".join(achieved_id.skill_programme_ids.mapped("seta_branch_id.name"))

    def _get_qual_credits_value(self, achieved_id):
        return ",".join(
            [str(c) for c in achieved_id.skill_programme_ids.mapped("total_credit")]
        )

    def _get_unit_standard(self, achieved_id):
        """Groups Unit Standards by type"""
        lines = achieved_id.skill_unit_standard_line_ids
        unit_standard_data = []
        types = sorted(list(set(lines.mapped("type"))))

        for u_type in types:
            type_lines = lines.filtered(lambda l: l.type == u_type)
            val_lst = [
                {
                    "name": l.title,
                    "credit": l.level3,
                    "nqf_level": l.level2,
                    "saqa_us_id": l.id_no,
                }
                for l in type_lines
            ]

            unit_standard_data.append(
                {
                    "value": val_lst[::-1],
                    "t_credits": sum(int(l.level3 or 0) for l in type_lines),
                    "counter": len(types),
                }
            )
        return unit_standard_data

    def _get_status(self, achieved_id):
        # Status logic preserved (static False as per your notes)
        return {"achieve": False}

    def _get_certificate_no(self, achieved_id):
        """ORM filter to find the specific skill programme line for the learner"""
        match = achieved_id.learner_id.skills_programme_ids.filtered(
            lambda s: s.skills_programme_id.id
            == achieved_id.skill_learner_assessment_achieved_line_id.id
        )
        return {"certificate_no": match[:1].certificate_no or False}

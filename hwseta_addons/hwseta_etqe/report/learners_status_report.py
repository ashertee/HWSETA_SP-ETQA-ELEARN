from odoo import models, api


class LearnerStatusReport(models.AbstractModel):
    # The name must match: report.[module_name].[report_id]
    _name = "report.hwseta_etqe.report_learner_status_report"
    _description = "Learner Assessment Status Report Logic"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Replaces the old localcontext.update.
        Provides data to the QWeb template.
        """
        docs = self.env["provider.assessment"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "provider.assessment",
            "docs": docs,
            "get_learner_status": self._get_learner_status,
        }

    def _get_learner_status(self, data):
        """
        Optimized logic to retrieve learner data filtered by the current user's provider.
        """
        learner_lst = []
        # Get the current user's associated partner (Provider)
        current_provider = self.env.user.partner_id

        # Search for learner records linked to this specific provider in one query
        learners = self.env["learner.registration.qualification"].search(
            [("learner_id", "!=", False), ("provider_id", "=", current_provider.id)]
        )

        for learner in learners:
            learner_lst.append(
                {
                    "provider_id": learner.provider_id.name,
                    "id": learner.learner_id.identification_id,
                    "name": learner.learner_id.name,
                    "title": learner.learner_qualification_parent_id.name,
                    "achieve": "Yes" if learner.is_learner_achieved else "No",
                    "complete": "Yes" if learner.is_complete else "No",
                }
            )

        return learner_lst


class StatusReportView(models.AbstractModel):
    # This name MUST match: report.[module_name].[template_id]
    # It also must match the 'report_name' defined in your ir.actions.report XML
    _name = "report.hwseta_etqe.report_learner_status_report"
    _description = "Learner Status Report View"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        This method replaces the old 'rml_parse' and 'localcontext' logic.
        It prepares the data and functions available to the QWeb template.
        """
        # 'docs' represents the records the user selected to print
        docs = self.env["provider.assessment"].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": "provider.assessment",
            "docs": docs,
            # Map your helper methods here so they can be called from the XML template
            "get_learner_status": self._get_learner_status,
        }

    def _get_learner_status(self, data):
        """
        Your custom logic (formerly in the learner_status_report class)
        should be moved directly into this class as a method.
        """
        # Implementation of your status logic goes here...
        pass

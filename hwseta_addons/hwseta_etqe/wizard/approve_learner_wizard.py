from odoo import models, fields, api, _
import xlsxwriter
import io
import base64


class ApproveLearnerWizard(models.TransientModel):
    _name = "approve.learner.wizard"
    _description = "Wizard to Approve Multiple Learners and Export Logs"

    war_label = fields.Text(string="Not Approved Records")

    @api.model
    def default_get(self, fields_list):
        # Modern Odoo uses fields_list as the parameter name
        res = super(ApproveLearnerWizard, self).default_get(fields_list)

        # Access context safely using self.env.context
        err_log = self.env.context.get("error_log")
        if err_log:
            res.update(
                {
                    "war_label": err_log,
                }
            )
        return res

    def learner_error_log(self):
        self.ensure_one()

        # Initialize the buffer and workbook
        buffered = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffered)
        worksheet1 = workbook.add_worksheet("Approval Status")

        # Formatting
        worksheet1.set_column(0, 2, 20)
        header_format = workbook.add_format(
            {"bold": True, "border": 1, "align": "center", "bg_color": "#D3D3D3"}
        )

        # Write Headers
        worksheet1.write("A1", "Approved Learners", header_format)
        worksheet1.write("B1", "Non-Approved Learners", header_format)

        # Write Non-Approved IDs (Column B)
        non_apr_ids = self.env.context.get("non_apr_ids", [])
        row = 1
        for record_id in non_apr_ids:
            if record_id:
                worksheet1.write(row, 1, str(record_id))
                row += 1

        # Write Approved IDs (Column A)
        approve_ids = self.env.context.get("approve_ids", [])
        row = 1
        for record_id in approve_ids:
            if record_id:
                worksheet1.write(row, 0, str(record_id))
                row += 1

        workbook.close()

        # Prepare the binary data
        xlsx_data = buffered.getvalue()
        out_data = base64.b64encode(xlsx_data)

        # Create Attachment
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Learners_Approval_Log.xlsx",
                "type": "binary",
                "datas": out_data,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )

        # Return URL action for download
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

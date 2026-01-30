from odoo import models, fields, api, _
import re


class AtrErrorLog(models.TransientModel):
    _name = 'atr.error.log'
    _description = 'Will show ATR log if something goes wrong.'

    show_atr_error_log = fields.Html(string='ATR Error Log')
    atr_error_log_download = fields.Text(string='ATR Error Log')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self.env.context

        if context.get('error_log_msg'):
            msg_list = context['error_log_msg'].split('=')
            html_msg = []
            text_msg = []

            for msg in msg_list:
                html_msg.append(msg)
                clean_msg = re.sub('<[^>]*>', '', msg)
                text_msg.append(clean_msg)

            res.update({
                'show_atr_error_log': '<br/>'.join(html_msg),
                'atr_error_log_download': '\n\n'.join(text_msg),
            })

        return res

    def action_download_incorrect_atr_file(self):
        self.ensure_one()
        incorrect_id = self.env.context.get('incorrect_id')

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/binary/saveas?model=ir.attachment&field=datas'
                   f'&filename_field=name&id={incorrect_id}',
            'target': 'self',
        }

    def action_download_error_log(self):
        self.ensure_one()
        return self.env.ref(
            'hwseta_sdp.atr_error_log_report'
        ).report_action(self)

    def action_delete_incorrect_records(self):
        context = self.env.context

        if context.get('actual_training_data_list'):
            self.env['actual.training.d1.fields'].browse(
                context['actual_training_data_list']
            ).unlink()

        if context.get('actual_adult_education_training_list'):
            self.env['actual.adult.education.fields'].browse(
                context['actual_adult_education_training_list']
            ).unlink()

        return True

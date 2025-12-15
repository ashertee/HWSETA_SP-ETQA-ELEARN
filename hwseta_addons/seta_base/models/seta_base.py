from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError,AccessError
import re
from lxml import etree
DEBUG = True

if DEBUG:
	import logging

	logger = logging.getLogger(__name__)


	def dbg(msg):
		logger.info(msg)
else:
	def dbg(msg):
		pass



class hwseta_mail_activity_schedule(models.TransientModel):
	_inherit = "mail.activity.schedule"

	seta_users_ids = fields.Many2many(comodel_name="res.users", compute="_compute_seta_users_ids")

	@api.depends("activity_user_id")
	def _compute_seta_users_ids(self):
		users_search = self.env['res.users'].search([])
		users_ids = []
		for user in users_search:
			if user.has_group('seta_base.seta_internal'):
				users_ids.append(user.id)
		for record in self:
			record.seta_users_ids = self.env["res.users"].search([('id', 'in', users_ids)])




# class IrAttachment(models.Model):
# 	_inherit = 'ir.attachment'
#
# 	@api.model
# 	def unlink(self):
# 		for attachment in self:
# 			if attachment.create_uid.id != self.env.user.id and attachment.res_model in ['seta.it.helpdesk','helpdesk.ticket']:
# 				raise UserError("You do not have permission to delete this attachment.")
# 			# Check if it's linked to a protected model
# 			if attachment.res_model in ['requisition.goods.services.transaction','seta.supplier.register','seta.supplier.register.transaction','seta.supplier.update.transaction','seta.purchase.order','rfq.purchase.order']:
# 				# Allow only users in a specific group, e.g., system administrators
# 				if not self.env.user.has_group('base.group_system'):
# 					raise AccessError(_("You are not allowed to delete attachments."))
#
# 		return super(IrAttachment, self).unlink()




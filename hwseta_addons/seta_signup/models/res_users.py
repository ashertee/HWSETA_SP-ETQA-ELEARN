from odoo import api, fields, models, _
DEBUG = True

if DEBUG:
	import logging

	logger = logging.getLogger(__name__)


	def dbg(msg):
		logger.info(msg)
else:
	def dbg(msg):
		pass


class ResUsers(models.Model):
	_inherit = 'res.users'

	popi_consent = fields.Boolean(default=False)
	marketing_consent = fields.Boolean(default=False)

from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
import werkzeug
import logging
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_users import SignupError
from email_validator import EmailSyntaxError, EmailUndeliverableError, validate_email
from ... import auth_signup_verify_email as verify

_logger = logging.getLogger(__name__)

DEBUG = True

if DEBUG:
	import logging

	logger = logging.getLogger(__name__)


	def dbg(msg):
		logger.info(msg)
else:
	def dbg(msg):
		pass

class SignupVerifyEmail(verify.controllers.main.SignupVerifyEmail):

	def passwordless_signup(self):
		values = request.params
		_logger.info('passwordless')
		_logger.info(values)
		qcontext = self.get_auth_signup_qcontext()

		# Check good format of e-mail
		try:
			validate_email(values.get("login", ""))
		except EmailSyntaxError as error:
			qcontext["error"] = getattr(
				error,
				"message",
				_("That does not seem to be an email address."),
			)
			return request.render("auth_signup.signup", qcontext)
		except EmailUndeliverableError as error:
			qcontext["error"] = str(error)
			return request.render("auth_signup.signup", qcontext)
		except Exception as error:
			qcontext["error"] = str(error)
			return request.render("auth_signup.signup", qcontext)
		if not values.get("email"):
			values["email"] = values.get("login")

		# preserve user lang
		values["lang"] = request.context.get("lang", "")

		# remove values that could raise "Invalid field '*' on model 'res.users'"
		values.pop("redirect", "")
		values.pop("token", "")
		values.pop("g-recaptcha-response", "")

		# default name to login
		# values["name"] = values['login']
		# Remove password
		values["password"] = ""
		sudo_users = request.env["res.users"].with_context(create_user=True).sudo()

		try:
			with request.cr.savepoint():
				sudo_users.signup(values, qcontext.get("token"))
				sudo_users.reset_password(values.get("login"))
		except Exception as error:
			# Duplicate key or wrong SMTP settings, probably
			_logger.exception(error)
			if (
					request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))])
			):
				qcontext["error"] = _(
					"Another user is already registered using this email" " address."
				)
			else:
				# Agnostic message for security
				qcontext["error"] = _(
					"Something went wrong, please try again later or" " contact us."
				)
			return request.render("auth_signup.signup", qcontext)

		qcontext["message"] = _("Check your email to activate your account!")
		return request.render("auth_signup.reset_password", qcontext)

# class AuthSignupHomeInherit(AuthSignupHome):


	# @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
	# def web_auth_signup(self, *args, **kw):
	# 	dbg("called other def")
	# 	qcontext = self.get_auth_signup_qcontext()
	#
	# 	if not qcontext.get('token') and not qcontext.get('signup_enabled'):
	# 		raise werkzeug.exceptions.NotFound()
	#
	# 	if 'error' not in qcontext and request.httprequest.method == 'POST':
	# 		try:
	# 			self.do_signup(qcontext)
	# 			# Send an account creation confirmation email
	# 			if qcontext.get('token'):
	# 				User = request.env['res.users']
	# 				user_sudo = User.sudo().search(
	# 					User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
	# 				)
	# 				template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
	# 				if user_sudo and template:
	# 					template.sudo().send_mail(user_sudo.id, force_send=True)
	# 			return self.web_login(*args, **kw)
	# 		except UserError as e:
	# 			qcontext['error'] = e.args[0]
	# 		except (SignupError, AssertionError) as e:
	# 			if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
	# 				qcontext["error"] = _("Another user is already registered using this email address.")
	# 			else:
	# 				_logger.error("%s", e)
	# 				qcontext['error'] = _("Could not create a new account.")
	#
	# 	response = request.render('auth_signup.signup', qcontext)
	# 	response.headers['X-Frame-Options'] = 'DENY'
	# 	return response

	# def _prepare_signup_values(self, qcontext):
	# 	values = {key: qcontext.get(key) for key in ('login', 'name', 'password', 'popi_consent', 'marketing_consent')}
	# 	dbg(values)
	# 	values['name'] = values['login']
	# 	dbg(values)
	# 	if not values:
	# 		raise UserError(_("The form was not properly filled in."))
	# 	if values.get('password') != qcontext.get('confirm_password'):
	# 		raise UserError(_("Passwords do not match; please retype them."))
	# 	supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
	# 	lang = request.context.get('lang', '')
	# 	if lang in supported_lang_codes:
	# 		values['lang'] = lang
	# 	return values
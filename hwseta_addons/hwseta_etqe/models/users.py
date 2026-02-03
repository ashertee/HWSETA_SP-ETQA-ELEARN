import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def copy_users_crypt(self):
        """Migrated from Odoo 8: Backup and clear passwords."""
        # Clear existing backup records
        self.env['res.users.copy'].search([]).unlink()
        
        # Search all users except the superuser (ID 1)
        users = self.env['res.users'].search([('id', '!=', 1)])
        
        for user in users:
            # Create backup
            self.env['res.users.copy'].create({
                'password_crypt': user.password_crypt,
                'password': user.password,
                'login': user.login,
                'id_copy': str(user.id) # id_copy is Char in your model
            })
            
            _logger.info("Backing up user ID: %s", user.id)
            
            # Clear passwords on the original user
            # Note: Directly clearing hashed passwords may trigger re-hashing logic
            user.write({
                'password_crypt': False,
                'password': False
            })

    def restore_users_crypt(self):
        """Migrated from Odoo 8: Restore hashed passwords."""
        backups = self.env['res.users.copy'].search([])
        for user_copy in backups:
            # Use sudo() if this needs to run without strict ACL checks during migration
            real_user = self.env['res.users'].browse(int(user_copy.id_copy))
            if real_user.exists():
                real_user.password_crypt = user_copy.password_crypt

class ResUsersCopy(models.Model):
    _name = 'res.users.copy'
    _description = 'User Password Backup'

    password_crypt = fields.Char()
    password = fields.Char()
    login = fields.Char()
    id_copy = fields.Char(string="Original User ID")
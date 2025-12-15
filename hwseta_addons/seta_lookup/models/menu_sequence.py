from odoo import models, api

class MenuSequenceUpdater(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def update_child_menu_sequence(self):
        parent_menu = self.env['ir.ui.menu'].search([('name', '=', 'Parent Menu')], limit=1)
        print(parent_menu)
        if parent_menu:
            child_menus = self.env['ir.ui.menu'].search([('parent_id', '=', parent_menu.id)])
            
            # Sort child menus alphabetically by name, then set sequence
            for index, child_menu in enumerate(sorted(child_menus, key=lambda menu: menu.name)):
                child_menu.sequence = index + 1

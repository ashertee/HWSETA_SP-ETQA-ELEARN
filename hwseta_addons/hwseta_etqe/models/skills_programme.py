from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError

class SkillsProgrammeUnitStandards(models.Model):
    _name = 'skills.programme.unit.standards'
    _description = 'Skills Programme Unit Standards'
    _rec_name = 'id_no'

    name = fields.Char(string='Name', required=True)
    
    type = fields.Selection([
        ('Core', 'Core'),
        ('Fundamental', 'Fundamental'),
        ('Elective', 'Elective'),
        ('Knowledge Module', 'Knowledge Module'),
        ('Practical Skill Module', 'Practical Skill Module'),
        ('Work Experience Module', 'Work Experience Module'),
        ('Exit Level Outcomes', 'Exit Level Outcomes'),
    ], string='Type', required=True, tracking=True) # Changed from track_visibility
    
    type_key = fields.Integer("Type Key")
    id_no = fields.Char(string='ID NO')
    title = fields.Char(string='UNIT STANDARD TITLE', required=True)
    level1 = fields.Char(string='PRE-2009 NQF LEVEL')
    level2 = fields.Char(string='NQF LEVEL')
    level3 = fields.Char(string='CREDITS')
    selection = fields.Boolean(string='SELECT', tracking=True) # Changed from track_visibility
    
    skills_programme_id = fields.Many2one(
        'skills.programme', 
        string='Skills Programme Reference', 
        ondelete='cascade'
    )
    
    # Relational fields
    skills_unit_standards_id = fields.Many2one(
        'learner.assessment.line.for.skills', 
        string='Skills Unit Standards'
    )
    skills_unit_standards_verify_id = fields.Many2one(
        'learner.assessment.verify.line.for.skills', 
        string='Skills Unit Standards'
    )
    skills_unit_standards_achieve_id = fields.Many2one(
        'learner.assessment.achieve.line.for.skills', 
        string='Skills Unit Standards'
    )
    skills_unit_standards_achieved_id = fields.Many2one(
        'learner.assessment.achieved.line.for.skills', 
        string='Skills Unit Standards'
    )


class SkillsProgramme(models.Model):
    _name = 'skills.programme'
    _description = 'Skills Programme'
    # In Odoo 18, we use _rec_names_search for multi-field quick searching
    _rec_names_search = ['name', 'code']

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    qualification_id = fields.Many2one(
        'provider.qualification', string='Qualification', required=True)
    saqa_qual_id = fields.Char(string='SAQA QUAL ID')
    applicant = fields.Char(string='Applicant')
    notes = fields.Text(string='Comment')
    if_us = fields.Boolean(string='US')
    
    total_credit = fields.Integer(
        string="Total Credit", 
        compute="_compute_total_credit", 
        store=True # Recommended to store for performance
    )
    
    unit_standards_line = fields.One2many(
        'skills.programme.unit.standards', 'skills_programme_id', string='Unit Standards')
    seta_branch_id = fields.Many2one('seta.id', string='Seta Branch')
    is_archive = fields.Boolean('Archive', default=False)

    # Relational back-references
    skills_id = fields.Many2one('learner.assessment.line.for.skills', string='Skills Programme')
    skills_verify_id = fields.Many2one('learner.assessment.verify.line.for.skills', string='Skills Programme')
    skills_achieve_id = fields.Many2one('learner.assessment.achieve.line.for.skills', string='Skills Programme')
    skills_achieved_id = fields.Many2one('learner.assessment.achieved.line.for.skills', string='Skills Programme')

    # 1. Modern Display Name (Replaces name_get)
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            record.display_name = name

    # 2. Modern Total Credit Computation
    @api.depends('unit_standards_line.selection', 'unit_standards_line.level3')
    def _compute_total_credit(self):
        for skill in self:
            total = 0
            for skill_line in skill.unit_standards_line:
                if skill_line.selection and skill_line.level3:
                    try:
                        total += int(skill_line.level3)
                    except ValueError:
                        continue
            skill.total_credit = total

    # 3. Modern Onchange: Qualification
    @api.onchange('qualification_id')
    def _onchange_qualification_id(self):
        if not self.qualification_id:
            self.unit_standards_line = [Command.clear()]
            return

        self.saqa_qual_id = self.qualification_id.saqa_qual_id

        lines = [Command.clear()] + [
            Command.create({
                'name': q_line.title,
                'type': q_line.type,
                'id_no': q_line.id_no,
                'title': q_line.title,
                'level1': q_line.level1,
                'level2': q_line.level2,
                'level3': q_line.level3,
                'selection': False,
            })
            for q_line in self.qualification_id.qualification_line
        ]

        self.unit_standards_line = lines
        
        # Domain filtering for qualification_id is better handled in the XML 
        # using domain="[('seta_branch_id','=','11')]"

    # 4. Uniqueness Constraints (Better than onchanges for validation)
    @api.constrains('code', 'name')
    def _check_uniqueness(self):
        for record in self:
            if record.code:
                duplicate_code = self.search([
                    ('id', '!=', record.id), 
                    ('code', '=', record.code.strip())
                ])
                if duplicate_code:
                    raise ValidationError(_('Please enter a unique Skills Programme Code.'))
            
            if record.name:
                duplicate_name = self.search([
                    ('id', '!=', record.id), 
                    ('name', '=', record.name.strip())
                ])
                if duplicate_name:
                    raise ValidationError(_('Please enter a unique Skills Programme Name.'))

    # 5. Simple State Sync Onchanges
    @api.onchange('is_archive')
    def _onchange_is_archive(self):
        if self.is_archive:
            self.seta_branch_id = False

    @api.onchange('seta_branch_id')
    def _onchange_seta_branch_id(self):
        # Assuming ID 1 is a specific branch logic
        if self.seta_branch_id and self.seta_branch_id.id == 1:
            self.is_archive = False

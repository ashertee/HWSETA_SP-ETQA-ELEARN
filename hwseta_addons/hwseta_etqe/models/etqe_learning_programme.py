from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError

from datetime import datetime
import logging

DEBUG = True

_logger = logging.getLogger(__name__)

def dbg(msg):
    if DEBUG:
        _logger.info(msg)


###############################
## LEARNING PROGRAMME MASTER ##
###############################

class EtqeLearningProgramme(models.Model):
    _name = 'etqe.learning.programme'
    _description = 'Learning Programme'
    _rec_name = 'name'

    # --------------------
    # DISPLAY
    # --------------------

    def name_get(self):
        res = []
        for record in self:
            name = record.name or ''
            if record.code:
                name = f"[{record.code}] {name}"
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', ('name', operator, name), ('code', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()

    # --------------------
    # COMPUTES
    # --------------------

    @api.depends('unit_standards_line.selection', 'unit_standards_line.level3')
    def _compute_total_credit(self):
        for rec in self:
            total = 0
            for line in rec.unit_standards_line:
                if line.selection and line.level3:
                    # Check if the string consists only of digits
                    if str(line.level3).isdigit():
                        total += int(line.level3)
                    else:
                        # Optional: Log a warning or handle floats if 'dvdv' was a typo
                        pass
            rec.total_credit = total
    # --------------------
    # ONCHANGE
    # --------------------

    from odoo import Command

    @api.onchange('qualification_id')
    def _onchange_qualification_id(self):
        if not self.qualification_id:
            self.unit_standards_line = [Command.clear()]
            return

        commands = [Command.clear()]

        for line in self.qualification_id.qualification_line:
            commands.append(Command.create({
                'name': line.title,
                'type': line.type,
                'id_no': line.id_no,
                'title': line.title,
                'level1': line.level1,
                'level2': line.level2,
                'level3': line.level3,
                'selection': line.type != 'Elective',
                'type_key': {'Fundamental': 1, 'Core': 2, 'Elective': 3}.get(line.type),
            }))

        self.unit_standards_line = commands
        self.saqa_qual_id = self.qualification_id.saqa_qual_id

    @api.onchange('is_archive')
    def _onchange_is_archive(self):
        if self.is_archive:
            self.seta_branch_id = False

    @api.onchange('seta_branch_id')
    def _onchange_seta_branch_id(self):
        if self.seta_branch_id and self.seta_branch_id.id == 1:
            self.is_archive = False

    @api.onchange('code')
    def _onchange_code(self):
        if self.code:
            exists = self.search(
                [('code', '=', self.code), ('id', '!=', self.id)],
                limit=1
            )
            if exists:
                self.code = False
                return {
                    'warning': {
                        'title': _('Duplicate Record'),
                        'message': _('Learning Programme ID must be unique.'),
                    }
                }

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            exists = self.search(
                [('name', '=', self.name), ('id', '!=', self.id)],
                limit=1
            )
            if exists:
                self.name = False
                return {
                    'warning': {
                        'title': _('Duplicate Record'),
                        'message': _('Learning Programme Name must be unique.'),
                    }
                }

    # --------------------
    # SQL CONSTRAINTS
    # --------------------

    _sql_constraints = [
        ('lp_code_uniq', 'unique(code)', 'Learning Programme Code must be unique!')
    ]

    # --------------------
    # FIELDS
    # --------------------

    name = fields.Char(string='Learning Programme Title', required=True)
    code = fields.Char(string='Learning Programme ID', required=True)

    qualification_id = fields.Many2one(
        'provider.qualification', string='Qualification', required=True
    )

    saqa_qual_id = fields.Char(string='SAQA QUAL ID')
    applicant = fields.Char(string='Applicant')
    notes = fields.Text(string='Comment')

    if_us = fields.Boolean(string='US')
    pn_level = fields.Char(string='PRE-2009 NQF LEVEL')
    n_level = fields.Char(string='NQF LEVEL')

    total_credit = fields.Integer(
        string='Total Credit',
        compute='_compute_total_credit',
        store=True,
    )

    unit_standards_line = fields.One2many(
        'etqe.learning.programme.unit.standards',
        'learning_programme_id',
        string='Unit Standards',
    )

    seta_branch_id = fields.Many2one('seta.branches', string='SETA Branch')
    is_archive = fields.Boolean(string='Archive')

    # Assessment links
    lp_id = fields.Many2one('learner.assessment.line.for.lp')
    lp_verify_id = fields.Many2one('learner.assessment.verify.line.for.lp')
    lp_achieve_id = fields.Many2one('learner.assessment.achieve.line.for.lp')
    lp_achieved_id = fields.Many2one('learner.assessment.achieved.line.for.lp')


class EtqeLearningProgrammeUnitStandards(models.Model):
    _name = 'etqe.learning.programme.unit.standards'
    _description = 'ETQE Learning Programme Unit Standards'
    _rec_name = 'id_no'

    # --------------------
    # FIELDS
    # --------------------

    name = fields.Char(string='Name', required=True)

    type = fields.Selection(
        [
            ('Core', 'Core'),
            ('Fundamental', 'Fundamental'),
            ('Elective', 'Elective'),
        ],
        string='Type',
        required=True,
        tracking=True,
    )

    id_no = fields.Char(string='ID No')
    title = fields.Char(string='Unit Standard Title', required=True)

    level1 = fields.Char(string='PRE-2009 NQF Level')
    level2 = fields.Char(string='NQF Level')
    level3 = fields.Char(string='Credits')

    selection = fields.Boolean(string='Select', tracking=True)
    type_key = fields.Integer(string='Type Key')

    learning_programme_id = fields.Many2one(
        'etqe.learning.programme',
        string='ETQE Learning Programme',
        ondelete='cascade',
    )

    seta_approved_lp = fields.Boolean(
        string='SETA Learning Material',
        tracking=True,
    )

    provider_approved_lp = fields.Boolean(
        string='Provider Learning Material',
        tracking=True,
    )

    # --------------------
    # ASSESSMENT LINKS
    # --------------------

    lp_unit_standards_id = fields.Many2one(
        'learner.assessment.line.for.lp',
        string='Learning Programme Unit Standards',
    )

    lp_unit_standards_verify_id = fields.Many2one(
        'learner.assessment.verify.line.for.lp',
        string='Learning Programme Unit Standards',
    )

    lp_unit_standards_achieve_id = fields.Many2one(
        'learner.assessment.achieve.line.for.lp',
        string='Learning Programme Unit Standards',
    )

    lp_unit_standards_achieved_id = fields.Many2one(
        'learner.assessment.achieved.line.for.lp',
        string='Learning Programme Unit Standards',
    )

    # --------------------
    # ONCHANGE
    # --------------------

    @api.onchange('seta_approved_lp')
    def _onchange_seta_approved_lp(self):
        if self.seta_approved_lp:
            self.provider_approved_lp = False

    @api.onchange('provider_approved_lp')
    def _onchange_provider_approved_lp(self):
        if self.provider_approved_lp:
            self.seta_approved_lp = False

    @api.onchange('type')
    def _onchange_type(self):
        mapping = {
            'Core': 1,
            'Fundamental': 2,
            'Elective': 3,
        }
        self.type_key = mapping.get(self.type)


################################################################
# PROVIDER MASTER LEARNING PROGRAMME
################################################################

# FOR LEARNING PROGRAMME UNIT STANDARDS


class LearningProgrammeUnitStandardsMasterRel(models.Model):
    _name = 'learning.programme.unit.standards.master.rel'
    _description = 'Learning Programme Unit Standards Master Relation'
    _rec_name = 'type'

    # --------------------
    # FIELDS
    # --------------------

    name = fields.Char(string='Name')

    type = fields.Selection(
        [
            ('Core', 'Core'),
            ('Fundamental', 'Fundamental'),
            ('Elective', 'Elective'),
            ('Knowledge Module', 'Knowledge Module'),
            ('Practical Skill Module', 'Practical Skill Module'),
            ('Work Experience Module', 'Work Experience Module'),
            ('Exit Level Outcomes', 'Exit Level Outcomes'),
        ],
        string='Type',
        required=True,
        tracking=True,
    )

    id_no = fields.Char(string='ID No')
    title = fields.Char(string='Unit Standard Title', required=True)

    level1 = fields.Char(string='PRE-2009 NQF Level')
    level2 = fields.Char(string='NQF Level')
    level3 = fields.Char(string='Credits')

    selection = fields.Boolean(string='Select')

    learning_programme_id = fields.Many2one(
        'learning.programme.master.rel',
        string='Learning Programme Reference',
        ondelete='cascade',
    )

    seta_approved_lp = fields.Boolean(
        string='SETA Learning Material',
        tracking=True,
    )

    provider_approved_lp = fields.Boolean(
        string='Provider Learning Material',
        tracking=True,
    )


# FOR LEARNING PROGRAMME


class LearningProgrammeMasterRel(models.Model):
    _name = 'learning.programme.master.rel'
    _description = 'Learning Programme Master Relation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # --------------------------------------------------
    # FIELDS
    # --------------------------------------------------

    learning_programme_id = fields.Many2one(
        'etqe.learning.programme',
        string='Learning Programme',
        tracking=True
    )

    unit_standards_line = fields.One2many(
        'learning.programme.unit.standards.master.rel',
        'learning_programme_id',
        string='Unit Standards'
    )

    learning_programme_partner_rel_id = fields.Many2one(
        'res.partner',
        string='Provider Partner Reference',
        tracking=True
    )

    lp_saqa_id = fields.Char(string='SAQA QUAL ID', tracking=True)

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting_approval', 'Waiting Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        string='Status',
        default='draft',
        tracking=True
    )

    request_send = fields.Boolean(string='Send Request', default=False)
    approval_request = fields.Boolean(string='Approval Request', default=False)
    reject_request = fields.Boolean(string='Reject Request', default=False)

    assessors_id = fields.Many2one(
        'hr.employee',
        string='Assessor',
        domain="[('is_active_assessor','=',True),('is_assessors','=',True)]",
        tracking=True
    )

    assessor_sla_document = fields.Many2one(
        'ir.attachment',
        string='Assessor SLA Document'
    )

    moderators_id = fields.Many2one(
        'hr.employee',
        string='Moderator',
        domain="[('is_active_moderator','=',True),('is_moderators','=',True)]",
        tracking=True
    )

    moderator_sla_document = fields.Many2one(
        'ir.attachment',
        string='Moderator SLA Document'
    )

    assessor_no = fields.Char(string='Assessor ID')
    moderator_no = fields.Char(string='Moderator ID')

    # --------------------------------------------------
    # SECURITY HELPERS
    # --------------------------------------------------

    def _check_access_rights(self):
        return any([
            self.env.user.has_group('hwseta_etqe.group_prov_quals'),
            self.env.user.has_group('hwseta_etqe.group_seta_administrator'),
            self.env.user.has_group('hwseta_etqe.group_etqe_provincial_manager'),
            self.env.user.has_group('hwseta_etqe.group_etqe_provider'),
            self.env.user.has_group('hwseta_etqe.group_etqe_executive_manager'),
        ])

    # --------------------------------------------------
    # ORM OVERRIDES
    # --------------------------------------------------

    def unlink(self):
        for rec in self:
            if not rec._check_access_rights():
                raise UserError(
                    _("You don't have the Access Rights Group: Provider Qualification Administrator")
                )

            rec.unit_standards_line.unlink()

            if rec.learning_programme_partner_rel_id:
                rec.learning_programme_partner_rel_id.message_post(
                    body=_("Unlinked Learning Programme: %s") % (rec.lp_saqa_id or '')
                )

        return super().unlink()

    @api.model
    def create(self, vals):
        if not self._check_access_rights():
            raise UserError(
                _("You don't have the Access Rights Group: Provider Qualification Administrator")
            )

        if not vals.get('learning_programme_partner_rel_id'):
            raise UserError(_("No accreditation qualification ID found"))

        partner = self.env['res.partner'].browse(vals['learning_programme_partner_rel_id'])
        if partner:
            partner.message_post(
                body=_("Created Learning Programme: %s") % vals.get('lp_saqa_id', '')
            )

        return super().create(vals)

    # --------------------------------------------------
    # ONCHANGE METHODS
    # --------------------------------------------------

    @api.onchange('assessor_no')
    def _onchange_assessor_no(self):
        if self.assessor_no:
            assessor = self.env['hr.employee'].search(
                [('assessor_seq_no', '=', self.assessor_no)],
                limit=1
            )
            self.assessors_id = assessor

    @api.onchange('moderator_no')
    def _onchange_moderator_no(self):
        if self.moderator_no:
            moderator = self.env['hr.employee'].search(
                [('moderator_seq_no', '=', self.moderator_no)],
                limit=1
            )
            self.moderators_id = moderator

    @api.onchange('learning_programme_id')
    def _onchange_learning_programme_id(self):
        if not self.learning_programme_id:
            return

        unit_lines = []
        for line in self.learning_programme_id.unit_standards_line:
            if line.selection:
                unit_lines.append((0, 0, {
                    'name': line.name,
                    'type': line.type,
                    'id_no': line.id_no,
                    'title': line.title,
                    'level1': line.level1,
                    'level2': line.level2,
                    'level3': line.level3,
                    'selection': True,
                    'seta_approved_lp': line.seta_approved_lp,
                    'provider_approved_lp': line.provider_approved_lp,
                }))

        self.unit_standards_line = unit_lines
        self.lp_saqa_id = self.learning_programme_id.saqa_qual_id

    # --------------------------------------------------
    # WORKFLOW ACTIONS
    # --------------------------------------------------

    def action_send_request(self):
        self.write({
            'status': 'waiting_approval',
            'request_send': True
        })

    def action_approved_request(self):
        self.write({
            'status': 'approved',
            'approval_request': True
        })

    def action_rejected_request(self):
        self.write({
            'status': 'rejected',
            'reject_request': True
        })


################################################################
# PROVIDER MASTER CAMPUS LEARNING PROGRAMME                    #
################################################################
# FOR LEARNING PROGRAMME UNITS STANDARDS


class LearningProgrammeUnitStandardsMasterCampusRel(models.Model):
    _name = 'learning.programme.unit.standards.master.campus.rel'
    _description = 'Learning Programme Unit Standards Master Campus Rel'
    _rec_name = 'type'

    name = fields.Char(string='Name')

    type = fields.Char(
        string='Type',
        required=True
    )

    id_no = fields.Char(string='ID NO')

    title = fields.Char(
        string='UNIT STANDARD TITLE',
        required=True
    )

    level1 = fields.Char(string='PRE-2009 NQF LEVEL')
    level2 = fields.Char(string='NQF LEVEL')
    level3 = fields.Char(string='CREDITS')

    selection = fields.Boolean(string='SELECT')

    learning_programme_id = fields.Many2one(
        'learning.programme.master.campus.rel',
        string='Learning Programme Reference',
        ondelete='cascade'
    )

    seta_approved_lp = fields.Boolean(
        string='SETA Learning Material',
        tracking=True
    )

    provider_approved_lp = fields.Boolean(
        string='PROVIDER Learning Material',
        tracking=True
    )


# --------------------------------------------------
# LEARNING PROGRAMME MASTER (CAMPUS)
# --------------------------------------------------

class LearningProgrammeMasterCampusRel(models.Model):
    _name = 'learning.programme.master.campus.rel'
    _description = 'Learning Programme Master Campus Rel'

    learning_programme_id = fields.Many2one(
        'etqe.learning.programme',
        string='Learning Programme'
    )

    unit_standards_line = fields.One2many(
        'learning.programme.unit.standards.master.campus.rel',
        'learning_programme_id',
        string='Unit Standards'
    )

    learning_programme_partner_campus_rel_id = fields.Many2one(
        'res.partner',
        string='Provider Accreditation Reference'
    )

    lp_saqa_id = fields.Char(string='SAQA QUAL ID')

    # --------------------------------------------------
    # ONCHANGE
    # --------------------------------------------------

    @api.onchange('learning_programme_id')
    def _onchange_learning_programme_id(self):
        if not self.learning_programme_id:
            return

        unit_standards = []

        for line in self.learning_programme_id.unit_standards_line:
            if line.selection:
                unit_standards.append((0, 0, {
                    'name': line.name,
                    'type': line.type,
                    'id_no': line.id_no,
                    'title': line.title,
                    'level1': line.level1,
                    'level2': line.level2,
                    'level3': line.level3,
                    'selection': True,
                    'seta_approved_lp': line.seta_approved_lp,
                    'provider_approved_lp': line.provider_approved_lp,
                }))

        self.unit_standards_line = unit_standards
        self.lp_saqa_id = self.learning_programme_id.saqa_qual_id


################################################################
# LEARNER REGISTRATION AND MASTER LEARNING PROGRAMME           #
################################################################

# FOR LEARNING PROGRAMME UNIT STANDARDS


class LearningProgrammeUnitStandardsLearnerRel(models.Model):
    _name = 'learning.programme.unit.standards.learner.rel'
    _description = 'Learning Programme Unit Standards Learner Rel'
    _rec_name = 'type'

    name = fields.Char(string='Name')

    type = fields.Selection(
        [
            ('Core', 'Core'),
            ('Fundamental', 'Fundamental'),
            ('Elective', 'Elective'),
            ('Knowledge Module', 'Knowledge Module'),
            ('Practical Skill Module', 'Practical Skill Module'),
            ('Work Experience Module', 'Work Experience Module'),
            ('Exit Level Outcomes', 'Exit Level Outcomes'),
        ],
        string='Type',
        tracking=True
    )

    id_no = fields.Char(string='ID NO')

    title = fields.Char(
        string='UNIT STANDARD TITLE',
    )

    level1 = fields.Char(string='PRE-2009 NQF LEVEL')
    level2 = fields.Char(string='NQF LEVEL')
    level3 = fields.Char(string='CREDITS')

    selection = fields.Boolean(string='SELECT')

    learning_programme_id = fields.Many2one(
        'learning.programme.learner.rel',
        string='Learning Programme Reference',
        ondelete='cascade'
    )

    seta_approved_lp = fields.Boolean(
        string='SETA Learning Material',
        tracking=True
    )

    provider_approved_lp = fields.Boolean(
        string='PROVIDER Learning Material',
        tracking=True
    )

    achieve = fields.Boolean(
        string='ACHIEVE',
        default=False
    )


# FOR LEARNING PROGRAMME


class LearningProgrammeLearnerRel(models.Model):
    _name = 'learning.programme.learner.rel'
    _description = 'Learning Programme Learner Rel'

    lp_saqa_id = fields.Char(string='SAQA QUAL ID')

    learning_programme_id = fields.Many2one(
        'etqe.learning.programme',
        string='Learning Programme',
        required=True
    )

    unit_standards_line = fields.One2many(
        'learning.programme.unit.standards.learner.rel',
        'learning_programme_id',
        string='Unit Standards'
    )

    learning_programme_learner_rel_id = fields.Many2one(
        'learner.registration',
        string='Learner Registration Reference'
    )

    learning_programme_learner_rel_ids = fields.Many2one(
        'hr.employee',
        string='Learner Master Reference'
    )
    select = fields.Boolean("Selection", default=True)

    start_date = fields.Date()
    end_date = fields.Date()

    assessors_id = fields.Many2one(
        'hr.employee',
        domain=[('is_active_assessor', '=', True), ('is_assessors', '=', True)]
    )
    assessor_date = fields.Date()

    moderators_id = fields.Many2one(
        'hr.employee',
        domain=[('is_active_moderator', '=', True), ('is_moderators', '=', True)]
    )
    moderator_date = fields.Date()

    minimum_credits = fields.Integer(
        related='learning_programme_id.total_credit',
        store=True
    )

    total_credits = fields.Integer(
        compute='_compute_total_credits',
        store=True
    )

    batch_id = fields.Many2one('batch.master', domain="[('qual_skill_batch', '=', 'lp')]")

    provider_id = fields.Many2one(
        'res.partner',
        default=lambda self: self.env.user.partner_id
    )

    approval_date = fields.Date()
    is_learner_achieved = fields.Boolean(default=False)
    is_complete = fields.Boolean(default=False)

    certificate_no = fields.Char()
    certificate_date = fields.Date()

    lp_status = fields.Char()
    lqw_status = fields.Char(default='awaiting_approval')

    # ---------------------------------------------------------
    # COMPUTES
    # ---------------------------------------------------------

    @api.depends('unit_standards_line.selection', 'unit_standards_line.level3')
    def _compute_total_credits(self):
        for rec in self:
            total = 0
            for line in rec.unit_standards_line:
                # Check if line is selected AND level3 has a value
                if line.selection and line.level3:
                    # Use .isdigit() to check if the string contains only numbers
                    if line.level3.replace('.', '', 1).isdigit():
                        total += float(line.level3)  # Use float in case of decimals
                    else:
                        # Optional: Log a warning or skip if it's junk text like 'dvdv'
                        continue
            rec.total_credits = total

    # ---------------------------------------------------------
    # ONCHANGE (Odoo 18 style)
    # ---------------------------------------------------------

    @api.onchange('learning_programme_id')
    def _onchange_learning_programme(self):
        if not self.learning_programme_id:
            return

        self.lp_saqa_id = self.learning_programme_id.saqa_qual_id

        # 1. Start with the clear command (5, 0, 0) in a normal Python list
        lines = [(5, 0, 0)]

        # 2. Append the new line commands to that list
        for us in self.learning_programme_id.unit_standards_line:
            if us.selection:
                lines.append((0, 0, {
                    'name': us.name,
                    'type': us.type,
                    'id_no': us.id_no,
                    'title': us.title,
                    'level1': us.level1,
                    'level2': us.level2,
                    'level3': us.level3,
                    'selection': True,
                    'seta_approved_lp': us.seta_approved_lp,
                    'provider_approved_lp': us.provider_approved_lp,
                }))

        # 3. Assign the entire list to the field
        self.unit_standards_line = lines
    # ---------------------------------------------------------
    # BUSINESS ACTIONS
    # ---------------------------------------------------------

    def lqw_approve_lp(self):
        self.ensure_one()

        if not self.env.user.has_group(
            'hwseta_etqe.group_lqw_approver'
        ) and not self.env.user.has_group(
            'hwseta_etqe.group_seta_administrator'
        ):
            raise UserError(_('You are not authorised to approve this LP.'))

        self.write({
            'is_learner_achieved': True,
            'approval_date': fields.Date.today(),
            'lp_status': 'Achieved',
            'lqw_status': 'approved',
        })
        learner = self.env['hr.employee'].browse(self.learning_programme_learner_rel_ids.id)

        if learner:
            learner.message_post(
                body=_('Learning Programme approved: %s')
                % self.learning_programme_id.name
            )

    # ---------------------------------------------------------
    # CREATE / DELETE
    # ---------------------------------------------------------

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        learner = self.env['hr.employee'].browse(vals.get('learning_programme_learner_rel_ids'))
        if learner:
            learner.message_post(
                body=_(
                    'Enrolled in %s (Certificate: %s)'
                ) % (rec.learning_programme_id.name, rec.certificate_no or '-')
            )

        return rec

    def unlink(self):
        for rec in self:
            learner = self.env['hr.employee'].browse(vals.get('learning_programme_learner_rel_ids'))
            if learner:
                learner.message_post(
                    body=_(
                        'Learning Programme removed: %s'
                    ) % rec.learning_programme_id.name
                )
        return super().unlink()


################################################################
# LEARNER ASSESSMENT FOR LEARNING PROGRAMME                    #
################################################################


class LearnerAssessmentLineForLP(models.Model):
    _name = 'learner.assessment.line.for.lp'
    _description = 'Learner Assessment Line for Learning Programme'

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    provider_assessment_ref_id_for_lp = fields.Many2one(
        'provider.assessment',
        string='Provider Assessment Reference'
    )

    learner_id = fields.Many2one(
        'hr.employee',
        string='Learner',
        required=True
    )

    assessors_id = fields.Many2one(
        'hr.employee',
        string='Assessor',
        domain=[('is_assessors', '=', True)]
    )

    moderators_id = fields.Many2one(
        'hr.employee',
        string='Moderator',
        domain=[('is_moderators', '=', True)]
    )

    learner_identity_number = fields.Char(string='Learner Number')
    timetable_id = fields.Many2one('learner.timetable')

    verify = fields.Boolean(string='Verification')

    provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        default=lambda self: self.env.context.get('provider')
    )

    identification_id = fields.Char(string='National ID')

    lp_learner_assessment_line_id = fields.Many2many(
        'etqe.learning.programme',
        string='Learning Programmes'
    )

    lp_unit_standards_learner_assessment_line_id = fields.Many2many(
        'etqe.learning.programme.unit.standards',  # 1. The comodel
        'lp_unit_std_assessment_rel',  # 2. The relation table name (STAY UNDER 63)
        'line_id',  # 3. Column pointing to this model
        'std_id',  # 4. Column pointing to target model
        string='Learning Programme Unit Standards'
    )

    # ---------------------------------------------------------
    # ONCHANGE METHODS (Odoo 18 style)
    # ---------------------------------------------------------

    @api.onchange('assessors_id', 'moderators_id')
    def _onchange_assessor_moderator(self):
        if self.assessors_id and self.moderators_id:
            if self.assessors_id == self.moderators_id:
                self.assessors_id = False
                self.moderators_id = False
                return {
                    'warning': {
                        'title': _('Error'),
                        'message': _('Assessor and Moderator cannot be the same.')
                    }
                }

    @api.onchange('learner_identity_number')
    def _onchange_learner_identity_number(self):
        if self.learner_identity_number:
            learner = self.env['hr.employee'].search(
                [('learner_reg_no', '=', self.learner_identity_number)],
                limit=1
            )
            self.learner_id = learner

    @api.onchange('provider_id')
    def _onchange_provider_id(self):
        if not self.provider_id:
            return

        provider = self.provider_id
        user = self.env.user

        # ---------------- Learners ----------------
        learners = self.env['hr.employee'].search([
            ('is_learner', '=', True),
            ('provider_learner', '=', True),
            ('state', 'in', ['active', 'replacement'])
        ])

        if not user._is_admin():
            learners = learners.filtered(
                lambda l: any(
                    q.provider_id == user.partner_id
                    for q in l.learner_qualification_ids
                )
            )

        # ---------------- Learning Programmes ----------------
        learning_programmes = provider.learning_programme_ids.mapped(
            'learning_programme_id'
        )

        # ---------------- Assessors ----------------
        assessors = provider.assessors_ids.mapped('assessors_id')

        # ---------------- Moderators ----------------
        moderators = provider.moderators_ids.mapped('moderators_id')

        return {
            'domain': {
                'learner_id': [('id', 'in', learners.ids)],
                'lp_learner_assessment_line_id': [('id', 'in', learning_programmes.ids)],
                'assessors_id': [('id', 'in', assessors.ids)],
                'moderators_id': [('id', 'in', moderators.ids)],
            }
        }

    @api.onchange('lp_learner_assessment_line_id')
    def _onchange_learning_programmes(self):
        unit_standards = self.lp_learner_assessment_line_id.mapped(
            'unit_standards_line'
        )
        return {
            'domain': {
                'lp_unit_standards_learner_assessment_line_id': [
                    ('id', 'in', unit_standards.ids)
                ]
            }
        }


class LearnerAssessmentAchieveLineForLP(models.Model):
    _name = 'learner.assessment.achieve.line.for.lp'
    _description = 'Learner Assessment Achieve Line for Learning Programme'

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    provider_assessment_achieve_ref_id_for_lp = fields.Many2one(
        'provider.assessment',
        string='Provider Assessment Achieve Reference'
    )

    learner_id = fields.Many2one(
        'hr.employee',
        string='Learner',
        required=True
    )

    assessors_id = fields.Many2one(
        'hr.employee',
        string='Assessor',
        domain=[('is_assessors', '=', True)]
    )

    moderators_id = fields.Many2one(
        'hr.employee',
        string='Moderator',
        domain=[('is_moderators', '=', True)]
    )

    learner_identity_number = fields.Char(
        string='Learner Number'
    )

    timetable_id = fields.Many2one(
        'learner.timetable',
        string='Timetable'
    )

    achieve = fields.Boolean(
        string='Achieved'
    )

    identification_id = fields.Char(
        string='National ID'
    )

    lp_learner_assessment_achieve_line_id = fields.Many2many(
        'etqe.learning.programme',
        'lp_learner_assess_achieve_rel',  # Shortened relation table name
        'achieve_line_id',  # This model column
        'lp_id',  # Target model column
        string='Learning Programmes'
    )

    lp_unit_standards_learner_assessment_achieve_line_id = fields.Many2many(
        'etqe.learning.programme.unit.standards',  # Target Model
        'lp_unit_std_achieve_rel',  # Table Name (23 chars - Safe!)
        'achieve_line_id',  # Column 1 (Link to current model)
        'unit_std_id',  # Column 2 (Link to target model)
        string='Learning Programme Unit Standards'
    )

    # ---------------------------------------------------------
    # ONCHANGE (OPTIONAL BUT SAFE)
    # ---------------------------------------------------------

    @api.onchange('assessors_id', 'moderators_id')
    def _onchange_assessor_moderator(self):
        if self.assessors_id and self.moderators_id:
            if self.assessors_id == self.moderators_id:
                self.assessors_id = False
                self.moderators_id = False
                return {
                    'warning': {
                        'title': 'Error',
                        'message': 'Assessor and Moderator cannot be the same.'
                    }
                }


class LearnerAssessmentVerifyLineForLP(models.Model):
    _name = 'learner.assessment.verify.line.for.lp'
    _description = 'Learner Assessment Verify Line for Learning Programme'

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    provider_assessment_verify_ref_id_for_lp = fields.Many2one(
        'provider.assessment',
        string='Provider Assessment Verify Reference'
    )

    learner_id = fields.Many2one(
        'hr.employee',
        string='Learner',
        required=True
    )

    assessors_id = fields.Many2one(
        'hr.employee',
        string='Assessor',
        domain=[('is_assessors', '=', True)]
    )

    moderators_id = fields.Many2one(
        'hr.employee',
        string='Moderator',
        domain=[('is_moderators', '=', True)]
    )

    learner_identity_number = fields.Char(
        string='Learner Number'
    )

    identification_id = fields.Char(
        string='National ID'
    )

    timetable_id = fields.Many2one(
        'learner.timetable',
        string='Timetable'
    )

    verify = fields.Boolean(
        string='Verified'
    )

    comment = fields.Char(
        string='Comment'
    )

    lp_learner_assessment_verify_line_id = fields.Many2many(
        'etqe.learning.programme',
        'lp_learner_assess_verify_rel',  # Manual Table Name (Safe < 63 chars)
        'verify_line_id',  # Column 1 (Link to current model)
        'lp_id',  # Column 2 (Link to target model)
        string='Learning Programmes'
    )

    lp_unit_standards_learner_assessment_verify_line_id = fields.Many2many(
        'etqe.learning.programme.unit.standards',  # Target Model
        'lp_unit_std_verify_rel',  # Sourced table name (Stay under 63)
        'verify_line_id',  # Column 1 (Link to this model)
        'unit_std_id',  # Column 2 (Link to target model)
        string='Learning Programme Unit Standards'
    )

    # ---------------------------------------------------------
    # ONCHANGE VALIDATION
    # ---------------------------------------------------------

    @api.onchange('assessors_id', 'moderators_id')
    def _onchange_assessor_moderator(self):
        if self.assessors_id and self.moderators_id:
            if self.assessors_id == self.moderators_id:
                self.assessors_id = False
                self.moderators_id = False
                return {
                    'warning': {
                        'title': 'Error',
                        'message': 'Assessor and Moderator cannot be the same.'
                    }
                }


class LearnerAssessmentEvaluateLineForLP(models.Model):
    _name = 'learner.assessment.evaluate.line.for.lp'
    _description = 'Learner Assessment Evaluate Line for Learning Programme'

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    provider_assessment_evaluate_ref_id_for_lp = fields.Many2one(
        'provider.assessment',
        string='Provider Assessment Evaluate Reference'
    )

    learner_id = fields.Many2one(
        'hr.employee',
        string='Learner',
        required=True
    )

    assessors_id = fields.Many2one(
        'hr.employee',
        string='Assessor',
        domain=[('is_assessors', '=', True)]
    )

    moderators_id = fields.Many2one(
        'hr.employee',
        string='Moderator',
        domain=[('is_moderators', '=', True)]
    )

    learner_identity_number = fields.Char(
        string='Learner Number'
    )

    identification_id = fields.Char(
        string='National ID'
    )

    timetable_id = fields.Many2one(
        'learner.timetable',
        string='Timetable'
    )

    evaluate = fields.Boolean(
        string='Evaluated'
    )

    comment = fields.Char(
        string='Comment'
    )

    lp_learner_assessment_evaluate_line_id = fields.Many2many(
        'etqe.learning.programme',
        'lp_learner_assess_eval_rel',  # Manual Table Name (Safe & Short)
        'eval_line_id',  # Column 1
        'lp_id',  # Column 2
        string='Learning Programmes'
    )

    lp_unit_standards_learner_assessment_evaluate_line_id = fields.Many2many(
        'etqe.learning.programme.unit.standards',  # Target Model
        'lp_unit_std_evaluate_rel',  # Table Name (24 chars - SAFE)
        'evaluate_line_id',  # Column 1 (Source link)
        'unit_std_id',  # Column 2 (Target link)
        string='Learning Programme Unit Standards'
    )

    # ---------------------------------------------------------
    # ONCHANGE VALIDATION
    # ---------------------------------------------------------

    @api.onchange('assessors_id', 'moderators_id')
    def _onchange_assessor_moderator(self):
        if self.assessors_id and self.moderators_id:
            if self.assessors_id == self.moderators_id:
                self.assessors_id = False
                self.moderators_id = False
                return {
                    'warning': {
                        'title': 'Error',
                        'message': 'Assessor and Moderator cannot be the same.'
                    }
                }


class LearnerAssessmentAchievedLineForLP(models.Model):
    _name = 'learner.assessment.achieved.line.for.lp'
    _description = 'Learner Assessment Achieved Line for Learning Programme'

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    provider_assessment_achieved_ref_id_for_lp = fields.Many2one(
        'provider.assessment',
        string='Provider Assessment Achieved Reference'
    )

    learner_id = fields.Many2one(
        'hr.employee',
        string='Learner',
        required=True
    )

    assessors_id = fields.Many2one(
        'hr.employee',
        string='Assessor',
        domain=[('is_assessors', '=', True)]
    )

    moderators_id = fields.Many2one(
        'hr.employee',
        string='Moderator',
        domain=[('is_moderators', '=', True)]
    )

    learner_identity_number = fields.Char(
        string='Learner Number'
    )

    identification_id = fields.Char(
        string='National ID'
    )

    is_learner_achieved = fields.Boolean(
        string='Achieved'
    )

    timetable_id = fields.Many2one(
        'learner.timetable',
        string='Timetable'
    )

    lp_learner_assessment_achieved_line_id = fields.Many2many(
        'etqe.learning.programme',
        'lp_learner_assess_achieved_rel',  # Manual Table Name (Safe)
        'achieved_line_id',  # Column 1
        'lp_id',  # Column 2
        string='Learning Programmes'
    )

    lp_unit_standards_learner_assessment_achieved_line_id = fields.Many2many(
        'etqe.learning.programme.unit.standards',  # Target Model
        'lp_unit_std_achieved_rel',  # Table Name (24 chars - SAFE)
        'achieved_line_id',  # Column 1 (Link to current model)
        'unit_std_id',  # Column 2 (Link to target model)
        string='Learning Programme Unit Standards'
    )

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    @api.onchange('assessors_id', 'moderators_id')
    def _onchange_assessor_moderator(self):
        if self.assessors_id and self.moderators_id:
            if self.assessors_id == self.moderators_id:
                self.assessors_id = False
                self.moderators_id = False
                return {
                    'warning': {
                        'title': 'Error',
                        'message': 'Assessor and Moderator cannot be the same.'
                    }
                }


###########################################
## LEARNING PROGRAMME ACCREDITATION REL  ##
###########################################


class LearningProgrammeAccreditationRel(models.Model):
    _name = 'learning.programme.accreditation.rel'
    _description = 'Learning Programme Accreditation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ---------------------------------------------------------
    # FIELDS
    # ---------------------------------------------------------

    saqa_qual_id = fields.Char(string='SAQA QUAL ID', tracking=True)

    learning_programme_id = fields.Many2one(
        'etqe.learning.programme',
        string='Learning Programme',
        tracking=True,
        required=True
    )

    qualification_id = fields.Many2one(
        'provider.qualification',
        string='Qualification',
        ondelete='restrict'
    )

    unit_standards_line = fields.One2many(
        'learning.programme.unit.standards.accreditation.rel',
        'learning_programme_id',
        string='Unit Standards'
    )

    learning_programme_accreditation_rel_id = fields.Many2one(
        'provider.accreditation',
        string='Provider Accreditation Reference'
    )

    select = fields.Boolean(default=True)
    verify = fields.Boolean(string='Verified', default=False, tracking=True)

    minimum_credits = fields.Integer(
        related='learning_programme_id.total_credit',
        string='Minimum Credits',
        store=True
    )

    total_credits = fields.Integer(
        compute='_compute_total_credits',
        store=True
    )

    assessors_id = fields.Many2one(
        'hr.employee',
        string='Assessor',
        domain=[('is_active_assessor', '=', True), ('is_assessors', '=', True)]
    )

    assessor_sla_document = fields.Many2one(
        'ir.attachment',
        string='Assessor SLA Document'
    )

    moderators_id = fields.Many2one(
        'hr.employee',
        string='Moderator',
        domain=[('is_active_moderator', '=', True), ('is_moderators', '=', True)]
    )

    moderator_sla_document = fields.Many2one(
        'ir.attachment',
        string='Moderator SLA Document'
    )

    assessor_no = fields.Char(string='Assessor ID')
    moderator_no = fields.Char(string='Moderator ID')

    # ---------------------------------------------------------
    # COMPUTES
    # ---------------------------------------------------------

    @api.depends('unit_standards_line.selection', 'unit_standards_line.level3')
    def _compute_total_credits(self):
        for rec in self:
            rec.total_credits = sum(
                int(line.level3)
                for line in rec.unit_standards_line
                if line.selection and line.level3
            )

    # ---------------------------------------------------------
    # ONCHANGE LOGIC
    # ---------------------------------------------------------

    @api.onchange('learning_programme_id')
    def _onchange_learning_programme(self):
        if not self.learning_programme_id:
            return

        self.saqa_qual_id = self.learning_programme_id.saqa_qual_id
        self.qualification_id = self.learning_programme_id.qualification_id.id

        unit_lines = []
        for us in self.learning_programme_id.unit_standards_line:
            if us.selection:
                unit_lines.append((0, 0, {
                    'name': us.name,
                    'type': us.type,
                    'id_no': us.id_no,
                    'title': us.title,
                    'level1': us.level1,
                    'level2': us.level2,
                    'level3': us.level3,
                    'selection': True,
                    'seta_approved_lp': us.seta_approved_lp,
                    'provider_approved_lp': us.provider_approved_lp,
                }))

        self.unit_standards_line = unit_lines

    @api.onchange('assessor_no')
    def _onchange_assessor_no(self):
        if not self.assessor_no or not self.learning_programme_id:
            return

        assessor = self.env['hr.employee'].search([
            ('is_active_assessor', '=', True),
            ('assessor_seq_no', '=', self.assessor_no.strip())
        ], limit=1)

        if not assessor:
            self.assessor_no = False
            raise UserError(_('Invalid Assessor Number'))

        allowed_quals = assessor.qualification_ids.mapped('qualification_hr_id').ids
        if self.learning_programme_id.qualification_id.id not in allowed_quals:
            self.assessor_no = False
            raise UserError(_('Assessor not linked to this Learning Programme'))

        self.assessors_id = assessor.id

    @api.onchange('moderator_no')
    def _onchange_moderator_no(self):
        if not self.moderator_no or not self.learning_programme_id:
            return

        moderator = self.env['hr.employee'].search([
            ('is_active_moderator', '=', True),
            ('moderator_seq_no', '=', self.moderator_no.strip())
        ], limit=1)

        if not moderator:
            self.moderator_no = False
            raise UserError(_('Invalid Moderator Number'))

        allowed_quals = moderator.moderator_qualification_ids.mapped('qualification_hr_id').ids
        if self.learning_programme_id.qualification_id.id not in allowed_quals:
            self.moderator_no = False
            raise UserError(_('Moderator not linked to this Learning Programme'))

        self.moderators_id = moderator.id


class LearningProgrammeUnitStandardsAccreditationRel(models.Model):
    _name = 'learning.programme.unit.standards.accreditation.rel'
    _description = 'Learning Programme Unit Standards Accreditation'
    _rec_name = 'title'

    name = fields.Char(string='Name')

    type = fields.Selection(
        [
            ('Core', 'Core'),
            ('Fundamental', 'Fundamental'),
            ('Elective', 'Elective'),
        ],
        string='Type',
        required=True
    )

    id_no = fields.Char(string='ID No')
    title = fields.Char(string='Unit Standard Title', required=True)

    level1 = fields.Char(string='Pre-2009 NQF Level')
    level2 = fields.Char(string='NQF Level')
    level3 = fields.Char(string='Credits')

    selection = fields.Boolean(string='Selected', default=True)

    learning_programme_id = fields.Many2one(
        'learning.programme.accreditation.rel',
        string='Learning Programme',
        ondelete='cascade',
        required=True
    )

    seta_approved_lp = fields.Boolean(string='SETA Learning Material')
    provider_approved_lp = fields.Boolean(string='Provider Learning Material')


#################################################
## LEARNING PROGRAMME ACCREDITATION CAMPUS REL ##
#################################################


class LearningProgrammeAccreditationCampusRel(models.Model):
    _name = 'learning.programme.accreditation.campus.rel'
    _description = 'Learning Programme Accreditation Campus'

    saqa_qual_id = fields.Char(string='SAQA QUAL ID')

    learning_programme_id = fields.Many2one(
        'etqe.learning.programme',
        string='Learning Programme',
        required=True
    )

    unit_standards_line = fields.One2many(
        'lp.unit.standards.ac.rel',
        'learning_programme_id',
        string='Unit Standards'
    )

    learning_programme_accreditation_rel_id = fields.Many2one(
        'provider.accreditation.campus',
        string='Provider Accreditation Reference'
    )

    seta_approved_lp = fields.Boolean(string='SETA Learning Material')
    provider_approved_lp = fields.Boolean(string='Provider Learning Material')

    # ---------------------------------------------------------------------
    # Onchange
    # ---------------------------------------------------------------------
    @api.onchange('learning_programme_id')
    def _onchange_learning_programme_id(self):
        if not self.learning_programme_id:
            self.unit_standards_line = [(5, 0, 0)]
            self.saqa_qual_id = False
            return

        unit_standards_vals = []

        for us in self.learning_programme_id.unit_standards_line:
            if us.selection:
                unit_standards_vals.append(
                    (0, 0, {
                        'name': us.name,
                        'type': us.type,
                        'id_no': us.id_no,
                        'title': us.title,
                        'level1': us.level1,
                        'level2': us.level2,
                        'level3': us.level3,
                        'selection': True,
                        'seta_approved_lp': us.seta_approved_lp,
                        'provider_approved_lp': us.provider_approved_lp,
                    })
                )

        self.unit_standards_line = unit_standards_vals
        self.saqa_qual_id = self.learning_programme_id.saqa_qual_id


class LpUnitStandardsAccreditationCampusRel(models.Model):
    _name = 'lp.unit.standards.ac.rel'
    _description = 'Learning Programme Unit Standards Accreditation Campus'
    _rec_name = 'type'

    name = fields.Char(string='Name')

    type = fields.Selection(
        [
            ('Core', 'Core'),
            ('Fundamental', 'Fundamental'),
            ('Elective', 'Elective'),
        ],
        string='Type',
        required=True
    )

    id_no = fields.Char(string='ID NO')
    title = fields.Char(string='UNIT STANDARD TITLE', required=True)

    level1 = fields.Char(string='PRE-2009 NQF LEVEL')
    level2 = fields.Char(string='NQF LEVEL')
    level3 = fields.Char(string='CREDITS')

    selection = fields.Boolean(string='SELECT')

    learning_programme_id = fields.Many2one(
        'learning.programme.accreditation.campus.rel',
        string='Learning Programme Reference',
        ondelete='cascade'
    )

    seta_approved_lp = fields.Boolean(string='SETA Learning Material')
    provider_approved_lp = fields.Boolean(string='PROVIDER Learning Material')

from odoo import fields, models, api

# ---------------------------------------------------------
# Selection field (unchanged, still valid)
# ---------------------------------------------------------
GET_GENDERS = [
    ('am', 'African Male'),
    ('af', 'African Female'),
    ('ad', 'African Disabled'),
    ('cm', 'Coloured Male'),
    ('cf', 'Coloured Female'),
    ('cd', 'Coloured Disabled'),
    ('im', 'Indian Male'),
    ('if', 'Indian Female'),
    ('id', 'Indian Disabled'),
    ('wm', 'White Male'),
    ('wf', 'White Female'),
    ('wd', 'White Disabled'),
]

# ---------------------------------------------------------
# Helper Function (optional: move to utils.py)
# ---------------------------------------------------------
def get_occupation_and_specialization(ofo_code_data):
    data = []

    occupation = ofo_code_data.occupation or False
    data.append(occupation)

    specializations = ofo_code_data.specialize_ids
    if specializations:
        special_sub = ",".join(specializations.mapped('name'))
        data.append(special_sub)
    else:
        data.append(False)

    return data


# ---------------------------------------------------------
# Actual Training Model (Migrated)
# ---------------------------------------------------------
class ActualTrainingD1(models.Model):
    _name = 'actual.training.d1'
    _description = 'Actual Training D1'

    actual_training_fields_ids = fields.One2many(
        'actual.training.d1.fields',
        'actual_training_id',
        string='Actual Training D1'
    )

    related_wsp = fields.Many2one(
        'wsp.plan',
        string="Related WSP"
    )

    def action_save(self):
        """Replaces save_btn from Odoo 8"""
        self.ensure_one()

        active_id = self.env.context.get('active_id')
        if active_id:
            self.related_wsp = active_id

            self.env['wsp.plan'].browse(active_id).write({
                'actual_training_id': self.id
            })

        return {
            'name': 'WSP',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'wsp.plan',
            'res_id': active_id,
        }


class ActualTrainingD1Fields(models.Model):
    _name = 'actual.training.d1.fields'
    _description = 'Actual Training D1 Fields'

    name = fields.Char(string='First Name')
    surname = fields.Char(string='Surname')
    code = fields.Many2one('ofo.code', string='OFO')
    major = fields.Char(string='Major')
    sub_major_group = fields.Char(string='Sub Major Group')
    occupation = fields.Char(string='Occupation')
    specialization = fields.Many2one('specialize.subject', string='Specialisation')
    municipality = fields.Char(string='Municipality')
    urban = fields.Char(string='Urban')
    type_training = fields.Char(string='Type of Training Intervention')
    name_training = fields.Char(string='Name of Training Intervention')
    training_cost = fields.Float(string='Training Cost Per Learning')
    non_aligned = fields.Boolean(string='Non Aligned')
    nqf_level = fields.Char(string='NQF Level')
    gender = fields.Selection(GET_GENDERS, string='Gender')
    age_group = fields.Selection([
        ('less_than_thirty_five', '<35'),
        ('thirty_five_to_fifty_five', '35-55'),
        ('greater_than_fifty_five', '>55')
    ], string='Age Group')
    total_cost = fields.Float(string='Total Cost')

    actual_training_id = fields.Many2one(
        'actual.training.d1',
        string='Actual Training'
    )

    @api.onchange('code')
    def _onchange_code(self):
        if self.code:
            values = get_occupation_and_specialization(self.code)
            self.occupation = values[0] or False
            self.specialization = values[1] or False

## Wizard for Actual Adult Education.
class ActualAdultEducation(models.Model):
    _name = 'actual.adult.education'
    _description = 'Actual Adult Education'

    actual_adult_education_fields_ids = fields.One2many(
        'actual.adult.education.fields',
        'actual_adult_education_id',
        string='Actual Adult Education'
    )

    related_wsp = fields.Many2one('wsp.plan', string="Related WSP")

    def action_save(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')

        if active_id:
            self.related_wsp = active_id
            self.env['wsp.plan'].browse(active_id).write({
                'actual_adult_education_id': self.id
            })

        return {
            'name': 'WSP',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'wsp.plan',
            'res_id': active_id,
        }

class ActualAdultEducationFields(models.Model):
    _name = 'actual.adult.education.fields'
    _description = 'Actual Adult Education Fields'

    name = fields.Char(string='First Name')
    surname = fields.Char(string='Surname')
    id_number = fields.Char(string='Id Number')

    population_group = fields.Selection([
        ('african', 'African'),
        ('coloured', 'Coloured'),
        ('indian', 'Indian'),
        ('white', 'White')
    ], string='Population Group')

    gender = fields.Selection(GET_GENDERS, string='Gender')

    dissability_status_and_type = fields.Selection([
        ('unknown_dissability_status', 'Unknown Disability Status')
    ], string='Disability Status Type')

    learner_province = fields.Many2one('res.country.state', string='Learner Province')
    municipality = fields.Char(string='Municipality')
    urban = fields.Char(string='Urban')

    aet_start_date = fields.Date(string='AET Start Date')
    aet_end_date = fields.Date(string='AET End Date')

    provider = fields.Char(string='Provider')

    aet_level = fields.Selection([
        ('aet_level_1', 'AET Level 1')
    ], string='AET Level')

    aet_subject = fields.Selection([
        ('numeracy', 'Numeracy')
    ], string='AET Subject')

    free_text = fields.Char(string='Free Text')

    actual_adult_education_id = fields.Many2one(
        'actual.adult.education',
        string='Actual Adult Education'
    )

class ActualPivotalTraining(models.Model):
    _name = 'actual.pivotal.training'
    _description = 'Actual Pivotal Training'

    actual_pivotal_training_fields_ids = fields.One2many(
        'actual.pivotal.training.fields',
        'actual_pivotal_training_id',
        string='Actual Pivotal Training'
    )

    related_wsp = fields.Many2one('wsp.plan', string="Related WSP")

    def action_save(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')

        if active_id:
            self.related_wsp = active_id
            self.env['wsp.plan'].browse(active_id).write({
                'actual_pivotal_training_id': self.id
            })

        return {
            'name': 'WSP',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'wsp.plan',
            'res_id': active_id,
        }

class ActualPivotalTrainingFields(models.Model):
    _name = 'actual.pivotal.training.fields'
    _description = 'Actual Pivotal Training Fields'

    name = fields.Char(string='First Name')
    surname = fields.Char(string='Surname')
    ofo_code = fields.Many2one('ofo.code', string='OFO')

    major = fields.Char(string='Major')
    sub_major_group = fields.Char(string='Sub Major')
    occupation = fields.Char(string='Occupation')
    specialization = fields.Many2one('specialize.subject', string='Specialisation')

    socio_economic_status = fields.Selection([
        ('employed', 'Employed'),
        ('unemployed', 'Unemployed')
    ], string='Socio Economic Status')

    pivotal_programme_institution = fields.Char(string='Pivotal Programme Institution')
    pivotal_programme_qualification = fields.Char(string='Pivotal Programme Qualification')
    pivotal_programme_type = fields.Selection([
        ('academic', 'Academic')
    ], string='Pivotal Programme Type')

    cost = fields.Float(string='Cost')
    municipality = fields.Char(string='Municipality')
    urban = fields.Char(string='Urban')

    province = fields.Many2one('res.country.state', string='Province')

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    gender = fields.Selection(GET_GENDERS, string='Gender')
    total_person = fields.Integer(string='Total Person')

    age_group = fields.Selection([
        ('less_than_thirty_five', '<35'),
        ('thirty_five_to_fifty_five', '35-55'),
        ('greater_than_fifty_five', '>55')
    ], string='Age Group')

    total_cost = fields.Float(string='Total Cost')

    actual_pivotal_training_id = fields.Many2one(
        'actual.pivotal.training',
        string='Actual Pivotal Training'
    )

    @api.onchange('ofo_code')
    def _onchange_ofo_code(self):
        if self.ofo_code:
            values = get_occupation_and_specialization(self.ofo_code)
            self.occupation = values[0] or False
            self.specialization = values[1] or False

############# Planned Related Wizards ##############
class TotalEmploymentProfile(models.Model):
    _name = 'total.employment.profile'
    _description = 'Total Employment Profile'

    total_employment_profile_fields_ids = fields.One2many(
        'total.employment.profile.fields',
        'total_employment_profile_id',
        string='Total Employment Profile'
    )

    related_wsp = fields.Many2one('wsp.plan', string="Related WSP")

    def action_save(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')

        if active_id:
            self.related_wsp = active_id
            self.env['wsp.plan'].browse(active_id).write({
                'total_employment_profile_id': self.id
            })

        return {
            'name': 'WSP',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'wsp.plan',
            'res_id': active_id,
        }

class TotalEmploymentProfileFields(models.Model):
    _name = 'total.employment.profile.fields'
    _description = 'Total Employment Profile Fields'

    name = fields.Char(string='First Name')
    surname = fields.Char(string='Surname')
    ofo_code = fields.Many2one('ofo.code', string='OFO')

    occupation = fields.Char(string='Occupation')
    specialization = fields.Many2one('specialize.subject', string='Specialisation')

    municipality = fields.Char(string='Municipality')
    province = fields.Many2one('res.country.state', string='Province')

    urban = fields.Selection([
        ('urban', 'Urban'),
        ('rural', 'Rural')
    ], string='Urban/Rural')

    highest_education_level = fields.Char(string='Highest Education Level')
    scarce_skill = fields.Char(string='Scarce Skill')

    gender = fields.Selection(GET_GENDERS, string='Gender')

    age_group = fields.Selection([
        ('less_than_thirty_five', '<35'),
        ('thirty_five_to_fifty_five', '35-55'),
        ('greater_than_fifty_five', '>55')
    ], string='Age Group')

    total_employment_profile_id = fields.Many2one(
        'total.employment.profile',
        string='Total Employment Profile'
    )

    @api.onchange('ofo_code')
    def _onchange_ofo_code(self):
        if self.ofo_code:
            values = get_occupation_and_specialization(self.ofo_code)
            self.occupation = values[0] or False
            self.specialization = values[1] or False

class PlannedTrainingNonPivotal(models.Model):
    _name = 'planned.training.non.pivotal'
    _description = 'Planned Training Non Pivotal'

    planned_training_non_pivotal_fields_ids = fields.One2many(
        'planned.training.non.pivotal.fields',
        'planned_training_non_pivotal_id',
        string='Planned Training Non Pivotal'
    )

    related_wsp = fields.Many2one('wsp.plan', string="Related WSP")

    def action_save(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')

        if active_id:
            self.related_wsp = active_id
            self.env['wsp.plan'].browse(active_id).write({
                'planned_training_non_pivotal_id': self.id
            })

        return {
            'name': 'WSP',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'wsp.plan',
            'res_id': active_id,
        }

class PlannedTrainingNonPivotalFields(models.Model):
    _name = 'planned.training.non.pivotal.fields'
    _description = 'Planned Training Non Pivotal Fields'

    name = fields.Char(string='First Name')
    surname = fields.Char(string='Surname')

    type_of_training = fields.Selection([
        ('non_pivotal', 'Non Pivotal')
    ], string='Type Of Training')

    ofo_code = fields.Many2one('ofo.code', string='OFO')
    occupation = fields.Char(string='Occupation')
    specialization = fields.Many2one('specialize.subject', string='Specialisation')

    municipality = fields.Char(string='Municipality')
    province = fields.Many2one('res.country.state', string='Province')

    urban = fields.Selection([
        ('urban', 'Urban'),
        ('rural', 'Rural')
    ], string='Urban/Rural')

    socio_economic_status = fields.Selection([
        ('employed', 'Employed'),
        ('unemployed', 'Unemployed')
    ], string='Socio Economic Status')

    type_of_training_inter = fields.Char(string='Type of Training Intervention')
    name_of_training_inter = fields.Char(string='Name of Training Intervention')

    training_cost_per_learner = fields.Float(string='Training Cost Per Learner')
    nqf_aligned = fields.Boolean(string='NQF Aligned')
    nqf_level = fields.Char(string='NQF Level')

    gender = fields.Selection(GET_GENDERS, string='Gender')

    age_group = fields.Selection([
        ('less_than_thirty_five', '<35'),
        ('thirty_five_to_fifty_five', '35-55'),
        ('greater_than_fifty_five', '>55')
    ], string='Age Group')

    total_cost = fields.Float(string='Total Cost')

    planned_training_non_pivotal_id = fields.Many2one(
        'planned.training.non.pivotal',
        string='Planned Training Non Pivotal'
    )

    @api.onchange('ofo_code')
    def _onchange_ofo_code(self):
        if self.ofo_code:
            values = get_occupation_and_specialization(self.ofo_code)
            self.occupation = values[0] or False
            self.specialization = values[1] or False



class PlannedAdultEducationTraining(models.Model):
    _name = 'planned.adult.education.training'
    _description = 'Planned Adult Education Training'

    planned_adult_education_fields_ids = fields.One2many(
        'planned.adult.education.training.fields',
        'planned_adult_education_training_id',
        string='Planned Adult Education Training'
    )

    related_wsp = fields.Many2one('wsp.plan', string="Related WSP")

    def action_save(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')

        if active_id:
            self.related_wsp = active_id
            self.env['wsp.plan'].browse(active_id).write({
                'planned_adult_education_training_id': self.id
            })

        return {
            'name': 'WSP',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'wsp.plan',
            'res_id': active_id,
        }


class PlannedAdultEducationTrainingFields(models.Model):
    _name = 'planned.adult.education.training.fields'
    _description = 'Planned Adult Education Training Fields'

    name = fields.Char(string='First Name')
    surname = fields.Char(string='Surname')
    id_number = fields.Char(string='Id Number')

    population_group = fields.Selection([
        ('african', 'African'),
        ('coloured', 'Coloured'),
        ('indian', 'Indian'),
        ('white', 'White')
    ], string='Population Group')

    gender = fields.Selection(GET_GENDERS, string='Gender')

    dissability_status_and_type = fields.Selection([
        ('unknown', 'Unknown')
    ], string='Disability Status and Type')

    province = fields.Many2one('res.country.state', string='Learner Province')
    municipality = fields.Char(string='Municipality')

    urban = fields.Selection([
        ('urban', 'Urban'),
        ('rural', 'Rural')
    ], string='Urban/Rural')

    start_date = fields.Date(string='AET Start Date')
    end_date = fields.Date(string='AET End Date')

    provider = fields.Char(string='Provider')

    aet_level = fields.Selection([
        ('aet_level_1', 'AET Level 1')
    ], string='AET Level')

    aet_subject = fields.Selection([
        ('numeracy', 'Numeracy')
    ], string='AET Subject')

    reason = fields.Char(string='Reason')

    planned_adult_education_training_id = fields.Many2one(
        'planned.adult.education.training',
        string='Planned Adult Education Training'
    )

class ScarceAndCriticalSkills(models.Model):
    _name = 'scarce.and.critical.skills'
    _description = 'Scarce and Critical Skills'

    scarce_and_critical_skills_fields_ids = fields.One2many(
        'scarce.and.critical.skills.fields',
        'scarce_and_critical_skills_id',
        string='Scarce and Critical Skills'
    )

    related_wsp = fields.Many2one('wsp.plan', string="Related WSP")

    def action_save(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')

        if active_id:
            self.related_wsp = active_id
            self.env['wsp.plan'].browse(active_id).write({
                'scarce_and_critical_skills_id': self.id
            })

        return {
            'name': 'WSP',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'wsp.plan',
            'res_id': active_id,
        }


class ScarceAndCriticalSkillsFields(models.Model):
    _name = 'scarce.and.critical.skills.fields'
    _description = 'Scarce and Critical Skills Fields'

    name = fields.Char(string='First Name')
    surname = fields.Char(string='Surname')

    ofo_code = fields.Many2one('ofo.code', string='OFO')
    occupation = fields.Char(string='Occupation')
    specialization = fields.Many2one(
        'specialize.subject',
        string='Specialisation'
    )

    scarce_skill = fields.Char(string='Scarce Skills')
    critical_skill = fields.Char(string='Critical Skills')

    number_of_vacancies = fields.Integer(string='Number Of Vacancies')
    number_of_potential_vacancies = fields.Integer(
        string='Number Of Potential Vacancies'
    )

    nqf_level = fields.Char(string='NQF Level')
    degree_of_scarcity = fields.Char(string='Degree of Scarcity')
    reason_for_scarcity = fields.Char(
        string='Reason for Scarcity / Critical'
    )

    gender = fields.Selection(GET_GENDERS, string='Gender')

    planned_strategy_address = fields.Char(
        string='Planned Strategy to address the scarcity'
    )

    province = fields.Many2one(
        'res.country.state',
        string='Province'
    )

    is_reflected = fields.Boolean(
        string='Is this reflected to your EE Plan?'
    )

    comments = fields.Char(string='Comments')

    scarce_and_critical_skills_id = fields.Many2one(
        'scarce.and.critical.skills',
        string='Scarce and Critical Skills'
    )

    @api.onchange('ofo_code')
    def _onchange_ofo_code(self):
        if self.ofo_code:
            values = get_occupation_and_specialization(self.ofo_code)
            self.occupation = values[0] or False
            self.specialization = values[1] or False
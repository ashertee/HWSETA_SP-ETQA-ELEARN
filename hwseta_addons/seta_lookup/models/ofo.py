from odoo import fields, models, api, _
import pandas as pd
DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(*args):
        logger.info("".join([str(a) for a in args]))

else:

    def dbg(*args):
        pass

class OfoCodeSpecialisationsLookup(models.Model):
    _name = "ofo.code.specialisation.lookup"

    name = fields.Char()

class OfoCodeOccupationLookup(models.Model):
    _name = "ofo.code.occupation.lookup"

    name = fields.Char()

class OfoCodeLookup(models.Model):
    _name = "ofo.code.lookup"

    name = fields.Char()
    ofo_code = fields.Char()
    ofo_year = fields.Char()
    occupation = fields.Char()
    trade = fields.Boolean()
    green_skill = fields.Boolean()
    green_occupation = fields.Boolean()

    specialisation = fields.Many2many('ofo.code.specialisation.lookup')

    def action_import_ofo_lookup(self):
        record_template = """
<odoo>
    <data noupdate="1">

        <record id="specialisation_{{ specialisation_id }}" model="ofo.code.specialisation.lookup">
            <field name="name">{{ specialisation_name }}</field>
        </record>

        <record id="occupation_{{ occupation_id }}" model="ofo.code.occupation.lookup">
            <field name="name">{{ occupation_name }}</field>
        </record>

        <record id="ofo_code_{{ ofo_code_id }}" model="ofo.code.lookup">
            <field name="name">{{ ofo_code_name }}</field>
            <field name="ofo_code">{{ ofo_code }}</field>
            <field name="ofo_year">{{ ofo_year }}</field>
            <field name="occupation" eval="[(6, 0, [ref('occupation_{{ occupation_id }}')])]" />
            <field name="specialisation" eval="[(6, 0, [ref('specialisation_{{ specialisation_id }}')])]" />
        </record>

    </data>
</odoo>
        """
        ofo_template = """
        <record id="ofo_code_{{ ofo_code_id }}" model="ofo.code.lookup">
            <field name="name">{{ ofo_code_name }}</field>
            <field name="ofo_code">{{ ofo_code }}</field>
            <field name="ofo_year">{{ ofo_year }}</field>
            <field name="occupation" eval="[(6, 0, [ref('occupation_{{ occupation_id }}')])]" />
            <field name="specialisation" eval="[(6, 0, [ref('specialisation_{{ specialisation_id }}')])]" />
        </record>
        """
        occupation_template = """
        <record id="occupation_{{ occupation_id }}" model="ofo.code.occupation.lookup">
            <field name="name">{{ occupation_name }}</field>
        </record>
        """
        specialisation_template = """
        <record id="specialisation_{{ specialisation_id }}" model="ofo.code.specialisation.lookup">
            <field name="name">{{ specialisation_name }}</field>
        </record>
        """
        file_path = "/var/lib/odoo/ofo.xlsx"
        all_sheets = {}
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            for sheet_name in sheet_names:
                df = excel_file.parse(sheet_name)
                all_sheets[sheet_name] = df

        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")
            #ofos = pd.read_excel("/var/lib/odoo/ofo.xlsx")
            #raise UserError(ofos)

        #import specialisations
        for a in all_sheets['Specialisations']:
            a["specialisation_id"] = a["Description"].replace(" ","_").lower()
            a["specialisation_name"] = a["Description"].replace(" ","_").lower()



        #import occupations

        #import ofos


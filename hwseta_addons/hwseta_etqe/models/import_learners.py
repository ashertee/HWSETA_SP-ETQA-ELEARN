from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import xlrd
import datetime
import logging

_logger = logging.getLogger(__name__)


class ImportLearnersTemplate(models.TransientModel):
    _name = "import.learners.template"
    _description = "Import Learners Template"

    learner_file = fields.Binary(string="Upload Learners File", required=True)

    def validate_id_number(self, id_number):
        """
        Normalize ID numbers coming from Excel (float / string)
        """
        if id_number is None:
            return False

        if isinstance(id_number, float):
            id_number = int(id_number)

        id_number = str(id_number).strip()
        return id_number

    def validate_long_number(self, number):
        """
        Normalize long numeric values from Excel
        """
        if number is None:
            return False

        _logger.info("Type of number: %s", type(number))

        if isinstance(number, float):
            number = int(number)

        number = str(number).split(".")[0].strip()
        return number

    def get_genders(self, gender_value):
        """
        Map Excel gender values to system gender
        """
        gender = False
        if not gender_value:
            return gender

        gender_value = str(gender_value).strip().lower()
        _logger.info("Gender value: %s", gender_value)

        if gender_value in ["m - male", "male", "m"]:
            gender = "male"
        elif gender_value in ["f - female", "female", "f"]:
            gender = "female"

        return gender

    def validate_date(self, input_date, workbook):
        """
        Convert Excel date or string date to proper date
        """
        try:
            if isinstance(input_date, str):
                return datetime.datetime.strptime(input_date, "%d/%m/%Y").date()

            if isinstance(input_date, float):
                return datetime.datetime(
                    *xlrd.xldate_as_tuple(input_date, workbook.datemode)
                ).date()

        except Exception as e:
            _logger.warning("Date conversion failed: %s", e)

        return False

    def get_gender_saqa_code(self, gender_saqa_value):
        """
        Map SAQA gender codes
        """
        if not gender_saqa_value:
            return False

        gender = str(gender_saqa_value).strip().lower()

        if gender == "m":
            return "m"
        if gender == "f":
            return "f"

        return False

    def get_disability_status(self, disability_value):
        """
        Map disability values to internal codes
        """
        if not disability_value:
            return False

        disability_map = {
            "sight ( even with glasses )": "sight",
            "hearing ( even with h.aid )": "hearing",
            "communication ( talk/listen)": "communication",
            "physical ( move/stand, etc)": "physical",
            "intellectual ( learn,etc)": "intellectual",
            "emotional ( behav/psych)": "emotional",
            "multiple": "multiple",
            "disabled but unspecified": "disabled",
            "none": "none",
        }

        key = str(disability_value).strip().lower()
        return disability_map.get(key, False)

    def get_equity(self, race_value):
        """
        Map race/equity values
        """
        if not race_value:
            return False

        race_map = {
            "black: african": "black_african",
            "black: indian / asian": "black_indian",
            "black: coloured": "black_coloured",
            "indian": "indian",
            "white": "white",
            "other": "other",
            "unknown": "unknown",
        }

        key = str(race_value).strip().lower()
        return race_map.get(key, False)

    def get_language(self, lang_value):
        """
        Get language ID from res.lang
        """
        if not lang_value:
            return False

        lang = self.env["res.lang"].search(
            [("name", "=", str(lang_value).strip())], limit=1
        )
        return lang.id if lang else False

    def get_country(self, country_value):
        if not country_value:
            return False

        country = self.env["res.country"].search(
            [("name", "=", str(country_value).strip())], limit=1
        )
        return country.id if country else False

    def get_province(self, province_value):
        if not province_value:
            return False

        province = self.env["res.country.state"].search(
            [("name", "=", str(province_value).strip())], limit=1
        )
        return province.id if province else False

    def get_city(self, city_value):
        if not city_value:
            return False

        city = self.env["res.city"].search(
            [("name", "=", str(city_value).strip())], limit=1
        )
        return city.id if city else False

    def get_suburb(self, suburb_value):
        if not suburb_value:
            return False

        suburb = self.env["res.suburb"].search(
            [("name", "=", str(suburb_value).strip())], limit=1
        )
        return suburb.id if suburb else False

    def get_municipality(self, municipality_value):
        if not municipality_value:
            return False

        municipality = self.env["res.municipality"].search(
            [("name", "=", str(municipality_value).strip())], limit=1
        )
        return municipality.id if municipality else False

    def import_learners(self):
        if not self.learner_file:
            raise UserError(_("Please upload a file."))

        try:
            learner_data = base64.b64decode(self.learner_file)
            workbook = xlrd.open_workbook(file_contents=learner_data)
        except Exception as e:
            raise UserError(_("Invalid Excel file format.\n%s") % e)

        sheet = workbook.sheet_by_index(0)

        learner_obj = self.env["learner.registration"]
        hr_employee = self.env["hr.employee"]
        batch_obj = self.env["batch.master"]

        for row_idx in range(1, sheet.nrows):
            row = sheet.row(row_idx)

            # Skip blank rows
            if not any(col.value for col in row):
                continue

            # ---------- BASIC NORMALIZATION ----------
            id_number = self.validate_id_number(row[30].value)
            if not id_number:
                continue

            gender = self.get_genders(str(row[20].value))
            gender_saqa_code = self.get_gender_saqa_code(str(row[21].value))
            disability_status = self.get_disability_status(str(row[24].value))
            equity = self.get_equity(str(row[37].value))
            language = self.get_language(str(row[36].value))
            country_of_nationality = self.get_country(str(row[29].value))

            work_phone = self.validate_long_number(row[6].value)
            cell = self.validate_long_number(row[39].value)
            fax = self.validate_long_number(row[40].value)

            # ---------- EXISTING LEARNER CHECK ----------
            existing = hr_employee.search(
                [("learner_identification_id", "=", id_number)], limit=1
            )

            vals = {
                "is_existing_learner": bool(existing),
                "identification_id": id_number,
                "name": str(row[1].value),
                "middle_name": str(row[2].value),
                "person_last_name": str(row[4].value),
                "gender": gender,
                "gender_saqa_code": gender_saqa_code,
                "disability_status": disability_status,
                "equity": equity,
                "home_language_code": language,
                "country_id": country_of_nationality,
                "cell": cell,
                "work_phone": work_phone,
                "person_fax_number": fax,
                "is_learner": True,
                "provider_learner": True,
                "learner_status": "Enrolled",
                "seta_elements": True,
            }

            learner = learner_obj.create(vals)

            # ---------- BATCH PROCESSING ----------
            batch_code = str(row[68].value).strip()
            batch = batch_obj.search(
                [("batch_id", "=", batch_code), ("batch_status", "=", "open")], limit=1
            )

            if not batch:
                continue

            start_date = self.validate_date(row[69].value, workbook)
            end_date = self.validate_date(row[70].value, workbook)

            assessor = self.env["hr.employee"].search(
                [
                    (
                        "assessor_moderator_identification_id",
                        "=",
                        str(row[71].value).strip(),
                    )
                ],
                limit=1,
            )
            moderator = self.env["hr.employee"].search(
                [
                    (
                        "assessor_moderator_identification_id",
                        "=",
                        str(row[75].value).strip(),
                    )
                ],
                limit=1,
            )

            # ---------- QUALIFICATION ----------
            if batch.qual_skill_batch == "qual":
                self.env["learner.registration.qualification"].create(
                    {
                        "learner_qualification_id": learner.id,
                        "learner_qualification_parent_id": batch.qualification_id.id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "assessors_id": assessor.id if assessor else False,
                        "moderators_id": moderator.id if moderator else False,
                        "batch_id": batch.id,
                    }
                )

            # ---------- SKILL PROGRAMME ----------
            elif batch.qual_skill_batch == "skill":
                self.env["skills.programme.learner.rel"].create(
                    {
                        "skills_programme_learner_rel_id": learner.id,
                        "skills_programme_id": batch.skills_programme_id.id,
                        "start_date": start_date,
                        "end_date": end_date,
                        "assessors_id": assessor.id if assessor else False,
                        "moderators_id": moderator.id if moderator else False,
                        "batch_id": batch.id,
                    }
                )

            # ---------- LEARNING PROGRAMME ----------
            elif batch.qual_skill_batch == "lp":
                lp = self.env["learning.programme.learner.rel"].create(
                    {
                        "learning_programme_learner_rel_id": learner.id,
                        "learning_programme_id": batch.learning_programme_id.id,
                        "lp_saqa_id": batch.learning_programme_id.code,
                        "start_date": start_date,
                        "end_date": end_date,
                        "assessors_id": assessor.id if assessor else False,
                        "moderators_id": moderator.id if moderator else False,
                        "batch_id": batch.id,
                    }
                )

                for unit in batch.learning_programme_id.unit_standards_line.filtered(
                    "selection"
                ):
                    self.env["learning.programme.unit.standards.learner.rel"].create(
                        {
                            "learning_programme_id": lp.id,
                            "id_no": unit.id_no,
                            "type": unit.type,
                            "title": unit.title,
                            "level1": unit.level1,
                            "level2": unit.level2,
                            "level3": unit.level3,
                            "selection": True,
                            "seta_approved_lp": unit.seta_approved_lp,
                        }
                    )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Import Complete"),
                "message": _("Learners imported successfully."),
                "type": "success",
                "sticky": False,
            },
        }

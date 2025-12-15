from odoo import api, fields, models, _
import re

DEBUG = True

if DEBUG:
    import logging

    logger = logging.getLogger(__name__)

    def dbg(msg):
        logger.info(msg)

else:

    def dbg(msg):
        pass


class SetaMap(models.Model):
    _name = "seta.map"

    name = fields.Char()
    odoo_model = fields.Char()
    setmis_version = fields.Char()
    nlrd_version = fields.Char()
    line_ids = fields.One2many("seta.map.line", "map_id")


class SetaMapLine(models.Model):
    _name = "seta.map.line"
    _rec_name = "odoo_field"

    odoo_field = fields.Char()
    seq_setmis = fields.Integer()
    seq_nlrd = fields.Integer()
    setmis_position = fields.Integer()
    nlrd_position = fields.Integer()
    odoo_label = fields.Char()
    data_classification = fields.Char()
    odoo_field_type = fields.Char()
    odoo_description = fields.Char()
    setmis_description = fields.Char()
    nlrd_description = fields.Char()
    setmis_field = fields.Char()
    setmis_len = fields.Integer()
    nlrd_field = fields.Char()
    nlrd_len = fields.Integer()
    model_id = fields.Char()
    map_id = fields.Many2one("seta.map")
    # seta_id = fields.char()
    validation_ids = fields.Many2many("seta.map.line.validation")


class SetaMapValidationType(models.Model):
    _name = "seta.map.line.validation.type"

    name = fields.Char()


class SetaMapLineValidation(models.Model):
    _name = "seta.map.line.validation"

    name = fields.Char()
    validation_type = fields.Many2one("seta.map.line.validation.type")
    validation_value = fields.Char()
    business_validation_value = fields.Char()
    error_message = fields.Text()
    business_error_message = fields.Text()
    system_applied = fields.Selection(
        string="system_applied", selection=[("nlrd", "nlrd"), ("setmis", "setmis")]
    )


    def validation_call(self, record_id, val):
        record = self.browse(record_id)
        if not (record and val):
            return False, False, False

        dbg(f"This is the value: {val}")
        dbg("Inside the validation call method")
        dbg(f"Validation value: {record.validation_value}")
        dbg(f"Validation Type: {record.validation_type.name}")

        if record.validation_value and record.validation_type:
            unique_validation_name = f"{record.validation_type.name}:{val}"
            pattern = record.validation_value
            bus_pattern = record.business_validation_value
            res = None
            bus_res = None

            if record.validation_type.name == "regex findall not in":
                res = bool(re.findall(pattern, val))
                if bus_pattern:
                    bus_res = bool(re.findall(bus_pattern, val))

            elif record.validation_type.name == "regex match":
                res = re.match(pattern, val)
            elif record.validation_type.name == "regex full match":
                res = re.fullmatch(pattern, val)
            else:
                raise Warning("Unsupported validation type")

            if res if record.validation_type.name == "regex findall not in" else not res:
                return (
                    True,
                    f"{record.error_message}",
                    unique_validation_name,
                )

            if bus_res:
                if record.validation_type.name == "regex findall not in":
                    return (
                        True,
                        f"{record.business_error_message}",
                        unique_validation_name,
                    )

        return False, False, False

    def validatate(self, record_id, val):
        record = self.browse(record_id)
        if not (record and val):
            return False, False, False

        if record.validation_value and record.validation_type:
            unique_validation_name = f"{record.validation_type.name}:{val}"
            pattern = record.validation_value
            bus_pattern = record.business_validation_value
            res = None
            bus_res = None

            if record.validation_type.name == "regex findall not in":
                res = bool(re.findall(pattern, val))
                if bus_pattern:
                    bus_res = bool(re.findall(bus_pattern, val))

            elif record.validation_type.name == "regex match":
                res = re.match(pattern, val)
            elif record.validation_type.name == "regex full match":
                res = re.fullmatch(pattern, val)
            else:
                raise Warning("Unsupported validation type")
            
            if bus_res:
                return (
                    True,
                    f"{record.business_error_message}",
                    unique_validation_name,
                )
            
            if res and record.validation_type.name == "regex findall not in":
                return (
                    True,
                    f"{record.error_message}",
                    unique_validation_name,
                )
            
            if res:
                if record.validation_type.name == "regex match":
                    return (
                        True,
                        f"{record.error_message}",
                        unique_validation_name,
                    )
            if not res:
                 if record.validation_type.name == "regex full match":
                    return (
                        True,
                        f"{record.error_message}",
                        unique_validation_name,
                    )
        
        return False, False, False
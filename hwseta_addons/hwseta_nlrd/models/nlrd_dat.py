import re
import os
import logging
from collections import OrderedDict as OD

_logger = logging.getLogger(__name__)

dat21 = [[20, 10, 10, 128, 10, 50, 50, 50, 4, 20, 20, 20, 50, 50, 20, 20, 20, 8, 8, 20, 10, 10, 2, 4, 3, 2, 6, 2, 2, 6, 50, 50, 50, 4, 50, 8],
         ['Provider_Code', 'Etqa_Id', 'Std_Industry_Class_Code', 'Provider_Name', 'Provider_Type_Id', 'Provider_Address_1', 'Provider_Address_2', 'Provider_Address_3', 'Provider_Postal_Code', 'Provider_Phone_Number', 'Provider_Fax_Number', 'Provider_Sars_Number', 'Provider_Contact_Name', 'Provider_Contact_Email_Address', 'Provider_Contact_Phone_Number', 'Provider_Contact_Cell_Number', 'Provider_Accreditation_Num', 'Provider_Accredit_Start_Date', 'Provider_Accredit_End_Date', 'Etqa_Decision_Number', 'Provider_Class_Id', 'Structure_Status_Id', 'Province_Code', 'Country_Code', 'Latitude_Degree', 'Latitude_Minutes', 'Latitude_Seconds', 'Longitude_Degree', 'Longitude_Minutes', 'Longitude_Seconds', 'Provider_Physical_Address_1', 'Provider_Physical_Address_2', 'Provider_Physical_Address_Town', 'Provider_Phys_Address_Postcode', 'Provider_Web_Address', 'Date_Stamp']]

dat24 = [[10, 10, 10, 20, 10, 20, 1, 8, 8, 20, 10, 8],
         ['Learnership_Id', 'Qualification_Id', 'Unit_Standard_Id', 'Provider_Code', 'Provider_Etqa_Id', 'Provider_Accreditation_Num', 'Provider_Accredit_Assessor_Ind', 'Provider_Accred_Start_Date', 'Provider_Accred_End_Date', 'Etqa_Decision_Number', 'Provider_Accred_Status_Code', 'Date_Stamp']]

dat25 = [[15, 20, 3, 10, 3, 10, 1, 10, 2, 10, 45, 26, 50, 10, 8, 50, 50, 50, 50, 50,
		  50, 4, 4, 20, 20, 20, 50, 2, 20, 10, 45, 20, 3, 20, 10, 2, 2, 2, 2, 2, 2, 8, ], ['National_Id',  # c
																							   'Person_Alternate_Id',
																							   'Alternate_Id_Type',
																							   'Equity_Code',  # y
																							   'Nationality_Code',  # y
																							   'Home_Language_Code',
																							   'Gender_Code',  # y
																							   'Citizen_Resident_Status_Code',
																							   'Socioeconomic_Status_Code',
																							   'Disability_Status_Code',
																							   'Person_Last_Name',  # y
																							   'Person_First_Name',  # y
																							   'Person_Middle_Name',
																							   'Person_Title',
																							   'Person_Birth_Date',
																							   'Person_Home_Address_1',
																							   'Person_Home_Address_2',
																							   'Person_Home_Address_3',
																							   'Person_Postal_Address_1',
																							   'Person_Postal_Address_2',
																							   'Person_Postal_Address_3',
																							   'Person_Home_Addr_Postal_Code',
																							   'Person_Postal_Addr_Post_Code',
																							   'Person_Phone_Number',
																							   'Person_Cell_Phone_Number',
																							   'Person_Fax_Number',
																							   'Person_Email_Address',
																							   'Province_Code',  # y
																							   'Provider_Code',  # c
																							   'Provider_Etqa_Id',
																							   'Person_Previous_Provider_Lastname',
																							   'Person_Previous_Alternate_Id',
																							   'Person_Previous_Alternate_Id_Type',
																							   'Person_Previous_Provider_Code',
																							   'Person_Previous_Provider_Etqe_Id',
																							   'Seeing_Rating_Id',
																							   'Hearing_Rating_Id',
																							   'Communicating_Rating_Id',
																							   'Walking_Rating_Id',
																							   'Remembering_Rating_Id',
																							   'Self_Care_Rating_Id',
																							   'Date_Stamp',  # y
																							   ]]

dat26 = [[15, 20, 3, 5, 20, 10, 8, 8, 10, 20, 20, 10, 8, ], ['National_Id',
															 'Person_Alternate_Id',
															 'Alternate_Type_Id',
															 'Designation_Id',  # blanket
															 'Designation_Registration_Number',
															 'Designation_Etqa_Id',  # blanket
															 'Designation_Start_Date',
															 'Designation_End_Date',
															 'Structure_Status_Id',  # blanket
															 'Etqa_Decision_Number',  # blank
															 'Provider_Code',
															 'Provider_Etqa_Id',
															 'Date_Stamp', ]]

dat27 = [[10, 10, 10, 5, 20, 10, 8, 8, 20, 10, 8, ], ['Learnership_Id',
													  'Qualification_Id',
													  'Unit_Standard_Id',
													  'Designation_Id',  # blanket req
													  'Designation_Registration_Number',  # req
													  'Designation_Etqa_Id',  # req blanket
													  'Nqf_Designation_Start_Date',  # req
													  'Nqf_Designation_End_Date',  # req
													  'Etqa_Decision_Number',
													  'Nqf_Desig_Status_Code',  # req
													  'Date_Stamp',  # req
													  ]]

dat29 = [[15, 20, 3, 10, 3, 20, 3, 8, 8, 3, 2, 10, 20, 10, 10, 8, 8, ], ['national_id',
																		 'person_alternate_id',
																		 'alternate_id_type',
																		 'qualification_id',
																		 'learner_achievement_status_id',
																		 'assessor_registration_number',
																		 'learner_achievement_type_id',
																		 # todo: find or pass flat value 6 is  other
																		 'learner_achievement_date',
																		 # todo:needs eval based on learner_achievement_type_id
																		 'learner_enrolled_date',
																		 'honours_classification',  # not req
																		 'part_of',
																		 'learnership_id',  # not req
																		 'provider_code',
																		 'provider_etqa_id',  # blanket
																		 'assessor_etqa_id',  # blanket
																		 'certification_date',
																		 'date_stamp', ]]

def replace_unicode_with_normal(text):
    if not text:
        return ""
    unimap = {
        "ß": "b", "à": "a", "á": "a", "â": "a", "ã": "a", "ä": "a", "å": "a", "æ": "ae", "ç": "c",
        "è": "e", "é": "e", "ê": "e", "ë": "e", "ì": "i", "í": "i", "î": "i", "ï": "i", "ð": "o",
        "ñ": "n", "ò": "o", "ó": "o", "õ": "o", "ö": "o", "ø": "o", "ù": "u", "ú": "u",
        "û": "u", "ü": "u", "ý": "y", "þ": "b", "ÿ": "y",
    }
    for key, val in unimap.items():
        text = text.replace(key, val)
    # Remove any remaining non-ascii characters
    return text.encode("ascii", "ignore").decode("ascii")


def gendat(vald, lens, fields_list, datfile_name):
    """
    Generates fixed-width DAT files.
    """
    # Define file path - Use Odoo data directory or a configurable parameter
    output_dir = "/var/log/odoo/nlrd_dat_files/"
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            _logger.error(f"Could not create directory {output_dir}: {e}")
            return

    line_content = ""
    for i, field in enumerate(fields_list):
        width = lens[i]
        # Get value and handle None/False
        raw_value = vald.get(field, "")
        if raw_value is False or raw_value is None:
            raw_value = ""

        # Convert to string and clean unicode
        value = replace_unicode_with_normal(str(raw_value))

        # Format as fixed width: left aligned, truncated if too long
        formatted_value = f"{value[:width]:<{width}}"
        line_content += formatted_value

    line_content += "\r\n"

    file_path = os.path.join(output_dir, datfile_name)
    mode = 'a' if os.path.exists(file_path) else 'w'

    with open(file_path, mode, encoding='ascii') as f:
        f.write(line_content)


import pandas as pd
import psycopg2
import os
import time
def logman(text, logger=False):
    if logger == True:
        print (time.time())
        print(text)
    else:
        pass

class ImportTool:
    def __init__(self, sheet, rec, dbn):
        self.sheet = sheet
        self.rec = rec

        pwf = os.environ["PASSWORD_FILE"]
        with open(pwf,'r') as f:
            password = f.read()

        dbname = dbn
        user = "odoo"
        host = "db"
        port = "5432"

        try: 
            conn = psycopg2.connect(f"dbname={dbname} user={user} password={password} host={host} port={port}")
        except Exception as e:
            conn = psycopg2.connect(f"dbname={dbname} user={user} password={password} host=localhost port={port}")
        cur = conn.cursor()
        cur.execute("SELECT * FROM equity_code")
        races = cur.fetchall()
        cur.execute("SELECT * FROM gender_code")
        genders = cur.fetchall()
        cur.execute("SELECT * FROM citizen_resident_status_code")
        citizens = cur.fetchall()
        cur.execute("SELECT * FROM alternate_id_type_id")
        idtypes = cur.fetchall()
        cur.execute("SELECT * FROM res_city")
        cities = cur.fetchall()
        cur.execute("SELECT * FROM province_code")
        provinces = cur.fetchall()
        cur.execute("SELECT * FROM urban_rural_id")
        urbans = cur.fetchall()
        cur.execute("SELECT * FROM highest_education")
        highests = cur.fetchall()
        highest_map = {}
        for r in highests:
            highest_map[r[3].upper()] = str(r[0])
            highest_map[r[3].lower()] = str(r[0])
            highest_map[r[3].title()] = str(r[0])
        urban_map = {}
        for r in urbans:
            urban_map[r[3].upper()] = str(r[0])
            urban_map[r[3].lower()] = str(r[0])
            urban_map[r[3].title()] = str(r[0])

        province_map = {}
        for r in provinces:
            province_map[r[8].upper()] = str(r[0])
            province_map[r[8].lower()] = str(r[0])
            province_map[r[8].title()] = str(r[0])
        city_map = {}
        for r in city_map:
            city_map[r[8].upper()] = str(r[0])
            city_map[r[8].lower()] = str(r[0])
            city_map[r[8].title()] = str(r[0])
        id_map = {}
        for r in idtypes:
            id_map[r[3].upper()] = str(r[0])
            id_map[r[3].lower()] = str(r[0])
            id_map[r[3].title()] = str(r[0])
        citizen_map = {}
        for r in citizens:
            citizen_map[r[3].upper()] = str(r[0])
            citizen_map[r[3].lower()] = str(r[0])
            citizen_map[r[3].title()] = str(r[0])
        gender_map = {}
        for r in genders:
            gender_map[r[3].upper()] = str(r[0])
            gender_map[r[3].lower()] = str(r[0])
            gender_map[r[3].title()] = str(r[0])
        race_map = {}
        for r in races:
            race_map[r[3].upper()] = str(r[0])
            race_map[r[3].lower()] = str(r[0])
            race_map[r[3].title()] = str(r[0])
        cur.close()
        conn.close()
        self.province_map = province_map
        self.city_map = city_map
        self.id_map = id_map
        self.gender_map = gender_map
        self.race_map = race_map
        self.citizen_map = citizen_map
        self.urban_map = urban_map
        self.highest_map = highest_map

    def get_urban(self, r):
        try:
            return self.urban_map[r]
        except KeyError:
            return self.get_urban("Unknown")
        finally:
            return 1

    def get_highest(self, r):
        try:
            return self.highest_map[r]
        except KeyError:
            return self.get_highest("Unknown")
        finally:
            return 1

    def get_province(self, r):
        try:
            return self.province_map[r]
        except KeyError:
            return 1 #self.get_province("Unknown")
        finally:
            return 1

    def get_city(self, r):
        try:
            return self.city_map[r]
        except KeyError:
            return 1 #self.get_city("Unknown")
        finally:
            return 1

    def get_citizen(self, r):
        try:
            return self.citizen_map[r]
        except KeyError:
            return self.get_citizen("Unknown")

    def get_id(self, r):
        try:
            return self.id_map[r]
        except KeyError:
            return self.get_id("Unknown")

    def get_race(self, r):
        try:
            return self.race_map[r]
        except KeyError:
            return self.get_race("Unknown")

    def get_gender(self, r):
        if r == "Unknown":
            return "1"
        try:
            return self.gender_map[r]
        except KeyError:
            return self.get_gender("Unknown")

    def import_tep(self):
        #print(self.sheet, self.rec)
        df = pd.read_excel(self.sheet)
        logman("ID Type...", True)
        df['ID Type'] = [self.get_id(r) for r in list(df['ID Type'])]
        logman("Citizen...", True)
        df['Citizen Status'] = [self.get_citizen(r) for r in list(df['Citizen Status'])]
        logman("Urban...", True)
        df['Urban / Rural'] = [self.get_urban(r) for r in list(df['Urban / Rural'])]
        logman("City...", True)
        df['City'] = [self.get_city(r) for r in list(df['City'])]
        logman("Highest Education Level...", True)
        df['Highest Education Level'] = [self.get_highest(r) for r in list(df['Highest Education Level'])]
        logman("Province...", True)
        df['Province'] = [self.get_province(r) for r in list(df['Province'])]
        logman("Race...", True)
        df['Race'] = [self.get_race(r) for r in list(df['Race'])]
        logman("Gender...", True)
        df['Gender'] = [self.get_gender(r) for r in list(df['Gender'])]
        logman("Name...", True)
        df['Name'] = [str(r).title() for r in list(df['Name'])]
        logman("Rec...", True)
        df['Rec'] = "{'sdl_number': '" + df["SDL_Number"].astype(str) +"', 'name': '"+ df["Name"].astype(str)+"', 'last_name': '"+	df["Last Name"].astype(str) +"', 'citizen_resident_status_code': "+	df["Citizen Status"].astype(str)+", 'id_type': "+df["ID Type"].astype(str)+", 'employee_id': '"+df["Employee ID"].astype(str)+"', 'date_of_birth': '"+df["Date of Birth"].astype(str)+"','ofo_code': '"+  df["OFO Code"].astype(str)+"', 'occupation': '"	+df["Occupation"].astype(str)+"', 'specialisation': '"+df["Specialization"].astype(str)+"', 'province': "	+df["Province"].astype(str)+ ", 'city': "+	df["City"].astype(str)+", 'urban_rural':"	+df["Urban / Rural"].astype(str)	+",'highest_education':"+df["Highest Education Level"].astype(str)	+", 'race': "+df["Race"].astype(str)	+", 'gender': "+df["Gender"].astype(str)	+", 'disability': "+df["Disability"].astype(str)+"}"
        values_disability = df['Disability'].astype(str)+", "
        values_urban = df['Urban / Rural'].astype(str)+", "
        values_highest = df['Highest Education Level'].astype(str)+", "
        values_city = df['City'].astype(str)+", "
        values_province = df['Province'].astype(str)+", "
        values_date_of_birth = "'" + df['Date of Birth'].astype(str) +"', "
        values_employee_id = "'" + df['Employee ID'].astype(str) +"', "
        values_ofo = "'" + df['OFO Code'].astype(str) +"', "
        values_name = "'" + df['Name'].astype(str) +"', "
        values_occupation = "'" + df['Occupation'].astype(str) +"', "
        values_specialisation = "'" + df['Specialization'].astype(str) +"', "
        values_gender = df['Gender'].astype(str)+", "
        values_race = df['Race'].astype(str)+ ", "
        values_last_name = "'" + df['Last Name'].astype(str) +"', "
        values_citizen = df['Citizen Status'].astype(str)+", "
        values_idtype = df['ID Type'].astype(str)
        df['Sql'] = "insert into tep_wspwiz (disability, urban_rural, highest_education, city, province, date_of_birth, employee_id, ofo_code, name, occupation, specialisation, gender, race, last_name, citizen_status, id_type) values (" + values_disability + values_urban + values_highest + values_city + values_province + values_date_of_birth + values_employee_id + values_ofo + values_name + values_occupation + values_specialisation + values_gender + values_race + values_last_name + values_citizen + values_idtype + ")"
        # SDL_Number	Name	Last Name	Citizen Status	ID Type	Employee ID		Date of Birth	OFO Code	Occupation	Specialization	Province	City	Urban / Rural	Highest Education Level	Race	Gender	Disability

        # df['Rec'] = "{ 'race': " + df['Race'] + ", 'gender':" + df['Gender'] + ", 'name': '" + df['Name'] + "', 'employee_id': '" + df["Employee ID"] +"'"+ ", 'city':"+ df["City"] +"}"
        print(df['Sql'])
        return list(df['Sql'])


def test_data():
    print(os.environ['PASSWORD_FILE'])
    print(os.environ['PASSWORD_FILE'])
    import_test = ImportTool('tep.xlsx', 1, 'carol')
    import_test.import_tep()
    logger = True

if __name__ == '__main__':
    test_data()

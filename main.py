import os
import json
import zipfile 
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser
import pandas as pd
import tabulate



class Main:
    def __init__(self, Main_Path, Sub_Path):
        self.main_path = Main_Path
        self.sub_path = Sub_Path
        self.attendance = pd.DataFrame()
        self.subject_data = {}
        self.Extract_data()
        self.Main()

    def Extract_data(self):
        self.attendance = pd.read_csv(self.main_path + '.csv')
        for subject in os.listdir(self.sub_path):
            subject_name = subject[:-4]
            self.subject_data[subject_name] = pd.read_csv(os.path.join(self.sub_path, subject))
        
    def Store_data(self):
        self.attendance.to_csv(self.main_path + '.csv', index=False)
        for subject_name, data in self.subject_data.items():
            data.to_csv(os.path.join(self.sub_path, subject_name + '.csv'), index=False)
        self.Main()
    
    def Display_data(self,Table_Format='pretty',Table=True):
        if Table:
            print(tabulate.tabulate(self.attendance, headers='keys', tablefmt=Table_Format))
            for subject_name, data in self.subject_data.items():
                print(f"\nSubject: {subject_name}")
                print(tabulate.tabulate(data, headers='keys', tablefmt=Table_Format))
        else:
            print(self.attendance)
            for subject_name, data in self.subject_data.items():
                print(f"\nSubject: {subject_name}")
                print(data)

    def cli_parser(self,choices = range(1,6)):
        parser = ArgumentParser(prog = "Attendance Manager CLI",
            description = "Interactive terminal UI for viewing attendance")
        parser.add_argument("-o","--option",type = int, help = (
        "1. Add Attendence\n"
        "2. Toggle Attendence\n"
        "3. Archive semester (move old data & create new skeleton)\n"
        "4. Create new semester configuration\n"
        "5. Exit")
        ,choices = choices, required = True)

        args = parser.parse_args()
        return args.option

    def _semester_config_path(self):
        """
        Reads semester_config.cfg path
        """
        return Path(self.main_path).parents[1] / 'semester_config.cfg'
    
    def load_semester_config(self):
        """
        Loads semester config from "semester_config.cfg"
        """
        cfg_path: Path = self._semester_config_path()
        
        if not cfg_path.exists():
            return None # Return None: to show a semester_config.cfg does not exist
        try:
            data = cfg_path.read_text().strip()
            if not data:
                return False
            dct = json.loads(data)
            return dct
        except Exception as e:
            return e # Return False: to show issue with reading semester_config into json

    def has_semester_ended(self,cfg):
        """
        This checks of the semester date has passed.
        """
        end_date = datetime.strptime(cfg["end_date"],"%Y-%m-%d")
        return end_date < datetime.now() 
    
    def archive_semester(self, semester_id, archive = False, dry_run = False):
        """
        This method archives the semester data int `Data/archives` folder
        """
        
        archives = Path(self.main_path).parents[1] / 'archives'
        archives.mkdir(exist_ok = True)
        attendence_data = Path(self.main_path + ".csv")
        subject_data = list(Path(self.sub_path).glob("*.csv"))

        if not ([attendence_data]+subject_data):
            return {"status": "no_files", "message": "No attendance/subject CSVs found to archive."}


        if dry_run:
            return {
            "status": "dry_run",
            "planned": {
                "archive_to": str(archives / (semester_id + ".zip")),
                "files": [f'{x}' for x in [attendence_data]+subject_data]
            }
            }

        
        attendence_header = {attendence_data : pd.read_csv(attendence_data).columns}
        subject_headers = {subj : pd.read_csv(subj).columns for subj in subject_data}

        

        tmp_file = archives / f'tmp_{semester_id}.zip'
        final_path = archives / f'{semester_id}.zip'

        

        try:
            with zipfile.ZipFile(tmp_file,"w") as zObject:
                for file in [attendence_data] + subject_data:
                    zObject.write(f'{file}',arcname = os.sep.join(file.parts[-2:]))

            with zipfile.ZipFile(tmp_file,"r") as zf:
                names = {os.path.split(x)[-1] for x in zf.namelist()}
                
            if names ^ {x.name for x in [attendence_data]+subject_data}:
                tmp_file.unlink(missing_ok=True)
                raise RuntimeError("zip verification failed: missing files")
            
            os.replace(str(tmp_file), str(final_path))
            for p in [attendence_data]+subject_data:
                p.unlink()
            for filename, cols in (attendence_header | subject_headers).items():
                df = pd.DataFrame(columns = cols)
                df.to_csv(filename, index = False)

            return {"status": "ok", "message": f'Sucessfully archived to {final_path}'}
        except Exception as e:
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
            return {"status": "error", "message": repr(e)}





    
    def prompt_user_to_archive(self):
        """
        Archives attendence and related csv files in Overall and Subject_Data Folders.
        User can choose either to archive or dry run.
        """
        cfg = self.load_semester_config()
        if cfg is None:
            print("Could not find 'semester_config.cfg' file")
            return 
        elif cfg is False:
            print('semester_config.cfg found empty')
            return
        elif isinstance(cfg,Exception):
            print(cfg.args[0])
            return 
        if not cfg.get("end_date",""):
            print("No end date found")
            return 
        if not self.has_semester_ended(cfg):
            print(f"Semester has not ended. End date: {cfg['end_date']}")
            return 
        
        semester_id = cfg["semester_id"]
        choice = input("Archive now: (y = archive, d = dry run, n = skip): ").strip().lower()
        if choice == "d":
            res = self.archive_semester(semester_id,dry_run = True)
            print(f"Planned moves (dry-run): ")
            print(f"Archive path: ",res["planned"]["archive_to"])
            print(f"Archive following files:")
            print("\n".join(f'\t- {x}' for x in res["planned"]["files"]))
            
            

        elif choice == "y":
            res = self.archive_semester(semester_id, archive = True)
            print("Archive done: ",res["message"])
        else:
            print("Skipping for now")
        return True
    
    def save_semester_config(self):
        """
        Save new semester data to semester_config.cfg in below format.
        {
            "semester_id": "Data 2024",
            "start_date": "2025-01-13",
            "end_date": "2025-10-12"
        }
        """
        p = self._semester_config_path()
        p.parent.mkdir(parents=True, exist_ok=True)

        semester_id = input("Semester ID: ").strip()
        semester_end_date = input("Semester End Date in dd/mm/YYYY format: ").strip()

        if not (semester_id and semester_end_date):
            print("'Semester ID' and 'Semester End Date' cannot be left empty")
            return 
        try:
            semester_end_date = datetime.strptime(semester_end_date,"%d/%m/%Y")
        except ValueError as e:
            print("Semester end date is not in expexted fomat of dd/mm/YYYY")
            return 
        
        cfg = {
        "semester_id": semester_id,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": semester_end_date.strftime("%Y-%m-%d")
        }

        if self.has_semester_ended(cfg):
            return "Semester End date cannot be before current date"

        json.dump(cfg,open(p,"w"),indent = 2)


        

        
    
        

    
    def Main(self):
        self.Display_data()
        user_input = self.cli_parser()
        print("User input",user_input)
        
        if user_input==1:
            Subject_list=self.attendance['Subject'].tolist()
            print("Chose Subject Name: ")
            print(Subject_list)
            subject=input("Enter Subject Name or Index: ") 
            if subject.isdigit():
                subject=Subject_list[int(subject)]
            present = input("Present? (Y/N): ").capitalize()[0] in ['Y','T',1]
            self.Add_Attendance(subject, present)

        elif user_input==2:
            Subject_list=self.attendance['Subject'].tolist()
            print("Chose Subject Name: ")
            print(Subject_list)
            subject=input("Enter Subject Name or Index: ") 
            if subject.isdigit():
                subject=Subject_list[int(subject)]
            input_date = input("Enter Date [Format: Wed Nov 12 2025]: ")
            self.Toggle_Attendance(subject, datetime.datetime.strptime(input_date, "%a %b %d %Y"))
        elif user_input==5:
            exit()
        elif user_input == 3:
            self.prompt_user_to_archive()
        elif user_input == 4:
            self.save_semester_config()
        else:
            print("Invalid Input")
            self.Main()
        
    def Add_Attendance(self, subject, present):
        subject_df = self.subject_data[subject]
        new_row = pd.DataFrame([{
            'Lec_Date': datetime.datetime.now().strftime("%a %b %d %Y"),
            'Status': bool(present)
        }])
        subject_df = pd.concat([subject_df, new_row], ignore_index=True)
        self.attendance.loc[self.attendance['Subject'] == subject, 'Total Classes'] += 1
        if present:
            self.attendance.loc[self.attendance['Subject'] == subject, 'Present'] += 1
        self.attendance.loc[self.attendance['Subject'] == subject, 'Attendance Percentage'] = \
            (self.attendance.loc[self.attendance['Subject'] == subject, 'Present'] / 
             self.attendance.loc[self.attendance['Subject'] == subject, 'Total Classes'] * 100).round(2)
        self.attendance.loc[self.attendance['Subject'] == subject, 'Last Updated'] = datetime.datetime.now().strftime("%a %b %d %Y")
        self.subject_data[subject] = subject_df
        self.Store_data()

    def Toggle_Attendance(self, subject, date):
        present = bool(self.subject_data[subject].loc[pd.to_datetime(self.subject_data[subject]['Lec_Date'], format="%a %b %d %Y") == date,'Status'].values[0])
        self.subject_data[subject].loc[pd.to_datetime(self.subject_data[subject]['Lec_Date'], format="%a %b %d %Y") == date,'Status'] = not present
        if present:
            self.attendance.loc[self.attendance['Subject'] == subject, 'Present'] -= 1
        else:
            self.attendance.loc[self.attendance['Subject'] == subject, 'Present'] += 1
        self.attendance.loc[self.attendance['Subject'] == subject, 'Attendance Percentage'] = \
            (self.attendance.loc[self.attendance['Subject'] == subject, 'Present'] / 
             self.attendance.loc[self.attendance['Subject'] == subject, 'Total Classes'] * 100).round(2)
        self.attendance.loc[self.attendance['Subject'] == subject, 'Last Updated'] = datetime.datetime.now().strftime("%a %b %d %Y")
        self.Store_data()

    


if __name__ == '__main__':
    Main('Data/Overall/Attendance', 'Data/Subject_Data/')
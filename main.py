import sqlite3
import json
import re
import sys
import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QGridLayout, QLabel, QHBoxLayout, QInputDialog,
    QLineEdit, QFormLayout, QTabWidget, QHeaderView
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont
from PyQt5.QtCore import Qt, QLocale

# Klasi bazastvis gankutvnili
class StudentDatabase:
    def __init__(self, db_name="students.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # studentebis informacia am bazis tableshi mogrovdeba,da am qverit vqmnit
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS STUDENTS(
                                STUDENT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                NAME TEXT, LAST_NAME TEXT, GPA REAL,
                                MAJOR TEXT, YEAR INT, EMAIL TEXT, GRADES TEXT)''')

        # gamocdebis shesabamisi veli,table bazashi
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS EXAMS(
                                EXAM_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                EXAM_NAME TEXT, EXAM_DATE TEXT, DESCRIPTION TEXT)''')

        # Table studentebis da gamocdebis shesabamisi
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS STUDENT_EXAMS(
                                STUDENT_ID INTEGER,
                                EXAM_ID INTEGER,
                                FOREIGN KEY(STUDENT_ID) REFERENCES STUDENTS(STUDENT_ID),
                                FOREIGN KEY(EXAM_ID) REFERENCES EXAMS(EXAM_ID))''')
        self.conn.commit()

    def add_student(self, name, last_name, gpa, major, year, email):
        if not self.validate_email(email):
            return False
        
        grades_json = json.dumps({})
        try:
            self.cursor.execute('''INSERT INTO STUDENTS 
                                (NAME, LAST_NAME, GPA, MAJOR, YEAR, EMAIL, GRADES)
                                VALUES (?,?,?,?,?,?,?)''', 
                                (name, last_name, gpa, major, year, email, grades_json))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def delete_student(self, student_id):
        try:
            self.cursor.execute("DELETE FROM STUDENTS WHERE STUDENT_ID=?", (student_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_all_students(self, order_by="STUDENT_ID"):
        """
        Yvela informacias abrunebs studentze,es modis ra tqma unda bazidan,laqdeba aseve zrdadobit
        """
        query = f"SELECT * FROM STUDENTS ORDER BY {order_by} ASC"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def add_exam(self, exam_name, exam_date, description):
        try:
            self.cursor.execute('''INSERT INTO EXAMS 
                                (EXAM_NAME, EXAM_DATE, DESCRIPTION)
                                VALUES (?,?,?)''', 
                                (exam_name, exam_date, description))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_all_exams(self, order_by="EXAM_ID"):
        query = f"SELECT * FROM EXAMS ORDER BY {order_by} ASC"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def delete_exam(self, exam_id):
        try:
            self.cursor.execute("DELETE FROM EXAMS WHERE EXAM_ID=?", (exam_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def assign_student_to_exam(self, student_id, exam_id):
        try:
            self.cursor.execute('''INSERT INTO STUDENT_EXAMS 
                                (STUDENT_ID, EXAM_ID)
                                VALUES (?,?)''', 
                                (student_id, exam_id))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_all_assignments(self, order_by="STUDENT_EXAMS.STUDENT_ID"):
 
        query = f'''
            SELECT STUDENT_EXAMS.STUDENT_ID, STUDENTS.NAME,
                   EXAMS.EXAM_ID, EXAMS.EXAM_NAME
            FROM STUDENT_EXAMS
            JOIN STUDENTS ON STUDENTS.STUDENT_ID = STUDENT_EXAMS.STUDENT_ID
            JOIN EXAMS ON EXAMS.EXAM_ID = STUDENT_EXAMS.EXAM_ID
            ORDER BY {order_by} ASC
        '''
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_exams_for_student(self, student_id):
        """
     
        Abrunebs bazidan da moaqvs monacemebi gamocdebze,student aidi primary keyt
        """
        query = """
            SELECT EXAMS.EXAM_ID, EXAMS.EXAM_NAME, EXAMS.EXAM_DATE, EXAMS.DESCRIPTION
            FROM STUDENT_EXAMS
            JOIN EXAMS ON STUDENT_EXAMS.EXAM_ID = EXAMS.EXAM_ID
            WHERE STUDENT_EXAMS.STUDENT_ID = ?
        """
        self.cursor.execute(query, (student_id,))
        return self.cursor.fetchall()

    def get_student_by_id(self, student_id):
        """
        Returns (NAME, LAST_NAME) for the given student_id, or None if not found.
        """
        try:
            self.cursor.execute("SELECT NAME, LAST_NAME FROM STUDENTS WHERE STUDENT_ID=?", (student_id,))
            row = self.cursor.fetchone()
            if row:
                
                return row
            return None
        except sqlite3.Error:
            return None

    @staticmethod
    def validate_email(email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

#QT 5   ui aris es,mtavari frontendi,ui qti
class StudentManagementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.db = StudentDatabase()
        self.current_order = "STUDENT_ID"

       #sortireba
        self.STUDENT_SORT_MAP = {
            "ID": "STUDENT_ID",
            "Name": "NAME",
            "Last Name": "LAST_NAME",
            "GPA": "GPA",
            "Year": "YEAR"
        }
        self.EXAM_SORT_MAP = {
            "ID": "EXAM_ID",
            "Name": "EXAM_NAME",
            "Date": "EXAM_DATE"
        }
        self.ASSIGN_SORT_MAP = {
            "Student ID": "STUDENT_EXAMS.STUDENT_ID",
            "Student Name": "STUDENTS.NAME",
            "Exam ID": "EXAMS.EXAM_ID",
            "Exam Name": "EXAMS.EXAM_NAME"
        }

        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Student and Exam Management System")
        self.setGeometry(100, 100, 1100, 600)
        
 
        self.setStyleSheet("""
            background-color: #2c3e50; /* Dark background */
            color: #ecf0f1; /* Light text */
            font-size: 14px;
        """)

     
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #34495e;
            }
            QTabBar::tab {
                background: #34495e;
                color: #ecf0f1;
                padding: 8px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #3b4c5c;
            }
        """)
        self.tabs.addTab(self.create_student_tab(), "Students")
        self.tabs.addTab(self.create_exam_tab(), "Exams")
        self.tabs.addTab(self.create_assignments_tab(), "Assigned Students")
      
        self.tabs.addTab(self.create_student_exams_tab(), "Student")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    #studentebis gverdi,tabi
    def create_student_tab(self):
        student_tab = QWidget()
        layout = QVBoxLayout()


        self.student_table = QTableWidget()
        self.student_table.setColumnCount(7)
        self.student_table.setHorizontalHeaderLabels(["ID", "Name", "Last Name", "GPA", "Major", "Year", "Email"])
        self.student_table.verticalHeader().setVisible(False)
        header = self.student_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        table_font = self.student_table.font()
        table_font.setPointSize(11)
        self.student_table.setFont(table_font)

        self.student_table.setStyleSheet("""
            QTableWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
                gridline-color: #bdc3c7;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 4px;
            }
        """)

        control_layout = QHBoxLayout()


        self.student_sort_combo = QComboBox()
        self.student_sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        self.student_sort_combo.addItems(self.STUDENT_SORT_MAP.keys())
        self.student_sort_combo.currentIndexChanged.connect(self.on_student_sort_change)
        control_layout.addWidget(QLabel("Sort by:"))
        control_layout.addWidget(self.student_sort_combo)

        self.refresh_btn = self.create_button("Refresh", "#2980b9", self.refresh_student_data)
        self.delete_btn = self.create_button("Delete Student", "#c0392b", self.delete_student)
        self.add_btn = self.create_button("Add Student", "#27ae60", self.add_student)

        control_layout.addStretch()
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.delete_btn)
        control_layout.addWidget(self.add_btn)

        layout.addLayout(control_layout)
        layout.addWidget(self.student_table)

        student_tab.setLayout(layout)
        self.refresh_student_data()  
        return student_tab

    def on_student_sort_change(self):
  
        chosen_text = self.student_sort_combo.currentText()
        db_column = self.STUDENT_SORT_MAP[chosen_text]
        self.refresh_student_data(order_by=db_column)

    def refresh_student_data(self, order_by=None):
        if order_by:
            self.current_order = order_by
        students = self.db.get_all_students(self.current_order)
        self.student_table.setRowCount(len(students))

        for row, student in enumerate(students):
            for col, data in enumerate(student):
                item = QTableWidgetItem(str(data))
               
                if col in (0, 5):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.student_table.setItem(row, col, item)

    def add_student(self):
        form = QWidget()
        form.setWindowTitle("Add New Student")
        form.setMinimumWidth(400)
        
        layout = QFormLayout()
        form.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)

        
        name_input = QLineEdit()
        last_name_input = QLineEdit()
        

        gpa_input = QLineEdit()
        gpa_validator = QDoubleValidator(0.0, 4.0, 2)
        gpa_validator.setNotation(QDoubleValidator.StandardNotation)
        gpa_validator.setLocale(QLocale.c())  # Force '.' as decimal separator
        gpa_input.setValidator(gpa_validator)
        
        major_input = QComboBox()
        major_input.addItems([
            "Computer Science", "Information Technology", 
            "Electrical Engineering", "Mechanical Engineering",
            "Business Administration", "Mathematics", "Physics"
        ])
        
        year_input = QLineEdit()
        current_year = datetime.datetime.now().year
        year_validator = QIntValidator(1999, current_year)
        year_input.setValidator(year_validator)
        
        email_input = QLineEdit()

        # form fanjaristvis sadac monacemebs vwert,vamatebt xazebs
        layout.addRow(QLabel("First Name:"), name_input)
        layout.addRow(QLabel("Last Name:"), last_name_input)
        layout.addRow(QLabel("GPA (0.0-4.0):"), gpa_input)
        layout.addRow(QLabel("Major:"), major_input)
        layout.addRow(QLabel("Enrollment Year:"), year_input)
        layout.addRow(QLabel("Email:"), email_input)

   
        submit_btn = QPushButton("Submit")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        
        def submit():
            if not all([name_input.text(), last_name_input.text(), gpa_input.text(),
                       year_input.text(), email_input.text()]):
                QMessageBox.warning(form, "Error", "All fields are required!")
                return

            try:
                success = self.db.add_student(
                    name_input.text(),
                    last_name_input.text(),
                    float(gpa_input.text()),
                    major_input.currentText(),
                    int(year_input.text()),
                    email_input.text()
                )
                
                if success:
                    QMessageBox.information(form, "Success", "Student added successfully!")
                    self.refresh_student_data()
                    form.close()
                else:
                    QMessageBox.warning(form, "Error", "Invalid email format or database error!")
            except ValueError:
                QMessageBox.warning(form, "Error", "Please enter valid values!")

        submit_btn.clicked.connect(submit)
        layout.addRow(submit_btn)
        form.setLayout(layout)
        form.show()

    def delete_student(self):
        student_id, ok = QInputDialog.getText(self, "Delete Student", "Enter Student ID:")
        if not ok:
            return
        
        if not student_id.isdigit():
            QMessageBox.warning(self, "Error", "Invalid Student ID format!")
            return

        if self.db.delete_student(int(student_id)):
            QMessageBox.information(self, "Success", "Student deleted successfully!")
            self.refresh_student_data()
            self.refresh_assignments_data()  # In case that student had assignments
        else:
            QMessageBox.warning(self, "Error", "Student not found or deletion failed!")

    #qmnis gamocdebis fanjaras anu tabs
    def create_exam_tab(self):
        exam_tab = QWidget()
        layout = QVBoxLayout()

       
        self.exam_table = QTableWidget()
        self.exam_table.setColumnCount(3)
        self.exam_table.setHorizontalHeaderLabels(["ID", "Exam Name", "Date"])
        self.exam_table.verticalHeader().setVisible(False)
        
        header = self.exam_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        table_font = self.exam_table.font()
        table_font.setPointSize(11)
        self.exam_table.setFont(table_font)

        self.exam_table.setStyleSheet("""
            QTableWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
                gridline-color: #bdc3c7;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 4px;
            }
        """)


        exam_control_layout = QHBoxLayout()

        self.exam_sort_combo = QComboBox()
        self.exam_sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.exam_sort_combo.addItems(self.EXAM_SORT_MAP.keys())
        self.exam_sort_combo.currentIndexChanged.connect(self.on_exam_sort_change)
        exam_control_layout.addWidget(QLabel("Sort by:"))
        exam_control_layout.addWidget(self.exam_sort_combo)

        self.refresh_exam_btn = self.create_button("Refresh Exams", "#2980b9", self.refresh_exam_data)
        self.add_exam_btn = self.create_button("Add Exam", "#27ae60", self.add_exam)
        self.delete_exam_btn = self.create_button("Delete Exam", "#c0392b", self.delete_exam)

        self.assign_student_btn = self.create_button("Assign Student", "#2980b9", self.assign_student_to_exam)

        exam_control_layout.addStretch()
        exam_control_layout.addWidget(self.refresh_exam_btn)
        exam_control_layout.addWidget(self.assign_student_btn)
        exam_control_layout.addWidget(self.add_exam_btn)
        exam_control_layout.addWidget(self.delete_exam_btn)

        layout.addLayout(exam_control_layout)
        layout.addWidget(self.exam_table)

        exam_tab.setLayout(layout)
        self.refresh_exam_data()
        return exam_tab

    def on_exam_sort_change(self):
        chosen_text = self.exam_sort_combo.currentText()
        db_column = self.EXAM_SORT_MAP[chosen_text]
        self.refresh_exam_data(order_by=db_column)

    def refresh_exam_data(self, order_by=None):
        if not order_by:
            order_by = "EXAM_ID"
        exams = self.db.get_all_exams(order_by)
        self.exam_table.setRowCount(len(exams))
        
        for row, exam in enumerate(exams):
            for col, data in enumerate(exam[:3]):  # ID, Name, Date
                item = QTableWidgetItem(str(data))
                if col == 0:  # Right-align ID
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.exam_table.setItem(row, col, item)

    def add_exam(self):
        form = QWidget()
        form.setWindowTitle("Add New Exam")
        form.setMinimumWidth(400)
        
        layout = QFormLayout()
        form.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)


        exam_name_input = QLineEdit()
        exam_date_input = QLineEdit()
        description_input = QLineEdit()

        layout.addRow(QLabel("Exam Name:"), exam_name_input)
        layout.addRow(QLabel("Exam Date (YYYY-MM-DD):"), exam_date_input)
        layout.addRow(QLabel("Description:"), description_input)

     
        submit_btn = QPushButton("Submit")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)

        def submit():
            if not all([exam_name_input.text(), exam_date_input.text()]):
                QMessageBox.warning(form, "Error", "Exam Name and Date are required!")
                return

            try:
                success = self.db.add_exam(
                    exam_name_input.text(),
                    exam_date_input.text(),
                    description_input.text()
                )
                
                if success:
                    QMessageBox.information(form, "Success", "Exam added successfully!")
                    self.refresh_exam_data()
                    form.close()
                else:
                    QMessageBox.warning(form, "Error", "Database error!")
            except ValueError:
                QMessageBox.warning(form, "Error", "Please enter valid values!")

        submit_btn.clicked.connect(submit)
        layout.addRow(submit_btn)
        form.setLayout(layout)
        form.show()

    def delete_exam(self):
        """
        gamocdis washlis funqcia,romelic auqmebs da shlis gamocdas
        """
        exam_id_str, ok = QInputDialog.getText(self, "Delete Exam", "Enter Exam ID:")
        if not ok or not exam_id_str.isdigit():
            QMessageBox.warning(self, "Error", "Invalid Exam ID!")
            return
        exam_id = int(exam_id_str)

        if self.db.delete_exam(exam_id):
            QMessageBox.information(self, "Success", "Exam deleted successfully!")
            self.refresh_exam_data()
            self.refresh_assignments_data()  # In case that exam was assigned
        else:
            QMessageBox.warning(self, "Error", "Exam not found or deletion failed!")

    def assign_student_to_exam(self):
        """
        Patara dialogs da fanjaras xsnis,gvadzlvs sashualebas rom studenti davnishnot gamocdaze
        """
        # Create a small QWidget as a dialog
        dialog = QWidget()
        dialog.setWindowTitle("Assign Student to Exam")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout()

        form_layout = QFormLayout()


        exam_combo = QComboBox()
        all_exams = self.db.get_all_exams()

        for exam in all_exams:
            exam_id, exam_name, exam_date = exam[:3]  # ignoring description
            display_text = f"{exam_name} (ID: {exam_id})"
            exam_combo.addItem(display_text, exam_id)

        student_id_input = QLineEdit()
        student_id_input.setPlaceholderText("Enter Student ID")

        form_layout.addRow(QLabel("Exam:"), exam_combo)
        form_layout.addRow(QLabel("Student ID:"), student_id_input)
        layout.addLayout(form_layout)

        assign_btn = QPushButton("Assign")
        assign_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2471a3;
            }
        """)

        def do_assign():
            selected_exam_id = exam_combo.currentData()
            sid_str = student_id_input.text().strip()
            if not sid_str.isdigit():
                QMessageBox.warning(dialog, "Error", "Invalid Student ID!")
                return

            student_id = int(sid_str)

            if self.db.assign_student_to_exam(student_id, selected_exam_id):
                QMessageBox.information(dialog, "Success", "Student assigned to exam successfully!")
                self.refresh_exam_data()
                self.refresh_assignments_data()
                dialog.close()
            else:
                QMessageBox.warning(dialog, "Error", "Assignment failed! (Check IDs or DB error)")

        assign_btn.clicked.connect(do_assign)
        layout.addWidget(assign_btn)

        dialog.setLayout(layout)
        dialog.show()

    # ---------------------- Assignments Tab ---------------------- #
    def create_assignments_tab(self):
        assignments_tab = QWidget()
        layout = QVBoxLayout()

       
        self.assignments_table = QTableWidget()

        self.assignments_table.setColumnCount(4)
        self.assignments_table.setHorizontalHeaderLabels(["Student ID", "Student Name", "Exam ID", "Exam Name"])
        self.assignments_table.verticalHeader().setVisible(False)

        header = self.assignments_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        table_font = self.assignments_table.font()
        table_font.setPointSize(11)
        self.assignments_table.setFont(table_font)

        self.assignments_table.setStyleSheet("""
            QTableWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
                gridline-color: #bdc3c7;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 4px;
            }
        """)


        control_layout = QHBoxLayout()

        self.assign_sort_combo = QComboBox()
        self.assign_sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.assign_sort_combo.addItems(self.ASSIGN_SORT_MAP.keys())
        self.assign_sort_combo.currentIndexChanged.connect(self.on_assign_sort_change)
        control_layout.addWidget(QLabel("Sort by:"))
        control_layout.addWidget(self.assign_sort_combo)

        refresh_btn = self.create_button("Refresh", "#2980b9", self.refresh_assignments_data)

        control_layout.addStretch()
        control_layout.addWidget(refresh_btn)

        layout.addLayout(control_layout)
        layout.addWidget(self.assignments_table)
        assignments_tab.setLayout(layout)

        self.refresh_assignments_data()
        return assignments_tab

    def on_assign_sort_change(self):
        chosen_text = self.assign_sort_combo.currentText()
        db_column = self.ASSIGN_SORT_MAP[chosen_text]
        self.refresh_assignments_data(order_by=db_column)

    def refresh_assignments_data(self, order_by=None):
        """
        Es funqia,da buttoni,ubralod anaxlebs informacias programashive
        """
        if not order_by:
            order_by = "STUDENT_EXAMS.STUDENT_ID"

        assignments = self.db.get_all_assignments(order_by)
        self.assignments_table.setRowCount(len(assignments))

        # assignments[i] -> (STUDENT_ID, STUDENT_NAME, EXAM_ID, EXAM_NAME)
        for row, assignment in enumerate(assignments):
            for col, data in enumerate(assignment):
                item = QTableWidgetItem(str(data))
                # Right-align numeric columns (student_id=0, exam_id=2)
                if col in (0, 2):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.assignments_table.setItem(row, col, item)

    #Tab 2 Student exams (meore gverdi Chveni programis,fanjara)
    def create_student_exams_tab(self):
        """
        qmnis calke tabs anu meore fanjaras pyqtshi,studen idss tu chawert miabav anu danishnav mas gamocdaze
        
        """
        tab = QWidget()
        layout = QVBoxLayout()

        # --- Input field and button to load data ---
        input_layout = QHBoxLayout()
        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Enter Student ID")
        self.student_id_input.setStyleSheet("""
            QLineEdit {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
            }
        """)

        load_button = self.create_button("Load Exams", "#2980b9", self.load_student_exams)

        input_layout.addWidget(self.student_id_input)
        input_layout.addWidget(load_button)

        layout.addLayout(input_layout)

        #qt labli,rom sruli studentis saxeli achvenos
        self.student_name_label = QLabel("Student Name: N/A")
        name_font = QFont()
        name_font.setBold(True)
        self.student_name_label.setFont(name_font)
        layout.addWidget(self.student_name_label)


        self.student_exams_table = QTableWidget()

        self.student_exams_table.setColumnCount(4)
        self.student_exams_table.setHorizontalHeaderLabels(["Exam ID", "Exam Name", "Exam Date", "Description"])
        self.student_exams_table.verticalHeader().setVisible(False)

        header = self.student_exams_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        table_font = self.student_exams_table.font()
        table_font.setPointSize(11)
        self.student_exams_table.setFont(table_font)

        self.student_exams_table.setStyleSheet("""
            QTableWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
                gridline-color: #bdc3c7;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 4px;
            }
        """)

        layout.addWidget(self.student_exams_table)
        tab.setLayout(layout)

        return tab

    def load_student_exams(self):
        """

        studentis aidis kitxulobis pyqts input yutshi,danishnul gamocdebsac igebs es funqcia,
        da abrunebs da wers in examebis anu gamocdebis cxrilshi,
        srul saxelsa da gvarsac wers tu napovnia
        """
        sid_text = self.student_id_input.text().strip()
        if not sid_text.isdigit():
            QMessageBox.warning(self, "Error", "Please enter a valid numeric Student ID.")
            return

        student_id = int(sid_text)

        # 1) studetis sruli saxelis migeba
        student_data = self.db.get_student_by_id(student_id)  
        if student_data:
            first_name, last_name = student_data
            self.student_name_label.setText(f"Student Name: {first_name} {last_name}")
        else:
            self.student_name_label.setText("Student Name: Not found")

        exams = self.db.get_exams_for_student(student_id)
        self.student_exams_table.setRowCount(len(exams))
        for row_idx, exam in enumerate(exams):
            # exam -> (EXAM_ID, EXAM_NAME, EXAM_DATE, DESCRIPTION)
            for col_idx, val in enumerate(exam):
                item = QTableWidgetItem(str(val))
                if col_idx == 0:  # Right-align exam ID
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.student_exams_table.setItem(row_idx, col_idx, item)

        if not exams:
            QMessageBox.information(self, "No Exams Found", "This student is not assigned to any exams.")

    def create_button(self, text, color, callback):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def darken_color(self, hex_color, factor=0.8):
        rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
        darkened = [max(0, int(c * factor)) for c in rgb]
        return f'#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}'


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentManagementApp()
    window.show()
    sys.exit(app.exec_())

import datetime
import re

from PyQt5.QtCore import QTimer, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QTextDocument

from tools.helpful_functions import *


class EditEmployeeDialog(QDialog):
    """
    A dialog for editing employee information, dynamically generating fields based on provided data.

    Attributes:
        dataUpdated (pyqtSignal): Signal emitted when data is updated successfully.
        employee_id (int): The ID of the employee being edited.
        table_name (str): The name of the database table where employee data is stored.
        employee_data (list): A list of dictionaries containing employee data.
    """
    dataUpdated = pyqtSignal()

    def __init__(self, employee_id: int, table_name: str, employee_data: list, parent=None):
        """
        Initializes the EditEmployeeDialog with the given employee ID, table name, and employee data.

        Args:
            employee_id (int): The ID of the employee to edit.
            table_name (str): The name of the database table.
            employee_data (list): The employee data to be edited.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.employee_id = employee_id
        self.table_name = table_name
        self.employee_data = employee_data
        self.initUI()
        self.resize(500, 600)

    def initUI(self):
        """
        Initializes the user interface for the dialog, including form fields and control buttons.
        """
        # Main layout for the dialog
        mainLayout = QVBoxLayout(self)

        self.fields = {}

        # Initialize the form layout and add it to the main layout
        self.formLayout = QFormLayout()
        self.initializeFields()  # Initialize fields and add them to formLayout
        mainLayout.addLayout(self.formLayout)  # Add the form layout to the main layout

        # Initialize control buttons and add them to the main layout
        self.addControlButtons(mainLayout)

        # Set the main layout on the widget
        self.setLayout(mainLayout)

    def initializeFields(self):
        """
        Iterates over the employee data and adds a form field for each data item.
        """
        for item in self.employee_data:
            self.addFieldsForItem(item)

    def addFieldsForItem(self, item: dict):
        """
        Adds form fields for the given item to the form layout.

        Args:
            item (dict): A dictionary containing the details of the item to add to the form.
        """
        db_keys = item['db_key']
        label_texts = [self.formatLabelText(key) for key in db_keys if key]
        current_values = self.getCurrentValues(item['value_widget'].text(), db_keys)

        for index, key in enumerate(db_keys):
            if key:  # Ensure key is not None
                widget = self.createFieldWidget(key, current_values[index])
                self.formLayout.addRow(QLabel(label_texts[index]), widget)
                self.fields[key] = widget

    def getCurrentValues(self, text: str, db_keys: list) -> list:
        """
        Extracts and returns the current values from the given HTML text based on the database keys.
        """
        plain_text = self.stripHtmlTags(text)

        if 'first_name' in db_keys and 'last_name' in db_keys:
            return self.split_name(plain_text)
        elif {'address', 'city', 'state', 'zipcode'}.issubset(set(db_keys)):
            return self.split_address(plain_text)
        elif any(key and key.endswith('_conversion') for key in db_keys):  # Check for None before calling endswith
            return self.split_conversion(plain_text)
        return [plain_text] if db_keys else []

    @staticmethod
    def split_conversion(text: str) -> list:
        """
        Splits a numerical value from its unit in a string, returning just the number.
        """
        match = re.search(r'(\d+(\.\d+)?)', text)
        return [match.group(1), ''] if match else [text, '']

    @staticmethod
    def split_name(name: str) -> list:
        """
        Splits a full name into first and last name.
        """
        parts = name.split()
        return [' '.join(parts[:-1]), parts[-1]] if len(parts) > 1 else [name, '']

    @staticmethod
    def split_address(address: str) -> list:
        """
        Uses a regular expression to split an address string into its components: address, city, state, and zipcode.

        Args:
            address (str): The address string to split.

        Returns:
            list: A list containing the address, city, state, and zipcode. If the address does not match the expected
            format, returns the original address and empty strings for the other components.
        """
        # Use regex to split address into components
        match = re.match(r'^(.*),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})$', address)
        if match:
            return [match.group(1), match.group(2), match.group(3), match.group(4)]
        else:
            # Fallback if address does not match expected format
            return [address, "", "", ""]

    @staticmethod
    def createFieldWidget(key: str, value: str):
        """
        Creates and returns a widget appropriate for the given field key and value.
        """
        if key == 'availability':
            comboBox = QComboBox()
            comboBox.addItems(['W', 'NW', '~A', 'NA'])  # Availability options
            comboBox.setCurrentText(value)  # Set current value if exists
            return comboBox
        elif 'conversion' in key:
            comboBox = QComboBox()
            comboBox.addItems(["$/hr", "$/yr"])
            comboBox.setCurrentText(value)
            return comboBox
        else:
            return QLineEdit(value)

    def addControlButtons(self, layout: QVBoxLayout):
        """
        Adds control buttons (Save and Cancel) to the given layout.

        Args:
            layout (QVBoxLayout): The layout to which the buttons will be added.
        """
        # Initialize control buttons
        saveButton = QPushButton("Save")
        cancelButton = QPushButton("Cancel")

        # Button layout for control buttons
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(saveButton)
        buttonLayout.addWidget(cancelButton)

        # Add button layout to the main layout passed as an argument
        layout.addLayout(buttonLayout)

        # Connect signals to slots
        saveButton.clicked.connect(self.onSave)
        cancelButton.clicked.connect(self.reject)

    def onSave(self):
        """
        Handles the save action, updating the database and UI fields with new values.
        """
        updated_data = {}
        error_messages = []
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                text_value = widget.text().strip()
            elif isinstance(widget, QComboBox):
                text_value = widget.currentText().strip()
            else:
                text_value = None

            if text_value == 'N/A':
                continue

            # Check and format 'hired_date'
            if 'date' in key:
                try:
                    QDate.fromString(text_value, 'dd/MM/yyyy').toString('yyyy-MM-dd')
                except ValueError:
                    error_messages.append(f"{key} must be in 'DD/MM/YYYY' format.")
                    continue

                # Validate 'pay' to be a float
            if key == 'pay':
                try:
                    float(text_value)
                except ValueError:
                    error_messages.append(f"{key} must be a valid number.")
                    continue

                # Specific validation for 'availability', 'employee_type', etc., can be added here

                # If all validations pass, add the data to updated_data
            updated_data[key] = text_value

            # If there are validation errors, show them and abort the save
            if error_messages:
                QMessageBox.warning(self, "Validation Error", "\n".join(error_messages))
                return

        # Update the database and UI
        for item in self.employee_data:
            db_keys = item['db_key']
            for key in db_keys:
                if key in updated_data:
                    value = updated_data[key]
                    # Prepare value for SQL query (handle NULL values)
                    if value in [None, 'N/A', 'NULL', 'None', '']:
                        value = 'NULL'
                    # Construct SQL query differently based on whether value is None or not
                    query = f"UPDATE {self.table_name} SET {key} = %s WHERE id = %s"
                    execute_query(query, (value, self.employee_id))

            # Update the UI component
            new_values = [updated_data.get(key, '') for key in db_keys]
            new_text = self.concatenate_values(db_keys, new_values)
            formatted_value = f'<span style="color: grey;">{new_text}</span>'
            item['value_widget'].setText(formatted_value)

        self.dataUpdated.emit()
        self.accept()

    @staticmethod
    def concatenate_values(db_keys: list, values: list) -> str:
        """
        Concatenates a list of values into a single string based on the context provided by db_keys.

        Args:
            db_keys (list): A list of database key names indicating the context for concatenation.
            values (list): A list of values corresponding to the keys in db_keys.

        Returns:
            str: A concatenated string of values formatted based on the specific keys provided.
        """
        # Replace None with "None" in values list
        values = [str(value) if value is not None else "None" for value in values]

        # Custom logic to concatenate values based on the specific keys
        if 'first_name' in db_keys and 'last_name' in db_keys:
            return ' '.join(values)  # Simple space join for names
        elif 'address' in db_keys and 'city' in db_keys:
            # Assuming values follow the order: [address, city, state, zipcode]
            return ', '.join(values[:2]) + ', ' + ' '.join(values[2:])  # Custom format for address
        # Add more conditions as needed
        return ' '.join(values)  # Default join

    @staticmethod
    def formatLabelText(key: str) -> str:
        """
        Formats a database field key into a more readable label text by capitalizing words and replacing underscores with spaces.

        Args:
            key (str): The database field key to format.

        Returns:
            str: The formatted label text.
        """
        return ' '.join(word.capitalize() for word in key.split('_'))

    @staticmethod
    def stripHtmlTags(htmlText: str) -> str:
        """
        Removes HTML tags from the given text.

        Args:
            htmlText (str): The HTML text to clean.

        Returns:
            str: The plain text without HTML tags.
        """
        doc = QTextDocument()
        doc.setHtml(htmlText)
        return doc.toPlainText()


class AddFieldDialog(QDialog):
    dataUpdated = pyqtSignal()

    def __init__(self, _id, table_name, added_fields, parent=None):
        super().__init__(parent)
        self._id = _id
        self.table_name = table_name
        self.added_fields = added_fields
        self.setWindowTitle("Add Employee Information")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.initUI()
        self.tempMsgBox = None  # Temporary storage for the message box

    def initUI(self):
        layout = QVBoxLayout(self)

        self.formLayout = QFormLayout()
        self.fieldEdit = QLineEdit()
        self.valueEdit = QLineEdit()
        self.formLayout.addRow("Field:", self.fieldEdit)
        self.formLayout.addRow("Value:", self.valueEdit)
        layout.addLayout(self.formLayout)

        buttonLayout = QHBoxLayout()
        addButton = QPushButton("Add")
        addButton.clicked.connect(self.onAddClicked)
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.onSaveClicked)

        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(saveButton)
        layout.addLayout(buttonLayout)

    @staticmethod
    def column_exists(table_name, column_name):
        db_config = load_json_file()
        database_name = db_config.get("database")
        query = """
            SELECT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s 
                AND COLUMN_NAME = %s
            ) AS `exists`;
            """
        # Assuming `execute_query` is a function that executes your SQL query and returns the results
        # You need to replace 'your_database_name' with the actual name of your database
        result = execute_query(query, (database_name, table_name, column_name), fetch_mode='one')

        return result[0] == 1

    def onAddClicked(self):
        field = self.fieldEdit.text().strip()
        value = self.valueEdit.text()
        table = self.table_name

        if not self.column_exists(table, field):
            # Column does not exist, so add it
            add_column_query = f"ALTER TABLE {table} ADD COLUMN {field} VARCHAR(255) NULL;"
            execute_query(add_column_query)
            print(f"Column {field} added.")

        # Now, update the record with the new value
        update_query = f"UPDATE {table} SET {field} = %s WHERE id = %s"
        data = (value, self._id)
        execute_query(update_query, data)

        self.added_fields[field] = value

        self.showMessage("Information added successfully.")

    def onSaveClicked(self):
        # Emit the signal to indicate data has been updated
        self.dataUpdated.emit()

        # Close the dialog
        self.accept()

    def showMessage(self, message):
        self.tempMsgBox = QMessageBox(self)  # Make it an attribute
        self.tempMsgBox.setText(message)
        self.tempMsgBox.setStandardButtons(QMessageBox.NoButton)
        self.tempMsgBox.setWindowTitle("Success")
        self.tempMsgBox.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.tempMsgBox.show()

        # Use a QTimer to close the message box after a delay
        QTimer.singleShot(1000, self.closeMessageBox)

    def closeMessageBox(self):
        if self.tempMsgBox:
            # Attempt to close the message box
            closed = self.tempMsgBox.close()
            if not closed:
                # If the message box did not close, forcefully delete it
                print("Message box did not close, deleting forcefully.")
                self.tempMsgBox.deleteLater()
            self.tempMsgBox = None  # Clear the reference


class ManageJobOrderDialog(QDialog):
    employeeAdded = pyqtSignal()

    def __init__(self, action, job_data=None, employee_id=None, parent=None):
        super().__init__(parent)
        self.action = action
        self.jobData = job_data
        self.employee_id = employee_id
        self.setWindowTitle("Job Order Control Page")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.initUI()

    def initUI(self):
        dialogLayout = QVBoxLayout()

        titleLabel = QLabel("Job Order Control Page")
        titleLabel.setFont(QFont("Arial", 16, QFont.Bold))
        dialogLayout.addWidget(titleLabel)

        self.setupCurrentJobGroupBox(dialogLayout)
        self.setupJobAndDataInfo(dialogLayout)

        actionButton = QPushButton(self.action)
        dialogLayout.addWidget(actionButton)
        if self.action == "Add":
            actionButton.clicked.connect(lambda: self.performAddAction(self.employee_id))
        elif self.action == "Change":
            actionButton.clicked.connect(lambda: self.performChangeAction(self.employee_id))
        elif self.action == "Remove":
            actionButton.clicked.connect(lambda: self.performRemoveAction(self.employee_id))

        self.setLayout(dialogLayout)

    def setupCurrentJobGroupBox(self, dialogLayout):
        currentJobGroup = QGroupBox("Current Job Information")
        currentJobLayout = QVBoxLayout()

        if self.jobData:
            self.update_job_info(layout=currentJobLayout, jobData=self.jobData)
        else:
            currentJobLayout.addWidget(QLabel("Not on a job currently."))

        currentJobGroup.setLayout(currentJobLayout)
        dialogLayout.addWidget(currentJobGroup)

    def setupJobAndDataInfo(self, dialogLayout):
        # Horizontal layout to hold both Job Information and Possible Job Data side by side
        verticalLayout = QVBoxLayout()

        jobInfoGroup = QGroupBox("Employee Information")
        jobInfoLayout = QHBoxLayout()
        self.setupPossibleJobGroupBox(jobInfoLayout)
        self.setupPaySelection(jobInfoLayout)
        self.setupHiringDateSelection(jobInfoLayout)
        jobInfoGroup.setLayout(jobInfoLayout)

        # Possible Job Data GroupBox
        possibleJobDataGroup = QGroupBox("Possible Job Information")
        self.possibleJobDataLayout = QVBoxLayout()
        # Initially populate with data from the selected job in the combobox, if available
        self.update_job_info(layout=self.possibleJobDataLayout, jobData=self.jobData)
        possibleJobDataGroup.setLayout(self.possibleJobDataLayout)

        # Add both group boxes to the horizontal layout
        verticalLayout.addWidget(jobInfoGroup)
        verticalLayout.addWidget(possibleJobDataGroup)

        # Add the horizontal layout to the dialog's main layout
        dialogLayout.addLayout(verticalLayout)

    def setupPossibleJobGroupBox(self, jobInfoLayout):
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Job Title:"))
        self.jobComboBox = QComboBox()
        self.jobComboBox.setEditable(True)
        job_titles = self.fetch_job_titles()
        if job_titles:
            self.jobComboBox.setCompleter(QCompleter(job_titles))
            self.jobComboBox.addItems(job_titles)
        layout.addWidget(self.jobComboBox)

        # Connect the currentIndexChanged signal to a new method that updates job info
        self.jobComboBox.currentIndexChanged.connect(self.onJobComboBoxChange)

        # Adjust the stretch factors here
        layout.setStretch(0, 1)  # QLabel stretch
        layout.setStretch(1, 3)  # self.jobComboBox stretch, giving it more space

        jobInfoLayout.addLayout(layout)

    def setupPaySelection(self, jobInfoLayout):
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Pay:"))
        self.payLineEdit = QLineEdit()
        self.payLineEdit.setPlaceholderText("Enter pay rate")
        layout.addWidget(self.payLineEdit)

        self.payTypeComboBox = QComboBox()
        self.payTypeComboBox.addItems(["$/hr", "$/yr"])
        layout.addWidget(self.payTypeComboBox)

        # Adjust the stretch factors here
        layout.setStretch(1, 2)  # Give some more space to the payLineEdit but less than jobComboBox

        jobInfoLayout.addLayout(layout)

    def setupHiringDateSelection(self, jobInfoLayout):
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Start Date:"))
        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDate(QDate.currentDate())
        layout.addWidget(self.dateEdit)

        # Adjust the stretch factors here, if needed
        layout.setStretch(1, 1)  # Keep the default stretch for the dateEdit

        jobInfoLayout.addLayout(layout)

    def fetch_job_titles(self):
        query = "SELECT job_title, po_order_number FROM job_orders"
        result = execute_query(query, fetch_mode="all")
        if not result:
            # No job titles were found, inform the user and exit the function
            QMessageBox.information(self, "No Jobs Available", "There are no job orders currently available.")
            return []

        self.jobData = self.get_job_data(result[0][0], result[0][1])
        return [f"{title[0]} - {title[1]}" for title in result]

    @staticmethod
    def get_job_data(job_title, po_order_number):
        query = "SELECT * FROM job_orders WHERE job_title = %s AND po_order_number = %s"
        result = execute_query(query, (job_title, po_order_number), fetch_mode="one", get_column_names=True)
        if result and 'column_names' in result and 'result' in result:
            return dict(zip(result['column_names'], result['result']))
        return None

    @staticmethod
    def create_job_data_groupbox(jobData):
        jobDataGroupBox = QGroupBox("Job Data")
        gridLayout = QGridLayout(jobDataGroupBox)

        row, col = 0, 0
        for key, value in jobData.items():
            # Skip conversion rates from being directly added
            if key.endswith("_conversion"):
                continue

            # Initialize formatted_value with just the value in a span
            formatted_value = f'<span style="color:gray;">{value}'

            # If the key involves a rate that has a conversion, append it within the span
            if "bill_rate" in key and "bill_rate_conversion" in jobData:
                conversion = jobData["bill_rate_conversion"]
                formatted_value += f' {conversion}</span>'  # Close the span after adding conversion
            elif "pay_rate" in key and "pay_rate_conversion" in jobData:
                conversion = jobData["pay_rate_conversion"]
                formatted_value += f' {conversion}</span>'  # Close the span after adding conversion
            else:
                formatted_value += '</span>'  # Close the span if no conversion is added

            formatted_key = key.replace("_", " ").title()
            gridLayout.addWidget(QLabel(f"{formatted_key}: {formatted_value}"), row, col)
            row += 1
            if row >= 6:  # Adjust the grid layout for a new column
                row, col = 0, col + 1

        return jobDataGroupBox

    def onJobComboBoxChange(self, index):
        # Assuming index refers to the new selected index in jobComboBox
        # You might want to fetch new job data based on this index and update the UI
        selected_title = self.jobComboBox.currentText()
        job_title, po_order_number = selected_title.split(" - ", 1) if " - " in selected_title else (None, None)
        if job_title and po_order_number:
            jobData = self.get_job_data(job_title, po_order_number)
            if jobData:
                # Now, update the UI with this jobData
                self.update_job_info(self.possibleJobDataLayout, jobData=jobData)
                self.jobData = jobData

    def update_job_info(self, layout, comboBox=None, jobData=None):
        if comboBox:
            selected_title = comboBox.currentText()
            job_title, po_order_number = selected_title.split(" - ", 1) if " - " in selected_title else (None, None)
            if not job_title or not po_order_number:
                layout.addWidget(QLabel("Invalid job selection."))
                return
            jobData = self.get_job_data(job_title, po_order_number)

        if jobData:
            jobDataGroupBox = self.create_job_data_groupbox(jobData)
            self.clear_layout(layout)
            layout.addWidget(jobDataGroupBox)
        else:
            layout.addWidget(QLabel("No data available for the selected job."))

    @staticmethod
    def check_employee_id(employee_id):
        if employee_id is None:
            print("Employee ID is missing.")
            return False
        return True

    @staticmethod
    def get_employer_id(company):
        client_query = "SELECT id FROM clients WHERE employer_company = %s"
        client_result = execute_query(client_query, (company,), fetch_mode="one")
        if not client_result:
            print("Employer not found in the database.")
            return None
        return client_result[0]

    def validate_dates(self, start_date_str, end_date_str, hired_date):
        # Ensure date strings are in the correct format
        start_date_str = start_date_str.strftime("%Y-%m-%d") if isinstance(start_date_str,
                                                                           datetime.date) else start_date_str
        end_date_str = end_date_str.strftime("%Y-%m-%d") if isinstance(end_date_str, datetime.date) else end_date_str

        # Convert start and end dates from string to QDate
        start_date = QDate.fromString(start_date_str, "yyyy-MM-dd")
        end_date = QDate.fromString(end_date_str, "yyyy-MM-dd")
        if not (start_date <= hired_date <= end_date):
            reply = QMessageBox.question(self, "Confirm Action",
                                         "The hired date is not within the job order start and end dates. "
                                         "Do you want to save this employee to this job anyway?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            return reply == QMessageBox.Yes
        return True

    def validate_pay(self, pay_rate):
        if not pay_rate:
            QMessageBox.warning(self, "Pay Rate Missing", "Pay rate cannot be empty. Please enter a value.")
            return False
        else:
            return True

    def performAddAction(self, employee_id):
        if not self.check_employee_id(employee_id):
            return

        job_order_id, po_order_number = self.job_data_values()
        start_date_str, end_date_str = self.jobData.get('start_date'), self.jobData.get('end_date')
        company = self.jobData.get('company')
        employer_id = self.get_employer_id(company)
        if employer_id is None:
            return

        pay_rate, pay_conversion, hired_date = self.extract_pay_details()
        if not self.validate_pay(pay_rate) or not self.validate_dates(start_date_str, end_date_str, hired_date):
            return

        self.update_job2employer_ids(employee_id, job_order_id, employer_id)
        self.update_employees(employee_id, po_order_number, pay_rate, pay_conversion, hired_date)
        change_active_needed_employees(employer_id, job_order_id)
        self.finalize_action("Employee has been added to the job successfully.")

    def performChangeAction(self, employee_id):
        if not self.check_employee_id(employee_id):
            return

            # Retrieve current job order and client ID
        old_job_order_id, old_client_id = retrieve_current_job_order(employee_id)
        if not old_job_order_id:
            print("No current job order found for the employee.")
            return
        change_active_needed_employees(old_client_id, old_job_order_id, subtract_needed_employees=False)

        # Assume new job order details are stored in self.jobData
        new_job_order_id, po_order_number = self.job_data_values()
        company = self.jobData.get('company')
        new_client_id = self.get_employer_id(company)
        if new_client_id is None:
            return

        pay_rate, pay_conversion, hired_date = self.extract_pay_details()
        if not pay_rate:
            QMessageBox.warning(self, "Pay Rate Missing", "Pay rate cannot be empty. Please enter a value.")
            return

        # Begin transaction (pseudo-code, replace with actual transaction handling)
        try:
            # Archive current job order details
            self.archive_and_delete_employee_job_order(employee_id, old_job_order_id)

            # Update job2employer_ids with the new job order and client ID
            self.update_job2employer_ids(employee_id, new_job_order_id, new_client_id)
            change_active_needed_employees(new_client_id, new_job_order_id)

            # Update the employees table with the new details
            self.update_employees(employee_id, po_order_number, pay_rate, pay_conversion, hired_date)

            # Commit transaction here (pseudo-code)
            print("Employee job order changed successfully.")
            self.finalize_action("Employee job order changed successfully.")
        except Exception as e:
            # Rollback transaction here (pseudo-code)
            print(f"An error occurred: {e}")
            QMessageBox.critical(self, "Error", "An error occurred while changing the job order.")

    def job_data_values(self):
        return self.jobData.get('id'), self.jobData.get('po_order_number')

    def extract_pay_details(self):
        pay_rate = self.payLineEdit.text()
        pay_conversion = self.payTypeComboBox.currentText()
        hired_date = QDate.fromString(self.dateEdit.date().toString("yyyy-MM-dd"), "yyyy-MM-dd")
        return pay_rate, pay_conversion, hired_date

    @staticmethod
    def update_job2employer_ids(employee_id, job_order_id, employer_id):
        insert_query = "INSERT INTO job2employer_ids (employee_id, job_order_id, client_id) VALUES (%s, %s, %s)"
        execute_query(insert_query, (employee_id, job_order_id, employer_id))

    def update_employees(self, employee_id, po_order_number, pay_rate, pay_conversion, hired_date):
        # Convert QDate to string in 'YYYY-MM-DD' format for MySQL
        hired_date_str = hired_date.toString("yyyy-MM-dd")

        update_query = """
            UPDATE employees 
            SET job_id = %s, 
                pay = %s, 
                pay_conversion = %s, 
                hired_date = %s, 
                availability = 'W', 
                employee_type = %s 
            WHERE id = %s
            """
        execute_query(update_query, (
            po_order_number, pay_rate, pay_conversion, hired_date_str,
            self.jobData.get('position_type'), employee_id))

    def finalize_action(self, message):
        self.employeeAdded.emit()
        QMessageBox.information(self, "Action Completed", message)
        self.accept()

    @staticmethod
    def clear_layout(layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

import re
from pathlib import Path

from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot, QDate
from PyQt5.QtGui import QTextDocument, QIcon
from PyQt5.QtWidgets import *

from resources.tools import resource_path, load_json_file, execute_query

application_path = str(resource_path(Path.cwd()))


class EditCompanyDialog(QDialog):
    """
    A dialog for editing job information, dynamically generating fields based on provided data.

    Attributes:
        dataUpdated (pyqtSignal): Signal emitted when data is updated successfully.
        job_id (int): The ID of the job being edited.
        table_name (str): The name of the database table where job data is stored.
        job_data (list): A list of dictionaries containing job data.
    """
    dataUpdated = pyqtSignal()

    def __init__(self, job_id: int, table_name: str, job_data: list, parent=None):
        """
        Initializes the EditEmployeeDialog with the given job ID, table name, and job data.

        Args:
            job_id (int): The ID of the job to edit.
            table_name (str): The name of the database table.
            job_data (list): The job data to be edited.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.job_id = job_id
        self.table_name = table_name
        self.job_data = job_data
        self.initUI()
        self.resize(600, 350)

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
        Iterates over the job data and adds a form field for each data item.
        """
        for item in self.job_data:
            self.addFieldsForItem(item)

    def addFieldsForItem(self, item: dict):
        """
        Adds form fields for the given item to the form layout.

        Args:
            item (dict): A dictionary containing the details of the item to add to the form.
        """
        db_keys = item['db_key']
        label_texts = [self.formatLabelText(key) for key in db_keys if key]
        current_values = self.getCurrentValues(item['value_widget'].text(), db_keys) if isinstance(item['value_widget'],
                                                                                                   (QLineEdit,
                                                                                                    QLabel)) else []

        for index, key in enumerate(db_keys):
            if key:  # Ensure key is not None
                # Create a horizontal layout to hold the label, line edit, and button
                layout = QHBoxLayout()

                if isinstance(item['value_widget'], (QTextEdit, QListWidget)):
                    # Create widgets
                    label = QLabel(label_texts[index])
                    lineEdit = QLineEdit()
                    browseButton = QPushButton("Browse")
                    browseButton.clicked.connect(lambda _, le=lineEdit: self.onBrowseClicked(le))

                    # Add widgets to the horizontal layout
                    layout.addWidget(label)
                    layout.addWidget(lineEdit)  # Placeholder for displaying file path or similar
                    layout.addWidget(browseButton)

                    # Add the horizontal layout to the form layout
                    rowWidget = QWidget()
                    rowWidget.setLayout(layout)
                    self.formLayout.addRow(rowWidget)

                    # Track the line edit and browse button for accessing their values later
                    self.fields[key] = lineEdit

                elif isinstance(item['value_widget'], (QLineEdit, QLabel)):
                    if key == "position_type":
                        comboBox = QComboBox()
                        comboBox.addItems(
                            ['Direct Placement', 'Contract', 'Contract to Hire', 'Full Time/Contract', '1099'])
                        self.formLayout.addRow(QLabel(label_texts[index]), comboBox)
                        self.fields[key] = comboBox
                    else:
                        lineEdit = QLineEdit(current_values[index] if current_values else "")
                        self.formLayout.addRow(QLabel(label_texts[index]), lineEdit)
                        self.fields[key] = lineEdit

    @pyqtSlot()
    def onBrowseClicked(self, lineEdit):
        filePath, _ = QFileDialog.getOpenFileName(self, "Select File", "",
                                                  "Word Documents (*.docx *.doc);;"
                                                  "PDF Files (*.pdf);;"
                                                  "Text Files (*.txt)")
        if filePath:
            # Update the QLineEdit with the selected file path
            lineEdit.setText(filePath)

    def getCurrentValues(self, text: str, db_keys: list) -> list:
        """
        Extracts and returns the current values from the given HTML text based on the database keys.

        Args:
            text (str): The HTML text from which to extract values.
            db_keys (list): A list of database keys corresponding to the values in the text.

        Returns:
            list: A list of values extracted from the text.
        """
        plain_text = self.stripHtmlTags(text)
        return [plain_text] * len(db_keys)

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

        # Gather new values for each db_key and check their formats
        for key, widget in self.fields.items():
            # Correctly handle different widget types to get text_value
            if isinstance(widget, QLineEdit):
                text_value = widget.text()
            elif isinstance(widget, QComboBox):
                text_value = widget.currentText()
            else:
                text_value = None  # Add appropriate handling for other widget types if necessary

            if text_value == 'N/A':
                continue

            if key == 'bill_rate':
                # Check and parse bill rate for both $/hr and $/yr
                bill_rate_match = re.match(r'^(\d+(\.\d+)?)\s*-\s*(\d+(\.\d+)?)\s*(\$\/hr|\$\/yr)$', text_value)
                if bill_rate_match:
                    updated_data['bill_rate_min'] = bill_rate_match.group(1)
                    updated_data['bill_rate_max'] = bill_rate_match.group(3)
                    updated_data['bill_rate_conversion'] = bill_rate_match.group(5)
                else:
                    error_messages.append("Bill rate must be in the form 'float - float $/hr or $/yr'.")
            elif key == 'pay_rate':
                # Check and parse pay rate for both $/hr and $/yr
                pay_rate_match = re.match(r'^(\d+(\.\d+)?)\s*(\$\/hr|\$\/yr)$', text_value)
                if pay_rate_match:
                    updated_data['pay_rate'] = pay_rate_match.group(1)
                    updated_data['pay_conversion'] = pay_rate_match.group(2)
                else:
                    error_messages.append("Pay rate must be in the form 'float $/hr or $/yr'.")
            elif 'date' in key:
                # Attempt to parse the date text into a QDate object in various common formats
                date_formats = ['dd/MM/yyyy', 'MM/dd/yyyy', 'yyyy-MM-dd']
                date_obj = None
                for fmt in date_formats:
                    date_obj = QDate.fromString(text_value, fmt)
                    if date_obj.isValid():
                        break

                if date_obj and date_obj.isValid():
                    # If valid, format the date into yyyy-MM-dd for database
                    updated_data[key] = date_obj.toString('yyyy-MM-dd')
                else:
                    # If not valid, add an error message and skip updating this field
                    error_messages.append(
                        f"{key} must be in a valid date format (DD/MM/YYYY, MM/DD/YYYY, or YYYY-MM-DD).")
                    continue
            else:
                updated_data[key] = text_value

        if error_messages:
            # If there are any formatting errors, show them to the user and abort the save.
            QMessageBox.warning(self, "Input Error", "\n".join(error_messages))
            return

        # Update the database and UI fields with the new values
        for item in self.job_data:
            db_keys = item['db_key']
            for key in db_keys:
                if key in updated_data:  # Ensure we only update keys that were present in the form
                    value = updated_data[key]
                    if value in [None, 'N/A', 'NULL', 'None', '']:
                        value = 'NULL'
                    query = f"UPDATE {self.table_name} SET {key} = %s WHERE id = %s"
                    execute_query(query, (value, self.job_id))

        self.dataUpdated.emit()
        self.accept()

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
        self.setWindowIcon(QIcon(str(Path(application_path, 'resources', 'icons', 'crm-icon-high-seas.png'))))
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
        self.tempMsgBox.setWindowIcon(QIcon(str(Path(application_path, 'resources', 'icons',
                                                     'crm-icon-high-seas.png'))))
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

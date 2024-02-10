from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QTextDocument

from resources.tools.helpful_functions import *


class EditCompanyDialog(QDialog):
    """
    A dialog for editing company information, dynamically generating fields based on provided data.

    Attributes:
        dataUpdated (pyqtSignal): Signal emitted when data is updated successfully.
        company_id (int): The ID of the company being edited.
        table_name (str): The name of the database table where company data is stored.
        company_data (list): A list of dictionaries containing company data.
    """
    dataUpdated = pyqtSignal()

    def __init__(self, company_id: int, table_name: str, company_data: list, parent=None):
        """
        Initializes the EditEmployeeDialog with the given company ID, table name, and company data.

        Args:
            company_id (int): The ID of the company to edit.
            table_name (str): The name of the database table.
            company_data (list): The company data to be edited.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.company_id = company_id
        self.table_name = table_name
        self.company_data = company_data
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
        Iterates over the company data and adds a form field for each data item.
        """
        for item in self.company_data:
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
                widget = QLineEdit(current_values[index])
                self.formLayout.addRow(QLabel(label_texts[index]), widget)
                self.fields[key] = widget

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
        # First, gather new values for each db_key
        updated_data = {}
        error_messages = []

        for key, widget in self.fields.items():
            text_value = widget.text().strip()

            # Validate email
            if key == 'contact_email' and text_value:
                if not re.match(r"[^@]+@[^@]+\.[^@]+", text_value):
                    error_messages.append(f"{key} must be a valid email address.")
                    continue

            # Validate billing allowance as a decimal
            if key == 'billing_allowance' and text_value:
                try:
                    float(text_value)  # Attempt to convert text to float
                except ValueError:
                    error_messages.append(f"{key} must be a valid decimal number.")
                    continue

            # Here, you can add more validations as needed, such as for 'contact_phone'

            updated_data[key] = text_value

        # If there are validation errors, show them and abort the save
        if error_messages:
            QMessageBox.warning(self, "Validation Error", "\n".join(error_messages))
            return

        # Update the database and UI fields with the new values
        for item in self.company_data:
            db_keys = item['db_key']
            for key in db_keys:
                if key in updated_data:
                    value = updated_data[key] if updated_data[key] not in [None, 'N/A', 'NULL', 'None',
                                                                           ''] else 'NULL'
                    query = f"UPDATE {self.table_name} SET {key} = %s WHERE id = %s"
                    execute_query(query, (value, self.company_id))

            # Update the corresponding value_widget in company_data
            new_text = self.concatenate_values(db_keys, [updated_data.get(key, '') for key in db_keys])
            formatted_value = f'<span style="color: grey;">{new_text}</span>'
            item['value_widget'].setText(formatted_value)

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

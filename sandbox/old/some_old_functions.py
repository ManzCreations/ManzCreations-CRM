import importlib

def dynamic_import(module_name):
    module = importlib.import_module(module_name)
    return module

def setupHeaders(self):
    """Sets up the employer information header and billing allowance subheader."""
    self.gridLayout = QGridLayout()

    employerFont = QFont()
    employerFont.setBold(True)

    employerCompanyLabel = QLabel(f"Employer: {self.employerData.get('Employer Company', 'N/A')}")
    employerCompanyLabel.setFont(employerFont)
    employerCompanyLabel.setStyleSheet("color: blue;")
    self.gridLayout.addWidget(employerCompanyLabel, 0, 0)

    contactPersonLabel = QLabel(f"Contact: {self.employerData.get('Contact Person', 'N/A')}")
    contactPersonLabel.setFont(employerFont)
    contactPersonLabel.setStyleSheet("color: blue;")
    self.gridLayout.addWidget(contactPersonLabel, 0, 1)

    billingAllowance = self.employerData.get('Billing Allowance', 0)
    numericValue = billingAllowance.replace('$', '').replace(',', '')
    try:
        formattedAllowance = "${:,.2f}".format(Decimal(numericValue))
    except Exception as e:
        formattedAllowance = "N/A"
    billingAllowanceLabel = QLabel(f"Billing Allowance: {formattedAllowance}")
    subheaderFont = QFont()
    subheaderFont.setItalic(True)
    billingAllowanceLabel.setFont(subheaderFont)
    self.gridLayout.addWidget(billingAllowanceLabel, 1, 0, 1, 2)


def setupEmployeeSelection(self):
    """Sets up the employee selection field and button."""
    self.employeeLineEdit = QLineEdit()
    self.employeeLineEdit.setPlaceholderText("Type employee name...")
    self.employeeLineEdit.setValidator(QRegExpValidator(QRegExp("[A-Za-z ]+")))

    selectEmployeeButton = QPushButton("Select Employee")
    selectEmployeeButton.clicked.connect(self.openEmployeeSelectionDialog)
    self.gridLayout.addWidget(self.employeeLineEdit, 2, 0)
    self.gridLayout.addWidget(selectEmployeeButton, 2, 1)


def setupJobOrderFields(self):
    """Sets up input fields for job order details including validators."""
    locationValidator = QRegExpValidator(QRegExp("[0-9A-Za-z ]+"))
    paymentValidator = QRegExpValidator(QRegExp("^\\d*\\.?\\d+$"))  # Currency format
    idValidator = QRegExpValidator(QRegExp("[A-Za-z0-9-]+"))

    self.locationLineEdit = QLineEdit()
    self.locationLineEdit.setValidator(locationValidator)
    self.paymentLineEdit = QLineEdit()
    self.paymentLineEdit.setValidator(paymentValidator)
    self.poOrderNumberLineEdit = QLineEdit()
    self.poOrderNumberLineEdit.setValidator(idValidator)

    self.hireDateEdit = QDateEdit(calendarPopup=True)
    self.hireDateEdit.setDisplayFormat("MM/dd/yyyy")
    self.finishDateEdit = QDateEdit(calendarPopup=True)
    self.finishDateEdit.setDisplayFormat("MM/dd/yyyy")

    self.jobIDEdit = QLineEdit()
    self.jobIDEdit.setValidator(idValidator)

    self.paymentTypeCombo = QComboBox()
    self.paymentTypeCombo.addItems(["Hourly", "Yearly"])

    self.paymentLayout = QVBoxLayout()
    self.addJobOrderFieldToLayout("Location:", self.locationLineEdit)
    self.addPaymentSection()
    self.addJobOrderFieldToLayout("Hire Date:", self.hireDateEdit)
    self.addJobOrderFieldToLayout("Finish Date:", self.finishDateEdit)
    self.addJobOrderFieldToLayout("Job ID:", self.jobIDEdit)
    self.addJobOrderFieldToLayout("PO Order Number:", self.poOrderNumberLineEdit)


class EditEmployeeDialog(QDialog):
    dataUpdated = pyqtSignal()

    def __init__(self, employee_id, table_name, employee_data, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.table_name = table_name
        self.employee_data = employee_data
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.formLayout = QFormLayout()
        self.fields = {}
        self.initializeForm()
        self.addControlButtons()

        layout = QVBoxLayout(self)
        self.formLayout = QFormLayout()
        self.fields = {}

        for item in self.employee_data:
            db_keys = item['db_key']
            label_texts = [self.format_label_text(key) for key in db_keys if key]

            current_values = self.get_current_values(item['value_widget'].text(), db_keys)
            for index, key in enumerate(db_keys):
                if key:  # Ensure key is not None
                    if 'conversion' in key:
                        combo = QComboBox()
                        combo.addItems(["$/hr", "$/yr"])
                        combo.setCurrentText(current_values[index])
                        self.formLayout.addRow(QLabel(label_texts[index]), combo)
                        self.fields[key] = combo
                    else:
                        edit = QLineEdit(current_values[index])
                        self.formLayout.addRow(QLabel(label_texts[index]), edit)
                        self.fields[key] = edit

        layout.addLayout(self.formLayout)

        # Buttons
        saveButton = QPushButton("Save")
        cancelButton = QPushButton("Cancel")
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(saveButton)
        buttonLayout.addWidget(cancelButton)
        layout.addLayout(buttonLayout)

        saveButton.clicked.connect(self.onSave)
        cancelButton.clicked.connect(self.reject)

        self.setLayout(layout)

    @staticmethod
    def format_label_text(key):
        # Remove underscores and capitalize words
        return ' '.join(word.capitalize() for word in key.split('_'))

    def get_current_values(self, text, db_keys):
        plain_text = self.strip_html_tags(text)

        if len(db_keys) > 1:
            if "first_name" in db_keys and "last_name" in db_keys:
                return self.split_name(plain_text)
            elif "address" in db_keys and "city" in db_keys and "state" in db_keys and "zipcode" in db_keys:
                return self.split_address(plain_text)
            elif any("conversion" in key for key in db_keys if key is not None):
                return self.split_conversion(plain_text)
        return [plain_text] * len(db_keys)

    def add_conversion_fields(self, item, db_keys):
        label_text = item['label_text']
        current_values = self.get_current_values(item['value_widget'].text(), db_keys)
        for index, key in enumerate(db_keys):
            if 'conversion' in key:
                combo = QComboBox()
                combo.addItems(["$/hr", "$/yr"])
                combo.setCurrentText(current_values[index])
                self.formLayout.addRow(QLabel(label_text), combo)
                self.fields[key] = combo
            else:
                edit = QLineEdit(current_values[index])
                self.formLayout.addRow(QLabel(label_text), edit)
                self.fields[key] = edit

    @staticmethod
    def split_conversion(text):
        # Assuming the text format is "12.00 $/hr" or similar
        match = re.match(r'(\d+\.\d+)\s+(\$\S+)', text)
        if match:
            return [match.group(1), match.group(2)]
        else:
            # Fallback if the text does not match the expected format
            return [text, '']

    @staticmethod
    def split_name(name):
        # Split name into first and last name based on provided logic
        parts = name.split()
        if len(parts) > 2:
            # More complex names with middle names or initials
            first_name = " ".join(parts[:-2])
            last_name = " ".join(parts[-2:])
        elif len(parts) == 2:
            # Simple first and last name
            first_name, last_name = parts
        else:
            # Fallback to using the whole name as first name if splitting is not possible
            first_name = name
            last_name = ""
        return [first_name, last_name]

    @staticmethod
    def split_address(address):
        # Use regex to split address into components
        match = re.match(r'^(.*),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})$', address)
        if match:
            return [match.group(1), match.group(2), match.group(3), match.group(4)]
        else:
            # Fallback if address does not match expected format
            return [address, "", "", ""]

    def onSave(self):
        updated_data = {}
        # First, gather new values for each db_key
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                updated_data[key] = widget.text()
            elif isinstance(widget, QComboBox):
                updated_data[key] = widget.currentText()

        # Then, update each field in the database and prepare updated HTML for value_widgets
        for item in self.employee_data:
            db_keys = item['db_key']
            new_values = [updated_data[key] for key in db_keys if key in updated_data]
            if len(new_values) > 1:
                # Special handling for fields that need to be concatenated
                new_text = self.concatenate_values(db_keys, new_values)
            else:
                new_text = new_values[0] if new_values else ""
            formatted_value = f'<span style="color: grey;">{new_text}</span>'

            # Update the database
            for key in db_keys:
                if key and key in updated_data:  # Ensure we only update keys that were present in the form
                    query = f"UPDATE {self.table_name} SET {key} = %s WHERE id = %s"
                    execute_query(query, (updated_data[key], self.employee_id))

            # Update the corresponding value_widget in employee_data
            item['value_widget'].setText(formatted_value)

        self.dataUpdated.emit()
        self.accept()

    @staticmethod
    def concatenate_values(db_keys, values):
        # Custom logic to concatenate values based on the specific keys
        if 'first_name' in db_keys and 'last_name' in db_keys:
            return ' '.join(values)  # Simple space join for names
        elif 'address' in db_keys and 'city' in db_keys:
            # Assuming values follow the order: [address, city, state, zipcode]
            return ', '.join(values[:2]) + ', ' + ' '.join(values[2:])  # Custom format for address
        # Add more conditions as needed
        return ' '.join(values)  # Default join

    @staticmethod
    def strip_html_tags(text):
        """Utility function to remove HTML tags from a string."""
        doc = QTextDocument()
        doc.setHtml(text)
        return doc.toPlainText()
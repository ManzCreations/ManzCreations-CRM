from decimal import Decimal

from PyQt5.QtCore import QRegExp, QDate, QPoint, Qt
from PyQt5.QtGui import QRegExpValidator, QKeyEvent

from resources.tools.helpful_functions import *
from resources.tools.mydb import *


class AddNoteButton(QPushButton):
    def __init__(self, icon, notesList, parent=None):
        super().__init__(icon, "", parent)
        self.clicked.connect(self.addNote)
        self.notesList = notesList

    def addNote(self):
        dialog = NoteDialog(self.parent())
        if dialog.exec_():
            noteTitle = dialog.titleEdit.text()
            noteText = dialog.noteEdit.toPlainText()
            self.notesList.addNote(noteTitle, noteText)


class FocusLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.parent().focusNextChild()
        else:
            super().keyPressEvent(event)


class NoteDialog(QDialog):
    def __init__(self, parent=None, title="", text=""):
        super().__init__(parent)  # Ensure parent is the first argument
        self.setWindowTitle("Edit Note" if title else "Add Note")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        layout = QVBoxLayout(self)

        self.titleEdit = FocusLineEdit(title)
        self.titleEdit.setParent(self)  # Set parent for the FocusLineEdit
        layout.addWidget(self.titleEdit)

        self.noteEdit = QTextEdit(text)
        layout.addWidget(self.noteEdit)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)


class EmployeeSelectionDialog(QDialog):
    """
    A dialog for selecting an employee from a tree structure.

    The top-level items in the tree are employees, and the child items are their details.
    Allows selection of an employee for further actions like creating a job order.

    Functions:
    - __init__: Initializes the EmployeeSelectionDialog.
    - setup_ui: Sets up the user interface components and layout.
    - populate_tree: Populates the tree widget with employee data.
    - on_item_double_clicked: Slot to handle double-click events on tree widget items.
    - accept: Handles the acceptance (OK button clicked) of the dialog.
    - openEmployeeSelectionDialog: Opens the dialog to select an employee for the job order.
    - submitJobOrder: Collects data from fields and handles job order submission logic.

    Attributes:
    - treeWidget (QTreeWidget): Widget to display and select employees.
    - buttonBox (QDialogButtonBox): Contains buttons for accepting or canceling the dialog.
    - selected_employee_name (Optional[str]): The name of the selected employee.
    - selected_employee_id (Optional[int]): The ID of the selected employee.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nameFilterEdit = QLineEdit()
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.treeWidget = QTreeWidget(self)
        self.selected_employee_name = None
        self.selected_employee_id = None
        self.setWindowTitle("Select Employee")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.setup_ui()
        self.populate_tree()

        # Connect the double click signal to the slot
        self.treeWidget.itemDoubleClicked.connect(self.on_item_double_clicked)

    def setup_ui(self):
        """
        Set up the user interface components and layout.
        """

        # Create a QVBoxLayout instance
        layout = QVBoxLayout()

        # Text edit field to filter names
        self.nameFilterEdit.setPlaceholderText("Filter names...")
        self.nameFilterEdit.textChanged.connect(self.filterNames)
        layout.addWidget(self.nameFilterEdit)

        # Tree widget to display employees and their details
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(["Employee", "Value"])
        layout.addWidget(self.treeWidget)

        # Buttons for dialog control
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        # Set the layout for the dialog
        self.setLayout(layout)

    def filterNames(self):
        filter_text = self.nameFilterEdit.text().lower()

        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            # Assuming the name is the text of the first column of the tree item
            name = item.text(0).lower()
            item.setHidden(filter_text not in name)

    def populate_tree(self):
        """
        Populate the tree widget with employee data.
        Each top-level item is an employee's name, with child items for their details.
        """
        # Fetch data from the database
        result = execute_query("SELECT * FROM employees WHERE availability IN ('NW', '~A')",
                               get_column_indices=True,
                               fetch_mode="all")
        column_indices = result["column_indices"]
        available_employees = result["result"]

        for emp_data in available_employees:
            emp_name = f"{emp_data[column_indices['first_name']]} {emp_data[column_indices['last_name']]}"
            parent = QTreeWidgetItem(self.treeWidget, [emp_name, ""])
            parent.setData(0, Qt.UserRole, emp_data[column_indices['id']])

            # Add desired details as child items
            for detail in ["id", "email", "phone", "zipcode"]:
                value_str = str(emp_data[column_indices[detail]]) if emp_data[
                                                                         column_indices[detail]] is not None else ""
                QTreeWidgetItem(parent, [detail, value_str])

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Slot to handle double-click events on tree widget items.
        It performs the same action as clicking the OK button.
        """
        if item and item.parent() is None:  # Ensure it's a top-level item
            self.selected_employee_id = item.data(0, Qt.UserRole)
            self.selected_employee_name = item.text(0)
            self.accept()  # Accept the dialog

    def accept(self):
        """
        Handle the acceptance (OK button clicked) of the dialog.
        """
        selected_item = self.treeWidget.currentItem()
        # Check if the selected item is a top-level item (an employee)
        if selected_item and selected_item.parent() is None:
            self.selected_employee_id = selected_item.data(0, Qt.UserRole)
            self.selected_employee_name = selected_item.text(0)
            self.parent().employeeId = self.selected_employee_id
        super().accept()  # Proceed with the dialog acceptance


class NotesListWidget(QListWidget):
    # Add functionality for saving, reloading, and editing notes
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes = {}  # Dictionary to store notes with titles
        self.itemDoubleClicked.connect(self.editNote)

    def addNote(self, title, text):
        if title not in self.notes:
            self.addItem(f"{title}: {text[:10]}...")
        self.notes[title] = text

    def editNote(self, item):
        title = ""
        text = ""
        for key, value in self.notes.items():
            if key == item.text().split(":", 1)[0]:
                title = key
                text = value
        dialog = NoteDialog(self, title, text)  # 'self' refers to the parent widget
        if dialog.exec_():
            updatedTitle = dialog.titleEdit.text()
            updatedText = dialog.noteEdit.toPlainText()
            # Update the note
            self.notes.pop(title, None)  # Remove old note if title changed
            self.notes[updatedTitle] = updatedText
            if updatedTitle != title:
                self.takeItem(self.row(item))
                self.addItem(updatedTitle)


class SnapSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setValueToNearestTen(event.pos())

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.setValueToNearestTen(event.pos())

    def setValueToNearestTen(self, pos: QPoint):
        # Calculate the value based on the position of the click
        if self.orientation() == Qt.Horizontal:
            value = self.minimum() + ((self.maximum() - self.minimum()) * pos.x()) / self.width()
        else:
            value = self.minimum() + ((self.maximum() - self.minimum()) * (self.height() - pos.y())) / self.height()

        # Snap value to nearest multiple of 10
        rounded_value = 10 * round(value / 10)
        self.setValue(rounded_value)


class ImportButton(QPushButton):
    def __init__(self, jobDescriptionEdit, parent=None):
        super().__init__("Import", parent)
        self.jobDescriptionEdit = jobDescriptionEdit
        self.clicked.connect(self.importText)

    def importText(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                  "Word Documents (*.docx *.doc);;"
                                                  "PDF Files (*.pdf);;"
                                                  "Text Files (*.txt)")
        if filename:
            self.jobDescriptionEdit.setPlainText(read_text_file(filename))


class JobOrderPage(QDialog):
    """
    Dialog for creating a job order based on selected employer data.

    Allows the user to input details for a new job order and select an employee for the job.
    Validates the selected employee name against the database.

    Functions:
    - __init__: Initializes the JobOrderPage with employer data.
    - openEmployeeSelectionDialog: Opens the dialog to select an employee for the job order.
    - submitJobOrder: Collects data from fields and handles job order submission logic.
    - validateEmployeeName: Validates the entered employee name against the database.
    - checkForSingleMatch: Checks for a single match of the partially entered name in the database.
    - initUI: Initializes the user interface components and validators for input fields.
    - setupHeaders: Sets up the employer information header and billing allowance subheader.
    - setupEmployeeSelection: Sets up the employee selection field and button.
    - setupJobOrderFields: Sets up input fields for job order details including validators.
    - setupSubmitButton: Sets up the submit button for the job order form.
    - addJobOrderFieldToLayout: Utility function to add job order fields to the layout.
    - addPaymentSection: Sets up the payment section including the payment type dropdown.

    Attributes:
    - employerData (dict): Data about the employer for whom the job order is being created.
    - employerId (int): The ID of the employer.
    - employeeId (Optional[int]): The ID of the selected employee for the job order.
    - employeeLineEdit (QLineEdit): Input field for typing the employee's name.
    """

    def __init__(self, employerData: dict, employerId: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Job Order")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.employerData = employerData
        self.employerId = employerId
        self.employeeId = None

        self.initUI()

        self.setupFields()

        # Populate fields if employerData is not empty
        if self.employerData:
            self.populateEmployerFields()

        # For Testing
        self.titleLineEdit.setText("Test")
        self.poOrderNumberEdit.setText("123T")
        self.addressEdit.setText("123 I Dont Know Lane")
        self.cityEdit.setText("Whoville")
        self.zipEdit.setText("13124")
        self.billRateMinEdit.setText("12")
        self.billRateMaxEdit.setText("15")
        self.openingsEdit.setText("25")

    def initUI(self):
        """Initializes the user interface components and validators for input fields."""
        # Master layout for the entire dialog (horizontal)
        masterLayout = QHBoxLayout()

        # Left layout for several sections (vertical)
        leftLayout = QVBoxLayout()
        self.setupTitleAndPositionType(leftLayout)
        self.setupCompanyInformation(leftLayout)
        self.setupJobData(leftLayout)
        self.setupJobSpecifications(leftLayout)
        masterLayout.addLayout(leftLayout)

        # Adding the Job Descriptions section on the right
        self.setupJobDescriptions(masterLayout)

        # Final layout for the entire dialog including the submit button (vertical)
        finalLayout = QVBoxLayout()
        finalLayout.addLayout(masterLayout)

        # Setup submit button
        self.setupSubmitButton(finalLayout)

        # Setup validators
        self.setupValidators()

        # Finalize layout by setting it to the dialog
        self.setLayout(finalLayout)

    def setupTitleAndPositionType(self, layout):
        """Sets up the title and position type group box."""
        titleGroupBox = QGroupBox("Job Information")
        titleLayout = QHBoxLayout()

        titleLayout.addWidget(QLabel("Title:"))
        self.titleLineEdit = QLineEdit()
        titleLayout.addWidget(self.titleLineEdit)

        titleLayout.addWidget(QLabel("PO Order Number:"))
        self.poOrderNumberEdit = QLineEdit()
        titleLayout.addWidget(self.poOrderNumberEdit)

        titleLayout.addWidget(QLabel("Position Type:"))
        self.positionTypeComboBox = QComboBox()
        titleLayout.addWidget(self.positionTypeComboBox)

        titleGroupBox.setLayout(titleLayout)
        layout.addWidget(titleGroupBox)

    def setupCompanyInformation(self, layout):
        """Sets up the company information group box."""
        companyGroupBox = QGroupBox("Company Information")
        companyInfoLayout = QGridLayout()

        # Add widgets for company information
        companyInfoLayout.addWidget(QLabel("Contact Name:"), 0, 0)
        self.contactNameEdit = QLineEdit()
        companyInfoLayout.addWidget(self.contactNameEdit, 0, 1)

        companyInfoLayout.addWidget(QLabel("Company:"), 1, 0)
        self.companyComboBox = QComboBox()
        companyInfoLayout.addWidget(self.companyComboBox, 1, 1)

        companyInfoLayout.addWidget(QLabel("Billing Allowance:"), 1, 2)
        self.billingAllowanceEdit = QLineEdit()
        self.billingAllowanceEdit.setEnabled(False)
        companyInfoLayout.addWidget(self.billingAllowanceEdit, 1, 3)

        companyInfoLayout.addWidget(QLabel("Address:"), 2, 0)
        self.addressEdit = QLineEdit()
        companyInfoLayout.addWidget(self.addressEdit, 2, 1)

        companyInfoLayout.addWidget(QLabel("State:"), 2, 2)
        self.stateComboBox = QComboBox()
        companyInfoLayout.addWidget(self.stateComboBox, 2, 3)

        companyInfoLayout.addWidget(QLabel("City:"), 3, 0)
        self.cityEdit = QLineEdit()
        companyInfoLayout.addWidget(self.cityEdit, 3, 1)

        companyInfoLayout.addWidget(QLabel("Zip:"), 3, 2)
        self.zipEdit = QLineEdit()
        companyInfoLayout.addWidget(self.zipEdit, 3, 3)

        companyGroupBox.setLayout(companyInfoLayout)
        layout.addWidget(companyGroupBox)

    def setupJobData(self, layout):
        """Sets up the job data group box."""
        jobDataGroupBox = QGroupBox("Job Data")
        jobDataLayout = QVBoxLayout()

        billPayRateLayout = QHBoxLayout()

        billPayRateLayout.addWidget(QLabel("Bill Rate"))
        self.billRateMinEdit = QLineEdit()
        billPayRateLayout.addWidget(self.billRateMinEdit)
        billPayRateLayout.addWidget(QLabel(" - "))
        self.billRateMaxEdit = QLineEdit()
        billPayRateLayout.addWidget(self.billRateMaxEdit)
        self.billRateComboBox = QComboBox()
        billPayRateLayout.addWidget(self.billRateComboBox)

        billPayRateLayout.addWidget(QLabel("Pay Rate"))
        self.payRateEdit = QLineEdit()
        billPayRateLayout.addWidget(self.payRateEdit)
        self.payRateComboBox = QComboBox()
        billPayRateLayout.addWidget(self.payRateComboBox)

        jobDataLayout.addLayout(billPayRateLayout)

        startEndDateLayout = QHBoxLayout()
        startEndDateLayout.addWidget(QLabel("Start Date:"))
        self.startDateEdit = QDateEdit(calendarPopup=True)
        startEndDateLayout.addWidget(self.startDateEdit)

        startEndDateLayout.addWidget(QLabel("End Date:"))
        self.endDateEdit = QDateEdit(calendarPopup=True)
        startEndDateLayout.addWidget(self.endDateEdit)
        jobDataLayout.addLayout(startEndDateLayout)

        jobDataGroupBox.setLayout(jobDataLayout)
        layout.addWidget(jobDataGroupBox)

    def setupJobSpecifications(self, layout):
        """Sets up the job specifications group box."""
        jobSpecGroupBox = QGroupBox("Job Specifications")
        jobSpecLayout = QVBoxLayout()

        openingsExperienceLayout = QHBoxLayout()
        openingsExperienceLayout.addWidget(QLabel("Openings:"))
        self.openingsEdit = QLineEdit()
        self.openingsEdit.setFixedWidth(200)
        openingsExperienceLayout.addWidget(self.openingsEdit)
        openingsExperienceLayout.addWidget(QLabel("Experience Level"))
        self.experienceLevelComboBox = QComboBox()
        openingsExperienceLayout.addWidget(self.experienceLevelComboBox)
        jobSpecLayout.addLayout(openingsExperienceLayout)

        # Setup for Requirements as a 2x3 grid of checkboxes
        requirementsGroupBox = QGroupBox("Requirements")
        requirementsLayout = QGridLayout()

        # Example checkboxes (add or modify as needed)
        self.checkBoxes = []
        boxNames = ["OT", "References", "Travel", "Drug Test", "Background Check", "Security Clearance"]
        for i in range(6):  # To create a 2x3 grid
            checkBox = QCheckBox(f"{boxNames[i]}")
            self.checkBoxes.append(checkBox)

            # Adjust the font size of the checkbox
            font = checkBox.font()
            font.setPointSize(font.pointSize() - 1)  # Decrease the font size by 1
            checkBox.setFont(font)

            row = i // 3  # Integer division to get row index
            col = i % 3  # Modulo to get column index
            requirementsLayout.addWidget(checkBox, row, col)  # Offset by 1 due to label row

        requirementsGroupBox.setLayout(requirementsLayout)

        jobSpecLayout.addWidget(requirementsGroupBox)

        onsiteFlexibilityLayout = QHBoxLayout()
        onsiteFlexibilityLayout.addWidget(QLabel("Onsite Flexibility"))
        self.onsiteFlexibilitySlider = SnapSlider(Qt.Horizontal)
        onsiteFlexibilityLayout.addWidget(self.onsiteFlexibilitySlider)
        self.onsiteFlexibilityLabel = QLabel("0% Remote")
        onsiteFlexibilityLayout.addWidget(self.onsiteFlexibilityLabel)
        jobSpecLayout.addLayout(onsiteFlexibilityLayout)

        jobSpecGroupBox.setLayout(jobSpecLayout)
        layout.addWidget(jobSpecGroupBox)

    def setupJobDescriptions(self, layout):
        # Setup for Job Description and Notes
        jobDescriptionGroupBox = QGroupBox("Job Description and Notes")
        jobDescriptionLayout = QVBoxLayout()

        # Job Description
        labelsLayout = QHBoxLayout()
        labelsLayout.addWidget(QLabel("Job Description:"))
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        labelsLayout.addSpacerItem(spacer)
        self.jobDescriptionEdit = QTextEdit()
        self.importDescriptionButton = ImportButton(self.jobDescriptionEdit, self)
        labelsLayout.addWidget(self.importDescriptionButton)
        jobDescriptionLayout.addLayout(labelsLayout)
        jobDescriptionLayout.addWidget(self.jobDescriptionEdit)

        # Notes
        labelsLayout = QHBoxLayout()
        labelsLayout.addWidget(QLabel("Notes:"))
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        labelsLayout.addSpacerItem(spacer)
        self.notesList = NotesListWidget()
        self.addNotesButton = AddNoteButton(QIcon("icons/iconmonstr-plus-square-multiple-lined.svg"),
                                            self.notesList, self)
        labelsLayout.addWidget(self.addNotesButton)
        jobDescriptionLayout.addLayout(labelsLayout)
        jobDescriptionLayout.addWidget(self.notesList)

        jobDescriptionGroupBox.setLayout(jobDescriptionLayout)
        layout.addWidget(jobDescriptionGroupBox)

    def setupSubmitButton(self, layout):
        """Sets up the submit button for the job order form."""
        self.submitButton = QPushButton("Submit Job Order")
        self.submitButton.clicked.connect(self.submitJobOrder)
        layout.addWidget(self.submitButton)

    def setupFields(self):
        # Edit fields
        self.stateComboBox.setEditable(True)  # Make the combo box editable

        # List of 50 US states
        states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
                  "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
                  "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
                  "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
                  "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
                  "New Hampshire", "New Jersey", "New Mexico", "New York",
                  "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
                  "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
                  "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
                  "West Virginia", "Wisconsin", "Wyoming"]

        self.stateComboBox.addItems(states)

        # Do the same for the company
        self.companyComboBox.setEditable(True)

        query = "SELECT employer_company FROM clients"
        result = execute_query(query, fetch_mode="all")
        companies = [item[0] for item in result] if result else []

        self.companyComboBox.addItems(companies)
        self.companyComboBox.currentIndexChanged.connect(self.onCompanyChanged)
        self.companyComboBox.editTextChanged.connect(self.onCompanyEdit)

        # Optionally, set up the completion mode
        completer = QCompleter(states)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.stateComboBox.setCompleter(completer)

        self.onsiteFlexibilitySlider.setTickPosition(QSlider.TicksBelow)
        self.onsiteFlexibilitySlider.setTickInterval(10)
        self.onsiteFlexibilitySlider.setSingleStep(10)
        self.onsiteFlexibilitySlider.setMinimum(0)
        self.onsiteFlexibilitySlider.setMaximum(100)

        # Connect the slider's valueChanged signal
        self.onsiteFlexibilitySlider.valueChanged.connect(self.updateSliderValue)

        self.positionTypeComboBox.addItems(["Direct Placement", "Contract", "Contract to Hire",
                                            "Full Time/Contract", "1099"])

        self.billRateComboBox.addItems(["$/hr", "$/yr"])
        self.payRateComboBox.addItems(["$/hr", "$/yr"])

        self.experienceLevelComboBox.addItems(["GED", "High School Diploma", "Associate's Degree",
                                               "Bachelor's Degree", "Master's Degree", "Doctorate", "Other"])

        # Default Hire Date to current day
        self.startDateEdit.setDate(QDate.currentDate())

        # Default Finish Date to 6 months later
        self.endDateEdit.setDate(QDate.currentDate().addMonths(6))

    def setupValidators(self):
        currencyValidator = QRegExpValidator(QRegExp(r"^(\d{1,3}(,\d{3})*|\d+)(\.\d{1,2})?$"))
        address_validator = QRegExpValidator(QRegExp("^\d+\s[A-Za-z\s]+$"))
        zip_validator = QRegExpValidator(QRegExp("^\d{5}(-\d{4})?$"))
        only_letters_validator = QRegExpValidator(QRegExp("^[A-Za-z]+$"))
        number_validator = QRegExpValidator(QRegExp("^-?\\d+$"))

        self.addressEdit.setValidator(address_validator)
        self.zipEdit.setValidator(zip_validator)
        self.billRateMinEdit.setValidator(currencyValidator)
        self.payRateEdit.setValidator(currencyValidator)
        self.billRateMaxEdit.setValidator(currencyValidator)
        self.cityEdit.setValidator(only_letters_validator)
        self.openingsEdit.setValidator(number_validator)

    def populateEmployerFields(self):
        index = self.companyComboBox.findText(self.employerData.get('Employer Company', 'N/A'))
        self.companyComboBox.setCurrentIndex(index)
        self.contactNameEdit.setText(self.employerData.get('Contact Person', 'N/A'))
        billingAllowance = self.employerData.get('Billing Allowance', 0)
        self.billingAllowanceEdit.setText(self.getBillingAllowanceString(billingAllowance))

    def updateSliderValue(self, value):
        """Updates the label next to the slider with the current value and 'Remote'."""
        self.onsiteFlexibilityLabel.setText(f"{value}% Remote")

    def onCompanyChanged(self, index):
        self.updateContactAndBilling(self.companyComboBox.currentText())

    def onCompanyEdit(self, text):
        self.updateContactAndBilling(text)

    def updateContactAndBilling(self, companyName):
        # Update contact person and billing allowance based on selected company
        query = "SELECT contact_person, billing_allowance FROM clients WHERE employer_company = %s"
        result = execute_query(query, (companyName,), fetch_mode="one")
        if result:
            contact_person, billing_allowance = result
            self.contactNameEdit.setText(contact_person)
            self.billingAllowanceEdit.setText(self.getBillingAllowanceString(billing_allowance))

    @staticmethod
    def getBillingAllowanceString(billingAllowance):
        billingAllowance = str(billingAllowance)
        numericValue = billingAllowance.replace('$', '').replace(',', '')
        try:
            formattedAllowance = "${:,.2f}".format(Decimal(numericValue))
        except Exception as e:
            formattedAllowance = "N/A"
        return formattedAllowance

    def addJobOrderFieldToLayout(self, labelText: str, widget):
        """Utility function to add job order fields to the layout."""
        self.paymentLayout.addWidget(QLabel(labelText))
        self.paymentLayout.addWidget(widget)

    def addPaymentSection(self):
        """Sets up the payment section including the payment type dropdown."""
        paymentHLayout = QHBoxLayout()
        paymentHLayout.addWidget(QLabel("Payment ($):"))
        paymentHLayout.addWidget(self.paymentLineEdit)
        paymentHLayout.addWidget(self.paymentTypeCombo)
        self.paymentLayout.addLayout(paymentHLayout)

    def openEmployeeSelectionDialog(self):
        """Opens a dialog for selecting an employee for the job order."""
        dialog = EmployeeSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.employeeId = dialog.selected_employee_id
            self.employeeLineEdit.setText(dialog.selected_employee_name if self.employeeId else "")

    def submitJobOrder(self):
        """Collects data from fields and handles job order submission logic."""
        # Validate and gather data from input fields
        if not (poOrderNumber := self.validateText(self.poOrderNumberEdit.text(), 15, "PO Order Number")):
            return
        if not (location := self.validateLocation()):
            return
        if not (company := self.validateText(self.companyComboBox.currentText(), 255, "Company Name")):
            return
        start_date = self.startDateEdit.date().toString("yyyy-MM-dd")
        end_date = self.endDateEdit.date().toString("yyyy-MM-dd")
        active_employees = 0
        if not (needed_employees := self.validateInt(self.openingsEdit.text(), "Openings")):
            return
        if not (job_title := self.validateText(self.titleLineEdit.text(), 255, "Job Title")):
            return
        position_type = self.positionTypeComboBox.currentText()
        bill_rate_min = self.validateDecimal(self.billRateMinEdit.text(), "Bill Rate Min")
        bill_rate_max = self.validateDecimal(self.billRateMaxEdit.text(), "Bill Rate Max")
        bill_rate_conversion = self.billRateComboBox.currentText()
        pay_rate = self.validateDecimal(self.payRateEdit.text(), "Pay Rate")
        pay_rate_conversion = self.payRateComboBox.currentText()
        min_experience = self.experienceLevelComboBox.currentText()
        requirements = ", ".join([checkbox.text() for checkbox in self.checkBoxes if checkbox.isChecked()])
        remote = self.getRemoteText()
        job_description_path = self.saveJobDescription(self.jobDescriptionEdit.toPlainText(), job_title, poOrderNumber)
        notes_path = self.saveNotes(job_title, poOrderNumber)

        # Check if the PO Order Number already exists in the database
        if self.checkPoOrderNumberExists(poOrderNumber):
            response = QMessageBox.question(self, "Override Job Order",
                                            f"The PO Order Number {poOrderNumber} is already in use. "
                                            "Would you like to override the existing job order?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if response == QMessageBox.No:
                return  # User chose not to override, exit the function

            # Update existing job order
            self.updateJobOrder(poOrderNumber, location, company, start_date, end_date,
                                active_employees, needed_employees, job_title, position_type,
                                bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate,
                                pay_rate_conversion, min_experience, requirements, remote,
                                job_description_path, notes_path)
        else:
            # Insert new job order
            self.insertJobOrder(poOrderNumber, location, company, start_date, end_date,
                                active_employees, needed_employees, job_title, position_type,
                                bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate,
                                pay_rate_conversion, min_experience, requirements, remote,
                                job_description_path, notes_path)

        self.close()

    def validateText(self, value, max_length, field_name):
        """Validates text fields with length constraints."""
        if len(value) > max_length:
            QMessageBox.warning(self, "Input Error", f"{field_name} must be no more than {max_length} characters.")
            return None
        return value

    def validateDecimal(self, value, field_name):
        """Validates and converts a string to a decimal format."""
        try:
            return "{:.2f}".format(float(value)) if value else None
        except ValueError:
            QMessageBox.warning(self, "Input Error", f"Invalid decimal value for {field_name}. "
                                                     f"Please enter a valid number.")
            return None

    def validateInt(self, value, field_name):
        """Validates and converts a string to an integer."""
        try:
            return int(value)
        except ValueError:
            QMessageBox.warning(self, "Input Error", f"Invalid integer value for {field_name}. "
                                                     f"Please enter a whole number.")
            return None

    def validateLocation(self):
        """Validates and constructs the location string."""
        address = self.addressEdit.text()
        city = self.cityEdit.text()
        state = self.stateComboBox.currentText()
        zipCode = self.zipEdit.text()
        location = f"{address}, {city}, {state} {zipCode}"
        if len(location) > 100:
            QMessageBox.warning(self, "Input Error", "Location string is too long. "
                                                     "Please shorten the address, city, state, or ZIP code.")
            return None
        return location

    def getRemoteText(self):
        """Returns the text for the 'remote' field based on the slider's value."""
        remote_value = self.onsiteFlexibilitySlider.value()
        if remote_value == 0:
            return "On-Site"
        elif remote_value == 100:
            return "Fully Remote"
        else:
            return f"{remote_value}% Remote"

    @staticmethod
    def saveJobDescription(job_description, job_title, poOrderNumber):
        # Create a directory for job descriptions
        job_description_dir = Path('job_descriptions')
        job_description_dir.mkdir(exist_ok=True)

        # Save Job Description
        job_description_path = None
        if job_description.strip():
            job_description_filename = f"{job_title}_{poOrderNumber}_job_description.txt"
            job_description_path = job_description_dir / job_description_filename
            with job_description_path.open("w", encoding="utf-8") as file:
                file.write(job_description)

        return str(job_description_path)

    def saveNotes(self, job_title, poOrderNumber):
        # Create a directory for job descriptions
        job_description_dir = Path('job_descriptions')
        job_description_dir.mkdir(exist_ok=True)

        # Save Notes
        notes_path = None
        if self.notesList.notes:
            notes_filename = f"{job_title}_{poOrderNumber}_notes.txt"
            notes_path = job_description_dir / notes_filename
            with notes_path.open("w", encoding="utf-8") as file:
                for title, note in self.notesList.notes.items():
                    file.write(f"Title: {title}\nNote: {note}\n\n")

        return str(notes_path)

    @staticmethod
    def checkPoOrderNumberExists(poOrderNumber):
        query = "SELECT COUNT(*) FROM job_orders WHERE po_order_number = %s"
        result = execute_query(query, (poOrderNumber,))
        return result and result[0] > 0

    @staticmethod
    def getEmployeeIdByName(name: str) -> int:
        """Retrieves the employee ID based on the provided name."""
        query = "SELECT id FROM employees WHERE CONCAT(first_name, ' ', last_name) = %s"
        result = execute_query(query, (name,))
        if result:
            return result[0]
        return 0  # Return 0 if not found or on error

    @staticmethod
    def insertJobOrder(poOrderNumber, location, company, start_date, end_date,
                       active_employees, needed_employees, job_title, position_type,
                       bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate,
                       pay_rate_conversion, min_experience, requirements, remote,
                       job_description_path, notes_path):
        """Inserts the new job order into the database."""
        # SQL query to insert job order
        query = """
                INSERT INTO job_orders (po_order_number, location, company, start_date, end_date, 
                                        active_employees, needed_employees, job_title, position_type,
                                        bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate, 
                                        pay_rate_conversion, min_experience, requirements, remote, 
                                        job_description_path, notes_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        data = (poOrderNumber, location, company, start_date, end_date, active_employees, needed_employees,
                job_title, position_type, bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate,
                pay_rate_conversion, min_experience, requirements, remote,
                job_description_path, notes_path)

        execute_query(query, data)

    @staticmethod
    def updateJobOrder(poOrderNumber, location, company, start_date, end_date,
                       active_employees, needed_employees, job_title, position_type,
                       bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate,
                       pay_rate_conversion, min_experience, requirements, remote,
                       job_description_path, notes_path):
        """Updates an existing job order in the database."""
        # SQL query to insert job order
        query = """
                UPDATE job_orders
                SET location = %s, company = %s, start_date = %s, end_date = %s, 
                    active_employees = %s, needed_employees = %s, job_title = %s, position_type = %s,
                    bill_rate_min = %s, bill_rate_max = %s, bill_rate_conversion = %s, pay_rate = %s, 
                    pay_rate_conversion = %s, min_experience = %s, requirements = %s, remote = %s, 
                    job_description_path = %s, notes_path = %s
                WHERE po_order_number = %s
            """
        data = (poOrderNumber, location, company, start_date, end_date, active_employees, needed_employees,
                job_title, position_type, bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate,
                pay_rate_conversion, min_experience, requirements, remote,
                job_description_path, notes_path)

        execute_query(query, data)

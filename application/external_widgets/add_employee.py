from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator

from resources.tools.mydb import *


class AddEmployeeDialog(QDialog):
    """
    Dialog for adding a new employee to the database.

    Allows the user to input details for a new employee, including their personal information and job details.
    Validates the input data to ensure it meets specified format requirements.

    Functions:
    - __init__: Initializes the dialog with input fields and validators.
    - getEmployeeData: Returns the entered employee data as a dictionary.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Employee")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.layout = QFormLayout(self)

        # Initialize input fields with labels
        self.fNameEdit = QLineEdit()
        self.fNameEdit.setToolTip("Enter first name (letters only). Example: John")
        self.layout.addRow(QLabel("First Name:"), self.fNameEdit)

        self.lNameEdit = QLineEdit()
        self.lNameEdit.setToolTip("Enter last name (letters only). Example: Doe")
        self.layout.addRow(QLabel("Last Name:"), self.lNameEdit)

        self.emailEdit = QLineEdit()
        self.emailEdit.setToolTip("Enter a valid email address. Example: example@email.com")
        self.layout.addRow(QLabel("Email:"), self.emailEdit)

        self.phoneEdit = QLineEdit()
        self.phoneEdit.setToolTip("Enter phone number. Example formats: +1 (123) 456-7890, 123-456-7890")
        self.layout.addRow(QLabel("Phone Number:"), self.phoneEdit)

        self.addressEdit = QLineEdit()
        self.addressEdit.setToolTip(
            "Enter address with numeric street number followed by street name. Example: 123 Main Street")
        self.layout.addRow(QLabel("Address:"), self.addressEdit)

        self.cityEdit = QLineEdit()
        self.cityEdit.setToolTip("Enter city name (letters only). Example: New York")
        self.layout.addRow(QLabel("City:"), self.cityEdit)

        self.stateEdit = QLineEdit()
        self.stateEdit.setToolTip("Enter state name (letters only). Example: California")
        self.layout.addRow(QLabel("State:"), self.stateEdit)

        self.zipEdit = QLineEdit()
        self.zipEdit.setToolTip("Enter zip code (numbers and optional hyphen). Example: 12345 or 12345-6789")
        self.layout.addRow(QLabel("Zip Code:"), self.zipEdit)

        # Initialize the 'Resume Path' row
        self.resumePathEdit = QLineEdit()
        self.resumePathEdit.setToolTip("Enter the path to the resume. Example: C:/Users/JohnDoe/resume.pdf")

        # Browse button
        self.browseButton = QPushButton("Browse...")
        self.browseButton.clicked.connect(self.openFileDialog)

        # QHBoxLayout for 'Resume Path' and 'Browse' button
        resumePathLayout = QHBoxLayout()
        resumePathLayout.addWidget(self.resumePathEdit)
        resumePathLayout.addWidget(self.browseButton)

        # Add row to the main layout
        self.layout.addRow(QLabel("Resume Path:"), resumePathLayout)

        # Set up validators
        only_letters_validator = QRegExpValidator(QRegExp("^[A-Za-z]+$"))
        first_name_validator = QRegExpValidator(QRegExp("^[A-Za-z]+(?:\s[A-Za-z\.]+)?$"))
        last_name_validator = QRegExpValidator(QRegExp("^[A-Za-z]+(?:\s(?:Jr\.|Sr\.|III|IV|V|VI|[A-Za-z]+))?$"))
        self.fNameEdit.setValidator(first_name_validator)
        self.lNameEdit.setValidator(last_name_validator)
        self.cityEdit.setValidator(only_letters_validator)
        self.stateEdit.setValidator(only_letters_validator)

        email_validator = QRegExpValidator(QRegExp("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"))
        self.emailEdit.setValidator(email_validator)

        phone_validator = QRegExpValidator(QRegExp("^\+?1?\s?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}$"))
        self.phoneEdit.setValidator(phone_validator)

        address_validator = QRegExpValidator(QRegExp("^\d+\s[A-Za-z\s]+$"))
        self.addressEdit.setValidator(address_validator)

        zip_validator = QRegExpValidator(QRegExp("^\d{5}(-\d{4})?$"))
        self.zipEdit.setValidator(zip_validator)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

        # For Testing
        self.fNameEdit.setText("Esteban")
        self.lNameEdit.setText("Martinez")
        self.emailEdit.setText("emart@gmail.com")
        self.phoneEdit.setText("+1 (919) 123-4567")
        self.addressEdit.setText("1234 Hi There Lane")
        self.cityEdit.setText("Raleigh")
        self.stateEdit.setText("NC")
        self.zipEdit.setText("27703")

    def openFileDialog(self):
        # Open file dialog to select a file, allowing .txt, .pdf, or .docx files
        filePath, _ = QFileDialog.getOpenFileName(self, "Select Resume", "",
                                                  "Documents (*.txt *.pdf *.docx);;All files (*.*)")
        if filePath:
            self.resumePathEdit.setText(filePath)

    def getEmployeeData(self) -> dict:
        """
        Retrieves the data entered by the user in the dialog and returns it as a dictionary.

        Returns:
            dict: A dictionary containing all the employee data.
        """
        return {
            "first_name": self.fNameEdit.text(),
            "last_name": self.lNameEdit.text(),
            "email": self.emailEdit.text(),
            "phone": self.phoneEdit.text(),
            "address": self.addressEdit.text(),
            "city": self.cityEdit.text(),
            "state": self.stateEdit.text(),
            "zipcode": self.zipEdit.text(),
            "resume_path": self.resumePathEdit.text()
        }

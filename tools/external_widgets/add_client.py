from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator, QIcon

from tools.mydb import *


class AddClientDialog(QDialog):
    """
    Dialog for adding a new client to the database.

    Allows the user to input details for a new client, including their contact person's phone number and email address.

    Functions:
    - __init__: Initializes the dialog with input fields.
    - getClientData: Returns the entered client data as a dictionary.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Client")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.layout = QFormLayout(self)

        # Initialize input fields with labels
        self.employerCompanyEdit = QLineEdit()
        self.layout.addRow(QLabel("Employer Company:"), self.employerCompanyEdit)

        self.contactPersonEdit = QLineEdit()
        self.layout.addRow(QLabel("Contact Person:"), self.contactPersonEdit)

        self.contactPhoneNumberEdit = QLineEdit()
        self.layout.addRow(QLabel("Contact Phone Number:"), self.contactPhoneNumberEdit)

        self.contactEmailAddressEdit = QLineEdit()
        self.layout.addRow(QLabel("Contact Email Address:"), self.contactEmailAddressEdit)

        self.addressEdit = QLineEdit()
        self.layout.addRow(QLabel("Address:"), self.addressEdit)

        self.billingAllowanceEdit = QLineEdit()
        self.layout.addRow(QLabel("Billing Allowance:"), self.billingAllowanceEdit)

        self.activeEmployeesEdit = QLineEdit()
        self.layout.addRow(QLabel("Active Employees:"), self.activeEmployeesEdit)

        # Validators for the input fields
        only_letters_validator = QRegExpValidator(QRegExp("^[A-Za-z]+$"))
        self.contactPersonEdit.setValidator(only_letters_validator)

        email_validator = QRegExpValidator(QRegExp("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"))
        self.contactEmailAddressEdit.setValidator(email_validator)

        phone_validator = QRegExpValidator(QRegExp("^\+?1?\s?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}$"))
        self.contactPhoneNumberEdit.setValidator(phone_validator)

        number_validator = QRegExpValidator(QRegExp(r"^(\d{1,3}(,\d{3})*|\d+)(\.\d{1,2})?$"))
        self.billingAllowanceEdit.setValidator(number_validator)
        self.activeEmployeesEdit.setValidator(number_validator)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

        # For Testing
        self.employerCompanyEdit.setText("John Cena LLC")
        self.contactPersonEdit.setText("Johnathan Cenaly")
        self.contactPhoneNumberEdit.setText("+1 (919) 123-4567")
        self.contactEmailAddressEdit.setText("youdontknowme@gmail.com")
        self.addressEdit.setText("1234 Hi There Lane, Raleigh, NC 27703")
        self.billingAllowanceEdit.setText("100,000,000")
        self.activeEmployeesEdit.setText("5")

    def getClientData(self) -> dict:
        """
        Retrieves the data entered by the user in the dialog, including the contact person's phone number and email
        address, and returns it as a dictionary.

        Returns:
            dict: A dictionary containing all the client data.
        """
        phone_number = self.contactPhoneNumberEdit.text().replace('+1 ', '').replace('(', '').replace(') ', '').replace(
            '-', '')
        return {
            "employer_company": self.employerCompanyEdit.text(),
            "contact_person": self.contactPersonEdit.text(),
            "contact_phone": phone_number,
            "contact_email": self.contactEmailAddressEdit.text(),
            "address": self.addressEdit.text(),
            "billing_allowance": float(self.billingAllowanceEdit.text().replace(',', '')),
            "active_employees": self.activeEmployeesEdit.text(),
        }

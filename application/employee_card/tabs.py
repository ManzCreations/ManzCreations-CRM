import sys
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QMenu, QAction, QApplication

from application.company_card.company_card import ClientCard
from application.employee_card.dialogs import EditEmployeeDialog, AddFieldDialog, ManageJobOrderDialog
from resources.tools.helpful_functions import *
from application.job_order_card.job_order_card import JobOrderCard
from resources.tools.mydb import *


class CardTableWidget(QTableWidget):
    def __init__(self, job_orders, *args, **kwargs):
        super(CardTableWidget, self).__init__(*args, **kwargs)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setMouseTracking(True)  # Enable mouse tracking to show tooltips on hover
        self.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.setupTable(job_orders)
        self.populateTable(job_orders)
        self.disableTable()
        self.adjustColumnResizing()

    def setupTable(self, job_orders):
        if job_orders:
            self.setColumnCount(len(job_orders[0]))
            self.setHorizontalHeaderLabels(job_orders[0].keys())

    def populateTable(self, job_orders):
        self.setRowCount(len(job_orders))
        for row_index, job_order in enumerate(job_orders):
            for col_index, (key, value) in enumerate(job_order.items()):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))  # Set tooltip for each cell
                self.setItem(row_index, col_index, item)

    def onHeaderClicked(self, logicalIndex):
        """
        Sorts the table based on the clicked column header and updates the header to display a sorting arrow.

        Args:
            logicalIndex (int): Index of the clicked column header.

        The method toggles sorting order and updates the table based on the selected column.
        """
        self.currentSortOrder = not getattr(self, 'currentSortOrder', False)
        sorting_order = Qt.AscendingOrder if self.currentSortOrder else Qt.DescendingOrder
        self.sortItems(logicalIndex, sorting_order)

        # Update header icons for sorting indication
        for i in range(self.columnCount()):
            header = self.horizontalHeaderItem(i)
            header.setIcon(QIcon())  # Clear previous icons

        # Set the sort indicator icon
        sort_icon = QIcon("^") if self.currentSortOrder else QIcon("↓")
        self.horizontalHeaderItem(logicalIndex).setIcon(sort_icon)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        delete_col_action = QAction("Delete Column", self)
        context_menu.addAction(delete_col_action)

        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_col_action:
            col = self.columnAt(event.pos().x())
            self.removeColumn(col)

    def disableTable(self):
        rowCount = self.rowCount()
        columnCount = self.columnCount()

        for row in range(rowCount):
            for column in range(columnCount):
                item = self.item(row, column)
                # If there's no item in a cell, create one to ensure it's editable
                if not item:
                    item = QTableWidgetItem()
                    self.setItem(row, column, item)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def adjustColumnResizing(self):
        # Ensure QApplication instance is available for QFontMetrics
        app = QApplication.instance() if QApplication.instance() else QApplication(sys.argv)

        fontMetrics = QFontMetrics(self.font())
        totalWidth = 0

        # Iterate through each column to find the maximum width
        for column in range(self.columnCount()):
            maxWidth = fontMetrics.width(self.horizontalHeaderItem(column).text()) + 50  # Adding some padding

            for row in range(self.rowCount()):
                item = self.item(row, column)
                if item:  # Check if item is not None
                    itemWidth = fontMetrics.width(item.text()) + 50  # Again, adding some padding
                    maxWidth = max(maxWidth, itemWidth)

            self.setColumnWidth(column, maxWidth)
            totalWidth += maxWidth

        # Set the minimum width of the table to accommodate the widest cell or column name
        self.setMinimumWidth(totalWidth)


class GeneralDataTab(QWidget):
    def __init__(self, employee_id=None):
        super().__init__()
        self.employee_id = employee_id
        self.added_fields = {}
        self.ui_fields = []
        self.extra_columns = None
        self.initUI()

    def initUI(self):
        # Main layout for the widget
        self.mainLayout = QVBoxLayout(self)

        # Create group boxes
        generalInfoGroupBox = QGroupBox("General Information")
        jobInfoGroupBox = QGroupBox("Job Information")
        otherInfoGroupBox = QGroupBox("Other Information")

        # Form layouts for group boxes
        generalInfoLayout = QFormLayout()
        jobInfoLayout = QFormLayout()
        otherInfoLayout = QFormLayout()

        # Styling fonts for labels
        titleFont = QFont("Arial", 10, QFont.Bold)
        dataFont = QFont("Arial", 10)

        # Fetching employee data from the database
        query = "SELECT * FROM employees WHERE id = %s"
        data = (self.employee_id,)
        result = execute_query(query, data, fetch_mode="one", get_column_names=True)

        # Create the title label
        titleLabel = QLabel("<h2 style='color: #64bfd1;'>Employee Information</h2>")
        titleLabel.setAlignment(Qt.AlignLeft)
        self.mainLayout.addWidget(titleLabel)

        # Process and display fetched data
        if result and 'result' in result and 'column_names' in result:
            employee_data = dict(zip(result['column_names'], result['result']))

            # Add rows to General Information
            self.addDataRow(generalInfoLayout, "Employee:", "first_name", "last_name", employee_data, titleFont,
                            dataFont)
            self.addAddressRow(generalInfoLayout, employee_data, titleFont, dataFont)
            self.addDataRow(generalInfoLayout, "Phone Number:", "phone", None, employee_data, titleFont, dataFont)
            self.addDataRow(generalInfoLayout, "Availability:", "availability", None, employee_data, titleFont,
                            dataFont)
            self.addDataRow(generalInfoLayout, "Resume Path:", "resume_path", None, employee_data, titleFont,
                            dataFont)

            # Add rows to Job Information
            self.addDataRow(jobInfoLayout, "Job Id:", "job_id", None, employee_data, titleFont, dataFont)
            self.addDataRow(jobInfoLayout, "Current Pay:", "pay", "pay_conversion", employee_data, titleFont, dataFont)
            self.addDataRow(jobInfoLayout, "Hire Date:", "hired_date", None, employee_data, titleFont, dataFont)
            self.addDataRow(jobInfoLayout, "Employee Type:", "employee_type", None, employee_data, titleFont, dataFont)

            # User added data into Other Information
            defined_columns = self.get_defined_columns_for_table("employees")
            actual_columns = self.get_actual_columns_from_db("employees")
            self.add_missing_columns_to_ui(otherInfoLayout, self.employee_id, defined_columns, actual_columns,
                                           titleFont, dataFont)

            # Set layouts to group boxes
            generalInfoGroupBox.setLayout(generalInfoLayout)
            jobInfoGroupBox.setLayout(jobInfoLayout)
            otherInfoGroupBox.setLayout(otherInfoLayout)

            # Add group boxes to the main layout
            self.mainLayout.addWidget(generalInfoGroupBox)
            self.mainLayout.addWidget(jobInfoGroupBox)
            self.mainLayout.addWidget(otherInfoGroupBox)

            # Button on the left
            buttonLayout = QHBoxLayout()

            addButton = QPushButton("Add Information")
            addButton.setIcon(QIcon("icons/iconmonstr-plus-6.svg"))
            addButton.clicked.connect(self.onAddButtonClicked)

            editButton = QPushButton("Edit Information")
            editButton.setIcon(QIcon("icons/iconmonstr-pencil-line-lined.svg"))
            editButton.clicked.connect(self.onEditButtonClicked)

            buttonLayout.addWidget(addButton)
            buttonLayout.addWidget(editButton)
            buttonLayout.addStretch()

            self.mainLayout.addLayout(buttonLayout)

            # Save this for later updates
            self.formLayout = otherInfoLayout

            # Add the horizontal layout to the main layout
            self.mainLayout.addStretch()
            self.setLayout(self.mainLayout)

    def addDataRow(self, layout, label, key1, key2, data, titleFont, dataFont):
        """ Adds a data row to the form layout """
        labelWidget = QLabel(label)
        labelWidget.setFont(titleFont)
        value = f"{data.get(key1, '')} {data.get(key2, '')}".strip() if key2 else data.get(key1, 'N/A')
        # Convert value to a string for comparison, handling None and empty strings explicitly
        value_str = str(value) if value is not None else ""

        # Check if the value, once converted to a string, contains 'none', 'null', 'n/a', or is empty
        if not value or 'none' in value_str.lower() or 'null' in value_str.lower() or 'n/a' in value_str.lower() or not value_str.strip():
            value = "N/A"

        valueWidget = QLabel(f'<span style="color: grey;">{value if value else "N/A"}</span>')
        valueWidget.setFont(dataFont)
        layout.addRow(labelWidget, valueWidget)

        # Add to ui_fields for future reference
        self.ui_fields.append({
            "label_text": label,
            "db_key": (key1, key2),
            "value_widget": valueWidget,
        })

    def addAddressRow(self, layout, data, titleFont, dataFont):
        """ Adds the address row to the form layout """
        addressLabel = QLabel("Address:")
        addressLabel.setFont(titleFont)
        address = data.get("address", "")
        city = data.get("city", "")
        state = data.get("state", "")
        zipcode = data.get("zipcode", "")
        fullAddress = f"{address}, {city}, {state} {zipcode}".strip(", ")
        addressValue = QLabel(f'<span style="color: grey;">{fullAddress if fullAddress else "N/A"}</span>')
        addressValue.setFont(dataFont)
        layout.addRow(addressLabel, addressValue)

        # Add to ui_fields for future reference
        label = "Address:"
        keys = ("address", "city", "state", "zipcode")
        self.ui_fields.append({
            "label_text": label,
            "db_key": keys,
            "value_widget": addressValue,
        })

    def onAddButtonClicked(self):
        dialog = AddFieldDialog(self.employee_id, "employees", self.added_fields, self)
        dialog.dataUpdated.connect(self.refreshEmployeeData)
        dialog.exec_()

    def refreshEmployeeData(self):
        titleFont = QFont("Arial", 10, QFont.Bold)
        dataFont = QFont("Arial", 10)
        for key, value in self.added_fields.items():
            if key not in self.extra_columns:
                self.addDataRow(self.formLayout, key.replace('_', ' ').title() + ":", key, None,
                                {key: value}, titleFont, dataFont)

        self.added_fields = {}

    @staticmethod
    def get_defined_columns_for_table(table_name):
        # Load the JSON schema for the table
        table_schemas = load_json_file(Path('../resources/tools/table_schemas.json'))
        if table_name in table_schemas:
            # Extract just the column names from the SQL definition
            columns = [line.split()[0] for line in table_schemas[table_name] if line.upper().startswith('    ')]
            return columns
        return []

    @staticmethod
    def get_actual_columns_from_db(table_name):
        query = "SHOW COLUMNS FROM " + table_name
        result = execute_query(query, fetch_mode="all", skip_SELECT=True)
        if result:
            # The column name is the first item in each tuple returned
            return [column[0] for column in result]
        return []

    def add_missing_columns_to_ui(self, formLayout, employee_id, defined_columns, actual_columns, titleFont, dataFont):
        # Find the difference between the actual columns and the defined columns
        self.extra_columns = set(actual_columns) - set(defined_columns)
        for column in self.extra_columns:
            # Fetch the data for the extra column for the given employee
            query = f"SELECT {column} FROM employees WHERE id = %s"
            result = execute_query(query, (employee_id,), fetch_mode="one")
            if result:
                # Display the extra data
                self.addDataRow(formLayout, column.replace('_', ' ').title() + ":", column, None, {column: result[0]},
                                titleFont, dataFont)

    def onEditButtonClicked(self):
        dialog = EditEmployeeDialog(self.employee_id, "employees", self.ui_fields, self)
        dialog.dataUpdated.connect(self.updateEmployeeData)
        dialog.exec_()

    def updateEmployeeData(self):
        pass


class CompanyDataTab(QWidget):
    def __init__(self, employer_id=None, job_id=None):
        super().__init__()
        self.employer_id = employer_id
        self.job_id = job_id
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()

        titleFont = QFont("Arial", 10, QFont.Bold)
        dataFont = QFont("Arial", 10)

        # Check if the employee ID is provided and not None
        if self.employer_id is not None:
            # If a current job ID is found, fetch company data
            if self.job_id:
                company_data = self.get_company_data(self.employer_id)
            else:
                company_data = {}
        else:
            company_data = {}

        # Create the title label
        titleLabel = QLabel("<h2 style='color: #64bfd1;'>Company Information</h2>")
        titleLabel.setAlignment(Qt.AlignLeft)
        layout.addWidget(titleLabel)

        # Display company information
        self.addDataRow(formLayout, "Company:", "employer_company", company_data, titleFont, dataFont)
        self.addDataRow(formLayout, "Contact Person:", "contact_person", company_data, titleFont, dataFont)
        self.addDataRow(formLayout, "Contact Person's Phone Number:", "contact_phone", company_data, titleFont,
                        dataFont)
        self.addDataRow(formLayout, "Contact Person's Email Address:", "contact_email", company_data, titleFont,
                        dataFont)
        self.addDataRow(formLayout, "Company Address:", "address", company_data, titleFont, dataFont)
        self.addDataRow(formLayout, "Current Billing Allowance:", "billing_allowance", company_data, titleFont,
                        dataFont)

        # Button on the left
        buttonLayout = QHBoxLayout()
        actionButton = QPushButton("Open Client Card")
        # Set an icon for the button if desired
        actionButton.setIcon(QIcon("icons/iconmonstr-share-8.svg"))
        actionButton.clicked.connect(self.onActionButtonClicked)
        buttonLayout.addWidget(actionButton)
        buttonLayout.addStretch()

        layout.addLayout(formLayout)
        layout.addLayout(buttonLayout)
        layout.addStretch()
        self.setLayout(layout)

    @staticmethod
    def get_company_data(employer_id: int) -> dict:
        """
        Fetches the data for a specific employer based on the employer_id.

        Args:
            employer_id (int): The ID of the employer to fetch.

        Returns:
            dict: A dictionary containing the employer's data, with column names as keys.
        """
        # SQL query to select the row with the given employer_id
        query = "SELECT * FROM clients WHERE id = %s"

        # Execute the query using the provided execute_query function
        result = execute_query(query, (employer_id,), fetch_mode='one', get_column_names=True)

        # Check if we have both column names and result data
        if 'column_names' in result and 'result' in result:
            # Combine column names and row data into a dictionary
            return dict(zip(result['column_names'], result['result']))
        else:
            # Return an empty dict if there is no data or an error occurred
            return {}

    @staticmethod
    def addDataRow(layout, label, key, data, titleFont, dataFont):
        """Adds a data row to the form layout."""
        labelWidget = QLabel(label)
        labelWidget.setFont(titleFont)
        # Ensure the value is converted to a string and set its color to grey using HTML
        if key == "billing_allowance":
            value = f"${data.get(key, 0):,.2f}"
        else:
            value = str(data.get(key, "N/A"))
        valueWidget = QLabel(f'<span style="color: grey;">{value}</span>')
        valueWidget.setFont(dataFont)
        layout.addRow(labelWidget, valueWidget)

    def onActionButtonClicked(self):
        if self.employer_id is None:
            QMessageBox.warning(self, "No Company Found", "No company was found for the selected employee.")
            return
        allJobIds = self.getAllJobIds(self.employer_id)
        clientCard = ClientCard(self.employer_id, allJobIds)  # Ensure you pass the correct ID here
        clientCard.exec_()

    @staticmethod
    def getAllJobIds(_id):
        company_name_query = f"SELECT employer_company FROM clients WHERE id = %s"
        company_name = execute_query(company_name_query, (_id,))
        query = f"SELECT id FROM job_orders WHERE company = %s"
        result = execute_query(query, company_name, fetch_mode="all")

        if result:
            return result
        else:
            return None


class JobOrderDataTab(QWidget):
    refreshPages = pyqtSignal()

    def __init__(self, employee_id=None, job_id=None):
        super().__init__()
        self.job_id = job_id
        self.employee_id = employee_id
        self.jobData = self.fetch_job_data()
        self.initUI()
        self.setMinimumWidth(1200)

    def initUI(self):
        # Main layout for the widget
        mainLayout = QHBoxLayout(self)

        # Scroll Area setup
        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Scroll Widget setup
        scrollWidget = QWidget()
        scrollArea.setWidget(scrollWidget)
        subLayout = QVBoxLayout(scrollWidget)

        # Create the title label
        titleLabel = QLabel("<h2 style='color: #64bfd1;'>Job Order Information</h2>")
        titleLabel.setAlignment(Qt.AlignLeft)
        subLayout.addWidget(titleLabel)

        # Job Order Information Group
        jobOrderGroup = QGroupBox("Job Order Information")
        jobInfoLayout = QHBoxLayout()
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        # Assuming self.jobData is a dictionary containing all the job data
        job_title = self.jobData.get('job_title', 'N/A')
        po_order_number = self.jobData.get('po_order_number', 'N/A')
        company = self.jobData.get('company', 'N/A')
        location = self.jobData.get('location', 'N/A')
        position_type = self.jobData.get('position_type', 'N/A')
        start_date = self.jobData.get('start_date', 'N/A')
        end_date = self.jobData.get('end_date', 'N/A')

        self.addDataLabel(leftLayout, "Job Title:", job_title)
        self.addDataLabel(leftLayout, "PO Order Number:", po_order_number)
        self.addDataLabel(leftLayout, "Company:", company)
        self.addDataLabel(leftLayout, "Location:", location, wrapText=True)

        self.addDataLabel(rightLayout, "Position Type:", position_type)
        self.addDataLabel(rightLayout, "Start Date:", start_date)
        self.addDataLabel(rightLayout, "End Date:", end_date)

        jobInfoLayout.addLayout(leftLayout)
        jobInfoLayout.addLayout(rightLayout)
        jobOrderGroup.setLayout(jobInfoLayout)

        # Job Financials & Specifications Group
        jobFinancialsSpecsGroup = QGroupBox("Job Financials & Specifications")
        jobSpecLayout = QHBoxLayout()
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        bill_rate_min = self.jobData.get('bill_rate_min', 'N/A')
        bill_rate_max = self.jobData.get('bill_rate_max', 'N/A')
        bill_rate_conversion = self.jobData.get('bill_rate_conversion', 'N/A')
        requirements = self.jobData.get('requirements', 'N/A')
        remote = self.jobData.get('remote', 'N/A')
        pay_rate = self.jobData.get('pay_rate', 'N/A')
        pay_rate_conversion = self.jobData.get('pay_rate_conversion', 'N/A')

        self.addDataLabel(leftLayout, "Bill Rate:", f"{bill_rate_min} - {bill_rate_max} {bill_rate_conversion}")
        self.addDataLabel(leftLayout, "Requirements:", requirements, wrapText=True)

        self.addDataLabel(rightLayout, "Pay Rate:", f"{pay_rate} {pay_rate_conversion}")
        self.addDataLabel(rightLayout, "Position Requirement:", remote)
        rightLayout.addStretch()

        jobSpecLayout.addLayout(leftLayout)
        jobSpecLayout.addLayout(rightLayout)
        jobFinancialsSpecsGroup.setLayout(jobSpecLayout)

        # Job Description and Notes Group
        jobNotesGroup = QGroupBox("Job Description and Notes")
        jobNotesLayout = QVBoxLayout()

        # Read job_description and notes from text files
        if self.jobData.get('job_description_path', '') in [None, 'N/A', 'NULL', 'None', '']:
            job_description = "No Job Description Found."
        else:
            job_description = read_text_file(self.jobData.get('job_description_path', ''))
        if self.jobData.get('notes_path', '') in [None, 'N/A', 'NULL', 'None', '']:
            notes = "No Notes Found."
        else:
            notes = read_text_file(self.jobData.get('notes_path', ''))

        self.addDataLabel(jobNotesLayout, "Job Description:", job_description, wrapText=True, HBox=False)
        self.addDataLabel(jobNotesLayout, "Notes:", notes, wrapText=True, HBox=False)

        jobNotesGroup.setLayout(jobNotesLayout)

        # Add groups to the sub-layout
        subLayout.addWidget(jobOrderGroup)
        subLayout.addWidget(jobFinancialsSpecsGroup)
        subLayout.addWidget(jobNotesGroup)

        # Buttons
        buttonLayout = QVBoxLayout()
        plus_icon = QIcon("icons/iconmonstr-plus-6.svg")
        addToJobOrderButton = QPushButton("Add to")
        addToJobOrderButton.setIcon(plus_icon)

        x_icon = QIcon("icons/iconmonstr-x-mark-circle-lined.svg")
        removeFromJobOrderButton = QPushButton("Remove from")
        removeFromJobOrderButton.setIcon(x_icon)

        change_icon = QIcon("icons/iconmonstr-redo-6.svg")
        changeJobOrderButton = QPushButton("Change")
        changeJobOrderButton.setIcon(change_icon)

        open_icon = QIcon("icons/iconmonstr-share-8.svg")
        openButton = QPushButton("Open Job Order Card")
        openButton.setIcon(open_icon)

        # Set button enabled state based on self.job_id
        if self.job_id is not None:
            removeFromJobOrderButton.setEnabled(True)
            changeJobOrderButton.setEnabled(True)
            addToJobOrderButton.setEnabled(False)
        else:
            removeFromJobOrderButton.setEnabled(False)
            changeJobOrderButton.setEnabled(False)
            addToJobOrderButton.setEnabled(True)

        # Connect buttons to the dialog opening function
        addToJobOrderButton.clicked.connect(lambda: self.openJobOrderDialog("Add", self.jobData, self.employee_id))
        removeFromJobOrderButton.clicked.connect(self.performRemoveAction)
        changeJobOrderButton.clicked.connect(lambda: self.openJobOrderDialog("Change", self.jobData, self.employee_id))
        openButton.clicked.connect(lambda: self.openJobOrderCard(self.job_id))

        buttonLayout.addWidget(addToJobOrderButton)
        buttonLayout.addWidget(removeFromJobOrderButton)
        buttonLayout.addWidget(changeJobOrderButton)
        buttonLayout.addWidget(openButton)

        buttonLayout.addStretch()

        # Add button layout to main layout
        mainLayout.addWidget(scrollArea)
        mainLayout.addLayout(buttonLayout)

        # Set the main layout
        self.setLayout(mainLayout)

    def fetch_job_data(self):
        # Fetch job order data from the database
        query = "SELECT * FROM job_orders WHERE id = %s"
        result = execute_query(query, (self.job_id,), fetch_mode="one", get_column_names=True)
        if result and 'column_names' in result and result['result']:
            return dict(zip(result['column_names'], result['result']))
        return {}

    def openJobOrderDialog(self, action, job_data=None, employee_id=None):
        # Check if job orders are available before opening the dialog
        if not self.check_job_orders_available():
            QMessageBox.warning(self, "No Jobs Available", "There are no job orders currently available.")
            return  # Exit the function if no jobs are available, preventing the dialog from opening

        dialog = ManageJobOrderDialog(action, job_data=job_data, employee_id=employee_id, parent=self)
        dialog.employeeAdded.connect(self.refreshData)
        dialog.exec_()

    def performRemoveAction(self):
        if not self.check_employee_id(self.employee_id):
            return

        job_order_id, client_id = retrieve_current_job_order(self.employee_id)
        if job_order_id is None:
            return

        archive_and_delete_employee_job_order(self.employee_id, job_order_id)
        self.update_employee_status_to_not_working(self.employee_id)
        change_active_needed_employees(client_id, job_order_id, subtract_needed_employees=False)
        self.refreshData()
        QMessageBox.information(self, "Action Completed", "Employee has been removed from the job"
                                                          "successfully.")

    @staticmethod
    def check_employee_id(employee_id):
        if employee_id is None:
            print("Employee ID is missing.")
            return False
        return True

    @staticmethod
    def update_employee_status_to_not_working(employee_id):
        update_employee_query = """
            UPDATE employees SET availability = 'NW', pay = NULL, pay_conversion = NULL, 
                                hired_date = NULL, job_id = NULL WHERE id = %s
        """
        execute_query(update_employee_query, (employee_id,))

    @staticmethod
    def check_job_orders_available():
        # This function checks if there are any job orders available
        # It returns True if job orders are available, False otherwise
        query = "SELECT COUNT(*) FROM job_orders"
        result = execute_query(query, fetch_mode="one")
        return result and result[0] > 0

    def refreshData(self):
        # Emit the signal to indicate data has been updated
        self.refreshPages.emit()

    @staticmethod
    def addDataLabel(layout, labelText, valueText, wrapText=False, HBox=True):
        """
        Mimics adding a data row to a form layout using QVBoxLayout or QHBoxLayout.

        Args:
            layout (QLayout): The main layout to which the label and value will be added.
            labelText (str): The text for the label part.
            valueText (str): The text for the value part.
            wrapText (bool): Whether to enable word wrapping for the value.
        """
        # Create a horizontal layout for the label-value pair
        if HBox:
            rowLayout = QHBoxLayout()
        else:
            rowLayout = QVBoxLayout()

        # Label widget
        labelWidget = QLabel(f"{labelText}")
        labelWidget.setFont(QFont("Arial", 10, QFont.Bold))
        rowLayout.addWidget(labelWidget)

        # Value widget with HTML styling for gray text and optional word wrapping
        formattedValue = f'<span style="color: gray;">{valueText}</span>'
        valueWidget = QLabel(formattedValue)
        valueWidget.setFont(QFont("Arial", 10))
        valueWidget.setTextFormat(Qt.RichText)
        valueWidget.setWordWrap(wrapText)
        rowLayout.addWidget(valueWidget)

        # Add the horizontal layout to the main layout
        layout.addLayout(rowLayout)

    def openJobOrderCard(self, dbId):
        if dbId is None:
            QMessageBox.warning(self, "No Job Order Found", "No job order was found for the selected employee.")
            return
        jobOrderCard = JobOrderCard(dbId)
        jobOrderCard.clientCardRequested.connect(self.openClientCard)
        jobOrderCard.exec_()

    @staticmethod
    def openClientCard(job_id):
        client_id_query = "SELECT client_id from job2employer_ids WHERE job_order_id = %s"
        client_id = execute_query(client_id_query, (job_id,), fetch_mode="one")
        clientCard = ClientCard(client_id[0], job_id)
        clientCard.exec_()


class OldJobOrdersTab(QWidget):
    def __init__(self, employee_id, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Fetch employee name using employee_id
        self.employee_first_name, self.employee_last_name = self.fetch_employee_name()

        # Fetch old job order details for this employee
        job_orders = self.fetch_old_job_orders()

        # Create Scroll Area
        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)

        # Scroll Area Widget Contents
        scrollWidget = QWidget()
        scrollLayout = QVBoxLayout(scrollWidget)

        # Export button
        buttonLayout = QHBoxLayout()
        self.exportButton = QPushButton("Export Table")
        self.exportButton.setObjectName("exportButton")
        self.exportButton.clicked.connect(self.exportToExcel)
        buttonLayout.addWidget(self.exportButton)
        buttonLayout.addStretch()
        scrollLayout.addLayout(buttonLayout)

        self.exportButton.setStyleSheet("""
            QPushButton#exportButton {
                font-size: 12pt; /* Larger font size */
                padding: 10px 25px; /* Larger padding for bigger button */
                background-color: #64bfd1; /* Background color */
                color: white; /* Text color */
                border-radius: 5px; /* Optional: rounded corners */
            }
            QPushButton#exportButton:hover {
                background-color: #59a9c4; /* Slightly different color on hover */
            }
        """)

        # Set up the table
        self.table = CardTableWidget(job_orders)
        scrollLayout.addWidget(self.table)
        scrollArea.setWidget(scrollWidget)

        # Filter and Sorting Section
        self.filterSectionHeader = QLabel("Filter Old Job Orders")
        self.filterSectionHeader.setStyleSheet("font-size: 14pt; font-weight: bold; color: #64bfd1; margin-top: 10px;")
        self.filterRowLayout = QHBoxLayout()
        self.filterRowLayout.setSpacing(10)
        self.filterRowLayout.addWidget(self.filterSectionHeader)

        # Filter Text Editor
        self.filterTextEditor = QLineEdit()
        self.filterTextEditor.setPlaceholderText("Filter...")
        self.filterTextEditor.textChanged.connect(self.filterTable)
        self.filterRowLayout.addWidget(self.filterTextEditor)

        self.swButton = QPushButton("Sw")
        self.swButton.setCheckable(True)
        self.swButton.clicked.connect(self.updateButtonStyle)
        self.swButton.setToolTip("Starts With: Filter words starting with the entered criteria.")
        self.filterRowLayout.addWidget(self.swButton)

        self.ccButton = QPushButton("Cc")
        self.ccButton.setCheckable(True)
        self.ccButton.clicked.connect(self.updateButtonStyle)
        self.ccButton.setToolTip("Match Case: Filter with case sensitivity.")
        self.filterRowLayout.addWidget(self.ccButton)

        # Add the table to the layout
        layout.addWidget(scrollArea)
        layout.addLayout(self.filterRowLayout)

    def fetch_employee_name(self):
        # Fetch the first and last name of the employee from the employees table
        query = "SELECT first_name, last_name FROM employees WHERE id = %s"
        result = execute_query(query, (self.employee_id,), fetch_mode="one")
        if result:
            # Directly return the tuple assuming the first element is first_name and the second is last_name
            return result
        return "Unknown", "Unknown"

    def fetch_old_job_orders(self):
        # Assuming execute_query returns a list of tuples, convert them to dictionaries
        query = """
        SELECT hired_date, pay, pay_conversion, po_order_number, location, company, job_title, position_type, remote
        FROM old_employee_job_orders
        WHERE first_name = %s AND last_name = %s
        """
        results = execute_query(query, (self.employee_first_name, self.employee_last_name), fetch_mode="all")
        columns = ["Hired Date", "Pay", "Pay Rate", "PO Order Number", "Location", "Company", "Job Title",
                   "Position Type", "Remote (%)"]
        job_orders = [dict(zip(columns, result)) for result in results]
        return job_orders

    def updateButtonStyle(self, sender):
        """
        Updates the style of the Sw and Cc buttons based on their checked state.
        """
        sender = self.sender()
        if sender.isChecked():
            sender.setStyleSheet("background-color: #4d8d9c;")  # Darker color when checked
        else:
            sender.setStyleSheet("")  # Revert to default stylesheet

    def filterTable(self):
        """
        Filters the table rows based on the text entered in the filterTextEditor and the selected column.

        The method performs a case-insensitive comparison of the filter text with the data in the selected column.
        It hides rows that do not contain the filter text in the selected column. The comparison takes into
        account the data type of the column (numeric, date, or string) for appropriate formatting and comparison.
        """
        filter_text = self.filterTextEditor.text()
        column_index = self.table.currentColumn()

        if column_index == -1:
            return  # Exit if no column is selected

        for row in range(self.table.rowCount()):
            item = self.table.item(row, column_index)
            if item is None:
                self.table.setRowHidden(row, True)
                continue

            cell_value = item.text()

            # Adjust for case sensitivity based on Cc button
            if not self.ccButton.isChecked():
                filter_text = filter_text.lower()
                cell_value = cell_value.lower()

            # Adjust for "Starts With" functionality based on Sw button
            if self.swButton.isChecked():
                self.table.setRowHidden(row, not cell_value.startswith(filter_text))
            else:
                self.table.setRowHidden(row, filter_text not in cell_value)

    def exportToExcel(self):
        try:
            # Directory where the Excel files will be saved
            export_dir = "exported_tables"
            os.makedirs(export_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Prepare data for export
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for column in range(self.table.columnCount()):
                    item = self.table.item(row, column)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(data, columns=[self.table.horizontalHeaderItem(i).text() for i in
                                             range(self.table.columnCount())])

            # Naming strategy: "employees_" + current date
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            employee_name = f"{self.employee_first_name} {self.employee_last_name}".replace(" ", "_")
            file_name = f"old_job_orders_under_{employee_name}_{current_date}.xlsx"
            file_path = os.path.join(export_dir, file_name)

            # Export to Excel
            df.to_excel(file_path, index=False)

            # Open file location in file explorer
            self.openFileLocation(export_dir)

            # Open the exported Excel file
            self.openFile(file_path)

            print(f"Table exported successfully to {file_path}")
        except Exception as e:
            QMessageBox.critical(None, "Export Error", f"An error occurred while exporting the table:\n{e}")

    @staticmethod
    def openFileLocation(path):
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':  # macOS
            os.system(f'open "{path}"')
        else:  # Linux variants
            os.system(f'xdg-open "{path}"')

    @staticmethod
    def openFile(file_path):
        if sys.platform == 'win32':
            os.startfile(file_path)
        elif sys.platform == 'darwin':  # macOS
            os.system(f'open "{file_path}"')
        else:  # Linux variants
            os.system(f'xdg-open "{file_path}"')

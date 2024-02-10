import os
import sys
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QFont
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QMenu, QAction, QApplication

from application.company_card.dialogs import EditCompanyDialog, AddFieldDialog
from application.job_order_card.job_order_card import JobOrderCard
from resources.tools.mydb import *


class CardTableWidget(QTableWidget):
    def __init__(self, job_orders, *args, **kwargs):
        super(CardTableWidget, self).__init__(*args, **kwargs)
        self.job_ids = {}
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setMouseTracking(True)  # Enable mouse tracking to show tooltips on hover
        self.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.setupTable(job_orders)
        self.populateTable(job_orders)
        self.disableTable()
        self.adjustColumnResizing()
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)

    def setupTable(self, job_orders):
        if job_orders:
            self.setColumnCount(len(job_orders[0]))
            self.setHorizontalHeaderLabels(job_orders[0].keys())

    def populateTable(self, job_orders):
        self.setRowCount(len(job_orders))
        # Assuming the job title is unique and you have a method to execute SQL queries
        query = "SELECT id FROM job_orders WHERE job_title = %s AND po_order_number = %s AND company = %s"
        for row_index, job_order in enumerate(job_orders):
            job_title = job_order.get("Job Title", "")
            po_order = job_order.get("PO Order Number", "")
            company = job_order.get("Company", "")

            if result := execute_query(
                query, (job_title, po_order, company), fetch_mode="one"
            ):
                job_id = result[0]
                self.job_ids[row_index] = job_id  # Store the job_id associated with this row
            else:
                self.job_ids[row_index] = None  # No job_id found for this job title

            for col_index, (key, value) in enumerate(job_order.items()):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))  # Set tooltip for each cell
                self.setItem(row_index, col_index, item)

    def onItemDoubleClicked(self, item):
        row = item.row()
        job_id = self.job_ids.get(row)
        if job_id is not None:
            jobOrderCard = JobOrderCard(job_id)
            jobOrderCard.exec_()
        else:
            QMessageBox.warning(self, "Error", "Job ID not found for the selected job order.")

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
                if item := self.item(row, column):
                    itemWidth = fontMetrics.width(item.text()) + 50  # Again, adding some padding
                    maxWidth = max(maxWidth, itemWidth)

            self.setColumnWidth(column, maxWidth)
            totalWidth += maxWidth

        # Set the minimum width of the table to accommodate the widest cell or column name
        self.setMinimumWidth(totalWidth)


class CompanyInformationTab(QWidget):
    def __init__(self, company_id=None):
        super().__init__()
        self.company_id = company_id
        self.added_fields = {}
        self.ui_fields = []
        self.extra_columns = None
        self.initUI()

    def initUI(self):
        # Main layout for the widget
        self.mainLayout = QVBoxLayout(self)

        # Create group boxes
        companyInfoGroupBox = QGroupBox("Company Information")
        contactPersonGroupBox = QGroupBox("Contact Person")
        otherInfoGroupBox = QGroupBox("Other Information")

        # Form layouts for group boxes
        companyInfoLayout = QFormLayout()
        contactPersonLayout = QFormLayout()
        otherInfoLayout = QFormLayout()

        # Styling fonts for labels
        titleFont = QFont("Arial", 10, QFont.Bold)
        dataFont = QFont("Arial", 10)

        # Fetching company data from the database
        query = "SELECT * FROM clients WHERE id = %s"
        data = (self.company_id,)
        result = execute_query(query, data, fetch_mode="one", get_column_names=True)

        # Create the title label
        titleLabel = QLabel("<h2 style='color: #64bfd1;'>Company Information</h2>")
        titleLabel.setAlignment(Qt.AlignLeft)
        self.mainLayout.addWidget(titleLabel)

        # Process and display fetched data
        if result and 'result' in result and 'column_names' in result:
            company_data = dict(zip(result['column_names'], result['result']))

            # Add data rows to Company Information
            self.addDataRow(companyInfoLayout, "Company Name:", "employer_company", None, company_data, titleFont,
                            dataFont)
            self.addDataRow(contactPersonLayout, "Contact Person:", "contact_person", None, company_data, titleFont,
                            dataFont)
            self.addDataRow(contactPersonLayout, "Contact Phone:", "contact_phone", None, company_data, titleFont,
                            dataFont)
            self.addDataRow(contactPersonLayout, "Contact Email:", "contact_email", None, company_data, titleFont,
                            dataFont)
            self.addDataRow(companyInfoLayout, "Address:", "address", None, company_data, titleFont, dataFont)
            self.addDataRow(companyInfoLayout, "Billing Allowance:", "billing_allowance", None, company_data, titleFont,
                            dataFont)
            self.addDataRow(companyInfoLayout, "Active Employees:", "active_employees", None, company_data, titleFont,
                            dataFont)

            # User added data into Other Information
            defined_columns = self.get_defined_columns_for_table("clients")
            actual_columns = self.get_actual_columns_from_db("clients")
            self.add_missing_columns_to_ui(otherInfoLayout, self.company_id, defined_columns, actual_columns,
                                           titleFont, dataFont)

            # Set layout to the group box
            companyInfoGroupBox.setLayout(companyInfoLayout)
            contactPersonGroupBox.setLayout(contactPersonLayout)
            otherInfoGroupBox.setLayout(otherInfoLayout)

            # Add group box to the main layout
            self.mainLayout.addWidget(companyInfoGroupBox)
            self.mainLayout.addWidget(contactPersonGroupBox)
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
        """Adds a data row to the form layout"""
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

    def onAddButtonClicked(self):
        dialog = AddFieldDialog(self.company_id, "clients", self.added_fields, self)
        dialog.dataUpdated.connect(self.refreshCompanyData)
        dialog.exec_()

    def refreshCompanyData(self):
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
        table_schemas = load_json_file(Path('tools/table_schemas.json'))
        if table_name in table_schemas:
            return [
                line.split()[0]
                for line in table_schemas[table_name]
                if line.upper().startswith('    ')
            ]
        return []

    @staticmethod
    def get_actual_columns_from_db(table_name):
        query = "SHOW COLUMNS FROM " + table_name
        if result := execute_query(query, fetch_mode="all", skip_SELECT=True):
            # The column name is the first item in each tuple returned
            return [column[0] for column in result]
        return []

    def add_missing_columns_to_ui(self, formLayout, company_id, defined_columns, actual_columns, titleFont, dataFont):
        # Find the difference between the actual columns and the defined columns
        self.extra_columns = set(actual_columns) - set(defined_columns)
        for column in self.extra_columns:
            # Fetch the data for the extra column for the given employee
            query = f"SELECT {column} FROM clients WHERE id = %s"
            if result := execute_query(query, (company_id,), fetch_mode="one"):
                # Display the extra data
                self.addDataRow(formLayout, column.replace('_', ' ').title() + ":", column, None, {column: result[0]},
                                titleFont, dataFont)

    def onEditButtonClicked(self):
        dialog = EditCompanyDialog(self.company_id, "clients", self.ui_fields, self)
        dialog.dataUpdated.connect(self.updateCompanyData)
        dialog.exec_()

    def updateCompanyData(self):
        pass


class CurrentJobOrdersTab(QWidget):
    def __init__(self, employer_id, parent=None):
        super().__init__(parent)
        self.employer_id = employer_id
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Fetch employee name using company_id
        self.company_name = self.fetch_company_name()

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

    def fetch_company_name(self):
        # Fetch the first and last name of the employee from the employees table
        query = "SELECT employer_company FROM clients WHERE id = %s"
        if result := execute_query(query, (self.employer_id,), fetch_mode="one"):
            # Directly return the tuple assuming the first element is first_name and the second is last_name
            return result[0]
        return "Unknown"

    def fetch_old_job_orders(self):
        # Assuming execute_query returns a list of tuples, convert them to dictionaries
        query = """
        SELECT job_title, po_order_number, company, location, start_date, end_date, active_employees, needed_employees, 
        position_type, bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate, pay_rate_conversion,
        min_experience, requirements, remote, job_description_path, notes_path
        FROM job_orders
        WHERE company = %s
        """
        results = execute_query(query, (self.company_name,), fetch_mode="all")
        columns = ["Job Title", "PO Order Number", "Company", "Location", "Start Date", "End Date", "Active Employees",
                   "Needed Employees", "Position Type", "Bill Rate (Min)", "Bill Rate (Max)", "Bill Rate", "Pay",
                   "Pay Rate", "Min Experience", "Requirements", "Remote (%)", "Job Description Path", "Notes Path"]
        return [dict(zip(columns, result)) for result in results]

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
            company_name = f"{self.company_name}".replace(" ", "_")
            file_name = f"job_orders_under_{company_name}_{current_date}.xlsx"
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


class OldCompanyJobOrdersTab(QWidget):
    def __init__(self, employer_id, parent=None):
        super().__init__(parent)
        self.employer_id = employer_id
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Fetch employee name using company_id
        self.company_name = self.fetch_company_name()

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

    def fetch_company_name(self):
        # Fetch the first and last name of the employee from the employees table
        query = "SELECT employer_company FROM clients WHERE id = %s"
        if result := execute_query(query, (self.employer_id,), fetch_mode="one"):
            # Directly return the tuple assuming the first element is first_name and the second is last_name
            return result[0]
        return "Unknown"

    def fetch_old_job_orders(self):
        # Assuming execute_query returns a list of tuples, convert them to dictionaries
        query = """
        SELECT contact_person, location, po_order_number, start_date, end_date, needed_employees, job_title, 
        position_type, bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate, pay_rate_conversion,
        min_experience, requirements, remote, job_description_path, notes_path
        FROM old_company_job_orders
        WHERE employer_company = %s
        """
        results = execute_query(query, (self.company_name,), fetch_mode="all")
        columns = ["Contact Person", "Location", "PO Order Number", "Start Date", "End Date", "Needed Employees",
                   "Job Title", "Position Type", "Bill Rate (Min)", "Bill Rate (Max)", "Bill Rate", "Pay Rate",
                   "Pay Rate", "Min Experience", "Requirements", "Remote (%)", "Job Description Path", "Notes Path"]
        return [dict(zip(columns, result)) for result in results]

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
            company_name = f"{self.company_name}".replace(" ", "_")
            file_name = f"old_job_orders_under_{company_name}_{current_date}.xlsx"
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

import locale
from datetime import timedelta

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import *

# Import application specific files
from application.external_widgets import *
from application.finder_agent import *

from resources.tools import *

locale.setlocale(locale.LC_ALL, '')  # Set to the user's default locale

###################################
# Column Headers

# Determine if the application is a frozen executable or a script
application_path = str(resource_path(Path.cwd()))

# Example of how to use application_path to build a path to resources
column_data_path = Path(application_path, 'resources', 'tools', 'column_data.json')
HEADERS = load_json_file(column_data_path, "Column Data JSON file")


###################################


class EmployeePage(QWidget):
    """
    Represents the GUI for managing employee information. It includes
    a table displaying employee data, filter functionality, and sorting
    by clicking on column headers.

    Functions:
    - __init__: Initializes the widget with a layout, header, table, and filter tools.
    - populateTable: Fetches and displays employee data from the database.
    - onHeaderClicked: Handles sorting when a table header is clicked.
    - updateButtonStyle: Updates the style of filter buttons based on their state.
    - filterTable: Filters the table based on entered text and selected column.
    - openAddEmployeeDialog: Opens a dialog to add a new employee.
    - addEmployeeToDatabase: Inserts new employee data into the database.
    - addEmployeeToTable: Adds a new employee row to the table.
    """

    def __init__(self, employee_type=None, parent=None):
        super().__init__(parent)

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)

        # Header with title and an optional image
        self.headerLayout = QHBoxLayout()
        self.titleLabel = QLabel("Employee Management")
        self.titleLabel.setStyleSheet("font-size: 18pt; font-weight: bold; color: #64bfd1;")
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch()

        # Optional: Add an image to the header
        self.headerIcon = QLabel()
        self.headerIcon.setPixmap(QIcon(str(Path(application_path, 'resources', 'example.png'))).pixmap(50, 50))
        self.headerLayout.addWidget(self.headerIcon)

        # Refresh Table Button
        self.refreshTableButton = QPushButton()
        buttonHeight = self.refreshTableButton.sizeHint().height()
        self.refreshTableButton.setIcon(QIcon(str(Path(application_path, 'resources', 'icons',
                                                       'iconmonstr-refresh-lined.svg'))))
        self.refreshTableButton.setIconSize(QSize(buttonHeight, buttonHeight))
        self.refreshTableButton.clicked.connect(self.populateTable)
        self.headerLayout.addWidget(self.refreshTableButton)

        self.layout.addLayout(self.headerLayout)

        # Table and button layout
        tableButtonLayout = QHBoxLayout()

        # Create Scroll Area
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)

        # Scroll Area Widget Contents
        self.scrollAreaWidgetContents = QWidget()

        # Scroll Area Layer
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(self.scrollAreaLayout)

        # Table Widget for Employees
        self.tableWidget = TableWidget(HEADERS["EMPLOYEE_HEADERS"], "Employee")
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.scrollAreaLayout.addWidget(self.tableWidget)

        # Set the scroll area widget
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        tableButtonLayout.addWidget(self.scrollArea)

        # Layout for buttons
        buttonsLayout = QVBoxLayout()

        self.addEmployeeButton = QPushButton("Add New Employee")
        self.editButton = QPushButton("Edit Employees")
        self.saveButton = QPushButton("Save Updates")
        self.revertButton = QPushButton("Revert Changes")
        self.deleteButton = QPushButton("Delete Employee(s)")
        self.exportButton = QPushButton("Export Table")

        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

        # Add buttons to the buttons layout
        buttonsLayout.addWidget(self.addEmployeeButton)
        buttonsLayout.addWidget(self.editButton)
        buttonsLayout.addWidget(self.saveButton)
        buttonsLayout.addWidget(self.revertButton)
        buttonsLayout.addWidget(self.deleteButton)
        buttonsLayout.addWidget(self.exportButton)

        # Add some stretch to push everything up
        buttonsLayout.addStretch()

        # Add the Open Job Finder Agent Button
        self.openJobFinderAgentButton = QPushButton("Open Job Finder Agent")
        self.openJobFinderAgentButton.clicked.connect(self.openJobFinderAgent)
        buttonsLayout.addWidget(self.openJobFinderAgentButton, alignment=Qt.AlignBottom)

        tableButtonLayout.addLayout(buttonsLayout)

        self.addEmployeeButton.clicked.connect(self.openAddEmployeeDialog)
        self.editButton.clicked.connect(self.enableEditing)
        self.saveButton.clicked.connect(self.saveUpdates)
        self.revertButton.clicked.connect(self.revertChanges)
        self.deleteButton.clicked.connect(self.deleteEntry)
        self.exportButton.clicked.connect(self.exportToExcel)

        self.originalTableData = None

        self.layout.addLayout(tableButtonLayout)

        # Filter and Sorting Section Header
        self.filterSectionHeader = QLabel("Filter Employees")
        self.filterSectionHeader.setStyleSheet("font-size: 14pt; font-weight: bold; color: #64bfd1; margin-top: 10px;")
        self.layout.addWidget(self.filterSectionHeader)

        # Filter Row
        self.filterRowLayout = QHBoxLayout()
        self.filterRowLayout.setSpacing(10)

        # Filter and Sorting Section Header
        self.filterSectionHeader = QLabel(
            "Filter Employees (Select a column, then type to filter. Double-click a column header to sort.)")
        self.filterSectionHeader.setStyleSheet("font-size: 10pt; margin-top: 10px;")
        self.layout.addWidget(self.filterSectionHeader)

        # Text Editor for Filtering
        self.filterTextEditor = QLineEdit()
        self.filterTextEditor.setPlaceholderText("Filter...")
        self.filterTextEditor.textChanged.connect(self.filterTable)
        self.filterTextEditor.setToolTip("Enter text to filter the employee data in the selected column.")
        self.filterRowLayout.addWidget(self.filterTextEditor)

        # Starts With Button
        self.swButton = QPushButton("Sw")
        self.swButton.setCheckable(True)
        self.swButton.clicked.connect(self.updateButtonStyle)
        self.swButton.setToolTip(
            "Starts With: Select this button if you want to filter only to words that start with the letters/numbers "
            "in your filter criteria.")
        self.filterRowLayout.addWidget(self.swButton)

        # Match Case Button
        self.ccButton = QPushButton("Cc")
        self.ccButton.setCheckable(True)
        self.ccButton.clicked.connect(self.updateButtonStyle)
        self.ccButton.setToolTip(
            "Match Case: Select this button if you want to match the case that you have in the filter criteria.")
        self.filterRowLayout.addWidget(self.ccButton)

        self.layout.addLayout(self.filterRowLayout)

        # Populate the Table
        self.employee_type = employee_type
        self.populateTable(self.employee_type)

    def enableEditing(self):
        self.tableWidget.enableEditing()
        self.editButton.setEnabled(False)
        self.saveButton.setEnabled(True)
        self.revertButton.setEnabled(True)
        self.deleteButton.setEnabled(True)

    def saveUpdates(self):
        # Construct and execute SQL queries based on pendingChanges
        for change in self.tableWidget.pendingChanges:
            sql = f"UPDATE employees SET {change['columnName']} = %s WHERE id = %s"
            data = (change['newValue'], change['rowId'])
            execute_query(sql, data)

        # Clear pending changes after saving
        self.tableWidget.pendingChanges.clear()

        # For now, just show a message box.
        QMessageBox.information(self, "Info", "Changes saved.")
        self.disableEditing()

    def revertChanges(self):
        # Revert changes: Reset the table data to originalTableData
        for row in range(self.tableWidget.rowCount()):
            for col in range(self.tableWidget.columnCount()):
                if self.tableWidget.item(row, col):
                    self.tableWidget.item(row, col).setText(self.tableWidget.originalTableData[row][col])
        # Clear pending changes
        self.tableWidget.pendingChanges.clear()

    def deleteEntry(self):
        # Determine the selected rows in the table widget
        selectedRows = self.tableWidget.selectionModel().selectedRows()
        if not selectedRows:
            QMessageBox.warning(self, "Selection Required", "Please select at least one row to delete.")
            return

        # Confirmation dialog before deletion
        reply = QMessageBox.question(self, "Delete Entries", "Are you sure you want to delete the selected entries?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                connection = create_db_connection()  # Assuming this function returns a valid connection
                if connection:
                    with connection.cursor() as cursor:
                        # Begin a transaction
                        connection.start_transaction()
                        for selectedRow in sorted(selectedRows, reverse=True):
                            idToDelete = selectedRow.row() + 1
                            for i in range(self.tableWidget.columnCount()):
                                if self.tableWidget.isColumnHidden(i):
                                    idToDelete = int(self.tableWidget.item(selectedRow.row(), i).text())

                            job_order_id, client_id = retrieve_current_job_order(idToDelete)
                            if job_order_id is not None:
                                archive_and_delete_employee_job_order(idToDelete, job_order_id)
                                change_active_needed_employees(client_id, job_order_id, subtract_needed_employees=False)

                            # Assuming the table is named 'employees', adjust as necessary
                            deleteQuery = "DELETE FROM employees WHERE id = %s"
                            cursor.execute(deleteQuery, (idToDelete,))
                        # Commit the transaction
                        connection.commit()
                    QMessageBox.information(self, "Success", "The selected entries have been deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")
                # Rollback in case of error
                if connection.in_transaction:
                    connection.rollback()
            finally:
                if connection and connection.is_connected():
                    connection.close()

            # Remove the rows from the table widget. Iterate in reverse order to avoid index shifting issues.
            for selectedRow in sorted(selectedRows, reverse=True):
                self.tableWidget.removeRow(selectedRow.row())

    def disableEditing(self):
        self.tableWidget.disableEditing()
        self.editButton.setEnabled(True)
        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

    def onHeaderClicked(self, logicalIndex):
        """
        Sorts the table based on the clicked column header and updates the header to display a sorting arrow.

        Args:
            logicalIndex (int): Index of the clicked column header.

        The method toggles sorting order and updates the table based on the selected column.
        """
        self.currentSortOrder = not getattr(self, 'currentSortOrder', False)
        sorting_order = Qt.AscendingOrder if self.currentSortOrder else Qt.DescendingOrder
        self.tableWidget.sortItems(logicalIndex, sorting_order)

        # Update header icons for sorting indication
        for i in range(self.tableWidget.columnCount()):
            header = self.tableWidget.horizontalHeaderItem(i)
            header.setIcon(QIcon())  # Clear previous icons

        # Set the sort indicator icon
        sort_icon = QIcon("^") if self.currentSortOrder else QIcon("↓")
        self.tableWidget.horizontalHeaderItem(logicalIndex).setIcon(sort_icon)

    def updateButtonStyle(self):
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
        column_index = self.tableWidget.currentColumn()

        if column_index == -1:
            return  # Exit if no column is selected

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, column_index)
            if item is None:
                self.tableWidget.setRowHidden(row, True)
                continue

            cell_value = item.text()

            # Adjust for case sensitivity based on Cc button
            if not self.ccButton.isChecked():
                filter_text = filter_text.lower()
                cell_value = cell_value.lower()

            # Adjust for "Starts With" functionality based on Sw button
            if self.swButton.isChecked():
                self.tableWidget.setRowHidden(row, not cell_value.startswith(filter_text))
            else:
                self.tableWidget.setRowHidden(row, filter_text not in cell_value)

    def populateTable(self, employee_type=None):
        """
        Populate the table with data from the employees database.
        Optionally filters the employees based on their type.
        """
        if employee_type is None:
            employee_type = self.employee_type
        self.tableWidget.setRowCount(0)  # Clear the table

        # Adjust SQL query based on employee type
        query = "SELECT * FROM employees"
        if employee_type:
            if employee_type == "1099":
                # Select employees where employee_type is '1099' and availability is not 'NA'
                query += " WHERE employee_type = '1099' AND availability <> 'NA'"
            elif employee_type == "Not Active":
                # Select employees where availability is 'NA'
                query += " WHERE availability = 'NA'"
            elif employee_type == "W2":
                # Select employees where employee_type is not '1099' (including NULL) and availability is not 'NA'
                query += " WHERE (employee_type <> '1099' OR employee_type IS NULL) AND availability <> 'NA'"

        # Fetch data from the database
        results = execute_query(query, fetch_mode="all", return_cursor=True)
        employees = results["result"]
        cursor = results["cursor"]
        for row, emp_data in enumerate(employees):
            self.tableWidget.insertRow(row)
            column_names = list(HEADERS["EMPLOYEE_HEADERS"].keys())
            for column, column_name in enumerate(column_names):
                # Get the value corresponding to the column name
                value = emp_data[cursor.column_names.index(column_name)]
                if column_name == "phone" and len(value) == 10:
                    value = f"+1 ({value[:3]}) {value[3:6]}-{value[6:]}"
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.tableWidget.setItem(row, column, item)
                if column_name == "id":
                    self.tableWidget.hideColumn(column)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def openAddEmployeeDialog(self) -> None:
        """
        Opens the dialog to add a new employee. If the dialog is accepted, it retrieves the entered
        employee data, adds it to the database, and updates the GUI table to reflect the new entry.

        The dialog data is collected from the AddEmployeeDialog instance. This data is then passed to
        methods for adding the data to the database and updating the GUI table.
        """
        dialog = AddEmployeeDialog()
        if dialog.exec_() == QDialog.Accepted:
            employee_data = dialog.getEmployeeData()
            sql_headers = list(employee_data.keys())

            # Check if an employee with the same name already exists
            query = "SELECT id FROM employees WHERE first_name = %s AND last_name = %s"
            result = execute_query(query, (employee_data["first_name"], employee_data["last_name"]))
            existing_employee_id = False
            if result:
                existing_employee_id = result[0]
            if existing_employee_id:
                reply = QMessageBox.question(
                    self, 'Update Existing Employee',
                    "An employee with the same name already exists. Would you like to update their information?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    addToDatabase(employee_data, sql_headers,
                                  "employees", "update", existing_employee_id)
                    QMessageBox.information(self, "Updated", "The employee's information has been updated.")
                else:
                    return  # Do not proceed with adding a new employee
            else:
                addToDatabase(employee_data, sql_headers, "employees")
            self.populateTable(self.employee_type)
        else:
            return

        # Determine the id for the new employee based on the database
        query = "SELECT id FROM employees WHERE first_name = %s AND last_name = %s"
        result = execute_query(query, (employee_data["first_name"], employee_data["last_name"]))
        dialog = EmployeeCard(database_id=result[0])
        if dialog.exec_() == QDialog.Accepted:
            pass

    @staticmethod
    def openJobFinderAgent():
        dialog = RankingJobOrderResultsDialog()
        dialog.exec_()

    def exportToExcel(self):
        try:
            # Directory where the Excel files will be saved
            out_dir = find_output_directory()
            export_dir = Path(out_dir, "exported_tables")
            os.makedirs(export_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Prepare data for export
            data = []
            for row in range(self.tableWidget.rowCount()):
                row_data = []
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(data, columns=[self.tableWidget.horizontalHeaderItem(i).text() for i in
                                             range(self.tableWidget.columnCount())])

            # Naming strategy: "employees_" + current date
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"employees_{current_date}.xlsx"
            file_path = os.path.join(resource_path(export_dir), file_name)

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


class ClientPage(QWidget):
    """
    Represents the GUI for managing client (employer) information. It includes
    a table for displaying client data and functionality to create job orders.

    Functions:
    - __init__: Initializes the widget with layout, header, table, and filter tools.
    - populateTable: Fetches and displays client data from the database.
    - onHeaderClicked: Handles sorting when a table header is clicked.
    - updateButtonStyle: Updates the style of filter buttons based on their state.
    - filterTable: Filters the table based on entered text and selected column.
    - createJobOrder: Initiates job order creation for a selected employer.
    - getEmployerId: Retrieves the employer ID for a given row in the table.
    - openAddClientDialog: Opens a dialog to add a new client.
    - addClientToDatabase: Inserts new client data into the database.
    - addClientToTable: Adds a new client row to the table.

    Note: The "Filter method" mentioned in comments is not implemented in the provided code.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Header with title and an optional image
        self.headerLayout = QHBoxLayout()
        self.titleLabel = QLabel("Client Management")
        self.titleLabel.setStyleSheet("font-size: 18pt; font-weight: bold; color: #64bfd1;")
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch()

        # Optional: Add an image to the header
        self.headerIcon = QLabel()
        self.headerIcon.setPixmap(QIcon(str(Path(application_path, 'resources', 'example.png'))).pixmap(50, 50))
        self.headerLayout.addWidget(self.headerIcon)

        # Refresh Table Button
        self.refreshTableButton = QPushButton()
        buttonHeight = self.refreshTableButton.sizeHint().height()
        self.refreshTableButton.setIcon(QIcon(str(Path(application_path, 'resources', 'icons',
                                                       'iconmonstr-refresh-lined.svg'))))
        self.refreshTableButton.setIconSize(QSize(buttonHeight, buttonHeight))
        self.refreshTableButton.clicked.connect(self.populateTable)
        self.headerLayout.addWidget(self.refreshTableButton)

        self.layout.addLayout(self.headerLayout)

        # Table and button layout
        tableButtonLayout = QHBoxLayout()

        # Create Scroll Area
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)

        # Scroll Area Widget Contents
        self.scrollAreaWidgetContents = QWidget()

        # Scroll Area Layer
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(self.scrollAreaLayout)

        # Table Widget for Clients
        self.tableWidget = TableWidget(HEADERS["CLIENT_HEADERS"], "Client")
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.scrollAreaLayout.addWidget(self.tableWidget)

        # Set the scroll area widget
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        tableButtonLayout.addWidget(self.scrollArea)

        # Layout for buttons
        buttonsLayout = QVBoxLayout()

        self.addClientButton = QPushButton("Add New Client")
        self.editButton = QPushButton("Edit Clients")
        self.saveButton = QPushButton("Save Updates")
        self.revertButton = QPushButton("Revert Changes")
        self.deleteButton = QPushButton("Delete Client(s)")
        self.exportButton = QPushButton("Export Table")

        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

        # Add buttons to the buttons layout
        buttonsLayout.addWidget(self.addClientButton)
        buttonsLayout.addWidget(self.editButton)
        buttonsLayout.addWidget(self.saveButton)
        buttonsLayout.addWidget(self.revertButton)
        buttonsLayout.addWidget(self.deleteButton)
        buttonsLayout.addWidget(self.exportButton)

        # Add some stretch to push everything up
        buttonsLayout.addStretch()
        tableButtonLayout.addLayout(buttonsLayout)

        self.addClientButton.clicked.connect(self.openAddClientDialog)
        self.editButton.clicked.connect(self.enableEditing)
        self.saveButton.clicked.connect(self.saveUpdates)
        self.revertButton.clicked.connect(self.revertChanges)
        self.deleteButton.clicked.connect(self.deleteEntry)
        self.exportButton.clicked.connect(self.exportToExcel)

        self.originalTableData = None

        self.layout.addLayout(tableButtonLayout)

        # Filter and Sorting Section Header
        self.filterSectionHeader = QLabel("Filter Clients")
        self.filterSectionHeader.setStyleSheet("font-size: 14pt; font-weight: bold; color: #64bfd1; margin-top: 10px;")
        self.layout.addWidget(self.filterSectionHeader)

        # Filter Section Header
        self.filterSectionHeader = QLabel(
            "Filter Clients (Select a column, then type to filter. Double-click a column header to sort.)")
        self.filterSectionHeader.setStyleSheet("font-size: 10pt; margin-top: 10px;")
        self.layout.addWidget(self.filterSectionHeader)

        # Filter Row
        self.filterRowLayout = QHBoxLayout()
        self.filterRowLayout.setSpacing(10)

        # Text Editor for Filtering
        self.filterTextEditor = QLineEdit()
        self.filterTextEditor.setPlaceholderText("Filter...")
        self.filterTextEditor.textChanged.connect(self.filterTable)
        self.filterTextEditor.setToolTip("Enter text to filter the client data in the selected column.")
        self.filterRowLayout.addWidget(self.filterTextEditor)

        # Starts With Button
        self.swButton = QPushButton("Sw")
        self.swButton.setCheckable(True)
        self.swButton.clicked.connect(self.updateButtonStyle)
        self.swButton.setToolTip(
            "Starts With: Select this button if you want to filter only to words that start with the letters/numbers "
            "in your filter criteria.")
        self.filterRowLayout.addWidget(self.swButton)

        # Match Case Button
        self.ccButton = QPushButton("Cc")
        self.ccButton.setCheckable(True)
        self.ccButton.clicked.connect(self.updateButtonStyle)
        self.ccButton.setToolTip(
            "Match Case: Select this button if you want to match the case that you have in the filter criteria.")
        self.filterRowLayout.addWidget(self.ccButton)

        self.layout.addLayout(self.filterRowLayout)

        # Button for creating job orders
        self.createJobOrderButton = QPushButton("Create Job Order")
        self.createJobOrderButton.clicked.connect(self.createJobOrder)
        self.layout.addWidget(self.createJobOrderButton)

        self.populateTable()

    def enableEditing(self):
        self.tableWidget.enableEditing()
        self.editButton.setEnabled(False)
        self.saveButton.setEnabled(True)
        self.revertButton.setEnabled(True)
        self.deleteButton.setEnabled(True)

    def saveUpdates(self):
        # Construct and execute SQL queries based on pendingChanges
        for change in self.tableWidget.pendingChanges:
            sql = f"UPDATE clients SET {change['columnName']} = %s WHERE id = %s"
            data = (change['newValue'], change['rowId'])
            execute_query(sql, data)

        # Clear pending changes after saving
        self.tableWidget.pendingChanges.clear()

        # For now, just show a message box.
        QMessageBox.information(self, "Info", "Changes saved.")
        self.disableEditing()

    def revertChanges(self):
        # Revert changes: Reset the table data to originalTableData
        for row in range(self.tableWidget.rowCount()):
            for col in range(self.tableWidget.columnCount()):
                if self.tableWidget.item(row, col):
                    self.tableWidget.item(row, col).setText(self.tableWidget.originalTableData[row][col])
        # Clear pending changes
        self.tableWidget.pendingChanges.clear()

    def deleteEntry(self):
        # Determine the selected rows in the table widget
        selectedRows = self.tableWidget.selectionModel().selectedRows()
        if not selectedRows:
            QMessageBox.warning(self, "Selection Required", "Please select at least one row to delete.")
            return

        # Confirmation dialog before deletion
        reply = QMessageBox.question(self, "Delete Entries", "Are you sure you want to delete the selected entries?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                connection = create_db_connection()  # Assuming this function returns a valid connection
                if connection:
                    with connection.cursor() as cursor:
                        # Begin a transaction
                        connection.start_transaction()
                        for selectedRow in sorted(selectedRows, reverse=True):
                            idToDelete = selectedRow.row() + 1
                            for i in range(self.tableWidget.columnCount()):
                                if self.tableWidget.isColumnHidden(i):
                                    idToDelete = int(self.tableWidget.item(selectedRow.row(), i).text())

                            # Fetch employer_company for the selected row
                            employer_company_query = "SELECT employer_company FROM clients WHERE id = %s"
                            cursor.execute(employer_company_query, (idToDelete,))
                            employer_company = cursor.fetchone()

                            # Fetch all job order ids for this company
                            job_order_ids_query = "SELECT id FROM job_orders WHERE company = %s"
                            cursor.execute(job_order_ids_query, employer_company)
                            job_order_ids = cursor.fetchall()

                            for job_order_id in job_order_ids:
                                # Archive and delete each job order
                                archive_and_delete_company_job_order(idToDelete, job_order_id[0])

                            # Assuming the table is named 'employees', adjust as necessary
                            deleteQuery = "DELETE FROM clients WHERE id = %s"
                            cursor.execute(deleteQuery, (idToDelete,))
                        # Commit the transaction
                        connection.commit()
                    QMessageBox.information(self, "Success", "The selected entries have been deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")
                # Rollback in case of error
                if connection.in_transaction:
                    connection.rollback()
            finally:
                if connection and connection.is_connected():
                    connection.close()

            # Remove the rows from the table widget. Iterate in reverse order to avoid index shifting issues.
            for selectedRow in sorted(selectedRows, reverse=True):
                self.tableWidget.removeRow(selectedRow.row())

    def disableEditing(self):
        self.tableWidget.disableEditing()
        self.editButton.setEnabled(True)
        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

    def onHeaderClicked(self, logicalIndex):
        """
        Sorts the table based on the clicked column header and updates the header to display a sorting arrow.

        Args:
            logicalIndex (int): Index of the clicked column header.

        The method toggles sorting order and updates the table based on the selected column.
        """
        self.currentSortOrder = not getattr(self, 'currentSortOrder', False)
        sorting_order = Qt.AscendingOrder if self.currentSortOrder else Qt.DescendingOrder
        self.tableWidget.sortItems(logicalIndex, sorting_order)

        # Update header icons for sorting indication
        for i in range(self.tableWidget.columnCount()):
            header = self.tableWidget.horizontalHeaderItem(i)
            header.setIcon(QIcon())  # Clear previous icons

        # Set the sort indicator icon
        sort_icon = QIcon("^") if self.currentSortOrder else QIcon("↓")
        self.tableWidget.horizontalHeaderItem(logicalIndex).setIcon(sort_icon)

    def updateButtonStyle(self):
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
        column_index = self.tableWidget.currentColumn()

        if column_index == -1:
            return  # Exit if no column is selected

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, column_index)
            if item is None:
                self.tableWidget.setRowHidden(row, True)
                continue

            cell_value = item.text()

            # Adjust for case sensitivity based on Cc button
            if not self.ccButton.isChecked():
                filter_text = filter_text.lower()
                cell_value = cell_value.lower()

            # Adjust for "Starts With" functionality based on Sw button
            if self.swButton.isChecked():
                self.tableWidget.setRowHidden(row, not cell_value.startswith(filter_text))
            else:
                self.tableWidget.setRowHidden(row, filter_text not in cell_value)

    def populateTable(self):
        """
        Populate the table with data from the clients database.
        Optionally filters the employees based on their type.
        """
        self.tableWidget.setRowCount(0)  # Clear the table

        # Adjust SQL query based on employee type
        query = "SELECT * FROM clients"

        # Fetch data from the database
        results = execute_query(query, fetch_mode="all", return_cursor=True)
        clients = results["result"]
        cursor = results["cursor"]
        for row, client_data in enumerate(clients):
            self.tableWidget.insertRow(row)
            column_names = list(HEADERS["CLIENT_HEADERS"].keys())
            for column, column_name in enumerate(column_names):
                # Get the value corresponding to the column name
                value = client_data[cursor.column_names.index(column_name)]
                if column_name == "contact_phone":
                    if len(value) == 10:
                        value = f"+1 ({value[:3]}) {value[3:6]}-{value[6:]}"
                elif column_name == "billing_allowance":
                    value = locale.currency(value, grouping=True)
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.tableWidget.setItem(row, column, item)
                if column_name == "id":
                    self.tableWidget.hideColumn(column)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def createJobOrder(self):
        """
        Logic to handle job order creation based on the selected employer.
        This sets the employer_id and employer_data for JobOrderPage.
        """
        # Make sure the user only selects a single company
        selectedCells = self.tableWidget.selectionModel().selectedIndexes()
        uniqueRows = set(cell.row() for cell in selectedCells)
        employerData = {}
        employer_id = None
        if len(uniqueRows) == 1:
            selectedRow = self.tableWidget.currentRow()
            for i in range(self.tableWidget.columnCount()):
                column_name = self.tableWidget.horizontalHeaderItem(i).text()
                item = self.tableWidget.item(selectedRow, i)
                employerData[column_name] = item.text() if item is not None else ""
                # Fetch the employer's ID
                if self.tableWidget.isColumnHidden(i):
                    employer_id = int(self.tableWidget.item(selectedRow, i).text())
        elif len(uniqueRows) > 1:
            show_error_message("You may only select a single company to create a job order. Please try again.")
            return

        self.parent().showJobOrderPage(employerData, employer_id)
        self.populateTable()

    def getEmployerId(self, row: int) -> Optional[Any]:
        """
        Retrieve the employer ID for the given row in the table.
        This method needs to be adapted to retrieve the actual employer ID from your data source.
        """
        # Example: Assuming you have employer's company name as the first column in the table
        employer_company = self.tableWidget.item(row, 0).text()

        # Now, use this information to query your database and fetch the corresponding employer_id
        query = "SELECT id FROM clients WHERE employer_company = %s"
        result = execute_query(query, (employer_company,))
        if result:
            return result[0]  # Return the first element of the tuple
        else:
            return None

    def openAddClientDialog(self) -> None:
        """
        Opens the dialog to add a new client. Retrieves the entered client data,
        adds it to the database, and updates the GUI table to reflect the new entry.
        """
        dialog = AddClientDialog()
        if dialog.exec_() == QDialog.Accepted:
            client_data = dialog.getClientData()
            sql_headers = list(client_data.keys())

            # Check if an employer with the same name already exists
            query = "SELECT id FROM clients WHERE employer_company = %s"
            result = execute_query(query, (client_data["employer_company"],))
            existing_employer_id = False
            if result:
                existing_employer_id = result[0]
            if existing_employer_id:
                reply = QMessageBox.question(
                    self, 'Update Existing Client',
                    "An company with the same name already exists. Would you like to update their information?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    addToDatabase(client_data, sql_headers, "clients", "update", existing_employer_id)
                    QMessageBox.information(self, "Updated", "The client's information has been updated.")
                else:
                    return  # Do not proceed with adding a new employer
            else:
                addToDatabase(client_data, sql_headers, "clients")
            self.populateTable()

    def exportToExcel(self):
        try:
            # Directory where the Excel files will be saved
            out_dir = find_output_directory()
            export_dir = Path(out_dir, "exported_tables")
            os.makedirs(export_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Prepare data for export
            data = []
            for row in range(self.tableWidget.rowCount()):
                row_data = []
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(data, columns=[self.tableWidget.horizontalHeaderItem(i).text() for i in
                                             range(self.tableWidget.columnCount())])

            # Naming strategy: "employees_" + current date
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"clients_{current_date}.xlsx"
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


class CurrentJobOrdersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)

        # Header
        self.headerLayout = QHBoxLayout()
        self.titleLabel = QLabel("Current Job Orders")
        self.titleLabel.setStyleSheet("font-size: 18pt; font-weight: bold; color: #64bfd1;")
        self.headerLayout.addWidget(self.titleLabel)
        self.layout.addLayout(self.headerLayout)

        # Table and button layout
        tableButtonLayout = QHBoxLayout()

        # Create Scroll Area
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)

        # Scroll Area Widget Contents
        self.scrollAreaWidgetContents = QWidget()

        # Scroll Area Layer
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(self.scrollAreaLayout)

        # Table Widget for Job Orders
        self.tableWidget = TableWidget(HEADERS["JOB_ORDER_HEADERS"], "Job Order")
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.scrollAreaLayout.addWidget(self.tableWidget)

        # Set the scroll area widget
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        tableButtonLayout.addWidget(self.scrollArea)

        # Layout for buttons
        buttonsLayout = QVBoxLayout()

        self.editButton = QPushButton("Edit Job Orders")
        self.saveButton = QPushButton("Save Updates")
        self.revertButton = QPushButton("Revert Changes")
        self.deleteButton = QPushButton("Delete Job Order(s)")
        self.exportButton = QPushButton("Export Table")

        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

        # Add buttons to the buttons layout
        buttonsLayout.addWidget(self.editButton)
        buttonsLayout.addWidget(self.saveButton)
        buttonsLayout.addWidget(self.revertButton)
        buttonsLayout.addWidget(self.deleteButton)
        buttonsLayout.addWidget(self.exportButton)

        # Add some stretch to push everything up
        buttonsLayout.addStretch()

        # Add the Open Employee Finder Agent Button
        self.openEmployeeFinderAgentButton = QPushButton("Open Employee Finder Agent")
        self.openEmployeeFinderAgentButton.clicked.connect(self.openEmployeeFinderAgent)
        buttonsLayout.addWidget(self.openEmployeeFinderAgentButton, alignment=Qt.AlignBottom)

        tableButtonLayout.addLayout(buttonsLayout)

        self.editButton.clicked.connect(self.enableEditing)
        self.saveButton.clicked.connect(self.saveUpdates)
        self.revertButton.clicked.connect(self.revertChanges)
        self.deleteButton.clicked.connect(self.deleteEntry)
        self.exportButton.clicked.connect(self.exportToExcel)

        self.originalTableData = None

        self.layout.addLayout(tableButtonLayout)

        # Filter and Sorting Section
        self.filterSectionHeader = QLabel("Filter Job Orders")
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

        self.layout.addLayout(self.filterRowLayout)

        # Populate the Table
        self.populateTable()

    def enableEditing(self):
        self.tableWidget.enableEditing()
        self.editButton.setEnabled(False)
        self.saveButton.setEnabled(True)
        self.revertButton.setEnabled(True)
        self.deleteButton.setEnabled(True)

    def saveUpdates(self):
        # Construct and execute SQL queries based on pendingChanges
        for change in self.tableWidget.pendingChanges:
            sql = f"UPDATE job_orders SET {change['columnName']} = %s WHERE id = %s"
            data = (change['newValue'], change['rowId'])
            execute_query(sql, data)

        # Clear pending changes after saving
        self.tableWidget.pendingChanges.clear()

        # For now, just show a message box.
        QMessageBox.information(self, "Info", "Changes saved.")
        self.disableEditing()

    def revertChanges(self):
        # Revert changes: Reset the table data to originalTableData
        for row in range(self.tableWidget.rowCount()):
            for col in range(self.tableWidget.columnCount()):
                if self.tableWidget.item(row, col):
                    self.tableWidget.item(row, col).setText(self.tableWidget.originalTableData[row][col])
        # Clear pending changes
        self.tableWidget.pendingChanges.clear()

    def deleteEntry(self):
        # Determine the selected rows in the table widget
        selectedRows = self.tableWidget.selectionModel().selectedRows()
        if not selectedRows:
            QMessageBox.warning(self, "Selection Required", "Please select at least one row to delete.")
            return

        # Confirmation dialog before deletion
        reply = QMessageBox.question(self, "Delete Entries", "Are you sure you want to delete the selected entries?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                connection = create_db_connection()  # Assuming this function returns a valid connection
                if connection:
                    with connection.cursor() as cursor:
                        # Begin a transaction
                        connection.start_transaction()
                        for selectedRow in sorted(selectedRows, reverse=True):
                            idToDelete = selectedRow.row() + 1
                            for i in range(self.tableWidget.columnCount()):
                                if self.tableWidget.isColumnHidden(i):
                                    idToDelete = int(self.tableWidget.item(selectedRow.row(), i).text())

                            client_id = retrieve_current_company(idToDelete)
                            if client_id is not None:
                                self.remove_active_employees_from_client(client_id, idToDelete)
                                archive_and_delete_company_job_order(client_id, idToDelete)

                            # Assuming the table is named 'employees', adjust as necessary
                            deleteQuery = "DELETE FROM job_orders WHERE id = %s"
                            cursor.execute(deleteQuery, (idToDelete,))
                        # Commit the transaction
                        connection.commit()
                    QMessageBox.information(self, "Success", "The selected entries have been deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")
                # Rollback in case of error
                if connection.in_transaction:
                    connection.rollback()
            finally:
                if connection and connection.is_connected():
                    connection.close()

            # Remove the rows from the table widget. Iterate in reverse order to avoid index shifting issues.
            for selectedRow in sorted(selectedRows, reverse=True):
                self.tableWidget.removeRow(selectedRow.row())

    @staticmethod
    def remove_active_employees_from_client(employer_id, job_order_id):
        # Fetch the current values of needed_employees and active_employees
        query = "SELECT active_employees FROM job_orders WHERE id = %s"
        result = execute_query(query, (job_order_id,), fetch_mode='one')
        if result:
            jo_active_employees = result[0]
        else:
            return

        query = "SELECT active_employees FROM clients WHERE id = %s"
        result = execute_query(query, (employer_id,), fetch_mode='one')
        if result:
            cl_active_employees = result[0]
        else:
            return

        # Decrement needed_employees
        new_active_employees = cl_active_employees - jo_active_employees

        # Update the clients table with the new values
        update_query = """
                        UPDATE clients 
                        SET active_employees = %s 
                        WHERE id = %s
                        """
        execute_query(update_query, (new_active_employees, employer_id))

    def disableEditing(self):
        self.tableWidget.disableEditing()
        self.editButton.setEnabled(True)
        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

    def onHeaderClicked(self, logicalIndex):
        """
        Sorts the table based on the clicked column header and updates the header to display a sorting arrow.

        Args:
            logicalIndex (int): Index of the clicked column header.

        The method toggles sorting order and updates the table based on the selected column.
        """
        self.currentSortOrder = not getattr(self, 'currentSortOrder', False)
        sorting_order = Qt.AscendingOrder if self.currentSortOrder else Qt.DescendingOrder
        self.tableWidget.sortItems(logicalIndex, sorting_order)

        # Update header icons for sorting indication
        for i in range(self.tableWidget.columnCount()):
            header = self.tableWidget.horizontalHeaderItem(i)
            header.setIcon(QIcon())  # Clear previous icons

        # Set the sort indicator icon
        sort_icon = QIcon("^") if self.currentSortOrder else QIcon("↓")
        self.tableWidget.horizontalHeaderItem(logicalIndex).setIcon(sort_icon)

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
        column_index = self.tableWidget.currentColumn()

        if column_index == -1:
            return  # Exit if no column is selected

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, column_index)
            if item is None:
                self.tableWidget.setRowHidden(row, True)
                continue

            cell_value = item.text()

            # Adjust for case sensitivity based on Cc button
            if not self.ccButton.isChecked():
                filter_text = filter_text.lower()
                cell_value = cell_value.lower()

            # Adjust for "Starts With" functionality based on Sw button
            if self.swButton.isChecked():
                self.tableWidget.setRowHidden(row, not cell_value.startswith(filter_text))
            else:
                self.tableWidget.setRowHidden(row, filter_text not in cell_value)

    def populateTable(self):
        """
        Populate the table with data from the clients database.
        Optionally filters the employees based on their type.
        """
        self.tableWidget.setRowCount(0)  # Clear the table

        # Adjust SQL query based on employee type
        query = "SELECT * FROM job_orders"

        # Fetch data from the database
        results = execute_query(query, fetch_mode="all", return_cursor=True)
        job_orders = results["result"]
        cursor = results["cursor"]
        for row, job_data in enumerate(job_orders):
            self.tableWidget.insertRow(row)
            column_names = list(HEADERS["JOB_ORDER_HEADERS"].keys())
            for column, column_name in enumerate(column_names):
                # Get the value corresponding to the column name
                value = job_data[cursor.column_names.index(column_name)]
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.tableWidget.setItem(row, column, item)
                if column_name == "id":
                    self.tableWidget.hideColumn(column)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    @staticmethod
    def openEmployeeFinderAgent():
        dialog = RankingEmployeeResultsDialog()
        dialog.exec_()

    def exportToExcel(self):
        try:
            # Directory where the Excel files will be saved
            out_dir = find_output_directory()
            export_dir = Path(out_dir, "exported_tables")
            os.makedirs(export_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Prepare data for export
            data = []
            for row in range(self.tableWidget.rowCount()):
                row_data = []
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(data, columns=[self.tableWidget.horizontalHeaderItem(i).text() for i in
                                             range(self.tableWidget.columnCount())])

            # Naming strategy: "employees_" + current date
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"job_orders_{current_date}.xlsx"
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


class OldJobOrdersPage(QWidget):
    def __init__(self, dbSide, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.dbSide = dbSide
        self.table = "old_employee_job_orders" if self.dbSide == "Employee" else "old_company_job_orders"
        self.layout.setSpacing(5)

        # Header
        self.headerLayout = QHBoxLayout()
        self.titleLabel = QLabel("Old Job Orders")
        self.titleLabel.setStyleSheet("font-size: 18pt; font-weight: bold; color: #64bfd1;")
        self.headerLayout.addWidget(self.titleLabel)
        self.layout.addLayout(self.headerLayout)

        # Delete Entries Button
        self.headerLayout.addStretch()
        self.deleteEntriesButton = QPushButton("Delete Entry(s)")
        self.deleteEntriesButton.clicked.connect(self.deleteEntries)
        self.headerLayout.addWidget(self.deleteEntriesButton)

        self.exportButton = QPushButton("Export Table")
        self.exportButton.clicked.connect(self.exportToExcel)
        self.headerLayout.addWidget(self.exportButton)

        self.layout.addLayout(self.headerLayout)

        # Create Scroll Area
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)

        # Scroll Area Widget Contents
        self.scrollAreaWidgetContents = QWidget()

        # Scroll Area Layer
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(self.scrollAreaLayout)

        # Table Widget for Old Job Orders
        self.headers = HEADERS["OLD_EMPLOYEE_JOB_ORDER_HEADERS"] if self.dbSide == "Employee" else HEADERS[
            "OLD_COMPANY_JOB_ORDER_HEADERS"]
        self.tableWidget = TableWidget(self.headers, "Old Job Orders")
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.scrollAreaLayout.addWidget(self.tableWidget)

        # Set the scroll area widget
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea.horizontalScrollBar().setVisible(True)

        self.layout.addWidget(self.scrollArea)

        # Filter and Sorting Section
        self.filterSectionHeader = QLabel("Filter Job Orders")
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

        self.layout.addLayout(self.filterRowLayout)

        # Populate the Table with data
        self.populateTable()

    def populateTable(self):
        """
        Populate the table with data from the clients database.
        Optionally filters the employees based on their type.
        """
        self.tableWidget.setRowCount(0)  # Clear the table

        # Adjust SQL query based on employee type
        query = f"SELECT * FROM {self.table}"

        # Fetch data from the database
        results = execute_query(query, fetch_mode="all", return_cursor=True)
        job_orders = results["result"]
        cursor = results["cursor"]
        for row, job_data in enumerate(job_orders):
            self.tableWidget.insertRow(row)
            column_names = list(self.headers.keys())
            for column, column_name in enumerate(column_names):
                # Get the value corresponding to the column name
                value = job_data[cursor.column_names.index(column_name)]
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.tableWidget.setItem(row, column, item)
                if column_name == "id":
                    self.tableWidget.hideColumn(column)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def filterTable(self):
        """
        Filters the table rows based on the text entered in the filterTextEditor and the selected column.

        The method performs a case-insensitive comparison of the filter text with the data in the selected column.
        It hides rows that do not contain the filter text in the selected column. The comparison takes into
        account the data type of the column (numeric, date, or string) for appropriate formatting and comparison.
        """
        filter_text = self.filterTextEditor.text()
        column_index = self.tableWidget.currentColumn()

        if column_index == -1:
            return  # Exit if no column is selected

        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, column_index)
            if item is None:
                self.tableWidget.setRowHidden(row, True)
                continue

            cell_value = item.text()

            # Adjust for case sensitivity based on Cc button
            if not self.ccButton.isChecked():
                filter_text = filter_text.lower()
                cell_value = cell_value.lower()

            # Adjust for "Starts With" functionality based on Sw button
            if self.swButton.isChecked():
                self.tableWidget.setRowHidden(row, not cell_value.startswith(filter_text))
            else:
                self.tableWidget.setRowHidden(row, filter_text not in cell_value)

    def deleteEntries(self):
        # Determine the selected rows in the table widget
        selectedRows = self.tableWidget.selectionModel().selectedRows()
        if not selectedRows:
            QMessageBox.warning(self, "Selection Required", "Please select at least one row to delete.")
            return

        # Confirmation dialog before deletion
        reply = QMessageBox.question(self, "Delete Entries",
                                     "Are you sure you want to delete the selected entries?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                connection = create_db_connection()  # Assuming this function returns a valid connection
                if connection:
                    with connection.cursor() as cursor:
                        # Begin a transaction
                        connection.start_transaction()
                        for selectedRow in sorted(selectedRows, reverse=True):
                            idToDelete = selectedRow.row() + 1
                            for i in range(self.tableWidget.columnCount()):
                                if self.tableWidget.isColumnHidden(i):
                                    idToDelete = int(self.tableWidget.item(selectedRow.row(), i).text())

                            # Assuming the table is named 'employees', adjust as necessary
                            deleteQuery = f"DELETE FROM {self.table} WHERE id = %s"
                            cursor.execute(deleteQuery, (idToDelete,))
                        # Commit the transaction
                        connection.commit()
                    QMessageBox.information(self, "Success", "The selected entries have been deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {e}")
                # Rollback in case of error
                if connection.in_transaction:
                    connection.rollback()
            finally:
                if connection and connection.is_connected():
                    connection.close()

            # Remove the rows from the table widget. Iterate in reverse order to avoid index shifting issues.
            for selectedRow in sorted(selectedRows, reverse=True):
                self.tableWidget.removeRow(selectedRow.row())

    def onHeaderClicked(self, logicalIndex):
        """
        Sorts the table based on the clicked column header and updates the header to display a sorting arrow.

        Args:
            logicalIndex (int): Index of the clicked column header.

        The method toggles sorting order and updates the table based on the selected column.
        """
        self.currentSortOrder = not getattr(self, 'currentSortOrder', False)
        sorting_order = Qt.AscendingOrder if self.currentSortOrder else Qt.DescendingOrder
        self.tableWidget.sortItems(logicalIndex, sorting_order)

        # Update header icons for sorting indication
        for i in range(self.tableWidget.columnCount()):
            header = self.tableWidget.horizontalHeaderItem(i)
            header.setIcon(QIcon())  # Clear previous icons

        # Set the sort indicator icon
        sort_icon = QIcon("^") if self.currentSortOrder else QIcon("↓")
        self.tableWidget.horizontalHeaderItem(logicalIndex).setIcon(sort_icon)

    def updateButtonStyle(self, sender):
        """
        Updates the style of the Sw and Cc buttons based on their checked state.
        """
        sender = self.sender()
        if sender.isChecked():
            sender.setStyleSheet("background-color: #4d8d9c;")  # Darker color when checked
        else:
            sender.setStyleSheet("")  # Revert to default stylesheet

    def exportToExcel(self):
        try:
            # Directory where the Excel files will be saved
            out_dir = find_output_directory()
            export_dir = Path(out_dir, "exported_tables")
            os.makedirs(export_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Prepare data for export
            data = []
            for row in range(self.tableWidget.rowCount()):
                row_data = []
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(data, columns=[self.tableWidget.horizontalHeaderItem(i).text() for i in
                                             range(self.tableWidget.columnCount())])

            # Naming strategy: "employees_" + current date
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"old_job_orders_{current_date}.xlsx"
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


class DashboardPage(QWidget):
    """
    A placeholder page for the Dashboard section of the application.

    Currently, it displays a 'Coming Soon' message.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Message Label
        messageLabel = QLabel("Dashboard Coming Soon")
        messageLabel.setAlignment(Qt.AlignCenter)  # Center align the text
        self.layout.addWidget(messageLabel)


class MainWindow(QMainWindow):
    """
    MainWindow is the main application window that contains the menu and other widgets.

    Functions:
    - __init__: Initializes the MainWindow.
    - initUI: Sets up the main window's title, size, and menu bar.
    - showEmployeePage: Shows the EmployeePage widget when the "Manage Employees" menu item is clicked.
    - showClientPage: Shows the ClientPage widget when the "Manage Clients" menu item is clicked.
    - showJobOrderPage: Shows the JobOrderPage dialog for creating job orders.
    """

    def __init__(self):
        super().__init__()
        self.employeePage = None
        self.clientPage = None
        self.currentJobOrderPage = None
        self.dashboardPage = None
        self.initUI()
        self.setCentralWidget(self.dashboardPage)

    def initUI(self):
        # Setting up the main window
        self.setWindowTitle("Employee and Client Management System")
        self.setGeometry(100, 100, 1720, 600)
        self.setWindowIcon(QIcon(str(Path(application_path, 'resources', 'icons', 'crm-icon-high-seas.png'))))

        # Create menu bar and add items
        menubar = self.menuBar()
        dashboardMenu = menubar.addMenu('Dashboard')
        employeeMenu = menubar.addMenu('Employee')
        clientMenu = menubar.addMenu('Client')

        # Create actions for menu items
        manageW2Action = QAction("Manage W-2 Employees", self)
        manageW2Action.triggered.connect(lambda: self.manage_employees("W2"))
        manage1099Action = QAction("Manage 1099 Employees", self)
        manage1099Action.triggered.connect(lambda: self.manage_employees("1099"))
        manageNAAction = QAction("Manage Not Active Employees", self)
        manageNAAction.triggered.connect(lambda: self.manage_employees("Not Active"))
        viewOldEmployeeJobOrdersAction = QAction("View Old Job Orders", self)
        viewOldEmployeeJobOrdersAction.triggered.connect(lambda: self.showOldJobOrdersPage("Employee"))
        employeeMenu.addAction(manageW2Action)
        employeeMenu.addAction(manage1099Action)
        employeeMenu.addAction(manageNAAction)
        employeeMenu.addAction(viewOldEmployeeJobOrdersAction)

        clientAction = QAction("Manage Clients", self)
        clientAction.triggered.connect(self.showClientPage)
        clientMenu.addAction(clientAction)
        jobOrderAction = QAction("Current Job Orders", self)
        jobOrderAction.triggered.connect(self.showCurrentJobOrderPage)
        clientMenu.addAction(jobOrderAction)
        viewOldClientJobOrdersAction = QAction("View Old Job Orders", self)
        viewOldClientJobOrdersAction.triggered.connect(lambda: self.showOldJobOrdersPage("Client"))
        clientMenu.addAction(viewOldClientJobOrdersAction)

        dashboardAction = QAction('Dashboard', self)
        dashboardAction.triggered.connect(self.showDashboardPage)
        dashboardMenu.addAction(dashboardAction)

        self.showDashboardPage()

    def manage_employees(self, employee_type):
        """
        Display employees of a specific type in the table widget.

        Args:
            employee_type (str): The type of employees to display ("W2" or "1099").
        """
        try:
            self.employeePage = EmployeePage(employee_type)
            self.setCentralWidget(self.employeePage)
        except RuntimeError as e:
            show_error_message(f"Error occurred: {e}. Please try again.")

    def showClientPage(self):
        # Show the Client Page
        try:
            self.clientPage = ClientPage()
            self.setCentralWidget(self.clientPage)
        except RuntimeError as e:
            show_error_message(f"Error occurred: {e}. Please try again.")

    def showJobOrderPage(self, employerData, employer_id):
        jobOrderDialog = JobOrderPage(employerData, employer_id, self)
        jobOrderDialog.exec_()  # Executing the dialog

    def showOldJobOrdersPage(self, dbSide):
        # Show the Old Job Orders Page
        try:
            oldJobOrdersPage = OldJobOrdersPage(dbSide)  # You need to define this class
            self.setCentralWidget(oldJobOrdersPage)
        except RuntimeError as e:
            show_error_message(f"Error occurred: {e}. Please try again.")

    def showCurrentJobOrderPage(self):
        # Show the Client Page
        try:
            self.currentJobOrderPage = CurrentJobOrdersPage()
            self.setCentralWidget(self.currentJobOrderPage)
        except RuntimeError as e:
            show_error_message(f"Error occurred: {e}. Please try again.")

    def showDashboardPage(self):
        # Show the Dashboard Page
        try:
            self.dashboardPage = DashboardPage()
            self.setCentralWidget(self.dashboardPage)
        except RuntimeError as e:
            show_error_message(f"Error occurred: {e}. Please try again.")


def load_stylesheet() -> str:
    """
    Load the stylesheet from a given file path.

    :return: The stylesheet content as a string.
    """
    # Determine the full path to the icons folder
    icons_path = Path(application_path, 'resources', 'icons')
    try:
        with open(Path(application_path, 'resources', 'style_properties', 'stylesheet.qss'), "r") as file:
            return file.read().replace('{{ICON_PATH}}', str(icons_path).replace("\\", "/"))
    except IOError:
        print(
            f"Error opening stylesheet file: "
            f"{Path(application_path, 'resources', 'style_properties', 'stylesheet.qss')}")
        return ""


def update_employee_availability():
    # Today's date for reference
    today = datetime.now()
    one_month_away = today + timedelta(days=30)

    # Find job_orders ending in 1 month
    job_orders_ending_soon_query = """
            SELECT id FROM job_orders WHERE end_date BETWEEN %s AND %s
            """
    job_orders_ending_soon = execute_query(job_orders_ending_soon_query, (today, one_month_away), fetch_mode='all')

    # Update employees associated with these job orders to "~A"
    for job_id in job_orders_ending_soon:
        update_employees_availability_query = """
            UPDATE employees SET availability = '~A'
            WHERE id IN (SELECT employee_id FROM job2employer_ids WHERE job_order_id = %s)
            """
        execute_query(update_employees_availability_query, (job_id[0],))

    # Step 2: Find job orders that ended yesterday
    job_orders_ended_yesterday_query = """
        SELECT id FROM job_orders WHERE end_date < %s
        """
    job_orders_ended_yesterday = execute_query(job_orders_ended_yesterday_query, (today,), fetch_mode='all')

    # Update employees associated with these job orders
    for job_id in job_orders_ended_yesterday:
        # Retrieve employee IDs for the job_id
        employee_ids_query = """
            SELECT employee_id FROM job2employer_ids WHERE job_order_id = %s
        """
        employee_ids = execute_query(employee_ids_query, (job_id[0],), fetch_mode="all")

        client_id_query = """
            SELECT client_id FROM job2employer_ids WHERE job_order_id = %s
        """
        client_id = execute_query(client_id_query, (job_id[0],), fetch_mode="one")

        for employee_id in employee_ids:
            # Archive and delete job order details for each employee
            archive_and_delete_employee_job_order(employee_id[0], job_id[0])
            archive_and_delete_company_job_order(client_id[0], job_id[0])

            # Update employee's status and details
            update_employee_query = """
                UPDATE employees 
                SET availability = 'NW', employee_type = NULL, job_id = NULL, hired_date = NULL, pay = NULL, 
                pay_conversion = NULL 
                WHERE id = %s
            """
            execute_query(update_employee_query, (employee_id[0],))


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)
    # Try connecting and checking the database and tables
    config = load_json_file(file_type="Database Configuration JSON file", skip_error_dlg=True)
    if config:
        # Try to connect with existing config
        connection_success = check_database_and_tables(config["database"])
    else:
        connection_success = False

    if not connection_success:
        # Show dialog to get new database info
        db_info = getDatabaseInfo()
        if db_info:
            host, user, password, database = db_info
            # Save new config and attempt to create the database and tables
            new_config = {"host": host, "user": user, "password": password, "database": database}
            save_db_config(new_config)
            if not check_database_and_tables(database):
                QMessageBox.critical(None, "Error", "Failed to create the database or tables.")
        else:
            QMessageBox.critical(None, "Error", "Database connection details are required to start "
                                                "the application.")

    update_employee_availability()
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QIcon
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QApplication, QMenu, QAction

from tools.company_card.company_card import ClientCard
from tools.employee_card.employee_card import EmployeeCard
from tools.job_order_card.job_order_card import JobOrderCard
from tools.mydb import *


class TableWidget(QTableWidget):
    def __init__(self, headers, type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.originalTableData = []  # Initialize the original data holder
        self.pendingChanges = []  # Initialize the changes holder
        # Connect the itemChanged signal
        self.itemChanged.connect(self.handleItemChanged)
        self.headers = headers
        self.setColumnCount(len(self.headers.values()))
        self.setHorizontalHeaderLabels(self.headers.values())
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.headerContextMenu)
        self.cellDoubleClicked.connect(self.cellDoubleClickHandler)
        self.tableType = type
        self.isRecordingChanges = False  # Add flag to control change recording

        # Configure column resizing behavior
        self.adjustColumnResizing()

        self.disableEditing()

    def headerContextMenu(self, pos):
        menu = QMenu(self)
        delete_col_action = QAction("Delete Column", self)
        menu.addAction(delete_col_action)
        action = menu.exec_(self.mapToGlobal(pos))
        if action == delete_col_action:
            col = self.horizontalHeader().logicalIndexAt(pos)
            self.removeColumn(col)

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

    def enableEditing(self):
        self.enableTable()
        # Copy the original data from the table
        self.originalTableData = [[self.item(row, col).text() if self.item(row, col) else ""
                                   for col in range(self.columnCount())] for row in range(self.rowCount())]
        self.setEditTriggers(QTableWidget.AllEditTriggers)

    def disableEditing(self):
        self.disableTable()
        self.setEditTriggers(QTableWidget.NoEditTriggers)

    def handleItemChanged(self, item):
        if item is None or not self.isRecordingChanges:  # Check flag before recording changes
            return

        # Grab the row value as it pertains to the database, not this table.
        rowId = self.currentRow()
        for i in range(self.columnCount()):
            if self.isColumnHidden(i):
                hiddenItem = self.item(rowId, i)
                if hiddenItem is not None:
                    rowId = int(hiddenItem.text())
                    break
        columnName = self.horizontalHeaderItem(item.column()).text()
        for key, value in self.headers.items():
            if value == columnName:
                columnName = key
        newValue = item.text()
        try:
            originalValue = self.originalTableData[item.row()][item.column()]
        except IndexError:
            originalValue = ""
        # Check if the new value is different from the original
        if newValue != originalValue:
            # Record the change
            self.pendingChanges.append({
                "rowId": rowId,
                "columnName": columnName,
                "newValue": newValue
            })

    def enableTable(self):
        nonEditableColumns = ['Job ID', 'Hired Date', 'Availability', 'Active Employees', 'PO Order Number']
        rowCount = self.rowCount()
        columnCount = self.columnCount()

        for column in range(columnCount):
            columnName = self.horizontalHeaderItem(column).text()
            if columnName not in nonEditableColumns:
                for row in range(rowCount):
                    item = self.item(row, column)
                    # If there's no item in a cell, create one to ensure it can be potentially editable
                    if not item:
                        item = QTableWidgetItem()
                        self.setItem(row, column, item)
                    # Only allow editing if the column name is not in the non-editable list
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
            else:
                # For non-editable columns, ensure the flag for editing is not set
                for row in range(rowCount):
                    item = self.item(row, column)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        self.isRecordingChanges = True

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
        self.isRecordingChanges = False

    def cellDoubleClickHandler(self, row, column):
        # Determine the Database ID from the row
        dbId = self.getDatabaseId(row)

        # Call the appropriate class based on tableType
        if self.tableType == "Employee":
            job_id = self.getId(dbId, "employee_id", "job_order_id")
            employer_id = self.getId(dbId, "employee_id", "client_id")
            employeeCard = EmployeeCard(dbId, employer_id, job_id)
            employeeCard.exec_()
        elif self.tableType == "Client":
            allJobIds = self.getAllJobIds(dbId)
            clientCard = ClientCard(dbId, allJobIds)
            clientCard.exec_()
        elif self.tableType == "Job Order":
            jobOrderCard = JobOrderCard(dbId)
            jobOrderCard.clientCardRequested.connect(self.openClientCard)
            jobOrderCard.exec_()

    def getDatabaseId(self, row):
        # Assuming the database ID is stored in a specific column, e.g., the first hidden column
        for i in range(self.columnCount()):
            if self.isColumnHidden(i):
                item = self.item(row, i)
                if item is not None:
                    return int(item.text())
        return None

    @staticmethod
    def getId(_id, input_id, output_id):
        query = f"SELECT {output_id} FROM job2employer_ids WHERE {input_id} = %s;"
        data = (_id,)
        result = execute_query(query, data, fetch_mode='one')

        if result:
            return result[0]
        else:
            # Handle the case where the query encountered an error
            return None

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

    @staticmethod
    def openClientCard(job_id):
        query = f"SELECT company FROM job_orders WHERE id = %s"
        company_name = execute_query(query, (job_id,), fetch_mode="one")
        query = f"SELECT id FROM clients WHERE employer_company = %s"
        employer_id = execute_query(query, company_name, fetch_mode="one")
        employer_id = employer_id[0]
        query = f"SELECT id FROM job_orders WHERE company = %s"
        allJobIds = execute_query(query, company_name, fetch_mode="all")

        clientCard = ClientCard(employer_id, allJobIds)
        clientCard.exec_()


def getDatabaseInfo(parent=None):
    dialog = QDialog(parent)
    layout = QVBoxLayout(dialog)

    # Create line edits for database information with hints
    host_edit = QLineEdit()
    host_edit.setPlaceholderText("localhost")
    user_edit = QLineEdit()
    user_edit.setPlaceholderText("root")
    password_edit = QLineEdit()
    password_edit.setEchoMode(QLineEdit.Password)
    database_edit = QLineEdit()
    database_edit.setPlaceholderText("")

    # Add widgets to layout
    layout.addWidget(QLabel("Host:"))
    layout.addWidget(host_edit)
    layout.addWidget(QLabel("Username:"))
    layout.addWidget(user_edit)
    layout.addWidget(QLabel("Password:"))
    layout.addWidget(password_edit)
    layout.addWidget(QLabel("Database Name:"))
    layout.addWidget(database_edit)

    # Dialog buttons
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    # Show dialog and wait for user action
    if dialog.exec_() == QDialog.Accepted:
        return host_edit.text(), user_edit.text(), password_edit.text(), database_edit.text()
    else:
        return None

import os
import sys
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import (QVBoxLayout, QScrollArea, QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QTableWidgetItem, QApplication)

from tools.job_order_card.job_order_card import JobOrderCard
from tools.mydb import *


class CardTableWidget(QTableWidget):
    def __init__(self, rankings, *args, **kwargs):
        super(CardTableWidget, self).__init__(*args, **kwargs)
        self.job_ids = {}
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setMouseTracking(True)  # Enable mouse tracking to show tooltips on hover
        self.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.setupTable()
        self.populateTable(rankings)
        self.disableTable()
        self.adjustColumnResizing()
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)

    def populateTable(self, rankings):
        row = 0
        ranking_number = 1  # Initialize ranking number
        for index, score in rankings:
            if score == 0.0:
                continue  # Skip if score is 0.00

            # Fetch employee data using execute_query function
            employee_query = ("SELECT first_name, last_name, availability, job_id, employee_type FROM employees "
                              "WHERE id = %s")
            employee_result = execute_query(employee_query, (index,), fetch_mode="one", get_column_names=True)

            if employee_result and 'result' in employee_result and employee_result['result']:
                employee_data = employee_result['result']
                column_names = employee_result.get('column_names', [])
                first_name_index = column_names.index('first_name') if 'first_name' in column_names else None
                last_name_index = column_names.index('last_name') if 'last_name' in column_names else None

                employee_name = f"{employee_data[first_name_index]} {employee_data[last_name_index]}" if first_name_index is not None and last_name_index is not None else "N/A"
                match_percentage = "{:.2%}".format(score)  # Convert score to percentage
                availability_index = column_names.index('availability') if 'availability' in column_names else None
                job_id_index = column_names.index('job_id') if 'job_id' in column_names else None
                employee_type_index = column_names.index('employee_type') if 'employee_type' in column_names else None

                availability = employee_data[availability_index] if availability_index is not None else "N/A"
                job_id = employee_data[job_id_index] if job_id_index is not None else "N/A"
                employee_type = employee_data[employee_type_index] if employee_type_index is not None else "N/A"

                # Prepare data for the table
                data = [employee_name, match_percentage, str(ranking_number), availability, job_id, employee_type,
                        str(index)]

                self.setRowCount(row + 1)
                for col, value in enumerate(data):
                    self.setItem(row, col, QTableWidgetItem(str(value)))

                row += 1
                ranking_number += 1  # Increment ranking for the next row

    def setupTable(self):
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
            ["Employee Name", "Match (%)", "Ranking", "Availability", "Job ID", "Employee Type", "Database ID"])

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
                item = self.item(row, column)
                if item:  # Check if item is not None
                    itemWidth = fontMetrics.width(item.text()) + 50  # Again, adding some padding
                    maxWidth = max(maxWidth, itemWidth)

            self.setColumnWidth(column, maxWidth)
            totalWidth += maxWidth

        # Set the minimum width of the table to accommodate the widest cell or column name
        self.setMinimumWidth(totalWidth)


class RankingResultsDialog(QDialog):
    def __init__(self, rankings, parent=None):
        super().__init__(parent)
        self.rankings = sorted(rankings, key=lambda x: x[1], reverse=True)  # Sort rankings by score in descending order
        self.setWindowTitle("Ranking Results")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.resize(1000, 800)

        layout = QVBoxLayout(self)

        # Title label
        self.titleLabel = QLabel("Ranking Results Overview")
        self.titleLabel.setStyleSheet("font-size: 20pt; font-weight: bold; color: #64bfd1;")
        layout.addWidget(self.titleLabel)

        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)

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

        self.table = CardTableWidget(self.rankings)
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

        # Hide the 'Database ID' column
        self.table.setColumnHidden(6, True)

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
            file_name = f"employees_{current_date}.xlsx"
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


def load_stylesheet() -> str:
    """
    Load the stylesheet from a given file path.

    :return: The stylesheet content as a string.
    """
    # Determine the full path to the icons folder
    base_dir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
    icons_path = f"{base_dir}/icons"

    try:
        with open(os.path.join(base_dir, 'style_properties', 'stylesheet.qss'), "r") as file:
            return file.read().replace('{{ICON_PATH}}', icons_path)
    except IOError:
        print(f"Error opening stylesheet file: {os.path.join(base_dir, 'style_properties', 'stylesheet.qss')}")
        return ""


# Example usage
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)
    # Try connecting and checking the database and tables
    config = load_json_file(file_type="Database Configuration JSON file")
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

    # Mock rankings
    rankings = [(1, 0.95), (2, 0.85), (3, 0.0)]  # Example rankings
    dialog = RankingResultsDialog(rankings)
    dialog.show()
    sys.exit(app.exec_())

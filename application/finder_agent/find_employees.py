import sys
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (QVBoxLayout, QScrollArea, QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QTableWidgetItem, QApplication)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from application.employee_card.employee_card import EmployeeCard
from resources.tools.helpful_functions import *


class CardTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(CardTableWidget, self).__init__(*args, **kwargs)
        self.job_ids = {}
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setMouseTracking(True)  # Enable mouse tracking to show tooltips on hover
        self.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.setupTable()
        self.disableTable()
        self.adjustColumnResizing()
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)

    def populateTable(self, rankings):
        self.clearContents()  # Clear the table contents before populating
        self.setRowCount(0)  # Reset the row count to 0 to remove all existing rows
        row = 0
        ranking_number = 1  # Initialize ranking number
        for index, score in rankings:
            _id = index[0]
            if score == 0.0:
                continue  # Skip if score is 0.00

            # Fetch employee data using execute_query function
            employee_query = ("SELECT first_name, last_name, availability, job_id, employee_type FROM employees "
                              "WHERE id = %s")
            employee_result = execute_query(employee_query, (_id,), fetch_mode="one", get_column_names=True)

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
                        str(index[0])]

                self.setRowCount(row + 1)
                for col, value in enumerate(data):
                    item = QTableWidgetItem(str(value))
                    # Set tooltip for each item. You can customize this tooltip as needed.
                    tooltip_text = f"{value}"
                    item.setToolTip(tooltip_text)
                    self.setItem(row, col, item)

                row += 1
                ranking_number += 1  # Increment ranking for the next row

    def setupTable(self):
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
            ["Employee Name", "Match (%)", "Ranking", "Availability", "Job ID", "Employee Type", "Database ID"])

    def onItemDoubleClicked(self, item):
        row = item.row()
        employee_id_column = next(
            (col for col in range(self.columnCount()) if self.isColumnHidden(col)),
            None,
        )
        if employee_id_column is None:
            QMessageBox.warning(self, "Error", "Employee ID column not found.")

        elif employee_id_item := self.item(row, employee_id_column):
            employee_id = int(employee_id_item.text())
            employeeCard = EmployeeCard(employee_id)
            employeeCard.exec_()
        else:
            QMessageBox.warning(self, "Error", "Employee ID not found for the selected row.")

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


class RankingEmployeeResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ranking Employees")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.resize(1000, 800)

        layout = QVBoxLayout(self)

        # Title label
        self.titleLabel = QLabel("Ranking Employees To Job Description")
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

        # Job Info Drop Down and Button
        self.jobComboBox = QComboBox()
        self.jobOrderData = {}
        self.populateJobOrders()
        self.setupCompleter()
        label = QLabel("Choose Job Order:")
        self.generateRankingsButton = QPushButton("Rank Employees")
        self.generateRankingsButton.clicked.connect(self.generateEmployeeRankings)

        buttonLayout.addWidget(label)
        buttonLayout.addWidget(self.jobComboBox)
        buttonLayout.addWidget(self.generateRankingsButton)
        scrollLayout.addLayout(buttonLayout)

        self.table = CardTableWidget()
        scrollLayout.addWidget(self.table)
        scrollArea.setWidget(scrollWidget)

        # Filter and Sorting Section
        self.filterSectionHeader = QLabel("Filter Employees")
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

    def populateJobOrders(self):
        query = "SELECT job_description_path, job_title, po_order_number FROM job_orders"
        if results := execute_query(query, fetch_mode='all'):
            for job_description_path, job_title, po_order_number in results:
                combo_box_string = f"{job_title}-{po_order_number}"
                self.jobComboBox.addItem(combo_box_string)
                self.jobOrderData[combo_box_string] = job_description_path

    def setupCompleter(self):
        # Extract the combo box items
        items = [self.jobComboBox.itemText(i) for i in range(self.jobComboBox.count())]
        completer = QCompleter(items)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.jobComboBox.setEditable(True)
        self.jobComboBox.setCompleter(completer)

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
            file_name = f"employee_rankings_{current_date}.xlsx"
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

    def generateEmployeeRankings(self):
        selected_text = self.jobComboBox.currentText()
        job_description_path = self.jobOrderData[selected_text]

        # Check if the file extension is supported
        if not job_description_path or not job_description_path.endswith(('.doc', '.docx', '.pdf', '.txt')):
            QMessageBox.warning(self, "Unsupported File Type",
                                f"The job description path '{job_description_path}' is not supported.\n"
                                "Supported file types are: .doc, .docx, .pdf, .txt")
            self.show()  # Show the dialog again for the user to make another selection
            return

        self.generateRankingsButton.setText("Processing...")
        self.generateRankingsButton.setEnabled(False)

        # Force the UI to update
        QApplication.processEvents()

        texts = [read_text_file(job_description_path)]
        employee_data = []

        employees_query = "SELECT id, resume_path FROM employees"
        employees = execute_query(employees_query, fetch_mode="all")
        for employee_id, resume_path in employees:
            extracted_text = read_text_file(resume_path)
            texts.append(extracted_text)
            employee_data.append((employee_id, resume_path))

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)

        cosine_similarities = cosine_similarity(tfidf_matrix[:1], tfidf_matrix[1:])
        similarity_scores = cosine_similarities.flatten()
        rankings = sorted(
            list(zip(employee_data, similarity_scores)),
            key=lambda x: x[1],
            reverse=True,
        )

        self.table.populateTable(rankings)

        self.generateRankingsButton.setText("Rank Employees")
        self.generateRankingsButton.setEnabled(True)

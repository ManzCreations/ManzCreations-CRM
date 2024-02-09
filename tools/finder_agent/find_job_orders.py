import os
import sys
import threading
from datetime import datetime

import docx
import pandas as pd
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (QVBoxLayout, QScrollArea, QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QTableWidgetItem, QApplication)
from pdfminer.high_level import extract_text as extract_text_pdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tools.employee_card.employee_card import EmployeeCard
from tools.mydb import *


class CardTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(CardTableWidget, self).__init__(*args, **kwargs)
        self.job_ids = {}
        self.employee_name = ""
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

            # Fetch job data using execute_query function
            job_query = ("SELECT job_title, po_order_number, company, start_date, end_date, needed_employees, "
                              "position_type, min_experience FROM job_orders WHERE id = %s")
            job_result = execute_query(job_query, (_id,), fetch_mode="one", get_column_names=True)

            if job_result and 'result' in job_result and job_result['result']:
                job_data = job_result['result']
                column_names = job_result.get('column_names', [])

                job_title_index = column_names.index('job_title')
                po_order_number_index = column_names.index('po_order_number')
                company_index = column_names.index('company')
                start_date_index = column_names.index('start_date')
                end_date_index = column_names.index('end_date')
                needed_employees_index = column_names.index('needed_employees')
                position_type_index = column_names.index('position_type')
                min_experience_index = column_names.index('min_experience')

                match_percentage = "{:.2%}".format(score)  # Convert score to percentage
                job_title = job_data[job_title_index] if job_title_index is not None else "N/A"
                po_order_number = job_data[po_order_number_index] if po_order_number_index is not None else "N/A"
                company = job_data[company_index] if company_index is not None else "N/A"
                start_date = job_data[start_date_index] if start_date_index is not None else "N/A"
                end_date = job_data[end_date_index] if end_date_index is not None else "N/A"
                needed_employees = job_data[needed_employees_index] if needed_employees_index is not None else "N/A"
                position_type = job_data[position_type_index] if position_type_index is not None else "N/A"
                min_experience = job_data[min_experience_index] if min_experience_index is not None else "N/A"

                # Prepare data for the table
                data = [job_title, po_order_number, match_percentage, str(ranking_number), company,
                        start_date, end_date, str(needed_employees), position_type, min_experience, str(index[0])]

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
            ["Job Title", "PO Order Number", "Match (%)", "Ranking", "Company", "Start Date", "End Date",
             "Needed Employees", "Position Type", "Minimum Experience", "Database ID"])

    def onItemDoubleClicked(self, item):
        row = item.row()
        job_id_column = None

        # Loop through the columns to find the hidden one (assumed to be job_id)
        for col in range(self.columnCount()):
            if self.isColumnHidden(col):
                job_id_column = col
                break

        if job_id_column is not None:
            job_id_item = self.item(row, job_id_column)
            if job_id_item:
                job_id = int(job_id_item.text())
                jobCard = JobOrderCard(job_id)
                jobCard.exec_()
            else:
                QMessageBox.warning(self, "Error", "Employee ID not found for the selected row.")
        else:
            QMessageBox.warning(self, "Error", "Employee ID column not found.")

    def onHeaderClicked(self, logicalIndex):
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


class RankingJobOrderResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ranking Job Orders")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.resize(1000, 800)

        layout = QVBoxLayout(self)

        # Title label
        self.titleLabel = QLabel("Ranking Job Orders To Employee")
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
        self.employeeComboBox = QComboBox()
        self.employeeData = {}
        self.populateJobOrders()
        self.setupCompleter()
        label = QLabel("Choose Employee:")
        self.generateRankingsButton = QPushButton("Rank Job Orders")
        self.generateRankingsButton.clicked.connect(self.generateJobOrderRankings)

        buttonLayout.addWidget(label)
        buttonLayout.addWidget(self.employeeComboBox)
        buttonLayout.addWidget(self.generateRankingsButton)
        scrollLayout.addLayout(buttonLayout)

        self.table = CardTableWidget()
        scrollLayout.addWidget(self.table)
        scrollArea.setWidget(scrollWidget)

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

        # Add the table to the layout
        layout.addWidget(scrollArea)
        layout.addLayout(self.filterRowLayout)

        # Hide the 'Database ID' column
        self.table.setColumnHidden(6, True)

    def populateJobOrders(self):
        query = "SELECT resume_path, first_name, last_name FROM employees"
        results = execute_query(query, fetch_mode='all')
        if results:
            for resume_path, first_name, last_name in results:
                combo_box_string = f"{first_name} {last_name}"
                self.employeeComboBox.addItem(combo_box_string)
                self.employeeData[combo_box_string] = resume_path

    def setupCompleter(self):
        # Extract the combo box items
        items = [self.employeeComboBox.itemText(i) for i in range(self.employeeComboBox.count())]
        completer = QCompleter(items)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.employeeComboBox.setEditable(True)
        self.employeeComboBox.setCompleter(completer)

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
            file_name = f"job_order_rankings_{current_date}.xlsx"
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

    def generateJobOrderRankings(self):
        selected_text = self.employeeComboBox.currentText()
        resume_path = self.employeeData[selected_text]

        # Check if the file extension is supported
        if not resume_path or not resume_path.endswith(('.doc', '.docx', '.pdf', '.txt')):
            QMessageBox.warning(self, "Unsupported File Type",
                                f"The resume path '{resume_path}' is not supported.\n"
                                "Supported file types are: .doc, .docx, .pdf, .txt")
            self.show()  # Show the dialog again for the user to make another selection
            return

        self.generateRankingsButton.setText("Processing...")
        self.generateRankingsButton.setEnabled(False)

        # Force the UI to update
        QApplication.processEvents()

        texts = [read_text_file(resume_path)]
        job_data = []

        job_orders_query = "SELECT id, job_description_path FROM job_orders"
        job_orders = execute_query(job_orders_query, fetch_mode="all")
        for job_id, job_description_path in job_orders:
            extracted_text = read_text_file(job_description_path)
            texts.append(extracted_text)
            job_data.append((job_id, job_description_path))

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)

        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        similarity_scores = cosine_similarities.flatten()
        rankings = sorted([(job_id, score) for job_id, score in zip(job_data, similarity_scores)],
                          key=lambda x: x[1], reverse=True)

        self.table.populateTable(rankings)

        self.generateRankingsButton.setText("Rank Job Orders")
        self.generateRankingsButton.setEnabled(True)


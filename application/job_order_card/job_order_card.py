from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QApplication, QVBoxLayout, QListWidgetItem

from application.job_order_card.dialogs import EditCompanyDialog, AddFieldDialog
from resources.tools.helpful_functions import *


class JobOrderCard(QDialog):
    clientCardRequested = pyqtSignal(int)

    def __init__(self, job_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Details")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.resize(1200, 800)  # Set the size of the dialog

        self.job_id = job_id
        self.employer_id = None
        self.added_fields = {}
        self.ui_fields = []
        self.extra_columns = None
        self.initUI()

        # Adjust the size to screen resolution
        self.adjustSizeToScreen()

    def initUI(self):
        mainLayout = QVBoxLayout()

        # Top bar setup
        top_bar_layout = QHBoxLayout()

        # Create the title label
        titleLabel = QLabel("<h2 style='color: #64bfd1;'>Job Order Information</h2>")
        titleLabel.setAlignment(Qt.AlignLeft)
        top_bar_layout.addWidget(titleLabel)
        top_bar_layout.addStretch()

        # Company name label
        self.name_label = QLabel()
        self.fetchAndSetName()
        self.name_label.setFont(QFont("Arial", 16))
        self.name_label.setStyleSheet("color: #64bfd1; font-weight: bold;")
        top_bar_layout.addWidget(self.name_label)

        # Company icon label
        icon_label = QLabel()
        icon_pixmap = QPixmap("icons/iconmonstr-briefcase-5-white.svg")  # Placeholder icon
        scaled_pixmap = icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio)
        icon_label.setPixmap(scaled_pixmap)
        top_bar_layout.addWidget(icon_label)

        mainLayout.addLayout(top_bar_layout)

        # Create group boxes
        jobInfoGroupBox = QGroupBox("Job Information")
        jobDataGroupBox = QGroupBox("Job Data")
        jobSpecsGroupBox = QGroupBox("Job Specifications")
        jobReqsGroupBox = QGroupBox("Job Requirements")
        jobDescGroupBox = QGroupBox("Job Description")
        otherInfoGroupBox = QGroupBox("Other Information")

        # Scroll Area Setup
        scrollArea = QScrollArea(self)  # Create a QScrollArea
        scrollArea.setWidgetResizable(True)  # Allow the widget to be resizable
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Container Widget
        containerWidget = QWidget()  # This widget will hold the content
        innerLayout = QHBoxLayout(containerWidget)

        # Layouts for group boxes
        generalLayout = QVBoxLayout()
        self.jobInfoLayout = QHBoxLayout()
        self.jobInfoLeftLayout = QVBoxLayout()
        self.jobInfoRightLayout = QVBoxLayout()
        self.jobDataLayout = QHBoxLayout()
        self.jobDataLeftLayout = QVBoxLayout()
        self.jobDataRightLayout = QVBoxLayout()
        self.jobSpecsLayout = QHBoxLayout()
        self.jobSpecsLeftLayout = QVBoxLayout()
        self.jobSpecsRightLayout = QVBoxLayout()
        self.jobReqsLayout = QHBoxLayout()
        self.jobDescLayout = QVBoxLayout()
        self.otherInfoLayout = QGridLayout()

        self.addDataToLayout()

        # Add sub layouts to main layouts
        self.jobInfoLeftLayout.addStretch()
        self.jobInfoRightLayout.addStretch()
        self.jobDataLeftLayout.addStretch()
        self.jobDataRightLayout.addStretch()
        self.jobSpecsLeftLayout.addStretch()
        self.jobSpecsRightLayout.addStretch()
        self.jobInfoLayout.addLayout(self.jobInfoLeftLayout)
        self.jobInfoLayout.addLayout(self.jobInfoRightLayout)
        self.jobDataLayout.addLayout(self.jobDataLeftLayout)
        self.jobDataLayout.addLayout(self.jobDataRightLayout)
        self.jobSpecsLayout.addLayout(self.jobSpecsLeftLayout)
        self.jobSpecsLayout.addLayout(self.jobSpecsRightLayout)

        # Set layouts to the group boxes
        jobInfoGroupBox.setLayout(self.jobInfoLayout)
        jobDataGroupBox.setLayout(self.jobDataLayout)
        jobSpecsGroupBox.setLayout(self.jobSpecsLayout)
        jobReqsGroupBox.setLayout(self.jobReqsLayout)
        jobDescGroupBox.setLayout(self.jobDescLayout)
        otherInfoGroupBox.setLayout(self.otherInfoLayout)

        # Add group box to the general layout
        generalLayout.addWidget(jobInfoGroupBox)
        generalLayout.addWidget(jobDataGroupBox)
        generalLayout.addWidget(jobSpecsGroupBox)
        generalLayout.addWidget(jobReqsGroupBox)
        generalLayout.addWidget(otherInfoGroupBox)

        # Add general layout and job description to main layout
        innerLayout.addLayout(generalLayout)
        innerLayout.addWidget(jobDescGroupBox)
        scrollArea.setWidget(containerWidget)
        mainLayout.addWidget(scrollArea)

        # Button on the left
        buttonLayout = QHBoxLayout()

        addButton = QPushButton("Add Information")
        addButton.setIcon(QIcon("icons/iconmonstr-plus-6.svg"))
        addButton.clicked.connect(self.onAddButtonClicked)

        editButton = QPushButton("Edit Information")
        editButton.setIcon(QIcon("icons/iconmonstr-pencil-line-lined.svg"))
        editButton.clicked.connect(self.onEditButtonClicked)

        clientCardButton = QPushButton("Open Client Card")
        clientCardButton.setIcon(QIcon("icons/iconmonstr-share-8.svg"))
        clientCardButton.clicked.connect(self.onClientCardButtonClicked)

        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(editButton)
        buttonLayout.addWidget(clientCardButton)
        buttonLayout.addStretch()

        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

    def fetchAndSetName(self):
        # Fetch company name from the database
        query = "SELECT job_title FROM job_orders WHERE id = %s"
        data = (self.job_id,)

        result = execute_query(query, data, fetch_mode="one")
        if result:
            self.name_label.setText(result[0])
        else:
            self.name_label.setText("Job Title Not Available")

    def addDataToLayout(self):
        # Styling fonts for labels
        titleFont = QFont("Arial", 10, QFont.Bold)
        dataFont = QFont("Arial", 10)

        # Fetching company data from the database
        query = "SELECT * FROM job_orders WHERE id = %s"
        data = (self.job_id,)
        result = execute_query(query, data, fetch_mode="one", get_column_names=True)

        if result and 'result' in result and 'column_names' in result:
            job_data = dict(zip(result['column_names'], result['result']))

            self.addData(self.jobInfoLeftLayout, "Job Title:", "job_title", None, job_data, titleFont, dataFont)
            self.addData(self.jobInfoRightLayout, "PO Order Number:", "po_order_number", None, job_data, titleFont,
                         dataFont)
            self.addData(self.jobInfoLeftLayout, "Position Type:", "position_type", None, job_data, titleFont, dataFont)
            self.addData(self.jobInfoLeftLayout, "Location:", "location", None, job_data, titleFont, dataFont)
            self.addData(self.jobInfoRightLayout, "Company:", "company", None, job_data, titleFont, dataFont)

            # Grab pay and bill rates
            bill_min = job_data.get("bill_rate_min", "")
            bill_max = job_data.get("bill_rate_max", "")
            bill_conversion = job_data.get("bill_rate_conversion", "")
            pay = job_data.get("pay_rate", "")
            pay_conversion = job_data.get("pay_rate_conversion", "")
            if f"{bill_min}{bill_max}" == "":
                bill_rate_data = {"bill_rate": "N/A"}
            else:
                bill_rate_data = {"bill_rate": f"{bill_min} - {bill_max} {bill_conversion}"}

            if pay == "":
                pay_rate_data = {"pay_rate": "N/A"}
            else:
                pay_rate_data = {"pay_rate": f"{pay} {pay_conversion}"}

            self.addData(self.jobDataLeftLayout, "Bill Rate:", "bill_rate", None, bill_rate_data, titleFont, dataFont)
            self.addData(self.jobDataLeftLayout, "Pay Rate:", "pay_rate", None, pay_rate_data, titleFont, dataFont)
            self.addData(self.jobDataRightLayout, "Start Date:", "start_date", None, job_data, titleFont, dataFont)
            self.addData(self.jobDataRightLayout, "End Date:", "end_date", None, job_data, titleFont, dataFont)

            self.addData(self.jobSpecsLeftLayout, "Needed Employees:", "needed_employees", None, job_data,
                         titleFont, dataFont)
            self.addData(self.jobSpecsLeftLayout, "Currently Active Employees:", "active_employees", None, job_data,
                         titleFont, dataFont)
            self.addData(self.jobSpecsRightLayout, "Minimum Experience:", "min_experience", None, job_data,
                         titleFont, dataFont)

            self.addData(self.jobReqsLayout, "Requirements:", "requirements", None, job_data, titleFont, dataFont)
            self.addData(self.jobReqsLayout, "Onsite Requirement:", "remote", None, job_data, titleFont, dataFont)

            # Job Description
            self.addJobDescription(self.jobDescLayout, "Job Description:", "job_description_path",
                                   job_data, titleFont, dataFont)

            self.addNotes(self.jobDescLayout, "Notes:", "notes_path", job_data, titleFont, dataFont)

            # User added data into Other Information
            defined_columns = self.get_defined_columns_for_table("job_orders")
            actual_columns = self.get_actual_columns_from_db("job_orders")
            self.add_missing_columns_to_ui(self.otherInfoLayout, self.job_id, defined_columns, actual_columns,
                                           titleFont, dataFont)

    def adjustSizeToScreen(self):
        screen = QApplication.primaryScreen().geometry()
        maxWidth = screen.width() * 0.9
        minWidth = 1200  # Set this based on your layout's needs to avoid horizontal scrolling

        # Ensuring dialog is wide enough or adjusted to screen width
        finalWidth = max(minWidth, maxWidth)  # Use the larger of minWidth or 90% of screen width
        finalHeight = self.height()

        self.resize(finalWidth, finalHeight)
        self.setMinimumWidth(minWidth)  # Ensure dialog does not go below content's required width
        self.setMaximumSize(screen.width(), screen.height())

    def addData(self, layout, label, key1, key2, data, titleFont, dataFont):
        """Adds a data field to the box layout"""
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

        # Create a horizontal field
        hLayout = QHBoxLayout()
        hLayout.addWidget(labelWidget)
        hLayout.addWidget(valueWidget)

        layout.addLayout(hLayout)

        # Add to ui_fields for future reference
        self.ui_fields.append({
            "label_text": label,
            "label_widget": labelWidget,
            "db_key": (key1, key2),
            "value_widget": valueWidget,
        })

    @staticmethod
    def get_defined_columns_for_table(table_name):
        # Load the JSON schema for the table
        table_schemas = load_json_file(Path('tools/table_schemas.json'))
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

    def add_missing_columns_to_ui(self, gridLayout, job_id, defined_columns, actual_columns, titleFont, dataFont):
        # Find the difference between the actual columns and the defined columns
        self.extra_columns = set(actual_columns) - set(defined_columns)
        column_index = 0  # Initialize column index to manage layout positioning

        for column in self.extra_columns:
            # Fetch the data for the extra column for the given job order
            query = f"SELECT {column} FROM job_orders WHERE id = %s"
            result = execute_query(query, (job_id,), fetch_mode="one")
            if result:
                # Calculate grid position
                row = column_index // 2  # Integer division to calculate the row
                col = column_index % 2  # Modulo to alternate between columns 0 and 1

                # Create label and value widgets
                labelWidget = QLabel(column.replace('_', ' ').title() + ":")
                labelWidget.setFont(titleFont)
                value = result[0] if result[0] is not None else "N/A"
                valueWidget = QLabel(f'<span style="color: grey;">{value}</span>')
                valueWidget.setFont(dataFont)

                # Add widgets to the grid layout at calculated positions
                gridLayout.addWidget(labelWidget, row, col * 2)  # Multiply col by 2 for label
                gridLayout.addWidget(valueWidget, row, col * 2 + 1)  # Next column for value

                column_index += 1  # Increment column index for next iteration

                # Add to ui_fields for future reference
                self.ui_fields.append({
                    "label_text": column.replace('_', ' ').title() + ":",
                    "label_widget": labelWidget,
                    "db_key": (column,),
                    "value_widget": valueWidget,
                })

    def addJobDescription(self, layout, label, key, data, titleFont, dataFont):
        labelWidget = QLabel(label)
        labelWidget.setFont(titleFont)
        jobDescriptionEdit = QTextEdit()
        jobDescriptionEdit.setReadOnly(True)

        try:
            jobDescriptionEdit.setText(read_text_file(data.get(key)))
        except FileNotFoundError:
            jobDescriptionEdit.setText("Job description file not found.")
        except Exception as e:
            jobDescriptionEdit.setText(f"Could not load the job description due to the following error: \n{e}.")

        jobDescriptionEdit.setFont(dataFont)
        jobDescriptionEdit.setStyleSheet("color: gray;")
        layout.addWidget(labelWidget)
        layout.addWidget(jobDescriptionEdit)

        # Add to ui_fields for future reference
        self.ui_fields.append({
            "label_text": label,
            "label_widget": labelWidget,
            "db_key": (key,),
            "value_widget": jobDescriptionEdit,
        })

    def addNotes(self, layout, label, key, data, titleFont, dataFont):
        labelWidget = QLabel(label)
        labelWidget.setFont(titleFont)
        notesListWidget = QListWidget()

        try:
            with open(data.get(key), 'r') as file:
                notes_content = file.readlines()
                current_title = ""
                current_note = ""
                for line in notes_content:
                    if line.startswith("Title: "):
                        # If there's a current note being processed, add it before starting a new one
                        if current_title:
                            item = QListWidgetItem(f"{current_title}: {current_note[:10]}...")
                            item.setForeground(QColor('gray'))  # Set the text color to gray
                            notesListWidget.addItem(item)
                            current_note = ""  # Reset current note for the next one
                        current_title = line[len("Title: "):].strip()  # Remove the "Title: " part
                    elif line.startswith("Note: "):
                        current_note += line[len("Note: "):]  # Append text after "Note: "
                    elif line.strip() == "" and current_title:  # End of a note section
                        # Add the note to the list and reset for the next note
                        item = QListWidgetItem(f"{current_title}: {current_note[:10]}...")
                        item.setForeground(QColor('gray'))  # Set the text color to gray
                        notesListWidget.addItem(item)
                        current_title = ""
                        current_note = ""
                # Add the last note if the file doesn't end with an empty line
                if current_title:
                    item = QListWidgetItem(f"{current_title}: {current_note[:10]}...")
                    item.setForeground(QColor('gray'))  # Set the text color to gray
                    notesListWidget.addItem(item)
        except FileNotFoundError:
            item = QListWidgetItem("Notes file not found.")
            item.setForeground(QColor('gray'))  # Set the text color to gray
            notesListWidget.addItem(item)
        except Exception as e:
            item = QListWidgetItem(f"Could not load the notes due to the following error: \n{e}.")
            item.setForeground(QColor('gray'))  # Set the text color to gray
            notesListWidget.addItem(item)

        notesListWidget.setFont(dataFont)
        layout.addWidget(labelWidget)
        layout.addWidget(notesListWidget)

        # Add to ui_fields for future reference
        self.ui_fields.append({
            "label_text": label,
            "label_widget": labelWidget,
            "db_key": (key,),
            "value_widget": notesListWidget,
        })

    def onAddButtonClicked(self):
        dialog = AddFieldDialog(self.job_id, "job_orders", self.added_fields, self)
        dialog.dataUpdated.connect(self.refreshCompanyData)
        dialog.exec_()

    def refreshCompanyData(self):
        # Clear existing dynamic UI elements
        for ui_field in self.ui_fields:
            if 'label_widget' in ui_field:  # Check if the label widget exists and delete it
                ui_field['label_widget'].deleteLater()
            ui_field['value_widget'].deleteLater()
        self.ui_fields.clear()  # Clear the list after removing widgets
        self.addDataToLayout()
        self.added_fields = {}
        self.adjustSizeToScreen()

    def onEditButtonClicked(self):
        dialog = EditCompanyDialog(self.job_id, "job_orders", self.ui_fields, self)
        dialog.dataUpdated.connect(self.refreshCompanyData)
        dialog.exec_()

    def onClientCardButtonClicked(self):
        self.clientCardRequested.emit(self.job_id)

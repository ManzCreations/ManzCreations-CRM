from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import *

from resources.tools import resource_path, execute_query
from .tabs import GeneralDataTab, CompanyDataTab, JobOrderDataTab, OldJobOrdersTab

application_path = str(resource_path(Path.cwd()))


class EmployeeCard(QDialog):
    def __init__(self, database_id=None, employer_id=None, job_order_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Employee Details")
        self.setWindowIcon(QIcon(str(Path(application_path, 'resources', 'icons', 'crm-icon-high-seas.png'))))
        self.resize(800, 800)  # Set the size of the dialog

        self.database_id = database_id
        self.employer_id = employer_id
        self.job_order_id = job_order_id
        self.initUI()

        # Force the QDialog to never be larger than the screen resolution
        self.adjustSizeToScreen()

    def initUI(self):
        main_layout = QVBoxLayout()  # Change to QVBoxLayout for vertical stacking

        # Top bar with person icon and name aligned to the right
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()  # Add stretch to push content to the right

        # Name label
        self.name_label = QLabel()
        self.fetchAndSetName()
        self.name_label.setFont(QFont("Arial", 16))
        self.name_label.setStyleSheet("color: #64bfd1; font-weight: bold;")
        top_bar_layout.addWidget(self.name_label)

        # Person icon label
        person_icon_label = QLabel()
        icon_pixmap = QPixmap(str(Path(application_path, 'resources', 'icons', 'iconmonstr-construction-3-white.svg')))
        scaled_pixmap = icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio)  # Scale the pixmap
        person_icon_label.setPixmap(scaled_pixmap)
        top_bar_layout.addWidget(person_icon_label)

        main_layout.addLayout(top_bar_layout)

        # Tab layout with icons
        tab_layout = QHBoxLayout()
        left_tab_widget = QTabWidget()
        left_tab_widget.setTabPosition(QTabWidget.North)

        # Home Tab
        general_tab = GeneralDataTab(self.database_id)

        # Edit Tab
        company_tab = CompanyDataTab(self.employer_id, self.job_order_id)

        # Job Order Tab
        job_order_tab = JobOrderDataTab(self.database_id, self.job_order_id)
        job_order_tab.refreshPages.connect(self.handleDataUpdated)

        # Old Job Orders Tab
        old_job_orders_tab = OldJobOrdersTab(self.database_id)

        # Post-processing
        icons = [
            QIcon(str(Path(application_path, 'resources', 'icons', 'iconmonstr-info-10.svg'))),
            QIcon(str(Path(application_path, 'resources', 'icons', 'iconmonstr-building-20.svg'))),
            QIcon(str(Path(application_path, 'resources', 'icons', 'iconmonstr-briefcase-5.svg'))),
            QIcon(str(Path(application_path, 'resources', 'icons', 'iconmonstr-inbox-22.svg')))
        ]
        tab_titles = ["Employee", "Company", "Current Job Order", "Old Job Orders"]
        tabs = [general_tab, company_tab, job_order_tab, old_job_orders_tab]

        for title, tab, icon in zip(tab_titles, tabs, icons):
            wrapped_title = self.wrap_text(title, max_length=10)
            left_tab_widget.addTab(tab, icon, title)

        tab_layout.addWidget(left_tab_widget)
        tab_layout.addStretch()  # Add stretch to the right of the tabs
        main_layout.addLayout(tab_layout)  # Add the tab layout to the main layout

        self.setLayout(main_layout)

    def handleDataUpdated(self):
        # Logic that decides when to close and reinitialize
        self.close()  # Close the dialog

    @staticmethod
    def wrap_text(text, max_length=10):
        """Wrap text if it exceeds max_length."""
        if len(text) > max_length:
            return '\n'.join(text[i:i + max_length] for i in range(0, len(text), max_length))
        return text

    def fetchAndSetName(self):
        # SQL query to get first_name and last_name based on database_id
        query = "SELECT first_name, last_name FROM employees WHERE id = %s"
        data = (self.database_id,)

        # Assuming execute_query is a function that executes the query and returns the result
        result = execute_query(query, data, fetch_mode="one")

        # Check if result is not None and has required data
        if result and result[0] and result[1]:
            first_name, last_name = result
            full_name = f"{first_name} {last_name}"
            self.name_label.setText(full_name)
        else:
            self.name_label.setText("Name not available")

    def adjustSizeToScreen(self):
        # Assume a base width and calculate additional width as needed
        baseWidth = 800
        calculatedWidth = baseWidth  # In a real scenario, calculate this based on the content

        # Get the screen's resolution
        screen = QApplication.primaryScreen().geometry()

        # Calculate the maximum width considering some margins
        maxWidth = screen.width() * 0.9  # 90% of screen width

        # Choose the smaller of calculated width or max screen width
        finalWidth = min(calculatedWidth, maxWidth)
        finalHeight = self.height()  # Keep the current height or adjust as necessary

        self.resize(finalWidth, finalHeight)

        # Ensure the dialog doesn't exceed screen size
        self.setMaximumSize(screen.width(), screen.height())

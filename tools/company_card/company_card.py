from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QApplication, QVBoxLayout

from tools.company_card.tabs import CompanyInformationTab, CurrentJobOrdersTab, OldCompanyJobOrdersTab
from tools.helpful_functions import *
from tools.mydb import *


class ClientCard(QDialog):
    def __init__(self, company_id=None, jobIds=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Details")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.resize(1000, 800)  # Set the size of the dialog

        self.company_id = company_id
        self.job_ids = jobIds
        self.initUI()

        # Adjust the size to screen resolution
        self.adjustSizeToScreen()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Top bar setup
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()

        # Company name label
        self.name_label = QLabel()
        self.fetchAndSetName()
        self.name_label.setFont(QFont("Arial", 16))
        self.name_label.setStyleSheet("color: #64bfd1; font-weight: bold;")
        top_bar_layout.addWidget(self.name_label)

        # Company icon label
        icon_label = QLabel()
        icon_pixmap = QPixmap("icons/iconmonstr-building-20-white.svg")  # Placeholder icon
        scaled_pixmap = icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio)
        icon_label.setPixmap(scaled_pixmap)
        top_bar_layout.addWidget(icon_label)

        main_layout.addLayout(top_bar_layout)

        # Tab layout
        tab_layout = QHBoxLayout()
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.North)

        # Tabs
        company_info_tab = CompanyInformationTab(self.company_id)
        current_job_orders_tab = CurrentJobOrdersTab(self.company_id)
        old_job_orders_tab = OldCompanyJobOrdersTab(self.company_id)

        # Icons for tabs
        icons = [
            QIcon("icons/iconmonstr-info-10.svg"),
            QIcon("icons/iconmonstr-briefcase-5.svg"),
            QIcon("icons/iconmonstr-inbox-22.svg")
        ]
        tab_titles = ["Company Information", "Current Job Orders", "Old Job Orders"]
        tabs = [company_info_tab, current_job_orders_tab, old_job_orders_tab]

        for title, tab, icon in zip(tab_titles, tabs, icons):
            tab_widget.addTab(tab, icon, title)

        tab_layout.addWidget(tab_widget)
        main_layout.addLayout(tab_layout)

        self.setLayout(main_layout)

    def fetchAndSetName(self):
        # Fetch company name from the database
        query = "SELECT employer_company FROM clients WHERE id = %s"
        data = (self.company_id,)

        result = execute_query(query, data, fetch_mode="one")
        if result:
            self.name_label.setText(result[0])
        else:
            self.name_label.setText("Company Name Not Available")

    def adjustSizeToScreen(self):
        screen = QApplication.primaryScreen().geometry()
        maxWidth = screen.width() * 0.9
        finalWidth = min(800, maxWidth)
        finalHeight = self.height()
        self.resize(finalWidth, finalHeight)
        self.setMaximumSize(screen.width(), screen.height())

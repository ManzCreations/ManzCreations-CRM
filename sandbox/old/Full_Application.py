import random
import numpy as np
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QComboBox, QLabel, QPushButton, QListWidget,
    QTableWidget, QTableWidgetItem, QListWidgetItem
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator


class ExampleData:
    @staticmethod
    def generate_sales_activity_data():
        # Generate example sales activity data
        companies = ['Company A', 'Company B', 'Company C', 'Company D', 'Company E']
        data = {company: random.randint(1, 10) for company in companies}
        return data

    @staticmethod
    def generate_business_data():
        # Generate example business data
        data = [
            {'Category': 'Category 1', 'Existing': random.randint(10, 30), 'New': random.randint(5, 15)},
            {'Category': 'Category 2', 'Existing': random.randint(10, 30), 'New': random.randint(5, 15)},
            {'Category': 'Category 3', 'Existing': random.randint(10, 30), 'New': random.randint(5, 15)}
        ]
        return data

    @staticmethod
    def generate_leads_data():
        # Generate example leads data with sources and created months
        sources = ['Source A', 'Source B', 'Source C']
        leads = [{'Source': random.choice(sources), 'Created Month': random.choice(['Jan', 'Feb', 'Mar', 'Apr'])} for _ in range(20)]
        return leads

    @staticmethod
    def generate_today_tasks():
        # Generate example tasks due today
        tasks = [
            {'task': 'Task 1', 'due_date': '2023-10-30'},
            {'task': 'Task 2', 'due_date': '2023-10-30'},
            {'task': 'Task 3', 'due_date': '2023-10-30'},
        ]
        return tasks

    @staticmethod
    def generate_opportunities_data():
        # Generate example opportunities data
        opportunities = [
            {'opportunity': 'Opportunity 1', 'my_opportunity': True},
            {'opportunity': 'Opportunity 2', 'my_opportunity': False},
            {'opportunity': 'Opportunity 3', 'my_opportunity': True},
        ]
        return opportunities

    @staticmethod
    def generate_leads_table_data():
        # Generate example leads data for a table
        leads = [
            {'name': 'John Doe', 'my_lead': True},
            {'name': 'Jane Smith', 'my_lead': False},
            {'name': 'Bob Johnson', 'my_lead': True},
        ]
        return leads

class BarChartWidget(FigureCanvas):
    def __init__(self, data, title, xlabel, ylabel, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)

        self.ax = self.figure.add_subplot(111)

        if "Sales" in title:
            x_data = list(data.values())
            y_data = list(data.keys())
            self.ax.barh(y_data, x_data)
        elif "Business" in title:
            categories = [item['Category'] for item in data]
            existing_values = [item['Existing'] for item in data]
            new_values = [item['New'] for item in data]

            x = np.arange(len(categories))
            width = 0.35

            self.ax.bar(x - width / 2, existing_values, width, label='Existing')
            self.ax.bar(x + width / 2, new_values, width, label='New')
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(categories)
            self.ax.legend()
        elif "Leads" in title:
            data_list = [item['Source'] for item in data]
            x_data = sorted(set(data_list))
            counts = {item: data_list.count(item) for item in set(data_list)}
            sorted_counts = {key: counts[key] for key in sorted(counts.keys())}
            y_data = list(sorted_counts.values())
            self.ax.barh(x_data, y_data)
        else:
            return

        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.draw()


class CRMApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('CRM Application')
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout()
        central_widget.setLayout(layout)

        # Creating example data
        sales_data = ExampleData.generate_sales_activity_data()
        business_data = ExampleData.generate_business_data()
        leads_data = ExampleData.generate_leads_data()
        today_tasks = ExampleData.generate_today_tasks()
        opportunities = ExampleData.generate_opportunities_data()
        leads_table_data = ExampleData.generate_leads_table_data()

        # Adding widgets to the layout
        layout.addWidget(BarChartWidget(sales_data, "Sales Activity", "Record Count", "Company/Account"), 0, 0)
        layout.addWidget(BarChartWidget(business_data, "Business", "Amount", "Category"), 0, 1)
        layout.addWidget(BarChartWidget(leads_data, "Leads by Source and Created Month", "Lead Source > Created Month",
                                        "Record Count"), 0, 2)

        today_tasks_layout = QVBoxLayout()
        today_tasks_label = QLabel("Today's Tasks")
        today_tasks_layout.addWidget(today_tasks_label)
        task_filter = QComboBox()
        task_filter.addItems(['All', 'Due Today', 'Completed'])
        today_tasks_layout.addWidget(task_filter)

        task_list = QListWidget()
        for task in today_tasks:
            task_item = QListWidgetItem(f"{task['task']} - Due: {task['due_date']}")
            task_item.setFlags(task_item.flags() | 2)  # Add checkable flag
            task_item.setCheckState(0)  # Unchecked by default
            task_list.addItem(task_item)
        today_tasks_layout.addWidget(task_list)
        view_all_button = QPushButton("View All")
        today_tasks_layout.addWidget(view_all_button)
        layout.addLayout(today_tasks_layout, 1, 0)

        opportunities_layout = QVBoxLayout()
        opportunities_label = QLabel("My Opportunities")
        opportunities_layout.addWidget(opportunities_label)

        opportunities_table = QTableWidget()
        opportunities_table.setColumnCount(2)
        opportunities_table.setHorizontalHeaderLabels(['Opportunity', 'My Opportunity'])
        opportunities_table.setRowCount(len(opportunities))

        for i, opp in enumerate(opportunities):
            opportunities_table.setItem(i, 0, QTableWidgetItem(opp['opportunity']))
            opportunities_table.setItem(i, 1, QTableWidgetItem("Yes" if opp['my_opportunity'] else "No"))

        view_opportunities_button = QPushButton("View All")
        opportunities_layout.addWidget(opportunities_table)
        opportunities_layout.addWidget(view_opportunities_button)
        layout.addLayout(opportunities_layout, 1, 1)

        leads_layout = QVBoxLayout()
        leads_label = QLabel("My Leads")
        leads_layout.addWidget(leads_label)

        leads_table = QTableWidget()
        leads_table.setColumnCount(2)
        leads_table.setHorizontalHeaderLabels(['Name', 'My Lead'])
        leads_table.setRowCount(len(leads_table_data))

        for i, lead in enumerate(leads_table_data):
            leads_table.setItem(i, 0, QTableWidgetItem(lead['name']))
            leads_table.setItem(i, 1, QTableWidgetItem("Yes" if lead['my_lead'] else "No"))

        view_leads_button = QPushButton("View All")
        leads_layout.addWidget(leads_table)
        leads_layout.addWidget(view_leads_button)
        layout.addLayout(leads_layout, 1, 2)

        self.show()


def main():
    app = QApplication(sys.argv)
    crm_app = CRMApplication()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

import sys
from io import BytesIO

import cairosvg
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def invert_image(image_path, output_path):
    # Check if the image is in SVG format
    is_svg = image_path.lower().endswith(".svg")

    # Load the image using cairosvg and convert it to a QImage
    if is_svg:
        with open(image_path, "rb") as svg_file:
            svg_data = svg_file.read()
        png_data = cairosvg.svg2png(bytestring=svg_data)
        png_image = BytesIO(png_data)
        image = plt.imread(png_image)
    else:
        # Load a standard image format (e.g., PNG)
        image = plt.imread(image_path)

    # Create a mask for pixels with gradient (not completely black)
    gradient_mask = np.any(image[:, :, :3] < 0.99, axis=-1)  # Adjust the threshold as needed

    # Set the background color to #333333
    image[~gradient_mask, :3] = [51 / 255, 51 / 255, 51 / 255]  # RGB values for #333333

    # Set the image color to white
    image[gradient_mask, :3] = [1, 1, 1]

    # Save the modified image
    plt.imsave(output_path, image)


class HomeTab(QWidget):
    def __init__(self, employee_data):
        super().__init__()
        self.employee_data = employee_data
        self.initUI()

    def initUI(self):
        home_layout = QGridLayout(self)
        for row, (key, value) in enumerate(self.employee_data.items()):
            key_label = QLabel(f"{key.capitalize()}:")
            value_label = QLabel(str(value))
            home_layout.addWidget(key_label, row, 0)
            home_layout.addWidget(value_label, row, 1)


class EditTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Customize the content of the Edit Tab as needed
        pass


class JobOrderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Customize the content of the Job Order Tab as needed
        pass


class EmployeeCard(QDialog):
    def __init__(self, employee_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Employee Details")
        self.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
        self.setFixedSize(600, 400)  # Set the size of the dialog

        self.employee_data = employee_data
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()  # Change to QVBoxLayout for vertical stacking

        # Top bar with person icon and name
        top_bar_layout = QHBoxLayout()
        person_icon_label = QLabel()
        icon_pixmap = QPixmap("icons/iconmonstr-construction.svg")
        person_icon_label.setPixmap(icon_pixmap)
        top_bar_layout.addWidget(person_icon_label)
        name_label = QLabel(f"{self.employee_data['first_name']} {self.employee_data['last_name']}")
        name_label.setFont(QFont("Arial", 16))
        top_bar_layout.addWidget(name_label)
        top_bar_layout.addStretch()  # Add stretch to push content to the left
        main_layout.addLayout(top_bar_layout)

        # Tab layout with icons
        tab_layout = QHBoxLayout()
        left_tab_widget = QTabWidget()
        left_tab_widget.setTabPosition(QTabWidget.West)

        # Home Tab
        home_tab = HomeTab(self.employee_data)
        left_tab_widget.addTab(home_tab, QIcon(), "")

        # Edit Tab
        edit_tab = EditTab()
        left_tab_widget.addTab(edit_tab, QIcon(), "")

        # Job Order Tab
        job_order_tab = JobOrderTab()
        left_tab_widget.addTab(job_order_tab, QIcon(), "")

        # Adding tabs with icons
        icon1 = QIcon("icons/iconmonstr-building-10.svg")
        icon2 = QIcon("icons/iconmonstr-pencil-line-lined.svg")
        icon3 = QIcon("icons/iconmonstr-briefcase-5.svg")

        rotated_icon1 = icon1.pixmap(24, 24).transformed(QTransform().rotate(90))  # Rotate 90 degrees
        rotated_icon2 = icon2.pixmap(24, 24).transformed(QTransform().rotate(90))  # Rotate 90 degrees
        rotated_icon3 = icon3.pixmap(24, 24).transformed(QTransform().rotate(90))  # Rotate 90 degrees

        left_tab_widget.setTabIcon(0, QIcon(rotated_icon1))  # Set the icon for the first tab
        left_tab_widget.setTabIcon(1, QIcon(rotated_icon2))
        left_tab_widget.setTabIcon(2, QIcon(rotated_icon3))

        tab_layout.addWidget(left_tab_widget)
        tab_layout.addStretch()  # Add stretch to the right of the tabs
        main_layout.addLayout(tab_layout)  # Add the tab layout to the main layout

        self.setLayout(main_layout)


# Example usage
employee_data = {
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'john.doe@example.com',
    'phone': '123-456-7890',
    'address': '123 Main Street',
    'city': 'Anytown',
    'state': 'Anystate',
    'zipcode': '12345',
    'current_job_id': '1001',
    'employee_type': 'Full-Time',
    'hired_date': '2024-01-01'
}


def load_stylesheet(file_path: str) -> str:
    """
    Load the stylesheet from a given file path.

    :param file_path: Path to the stylesheet file.
    :return: The stylesheet content as a string.
    """
    try:
        with open(file_path, "r") as file:
            return file.read()
    except IOError:
        print(f"Error opening stylesheet file: {file_path}")
        return ""


app = QApplication(sys.argv)
app.setFont(QFont("Arial", 10))
stylesheet = load_stylesheet("style_properties/stylesheet.qss")
app.setStyleSheet(stylesheet)
dialog = EmployeeCard(employee_data)
dialog.show()
sys.exit(app.exec_())

# ManzCreations CRM

ManzCreations CRM is a Customer Relationship Management application that helps businesses manage client information, employee details, and job orders efficiently. Built with Python and PyQt5, it features a user-friendly interface and utilizes Pandas for data manipulation and MySQL for data storage, making it a powerful tool for enhancing customer service and business operations.

## Getting Started

### Prerequisites

- Python 3.8 or later
- MySQL Server

### Setting Up MySQL

1. Install MySQL Server on your system.
2. Create a database for ManzCreations CRM:
   CREATE DATABASE manzCreations_crm;
3. Import the ManzCreations CRM database schema (provided separately).

### Setting Up Python

1. Ensure Python is installed on your system.
2. Clone the repository or download the project to your local machine.
3. Navigate to the project directory.
4. Install required Python packages using the `requirements.txt` file:
pip install -r requirements.txt


### Creating an Executable from the Python Application

To create an executable version of ManzCreations CRM, you can use PyInstaller:

1. Install PyInstaller:
pip install pyinstaller

2. Navigate to the project directory and run:
pyinstaller --onefile --windowed manzCreations_crm.py

3. The executable will be located in the `dist` directory.

## Running ManzCreations CRM

To run ManzCreations CRM, execute the Python script or the generated executable:
python manzCreations_crm.py

or if using the executable:
./dist/manzCreations_crm

## Contributing

Contributions to ManzCreations CRM are welcome! Please refer to CONTRIBUTING.md for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.

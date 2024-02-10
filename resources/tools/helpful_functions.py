import os
import subprocess
import tempfile
from typing import Dict, List

import docx
import fitz  # PyMuPDF
from PyQt5.QtWidgets import QMessageBox

from resources.tools.mydb import *


def show_error_message(message: str) -> None:
    """
    Show an error message to the user.

    :param message: The error message to display.
    """
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Warning)
    msgBox.setText(message)
    msgBox.setWindowTitle("Error")
    msgBox.setWindowIcon(QIcon("icons/crm-icon-high-seas.png"))
    msgBox.setStandardButtons(QMessageBox.Ok)
    msgBox.exec_()


def addToDatabase(data: Dict[str, str], headers: List[str], table_name: str, update_criteria: str = "add",
                  entry_id: int = None) -> None:
    """
    Dynamically adds a new employee's data to the database based on the provided headers.

    This function constructs an SQL INSERT command dynamically using the provided headers list for column names
    and the `employee_data` dictionary for the corresponding values. It is designed to handle exceptions during
    database operations and ensures the database connection is properly managed.

    Args:
        data (Dict[str, str]): A dictionary containing the data for the new employee,
            where keys correspond to the column names.
        headers (List[str]): A list of strings representing the column names in the database table.
        table_name (str): The name of the table to insert the data into.
        update_criteria (str): The criteria that the code uses to either update the existing database or add the entry
            into the existing database. (add --Create a new entry. update --Update an existing entry)
        entry_id (int): The id relating to the index of the entry specifically for updating the entry.

    Note:
        The `data` dictionary must contain all the keys specified in `headers`. Missing keys will
        lead to a KeyError. Ensure the dictionary is complete before calling this function.
    """
    try:
        if update_criteria == "add":
            columns = ', '.join(headers)
            placeholders = ', '.join(['%s' for _ in headers])
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            values = tuple(data[header] for header in headers)
            execute_query(sql, values)
        elif update_criteria == "update":
            # Constructing the SQL UPDATE statement dynamically based on the employee_data keys
            update_parts = [f"{key} = %s" for key in data]
            sql_update_query = f"UPDATE employees SET {', '.join(update_parts)} WHERE id = %s"

            # Preparing the data tuple including all data values followed by the employee_id
            data_tuple = tuple(data.values()) + (entry_id,)

            execute_query(sql_update_query, data_tuple)
    except KeyError as e:
        print(f"Connection to Database terminated due to: {e}")


def archive_and_delete_employee_job_order(employee_id, job_order_id):
    # Archive job order and employee details
    job_order_query = ("SELECT po_order_number, location, company, job_title, position_type, remote "
                       "FROM job_orders WHERE id = %s")
    job_order_data = execute_query(job_order_query, (job_order_id,), fetch_mode="one")

    employee_query = "SELECT first_name, last_name, hired_date, pay, pay_conversion FROM employees WHERE id = %s"
    employee_data = execute_query(employee_query, (employee_id,), fetch_mode="one")

    combined_data = employee_data + job_order_data
    insert_old_data_query = """
        INSERT INTO old_employee_job_orders (first_name, last_name, hired_date, pay, pay_conversion,
                                             po_order_number, location, company, job_title, position_type, remote)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(insert_old_data_query, combined_data)

    # Delete the row from job2employer_ids
    delete_query = "DELETE FROM job2employer_ids WHERE employee_id = %s AND job_order_id = %s"
    execute_query(delete_query, (employee_id, job_order_id))


def archive_and_delete_company_job_order(client_id, job_order_id):
    # Fetch job order details
    job_order_query = ("SELECT location, po_order_number, start_date, end_date, needed_employees, job_title, "
                       "position_type, bill_rate_min, bill_rate_max, bill_rate_conversion, pay_rate, "
                       "pay_rate_conversion, min_experience, requirements, remote, job_description_path, notes_path "
                       "FROM job_orders WHERE id = %s")
    job_order_data = execute_query(job_order_query, (job_order_id,), fetch_mode="one")

    # Fetch client details
    client_query = "SELECT employer_company, contact_person FROM clients WHERE id = %s"
    client_data = execute_query(client_query, (client_id,), fetch_mode="one")

    # Combine the data from both queries
    combined_data = client_data + job_order_data

    # Insert archived job order data into old_company_job_orders
    insert_old_company_job_orders_query = """
        INSERT INTO old_company_job_orders (employer_company, contact_person, location, po_order_number, start_date, 
        end_date, needed_employees, job_title, position_type, bill_rate_min, bill_rate_max, bill_rate_conversion, 
        pay_rate, pay_rate_conversion, min_experience, requirements, remote, job_description_path, notes_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(insert_old_company_job_orders_query, combined_data)

    # Optionally, if there's a relationship to be removed from job2employer_ids or similar, delete that too
    delete_relationship_query = "DELETE FROM job2employer_ids WHERE job_order_id = %s AND client_id = %s"
    execute_query(delete_relationship_query, (job_order_id, client_id))

    # Delete the job order from job_orders
    delete_job_order_query = "DELETE FROM job_orders WHERE id = %s"
    execute_query(delete_job_order_query, (job_order_id,))


def retrieve_current_job_order(employee_id):
    job2employer_query = "SELECT job_order_id, client_id FROM job2employer_ids WHERE employee_id = %s"
    job2employer_data = execute_query(job2employer_query, (employee_id,), fetch_mode="one")
    if not job2employer_data:
        print("No job order found for this employee.")
        return None, None
    return job2employer_data


def retrieve_current_company(job_order_id):
    company_name_query = "SELECT company FROM job_orders WHERE id = %s"
    company_name = execute_query(company_name_query, (job_order_id,), fetch_mode="one")
    job2employer_query = "SELECT id FROM clients WHERE employer_company = %s"
    company_name = company_name[0] if isinstance(company_name, tuple) else company_name
    job2employer_data = execute_query(job2employer_query, (company_name,), fetch_mode="one")
    if not job2employer_data:
        print("No client found for this job order.")
        return None
    return job2employer_data[0] if isinstance(job2employer_data, tuple) else job2employer_data


def change_active_needed_employees(employer_id, job_order_id, subtract_needed_employees=True):
    # Fetch the current values of needed_employees and active_employees
    query = "SELECT needed_employees, active_employees FROM job_orders WHERE id = %s"
    result = execute_query(query, (job_order_id,), fetch_mode='one')
    if result:
        needed_employees, active_employees = result

        # Prepare new values based on the operation
        new_needed_employees = needed_employees - 1 if subtract_needed_employees else needed_employees + 1
        new_active_employees = active_employees + 1 if subtract_needed_employees else active_employees - 1

        # Check if the operation leads to negative numbers
        if new_needed_employees < 0 or new_active_employees < 0:
            reply = QMessageBox.question(None, "Confirm Operation",
                                         "This operation will result in negative numbers for employees. "
                                         "Are you sure you want to proceed?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.No:
                return  # User chose not to proceed

        # Update job_orders table with new values
        update_query = """
            UPDATE job_orders 
            SET needed_employees = %s, active_employees = %s 
            WHERE id = %s
            """
        execute_query(update_query, (new_needed_employees, new_active_employees, job_order_id))

        # Update clients table
        query = "SELECT active_employees FROM clients WHERE id = %s"
        result = execute_query(query, (employer_id,), fetch_mode='one')
    if result:
        active_employees = result[0]
        new_active_employees = active_employees + 1 if subtract_needed_employees else active_employees - 1

        update_query = """
                    UPDATE clients 
                    SET active_employees = %s 
                    WHERE id = %s
                    """
        execute_query(update_query, (new_active_employees, employer_id))


def convert_doc_to_docx(doc_path):
    """Converts a .doc file to .docx using LibreOffice."""
    tmp_dir = tempfile.mkdtemp()
    subprocess.run(['libreoffice', '--convert-to', 'docx', '--outdir', tmp_dir, doc_path], stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    base_name = os.path.splitext(os.path.basename(doc_path))[0]
    return os.path.join(tmp_dir, f"{base_name}.docx")


def read_docx_file(file_path):
    """Reads a .docx file and returns its text content."""
    doc = docx.Document(file_path)
    return '\n'.join([para.text for para in doc.paragraphs])


def read_pdf_file(file_path):
    """Reads a .pdf file and returns its text content."""
    with fitz.open(file_path) as doc:
        text = "".join(page.get_text() for page in doc)
    return text


def read_text_file(file_path):
    """Reads text from a file based on its extension. Supports .txt, .docx, .doc, and .pdf."""
    if file_path in [None, 'N/A', 'NULL', 'None', '']:
        return "File not found."
    extension = os.path.splitext(file_path)[-1].lower()
    try:
        if extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        elif extension == '.docx':
            return read_docx_file(file_path)
        elif extension == '.doc':
            converted_path = convert_doc_to_docx(file_path)
            text = read_docx_file(converted_path)
            os.remove(converted_path)  # Clean up the temporary .docx file
            return text
        elif extension == '.pdf':
            return read_pdf_file(file_path)
        else:
            return "Unsupported file format."
    except Exception as e:
        return f"An error occurred: {e}"

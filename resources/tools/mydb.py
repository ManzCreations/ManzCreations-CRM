import json
import sys
import os
from pathlib import Path
from typing import Tuple, Any, Optional, Dict, Union

import mysql.connector
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from mysql.connector import Error, MySQLConnection


def get_application_path():
    # Determine if the application is a frozen executable or a script
    if getattr(sys, 'frozen', False):
        exe_path = Path(sys.executable).parent
    else:
        # If running as a script, go up two levels from the script's location to reach the project root
        return Path(os.path.dirname(os.path.abspath(__file__))).parent.parent

    # Construct the path to the JSON file based on the exe location
    json_path = exe_path / 'path_to_some_persistent_storage.json'

    # Attempt to read the JSON file
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)
            # Assuming 'start_paths' is a list and you're interested in the first item
            start_path = Path(data['start_paths'][0])
            # Use the parent of the start_path as the application path
            return start_path.parent
    except Exception as e:
        print(f"Error reading or processing the JSON file: {e}")
        # Fallback to the exe_path if there's an issue
        return exe_path


# Determine if the application is a frozen executable or a script
application_path = get_application_path()

CONFIG_PATH = Path(Path(application_path, 'resources', 'tools', 'db_config.json'))
TABLE_QUERIES_PATH = Path(Path(application_path, 'resources', 'tools', 'table_schemas.json'))


def load_json_file(file_path: Path = CONFIG_PATH, file_type: str = "JSON file", skip_error_dlg: bool = False) \
        -> Optional[Dict]:
    """
    Loads content from a specified JSON file.

    Args:
        file_path (Path): The file path to the JSON file.
        file_type (str): A string representing the type of file being loaded. Defaults to "JSON file".
        skip_error_dlg (bool): A boolean operator that tells the script to open a dialog showing the error or not.

    Returns:
        Optional[Dict]: A dictionary containing the loaded data, or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        if not skip_error_dlg:
            showCriticalMessage("File Not Found Error", f"{file_type} not found.")
        return None
    except json.JSONDecodeError:
        showCriticalMessage("JSON Decode Error", f"Error decoding {file_type}.")
        return None


def save_db_config(config: Dict, config_path: Path = CONFIG_PATH) -> None:
    """
    Saves the given database configuration to a JSON file.

    Args:
        config (Dict): The database configuration details to save.
        config_path (Path): The file path where the configuration should be saved.

    Returns:
        None
    """
    try:
        with config_path.open('w') as file:
            json.dump(config, file)
    except Exception as e:
        showCriticalMessage("Save Error", f"Error saving database configuration: {e}")


def create_db_connection(config_path: Path = CONFIG_PATH) -> Optional[MySQLConnection]:
    """
    Creates a database connection using the configuration from a JSON file.

    Args:
        config_path (Path): The path to the JSON file containing the database configuration.

    Returns:
        Optional[MySQLConnection]: A connection object if successful, None otherwise.
    """
    config = load_json_file(config_path, "Database Configuration JSON file")
    if config is None:
        return None

    try:
        connection = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        print("MySQL Database connection successful")
        return connection
    except Error as e:
        showCriticalMessage("Connection Error", f"The error '{e}' occurred")
        return None


def get_column_indices(cursor):
    """
    Returns a list of column indices from the cursor description.

    Args:
        cursor: The database cursor after executing a query.

    Returns:
        List[int]: A list of column indices.
    """
    return [i for i, _ in enumerate(cursor.description)]


def get_column_names(cursor):
    """
    Returns a list of column names from the cursor description.

    Args:
        cursor: The database cursor after executing a query.

    Returns:
        List[str]: A list of column names.
    """
    return [col[0] for col in cursor.description]


def execute_query(query: str, data: Tuple[Any, ...] = None, **kwargs) -> Union[Dict[str, Any], Any]:
    """
    Executes a SQL query with optional parameters and behaviors controlled by keyword arguments.

    Args:
        query (str): SQL query to execute.
        data (Optional[Tuple[Any, ...]]): Parameters to substitute into the query. Defaults to None.

    Keyword Args:
        fetch_mode (str): Specifies how results should be fetched ('one', 'all', or 'none').
        return_cursor (bool): If True, returns the cursor for custom operations. Default is False.
        get_column_indices (bool): If True, includes column indices in the result. Default is False.
        get_column_names (bool): If True, fetches all column names. Default is False.

    Returns:
        Union[Dict[str, Any], Any]: If 'result' is the only key in the resulting dictionary, returns its value directly.
                                    Otherwise, returns a dictionary with keys corresponding to operations (fetch_mode,
                                    return_cursor, get_column_indices, get_column_names) and their outcomes.

    Note:
        - The function automatically commits the transaction if the query does not start with "SELECT".
        - The connection to the database is closed before returning unless 'return_cursor' is True.
        - If 'return_cursor' is True, the caller is responsible for managing the cursor and connection.
    """
    connection = create_db_connection()
    result_dict = {}

    if connection.is_connected():
        cursor = connection.cursor(buffered=True)
        try:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)

            if "get_column_indices" in kwargs and kwargs["get_column_indices"]:
                result_dict["column_indices"] = get_column_indices(cursor)

            if "get_column_names" in kwargs and kwargs["get_column_names"]:
                result_dict["column_names"] = get_column_names(cursor)

            if "return_cursor" in kwargs and kwargs["return_cursor"]:
                result_dict["cursor"] = cursor

            if query.strip().upper().startswith("SELECT") or ("skip_SELECT" in kwargs and kwargs["skip_SELECT"]):
                if kwargs.get("fetch_mode") == "all":
                    result_dict["result"] = cursor.fetchall()
                else:
                    result_dict["result"] = cursor.fetchone()
            else:
                # For non-SELECT queries, you might want to return the number of affected rows, for example
                result_dict["affected_rows"] = cursor.rowcount
                connection.commit()

        except Error as e:
            print(f"The error '{e}' occurred")
            showCriticalMessage("Query Execution Error", f"The error '{e}' occurred")
            result_dict['error'] = str(e)
        finally:
            cursor.close()
            connection.close()

    if len(result_dict) == 1 and "result" in result_dict:
        return result_dict["result"]
    else:
        return result_dict


def check_database_and_tables(database: str, config_path: Path = CONFIG_PATH) -> bool:
    """
    Verifies the existence of the specified database and required tables. Attempts to create missing tables.

    Args:
        database (str): The name of the database to check and potentially create tables within.
        config_path (Path): The path to the JSON file containing database configurations.

    Returns:
        bool: True if the database and all required tables exist or were successfully created, False otherwise.
    """
    connection = create_db_connection(config_path)
    if connection is None:
        return False

    try:
        tables = ["employees", "clients", "job_orders", "job2employer_ids"]
        for table in tables:
            result = execute_query(f"SHOW TABLES LIKE '{table}';")
            if not result:
                print(f"Table {table} does not exist. Creating...")
                create_table(table)
        return True
    except Error as e:
        showCriticalMessage("Database Check Error", f"An error occurred: {e}")
        return False
    finally:
        if connection.is_connected():
            connection.close()


def create_table(table_name: str) -> None:
    """
    Creates a specified table in the database if it does not exist.

    Args:
        table_name (str): The name of the table to create.

    Returns:
        None
    """
    queries = load_json_file(TABLE_QUERIES_PATH)
    query = queries.get(table_name)
    if query:
        try:
            execute_query(query)
            print(f"Table {table_name} checked/created successfully.")
        except Exception as e:
            QMessageBox.critical(None, "Table Creation Error", f"Error creating table '{table_name}': {e}")
    else:
        QMessageBox.critical(None, "Table Creation Error", f"Query for table '{table_name}' not found.")


def showCriticalMessage(title, message):
    dialog = QDialog()
    dialog.setWindowTitle(title)
    dialog.setWindowIcon(QIcon(str(Path(application_path, 'resources', 'icons', 'crm-icon-high-seas.png'))))
    layout = QVBoxLayout()

    # Message Label with word wrap enabled
    label = QLabel(message)
    label.setWordWrap(True)  # Enable word wrap
    layout.addWidget(label)

    # Buttons: OK and Copy to Clipboard
    buttonLayout = QHBoxLayout()
    okButton = QPushButton("OK")
    copyButton = QPushButton("Copy to Clipboard")
    buttonLayout.addWidget(okButton)
    buttonLayout.addWidget(copyButton)
    layout.addLayout(buttonLayout)

    dialog.setLayout(layout)

    # Connect the OK button to close the dialog
    okButton.clicked.connect(dialog.close)

    # Connect the Copy button to copy the message to clipboard
    def copyToClipboard():
        clipboard = QApplication.clipboard()
        clipboard.setText(message)
        dialog.close()

    copyButton.clicked.connect(copyToClipboard)

    # Show the dialog
    dialog.exec_()

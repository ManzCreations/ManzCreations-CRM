import json
import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QHBoxLayout

DECRYPTION_KEY_LOCATION = Path("path_to_some_persistent_storage.json")  # Update this path accordingly


# Determine if the application is a frozen executable or a script
if getattr(sys, 'frozen', False):
    application_path = Path(sys._MEIPASS)
else:
    application_path = Path(os.path.dirname(os.path.abspath(__file__)))

# Go up two levels from the current application_path
application_path = application_path.parent.parent

# Read the stylesheet content
stylesheet_path = Path(application_path, 'resources', 'style_properties', 'stylesheet.qss')
with open(stylesheet_path, 'r') as file:
    stylesheet = file.read()


class ConfigDialog(QDialog):
    def __init__(self, stylesheet):
        super().__init__()
        self.setStyleSheet(stylesheet)
        self.setWindowTitle("Configuration Required")
        self.setLayout(QVBoxLayout())
        self.setMinimumSize(400, 120)

        self.label = QLabel("Please locate your 'config.json' file to proceed.\n"
                            "This file contains important configuration settings.")
        self.layout().addWidget(self.label)

        # Edit field and Browse button next to it
        self.editField = QLineEdit()
        self.browseButton = QPushButton("Browse")
        self.browseButton.clicked.connect(self.browseFile)

        editLayout = QHBoxLayout()
        editLayout.addWidget(self.editField)
        editLayout.addWidget(self.browseButton)
        self.layout().addLayout(editLayout)

        # OK and Cancel buttons at the bottom
        self.okButton = QPushButton("OK")
        self.okButton.clicked.connect(self.confirm)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.cancel)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        self.layout().addLayout(buttonLayout)

        self.configPath = ""

    def browseFile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select config file", "", "JSON files (*.json)")
        if file:
            self.editField.setText(file)

    def confirm(self):
        if self.editField.text():
            self.configPath = self.editField.text()
            self.accept()
        else:
            QMessageBox.warning(self, "Configuration Required", "A valid config file location is required to proceed.")

    def cancel(self):
        QMessageBox.critical(self, "Application Cannot Proceed",
                             "You must choose a valid location of a config file with a valid decryption key. "
                             "If that is not provided, the application will not open.")
        self.reject()


def get_config_path():
    if DECRYPTION_KEY_LOCATION.exists():
        with open(DECRYPTION_KEY_LOCATION, 'r') as file:
            return file.read().strip()
    return ""


def set_config_path(path):
    with open(DECRYPTION_KEY_LOCATION, 'w') as file:
        file.write(path)


def prompt_for_config_path():
    app = QApplication([])
    dialog = ConfigDialog(stylesheet)
    if dialog.exec_() == QDialog.Accepted:
        set_config_path(dialog.configPath)
        return dialog.configPath
    return ""


def read_config():
    config_path = get_config_path()
    if not config_path or not Path(config_path).exists():
        config_path = prompt_for_config_path()
    if not config_path:  # Still no path, exit or handle error
        raise FileNotFoundError("Config file not found.")
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


def init_gpg(gpg_home, gpg_binary_path):
    import gnupg
    return gnupg.GPG(gnupghome=gpg_home, gpgbinary=gpg_binary_path)


# Function to recursively decrypt files
def decrypt_files():
    config = read_config()
    passphrase = config['passphrase']
    gpg = init_gpg(config['gpg_home'], config['gpg_binary_path'])
    for start_path in config['start_paths']:
        for root, dirs, files in os.walk(start_path):
            for file in files:
                if file.endswith(".gpg"):
                    encrypted_file_path = Path(root) / file
                    decrypted_file_path = encrypted_file_path.with_suffix('')
                    with open(encrypted_file_path, 'rb') as f:
                        status = gpg.decrypt_file(f, passphrase=passphrase, output=str(decrypted_file_path))
                        if status.ok:
                            print(f"Decrypted: {encrypted_file_path}")
                        else:
                            print(f"Failed to decrypt: {encrypted_file_path}")


if __name__ == '__main__':
    decrypt_files()

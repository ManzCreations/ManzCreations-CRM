# ManzCreations CRM

ManzCreations CRM is a Customer Relationship Management application that helps businesses manage client information, employee details, and job orders efficiently. Built with Python and PyQt5, it features a user-friendly interface and utilizes Pandas for data manipulation and MySQL for data storage, making it a powerful tool for enhancing customer service and business operations.

## Getting Started

### Prerequisites

- Python 3.8 or later
- MySQL Server
- LibreOffice (for document handling)
- GnuPG (for file encryption and decryption)

### Setting Up MySQL

1. Before installing MySQL Server, ensure the Visual Studio 2019 x64 Redistributable is installed on your system. This is crucial for MySQL Server to function properly. Download and install the most updated version of Visual Studio 2019 x64 Redistributable from [the official Microsoft download page](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).
2. Install MySQL Server on your system.
3. Create a database for ManzCreations CRM:
   CREATE DATABASE manzCreations_crm;
4. Import the ManzCreations CRM database schema (provided separately).

### Setting Up Python

1. Ensure Python is installed on your system.
2. Clone the repository or download the project to your local machine.
3. Navigate to the project directory.
4. Install required Python packages using the `requirements.txt` file:
pip install -r requirements.txt


### Installing and Configuring LibreOffice

1. Download and install LibreOffice from [the official website](https://www.libreoffice.org/download/download/).
2. Add the path to the LibreOffice executable to your system's environment variables.

### Installing and Configuring GnuPG

1. Download and install GnuPG from [the official GnuPG website](https://gnupg.org/download/index.html).
2. Add the path to the GnuPG executable (`bin` directory) to your system's environment variables.

### Configuring Decryption

Create a JSON file named `config.json` in a secure location outside of your application directory to prevent unauthorized access with the following format:

```json
{
 "passphrase": "YourPassphraseHere",
 "start_paths": [
     "C:/Users/manzf/Documents/ManzCreations-CRM/application"
 ],
 "gpg_binary_path": "C:/Program Files (x86)/GnuPG/bin/gpg.exe",
 "gpg_home": "C:/Users/manzf/AppData/Roaming/gnupg"
}
```
Replace YourPassphraseHere with the passphrase provided by the owner of the code.

Creating a JSON file is straightforward:

1. Open a text editor (like Notepad on Windows, TextEdit on Mac, or Gedit on Linux).
2. Type the JSON structure with keys and values.
3. Save the file with a .json extension.

Each key in the config.json dictionary explained:
- `passphrase`: A secret key used for encryption or decryption. Ensure it's complex for security.
- `start_paths`: An array of paths where the application begins execution, pointing to necessary directories or files.
- `gpg_binary_path`: The file path to the GnuPG executable, used for cryptographic operations.
- `gpg_home`: Directory path where GnuPG stores its configuration files and keyrings.
- 
Remember, each key-value pair in the JSON file configures how your application handles decryption, starting from specifying the passphrase to defining paths for necessary executables and directories. Always use absolute paths for directories to avoid errors.

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

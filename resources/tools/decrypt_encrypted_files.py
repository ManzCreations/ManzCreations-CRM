import json
import os
from pathlib import Path

import gnupg

DECRYPTION_KEY_LOCATION = ""


# Function to read configuration from JSON file
def read_config(config_path=DECRYPTION_KEY_LOCATION):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


# Initialize GPG
def init_gpg(gpg_home, gpg_binary_path):
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
                        # Assuming you have a way to securely provide the passphrase
                        status = gpg.decrypt_file(f, passphrase=passphrase, output=str(decrypted_file_path))

                        if status.ok:
                            print(f"Decrypted: {encrypted_file_path}")
                        else:
                            print(f"Failed to decrypt: {encrypted_file_path}")


if __name__ == '__main__':
    decrypt_files()

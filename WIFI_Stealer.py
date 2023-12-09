import os
import subprocess
import re
import csv
import socket

# Function to check and rename the file if it exists
def rename_existing_file(filename):
    if os.path.exists(filename):
        base_name, ext = os.path.splitext(filename)
        count = 1
        while True:
            new_filename = f"{base_name}_{count}{ext}"
            if not os.path.exists(new_filename):
                return new_filename
            count += 1
    return filename  # Return original filename if it doesn't exist

# Function to retrieve detailed Wi-Fi profiles and save as TXT files
def save_wifi_profiles():
    profiles = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True).stdout
    ssid_names = re.findall(r"All User Profile\s+:\s(.*)", profiles)

    for ssid in ssid_names:
        try:
            ssid_info = subprocess.run(["netsh", "wlan", "show", "profile", ssid.strip(), "key=clear"], capture_output=True, text=True).stdout
            # Remove problematic characters '*' and ''' from SSID names
            cleaned_ssid = re.sub(r'[*\']', '', ssid)
            txt_file = os.path.join(profile_folder, f"{cleaned_ssid}.txt")
            txt_file = rename_existing_file(txt_file)  # Check and rename if file exists
            with open(txt_file, "w", encoding="utf-8") as file:
                file.write(ssid_info)
        except subprocess.CalledProcessError as e:
            print(f"Error retrieving profile {ssid}: {e}")

# Function to clean SSID names from special characters
def clean_ssid(ssid):
    # Replace problematic characters with their escape sequences
    cleaned_ssid = ssid.replace('*', r'\*').replace("'", r"\'")
    return cleaned_ssid

# Retrieve Wi-Fi profiles with password information
profiles = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True).stdout
ssid_names = re.findall(r"All User Profile\s+:\s(.*)", profiles)
ssid_passwords_dict = {}  # To store SSID-password pairs without duplicates

for ssid in ssid_names:
    ssid_info = subprocess.run(["netsh", "wlan", "show", "profile", ssid.strip(), "key=clear"], capture_output=True, text=True).stdout
    password = re.search(r"Key Content\s+:\s(.*)", ssid_info)
    if password:
        # Normalize SSID names by stripping spaces and converting to lowercase
        normalized_ssid = clean_ssid(ssid.strip().lower())
        if normalized_ssid not in ssid_passwords_dict:  # Check if the SSID is not already added
            ssid_passwords_dict[normalized_ssid] = password.group(1)
            print(f"SSID: {ssid}\nPassword: {password.group(1)}\n")

# Get the computer's hostname
pc_name = socket.gethostname()

# Create a 'dump' folder if it doesn't exist
dump_folder = "Extracted"
if not os.path.exists(dump_folder):
    os.makedirs(dump_folder)

# Find the next available file name for all-in-one CSV
csv_all_base_name = f"wifi_passwords_{pc_name}"
count = 1
while True:
    csv_all_file = os.path.join(dump_folder, f"{csv_all_base_name}_{count}.csv")
    if not os.path.exists(csv_all_file):
        csv_all_file = rename_existing_file(csv_all_file)  # Check and rename if file exists
        with open(csv_all_file, "w", newline="", encoding="utf-8") as file:
            fieldnames = ["SSID", "Password"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            ssid_passwords = [{"SSID": ssid, "Password": password} for ssid, password in ssid_passwords_dict.items()]
            writer.writeheader()
            writer.writerows(ssid_passwords)
        break
    count += 1

# Create folders for Wi-Fi profiles and save as TXT files
wifi_profiles_folder = f"wifi_profiles_{pc_name}"
count = 1
while True:
    profile_folder = os.path.join(dump_folder, f"{wifi_profiles_folder}_{count}")
    if not os.path.exists(profile_folder):
        os.makedirs(profile_folder)
        break
    count += 1

save_wifi_profiles()

print(f"All SSIDs and passwords saved in file: {csv_all_file}")
print(f"Wifi profiles saved in {wifi_profiles_folder}_{count}")
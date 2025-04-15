# by zhlhlf

import requests
import json
from tabulate import tabulate
import subprocess

# Alist configuration
ALIST_URL = "http://127.0.0.1:5244"
USERNAME = "admin"  # Replace with your actual username
PASSWORD = "admin"  # Replace with your actual password

# Reset password
def reset_password():
    try:
        subprocess.check_call(["./alist", "admin", "set", PASSWORD])
        print("Password reset successfully")
    except Exception as e:
        print(f"Failed to reset password: {e}")

# Login to get token
def login():
    login_url = f"{ALIST_URL}/api/auth/login"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        return response.json()["data"]["token"]
    else:
        raise Exception(f"Login failed: {response.text}")

# Add storage
def add_storage(token, storage_data):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    url = f"{ALIST_URL}/api/admin/storage/create"
    response = requests.post(url, json=storage_data, headers=headers)
    if response.status_code == 200:
        print(f"Successfully added storage: {storage_data['mount_path']}")
        return True
    else:
        print(f"Failed to add storage {storage_data['mount_path']}: {response.text}")
        return False

# Get storage list
def get_storage_list(token):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    url = f"{ALIST_URL}/api/admin/storage/list"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["content"]
    else:
        raise Exception(f"Failed to get storage list: {response.text}")

def print_storage_list(storages):
    # Prepare data for table
    table_data = []
    for storage in storages:
        table_data.append([
            storage["id"],
            storage["mount_path"],
            storage["driver"],
            storage["status"],
            "Enabled" if not storage["disabled"] else "Disabled"
        ])
    
    # Print table
    headers = ["ID", "Mount Path", "Driver", "Status", "Enabled"]
    print("\nCurrent Storage List:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def main():
    # Reset password
    reset_password()

    # Load the JSON data
    try:
        with open('alist_config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: alist_config.json not found in current directory")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in alist_config.json")
        return
    
    # Login to get token
    try:
        token = login()
        print("Login successful")
    except Exception as e:
        print(e)
        return
    # Add each storage
    print("\nAdding storages...")
    for storage in data["storages"]:
        storage_data = {
            "mount_path": storage["mount_path"],
            "order": storage["order"],
            "driver": storage["driver"],
            "cache_expiration": storage["cache_expiration"],
            "status": storage["status"],
            "addition": storage["addition"],
            "remark": storage["remark"],
            "disabled": storage["disabled"],
            "enable_sign": storage["enable_sign"],
            "order_by": storage["order_by"],
            "order_direction": storage["order_direction"],
            "extract_folder": storage["extract_folder"],
            "web_proxy": storage["web_proxy"],
            "webdav_policy": storage["webdav_policy"],
            "proxy_range": storage["proxy_range"],
            "down_proxy_url": storage["down_proxy_url"]
        }
        add_storage(token, storage_data)
    
    # Get and print current storage list
    try:
        current_storages = get_storage_list(token)
        print_storage_list(current_storages)
    except Exception as e:
        print(f"Error getting storage list: {e}")

if __name__ == "__main__":
    # Install tabulate if not already installed
    try:
        from tabulate import tabulate
    except ImportError:
        print("Installing required package: tabulate")
        subprocess.check_call(["pip", "install", "tabulate"])
        from tabulate import tabulate
    
    main()
      
      
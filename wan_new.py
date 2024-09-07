import os
import csv
import pandas as pd
import chardet

# Create input and output folders if they don't exist
input_folder = 'input'
output_folder = 'output'

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Function to normalize the node type
def normalize_node_type(node_type):
    if node_type.startswith('C'):
        return 'C1'
    elif node_type.startswith('B3'):
        return 'B3'
    elif node_type.startswith('B4'):
        return 'B4'
    elif node_type.startswith('A3'):
        return 'A3'
    elif node_type.startswith('A4'):
        return 'A4'
    else:
        return node_type  # Fallback if none of the conditions match

# Function to generate configuration based on the provided template
def generate_config(interface, vlan, ip_address, subnet_mask, remote_site_id_last7, port, remote_port_modified, area):
    config_template = f"""
configure terminal
l2-mode {interface}
int {interface}
bpdu-tu en
int lldp
lldp transmit-and-receive
exit
description To_{remote_site_id_last7}_{remote_port_modified}
set mpls enable
no shut
vlan {vlan}
description To_{remote_site_id_last7}_{remote_port_modified}_A-{area}
ip add {ip_address} {subnet_mask}
l3-mtu 9216
set mpls enable
set l3-mpls enable
no shut
end
"""
    return config_template

# Function to parse the Interfaces CSV and create a lookup dictionary
def create_interface_lookup(interfaces_csv):
    interface_lookup = {}
    with open(interfaces_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (normalize_node_type(row['Type of Node']), row['Ports'])
            interface_lookup[key] = row['Interface']
    return interface_lookup

# Function to parse the WAN CSV and generate configurations for a given site ID
def generate_site_config(site_id, node_type, csv_file, interface_lookup):
    subnet_mask = "255.255.255.252"  # Subnet mask for /30 network
    configs = []

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['A End SITE ID'] == site_id or row['B End SITE ID'] == site_id:
                port = row['A End Port Details'] if row['A End SITE ID'] == site_id else row['B End Port Details']
                remote_port = row['B End Port Details'] if row['A End SITE ID'] == site_id else row['A End Port Details']
                vlan = row['VLAN']
                ip_address = row['A End IP Address'] if row['A End SITE ID'] == site_id else row['B End IP Address']
                remote_site_id = row['B End SITE ID'] if row['A End SITE ID'] == site_id else row['A End SITE ID']
                area = row['OSPF Area']
                remote_site_id_last7 = remote_site_id[-7:]
                remote_port_modified = remote_port.replace('/', '-')
                interface = interface_lookup.get((node_type, port), port)
                config = generate_config(interface, vlan, ip_address, subnet_mask, remote_site_id_last7, port, remote_port_modified, area)
                configs.append(config)

    return configs

# Function to save configurations to a text file
def save_configs_to_file(site_id, configs):
    filename = os.path.join(output_folder, f"{site_id}_WAN.txt")
    with open(filename, 'w') as file:
        for config in configs:
            file.write(config)
    print(f"Configurations saved to {filename}")

# Main function to execute the script
def main():
    wan_csv_file = os.path.join(input_folder, 'WAN.csv')  # Path to the WAN CSV file
    interfaces_csv_file = 'input/interfaces.csv'  # Path to the Interfaces CSV file
    loopback_csv_file = os.path.join(input_folder, 'loopback.csv')  # Path to the Loopback CSV file

    # Create interface lookup dictionary
    interface_lookup = create_interface_lookup(interfaces_csv_file)

    # Load the loopback CSV to get site IDs and node types
    with open(loopback_csv_file, 'rb') as file:
        result = chardet.detect(file.read())
        encoding = result['encoding']
    df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)

    while True:
        generate_for_all = input("Do you want to generate WAN configurations for all sites? (yes/no): ").strip().lower()
        
        if generate_for_all == 'yes':
            for site_id in df_loopback['SITE ID'].unique():
                site_info = df_loopback[df_loopback['SITE ID'] == site_id]
                if not site_info.empty:
                    node_type_raw = site_info['Type of Node'].values[0]
                    node_type = normalize_node_type(node_type_raw)

                    print(f"Generating WAN configuration for Site ID: {site_id} with Node Type: {node_type}")
                    configs = generate_site_config(site_id, node_type, wan_csv_file, interface_lookup)
                    save_configs_to_file(site_id, configs)
                else:
                    print(f"Site ID {site_id} not found in loopback.csv.")
            print("WAN configurations generated for all sites.")
            break

        else:
            while True:
                site_id = input("Enter the Site ID: ")

                site_info = df_loopback[df_loopback['SITE ID'] == site_id]
                if not site_info.empty:
                    node_type_raw = site_info['Type of Node'].values[0]
                    node_type = normalize_node_type(node_type_raw)

                    print(f"Generating WAN configuration for Site ID: {site_id} with Node Type: {node_type}")
                    configs = generate_site_config(site_id, node_type, wan_csv_file, interface_lookup)
                    save_configs_to_file(site_id, configs)
                else:
                    print(f"Site ID {site_id} not found in loopback.csv.")

                restart = input("Do you want to generate WAN configurations for another Site-ID? (yes/no): ").strip().lower()
                if restart != 'yes':
                    break

        exit_script = input("Do you want to exit the script? (yes/no): ").strip().lower()
        if exit_script == 'yes':
            print("Exiting the script.")
            break

if __name__ == "__main__":
    main()

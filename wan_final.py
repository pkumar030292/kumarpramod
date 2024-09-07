import os
import csv
import chardet

# Create input and output folders if they don't exist
input_folder = 'input'
output_folder = 'output'

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

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
description Towards_{remote_site_id_last7}_{remote_port_modified}
set mpls enable
no shut
vlan {vlan}
description Towards_{remote_site_id_last7}_{remote_port_modified}_A-{area}
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
            key = (row['Type of Node'], row['Ports'])
            interface_lookup[key] = row['Interface']
    return interface_lookup

# Function to parse the WAN CSV and generate configurations for a given site ID
def generate_site_config(site_id, node_type, csv_file, interface_lookup):
    subnet_mask = "255.255.255.252"  # Subnet mask for /30 network
    configs = []

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['A End SITE ID'] == site_id:
                port = row['A End Port Details']
                remote_port = row['B End Port Details']
                vlan = row['VLAN']
                ip_address = row['A End IP Address']
                remote_site_id = row['B End SITE ID']
                area = row['OSPF Area']
                remote_site_id_last7 = remote_site_id[-7:]
                remote_port_modified = remote_port.replace('/', '-')
                interface = interface_lookup.get((node_type, port), port)
                config = generate_config(interface, vlan, ip_address, subnet_mask, remote_site_id_last7, port, remote_port_modified, area)
                configs.append(config)
            elif row['B End SITE ID'] == site_id:
                port = row['B End Port Details']
                remote_port = row['A End Port Details']
                vlan = row['VLAN']
                ip_address = row['B End IP Address']
                remote_site_id = row['A End SITE ID']
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
    while True:
        site_id = input("Enter the Site ID: ")
        node_type = input("Enter the Node Type(C1,B4,B3,A4,A3): ")
        wan_csv_file = os.path.join(input_folder, 'WAN.csv')  # Path to the WAN CSV file
        interfaces_csv_file = os.path.join(input_folder, 'Interfaces.csv')  # Path to the Interfaces CSV file

        # Create interface lookup dictionary
        interface_lookup = create_interface_lookup(interfaces_csv_file)

        # Generate configurations
        configs = generate_site_config(site_id, node_type, wan_csv_file, interface_lookup)
        
        # Save configurations to file
        save_configs_to_file(site_id, configs)
        # Ask user if they want to restart or, exit
        restart = input("Do you want to generate WAN configurations for another Site-ID? (yes/no): ").strip().lower()
        if restart != 'yes':
            print("Exiting the script.")
            break

if __name__ == "__main__":
    main()
import os
import csv
import chardet

# Create input and output folders if they don't exist
input_folder = 'input'
output_folder = 'output'

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Function to generate global configuration based on the provided template
def generate_global_config(router_id):
    return f"""configure terminal

bfd global interval 3 min_rx 3 offload
bfd enable

end

conf t
rsvp
router-id {router_id}
set rsvp disable
no signalling refresh reduction disable
signalling label range min 200001 max 260000
reoptimize-time 14400
signalling hello supported
signalling hello graceful-restart full
signalling hello graceful-restart recovery-time 480
signalling hello graceful-restart restart-time 1920
enable bfd
set rsvp enable
end
"""

# Function to generate TE-Link configuration based on the provided template
def generate_te_link_config(router_id, remote_router_id, vlan, site_id_last7, remote_site_id_last7, area, ip_address, remote_ip_address, link_bw):
    metric = int(100 / link_bw)
    config_template = f"""
conf t
rsvp
interface vlan {vlan}
shutdown
signalling hello supported
signalling mtu 1500
signalling ttl 64
no shutdown
end

conf terminal
mpls traffic-eng tunnels
mpls traffic-eng
te-link {site_id_last7}_{remote_site_id_last7}_A-{area}
shutdown
metric {metric}
remote router-id {remote_router_id}
address-type ipv4
local te-link ipv4 {ip_address} remote te-link ipv4 {remote_ip_address}
advertise
link type point-to-point
interface vlan {vlan}
no shutdown
exit
no shutdown
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

# Function to parse the Loopback CSV and create a lookup dictionary
def create_loopback_lookup(loopback_csv):
    loopback_lookup = {}
    with open(loopback_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            loopback_lookup[row['SITE ID']] = row['Router ID']
    return loopback_lookup

# Function to parse the WAN CSV and generate configurations for a given site ID
def generate_site_config(site_id, wan_csv_file, interfaces_csv_file, loopback_csv_file):
    subnet_mask = "255.255.255.252"  # Subnet mask for /30 network
    configs = []

    # Create interface lookup dictionary
    interface_lookup = create_interface_lookup(interfaces_csv_file)

    # Create loopback lookup dictionary
    loopback_lookup = create_loopback_lookup(loopback_csv_file)

    with open(wan_csv_file, 'r') as file:
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
                site_id_last7 = site_id[-7:]
                remote_port_modified = remote_port.replace('/', '-')
                interface = interface_lookup.get((port), port)
                router_id = loopback_lookup.get(site_id)
                remote_router_id = loopback_lookup.get(remote_site_id)
                remote_ip_address = row['B End IP Address']
                link_bw = float(row['Link BW'].replace('G', ''))  # Assuming Link BW is in Gbps
                config = generate_te_link_config(router_id, remote_router_id, vlan, site_id_last7, remote_site_id_last7, area, ip_address, remote_ip_address, link_bw)
                configs.append(config)
            elif row['B End SITE ID'] == site_id:
                port = row['B End Port Details']
                remote_port = row['A End Port Details']
                vlan = row['VLAN']
                ip_address = row['B End IP Address']
                remote_site_id = row['A End SITE ID']
                area = row['OSPF Area']
                remote_site_id_last7 = remote_site_id[-7:]
                site_id_last7 = site_id[-7:]
                remote_port_modified = remote_port.replace('/', '-')
                interface = interface_lookup.get((port), port)
                router_id = loopback_lookup.get(site_id)
                remote_router_id = loopback_lookup.get(remote_site_id)
                remote_ip_address = row['A End IP Address']
                link_bw = float(row['Link BW'].replace('G', ''))  # Assuming Link BW is in Gbps
                config = generate_te_link_config(router_id, remote_router_id, vlan, site_id_last7, remote_site_id_last7, area, ip_address, remote_ip_address, link_bw)
                configs.append(config)

    return configs

# Function to save configurations to a text file
def save_configs_to_file(site_id, global_config, configs):
    filename = os.path.join(output_folder, f"{site_id}_rsvp_config.txt")
    with open(filename, 'w') as file:
        file.write(global_config)
        for config in configs:
            file.write(config)
    print(f"RSVP configurations saved to {filename}")

# Main function to execute the script
def main():
    loopback_csv_file = os.path.join(input_folder, 'loopback.csv')  # Path to the Loopback CSV file
    wan_csv_file = os.path.join(input_folder, 'WAN.csv')  # Path to the WAN CSV file
    interfaces_csv_file = os.path.join(input_folder, 'Interfaces.csv')  # Path to the Interfaces CSV file

    while True:
        option = input("Do you want to generate configurations for all sites or just one? (all/one): ").strip().lower()

        # Create loopback lookup dictionary
        loopback_lookup = create_loopback_lookup(loopback_csv_file)

        if option == 'all':
            for site_id in loopback_lookup.keys():
                router_id = loopback_lookup.get(site_id)
                if router_id:
                    # Generate global configuration
                    global_config = generate_global_config(router_id)

                    # Generate TE-Link configurations
                    configs = generate_site_config(site_id, wan_csv_file, interfaces_csv_file, loopback_csv_file)

                    # Save configurations to file
                    save_configs_to_file(site_id, global_config, configs)
                else:
                    print(f"Router ID not found for Site ID: {site_id}")

        elif option == 'one':
            while True:
                site_id = input("Enter the Site ID: ")

                router_id = loopback_lookup.get(site_id)
                if router_id:
                    # Generate global configuration
                    global_config = generate_global_config(router_id)

                    # Generate TE-Link configurations
                    configs = generate_site_config(site_id, wan_csv_file, interfaces_csv_file, loopback_csv_file)

                    # Save configurations to file
                    save_configs_to_file(site_id, global_config, configs)
                else:
                    print(f"Router ID not found for Site ID: {site_id}")

                # Ask user if they want to create another configuration
                another = input("Do you want to generate RSVP configurations for another Site-ID? (yes/no): ").strip().lower()
                if another != 'yes':
                    break

        # Ask user if they want to restart or exit
        restart = input("Do you want to start the script again? (yes/no): ").strip().lower()
        if restart != 'yes':
            print("Exiting the script.")
            break

if __name__ == "__main__":
    main()

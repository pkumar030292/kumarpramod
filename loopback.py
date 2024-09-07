import os
import pandas as pd
import chardet

# Create input and output folders if they don't exist
input_folder = 'input'
output_folder = 'output'

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Function to generate loopback configuration based on the provided template
def generate_loopback_config(loopback_number, loopback_type, loopback_area, loopback_ip):
    config_template = f"""
config terminal
interface loopback {loopback_number}
description {loopback_type}_Lo{loopback_number}_A-{loopback_area}
ip address {loopback_ip} 255.255.255.255
end
"""
    return config_template

# Function to parse the Loopback CSV and generate configurations for a specific site ID
def generate_loopback_configs(loopback_csv_file, site_id):
    configs = []
    with open(loopback_csv_file, 'rb') as file:
        result = chardet.detect(file.read())
        encoding = result['encoding']
    df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
    for index, row in df.iterrows():
        if row['SITE ID'] == site_id:
            for i in range(1, 5):  # Loop through Area ID - 1 to Area ID - 4
                area_key = f"Area ID - {i}"
                mgmt_ip_key = f"Management IP - Loopback {2*i-1}"
                service_ip_key = f"Service IP - Loopback {2*i}"

                if area_key in row and pd.notna(row[area_key]):
                    loopback_area = int(row[area_key])  # Convert to integer

                    if mgmt_ip_key in row and pd.notna(row[mgmt_ip_key]):
                        loopback_number = 2*i-1
                        loopback_type = "MGMT"
                        loopback_ip = str(row[mgmt_ip_key]).strip()
                        config = generate_loopback_config(loopback_number, loopback_type, loopback_area, loopback_ip)
                        configs.append(config)

                    if service_ip_key in row and pd.notna(row[service_ip_key]):
                        loopback_number = 2*i
                        loopback_type = "Service"
                        loopback_ip = str(row[service_ip_key]).strip()
                        config = generate_loopback_config(loopback_number, loopback_type, loopback_area, loopback_ip)
                        configs.append(config)

    return configs

# Function to save configurations to a text file
def save_loopback_configs_to_file(site_id, configs):
    filename = os.path.join(output_folder, f"{site_id}_loopback_config.txt")
    with open(filename, 'w') as file:
        for config in configs:
            file.write(config)
    print(f"Loopback configurations saved to {filename}")

# Main function to execute the script
def main():
    while True:
        site_id = input("Enter the Site ID: ")
        loopback_csv_file = os.path.join(input_folder, 'loopback.csv')  # Path to the Loopback CSV file

        # Generate loopback configurations for the specified site ID
        configs = generate_loopback_configs(loopback_csv_file, site_id)
        
        # Save configurations to file
        save_loopback_configs_to_file(site_id, configs)
        # Ask user if they want to restart or, exit
        restart = input("Do you want to generate Loopback configurations for another Site-ID? (yes/no): ").strip().lower()
        if restart != 'yes':
            print("Exiting the script.")
            break

if __name__ == "__main__":
    main()
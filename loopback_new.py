import os
import pandas as pd
import chardet
from datetime import datetime
import sys

def ensure_directories(input_folder, output_folder):
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

def generate_loopback_config(loopback_number, loopback_type, loopback_area, loopback_ip):
    config_template = f"""
config terminal
interface loopback {loopback_number}
description {loopback_type}_Lo{loopback_number}_A-{loopback_area}
ip address {loopback_ip} 255.255.255.255
end
"""
    return config_template

def generate_basic_config(site_id, site_name, router_id):
    current_date = datetime.now().strftime("%m/%d/%Y")
    current_time = datetime.now().strftime("%H:%M:%S")

    config_template = f"""
configure terminal
system date {current_date}
system time {current_time}
hostname "{site_id}"
system location "{site_name}"
system router-id {router_id}
end
"""
    return config_template

def generate_mtu_config():
    config_template = f"""
configure terminal
switch-config
no global l3mtu 1518
global l3mtu 9216
global l3mtu 9192
end
"""
    return config_template

def generate_loopback_configs(loopback_csv_file, site_id):
    configs = []
    try:
        with open(loopback_csv_file, 'rb') as file:
            result = chardet.detect(file.read())
            encoding = result['encoding']
        df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
        site_data = df_loopback[df_loopback['SITE ID'] == site_id].iloc[0]

        basic_config = generate_basic_config(site_data['SITE ID'], site_data['Site Name'], site_data['Router ID'])
        configs.append(basic_config)

        mtu_config = generate_mtu_config()
        configs.append(mtu_config)

        for index, row in df_loopback.iterrows():
            if row['SITE ID'] == site_id:
                for i in range(1, 5):
                    area_key = f"Area ID - {i}"
                    mgmt_ip_key = f"Management IP - Loopback {2*i-1}"
                    service_ip_key = f"Service IP - Loopback {2*i}"

                    if area_key in row and pd.notna(row[area_key]):
                        loopback_area = int(row[area_key])

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

    except Exception as e:
        print(f"Error generating loopback configs: {e}")
        sys.exit(1)

    return configs

def save_loopback_configs_to_file(output_folder, site_id, configs):
    filename = os.path.join(output_folder,'OP_LOOPBACK', f"{site_id}_loopback_config.txt")
    with open(filename, 'w') as file:
        for config in configs:
            file.write(config)
    print(f"Loopback configurations saved to {filename}")

def main():
    if len(sys.argv) != 5:
        print("Usage: python loopback_new.py <input_folder> <output_folder> <site_id> <all_or_single>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    site_id = sys.argv[3]
    mode = sys.argv[4]

    ensure_directories(input_folder, output_folder)
    print(input_folder, "this is testing only..............")
    loopback_csv_file = os.path.join(input_folder, 'IP_loopback', 'loopback.csv')

    if mode == 'all':
        try:
            with open(loopback_csv_file, 'rb') as file:
                result = chardet.detect(file.read())
                encoding = result['encoding']
            df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)

            for site_id in df_loopback['SITE ID'].unique():
                print(f"Generating Loopback configuration for Site ID: {site_id}", file=sys.stderr)
                configs = generate_loopback_configs(loopback_csv_file, site_id)
                save_loopback_configs_to_file(output_folder, site_id, configs)

            print("Loopback configurations generated for all sites.", file=sys.stderr)
        except Exception as e:
            print(f"Error generating configurations for all sites: {e}", file=sys.stderr)
            sys.exit(1)
    elif mode == 'single':
        try:
            with open(loopback_csv_file, 'rb') as file:
                result = chardet.detect(file.read())
                encoding = result['encoding']
            df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
            if site_id in df_loopback['SITE ID'].values:
                # print(f"Generating Loopback configuration for Site ID: {site_id}", file=sys.stderr)
                configs = generate_loopback_configs(loopback_csv_file, site_id)
                save_loopback_configs_to_file(output_folder, site_id, configs)
                print(f"Site ID {site_id} not found in the CSV file.", file=sys.stderr)
                sys.exit(0)
            else:
                print(f"Site ID {site_id} not found in the CSV file.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error generating Loopback configuration for single site: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Invalid mode specified. Use 'all' or 'single'.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

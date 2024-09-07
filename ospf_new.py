import os
import sys
import pandas as pd
import chardet

def ensure_directories(input_folder, output_folder):
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

def generate_ospf_config(router_id, loopback_configs, wan_configs):
    config = f"""
configure terminal
router ospf
router-id {router_id}
nsf ietf restart-support
nsf ietf restart-interval 1800
end
"""
    for loopback_ip, loopback_area in loopback_configs:
        config += f"""
configure terminal
router ospf
network {loopback_ip} area 0.0.0.{loopback_area}
end
"""

    for wan_ip, wan_area, vlan, link_bw in wan_configs:
        cost = int(100 / link_bw)
        config += f"""
configure terminal
router ospf
network {wan_ip} area 0.0.0.{wan_area}
end

configure terminal
VLAN {vlan}
ip ospf network point-to-point
ip ospf hello-interval 30
ip ospf dead-interval 1800
ip ospf cost {cost}
end
"""
    return config

def get_loopback_configs(loopback_csv_file, site_id):
    loopback_configs = []
    try:
        with open(loopback_csv_file, 'rb') as file:
            result = chardet.detect(file.read())
            encoding = result['encoding']
        df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
    except Exception as e:
        print(f"Error reading loopback CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    for index, row in df_loopback.iterrows():
        if row['SITE ID'] == site_id:
            for i in range(1, 5):
                area_key = f"Area ID - {i}"
                mgmt_ip_key = f"Management IP - Loopback {2*i-1}"
                service_ip_key = f"Service IP - Loopback {2*i}"

                if area_key in row and pd.notna(row[area_key]):
                    loopback_area = int(row[area_key])

                    if mgmt_ip_key in row and pd.notna(row[mgmt_ip_key]):
                        loopback_ip = str(row[mgmt_ip_key]).strip()
                        loopback_configs.append((loopback_ip, loopback_area))

                    if service_ip_key in row and pd.notna(row[service_ip_key]):
                        loopback_ip = str(row[service_ip_key]).strip()
                        loopback_configs.append((loopback_ip, loopback_area))

    return loopback_configs

def get_wan_configs(wan_csv_file, site_id):
    wan_configs = []
    try:
        df = pd.read_csv(wan_csv_file)
    except Exception as e:
        print(f"Error reading WAN CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    for index, row in df.iterrows():
        if row['A End SITE ID'] == site_id or row['B End SITE ID'] == site_id:
            wan_ip = row['A End IP Address'] if row['A End SITE ID'] == site_id else row['B End IP Address']
            wan_area = row['OSPF Area']
            vlan = row['VLAN']
            link_bw = float(row['Link BW'].replace('G', ''))
            wan_configs.append((wan_ip, wan_area, vlan, link_bw))

    return wan_configs

def save_ospf_configs_to_file(output_folder, site_id, config):
    filename = os.path.join(output_folder, 'OP_OSPF', f"{site_id}_ospf_config.txt")
    try:
        with open(filename, 'w') as file:
            file.write(config)
        print(f"OSPF configurations saved to {filename}")
    except Exception as e:
        print(f"Error saving OSPF configurations: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 5:
        print("Usage: python ospf_new.py <input_folder> <output_folder> <site_id> <all_or_single>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    site_id = sys.argv[3]
    mode = sys.argv[4]

    ensure_directories(input_folder, output_folder)
    loopback_csv_file = os.path.join(input_folder, 'IP_loopback', 'loopback.csv')
    wan_csv_file = os.path.join(input_folder, 'IP_loopback', 'wan.csv')

    if mode == 'all':
        try:
            with open(loopback_csv_file, 'rb') as file:
                result = chardet.detect(file.read())
                encoding = result['encoding']
            df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
            for site_id in df_loopback['SITE ID'].unique():
                router_id = df_loopback[df_loopback['SITE ID'] == site_id]['Router ID'].values[0]
                loopback_configs = get_loopback_configs(loopback_csv_file, site_id)
                wan_configs = get_wan_configs(wan_csv_file, site_id)
                config = generate_ospf_config(router_id, loopback_configs, wan_configs)
                save_ospf_configs_to_file(output_folder, site_id, config)

            print("OSPF configurations generated for all sites.")
        except Exception as e:
            print(f"Error generating configurations for all sites: {e}", file=sys.stderr)
            sys.exit(1)
    elif mode == 'single_ospf':
        try:
            with open(loopback_csv_file, 'rb') as file:
                result = chardet.detect(file.read())
                encoding = result['encoding']
            df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
            if site_id in df_loopback['SITE ID'].values:
                router_id = df_loopback[df_loopback['SITE ID'] == site_id]['Router ID'].values[0]
                loopback_configs = get_loopback_configs(loopback_csv_file, site_id)
                wan_configs = get_wan_configs(wan_csv_file, site_id)
                config = generate_ospf_config(router_id, loopback_configs, wan_configs)
                save_ospf_configs_to_file(output_folder, site_id, config)
                print(f"Single OSPF configuration generated for Site ID: {site_id}")
            else:
                print(f"Site ID {site_id} not found in the CSV file.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error generating configuration for single site: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Invalid mode specified. Use 'all' or 'single_ospf'.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

import os
import sys

import pandas as pd
import chardet

# Create input and output folders if they don't exist
def ensure_directories(input_folder, output_folder):
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)


# Function to generate BGP configuration for Client based on the provided template
def generate_bgp_config_client(asn, router_id, rr_service_loopback_ip, area_service_loopback_ip, neighbor_asn, is_abr):
    if is_abr:
        config_template = f"""
configure terminal
router bgp {asn}
nei {rr_service_loopback_ip} remote-as {neighbor_asn}
nei {rr_service_loopback_ip} update-source {area_service_loopback_ip}
nei {rr_service_loopback_ip} timers holdtime 2400
address-family ipv4
no nei {rr_service_loopback_ip} activate
exit
address-family vpnv4
nei {rr_service_loopback_ip} activate
exit
address-family l2vpn
nei {rr_service_loopback_ip} activate
exit
address-family ipv4-label-unicast
nei {rr_service_loopback_ip} activate
nei {rr_service_loopback_ip} route-map Deny_DCN in
nei {rr_service_loopback_ip} route-reflector-client
nei {rr_service_loopback_ip} next-hop-self
exit
end
"""
    else:
        config_template = f"""
configure terminal
router bgp {asn}
nei {rr_service_loopback_ip} remote-as {neighbor_asn}
nei {rr_service_loopback_ip} update-source {area_service_loopback_ip}
nei {rr_service_loopback_ip} timers holdtime 2400
address-family ipv4
no nei {rr_service_loopback_ip} activate
exit
address-family vpnv4
nei {rr_service_loopback_ip} activate
exit
address-family l2vpn
nei {rr_service_loopback_ip} activate
exit
address-family ipv4-label-unicast
nei {rr_service_loopback_ip} activate
nei {rr_service_loopback_ip} route-map Deny_DCN in
exit
end
"""
    return config_template

# Function to generate BGP configuration for RR based on the provided template
def generate_bgp_config_rr(asn, router_id, client_service_loopback_ip, area_service_loopback_ip, neighbor_asn):
    config_template = f"""
configure terminal
router bgp {asn}
nei {client_service_loopback_ip} remote-as {neighbor_asn}
nei {client_service_loopback_ip} update-source {area_service_loopback_ip}
nei {client_service_loopback_ip} timers holdtime 2400
address-family ipv4
no nei {client_service_loopback_ip} activate
exit
address-family vpnv4
nei {client_service_loopback_ip} activate
nei {client_service_loopback_ip} route-reflector-client
exit
address-family l2vpn
nei {client_service_loopback_ip} activate
nei {client_service_loopback_ip} route-reflector-client
exit
address-family ipv4-label-unicast
nei {client_service_loopback_ip} activate
nei {client_service_loopback_ip} route-reflector-client
nei {client_service_loopback_ip} next-hop-self
nei {client_service_loopback_ip} route-map Deny_DCN in
exit
end
"""
    return config_template

# Function to generate BGP configuration for RR to RR peer based on the provided template
def generate_bgp_config_rr_to_rr(asn, router_id, rr_peer_service_loopback_ip, area_service_loopback_ip, neighbor_asn):
    config_template = f"""
configure terminal
router bgp {asn}
nei {rr_peer_service_loopback_ip} remote-as {neighbor_asn}
nei {rr_peer_service_loopback_ip} update-source {area_service_loopback_ip}
nei {rr_peer_service_loopback_ip} timers holdtime 2400
address-family ipv4
no nei {rr_peer_service_loopback_ip} activate
exit
address-family vpnv4
nei {rr_peer_service_loopback_ip} activate
exit
address-family l2vpn
nei {rr_peer_service_loopback_ip} activate
exit
address-family ipv4-label-unicast
nei {rr_peer_service_loopback_ip} activate
nei {rr_peer_service_loopback_ip} route-map Deny_DCN in
nei {rr_peer_service_loopback_ip} route-reflector-client
nei {rr_peer_service_loopback_ip} next-hop-self
exit
end
"""
    return config_template

# Function to parse the Loopback IP Areas CSV and generate BGP configurations for a specific site ID
def generate_bgp_configs(loopback_csv_file, loopback_ip_areas_csv_file, site_id):
    configs = []
    with open(loopback_csv_file, 'rb') as file:
        result = chardet.detect(file.read())
        encoding = result['encoding']
    df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
    df_areas = pd.read_csv(loopback_ip_areas_csv_file)

    # Get router ID, ASN, and ABR status from loopback CSV
    router_info = df_loopback[df_loopback['SITE ID'] == site_id].iloc[0]
    router_id = router_info['Router ID']
    asn = router_info['ASN']
    is_abr = router_info['ABR/Non-ABR'] == 'ABR'

    client_rows = df_areas[(df_areas['Site ID'] == site_id) & (df_areas['BGP Role'] == 'Client') & (df_areas['Type'] == 'Service')]
    rr_rows = df_areas[(df_areas['Site ID'] == site_id) & (df_areas['BGP Role'] == 'RR') & (df_areas['Type'] == 'Service')]

    for index, client_row in client_rows.iterrows():
        area = client_row['Area']
        area_service_loopback_ip = client_row['IP Address']
        neighbor_asn = asn  # Assuming neighbor ASN is the same as the local ASN

        rr_in_area = df_areas[(df_areas['Area'] == area) & (df_areas['BGP Role'] == 'RR') & (df_areas['Type'] == 'Service')]
        for _, rr_row in rr_in_area.iterrows():
            rr_service_loopback_ip = rr_row['IP Address']
            config = generate_bgp_config_client(asn, router_id, rr_service_loopback_ip, area_service_loopback_ip, neighbor_asn, is_abr)
            configs.append(config)

    for index, rr_row in rr_rows.iterrows():
        area = rr_row['Area']
        area_service_loopback_ip = rr_row['IP Address']
        neighbor_asn = asn  # Assuming neighbor ASN is the same as the local ASN

        clients_in_area = df_areas[(df_areas['Area'] == area) & (df_areas['BGP Role'] == 'Client') & (df_areas['Type'] == 'Service')]
        for _, client_row in clients_in_area.iterrows():
            client_service_loopback_ip = client_row['IP Address']
            config = generate_bgp_config_rr(asn, router_id, client_service_loopback_ip, area_service_loopback_ip, neighbor_asn)
            configs.append(config)

        rr_peers_in_area = df_areas[(df_areas['Area'] == area) & (df_areas['BGP Role'] == 'RR') & (df_areas['Type'] == 'Service') & (df_areas['Router ID'] != router_id)]
        for _, rr_peer_row in rr_peers_in_area.iterrows():
            rr_peer_service_loopback_ip = rr_peer_row['IP Address']
            config = generate_bgp_config_rr_to_rr(asn, router_id, rr_peer_service_loopback_ip, area_service_loopback_ip, neighbor_asn)
            configs.append(config)

    return configs

# Function to save configurations to a text file
def save_bgp_configs_to_file(output_folder,site_id, configs):
    filename = os.path.join(output_folder,"OP_BGP_SERVICE", f"{site_id}_bgp_service_config.txt")
    with open(filename, 'w') as file:
        for config in configs:
            file.write(config)
    print(f"BGP configurations saved to {filename}")

# Main function to execute the script
def main():
    if len(sys.argv) != 5:
        print("Usage: python bgp_new.py <input_folder> <output_folder> <site_id> <all_or_single>")
        print(sys.argv)
        sys.exit(1)
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    site_id = sys.argv[3]
    mode = sys.argv[4]


    loopback_csv_file = os.path.join(input_folder,'IP_loopback', 'loopback.csv')  # Path to the Loopback CSV file
    loopback_ip_areas_csv_file = os.path.join(input_folder, 'IP_loopback','loopback_ip_areas.csv')  # Path to the Loopback IP Areas CSV file

    if mode == 'all':
        try:
            with open(loopback_csv_file, 'rb') as file:
                result = chardet.detect(file.read())
                encoding = result['encoding']
            df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
            site_ids = df_loopback['SITE ID'].unique()

            for site_id in site_ids:
                configs = generate_bgp_configs(loopback_csv_file, loopback_ip_areas_csv_file, site_id)
                save_bgp_configs_to_file(output_folder,site_id, configs)
            print("All configurations generated successfully.")
        except Exception as e:
            print(f"Error generatingsssss configurations for all sites: {e}", file=sys.stderr)
            sys.exit(1)

    if mode == 'single_bgp_service':
        try:
            with open(loopback_csv_file, 'rb') as file:
                result = chardet.detect(file.read())
                encoding = result['encoding']
            df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
            if site_id in df_loopback['SITE ID'].values:
                configs = generate_bgp_configs(loopback_csv_file, loopback_ip_areas_csv_file, site_id)
                save_bgp_configs_to_file(output_folder,site_id, configs)
                print(f"Single BGP configuration generated for Site ID: {site_id}")
                sys.exit(0)

            else:
                print(f"Site ID {site_id} not found in the CSV file.", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error generating configuration for single site: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()


import os
import sys
import pandas as pd
import chardet

def ensure_directories(input_folder, output_folder):
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

# Function to generate BGP configuration for Client based on the provided template
def generate_bgp_config_client(asn, router_id, rr_peer_area_management_ip, area_management_loopback_ip, neighbor_asn, is_abr, area_number, is_gw):
    nhs_up_or_gw = "NHS_Gw" if is_gw else "NHS_Up"
    config_template = f"""
configure terminal
router bgp {asn}
bgp router-id {router_id}
redistribute connected route-map cont
nei {rr_peer_area_management_ip} remote-as {neighbor_asn}
nei {rr_peer_area_management_ip} update-source {area_management_loopback_ip}
nei {rr_peer_area_management_ip} timers holdtime 2400
address-family ipv4
nei {rr_peer_area_management_ip} activate
nei {rr_peer_area_management_ip} route-map Deny_LU in
nei {rr_peer_area_management_ip} route-map {nhs_up_or_gw} out
exit
address-family vpnv4
exit
address-family l2vpn
exit
address-family ipv4-label-unicast
exit
bgp graceful-restart restart-time 2100 stalepath-time 2160
exit
end
"""
    return config_template

# Function to generate BGP configuration for Non-ABR Client based on the provided template
def generate_bgp_config_client_non_abr(asn, router_id, rr_peer_area_management_ip, area_management_loopback_ip, neighbor_asn):
    config_template = f"""
configure terminal
router bgp {asn}
bgp router-id {router_id}
redistribute connected route-map cont
nei {rr_peer_area_management_ip} remote-as {neighbor_asn}
nei {rr_peer_area_management_ip} update-source {area_management_loopback_ip}
nei {rr_peer_area_management_ip} timers holdtime 2400
address-family ipv4
nei {rr_peer_area_management_ip} activate
nei {rr_peer_area_management_ip} route-map Deny_LU in
exit
address-family vpnv4
exit
address-family l2vpn
exit
address-family ipv4-label-unicast
exit
bgp graceful-restart restart-time 2100 stalepath-time 2160
exit
end
"""
    return config_template

# Function to generate BGP configuration for RR based on the provided template
def generate_bgp_config_rr(asn, router_id, client_peer_area_management_ip, area_management_loopback_ip, neighbor_asn, area_number, is_gw, agg_area):
    nhs_down_or_gw = "NHS_Gw" if is_gw and area_number == agg_area else f"NHS_Down_A{int(area_number)}"
    config_template = f"""
configure terminal
router bgp {asn}
bgp router-id {router_id}
redistribute connected route-map cont
nei {client_peer_area_management_ip} remote-as {neighbor_asn}
nei {client_peer_area_management_ip} update-source {area_management_loopback_ip}
nei {client_peer_area_management_ip} timers holdtime 2400
address-family ipv4
nei {client_peer_area_management_ip} activate
nei {client_peer_area_management_ip} route-map Deny_LU in
nei {client_peer_area_management_ip} route-map {nhs_down_or_gw} out
nei {client_peer_area_management_ip} route-reflector-client
exit
address-family vpnv4
exit
address-family l2vpn
exit
address-family ipv4-label-unicast
exit
bgp graceful-restart restart-time 2100 stalepath-time 2160
exit
end
"""
    return config_template

# Updated function to generate BGP configuration for RR to RR peer based on the provided template
def generate_bgp_config_rr_to_rr(asn, router_id, rr_peer_area_management_loopback_ip, area_management_loopback_ip, neighbor_asn):
    config_template = f"""
configure terminal
router bgp {asn}
bgp router-id {router_id}
redistribute connected route-map cont
nei {rr_peer_area_management_loopback_ip} remote-as {neighbor_asn}
nei {rr_peer_area_management_loopback_ip} update-source {area_management_loopback_ip}
nei {rr_peer_area_management_loopback_ip} timers holdtime 2400
address-family ipv4
nei {rr_peer_area_management_loopback_ip} activate
nei {rr_peer_area_management_loopback_ip} route-map Deny_LU in
exit
address-family vpnv4
exit
address-family l2vpn
exit
address-family ipv4-label-unicast
exit
bgp graceful-restart restart-time 2100 stalepath-time 2160
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
    asn = int(router_info['ASN'])
    is_abr = router_info['ABR/Non-ABR'] == 'ABR'
    is_gw = router_info['GW'] == 'Yes'
    agg_area = int(router_info['Area ID - 1'])

    client_rows = df_areas[(df_areas['Site ID'] == site_id) & (df_areas['BGP Role'] == 'Client') & (df_areas['Type'] == 'Management')]
    rr_rows = df_areas[(df_areas['Site ID'] == site_id) & (df_areas['BGP Role'] == 'RR') & (df_areas['Type'] == 'Management')]

    for index, client_row in client_rows.iterrows():
        area = client_row['Area']
        area_management_loopback_ip = client_row['IP Address']
        neighbor_asn = asn  # Assuming neighbor ASN is the same as the local ASN

        rr_in_area = df_areas[(df_areas['Area'] == area) & (df_areas['BGP Role'] == 'RR') & (df_areas['Type'] == 'Management')]
        for _, rr_row in rr_in_area.iterrows():
            rr_peer_area_management_ip = rr_row['IP Address']
            if not is_abr:
                config = generate_bgp_config_client_non_abr(asn, router_id, rr_peer_area_management_ip, area_management_loopback_ip, neighbor_asn)
            else:
                config = generate_bgp_config_client(asn, router_id, rr_peer_area_management_ip, area_management_loopback_ip, neighbor_asn, is_abr, int(area), is_gw)
            configs.append(config)

    for index, rr_row in rr_rows.iterrows():
        area = rr_row['Area']
        area_management_loopback_ip = rr_row['IP Address']
        neighbor_asn = asn  # Assuming neighbor ASN is the same as the local ASN

        clients_in_area = df_areas[(df_areas['Area'] == area) & (df_areas['BGP Role'] == 'Client') & (df_areas['Type'] == 'Management')]
        for _, client_row in clients_in_area.iterrows():
            client_peer_area_management_ip = client_row['IP Address']
            config = generate_bgp_config_rr(asn, router_id, client_peer_area_management_ip, area_management_loopback_ip, neighbor_asn, int(area), is_gw, agg_area)
            configs.append(config)

        rr_peers_in_area = df_areas[(df_areas['Area'] == area) & (df_areas['BGP Role'] == 'RR') & (df_areas['Type'] == 'Management') & (df_areas['Router ID'] != router_id)]
        for _, rr_peer_row in rr_peers_in_area.iterrows():
            rr_peer_area_management_loopback_ip = rr_peer_row['IP Address']
            config = generate_bgp_config_rr_to_rr(asn, router_id, rr_peer_area_management_loopback_ip, area_management_loopback_ip, neighbor_asn)
            configs.append(config)

    return configs

# Function to save configurations to a text file
def save_bgp_configs_to_file(output_folder,site_id, configs):
    filename = os.path.join(output_folder,"OP_BGP", f"{site_id}_bgp_config.txt")
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
                # Generate BGP configurations for each site ID
                configs = generate_bgp_configs(loopback_csv_file, loopback_ip_areas_csv_file, site_id)
                # Save configurations to file
                save_bgp_configs_to_file(output_folder,site_id, configs)
            print("BGP configurations generated for all sites.")
        except Exception as e:
            print(f"Error generating configurations for all sites: {e}", file=sys.stderr)
            sys.exit(1)
    elif mode == 'single_bgp':
        try:
            with open(loopback_csv_file, 'rb') as file:
                result = chardet.detect(file.read())
                encoding = result['encoding']
            df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
            if site_id in df_loopback['SITE ID'].values:
                configs = generate_bgp_configs(loopback_csv_file, loopback_ip_areas_csv_file, site_id)
                # Save configurations to file
                save_bgp_configs_to_file(output_folder,site_id, configs)
                print(f"Single BGP configuration generated for Site ID: {site_id}")
            else:
                print(f"Site ID {site_id} not found in the CSV file.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error generating configuration for single site: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print("Invalid mode specified. Use 'all' or 'single_BGP_E'.", file=sys.stderr)
        sys.exit(1)





'''''

    # Ask if the user wants to generate configs for all sites or a specific site
    generate_for_all = input("Do you want to generate BGP configurations for all sites? (yes/no): ").strip().lower()

    if generate_for_all == 'yes':
        # Load the loopback CSV to get all site IDs
        with open(loopback_csv_file, 'rb') as file:
            result = chardet.detect(file.read())
            encoding = result['encoding']
        df_loopback = pd.read_csv(loopback_csv_file, encoding=encoding)
        site_ids = df_loopback['SITE ID'].unique()

        for site_id in site_ids:
            # Generate BGP configurations for each site ID
            configs = generate_bgp_configs(loopback_csv_file, loopback_ip_areas_csv_file, site_id)
            # Save configurations to file
            save_bgp_configs_to_file(site_id, configs)
    else:
        while True:

            # Ask for a specific site ID
            site_id = input("Enter the Site ID: ")
            # Generate BGP configurations for the specified site ID
            configs = generate_bgp_configs(loopback_csv_file, loopback_ip_areas_csv_file, site_id)
            # Save configurations to file
            save_bgp_configs_to_file(site_id, configs)

            # Ask user if they want to generate for another site ID
            another_site = input("Do you want to generate BGP configurations for another Site-ID? (yes/no): ").strip().lower()
            if another_site != 'yes':
                print("Exiting the script.")
                break

    print("BGP configuration generation completed.")
'''
if __name__ == "__main__":
    main()

import os
import sys
import traceback

import pandas as pd
import ast
import chardet
from flask import logging


def ensure_directories(input_folder, output_folder):
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

def generate_route_maps(site_id, asba, area_community_file, area_relations_file, loopback_csv_file, output_folder):
    try:# Load necessary CSV files
        with open(loopback_csv_file, 'rb') as file:
            result = chardet.detect(file.read())
            encoding = result['encoding']
        area_community_df = pd.read_csv(area_community_file)
        area_relations_df = pd.read_csv(area_relations_file)
        loopback_df = pd.read_csv(loopback_csv_file, encoding=encoding)

        # Filter the data for the specified site
        site_data = loopback_df[loopback_df['SITE ID'] == site_id]

        # Initialize output list for all configurations
        route_map_configs = []

        # 1. Deny_DCN Route Maps
        route_map_configs.append("config terminal")
        seq_num = 1
        for _, row in area_community_df.iterrows():
            area_number = int(row['Area Number'])
            community_number = int(row['Area Community Numbering'])
            route_map_configs.append(f"route-map Deny_DCN deny {seq_num}")
            route_map_configs.append(f"match community comm-num {asba}:{community_number}")
            route_map_configs.append("exit")
            seq_num += 1
        route_map_configs.append("end")
        route_map_configs.append("")

        # 2. Deny_LU Route Map
        route_map_configs.append("config terminal")
        route_map_configs.append("route-map Deny_LU")
        route_map_configs.append(f"match community comm-num {asba}:2")
        route_map_configs.append("exit")
        route_map_configs.append("end")
        route_map_configs.append("")

        # 3. Cont Route Map
        route_map_configs.append("config terminal")
        seq_num = 1
        for i in range(1, 5):
            area_column = f"Area ID - {i}"
            mgmt_ip_column = f"Management IP - Loopback {2 * i - 1}"
            svc_ip_column = f"Service IP - Loopback {2 * i}"

            if pd.notna(site_data.iloc[0][area_column]):
                area_number = int(site_data.iloc[0][area_column])
                mgmt_ip = site_data.iloc[0][mgmt_ip_column]
                svc_ip = site_data.iloc[0][svc_ip_column]

                community_number = int(area_community_df.loc[area_community_df[
                                                                 'Area Number'] == area_number, 'Area Community Numbering'].values[
                                           0])

                # Management Loopback
                route_map_configs.append(f"route-map cont {seq_num}")
                route_map_configs.append(f"match destination ip {mgmt_ip} 255.255.255.255")
                route_map_configs.append(f"set community comm-num {asba}:{community_number}")
                route_map_configs.append("exit")
                seq_num += 1

                # Service Loopback
                route_map_configs.append(f"route-map cont {seq_num}")
                route_map_configs.append(f"match destination ip {svc_ip} 255.255.255.255")
                route_map_configs.append(f"set community comm-num {asba}:2")
                route_map_configs.append("exit")
                seq_num += 1

        route_map_configs.append("end")
        route_map_configs.append("")

        # 4. GW/ABR Configuration
        if site_data.iloc[0]['GW'] == 'Yes':
            is_abr = site_data.iloc[0]['ABR/Non-ABR'] == 'ABR'
            agg_area = int(site_data.iloc[0]['Area ID - 1'])
            agg_mgmt_ip = site_data.iloc[0]['Management IP - Loopback 1']

            if not is_abr:
                # a.) GW is Non-ABR - NHS_Gw and extRoutes
                route_map_configs.append("config terminal")
                route_map_configs.append("route-map NHS_Gw")
                route_map_configs.append(f"match community comm-num {asba}:1")
                route_map_configs.append(f"set next-hop ip {agg_mgmt_ip}")
                route_map_configs.append("exit")
                route_map_configs.append("route-map NHS_Gw 10")
                route_map_configs.append("exit")
                route_map_configs.append("end")
                route_map_configs.append("")

                route_map_configs.append("config terminal")
                route_map_configs.append("route-map extRoutes")
                route_map_configs.append("match as-path filter 1")
                route_map_configs.append(f"set community comm-num {asba}:1")
                route_map_configs.append("exit")
                route_map_configs.append("end")
                route_map_configs.append("")
            else:
                # b.) GW is ABR - NHS_Gw, extRoutes, NHS_Down
                route_map_configs.append("config terminal")
                route_map_configs.append("route-map extRoutes")
                route_map_configs.append("match as-path filter 1")
                route_map_configs.append(f"set community comm-num {asba}:1")
                route_map_configs.append("exit")
                route_map_configs.append("end")
                route_map_configs.append("")

                # NHS_Gw
                route_map_configs.append("config terminal")
                route_map_configs.append("route-map NHS_Gw")
                route_map_configs.append(f"match community comm-num {asba}:1")
                route_map_configs.append(f"set next-hop ip {agg_mgmt_ip}")
                route_map_configs.append("exit")
                seq_num = 2

                for i in range(2, 5):
                    area_column = f"Area ID - {i}"

                    if pd.notna(site_data.iloc[0][area_column]):
                        area_number = int(site_data.iloc[0][area_column])
                        if area_number != agg_area:  # Skip the Agg Area
                            community_number = int(area_community_df.loc[area_community_df[
                                                                             'Area Number'] == area_number, 'Area Community Numbering'].values[
                                                       0])

                            route_map_configs.append(f"route-map NHS_Gw {seq_num}")
                            route_map_configs.append(f"match community comm-num {asba}:{community_number}")
                            route_map_configs.append(f"set next-hop ip {agg_mgmt_ip}")
                            route_map_configs.append("exit")
                            seq_num += 1

                            # Check if this area is a Pre-Agg area with access areas
                            access_areas = area_relations_df[area_relations_df['Pre-Agg Area'] == area_number][
                                'Access Areas']
                            if not access_areas.empty:
                                for access_area_str in access_areas.values:
                                    access_area_str = access_area_str.replace(' ', ',')
                                    access_area_list = ast.literal_eval(access_area_str)
                                    for access_area in access_area_list:
                                        access_community_number = int(area_community_df.loc[
                                                                          area_community_df['Area Number'] == int(
                                                                              access_area), 'Area Community Numbering'].values[
                                                                          0])
                                        route_map_configs.append(f"route-map NHS_Gw {seq_num}")
                                        route_map_configs.append(
                                            f"match community comm-num {asba}:{access_community_number}")
                                        route_map_configs.append(f"set next-hop ip {agg_mgmt_ip}")
                                        route_map_configs.append("exit")
                                        seq_num += 1

                route_map_configs.append("route-map NHS_Gw 10")
                route_map_configs.append("exit")
                route_map_configs.append("end")
                route_map_configs.append("")

                # NHS_Down_A{area number}
                for i in range(2, 5):
                    area_column = f"Area ID - {i}"
                    mgmt_ip_column = f"Management IP - Loopback {2 * i - 1}"

                    if pd.notna(site_data.iloc[0][area_column]):
                        area_number = int(site_data.iloc[0][area_column])
                        community_number = int(area_community_df.loc[area_community_df[
                                                                         'Area Number'] == area_number, 'Area Community Numbering'].values[
                                                   0])
                        access_areas = area_relations_df[area_relations_df['Pre-Agg Area'] == area_number]['Access Areas']

                        route_map_configs.append(f"config terminal")
                        route_map_configs.append(f"route-map NHS_Down_A{area_number}")
                        route_map_configs.append(f"match community comm-num {asba}:{community_number}")
                        route_map_configs.append("exit")

                        seq_num = 2
                        if not access_areas.empty:
                            for access_area_str in access_areas.values:
                                access_area_str = access_area_str.replace(' ', ',')
                                access_area_list = ast.literal_eval(access_area_str)
                                for access_area in access_area_list:
                                    access_community_number = int(area_community_df.loc[
                                                                      area_community_df['Area Number'] == int(
                                                                          access_area), 'Area Community Numbering'].values[
                                                                      0])
                                    route_map_configs.append(f"route-map NHS_Down_A{area_number} {seq_num}")
                                    route_map_configs.append(f"match community comm-num {asba}:{access_community_number}")
                                    route_map_configs.append("exit")
                                    seq_num += 1

                        nhs_mgmt_ip = site_data.iloc[0][mgmt_ip_column]
                        route_map_configs.append(f"route-map NHS_Down_A{area_number} 10")
                        route_map_configs.append(f"set next-hop ip {nhs_mgmt_ip}")
                        route_map_configs.append("exit")
                        route_map_configs.append("end")
                        route_map_configs.append("")

        else:
            # 5. Non-GW Configuration (for ABR and Non-ABR)
            if site_data.iloc[0]['ABR/Non-ABR'] == 'ABR':
                agg_area = int(site_data.iloc[0]['Area ID - 1'])
                agg_mgmt_ip = site_data.iloc[0]['Management IP - Loopback 1']

                # NHS_Up Rule
                route_map_configs.append("config terminal")
                seq_num = 1
                for i in range(1, 5):
                    area_column = f"Area ID - {i}"
                    if pd.notna(site_data.iloc[0][area_column]) and int(site_data.iloc[0][area_column]) != agg_area:
                        area_number = int(site_data.iloc[0][area_column])
                        community_number = int(area_community_df.loc[area_community_df[
                                                                         'Area Number'] == area_number, 'Area Community Numbering'].values[
                                                   0])
                        route_map_configs.append(f"route-map NHS_Up {seq_num}")
                        route_map_configs.append(f"match community comm-num {asba}:{community_number}")
                        route_map_configs.append(f"set next-hop ip {agg_mgmt_ip}")
                        route_map_configs.append("exit")
                        seq_num += 1
                        access_areas = area_relations_df.loc[
                            area_relations_df['Pre-Agg Area'] == area_number, 'Access Areas']
                        if not access_areas.empty:
                            for access_area_str in access_areas.values:
                                access_area_str = access_area_str.replace(' ', ',')
                                access_area_list = ast.literal_eval(access_area_str)
                                for access_area in access_area_list:
                                    access_community_number = int(area_community_df.loc[
                                                                      area_community_df['Area Number'] == int(
                                                                          access_area), 'Area Community Numbering'].values[
                                                                      0])
                                    route_map_configs.append(f"route-map NHS_Up {seq_num}")
                                    route_map_configs.append(f"match community comm-num {asba}:{access_community_number}")
                                    route_map_configs.append(f"set next-hop ip {agg_mgmt_ip}")
                                    route_map_configs.append("exit")
                                    seq_num += 1
                route_map_configs.append(f"route-map NHS_Up 10")
                route_map_configs.append("exit")
                route_map_configs.append("end\n")

                # NHS_Down_A Rules
                for i in range(1, 5):
                    area_column = f"Area ID - {i}"
                    if pd.notna(site_data.iloc[0][area_column]) and int(site_data.iloc[0][area_column]) != agg_area:
                        area_number = int(site_data.iloc[0][area_column])
                        mgmt_ip_column = f"Management IP - Loopback {2 * i - 1}"
                        mgmt_ip = site_data.iloc[0][mgmt_ip_column]
                        community_number = int(area_community_df.loc[area_community_df[
                                                                         'Area Number'] == area_number, 'Area Community Numbering'].values[
                                                   0])
                        route_map_configs.append("config terminal")
                        route_map_configs.append(f"route-map NHS_Down_A{area_number}")
                        route_map_configs.append(f"match community comm-num {asba}:{community_number}")
                        route_map_configs.append("exit")
                        seq_num = 2
                        access_areas = area_relations_df.loc[
                            area_relations_df['Pre-Agg Area'] == area_number, 'Access Areas']
                        if not access_areas.empty:
                            for access_area_str in access_areas.values:
                                access_area_str = access_area_str.replace(' ', ',')
                                access_area_list = ast.literal_eval(access_area_str)
                                for access_area in access_area_list:
                                    access_community_number = int(area_community_df.loc[
                                                                      area_community_df['Area Number'] == int(
                                                                          access_area), 'Area Community Numbering'].values[
                                                                      0])
                                    route_map_configs.append(f"route-map NHS_Down_A{area_number} {seq_num}")
                                    route_map_configs.append(f"match community comm-num {asba}:{access_community_number}")
                                    route_map_configs.append("exit")
                                    seq_num += 1

                        route_map_configs.append(f"route-map NHS_Down_A{area_number} 10")
                        route_map_configs.append(f"set next-hop ip {mgmt_ip}")
                        route_map_configs.append("exit")
                        route_map_configs.append("end\n")
            else:
                # Non-GW, Non-ABR: No further configurations required
                route_map_configs.append("end")

        # Write all configurations to a single file
        output_file = os.path.join(output_folder,'OP_route_Map',f'{site_id}_route_map.txt')
        with open(output_file, 'w') as f:
            f.write("\n".join(route_map_configs))
        print(f"Route-map configuration saved to {output_file}",file=sys.stdout)

    except Exception as e:
        print("Error",sys.stderr)
        logging.error("Error generating route map configurations: %s", traceback.format_exc())
        raise
if __name__ == "__main__":

    if len(sys.argv) < 7:
        print("Usage: route_map_new.py <input_dir> <user_dir> <output_dir> <user_id> <mode> <asba_number> [site_id]")
        sys.exit(1)

    input_folder = sys.argv[1]
    user_dir = sys.argv[2]
    output_folder = sys.argv[3]
    mode = sys.argv[5]
    asba_number = sys.argv[6]

    site_id = sys.argv[7] if len(sys.argv) > 7 else None

    ensure_directories(input_folder, output_folder)

    area_community_file = os.path.join(input_folder, 'IP_loopback', 'area_community_numbering.csv')
    area_relations_file = os.path.join(input_folder, 'IP_loopback', 'area_relations.csv')
    loopback_csv_file = os.path.join(input_folder, 'IP_loopback', 'loopback.csv')

    with open(loopback_csv_file, 'rb') as file:
        result = chardet.detect(file.read())
        encoding = result['encoding']
    loopback_df = pd.read_csv(loopback_csv_file, encoding=encoding)

    if mode == 'all':
        for site_id in loopback_df['SITE ID'].unique():
            generate_route_maps(site_id, asba_number, area_community_file, area_relations_file, loopback_csv_file,
                                output_folder)


    elif mode == 'single_route_map':
        try:
            if site_id is None:
                print("Error: Site ID must be provided in single_route_map mode.", file=sys.stderr)
                sys.exit(1)
            generate_route_maps(site_id, asba_number, area_community_file, area_relations_file, loopback_csv_file,
                                output_folder)
            print("Files Generated Successfully 'OP_Route_Map' directory",file=sys.stdout)
            sys.exit(0)
        except Exception as e:
            print(f"Error generating Loopback configuration for single site: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Invalid mode. Use 'all' or 'single_route_map'.", file=sys.stderr)
        sys.exit(1)
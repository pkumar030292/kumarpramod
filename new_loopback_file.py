import pandas as pd
import chardet

# Read the CSV file
loopback_csv_file = 'input/loopback.csv'
with open(loopback_csv_file, 'rb') as file:
    result = chardet.detect(file.read())
    encoding = result['encoding']
df = pd.read_csv(loopback_csv_file, encoding=encoding)

# Initialize a list to store the new data
new_data = []

# Iterate through each row in the dataframe
for index, row in df.iterrows():
    site_id = row['SITE ID']
    router_id = row['Router ID']
    
    # Process Area ID - 1
    if pd.notna(row['Area ID - 1']):
        area = row['Area ID - 1']
        bgp_role = row['BGP Role - 1']
        if pd.notna(row['Management IP - Loopback 1']):
            new_data.append([site_id, router_id, area, 'Management', 1, row['Management IP - Loopback 1'], bgp_role])
        if pd.notna(row['Service IP - Loopback 2']):
            new_data.append([site_id, router_id, area, 'Service', 2, row['Service IP - Loopback 2'], bgp_role])
    
    # Process Area ID - 2
    if pd.notna(row['Area ID - 2']):
        area = row['Area ID - 2']
        bgp_role = row['BGP Role - 2']
        if pd.notna(row['Management IP - Loopback 3']):
            new_data.append([site_id, router_id, area, 'Management', 3, row['Management IP - Loopback 3'], bgp_role])
        if pd.notna(row['Service IP - Loopback 4']):
            new_data.append([site_id, router_id, area, 'Service', 4, row['Service IP - Loopback 4'], bgp_role])
    
    # Process Area ID - 3
    if pd.notna(row['Area ID - 3']):
        area = row['Area ID - 3']
        bgp_role = row['BGP Role - 3']
        if pd.notna(row['Management IP - Loopback 5']):
            new_data.append([site_id, router_id, area, 'Management', 5, row['Management IP - Loopback 5'], bgp_role])
        if pd.notna(row['Service IP - Loopback 6']):
            new_data.append([site_id, router_id, area, 'Service', 6, row['Service IP - Loopback 6'], bgp_role])
    
    # Process Area ID - 4
    if pd.notna(row['Area ID - 4']):
        area = row['Area ID - 4']
        bgp_role = row['BGP Role - 4']
        if pd.notna(row['Management IP - Loopback 7']):
            new_data.append([site_id, router_id, area, 'Management', 7, row['Management IP - Loopback 7'], bgp_role])
        if pd.notna(row['Service IP - Loopback 8']):
            new_data.append([site_id, router_id, area, 'Service', 8, row['Service IP - Loopback 8'], bgp_role])

# Create a new dataframe with the extracted data
new_df = pd.DataFrame(new_data, columns=['Site ID', 'Router ID', 'Area', 'Type', 'Loopback Number', 'IP Address', 'BGP Role'])

# Save the new dataframe to a CSV file
output_file = 'input/loopback_ip_areas.csv'
new_df.to_csv(output_file, index=False)

print(new_df.head(10))
print(f"Total rows in new CSV: {len(new_df)}")
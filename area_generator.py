import os
from wepage_app_n import area_generate_configurations
import pandas as pd
import chardet
import sys

def ensure_directories(input_folder, output_folder):
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
def process_areas(input_folder, agg_ospf_area):
    # Load the input CSV file
    # Detect the file's encoding
    loopback_csv_path = os.path.join(input_folder,'IP_loopback', 'loopback.csv')
    with open(loopback_csv_path, 'rb') as file:
        result = chardet.detect(file.read())
        encoding = result['encoding']

    # Read the file using the detected encoding
    df = pd.read_csv(loopback_csv_path, encoding=encoding)
    
    #df = pd.read_csv(input_file)

    # Extract all unique areas from Area ID - 1, 2, 3, & 4 columns
    unique_areas = pd.concat([df['Area ID - 1'], df['Area ID - 2'], df['Area ID - 3'], df['Area ID - 4']]).dropna().unique()
    print(output_folder,"THIS IS OUTPUT FOLDER")
    # Save the unique areas into a CSV file named area_numbering.csv
    area_numbering_df = pd.DataFrame(unique_areas, columns=['Area Number'])
    area_numbering_df.to_csv(os.path.join(output_folder,'IP_loopback', 'area_numbering.csv'), index=False)

    # Filter Area ID - 1 column with Agg OSPF Area
    filtered_df = df[df['Area ID - 1'] == agg_ospf_area]

    # Find all areas in Area ID - 2, 3, & 4 columns in the filtered area
    pre_agg_areas = pd.concat([filtered_df['Area ID - 2'], filtered_df['Area ID - 3'], filtered_df['Area ID - 4']]).dropna().unique()

    # Initialize lists to store the hierarchical information
    area_hierarchy = []
    area_community_numbering = []

    # Assign Community Numbers and build the hierarchy
    for pre_agg_area in pre_agg_areas:
        # Filter for the Pre-Agg Area
        pre_agg_filtered_df = df[df['Area ID - 1'] == pre_agg_area]
        
        # Identify Access Areas within this Pre-Agg Area
        access_areas = pd.concat([pre_agg_filtered_df['Area ID - 2'], pre_agg_filtered_df['Area ID - 3'], pre_agg_filtered_df['Area ID - 4']]).dropna().unique()

        # Assign community numbering
        pre_agg_community_number = f"{agg_ospf_area:1d}{pre_agg_area:02.0f}00"
        area_community_numbering.append((pre_agg_area, pre_agg_community_number))
        
        # For the Pre-Agg area, start with the Agg area in the hierarchy
        area_hierarchy.append((agg_ospf_area, f"{agg_ospf_area:1d}0000", pre_agg_area, pre_agg_community_number, access_areas))
        
        for access_area in access_areas:
            # Access Area Community Numbering
            access_area_community_number = f"{agg_ospf_area:1d}{pre_agg_area:02.0f}{access_area:02.0f}"
            area_community_numbering.append((access_area, access_area_community_number))

    # Add the Agg Area itself to the numbering list
    agg_area_community_number = f"{agg_ospf_area:1d}0000"
    area_community_numbering.insert(0, (agg_ospf_area, agg_area_community_number))

    # Create DataFrames for Area Community Numbering and Area Relations
    area_community_numbering_df = pd.DataFrame(area_community_numbering, columns=['Area Number', 'Area Community Numbering'])
    area_hierarchy_df = pd.DataFrame(area_hierarchy, columns=['Agg Area', 'Agg Area Community Number', 'Pre-Agg Area', 'Pre-Agg Area Community Number', 'Access Areas'])

    # Save the results to CSV files
    # area_community_numbering_df.to_csv(output_folder,'area_community_numbering.csv', index=False)
    # area_hierarchy_df.to_csv(output_folder,'area_relations.csv', index=False)
    area_community_numbering_df.to_csv(os.path.join(output_folder,'IP_loopback', 'area_community_numbering.csv'), index=False)
    area_hierarchy_df.to_csv(os.path.join(output_folder,'IP_loopback','area_relations.csv'), index=False)


if __name__ == "__main__":
    # Define the input file path
    if len(sys.argv) != 5:
        print("Usage: python loopback_new.py <input_folder> <output_folder> <site_id> <all_or_single>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    site_id = sys.argv[3]
    mode = sys.argv[4]
    input_file = (input_folder,"loopback.csv")
    print(input_file,"hhhhhhhhhhhhhhhhhhhhhhhhhh")
    if len(sys.argv) != 5:
        print("Usage: area_generator.py <user_dir> <output_dir> <user_id> <area_number>")
        sys.exit(1)

    user_dir = sys.argv[1]
    output_dir = sys.argv[2]
    user_id = sys.argv[3]
    area_number = sys.argv[4]

    print(
        f"Received arguments: user_dir={user_dir}, output_dir={output_dir}, user_id={user_id}, area_number={area_number}")

    # Debug print to track the values before formatting
    try:
        # Example processing code
        print(f"Processing with area number: {area_number}")
        agg_ospf_area = int(area_number)  # int(input("Please enter the Agg OSPF Area number: "))

        # Process the areas and generate the required files
        process_areas(input_folder, agg_ospf_area)
        # Example of a correct formatting operation
        print("Area number: {}".format(area_number))  # Ensure correct type
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

   # Prompt the user to input the Agg OSPF Area number

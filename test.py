import argparse
import os


def generate_configuration_file(site_id, output_dir, filename):
    # Define the path for the new file
    file_path = os.path.join(output_dir, filename)

    # Create and write to the file
    with open(file_path, 'w') as file:
        file.write(f"Configuration for Site ID: {site_id}\n")
        # Add more configuration details as needed
        file.write("Details and configuration parameters...\n")

    print(f"Configuration file created at {file_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Configuration File.')
    parser.add_argument('site_id', type=str, help='The Site ID to process')
    parser.add_argument('output_dir', type=str, help='The directory to save the configuration file')
    parser.add_argument('filename', type=str, help='The filename for the configuration file')
    args = parser.parse_args()

    # Call the function with the provided arguments
    generate_configuration_file(args.site_id, args.output_dir, args.filename)

"""
create_rg.py

This script reads a JSON configuration file that defines Azure resource groups,
then creates or updates each resource group using the Azure SDK for Python.

Usage:
    python create_rg.py --input_file custom_input.json

Requirements:
    - Azure CLI logged in OR environment credentials set up
    - 'azure-identity' and 'azure-mgmt-resource' libraries installed
    - A valid JSON configuration file with the required structure
"""

# Import the needed credential and management objects from the libraries.
import json
import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

def main():
    """
    Main Loop
    """

    # Parse the command-line argument for a custom input file
    parser = argparse.ArgumentParser(
        description="Create Azure Resource Groups from a JSON config file.")
    parser.add_argument(
        '--input_file', type=str, required=True, help='Path to the input JSON file.')
    args = parser.parse_args()

    # Load the JSON configuration from the specified file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Output list to store result of each resource group operation
    output = []

    # Initialize credential using DefaultAzureCredential (supports CLI, env, etc.)
    credential = DefaultAzureCredential()

    # Iterate over each resource group defined in the input JSON
    for rg in config["resource_groups"]:
        subscription_id = rg["subscription_id"]
        rg_name = rg["resource_group"]
        location = rg["location"]

        # Create a Resource Management client for the current subscription
        resource_client = ResourceManagementClient(credential, subscription_id)

        try:
            # Attempt to create or update the resource group
            rg_result = resource_client.resource_groups.create_or_update(
                rg_name, { "location": location })

            result = {
                    "resource_group": rg_result.name,
                    "location": rg_result.location,
                    "status": "success"
                }
        except Exception as e:
            # Catch and store any errors that occur during creation
            result = {
                "resource_group": rg_name,
                "status": "failed",
                "reason": str(e)
                }

        # Append result to output list
        output.append(result)

    # Write the output to a file for logging and tracking
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()

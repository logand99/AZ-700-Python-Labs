"""
create_private_dns_zone.py

This script reads a JSON configuration file to create Azure Private DNS zones across specified
resource groups and subscriptions using the Azure SDK for Python.

Usage:
    python create_private_dns_zone.py --input_file custom_input.json

Requirements:
    - Azure CLI logged in OR environment credentials configured
    - 'azure-identity', 'azure-mgmt-resource', and 'azure-mgmt-privatedns' libraries installed
    - JSON file defining resource groups and private DNS zone configurations
"""

# Import the needed credential and management objects from the libraries.
import json
import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.privatedns import PrivateDnsManagementClient

def main():
    """
    Main Loop
    """

    # Set up argparse to allow flexible input
    parser = argparse.ArgumentParser(
        description="Create Azure Private DNS Zones from JSON config.")
    parser.add_argument(
        '--input_file', type=str, required=True, help='Path to the input JSON configuration file.')
    args = parser.parse_args()

    # Load configuration data from the specified file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Initialize Azure credentials
    credential = DefaultAzureCredential()
    output = []

    # Loop through private DNS zone definitions
    for zone in config['private_dns_zones']:
        try:
            rg_name = zone["resource_group"]
            zone_name = zone["private_zone_name"]

            # Loop over each Resource Group to find the right subscription ID
            for rg in config["resource_groups"]:
                if rg["resource_group"] == rg_name:
                    subscription_id = rg["subscription_id"]
                    break

            if not subscription_id:
                raise Exception(f"Subscription ID not found for resource group: {rg_name}")

            # Initialize Azure SDK clients for the given subscription
            resource_client = ResourceManagementClient(credential, subscription_id)
            private_dns_client = PrivateDnsManagementClient(credential, subscription_id)

            # Check if RG exists
            rg_exists = resource_client.resource_groups.check_existence(rg_name)

            if not rg_exists:
                result = {
                    "resource_group": rg_name,
                    "status": "failed",
                    "reason": "Resource group does not exist"
                }
                output.append(result)
                continue

            # Create or update the private DNS zone (location is always 'global')
            zone_result = private_dns_client.private_zones.begin_create_or_update(
                rg_name,
                zone_name,
                {
                    "location": "global"
                }
            ).result()

            result = {
                    "private_dns_zone_name": zone_result.name,
                    "resource_group": rg_name,
                    "location": zone_result.location,
                    "status": "success"
                }

        except Exception as e:
            # Capture error and report failure
            result = {
                "private_dns_zone_name": zone_name,
                "resource_group": rg_name,
                "status": "failed",
                "reason": str(e)
            }

        # Write results to output file
        output.append(result)

    # Write results to JSON file
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()

"""
create_public_ip.py

This script reads a JSON configuration file that defines an Azure Public
IP Address and deploys it to specified resource group.

Usage:
    python create_public_ip.py --input_file custom_input.json

Requirements:
    - Azure CLI logged in OR environment credentials configured
    - 'azure-identity', 'azure-mgmt-resource', and 'azure-mgmt-network' libraries installed
    - A valid JSON configuration file with the required structure
"""

# Import the needed credential and management objects from the libraries.
import json
import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import PublicIPAddressSku

def main():
    """
    Main Loop
    """

    # Set up argument parser for dynamic input file
    parser = argparse.ArgumentParser(
        description="Create Azure VNets from a JSON config file.")
    parser.add_argument(
        '--input_file', type=str, required=True, help='Path to the input JSON file.')
    args = parser.parse_args()

    # Load the input configuration JSON
    with open(args.input_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Prepare output list to capture status for each VNet
    output = []

    # Initialize credential object
    credential = DefaultAzureCredential()

    # Iterate through each VNet and its subnets
    for ip in config["public_ips"]:
        try:
            rg_name = ip["resource_group"]
            location = ip["location"]
            public_ip_name = ip["name"]
            version = ip["version"]
            allocation_method = ip["allocation_method"]
            sku = ip["sku"]
            tier = ip["tier"]

            # Loop over each Resource Group to find the right subscription ID
            for rg in config["resource_groups"]:
                if rg["resource_group"] == rg_name:
                    subscription_id = rg["subscription_id"]
                    break

            if not subscription_id:
                raise Exception(f"Subscription ID not found for resource group: {rg_name}")

            # Initialize management clients
            resource_client = ResourceManagementClient(credential, subscription_id)
            network_client = NetworkManagementClient(credential, subscription_id)

            # Check whether the resource group exists
            rg_exists = resource_client.resource_groups.check_existence(rg_name)

            if not rg_exists:
                result = {
                    "resource_group": rg_name,
                    "status": "failed",
                    "reason": "Resource group does not exist"
                }
                output.append(result)
                continue

            # Creatre or update the Public IP Address
            public_ip_result = network_client.public_ip_addresses.begin_create_or_update(
                rg_name,
                public_ip_name,
                {
                    "location": location,
                    "sku": PublicIPAddressSku(name=sku,tier=tier),
                    "public_ip_allocation_method": allocation_method,
                    "public_ip_address_version": version
                }
            ).result()

            result = {
                "public_ip_name": public_ip_result.name,
                "location": public_ip_result.location,
                "resource_group": rg_name,
                "status": "success"
            }

        except Exception as e:
            # Capture error and report failure
            result = {
                "public_ip_name": public_ip_name,
                "resource_group": rg_name,
                "status": "failed",
                "reason": str(e)
            }

        # Add result to the output list
        output.append(result)

    # Write results to JSON file
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()

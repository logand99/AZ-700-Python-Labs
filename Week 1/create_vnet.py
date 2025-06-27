"""
create_vnet.py

This script reads a JSON configuration file that defines Azure Virtual Networks (VNets)
and deploys them to specified resource groups across multiple subscriptions.

Usage:
    python create_vnet.py --input_file custom_input.json

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

    # Loop over each VNet configuration
    for vnet in config["vnets"]:
        try:
            rg_name = vnet["resource_group"]
            vnet_name = vnet["vnet_name"]
            address_space = vnet["address_space"]
            location = vnet["location"]

            # Loop over each Resource Group to find the right subscription ID
            for rg in config["resource_groups"]:
                if rg["resource_group"] == rg_name:
                    subscription_id = rg["subscription_id"]
                    break

            if not subscription_id:
                raise Exception(f"Subscription ID not found for resource group: {rg_name}")

            # Initialize clients for the current subscription
            resource_client = ResourceManagementClient(credential, subscription_id)
            network_client = NetworkManagementClient(credential, subscription_id)

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

            # Create or update the virtual network
            vnet_result = network_client.virtual_networks.begin_create_or_update(
                rg_name, 
                vnet_name, 
                {
                    "location": location,
                    "address_space": {"address_prefixes": [address_space]}
                }).result()

            result = {
                    "vnet_name": vnet_result.name,
                    "resource_group": rg_name,
                    "address_space": vnet_result.address_space.address_prefixes,
                    "location": vnet_result.location,
                    "status": "success"
                }

        except Exception as e:
            # Capture any exception as a failed operation
            result = {
                "vnet_name": vnet_name,
                "resource_group": rg_name,
                "status": "failed",
                "reason": str(e)
            }

        # Append result to output
        output.append(result)

    # Write results to JSON file
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()

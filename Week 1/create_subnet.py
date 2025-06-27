"""
create_subnets.py

This script reads a JSON configuration file to create subnets within existing Azure Virtual Networks (VNets),
using the Azure SDK for Python.

Usage:
    python create_subnets.py --input_file custom_input.json

Requirements:
    - Azure CLI logged in OR environment credentials configured
    - 'azure-identity', 'azure-mgmt-resource', and 'azure-mgmt-network' libraries installed
    - A valid JSON configuration file with VNets and subnets defined
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

    # Parse input JSON file via command line
    parser = argparse.ArgumentParser(
        description="Create Azure subnets from a JSON config file.")
    parser.add_argument(
        '--input_file', type=str, required=True, help='Path to the input JSON file.')
    args = parser.parse_args()

    # Load configuration data from input file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Prepare results list for output
    output = []

    # Initialize Azure credential
    credential = DefaultAzureCredential()

    # Iterate over VNets and their subnets
    for vnet in config["vnets"]:
        for subnet in vnet["subnets"]:
            try:
                rg_name = vnet["resource_group"]
                vnet_name = vnet["vnet_name"]
                subnet_name = subnet["subnet_name"]
                address_prefix = subnet["subnet_prefix"]

                # Loop over each Resource Group to find the right subscription ID
                for rg in config["resource_groups"]:
                    if rg["resource_group"] == rg_name:
                        subscription_id = rg["subscription_id"]
                        break

                if not subscription_id:
                    raise Exception(f"Subscription ID not found for resource group: {rg_name}")

                # Initialize resource and network clients for the subscription
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

                # Create or update the subnet
                subnet_result = network_client.subnets.begin_create_or_update(
                    rg_name,
                    vnet_name,
                    subnet_name,
                    {
                        "address_prefix": address_prefix
                    }
                ).result()

                result = {
                    "vnet_name": vnet_name,
                    "subnet_name": subnet_result.name,
                    "subnet_prefix": subnet_result.address_prefix,
                    "resource_group": rg_name,
                    "status": "success"
                }

            except Exception as e:
                # Capture error and report failure
                result = {
                    "vnet_name": vnet_name,
                    "subnet_name": subnet_name,
                    "resource_group": rg_name,
                    "status": "failed",
                    "reason": str(e)
                }

            # Save the result for this subnet
            output.append(result)

    # Write results to JSON file
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()

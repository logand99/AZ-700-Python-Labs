"""
update_subnet.py

This script reads a JSON configuration file that defines Azure Route Tables
and Network Security Groups (NSGs), and subnets. Then updates each subnets
to specified resource groups across multiple subscriptions.

Usage:
    python update_subnet.py --input_file custom_input.json

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

# Iterate through each VNet and its subnets
    for vnet in config["vnets"]:
        for subnet_config in vnet["subnets"]:
            try:
                rg_name = vnet["resource_group"]
                subnet_name = subnet_config["subnet_name"]
                vnet_name = vnet["vnet_name"]
                # Safely get NSG and Route Table names from subnet definition
                nsg_name = subnet_config.get("nsg_name")
                route_table_name = subnet_config.get("route_table_name")

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

                # Fetch existing subnet config
                subnet = network_client.subnets.get(rg_name, vnet_name, subnet_name)

                # Modify only the desired fields
                if nsg_name:
                    subnet.network_security_group = {
                        "id": f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}"
                            f"/providers/Microsoft.Network/networkSecurityGroups/{nsg_name}"
                    }

                if route_table_name:
                    subnet.route_table = {
                        "id": f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                            f"/providers/Microsoft.Network/routeTables/{route_table_name}"
                    }

                # Begin update without overwriting other fields
                subnet_result = network_client.subnets.begin_create_or_update(
                    rg_name,
                    vnet_name,
                    subnet_name,
                    subnet
                ).result()

                result = {
                    "subnet_name": subnet_result.name,
                    "vnet_name": vnet_name,
                    "resource_group": rg_name,
                    "status": "success"
                }

            except Exception as e:
                # Capture error and report failure
                result = {
                    "subnet_name": subnet_name,
                    "vnet_name": vnet_name,
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

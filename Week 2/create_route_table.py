"""
create_route_table.py

This script reads a JSON configuration file that defines Azure Route Tables
and deploys them to specified resource groups across multiple subscriptions.

Usage:
    python create_route_table.py --input_file custom_input.json

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
        for subnet in vnet["subnets"]:
            try:
                # Skip subnets that do not define Route Table configuration
                if "route_table_name" not in subnet and "routes" not in subnet:
                    continue

                rg_name = vnet["resource_group"]
                location = vnet["location"]
                route_table_name = subnet["route_table_name"]
                disable_bgp_propagation = subnet["disable_bgp_propagation"]
                route_list = []

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

                if "routes" in subnet:
                    for route in subnet["routes"]:
                        route_dict = {
                            "name": route["name"],
                            "address_prefix": route["address_prefix"],
                            "next_hop_type": route["next_hop_type"],
                            "next_hop_ip_address": route["next_hop_ip_address"]
                        }

                        route_list.append(route_dict)

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

                # Create or update the Route Table with Routes
                route_table_result = network_client.route_tables.begin_create_or_update(
                    rg_name,
                    route_table_name,
                    {
                        "location": location,
                        "routes": route_list,
                        "disable_bgp_route_propagation": disable_bgp_propagation
                    }
                ).result()

                result = {
                    "route_table_name": route_table_result.name,
                    "location": route_table_result.location,
                    "resource_group": rg_name,
                    "status": "success"
                }

            except Exception as e:
                # Capture error and report failure
                result = {
                    "route_table_name": route_table_name,
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

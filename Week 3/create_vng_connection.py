"""
create_vng_connection.py

This script reads a JSON configuration file that defines an Azure Virtual
Network Gateway and connections and deploys them to specified vnet and subnet.

Usage:
    python create_vng_connection.py --input_file custom_input.json

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
    for gateway in config["vpn_gateways"]:
        for connection in gateway["connections"]:
            try:
                rg_name = gateway["resource_group"]
                location = gateway["location"]
                connection_name = connection["name"]
                connection_type = connection["connection_type"]
                gateway_name = gateway["name"]
                remote_gateway = connection["local_gateway_name"]
                dpd_timeout = connection["dpd_timeout_seconds"]
                protocol_type = connection["protocol_type"]
                shared_key = connection["shared_key"]
                enable_bgp = connection["enable_bgp"]
                ip_sec_policies = []

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

                gateway_resource = network_client.virtual_network_gateways.get(
                    rg_name,
                    gateway_name
                )

                local_gateway_resource = network_client.local_network_gateways.get(
                    rg_name,
                    remote_gateway
                )

                for policy in connection["ip_sec_policies"]:
                    policy_dict = {
                        "sa_life_time_seconds": policy["sa_life_time_seconds"],
                        "sa_data_size_kilobytes": policy["sa_data_size_kilobytes"],
                        "ipsec_encryption": policy["ipsec_encryption"],
                        "ipsec_integrity": policy["ipsec_integrity"],
                        "ike_encryption": policy["ike_encryption"],
                        "ike_integrity": policy["ike_integrity"],
                        "dh_group": policy["dh_group"]
                    }

                    ip_sec_policies.append(policy_dict)

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

                # Create or update the Virtual Network Gateway
                vpn_connection_result = \
                    network_client.virtual_network_gateway_connections.begin_create_or_update(
                        rg_name,
                        connection_name,
                        {
                            "location": location,
                            "virtual_network_gateway1": gateway_resource,
                            "local_network_gateway2": local_gateway_resource,
                            "connection_type": connection_type,
                            "dpd_timeout_seconds": dpd_timeout,
                            "connection_protocol": protocol_type,
                            "shared_key": shared_key,
                            "enable_bgp": enable_bgp,
                            "ipsec_policies": ip_sec_policies
                        }
                    ).result()

                result = {
                    "vpn_connection_name": vpn_connection_result.name,
                    "resource_group": rg_name,
                    "status": "success"
                }

            except Exception as e:
                # Capture error and report failure
                result = {
                    "vpn_connection_name": connection_name,
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

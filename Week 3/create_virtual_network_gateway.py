"""
create_vpn_gateway.py

This script reads a JSON configuration file that defines an Azure Virtual
Network Gateway and deploys it to specified vnet and subnet.

Usage:
    python create_vpn_gateway.py --input_file custom_input.json

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
from azure.mgmt.network.models import VirtualNetworkGatewayIPConfiguration, VirtualNetworkGatewaySku, SubResource

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
        try:
            rg_name = gateway["resource_group"]
            location = gateway["location"]
            gateway_name = gateway["name"]
            gateway_type = gateway["gateway_type"]
            sku = gateway["sku"]
            vpn_type = gateway["vpn_type"]
            subnet = gateway["subnet_name"]
            vnet = gateway["vnet_name"]
            public_ip_name = gateway["public_ip_name"]
            enable_active_active = gateway["enable_active_active"]

            # Loop over each Resource Group to find the right subscription ID
            for rg in config["resource_groups"]:
                if rg["resource_group"] == rg_name:
                    subscription_id = rg["subscription_id"]
                    break

            if not subscription_id:
                raise Exception(f"Subscription ID not found for resource group: {rg_name}")

            subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}/providers/" \
                f"Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"

            public_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}/providers/" \
                f"Microsoft.Network/publicIPAddresses/{public_ip_name}"

            # Construct SubResource objects from raw ID strings
            subnet_resource = SubResource(id=subnet_id)
            public_ip_resource = SubResource(id=public_ip_id)

            # Construct IP configuration object
            ip_config = VirtualNetworkGatewayIPConfiguration(
                name="Default",
                subnet=subnet_resource,
                public_ip_address=public_ip_resource,
            )

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

            # Create or update the Virtual Network Gateway
            vpn_gateway_result = network_client.virtual_network_gateways.begin_create_or_update(
                rg_name,
                gateway_name,
                {
                    "location": location,
                    "ip_configurations": [ip_config],
                    "gateway_type": gateway_type,
                    "vpn_type": vpn_type,
                    "active": enable_active_active,
                    "sku": VirtualNetworkGatewaySku(name=sku,tier=sku)
                }
            ).result()

            result = {
                "vpn_gateway_name": vpn_gateway_result.name,
                "location": vpn_gateway_result.location,
                "resource_group": rg_name,
                "status": "success"
            }

        except Exception as e:
            # Capture error and report failure
            result = {
                "vpn_gateway_name": gateway_name,
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

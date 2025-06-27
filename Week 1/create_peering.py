"""
create_peerings.py

This script reads a JSON configuration file and creates virtual network (VNet) peerings
between Azure VNets across resource groups and subscriptions, based on defined settings.

Usage:
    python create_peerings.py --input_file custom_input.json

Requirements:
    - Azure CLI logged in OR environment credentials configured
    - 'azure-identity', 'azure-mgmt-resource', and 'azure-mgmt-network' libraries installed
    - JSON config with valid VNet and peering definitions
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

    # Argument parsing for custom input file
    parser = argparse.ArgumentParser(
        description="Create VNet peerings from a JSON config file.")
    parser.add_argument(
        '--input_file', type=str, required=True, help='Path to the input JSON file.')
    args = parser.parse_args()

    # Load configuration from input file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Initialize Azure credentials
    credential = DefaultAzureCredential()
    output = []

    # Loop through VNets to configure peering
    for vnet in config['vnets']:
        try:
            rg_name = vnet["resource_group"]
            vnet_name = vnet["vnet_name"]

            # Loop over each Resource Group to find the right subscription ID
            for rg in config["resource_groups"]:
                if rg["resource_group"] == rg_name:
                    subscription_id = rg["subscription_id"]
                    break

            if not subscription_id:
                raise Exception(f"Subscription ID not found for resource group: {rg_name}")

            # Initialize clients for the subscription
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

            # Iterate over defined peerings for the current VNet
            for peering in vnet['peerings']:
                peering_name = peering["peering_name"]
                settings = peering.get("peering_settings", {})
                remote_vnet_name = settings.get("remote_virtual_network")

                if not remote_vnet_name:
                    raise Exception(
                        f"No 'remote_virtual_network' specified in peering: {peering_name}")

                # Find remote VNet and resource group
                for vnet in config['vnets']:
                    if vnet['vnet_name'] == remote_vnet_name:
                        remote_rg_name = vnet["resource_group"]
                        break

                if not remote_rg_name:
                    raise Exception(f"Remote Resource group does not exist")

                for rg in config["resource_groups"]:
                    if rg["resource_group"] == remote_rg_name:
                        remote_sub_id = rg["subscription_id"]

                if not remote_sub_id:
                    raise Exception(f"Remote Subscription ID does not exist")

                # Construct peering parameters
                peering_parameters = {
                    "remote_virtual_network": {
                        "id": f"/subscriptions/{remote_sub_id}/resourceGroups/{remote_rg_name}" \
                            f"/providers/Microsoft.Network/virtualNetworks/{remote_vnet_name}"
                    },
                    "allow_virtual_network_access": settings.get(
                        "allow_virtual_network_access", True),
                    "allow_forwarded_traffic": settings.get("allow_forwarded_traffic", False),
                    "allow_gateway_transit": settings.get("allow_gateway_transit", False),
                    "use_remote_gateways": settings.get("use_remote_gateways", False)
                }

                # Create or update the peering
                peering_result = network_client.virtual_network_peerings.begin_create_or_update(
                    rg_name,
                    vnet_name,
                    peering_name,
                    peering_parameters
                ).result()

                result = {
                        "peering_name": peering_result.name,
                        "resource_group": rg_name,
                        "status": "success"
                    }

        except Exception as e:
            # Capture error and report failure
            result = {
                "peering_name": peering_name,
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

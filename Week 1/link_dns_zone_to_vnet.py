"""
link_dns_zone_to_vnet.py

This script reads a JSON configuration file and links virtual networks (VNets) to Azure Private DNS Zones
across multiple subscriptions. It supports enabling or disabling auto-registration for each VNet.

Usage:
    python link_dns_zone_to_vnet.py --input_file custom_input.json

Requirements:
    - Azure CLI logged in OR environment credentials configured
    - 'azure-identity', 'azure-mgmt-resource', 'azure-mgmt-network', and 'azure-mgmt-privatedns' installed
    - JSON file defining resource groups, private DNS zones, and virtual network links
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

    # Accept custom input JSON file from command-line
    parser = argparse.ArgumentParser(
        description="Link VNets to Private DNS Zones from JSON config.")
    parser.add_argument(
        '--input_file', type=str, required=True, help='Path to the input JSON file.')
    args = parser.parse_args()

    # Load configuration
    with open(args.input_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Initialize Azure credential
    credential = DefaultAzureCredential()
    output = []

    # Loop through each private DNS zone to process its VNet links
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

            # Initialize SDK clients for this subscription
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

            # Process each virtual network link
            for link in zone["virtual_network_links"]:
                link_name = link["link_name"]
                vnet_name = link["vnet_name"]
                vnet_rg = link["vnet_resource_group"]
                registration_enabled = link["registration_enabled"]

                for rg in config["resource_groups"]:
                    if rg["resource_group"] == vnet_rg:
                        vnet_sub_id = rg["subscription_id"]
                        break

                if not vnet_sub_id:
                    raise Exception(f"Subscription ID not found for VNet resource group: {vnet_rg}")

                # Construct full VNet ID
                vnet_id = (
                        f"/subscriptions/{vnet_sub_id}/resourceGroups/{vnet_rg}/"
                        f"providers/Microsoft.Network/virtualNetworks/{vnet_name}"
                )

                # Define link parameters
                link_params = {
                    "location": "global",
                    "virtual_network": {"id": vnet_id},
                    "registration_enabled": registration_enabled
                }

                # Create or update the VNet link to the DNS zone
                link_result = private_dns_client.virtual_network_links.begin_create_or_update(
                    rg_name,
                    zone_name,
                    link_name,
                    link_params
                ).result()

                result = {
                        "virtual_network_link_name": link_result.name,
                        "resource_group": rg_name,
                        "location": link_result.location,
                        "status": "success"
                    }

        except Exception as e:
            # Capture error for this specific link
            result = {
                "virtual_network_link_name": link_name,
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

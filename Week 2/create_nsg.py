"""
create_nsgs.py

This script reads a JSON configuration file to
create Network Security Groups (NSGs) with defined rules

It supports multiple subscriptions and resource groups using Azure SDK for Python.

Usage:
    python create_nsgs.py --input_file custom_input.json

Requirements:
    - Azure CLI logged in OR environment credentials configured
    - 'azure-identity', 'azure-mgmt-resource', and 'azure-mgmt-network' libraries installed
    - A valid JSON configuration file with VNets, subnets, and NSG definitions
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

    # Set up argparse to accept custom input JSON file
    parser = argparse.ArgumentParser(
        description="Create NSGs and associate them with Azure subnets.")
    parser.add_argument(
        '--input_file', type=str, required=True, help='Path to the input JSON configuration file.')
    args = parser.parse_args()

    # Load configuration data
    with open(args.input_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Output list for results tracking
    output = []

    # Initialize Azure credential
    credential = DefaultAzureCredential()

    # Iterate through each VNet and its subnets
    for vnet in config["vnets"]:
        for subnet in vnet["subnets"]:
            try:
                # Skip subnets that do not define NSG configuration
                if "nsg_name" not in subnet and "nsg_rules" not in subnet:
                    continue

                rg_name = vnet["resource_group"]
                location = vnet["location"]
                nsg_name = subnet["nsg_name"]
                rule_list = []

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

                for rule in subnet["nsg_rules"]:
                    rule_dict = {
                        "name": rule["name"],
                        "description": rule["description"],
                        "direction": rule["direction"],
                        "priority": int(rule["priority"]),
                        "protocol": rule["protocol"],
                        "access": rule["action"]
                    }

                    # Normalize address/port prefixes
                    if rule["source_address_prefixes"] == ["*"]:
                        rule_dict["source_address_prefix"] = "*"
                    else:
                        rule_dict["source_address_prefixes"] = rule["source_address_prefixes"]

                    if rule["source_port_ranges"] == ["*"]:
                        rule_dict["source_port_range"] = "*"
                    else:
                        rule_dict["source_port_ranges"] = rule["source_port_ranges"]

                    if rule["destination_address_prefixes"] == ["*"]:
                        rule_dict["destination_address_prefix"] = "*"
                    else:
                        rule_dict[
                            "destination_address_prefixes"] = rule["destination_address_prefixes"]

                    if rule["destination_port_ranges"] == ["*"]:
                        rule_dict["destination_port_range"] = "*"
                    else:
                        rule_dict["destination_port_ranges"] = rule["destination_port_ranges"]

                    rule_list.append(rule_dict)

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

                # Create or update the NSG with rules
                nsg_result = network_client.network_security_groups.begin_create_or_update(
                    rg_name,
                    nsg_name,
                    {
                        "location": location,
                        "security_rules": rule_list
                    }
                ).result()

                result = {
                    "nsg_name": nsg_result.name,
                    "location": nsg_result.location,
                    "resource_group": rg_name,
                    "status": "success"
                }

            except Exception as e:
                # Capture error and report failure
                result = {
                    "nsg_name": nsg_name,
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

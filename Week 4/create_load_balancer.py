"""
create_load_balancer.py

This script reads a JSON configuration file that defines an Azure Load
Balancer and deploys it to specified vnet and subnet.

Usage:
    python create_load_balancer.py --input_file custom_input.json

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
from azure.mgmt.network.models import \
    SubResource, FrontendIPConfiguration, LoadBalancerSku, \
    BackendAddressPool, LoadBalancerBackendAddress, LoadBalancingRule, Probe, OutboundRule

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

    # Iterate through each load balancer
    for load_balancer in config["load_balancers"]:
        try:
            rg_name = load_balancer["resource_group"]
            location = load_balancer["location"]
            load_balancer_name = load_balancer["name"]
            load_balancer_type = load_balancer["type"]
            sku = load_balancer["sku"]
            tier = load_balancer["tier"]

            # Loop over each Resource Group to find the right subscription ID
            for rg in config["resource_groups"]:
                if rg["resource_group"] == rg_name:
                    subscription_id = rg["subscription_id"]
                    break

            if not subscription_id:
                raise Exception(f"Subscription ID not found for resource group: {rg_name}")

            # Public Global Load balancer
            if load_balancer_type == "public" and tier == "Global":
                public_ip_name = load_balancer["public_ip_name"]
                frontend_name = load_balancer["frontend_name"]

                public_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/" \
                    f"{rg_name}/providers/Microsoft.Network/publicIPAddresses/{public_ip_name}"

                # Construct SubResource objects from raw ID strings
                public_ip_resource = SubResource(id=public_ip_id)

                # Construct IP configuration object
                ip_config = FrontendIPConfiguration(
                    name=frontend_name,
                    public_ip_address=public_ip_resource
                )

                # Initialize management clients
                resource_client = ResourceManagementClient(credential, subscription_id)
                network_client = NetworkManagementClient(credential, subscription_id)

                # Contruct Backend Address Pool Object
                for backend_pool in load_balancer["backend_pools"]:
                    if not backend_pool:
                        break
                    backend_pool_name = backend_pool["name"]
                    backend_addresses = []
                    for backend_address in backend_pool["backend_addresses"]:
                        address_name = backend_address["name"]
                        backend_load_balancer_rg = backend_address["backend_load_balancer_rg"]
                        backend_load_balancer_name = backend_address["backend_load_balancer_name"]
                        backend_ip_address_config = backend_address[
                                                "backend_load_balancer_frontend_ip_name"]

                        # Loop over each Resource Group to find the right subscription ID
                        for rg in config["resource_groups"]:
                            if rg["resource_group"] == backend_load_balancer_rg:
                                backend_lb_subscription_id = rg["subscription_id"]
                                break

                        if not backend_lb_subscription_id:
                            raise Exception(f"Subscription ID not found for resource group: " \
                                f"{backend_load_balancer_rg}")

                        front_end_id = f"/subscriptions/{backend_lb_subscription_id}" \
                            f"/resourceGroups/{backend_load_balancer_rg}/providers/" \
                            f"Microsoft.Network/loadBalancers/{backend_load_balancer_name}" \
                                f"/frontendIPConfigurations/{backend_ip_address_config}"

                        # Construct SubResource objects from raw ID strings
                        front_end_resource = SubResource(id=front_end_id)

                        # Construct backend address configuration object
                        backend_address_config = LoadBalancerBackendAddress(
                            name=address_name,
                            load_balancer_frontend_ip_configuration=front_end_resource
                        )

                        # Add the config object to a list
                        backend_addresses.append(backend_address_config)

                    # Construct the backend pool configuration object
                    backend_pool_config = BackendAddressPool(
                        name=backend_pool_name,
                        load_balancer_backend_addresses=backend_addresses
                    )

                # Get the front end ip ID
                frontend_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/" \
                    f"{rg_name}/providers/Microsoft.Network/loadBalancers/" \
                    f"{load_balancer_name}/frontendIPConfigurations/{frontend_name}"

                # Get the backend pool ID
                backend_pool_id = f"/subscriptions/{subscription_id}/resourceGroups/" \
                    f"{rg_name}/providers/Microsoft.Network/loadBalancers/" \
                    f"{load_balancer_name}/backendAddressPools/{backend_pool_name}"

                # Construct the load balancing rule
                for rule in load_balancer["load_balancing_rules"]:
                    load_balancer_rule_name = rule["name"]
                    protocol = rule["protocol"]
                    load_distribution = rule["load_distribution"]
                    frontend_port = rule["frontend_port"]
                    backend_port = rule["backend_port"]
                    idle_timeout = rule["idle_timeout"]
                    floating_ip = rule["floating_ip"]

                    load_balancer_rule_config = LoadBalancingRule(
                        name=load_balancer_rule_name,
                        frontend_ip_configuration=SubResource(id=frontend_ip_id),
                        backend_address_pools=[SubResource(id=backend_pool_id)],
                        protocol=protocol,
                        load_distribution=load_distribution,
                        frontend_port=frontend_port,
                        backend_port=backend_port,
                        idle_timeout_in_minutes=idle_timeout,
                        enable_floating_ip=floating_ip,
                    )

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

                # Create or update the Load Balancer
                load_balancer_result = network_client.load_balancers.begin_create_or_update(
                    rg_name,
                    load_balancer_name,
                    {
                        "location": location,
                        "frontend_ip_configurations": [ip_config],
                        "backend_address_pools": [backend_pool_config],
                        "load_balancing_rules": [load_balancer_rule_config],
                        "sku": LoadBalancerSku(name=sku,tier=tier)
                    }
                ).result()

                # Update the backend pool with the correct back end load balancers
                backend_pool_result = \
                    network_client.load_balancer_backend_address_pools.begin_create_or_update(
                    rg_name,
                    load_balancer_name,
                    backend_pool_name,
                    {
                        "name": backend_pool_name,
                        "properties": {
                            "loadBalancerBackendAddresses": backend_addresses
                        }
                    }
                ).result()

                result = {
                    "load_balancer_name": load_balancer_result.name,
                    "location": load_balancer_result.location,
                    "resource_group": rg_name,
                    "status": "success"
                }

            # Public Regional load balancer
            elif load_balancer_type == "public" and tier == "Regional":
                public_ip_name = load_balancer["public_ip_name"]
                frontend_name = load_balancer["frontend_name"]

                public_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/" \
                    f"{rg_name}/providers/Microsoft.Network/publicIPAddresses/{public_ip_name}"

                # Construct SubResource objects from raw ID strings
                public_ip_resource = SubResource(id=public_ip_id)

                # Construct IP configuration object
                ip_config = FrontendIPConfiguration(
                    name=frontend_name,
                    public_ip_address=public_ip_resource
                )

                # Initialize management clients
                resource_client = ResourceManagementClient(credential, subscription_id)
                network_client = NetworkManagementClient(credential, subscription_id)

                # Contruct Backend Address Pool Object
                for backend_pool in load_balancer["backend_pools"]:
                    backend_pool_name = backend_pool["name"]
                    backend_addresses = []
                    for backend_address in backend_pool["backend_addresses"]:
                        address_name = backend_address["name"]
                        vnet = backend_address["vnet_name"]
                        subnet = backend_address["subnet_name"]
                        backend_ip_address = backend_address["ip_address"]

                        subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                            f"/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"

                        vnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                            f"/providers/Microsoft.Network/virtualNetworks/{vnet}"

                        # Construct SubResource objects from raw ID strings
                        subnet_resource = SubResource(id=subnet_id)
                        vnet_resource = SubResource(id=vnet_id)

                        # Construct backend address configuration object
                        backend_address_config = LoadBalancerBackendAddress(
                            name=address_name,
                            virtual_network=vnet_resource,
                            subnet=subnet_resource,
                            ip_address=backend_ip_address,
                        )

                        # Add the config object to a list
                        backend_addresses.append(backend_address_config)

                    # Construct backend pool configuration object
                    backend_pool_config = BackendAddressPool(
                        name=backend_pool_name,
                        load_balancer_backend_addresses=backend_addresses
                    )

                # Construct the health probe object
                for probe in load_balancer["health_probes"]:
                    probe_name = probe["name"]
                    protocol = probe["protocol"]
                    port = probe["port"]
                    interval = probe["interval"]

                    probe_config = Probe(
                        name=probe_name,
                        protocol=protocol,
                        port=port,
                        interval_in_seconds=interval
                    )

                # Get the frontend ip ID
                frontend_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                    f"/providers/Microsoft.Network/loadBalancers/{load_balancer_name}" \
                    f"/frontendIPConfigurations/{frontend_name}"

                # Get the backend pool ID
                backend_pool_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                    f"/providers/Microsoft.Network/loadBalancers/{load_balancer_name}" \
                    f"/backendAddressPools/{backend_pool_name}"

                health_probe_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                    f"/providers/Microsoft.Network/loadBalancers/{load_balancer_name}" \
                    f"/probes/{probe_name}"

                # Contruct the load balancing rule object
                for rule in load_balancer["load_balancing_rules"]:
                    load_balancer_rule_name = rule["name"]
                    protocol = rule["protocol"]
                    load_distribution = rule["load_distribution"]
                    frontend_port = rule["frontend_port"]
                    backend_port = rule["backend_port"]
                    idle_timeout = rule["idle_timeout"]
                    floating_ip = rule["floating_ip"]
                    tcp_reset = rule["tcp_reset"]
                    outbound_snat = rule["disable_outbound_snat"]

                    load_balancer_rule_config = LoadBalancingRule(
                        name=load_balancer_rule_name,
                        frontend_ip_configuration=SubResource(id=frontend_ip_id),
                        backend_address_pools=[SubResource(id=backend_pool_id)],
                        probe=SubResource(id=health_probe_id),
                        protocol=protocol,
                        load_distribution=load_distribution,
                        frontend_port=frontend_port,
                        backend_port=backend_port,
                        idle_timeout_in_minutes=idle_timeout,
                        enable_floating_ip=floating_ip,
                        enable_tcp_reset=tcp_reset,
                        disable_outbound_snat=outbound_snat
                    )

                # Create the outbound nat rule object
                for nat_rule in load_balancer["outbound_nat_rules"]:
                    nat_rule_name = nat_rule["name"]
                    outbound_ports = nat_rule["allocated_outbound_ports"]
                    protocol = nat_rule["protocol"]
                    tcp_reset = nat_rule["tcp_reset"]
                    idle_timeout = nat_rule["idle_timeout"]

                outbound_nat_rule_config = OutboundRule(
                    name=nat_rule_name,
                    allocated_outbound_ports=outbound_ports,
                    frontend_ip_configurations=[SubResource(id=frontend_ip_id)],
                    backend_address_pool=SubResource(id=backend_pool_id),
                    protocol=protocol,
                    enable_tcp_reset=tcp_reset,
                    idle_timeout_in_minutes=idle_timeout
                )

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

                # Create or update the Load Balancer
                load_balancer_result = network_client.load_balancers.begin_create_or_update(
                    rg_name,
                    load_balancer_name,
                    {
                        "location": location,
                        "frontend_ip_configurations": [ip_config],
                        "backend_address_pools": [backend_pool_config],
                        "probes": [probe_config],
                        "load_balancing_rules": [load_balancer_rule_config],
                        "outbound_rules": [outbound_nat_rule_config],
                        "sku": LoadBalancerSku(name=sku,tier=tier)
                    }
                ).result()

                # Update NICs to reference the backend pool
                for backend_address in backend_pool["backend_addresses"]:
                    ip_address = backend_address["ip_address"]

                    for nic in network_client.network_interfaces.list(rg_name):
                        for ip_config in nic.ip_configurations:
                            if ip_config.private_ip_address == ip_address:
                                ip_config.load_balancer_backend_address_pools = [
                                    SubResource(id=backend_pool_id)
                            ]

                                nic_params = {
                                    "location": nic.location,
                                    "ip_configurations": nic.ip_configurations,
                                }

                                # Update NIC with backend pool
                                nic_result = \
                                network_client.network_interfaces.begin_create_or_update(
                                    rg_name,
                                    nic.name,
                                    nic_params
                                ).result()

                result = {
                    "load_balancer_name": load_balancer_result.name,
                    "location": load_balancer_result.location,
                    "resource_group": rg_name,
                    "status": "success"
                }

            # Internal load balancer
            elif load_balancer_type == "private":
                subnet = load_balancer["subnet_name"]
                vnet = load_balancer["vnet_name"]
                frontend_ip_address = load_balancer["ip_address"]
                frontend_name = load_balancer["frontend_name"]
                allocation_method = load_balancer["private_ip_allocation_method"]

                subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                    f"/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"

                # Construct SubResource objects from raw ID strings
                subnet_resource = SubResource(id=subnet_id)

                # Construct IP configuration object
                ip_config = FrontendIPConfiguration(
                    name=frontend_name,
                    subnet=subnet_resource,
                    private_ip_allocation_method=allocation_method,
                    private_ip_address=frontend_ip_address
                )

                # Initialize management clients
                resource_client = ResourceManagementClient(credential, subscription_id)
                network_client = NetworkManagementClient(credential, subscription_id)

                # Contruct Backend Address Pool Object
                for backend_pool in load_balancer["backend_pools"]:
                    backend_pool_name = backend_pool["name"]
                    backend_addresses = []
                    for backend_address in backend_pool["backend_addresses"]:
                        address_name = backend_address["name"]
                        vnet = backend_address["vnet_name"]
                        subnet = backend_address["subnet_name"]
                        backend_ip_address = backend_address["ip_address"]

                        subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                            f"/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}"

                        vnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                            f"/providers/Microsoft.Network/virtualNetworks/{vnet}"

                        # Construct SubResource objects from raw ID strings
                        subnet_resource = SubResource(id=subnet_id)
                        vnet_resource = SubResource(id=vnet_id)

                        # Contruct the backend address config
                        backend_address_config = LoadBalancerBackendAddress(
                            name=address_name,
                            virtual_network=vnet_resource,
                            subnet=subnet_resource,
                            ip_address=backend_ip_address,
                        )

                        # Add the backend address config to a list
                        backend_addresses.append(backend_address_config)

                    # Construct the backend address pool
                    backend_pool_config = BackendAddressPool(
                        name=backend_pool_name,
                        load_balancer_backend_addresses=backend_addresses
                    )

                # Construct the health probe object
                for probe in load_balancer["health_probes"]:
                    probe_name = probe["name"]
                    protocol = probe["protocol"]
                    port = probe["port"]
                    interval = probe["interval"]

                    probe_config = Probe(
                        name=probe_name,
                        protocol=protocol,
                        port=port,
                        interval_in_seconds=interval
                    )

                # Get the frontend ip ID
                frontend_ip_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                    f"/providers/Microsoft.Network/loadBalancers/{load_balancer_name}" \
                    f"/frontendIPConfigurations/{frontend_name}"

                # Get the backend pool ID
                backend_pool_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                    f"/providers/Microsoft.Network/loadBalancers/{load_balancer_name}" \
                    f"/backendAddressPools/{backend_pool_name}"

                health_probe_id = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}" \
                    f"/providers/Microsoft.Network/loadBalancers/{load_balancer_name}" \
                    f"/probes/{probe_name}"

                # Contruct the load balancing rule object
                for rule in load_balancer["load_balancing_rules"]:
                    load_balancer_rule_name = rule["name"]
                    protocol = rule["protocol"]
                    load_distribution = rule["load_distribution"]
                    frontend_port = rule["frontend_port"]
                    backend_port = rule["backend_port"]
                    idle_timeout = rule["idle_timeout"]
                    floating_ip = rule["floating_ip"]
                    tcp_reset = rule["tcp_reset"]

                    load_balancer_rule_config = LoadBalancingRule(
                        name=load_balancer_rule_name,
                        frontend_ip_configuration=SubResource(id=frontend_ip_id),
                        backend_address_pools=[SubResource(id=backend_pool_id)],
                        probe=SubResource(id=health_probe_id),
                        protocol=protocol,
                        load_distribution=load_distribution,
                        frontend_port=frontend_port,
                        backend_port=backend_port,
                        idle_timeout_in_minutes=idle_timeout,
                        enable_floating_ip=floating_ip,
                        enable_tcp_reset=tcp_reset
                    )

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

                # Create or update the Load Balancer
                load_balancer_result = network_client.load_balancers.begin_create_or_update(
                    rg_name,
                    load_balancer_name,
                    {
                        "location": location,
                        "frontend_ip_configurations": [ip_config],
                        "backend_address_pools": [backend_pool_config],
                        "probes": [probe_config],
                        "load_balancing_rules": [load_balancer_rule_config],
                        "sku": LoadBalancerSku(name=sku,tier=tier)
                    }
                ).result()

                # Update NICs to reference the backend pool
                for backend_address in backend_pool["backend_addresses"]:
                    ip_address = backend_address["ip_address"]

                    for nic in network_client.network_interfaces.list(rg_name):
                        for ip_config in nic.ip_configurations:
                            if ip_config.private_ip_address == ip_address:
                                ip_config.load_balancer_backend_address_pools = [
                                    SubResource(id=backend_pool_id)
                            ]

                                nic_params = {
                                    "location": nic.location,
                                    "ip_configurations": nic.ip_configurations,
                                }

                                # Update NIC with backend pool
                                nic_result = \
                                    network_client.network_interfaces.begin_create_or_update(
                                    rg_name,
                                    nic.name,
                                    nic_params
                                ).result()

                result = {
                    "load_balancer_name": load_balancer_result.name,
                    "location": load_balancer_result.location,
                    "resource_group": rg_name,
                    "status": "success"
                }

        except Exception as e:
            # Capture error and report failure
            result = {
                "load_balancer_name": load_balancer_name,
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

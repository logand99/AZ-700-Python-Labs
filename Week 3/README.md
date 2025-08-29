# Azure Python Scripting Toolkit
## AZ-700 Prep - Week 3

> 📌 This is Week 3 of a 6-week AZ-700 study and scripting project. For context and previous work, see [Week 1](https://github.com/logand99/AZ-700-Python-Labs/tree/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%201)

This project automates the creation and configuration of core Azure networking components using Python and the Azure SDKs. It supports multi-subscription and multi-region deployments defined via a single JSON configuration file.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🔧 Features added this week

- Create Public IPs
- Create Virtual Network Gateways
- Create Local Network Gateways
- Create connections between local network gateways and Virtual Network Gateways
- Modular scripts – run individually or in sequence

---

## 📁 Prerequisites

- Python 3.8+
- Azure CLI authenticated (or other credential methods supported by `DefaultAzureCredential`)
- Azure SDK libraries installed:

```bash
pip install azure-identity azure-mgmt-resource azure-mgmt-network azure-mgmt-privatedns
```

## ▶️ Usage

Each script accepts a named JSON file using the --input_file argument:
```bash
python create_public_ip.py --input_file inputs.json
```

## 📜 Script Order (Initial Deployment)

You should run the scripts in order from Week 1 and Week 2 folders. After the initial deployment, they can be safely rerun independently as needed.
Before running these scripts, be sure that a GatewaySubnet has been defined and deployed using create_subnet.py from Week 1. This subnet is required for the Virtual Network Gateway to be created successfully.

1. [create_public_ip.py](https://github.com/logand99/AZ-700-Python-Labs/blob/bac6a465e0ca5ab81d0382a41e59a5e81b1501dc/Week%203/create_public_ip.py)\
   Deploys Public IPs. Configured via public_ips in the input JSON.

2. [create_virtual_network_gateway.py](https://github.com/logand99/AZ-700-Python-Labs/blob/bac6a465e0ca5ab81d0382a41e59a5e81b1501dc/Week%203/create_virtual_network_gateway.py)\
   Deploys VPN Gateways. Supports SKUs, VPN types, and active-active toggle.

3. [create_local_network_gateway.py](https://github.com/logand99/AZ-700-Python-Labs/blob/bac6a465e0ca5ab81d0382a41e59a5e81b1501dc/Week%203/create_local_network_gateway.py)\
   Represents your on-prem site with IP address and routed prefixes.

4. [create_vng_connection.py](https://github.com/logand99/AZ-700-Python-Labs/blob/5eedc264e1e07dd208158d5a733f22b5511ebc6e/Week%203/create_vng_connection.py)\
   Creates the VPN connection between your VNet gateway and local gateway.

## 🔄 Rerunning Scripts

All scripts are idempotent where possible:

- Re-running will update existing resources.
- Connections and Gateways will reflect latest config from inputs.json.

## 📂 Input File Format

All scripts read from a shared inputs.json. It must include:

- resource_groups: array of subscription, name, location
- vnets: each with name, address space, subnets, and peerings
- subnets: each may include an associated NSG, route table name, and security rules
- private_dns_zones: with registration-enabled VNet links
- public_ips: including names, skus, versions, etc.
- vpn_gateways: with all properties needed, and connections to local network gateways
- local_network_gateways: with on prem IP properties
- See [inputs-example.json](https://github.com/logand99/AZ-700-Python-Labs/blob/8c9be5141eb7b09eb38bd1cd0dad8c4349171b7d/Week%203/inputs-example.json) in this repo for an example.

## ✅ Output

Each script writes a result summary to output.json, including:

- Resource name
- Resource group
- Status (success / failed)
- Reason for any failures

## 🧑‍💻 Author

Logan Davis\
Network Administrator @ Dot Foods\
[LinkedIn](https://www.linkedin.com/in/logan-davis-991726237/)\
[Portfolio](https://logand99.com)


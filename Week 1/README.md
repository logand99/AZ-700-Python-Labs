# Azure Python Scripting Toolkit

This project automates the creation and configuration of core Azure networking components using Python and the Azure SDKs. It supports multi-subscription and multi-region deployments defined via a single JSON configuration file.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🔧 Features

- Deploy Resource Groups, VNets, Subnets
- Configure NSGs and associate with subnets
- Create VNet peerings
- Deploy Private DNS zones
- Link VNets to Private DNS zones
- JSON-driven deployment model for repeatability and control
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
python create_rg.py --input_file inputs.json
```

## 📜 Script Order (Initial Deployment)

You should run these scripts in the following order when setting up from scratch. After the initial deployment, they can be safely rerun independently as needed.

1. [create_rg.py](https://github.com/logand99/AZ-700-Python-Labs/blob/f5d1750a9f6c66d56c9f4f1ffb73e05af93e976b/Week%201/create_rg.py)\
   Creates all resource groups defined in the input file.

2. [create_vnet.py](https://github.com/logand99/AZ-700-Python-Labs/blob/f5d1750a9f6c66d56c9f4f1ffb73e05af93e976b/Week%201/create_vnet.py)\
   Deploys virtual networks with address spaces across specified regions.

3. [create_subnet.py](https://github.com/logand99/AZ-700-Python-Labs/blob/f5d1750a9f6c66d56c9f4f1ffb73e05af93e976b/Week%201/create_subnet.py)\
   Creates subnets within each VNet.

4. [create_nsg.py](https://github.com/logand99/AZ-700-Python-Labs/blob/f5d1750a9f6c66d56c9f4f1ffb73e05af93e976b/Week%201/create_nsg.py)\
   Creates Network Security Groups and attaches them to subnets. Rules are defined in the input JSON.

5. [create_peering.py](https://github.com/logand99/AZ-700-Python-Labs/blob/f5d1750a9f6c66d56c9f4f1ffb73e05af93e976b/Week%201/create_peering.py)\
   Establishes VNet peerings across defined virtual networks.

6. [create_private_dns_zone.py](https://github.com/logand99/AZ-700-Python-Labs/blob/f5d1750a9f6c66d56c9f4f1ffb73e05af93e976b/Week%201/create_private_dns_zone.py)\
   Deploys Private DNS zones in the appropriate resource groups.

7. [link_dns_zone_to_vnet.py](https://github.com/logand99/AZ-700-Python-Labs/blob/f5d1750a9f6c66d56c9f4f1ffb73e05af93e976b/Week%201/link_dns_zone_to_vnet.py)\
   Links VNets to Private DNS zones with optional auto-registration.

## 🔄 Rerunning Scripts

All scripts are idempotent where possible:

- Re-running will update existing resources.
- Subnets and NSGs will reflect latest config from inputs.json.
- DNS zone links and peerings will be updated if already present.
- Safe to run in any order after the initial deployment.

## 📂 Input File Format

All scripts read from a shared inputs.json. It must include:

- resource_groups: array of subscription, name, location
- vnets: each with name, address space, subnets, and peerings
- subnets: with optional NSG names and security rules
- private_dns_zones: with registration-enabled VNet links
- See [inputs-example.json](https://github.com/logand99/AZ-700-Python-Labs/blob/dde411d26f36abd7291484f657d8f61364246f9a/Week%201/inputs-example.json) in this repo for an example.

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

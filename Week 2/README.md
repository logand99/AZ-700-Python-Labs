# Azure Python Scripting Toolkit
## AZ-700 Prep - Week 2 

> 📌 This is Week 2 of a 6-week AZ-700 study and scripting project. For context and previous work, see [Week 1](https://github.com/logand99/AZ-700-Python-Labs/tree/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%201)

This project automates the creation and configuration of core Azure networking components using Python and the Azure SDKs. It supports multi-subscription and multi-region deployments defined via a single JSON configuration file.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🔧 Features added this week

- Deploy Route Tables
- Updated script for creating NSGs
- Associating route tables/NSGs to subnets
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
python create_route_table.py --input_file inputs.json
```

## 📜 Script Order (Initial Deployment)

You should run the scripts in order from Week 1 folder. After the initial deployment, they can be safely rerun independently as needed.
create_route_table and create_nsg can be run in any order.

1. [create_nsg.py](https://github.com/logand99/AZ-700-Python-Labs/blob/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%202/create_nsg.py)\
   Creates Network Security Groups. Rules are defined in the input JSON.

2. [create_route_table.py](https://github.com/logand99/AZ-700-Python-Labs/blob/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%202/create_route_table.py)\
   Creates Route Tables. Routes are defined in the input JSON.

3. [update_subnet.py](https://github.com/logand99/AZ-700-Python-Labs/blob/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%202/update_subnet.py)\
   Updates subnets within each VNet. This will associate their respective Route Tables and NSGs if they have them defined.

4. [delete_rg.py](https://github.com/logand99/AZ-700-Python-Labs/blob/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%202/delete_rg.py)\
   Recursively deletes resource groups defined in the input JSON.

## 🔄 Rerunning Scripts

All scripts are idempotent where possible:

- Re-running will update existing resources.
- Route Tables and NSGs will reflect latest config from inputs.json.
- If you create new subnets using the script from Week 1, be sure to re-run update_subnet.py to apply NSGs and route tables to those subnets.

## 📂 Input File Format

All scripts read from a shared inputs.json. It must include:

- resource_groups: array of subscription, name, location
- vnets: each with name, address space, subnets, and peerings
- subnets: each may include an associated NSG, route table name, and security rules
- private_dns_zones: with registration-enabled VNet links
- See [inputs-example.json](https://github.com/logand99/AZ-700-Python-Labs/blob/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%202/inputs-example.json) in this repo for an example.

## ✅ Output

Each script writes a result summary to output.json, including:

- Resource name
- Resource group
- Status (success / failed)
- Reason for any failures

## 📄 Additional Files

- **Ubuntu_NVA_Commands.md**  
  Contains commands needed to set up IP forwarding, NAT, and FRR for BGP on a Ubuntu VM.

## 🧑‍💻 Author

Logan Davis\
Network Administrator @ Dot Foods\
[LinkedIn](https://www.linkedin.com/in/logan-davis-991726237/)\
[Portfolio](https://logand99.com)

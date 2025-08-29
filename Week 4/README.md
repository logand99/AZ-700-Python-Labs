# Azure Python Scripting Toolkit
## AZ-700 Prep - Week 4

> 📌 This is Week 4 of a 6-week AZ-700 study and scripting project. For context and previous work, see [Week 1](https://github.com/logand99/AZ-700-Python-Labs/tree/a1abfbf74b02dae6407a4a39cf489f98a3533887/Week%201)

This project automates the creation and configuration of core Azure networking components using Python and the Azure SDKs. It supports multi-subscription and multi-region deployments defined via a single JSON configuration file.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🔧 Features added this week

- Create Public IPs for public load balancers from week 3
- Create Global and Regional Public Load Balancers
- Create internal load balancer
- Create adding appropriate vms to backend pools, and create load balancing rules with health probesModular scripts – run individually or in sequence

---

## 📁 Prerequisites

- Python 3.8+
- Azure CLI authenticated (or other credential methods supported by `DefaultAzureCredential`)
- Azure SDK libraries installed:

```bash
pip install azure-identity azure-mgmt-resource azure-mgmt-network azure-mgmt-privatedns
```

## ▶️ Usage

The script accepts a named JSON file using the --input_file argument:
```bash
python create_load_balancer.py --input_file inputs.json
```

## 📜 Script Order (Initial Deployment)

You should run the scripts in order from Week 1, 2, and 3 folders. After the initial deployment, they can be safely rerun independently as needed.
Before running this script, be sure that a subnet for the load balancer has been defined and deployed using create_subnet.py from Week 1. This subnet is required for the load balancer to be created successfully.

1. [create_load_balancer.py](https://github.com/logand99/AZ-700-Python-Labs/)\
   Deploys load balancers. Configured via load_balancers in the input JSON.

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
- load_balancers: with backend pools, load balancing rules, and health probes
- See [inputs-example.json](https://github.com/logand99/AZ-700-Python-Labs/) in this repo for an example.

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


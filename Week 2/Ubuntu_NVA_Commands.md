```bash
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

# Enable SNAT/MASQUERADE
```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

# Allow forwarding between interfaces
```bash
sudo iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o eth1 -m state --state RELATED,ESTABLISHED -j ACCEPT
```

# Install FRRouting
```bash
sudo apt install frr frr-pythontools -y
```

# Enable BGP
```bash
sudo nano /etc/frr/daemons
```

# Change bgpd to yes:
```bash
bgpd=yes
```

# Configure BGP peering and route map
```bash
sudo nano /etc/frr/frr.conf
```
# Add to the end of the file
```bash
router bgp 65010
 bgp router-id 10.1.0.4

 neighbor 10.0.2.4 remote-as 65515
 neighbor 10.0.2.5 remote-as 65515

 address-family ipv4 unicast
  network 0.0.0.0/0
  neighbor 10.0.2.4 route-map EXPORT-DEFAULT out
  neighbor 10.0.2.5 route-map EXPORT-DEFAULT out
  neighbor 10.0.2.4 activate
  neighbor 10.0.2.5 activate
 exit-address-family

route-map EXPORT-DEFAULT permit 10
 match ip address prefix-list DEFAULT

ip prefix-list DEFAULT seq 5 permit 0.0.0.0/0
```

# Enable and start frr
```bash
sudo systemctl enable frr
sudo systemctl restart frr
```

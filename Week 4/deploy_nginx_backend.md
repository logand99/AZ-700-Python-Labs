# Deploying NGINX Backend VMs for Azure Load Balancer Testing

This script installs and configures a basic NGINX web server on each backend VM to help validate Azure Load Balancer traffic distribution.

It serves a simple HTML page that displays:
- The VM hostname
- The VM’s internal IP address
- The current timestamp

---

## 📦 Script

```bash
sudo apt-get update
sudo apt-get install -y nginx

# Put a host-unique index page
sudo bash -c 'cat >/var/www/html/index.html <<EOF
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>LB Test</title></head>
  <body style="font-family: sans-serif;">
    <h1>$(hostname)</h1>
    <p>IP: $(hostname -I | awk '\''{print $1}'\'')</p>
    <p>Time: $(date -Is)</p>
  </body>
</html>
EOF'
```

# Make sure nginx is up
```bash
sudo systemctl enable --now nginx
```

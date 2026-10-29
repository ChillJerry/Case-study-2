#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# Install nftables, retrying if networking is not ready.
installed=false

for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if apt-get update && apt-get install -y nftables; then
    installed=true
    break
  fi

  sleep 15
done

if [ "$installed" != "true" ]; then
  echo "Failed to install nftables" >&2
  exit 1
fi

# Enable IPv4 packet forwarding.
cat > /etc/sysctl.d/99-innovatech-gateway.conf <<'EOF'
net.ipv4.ip_forward=1
EOF

sysctl --system


# Configure forwarding and NAT for private AWS subnets.
cat > /etc/nftables.conf <<'EOF'
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain forward {
        type filter hook forward priority filter; policy drop;

        ct state established,related accept

        # Private AWS instances can access external services.
        ip saddr { 10.20.10.0/24, 10.20.20.0/24 } ip daddr != { 10.20.0.0/16, 10.30.0.0/24 } accept

        # AWS private subnets can reach the on-premises network over WireGuard.
        oifname "wg0" ip saddr { 10.20.10.0/24, 10.20.20.0/24 } ip daddr 10.30.0.0/24 accept

        # On-premises systems can reach the approved AWS private subnets.
        iifname "wg0" ip saddr 10.30.0.0/24 ip daddr { 10.20.10.0/24, 10.20.20.0/24 } accept
    }
}

table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;

        # NAT internet-bound traffic but preserve original VPN source addresses.
        ip saddr { 10.20.10.0/24, 10.20.20.0/24 } ip daddr != { 10.20.0.0/16, 10.30.0.0/24 } masquerade
    }
}
EOF


# Validate and activate the firewall configuration.
nft -c -f /etc/nftables.conf

systemctl enable nftables
systemctl restart nftables

echo "Innovatech gateway routing initialized"

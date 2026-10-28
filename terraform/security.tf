
resource "aws_security_group" "monitoring" {
  name        = "${var.project_name}-monitoring-sg"
  description = "Security group for monitoring services"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-monitoring-sg"
  }
}

resource "aws_security_group" "soar" {
  name        = "${var.project_name}-soar-sg"
  description = "Security group for SOAR services"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-soar-sg"
  }
}

resource "aws_security_group" "gateway" {
  name        = "${var.project_name}-gateway-sg"
  description = "Security group for VPN gateway"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-gateway-sg"
  }
}

# Monitoring server ingress

resource "aws_vpc_security_group_ingress_rule" "grafana" {
  security_group_id = aws_security_group.monitoring.id
  cidr_ipv4         = var.onprem_cidr
  from_port         = 3000
  to_port           = 3000
  ip_protocol       = "tcp"
  description       = "Grafana access through VPN"
}

resource "aws_vpc_security_group_ingress_rule" "loki" {
  security_group_id = aws_security_group.monitoring.id
  cidr_ipv4         = var.onprem_cidr
  from_port         = 3100
  to_port           = 3100
  ip_protocol       = "tcp"
  description       = "Loki ingestion from on-premises systems"
}

# SOAR server ingress

resource "aws_vpc_security_group_ingress_rule" "soar_api" {
  security_group_id            = aws_security_group.soar.id
  referenced_security_group_id = aws_security_group.monitoring.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
  description                  = "SOAR API and metrics from monitoring server"
}

# VPN gateway ingress

resource "aws_vpc_security_group_ingress_rule" "wireguard" {
  security_group_id = aws_security_group.gateway.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 51820
  to_port           = 51820
  ip_protocol       = "udp"
  description       = "WireGuard VPN endpoint"
}

resource "aws_vpc_security_group_ingress_rule" "gateway_forwarding" {
  security_group_id = aws_security_group.gateway.id
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "-1"
  description       = "Forwarding from internal VPC networks"
}

# Outbound connectivity

resource "aws_vpc_security_group_egress_rule" "monitoring_outbound" {
  security_group_id = aws_security_group.monitoring.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Outbound traffic through configured routes"
}

resource "aws_vpc_security_group_egress_rule" "soar_outbound" {
  security_group_id = aws_security_group.soar.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Outbound traffic through configured routes"
}

resource "aws_vpc_security_group_egress_rule" "gateway_outbound" {
  security_group_id = aws_security_group.gateway.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "VPN and forwarded traffic"
}

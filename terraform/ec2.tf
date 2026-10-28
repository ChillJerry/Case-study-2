
# Ubuntu Server 24.04 LTS
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# Monitoring server
resource "aws_instance" "monitoring" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.monitoring_instance_type
  subnet_id              = aws_subnet.monitoring.id
  private_ip             = "10.20.10.10"
  vpc_security_group_ids = [aws_security_group.monitoring.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_management.name

  associate_public_ip_address = false

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_size           = 40
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  tags = {
    Name = "${var.project_name}-monitoring"
    Role = "monitoring"
  }
}

# SOAR server
resource "aws_instance" "soar" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.soar_instance_type
  subnet_id              = aws_subnet.soar.id
  private_ip             = "10.20.20.10"
  vpc_security_group_ids = [aws_security_group.soar.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_management.name

  associate_public_ip_address = false

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  tags = {
    Name = "${var.project_name}-soar"
    Role = "soar"
  }
}

# WireGuard VPN gateway
resource "aws_instance" "gateway" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.gateway_instance_type
  subnet_id              = aws_subnet.gateway.id
  private_ip             = "10.20.30.10"
  vpc_security_group_ids = [aws_security_group.gateway.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_management.name

  associate_public_ip_address = false
  source_dest_check           = false

  user_data = file("${path.module}/bootstrap/gateway.sh")

  credit_specification {
    cpu_credits = "standard"
  }

  root_block_device {
    volume_size           = 12
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  tags = {
    Name = "${var.project_name}-gateway"
    Role = "gateway"
  }
}

# Public IP for the VPN endpoint
resource "aws_eip" "gateway" {
  domain   = "vpc"
  instance = aws_instance.gateway.id

  depends_on = [aws_internet_gateway.main]

  tags = {
    Name = "${var.project_name}-gateway-eip"
  }
}

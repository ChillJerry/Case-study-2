
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_subnet" "monitoring" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.monitoring_subnet_cidr
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.project_name}-monitoring"
  }
}

resource "aws_subnet" "soar" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.soar_subnet_cidr
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.project_name}-soar"
  }
}

resource "aws_subnet" "gateway" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.gateway_subnet_cidr
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.project_name}-gateway"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_route_table" "gateway" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-gateway-rt"
  }
}

resource "aws_route" "gateway_internet" {
  route_table_id         = aws_route_table.gateway.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "gateway" {
  subnet_id      = aws_subnet.gateway.id
  route_table_id = aws_route_table.gateway.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-private-rt"
  }
}

resource "aws_route_table_association" "monitoring" {
  subnet_id      = aws_subnet.monitoring.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "soar" {
  subnet_id      = aws_subnet.soar.id
  route_table_id = aws_route_table.private.id
}

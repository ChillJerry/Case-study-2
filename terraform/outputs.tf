
output "vpc_id" {
  description = "ID of the infrastructure VPC"
  value       = aws_vpc.main.id
}

output "monitoring_subnet_id" {
  value = aws_subnet.monitoring.id
}

output "soar_subnet_id" {
  value = aws_subnet.soar.id
}

output "gateway_subnet_id" {
  value = aws_subnet.gateway.id
}

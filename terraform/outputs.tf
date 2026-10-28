
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

output "monitoring_private_ip" {
  value = aws_instance.monitoring.private_ip
}

output "soar_private_ip" {
  value = aws_instance.soar.private_ip
}

output "gateway_private_ip" {
  value = aws_instance.gateway.private_ip
}

output "gateway_public_ip" {
  value = aws_eip.gateway.public_ip
}


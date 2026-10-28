
variable "aws_region" {
  description = "AWS region for the infrastructure"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Prefix for AWS resource names"
  type        = string
  default     = "innovatech-cs2"
}

variable "vpc_cidr" {
  description = "CIDR range for the AWS VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "monitoring_subnet_cidr" {
  type    = string
  default = "10.20.10.0/24"
}

variable "soar_subnet_cidr" {
  type    = string
  default = "10.20.20.0/24"
}

variable "gateway_subnet_cidr" {
  type    = string
  default = "10.20.30.0/24"
}

variable "onprem_cidr" {
  description = "Simulated on-premises network range"
  type        = string
  default     = "10.30.0.0/24"
}

variable "monitoring_instance_type" {
  description = "EC2 instance type for monitoring services"
  type        = string
  default     = "t3.medium"
}

variable "soar_instance_type" {
  description = "EC2 instance type for the SOAR application"
  type        = string
  default     = "t3.small"
}

variable "gateway_instance_type" {
  description = "EC2 instance type for the WireGuard gateway"
  type        = string
  default     = "t3.micro"
}

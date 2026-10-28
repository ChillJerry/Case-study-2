terraform {
  backend "s3" {
    bucket       = "innovatech-cs2-tfstate-898534748807"
    key          = "infrastructure/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
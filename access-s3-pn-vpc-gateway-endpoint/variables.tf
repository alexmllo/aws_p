variable "prefix" {
  default = "main"
}

variable "region" {
  type = string
}

variable "project" {
  default = "access-s3-pn-vpc-gateway-endpoint"
}

variable "contact" {
  default = "amitjansllorach1@gmail.com"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "subnet_cidr_list" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "instance_type" {
  default = "t2.micro"
}

variable "keyPath" {
  type    = string
  default = ""
}

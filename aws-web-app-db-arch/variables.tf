variable "region" {
  type = string
}

variable "prefix" {
  default = "main"
}

variable "project" {
  default = "project3"
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

variable "instances_type" {
  default = "t2.micro"
}

variable "db_name" {
  description = "Name of the RDS database"
  type        = string
  default     = "mydatabase"
}

variable "db_username" {
  description = "Username for the RDS database"
  type        = string
  default     = "admin"
}

we are trying to access the S3 bucket (AWS Object storage service) from private and public EC2 instances.

Provision an EC2 bastion host, a private EC2 instance, S3 buckets, and an IAM role to access S3 buckets. 

__AWS infra Setup__
- One EC2 instance with public IP that has routes configured to reach the internet( via Internet Gateway).
- One EC2 instance without public IP, cannot access the internet.
- One S3 bucket.
- One VPC gateway endpoint that will allow private access to the S3 bucket from VPC.
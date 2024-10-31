# Create a bastion ec2 instance on a public subnet and a storage bucket

# 1. Security group with ingress SSH and egress HTTP and HTTPS
# SSH port to enable SSH connection to bastion instance. HTTP and HTTPS port to enable ec2 instance talk to s3 buckets via HTTP/HTTPS endpoints.

resource "aws_security_group" "bastion-SSH" {
  description = "allow ssh to ec2"
  name        = "${local.prefix}-ssh_bastion"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress = {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = local.common_tags
}

# bastion ec2 instance
resource "aws_instance" "bastion" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.bastion-SSH.id, ]
  key_name               = "ssh-key"
  iam_instance_profile   = aws_iam_instance_profile.bastion_profile.name
  availability_zone      = "${data.aws_region.current.name}a"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-bastion-ec2" })
  )

  connection {
    type        = "ssh"
    user        = "ec2-user"
    password    = ""
    private_key = file(var.keyPath)
    host        = self.public_ip
  }

  provisioner "file" {
    source      = "setup_script.sh"
    destination = "/tmp/setup_script.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /tmp/setup_script.sh",
      "bash /tmp/setup_script.sh"
    ]
  }
  depends_on = [aws_route.public_internet_access]
}

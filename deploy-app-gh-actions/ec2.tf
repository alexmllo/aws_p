resource "aws_instance" "private" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public.id
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  availability_zone      = "${var.region}a"
  vpc_security_group_ids = [aws_security_group.docker_on_ec2.id, ]
  key_name               = var.ssh_key

  user_data = <<EOF
                #!/bin/bash
                yum update -y
                yum install -y docker
                systemctl enable docker
                systemctl start docker
                usermod -a -G docker ec2-user

                EOF

  tags = {
    "Name" = "docker-ec2-instance"
  }
}

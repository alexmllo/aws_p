# creating role for bastion server to access s3
resource "aws_iam_role" "bastion_role" {
  name = "${local.prefix}-bastion_server"
  assume_role_policy = jsondecode({
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

# IAM policy for S3 access
resource "aws_iam_policy" "s3_access_policy" {
  name        = "EC2S3AccessPolicy"
  description = "Policy to allow EC2 instance to access S3 bucket"

  # Specify required S3 permission
  policy = <<EOF
{
    "Version":"2012-10-17",
    "Statement": [
    {
        "Effect": "Allow",
        "Action": [
            "s3:GetObject",
            "s3:ListBucket",
        ],
        "Resource": [
            "arn:aws:s3:::${aws_s3_bucket.s3.arn}/*",
            "arn:aws:s3:::${aws_s3_bucket.s3}"
        ]
    }
    ]
}
EOF
}

# Attach IAM policy with the IAM role
resource "aws_iam_role_policy_attachment" "bastion" {
  role       = aws_iam_role.bastion_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

# Create IAM instance profile to allow ec2 instance to assume the IAM role associated with the instance profile
resource "aws_iam_instance_profile" "bastion_profile" {
  name = "bastion-profile"
  role = aws_iam_role.bastion_role.name
}

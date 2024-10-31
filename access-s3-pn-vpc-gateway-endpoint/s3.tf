# S3 bucket that we will access from the ec2 instance
resource "aws_s3_bucket" "s3" {
  bucket = "${data.aws_caller_identity.current.account_id}-bastion-bucket"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-s3-bucket" })
  )
}

# Enable bucket versioning
resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket = aws_s3_bucket.s3.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "bucket_block" {
  bucket = aws_s3_bucket.s3.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

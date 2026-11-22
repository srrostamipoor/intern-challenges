output "bucket_name" {
  value       = aws_s3_bucket.assets.bucket
  description = "The S3 bucket name"
}

output "bucket_arn" {
  value       = aws_s3_bucket.assets.arn
  description = "The S3 bucket ARN"
}

output "security_group_id" {
  value       = aws_security_group.web.id
  description = "The security group ID"
}

output "bucket_name" {
  description = "The name of the S3 assets bucket"
  value       = aws_s3_bucket.static.bucket
}

output "bucket_arn" {
  description = "The ARN of the S3 assets bucket"
  value       = aws_s3_bucket.static.arn
}

output "security_group_id" {
  description = "The ID of the web security group"
  value       = aws_security_group.web.id
}

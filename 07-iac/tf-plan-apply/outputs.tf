output "bucket_name" {
  value = aws_s3_bucket.assets.bucket
}

output "security_group_id" {
  value = aws_security_group.web.id
}

variable "project_name" {
  type        = string
  description = "Name prefix for all resources"
}

variable "environment" {
  type        = string
  description = "dev, staging, or production"
}

variable "bucket_versioning" {
  type        = bool
  description = "Enable S3 versioning"
  default     = false
}

variable "allowed_ports" {
  type        = list(number)
  description = "List of ingress ports to open"
  default     = [80, 443]
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to all resources"
  default     = {}
}
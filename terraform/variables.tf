variable "aws_region" {
  description = "AWS region for the Lightsail instance."
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Lightsail availability zone to use."
  type        = string
  default     = "us-east-1a"
}

variable "project_name" {
  description = "Prefix used for Lightsail resource names."
  type        = string
  default     = "ssh-of-empires"
}

variable "blueprint_id" {
  description = "Lightsail blueprint identifier."
  type        = string
  default     = "ubuntu_24_04"
}

variable "bundle_id" {
  description = "Lightsail bundle identifier."
  type        = string
  default     = "nano_3_0"
}

variable "player_username" {
  description = "SSH username that will be forced into the game."
  type        = string
  default     = "player"
}

variable "game_port" {
  description = "SSH port exposed for the forced game login."
  type        = number
  default     = 2222
}

variable "website_domain" {
  description = "Domain name served by nginx for the public website."
  type        = string
  default     = "ssh-of-empires.juanmartinez.xyz"
}

variable "remote_game_dir" {
  description = "Directory where the game code will be installed on the instance."
  type        = string
  default     = "/opt/ssh-of-empires"
}

variable "remote_web_root" {
  description = "Directory served by nginx for the exported static website."
  type        = string
  default     = "/var/www/ssh-of-empires"
}

variable "game_allowed_cidrs" {
  description = "CIDR ranges allowed to connect to the public game SSH port."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "web_allowed_cidrs" {
  description = "CIDR ranges allowed to connect to the website on ports 80 and 443."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_https" {
  description = "Whether to obtain a Let's Encrypt certificate and serve the website on HTTPS."
  type        = bool
  default     = false
}

variable "letsencrypt_email" {
  description = "Email address used for Let's Encrypt registration and expiration notices."
  type        = string
  default     = ""
}

variable "artifact_url_ttl_seconds" {
  description = "Lifetime of the presigned artifact download URLs used by first-boot bootstrap."
  type        = number
  default     = 86400
}

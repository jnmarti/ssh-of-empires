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

variable "admin_username" {
  description = "Initial SSH username for the selected blueprint."
  type        = string
  default     = "ubuntu"
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
  description = "Domain name served by nginx for the static website."
  type        = string
  default     = "ssh-of-empires.juanmartinez.xyz"
}

variable "enable_https" {
  description = "Whether to provision a Let's Encrypt certificate and serve the website over HTTPS."
  type        = bool
  default     = false
}

variable "letsencrypt_email" {
  description = "Email address used for Let's Encrypt registration and expiry notices. Leave empty to register without email."
  type        = string
  default     = ""
}

variable "public_key_path" {
  description = "Path to the public key that should be authorized for both admin and player logins."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "private_key_path" {
  description = "Path to the private key matching public_key_path, used by Terraform for bootstrap SSH."
  type        = string
  default     = "~/.ssh/id_ed25519"
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

variable "ssh_allowed_cidrs" {
  description = "CIDR ranges allowed to connect to ports 22 and 2222."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "web_allowed_cidrs" {
  description = "CIDR ranges allowed to connect to the website on ports 80 and 443."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

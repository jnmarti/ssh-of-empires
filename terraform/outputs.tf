output "public_ip" {
  description = "Static public IPv4 address for the game instance."
  value       = aws_lightsail_static_ip.this.ip_address
}

output "player_ssh_command" {
  description = "SSH command for joining the game. The public player endpoint allows anonymous SSH access and forces the game shell."
  value       = "ssh -p ${var.game_port} -t ${var.player_username}@${var.website_domain}"
}

output "lightsail_console_note" {
  description = "Use the Lightsail browser-based SSH client for admin access. Terraform does not provision an admin key."
  value       = "Admin access is intended to go through the Lightsail console browser SSH client."
}

output "player_ssh_host_key_fingerprint" {
  description = "Stable ED25519 SSH host key fingerprint for the public game endpoint."
  value       = data.external.ssh_host_key.result.fingerprint
}

output "website_url" {
  description = "Public website URL served from the instance."
  value       = var.enable_https ? "https://${var.website_domain}" : "http://${var.website_domain}"
}

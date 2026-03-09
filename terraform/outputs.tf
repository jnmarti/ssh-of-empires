output "public_ip" {
  description = "Static public IPv4 address for the game instance."
  value       = aws_lightsail_static_ip.this.ip_address
}

output "player_ssh_command" {
  description = "SSH command for joining the game."
  value       = "ssh -p ${var.game_port} -t ${var.player_username}@${aws_lightsail_static_ip.this.ip_address}"
}

output "admin_ssh_command" {
  description = "SSH command for the admin account used by Terraform bootstrap."
  value       = "ssh -p 22 ${var.admin_username}@${aws_lightsail_static_ip.this.ip_address}"
}

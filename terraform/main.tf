provider "aws" {
  region = var.aws_region
}

locals {
  public_key         = trimspace(file(pathexpand(var.public_key_path)))
  private_key        = file(pathexpand(var.private_key_path))
  game_source        = "${path.module}/../aoe_terminal.py"
  website_source_dir = "${path.module}/../website"
  website_files = sort([
    for rel in fileset(local.website_source_dir, "**") : rel
    if length(regexall("^(node_modules|\\.next|out)(/|$)", rel)) == 0
  ])
  website_hash        = sha256(join("", [for rel in local.website_files : "${rel}:${filesha256("${local.website_source_dir}/${rel}")}"]))
  shell_template      = "${path.module}/templates/player_ssh_game_shell.sh.tftpl"
  sshd_template       = "${path.module}/templates/sshd_terminal_empires.conf.tftpl"
  nginx_http_template = "${path.module}/templates/ssh_of_empires_site_http.conf.tftpl"
  nginx_template      = "${path.module}/templates/ssh_of_empires_site.conf.tftpl"
  instance_name       = "${var.project_name}-instance"
  static_ip_name      = "${var.project_name}-ip"
  key_pair_name       = "${var.project_name}-key"
  game_shell_path     = "${var.remote_game_dir}/ssh_game_shell.sh"
}

resource "aws_lightsail_key_pair" "this" {
  name       = local.key_pair_name
  public_key = local.public_key
}

resource "aws_lightsail_instance" "this" {
  name              = local.instance_name
  availability_zone = var.availability_zone
  blueprint_id      = var.blueprint_id
  bundle_id         = var.bundle_id
  key_pair_name     = aws_lightsail_key_pair.this.name
}

resource "aws_lightsail_static_ip" "this" {
  name = local.static_ip_name
}

resource "aws_lightsail_static_ip_attachment" "this" {
  static_ip_name = aws_lightsail_static_ip.this.name
  instance_name  = aws_lightsail_instance.this.name
}

resource "aws_lightsail_instance_public_ports" "this" {
  instance_name = aws_lightsail_instance.this.name

  port_info {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidrs     = var.ssh_allowed_cidrs
  }

  port_info {
    from_port = var.game_port
    to_port   = var.game_port
    protocol  = "tcp"
    cidrs     = var.ssh_allowed_cidrs
  }

  port_info {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    cidrs     = var.web_allowed_cidrs
  }

  dynamic "port_info" {
    for_each = var.enable_https ? [1] : []
    content {
      from_port = 443
      to_port   = 443
      protocol  = "tcp"
      cidrs     = var.web_allowed_cidrs
    }
  }
}

resource "null_resource" "bootstrap" {
  depends_on = [
    aws_lightsail_static_ip_attachment.this,
    aws_lightsail_instance_public_ports.this,
  ]

  triggers = {
    instance_id       = aws_lightsail_instance.this.id
    game_hash         = filesha256(local.game_source)
    website_hash      = local.website_hash
    shell_hash        = filesha256(local.shell_template)
    sshd_hash         = filesha256(local.sshd_template)
    nginx_http_hash   = filesha256(local.nginx_http_template)
    nginx_hash        = filesha256(local.nginx_template)
    public_key        = sha256(local.public_key)
    game_port         = tostring(var.game_port)
    player_user       = var.player_username
    remote_game_dir   = var.remote_game_dir
    website_domain    = var.website_domain
    website_root      = var.remote_web_root
    enable_https      = tostring(var.enable_https)
    letsencrypt_email = var.letsencrypt_email
  }

  connection {
    type        = "ssh"
    host        = aws_lightsail_static_ip.this.ip_address
    user        = var.admin_username
    private_key = local.private_key
    timeout     = "15m"
  }

  provisioner "file" {
    source      = local.game_source
    destination = "/tmp/aoe_terminal.py"
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-lc"]
    command     = <<-EOT
      set -euo pipefail
      cd '${local.website_source_dir}'
      npm ci
      npm run build
      rm -f /tmp/ssh-of-empires-site-out.tgz
      COPYFILE_DISABLE=1 tar -czf /tmp/ssh-of-empires-site-out.tgz -C '${local.website_source_dir}/out' .
    EOT
  }

  provisioner "file" {
    source      = "/tmp/ssh-of-empires-site-out.tgz"
    destination = "/tmp/ssh-of-empires-site-out.tgz"
  }

  provisioner "file" {
    content = templatefile(local.shell_template, {
      game_dir = var.remote_game_dir
    })
    destination = "/tmp/ssh_game_shell.sh"
  }

  provisioner "file" {
    content = templatefile(local.sshd_template, {
      player_username = var.player_username
      game_port       = var.game_port
      game_shell_path = local.game_shell_path
    })
    destination = "/tmp/ssh-of-empires-sshd.conf"
  }

  provisioner "file" {
    content = templatefile(local.nginx_http_template, {
      website_domain = var.website_domain
      web_root       = var.remote_web_root
    })
    destination = "/tmp/ssh-of-empires-site-http.conf"
  }

  provisioner "file" {
    content = templatefile(local.nginx_template, {
      website_domain = var.website_domain
      web_root       = var.remote_web_root
    })
    destination = "/tmp/ssh-of-empires-site-https.conf"
  }

  provisioner "file" {
    content     = "${local.public_key}\n"
    destination = "/tmp/player_authorized_keys"
  }

  provisioner "file" {
    content     = <<-EOT
      #!/bin/sh
      systemctl reload nginx
    EOT
    destination = "/tmp/reload-nginx.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "set -eux",
      "if command -v cloud-init >/dev/null 2>&1; then sudo cloud-init status --wait || true; fi",
      "sudo dpkg --configure -a || true",
      "sudo apt-get install -f -y || true",
      "sudo apt-get update",
      "sudo apt-get install -y python3 nginx certbot",
      "sudo mkdir -p ${var.remote_game_dir}",
      "sudo rm -rf ${var.remote_web_root}",
      "sudo mkdir -p ${var.remote_web_root}",
      "sudo mv /tmp/aoe_terminal.py ${var.remote_game_dir}/aoe_terminal.py",
      "sudo tar -xzf /tmp/ssh-of-empires-site-out.tgz -C ${var.remote_web_root}",
      "sudo mv /tmp/ssh_game_shell.sh ${local.game_shell_path}",
      "sudo chmod 755 ${var.remote_game_dir}/aoe_terminal.py ${local.game_shell_path}",
      "id -u ${var.player_username} >/dev/null 2>&1 || sudo useradd -m -s /bin/bash ${var.player_username}",
      "sudo mkdir -p /home/${var.player_username}/.ssh",
      "sudo mv /tmp/player_authorized_keys /home/${var.player_username}/.ssh/authorized_keys",
      "sudo chown -R ${var.player_username}:${var.player_username} /home/${var.player_username}/.ssh",
      "sudo chmod 700 /home/${var.player_username}/.ssh",
      "sudo chmod 600 /home/${var.player_username}/.ssh/authorized_keys",
      "sudo install -m 0644 /tmp/ssh-of-empires-sshd.conf /etc/ssh/sshd_config.d/90-ssh-of-empires.conf",
      "sudo install -m 0644 /tmp/ssh-of-empires-site-http.conf /etc/nginx/sites-available/ssh-of-empires.conf",
      "sudo ln -sfn /etc/nginx/sites-available/ssh-of-empires.conf /etc/nginx/sites-enabled/ssh-of-empires.conf",
      "sudo rm -f /etc/nginx/sites-enabled/default",
      "sudo sshd -t",
      "sudo nginx -t",
      "if systemctl list-unit-files ssh.socket >/dev/null 2>&1; then sudo systemctl disable --now ssh.socket || true; fi",
      "sudo systemctl enable ssh || true",
      "sudo systemctl restart ssh",
      "sudo systemctl enable nginx",
      "sudo systemctl restart nginx",
      "if [ \"${var.enable_https}\" = \"true\" ]; then sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy && sudo install -m 0755 /tmp/reload-nginx.sh /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh && if [ -n \"${var.letsencrypt_email}\" ]; then sudo certbot certonly --webroot -w ${var.remote_web_root} -d ${var.website_domain} --non-interactive --agree-tos --email \"${var.letsencrypt_email}\" --keep-until-expiring; else sudo certbot certonly --webroot -w ${var.remote_web_root} -d ${var.website_domain} --non-interactive --agree-tos --register-unsafely-without-email --keep-until-expiring; fi && sudo install -m 0644 /tmp/ssh-of-empires-site-https.conf /etc/nginx/sites-available/ssh-of-empires.conf && sudo nginx -t && (sudo systemctl enable certbot.timer || true) && sudo systemctl restart nginx; fi",
    ]
  }
}

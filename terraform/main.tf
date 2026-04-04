provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
data "external" "ssh_host_key" {
  depends_on = [
    aws_s3_bucket.artifacts,
  ]

  program = ["python3", local.ensure_host_key_script]

  query = {
    bucket                 = aws_s3_bucket.artifacts.bucket
    region                 = var.aws_region
    private_key_path       = local.ssh_host_private_key_path
    public_key_path        = local.ssh_host_public_key_path
    private_key_object_key = local.ssh_host_private_object_key
    public_key_object_key  = local.ssh_host_public_object_key
  }
}

data "external" "artifact_urls" {
  depends_on = [
    aws_s3_object.game_source,
    aws_s3_object.ssh_host_private,
    aws_s3_object.ssh_host_public,
    aws_s3_object.website_bundle,
  ]

  program = ["python3", local.presign_script]

  query = {
    bucket               = aws_s3_bucket.artifacts.bucket
    region               = var.aws_region
    game_key             = aws_s3_object.game_source.key
    site_key             = aws_s3_object.website_bundle.key
    ssh_host_private_key = aws_s3_object.ssh_host_private.key
    ssh_host_public_key  = aws_s3_object.ssh_host_public.key
    expires_in           = tostring(var.artifact_url_ttl_seconds)
  }
}

locals {
  game_source                 = "${path.module}/../aoe_terminal.py"
  website_source_dir          = "${path.module}/../website"
  build_dir                   = "${path.module}/build"
  website_bundle_path         = "${local.build_dir}/ssh-of-empires-site-out.tgz"
  bootstrap_template          = "${path.module}/templates/bootstrap_instance.sh.tftpl"
  https_bootstrap_template    = "${path.module}/templates/enable_https.sh.tftpl"
  ensure_host_key_script      = "${path.module}/../scripts/ensure_ssh_host_key.py"
  presign_script              = "${path.module}/../scripts/presign_artifact_urls.py"
  shell_template              = "${path.module}/templates/player_ssh_game_shell.sh.tftpl"
  sshd_template               = "${path.module}/templates/sshd_terminal_empires.conf.tftpl"
  nginx_template              = "${path.module}/templates/ssh_of_empires_site.conf.tftpl"
  sanitized_project_name      = replace(lower(var.project_name), "/[^a-z0-9-]/", "-")
  artifact_bucket_name        = "${local.sanitized_project_name}-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  instance_name               = "${var.project_name}-instance"
  static_ip_name              = "${var.project_name}-ip"
  game_shell_path             = "${var.remote_game_dir}/ssh_game_shell.sh"
  ssh_host_private_key_path   = "${local.build_dir}/ssh_host_ed25519_key"
  ssh_host_public_key_path    = "${local.build_dir}/ssh_host_ed25519_key.pub"
  ssh_host_private_object_key = "secrets/ssh/host_keys/ed25519/private"
  ssh_host_public_object_key  = "secrets/ssh/host_keys/ed25519/public"
  website_cert_dir            = "/etc/letsencrypt/live/${var.website_domain}"
  website_cert_fullchain_path = "${local.website_cert_dir}/fullchain.pem"
  website_cert_key_path       = "${local.website_cert_dir}/privkey.pem"
  website_files = sort([
    for rel in fileset(local.website_source_dir, "**") : rel
    if length(regexall("^(node_modules|\\.next|out)(/|$)", rel)) == 0
  ])
  game_hash            = filesha256(local.game_source)
  website_hash         = sha256(join("", [for rel in local.website_files : "${rel}:${filesha256("${local.website_source_dir}/${rel}")}"]))
  shell_hash           = filesha256(local.shell_template)
  sshd_hash            = filesha256(local.sshd_template)
  nginx_hash           = filesha256(local.nginx_template)
  bootstrap_hash       = filesha256(local.bootstrap_template)
  https_bootstrap_hash = filesha256(local.https_bootstrap_template)
  presign_hash         = filesha256(local.presign_script)
  game_object_key      = "artifacts/game/${local.game_hash}/aoe_terminal.py"
  site_object_key      = "artifacts/site/${local.website_hash}/site.tgz"
}

resource "terraform_data" "website_bundle" {
  triggers_replace = [
    local.website_hash,
  ]

  provisioner "local-exec" {
    working_dir = path.module
    command     = "../scripts/build_website_bundle.sh '${local.website_bundle_path}'"
    interpreter = ["/bin/bash", "-lc"]
  }
}

resource "terraform_data" "deployment" {
  triggers_replace = {
    game_hash            = local.game_hash
    website_hash         = local.website_hash
    shell_hash           = local.shell_hash
    sshd_hash            = local.sshd_hash
    nginx_hash           = local.nginx_hash
    bootstrap_hash       = local.bootstrap_hash
    https_bootstrap_hash = local.https_bootstrap_hash
    presign_hash         = local.presign_hash
    game_port            = tostring(var.game_port)
    player_user          = var.player_username
    remote_game_dir      = var.remote_game_dir
    website_domain       = var.website_domain
    website_root         = var.remote_web_root
    enable_https         = tostring(var.enable_https)
    letsencrypt_email    = var.letsencrypt_email
  }
}

resource "aws_s3_bucket" "artifacts" {
  bucket        = local.artifact_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "game_source" {
  bucket       = aws_s3_bucket.artifacts.id
  key          = local.game_object_key
  source       = local.game_source
  content_type = "text/x-python"
}

resource "aws_s3_object" "ssh_host_private" {
  depends_on = [
    data.external.ssh_host_key,
  ]

  bucket       = aws_s3_bucket.artifacts.id
  key          = local.ssh_host_private_object_key
  source       = data.external.ssh_host_key.result.private_path
  content_type = "application/octet-stream"
}

resource "aws_s3_object" "ssh_host_public" {
  depends_on = [
    data.external.ssh_host_key,
  ]

  bucket       = aws_s3_bucket.artifacts.id
  key          = local.ssh_host_public_object_key
  source       = data.external.ssh_host_key.result.public_path
  content_type = "text/plain"
}

resource "aws_s3_object" "website_bundle" {
  depends_on = [
    terraform_data.website_bundle,
  ]

  bucket       = aws_s3_bucket.artifacts.id
  key          = local.site_object_key
  source       = local.website_bundle_path
  content_type = "application/gzip"
}

resource "aws_lightsail_instance" "this" {
  depends_on = [
    aws_s3_object.game_source,
    aws_s3_object.ssh_host_private,
    aws_s3_object.ssh_host_public,
    aws_s3_object.website_bundle,
  ]

  name              = local.instance_name
  availability_zone = var.availability_zone
  blueprint_id      = var.blueprint_id
  bundle_id         = var.bundle_id
  user_data = templatefile(local.bootstrap_template, {
    enable_https         = var.enable_https
    game_dir             = var.remote_game_dir
    game_shell_path      = local.game_shell_path
    game_source_url      = data.external.artifact_urls.result.game_url
    ssh_host_private_url = data.external.artifact_urls.result.ssh_host_private_url
    ssh_host_public_url  = data.external.artifact_urls.result.ssh_host_public_url
    site_bundle_url      = data.external.artifact_urls.result.site_url
    player_username      = var.player_username
    web_root             = var.remote_web_root
    enable_https_script = var.enable_https ? templatefile(local.https_bootstrap_template, {
      website_domain     = var.website_domain
      letsencrypt_email  = var.letsencrypt_email
      expected_public_ip = aws_lightsail_static_ip.this.ip_address
      web_root           = var.remote_web_root
      nginx_https_config = templatefile(local.nginx_template, {
        website_domain             = var.website_domain
        web_root                   = var.remote_web_root
        tls_enabled                = true
        certificate_fullchain_path = local.website_cert_fullchain_path
        certificate_key_path       = local.website_cert_key_path
      })
    }) : ""
    sshd_config = templatefile(local.sshd_template, {
      player_username   = var.player_username
      game_port         = var.game_port
      game_shell_path   = local.game_shell_path
      ssh_host_key_path = "/etc/ssh/ssh_host_ed25519_key"
    })
    nginx_http_config = templatefile(local.nginx_template, {
      website_domain             = var.website_domain
      web_root                   = var.remote_web_root
      tls_enabled                = false
      certificate_fullchain_path = ""
      certificate_key_path       = ""
    })
    game_shell = templatefile(local.shell_template, {
      game_dir        = var.remote_game_dir
      player_username = var.player_username
    })
  })

  lifecycle {
    precondition {
      condition     = !var.enable_https || trimspace(var.letsencrypt_email) != ""
      error_message = "letsencrypt_email must be set when enable_https is true."
    }

    replace_triggered_by = [
      terraform_data.deployment,
    ]
  }
}

resource "aws_lightsail_static_ip" "this" {
  name = local.static_ip_name
}

resource "aws_lightsail_static_ip_attachment" "this" {
  static_ip_name = aws_lightsail_static_ip.this.name
  instance_name  = aws_lightsail_instance.this.name

  lifecycle {
    replace_triggered_by = [
      aws_lightsail_instance.this,
    ]
  }
}

resource "aws_lightsail_instance_public_ports" "this" {
  instance_name = aws_lightsail_instance.this.name

  port_info {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidrs     = ["0.0.0.0/0"]
  }

  port_info {
    from_port = var.game_port
    to_port   = var.game_port
    protocol  = "tcp"
    cidrs     = var.game_allowed_cidrs
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

  lifecycle {
    replace_triggered_by = [
      aws_lightsail_instance.this,
    ]
  }
}

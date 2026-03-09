#!/bin/zsh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SSH_DIR="$REPO_DIR/ssh"
HOST_KEY="$SSH_DIR/host_ed25519_key"
AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"
CONFIG_FILE="$SSH_DIR/sshd_config"
LOCAL_PUBKEY="$HOME/.ssh/id_ed25519.pub"

mkdir -p "$SSH_DIR"

if [ ! -f "$HOST_KEY" ]; then
  ssh-keygen -q -t ed25519 -N '' -f "$HOST_KEY"
fi

if [ ! -f "$AUTHORIZED_KEYS" ]; then
  if [ -f "$LOCAL_PUBKEY" ]; then
    cp "$LOCAL_PUBKEY" "$AUTHORIZED_KEYS"
  else
    echo "No $AUTHORIZED_KEYS file found and no $LOCAL_PUBKEY available to seed it." >&2
    exit 1
  fi
fi

chmod 600 "$HOST_KEY" "$AUTHORIZED_KEYS"

cat > "$CONFIG_FILE" <<EOF
Port 2222
ListenAddress 0.0.0.0
Protocol 2
HostKey $HOST_KEY
PidFile $SSH_DIR/sshd.pid
AuthorizedKeysFile $AUTHORIZED_KEYS
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
UsePAM no
PubkeyAuthentication yes
PermitTTY yes
AllowTcpForwarding no
X11Forwarding no
PrintMotd no
StrictModes no
Subsystem sftp internal-sftp
AcceptEnv TERM LANG LC_*
ForceCommand $REPO_DIR/scripts/ssh_game_shell.sh
EOF

chmod 600 "$CONFIG_FILE"
exec /usr/sbin/sshd -D -e -f "$CONFIG_FILE"

#!/usr/bin/env bash
# Prépare un VPS neuf pour Hellofedge (spec 0001, règles d'exploitation).
# À lancer une seule fois, en root, sur Ubuntu 24.04 (Hetzner Cloud CX23) :
#   curl -fsSL <url de ce fichier> -o provision.sh && bash provision.sh "<clé SSH publique du déploiement>"
# On peut le relancer sans risque : chaque étape vérifie ce qui est déjà fait.
#
# Ce qu'il fait :
# - mises à jour automatiques de sécurité, horloge synchronisée (chrony) ;
# - pare feu : seulement SSH (22), HTTP (80) et HTTPS (443, TCP et UDP) ;
# - 2 Go de swap ;
# - Docker et Docker Compose (dépôt officiel Docker) ;
# - un utilisateur `deploy` (clé SSH seule, membre du groupe docker) pour GitHub Actions ;
# - le dossier /opt/hellofedge et la sauvegarde de la base chaque nuit (7 jours gardés).
# Aucun secret ici : le fichier .env est écrit au déploiement, depuis les secrets GitHub.

set -euo pipefail

DEPLOY_KEY="${1:-}"
APP_DIR=/opt/hellofedge
APP_UID=1000   # l'utilisateur `hellofedge` de l'image Docker

if [[ $EUID -ne 0 ]]; then
  echo "Arrêt : lance ce script en root (sudo bash provision.sh ...)." >&2
  exit 1
fi
if [[ -z "$DEPLOY_KEY" ]]; then
  echo "Arrêt : donne la clé SSH publique du déploiement en premier argument." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "==> Mises à jour du système"
apt-get update -q
apt-get upgrade -yq
apt-get install -yq ca-certificates curl gnupg ufw chrony unattended-upgrades openssh-server cron
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> Horloge (chrony) et fuseau UTC"
timedatectl set-timezone UTC
systemctl enable --now chrony

echo "==> Pare feu"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable

echo "==> Swap de 2 Go"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Docker"
if ! command -v docker >/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  # shellcheck source=/dev/null
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -yq docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi
systemctl enable --now docker

echo "==> Utilisateur deploy (clé SSH seule)"
if ! id deploy >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash deploy
fi
usermod -aG docker deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
echo "$DEPLOY_KEY" > /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys

echo "==> SSH : clés seulement, pas de mot de passe"
install -d -m 755 /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/10-hellofedge.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
systemctl reload ssh || systemctl reload sshd

echo "==> Dossier de l'application"
install -d -m 750 -o deploy -g deploy "$APP_DIR" "$APP_DIR/backups"
# Le rapport de mesure est écrit par le conteneur (utilisateur $APP_UID).
install -d -m 775 -o "$APP_UID" -g deploy "$APP_DIR/exemples"

echo "==> Sauvegarde de la base chaque nuit à 03h15 UTC"
cat > /etc/cron.d/hellofedge-backup <<EOF
15 3 * * * deploy $APP_DIR/backup.sh >> $APP_DIR/backups/backup.log 2>&1
EOF
chmod 644 /etc/cron.d/hellofedge-backup

echo
echo "VPS prêt. Prochaine étape : le premier déploiement par GitHub Actions (deploy/VPS.md)."

#!/usr/bin/env bash
set -euo pipefail

# ── Options ────────────────────────────────────────────────────────────────
DRY_RUN=false
DOMAIN="${OPENASBL_DOMAIN:-}"
PORT="${OPENASBL_PORT:-8000}"
CERTBOT_EMAIL="${OPENASBL_CERTBOT_EMAIL:-}"

usage() {
  cat <<'USAGE'
Usage : install-server.sh --domain <sous-domaine> [options]

  --domain <fqdn>    Domaine servi par l'application (ex : openasbl.example.be)
  --port <n>         Port local de Gunicorn (défaut : 8000)
  --email <adresse>  Active HTTPS via certbot avec cette adresse
  --dry-run          Affiche les actions sans les exécuter
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --domain) DOMAIN="${2:-}"; shift 2 ;;
    --domain=*) DOMAIN="${1#*=}"; shift ;;
    --port) PORT="${2:-}"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --email) CERTBOT_EMAIL="${2:-}"; shift 2 ;;
    --email=*) CERTBOT_EMAIL="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Option inconnue : $1" >&2; usage; exit 1 ;;
  esac
done

run() {
  if $DRY_RUN; then
    echo "  + $*"
  else
    "$@"
  fi
}

# ── Root requis (sauf en simulation) ───────────────────────────────────────
if ! $DRY_RUN && [[ "$(id -u)" != "0" ]]; then
  echo "Erreur : ce script doit être lancé en tant que root (ex : sudo bash)." >&2
  exit 1
fi

# ── Vérifications préliminaires ────────────────────────────────────────────
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Erreur : ce script requiert Linux (Ubuntu/Debian)." >&2; exit 1
fi
if ! command -v apt-get >/dev/null 2>&1; then
  echo "Erreur : apt-get introuvable. Ubuntu/Debian requis." >&2; exit 1
fi
if [[ -z "$DOMAIN" ]]; then
  echo "Erreur : --domain est obligatoire (le vhost ne doit pas capter le trafic" >&2
  echo "         des autres services hébergés sur la machine)." >&2
  usage >&2
  exit 1
fi

# ── Variables ──────────────────────────────────────────────────────────────
REPO_URL="https://github.com/yetouse/openasbl.git"
APP_DIR="${OPENASBL_APP_DIR:-/opt/openasbl}"
APP_USER="${OPENASBL_APP_USER:-openasbl}"
SERVICE_FILE="/etc/systemd/system/openasbl.service"
NGINX_FILE="/etc/nginx/sites-available/openasbl"

echo "==> Domaine : $DOMAIN — Gunicorn sur 127.0.0.1:$PORT"

# ── Paquets système ────────────────────────────────────────────────────────
PKGS=(
  git python3 python3-venv python3-pip nginx
  libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
  libffi-dev libcairo2 libglib2.0-0
  tesseract-ocr tesseract-ocr-fra
)
[[ -n "$CERTBOT_EMAIL" ]] && PKGS+=(certbot python3-certbot-nginx)

echo "==> Vérification des paquets système..."
MISSING=()
for pkg in "${PKGS[@]}"; do
  dpkg -s "$pkg" >/dev/null 2>&1 || MISSING+=("$pkg")
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "  À installer : ${MISSING[*]}"
  run apt-get update -qq
  run apt-get install -y "${MISSING[@]}"
else
  echo "  Tous les paquets sont déjà installés."
fi

# ── Utilisateur système ────────────────────────────────────────────────────
echo "==> Utilisateur système '$APP_USER'..."
if $DRY_RUN; then
  echo "  + useradd --system --no-create-home --shell /usr/sbin/nologin $APP_USER"
elif ! id -u "$APP_USER" >/dev/null 2>&1; then
  useradd --system --no-create-home --shell /usr/sbin/nologin "$APP_USER"
else
  echo "  Utilisateur $APP_USER existe déjà."
fi

# ── Clone / mise à jour ────────────────────────────────────────────────────
echo "==> Dépôt dans $APP_DIR..."
if [[ -d "$APP_DIR/.git" ]]; then
  run git -C "$APP_DIR" pull --ff-only
else
  run git clone "$REPO_URL" "$APP_DIR"
fi

# ── Environnement virtuel ──────────────────────────────────────────────────
echo "==> Environnement virtuel..."
if [[ ! -f "$APP_DIR/venv/bin/python" ]]; then
  run python3 -m venv "$APP_DIR/venv"
fi
run "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
run "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# ── Clé secrète (générée une seule fois, conservée aux mises à jour) ───────
echo "==> Clé secrète Django..."
SECRET_KEY=""
if [[ -f "$SERVICE_FILE" ]]; then
  SECRET_KEY="$(sed -n 's/^Environment="DJANGO_SECRET_KEY=\(.*\)"$/\1/p' "$SERVICE_FILE" || true)"
fi
if [[ -z "$SECRET_KEY" ]]; then
  SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
  echo "  Nouvelle clé générée."
else
  echo "  Clé existante conservée."
fi

# ── Répertoires et permissions ─────────────────────────────────────────────
run mkdir -p /var/log/openasbl
run chown "$APP_USER":www-data /var/log/openasbl
run chown -R "$APP_USER":www-data "$APP_DIR"
run chmod 750 "$APP_DIR"

# ── Migration et collectstatic ─────────────────────────────────────────────
echo "==> Migration et collecte des fichiers statiques..."
DJANGO_ENV=(
  "OPENASBL_RUNTIME_MODE=server"
  "DJANGO_DEBUG=False"
  "DJANGO_SECRET_KEY=$SECRET_KEY"
  "DJANGO_ALLOWED_HOSTS=$DOMAIN"
)
if $DRY_RUN; then
  echo "  + sudo -u $APP_USER env <config> $APP_DIR/venv/bin/python manage.py migrate --noinput"
  echo "  + sudo -u $APP_USER env <config> $APP_DIR/venv/bin/python manage.py collectstatic --noinput"
else
  sudo -u "$APP_USER" env "${DJANGO_ENV[@]}" \
    "$APP_DIR/venv/bin/python" "$APP_DIR/manage.py" migrate --noinput
  sudo -u "$APP_USER" env "${DJANGO_ENV[@]}" \
    "$APP_DIR/venv/bin/python" "$APP_DIR/manage.py" collectstatic --noinput
fi

# ── Fichiers de déploiement (rendu des gabarits) ──────────────────────────
echo "==> Service systemd et vhost nginx..."
if $DRY_RUN; then
  echo "  + rendu $APP_DIR/deploy/openasbl.service → $SERVICE_FILE (domaine, port, clé)"
  echo "  + rendu $APP_DIR/deploy/nginx-openasbl.conf → $NGINX_FILE (domaine, port)"
  echo "  + ln -sf $NGINX_FILE /etc/nginx/sites-enabled/openasbl"
else
  python3 - "$APP_DIR" "$SERVICE_FILE" "$NGINX_FILE" "$DOMAIN" "$PORT" "$SECRET_KEY" <<'PYEOF'
import os, sys

app_dir, service_file, nginx_file, domain, port, secret_key = sys.argv[1:7]

def render(src, dst, mapping, mode):
    with open(src, encoding="utf-8") as fh:
        content = fh.read()
    for key, value in mapping.items():
        content = content.replace(key, value)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(dst, mode)

render(
    os.path.join(app_dir, "deploy/openasbl.service"),
    service_file,
    {"__SECRET_KEY__": secret_key, "__DOMAIN__": domain, "__PORT__": port},
    0o600,  # la clé secrète ne doit être lisible que par root
)
render(
    os.path.join(app_dir, "deploy/nginx-openasbl.conf"),
    nginx_file,
    {"__DOMAIN__": domain, "__PORT__": port},
    0o644,
)
PYEOF
  ln -sf "$NGINX_FILE" /etc/nginx/sites-enabled/openasbl
fi

# ── Services ──────────────────────────────────────────────────────────────
echo "==> Activation des services..."
run systemctl daemon-reload
run systemctl enable openasbl
run systemctl restart openasbl
run nginx -t
run systemctl reload nginx

# ── HTTPS ─────────────────────────────────────────────────────────────────
if [[ -n "$CERTBOT_EMAIL" ]]; then
  echo "==> Certificat TLS pour $DOMAIN..."
  run certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
    -m "$CERTBOT_EMAIL" --redirect
fi

# ── Checklist finale ──────────────────────────────────────────────────────
echo ""
echo "================================================"
echo "  Installation serveur terminée !"
echo "================================================"
echo ""
echo "  Domaine   : $DOMAIN"
echo "  Gunicorn  : 127.0.0.1:$PORT"
echo "  Service   : systemctl status openasbl"
echo "  Journaux  : journalctl -u openasbl -f"
echo ""
if [[ -z "$CERTBOT_EMAIL" ]]; then
  echo "  HTTPS non configuré. Pour l'activer :"
  echo "    apt install certbot python3-certbot-nginx"
  echo "    certbot --nginx -d $DOMAIN --redirect"
  echo ""
  echo "  Tant que le site répond en HTTP, les formulaires fonctionnent ;"
  echo "  une fois en HTTPS, Django s'appuie sur X-Forwarded-Proto (déjà"
  echo "  transmis par le vhost) pour valider les jetons CSRF."
  echo ""
fi
echo "  Créer le premier compte via l'assistant : https://$DOMAIN/"
echo ""

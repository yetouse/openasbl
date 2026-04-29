#!/usr/bin/env bash
set -euo pipefail

# ── Dry-run ────────────────────────────────────────────────────────────────
DRY_RUN=false
for arg in "$@"; do
  [[ "$arg" == "--dry-run" ]] && DRY_RUN=true
done

run() {
  if $DRY_RUN; then
    echo "  + $*"
  else
    "$@"
  fi
}

# ── Root requis ────────────────────────────────────────────────────────────
if [[ "$(id -u)" != "0" ]]; then
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

# ── Variables ──────────────────────────────────────────────────────────────
REPO_URL="https://github.com/yetouse/openasbl.git"
APP_DIR="${OPENASBL_APP_DIR:-/opt/openasbl}"
APP_USER="${OPENASBL_APP_USER:-openasbl}"

# ── Paquets système ────────────────────────────────────────────────────────
PKGS=(
  git python3 python3-venv python3-pip nginx
  libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
  libffi-dev libcairo2 libglib2.0-0
  tesseract-ocr tesseract-ocr-fra
)

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
  echo "  + id -u $APP_USER 2>/dev/null || useradd --system --no-create-home --shell /usr/sbin/nologin $APP_USER"
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

# ── Répertoires et permissions ─────────────────────────────────────────────
run mkdir -p /var/log/openasbl
run chown "$APP_USER":www-data /var/log/openasbl
run chown -R "$APP_USER":www-data "$APP_DIR"
run chmod 750 "$APP_DIR"

# ── Migration et collectstatic ─────────────────────────────────────────────
echo "==> Migration et collecte des fichiers statiques..."
if $DRY_RUN; then
  echo "  + sudo -u $APP_USER $APP_DIR/venv/bin/python $APP_DIR/manage.py migrate --noinput"
  echo "  + sudo -u $APP_USER $APP_DIR/venv/bin/python $APP_DIR/manage.py collectstatic --noinput"
else
  sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" "$APP_DIR/manage.py" migrate --noinput
  sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" "$APP_DIR/manage.py" collectstatic --noinput
fi

# ── Fichiers de déploiement (copie Python) ────────────────────────────────
echo "==> Installation service systemd et configuration nginx..."
if $DRY_RUN; then
  echo "  + python3: copie $APP_DIR/deploy/openasbl.service → /etc/systemd/system/openasbl.service"
  echo "  + python3: copie $APP_DIR/deploy/nginx-openasbl.conf → /etc/nginx/sites-available/openasbl"
  echo "  + ln -sf /etc/nginx/sites-available/openasbl /etc/nginx/sites-enabled/openasbl"
else
  python3 - "$APP_DIR" << 'PYEOF'
import shutil, os, sys
app_dir = sys.argv[1]
shutil.copy(os.path.join(app_dir, "deploy/openasbl.service"), "/etc/systemd/system/openasbl.service")
os.chmod("/etc/systemd/system/openasbl.service", 0o644)
shutil.copy(os.path.join(app_dir, "deploy/nginx-openasbl.conf"), "/etc/nginx/sites-available/openasbl")
os.chmod("/etc/nginx/sites-available/openasbl", 0o644)
PYEOF
  ln -sf /etc/nginx/sites-available/openasbl /etc/nginx/sites-enabled/openasbl
fi

# ── Services ──────────────────────────────────────────────────────────────
echo "==> Activation des services..."
run systemctl daemon-reload
run systemctl enable openasbl
run systemctl restart openasbl
run nginx -t
run systemctl reload nginx

# ── Checklist finale ──────────────────────────────────────────────────────
echo ""
echo "================================================"
echo "  Installation serveur terminée !"
echo "================================================"
echo ""
echo "Actions requises avant la mise en production :"
echo ""
echo "  1. SECRET_KEY — éditez /etc/systemd/system/openasbl.service"
echo "     Générez une clé :"
echo "     python3 -c \"import secrets; print(secrets.token_urlsafe(50))\""
echo ""
echo "  2. ALLOWED_HOSTS — même fichier, renseignez votre domaine"
echo "     ex : Environment=ALLOWED_HOSTS=mondomaine.be"
echo ""
echo "  3. server_name — éditez /etc/nginx/sites-available/openasbl"
echo "     Remplacez _ par votre domaine"
echo ""
echo "  4. HTTPS (certbot) :"
echo "     apt install certbot python3-certbot-nginx"
echo "     certbot --nginx -d mondomaine.be"
echo ""
echo "  Après toute modification du service :"
echo "  systemctl daemon-reload && systemctl restart openasbl"
echo ""

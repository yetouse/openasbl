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

# ── Vérifications préliminaires ────────────────────────────────────────────
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Erreur : ce script requiert Linux (Ubuntu/Debian)." >&2; exit 1
fi
if ! command -v apt-get >/dev/null 2>&1; then
  echo "Erreur : apt-get introuvable. Ubuntu/Debian requis." >&2; exit 1
fi

# ── Variables ──────────────────────────────────────────────────────────────
REPO_URL="https://github.com/yetouse/openasbl.git"
INSTALL_DIR="${OPENASBL_INSTALL_DIR:-$HOME/openasbl}"
DATA_DIR="${OPENASBL_DATA_DIR:-$HOME/.openasbl}"
PORT="${OPENASBL_PORT:-8765}"

SUDO_CMD=""
if [[ "$(id -u)" != "0" ]]; then
  SUDO_CMD="sudo"
fi

# ── Paquets système ────────────────────────────────────────────────────────
PKGS=(
  git python3 python3-venv python3-pip
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
  run $SUDO_CMD apt-get update -qq
  run $SUDO_CMD apt-get install -y "${MISSING[@]}"
else
  echo "  Tous les paquets sont déjà installés."
fi

# ── Clone / mise à jour ────────────────────────────────────────────────────
echo "==> Dépôt dans $INSTALL_DIR..."
if [[ -d "$INSTALL_DIR/.git" ]]; then
  run git -C "$INSTALL_DIR" pull --ff-only
else
  run git clone "$REPO_URL" "$INSTALL_DIR"
fi

# ── Environnement virtuel ──────────────────────────────────────────────────
echo "==> Environnement virtuel..."
if [[ ! -f "$INSTALL_DIR/venv/bin/python" ]]; then
  run python3 -m venv "$INSTALL_DIR/venv"
fi
run "$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
run "$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# ── Répertoire de données ──────────────────────────────────────────────────
run mkdir -p "$DATA_DIR"

# ── Migration ─────────────────────────────────────────────────────────────
echo "==> Migration de la base de données..."
if $DRY_RUN; then
  echo "  + OPENASBL_RUNTIME_MODE=desktop OPENASBL_DATA_DIR=$DATA_DIR \\"
  echo "      $INSTALL_DIR/venv/bin/python $INSTALL_DIR/manage.py migrate --noinput"
else
  OPENASBL_RUNTIME_MODE=desktop \
  OPENASBL_DATA_DIR="$DATA_DIR" \
  "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/manage.py" migrate --noinput
fi

# ── Résumé ─────────────────────────────────────────────────────────────────
echo ""
echo "================================================"
echo "  Installation desktop terminée !"
echo "================================================"
echo ""
echo "Pour lancer OpenASBL :"
echo "  cd $INSTALL_DIR"
echo "  ./scripts/run_desktop.sh"
echo ""
echo "Puis ouvrez : http://127.0.0.1:$PORT"
echo ""

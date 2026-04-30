# desktop/

Application Electron qui encapsule le backend Django d'OpenASBL dans une
fenêtre native, à la manière de Claude Desktop.

## État

**Phase 1 — MVP développeur.** Le shell Electron lance le `manage.py runserver`
existant et l'affiche dans une `BrowserWindow`. **Python 3.11+ est requis sur
la machine** (le runtime Python embarqué arrive en Phase 3).

## Prérequis

- Node.js 20+ et npm
- Python 3.11+ accessible :
  - Linux/macOS : un venv `./venv` à la racine du dépôt **ou** `python3` dans le PATH
  - Windows : `py -3` (recommandé) ou `python` dans le PATH
- Les dépendances Python du dépôt installées (`pip install -r requirements.txt`)

## Commandes

```bash
cd desktop
npm install              # installe Electron + electron-builder
npm run dev              # lance la fenêtre + Django local (port 8765)
                         # passe `--no-sandbox` pour autoriser un lancement
                         # local en root (CI/Xvfb). L'app packagée reste
                         # durcie via les options BrowserWindow ci-dessous.
npm run pack             # build non signé (dist/) — Phase 2
npm run dist             # produit l'installeur — Phase 2
```

## Comportement

- Variables passées à Django : `OPENASBL_RUNTIME_MODE=desktop`,
  `OPENASBL_DATA_DIR=<userData>/data`, `OPENASBL_PORT=<port>`.
- Port par défaut `8765`, repli sur un port libre s'il est occupé.
- `migrate --noinput` joué avant le `runserver` à chaque démarrage.
- Logs Django : `<userData>/logs/openasbl-backend.log`.
- Données utilisateur : `<userData>/data/` (SQLite, médias, statiques).
  - Linux : `~/.config/OpenASBL/`
  - Windows : `%APPDATA%/OpenASBL/`
  - macOS : `~/Library/Application Support/OpenASBL/`
- Fermeture de la fenêtre → `tree-kill` du process Python (zéro zombie).
- Fenêtre sécurisée : `contextIsolation: true`, `nodeIntegration: false`,
  `sandbox: true`, navigation externe redirigée vers le navigateur système.

## Limitations connues (Phase 1)

- Python doit être pré-installé sur la machine cible.
- Pas d'icône applicative dédiée (placeholder par défaut Electron). Déposer un
  PNG 512×512 dans `desktop/assets/icon.png` puis ajouter
  `icon: 'assets/icon.png'` dans `BrowserWindow` ainsi que dans la config
  `build` d'`electron-builder` quand un visuel sera prêt.
- WeasyPrint et Tesseract continuent d'utiliser les binaires système.

## Phases suivantes

Voir `docs/plans/electron-desktop.md` :

- Phase 2 — installeur Windows `.exe` via `electron-builder`.
- Phase 3 — runtime Python embarqué (zéro prérequis utilisateur).

# desktop/

Application Electron qui encapsule le backend Django d'OpenASBL dans une
fenêtre native, à la manière de Claude Desktop.

## État

Le desktop Electron est déjà **implémenté** : le repo contient `desktop/package.json`,
`desktop/src/main.js` et `desktop/src/preload.js`. La version packagée embarque
les sources Django dans `resources/backend` et provisionne un **venv Python par
utilisateur** sous `<userData>/runtime/venv` au premier lancement (puis le
réutilise tant que `requirements.txt` ne change pas). **Python 3.11+ reste
requis sur la machine hôte** ; le runtime Python embarqué arrive en Phase 3.

## Prérequis

- Node.js 20+ et npm
- Python 3.11+ accessible :
  - Linux/macOS : un venv `./.venv` ou `./venv` à la racine du dépôt **ou** `python3` dans le PATH
  - Windows : `py -3` (recommandé) ou `python` dans le PATH
- En dev, les dépendances Python du dépôt installées (`pip install -r requirements.txt`).
  En version packagée, l'app les installe automatiquement dans son venv runtime.

## Commandes

```bash
cd desktop
npm install              # installe Electron + electron-builder
npm run dev              # lance la fenêtre + Django local (port 8765)
                         # passe `--no-sandbox` pour autoriser un lancement
                         # local en root (CI/Xvfb). L'app packagée reste
                         # durcie via les options BrowserWindow ci-dessous.
npm run pack             # build non signé (dist/) — tests locaux
npm run dist             # produit l'installeur pour la plateforme courante
npm run dist:win         # produit l'installeur Windows NSIS (.exe)
                         # à exécuter de préférence sous Windows ; sous Linux,
                         # electron-builder requiert Wine pour l'étape NSIS —
                         # sans Wine, `dist/win-unpacked/` peut être généré
                         # mais l'installeur final `.exe` échouera.
```

## Installation Windows

Si vous êtes déjà dans **Windows PowerShell**, lancez directement :

```powershell
irm https://raw.githubusercontent.com/yetouse/openasbl/main/install-desktop.ps1 | iex
```

Si votre poste bloque l'exécution directe, utilisez la variante en deux étapes :

```powershell
$temp = Join-Path $env:TEMP 'install-desktop.ps1'
irm https://raw.githubusercontent.com/yetouse/openasbl/main/install-desktop.ps1 -OutFile $temp
Set-ExecutionPolicy -Scope Process Bypass -Force
& $temp
```

Si PowerShell vous dit encore que Python est introuvable, installez Python 3.11+ depuis python.org et désactivez les *App execution aliases* `python` / `python3` dans les paramètres Windows.

Si votre laptop est verrouillé par une politique d’entreprise et bloque toute installation, ce script ne pourra pas aller au bout localement : il faut un poste autorisé, une installation Python déjà présente, ou un installeur packagé validé par l’IT.

Le script clone/actualise le dépôt, prépare le venv Python, installe les dépendances Node du desktop et joue les migrations.

## Comportement

- Variables passées à Django : `OPENASBL_RUNTIME_MODE=desktop`,
  `OPENASBL_DATA_DIR=<userData>/data`, `OPENASBL_PORT=<port>`.
- Port par défaut `8765`, repli sur un port libre s'il est occupé.
- `migrate --noinput` joué avant le `runserver` à chaque démarrage.
- Logs Django : `<userData>/logs/openasbl-backend.log` (inclut aussi le
  bootstrap : création du venv et `pip install`).
- Données utilisateur : `<userData>/data/` (SQLite, médias, statiques). Le chemin `userData` est celui d'Electron ; le script `scripts/run_desktop.sh` s'y aligne par défaut en mode dev.
  - Linux : `~/.config/OpenASBL/`
  - Windows : `%APPDATA%/OpenASBL/`
  - macOS : `~/Library/Application Support/OpenASBL/`
- Runtime Python (mode packagé) : `<userData>/runtime/venv/`. Recréé/rééquipé
  automatiquement quand le hash de `requirements.txt` change
  (`<userData>/runtime/venv.requirements.sha256`).
- Backend root : en dev, racine du dépôt ; en packagé,
  `process.resourcesPath/backend` (sources copiées via `extraResources`).
- Fermeture de la fenêtre → `tree-kill` du process Python (zéro zombie).
- Fenêtre sécurisée : `contextIsolation: true`, `nodeIntegration: false`,
  `sandbox: true`, navigation externe redirigée vers le navigateur système.

## Limitations connues (Phase 2)

- Python 3.11+ doit toujours être pré-installé sur la machine cible
  (utilisé pour bootstrapper le venv runtime au premier lancement).
- Le premier lancement après installation est lent (création du venv +
  `pip install -r requirements.txt`).
- Pas d'icône applicative dédiée (placeholder par défaut Electron). Déposer un
  PNG 512×512 dans `desktop/assets/icon.png` puis ajouter
  `icon: 'assets/icon.png'` dans `BrowserWindow` ainsi que dans la config
  `build` d'`electron-builder` quand un visuel sera prêt.
- WeasyPrint et Tesseract continuent d'utiliser les binaires système.

## Phases suivantes

Voir `docs/plans/electron-desktop.md` :

- Phase 3 — runtime Python embarqué (zéro prérequis utilisateur).

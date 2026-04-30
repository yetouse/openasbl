# Plan : Application desktop OpenASBL (Electron)

## Objectif

Offrir la même expérience qu'un Claude Desktop : un installeur `.exe` pour
Windows, un double-clic, aucune ligne de commande, une fenêtre native qui
masque entièrement le serveur Django local.

## Existant

- Django 5 + SQLite, lancement actuel via `scripts/run_desktop.sh`.
- `desktop/README.md` est un placeholder, aucun `package.json`.
- WeasyPrint et Tesseract sont utilisés côté backend (PDF, OCR).
- Pas encore de runtime Python embarqué.

## Architecture cible

```
[ Electron main ]
   ├── spawn(python manage.py runserver 127.0.0.1:8765 --noreload)
   ├── attend la disponibilité HTTP (/healthz ou /)
   ├── BrowserWindow.loadURL("http://127.0.0.1:8765/")
   └── on app.quit / window-all-closed → kill du process Django
```

Principes :
- Port fixe par défaut (`8765`), repli sur port libre si occupé.
- Logs Django redirigés vers `%APPDATA%/OpenASBL/logs/`.
- Base SQLite et `media/` déplacés dans `%APPDATA%/OpenASBL/data/`.
- `STATIC_ROOT` collecté au build, servi via WhiteNoise.
- `preload.js` minimal (pas de `nodeIntegration`, `contextIsolation: true`).

---

## Phase 1 — MVP développeur

But : lancer l'app en local avec Python déjà installé.

Livrables :
- `desktop/package.json` (scripts `dev`, `start`, `pack`, `dist`).
- `desktop/src/main.js` : spawn Django, attente readiness, BrowserWindow.
- `desktop/src/preload.js` : surface IPC vide pour l'instant.
- `desktop/assets/` : icône `.png` provisoire.
- `desktop/scripts/wait-for-http.js` : helper readiness (polling HTTP).
- Mise à jour de `desktop/README.md` : prérequis, `npm install`, `npm run dev`.

Vérifications :
```bash
cd desktop && npm install
npm run dev               # ouvre la fenêtre, Django tourne en arrière-plan
python manage.py check
python manage.py test
```

Critère de sortie : double-clic depuis VS Code lance l'app, fermeture de la
fenêtre tue bien le process Python (vérifier `tasklist` / `ps`).

---

## Phase 2 — Installeur Windows

But : un `.exe` distribuable, encore avec Python pré-requis sur la machine.

Livrables :
- `electron-builder` configuré dans `desktop/package.json` (target `nsis`).
- Icônes `.ico` / `.icns`, raccourcis Bureau + Menu Démarrer.
- Détection du Python système (`py -3`, `python`, `PATH`), message clair si
  introuvable.
- Dossier utilisateur : `%APPDATA%/OpenASBL/{data,logs,media}` créé au
  premier lancement, migrations jouées automatiquement.
- Fichier de config persistant (port choisi, version DB).

Vérifications :
```bash
npm run pack              # build non signé pour tester
npm run dist              # produit OpenASBL-Setup-x.y.z.exe
```

Critère de sortie : installation sur une VM Windows propre (Python installé),
lancement, création de dossier, désinstallation propre.

---

## Phase 3 — Runtime Python embarqué

But : zéro prérequis. L'utilisateur installe et utilise, point.

Pistes :
- **python-build-standalone** (recommandé) : extraire un Python relocalisable
  dans `resources/python/` au build.
- Alternative : `pyinstaller --onedir` du backend Django, lancé comme binaire
  unique par Electron.
- Dépendances natives :
  - WeasyPrint → embarquer GTK runtime Windows ou basculer vers une lib
    pure-Python (ex. `xhtml2pdf`) selon qualité de rendu.
  - Tesseract → installer via l'installeur ou bundler `tesseract.exe` +
    `tessdata` (FR/NL/EN).
- Pré-création d'un venv au premier run, `pip install -r requirements.txt`
  depuis cache local (wheels embarqués).

Vérifications :
- Test sur Windows 10/11 sans Python ni GTK installés.
- Mesure taille installeur (cible < 250 Mo).

---

## Risques et points d'attention

| Risque | Mitigation |
|---|---|
| WeasyPrint dépend de GTK/Pango sur Windows | bundler GTK runtime ou changer de moteur PDF |
| Tesseract absent du système | embarquer le binaire + `tessdata` requis |
| Découverte de Python aléatoire (Phase 2) | sonder `py -3`, `python`, `PATH`, dialogue d'erreur explicite |
| Port `8765` occupé | fallback sur port aléatoire, propagé à `BrowserWindow` |
| Process Django zombie après crash Electron | `tree-kill` sur `app.before-quit` + `process.on('exit')` |
| Chemins `STATIC_ROOT` / `MEDIA_ROOT` en prod packagée | `collectstatic` au build, settings dédiés `desktop_settings.py` |
| Migrations sur DB utilisateur existante | `migrate` au démarrage, lock file pour éviter double exécution |

---

## Prochaine étape

Démarrer la Phase 1 : créer `desktop/package.json` et `desktop/src/main.js`,
brancher `npm run dev` sur le `manage.py runserver` existant.

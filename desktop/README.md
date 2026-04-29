# desktop/

Ce dossier accueillera l'application Electron pour le mode desktop.

## Intégration prévue

1. Electron lance `scripts/run_desktop.sh` en arrière-plan au démarrage.
2. Une fois le serveur Django prêt, Electron ouvre `http://127.0.0.1:${OPENASBL_PORT:-8765}` dans une `BrowserWindow`.
3. À la fermeture de la fenêtre, Electron termine le processus Django.

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `OPENASBL_PORT` | `8765` | Port d'écoute local |
| `OPENASBL_DATA_DIR` | `~/.openasbl` | Répertoire des données utilisateur |

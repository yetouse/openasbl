---
name: Project setup and access
description: OpenASBL déployé sur yetouse.cloud, GitHub repo, VPS Hostinger Ubuntu 24.04
type: project
---

Projet OpenASBL hébergé sur https://github.com/yetouse/openasbl.git

- Git config : Yannick CAISE <yannick.caise@gmail.com>
- Working directory : /home/yac/openasbl

**Déploiement production (2026-04-14) :**
- VPS Hostinger : 31.97.156.97 (Ubuntu 24.04, 2 vCPU, 8 Go RAM)
- Domaine : https://yetouse.cloud
- HTTPS : Let's Encrypt (certbot, renouvellement auto)
- SSH root direct depuis WSL (clé SSH configurée)
- App installée dans /opt/openasbl
- Gunicorn (systemd service) + Nginx reverse proxy
- Admin login : admin / OpenASBL2026! (à changer)

**Why:** Savoir comment accéder au projet et au serveur de production.
**How to apply:** Pour déployer : git push puis ssh root@31.97.156.97 pour pull + restart.

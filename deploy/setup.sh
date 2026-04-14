#!/bin/bash
# OpenASBL - Server setup script for Ubuntu VPS
# Run as root: bash setup.sh

set -e

APP_DIR="/opt/openasbl"
APP_USER="openasbl"

echo "=== OpenASBL Server Setup ==="

# 1. System packages
echo ">>> Installing system packages..."
apt update
apt install -y python3 python3-venv python3-pip nginx \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev libcairo2 libglib2.0-0 \
    git

# 2. Create app user
echo ">>> Creating app user..."
id -u $APP_USER &>/dev/null || useradd -r -m -s /bin/bash $APP_USER

# 3. Clone/update app
if [ -d "$APP_DIR" ]; then
    echo ">>> Updating app..."
    cd $APP_DIR
    git pull
else
    echo ">>> Cloning app..."
    git clone https://github.com/yetouse/openasbl.git $APP_DIR
fi

# 4. Python environment
echo ">>> Setting up Python environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install Pillow

# 5. Django setup
echo ">>> Running Django setup..."
python manage.py collectstatic --noinput
python manage.py migrate

# 6. Log directory
mkdir -p /var/log/openasbl
chown $APP_USER:www-data /var/log/openasbl

# 7. Permissions
chown -R $APP_USER:www-data $APP_DIR
chmod -R 750 $APP_DIR

# 8. Systemd service
echo ">>> Installing systemd service..."
cp $APP_DIR/deploy/openasbl.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable openasbl
systemctl start openasbl

# 9. Nginx
echo ">>> Configuring Nginx..."
cp $APP_DIR/deploy/nginx-openasbl.conf /etc/nginx/sites-available/openasbl
ln -sf /etc/nginx/sites-available/openasbl /etc/nginx/sites-enabled/openasbl
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "=== Setup complete ==="
echo ""
echo "IMPORTANT - Remaining steps:"
echo "  1. Edit /etc/systemd/system/openasbl.service"
echo "     - Set DJANGO_SECRET_KEY (generate with: python3 -c \"import secrets; print(secrets.token_urlsafe(50))\")"
echo "     - Set DJANGO_ALLOWED_HOSTS to your domain/IP"
echo "  2. Edit /etc/nginx/sites-available/openasbl"
echo "     - Set server_name to your domain/IP"
echo "  3. Reload: systemctl daemon-reload && systemctl restart openasbl && systemctl reload nginx"
echo "  4. Create admin user: cd $APP_DIR && source venv/bin/activate && python manage.py createsuperuser"
echo "  5. (Optional) Setup HTTPS with: certbot --nginx -d yourdomain.com"
echo ""

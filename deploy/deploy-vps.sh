#!/usr/bin/env bash
# Deploy CWAC-ADMIN to VPS at /opt/cwac-admin
# Run this script ON THE VPS as root: bash deploy-vps.sh
set -e

INSTALL_DIR="/opt/cwac-admin"
REPO_URL="https://github.com/sweddell/CWAC-ADMIN.git"
PORT=5100
# Public hostname the site will be served on — override when running:
#   DOMAIN=cwac.example.com bash deploy-vps.sh
DOMAIN="${DOMAIN:-cwac.example.com}"

echo "=== CWAC-ADMIN VPS Deployment ==="

# 1. Clone or update repo
if [ -d "$INSTALL_DIR/.git" ]; then
  echo ">> Updating existing repo..."
  cd "$INSTALL_DIR"
  git pull origin main
else
  echo ">> Cloning repo..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

# 2. Create venv and install deps
echo ">> Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet gunicorn

# 3. Install CWAC scanner
echo ">> Installing CWAC scanner..."
bash install_cwac.sh
cd cwac && npm install --silent && cd ..

# 3b. Install CWAC scanner Python deps into the same venv
# (the app spawns cwac/cwac.py with .venv/bin/python, so the scanner's
#  deps must live in this environment or scans fail with ModuleNotFoundError)
echo ">> Installing CWAC scanner Python dependencies..."
pip install --quiet -r cwac/requirements.txt

# 4. Copy config files to scanner
echo ">> Copying config files..."
cp config/*.json cwac/config/

# 5. Initialise database (only if it doesn't exist)
DB_PATH="cwac_admin_app/database/bi_integration/cwac_analytics.db"
if [ ! -f "$DB_PATH" ]; then
  echo ">> Initialising database..."
  sqlite3 "$DB_PATH" < cwac_admin_app/database/bi_integration/schema.sql
else
  echo ">> Database already exists, skipping init."
fi

# 6. Create .env if it doesn't exist
if [ ! -f ".env" ]; then
  echo ">> Creating .env..."
  SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  cat > .env <<EOF
SECRET_KEY=$SECRET
FLASK_ENV=production
PORT=$PORT
HOST=0.0.0.0
CHROME_EXTRA_ARGS=--disable-dev-shm-usage,--disable-gpu
EOF
  echo ">> .env created with generated SECRET_KEY"
else
  echo ">> .env already exists, skipping."
fi

# 6a. Ensure CHROME_EXTRA_ARGS is set (covers pre-existing .env files).
# The service runs as an unprivileged user so Chrome's sandbox stays on.
# Only add --no-sandbox manually if Chrome cannot start at all.
if ! grep -q '^CHROME_EXTRA_ARGS=' .env; then
  echo ">> Adding CHROME_EXTRA_ARGS to existing .env..."
  echo 'CHROME_EXTRA_ARGS=--disable-dev-shm-usage,--disable-gpu' >> .env
elif grep -q '^CHROME_EXTRA_ARGS=.*--no-sandbox' .env; then
  echo ">> WARNING: .env sets CHROME_EXTRA_ARGS with --no-sandbox — Chrome's"
  echo ">> sandbox is disabled for every scanned site. Remove it unless the"
  echo ">> kernel forbids user namespaces."
fi

# 6b. Ensure logs directory exists
mkdir -p "$INSTALL_DIR/logs"

# 6c. Run the service as a dedicated unprivileged user (never root):
# the scanner drives Chrome against arbitrary scanned sites, so the
# service must not have root privileges.
SERVICE_USER=cwacadmin
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
  echo ">> Creating service user: $SERVICE_USER"
  useradd --system --shell /usr/sbin/nologin "$SERVICE_USER"
fi
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# 7. Install systemd service
echo ">> Installing systemd service..."
cp deploy/cwac-admin.service /etc/systemd/system/cwac-admin.service
systemctl daemon-reload
systemctl enable cwac-admin
systemctl restart cwac-admin
echo ">> Service status:"
systemctl status cwac-admin --no-pager

# 8. Install nginx config (substitutes your domain into server_name)
echo ">> Installing nginx config for $DOMAIN..."
sed "s/cwac\.example\.com/$DOMAIN/g" deploy/cwac-admin-nginx.conf > /etc/nginx/sites-available/cwac-admin
ln -sf /etc/nginx/sites-available/cwac-admin /etc/nginx/sites-enabled/cwac-admin
nginx -t && systemctl reload nginx

echo ""
echo "=== Deployment complete! ==="
echo "App running internally on port $PORT"
echo "Next steps:"
echo "  1. Add DNS A record: $DOMAIN -> $(curl -s ifconfig.me)"
echo "  2. After DNS propagates: certbot --nginx -d $DOMAIN"
echo "  3. Visit https://$DOMAIN and change the default password!"

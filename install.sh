#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  UnboundSales — Script de instalação para VPS Linux (root)
# ═══════════════════════════════════════════════════════════
set -e

APP_DIR="/opt/unboundsales"
REPO="https://github.com/Shietnar/agentes.git"
SERVICE="unboundsales"
PORT=8501

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓ $1${NC}"; }
info() { echo -e "${YELLOW}→ $1${NC}"; }
err()  { echo -e "${RED}✗ $1${NC}"; exit 1; }

echo ""
echo "══════════════════════════════════════════"
echo "  UnboundSales — Instalação"
echo "══════════════════════════════════════════"
echo ""

# ── 1. Sistema ────────────────────────────────────────────
info "Atualizando pacotes..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git nginx curl > /dev/null
ok "Pacotes instalados"

# ── 2. Clonar ou atualizar ────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
    info "Repositório já existe — atualizando..."
    cd "$APP_DIR" && git pull --ff-only
    ok "Código atualizado"
else
    info "Clonando repositório..."
    git clone "$REPO" "$APP_DIR"
    ok "Repositório clonado em $APP_DIR"
fi
cd "$APP_DIR"

# ── 3. Ambiente Python ────────────────────────────────────
info "Criando ambiente virtual..."
python3 -m venv venv
ok "venv criado"

info "Instalando dependências (pode demorar alguns minutos)..."
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q
ok "Dependências instaladas"

# ── 4. Verificar .env ─────────────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  ATENÇÃO: arquivo .env não encontrado!${NC}"
    echo -e "${YELLOW}  Copie do seu Mac com o comando:${NC}"
    echo ""
    echo -e "  scp .env root@76.13.171.14:$APP_DIR/"
    echo -e "  scp config/client_secret.json root@76.13.171.14:$APP_DIR/config/"
    echo -e "  scp config/google-ads.yaml root@76.13.171.14:$APP_DIR/config/"
    echo ""
    echo -e "  Depois reinicie: systemctl restart $SERVICE"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
fi

# ── 5. Banco de dados ─────────────────────────────────────
info "Inicializando banco de dados..."
venv/bin/python3 -c "from database.models import criar_tabelas; criar_tabelas()" 2>/dev/null || true
ok "Banco pronto"

# ── 6. Systemd ────────────────────────────────────────────
info "Configurando serviço systemd..."
cat > /etc/systemd/system/$SERVICE.service << EOF
[Unit]
Description=UnboundSales Dashboard
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python -m streamlit run dashboard/app.py \\
    --server.port=$PORT \\
    --server.headless=true \\
    --server.address=127.0.0.1 \\
    --browser.gatherUsageStats=false
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE
systemctl restart $SERVICE
ok "Serviço $SERVICE ativo e habilitado no boot"

# ── 7. Nginx ──────────────────────────────────────────────
info "Configurando Nginx..."
cat > /etc/nginx/sites-available/$SERVICE << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass         http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
        proxy_buffering    off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/$SERVICE /etc/nginx/sites-enabled/$SERVICE
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
ok "Nginx configurado"

# ── 8. Firewall ───────────────────────────────────────────
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp  > /dev/null 2>&1 || true
    ufw allow 443/tcp > /dev/null 2>&1 || true
    ufw allow 22/tcp  > /dev/null 2>&1 || true
    ok "Firewall: portas 22, 80 e 443 abertas"
fi

# ── Resumo ────────────────────────────────────────────────
IP=$(curl -s ifconfig.me 2>/dev/null || echo "76.13.171.14")
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Instalação concluída!${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""
echo -e "  🌐 Acesse: ${GREEN}http://$IP${NC}"
echo ""
echo -e "  Comandos úteis:"
echo -e "    systemctl status $SERVICE    # ver status"
echo -e "    journalctl -u $SERVICE -f    # ver logs"
echo -e "    systemctl restart $SERVICE   # reiniciar"
echo ""

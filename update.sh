#!/bin/bash
# UnboundSales — Atualiza o código do GitHub e reinicia
set -e
APP_DIR="/opt/unboundsales"
echo "→ Atualizando código..."
cd "$APP_DIR" && git pull --ff-only
echo "→ Atualizando dependências..."
venv/bin/pip install -r requirements.txt -q
echo "→ Reiniciando serviço..."
systemctl restart unboundsales
echo "✓ Atualização concluída!"

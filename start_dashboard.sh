#!/bin/zsh
# UnboundSales — Script de inicialização do painel

PROJECT="/Users/shietnar/Desktop/Claude/Agentes-UnboundSales"
PYTHON="$PROJECT/venv/bin/python3"
PORT=8501
URL="http://localhost:$PORT"

cd "$PROJECT"

# Mata instância anterior, se houver
pkill -f "streamlit run dashboard/app.py" 2>/dev/null
sleep 1

# Usa o Python do venv diretamente (binário real — processa .pth files corretamente)
nohup "$PYTHON" -m streamlit run dashboard/app.py \
  --server.headless true \
  --server.port $PORT \
  --browser.gatherUsageStats false \
  > /tmp/unboundsales.log 2>&1 &

echo $! > /tmp/unboundsales.pid
echo "🚀 UnboundSales iniciando..."

# Aguarda o servidor ficar pronto (até 20 seg)
for i in {1..20}; do
    sleep 1
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo "✅ Pronto em $URL"
        open "$URL"
        exit 0
    fi
    echo "   Aguardando... ($i/20)"
done

echo "⚠️  Servidor demorou — abrindo mesmo assim..."
open "$URL"

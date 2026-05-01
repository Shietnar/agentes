#!/bin/zsh
pkill -f "streamlit run dashboard/app.py" 2>/dev/null
rm -f /tmp/unboundsales.pid
echo "🛑 UnboundSales encerrado."

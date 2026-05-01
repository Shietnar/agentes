"""
Script para gerar o Refresh Token do Google Ads.
Execute uma vez, copie o token gerado e coloque no .env
"""
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]
CLIENT_SECRET_FILE = "config/client_secret.json"

def gerar_refresh_token():
    print("""
╔══════════════════════════════════════════════╗
║     UNBOUND SALES — Gerador de Token Google  ║
╚══════════════════════════════════════════════╝

Vou abrir o navegador para você fazer login com
sua conta Google que tem acesso ao Google Ads.

Siga os passos na tela do navegador.
""")

    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES
    )

    # Abre o navegador automaticamente
    credentials = flow.run_local_server(
        port=8080,
        prompt="consent",
        access_type="offline"
    )

    print("\n✅ AUTENTICAÇÃO CONCLUÍDA!\n")
    print("=" * 50)
    print("Copie os valores abaixo para o seu arquivo .env:")
    print("=" * 50)
    print(f"\nGOOGLE_ADS_CLIENT_ID={credentials.client_id}")
    print(f"GOOGLE_ADS_CLIENT_SECRET={credentials.client_secret}")
    print(f"GOOGLE_ADS_REFRESH_TOKEN={credentials.refresh_token}")
    print("\n" + "=" * 50)

    # Salva automaticamente em um arquivo de referência
    with open("config/google_credentials.txt", "w") as f:
        f.write(f"GOOGLE_ADS_CLIENT_ID={credentials.client_id}\n")
        f.write(f"GOOGLE_ADS_CLIENT_SECRET={credentials.client_secret}\n")
        f.write(f"GOOGLE_ADS_REFRESH_TOKEN={credentials.refresh_token}\n")

    print("\nAs credenciais também foram salvas em: config/google_credentials.txt")
    print("Lembre de adicioná-las ao seu .env!\n")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    gerar_refresh_token()

"""
ETL Runner — captura e processa conhecimento para a base de agentes.

Uso:
  python etl/run_etl.py                    # processa todos os agentes
  python etl/run_etl.py --agent pedro      # processa só o agente pedro
  python etl/run_etl.py --agent pedro --force  # ignora cache TTL

O resultado são arquivos .md em agents/knowledge/{agent}/
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

# Garante imports do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.extractors.youtube import extrair_playlist, extrair_canal_recente, buscar_videos_por_query
from etl.extractors.web_scraper import extrair_artigo, extrair_blog_index
from etl.processors.knowledge_extractor import extrair_conhecimento, consolidar_conhecimento

_ETL_DIR = Path(__file__).parent
_SOURCES_FILE = _ETL_DIR / "sources.yaml"
_PROJECT_ROOT = _ETL_DIR.parent


def _carregar_config() -> dict:
    with open(_SOURCES_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _cache_path(cache_dir: Path, chave: str) -> Path:
    h = hashlib.md5(chave.encode()).hexdigest()[:12]
    return cache_dir / f"{h}.json"


def _cache_valido(path: Path, ttl_days: int) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(days=ttl_days)


def _salvar_cache(path: Path, dados: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)


def _ler_cache(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _salvar_conhecimento(output_dir: Path, agent: str, topico: str, conteudo: str) -> None:
    dest = output_dir / agent / f"{topico}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(conteudo, encoding="utf-8")
    print(f"  ✓ Salvo: {dest.relative_to(_PROJECT_ROOT)}")


def processar_youtube_playlist(
    fonte: dict, agent: str, config: dict, cache_dir: Path, force: bool
) -> None:
    playlist_id = fonte["id"]
    topico = fonte["topico"]
    idioma = fonte.get("idioma", "pt")
    max_videos = fonte.get("max_videos", 20)

    cache_key = f"yt_playlist_{playlist_id}"
    cp = _cache_path(cache_dir, cache_key)

    if not force and _cache_valido(cp, config["cache_ttl_days"]):
        print(f"  → [{topico}] cache válido, pulando extração")
        dados = _ler_cache(cp)
    else:
        print(f"  → [{topico}] extraindo playlist {playlist_id}...")
        videos = extrair_playlist(playlist_id, idioma=idioma, max_videos=max_videos)
        print(f"     {len(videos)} vídeos com transcrição")
        dados = {"videos": videos}
        _salvar_cache(cp, dados)

    if not dados["videos"]:
        print(f"  ✗ [{topico}] sem vídeos com transcrição")
        return

    print(f"  → [{topico}] consolidando {len(dados['videos'])} transcrições com Claude...")
    md = consolidar_conhecimento(dados["videos"], agent, topico, model=config["model"])
    if md:
        output_dir = _PROJECT_ROOT / config["output_dir"]
        _salvar_conhecimento(output_dir, agent, topico, md)
    else:
        print(f"  ✗ [{topico}] sem conteúdo relevante extraído")


def processar_youtube_search(
    fonte: dict, agent: str, config: dict, cache_dir: Path, force: bool
) -> None:
    query = fonte["query"]
    topico = fonte["topico"]
    max_videos = fonte.get("max_videos", 10)

    cache_key = f"yt_search_{query}"
    cp = _cache_path(cache_dir, cache_key)

    if not force and _cache_valido(cp, config["cache_ttl_days"]):
        print(f"  → [{topico}] cache válido, pulando busca")
        dados = _ler_cache(cp)
    else:
        print(f"  → [{topico}] buscando: \"{query}\"...")
        videos = buscar_videos_por_query(query, max_videos=max_videos)
        print(f"     {len(videos)} vídeos com transcrição encontrados")
        dados = {"videos": videos}
        _salvar_cache(cp, dados)

    if not dados["videos"]:
        print(f"  ✗ [{topico}] sem vídeos com transcrição")
        return

    print(f"  → [{topico}] consolidando {len(dados['videos'])} transcrições com Claude...")
    md = consolidar_conhecimento(dados["videos"], agent, topico, model=config["model"])
    if md:
        output_dir = _PROJECT_ROOT / config["output_dir"]
        _salvar_conhecimento(output_dir, agent, topico, md)
    else:
        print(f"  ✗ [{topico}] sem conteúdo relevante")


def processar_youtube_canal(
    fonte: dict, agent: str, config: dict, cache_dir: Path, force: bool
) -> None:
    channel_id = fonte["id"]
    topico = fonte["topico"]
    idioma = fonte.get("idioma", "pt")
    max_videos = fonte.get("max_videos", 10)

    cache_key = f"yt_canal_{channel_id}"
    cp = _cache_path(cache_dir, cache_key)

    if not force and _cache_valido(cp, config["cache_ttl_days"]):
        print(f"  → [{topico}] cache válido, pulando extração")
        dados = _ler_cache(cp)
    else:
        print(f"  → [{topico}] extraindo canal recente {channel_id}...")
        videos = extrair_canal_recente(channel_id, idioma=idioma, max_videos=max_videos)
        print(f"     {len(videos)} vídeos com transcrição")
        dados = {"videos": videos}
        _salvar_cache(cp, dados)

    if not dados["videos"]:
        print(f"  ✗ [{topico}] sem vídeos com transcrição")
        return

    print(f"  → [{topico}] consolidando com Claude...")
    md = consolidar_conhecimento(dados["videos"], agent, topico, model=config["model"])
    if md:
        output_dir = _PROJECT_ROOT / config["output_dir"]
        _salvar_conhecimento(output_dir, agent, topico, md)
    else:
        print(f"  ✗ [{topico}] sem conteúdo relevante")


def processar_web_artigo(
    fonte: dict, agent: str, config: dict, cache_dir: Path, force: bool
) -> None:
    url = fonte["url"]
    topico = fonte["topico"]
    idioma = fonte.get("idioma", "pt")

    cache_key = f"web_{url}"
    cp = _cache_path(cache_dir, cache_key)

    if not force and _cache_valido(cp, config["cache_ttl_days"]):
        print(f"  → [{topico}] cache válido, pulando scraping")
        dados = _ler_cache(cp)
    else:
        print(f"  → [{topico}] scraping {url}...")
        artigo = extrair_artigo(url)
        if not artigo:
            print(f"  ✗ [{topico}] falha ao extrair artigo")
            return
        dados = artigo
        _salvar_cache(cp, dados)

    print(f"  → [{topico}] extraindo conhecimento com Claude...")
    md = extrair_conhecimento(
        dados["conteudo"],
        agent,
        topico,
        fonte=url,
        titulo=dados.get("titulo", topico),
        model=config["model"],
    )
    if md:
        output_dir = _PROJECT_ROOT / config["output_dir"]
        _salvar_conhecimento(output_dir, agent, topico, md)
    else:
        print(f"  ✗ [{topico}] sem conteúdo relevante")


def processar_web_blog_index(
    fonte: dict, agent: str, config: dict, cache_dir: Path, force: bool
) -> None:
    url = fonte["url"]
    topico = fonte["topico"]
    max_articles = fonte.get("max_articles", 10)

    cache_key = f"blog_{url}"
    cp = _cache_path(cache_dir, cache_key)

    if not force and _cache_valido(cp, config["cache_ttl_days"]):
        print(f"  → [{topico}] cache válido, pulando scraping")
        dados = _ler_cache(cp)
    else:
        print(f"  → [{topico}] scraping blog {url}...")
        artigos = extrair_blog_index(url, max_articles=max_articles)
        print(f"     {len(artigos)} artigos extraídos")
        dados = {"artigos": artigos}
        _salvar_cache(cp, dados)

    if not dados.get("artigos"):
        print(f"  ✗ [{topico}] sem artigos extraídos")
        return

    # Consolida todos os artigos do blog como se fossem vídeos
    items = [{"titulo": a["titulo"], "transcricao": a["conteudo"]} for a in dados["artigos"]]
    print(f"  → [{topico}] consolidando {len(items)} artigos com Claude...")
    md = consolidar_conhecimento(items, agent, topico, model=config["model"])
    if md:
        output_dir = _PROJECT_ROOT / config["output_dir"]
        _salvar_conhecimento(output_dir, agent, topico, md)
    else:
        print(f"  ✗ [{topico}] sem conteúdo relevante")


def processar_agente(agent: str, config_completo: dict, force: bool) -> None:
    config = config_completo["config"]
    agente_config = config_completo["agents"].get(agent)
    if not agente_config:
        print(f"Agente '{agent}' não encontrado em sources.yaml")
        return

    cache_dir = _PROJECT_ROOT / config["raw_cache_dir"] / agent
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'━'*50}")
    print(f"AGENTE: {agent.upper()} — {agente_config.get('description', '')}")
    print(f"{'━'*50}")

    # YouTube
    for fonte in agente_config.get("youtube", []):
        tipo = fonte.get("type", "playlist")
        if tipo == "search":
            processar_youtube_search(fonte, agent, config, cache_dir, force)
        elif tipo == "channel_recent":
            processar_youtube_canal(fonte, agent, config, cache_dir, force)
        else:
            processar_youtube_playlist(fonte, agent, config, cache_dir, force)

    # Web
    for fonte in agente_config.get("web", []):
        tipo = fonte.get("tipo", "artigo")
        if tipo == "blog_index":
            processar_web_blog_index(fonte, agent, config, cache_dir, force)
        else:
            processar_web_artigo(fonte, agent, config, cache_dir, force)


def main():
    parser = argparse.ArgumentParser(description="ETL — captura conhecimento para agentes")
    parser.add_argument("--agent", help="Processar só este agente (ex: pedro)")
    parser.add_argument("--force", action="store_true", help="Ignorar cache TTL")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERRO: ANTHROPIC_API_KEY não definida no .env")
        sys.exit(1)

    config = _carregar_config()

    if args.agent:
        processar_agente(args.agent, config, args.force)
    else:
        for agent in config["agents"]:
            processar_agente(agent, config, args.force)

    print(f"\n✓ ETL concluído. Arquivos em: {config['config']['output_dir']}/")
    print("  Execute 'python push_prompts.py' para atualizar os agentes gerenciados.\n")


if __name__ == "__main__":
    main()

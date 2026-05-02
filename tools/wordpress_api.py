"""WordPress REST API — leitura e edição de páginas com suporte a Elementor."""
import requests
import json
import base64
from typing import Optional


def _headers(user: str, app_password: str) -> dict:
    token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def testar_conexao(wp_url: str, user: str, app_password: str) -> dict:
    url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/users/me"
    try:
        r = requests.get(url, headers=_headers(user, app_password), timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"ok": True, "usuario": data.get("name", user), "roles": data.get("roles", [])}
        return {"ok": False, "erro": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


def listar_paginas(wp_url: str, user: str, app_password: str, per_page: int = 100) -> list:
    url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/pages"
    params = {
        "per_page": per_page,
        "status": "any",
        "context": "edit",
        "_fields": "id,title,status,link,modified",
    }
    r = requests.get(url, headers=_headers(user, app_password), params=params, timeout=15)
    r.raise_for_status()
    return [
        {
            "id": p["id"],
            "titulo": p["title"]["rendered"],
            "status": p["status"],
            "url": p["link"],
            "modificada": p.get("modified", "")[:10],
        }
        for p in r.json()
    ]


def obter_pagina(wp_url: str, user: str, app_password: str, page_id: int) -> dict:
    url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/pages/{page_id}"
    r = requests.get(url, headers=_headers(user, app_password),
                     params={"context": "edit"}, timeout=15)
    r.raise_for_status()
    data = r.json()
    meta = data.get("meta", {})
    elementor_raw = meta.get("_elementor_data")
    return {
        "id": data["id"],
        "titulo": data["title"]["rendered"],
        "status": data["status"],
        "url": data["link"],
        "html_renderizado": data["content"]["rendered"],
        "html_raw": data["content"].get("raw", ""),
        "elementor_data": elementor_raw,
        "usa_elementor": elementor_raw not in (None, "", "[]"),
    }


def atualizar_conteudo_html(wp_url: str, user: str, app_password: str,
                             page_id: int, html: str) -> dict:
    """Atualiza o conteúdo da página via editor clássico."""
    url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/pages/{page_id}"
    payload = {"content": {"raw": html, "rendered": html}}
    r = requests.post(url, headers=_headers(user, app_password),
                      data=json.dumps(payload), timeout=20)
    if r.status_code in (200, 201):
        return {"sucesso": True, "link": r.json().get("link", "")}
    return {"sucesso": False, "erro": f"HTTP {r.status_code}: {r.text[:400]}"}


def atualizar_elementor_data(wp_url: str, user: str, app_password: str,
                              page_id: int, elementor_json: str) -> dict:
    """
    Atualiza o _elementor_data via REST API.
    Requer que o meta esteja registrado no REST (via functions.php ou plugin).
    """
    url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/pages/{page_id}"
    payload = {
        "meta": {
            "_elementor_data": elementor_json,
            "_elementor_edit_mode": "builder",
        }
    }
    r = requests.post(url, headers=_headers(user, app_password),
                      data=json.dumps(payload), timeout=20)
    if r.status_code in (200, 201):
        return {"sucesso": True, "link": r.json().get("link", "")}
    return {"sucesso": False, "erro": f"HTTP {r.status_code}: {r.text[:400]}"}


def injetar_html_elementor(wp_url: str, user: str, app_password: str,
                            page_id: int, html: str) -> dict:
    """
    Injeta o HTML como widget HTML do Elementor, substituindo toda a estrutura da página.
    Requer _elementor_data registrado no REST.
    """
    structure = [
        {
            "id": "ubs_section",
            "elType": "section",
            "isInner": False,
            "settings": {
                "padding": {
                    "unit": "px", "top": "0", "right": "0",
                    "bottom": "0", "left": "0", "isLinked": True,
                },
                "content_width": {"unit": "px", "size": 1200, "sizes": {}},
            },
            "elements": [
                {
                    "id": "ubs_col",
                    "elType": "column",
                    "settings": {"_column_size": 100},
                    "elements": [
                        {
                            "id": "ubs_html_widget",
                            "elType": "widget",
                            "widgetType": "html",
                            "settings": {"html": html},
                        }
                    ],
                }
            ],
        }
    ]
    return atualizar_elementor_data(
        wp_url, user, app_password, page_id,
        json.dumps(structure, ensure_ascii=False),
    )


_SNIPPET_ELEMENTOR_REST = """// Cole em functions.php do seu tema filho ou em um plugin custom:
add_action('rest_api_init', function() {
    foreach (['page', 'post'] as $type) {
        register_post_meta($type, '_elementor_data', [
            'show_in_rest' => true,
            'single'       => true,
            'type'         => 'string',
            'auth_callback' => function() { return current_user_can('edit_posts'); },
        ]);
        register_post_meta($type, '_elementor_edit_mode', [
            'show_in_rest' => true,
            'single'       => true,
            'type'         => 'string',
            'auth_callback' => function() { return current_user_can('edit_posts'); },
        ]);
    }
});"""


def snippet_elementor_rest() -> str:
    return _SNIPPET_ELEMENTOR_REST

"""PDF Extractor — extrai texto de arquivos PDF."""
from typing import Optional


def extrair_pdf(conteudo_bytes: bytes, nome_arquivo: str = "") -> Optional[str]:
    """
    Extrai texto de um PDF (bytes).
    Usa pdfplumber (preferido) com fallback para PyPDF2.
    Retorna texto limpo ou None se falhar.
    """
    try:
        import pdfplumber
        import io
        texto_partes = []
        with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
            for pagina in pdf.pages:
                t = pagina.extract_text()
                if t:
                    texto_partes.append(t.strip())
        texto = "\n\n".join(texto_partes)
        return texto if len(texto) > 200 else None
    except ImportError:
        pass
    except Exception:
        return None

    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(conteudo_bytes))
        partes = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                partes.append(t.strip())
        texto = "\n\n".join(partes)
        return texto if len(texto) > 200 else None
    except Exception:
        return None

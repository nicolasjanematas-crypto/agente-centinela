"""Agente Centinela — agente conversacional para vigilar un catálogo de productos.

Construido con smolagents (CodeAgent + LiteLLMModel). Responde en lenguaje natural
sobre precios, stock, histórico y alertas de compra usando seis herramientas propias.

Datos: proyecto Centinela (Escuela Musk) — 60 artículos ficticios y 120 días de
histórico de precios. Los datos son de ejemplo y pueden publicarse libremente.
"""

import os
import json
import csv
import statistics

import litellm
litellm.drop_params = True  # descarta parámetros que el modelo no acepta

from smolagents import CodeAgent, LiteLLMModel, tool

# ---------- carga de datos ----------
with open("catalogo.json", encoding="utf-8") as f:
    CATALOGO = json.load(f)["articulos"]

HISTORICO = {}
with open("historico_precios.csv", encoding="utf-8") as f:
    for fila in csv.DictReader(f):
        HISTORICO.setdefault(fila["id"], []).append(
            {"fecha": fila["fecha"], "precio": float(fila["precio"]), "stock": int(fila["stock"])}
        )

CATEGORIAS = sorted({a["categoria"] for a in CATALOGO})


def _formato_articulo(a):
    stock_txt = f"{a['stock']} uds" if a["stock"] > 0 else "AGOTADO"
    return (f"- {a['id']} | {a['nombre']} | {a['categoria']} | {a['tienda']} | "
            f"{a['precio']:.2f} eur (ref. {a['precio_referencia']:.2f} eur) | "
            f"stock: {stock_txt} | valoracion {a['valoracion']}/5")


@tool
def listar_categorias() -> str:
    """Devuelve la lista de categorias del catalogo con el numero de articulos de cada una.
    Args:
        (sin argumentos)
    """
    return "\n".join(
        f"- {cat}: {len([a for a in CATALOGO if a['categoria'] == cat])} articulos"
        for cat in CATEGORIAS
    )


@tool
def listar_articulos(categoria: str = "") -> str:
    """Lista los articulos del catalogo, opcionalmente filtrados por categoria.
    Args:
        categoria: Categoria a filtrar (por ejemplo 'moviles') o cadena vacia para ver todas.
    """
    arts = [a for a in CATALOGO if a["categoria"] == categoria] if categoria else list(CATALOGO)
    if not arts:
        return f"No hay articulos en la categoria '{categoria}'. Usa listar_categorias() para verlas."
    return "\n".join(_formato_articulo(a) for a in arts)


@tool
def buscar_articulos(texto: str) -> str:
    """Busca articulos por nombre o identificador (texto parcial, sin distinguir mayusculas).
    Args:
        texto: Texto a buscar en el nombre o el id del articulo (por ejemplo 'nexora' o 'ART-0007').
    """
    t = texto.lower()
    arts = [a for a in CATALOGO if t in a["nombre"].lower() or t in a["id"].lower()]
    if not arts:
        return f"No se encontro ningun articulo con '{texto}'."
    return "\n".join(_formato_articulo(a) for a in arts)


@tool
def historial_precio(id_articulo: str, dias: int = 30) -> str:
    """Devuelve el historico reciente de precios y stock de un articulo, con estadisticas.
    Args:
        id_articulo: Identificador del articulo, por ejemplo 'ART-0001'.
        dias: Numero de dias hacia atras a mostrar (por defecto 30).
    """
    regs = HISTORICO.get(id_articulo)
    if not regs:
        return f"No hay historico para '{id_articulo}'."
    recientes = regs[-dias:]
    precios = [r["precio"] for r in recientes]
    lineas = [f"- {r['fecha']}: {r['precio']:.2f} eur, stock {r['stock']}" for r in recientes]
    return (f"Historico ultimos {len(recientes)} dias de {id_articulo}:\n"
            + "\n".join(lineas)
            + f"\nMedia: {statistics.mean(precios):.2f} eur | Min: {min(precios):.2f} eur | "
            f"Ultimo: {precios[-1]:.2f} eur")


@tool
def resumen_categoria(categoria: str) -> str:
    """Resume una categoria: numero de articulos, precio medio, el mas barato, el mas caro y los agotados.
    Args:
        categoria: Nombre de la categoria, por ejemplo 'portatiles'.
    """
    arts = [a for a in CATALOGO if a["categoria"] == categoria]
    if not arts:
        return f"No existe la categoria '{categoria}'. Usa listar_categorias()."
    precios = [a["precio"] for a in arts]
    barato = min(arts, key=lambda a: a["precio"])
    caro = max(arts, key=lambda a: a["precio"])
    agotados = [a["id"] for a in arts if a["stock"] == 0]
    return (f"Categoria '{categoria}': {len(arts)} articulos | precio medio {statistics.mean(precios):.2f} eur\n"
            f"- Mas barato: {barato['nombre']} a {barato['precio']:.2f} eur\n"
            f"- Mas caro: {caro['nombre']} a {caro['precio']:.2f} eur\n"
            f"- Agotados: {len(agotados)} ({', '.join(agotados) if agotados else 'ninguno'})")


@tool
def detectar_alertas() -> str:
    """Detecta oportunidades y anomalias del catalogo: ofertas (precio muy bajo vs referencia),
    bajadas de mas del 10% respecto a la media de 30 dias, subidas de mas del 20% (posible error)
    y articulos agotados.
    Args:
        (sin argumentos)
    """
    alertas = []
    for a in CATALOGO:
        regs = HISTORICO.get(a["id"], [])
        precios30 = [r["precio"] for r in regs[-30:]]
        media30 = statistics.mean(precios30) if precios30 else a["precio"]
        if a["precio"] < a["precio_referencia"] * 0.85:
            alertas.append(f"OFERTA: {a['id']} {a['nombre']} - {a['precio']:.2f} eur "
                           f"(referencia {a['precio_referencia']:.2f} eur)")
        if media30 and (media30 - a["precio"]) / media30 > 0.10:
            alertas.append(f"BAJADA >10% vs media 30d: {a['id']} {a['nombre']} - ahora {a['precio']:.2f} eur "
                           f"(media {media30:.2f} eur)")
        if media30 and (a["precio"] - media30) / media30 > 0.20:
            alertas.append(f"SUBIDA >20% (revisar): {a['id']} {a['nombre']} - ahora {a['precio']:.2f} eur "
                           f"(media {media30:.2f} eur)")
        if a["stock"] == 0:
            alertas.append(f"AGOTADO: {a['id']} {a['nombre']}")
    return "\n".join(alertas) if alertas else "Sin alertas: el catalogo esta tranquilo."


# ---------- modelo ----------
# Modelo configurable por variable de entorno. Ejemplos:
#   gemini/gemini-3.6-flash     (necesita GEMINI_API_KEY, gratis en aistudio.google.com)
#   openai/gpt-4o               (necesita OPENAI_API_KEY)
#   groq/qwen3-32b              (necesita GROQ_API_KEY, gratis en console.groq.com)
MODELO_ID = os.environ.get("MODELO_ID", "gemini/gemini-3.6-flash")

modelo = LiteLLMModel(
    model_id=MODELO_ID,
    max_tokens=2096,
)

agente = CodeAgent(
    model=modelo,
    tools=[listar_categorias, listar_articulos, buscar_articulos,
           historial_precio, resumen_categoria, detectar_alertas],
    max_steps=8,
    verbosity_level=1,
)

if __name__ == "__main__":
    from smolagents.gradio_ui import GradioUI
    GradioUI(agente).launch()

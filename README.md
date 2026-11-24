# Agente Centinela

Agente conversacional construido con [smolagents](https://github.com/huggingface/smolagents)
que vigila un catálogo de productos: precios, stock, histórico y alertas de compra.
Responde en lenguaje natural usando seis herramientas propias (`@tool`).

## Qué puede responder

- *"¿Qué móviles hay con stock por menos de 300 €?"*
- *"¿Qué artículos han bajado más de un 10% respecto a su media?"*
- *"¿Qué está de oferta?"* / *"¿Qué está agotado?"*
- *"Hazme un informe de la categoría portátiles"*
- *"¿Cómo ha evolucionado el precio del ART-0007 este último mes?"*

## Herramientas del agente

| Herramienta | Qué hace |
|---|---|
| `listar_categorias` | Categorías del catálogo y nº de artículos |
| `listar_articulos` | Artículos, filtrables por categoría |
| `buscar_articulos` | Búsqueda por nombre o id |
| `historial_precio` | Histórico de precios con estadísticas |
| `resumen_categoria` | Informe: precio medio, más barato, más caro, agotados |
| `detectar_alertas` | Ofertas, bajadas >10% vs media 30 días, subidas >20%, agotados |

Las reglas de alerta siguen el enunciado del proyecto **Centinela** (Escuela Musk):
bajada de precio vs referencia, caída >10% respecto a la media de 30 días,
reposición de stock y subidas >20% (posible error de la tienda).

## Datos

`catalogo.json` (60 artículos ficticios en 6 categorías) y `historico_precios.csv`
(120 días de precios y stock). Son datos de ejemplo con semilla fija, publicables
sin restricciones.

## Requisitos

- Python 3.10+
- Una clave de API de alguno de estos proveedores (litellm soporta muchos más):
  - **Gemini** — gratis en [aistudio.google.com](https://aistudio.google.com) → `GEMINI_API_KEY`
  - **OpenAI** — [platform.openai.com](https://platform.openai.com) → `OPENAI_API_KEY`
  - **Groq** — gratis en [console.groq.com](https://console.groq.com) → `GROQ_API_KEY`

## Instalación y uso

```bash
pip install smolagents litellm "gradio<6"

export GEMINI_API_KEY="tu_clave"        # o OPENAI_API_KEY / GROQ_API_KEY
export MODELO_ID="gemini/gemini-3.6-flash"   # u "openai/gpt-4o", "groq/qwen3-32b", ...

python agente_centinela.py
```

Se abre una interfaz de chat en `http://127.0.0.1:7860` (añade `share=True` a
`launch()` en Colab para obtener un enlace público temporal).

## Cómo funciona

Es un `CodeAgent` de smolagents: el modelo razona, escribe código Python que llama
a las herramientas, ejecuta las acciones en un bucle y devuelve la respuesta final.
El modelo se conecta a través de `LiteLLMModel`, así que cambiar de proveedor
consiste en cambiar una cadena (`model_id`).

## Autor

Proyecto del curso de Agentes de Hugging Face (use case assignment, Unidad 3),
con los datos del proyecto transversal Centinela del curso de Python de Escuela Musk.

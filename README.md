# 🎧 Spotify AI Assistant

Asistente musical inteligente construido con **Microsoft Foundry**. Ayuda a descubrir música nueva, entender géneros y artistas, y analizar hábitos de escucha. Se puede usar desde la terminal o desde una interfaz web.

> Proyecto del **Challenge – Day 4** (Microsoft Foundry Labs · Tecnun).

---

## 🤖 Descripción del agente

**Spotify AI Assistant** es un agente creado en el portal de Microsoft Foundry (`spotify-ai-assistant`) sobre el modelo existente del proyecto del laboratorio (`gpt-5.4-mini`). Actúa como un experto musical cercano y entusiasta: recomienda música explicando *por qué* encaja con los gustos del usuario, responde preguntas sobre géneros, artistas e historia de la música, y analiza datos de escucha con cálculos y gráficos reales.

### Funciones principales

| Función | Qué hace | Ejemplo de pregunta |
|---|---|---|
| 🎵 **Music Discovery** | Recomienda artistas, álbumes y canciones según los gustos del usuario y explica cada recomendación. | *«Me gusta Arctic Monkeys y The Strokes. Recomiéndame cinco grupos.»* |
| 📊 **Listening Analytics** | Analiza los datos de escucha que aporta el usuario (canciones, artistas, reproducciones) y genera estadísticas y gráficos ejecutando Python. | *«Analiza mis canciones más escuchadas y crea un gráfico por género.»* |
| 📚 **Music Expert** | Responde preguntas sobre géneros, artistas e historia de la música usando una base de conocimiento propia. | *«¿Qué diferencias hay entre el indie rock y el alternative rock?»* |
| 🎧 **Playlist Ideas** | Diseña conceptos de playlist para cada situación (estudiar, gimnasio, viajar, fiesta…). | *«Hazme una playlist para estudiar durante dos horas.»* |

### Componentes configurados en Foundry

- **Instrucciones del sistema:** definen la personalidad del agente, sus cuatro funciones y sus reglas. Por ejemplo, no inventar estadísticas, no decir que tiene acceso a una cuenta real de Spotify y responder en el idioma del usuario.
- **Code Interpreter:** ejecuta Python en un entorno aislado para hacer cálculos exactos y generar gráficos, en lugar de estimar las cifras.
- **Custom Data (RAG):** base de conocimiento creada a partir de cuatro PDF propios (carpeta `documents/`), indexados en Azure AI Search por el profesor:
  - `01_music_genres_guide.pdf`: géneros, subgéneros y la *Energy Scale* (1–5) definida por el proyecto.
  - `02_artist_discovery_guide.pdf`: perfiles de artistas y *Discovery Ladders*.
  - `03_music_recommendations.pdf`: música recomendada por situación y playlists del proyecto, como la *Tecnun Study Session*.
  - `04_music_history_trends.pdf`: historia de la música y tendencias actuales.
- **MCP server:** integración con una fuente externa de información musical (metadatos de artistas y álbumes) para datos que no aparecen en los documentos.

### Límites (por diseño)

- El agente **no** accede a ninguna cuenta real de Spotify ni crea o modifica playlists en Spotify. Las playlists son propuestas.
- Los datos de escucha que analiza son los que el usuario le proporciona en la conversación.
- Si una información no está disponible o no se puede verificar, el agente lo indica en lugar de inventarla.

---

## 🏗️ Arquitectura

```
Usuario
  │
  ├── Terminal  (src/app.py)
  └── Web       (src/web.py · Gradio)
        │
        ▼
Python + Microsoft Foundry SDK (azure-ai-projects)
Autenticación con Microsoft Entra ID (DefaultAzureCredential)
        │
        ▼
Agente "spotify-ai-assistant" en Microsoft Foundry
  ├── Modelo existente del proyecto
  ├── Instrucciones del sistema
  ├── Code Interpreter      → estadísticas y gráficos
  ├── Knowledge base (RAG)  → PDFs musicales en Azure AI Search
  └── MCP server            → información musical externa
```

La aplicación no guarda claves en el código. Se autentica con la sesión de Azure del usuario (`az login`) y se conecta al agente por su nombre, mediante la API de *Responses/Conversations* del SDK. Cada sesión mantiene su propia conversación, así que el agente recuerda el contexto de las preguntas anteriores.

---

## 📁 Estructura del proyecto

```
├── documents/          # PDFs de la base de conocimiento (RAG)
├── outputs/            # Gráficos descargados de Code Interpreter (no se sube a git)
├── src/
│   ├── app.py          # Interfaz de terminal (menú)
│   └── web.py          # Interfaz web (Gradio)
├── .devcontainer/      # Configuración para GitHub Codespaces
├── .env                # Configuración local (NO se sube a git)
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

**Requisitos:** Python 3.10 o superior, Azure CLI y acceso (rol *Azure AI User*) al proyecto de Foundry del laboratorio.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux / Codespaces
source .venv/bin/activate

pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz del proyecto:

```
PROJECT_ENDPOINT=https://<recurso>.services.ai.azure.com/api/projects/<proyecto>
AGENT_NAME=spotify-ai-assistant
```

Inicia sesión en Azure:

```bash
az login                    # en local
az login --use-device-code  # en GitHub Codespaces
```

---

## ▶️ Ejecución

**Terminal**

```bash
python src/app.py
```

**Web:** abre `src/web.py` en VS Code y pulsa ▶ (*Run Python File*), o ejecuta:

```bash
python src/web.py
```

Se abrirá el navegador en `http://127.0.0.1:7860`.

---

## 🧪 Pruebas realizadas

| # | Prompt | Qué demuestra |
|---|---|---|
| 1 | *Recommend five artists similar to Arctic Monkeys.* | Instrucciones / descubrimiento musical |
| 2 | *Explain the difference between indie rock and alternative rock.* | RAG con citas a los PDFs |
| 3 | *What is the Discovery Ladder for Arctic Monkeys?* | RAG con información exclusiva de los documentos |
| 4 | *Analiza estos datos de escucha y crea un gráfico de reproducciones por género.* | Code Interpreter (cálculo y gráfico) |
| 5 | *Search for information about Daft Punk's albums.* | Integración MCP |
| 6 | *Create a playlist concept for a gym workout.* | Recomendación personalizada |

---

## 🛠️ Tecnologías

Microsoft Foundry · Foundry SDK para Python (`azure-ai-projects`) · Azure Identity · Azure AI Search · Code Interpreter · MCP · Gradio

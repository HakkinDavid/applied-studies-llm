# applied-llm
DOCUMENTACIÓN GENERAL DEL BACKEND
Proyecto: Applied Studies LLM
Archivo: DOCUMENTACION_GENERAL_BACKEND.txt


1. RESUMEN GENERAL


El backend es una API construida con FastAPI que permite subir material de estudio,
extraer su contenido, organizarlo dentro de un bosque de conocimiento y generar
un banco de preguntas usando un servicio de IA compatible con la librería de
OpenAI.

El frontend puede consumir las preguntas de dos formas:

1. Como JSON:
   GET /api/question-bank

2. Como archivo JavaScript compatible con el frontend actual:
   GET /egel/banco_preguntas.js

Este segundo endpoint produce:

   window.questions = [...];

Así el frontend puede seguir usando el banco como si fuera un archivo local.


2. FUNCIONAMIENTO GENERAL


El flujo principal del backend es:

1. El usuario sube un archivo.
2. El backend valida extensión, tamaño y contenido.
3. Se calcula el SHA-256 del archivo.
4. El archivo se guarda usando el SHA-256 como nombre.
5. Se extrae el texto del documento.
6. Se generan fragmentos de referencia del documento.
7. El documento se clasifica dentro de un bosque de conocimiento.
8. El sistema crea o reutiliza árbol, nodo y hoja.
9. La IA genera preguntas de opción múltiple.
10. Cada pregunta queda asociada al documento original y a un extracto.
11. Las preguntas se guardan en question_bank.json.
12. El frontend puede leerlas desde /egel/banco_preguntas.js.


3. ESTRUCTURA GENERAL DEL BACKEND


C:.
├───.venv
│   ├───Include
│   ├───Lib
│   │   └───site-packages
│   │       ├───annotated_doc
│   │       │   └───__pycache__
│   │       ├───annotated_doc-0.0.4.dist-info
│   │       │   └───licenses
│   │       ├───annotated_types
│   │       │   └───__pycache__
│   │       ├───annotated_types-0.7.0.dist-info
│   │       │   └───licenses
│   │       ├───anyio
│   │       │   ├───abc
│   │       │   │   └───__pycache__
│   │       │   ├───streams
│   │       │   │   └───__pycache__
│   │       │   ├───_backends
│   │       │   │   └───__pycache__
│   │       │   ├───_core
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───anyio-4.13.0.dist-info
│   │       │   └───licenses
│   │       ├───certifi
│   │       │   └───__pycache__
│   │       ├───certifi-2026.4.22.dist-info
│   │       │   └───licenses
│   │       ├───click
│   │       │   └───__pycache__
│   │       ├───click-8.3.3.dist-info
│   │       │   └───licenses
│   │       ├───colorama
│   │       │   ├───tests
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───colorama-0.4.6.dist-info
│   │       │   └───licenses
│   │       ├───distro
│   │       │   └───__pycache__
│   │       ├───distro-1.9.0.dist-info
│   │       ├───docx
│   │       │   ├───dml
│   │       │   │   └───__pycache__
│   │       │   ├───drawing
│   │       │   │   └───__pycache__
│   │       │   ├───enum
│   │       │   │   └───__pycache__
│   │       │   ├───image
│   │       │   │   └───__pycache__
│   │       │   ├───opc
│   │       │   │   ├───parts
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───oxml
│   │       │   │   ├───text
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───parts
│   │       │   │   └───__pycache__
│   │       │   ├───styles
│   │       │   │   └───__pycache__
│   │       │   ├───templates
│   │       │   │   └───default-docx-template
│   │       │   │       ├───customXml
│   │       │   │       │   └───_rels
│   │       │   │       ├───docProps
│   │       │   │       ├───word
│   │       │   │       │   ├───theme
│   │       │   │       │   └───_rels
│   │       │   │       └───_rels
│   │       │   ├───text
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───dotenv
│   │       │   └───__pycache__
│   │       ├───fastapi
│   │       │   ├───.agents
│   │       │   │   └───skills
│   │       │   │       └───fastapi
│   │       │   │           └───references
│   │       │   ├───dependencies
│   │       │   │   └───__pycache__
│   │       │   ├───middleware
│   │       │   │   └───__pycache__
│   │       │   ├───openapi
│   │       │   │   └───__pycache__
│   │       │   ├───security
│   │       │   │   └───__pycache__
│   │       │   ├───_compat
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───fastapi-0.136.1.dist-info
│   │       │   └───licenses
│   │       ├───h11
│   │       │   └───__pycache__
│   │       ├───h11-0.16.0.dist-info
│   │       │   └───licenses
│   │       ├───httpcore
│   │       │   ├───_async
│   │       │   │   └───__pycache__
│   │       │   ├───_backends
│   │       │   │   └───__pycache__
│   │       │   ├───_sync
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───httpcore-1.0.9.dist-info
│   │       │   └───licenses
│   │       ├───httpx
│   │       │   ├───_transports
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───httpx-0.28.1.dist-info
│   │       │   └───licenses
│   │       ├───idna
│   │       │   └───__pycache__
│   │       ├───idna-3.15.dist-info
│   │       │   └───licenses
│   │       ├───jiter
│   │       │   └───__pycache__
│   │       ├───jiter-0.14.0.dist-info
│   │       │   ├───licenses
│   │       │   └───sboms
│   │       ├───lxml
│   │       │   ├───html
│   │       │   │   └───__pycache__
│   │       │   ├───includes
│   │       │   │   ├───extlibs
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───libexslt
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───libxml
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───libxslt
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───isoschematron
│   │       │   │   ├───resources
│   │       │   │   │   ├───rng
│   │       │   │   │   └───xsl
│   │       │   │   │       └───iso-schematron-xslt1
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───lxml-6.1.0.dist-info
│   │       │   └───licenses
│   │       ├───multipart
│   │       │   └───__pycache__
│   │       ├───openai
│   │       │   ├───auth
│   │       │   │   └───__pycache__
│   │       │   ├───helpers
│   │       │   │   └───__pycache__
│   │       │   ├───lib
│   │       │   │   ├───streaming
│   │       │   │   │   ├───chat
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───responses
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───_parsing
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───resources
│   │       │   │   ├───admin
│   │       │   │   │   ├───organization
│   │       │   │   │   │   ├───groups
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   ├───projects
│   │       │   │   │   │   │   ├───groups
│   │       │   │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   │   ├───users
│   │       │   │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   ├───users
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───audio
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───beta
│   │       │   │   │   ├───chatkit
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───realtime
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───threads
│   │       │   │   │   │   ├───runs
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───chat
│   │       │   │   │   ├───completions
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───containers
│   │       │   │   │   ├───files
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───conversations
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───evals
│   │       │   │   │   ├───runs
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───fine_tuning
│   │       │   │   │   ├───alpha
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───checkpoints
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───jobs
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───realtime
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───responses
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───skills
│   │       │   │   │   ├───versions
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───uploads
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───vector_stores
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───webhooks
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───types
│   │       │   │   ├───admin
│   │       │   │   │   ├───organization
│   │       │   │   │   │   ├───groups
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   ├───projects
│   │       │   │   │   │   │   ├───groups
│   │       │   │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   │   ├───users
│   │       │   │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   ├───users
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───audio
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───beta
│   │       │   │   │   ├───chat
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───chatkit
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───realtime
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───threads
│   │       │   │   │   │   ├───runs
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───chat
│   │       │   │   │   ├───completions
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───containers
│   │       │   │   │   ├───files
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───conversations
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───evals
│   │       │   │   │   ├───runs
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───fine_tuning
│   │       │   │   │   ├───alpha
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───checkpoints
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───jobs
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───graders
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───realtime
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───responses
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───shared
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───shared_params
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───skills
│   │       │   │   │   ├───versions
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───uploads
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───vector_stores
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───webhooks
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───_extras
│   │       │   │   └───__pycache__
│   │       │   ├───_utils
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───openai-2.36.0.dist-info
│   │       │   └───licenses
│   │       ├───pip
│   │       │   ├───_internal
│   │       │   │   ├───cli
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───commands
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───distributions
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───index
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───locations
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───metadata
│   │       │   │   │   ├───importlib
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───models
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───network
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───operations
│   │       │   │   │   ├───build
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───install
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───req
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───resolution
│   │       │   │   │   ├───legacy
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───resolvelib
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───utils
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───vcs
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───_vendor
│   │       │   │   ├───cachecontrol
│   │       │   │   │   ├───caches
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───certifi
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───distlib
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───distro
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───idna
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───msgpack
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───packaging
│   │       │   │   │   ├───licenses
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───pkg_resources
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───platformdirs
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───pygments
│   │       │   │   │   ├───filters
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───formatters
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───lexers
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───styles
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───pyproject_hooks
│   │       │   │   │   ├───_in_process
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───requests
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───resolvelib
│   │       │   │   │   ├───resolvers
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───rich
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───tomli
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───tomli_w
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───truststore
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───urllib3
│   │       │   │   │   ├───contrib
│   │       │   │   │   │   ├───emscripten
│   │       │   │   │   │   │   └───__pycache__
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───http2
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   ├───util
│   │       │   │   │   │   └───__pycache__
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───pip-26.1.1.dist-info
│   │       │   └───licenses
│   │       │       └───src
│   │       │           └───pip
│   │       │               └───_vendor
│   │       │                   ├───cachecontrol
│   │       │                   ├───certifi
│   │       │                   ├───distlib
│   │       │                   ├───distro
│   │       │                   ├───idna
│   │       │                   ├───msgpack
│   │       │                   ├───packaging
│   │       │                   ├───pkg_resources
│   │       │                   ├───platformdirs
│   │       │                   ├───pygments
│   │       │                   ├───pyproject_hooks
│   │       │                   ├───requests
│   │       │                   ├───resolvelib
│   │       │                   ├───rich
│   │       │                   ├───tomli
│   │       │                   ├───tomli_w
│   │       │                   ├───truststore
│   │       │                   └───urllib3
│   │       ├───pydantic
│   │       │   ├───deprecated
│   │       │   │   └───__pycache__
│   │       │   ├───experimental
│   │       │   │   └───__pycache__
│   │       │   ├───plugin
│   │       │   │   └───__pycache__
│   │       │   ├───v1
│   │       │   │   └───__pycache__
│   │       │   ├───_internal
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───pydantic-2.13.4.dist-info
│   │       │   └───licenses
│   │       ├───pydantic_core
│   │       │   └───__pycache__
│   │       ├───pydantic_core-2.46.4.dist-info
│   │       │   ├───licenses
│   │       │   └───sboms
│   │       ├───pypdf
│   │       │   ├───annotations
│   │       │   │   └───__pycache__
│   │       │   ├───generic
│   │       │   │   └───__pycache__
│   │       │   ├───_codecs
│   │       │   │   └───__pycache__
│   │       │   ├───_crypt_providers
│   │       │   │   └───__pycache__
│   │       │   ├───_text_extraction
│   │       │   │   ├───_layout_mode
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───pypdf-6.11.0.dist-info
│   │       │   └───licenses
│   │       ├───python_docx-1.2.0.dist-info
│   │       │   └───licenses
│   │       ├───python_dotenv-1.2.2.dist-info
│   │       │   └───licenses
│   │       ├───python_multipart
│   │       │   └───__pycache__
│   │       ├───python_multipart-0.0.28.dist-info
│   │       │   └───licenses
│   │       ├───sniffio
│   │       │   ├───_tests
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───sniffio-1.3.1.dist-info
│   │       ├───starlette
│   │       │   ├───middleware
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───starlette-1.0.0.dist-info
│   │       │   └───licenses
│   │       ├───tqdm
│   │       │   ├───contrib
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───tqdm-4.67.3.dist-info
│   │       │   └───licenses
│   │       ├───typing_extensions-4.15.0.dist-info
│   │       │   └───licenses
│   │       ├───typing_inspection
│   │       │   └───__pycache__
│   │       ├───typing_inspection-0.4.2.dist-info
│   │       │   └───licenses
│   │       ├───uvicorn
│   │       │   ├───lifespan
│   │       │   │   └───__pycache__
│   │       │   ├───loops
│   │       │   │   └───__pycache__
│   │       │   ├───middleware
│   │       │   │   └───__pycache__
│   │       │   ├───protocols
│   │       │   │   ├───http
│   │       │   │   │   └───__pycache__
│   │       │   │   ├───websockets
│   │       │   │   │   └───__pycache__
│   │       │   │   └───__pycache__
│   │       │   ├───supervisors
│   │       │   │   └───__pycache__
│   │       │   └───__pycache__
│   │       ├───uvicorn-0.46.0.dist-info
│   │       │   └───licenses
│   │       └───__pycache__
│   └───Scripts
├───app
│   ├───core
│   │   └───__pycache__
│   ├───models
│   │   └───__pycache__
│   ├───routes
│   │   └───__pycache__
│   ├───services
│   │   └───__pycache__
│   └───__pycache__
├───storage
│   ├───references
│   ├───texts
│   └───uploads
└───__pycache__


4. CARPETAS IMPORTANTES

backend/app/core/
Guarda configuración general y rutas del sistema.

backend/app/models/
Guarda los modelos Pydantic que definen la forma de las respuestas.

backend/app/services/
Guarda la lógica principal del sistema: IA, archivos, texto, preguntas, bosque
de conocimiento y almacenamiento.

backend/app/routes/
Guarda los endpoints de la API.

backend/storage/uploads/
Guarda los documentos originales usando SHA-256 como nombre.

backend/storage/texts/
Guarda el texto extraído de cada documento.

backend/storage/references/
Guarda fragmentos del documento que después se asocian a preguntas.

backend/storage/materials.json
Índice de materiales subidos.

backend/storage/question_bank.json
Banco de preguntas generado.

backend/storage/knowledge_forest.json
Bosque de conocimiento construido por el sistema.


5. ENDPOINTS PRINCIPALES PARA EL FRONTEND


GET /api/health
Verifica que el backend esté funcionando y que el servicio de IA esté configurado.

POST /api/materials/upload
Sube un documento, lo procesa y genera preguntas.

GET /api/materials
Lista los documentos registrados.

GET /api/materials/{material_id}/references
Devuelve los fragmentos de referencia de un documento.

GET /api/question-bank
Devuelve el banco de preguntas en formato JSON.

DELETE /api/question-bank
Borra el banco de preguntas. Sirve para pruebas.

GET /api/knowledge-forest
Devuelve el bosque de conocimiento.

DELETE /api/knowledge-forest
Borra el bosque. Sirve para pruebas.

GET /egel/banco_preguntas.js
Devuelve el banco en formato JavaScript para el frontend:
window.questions = [...];


6. FORMATO DE PREGUNTA QUE RECIBE EL FRONTEND


Cada pregunta generada tiene esta estructura principal:

{
  "q": "Texto de la pregunta",
  "options": ["Opción 1", "Opción 2", "Opción 3", "Opción 4"],
  "answer": 0,
  "area": "Soluciones de cómputo inteligente",
  "subarea": "Tema específico",
  "synthetic": true,
  "source_material_id": "...",
  "source_document_id": "...",
  "source_document_name": "archivo.pdf",
  "source_ref_id": "p2-1",
  "source_page": 2,
  "source_excerpt": "Extracto breve del documento...",
  "tree_id": "...",
  "tree_name": "...",
  "node_id": "...",
  "node_name": "...",
  "leaf_id": "...",
  "leaf_name": "...",
  "knowledge_path": "Árbol > Nodo > Hoja"
}

Campos principales para el frontend:

q:
Texto de la pregunta.

options:
Lista de 4 opciones.

answer:
Índice de la respuesta correcta. Va de 0 a 3.

area:
Área compatible con los filtros del frontend actual.

subarea:
Tema o subtema de la pregunta.

synthetic:
Indica si la pregunta fue generada por IA.

source_document_name:
Nombre original del documento.

source_page:
Página aproximada del PDF. Puede ser null en DOCX, TXT o MD.

source_excerpt:
Extracto del documento para mostrar en el ícono de información.

knowledge_path:
Ruta del tema dentro del bosque de conocimiento.


7. VARIABLES IMPORTANTES


Nombre: OPENAI_API_KEY
Tipo: string
Archivo: app/core/config.py
Qué hace: Guarda la clave de acceso al proveedor de IA.
Cómo lo hace: Se carga desde el archivo .env usando os.getenv.

Nombre: OPENAI_BASE_URL
Tipo: string
Archivo: app/core/config.py
Qué hace: Define la URL base del proveedor compatible con OpenAI.
Cómo lo hace: Se carga desde .env y se usa para inicializar el cliente de IA.

Nombre: MODEL
Tipo: string
Archivo: app/core/config.py
Qué hace: Define el modelo usado para clasificar materiales y generar preguntas.
Cómo lo hace: Se carga desde .env y se manda en cada llamada al servicio de IA.

Nombre: MAX_FILE_SIZE_MB
Tipo: int
Archivo: app/core/config.py
Qué hace: Define el tamaño máximo permitido para archivos.
Cómo lo hace: Se lee desde .env; si no existe usa 10.

Nombre: MAX_FILE_SIZE_BYTES
Tipo: int
Archivo: app/core/config.py
Qué hace: Convierte el límite de MB a bytes.
Cómo lo hace: Multiplica MAX_FILE_SIZE_MB por 1024 * 1024.

Nombre: DEFAULT_QUESTION_COUNT
Tipo: int
Archivo: app/core/config.py
Qué hace: Define cuántas preguntas se generan por defecto.
Cómo lo hace: Se carga desde .env; si no existe usa 15.

Nombre: ALLOWED_EXTENSIONS
Tipo: set[str]
Archivo: app/core/config.py
Qué hace: Define los formatos permitidos.
Cómo lo hace: Contiene .pdf, .txt, .md y .docx.

Nombre: FRONTEND_COMPATIBLE_AREAS
Tipo: list[str]
Archivo: app/core/config.py
Qué hace: Mantiene compatibilidad con las áreas fijas del frontend.
Cómo lo hace: La IA elige una de estas áreas al generar preguntas.

Nombre: MAX_REFERENCE_CHARS
Tipo: int
Archivo: app/core/config.py
Qué hace: Define el tamaño máximo del extracto mostrado como referencia.
Cómo lo hace: Limita el texto que se guarda en source_excerpt.

Nombre: MAX_REFERENCES_FOR_PROMPT
Tipo: int
Archivo: app/core/config.py
Qué hace: Define cuántas referencias se mandan al modelo para elegir fuente.
Cómo lo hace: Limita el bloque de referencias dentro del prompt.

Nombre: BACKEND_DIR
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Representa la carpeta backend.
Cómo lo hace: Se calcula desde la ubicación del archivo paths.py.

Nombre: PROJECT_ROOT
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Representa la raíz del proyecto.
Cómo lo hace: Se obtiene subiendo un nivel desde backend.

Nombre: STORAGE_DIR
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Ruta donde se guardan datos generados.
Cómo lo hace: Apunta a backend/storage.

Nombre: UPLOADS_DIR
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Ruta donde se guardan archivos originales.
Cómo lo hace: Apunta a backend/storage/uploads.

Nombre: TEXTS_DIR
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Ruta donde se guardan textos extraídos.
Cómo lo hace: Apunta a backend/storage/texts.

Nombre: REFERENCES_DIR
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Ruta donde se guardan fragmentos de referencia.
Cómo lo hace: Apunta a backend/storage/references.

Nombre: QUESTION_BANK_FILE
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Ruta del banco de preguntas.
Cómo lo hace: Apunta a backend/storage/question_bank.json.

Nombre: KNOWLEDGE_FOREST_FILE
Tipo: Path
Archivo: app/core/paths.py
Qué hace: Ruta del bosque de conocimiento.
Cómo lo hace: Apunta a backend/storage/knowledge_forest.json.


8. FUNCIONES IMPORTANTES PARA EL FRONTEND Y LA API


Nombre: health
Tipo: función endpoint
Archivo: app/routes/health.py
Qué hace: Devuelve el estado del backend.
Cómo lo hace: Retorna status, mensaje, ai_configured, base_url y model.

Nombre: upload_material
Tipo: función endpoint async
Archivo: app/routes/materials.py
Qué hace: Recibe un archivo y genera preguntas.
Cómo lo hace: Valida el archivo, calcula SHA-256, extrae texto, genera referencias,
clasifica el material, genera preguntas y guarda metadatos.

Nombre: list_materials
Tipo: función endpoint
Archivo: app/routes/materials.py
Qué hace: Devuelve la lista de materiales subidos.
Cómo lo hace: Lee materials.json y ordena los materiales por fecha.

Nombre: get_material_references
Tipo: función endpoint
Archivo: app/routes/materials.py
Qué hace: Devuelve los fragmentos de referencia de un documento.
Cómo lo hace: Lee storage/references/{material_id}.json.

Nombre: get_question_bank
Tipo: función endpoint
Archivo: app/routes/questions.py
Qué hace: Devuelve todas las preguntas en JSON.
Cómo lo hace: Lee question_bank.json y devuelve total y questions.

Nombre: serve_question_bank_js
Tipo: función endpoint
Archivo: app/routes/questions.py
Qué hace: Devuelve el banco en formato JavaScript para el frontend.
Cómo lo hace: Lee question_bank.json y genera window.questions = [...];

Nombre: get_knowledge_forest
Tipo: función endpoint
Archivo: app/routes/forest.py
Qué hace: Devuelve el bosque de conocimiento.
Cómo lo hace: Lee knowledge_forest.json.

Nombre: serve_frontend_root
Tipo: función endpoint
Archivo: app/routes/frontend.py
Qué hace: Sirve el frontend compilado o muestra rutas útiles.
Cómo lo hace: Busca frontend/build/index.html.

Nombre: serve_frontend
Tipo: función endpoint
Archivo: app/routes/frontend.py
Qué hace: Sirve archivos estáticos del frontend.
Cómo lo hace: Busca el archivo solicitado dentro de frontend/build.


9. FUNCIONES IMPORTANTES DE ARCHIVOS


Nombre: calculate_sha256
Tipo: función
Archivo: app/services/files.py
Qué hace: Calcula el SHA-256 de un archivo.
Cómo lo hace: Usa hashlib.sha256 sobre los bytes del archivo.

Nombre: get_extension
Tipo: función
Archivo: app/services/files.py
Qué hace: Obtiene la extensión del archivo.
Cómo lo hace: Usa Path(filename).suffix.lower().

Nombre: validate_file
Tipo: función
Archivo: app/services/files.py
Qué hace: Valida extensión, tamaño y que el archivo no esté vacío.
Cómo lo hace: Compara contra ALLOWED_EXTENSIONS y MAX_FILE_SIZE_BYTES.


10. FUNCIONES IMPORTANTES DE TEXTO Y REFERENCIAS


Nombre: extract_text_and_references
Tipo: función
Archivo: app/services/text.py
Qué hace: Extrae texto y referencias del documento.
Cómo lo hace: Elige extractor según extensión: PDF, DOCX, TXT o MD.

Nombre: extract_pdf_text_and_references
Tipo: función
Archivo: app/services/text.py
Qué hace: Extrae texto de PDF y genera referencias por página.
Cómo lo hace: Usa pypdf para leer páginas y crea ref_id como p1-1, p2-1.

Nombre: extract_docx_text_and_references
Tipo: función
Archivo: app/services/text.py
Qué hace: Extrae texto de DOCX y genera referencias por párrafo.
Cómo lo hace: Usa python-docx y crea ref_id como par1-1.

Nombre: extract_plain_text_and_references
Tipo: función
Archivo: app/services/text.py
Qué hace: Extrae texto de TXT o MD y genera referencias.
Cómo lo hace: Decodifica el archivo y lo divide en fragmentos.

Nombre: clean_text
Tipo: función
Archivo: app/services/text.py
Qué hace: Limpia el texto extraído.
Cómo lo hace: Quita líneas vacías y espacios innecesarios.

Nombre: clean_references
Tipo: función
Archivo: app/services/text.py
Qué hace: Limpia fragmentos de referencia.
Cómo lo hace: Compacta espacios y genera extractos cortos.

Nombre: references_for_prompt
Tipo: función
Archivo: app/services/text.py
Qué hace: Prepara las referencias para que el modelo elija source_ref_id.
Cómo lo hace: Convierte cada referencia en una línea con id, página y extracto.

Nombre: limit_text_for_generation
Tipo: función
Archivo: app/services/text.py
Qué hace: Limita texto largo antes de mandarlo al modelo.
Cómo lo hace: Conserva inicio y final del documento.


11. FUNCIONES IMPORTANTES DE IA


Nombre: client
Tipo: OpenAI
Archivo: app/services/ai.py
Qué hace: Cliente de conexión al servicio de IA.
Cómo lo hace: Se inicializa con OPENAI_API_KEY, OPENAI_BASE_URL y MODEL.

Nombre: is_ai_configured
Tipo: función
Archivo: app/services/ai.py
Qué hace: Indica si el cliente de IA está listo.
Cómo lo hace: Revisa si client no es None.

Nombre: ensure_ai_client
Tipo: función
Archivo: app/services/ai.py
Qué hace: Valida configuración antes de usar IA.
Cómo lo hace: Revisa OPENAI_BASE_URL, OPENAI_API_KEY, MODEL y client.

Nombre: call_ai_text
Tipo: función
Archivo: app/services/ai.py
Qué hace: Llama al modelo y devuelve texto.
Cómo lo hace: Usa client.chat.completions.create.

Nombre: call_ai_json
Tipo: función
Archivo: app/services/ai.py
Qué hace: Llama al modelo y devuelve JSON.
Cómo lo hace: Usa call_ai_text y luego extract_json_from_model_text.


12. FUNCIONES IMPORTANTES DEL BOSQUE DE CONOCIMIENTO


Nombre: normalize_frontend_area
Tipo: función
Archivo: app/services/forest.py
Qué hace: Asegura que el área sea compatible con el frontend.
Cómo lo hace: Si el área no está en FRONTEND_COMPATIBLE_AREAS, usa una por defecto.

Nombre: summarize_forest_for_prompt
Tipo: función
Archivo: app/services/forest.py
Qué hace: Convierte el bosque actual en texto.
Cómo lo hace: Recorre árboles, nodos y hojas existentes.

Nombre: build_knowledge_classification_prompt
Tipo: función
Archivo: app/services/forest.py
Qué hace: Crea el prompt para clasificar un documento.
Cómo lo hace: Incluye bosque actual, pista opcional y material.

Nombre: classify_material_for_forest
Tipo: función
Archivo: app/services/forest.py
Qué hace: Clasifica el documento dentro del bosque.
Cómo lo hace: Llama a IA y espera JSON con tree, node, leaf y frontend_area.

Nombre: update_knowledge_forest
Tipo: función
Archivo: app/services/forest.py
Qué hace: Crea o actualiza árbol, nodo y hoja.
Cómo lo hace: Busca si existen; si no, crea ids con slugify y guarda el material.

Nombre: find_existing_tree_id
Tipo: función
Archivo: app/services/forest.py
Qué hace: Busca un árbol existente.
Cómo lo hace: Compara nombres normalizados.

Nombre: find_existing_node_id
Tipo: función
Archivo: app/services/forest.py
Qué hace: Busca un nodo existente dentro del árbol.
Cómo lo hace: Compara nombres normalizados.

Nombre: find_existing_leaf_id
Tipo: función
Archivo: app/services/forest.py
Qué hace: Busca una hoja existente dentro del nodo.
Cómo lo hace: Compara nombres normalizados.


13. FUNCIONES IMPORTANTES DE PREGUNTAS


Nombre: normalize_answer
Tipo: función
Archivo: app/services/questions.py
Qué hace: Convierte la respuesta correcta al índice que usa el frontend.
Cómo lo hace: Acepta 0-3, "0"-"3" o "A"-"D".

Nombre: get_reference_by_id
Tipo: función
Archivo: app/services/questions.py
Qué hace: Busca una referencia por source_ref_id.
Cómo lo hace: Recorre la lista de referencias y compara ref_id.

Nombre: fallback_reference
Tipo: función
Archivo: app/services/questions.py
Qué hace: Da una referencia de respaldo.
Cómo lo hace: Usa la primera referencia disponible.

Nombre: normalize_question
Tipo: función
Archivo: app/services/questions.py
Qué hace: Convierte una pregunta generada por IA al formato final.
Cómo lo hace: Valida q, options, answer y agrega campos de referencia y bosque.

Nombre: build_question_generation_prompt
Tipo: función
Archivo: app/services/questions.py
Qué hace: Crea el prompt para generar preguntas.
Cómo lo hace: Incluye material, referencias, ruta del bosque y formato esperado.

Nombre: generate_questions_with_ai
Tipo: función
Archivo: app/services/questions.py
Qué hace: Genera preguntas con IA.
Cómo lo hace: Llama a call_ai_json, normaliza cada pregunta y descarta inválidas.

Nombre: add_questions_to_bank
Tipo: función
Archivo: app/services/questions.py
Qué hace: Agrega preguntas nuevas al banco.
Cómo lo hace: Evita duplicados comparando el texto q en minúsculas.


14. FUNCIONES IMPORTANTES DE MATERIALES


Nombre: build_material_metadata
Tipo: función
Archivo: app/services/materials.py
Qué hace: Construye los metadatos finales de un documento.
Cómo lo hace: Junta información del archivo, clasificación, bosque y referencias.

Nombre: process_material_text
Tipo: función
Archivo: app/services/materials.py
Qué hace: Coordina el procesamiento de un texto ya extraído.
Cómo lo hace: Clasifica el material, actualiza bosque, genera preguntas y las guarda.


15. FUNCIONES IMPORTANTES DE ALMACENAMIENTO


Nombre: load_json
Tipo: función
Archivo: app/services/storage.py
Qué hace: Lee un archivo JSON.
Cómo lo hace: Si no existe o está dañado, devuelve valor por defecto.

Nombre: save_json
Tipo: función
Archivo: app/services/storage.py
Qué hace: Guarda información en JSON.
Cómo lo hace: Usa json.dump con ensure_ascii=False.

Nombre: load_index
Tipo: función
Archivo: app/services/storage.py
Qué hace: Carga materials.json.
Cómo lo hace: Usa load_json.

Nombre: save_index
Tipo: función
Archivo: app/services/storage.py
Qué hace: Guarda materials.json.
Cómo lo hace: Usa save_json.

Nombre: load_question_bank
Tipo: función
Archivo: app/services/storage.py
Qué hace: Carga question_bank.json.
Cómo lo hace: Devuelve lista vacía si no existe o no es lista.

Nombre: save_question_bank
Tipo: función
Archivo: app/services/storage.py
Qué hace: Guarda question_bank.json.
Cómo lo hace: Usa save_json.

Nombre: load_knowledge_forest
Tipo: función
Archivo: app/services/storage.py
Qué hace: Carga knowledge_forest.json.
Cómo lo hace: Si no existe, devuelve {"trees": {}}.

Nombre: save_knowledge_forest
Tipo: función
Archivo: app/services/storage.py
Qué hace: Guarda knowledge_forest.json.
Cómo lo hace: Usa save_json.

Nombre: load_material_references
Tipo: función
Archivo: app/services/storage.py
Qué hace: Carga referencias de un documento.
Cómo lo hace: Lee storage/references/{material_id}.json.

Nombre: save_material_references
Tipo: función
Archivo: app/services/storage.py
Qué hace: Guarda referencias de un documento.
Cómo lo hace: Escribe storage/references/{material_id}.json.


16. FUNCIONES AUXILIARES IMPORTANTES


Nombre: now_iso
Tipo: función
Archivo: app/services/utils.py
Qué hace: Devuelve fecha actual en formato ISO.
Cómo lo hace: Usa datetime.now(timezone.utc).isoformat().

Nombre: slugify
Tipo: función
Archivo: app/services/utils.py
Qué hace: Convierte nombres en ids seguros.
Cómo lo hace: Quita acentos, convierte a minúsculas y reemplaza espacios por guiones.

Nombre: extract_json_from_model_text
Tipo: función
Archivo: app/services/utils.py
Qué hace: Extrae JSON desde la respuesta del modelo.
Cómo lo hace: Limpia bloques markdown y usa json.loads.


17. ERRORES IMPORTANTES


400 - Formato no soportado:
El archivo no es PDF, DOCX, TXT o MD.

400 - Archivo vacío:
El archivo no contiene bytes.

400 - Archivo demasiado grande:
Supera MAX_FILE_SIZE_MB.

400 - Texto insuficiente:
El documento tiene menos de 50 caracteres útiles después de extraer texto.

400 - Número de preguntas inválido:
num_questions debe estar entre 1 y 40.

409 - Duplicado sin texto extraído:
El índice dice que el archivo existe, pero falta su TXT.

500 - Falta configuración:
No existe OPENAI_BASE_URL, OPENAI_API_KEY o MODEL.

500 - Respuesta inválida del modelo:
El modelo no devolvió JSON válido.

500 - Preguntas inválidas:
La IA respondió, pero ninguna pregunta cumplió el formato esperado.


18. CRITERIOS DE ACEPTACIÓN


El backend se considera correcto si:

1. Inicia con python -m uvicorn main:app --reload.
2. /api/health responde status ok.
3. ai_configured aparece como true.
4. /docs abre correctamente.
5. POST /api/materials/upload acepta PDF, DOCX, TXT o MD.
6. El archivo se guarda con SHA-256.
7. El texto se guarda en storage/texts.
8. Las referencias se guardan en storage/references.
9. El material se clasifica dentro del bosque.
10. Se generan preguntas.
11. Cada pregunta tiene q, options, answer, area, subarea y synthetic.
12. Cada pregunta tiene referencia al documento original.
13. /api/question-bank devuelve preguntas.
14. /egel/banco_preguntas.js devuelve window.questions = [...]
15. El frontend puede leer las preguntas sin cambiar su lógica base.


19. USO ESPERADO


1. Entrar a backend:

   cd backend

2. Crear entorno virtual:

   python -m venv .venv

3. Activarlo:

   .venv\Scripts\activate

4. Instalar dependencias:

   pip install -r requirements.txt

5. Crear .env:

   OPENAI_BASE_URL=...
   OPENAI_API_KEY=...
   MODEL=...
   MAX_FILE_SIZE_MB=10
   DEFAULT_QUESTION_COUNT=15

6. Correr servidor:

   python -m uvicorn main:app --reload

7. Abrir Swagger:

   http://127.0.0.1:8000/docs

8. Subir material:

   POST /api/materials/upload

9. Ver preguntas:

   http://127.0.0.1:8000/api/question-bank

10. Ver banco para frontend:

   http://127.0.0.1:8000/egel/banco_preguntas.js


20. NOTA PARA EL FRONTEND


El frontend puede usar directamente:

   /egel/banco_preguntas.js

y leer:

   window.questions

Los campos más útiles para mostrar información adicional son:

- item.source_document_name
- item.source_page
- item.source_excerpt
- item.knowledge_path
- item.tree_name
- item.node_name
- item.leaf_name

Ejemplo para fuentes:

Documento: item.source_document_name
Página: item.source_page
Extracto: item.source_excerpt
Tema: item.knowledge_path


FIN
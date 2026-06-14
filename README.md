# Anernan 🌊

> **Anernan** (Old English: *to run together, to flow together*) 

Anernan is a self-hosted, AI-augmented Idea Vault and personal knowledge base. It is built for thinkers, researchers, and builders who want to seamlessly aggregate information, connect disparate thoughts, and co-think with an AI companion.

While modern tools require you to manually organise, tag, and link your notes, Anernan automates the friction away. Simply drop your markdown files or PDFs into the vault. The system automatically ingests them, generates contextual tags, and maps semantic connections—creating an interconnected, second brain that both you and your local AI can read, query, and expand.

Because your data is grounded in plain text and standard formats, your knowledge remains yours forever. View your vault as a clean, distraction-free reader, an interactive mind-map, or a chat interface with your AI assistant.

## 🚀 Key Features

* **Automated Ingestion (MD & PDF):** Drop any .md or .pdf file into your vault. Anernan instantly parses the text, extracts key concepts, and integrates it into your knowledge base without manual data entry.

* **AI-Powered Auto-Tagging & Linking:** The engine automatically analyses your content to generate relevant tags and construct semantic [[WikiLinks]] between related documents, uncovering hidden connections across your data.

* **Dual-Read Engine (Human + AI):** Built from the ground up for hybrid reading. Access a beautiful, clean UI optimised for human focus, while a native AI layer continuously indexes the vault to answer complex prompts, synthesise summaries, or brainstorm ideas.

* **Self-Hosted & Private:** Complete ownership of your mind. Your PDFs, notes, and AI interactions stay entirely local or on your own server, keeping your private knowledge secure.

## 🛠️ Technology Stack

Anernan is designed with a lightweight, secure, and self-hostable architecture:

* **Backend:** Python + **FastAPI** to provide a fast, secure, and self-documenting REST API.
* **Database:** **SQLite** configured in Write-Ahead Logging (WAL) mode to support concurrent multi-user read/write operations with zero external database server configuration. Stored metadata, tags, and summaries leverage SQLite's hybrid NoSQL/JSON capabilities.
* **Frontend:** **React** (built with **Vite**) for a modern, responsive, and distraction-free user interface.
* **Client-Side Parsing:** PDF/Markdown text extraction and metadata generation (summarisation and tagging) are performed directly on the client side before upload. This keeps the backend server lightweight and non-blocking.
* **Security:** Role-based token authentication (JWT) protecting user uploads and guarding the **Admin Approval Queue**.

## 📅 Roadmap & Future Features

We are developing Anernan in distinct phases:

### Phase 1: MVP (Active Development)
* **Core Ingestion:** Drag-and-drop client-side PDF/Markdown parsing and metadata generation.
* **Admin Moderation:** Admin Approval Queue allowing administrators to review, approve, or reject uploaded vault documents.
* **Search Dashboard:** A responsive user interface to browse, filter, and search approved documents.
* **AI Agent REST API:** Secure search and content retrieval endpoints (`/api/v1/search`) allowing external AI agents to query approved knowledge.

### Phase 2: Git-Based Syncing
* **Distributed Vaults:** Native Git repository syncing to allow multiple self-hosted Anernan servers to synchronise their files and database records.
* **Collaboration Workflows:** Merge conflict resolution and multi-user vault sharing protocols.

### Phase 3: Native LLM Orchestration & MCP
* **Local Models:** Built-in model execution support (Ollama and Llama.cpp) for offline summarisation, embedding generation, and vector indexing.
* **Model Context Protocol (MCP):** Native MCP server integration, enabling compatible LLMs and external clients to interact directly with the vault.
* **Interactive Chat:** An in-app chat companion allowing users to talk directly to their knowledge vault.


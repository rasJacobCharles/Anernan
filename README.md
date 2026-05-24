# Anernan 🌊

> **Anernan** (Old English: *to run together, to flow together*) 

Anernan is a self-hosted, collaborative project management engine built for teams who love the flexibility of Markdown but need the structural power of an enterprise ticketing system. 

Local-first, text-based tools (like Obsidian) are incredible for personal planning, but collaborating with a team often forces you back into rigid, proprietary UIs. Anernan solves this by parsing standard `.md` files and using native `[[WikiLinks]]` to automatically collate Epics, Stories, Subtasks, and team dependencies into a single, shared source of truth.

Because your data is plain text, the presentation layer is entirely unopinionated. View your project as a structured, sequential **Waterfall** timeline, an **Agile/Kanban** board, or an interconnected **Dependency Graph**.

## 🚀 Key Features

* **WikiLink Dependencies:** Define hierarchies and blockers naturally. Linking `[[Epic-01]]` or `[[Blocked-By-Task]]` in a markdown file automatically generates the project architecture.
* **Multi-View Architecture:** Seamlessly toggle between a structured **Waterfall** timeline, an **Agile/Kanban** board, or a visual **Graph View** mapping out your entire project topology.
* **True Collaboration:** A shared, multiplayer ecosystem where you can assign tasks to teammates, tag metadata, track blocks, and view cross-user boards without losing local file flexibility.
* **Self-Hosted & Customizable:** Highly extensible architecture designed to put you in complete control of your data and workflows.
## 🛠️ Tech Stack (Experimental)

Anernan is built with a decoupled, high-performance architecture designed for speed and flexibility:

* **Frontend:** React (SPA for smooth, interactive UI transitions between Graph and Waterfall views)
* **Backend:** Go (Golang) for blazingly fast markdown parsing, file watching, and API routing
* **Database:** NoSQL (Optimized for flexible, schema-less graph and document relationships)

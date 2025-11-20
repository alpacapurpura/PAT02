PATCO AI Integration
====================

Overview
--------

- Sync manuals and category effective documents to RAG.
- Index entry/exit checklists per equipment category.
- Provide AI conversations via ``odoo_bot`` focused on active maintenance orders.

Configuration
-------------

Development
~~~~~~~~~~~

- Lift services: ``docker compose --profile patco-dev --profile ai-patco-dev up -d``
- Default MCP URL: ``http://ai-mcp-dev:8080`` (Docker internal)

Production
~~~~~~~~~~

- With ``RUNNING_ENV=prod`` or ``running_env=prod``, default MCP URL: ``https://ai.patcoperu.com`` (Traefik SSL)

Overrides (optional)
~~~~~~~~~~~~~~~~~~~~

- Environment: ``AI_MCP_URL``
- System parameter: ``ai.mcp.url``

Usage
-----

- Index attachments: mark ``Manual Doc (Index to RAG)`` on ``ir.attachment``.
- Index category checklists: run action ``Sync Checklists to RAG`` on ``maintenance.equipment.category``.
- Conversations: menu ``AI > Conversaciones IA``, write a question and click ``Preguntar``.

Notes
-----

- ``odoo_bot`` is created automatically on install.
- The bot reads only documents and basic data from the user's active maintenance orders.
# Repo Agent Platform

Sistema seguro para integrar repositorios y agentes sin romper el proyecto.

## Qué hace

- Mantiene un catálogo de repositorios externos.
- Genera agentes bajo demanda en un solo archivo JSONL.
- Valida formato antes de usarlo.
- Evita subir 15,000 archivos individuales.
- Deja la integración real en modo `dry-run` por defecto.

## Comandos

```bash
python repo_agent_platform/tools/generate_agents.py --count 15000 --output repo_agent_platform/generated/agents_15000.jsonl
python repo_agent_platform/tools/validate_catalog.py
python repo_agent_platform/tools/validate_agents.py repo_agent_platform/generated/agents_15000.jsonl
```

## Regla de seguridad

No se clonan 300 repositorios automáticamente dentro del proyecto. Primero se validan, luego se aprueban y después se agregan como submódulos o referencias externas.

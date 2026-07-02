# Repo Agent Master Pack

Paquete aprobado para integrar 300 repositorios de referencia y 15,000 agentes generados.

## Archivos generados fuera del repositorio

- `repos_catalog_300.json`
- `repos_catalog_300.csv`
- `agents_15000.jsonl`
- `scripts/validate_repos.py`
- `scripts/add_repos_as_submodules.py`
- `scripts/load_agents.py`

## Modo seguro de integración

1. Descargar `repos_agentes_master_pack.zip` desde ChatGPT.
2. Extraerlo en la raíz del proyecto.
3. Ejecutar validación:

```bash
python scripts/validate_repos.py
```

4. Agregar repositorios como submódulos en modo prueba:

```bash
python scripts/add_repos_as_submodules.py --target ./external --dry-run
```

5. Si todo está correcto:

```bash
python scripts/add_repos_as_submodules.py --target ./external
```

6. Validar agentes:

```bash
python scripts/load_agents.py --input agents_15000.jsonl
```

## Seguridad

- No guardar tokens ni claves en GitHub.
- No publicar ni desplegar sin revisión humana.
- Usar branch separado antes de producción.
- Ejecutar pruebas, escaneo de seguridad y rollback plan.

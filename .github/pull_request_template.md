## Problema y estado anterior

Describe el problema verificable y el comportamiento anterior.

## Solución y alcance

- Solución propuesta:
- Dentro de alcance:
- Fuera de alcance:
- Archivos modificados:

## Clasificación de riesgo

- Nivel: `R0 | R1 | R2 | R3 | R4`
- Dominio: `platform | agentic | data | security | trading | social | infrastructure | governance`
- Cambio reversible: `sí | no`
- Impacto externo: `ninguno | interno | usuario | financiero | público`
- Madurez: `PROPOSED | ADR_APPROVED | IMPLEMENTING | EXPERIMENTAL | VALIDATED | CERTIFIED | PRODUCTION_READY | SUSPENDED | RETIRED`

## Threat model y riesgos

- Activos protegidos:
- Amenazas consideradas:
- Controles:
- Riesgos residuales:
- Permission diff:
- Behavior diff:

## Pruebas y resultados

- Pruebas positivas:
- Pruebas negativas/adversariales:
- Lint/type checking/cobertura:
- Seguridad/SCA/SBOM:
- Resultado CI:

## Métricas y observabilidad

- Métricas/baseline:
- Logs/traces/alertas:
- SLI/SLO afectados:

## Migración, rollback y operación

- Migración:
- Rollback probado o verificable:
- Runbook:

## Coste y ownership

- Owner:
- Revisor independiente requerido:
- Coste inicial/operativo:
- Complejidad y lock-in:

## Evidencia y aprobaciones

- Evidencia ligada al commit/PR:
- Evidence Ledger:
- Decisión propuesta: `GO | CONDITIONAL_GO | NO_GO`
- Aprobador humano:
- Condiciones pendientes:

## Invariantes

- [ ] No contiene secretos ni datos personales.
- [ ] No amplía privilegios sin aprobación explícita.
- [ ] No habilita trading real, publicación automática, despliegue productivo ni acciones irreversibles.
- [ ] Las referencias externas son inmutables.
- [ ] Dependencias y artefactos tienen procedencia verificable.
- [ ] Auto-merge permanece deshabilitado.
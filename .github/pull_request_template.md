## Resumen

Describe el cambio y el problema que resuelve.

## Clasificación de riesgo

- Nivel: `R0 | R1 | R2 | R3 | R4`
- Dominio: `platform | agentic | data | security | trading | social | infrastructure | governance`
- Cambio reversible: `sí | no`
- Impacto externo: `ninguno | interno | usuario | financiero | público`

## Evidencia

- [ ] CI completo y exitoso.
- [ ] Pruebas relevantes ejecutadas.
- [ ] Riesgos residuales documentados.
- [ ] Plan de rollback probado o verificable.
- [ ] Evidencia añadida al ledger cuando aplique.

## Controles especiales

- [ ] No contiene secretos ni datos personales.
- [ ] No amplía privilegios sin aprobación explícita.
- [ ] No habilita trading real, publicación automática ni acciones irreversibles.
- [ ] Las referencias externas son inmutables.
- [ ] Dependencias y artefactos tienen procedencia verificable.

## GO/NO-GO

- Decisión propuesta: `GO | CONDITIONAL_GO | NO_GO`
- Aprobador humano:
- Condiciones pendientes:

## Rollback

Indica el commit, comando o procedimiento exacto para revertir el cambio.

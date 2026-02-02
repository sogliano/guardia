# E2E Tests

Los tests End-to-End (E2E) están implementados con Playwright y prueban el flujo completo de la aplicación.

## Estado Actual

**Los tests E2E están deshabilitados en CI/CD** para evitar fallos en el pipeline de deployment. Los tests E2E son más apropiados para desarrollo local donde se puede iterar y depurar fácilmente.

## Ejecutar Localmente

### Prerequisitos

```bash
# Instalar dependencias (solo primera vez)
npm ci

# Instalar navegadores de Playwright
npx playwright install chromium
```

### Correr Tests

```bash
# Ejecutar todos los tests E2E
npm run test:e2e

# Ejecutar en modo UI (interactivo)
npm run test:e2e:ui

# Ejecutar en modo debug
npm run test:e2e:debug

# Ejecutar un test específico
npx playwright test tests/e2e/dashboard.spec.ts
```

### Notas Importantes

1. **El servidor debe estar corriendo**: Playwright inicia automáticamente el servidor de desarrollo (`npm run dev`) configurado en `playwright.config.ts`

2. **Backend Mock**: Los tests mockean las respuestas del backend API. No necesitas el backend corriendo.

3. **Autenticación Mock**: Los tests usan un fixture de autenticación que mockea Clerk sin necesitar credenciales reales.

## Tests Disponibles

- `auth.spec.ts` - Flujo de autenticación
- `dashboard.spec.ts` - Dashboard y estadísticas
- `case-flow.spec.ts` - Gestión de casos
- `quarantine.spec.ts` - Gestión de cuarentena

## Por Qué Están Deshabilitados en CI

1. **Flakiness**: Los tests E2E pueden ser inconsistentes en entornos CI
2. **Tiempo**: Tardan más que los tests unitarios
3. **Complejidad**: Requieren setup adicional (navegadores, servidor)
4. **Cobertura**: Los tests unitarios cubren la lógica crítica

## Recomendación

- Ejecuta los tests E2E **localmente** antes de hacer PR
- Los tests unitarios (`npm test`) siguen corriendo en CI
- Para debugging, usa `npm run test:e2e:ui` o `npm run test:e2e:debug`

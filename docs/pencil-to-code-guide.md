# Guía: Generar Código desde Pencil (.pen)

## Qué es Pencil MCP

Pencil es un editor de diseño que trabaja con archivos `.pen`. Los archivos `.pen` están encriptados y **solo se pueden leer/escribir mediante las herramientas MCP de Pencil** (nunca con `Read`, `Grep`, etc.).

Claude Code tiene acceso directo a las herramientas de Pencil y puede:
- Leer la estructura de los frames diseñados
- Extraer componentes, estilos, colores, tipografía
- Generar código Vue/TypeScript que replica fielmente el diseño

---

## Flujo para generar código de un frame

### 1. Obtener el estado del editor

```
Pedirle a Claude: "Mirá el estado actual del editor Pencil"
```

Esto ejecuta `get_editor_state()` y devuelve:
- Archivo `.pen` activo
- Nodos top-level (screens/frames)
- Componentes reutilizables disponibles (design system)

### 2. Leer la estructura de un frame específico

```
Pedirle a Claude: "Leé la estructura completa del frame 'Dashboard' (ID: oCJ5E)"
```

Esto ejecuta `batch_get` con el nodeId y un `readDepth` alto para recorrer todos los hijos, componentes anidados, textos, estilos, etc.

### 3. Extraer variables y tokens de diseño

```
Pedirle a Claude: "Dame las variables de diseño del archivo .pen"
```

Esto ejecuta `get_variables()` y devuelve los tokens (colores, tipografías, spacing) definidos como variables CSS reutilizables.

### 4. Obtener screenshot para referencia visual

```
Pedirle a Claude: "Sacá screenshot del frame Dashboard"
```

Esto ejecuta `get_screenshot(nodeId)` para tener una referencia visual de cómo debe verse el resultado final.

### 5. Generar el código

```
Pedirle a Claude: "Generá el código Vue del frame Dashboard usando PrimeVue y los componentes existentes del frontend"
```

Claude va a:
1. Analizar la estructura del frame (layout, componentes, jerarquía)
2. Mapear componentes Pencil → componentes PrimeVue/Vue equivalentes
3. Extraer textos, colores, spacing exactos del diseño
4. Generar componentes `.vue` con `<script setup lang="ts">`
5. Usar los tokens de diseño como CSS variables

---

## Comandos útiles para pedirle a Claude

### Explorar lo que hay diseñado

```
"Mostrá todos los frames/pantallas del archivo .pen actual"
"Qué componentes del design system están disponibles?"
"Dame la estructura del frame Login (ID: bkNX8)"
```

### Generar código

```
"Generá el código Vue del frame [nombre/ID]"
"Implementá la pantalla de Login basándote en el diseño de Pencil"
"Convertí el Dashboard del .pen a un componente Vue con PrimeVue"
```

### Verificar resultado

```
"Compará el screenshot del diseño con el código generado"
"Revisá que el código coincida con los colores y spacing del diseño"
```

---

## Ejemplo completo paso a paso

Supongamos que querés generar el código del Login:

```
Vos: "Generá el código Vue de la pantalla de Login del archivo .pen"

Claude va a hacer internamente:
1. get_editor_state() → identifica el .pen activo
2. batch_get({nodeIds: ["bkNX8"], readDepth: 5}) → lee toda la estructura del Login
3. get_variables() → obtiene tokens de diseño (colores, fonts)
4. get_screenshot({nodeId: "bkNX8"}) → captura visual de referencia
5. Analiza componentes usados (botones, inputs, etc.)
6. Busca en frontend/src/ si ya existen componentes equivalentes
7. Genera/actualiza los archivos .vue correspondientes
```

---

## Notas importantes

- Los archivos `.pen` **NO se pueden leer con herramientas de archivo normales** (Read, cat, grep). Solo con Pencil MCP.
- Claude mapea automáticamente los componentes del design system de Pencil a componentes PrimeVue cuando es posible.
- El código generado sigue las convenciones del proyecto: Vue 3 Composition API, TypeScript, PrimeVue 4, indent 2 espacios.
- Si un componente del diseño ya existe en el código, Claude lo actualiza en vez de crear uno nuevo.

---

## IDs actuales de los frames principales

| Frame | ID | Descripción |
|-------|----|-------------|
| Screen 1 - Login | `bkNX8` | Pantalla de inicio de sesión |
| Screen 2 - Dashboard | `oCJ5E` | Dashboard principal |
| Design System | `frame-1761929672442` | Componentes lunaris |

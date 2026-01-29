# Guard-IA: Setup de Clerk Authentication

Guia paso a paso para configurar Clerk como sistema de autenticacion.

---

## Paso 1: Configurar Clerk Dashboard

1. Ir a https://dashboard.clerk.com y loguearte con tu cuenta
2. Crear una nueva aplicacion (o usar la existente):
   - Nombre: `Guard-IA`
   - Framework: seleccionar cualquiera (no importa, solo afecta los docs que te muestra)
3. En el sidebar izquierdo ir a **Configure > Email, phone, username**:
   - Activar **Email address** como metodo de identificacion
   - Desactivar Phone number y Username si estan activos

> **Nota**: La opcion "Enable allowlist" en **Configure > Restrictions** permite hacer invitation-only, pero requiere plan Pro de Clerk. En plan gratuito el sign-up queda abierto. Para controlar el acceso, simplemente no compartir la URL de login y desactivar manualmente usuarios no deseados desde el Dashboard.

---

## Paso 2: Obtener las API Keys

1. En el sidebar de Clerk ir a **Configure > API Keys**
2. Copiar las siguientes claves:
   - **Publishable key**: empieza con `pk_test_...` (es publica, va en el frontend)
   - **Secret key**: empieza con `sk_test_...` (es privada, solo backend)
3. Para obtener la **PEM Public Key**:
   - En la misma pagina de API Keys, buscar el link **"Show JWT public key"** o ir a **Configure > JWT Templates**
   - Copiar el bloque completo que empieza con `-----BEGIN PUBLIC KEY-----` y termina con `-----END PUBLIC KEY-----`

---

## Paso 3: Configurar variables de entorno

### Backend (`.env` en la raiz del proyecto)

Crear el archivo `.env` copiando `.env.example` si no existe:

```bash
cp .env.example .env
```

Editar `.env` y reemplazar los valores de Clerk:

```env
CLERK_SECRET_KEY=sk_test_TU_SECRET_KEY_AQUI
CLERK_PUBLISHABLE_KEY=pk_test_TU_PUBLISHABLE_KEY_AQUI
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqh...\n...TU_KEY_COMPLETA...\n-----END PUBLIC KEY-----"
```

**Nota sobre la PEM key**: La clave PEM tiene multiples lineas. En el `.env` ponerla en una sola linea reemplazando los saltos de linea con `\n`, todo entre comillas dobles.

### Frontend (`frontend/.env.local`)

Crear el archivo:

```bash
touch frontend/.env.local
```

Agregar:

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_TU_PUBLISHABLE_KEY_AQUI
```

Usar la misma Publishable Key que en el backend.

---

## Paso 4: Instalar dependencias del backend

Desde el directorio `backend/`:

```bash
cd backend
pip install -e .
```

Esto instala las nuevas dependencias: `PyJWT[crypto]` y `clerk-backend-api`.

---

## Paso 5: Ejecutar la migracion de base de datos

La base de datos necesita la nueva columna `clerk_id` en la tabla `users`.

Primero, asegurate de que PostgreSQL este corriendo:

```bash
docker compose up db -d
```

Luego, desde el directorio `backend/`:

```bash
cd backend
alembic revision --autogenerate -m "add clerk_id to users"
alembic upgrade head
```

El primer comando genera el script de migracion. El segundo lo aplica.

Si la tabla `users` no existia antes, la migracion la va a crear completa.

---

## Paso 6: Invitar al primer usuario

1. En el Clerk Dashboard ir a **Users** en el sidebar
2. Click en **"Invite user"** (o el boton de crear/invitar)
3. Ingresar el email del primer usuario admin
4. El usuario va a recibir un email con un link para crear su cuenta

---

## Paso 7: Verificar que todo funciona

### Levantar el proyecto

```bash
# Terminal 1: Base de datos
docker compose up db -d

# Terminal 2: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Checklist de verificacion

1. Abrir `http://localhost:5173` en el navegador
2. Deberia verse la pagina de login con el boton **"Sign In with Clerk"**
3. Click en el boton abre el modal de Clerk
4. Loguearse con el usuario invitado en el Paso 6
5. Despues del login, deberia redirigir al Dashboard automaticamente
6. En el sidebar deberia verse el nombre del usuario y el `<UserButton>` de Clerk
7. En la base de datos, verificar que se creo el registro:
   ```sql
   SELECT id, clerk_id, email, full_name, role FROM users;
   ```
   Deberia mostrar un usuario con `role = 'analyst'`
8. Probar el endpoint directamente (el token se obtiene desde Clerk):
   - `GET http://localhost:8000/api/v1/auth/me` sin token → 403
   - `GET http://localhost:8000/api/v1/auth/me` con Bearer token valido → datos del usuario

---

## Troubleshooting

### "Missing VITE_CLERK_PUBLISHABLE_KEY environment variable"
El frontend no encuentra la key. Verificar que `frontend/.env.local` existe y tiene `VITE_CLERK_PUBLISHABLE_KEY=pk_test_...`. Reiniciar el dev server despues de crear el archivo.

### "Invalid or expired token" al hacer requests al backend
La PEM public key en `.env` no coincide con la que usa Clerk. Ir a Clerk Dashboard > API Keys > Show JWT public key y copiarla de nuevo. Asegurarse de que los `\n` estan bien.

### El modal de Clerk no abre
Verificar que la Publishable Key es correcta y que el dominio `localhost:5173` no esta bloqueado en Clerk. En Clerk Dashboard > Configure > Paths, verificar los dominios permitidos.

### JIT provisioning falla ("Unable to verify user identity")
El `CLERK_SECRET_KEY` del backend es incorrecto o el usuario no existe en Clerk. Verificar la Secret Key en `.env`.

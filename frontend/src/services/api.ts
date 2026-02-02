import axios from 'axios'
import router from '@/router'

type GetTokenFn = () => Promise<string | null>

let clerkGetToken: GetTokenFn | null = null

export function setClerkGetToken(fn: GetTokenFn) {
  clerkGetToken = fn
}

/**
 * Determina la baseURL del API según el ambiente.
 * Prioridad:
 * 1. Variable de entorno VITE_API_BASE_URL (explícita)
 * 2. Auto-detección por hostname
 * 3. Desarrollo local (fallback)
 */
function getBaseURL(): string {
  // 1. Preferir variable de entorno explícita
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  // 2. Auto-detectar por hostname
  const hostname = window.location.hostname

  if (hostname === 'guardia-staging.vercel.app') {
    return 'https://guardia-api-staging-81580052566.us-east1.run.app/api/v1'
  }

  if (hostname === 'guardia.vercel.app' || hostname === 'guardia.strike.sh') {
    return 'https://guardia-api-production-81580052566.us-east1.run.app/api/v1'
  }

  // 3. Desarrollo local
  return 'http://localhost:8000/api/v1'
}

const api = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(async (config) => {
  if (clerkGetToken) {
    try {
      const token = await clerkGetToken()

      if (!token) {
        console.warn('No authentication token available')
        // Token is null - request will proceed without auth header
        // Backend will handle 401 and response interceptor will redirect to login
      } else {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (error) {
      console.error('Error getting authentication token:', error)
      // Error getting token - request will proceed without auth header
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      router.push({ name: 'login' })
    }
    return Promise.reject(error)
  },
)

export default api

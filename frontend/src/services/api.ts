import axios from 'axios'
import router from '@/router'

type GetTokenFn = () => Promise<string | null>

let clerkGetToken: GetTokenFn | null = null

export function setClerkGetToken(fn: GetTokenFn) {
  clerkGetToken = fn
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(async (config) => {
  if (clerkGetToken) {
    const token = await clerkGetToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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

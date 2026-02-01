import { vi } from 'vitest'

// Mock Clerk globally
vi.mock('@clerk/vue', () => ({
  useAuth: () => ({
    isLoaded: true,
    isSignedIn: true,
    userId: 'user_test123',
    getToken: vi.fn().mockResolvedValue('test_token'),
  }),
  useUser: () => ({
    user: {
      id: 'user_test123',
      primaryEmailAddress: { emailAddress: 'test@strike.sh' },
      firstName: 'Test',
      lastName: 'User',
    },
  }),
  ClerkProvider: {
    name: 'ClerkProvider',
    template: '<div><slot /></div>',
  },
}))

// Mock Chart.js
vi.mock('vue-chartjs', () => ({
  Line: { name: 'Line', template: '<div class="mock-line-chart"></div>' },
  Bar: { name: 'Bar', template: '<div class="mock-bar-chart"></div>' },
  Doughnut: { name: 'Doughnut', template: '<div class="mock-doughnut-chart"></div>' },
}))

// Mock router
vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      go: vi.fn(),
      back: vi.fn(),
    }),
    useRoute: () => ({
      params: {},
      query: {},
      path: '/',
    }),
  }
})

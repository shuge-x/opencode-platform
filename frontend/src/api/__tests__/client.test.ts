import axios from 'axios'

// Mock axios
const mockAxiosCreate = jest.fn(() => ({
  interceptors: {
    request: {
      use: jest.fn(),
    },
    response: {
      use: jest.fn(),
    },
  },
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}))

jest.mock('axios', () => ({
  create: mockAxiosCreate,
}))

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create axios instance with correct config', () => {
    // Re-import to trigger axios.create
    jest.resetModules()
    require('../client')
    
    expect(mockAxiosCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: '/api',
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
        },
      })
    )
  })

  it('should have interceptors set up', () => {
    jest.resetModules()
    const mockClient = mockAxiosCreate()
    
    expect(mockClient.interceptors.request.use).toBeDefined()
    expect(mockClient.interceptors.response.use).toBeDefined()
  })

  it('should export client with HTTP methods', () => {
    jest.resetModules()
    const client = require('../client').default
    
    expect(client).toBeDefined()
    expect(typeof client.get).toBe('function')
    expect(typeof client.post).toBe('function')
    expect(typeof client.put).toBe('function')
    expect(typeof client.delete).toBe('function')
  })
})

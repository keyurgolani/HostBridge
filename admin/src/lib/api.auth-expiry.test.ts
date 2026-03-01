import { beforeEach, describe, expect, it, vi } from 'vitest'

import { API } from './api'
import { useAuthStore } from '@/store/authStore'

describe('admin API session expiry handling', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ isAuthenticated: false, sessionToken: null })
    vi.restoreAllMocks()
  })

  it('logs out and redirects to /admin/login on 401 from protected endpoints', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(new Response(null, { status: 401 }))
    const locationAssignSpy = vi.fn()
    const api = new API({
      fetchImpl: fetchMock as typeof fetch,
      location: {
        pathname: '/admin',
        assign: locationAssignSpy,
      },
    })

    useAuthStore.getState().login('fake-session-token')

    await expect(api.getSystemHealth()).rejects.toThrow('Failed to fetch system health')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().sessionToken).toBeNull()
    expect(locationAssignSpy).toHaveBeenCalledWith('/admin/login')
  })

  it('does not redirect when login itself returns 401', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(new Response(null, { status: 401 }))
    const locationAssignSpy = vi.fn()
    const api = new API({
      fetchImpl: fetchMock as typeof fetch,
      location: {
        pathname: '/admin/login',
        assign: locationAssignSpy,
      },
    })

    await expect(api.login('wrong-password')).rejects.toThrow('Invalid password')

    expect(locationAssignSpy).not.toHaveBeenCalled()
  })
})

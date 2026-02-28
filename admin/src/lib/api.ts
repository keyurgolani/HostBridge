export interface HITLRequest {
  id: string
  created_at: string
  tool_name: string
  tool_category: string
  request_params: Record<string, any>
  request_context: Record<string, any>
  policy_rule_matched: string
  status: 'pending' | 'approved' | 'rejected' | 'expired'
  reviewed_by?: string
  reviewed_at?: string
  reviewer_note?: string
  execution_result?: Record<string, any>
  ttl_seconds: number
}

export interface AuditLogEntry {
  id: string
  timestamp: string
  tool_name: string
  tool_category: string
  protocol: string
  status: string
  duration_ms?: number
  error_message?: string
}

export interface SystemHealth {
  uptime: number
  pending_hitl: number
  tools_executed: number
  error_rate: number
}

class API {
  private baseUrl = window.location.origin

  async login(password: string): Promise<{ token: string }> {
    const response = await fetch(`${this.baseUrl}/admin/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
      credentials: 'include',
    })
    
    if (!response.ok) {
      throw new Error('Invalid password')
    }
    
    return response.json()
  }

  async getAuditLogs(limit = 100): Promise<AuditLogEntry[]> {
    const response = await fetch(`${this.baseUrl}/admin/api/audit?limit=${limit}`, {
      credentials: 'include',
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch audit logs')
    }
    
    return response.json()
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await fetch(`${this.baseUrl}/admin/api/health`, {
      credentials: 'include',
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch system health')
    }
    
    return response.json()
  }
}

export const api = new API()

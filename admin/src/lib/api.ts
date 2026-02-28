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
  request_params?: Record<string, any>
  response?: Record<string, any>
}

export interface SystemHealth {
  uptime: number
  pending_hitl: number
  tools_executed: number
  error_rate: number
}

export interface DetailedHealth {
  uptime: number
  pending_hitl: number
  tools_executed: number
  error_rate: number
  memory_used_mb: number
  memory_total_mb: number
  memory_percent: number
  cpu_percent: number
  db_size_mb: number
  db_path: string
  workspace_size_mb: number
  workspace_path: string
  websocket_connections: number
  python_version: string
  platform: string
  version: string
}

export interface ToolSchema {
  name: string
  category: string
  description: string
  input_schema: Record<string, any>
  output_schema?: Record<string, any>
  requires_hitl: boolean
}

export interface ToolListResponse {
  tools: ToolSchema[]
  total: number
}

export interface ConfigResponse {
  auth_enabled: boolean
  workspace_path: string
  database_path: string
  log_level: string
  http_config: Record<string, any>
  policy_rules_count: number
  tool_configs: Record<string, any>
}

export interface AuditLogFilterResponse {
  logs: AuditLogEntry[]
  total: number
  filtered: number
}

export interface DashboardStats {
  tool_stats: Array<{ tool_category: string; count: number }>
  status_stats: Array<{ status: string; count: number }>
  hourly_stats: Array<{ hour: string; count: number }>
  duration_stats: Array<{ tool_category: string; tool_name: string; avg_duration_ms: number }>
  pending_hitl: number
}

export interface ContainerInfo {
  id: string
  name: string
  status: string
  image: string
  created: string
}

export interface ContainerLogs {
  logs: string
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

  async logout(): Promise<void> {
    await fetch(`${this.baseUrl}/admin/api/logout`, {
      method: 'POST',
      credentials: 'include',
    })
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

  async getFilteredAuditLogs(params: {
    limit?: number
    offset?: number
    status?: string
    tool_category?: string
    tool_name?: string
    protocol?: string
    start_time?: string
    end_time?: string
    search?: string
  }): Promise<AuditLogFilterResponse> {
    const searchParams = new URLSearchParams()
    if (params.limit) searchParams.set('limit', params.limit.toString())
    if (params.offset) searchParams.set('offset', params.offset.toString())
    if (params.status) searchParams.set('status', params.status)
    if (params.tool_category) searchParams.set('tool_category', params.tool_category)
    if (params.tool_name) searchParams.set('tool_name', params.tool_name)
    if (params.protocol) searchParams.set('protocol', params.protocol)
    if (params.start_time) searchParams.set('start_time', params.start_time)
    if (params.end_time) searchParams.set('end_time', params.end_time)
    if (params.search) searchParams.set('search', params.search)

    const response = await fetch(`${this.baseUrl}/admin/api/audit/filtered?${searchParams}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch filtered audit logs')
    }

    return response.json()
  }

  async exportAuditLogs(format: 'json' | 'csv', params: {
    status?: string
    tool_category?: string
    start_time?: string
    end_time?: string
  }): Promise<Blob> {
    const searchParams = new URLSearchParams()
    searchParams.set('format', format)
    if (params.status) searchParams.set('status', params.status)
    if (params.tool_category) searchParams.set('tool_category', params.tool_category)
    if (params.start_time) searchParams.set('start_time', params.start_time)
    if (params.end_time) searchParams.set('end_time', params.end_time)

    const response = await fetch(`${this.baseUrl}/admin/api/audit/export?${searchParams}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to export audit logs')
    }

    return response.blob()
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

  async getDetailedHealth(): Promise<DetailedHealth> {
    const response = await fetch(`${this.baseUrl}/admin/api/health/detailed`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch detailed health')
    }

    return response.json()
  }

  async getTools(): Promise<ToolListResponse> {
    const response = await fetch(`${this.baseUrl}/admin/api/tools`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch tools')
    }

    return response.json()
  }

  async getToolSchema(category: string, name: string): Promise<ToolSchema> {
    const response = await fetch(`${this.baseUrl}/admin/api/tools/${category}/${name}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch tool schema')
    }

    return response.json()
  }

  async getConfig(): Promise<ConfigResponse> {
    const response = await fetch(`${this.baseUrl}/admin/api/config`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch config')
    }

    return response.json()
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await fetch(`${this.baseUrl}/admin/api/stats`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch dashboard stats')
    }

    return response.json()
  }

  async getContainers(): Promise<ContainerInfo[]> {
    const response = await fetch(`${this.baseUrl}/admin/api/containers`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch containers')
    }

    return response.json()
  }

  async getContainerLogs(containerId: string, tail = 100): Promise<ContainerLogs> {
    const response = await fetch(`${this.baseUrl}/admin/api/containers/${containerId}/logs?tail=${tail}`, {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to fetch container logs')
    }

    return response.json()
  }
}

export const api = new API()

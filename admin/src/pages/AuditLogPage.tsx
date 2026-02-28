import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { FileText, Search } from 'lucide-react'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { formatTimestamp, formatDuration, getStatusBadgeClass } from '@/lib/utils'
import { useState } from 'react'

export default function AuditLogPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => api.getAuditLogs(100),
    refetchInterval: 5000,
  })

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      searchTerm === '' ||
      log.tool_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.tool_category.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus = statusFilter === 'all' || log.status === statusFilter

    return matchesSearch && matchesStatus
  })

  const statusCounts = logs.reduce((acc, log) => {
    acc[log.status] = (acc[log.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-bold gradient-text mb-2">Audit Log</h1>
        <p className="text-muted-foreground">
          Complete history of all tool executions
        </p>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Executions"
          value={logs.length}
          icon={FileText}
          delay={0}
        />
        <StatCard
          label="Successful"
          value={statusCounts.success || 0}
          icon={FileText}
          variant="success"
          delay={0.1}
        />
        <StatCard
          label="Errors"
          value={statusCounts.error || 0}
          icon={FileText}
          variant="error"
          delay={0.2}
        />
        <StatCard
          label="Blocked"
          value={statusCounts.blocked || 0}
          icon={FileText}
          variant="warning"
          delay={0.3}
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search by tool name or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="all">All Status</option>
                <option value="success">Success</option>
                <option value="error">Error</option>
                <option value="blocked">Blocked</option>
                <option value="hitl_approved">HITL Approved</option>
                <option value="hitl_rejected">HITL Rejected</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Log Table */}
      <Card>
        <CardHeader>
          <CardTitle>Execution History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-12 text-muted-foreground">
              Loading audit logs...
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No logs found matching your filters
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Timestamp
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Tool
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Protocol
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Duration
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((log, index) => (
                    <motion.tr
                      key={log.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.02 }}
                      className="border-b border-border/50 hover:bg-accent/50 transition-colors"
                    >
                      <td className="py-3 px-4 text-sm">
                        {formatTimestamp(log.timestamp)}
                      </td>
                      <td className="py-3 px-4">
                        <code className="text-sm font-mono">
                          {log.tool_category}_{log.tool_name}
                        </code>
                      </td>
                      <td className="py-3 px-4 text-sm uppercase">
                        {log.protocol}
                      </td>
                      <td className="py-3 px-4">
                        <Badge className={getStatusBadgeClass(log.status)}>
                          {log.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-sm">
                        {log.duration_ms ? formatDuration(log.duration_ms) : '-'}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  variant = 'default',
  delay = 0,
}: {
  label: string
  value: number
  icon: any
  variant?: 'default' | 'success' | 'error' | 'warning'
  delay?: number
}) {
  const variantClasses = {
    default: 'text-primary',
    success: 'text-green-500',
    error: 'text-red-500',
    warning: 'text-yellow-500',
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
    >
      <Card hover>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-1">{label}</p>
              <p className={`text-3xl font-bold ${variantClasses[variant]}`}>
                {value}
              </p>
            </div>
            <Icon className={`w-8 h-8 ${variantClasses[variant]} opacity-50`} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

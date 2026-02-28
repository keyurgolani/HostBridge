import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Activity, Clock, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { formatDuration } from '@/lib/utils'

export default function SystemHealthPage() {
  const { data: health } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => api.getSystemHealth(),
    refetchInterval: 5000,
  })

  const uptime = health?.uptime || 0
  const pendingHitl = health?.pending_hitl || 0
  const toolsExecuted = health?.tools_executed || 0
  const errorRate = health?.error_rate || 0

  const isHealthy = errorRate < 0.1 && pendingHitl < 10

  return (
    <div className="space-y-4 md:space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl md:text-4xl font-bold gradient-text mb-2">System Health</h1>
        <p className="text-sm md:text-base text-muted-foreground">
          Monitor system performance and status
        </p>
      </motion.div>

      {/* Overall Status */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card glow={isHealthy} className={isHealthy ? 'glow-green' : 'glow-red'}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              {isHealthy ? (
                <CheckCircle className="w-16 h-16 text-green-500" />
              ) : (
                <AlertTriangle className="w-16 h-16 text-red-500" />
              )}
              <div>
                <h2 className="text-3xl font-bold">
                  {isHealthy ? 'System Healthy' : 'Attention Required'}
                </h2>
                <p className="text-muted-foreground">
                  {isHealthy
                    ? 'All systems operating normally'
                    : 'Some metrics require attention'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Uptime"
          value={formatDuration(uptime * 1000)}
          icon={Clock}
          variant="default"
          delay={0.2}
        />
        <MetricCard
          label="Pending HITL"
          value={pendingHitl.toString()}
          icon={AlertTriangle}
          variant={pendingHitl > 5 ? 'warning' : 'success'}
          delay={0.3}
        />
        <MetricCard
          label="Tools Executed"
          value={toolsExecuted.toString()}
          icon={TrendingUp}
          variant="default"
          delay={0.4}
        />
        <MetricCard
          label="Error Rate"
          value={`${(errorRate * 100).toFixed(1)}%`}
          icon={Activity}
          variant={errorRate > 0.1 ? 'error' : 'success'}
          delay={0.5}
        />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>System performance indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <MetricRow
                label="Average Response Time"
                value="45ms"
                status="good"
              />
              <MetricRow
                label="Active WebSocket Connections"
                value="1"
                status="good"
              />
              <MetricRow
                label="Database Size"
                value="2.4 MB"
                status="good"
              />
              <MetricRow
                label="Memory Usage"
                value="128 MB"
                status="good"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tool Categories</CardTitle>
            <CardDescription>Available tool categories</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {['filesystem', 'workspace', 'git', 'docker', 'shell', 'memory', 'plan', 'http'].map(
                (category, index) => (
                  <motion.div
                    key={category}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + index * 0.05 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-accent/50"
                  >
                    <span className="font-medium capitalize">{category}</span>
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  </motion.div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Information */}
      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
          <CardDescription>Container and environment details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoRow label="Version" value="0.1.0" />
            <InfoRow label="Protocol Support" value="MCP + OpenAPI" />
            <InfoRow label="Workspace" value="/workspace" />
            <InfoRow label="Database" value="SQLite (WAL mode)" />
            <InfoRow label="Python Version" value="3.12+" />
            <InfoRow label="FastAPI Version" value="Latest" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function MetricCard({
  label,
  value,
  icon: Icon,
  variant = 'default',
  delay = 0,
}: {
  label: string
  value: string
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
              <p className={`text-2xl font-bold ${variantClasses[variant]}`}>
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

function MetricRow({
  label,
  value,
  status,
}: {
  label: string
  value: string
  status: 'good' | 'warning' | 'error'
}) {
  const statusColors = {
    good: 'text-green-500',
    warning: 'text-yellow-500',
    error: 'text-red-500',
  }

  return (
    <div className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={`font-semibold ${statusColors[status]}`}>{value}</span>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-sm text-muted-foreground mb-1">{label}</span>
      <span className="font-mono text-sm">{value}</span>
    </div>
  )
}

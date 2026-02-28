import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Activity, Clock, AlertTriangle, CheckCircle, TrendingUp,
  Database, HardDrive, Cpu, MemoryStick, Globe, Server,
  Wifi, FileCode
} from 'lucide-react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { formatDuration } from '@/lib/utils'

export default function SystemHealthPage() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['detailed-health'],
    queryFn: () => api.getDetailedHealth(),
    refetchInterval: 5000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

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
                <CheckCircle className="w-12 h-12 md:w-16 md:h-16 text-green-500" />
              ) : (
                <AlertTriangle className="w-12 h-12 md:w-16 md:h-16 text-red-500" />
              )}
              <div>
                <h2 className="text-xl md:text-3xl font-bold">
                  {isHealthy ? 'System Healthy' : 'Attention Required'}
                </h2>
                <p className="text-muted-foreground text-sm md:text-base">
                  {isHealthy
                    ? 'All systems operating normally'
                    : 'Some metrics require attention'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Core Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
          value={toolsExecuted.toLocaleString()}
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

      {/* Resource Usage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="w-5 h-5" />
              Resource Usage
            </CardTitle>
            <CardDescription>Current system resource consumption</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Memory */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MemoryStick className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">Memory</span>
                  </div>
                  <span className="text-sm font-medium">
                    {health?.memory_used_mb?.toFixed(1)} MB / {health?.memory_total_mb?.toFixed(0)} MB
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${
                      (health?.memory_percent || 0) > 80
                        ? 'bg-red-500'
                        : (health?.memory_percent || 0) > 60
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${health?.memory_percent || 0}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{(health?.memory_percent || 0).toFixed(1)}% used</span>
                </div>
              </div>

              {/* CPU */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">CPU</span>
                  </div>
                  <span className="text-sm font-medium">
                    {(health?.cpu_percent || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${
                      (health?.cpu_percent || 0) > 80
                        ? 'bg-red-500'
                        : (health?.cpu_percent || 0) > 60
                        ? 'bg-yellow-500'
                        : 'bg-blue-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${health?.cpu_percent || 0}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>

              {/* Database Size */}
              <div className="flex items-center justify-between py-2 border-t border-border/50">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Database Size</span>
                </div>
                <span className="text-sm font-medium">
                  {(health?.db_size_mb || 0).toFixed(2)} MB
                </span>
              </div>

              {/* Workspace Size */}
              <div className="flex items-center justify-between py-2 border-t border-border/50">
                <div className="flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Workspace Size</span>
                </div>
                <span className="text-sm font-medium">
                  {(health?.workspace_size_mb || 0).toFixed(2)} MB
                </span>
              </div>

              {/* WebSocket Connections */}
              <div className="flex items-center justify-between py-2 border-t border-border/50">
                <div className="flex items-center gap-2">
                  <Wifi className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">WebSocket Connections</span>
                </div>
                <Badge variant={(health?.websocket_connections || 0) > 0 ? 'success' : 'default'}>
                  {health?.websocket_connections || 0}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5" />
              System Information
            </CardTitle>
            <CardDescription>Container and environment details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <InfoRow icon={Globe} label="Platform" value={health?.platform || 'Unknown'} />
              <InfoRow icon={FileCode} label="Python Version" value={health?.python_version || 'Unknown'} />
              <InfoRow icon={Server} label="Version" value={health?.version || '0.1.0'} />
              <InfoRow icon={Globe} label="Protocol Support" value="MCP + OpenAPI" />
              <InfoRow icon={HardDrive} label="Workspace Path" value={health?.workspace_path || '/workspace'} />
              <InfoRow icon={Database} label="Database Path" value={health?.db_path || '/app/data/hostbridge.db'} />
              <InfoRow icon={Database} label="Database Type" value="SQLite (WAL mode)" />
              <InfoRow icon={Server} label="Framework" value="FastAPI" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tool Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Tool Categories</CardTitle>
          <CardDescription>Available tool categories and their status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {['filesystem', 'workspace', 'git', 'docker', 'shell', 'memory', 'plan', 'http'].map(
              (category, index) => (
                <motion.div
                  key={category}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.6 + index * 0.05 }}
                  className="flex items-center justify-between p-3 rounded-lg bg-accent/50 border border-border/50"
                >
                  <span className="font-medium capitalize text-sm">{category}</span>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                </motion.div>
              )
            )}
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
              <p className={`text-xl md:text-2xl font-bold ${variantClasses[variant]}`}>
                {value}
              </p>
            </div>
            <Icon className={`w-6 h-6 md:w-8 md:h-8 ${variantClasses[variant]} opacity-50`} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function InfoRow({
  icon: Icon,
  label,
  value
}: {
  icon: any
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-border/30 last:border-0">
      <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <span className="text-xs text-muted-foreground">{label}</span>
        <p className="font-mono text-sm truncate">{value}</p>
      </div>
    </div>
  )
}

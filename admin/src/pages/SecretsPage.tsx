import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Key, RefreshCw, CheckCircle, AlertCircle, Lock, FileText,
  Copy, Check
} from 'lucide-react'
import { useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

export default function SecretsPage() {
  const queryClient = useQueryClient()
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  const { data: secrets, isLoading, refetch } = useQuery({
    queryKey: ['secrets'],
    queryFn: () => api.getSecrets(),
  })

  const reloadMutation = useMutation({
    mutationFn: () => api.reloadSecrets(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['secrets'] })
    },
  })

  const copyToClipboard = async (key: string) => {
    try {
      await navigator.clipboard.writeText(`{{secret:${key}}}`)
      setCopiedKey(key)
      setTimeout(() => setCopiedKey(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl md:text-4xl font-bold gradient-text mb-2">Secrets Management</h1>
          <p className="text-sm md:text-base text-muted-foreground">
            View and manage secret keys for tool authentication
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            className="w-full md:w-auto"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="default"
            onClick={() => reloadMutation.mutate()}
            disabled={reloadMutation.isPending}
            className="w-full md:w-auto"
          >
            {reloadMutation.isPending ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Reload Secrets
          </Button>
        </div>
      </motion.div>

      {/* Reload Status */}
      {reloadMutation.isSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-green-500/50 bg-green-500/5">
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div>
                  <p className="font-medium text-green-500">{reloadMutation.data.message}</p>
                  <p className="text-sm text-muted-foreground">
                    Loaded {reloadMutation.data.count} secret(s) from {reloadMutation.data.secrets_file}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {reloadMutation.isError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-red-500/50 bg-red-500/5">
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <div>
                  <p className="font-medium text-red-500">Failed to reload secrets</p>
                  <p className="text-sm text-muted-foreground">
                    {(reloadMutation.error as Error)?.message || 'Unknown error'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Secrets Overview */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/30">
                <Key className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Total Secrets</p>
                  <p className="font-semibold text-lg">{secrets?.count || 0}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/30">
                <FileText className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Source File</p>
                  <p className="font-mono text-sm truncate max-w-[150px] md:max-w-[250px]">
                    {secrets?.secrets_file?.split('/').pop() || 'secrets.env'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/30">
                <Lock className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Values Hidden</p>
                  <Badge variant="success">Protected</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Secrets List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="w-5 h-5" />
              Secret Keys
            </CardTitle>
            <CardDescription>
              Available secret keys for use in tool parameters with {'{{'}secret:KEY{'}}'} syntax
            </CardDescription>
          </CardHeader>
          <CardContent>
            {secrets?.keys && secrets.keys.length > 0 ? (
              <div className="space-y-2">
                {secrets.keys.map((key, index) => (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-accent/30 hover:bg-accent/50 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <Lock className="w-4 h-4 text-muted-foreground" />
                      <span className="font-mono text-sm">{key}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground font-mono hidden sm:inline">
                        {'{{'}secret:{key}{'}}'}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(key)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        {copiedKey === key ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Key className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                <p className="text-muted-foreground">No secrets configured</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Add secrets to your secrets.env file and reload
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Security Notes */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="border-yellow-500/50 bg-yellow-500/5">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-yellow-500">Security Note</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  Secret values are never exposed through the admin interface. Only key names are shown.
                  Use the {'{{'}secret:KEY{'}}'} template syntax in tool parameters to inject secrets securely.
                  Secrets are resolved at execution time and masked in audit logs.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Usage Guide */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Usage Guide</CardTitle>
            <CardDescription>How to use secrets in tool parameters</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-accent/30">
                <h4 className="font-medium mb-2">Template Syntax</h4>
                <code className="text-sm font-mono block p-2 bg-background rounded border border-border">
                  {'{{'}secret:YOUR_SECRET_KEY{'}}'}
                </code>
                <p className="text-sm text-muted-foreground mt-2">
                  Use this syntax anywhere you need to inject a secret value, such as:
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-accent/30">
                  <h4 className="font-medium mb-2">HTTP Headers</h4>
                  <pre className="text-xs font-mono p-2 bg-background rounded border border-border overflow-x-auto">
{`{
  "url": "https://api.example.com",
  "headers": {
    "Authorization": "Bearer {{secret:API_KEY}}"
  }
}`}
                  </pre>
                </div>

                <div className="p-4 rounded-lg bg-accent/30">
                  <h4 className="font-medium mb-2">Git Credentials</h4>
                  <pre className="text-xs font-mono p-2 bg-background rounded border border-border overflow-x-auto">
{`{
  "repo_path": ".",
  "auth_username": "{{secret:GIT_USER}}",
  "auth_password": "{{secret:GIT_TOKEN}}"
}`}
                  </pre>
                </div>

                <div className="p-4 rounded-lg bg-accent/30">
                  <h4 className="font-medium mb-2">Shell Environment</h4>
                  <pre className="text-xs font-mono p-2 bg-background rounded border border-border overflow-x-auto">
{`{
  "command": "deploy.sh",
  "env": {
    "AWS_ACCESS_KEY_ID": "{{secret:AWS_KEY}}",
    "AWS_SECRET_ACCESS_KEY": "{{secret:AWS_SECRET}}"
  }
}`}
                  </pre>
                </div>

                <div className="p-4 rounded-lg bg-accent/30">
                  <h4 className="font-medium mb-2">HTTP Request Body</h4>
                  <pre className="text-xs font-mono p-2 bg-background rounded border border-border overflow-x-auto">
{`{
  "url": "https://api.example.com/auth",
  "json_body": {
    "client_id": "{{secret:CLIENT_ID}}",
    "client_secret": "{{secret:CLIENT_SECRET}}"
  }
}`}
                  </pre>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

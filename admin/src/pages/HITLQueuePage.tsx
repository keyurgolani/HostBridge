import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { wsClient } from '@/lib/websocket'
import { HITLRequest } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { formatRelativeTime, formatTimestamp } from '@/lib/utils'

export default function HITLQueuePage() {
  const [requests, setRequests] = useState<HITLRequest[]>([])
  const [selectedRequest, setSelectedRequest] = useState<HITLRequest | null>(null)

  useEffect(() => {
    // Connect to WebSocket if not already connected
    if (!wsClient.isConnected()) {
      wsClient.connect()
    }

    // Request current pending requests when component mounts
    // This ensures we get the latest state even if WebSocket was already connected
    wsClient.requestPendingRequests()

    const unsubscribe = wsClient.onMessage((message) => {
      if (message.type === 'pending_requests') {
        setRequests(message.data)
      } else if (message.type === 'hitl_request') {
        // Add new request only if it doesn't already exist
        setRequests((prev) => {
          const exists = prev.some(req => req.id === message.data.id)
          if (exists) {
            console.log('Duplicate HITL request ignored:', message.data.id)
            return prev
          }
          return [message.data, ...prev]
        })
        // Play notification sound
        playNotificationSound()
      } else if (message.type === 'hitl_update') {
        setRequests((prev) =>
          prev.map((req) => (req.id === message.data.id ? message.data : req))
        )
        // Update selected request if it matches
        setSelectedRequest((current) => 
          current?.id === message.data.id ? message.data : current
        )
      }
    })

    // Don't disconnect on unmount - keep WebSocket alive for the app
    return () => {
      unsubscribe()
    }
  }, []) // Empty dependency array - only connect once

  const playNotificationSound = () => {
    // Create a simple beep sound
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    oscillator.frequency.value = 800
    oscillator.type = 'sine'
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)
    
    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.5)
  }

  const handleApprove = (id: string) => {
    wsClient.approveRequest(id)
  }

  const handleReject = (id: string) => {
    wsClient.rejectRequest(id, 'Rejected by administrator')
  }

  const pendingRequests = requests.filter((r) => r.status === 'pending')

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl md:text-4xl font-bold gradient-text mb-2">HITL Approval Queue</h1>
          <p className="text-sm md:text-base text-muted-foreground">
            Review and approve tool execution requests in real-time
          </p>
        </div>
        
        {/* Quick Stats */}
        <div className="flex gap-3">
          <div className="px-4 py-2 rounded-lg bg-accent/50 border border-border">
            <div className="text-xs text-muted-foreground">Pending</div>
            <div className="text-2xl font-bold text-yellow-500">{pendingRequests.length}</div>
          </div>
          <div className="px-4 py-2 rounded-lg bg-accent/50 border border-border">
            <div className="text-xs text-muted-foreground">Total</div>
            <div className="text-2xl font-bold">{requests.length}</div>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
        {/* Queue List */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <CardTitle className="text-lg md:text-xl">Pending Requests</CardTitle>
                <Badge variant={pendingRequests.length > 0 ? 'warning' : 'default'} className="w-fit">
                  {pendingRequests.length} pending
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <AnimatePresence mode="popLayout">
                {pendingRequests.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-center py-12"
                  >
                    <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500 opacity-50" />
                    <p className="text-muted-foreground">No pending requests</p>
                    <p className="text-sm text-muted-foreground mt-2">
                      All tool executions are running smoothly
                    </p>
                  </motion.div>
                ) : (
                  <div className="space-y-3">
                    {pendingRequests.map((request, index) => (
                      <HITLRequestCard
                        key={request.id}
                        request={request}
                        index={index}
                        isSelected={selectedRequest?.id === request.id}
                        onSelect={() => setSelectedRequest(request)}
                        onApprove={() => handleApprove(request.id)}
                        onReject={() => handleReject(request.id)}
                      />
                    ))}
                  </div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>
        </div>

        {/* Request Details */}
        <div className="lg:col-span-1">
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle>Request Details</CardTitle>
              <CardDescription>
                {selectedRequest ? 'Review the full request' : 'Select a request to view details'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedRequest ? (
                <RequestDetails request={selectedRequest} />
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No request selected</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function HITLRequestCard({
  request,
  index,
  isSelected,
  onSelect,
  onApprove,
  onReject,
}: {
  request: HITLRequest
  index: number
  isSelected: boolean
  onSelect: () => void
  onApprove: () => void
  onReject: () => void
}) {
  const [timeLeft, setTimeLeft] = useState(0)

  useEffect(() => {
    const updateTimeLeft = () => {
      const created = new Date(request.created_at).getTime()
      const now = Date.now()
      const elapsed = (now - created) / 1000
      const remaining = Math.max(0, request.ttl_seconds - elapsed)
      setTimeLeft(remaining)
    }

    updateTimeLeft()
    const interval = setInterval(updateTimeLeft, 1000)
    return () => clearInterval(interval)
  }, [request])

  const progress = (timeLeft / request.ttl_seconds) * 100

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ delay: index * 0.05 }}
      onClick={onSelect}
      className={`glass rounded-lg p-3 md:p-4 cursor-pointer transition-all duration-200 ${
        isSelected ? 'ring-2 ring-primary glow' : 'hover:bg-accent/50'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-base md:text-lg truncate">
            {request.tool_category}_{request.tool_name}
          </h4>
          <p className="text-xs md:text-sm text-muted-foreground">
            {formatRelativeTime(request.created_at)}
          </p>
        </div>
        <Badge variant="warning" className="w-fit">
          <Clock className="w-3 h-3 mr-1" />
          {Math.floor(timeLeft)}s
        </Badge>
      </div>

      <div className="mb-3">
        <div className="h-1.5 md:h-2 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-yellow-500 to-orange-500"
            initial={{ width: '100%' }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 1 }}
          />
        </div>
      </div>

      <p className="text-xs md:text-sm text-muted-foreground mb-3 line-clamp-2">
        {request.policy_rule_matched}
      </p>

      <div className="flex flex-col sm:flex-row gap-2">
        <Button
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onApprove()
          }}
          className="flex-1 text-sm"
        >
          <CheckCircle className="w-4 h-4 mr-1" />
          Approve
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={(e) => {
            e.stopPropagation()
            onReject()
          }}
          className="flex-1 text-sm"
        >
          <XCircle className="w-4 h-4 mr-1" />
          Reject
        </Button>
      </div>
    </motion.div>
  )
}

function RequestDetails({ request }: { request: HITLRequest }) {
  return (
    <div className="space-y-4">
      <div>
        <h5 className="text-sm font-semibold text-muted-foreground mb-1">Tool</h5>
        <p className="font-mono text-sm">
          {request.tool_category}_{request.tool_name}
        </p>
      </div>

      <div>
        <h5 className="text-sm font-semibold text-muted-foreground mb-1">Created</h5>
        <p className="text-sm">{formatTimestamp(request.created_at)}</p>
      </div>

      <div>
        <h5 className="text-sm font-semibold text-muted-foreground mb-1">Policy Rule</h5>
        <p className="text-sm">{request.policy_rule_matched}</p>
      </div>

      <div>
        <h5 className="text-sm font-semibold text-muted-foreground mb-1">Parameters</h5>
        <pre className="text-xs bg-muted/50 p-3 rounded-lg overflow-auto max-h-64">
          {JSON.stringify(request.request_params, null, 2)}
        </pre>
      </div>

      <div>
        <h5 className="text-sm font-semibold text-muted-foreground mb-1">Context</h5>
        <pre className="text-xs bg-muted/50 p-3 rounded-lg overflow-auto">
          {JSON.stringify(request.request_context, null, 2)}
        </pre>
      </div>
    </div>
  )
}

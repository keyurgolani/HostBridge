import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { formatDistanceToNow, format } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTimestamp(timestamp: string): string {
  return format(new Date(timestamp), 'MMM d, yyyy HH:mm:ss')
}

export function formatRelativeTime(timestamp: string): string {
  return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
}

export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  }
  if (ms < 60000) {
    return `${(ms / 1000).toFixed(2)}s`
  }
  return `${(ms / 60000).toFixed(2)}m`
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'success':
    case 'approved':
    case 'hitl_approved':
      return 'text-green-500'
    case 'error':
    case 'rejected':
    case 'hitl_rejected':
    case 'blocked':
      return 'text-red-500'
    case 'pending':
    case 'hitl_pending':
      return 'text-yellow-500'
    case 'expired':
    case 'hitl_expired':
      return 'text-orange-500'
    default:
      return 'text-gray-500'
  }
}

export function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'success':
    case 'approved':
    case 'hitl_approved':
      return 'bg-green-500/10 text-green-500 border-green-500/20'
    case 'error':
    case 'rejected':
    case 'hitl_rejected':
    case 'blocked':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'pending':
    case 'hitl_pending':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'expired':
    case 'hitl_expired':
      return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

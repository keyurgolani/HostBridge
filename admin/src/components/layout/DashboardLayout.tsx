import { Outlet, NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Bell, Activity, FileText, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { AuroraBackground } from '../effects/AuroraBackground'
import { FloatingParticles } from '../effects/FloatingParticles'
import { cn } from '@/lib/utils'

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const logout = useAuthStore((state) => state.logout)

  const navItems = [
    { to: '/hitl', icon: Bell, label: 'HITL Queue' },
    { to: '/audit', icon: FileText, label: 'Audit Log' },
    { to: '/health', icon: Activity, label: 'System Health' },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      <AuroraBackground />
      <FloatingParticles />
      
      {/* Header */}
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50"
      >
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <motion.h1
              className="text-2xl font-bold gradient-text"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              HostBridge Admin
            </motion.h1>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={logout}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
          >
            <LogOut size={18} />
            <span>Logout</span>
          </motion.button>
        </div>
      </motion.header>

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -300 }}
        animate={{ x: sidebarOpen ? 0 : -300 }}
        transition={{ type: 'spring', damping: 20 }}
        className="fixed left-0 top-16 bottom-0 w-64 glass border-r border-border/50 z-40"
      >
        <nav className="p-4 space-y-2">
          {navItems.map((item, index) => (
            <motion.div
              key={item.to}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-lg glow'
                      : 'hover:bg-accent hover:text-accent-foreground'
                  )
                }
              >
                <item.icon size={20} />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            </motion.div>
          ))}
        </nav>
      </motion.aside>

      {/* Main Content */}
      <main
        className={cn(
          'pt-20 transition-all duration-300',
          sidebarOpen ? 'pl-64' : 'pl-0'
        )}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

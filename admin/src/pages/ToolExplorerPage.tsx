import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, ChevronRight, CheckCircle, AlertCircle, Code,
  FileJson, Shield, Wrench
} from 'lucide-react'
import { api, ToolSchema } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'

export default function ToolExplorerPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedTool, setSelectedTool] = useState<ToolSchema | null>(null)

  const { data: toolsData, isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: () => api.getTools(),
  })

  const tools = toolsData?.tools || []

  // Filter tools
  const filteredTools = tools.filter((tool) => {
    const matchesSearch =
      searchTerm === '' ||
      tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCategory = !selectedCategory || tool.category === selectedCategory

    return matchesSearch && matchesCategory
  })

  // Get unique categories
  const categories = [...new Set(tools.map((t) => t.category))]

  // Group tools by category
  const toolsByCategory = categories.reduce((acc, category) => {
    acc[category] = filteredTools.filter((t) => t.category === category)
    return acc
  }, {} as Record<string, ToolSchema[]>)

  // Count tools requiring HITL
  const hitlCount = tools.filter((t) => t.requires_hitl).length

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl md:text-4xl font-bold gradient-text mb-2">Tool Explorer</h1>
        <p className="text-sm md:text-base text-muted-foreground">
          Browse and explore all available tools and their schemas
        </p>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={Wrench}
          label="Total Tools"
          value={tools.length}
          delay={0.1}
        />
        <StatCard
          icon={Code}
          label="Categories"
          value={categories.length}
          delay={0.2}
        />
        <StatCard
          icon={Shield}
          label="Requires HITL"
          value={hitlCount}
          variant="warning"
          delay={0.3}
        />
        <StatCard
          icon={CheckCircle}
          label="Auto-Approved"
          value={tools.length - hitlCount}
          variant="success"
          delay={0.4}
        />
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search tools..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedCategory(null)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                  !selectedCategory
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-accent hover:bg-accent/80'
                )}
              >
                All
              </button>
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors capitalize',
                    selectedCategory === category
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-accent hover:bg-accent/80'
                  )}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tools List */}
        <div className="lg:col-span-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(toolsByCategory).map(([category, categoryTools]) => (
                <motion.div
                  key={category}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg capitalize">{category}</CardTitle>
                        <Badge variant="default">{categoryTools.length}</Badge>
                      </div>
                      <CardDescription>
                        {category === 'fs' && 'Filesystem operations for reading, writing, and managing files'}
                        {category === 'workspace' && 'Workspace management and configuration tools'}
                        {category === 'shell' && 'Shell command execution with security controls'}
                        {category === 'git' && 'Git version control operations'}
                        {category === 'docker' && 'Docker container management'}
                        {category === 'http' && 'HTTP client for making web requests'}
                        {category === 'memory' && 'Knowledge graph memory operations'}
                        {category === 'plan' && 'DAG-based plan execution tools'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {categoryTools.map((tool) => (
                          <ToolItem
                            key={`${tool.category}_${tool.name}`}
                            tool={tool}
                            isSelected={selectedTool?.name === tool.name && selectedTool?.category === tool.category}
                            onSelect={() => setSelectedTool(tool)}
                          />
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}

              {filteredTools.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No tools found matching your search</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tool Details */}
        <div className="lg:col-span-1">
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle>Tool Details</CardTitle>
              <CardDescription>
                {selectedTool ? 'View schema and parameters' : 'Select a tool to view details'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AnimatePresence mode="wait">
                {selectedTool ? (
                  <motion.div
                    key={selectedTool.name}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="space-y-4"
                  >
                    <div>
                      <h4 className="font-semibold text-lg">
                        {selectedTool.category}_{selectedTool.name}
                      </h4>
                      <p className="text-sm text-muted-foreground mt-1">
                        {selectedTool.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge variant={selectedTool.requires_hitl ? 'warning' : 'success'}>
                        {selectedTool.requires_hitl ? 'Requires HITL' : 'Auto-Approved'}
                      </Badge>
                      <Badge variant="default" className="capitalize">
                        {selectedTool.category}
                      </Badge>
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <FileJson className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Input Schema</span>
                      </div>
                      <pre className="text-xs bg-muted/50 p-3 rounded-lg overflow-auto max-h-64 font-mono">
                        {JSON.stringify(selectedTool.input_schema, null, 2)}
                      </pre>
                    </div>

                    {selectedTool.output_schema && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <FileJson className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm font-medium">Output Schema</span>
                        </div>
                        <pre className="text-xs bg-muted/50 p-3 rounded-lg overflow-auto max-h-64 font-mono">
                          {JSON.stringify(selectedTool.output_schema, null, 2)}
                        </pre>
                      </div>
                    )}
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-8 text-muted-foreground"
                  >
                    <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No tool selected</p>
                    <p className="text-sm mt-1">Click on a tool to view its details</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function ToolItem({
  tool,
  isSelected,
  onSelect,
}: {
  tool: ToolSchema
  isSelected: boolean
  onSelect: () => void
}) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        'w-full flex items-center justify-between p-3 rounded-lg transition-all text-left',
        isSelected
          ? 'bg-primary/10 border border-primary/50 ring-1 ring-primary'
          : 'bg-accent/30 hover:bg-accent/50 border border-transparent'
      )}
    >
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <Code className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        <div className="min-w-0 flex-1">
          <code className="text-sm font-mono truncate block">{tool.name}</code>
          <p className="text-xs text-muted-foreground truncate">{tool.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {tool.requires_hitl && (
          <Shield className="w-4 h-4 text-yellow-500" />
        )}
        <ChevronRight className={cn(
          'w-4 h-4 text-muted-foreground transition-transform',
          isSelected && 'rotate-90'
        )} />
      </div>
    </button>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  variant = 'default',
  delay = 0,
}: {
  icon: any
  label: string
  value: number
  variant?: 'default' | 'success' | 'warning'
  delay?: number
}) {
  const variantClasses = {
    default: 'text-primary',
    success: 'text-green-500',
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
            <Icon className={`w-6 h-6 ${variantClasses[variant]} opacity-50`} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

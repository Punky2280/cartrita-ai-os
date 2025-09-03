// Cartrita AI OS - Search Interface Component
// Advanced global search with filtering, highlighting, and real-time results

'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Search,
  X,
  Filter,
  Calendar,
  User,
  MessageSquare,
  Bot,
  FileText,
  Hash,
  Clock,
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Copy,
  Bookmark,
  BookmarkCheck
} from 'lucide-react'
import { cn, formatMessageTime, highlightText } from '@/utils'
import { Button, Input, Badge, Card, CardContent, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Checkbox, Separator, ScrollArea } from '@/components/ui'
import { useSearch } from '@/hooks'
import type { SearchResult, SearchFilters, SearchResultType } from '@/types'

// Search result item component
function SearchResultItem({
  result,
  query,
  onClick,
  onBookmark,
  isBookmarked = false
}: {
  result: SearchResult
  query: string
  onClick: () => void
  onBookmark?: () => void
  isBookmarked?: boolean
}) {
  const getResultIcon = () => {
    switch (result.type) {
      case 'conversation':
        return MessageSquare
      case 'message':
        return MessageSquare
      case 'agent':
        return Bot
      case 'file':
        return FileText
      default:
        return Hash
    }
  }

  const getResultTypeLabel = () => {
    switch (result.type) {
      case 'conversation':
        return 'Conversation'
      case 'message':
        return 'Message'
      case 'agent':
        return 'Agent'
      case 'file':
        return 'File'
      default:
        return 'Other'
    }
  }

  const IconComponent = getResultIcon()

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="group"
    >
      <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="flex-shrink-0 mt-1">
              <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
                <IconComponent className="h-4 w-4 text-muted-foreground" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium truncate">
                    {highlightText(result.title, query)}
                  </h4>
                  <p className="text-xs text-muted-foreground mt-1">
                    {getResultTypeLabel()} • {formatMessageTime(result.timestamp)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {onBookmark && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onBookmark()
                      }}
                      className="h-8 w-8 p-0 bg-transparent hover:bg-accent hover:text-accent-foreground rounded"
                    >
                      {isBookmarked ? (
                        <BookmarkCheck className="h-4 w-4 text-primary" />
                      ) : (
                        <Bookmark className="h-4 w-4" />
                      )}
                    </button>
                  )}

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      navigator.clipboard.writeText(result.url || result.title)
                      toast.success('Copied to clipboard')
                    }}
                    className="h-8 w-8 p-0 bg-transparent hover:bg-accent hover:text-accent-foreground rounded"
                  >
                    <Copy className="h-4 w-4" />
                  </button>

                  {result.url && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        window.open(result.url, '_blank')
                      }}
                      className="h-8 w-8 p-0 bg-transparent hover:bg-accent hover:text-accent-foreground rounded"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Preview/Snippet */}
              {result.snippet && (
                <div className="mt-2">
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {highlightText(result.snippet, query)}
                  </p>
                </div>
              )}

              {/* Metadata */}
              <div className="flex items-center gap-2 mt-2">
                {result.metadata?.author && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <User className="h-3 w-3" />
                    {result.metadata.author}
                  </div>
                )}

                {result.metadata?.conversationTitle && (
                  <Badge className="text-xs">
                    {result.metadata.conversationTitle}
                  </Badge>
                )}

                {result.metadata?.agentName && (
                  <Badge className="text-xs">
                    {result.metadata.agentName}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

// Search filters component
function SearchFilters({
  filters,
  onFiltersChange,
  resultCounts
}: {
  filters: SearchFilters
  onFiltersChange: (filters: SearchFilters) => void
  resultCounts: Record<SearchResultType, number>
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handleTypeToggle = useCallback((type: SearchResultType) => {
    const newTypes = filters.types.includes(type)
      ? filters.types.filter(t => t !== type)
      : [...filters.types, type]

    onFiltersChange({
      ...filters,
      types: newTypes
    })
  }, [filters, onFiltersChange])

  const handleDateRangeChange = useCallback((dateRange: string) => {
    onFiltersChange({
      ...filters,
      dateRange: dateRange as any
    })
  }, [filters, onFiltersChange])

  const handleSortChange = useCallback((sortBy: string) => {
    onFiltersChange({
      ...filters,
      sortBy: sortBy as any
    })
  }, [filters, onFiltersChange])

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-8 w-8 p-0 bg-transparent hover:bg-accent hover:text-accent-foreground rounded"
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </div>
      </CardHeader>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <CardContent className="pt-0 space-y-4">
              {/* Result Types */}
              <div>
                <h4 className="text-sm font-medium mb-2">Content Types</h4>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { type: 'conversation' as const, label: 'Conversations', icon: MessageSquare },
                    { type: 'message' as const, label: 'Messages', icon: MessageSquare },
                    { type: 'agent' as const, label: 'Agents', icon: Bot },
                    { type: 'file' as const, label: 'Files', icon: FileText }
                  ].map(({ type, label, icon: Icon }) => (
                    <div key={type} className="flex items-center space-x-2">
                      <Checkbox
                        id={type}
                        checked={filters.types.includes(type)}
                        onCheckedChange={() => handleTypeToggle(type)}
                      />
                      <label
                        htmlFor={type}
                        className="text-sm flex items-center gap-2 cursor-pointer"
                      >
                        <Icon className="h-3 w-3" />
                        {label}
                        <Badge className="text-xs">
                          {resultCounts[type] || 0}
                        </Badge>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Date Range */}
              <div>
                <h4 className="text-sm font-medium mb-2">Date Range</h4>
                <Select value={filters.dateRange} onValueChange={handleDateRangeChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Time</SelectItem>
                    <SelectItem value="today">Today</SelectItem>
                    <SelectItem value="week">This Week</SelectItem>
                    <SelectItem value="month">This Month</SelectItem>
                    <SelectItem value="year">This Year</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Sort By */}
              <div>
                <h4 className="text-sm font-medium mb-2">Sort By</h4>
                <Select value={filters.sortBy} onValueChange={handleSortChange}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="relevance">Relevance</SelectItem>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="title">Title</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  )
}

// Main Search Interface Component
interface SearchInterfaceProps {
  isOpen: boolean
  onClose: () => void
  initialQuery?: string
  className?: string
}

export function SearchInterface({
  isOpen,
  onClose,
  initialQuery = '',
  className
}: SearchInterfaceProps) {
  const [query, setQuery] = useState(initialQuery)
  const [activeTab, setActiveTab] = useState<SearchResultType>('all')
  const [bookmarkedResults, setBookmarkedResults] = useState<Set<string>>(new Set())

  const {
    data: searchResults,
    isLoading,
    error,
    refetch
  } = useSearch(query)

  const [filters, setFilters] = useState<SearchFilters>({
    types: ['all'],
    dateRange: 'all',
    sortBy: 'relevance'
  })

  const updateFilters = useCallback((newFilters: SearchFilters) => {
    setFilters(newFilters)
  }, [])

  // Reset query when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuery(initialQuery)
    }
  }, [isOpen, initialQuery])

  // Handle search
  const handleSearch = useCallback((searchQuery: string) => {
    setQuery(searchQuery)
  }, [])

  // Handle result click
  const handleResultClick = useCallback((result: SearchResult) => {
    // Navigate to the result
    if (result.url) {
      window.open(result.url, '_blank')
    } else {
      // Handle internal navigation
      console.log('Navigate to:', result)
    }
  }, [])

  // Handle bookmark toggle
  const handleBookmarkToggle = useCallback((resultId: string) => {
    setBookmarkedResults(prev => {
      const newSet = new Set(prev)
      if (newSet.has(resultId)) {
        newSet.delete(resultId)
      } else {
        newSet.add(resultId)
      }
      return newSet
    })
  }, [])

  // Filter results by type
  const filteredResults = useMemo(() => {
    // Temporary fix - use empty array until search is properly implemented
    const results: any[] = []
    if (!results || results.length === 0) return []

    if (activeTab === 'all') {
      return results.filter(result =>
        filters.types.length === 0 || filters.types.includes(result.type)
      )
    }

    return results.filter(result => result.type === activeTab)
  }, [activeTab, filters.types])

  // Get result counts by type
  const resultCounts = useMemo(() => {
    const counts: Record<SearchResultType, number> = {
      all: 0,
      conversation: 0,
      message: 0,
      agent: 0,
      file: 0
    }

    // Temporary fix - use empty array until search is properly implemented
    const results: any[] = []
    if (results) {
      results.forEach((result: any) => {
        const type = result.type as SearchResultType
        if (type in counts) {
          counts[type]++
        }
        counts.all++
      })
    }

    return counts
  }, [])

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === '/' && e.ctrlKey) {
        e.preventDefault()
        // Focus search input
        const searchInput = document.querySelector('input[type="text"]') as HTMLInputElement
        searchInput?.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className={cn(
          'fixed top-4 left-4 right-4 bottom-4 bg-background rounded-lg shadow-2xl overflow-hidden',
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-4 p-4 border-b">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search conversations, messages, agents, files..."
              value={query}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10 pr-10"
              autoFocus
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 bg-transparent hover:bg-accent hover:text-accent-foreground rounded"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <button onClick={onClose} className="h-9 px-3 bg-transparent hover:bg-accent hover:text-accent-foreground rounded">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex h-full">
          {/* Sidebar with filters */}
          <div className="w-80 border-r p-4 overflow-y-auto">
            <SearchFilters
              filters={filters}
              onFiltersChange={updateFilters}
              resultCounts={resultCounts}
            />
          </div>

          {/* Main content */}
          <div className="flex-1 flex flex-col">
            {/* Tabs */}
            <div className="border-b px-4 py-2">
              <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as SearchResultType)}>
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="all" className="text-xs">
                    All ({resultCounts.all})
                  </TabsTrigger>
                  <TabsTrigger value="conversation" className="text-xs">
                    Conversations ({resultCounts.conversation})
                  </TabsTrigger>
                  <TabsTrigger value="message" className="text-xs">
                    Messages ({resultCounts.message})
                  </TabsTrigger>
                  <TabsTrigger value="agent" className="text-xs">
                    Agents ({resultCounts.agent})
                  </TabsTrigger>
                  <TabsTrigger value="file" className="text-xs">
                    Files ({resultCounts.file})
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            {/* Results */}
            <div className="flex-1 overflow-hidden">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-muted-foreground">Searching...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <p className="text-destructive mb-2">Search failed</p>
                    <p className="text-sm text-muted-foreground">{error.message}</p>
                    <button
                      onClick={() => refetch()}
                      className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              ) : filteredResults.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                      {query ? 'No results found' : 'Start typing to search...'}
                    </p>
                    {query && (
                      <p className="text-sm text-muted-foreground mt-2">
                        Try adjusting your search terms or filters
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <ScrollArea className="h-full">
                  <div className="p-4 space-y-3">
                    {filteredResults.map((result) => (
                      <SearchResultItem
                        key={result.id}
                        result={result}
                        query={query}
                        onClick={() => handleResultClick(result)}
                        onBookmark={() => handleBookmarkToggle(result.id)}
                        isBookmarked={bookmarkedResults.has(result.id)}
                      />
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

// Compact search button
export function SearchButton({
  onClick,
  className
}: {
  onClick: () => void
  className?: string
}) {
  return (
    <button
      onClick={onClick}
      className={cn('inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 gap-2', className)}
    >
      <Search className="h-4 w-4" />
      <span className="hidden sm:inline">Search</span>
      <kbd className="hidden sm:inline-flex items-center gap-0.5 text-xs text-muted-foreground">
        <span>Ctrl</span>
        <span>/</span>
      </kbd>
    </button>
  )
}
// Cartrita AI OS - File Upload Component
// Advanced file upload with drag-and-drop, progress tracking, and preview


import { useState, useRef, useCallback } from 'react'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Upload,
  X,
  File,
  Image as ImageIcon,
  Video,
  Music,
  FileText,
  Archive,
  AlertCircle,
  Loader2,
  Eye
} from 'lucide-react'
import { cn, formatFileSize, getFileExtension, isImageFile } from '@/utils'
import { Progress, Alert, AlertDescription } from '@/components/ui'
import { useFileUpload, useMultipleFileUpload } from '@/hooks'

// File type icons
const getFileIcon = (filename: string) => {
  const ext = getFileExtension(filename).toLowerCase()

  if (isImageFile(filename)) return ImageIcon
  if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'].includes(ext)) return Video
  if (['mp3', 'wav', 'flac', 'aac', 'ogg'].includes(ext)) return Music
  if (['pdf', 'doc', 'docx', 'txt', 'rtf'].includes(ext)) return FileText
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return Archive

  return File
}

// File preview component
function FilePreview({
  file,
  onRemove,
  uploadProgress,
  className
}: {
  file: File
  onRemove?: () => void
  uploadProgress?: number
  className?: string
}) {
  const [preview, setPreview] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  // Generate preview for images
  useState(() => {
    if (isImageFile(file.name)) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  })

  const IconComponent = getFileIcon(file.name)

  return (
    <>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className={cn(
          'relative group border rounded-lg p-3 bg-background',
          className
        )}
      >
        <div className="flex items-start gap-3">
          {/* File Icon/Preview */}
          <div className="flex-shrink-0">
            {preview ? (
              <div className="relative w-12 h-12 rounded-lg overflow-hidden bg-muted">
                <Image
                  src={preview}
                  alt={file.name}
                  width={48}
                  height={48}
                  className="w-full h-full object-cover cursor-pointer"
                  onClick={() => { { setShowPreview(true);; }}}
                />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                  <Eye className="h-4 w-4 text-white opacity-0 group-hover:opacity-100" />
                </div>
              </div>
            ) : (
              <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center">
                <IconComponent className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
          </div>

          {/* File Info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(file.size)}
            </p>

            {/* Upload Progress */}
            {uploadProgress !== undefined && (
              <div className="mt-2 space-y-1">
                <Progress value={uploadProgress} className="h-1" />
                <p className="text-xs text-muted-foreground">
                  {uploadProgress === 100 ? 'Complete' : `Uploading... ${uploadProgress}%`}
                </p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1">
            {preview && (
              <button
                className="h-8 w-8 p-0"
                onClick={() => { { setShowPreview(true);; }}}
              >
                <Eye className="h-4 w-4" />
              </button>
            )}

            {onRemove && (
              <button
                className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                onClick={onRemove}
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </motion.div>

      {/* Image Preview Modal */}
      <AnimatePresence>
        {showPreview && preview && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
            onClick={() => { { setShowPreview(false);; }}}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="relative max-w-4xl max-h-full"
              onClick={(e) => e.stopPropagation()}
            >
              <Image
                src={preview}
                alt={file.name}
                width={800}
                height={600}
                className="max-w-full max-h-full object-contain rounded-lg"
              />
              <button
                className="h-8 w-8 p-0"
                onClick={() => { { setShowPreview(false);; }}}
              >
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

// Drag and drop zone component
function DropZone({
  onFilesSelected,
  accept,
  multiple = true,
  disabled = false,
  className
}: {
  onFilesSelected: (files: File[]) => void
  accept?: string
  multiple?: boolean
  disabled?: boolean
  className?: string
}) {
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragOver(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      onFilesSelected(files)
    }
  }, [disabled, onFilesSelected])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      onFilesSelected(files)
    }
    // Reset input
    e.target.value = ''
  }, [onFilesSelected])

  const handleClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click()
    }
  }, [disabled])

  return (
    <>
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragOver
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-muted-foreground/50',
          disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
        whileHover={!disabled ? { scale: 1.01 } : {}}
        whileTap={!disabled ? { scale: 0.99 } : {}}
      >
        <Upload className="h-8 w-8 mx-auto mb-4 text-muted-foreground" />
        <div className="space-y-2">
          <p className="text-sm font-medium">
            {isDragOver ? 'Drop files here' : 'Click to upload or drag and drop'}
          </p>
          <p className="text-xs text-muted-foreground">
            {accept ? `Supported formats: ${accept}` : 'Any file type supported'}
          </p>
        </div>
      </motion.div>

      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileInputChange}
        className="hidden"
      />
    </>
  )
}

// Main File Upload Component
interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  accept?: string
  multiple?: boolean
  maxFiles?: number
  maxSize?: number // in bytes
  disabled?: boolean
  showProgress?: boolean
  className?: string
}

export function FileUpload({
  onFilesSelected,
  accept,
  multiple = true,
  maxFiles = 10,
  maxSize = 10 * 1024 * 1024, // 10MB
  disabled = false,
  showProgress = true,
  className
}: FileUploadProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const [errors, setErrors] = useState<string[]>([])

  const uploadFile = useFileUpload()
  const uploadMultipleFiles = useMultipleFileUpload()

  const validateFiles = useCallback((files: File[]): { valid: File[], errors: string[] } => {
    const valid: File[] = []
    const errors: string[] = []

    files.forEach((file) => {
      // Check file size
      if (file.size > maxSize) {
        errors.push(`${file.name}: File size exceeds ${formatFileSize(maxSize)}`)
        return
      }

      // Check file count
      if (selectedFiles.length + valid.length >= maxFiles) {
        errors.push(`Maximum ${maxFiles} files allowed`)
        return
      }

      valid.push(file)
    })

    return { valid, errors }
  }, [selectedFiles.length, maxFiles, maxSize])

  const handleFilesSelected = useCallback((files: File[]) => {
    const { valid, errors: validationErrors } = validateFiles(files)

    if (validationErrors.length > 0) {
      setErrors(validationErrors)
      validationErrors.forEach(error => toast.error(error))
    }

    if (valid.length > 0) {
      setSelectedFiles(prev => [...prev, ...valid])
      setErrors([])
      onFilesSelected(valid)
    }
  }, [validateFiles, onFilesSelected])

  const handleRemoveFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0) return

    try {
      if (selectedFiles.length === 1) {
        const result = await uploadFile.mutateAsync({
          file: selectedFiles[0]
        })

        if (result.success) {
          setUploadProgress(prev => ({ ...prev, [selectedFiles[0].name]: 100 }))
          toast.success('File uploaded successfully')
        }
      } else {
        const result = await uploadMultipleFiles.mutateAsync({
          files: selectedFiles
        })

        if (result.success) {
          const progress: Record<string, number> = {}
          selectedFiles.forEach(file => {
            progress[file.name] = 100
          })
          setUploadProgress(prev => ({ ...prev, ...progress }))
          toast.success(`${selectedFiles.length} files uploaded successfully`)
        }
      }
    } catch {
      toast.error('Upload failed')
    }
  }, [selectedFiles, uploadFile, uploadMultipleFiles])

  const clearAll = useCallback(() => {
    setSelectedFiles([])
    setUploadProgress({})
    setErrors([])
  }, [])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Drop Zone */}
      <DropZone
        onFilesSelected={handleFilesSelected}
        accept={accept}
        multiple={multiple}
        disabled={disabled}
      />

      {/* Selected Files */}
      <AnimatePresence>
        {selectedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">
                Selected Files ({selectedFiles.length})
              </h4>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { { { handleUpload();;; }}}}
                  disabled={uploadFile.isPending || uploadMultipleFiles.isPending}
                >
                  {uploadFile.isPending || uploadMultipleFiles.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Upload className="h-4 w-4 mr-2" />
                  )}
                  Upload
                </button>
                <button
                  onClick={clearAll}
                >
                  Clear All
                </button>
              </div>
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <FilePreview
                  key={`${file.name}-${index}`}
                  file={file}
                  onRemove={() => handleRemoveFile(index)}
                  uploadProgress={showProgress ? uploadProgress[file.name] : undefined}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Errors */}
      <AnimatePresence>
        {errors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <ul className="list-disc list-inside space-y-1">
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* File Limits Info */}
      <div className="text-xs text-muted-foreground space-y-1">
        <p>• Maximum {maxFiles} files</p>
        <p>• Maximum file size: {formatFileSize(maxSize)}</p>
        {accept && <p>• Supported formats: {accept}</p>}
      </div>
    </div>
  )
}

// Compact file upload button
export function FileUploadButton({
  onFilesSelected,
  accept,
  multiple = true,
  disabled = false,
  className
}: {
  onFilesSelected: (files: File[]) => void
  accept?: string
  multiple?: boolean
  disabled?: boolean
  className?: string
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click()
    }
  }, [disabled])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      onFilesSelected(files)
    }
    // Reset input
    e.target.value = ''
  }, [onFilesSelected])

  return (
    <>
      <button
        onClick={handleClick}
        disabled={disabled}
        className={className}
      >
        <Upload className="h-4 w-4" />
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileInputChange}
        className="hidden"
      />
    </>
  )
}
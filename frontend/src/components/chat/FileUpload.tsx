"use client"

import React, { useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { X, FileText, Image, File, Upload, Plus } from "lucide-react"

interface FileUploadProps {
  files: File[]
  onFilesChange: (files: File[]) => void
  maxFiles?: number
  maxSizeMB?: number
}

const ALLOWED_TYPES = {
  "application/pdf": [".pdf"],
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "text/plain": [".txt"],
  "text/markdown": [".md"],
}

export function FileUpload({
  files,
  onFilesChange,
  maxFiles = 5,
  maxSizeMB = 10,
}: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)
  const [imagePreviews, setImagePreviews] = useState<Map<string, string>>(new Map())

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return

    const newFiles: File[] = []
    const maxSize = maxSizeMB * 1024 * 1024

    Array.from(fileList).forEach((file) => {
      // Check file count
      if (files.length + newFiles.length >= maxFiles) {
        return
      }

      // Check file size
      if (file.size > maxSize) {
        alert(`File ${file.name} exceeds ${maxSizeMB}MB limit`)
        return
      }

      // Check file type
      const isValidType = Object.keys(ALLOWED_TYPES).some((mimeType) => {
        const extensions = ALLOWED_TYPES[mimeType as keyof typeof ALLOWED_TYPES]
        return extensions.some((ext) => file.name.toLowerCase().endsWith(ext))
      })

      if (!isValidType) {
        alert(`File type not supported: ${file.name}`)
        return
      }

      newFiles.push(file)
    })

    if (newFiles.length > 0) {
      const updatedFiles = [...files, ...newFiles]
      onFilesChange(updatedFiles)
      
      // Generate image previews for new image files
      newFiles.forEach((file) => {
        if (file.type.startsWith("image/")) {
          const fileKey = `${file.name}-${file.size}`
          const reader = new FileReader()
          reader.onload = (e) => {
            if (e.target?.result) {
              setImagePreviews(prev => new Map(prev).set(fileKey, e.target!.result as string))
            }
          }
          reader.readAsDataURL(file)
        }
      })
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const removeFile = (index: number) => {
    const fileToRemove = files[index]
    const newFiles = files.filter((_, i) => i !== index)
    onFilesChange(newFiles)
    // Clean up preview for removed file
    if (fileToRemove) {
      const fileKey = `${fileToRemove.name}-${fileToRemove.size}`
      setImagePreviews(prev => {
        const newMap = new Map(prev)
        newMap.delete(fileKey)
        return newMap
      })
    }
  }

  const getFileIcon = (file: File) => {
    if (file.type === "application/pdf") {
      return <FileText className="w-4 h-4" />
    } else if (file.type.startsWith("image/")) {
      return <Image className="w-4 h-4" />
    } else {
      return <File className="w-4 h-4" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
    return (bytes / (1024 * 1024)).toFixed(1) + " MB"
  }

  const isImage = (file: File) => file.type.startsWith("image/")
  const canAddMore = files.length < maxFiles

  return (
    <div className="space-y-2">
      <input
        ref={fileInputRef}
        type="file"
        title="Upload Files"
        multiple
        accept=".pdf,.png,.jpg,.jpeg,.txt,.md"
        onChange={(e) => handleFiles(e.target.files)}
        className="hidden"
      />

      {/* Show upload area only when no files are present */}
      {files.length === 0 && (
        <div
          className={`border-2 border-dashed rounded-lg p-3 md:p-4 transition-colors ${
            dragActive
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-muted-foreground/50"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center justify-center space-y-2">
            <Upload className="w-5 h-5 md:w-6 md:h-6 text-muted-foreground" />
            <p className="text-xs md:text-sm text-muted-foreground text-center">
              Drag and drop files here, or{" "}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-primary hover:underline"
              >
                browse
              </button>
            </p>
            <p className="text-[10px] md:text-xs text-muted-foreground">
              PDF, Images, Text files (max {maxSizeMB}MB, up to {maxFiles} files)
            </p>
          </div>
        </div>
      )}

      {/* Show compact file list when files are present */}
      {files.length > 0 && (
        <div className="space-y-2">
          {/* Horizontal scrollable file list */}
          <div className="flex gap-2 overflow-x-auto pb-2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex-shrink-0 w-24 md:w-28 bg-muted/50 rounded-lg border border-white/10 overflow-hidden group relative"
              >
                {/* Image preview or icon */}
                {isImage(file) && imagePreviews.get(`${file.name}-${file.size}`) ? (
                  <div className="relative w-full h-20 md:h-24 bg-muted">
                    <img
                      src={imagePreviews.get(`${file.name}-${file.size}`)}
                      alt={file.name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
                  </div>
                ) : (
                  <div className="w-full h-20 md:h-24 bg-muted/80 flex items-center justify-center">
                    {getFileIcon(file)}
                  </div>
                )}
                
                {/* File info */}
                <div className="p-1.5 md:p-2 space-y-0.5">
                  <p className="text-[10px] md:text-xs font-medium truncate" title={file.name}>
                    {file.name}
                  </p>
                  <p className="text-[9px] md:text-[10px] text-muted-foreground">
                    {formatFileSize(file.size)}
                  </p>
                </div>

                {/* Remove button */}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  className="absolute top-1 right-1 h-6 w-6 md:h-7 md:w-7 p-0 rounded-full bg-black/50 hover:bg-black/70 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3 h-3 md:w-3.5 md:h-3.5" />
                </Button>
              </div>
            ))}

            {/* Add more files button */}
            {canAddMore && (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex-shrink-0 w-24 md:w-28 h-full min-h-[120px] md:min-h-[140px] border-2 border-dashed border-muted-foreground/25 hover:border-primary/50 rounded-lg flex flex-col items-center justify-center gap-1.5 md:gap-2 transition-colors bg-muted/30 hover:bg-muted/50"
              >
                <Plus className="w-5 h-5 md:w-6 md:h-6 text-muted-foreground" />
                <span className="text-[10px] md:text-xs text-muted-foreground text-center px-1">
                  Add more
                </span>
              </button>
            )}
          </div>

          {/* File count indicator */}
          <div className="flex items-center justify-between text-[10px] md:text-xs text-muted-foreground px-1">
            <span>
              {files.length} of {maxFiles} files
            </span>
            {files.length >= maxFiles && (
              <span className="text-orange-500">Maximum reached</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


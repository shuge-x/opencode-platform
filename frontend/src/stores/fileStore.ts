import { create } from 'zustand'

export interface FileItem {
  id: string
  name: string
  type: 'file' | 'folder'
  size?: number
  path: string
  createdAt: string
  updatedAt: string
  content?: string
  language?: string
}

interface FileState {
  files: FileItem[]
  currentFile: FileItem | null
  selectedFiles: string[]
  searchQuery: string
  loading: boolean
  
  // Actions
  setFiles: (files: FileItem[]) => void
  addFile: (file: FileItem) => void
  updateFile: (id: string, updates: Partial<FileItem>) => void
  deleteFiles: (ids: string[]) => void
  setCurrentFile: (file: FileItem | null) => void
  toggleFileSelection: (id: string) => void
  clearSelection: () => void
  setSearchQuery: (query: string) => void
  setLoading: (loading: boolean) => void
}

export const useFileStore = create<FileState>((set, get) => ({
  files: [
    {
      id: '1',
      name: 'src',
      type: 'folder',
      path: '/src',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: '2',
      name: 'App.tsx',
      type: 'file',
      size: 2048,
      path: '/src/App.tsx',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      language: 'typescript',
      content: `import React from 'react'\n\nexport default function App() {\n  return <div>Hello World</div>\n}`
    },
    {
      id: '3',
      name: 'index.css',
      type: 'file',
      size: 512,
      path: '/src/index.css',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      language: 'css',
      content: `body {\n  margin: 0;\n  padding: 0;\n}\n`
    },
    {
      id: '4',
      name: 'package.json',
      type: 'file',
      size: 1024,
      path: '/package.json',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      language: 'json',
      content: `{\n  "name": "my-app",\n  "version": "1.0.0"\n}\n`
    }
  ],
  currentFile: null,
  selectedFiles: [],
  searchQuery: '',
  loading: false,

  setFiles: (files) => set({ files }),
  
  addFile: (file) => set((state) => ({
    files: [...state.files, file]
  })),
  
  updateFile: (id, updates) => set((state) => ({
    files: state.files.map(f => f.id === id ? { ...f, ...updates } : f),
    currentFile: state.currentFile?.id === id 
      ? { ...state.currentFile, ...updates } 
      : state.currentFile
  })),
  
  deleteFiles: (ids) => set((state) => ({
    files: state.files.filter(f => !ids.includes(f.id)),
    selectedFiles: [],
    currentFile: ids.includes(state.currentFile?.id || '') ? null : state.currentFile
  })),
  
  setCurrentFile: (file) => set({ currentFile: file }),
  
  toggleFileSelection: (id) => set((state) => ({
    selectedFiles: state.selectedFiles.includes(id)
      ? state.selectedFiles.filter(fid => fid !== id)
      : [...state.selectedFiles, id]
  })),
  
  clearSelection: () => set({ selectedFiles: [] }),
  
  setSearchQuery: (query) => set({ searchQuery: query }),
  
  setLoading: (loading) => set({ loading })
}))

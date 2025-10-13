import React, { useState, useRef, useEffect } from 'react'
import { Send, Upload, FileText, X, Bot, User } from 'lucide-react'
import { useDropzone } from 'react-dropzone'

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  files?: File[]
}

interface UploadedFile {
  id: string
  file: File
  status: 'uploading' | 'uploaded' | 'error'
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I can help you research information and answer questions. You can upload documents or ask me anything!',
      sender: 'assistant',
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const onDrop = (acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'uploading' as const
    }))
    
    setUploadedFiles(prev => [...prev, ...newFiles])
    
    // Simulate upload process
    setTimeout(() => {
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === newFiles.find(nf => nf.id === f.id)?.id 
            ? { ...f, status: 'uploaded' as const }
            : f
        )
      )
    }, 2000)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    multiple: true
  })

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const sendMessage = async () => {
    if (!inputValue.trim() && uploadedFiles.length === 0) return

    const newMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
      files: uploadedFiles.map(f => f.file)
    }

    setMessages(prev => [...prev, newMessage])
    setInputValue('')
    setUploadedFiles([])
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        "I've analyzed your question and the uploaded documents. Based on the information available, I can provide you with a comprehensive answer.",
        "Let me search through the knowledge base and conduct additional research to give you the most accurate information.",
        "I found relevant information in the uploaded documents. Here's what I discovered...",
        "This question requires deep research beyond what's in our current knowledge base. I'll conduct a thorough investigation.",
        "Based on the documents you've shared, I can see several key points that address your question."
      ]
      
      const response: Message = {
        id: Math.random().toString(36).substr(2, 9),
        content: responses[Math.floor(Math.random() * responses.length)],
        sender: 'assistant',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, response])
      setIsTyping(false)
    }, 2000)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">Research Assistant</h1>
              <p className="text-sm text-gray-400">Knowledge Base Conductor</p>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="pb-32 pt-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} px-4 mb-4`}>
            <div className={`flex items-start space-x-3 max-w-[80%] ${message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.sender === 'user' 
                  ? 'bg-gray-600' 
                  : 'bg-gradient-to-r from-blue-500 to-purple-500'
              }`}>
                {message.sender === 'user' ? (
                  <User className="w-4 h-4 text-white" />
                ) : (
                  <Bot className="w-4 h-4 text-white" />
                )}
              </div>
              <div className={`chat-bubble ${message.sender}`}>
                <p className="text-sm leading-relaxed">{message.content}</p>
                {message.files && message.files.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {message.files.map((file, index) => (
                      <div key={index} className="flex items-center space-x-2 text-xs bg-gray-600/50 rounded-lg px-3 py-2">
                        <FileText className="w-3 h-3" />
                        <span>{file.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start px-4 mb-4">
            <div className="flex items-start space-x-3 max-w-[80%]">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="chat-bubble assistant">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* File Upload Area */}
      {uploadedFiles.length === 0 && (
        <div className="fixed bottom-32 left-0 right-0 px-4">
          <div className="max-w-4xl mx-auto">
            <div
              {...getRootProps()}
              className={`file-upload-area ${isDragActive ? 'dragover' : ''}`}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg text-gray-300 mb-2">
                {isDragActive
                  ? 'Drop the files here...'
                  : 'Drag & drop files here, or click to select files'
                }
              </p>
              <p className="text-sm text-gray-400">
                Supports PDF, TXT, DOC, DOCX files
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="fixed bottom-32 left-0 right-0 px-4">
          <div className="max-w-4xl mx-auto">
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 shadow-lg">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Uploaded Files</h3>
              <div className="space-y-2">
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg border border-gray-600">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-gray-400" />
                      <span className="text-sm text-gray-200">{file.file.name}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        file.status === 'uploading' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' :
                        file.status === 'uploaded' ? 'bg-green-500/20 text-green-300 border border-green-500/30' :
                        'bg-red-500/20 text-red-300 border border-red-500/30'
                      }`}>
                        {file.status}
                      </span>
                    </div>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="text-gray-400 hover:text-red-400 transition-colors p-1"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="input-area">
        <div className="input-container">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Message Research Assistant..."
                className="w-full px-4 py-3 pr-12 border border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-gray-800 text-gray-100 placeholder-gray-400"
                rows={1}
                style={{ minHeight: '48px', maxHeight: '120px' }}
              />
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim() && uploadedFiles.length === 0}
                className="absolute right-2 bottom-2 p-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

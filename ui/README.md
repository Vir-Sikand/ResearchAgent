# Research Chat UI

A modern, standalone React UI for document upload and chat interface that will integrate with your research backend.

## Features

- **Modern Chat Interface**: Clean, responsive chat UI with message bubbles
- **Drag & Drop File Upload**: Support for PDF, TXT, DOC, DOCX files
- **Real-time Typing Indicators**: Shows when the assistant is "thinking"
- **File Management**: Upload multiple files with status indicators
- **Responsive Design**: Works on desktop and mobile devices
- **TypeScript**: Full type safety and better development experience

## Quick Start

1. **Install dependencies**:
   ```bash
   cd ui
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open in browser**: http://localhost:3000

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Dropzone** for file uploads
- **Lucide React** for icons
- **React Hook Form** for form handling

## Project Structure

```
ui/
├── src/
│   ├── App.tsx          # Main chat interface component
│   ├── main.tsx         # React entry point
│   └── index.css        # Global styles and Tailwind imports
├── package.json         # Dependencies and scripts
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
└── tsconfig.json        # TypeScript configuration
```

## Future Integration

This UI is designed to easily integrate with your existing backend:

- **API Endpoints**: Ready to connect to your MindsDB/agent-app services
- **File Upload**: Can be configured to upload to your backend
- **Real-time Updates**: Can be enhanced with WebSocket connections
- **Authentication**: Easy to add user authentication later

## Customization

- **Styling**: Modify `tailwind.config.js` and `src/index.css`
- **File Types**: Update the `accept` prop in the dropzone configuration
- **Messages**: Customize the mock responses in `App.tsx`
- **Layout**: Adjust the responsive breakpoints and spacing

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready to be served by any static file server.

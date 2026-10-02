import React, { useState } from 'react';
import { Navbar } from './components/Layout/Navbar';
import { Sidebar } from './components/Layout/Sidebar';
import { ChatArea } from './components/Chat/ChatArea';
import { ChatInput } from './components/Chat/ChatInput';
import { PdfViewerPanel } from './components/Documents/PdfViewerPanel';
import { useDocuments } from './hooks/useDocuments';
import { useChat } from './hooks/useChat';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';

export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeViewer, setActiveViewer] = useState<{
    docId: string;
    filename: string;
    page: number;
  } | null>(null);

  const {
    documents,
    selectedDocId,
    setSelectedDocId,
    uploadDocument,
    deleteDocument,
    isUploading,
    error: docError,
  } = useDocuments();

  const {
    messages,
    isStreaming,
    error: chatError,
    sendMessage,
    retryLastMessage,
    cancelStreaming,
    clearChat,
  } = useChat(selectedDocId);

  const selectedDoc = documents.find((d) => d.doc_id === selectedDocId);

  const handleOpenPdf = (docId: string, page: number, filename: string) => {
    setActiveViewer({
      docId,
      filename,
      page: page || 1,
    });
  };

  const handleViewFromSidebar = (docId: string, filename: string) => {
    setActiveViewer({
      docId,
      filename,
      page: 1,
    });
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <Navbar onClearChat={clearChat} />

      {/* Main Workspace Area */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Toggle Sidebar Button for Mobile */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute top-3 left-3 z-10 p-1.5 rounded-lg bg-slate-800/90 border border-slate-700 text-slate-400 hover:text-slate-200 transition-colors shadow-md md:hidden"
          title={sidebarOpen ? 'Fechar barra lateral' : 'Abrir barra lateral'}
        >
          {sidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
        </button>

        {/* Sidebar */}
        <div
          className={`${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } md:translate-x-0 transition-transform duration-200 ease-in-out absolute md:relative z-20 md:z-0 h-full`}
        >
          <Sidebar
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDoc={setSelectedDocId}
            onUpload={uploadDocument}
            onDelete={deleteDocument}
            onViewPdf={handleViewFromSidebar}
            isUploading={isUploading}
            error={docError}
          />
        </div>

        {/* Chat Conversation & Input */}
        <main className="flex-1 flex flex-col h-full bg-slate-950 overflow-hidden relative">
          <ChatArea
            messages={messages}
            isStreaming={isStreaming}
            error={chatError}
            onSendSuggestion={sendMessage}
            onOpenPdf={handleOpenPdf}
            onRetry={retryLastMessage}
          />
          <ChatInput
            onSend={sendMessage}
            onCancelStreaming={cancelStreaming}
            isStreaming={isStreaming}
            selectedDoc={selectedDoc}
            onClearDocFilter={() => setSelectedDocId(null)}
          />
        </main>

        {/* Integrated Side-by-Side PDF Viewer Panel */}
        {activeViewer && (
          <PdfViewerPanel
            docId={activeViewer.docId}
            filename={activeViewer.filename}
            initialPage={activeViewer.page}
            onClose={() => setActiveViewer(null)}
          />
        )}
      </div>
    </div>
  );
}

export default App;

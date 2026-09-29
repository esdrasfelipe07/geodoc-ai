import { useState, useEffect, useCallback } from 'react';
import { DocumentMetadata } from '../types';
import { api } from '../services/api';

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getDocuments();
      setDocuments(data.documents);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar documentos.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const uploadDocument = async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      const res = await api.uploadDocument(file);
      setDocuments((prev) => [res.document, ...prev]);
      return res.document;
    } catch (err: any) {
      setError(err.message || 'Erro ao fazer upload do documento.');
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const deleteDocument = async (docId: string) => {
    setError(null);
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
      if (selectedDocId === docId) {
        setSelectedDocId(null);
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao excluir documento.');
      throw err;
    }
  };

  return {
    documents,
    selectedDocId,
    setSelectedDocId,
    isLoading,
    isUploading,
    error,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
  };
}

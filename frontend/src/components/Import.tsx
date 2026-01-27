import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Upload, 
  FileText, 
  FolderOpen,
  Loader2,
  CheckCircle,
  AlertCircle,
  X,
  UploadCloud
} from 'lucide-react';
import { api } from '../api/client';
import clsx from 'clsx';

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  message?: string;
}

export function Import() {
  const { t } = useTranslation();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [directory, setDirectory] = useState('data/resumes');
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState<{ status: string; message: string } | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      (file) => 
        file.type === 'application/pdf' ||
        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        file.type === 'application/msword' ||
        file.type.startsWith('image/')
    );

    if (droppedFiles.length > 0) {
      setFiles((prev) => [
        ...prev,
        ...droppedFiles.map((file) => ({ file, status: 'pending' as const })),
      ]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    setFiles((prev) => [
      ...prev,
      ...selectedFiles.map((file) => ({ file, status: 'pending' as const })),
    ]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending');
    
    for (let i = 0; i < pendingFiles.length; i++) {
      const fileEntry = pendingFiles[i];
      const fileIndex = files.indexOf(fileEntry);
      
      setFiles((prev) => 
        prev.map((f, idx) => 
          idx === fileIndex ? { ...f, status: 'uploading' } : f
        )
      );

      try {
        await api.importFile(fileEntry.file);
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex 
              ? { ...f, status: 'success', message: t('common.success') } 
              : f
          )
        );
      } catch (err) {
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === fileIndex 
              ? { ...f, status: 'error', message: err instanceof Error ? err.message : t('common.error') } 
              : f
          )
        );
      }
    }
  };

  const handleBatchImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setBatchLoading(true);
    setBatchResult(null);

    try {
      const result = await api.importResumes({ directory });
      setBatchResult({ status: 'success', message: result.message });
    } catch (err) {
      setBatchResult({ 
        status: 'error', 
        message: err instanceof Error ? err.message : t('common.error') 
      });
    } finally {
      setBatchLoading(false);
    }
  };

  const pendingCount = files.filter((f) => f.status === 'pending').length;
  const successCount = files.filter((f) => f.status === 'success').length;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-2xl font-bold text-white">{t('import.title')}</h1>
        <p className="text-slate-400 mt-1">
          {t('import.subtitle')}
        </p>
      </div>

      {/* File Upload */}
      <div className="bg-void-800/50 border border-void-600/50 rounded-2xl p-6 animate-slide-up">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-neon-cyan" />
          {t('import.uploadFiles')}
        </h2>

        {/* Dropzone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={clsx(
            'relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200',
            dragActive 
              ? 'border-neon-cyan bg-neon-cyan/5' 
              : 'border-void-600 hover:border-void-500'
          )}
        >
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.png,.jpg,.jpeg"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <UploadCloud className={clsx(
            'w-12 h-12 mx-auto mb-4 transition-colors',
            dragActive ? 'text-neon-cyan' : 'text-slate-500'
          )} />
          <p className="text-slate-300 font-medium">
            {t('import.dropzone')}
          </p>
          <p className="text-slate-500 text-sm mt-1">
            {t('import.dropzoneHint')}
          </p>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 space-y-2">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-slate-400">
                {successCount > 0 && `${t('import.uploaded', { success: successCount })}, `}
                {t('import.pending', { count: pendingCount })}
              </p>
              {pendingCount > 0 && (
                <button
                  onClick={uploadFiles}
                  className="btn-primary text-sm py-2"
                >
                  {t('import.uploadButton', { count: pendingCount })}
                </button>
              )}
            </div>
            
            {files.map((fileEntry, i) => (
              <div
                key={i}
                className={clsx(
                  'flex items-center gap-3 p-3 rounded-lg border transition-colors',
                  fileEntry.status === 'success' && 'bg-neon-cyan/5 border-neon-cyan/30',
                  fileEntry.status === 'error' && 'bg-neon-pink/5 border-neon-pink/30',
                  fileEntry.status === 'uploading' && 'bg-neon-purple/5 border-neon-purple/30',
                  fileEntry.status === 'pending' && 'bg-void-700/30 border-void-600'
                )}
              >
                <FileText className={clsx(
                  'w-5 h-5',
                  fileEntry.status === 'success' && 'text-neon-cyan',
                  fileEntry.status === 'error' && 'text-neon-pink',
                  fileEntry.status === 'uploading' && 'text-neon-purple',
                  fileEntry.status === 'pending' && 'text-slate-500'
                )} />
                
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm truncate">{fileEntry.file.name}</p>
                  <p className="text-slate-500 text-xs">
                    {(fileEntry.file.size / 1024).toFixed(1)} KB
                    {fileEntry.message && ` • ${fileEntry.message}`}
                  </p>
                </div>

                {fileEntry.status === 'uploading' && (
                  <Loader2 className="w-5 h-5 text-neon-purple animate-spin" />
                )}
                {fileEntry.status === 'success' && (
                  <CheckCircle className="w-5 h-5 text-neon-cyan" />
                )}
                {fileEntry.status === 'error' && (
                  <AlertCircle className="w-5 h-5 text-neon-pink" />
                )}
                {fileEntry.status === 'pending' && (
                  <button
                    onClick={() => removeFile(i)}
                    className="p-1 text-slate-500 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Batch Import */}
      <div className="bg-void-800/50 border border-void-600/50 rounded-2xl p-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FolderOpen className="w-5 h-5 text-neon-purple" />
          {t('import.batchImport')}
        </h2>

        <form onSubmit={handleBatchImport} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-300 mb-2 block">
              {t('import.directoryPath')}
            </label>
            <input
              type="text"
              value={directory}
              onChange={(e) => setDirectory(e.target.value)}
              placeholder="data/resumes"
              className="input-field font-mono"
            />
            <p className="text-slate-500 text-xs mt-2">
              {t('import.directoryHint')}
            </p>
          </div>

          {batchResult && (
            <div className={clsx(
              'p-4 rounded-lg border',
              batchResult.status === 'success' 
                ? 'bg-neon-cyan/5 border-neon-cyan/30 text-neon-cyan'
                : 'bg-neon-pink/5 border-neon-pink/30 text-neon-pink'
            )}>
              {batchResult.message}
            </div>
          )}

          <button
            type="submit"
            disabled={batchLoading || !directory.trim()}
            className="btn-secondary flex items-center gap-2 disabled:opacity-50"
          >
            {batchLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {t('import.importing')}
              </>
            ) : (
              <>
                <FolderOpen className="w-5 h-5" />
                {t('import.importFromDirectory')}
              </>
            )}
          </button>
        </form>
      </div>

      {/* Tips */}
      <div className="bg-void-800/30 border border-void-600/30 rounded-xl p-5 animate-slide-up" style={{ animationDelay: '200ms' }}>
        <h3 className="font-medium text-white mb-3">{t('import.tips.title')}</h3>
        <ul className="space-y-2 text-sm text-slate-400">
          <li className="flex items-start gap-2">
            <span className="text-neon-cyan">•</span>
            {t('import.tips.pdf')}
          </li>
          <li className="flex items-start gap-2">
            <span className="text-neon-cyan">•</span>
            {t('import.tips.ocr')}
          </li>
          <li className="flex items-start gap-2">
            <span className="text-neon-cyan">•</span>
            {t('import.tips.ai')}
          </li>
          <li className="flex items-start gap-2">
            <span className="text-neon-cyan">•</span>
            {t('import.tips.duplicates')}
          </li>
        </ul>
      </div>
    </div>
  );
}

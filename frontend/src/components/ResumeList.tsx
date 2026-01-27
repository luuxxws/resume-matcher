import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Search, 
  FileText, 
  ChevronLeft, 
  ChevronRight,
  User,
  Mail,
  Phone,
  Briefcase,
  X,
  Trash2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { api, ResumeResponse, ResumeListResponse } from '../api/client';

function ResumeCard({ resume, onSelect, onDelete, t }: { 
  resume: ResumeResponse; 
  onSelect: () => void;
  onDelete: () => void;
  t: (key: string) => string;
}) {
  const json = resume.json_data as Record<string, unknown>;
  const name = json.full_name as string || 'Unknown';
  const position = json.current_position as string || 'No position';
  const email = json.email as string;
  const skills = (json.skills as string[]) || [];

  return (
    <div 
      className="group bg-void-800/50 border border-void-600/50 rounded-xl p-5 hover:border-neon-cyan/30 transition-all duration-200 cursor-pointer card-hover"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-neon-cyan/20 to-neon-purple/20 flex items-center justify-center">
            <User className="w-6 h-6 text-neon-cyan" />
          </div>
          <div>
            <h3 className="font-semibold text-white group-hover:text-neon-cyan transition-colors">
              {name}
            </h3>
            <p className="text-slate-400 text-sm">{position}</p>
            {email && (
              <p className="text-slate-500 text-xs mt-1 flex items-center gap-1">
                <Mail className="w-3 h-3" />
                {email}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {resume.has_embedding ? (
            <span className="badge badge-cyan">
              <CheckCircle className="w-3 h-3 mr-1" />
              {t('resumes.indexed_badge')}
            </span>
          ) : (
            <span className="badge badge-yellow">
              <AlertCircle className="w-3 h-3 mr-1" />
              {t('resumes.pending_badge')}
            </span>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-2 text-slate-500 hover:text-neon-pink hover:bg-neon-pink/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Skills */}
      {skills.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-4">
          {skills.slice(0, 5).map((skill, i) => (
            <span key={i} className="px-2 py-1 text-xs bg-void-700/50 text-slate-400 rounded">
              {skill}
            </span>
          ))}
          {skills.length > 5 && (
            <span className="px-2 py-1 text-xs bg-void-700/50 text-slate-500 rounded">
              +{skills.length - 5}
            </span>
          )}
        </div>
      )}

      <p className="text-xs text-slate-600 mt-3 truncate font-mono">
        {resume.file_name}
      </p>
    </div>
  );
}

function ResumeDetail({ resume, onClose, t }: { resume: ResumeResponse; onClose: () => void; t: (key: string, opts?: Record<string, unknown>) => string }) {
  const json = resume.json_data as Record<string, unknown>;
  const name = json.full_name as string || 'Unknown';
  const position = json.current_position as string || 'No position';
  const email = json.email as string;
  const phone = json.phone as string;
  const skills = (json.skills as string[]) || [];
  const summary = json.summary as string;
  const experience = json.years_experience as number;
  const education = (json.education as Array<{ degree?: string; institution?: string }>) || [];
  const workHistory = (json.work_history as Array<{ company?: string; position?: string; duration?: string }>) || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-void-800 border border-void-600 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-slide-up">
        {/* Header */}
        <div className="sticky top-0 bg-void-800 border-b border-void-600 p-6 flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-neon-cyan to-neon-purple flex items-center justify-center">
              <User className="w-7 h-7 text-void-900" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{name}</h2>
              <p className="text-slate-400">{position}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-void-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Contact */}
          <div className="flex flex-wrap gap-4">
            {email && (
              <div className="flex items-center gap-2 text-slate-400">
                <Mail className="w-4 h-4 text-neon-cyan" />
                <span className="text-sm">{email}</span>
              </div>
            )}
            {phone && (
              <div className="flex items-center gap-2 text-slate-400">
                <Phone className="w-4 h-4 text-neon-cyan" />
                <span className="text-sm">{phone}</span>
              </div>
            )}
            {experience && (
              <div className="flex items-center gap-2 text-slate-400">
                <Briefcase className="w-4 h-4 text-neon-cyan" />
                <span className="text-sm">{experience} years experience</span>
              </div>
            )}
          </div>

          {/* Summary */}
          {summary && (
            <div>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">{t('results.summary')}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{summary}</p>
            </div>
          )}

          {/* Skills */}
          {skills.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">{t('resumes.skills')}</h3>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill, i) => (
                  <span key={i} className="badge badge-cyan">{skill}</span>
                ))}
              </div>
            </div>
          )}

          {/* Work History */}
          {workHistory.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-slate-300 mb-3">{t('resumes.workHistory')}</h3>
              <div className="space-y-3">
                {workHistory.map((job, i) => (
                  <div key={i} className="pl-4 border-l-2 border-neon-purple/30">
                    <p className="text-white font-medium">{job.position}</p>
                    <p className="text-slate-400 text-sm">{job.company}</p>
                    {job.duration && (
                      <p className="text-slate-500 text-xs">{job.duration}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {education.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-slate-300 mb-3">{t('resumes.education')}</h3>
              <div className="space-y-2">
                {education.map((edu, i) => (
                  <div key={i} className="pl-4 border-l-2 border-neon-cyan/30">
                    <p className="text-white font-medium">{edu.degree}</p>
                    <p className="text-slate-400 text-sm">{edu.institution}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* File info */}
          <div className="pt-4 border-t border-void-600">
            <p className="text-xs text-slate-500 font-mono">
              <FileText className="w-3 h-3 inline mr-1" />
              {resume.file_name}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ResumeList() {
  const { t } = useTranslation();
  const [data, setData] = useState<ResumeListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [selectedResume, setSelectedResume] = useState<ResumeResponse | null>(null);
  const limit = 12;

  const fetchResumes = useCallback(() => {
    setLoading(true);
    api.listResumes({ limit, offset: page * limit, search: search || undefined })
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [page, search]);

  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchResumes();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this resume?')) return;
    try {
      await api.deleteResume(id);
      fetchResumes();
    } catch {
      alert('Failed to delete resume');
    }
  };

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('resumes.title')}</h1>
          <p className="text-slate-400 mt-1">
            {data ? t('resumes.indexed', { count: data.total }) : t('common.loading')}
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder={t('resumes.searchPlaceholder')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10 w-64"
            />
          </div>
          <button type="submit" className="btn-secondary">
            {t('resumes.search')}
          </button>
        </form>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-neon-pink/10 border border-neon-pink/30 rounded-xl p-4">
          <p className="text-neon-pink">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-40 rounded-xl skeleton" />
          ))}
        </div>
      )}

      {/* Resume Grid */}
      {!loading && data && (
        <>
          {data.resumes.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-400">{t('resumes.noResumes')}</h3>
              <p className="text-slate-500 mt-1">{t('resumes.noResumesHint')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.resumes.map((resume, i) => (
                <div
                  key={resume.id}
                  className="animate-slide-up opacity-0 [animation-fill-mode:forwards]"
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <ResumeCard
                    resume={resume}
                    onSelect={() => setSelectedResume(resume)}
                    onDelete={() => handleDelete(resume.id)}
                    t={t}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-2 text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-slate-400 text-sm">
                {t('resumes.page', { current: page + 1, total: totalPages })}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-2 text-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </>
      )}

      {/* Resume Detail Modal */}
      {selectedResume && (
        <ResumeDetail
          resume={selectedResume}
          onClose={() => setSelectedResume(null)}
          t={t}
        />
      )}
    </div>
  );
}

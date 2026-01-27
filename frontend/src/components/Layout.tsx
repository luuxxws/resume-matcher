import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  LayoutDashboard, 
  FileText, 
  Search, 
  Upload,
  Sparkles,
  Menu
} from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';
import { LanguageToggle } from './LanguageToggle';

export function Layout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: t('nav.dashboard'), href: '/', icon: LayoutDashboard },
    { name: t('nav.match'), href: '/match', icon: Search },
    { name: t('nav.resumes'), href: '/resumes', icon: FileText },
    { name: t('nav.import'), href: '/import', icon: Upload },
  ];

  return (
    <div className="min-h-screen bg-void-900 bg-grid-pattern bg-grid">
      {/* Background gradient overlay */}
      <div className="fixed inset-0 bg-gradient-radial from-neon-purple/5 via-transparent to-transparent pointer-events-none" />
      
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed top-0 left-0 z-50 h-screen w-64 bg-void-800/95 backdrop-blur-xl border-r border-void-600/50 transform transition-transform duration-300 ease-in-out',
        'lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 h-16 border-b border-void-600/50">
            <div className="relative">
              <Sparkles className="w-8 h-8 text-neon-cyan" />
              <div className="absolute inset-0 blur-md bg-neon-cyan/30 -z-10" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gradient">{t('app.name')}</h1>
              <p className="text-xs text-slate-500">{t('app.tagline')}</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group',
                    isActive 
                      ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20' 
                      : 'text-slate-400 hover:bg-void-700/50 hover:text-slate-200'
                  )}
                >
                  <item.icon className={clsx(
                    'w-5 h-5 transition-colors',
                    isActive ? 'text-neon-cyan' : 'text-slate-500 group-hover:text-slate-300'
                  )} />
                  <span className="font-medium">{item.name}</span>
                  {isActive && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-neon-cyan animate-pulse" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Footer with Language Toggle */}
          <div className="px-4 py-4 border-t border-void-600/50 space-y-3">
            <LanguageToggle />
            <div className="flex items-center gap-2 text-xs text-slate-500 px-2">
              <div className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse" />
              <span>{t('app.apiConnected')}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between px-4 h-16 bg-void-800/95 backdrop-blur-xl border-b border-void-600/50">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 text-slate-400 hover:text-white transition-colors"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-neon-cyan" />
              <span className="font-semibold text-gradient">{t('app.name')}</span>
            </div>
          </div>
          <LanguageToggle />
        </header>

        {/* Page content */}
        <main className="min-h-screen p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

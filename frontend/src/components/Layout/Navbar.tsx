import React, { useEffect, useState } from 'react';
import { Layers, Activity, Sparkles, Trash2, ExternalLink } from 'lucide-react';
import { api } from '../../services/api';
import { HealthStatus } from '../../types';

interface NavbarProps {
  onClearChat: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onClearChat }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    api.getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 flex items-center justify-between z-20 sticky top-0">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-950/40">
          <Layers className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-lg text-white tracking-tight">GeoDoc AI</h1>
            <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              RAG Geofísica
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Inteligência para Análise de Dados Sísmicos & Relatórios Técnicos
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Health status badge */}
        <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs">
          <span className={`w-2 h-2 rounded-full ${health ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          <span className="text-slate-300">
            {health ? `${health.llm_provider.toUpperCase()} (${health.llm_model})` : 'Conectando...'}
          </span>
        </div>

        {/* Clear chat button */}
        <button
          onClick={onClearChat}
          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors text-xs flex items-center space-x-1.5"
          title="Limpar conversa"
        >
          <Trash2 className="w-4 h-4" />
          <span className="hidden sm:inline">Limpar Chat</span>
        </button>

        {/* Swagger / Docs link */}
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-lg transition-colors flex items-center space-x-1.5"
        >
          <span>Swagger API</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </header>
  );
};

import React, { useState, useEffect, useRef } from "react";
import { 
  MessageSquare, Send, X, Minimize2, Maximize2, User, 
  ChevronDown, Search, CheckCheck, MapPin, Building, Share2, Paperclip, ShieldAlert
} from "lucide-react";
import { Collaborator } from "../types";

export interface ChatContact {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarColor: string;
  isOnline: boolean;
  structure?: string;
  province?: string;
}

export interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  receiverId: string;
  text: string;
  timestamp: string;
  isClauseShare?: boolean;
  clauseCode?: string;
  clauseExcerpt?: string;
}

interface MessagingWidgetProps {
  contacts: ChatContact[];
  currentProfile: { name: string; email: string };
  messages: ChatMessage[];
  onSendMessage: (receiverId: string, text: string, isClauseShare?: boolean, clauseCode?: string, clauseExcerpt?: string) => void;
  activeChatId: string;
  setActiveChatId: (id: string) => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export default function MessagingWidget({
  contacts,
  currentProfile,
  messages,
  onSendMessage,
  activeChatId,
  setActiveChatId,
  isOpen,
  setIsOpen
}: MessagingWidgetProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [inputText, setInputText] = useState("");
  const conversationEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  useEffect(() => {
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, activeChatId, isOpen, isMinimized]);

  const activeContact = contacts.find(c => c.id === activeChatId) || contacts[0];
  
  const filteredContacts = contacts.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.structure && c.structure.toLowerCase().includes(searchQuery.toLowerCase())) ||
    c.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeMessages = messages.filter(m => 
    (m.senderId === "me" && m.receiverId === activeChatId) ||
    (m.senderId === activeChatId && m.receiverId === "me")
  );

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendMessage(activeChatId, inputText.trim());
    setInputText("");
  };

  // Unread messages counts
  const getUnreadCount = (contactId: string) => {
    // We can simulate unread messages if desire, let's keep static demo unread flags 
    if (contactId === "marie-laurent" && messages.length <= 5) return 1;
    if (contactId === "chantal-mwamba" && messages.length <= 5) return 2;
    return 0;
  };

  if (!isOpen) {
    const unreadTotal = contacts.reduce((acc, c) => acc + getUnreadCount(c.id), 0);
    return (
      <button
        id="toggle-messaging-floating"
        onClick={() => {
          setIsOpen(true);
          setIsMinimized(false);
        }}
        className="fixed bottom-6 right-6 z-40 bg-[#020204] border border-emerald-500/30 hover:border-emerald-400 text-emerald-400 hover:text-emerald-300 font-bold px-4 py-3 rounded-full flex items-center gap-3.5 shadow-[0_10px_30px_rgba(0,0,0,0.5)] cursor-pointer group hover:scale-105 transition-all text-xs tracking-wider uppercase backdrop-blur-md"
      >
        <div className="relative">
          <MessageSquare className="h-5 w-5 fill-emerald-500/10 group-hover:animate-pulse" />
          {unreadTotal > 0 && (
            <span className="absolute -top-2.5 -right-2.5 h-4.5 w-4.5 rounded-full bg-red-500 text-white font-extrabold text-[9px] flex items-center justify-center animate-bounce shadow-md">
              {unreadTotal}
            </span>
          )}
        </div>
        <span className="font-sans font-bold select-none">Messagerie CNETP</span>
        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse inline-block"></span>
      </button>
    );
  }

  return (
    <div 
      className={`fixed z-40 bg-[#020204]/95 border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.8)] flex flex-col backdrop-blur-lg transition-all duration-300 ${
        isMinimized 
          ? "bottom-6 right-6 w-80 h-14" 
          : "bottom-6 right-6 w-[700px] h-[500px] max-w-[calc(100vw-2rem)] max-h-[calc(100vh-2rem)]"
      }`}
    >
      {/* HEADER */}
      <div className="h-14 border-b border-white/10 px-4.5 flex items-center justify-between shrink-0 bg-black/40 rounded-t-2xl">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 bg-emerald-500/15 border border-emerald-500/30 rounded-lg flex items-center justify-center text-emerald-400">
            <MessageSquare className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-xs font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
              Messagerie Sécurisée CNETP
              {!isMinimized && (
                <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-mono">
                  SÉCURISÉ (AES-256)
                </span>
              )}
            </h3>
            {isMinimized && (
              <p className="text-[10px] text-slate-500 font-medium">Discuter avec {activeContact.name}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button 
            type="button"
            onClick={() => setIsMinimized(!isMinimized)} 
            className="p-1.5 rounded-md text-slate-500 hover:text-white hover:bg-white/5 transition-all cursor-pointer"
            title={isMinimized ? "Agrandir" : "Réduire"}
          >
            <ChevronDown className={`h-4 w-4 transition-transform ${isMinimized ? "rotate-180" : ""}`} />
          </button>
          <button 
            type="button"
            onClick={() => setIsOpen(false)} 
            className="p-1.5 rounded-md text-slate-500 hover:text-white hover:bg-white/5 transition-all cursor-pointer"
            title="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* CONTENT (NOT SHOWN WHEN MINIMIZED) */}
      {!isMinimized && (
        <div className="flex-1 min-h-0 flex bg-transparent">
          
          {/* LEFT PANEL: CONTACTS LIST */}
          <div className="w-64 border-r border-white/10 flex flex-col h-full bg-black/25 shrink-0">
            <div className="p-3 border-b border-white/10">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3 w-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="Chercher un interlocuteur..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-white/5 bg-black/45 text-[11px] text-white font-medium focus:outline-hidden focus:border-emerald-500/30"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-white/5 scrollbar-none">
              {filteredContacts.length === 0 ? (
                <p className="p-4 text-[10.5px] text-slate-500 italic text-center">Aucun membre trouvé.</p>
              ) : (
                filteredContacts.map(c => {
                  const isSelected = c.id === activeChatId;
                  const unread = getUnreadCount(c.id);
                  return (
                    <button
                      key={c.id}
                      onClick={() => setActiveChatId(c.id)}
                      className={`w-full p-3 text-left transition-all duration-150 flex items-start gap-2.5 cursor-pointer relative ${
                        isSelected 
                          ? "bg-white/5" 
                          : "hover:bg-white/[0.02]"
                      }`}
                    >
                      {/* Avatar with indicator */}
                      <div 
                        className="h-8.5 w-8.5 rounded-full flex items-center justify-center text-white text-[10px] font-extrabold shrink-0 relative border border-white/10"
                        style={{ backgroundColor: c.avatarColor }}
                      >
                        {c.name.split(" ").map(n => n[0]).join("")}
                        {c.isOnline && (
                          <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 bg-emerald-500 border border-slate-900 rounded-full" />
                        )}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-1.5">
                          <span className="text-[11.5px] font-bold text-slate-200 truncate leading-snug">{c.name}</span>
                          {unread > 0 && (
                            <span className="px-1.5 py-0.5 rounded-full bg-emerald-500 text-black text-[8px] font-black shrink-0">
                              {unread}
                            </span>
                          )}
                        </div>
                        <p className="text-[9.5px] text-slate-400 mt-0.5 truncate font-semibold">{c.role}</p>
                        {c.structure && (
                          <p className="text-[8px] text-slate-500 mt-0.5 truncate font-mono">{c.structure.split(" (")[0]}</p>
                        )}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* RIGHT PANEL: ACTIVE THREAD */}
          <div className="flex-1 flex flex-col h-full bg-black/10">
            {/* Thread Header Info bar */}
            <div className="px-4.5 py-3 border-b border-white/5 bg-black/15 flex items-center justify-between shrink-0">
              <div className="min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <h4 className="text-xs font-extrabold text-white truncate">{activeContact.name}</h4>
                  <span className={`h-1.5 w-1.5 rounded-full ${activeContact.isOnline ? "bg-emerald-500" : "bg-slate-600"}`}></span>
                  <span className="text-[9px] text-slate-500 font-mono font-bold uppercase">{activeContact.isOnline ? "En ligne" : "Hors ligne"}</span>
                </div>
                <p className="text-[10px] text-slate-400 truncate mt-0.5 font-medium">
                  {activeContact.role} • <span className="text-emerald-400 font-semibold">{activeContact.structure}</span>
                </p>
              </div>
            </div>

            {/* Conversation Flow */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-none bg-[#020204]/30">
              {activeMessages.length === 0 ? (
                <p className="text-[10.5px] text-slate-500 italic py-12 text-center">Début de l'historique sécurisé des messages.</p>
              ) : (
                activeMessages.map(m => {
                  const isMe = m.senderId === "me";
                  return (
                    <div 
                      key={m.id}
                      className={`flex ${isMe ? "justify-end" : "justify-start"} animate-fadeIn`}
                    >
                      <div className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-xs shadow-sm leading-relaxed ${
                        isMe 
                          ? "bg-emerald-500/10 border border-emerald-500/25 text-slate-100" 
                          : "bg-white/[0.03] border border-white/5 text-slate-200"
                      }`}>
                        {/* If it's a clause share card, render beautifully */}
                        {m.isClauseShare && (
                          <div className="mb-2 pb-2 border-b border-white/10 text-[11px] bg-black/40 p-2.5 rounded-lg space-y-1.5 border-l-2 border-yellow-500 shadow-inner">
                            <div className="flex items-center gap-1.5 text-yellow-400 font-bold font-mono text-[9px] uppercase tracking-wider">
                              <Share2 className="h-3 w-3" />
                              Référence RDC : {m.clauseCode || "Clause de Norme"}
                            </div>
                            {m.clauseExcerpt && (
                              <blockquote className="text-[10px] text-slate-400 italic line-clamp-3 leading-normal border-l border-white/10 pl-2">
                                "{m.clauseExcerpt}"
                              </blockquote>
                            )}
                          </div>
                        )}

                        <p className="whitespace-pre-wrap">{m.text}</p>
                        
                        <div className="mt-1 flex items-center justify-end gap-1.5 text-[8.5px] text-white/40">
                          <span>{m.timestamp}</span>
                          {isMe && <CheckCheck className="h-3 w-3 text-emerald-400" />}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={conversationEndRef} />
            </div>

            {/* Input form */}
            <form onSubmit={handleSend} className="p-3 border-t border-white/10 bg-black/30 shrink-0">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder={`Écrire à ${activeContact.name.split(" ")[1] || activeContact.name}...`}
                  className="flex-1 text-xs px-3.5 py-2.5 rounded-lg border border-white/5 bg-black/50 text-white placeholder-slate-600 focus:outline-hidden focus:border-emerald-500/40 focus:ring-2 focus:ring-emerald-500/5 font-medium"
                />
                <button
                  type="submit"
                  disabled={!inputText.trim()}
                  className="h-9.5 w-9.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black flex items-center justify-center shrink-0 disabled:opacity-40 transition-all cursor-pointer shadow-md"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </form>

          </div>
        </div>
      )}
    </div>
  );
}

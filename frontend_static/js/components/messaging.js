/**
 * Messaging Widget Component
 */
const Messaging = {
    render(container) {
        container.innerHTML = `
            <!-- Floating Button -->
            <button onclick="Messaging.toggle()" class="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform z-50">
                <i data-lucide="message-square"></i>
            </button>

            <!-- Chat Window (hidden by default) -->
            <div id="chat-window" class="hidden fixed bottom-24 right-6 w-96 h-[500px] bg-[#020204] border border-white/10 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden animate-slideIn">
                <div class="p-4 border-b border-white/10 bg-white/5 flex items-center justify-between">
                    <h3 class="font-bold text-sm">Messagerie Sécurisée</h3>
                    <button onclick="Messaging.toggle()" class="text-slate-500 hover:text-white">
                        <i data-lucide="x" class="h-4 w-4"></i>
                    </button>
                </div>
                <div id="chat-messages" class="flex-1 overflow-y-auto p-4 space-y-4">
                    <div class="text-center text-[10px] text-slate-500 uppercase tracking-widest">Fin de la discussion cryptée</div>
                </div>
                <div class="p-4 border-t border-white/10">
                    <div class="flex gap-2">
                        <input type="text" id="chat-input" placeholder="Votre message..." class="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors">
                        <button onclick="Messaging.send()" class="p-2 bg-blue-600 text-white rounded-lg">
                            <i data-lucide="send" class="h-4 w-4"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        initLucide();
    },

    toggle() {
        const win = document.getElementById('chat-window');
        win.classList.toggle('hidden');
    },

    send() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        const msgContainer = document.getElementById('chat-messages');
        const msgHtml = `
            <div class="flex flex-col items-end">
                <div class="bg-blue-600 text-white px-3 py-2 rounded-2xl rounded-tr-none text-sm max-w-[80%] shadow-sm">
                    ${text}
                </div>
                <span class="text-[10px] text-slate-500 mt-1">À l'instant</span>
            </div>
        `;
        msgContainer.insertAdjacentHTML('beforeend', msgHtml);
        input.value = '';
        msgContainer.scrollTop = msgContainer.scrollHeight;
    },

    openChat(contactId) {
        const win = document.getElementById('chat-window');
        if (win.classList.contains('hidden')) {
            win.classList.remove('hidden');
        }
        alert(`Discussion cryptée ouverte avec ${contactId} !`);
    }
};

/**
 * API Wrapper pour la communication avec le backend Django
 */
const API = {
    baseUrl: window.__DJANGO_CONTEXT__?.apiBase || '/api/',
    csrfToken: window.__DJANGO_CONTEXT__?.csrfToken || '',

    async fetchDocs() {
        try {
            const res = await fetch(`${this.baseUrl}documents`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return data.data || data;
        } catch (err) {
            console.error("API Error (fetchDocs):", err);
            return [];
        }
    },

    async fetchCollaborators() {
        try {
            const res = await fetch(`${this.baseUrl}collaborators`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return data.data || data;
        } catch (err) {
            console.error("API Error (fetchCollaborators):", err);
            return [];
        }
    },

    async fetchDocVersions(docId) {
        try {
            const res = await fetch(`${this.baseUrl}documents/${docId}/versions`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return data.data || data;
        } catch (err) {
            console.error(`API Error (fetchDocVersions ${docId}):`, err);
            return [];
        }
    },

    async saveVersion(docId, data) {
        try {
            const res = await fetch(`${this.baseUrl}documents/${docId}/versions`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken
                },
                body: JSON.stringify(data),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error("API Error (saveVersion):", err);
            return { error: err.message };
        }
    },

    async rollbackVersion(docId, versionNumber, userData) {
        try {
            const res = await fetch(`${this.baseUrl}documents/${docId}/rollback`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken
                },
                body: JSON.stringify({
                    targetVersionNumber: versionNumber,
                    ...userData
                }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error("API Error (rollbackVersion):", err);
            return { error: err.message };
        }
    },

    async fetchExpertsList() {
        try {
            const res = await fetch(`${this.baseUrl}experts`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return data.data || data;
        } catch (err) {
            console.error("API Error (fetchExpertsList):", err);
            return [];
        }
    },

    async fetchWorkingGroups() {
        try {
            const res = await fetch(`${this.baseUrl}working-groups`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            return data.data || data;
        } catch (err) {
            console.error("API Error (fetchWorkingGroups):", err);
            return [];
        }
    }
};

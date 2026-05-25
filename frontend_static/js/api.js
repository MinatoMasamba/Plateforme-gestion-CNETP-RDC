/**
 * API Wrapper pour la communication avec le backend Django
 */
const API = {
    baseUrl: '', // Relatif au domaine serveur

    async fetchDocs() {
        try {
            const res = await fetch(`${this.baseUrl}/api/documents`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error("API Error (fetchDocs):", err);
            return [];
        }
    },

    async fetchCollaborators() {
        try {
            const res = await fetch(`${this.baseUrl}/api/collaborators`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error("API Error (fetchCollaborators):", err);
            return [];
        }
    },

    async fetchDocVersions(docId) {
        try {
            const res = await fetch(`${this.baseUrl}/api/documents/${docId}/versions`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error(`API Error (fetchDocVersions ${docId}):`, err);
            return [];
        }
    },

    async saveVersion(docId, data) {
        try {
            const res = await fetch(`${this.baseUrl}/api/documents/${docId}/versions`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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
            const res = await fetch(`${this.baseUrl}/api/documents/${docId}/rollback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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
            const res = await fetch(`${this.baseUrl}/api/experts`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error("API Error (fetchExpertsList):", err);
            return [];
        }
    },

    async fetchWorkingGroups() {
        try {
            const res = await fetch(`${this.baseUrl}/api/working-groups`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error("API Error (fetchWorkingGroups):", err);
            return [];
        }
    }
};

import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import { Document, DocumentVersion, Collaborator } from "./src/types";

// Initialize Gemini Client safely using the server-side environment key
const ai = process.env.GEMINI_API_KEY ? new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY }) : null;

const app = express();
const PORT = 3000;

app.use(express.json());

// In-memory Database of Documents
let documents: Document[] = [
  {
    id: "iso-9001",
    title: "Norme ISO 9001:2015 - Clause 4.1",
    code: "ISO-9001-4.1",
    category: "Qualité",
    description: "Compréhension de l'organisme et de son contexte pour l'amélioration continue.",
    content: "L'organisme doit déterminer les enjeux externes et internes pertinents par rapport à sa finalité et à son orientation stratégique, et qui influent sur sa capacité à s'assurer de l'atteinte des résultats attendus de son système de management de la qualité.\n\nL'organisme doit surveiller et passer en revue régulièrement les informations relatives à ces enjeux externes et internes afin de réagir par rapport aux aléas industriels.\n\nNote 1: Les enjeux stratégiques peuvent comprendre des conditions d'opportunité légales, technologiques, économiques ou concurrentielles.\nNote 2: La compréhension du contexte interne est facilitée par la surveillance des valeurs, de la culture d'entreprise et des indicateurs de performance.",
    updatedAt: "2026-05-19T21:45:00Z",
    updatedBy: "Marie Laurent",
    updatedByEmail: "marie.l@workspace.org",
    driveFolderUrl: "https://drive.google.com/drive/folders/cnetp_iso9001_v1",
    meetMeetingUrl: "https://meet.google.com/vax-vqqr-kxo",
    references: [
      { id: "ref-1", name: "Rapport d'audit de conformité préliminaire RDC.pdf", type: "Rapport Technique", description: "Audit des écarts par rapport aux standards africains ARSO.", url: "#", size: "1.4 MB" },
      { id: "ref-2", name: "Régulation ITP - Chapitre 4 - Matériaux.pdf", type: "Réglementation Connexe", description: "Cadre national de validation des matériaux locaux.", url: "#", size: "850 KB" }
    ]
  },
  {
    id: "iso-27001",
    title: "Norme ISO/IEC 27001:2022 - Clause 5.1",
    code: "ISO-27001-5.1",
    category: "Sécurité",
    description: "Soutien de la direction et leadership pour la sécurité de l'information (SMSI).",
    content: "La direction générale doit faire preuve de leadership et d'engagement par rapport au système de management de la sécurité de l'information en :\n- S'assurant que la politique et les objectifs de sécurité se coordonnent avec l'orientation stratégique de l'organisme ;\n- Intégrant les exigences du SMSI aux processus métiers opérationnels ;\n- Mettant à disposition les ressources nécessaires au fonctionnement ;\n- Communiquant sur l'importance de respecter les standards de sécurité de l'information.",
    updatedAt: "2026-05-19T18:30:00Z",
    updatedBy: "Arthur Dubois",
    updatedByEmail: "arthur.d@workspace.org",
    driveFolderUrl: "https://drive.google.com/drive/folders/cnetp_iso27001_smsi",
    meetMeetingUrl: "https://meet.google.com/fsk-tyue-vzw",
    references: [
      { id: "ref-3", name: "Directive cyber-sécurité pour les infrastructures critiques RDC.pdf", type: "Réglementation Connexe", description: "Exigences du Ministère du Numérique et ITP.", url: "#", size: "2.1 MB" }
    ]
  },
  {
    id: "charte-ia",
    title: "Charte Interne de Gouvernance de l'IA Générative",
    code: "GOUV-IA-2026",
    category: "Éthique",
    description: "Directives internes pour l'utilisation responsable et sécurisée des grands modèles de langage en entreprise.",
    content: "1. Transparence : Tout livrable destiné à nos clients ou partenaires ayant été consolidé ou rédigé avec l'assistance d'un agent de génération de texte doit impérativement comporter une mention légale de co-auteur synthétique.\n\n2. Confidentialité des données : Il est strictement prohibé d'injecter des données nominatives de clients (RGPD) ou des secrets de fabrication industriels dans des prompts de modèles externes non souverains.\n\n3. Responsabilité humaine : Un expert métier doit systématiquement relire de bout en bout et valider scientifiquement ou techniquement tout code ou document formalisé par l'IA avant son déploiement.",
    updatedAt: "2026-05-19T10:15:00Z",
    updatedBy: "Directeur de l'Innovation",
    updatedByEmail: "innovation@workspace.org",
    driveFolderUrl: "https://drive.google.com/drive/folders/cnetp_charte_ia",
    meetMeetingUrl: "https://meet.google.com/kws-ajsd-rra",
    references: []
  }
];

// In-memory Database of Versions
let versions: DocumentVersion[] = [
  // Version history for ISO-9001
  {
    id: "v1-iso",
    documentId: "iso-9001",
    versionNumber: 1,
    content: "L'organisme doit déterminer les enjeux pertinents par rapport à sa finalité et à son orientation stratégique qui influent sur sa capacité à atteindre le ou les résultats attendus de son SMQ.\n\nL'organisme doit surveiller les informations relatives à ces enjeux.\n\nNote 1: Les enjeux peuvent comprendre des facteurs positifs et négatifs.",
    author: "Jean Dupont",
    email: "jean.dupont@workspace.org",
    timestamp: "2026-05-17T09:00:00Z",
    comment: "Brouillon initial de la clause 4.1 d'après l'audit de certification.",
    isRollback: false
  },
  {
    id: "v2-iso",
    documentId: "iso-9001",
    versionNumber: 2,
    content: "L'organisme doit déterminer les enjeux externes et internes pertinents par rapport à sa finalité et à son orientation stratégique, et qui influent sur sa capacité à s'assurer de l'atteinte des résultats attendus de son système de management de la qualité.\n\nL'organisme doit surveiller et passer en revue régulièrement les informations relatives à ces enjeux externes et internes.\n\nNote 1: Les enjeux stratégiques peuvent comprendre des conditions d'opportunité légales, technologiques, économiques ou concurrentielles.",
    author: "Arthur Dubois",
    email: "arthur.d@workspace.org",
    timestamp: "2026-05-18T14:20:00Z",
    comment: "Ajout des notes de précision opérationnelle et différenciation des enjeux externes/internes.",
    isRollback: false
  },
  {
    id: "v3-iso",
    documentId: "iso-9001",
    versionNumber: 3,
    content: "L'organisme doit déterminer les enjeux externes et internes pertinents par rapport à sa finalité et à son orientation stratégique, et qui influent sur sa capacité à s'assurer de l'atteinte des résultats attendus de son système de management de la qualité.\n\nL'organisme doit surveiller et passer en revue régulièrement les informations relatives à ces enjeux externes et internes afin de réagir par rapport aux aléas industriels.\n\nNote 1: Les enjeux stratégiques peuvent comprendre des conditions d'opportunité légales, technologiques, économiques ou concurrentielles.\nNote 2: La compréhension du contexte interne est facilitée par la surveillance des valeurs, de la culture d'entreprise et des indicateurs de performance.",
    author: "Marie Laurent",
    email: "marie.l@workspace.org",
    timestamp: "2026-05-19T21:45:00Z",
    comment: "Ajout de la Note 2 sur le contexte interne et amélioration du suivi des risques industriels.",
    isRollback: false
  },

  // Version history for ISO-27001
  {
    id: "v1-27001",
    documentId: "iso-27001",
    versionNumber: 1,
    content: "La direction générale doit faire preuve de leadership par rapport au SMSI en s'assurant que la politique est définie et que les ressources nécessaires sont allouées.",
    author: "Arthur Dubois",
    email: "arthur.d@workspace.org",
    timestamp: "2026-05-18T10:00:00Z",
    comment: "Première ébauche abrégée pour la revue d'audit.",
    isRollback: false
  },
  {
    id: "v2-27001",
    documentId: "iso-27001",
    versionNumber: 2,
    content: "La direction générale doit faire preuve de leadership et d'engagement par rapport au système de management de la sécurité de l'information en :\n- S'assurant que la politique et les objectifs de sécurité se coordonnent avec l'orientation stratégique de l'organisme ;\n- Intégrant les exigences du SMSI aux processus métiers opérationnels ;\n- Mettant à disposition les ressources nécessaires au fonctionnement ;\n- Communiquant sur l'importance de respecter les standards de sécurité de l'information.",
    author: "Arthur Dubois",
    email: "arthur.d@workspace.org",
    timestamp: "2026-05-19T18:30:00Z",
    comment: "Mise en conformité complète avec la liste à puces règlementaire ISO27001 de l'ANSSI.",
    isRollback: false
  },

  // Version history for Charte IA
  {
    id: "v1-charte",
    documentId: "charte-ia",
    versionNumber: 1,
    content: "1. Transparence : Mentionnez si vous utilisez l'IA.\n2. RGPD : Ne pas mettre de données de clients sur l'IA.\n3. Relecture: Les humains doivent corriger les textes.",
    author: "Jean Dupont",
    email: "jean.dupont@workspace.org",
    timestamp: "2026-05-19T08:00:00Z",
    comment: "Premier jet informel rédigé rapidement en réunion.",
    isRollback: false
  },
  {
    id: "v2-charte",
    documentId: "charte-ia",
    versionNumber: 2,
    content: "1. Transparence : Tout livrable destiné à nos clients ou partenaires ayant été consolidé ou rédigé avec l'assistance d'un agent de génération de texte doit impérativement comporter une mention légale de co-auteur synthétique.\n\n2. Confidentialité des données : Il est strictement prohibé d'injecter des données nominatives de clients (RGPD) ou des secrets de fabrication industriels dans des prompts de modèles externes non souverains.\n\n3. Responsabilité humaine : Un expert métier doit systématiquement relire de bout en bout et valider scientifiquement ou techniquement tout code ou document formalisé par l'IA avant son déploiement.",
    author: "Directeur de l'Innovation",
    email: "innovation@workspace.org",
    timestamp: "2026-05-19T10:15:00Z",
    comment: "Formulation juridique et managériale de haut niveau avec mentions RGPD et responsabilité.",
    isRollback: false
  }
];

// Active mock list of workspace collaborators available
let collaborators: Collaborator[] = [
  { id: "col-1", name: "Jean Dupont", role: "Expert Qualité & Réglementaire", email: "jean.dupont@workspace.org", avatarColor: "#3b82f6", isActive: true },
  { id: "col-2", name: "Marie Laurent", role: "Responsable HSE & Audits", email: "marie.l@workspace.org", avatarColor: "#10b981", isActive: true },
  { id: "col-3", name: "Arthur Dubois", role: "RSSI / Directeur Sécurité", email: "arthur.d@workspace.org", avatarColor: "#f59e0b", isActive: false },
  { id: "col-4", name: "Chloé Bertrand", role: "Rédactrice Secrétariat Technique", email: "chloe.b@workspace.org", avatarColor: "#8b5cf6", isActive: true },
];

/* ---------------- API ROUTES ---------------- */

// Get list of documents
app.get("/api/documents", (req, res) => {
  res.json(documents);
});

// Get a specific document
app.get("/api/documents/:id", (req, res) => {
  const doc = documents.find(d => d.id === req.params.id);
  if (!doc) {
    return res.status(404).json({ error: "Document non trouvé" });
  }
  res.json(doc);
});

// Get version history for a specific document (newest first)
app.get("/api/documents/:id/versions", (req, res) => {
  const docsVersions = versions
    .filter(v => v.documentId === req.params.id)
    .sort((a, b) => b.versionNumber - a.versionNumber);
  res.json(docsVersions);
});

// Save a new version
app.post("/api/documents/:id/versions", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex(d => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouvé" });
  }

  const { content, author, email, comment } = req.body;
  
  if (content === undefined) {
    return res.status(400).json({ error: "Le contenu du document est obligatoire" });
  }

  // Get current version number for this document
  const docsVersions = versions.filter(v => v.documentId === docId);
  const nextVerNum = docsVersions.length > 0 
    ? Math.max(...docsVersions.map(v => v.versionNumber)) + 1 
    : 1;

  const newVersion: DocumentVersion = {
    id: `v${nextVerNum}-${docId}-${Date.now()}`,
    documentId: docId,
    versionNumber: nextVerNum,
    content,
    author: author || "Collaborateur Anonyme",
    email: email || "anonymous@workspace.org",
    timestamp: new Date().toISOString(),
    comment: comment || `Mise à jour v${nextVerNum}`,
    isRollback: false
  };

  // Append new version
  versions.push(newVersion);

  // Update current document state
  documents[docIndex].content = content;
  documents[docIndex].updatedAt = newVersion.timestamp;
  documents[docIndex].updatedBy = newVersion.author;
  documents[docIndex].updatedByEmail = newVersion.email;

  res.status(201).json({
    document: documents[docIndex],
    version: newVersion
  });
});

// Rollback/Revert to a previous version
app.post("/api/documents/:id/rollback", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex(d => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouvé" });
  }

  const { targetVersionNumber, author, email } = req.body;
  if (!targetVersionNumber) {
    return res.status(400).json({ error: "Le numéro de version cible est requis" });
  }

  // Find target version
  const targetVersion = versions.find(
    v => v.documentId === docId && v.versionNumber === Number(targetVersionNumber)
  );

  if (!targetVersion) {
    return res.status(404).json({ error: `La version v${targetVersionNumber} n'existe pas pour ce document` });
  }

  // To rollback cleanly, we create a NEW version in the database with the old content
  const docsVersions = versions.filter(v => v.documentId === docId);
  const nextVerNum = docsVersions.length > 0 
    ? Math.max(...docsVersions.map(v => v.versionNumber)) + 1 
    : 1;

  const rollbackVersion: DocumentVersion = {
    id: `v${nextVerNum}-${docId}-${Date.now()}`,
    documentId: docId,
    versionNumber: nextVerNum,
    content: targetVersion.content,
    author: author || "Gérant du Système",
    email: email || "admin@workspace.org",
    timestamp: new Date().toISOString(),
    comment: `Restauration de la version v${targetVersionNumber} de ${targetVersion.author}`,
    isRollback: true,
    restoredFromVersion: Number(targetVersionNumber)
  };

  // Add rollback to history
  versions.push(rollbackVersion);

  // Update original document to hold restored content
  documents[docIndex].content = targetVersion.content;
  documents[docIndex].updatedAt = rollbackVersion.timestamp;
  documents[docIndex].updatedBy = rollbackVersion.author;
  documents[docIndex].updatedByEmail = rollbackVersion.email;

  res.json({
    message: `Document restauré avec succès à la version v${targetVersionNumber}`,
    document: documents[docIndex],
    version: rollbackVersion
  });
});

// Add file reference upload
app.post("/api/documents/:id/references", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex(d => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouvé" });
  }

  const { name, type, description, size } = req.body;
  if (!name || !type) {
    return res.status(400).json({ error: "Le nom et le type de document ou référence sont requis." });
  }

  const newRef = {
    id: `ref-${Date.now()}`,
    name,
    type,
    description: description || "",
    size: size || "N/A",
    url: "#"
  };

  if (!documents[docIndex].references) {
    documents[docIndex].references = [];
  }
  documents[docIndex].references!.push(newRef);

  res.status(201).json(documents[docIndex]);
});

// Update Google Drive / Google Meet URLs
app.post("/api/documents/:id/drive-meet", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex(d => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouvé" });
  }

  const { driveFolderUrl, meetMeetingUrl } = req.body;
  if (driveFolderUrl !== undefined) {
    documents[docIndex].driveFolderUrl = driveFolderUrl;
  }
  if (meetMeetingUrl !== undefined) {
    documents[docIndex].meetMeetingUrl = meetMeetingUrl;
  }

  res.json(documents[docIndex]);
});

// Get workspace collaborators info
app.get("/api/collaborators", (req, res) => {
  res.json(collaborators);
});

// Gemini-powered revision feedback!
// Improves style, layout, suggests regulatory compliance phrasing.
app.post("/api/documents/:id/ai-review", async (req, res) => {
  const docId = req.params.id;
  const doc = documents.find(d => d.id === docId);
  if (!doc) {
    return res.status(404).json({ error: "Document non trouvé" });
  }

  const { content } = req.body;
  const textToAnalyze = content || doc.content;

  if (!ai) {
    // If Gemini key is not configured, fall back to an elegant rule-based mock revision
    // so that the app stays 100% operational and gives excellent suggestions even without a key on launch
    const reviewExplanation = "Analyse Réglementaire [Mode Démo - Clé API Absente] :\nLe système a analysé la clause. Suggestions de révision standard appliquée :\n- Amélioration du vocabulaire professionnel ('organisme' au lieu de 'société').\n- Rationalisation des paragraphes pour faciliter les audits.\n- Formatage harmonisé.";
    
    const suggestedText = textToAnalyze + "\n\n[Clause additionnelle de contrôle qualité : Les parties prenantes s'assurent que des indicateurs de conformité traçables (KPI) sont audités semestriellement afin d'en valider l'efficience opérationnelle.]";
    
    return res.json({
      suggestedText,
      explanation: reviewExplanation
    });
  }

  try {
    const prompt = `
    Tu es un conseiller expert en audit de conformité de standards et de normes réglementaires (ISO 9001, ISO 27001, etc.).
    Un collaborateur rédige un document intitulé "${doc.title}". Elle s'intègre dans la catégorie "${doc.category}".
    
    Voici le texte actuel écrit par le collaborateur :
    """
    ${textToAnalyze}
    """
    
    Ta tâche est de l'aider à l'améliorer. Suggère une version révisée, plus formelle, plus rigoureuse et conforme aux styles de rédaction des normes ISO.
    Ensuite, explique brièvement tes changements principaux en français.
    
    Renvoie ta réponse sous forme d'un objet JSON brut structuré de la manière suivante (assure-toi que la réponse soit EXCLUSIVEMENT un JSON valide, sans balise markdown):
    {
      "suggestedText": "Le texte entièrement réécrit de manière professionnelle et formelle...",
      "explanation": "Les explications courtes des améliorations rédigées ici..."
    }
    `;

    const response = await ai.models.generateContent({
      model: "gemini-3.5-flash",
      contents: prompt,
      config: {
        responseMimeType: "application/json"
      }
    });

    const outputText = response.text || "{}";
    try {
      const parsed = JSON.parse(outputText);
      res.json(parsed);
    } catch (parseErr) {
      // In case json decoding fails, split manually or return directly
      res.json({
        suggestedText: outputText,
        explanation: "Révision complétée avec succès par l'IA."
      });
    }
  } catch (err: any) {
    console.error("Gemini API error in background:", err);
    res.status(500).json({
      error: "Erreur lors de la génération par l'IA de conseil.",
      details: err.message
    });
  }
});


/* ----------- VITE / STATIC FILES MIDDLEWARE ----------- */

async function start() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Espace Normes Collaboratif backend running on http://localhost:${PORT}`);
  });
}

start();

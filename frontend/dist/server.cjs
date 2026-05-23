var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// server.ts
var import_express = __toESM(require("express"), 1);
var import_path = __toESM(require("path"), 1);
var import_vite = require("vite");
var import_genai = require("@google/genai");
var ai = process.env.GEMINI_API_KEY ? new import_genai.GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY }) : null;
var app = (0, import_express.default)();
var PORT = 3e3;
app.use(import_express.default.json());
var documents = [
  {
    id: "iso-9001",
    title: "Norme ISO 9001:2015 - Clause 4.1",
    code: "ISO-9001-4.1",
    category: "Qualit\xE9",
    description: "Compr\xE9hension de l'organisme et de son contexte pour l'am\xE9lioration continue.",
    content: "L'organisme doit d\xE9terminer les enjeux externes et internes pertinents par rapport \xE0 sa finalit\xE9 et \xE0 son orientation strat\xE9gique, et qui influent sur sa capacit\xE9 \xE0 s'assurer de l'atteinte des r\xE9sultats attendus de son syst\xE8me de management de la qualit\xE9.\n\nL'organisme doit surveiller et passer en revue r\xE9guli\xE8rement les informations relatives \xE0 ces enjeux externes et internes afin de r\xE9agir par rapport aux al\xE9as industriels.\n\nNote 1: Les enjeux strat\xE9giques peuvent comprendre des conditions d'opportunit\xE9 l\xE9gales, technologiques, \xE9conomiques ou concurrentielles.\nNote 2: La compr\xE9hension du contexte interne est facilit\xE9e par la surveillance des valeurs, de la culture d'entreprise et des indicateurs de performance.",
    updatedAt: "2026-05-19T21:45:00Z",
    updatedBy: "Marie Laurent",
    updatedByEmail: "marie.l@workspace.org",
    driveFolderUrl: "https://drive.google.com/drive/folders/cnetp_iso9001_v1",
    meetMeetingUrl: "https://meet.google.com/vax-vqqr-kxo",
    references: [
      { id: "ref-1", name: "Rapport d'audit de conformit\xE9 pr\xE9liminaire RDC.pdf", type: "Rapport Technique", description: "Audit des \xE9carts par rapport aux standards africains ARSO.", url: "#", size: "1.4 MB" },
      { id: "ref-2", name: "R\xE9gulation ITP - Chapitre 4 - Mat\xE9riaux.pdf", type: "R\xE9glementation Connexe", description: "Cadre national de validation des mat\xE9riaux locaux.", url: "#", size: "850 KB" }
    ]
  },
  {
    id: "iso-27001",
    title: "Norme ISO/IEC 27001:2022 - Clause 5.1",
    code: "ISO-27001-5.1",
    category: "S\xE9curit\xE9",
    description: "Soutien de la direction et leadership pour la s\xE9curit\xE9 de l'information (SMSI).",
    content: "La direction g\xE9n\xE9rale doit faire preuve de leadership et d'engagement par rapport au syst\xE8me de management de la s\xE9curit\xE9 de l'information en :\n- S'assurant que la politique et les objectifs de s\xE9curit\xE9 se coordonnent avec l'orientation strat\xE9gique de l'organisme ;\n- Int\xE9grant les exigences du SMSI aux processus m\xE9tiers op\xE9rationnels ;\n- Mettant \xE0 disposition les ressources n\xE9cessaires au fonctionnement ;\n- Communiquant sur l'importance de respecter les standards de s\xE9curit\xE9 de l'information.",
    updatedAt: "2026-05-19T18:30:00Z",
    updatedBy: "Arthur Dubois",
    updatedByEmail: "arthur.d@workspace.org",
    driveFolderUrl: "https://drive.google.com/drive/folders/cnetp_iso27001_smsi",
    meetMeetingUrl: "https://meet.google.com/fsk-tyue-vzw",
    references: [
      { id: "ref-3", name: "Directive cyber-s\xE9curit\xE9 pour les infrastructures critiques RDC.pdf", type: "R\xE9glementation Connexe", description: "Exigences du Minist\xE8re du Num\xE9rique et ITP.", url: "#", size: "2.1 MB" }
    ]
  },
  {
    id: "charte-ia",
    title: "Charte Interne de Gouvernance de l'IA G\xE9n\xE9rative",
    code: "GOUV-IA-2026",
    category: "\xC9thique",
    description: "Directives internes pour l'utilisation responsable et s\xE9curis\xE9e des grands mod\xE8les de langage en entreprise.",
    content: "1. Transparence : Tout livrable destin\xE9 \xE0 nos clients ou partenaires ayant \xE9t\xE9 consolid\xE9 ou r\xE9dig\xE9 avec l'assistance d'un agent de g\xE9n\xE9ration de texte doit imp\xE9rativement comporter une mention l\xE9gale de co-auteur synth\xE9tique.\n\n2. Confidentialit\xE9 des donn\xE9es : Il est strictement prohib\xE9 d'injecter des donn\xE9es nominatives de clients (RGPD) ou des secrets de fabrication industriels dans des prompts de mod\xE8les externes non souverains.\n\n3. Responsabilit\xE9 humaine : Un expert m\xE9tier doit syst\xE9matiquement relire de bout en bout et valider scientifiquement ou techniquement tout code ou document formalis\xE9 par l'IA avant son d\xE9ploiement.",
    updatedAt: "2026-05-19T10:15:00Z",
    updatedBy: "Directeur de l'Innovation",
    updatedByEmail: "innovation@workspace.org",
    driveFolderUrl: "https://drive.google.com/drive/folders/cnetp_charte_ia",
    meetMeetingUrl: "https://meet.google.com/kws-ajsd-rra",
    references: []
  }
];
var versions = [
  // Version history for ISO-9001
  {
    id: "v1-iso",
    documentId: "iso-9001",
    versionNumber: 1,
    content: "L'organisme doit d\xE9terminer les enjeux pertinents par rapport \xE0 sa finalit\xE9 et \xE0 son orientation strat\xE9gique qui influent sur sa capacit\xE9 \xE0 atteindre le ou les r\xE9sultats attendus de son SMQ.\n\nL'organisme doit surveiller les informations relatives \xE0 ces enjeux.\n\nNote 1: Les enjeux peuvent comprendre des facteurs positifs et n\xE9gatifs.",
    author: "Jean Dupont",
    email: "jean.dupont@workspace.org",
    timestamp: "2026-05-17T09:00:00Z",
    comment: "Brouillon initial de la clause 4.1 d'apr\xE8s l'audit de certification.",
    isRollback: false
  },
  {
    id: "v2-iso",
    documentId: "iso-9001",
    versionNumber: 2,
    content: "L'organisme doit d\xE9terminer les enjeux externes et internes pertinents par rapport \xE0 sa finalit\xE9 et \xE0 son orientation strat\xE9gique, et qui influent sur sa capacit\xE9 \xE0 s'assurer de l'atteinte des r\xE9sultats attendus de son syst\xE8me de management de la qualit\xE9.\n\nL'organisme doit surveiller et passer en revue r\xE9guli\xE8rement les informations relatives \xE0 ces enjeux externes et internes.\n\nNote 1: Les enjeux strat\xE9giques peuvent comprendre des conditions d'opportunit\xE9 l\xE9gales, technologiques, \xE9conomiques ou concurrentielles.",
    author: "Arthur Dubois",
    email: "arthur.d@workspace.org",
    timestamp: "2026-05-18T14:20:00Z",
    comment: "Ajout des notes de pr\xE9cision op\xE9rationnelle et diff\xE9renciation des enjeux externes/internes.",
    isRollback: false
  },
  {
    id: "v3-iso",
    documentId: "iso-9001",
    versionNumber: 3,
    content: "L'organisme doit d\xE9terminer les enjeux externes et internes pertinents par rapport \xE0 sa finalit\xE9 et \xE0 son orientation strat\xE9gique, et qui influent sur sa capacit\xE9 \xE0 s'assurer de l'atteinte des r\xE9sultats attendus de son syst\xE8me de management de la qualit\xE9.\n\nL'organisme doit surveiller et passer en revue r\xE9guli\xE8rement les informations relatives \xE0 ces enjeux externes et internes afin de r\xE9agir par rapport aux al\xE9as industriels.\n\nNote 1: Les enjeux strat\xE9giques peuvent comprendre des conditions d'opportunit\xE9 l\xE9gales, technologiques, \xE9conomiques ou concurrentielles.\nNote 2: La compr\xE9hension du contexte interne est facilit\xE9e par la surveillance des valeurs, de la culture d'entreprise et des indicateurs de performance.",
    author: "Marie Laurent",
    email: "marie.l@workspace.org",
    timestamp: "2026-05-19T21:45:00Z",
    comment: "Ajout de la Note 2 sur le contexte interne et am\xE9lioration du suivi des risques industriels.",
    isRollback: false
  },
  // Version history for ISO-27001
  {
    id: "v1-27001",
    documentId: "iso-27001",
    versionNumber: 1,
    content: "La direction g\xE9n\xE9rale doit faire preuve de leadership par rapport au SMSI en s'assurant que la politique est d\xE9finie et que les ressources n\xE9cessaires sont allou\xE9es.",
    author: "Arthur Dubois",
    email: "arthur.d@workspace.org",
    timestamp: "2026-05-18T10:00:00Z",
    comment: "Premi\xE8re \xE9bauche abr\xE9g\xE9e pour la revue d'audit.",
    isRollback: false
  },
  {
    id: "v2-27001",
    documentId: "iso-27001",
    versionNumber: 2,
    content: "La direction g\xE9n\xE9rale doit faire preuve de leadership et d'engagement par rapport au syst\xE8me de management de la s\xE9curit\xE9 de l'information en :\n- S'assurant que la politique et les objectifs de s\xE9curit\xE9 se coordonnent avec l'orientation strat\xE9gique de l'organisme ;\n- Int\xE9grant les exigences du SMSI aux processus m\xE9tiers op\xE9rationnels ;\n- Mettant \xE0 disposition les ressources n\xE9cessaires au fonctionnement ;\n- Communiquant sur l'importance de respecter les standards de s\xE9curit\xE9 de l'information.",
    author: "Arthur Dubois",
    email: "arthur.d@workspace.org",
    timestamp: "2026-05-19T18:30:00Z",
    comment: "Mise en conformit\xE9 compl\xE8te avec la liste \xE0 puces r\xE8glementaire ISO27001 de l'ANSSI.",
    isRollback: false
  },
  // Version history for Charte IA
  {
    id: "v1-charte",
    documentId: "charte-ia",
    versionNumber: 1,
    content: "1. Transparence : Mentionnez si vous utilisez l'IA.\n2. RGPD : Ne pas mettre de donn\xE9es de clients sur l'IA.\n3. Relecture: Les humains doivent corriger les textes.",
    author: "Jean Dupont",
    email: "jean.dupont@workspace.org",
    timestamp: "2026-05-19T08:00:00Z",
    comment: "Premier jet informel r\xE9dig\xE9 rapidement en r\xE9union.",
    isRollback: false
  },
  {
    id: "v2-charte",
    documentId: "charte-ia",
    versionNumber: 2,
    content: "1. Transparence : Tout livrable destin\xE9 \xE0 nos clients ou partenaires ayant \xE9t\xE9 consolid\xE9 ou r\xE9dig\xE9 avec l'assistance d'un agent de g\xE9n\xE9ration de texte doit imp\xE9rativement comporter une mention l\xE9gale de co-auteur synth\xE9tique.\n\n2. Confidentialit\xE9 des donn\xE9es : Il est strictement prohib\xE9 d'injecter des donn\xE9es nominatives de clients (RGPD) ou des secrets de fabrication industriels dans des prompts de mod\xE8les externes non souverains.\n\n3. Responsabilit\xE9 humaine : Un expert m\xE9tier doit syst\xE9matiquement relire de bout en bout et valider scientifiquement ou techniquement tout code ou document formalis\xE9 par l'IA avant son d\xE9ploiement.",
    author: "Directeur de l'Innovation",
    email: "innovation@workspace.org",
    timestamp: "2026-05-19T10:15:00Z",
    comment: "Formulation juridique et manag\xE9riale de haut niveau avec mentions RGPD et responsabilit\xE9.",
    isRollback: false
  }
];
var collaborators = [
  { id: "col-1", name: "Jean Dupont", role: "Expert Qualit\xE9 & R\xE9glementaire", email: "jean.dupont@workspace.org", avatarColor: "#3b82f6", isActive: true },
  { id: "col-2", name: "Marie Laurent", role: "Responsable HSE & Audits", email: "marie.l@workspace.org", avatarColor: "#10b981", isActive: true },
  { id: "col-3", name: "Arthur Dubois", role: "RSSI / Directeur S\xE9curit\xE9", email: "arthur.d@workspace.org", avatarColor: "#f59e0b", isActive: false },
  { id: "col-4", name: "Chlo\xE9 Bertrand", role: "R\xE9dactrice Secr\xE9tariat Technique", email: "chloe.b@workspace.org", avatarColor: "#8b5cf6", isActive: true }
];
app.get("/api/documents", (req, res) => {
  res.json(documents);
});
app.get("/api/documents/:id", (req, res) => {
  const doc = documents.find((d) => d.id === req.params.id);
  if (!doc) {
    return res.status(404).json({ error: "Document non trouv\xE9" });
  }
  res.json(doc);
});
app.get("/api/documents/:id/versions", (req, res) => {
  const docsVersions = versions.filter((v) => v.documentId === req.params.id).sort((a, b) => b.versionNumber - a.versionNumber);
  res.json(docsVersions);
});
app.post("/api/documents/:id/versions", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex((d) => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouv\xE9" });
  }
  const { content, author, email, comment } = req.body;
  if (content === void 0) {
    return res.status(400).json({ error: "Le contenu du document est obligatoire" });
  }
  const docsVersions = versions.filter((v) => v.documentId === docId);
  const nextVerNum = docsVersions.length > 0 ? Math.max(...docsVersions.map((v) => v.versionNumber)) + 1 : 1;
  const newVersion = {
    id: `v${nextVerNum}-${docId}-${Date.now()}`,
    documentId: docId,
    versionNumber: nextVerNum,
    content,
    author: author || "Collaborateur Anonyme",
    email: email || "anonymous@workspace.org",
    timestamp: (/* @__PURE__ */ new Date()).toISOString(),
    comment: comment || `Mise \xE0 jour v${nextVerNum}`,
    isRollback: false
  };
  versions.push(newVersion);
  documents[docIndex].content = content;
  documents[docIndex].updatedAt = newVersion.timestamp;
  documents[docIndex].updatedBy = newVersion.author;
  documents[docIndex].updatedByEmail = newVersion.email;
  res.status(201).json({
    document: documents[docIndex],
    version: newVersion
  });
});
app.post("/api/documents/:id/rollback", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex((d) => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouv\xE9" });
  }
  const { targetVersionNumber, author, email } = req.body;
  if (!targetVersionNumber) {
    return res.status(400).json({ error: "Le num\xE9ro de version cible est requis" });
  }
  const targetVersion = versions.find(
    (v) => v.documentId === docId && v.versionNumber === Number(targetVersionNumber)
  );
  if (!targetVersion) {
    return res.status(404).json({ error: `La version v${targetVersionNumber} n'existe pas pour ce document` });
  }
  const docsVersions = versions.filter((v) => v.documentId === docId);
  const nextVerNum = docsVersions.length > 0 ? Math.max(...docsVersions.map((v) => v.versionNumber)) + 1 : 1;
  const rollbackVersion = {
    id: `v${nextVerNum}-${docId}-${Date.now()}`,
    documentId: docId,
    versionNumber: nextVerNum,
    content: targetVersion.content,
    author: author || "G\xE9rant du Syst\xE8me",
    email: email || "admin@workspace.org",
    timestamp: (/* @__PURE__ */ new Date()).toISOString(),
    comment: `Restauration de la version v${targetVersionNumber} de ${targetVersion.author}`,
    isRollback: true,
    restoredFromVersion: Number(targetVersionNumber)
  };
  versions.push(rollbackVersion);
  documents[docIndex].content = targetVersion.content;
  documents[docIndex].updatedAt = rollbackVersion.timestamp;
  documents[docIndex].updatedBy = rollbackVersion.author;
  documents[docIndex].updatedByEmail = rollbackVersion.email;
  res.json({
    message: `Document restaur\xE9 avec succ\xE8s \xE0 la version v${targetVersionNumber}`,
    document: documents[docIndex],
    version: rollbackVersion
  });
});
app.post("/api/documents/:id/references", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex((d) => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouv\xE9" });
  }
  const { name, type, description, size } = req.body;
  if (!name || !type) {
    return res.status(400).json({ error: "Le nom et le type de document ou r\xE9f\xE9rence sont requis." });
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
  documents[docIndex].references.push(newRef);
  res.status(201).json(documents[docIndex]);
});
app.post("/api/documents/:id/drive-meet", (req, res) => {
  const docId = req.params.id;
  const docIndex = documents.findIndex((d) => d.id === docId);
  if (docIndex === -1) {
    return res.status(404).json({ error: "Document non trouv\xE9" });
  }
  const { driveFolderUrl, meetMeetingUrl } = req.body;
  if (driveFolderUrl !== void 0) {
    documents[docIndex].driveFolderUrl = driveFolderUrl;
  }
  if (meetMeetingUrl !== void 0) {
    documents[docIndex].meetMeetingUrl = meetMeetingUrl;
  }
  res.json(documents[docIndex]);
});
app.get("/api/collaborators", (req, res) => {
  res.json(collaborators);
});
app.post("/api/documents/:id/ai-review", async (req, res) => {
  const docId = req.params.id;
  const doc = documents.find((d) => d.id === docId);
  if (!doc) {
    return res.status(404).json({ error: "Document non trouv\xE9" });
  }
  const { content } = req.body;
  const textToAnalyze = content || doc.content;
  if (!ai) {
    const reviewExplanation = "Analyse R\xE9glementaire [Mode D\xE9mo - Cl\xE9 API Absente] :\nLe syst\xE8me a analys\xE9 la clause. Suggestions de r\xE9vision standard appliqu\xE9e :\n- Am\xE9lioration du vocabulaire professionnel ('organisme' au lieu de 'soci\xE9t\xE9').\n- Rationalisation des paragraphes pour faciliter les audits.\n- Formatage harmonis\xE9.";
    const suggestedText = textToAnalyze + "\n\n[Clause additionnelle de contr\xF4le qualit\xE9 : Les parties prenantes s'assurent que des indicateurs de conformit\xE9 tra\xE7ables (KPI) sont audit\xE9s semestriellement afin d'en valider l'efficience op\xE9rationnelle.]";
    return res.json({
      suggestedText,
      explanation: reviewExplanation
    });
  }
  try {
    const prompt = `
    Tu es un conseiller expert en audit de conformit\xE9 de standards et de normes r\xE9glementaires (ISO 9001, ISO 27001, etc.).
    Un collaborateur r\xE9dige un document intitul\xE9 "${doc.title}". Elle s'int\xE8gre dans la cat\xE9gorie "${doc.category}".
    
    Voici le texte actuel \xE9crit par le collaborateur :
    """
    ${textToAnalyze}
    """
    
    Ta t\xE2che est de l'aider \xE0 l'am\xE9liorer. Sugg\xE8re une version r\xE9vis\xE9e, plus formelle, plus rigoureuse et conforme aux styles de r\xE9daction des normes ISO.
    Ensuite, explique bri\xE8vement tes changements principaux en fran\xE7ais.
    
    Renvoie ta r\xE9ponse sous forme d'un objet JSON brut structur\xE9 de la mani\xE8re suivante (assure-toi que la r\xE9ponse soit EXCLUSIVEMENT un JSON valide, sans balise markdown):
    {
      "suggestedText": "Le texte enti\xE8rement r\xE9\xE9crit de mani\xE8re professionnelle et formelle...",
      "explanation": "Les explications courtes des am\xE9liorations r\xE9dig\xE9es ici..."
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
      res.json({
        suggestedText: outputText,
        explanation: "R\xE9vision compl\xE9t\xE9e avec succ\xE8s par l'IA."
      });
    }
  } catch (err) {
    console.error("Gemini API error in background:", err);
    res.status(500).json({
      error: "Erreur lors de la g\xE9n\xE9ration par l'IA de conseil.",
      details: err.message
    });
  }
});
async function start() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await (0, import_vite.createServer)({
      server: { middlewareMode: true },
      appType: "spa"
    });
    app.use(vite.middlewares);
  } else {
    const distPath = import_path.default.join(process.cwd(), "dist");
    app.use(import_express.default.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(import_path.default.join(distPath, "index.html"));
    });
  }
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Espace Normes Collaboratif backend running on http://localhost:${PORT}`);
  });
}
start();
//# sourceMappingURL=server.cjs.map

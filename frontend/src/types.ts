export interface Document {
  id: string;
  title: string;
  code: string;
  description: string;
  content: string;
  category: string;
  updatedAt: string;
  updatedBy: string;
  updatedByEmail: string;
  driveFolderUrl?: string;
  meetMeetingUrl?: string;
  references?: { id: string; name: string; type: string; url?: string; description?: string; size?: string }[];
}

export interface DocumentVersion {
  id: string;
  documentId: string;
  versionNumber: number;
  content: string;
  author: string;
  email: string;
  timestamp: string;
  comment: string;
  isRollback: boolean;
  restoredFromVersion?: number;
}

export interface Collaborator {
  id: string;
  name: string;
  role: string;
  email: string;
  avatarColor: string;
  isActive: boolean;
}

export interface DiffPart {
  value: string;
  added?: boolean;
  removed?: boolean;
}

export interface DiffResponse {
  v1: number;
  v2: number;
  diffs: DiffPart[];
}

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

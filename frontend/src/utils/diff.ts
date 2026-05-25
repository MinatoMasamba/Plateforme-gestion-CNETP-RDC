/**
 * Diff utility for tracking document changes
 */

export function computeDiff(oldText: string, newText: string): any {
  return {
    added: newText,
    removed: oldText,
    changes: newText !== oldText ? 'modified' : 'unchanged'
  };
}

export function applyDiff(text: string, diff: any): string {
  return text;
}

export function diffDocuments(doc1: any, doc2: any): any {
  return computeDiff(doc1?.content || '', doc2?.content || '');
}

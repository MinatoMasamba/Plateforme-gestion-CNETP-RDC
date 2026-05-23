import { DiffPart } from "../types";

/**
 * Performs a word-by-word diff between two text strings.
 * Returns parts of the text marked as added, removed, or unchanged.
 */
export function diffWords(oldStr: string, newStr: string): DiffPart[] {
  if (!oldStr) return [{ value: newStr, added: true }];
  if (!newStr) return [{ value: oldStr, removed: true }];

  // Split into words and spaces/punctuation to keep text formatting identical.
  const oldWords = oldStr.split(/(\s+)/);
  const newWords = newStr.split(/(\s+)/);

  const m = oldWords.length;
  const n = newWords.length;

  // Space-efficient or simple dynamic programming grid
  const dp: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldWords[i - 1] === newWords[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  const result: DiffPart[] = [];
  let i = m;
  let j = n;

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldWords[i - 1] === newWords[j - 1]) {
      result.unshift({ value: oldWords[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.unshift({ value: newWords[j - 1], added: true });
      j--;
    } else {
      result.unshift({ value: oldWords[i - 1], removed: true });
      i--;
    }
  }

  // Optimize and merge consecutive diff fragments of the same type for better DOM rendering
  const merged: DiffPart[] = [];
  for (const part of result) {
    if (!part.value) continue;
    const last = merged[merged.length - 1];
    if (
      last &&
      ((last.added && part.added) ||
        (last.removed && part.removed) ||
        (!last.added && !last.removed && !part.added && !part.removed))
    ) {
      last.value += part.value;
    } else {
      merged.push({ ...part });
    }
  }

  return merged;
}

export interface ParagraphDiff {
  id: string;
  type: "unchanged" | "added" | "removed" | "modified";
  oldText?: string;
  newText?: string;
  wordDiff?: DiffPart[]; // Set only if type === "modified"
}

/**
 * Align two documents line-by-line / paragraph-by-paragraph.
 * If a paragraph is deleted and then another added, they are paired as "modified"
 * and we perform a deep word-level diff inside that paragraph block to highlight specific edits.
 */
export function diffDocuments(oldText: string, newText: string): ParagraphDiff[] {
  // Normalize line endings and split by lines to analyze paragraphs / bullet structures
  const oldParas = oldText.split(/\r?\n/);
  const newParas = newText.split(/\r?\n/);

  const m = oldParas.length;
  const n = newParas.length;

  const dp: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldParas[i - 1] === newParas[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Trace back steps
  const steps: { type: "match" | "delete" | "add"; oldIdx: number; newIdx: number }[] = [];
  let i = m;
  let j = n;

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldParas[i - 1] === newParas[j - 1]) {
      steps.unshift({ type: "match", oldIdx: i - 1, newIdx: j - 1 });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      steps.unshift({ type: "add", oldIdx: -1, newIdx: j - 1 });
      j--;
    } else {
      steps.unshift({ type: "delete", oldIdx: i - 1, newIdx: -1 });
      i--;
    }
  }

  const paragraphs: ParagraphDiff[] = [];
  let stepIdx = 0;

  while (stepIdx < steps.length) {
    const step = steps[stepIdx];

    if (step.type === "match") {
      paragraphs.push({
        id: `p-match-${step.oldIdx}-${step.newIdx}`,
        type: "unchanged",
        oldText: oldParas[step.oldIdx],
        newText: newParas[step.newIdx],
      });
      stepIdx++;
    } else if (step.type === "delete") {
      // Check if subsequent step is an addition, so we can pair them as a modified paragraph
      const nextStep = steps[stepIdx + 1];
      if (nextStep && nextStep.type === "add") {
        const oText = oldParas[step.oldIdx];
        const nText = newParas[nextStep.newIdx];
        paragraphs.push({
          id: `p-mod-${step.oldIdx}-${nextStep.newIdx}`,
          type: "modified",
          oldText: oText,
          newText: nText,
          wordDiff: diffWords(oText, nText),
        });
        stepIdx += 2; // Jump both steps
      } else {
        paragraphs.push({
          id: `p-del-${step.oldIdx}`,
          type: "removed",
          oldText: oldParas[step.oldIdx],
        });
        stepIdx++;
      }
    } else {
      paragraphs.push({
        id: `p-add-${step.newIdx}`,
        type: "added",
        newText: newParas[step.newIdx],
      });
      stepIdx++;
    }
  }

  return paragraphs;
}

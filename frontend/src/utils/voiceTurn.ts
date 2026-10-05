// Only reject a near-verbatim question. Short answers and shared keywords are valid.
export function isAssistantEcho(answer: string, question: string): boolean {
  const tokens = (text: string) => text.toLocaleLowerCase().match(/[\p{L}\p{N}\p{M}]+/gu) || [];
  const spoken = tokens(answer);
  const prompt = tokens(question);
  if (spoken.length < 4 || prompt.length < 4) return false;
  const remaining = [...prompt];
  let matches = 0;
  for (const word of spoken) {
    const index = remaining.indexOf(word);
    if (index >= 0) { matches++; remaining.splice(index, 1); }
  }
  return matches / spoken.length >= 0.85 && matches / prompt.length >= 0.7;
}

export function stripAssistantEcho(answer: string, question: string): string {
  const words = [...answer.matchAll(/[\p{L}\p{N}\p{M}]+/gu)];
  const prompt = question.toLocaleLowerCase().match(/[\p{L}\p{N}\p{M}]+/gu) || [];
  let start = 0;
  let end = words.length;
  // Strip a captured question at either edge while preserving the user's answer.
  for (let count = Math.min(words.length, prompt.length); count >= 4; count--) {
    for (let offset = 0; offset <= prompt.length - count; offset++) {
      const fragment = prompt.slice(offset, offset + count).join(' ');
      if (words.slice(0, count).map(word => word[0].toLocaleLowerCase()).join(' ') === fragment) start = Math.max(start, count);
      if (words.slice(-count).map(word => word[0].toLocaleLowerCase()).join(' ') === fragment) end = Math.min(end, words.length - count);
    }
  }
  if (start >= end) return '';
  if (start === 0 && end === words.length) return isAssistantEcho(answer, question) ? '' : answer.trim();
  return answer.slice(words[start].index!, words[end - 1].index! + words[end - 1][0].length).trim();
}

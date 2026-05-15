export function highlightMentions(text) {
  if (!text) return "";

  return text.replace(
    /@([\p{L}\p{N}_\s.-]+)/gu,
    '<span class="font-black text-blue-600">@$1</span>',
  );
}

export function extractMentionedUserIdsFromText(text, selectedIds = [], members = []) {
  const lowerText = String(text || "").toLowerCase();
  const ids = new Set((selectedIds || []).map(Number));

  members.forEach((member) => {
    if (!member?.id || !member?.full_name) return;

    const nameMention = `@${member.full_name}`.toLowerCase();

    if (lowerText.includes(nameMention)) {
      ids.add(Number(member.id));
    }
  });

  return Array.from(ids).filter((id) => Number.isFinite(id) && id > 0);
}

export function normalizeMember(member) {
  if (!member) return null;

  if (member.user) {
    return {
      id: member.user.id,
      full_name: member.user.full_name || member.user.email || "User",
      email: member.user.email || "",
      avatar_url: member.user.avatar_url || "",
      role: member.role || "",
    };
  }

  return {
    id: member.id || member.user_id,
    full_name: member.full_name || member.email || "User",
    email: member.email || "",
    avatar_url: member.avatar_url || "",
    role: member.role || "",
  };
}

export function getInitials(name) {
  if (!name) return "?";

  const words = name.trim().split(/\s+/);

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase();
}

export function getAvatarColorClass(index = 0) {
  const colors = [
    "bg-blue-600",
    "bg-violet-600",
    "bg-emerald-600",
    "bg-amber-500",
    "bg-rose-600",
    "bg-cyan-600",
    "bg-indigo-600",
    "bg-fuchsia-600",
    "bg-slate-700",
  ];

  return colors[Math.abs(Number(index) || 0) % colors.length];
}

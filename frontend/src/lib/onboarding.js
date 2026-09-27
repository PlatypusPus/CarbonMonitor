const key = (userId) => `carbontrace:onboarding:${userId}`;

export function getOnboarding(userId) {
  if (!userId) return null;
  try {
    return JSON.parse(localStorage.getItem(key(userId)) || "null");
  } catch {
    return null;
  }
}

export const saveOnboarding = (userId, preferences) =>
  localStorage.setItem(key(userId), JSON.stringify(preferences));

const BASE_URL = "/api/games";

async function request(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${res.status}`);
  }
  return res.json();
}

export function createGame(vsAi) {
  return request(BASE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vs_ai: vsAi }),
  });
}

export function fetchGame(gameId) {
  return request(`${BASE_URL}/${gameId}`);
}

export function playMove(gameId, position) {
  return request(`${BASE_URL}/${gameId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ position }),
  });
}

export function resetGame(gameId, vsAi) {
  return request(`${BASE_URL}/${gameId}/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vs_ai: vsAi }),
  });
}

const JSON_HEADERS = { "Content-Type": "application/json" };

async function asJson(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `Request failed with status ${response.status}`);
  }
  return body;
}

export function createSongJob(query) {
  return fetch("/api/songs", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ query }),
  }).then(asJson);
}

export function getSongJob(jobId) {
  return fetch(`/api/songs/${jobId}`).then(asJson);
}

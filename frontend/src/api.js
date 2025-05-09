// ✅ frontend/src/api.js

const BASE = 'http://localhost:5000'; // 本機 Flask API base URL

export async function getPublicKey(userId) {
  const res = await fetch(`${BASE}/publicKey/${userId}`);
  const data = await res.json();
  return data.publicKey;
}

export async function uploadEncryptedFile(blob, encryptedSessionKey, filename) {
  const form = new FormData();
  form.append('file', blob, filename);
  form.append('encryptedKey', bufToHex(new Uint8Array(encryptedSessionKey)))

  const res = await fetch(`${BASE}/uploadFile`, {
    method: 'POST',
    body: form
  });
  return await res.json();
}

export async function downloadEncryptedFile(fileId) {
  const res = await fetch(`${BASE}/downloadFile/${fileId}`);
  const encryptedKey = res.headers.get('X-Encrypted-Key');
  const blob = await res.blob();
  return { fileBlob: blob, encryptedKeyHex: encryptedKey };
}

export async function unwrapSessionKey(encryptedKeyHex, token) {
  const res = await fetch(`${BASE}/unwrapKey`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ encryptedSessionKey: encryptedKeyHex })
  });
  const data = await res.json();
  return data.sessionKey;
}

function bufToHex(buffer) {
  return [...buffer].map(x => x.toString(16).padStart(2, '0')).join('')
}

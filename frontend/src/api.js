const BASE = 'http://localhost:5000';
const KMS = 'http://localhost:7000';

export async function getPublicKey(userId) {
  const res = await fetch(`${BASE}/publicKey/${userId}`);
  const data = await res.json();
  return data.publicKey;
}

function bufferToHex(buffer) {
  return [...new Uint8Array(buffer)].map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function uploadEncryptedFile(blob, encryptedSessionKey, filename) {
  const form = new FormData();
  form.append('file', blob, filename);
  form.append('encryptedKey', bufferToHex(encryptedSessionKey));

  const res = await fetch(`http://localhost:5000/uploadFile`, {
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

export async function getPrivateKeyFromKMS(token) {
  const res = await fetch(`${KMS}/kms/privateKey`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await res.json();
  return data.privateKey;
}

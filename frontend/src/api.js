const BASE = 'http://localhost:5000';

export async function getPublicKey(userId) {
  const res = await fetch(`${BASE}/publicKey/${userId}`);
  const data = await res.json();
  return data.publicKey;
}

export async function getPrivateKeyFromKMS(token) {
  const res = await fetch(`http://localhost:7000/kms/privateKey`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await res.json();
  return data.privateKey;
}

export async function uploadEncryptedFile(blob, encryptedKeys, filename) {
  const form = new FormData();
  form.append('file', blob, filename);
  form.append('encryptedKeys', JSON.stringify(encryptedKeys)); // 👈 加入這一行！

  const res = await fetch(`${BASE}/uploadFile`, {
    method: 'POST',
    body: form
  });

  return await res.json();
}

export async function downloadEncryptedFile(fileId, userId) {
  const res = await fetch(`${BASE}/downloadFile/${fileId}`, {
    headers: {
      'X-User-ID': userId
    }
  });

  const encryptedKey = res.headers.get('X-Encrypted-Key');
  const blob = await res.blob();
  return { fileBlob: blob, encryptedKeyHex: encryptedKey };
}

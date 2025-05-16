<template>
  <div class="container">
    <h2 class="title">Simulation CSE - Upload & Download</h2>
    <button @click="logout" class="logout">Logout</button>
    <div class="section">
      <input type="file" @change="handleFile" class="file-input" />

      <div class="share-section">
        <label>Share with:</label>
        <select v-model="selectedUserId" @change="addToSharedList" class="dropdown">
          <option disabled value="">-- Select user to share --</option>
          <option v-for="user in availableUsers" :key="user.id" :value="user.id">
            {{ user.username }}
          </option>
        </select>
        <div>Shared with: {{ sharedList }}</div>
      </div>

      <button @click="encryptAndUpload" :disabled="!file" class="action-button">Encrypt & Upload</button>
    </div>

    <hr />

    <div class="section">
      <h3 class="subtitle">My Accessible Files:</h3>
      <ul class="file-list">
        <li v-for="fid in myFiles" :key="fid">📄 {{ fid }}</li>
      </ul>
    </div>

    <div class="section">
      <input v-model="downloadId" placeholder="Enter file ID to download" class="input" />
      <button @click="downloadAndDecrypt" class="action-button">Download & Decrypt</button>
    </div>

    <div v-if="decryptedContent" class="section">
      <h3 class="subtitle">Decrypted Content:</h3>
      <pre class="output">{{ decryptedContent }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getPublicKey,
  uploadEncryptedFile,
  downloadEncryptedFile,
  getPrivateKeyFromKMS
} from '../api.js'

const userId = localStorage.getItem('userId')
const token = localStorage.getItem('jwt')

const file = ref(null)
const sharedList = ref([])
const availableUsers = ref([])
const selectedUserId = ref('')
const downloadId = ref('')
const decryptedContent = ref('')
const myFiles = ref([])

const handleFile = (e) => {
  file.value = e.target.files[0]
}

function addToSharedList() {
  if (selectedUserId.value && !sharedList.value.includes(selectedUserId.value)) {
    sharedList.value.push(selectedUserId.value)
  }
  selectedUserId.value = ''
}

async function fetchAvailableUsers() {
  const res = await fetch('http://localhost:5000/allUsers')
  const data = await res.json()
  availableUsers.value = data.users.filter(u => u.id !== userId)
}

async function fetchMyFiles() {
  const res = await fetch('http://localhost:5000/myFiles', {
    headers: { 'X-User-ID': userId }
  })
  const data = await res.json()
  myFiles.value = data.files || []
}

onMounted(() => {
  fetchAvailableUsers()
  fetchMyFiles()
})

async function encryptAndUpload() {
  const aesKey = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt'])
  const iv = crypto.getRandomValues(new Uint8Array(12))

  const fileData = await file.value.arrayBuffer()
  const encryptedData = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, aesKey, fileData)
  const rawKey = await crypto.subtle.exportKey('raw', aesKey)

  if (!sharedList.value.includes(userId)) sharedList.value.push(userId)

  const encryptedKeys = {}
  for (const uid of sharedList.value) {
    const pem = await getPublicKey(uid)
    const rsaKey = await importRSAPublicKey(pem)
    const encKey = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, rsaKey, rawKey)
    encryptedKeys[uid] = [...new Uint8Array(encKey)].map(b => b.toString(16).padStart(2, '0')).join('')
  }

  const blob = new Blob([iv, new Uint8Array(encryptedData)], { type: 'application/octet-stream' })
  const { fileId } = await uploadEncryptedFile(blob, encryptedKeys, file.value.name)

  alert(`Upload successful. File ID: ${fileId}`)
  fetchMyFiles()
}

async function downloadAndDecrypt() {
  try {
    const { fileBlob, encryptedKeyHex } = await downloadEncryptedFile(downloadId.value, userId)
    const privatePem = await getPrivateKeyFromKMS(token)
    const rsaPriv = await importRSAPrivateKey(privatePem)

    const decryptedKey = await crypto.subtle.decrypt(
      { name: 'RSA-OAEP' },
      rsaPriv,
      hexToBytes(encryptedKeyHex)
    )

    const aesKey = await crypto.subtle.importKey('raw', decryptedKey, { name: 'AES-GCM' }, false, ['decrypt'])
    const arrayBuffer = await fileBlob.arrayBuffer()
    const iv = new Uint8Array(arrayBuffer.slice(0, 12))
    const ciphertext = arrayBuffer.slice(12)

    const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, aesKey, ciphertext)

    const blob = new Blob([decrypted], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'decrypted_' + downloadId.value.split('_').slice(1).join('_')
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    alert('❌ Decryption failed. You may not have permission to access this file.')
    console.error(err)
  }
}

function logout() {
  localStorage.removeItem('jwt')
  localStorage.removeItem('userId')
  window.location.reload()
}

function hexToBytes(hex) {
  return new Uint8Array(hex.match(/.{1,2}/g).map(b => parseInt(b, 16)))
}

async function importRSAPublicKey(pem) {
  const b64 = pem.replace(/-----(BEGIN|END) PUBLIC KEY-----/g, '').replace(/\s/g, '')
  const der = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
  return await crypto.subtle.importKey('spki', der.buffer, { name: 'RSA-OAEP', hash: 'SHA-256' }, true, ['encrypt'])
}

async function importRSAPrivateKey(pem) {
  const b64 = pem.replace(/-----(BEGIN|END) PRIVATE KEY-----/g, '').replace(/\s/g, '')
  const der = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
  return await crypto.subtle.importKey('pkcs8', der.buffer, { name: 'RSA-OAEP', hash: 'SHA-256' }, true, ['decrypt'])
}
</script>

<style scoped>
.container {
  max-width: 700px;
  margin: auto;
  padding: 2rem;
  background: #1e1e1e;
  color: #eee;
  font-family: 'Segoe UI', sans-serif;
  border-radius: 8px;
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.5);
}
.title {
  text-align: center;
  margin-bottom: 1rem;
}
.subtitle {
  margin-top: 1.5rem;
}
.section {
  margin-top: 1.25rem;
}
.logout {
  float: right;
  background: #ff4c4c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
.file-input,
.input,
.dropdown {
  display: block;
  margin-top: 0.5rem;
  padding: 0.4rem;
  width: 100%;
  border-radius: 4px;
  border: 1px solid #444;
  background: #2b2b2b;
  color: #fff;
}
.action-button {
  margin-top: 0.75rem;
  background: #008cff;
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
.action-button:disabled {
  background: #444;
  cursor: not-allowed;
}
.output {
  background: #333;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  color: #aff;
}
.file-list {
  list-style: none;
  padding-left: 1rem;
  color: #ccc;
}
</style>


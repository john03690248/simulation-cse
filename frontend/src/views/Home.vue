<template>
  <div class="container">
    <h2>Simulation CSE - Upload & Download</h2>
    <button @click="logout" style="float:right;">Logout</button>
    <input type="file" @change="handleFile" />

    <div style="margin-top: 1rem">
      <label>Share with:</label>
      <select v-model="selectedUserId" @change="addToSharedList">
        <option disabled value="">-- Select user to share --</option>
        <option v-for="user in availableUsers" :key="user.id" :value="user.id">{{ user.username }}</option>
      </select>
      <div>Shared with: {{ sharedList }}</div>
    </div>

    <button @click="encryptAndUpload" :disabled="!file">Encrypt & Upload</button>

    <hr />

    <input v-model="downloadId" placeholder="Enter file ID to download" />
    <button @click="downloadAndDecrypt">Download & Decrypt</button>

    <div v-if="decryptedContent">
      <h3>Decrypted Content:</h3>
      <pre>{{ decryptedContent }}</pre>
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

onMounted(fetchAvailableUsers)

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
  max-width: 600px;
  margin: auto;
  padding: 2rem;
}
</style>

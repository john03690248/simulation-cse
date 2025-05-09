<template>
  <div class="container">
    <h2>Simulation CSE - Upload & Download</h2>
    <button @click="logout" style="float:right;">Logout</button>
    <input type="file" @change="handleFile" />
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
import { ref } from 'vue'
import {
  getPublicKey,
  uploadEncryptedFile,
  downloadEncryptedFile,
  unwrapSessionKey
} from '../api.js'

const userId = localStorage.getItem('userId')
const token = localStorage.getItem('jwt')

const file = ref(null)
const downloadId = ref('')
const decryptedContent = ref('')

const handleFile = (e) => {
  file.value = e.target.files[0]
}

async function encryptAndUpload() {
  const aesKey = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt'])
  const iv = crypto.getRandomValues(new Uint8Array(12))

  const fileData = await file.value.arrayBuffer()
  const encryptedData = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, aesKey, fileData)
  const rawKey = await crypto.subtle.exportKey('raw', aesKey)

  const pem = await getPublicKey(userId)
  const rsaKey = await importRSAPublicKey(pem)
  const encryptedSessionKey = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, rsaKey, rawKey)

  const blob = new Blob([iv, new Uint8Array(encryptedData)], { type: 'application/octet-stream' })
  const { fileId } = await uploadEncryptedFile(blob, encryptedSessionKey, file.value.name)

  alert(`Upload successful. File ID: ${fileId}`)
}

async function downloadAndDecrypt() {
  const { fileBlob, encryptedKeyHex } = await downloadEncryptedFile(downloadId.value)
  console.log('🔍 EncryptedKeyHex:', encryptedKeyHex)
  const decryptedKeyHex = await unwrapSessionKey(encryptedKeyHex, token)
  const rawKey = hexToBytes(decryptedKeyHex)
  
  const aesKey = await crypto.subtle.importKey('raw', rawKey, { name: 'AES-GCM' }, false, ['decrypt'])
  const arrayBuffer = await fileBlob.arrayBuffer()

  const iv = new Uint8Array(arrayBuffer.slice(0, 12))
  const ciphertext = arrayBuffer.slice(12)

  const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, aesKey, ciphertext)

  const blob = new Blob([decrypted], { type: 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'decrypted_' + downloadId.value.split('_').slice(1).join('_') // 取原始檔名
  a.click()
  URL.revokeObjectURL(url)

}

function hexToBytes(hex) {
  return new Uint8Array(hex.match(/.{1,2}/g).map((b) => parseInt(b, 16)))
}

function logout() {
  localStorage.removeItem('jwt')
  localStorage.removeItem('userId')
  window.location.reload()
}

async function importRSAPublicKey(pem) {
  const b64 = pem.replace(/-----(BEGIN|END) PUBLIC KEY-----/g, '').replace(/\s/g, '')
  const der = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))
  return await crypto.subtle.importKey('spki', der.buffer, { name: 'RSA-OAEP', hash: 'SHA-256' }, true, ['encrypt'])
}
</script>

<style scoped>
.container {
  max-width: 600px;
  margin: auto;
  padding: 2rem;
}
</style>

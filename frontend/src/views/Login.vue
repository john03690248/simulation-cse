<template>
  <div class="login-container">
    <h2>Login / Register</h2>
    <input v-model="username" placeholder="Username" />
    <input v-model="password" type="password" placeholder="Password" />

    <input v-if="needsOtp" v-model="otp" placeholder="Enter OTP" />

    <div v-if="qrCodeUrl" class="qrcode">
      <p>Scan this QR code with your Authenticator app:</p>
      <img :src="qrCodeUrl" alt="TOTP QR Code" />
    </div>

    <div class="buttons">
      <button @click="register" :disabled="needsOtp">Register</button>
      <button @click="handleLogin">{{ needsOtp ? 'Verify OTP' : 'Login' }}</button>
    </div>

    <p v-if="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const username = ref('')
const password = ref('')
const otp = ref('')
const userId = ref('')
const error = ref('')
const needsOtp = ref(false)
const qrCodeUrl = ref('')

async function register() {
  error.value = ''
  try {
    const res = await fetch('http://localhost:5000/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    const data = await res.json()
    if (data.id) {
      userId.value = data.id
      localStorage.setItem('userId', data.id)
      qrCodeUrl.value = `http://localhost:5000/totp_qrcode/${data.id}`
      await handleLogin()
    } else {
      error.value = data.error || 'Registration failed'
    }
  } catch (e) {
    error.value = 'Registration error'
  }
}

async function handleLogin() {
  error.value = ''

  if (!needsOtp.value) {
    try {
      const res = await fetch('http://localhost:5000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.value, password: password.value }),
      })
      const data = await res.json()
      if (data.message === 'TOTP required') {
        needsOtp.value = true
        userId.value = data.id
      } else if (data.token) {
        localStorage.setItem('jwt', data.token)
        localStorage.setItem('userId', data.id)
        window.location.reload()
      } else {
        error.value = data.error || 'Login failed'
      }
    } catch (e) {
      error.value = 'Login error'
    }

  } else {
    try {
      const res = await fetch('http://localhost:5000/verify2fa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: userId.value, otp: otp.value }),
      })
      const data = await res.json()
      if (data.token) {
        localStorage.setItem('jwt', data.token)
        localStorage.setItem('userId', data.id)
        window.location.reload()
      } else {
        error.value = data.error || 'OTP verification failed'
      }
    } catch (e) {
      error.value = 'OTP verification error'
    }
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: auto;
  padding: 2rem;
}
input {
  display: block;
  width: 100%;
  margin-bottom: 1rem;
  padding: 0.5rem;
}
.buttons {
  display: flex;
  gap: 1rem;
}
button {
  flex: 1;
  padding: 0.5rem;
}
.qrcode {
  text-align: center;
  margin-bottom: 1rem;
}
.qrcode img {
  max-width: 200px;
  border: 1px solid #ccc;
  padding: 0.5rem;
}
</style>

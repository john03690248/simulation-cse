<template>
  <div class="login-container">
    <h2>Login / Register</h2>
    <input v-model="username" placeholder="Username" />
    <input v-model="password" type="password" placeholder="Password" />
    <div class="buttons">
      <button @click="register">Register</button>
      <button @click="login">Login</button>
    </div>
    <p v-if="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const username = ref('')
const password = ref('')
const error = ref('')

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
      localStorage.setItem('userId', data.id)
      await login()
    } else {
      error.value = data.error || 'Registration failed'
    }
  } catch (e) {
    error.value = 'Registration error'
  }
}

async function login() {
  error.value = ''
  try {
    const res = await fetch('http://localhost:5000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    const data = await res.json()
    if (data.token) {
      localStorage.setItem('jwt', data.token)
      localStorage.setItem('userId', data.id)
      window.location.reload()
    } else {
      error.value = data.error || 'Login failed'
    }
  } catch (e) {
    error.value = 'Login error'
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
</style>

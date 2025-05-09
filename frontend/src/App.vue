<template>
  <component :is="currentView" />
</template>

<script setup>
import Home from './views/Home.vue'
import Login from './views/Login.vue'

const token = localStorage.getItem('jwt')
const userId = localStorage.getItem('userId')
const isLoggedIn = token && userId

const currentView = isLoggedIn ? Home : Login
</script>


# 🛡️ Simulation CSE (Client-Side Encryption) System

This is the final project for Spring 2025 Cryptography Engineering. It implements a secure **Client-Side Encryption (CSE)** simulation supporting:
- Multiple users (≥3)
- WebCrypto API (in-browser AES + RSA)
- Multi-node encrypted storage
- Integrated Key Management System (KMS)

---

## 🔐 Features

- AES-GCM 256-bit encryption (generated on client via WebCrypto)
- Per-user RSA key pairs managed by KMS
- JWT-based login & user authentication
- File encryption in browser, decryption after KMS authorization
- Multi-node storage for encrypted file distribution
- Automatic key wrapping/unwrapping using RSA-OAEP
- Upload record support (by file ID)

---

## 🚀 How to Run

### 1. Install Backend

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start KMS Server

```bash
python kms.py
```

### 3. Start Main App Server

```bash
python app.py
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on: `http://localhost:5173`  
Backend API: `http://localhost:5000`  
KMS API: `http://localhost:6000`

---

## 🗂️ Notes

- `.db`, `tokens/`, `users/`, `kms_keys/`, `storage_node_*/` are git-ignored
- JWT tokens are stored in `localStorage` and used to authorize unwrap requests
- All encryption/decryption is done **client-side**
- Server only stores encrypted content and wrapped session keys

---

## 📄 License

MIT License

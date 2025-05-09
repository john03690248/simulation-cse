
# Simulation CSE (Client-Side Encryption) System

This is a final project for the Spring 2025 Cryptography Engineering course. It implements a **Client-Side Encryption (CSE)** simulation system supporting:
- Multiple users (≥3)
- Multi-node storage
- WebCrypto API
- Key Management System (KMS)

## 💡 Features

- 🔐 End-to-end encryption with AES-GCM (256-bit)
- 🔑 Per-user RSA key pairs (for wrapping/unwrapping AES keys)
- 🌐 Multi-node storage simulation (`storage_node_*/`)
- 📦 Upload & Download encrypted files
- 🧾 File decryption via user private key (unwrapped through KMS)
- 👥 JWT-based frontend login (optional, stubbed in this version)

## 🚀 Quick Start

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

## 🗂️ Notes

- `.db`, `tokens/`, `users/`, `storage_node_*/` are git-ignored
- Uses WebCrypto for AES and RSA operations in the browser
- File IDs are used for download routing

## 📄 License

MIT License

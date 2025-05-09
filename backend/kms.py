
from flask import Flask, request, jsonify
import os, json, jwt
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

app = Flask(__name__)
SECRET_KEY = "supersecret"

def user_key_path(user_id):
    return os.path.join("kms_keys", f"{user_id}.json")

@app.route("/kms/register", methods=["POST"])
def register_keys():
    data = request.get_json()
    user_id = data["user_id"]
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    os.makedirs("kms_keys", exist_ok=True)
    with open(user_key_path(user_id), "w") as f:
        json.dump({"private_key": priv_pem, "public_key": pub_pem}, f)

    return jsonify({"publicKey": pub_pem})

@app.route("/kms/publicKey/<user_id>", methods=["GET"])
def get_pub(user_id):
    try:
        with open(user_key_path(user_id)) as f:
            return jsonify({"publicKey": json.load(f)["public_key"]})
    except:
        return jsonify({"error": "User not found"}), 404

@app.route("/kms/unwrap", methods=["POST"])
def unwrap_key():
    data = request.get_json()
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
    except:
        return jsonify({"error": "Invalid token"}), 403

    encrypted_key = bytes.fromhex(data["encryptedSessionKey"])
    with open(user_key_path(user_id)) as f:
        priv = serialization.load_pem_private_key(
            json.load(f)["private_key"].encode(), password=None
        )

    decrypted_key = priv.decrypt(
        encrypted_key,
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return jsonify({"sessionKey": decrypted_key.hex()})

if __name__ == "__main__":
    os.makedirs("kms_keys", exist_ok=True)
    app.run(host="0.0.0.0", port=6000, debug=True)

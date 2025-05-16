from flask import Flask, request, jsonify
import os, json, jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
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

@app.route("/kms/privateKey", methods=["GET"])
def get_private_key():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
    except:
        return jsonify({"error": "Invalid token"}), 403

    key_path = user_key_path(user_id)
    if not os.path.exists(key_path):
        return jsonify({"error": "No key found"}), 404

    with open(key_path, "r") as f:
        data = json.load(f)
        return jsonify({"privateKey": data["private_key"]})

if __name__ == "__main__":
    os.makedirs("kms_keys", exist_ok=True)
    app.run(host="0.0.0.0", port=7000, debug=True)


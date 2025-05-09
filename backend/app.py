
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, uuid, jwt, datetime, requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
app.config["SECRET_KEY"] = "supersecret"

def user_path(user_id):
    return os.path.join("users", f"{user_id}.json")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    user_id = str(uuid.uuid4())

    kms_res = requests.post("http://localhost:6000/kms/register", json={"user_id": user_id})
    pub_key = kms_res.json()["publicKey"]

    user_data = {
        "id": user_id,
        "username": username,
        "password": password,
        "public_key": pub_key,
    }

    os.makedirs("users", exist_ok=True)
    with open(user_path(user_id), "w") as f:
        json.dump(user_data, f)

    return jsonify({"id": user_id})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    for filename in os.listdir("users"):
        with open(os.path.join("users", filename), "r") as f:
            user = json.load(f)
            if user["username"] == username and user["password"] == password:
                token = jwt.encode(
                    {
                        "id": user["id"],
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=3),
                    },
                    app.config["SECRET_KEY"],
                    algorithm="HS256",
                )
                return jsonify({
                    "token": token,
                    "id": user["id"]
                })
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/publicKey/<user_id>", methods=["GET"])
def get_public_key(user_id):
    try:
        with open(user_path(user_id), "r") as f:
            user = json.load(f)
            return jsonify({"publicKey": user["public_key"]})
    except:
        return jsonify({"error": "User not found"}), 404

@app.route("/unwrapKey", methods=["POST"])
def unwrap_proxy():
    token = request.headers.get("Authorization", "")
    encrypted = request.get_json().get("encryptedSessionKey")
    if not encrypted:
        return jsonify({"error": "Missing encryptedSessionKey"}), 400

    try:
        res = requests.post("http://localhost:6000/kms/unwrap",
            headers={"Authorization": token},
            json={"encryptedSessionKey": encrypted}
        )
        return jsonify(res.json())
    except:
        return jsonify({"error": "KMS unavailable"}), 503

@app.route("/uploadFile", methods=["POST"])
def upload_file():
    file = request.files["file"]
    encrypted_key = request.form["encryptedKey"]
    filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)

    storage_nodes = ["storage_node_1", "storage_node_2"]
    chosen_node = storage_nodes[hash(filename) % len(storage_nodes)]
    filepath = os.path.join(chosen_node, filename)
    os.makedirs(chosen_node, exist_ok=True)
    file.save(filepath)

    os.makedirs("tokens", exist_ok=True)
    with open(os.path.join("tokens", filename + ".meta.json"), "w") as f:
        json.dump({"encryptedKey": encrypted_key}, f)

    return jsonify({"fileId": filename})

@app.route("/downloadFile/<file_id>", methods=["GET"])
def download_file(file_id):
    for node in ["storage_node_1", "storage_node_2"]:
        path = os.path.join(node, file_id)
        if os.path.exists(path):
            with open(os.path.join("tokens", file_id + ".meta.json")) as f:
                meta = json.load(f)

            response = send_file(path, as_attachment=True)
            response.headers["X-Encrypted-Key"] = meta["encryptedKey"]
            response.headers["Access-Control-Expose-Headers"] = "X-Encrypted-Key"
            return response
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    os.makedirs("users", exist_ok=True)
    os.makedirs("tokens", exist_ok=True)
    os.makedirs("storage_node_1", exist_ok=True)
    os.makedirs("storage_node_2", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)

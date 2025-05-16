from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, uuid, jwt, datetime, requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, 
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     expose_headers=["X-Encrypted-Key"],
     allow_headers=["Content-Type", "Authorization", "X-User-ID"])
app.config["SECRET_KEY"] = "supersecret"

def user_path(user_id):
    return os.path.join("users", f"{user_id}.json")

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        user_id = str(uuid.uuid4())

        kms_res = requests.post("http://localhost:7000/kms/register", json={"user_id": user_id})
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        res = requests.post("http://localhost:7000/kms/unwrap",
            headers={"Authorization": token},
            json={"encryptedSessionKey": encrypted}
        )
        return jsonify(res.json())
    except:
        return jsonify({"error": "KMS unavailable"}), 503

@app.route("/uploadFile", methods=["POST"])
def upload_file():
    file = request.files["file"]
    encrypted_keys_json = request.form["encryptedKeys"]
    encrypted_keys = json.loads(encrypted_keys_json)

    filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)

    storage_nodes = ["storage_node_1", "storage_node_2"]
    chosen_node = storage_nodes[hash(filename) % len(storage_nodes)]
    filepath = os.path.join(chosen_node, filename)
    os.makedirs(chosen_node, exist_ok=True)
    file.save(filepath)

    os.makedirs("tokens", exist_ok=True)
    metadata = {
        "owner": list(encrypted_keys.keys())[0],
        "sharedKeys": encrypted_keys
    }

    with open(os.path.join("tokens", filename + ".meta.json"), "w") as f:
        json.dump(metadata, f)

    return jsonify({"fileId": filename})

@app.route("/downloadFile/<file_id>", methods=["GET"])
def download_file(file_id):
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    for node in ["storage_node_1", "storage_node_2"]:
        path = os.path.join(node, file_id)
        if os.path.exists(path):
            with open(os.path.join("tokens", file_id + ".meta.json")) as f:
                meta = json.load(f)

            encrypted_key = meta["sharedKeys"].get(user_id)
            if not encrypted_key:
                return jsonify({"error": "Permission denied"}), 403

            response = send_file(path, as_attachment=True)
            response.headers["X-Encrypted-Key"] = encrypted_key
            response.headers["Access-Control-Expose-Headers"] = "X-Encrypted-Key"
            return response

    return jsonify({"error": "File not found"}), 404

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-User-ID'
    response.headers['Access-Control-Expose-Headers'] = 'X-Encrypted-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

@app.route("/allUsers", methods=["GET"])
def all_users():
    users = []
    for filename in os.listdir("users"):
        with open(os.path.join("users", filename), "r") as f:
            user = json.load(f)
            users.append({
                "id": user["id"],
                "username": user["username"]
            })
    return jsonify({"users": users})



if __name__ == "__main__":
    os.makedirs("users", exist_ok=True)
    os.makedirs("tokens", exist_ok=True)
    os.makedirs("storage_node_1", exist_ok=True)
    os.makedirs("storage_node_2", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, request, jsonify, send_from_directory
from ollama import chat
from PIL import Image
from pymongo import MongoClient
from datetime import datetime
import base64
import io
import json
from inventory_service import check_inventory
import requests
from bson import ObjectId
# ---------------- CONFIG ----------------
PHARMACY_API_URL = "http://192.168.137.183:5001/order"

# ---------------- FLASK APP ----------------
app = Flask(__name__)

# ---------------- MONGODB ----------------
client = MongoClient("mongodb://localhost:27017")
db = client["hospital"]
dbd = client["hospital_ai"]
collection = dbd["patients"]
doctor_collection = dbd["doctors"]

# ---------------- SEND TO PHARMACY ----------------
def send_to_pharmacy(medicine):
    try:
        payload = {
            "medicine_name": medicine["corrected_name"],
            "price": medicine["price"],
            "quantity": 1
        }

        response = requests.post(
            PHARMACY_API_URL,
            json=payload,
            timeout=5
        )

        return {
            "sent": True,
            "response_code": response.status_code,
            "pharmacy_response": response.json()
        }

    except Exception as e:
        return {
            "sent": False,
            "error": str(e)
        }

# ---------------- IMAGE TO BASE64 ----------------
def image_to_base64(file):
    image = Image.open(file).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/scan")
def auto_scan():
    return send_from_directory(".", "scan.html")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    return send_from_directory(".", "dashboard.html")
@app.route("/doctor_login", methods=["POST"])
def doctor_login():

    data = request.json

    name = data.get("name").strip()
    password = data.get("password").strip()

    print("Entered Name:", name)
    print("Entered Password:", password)

    doctor = doctor_collection.find_one({
        "name": {"$regex": f"^{name}$", "$options": "i"}
    })

    print("Doctor Found:", doctor)

    if not doctor:
        return jsonify({"status":"fail"})

    if str(doctor["password"]) != password:
        print("Password mismatch:", doctor["password"])
        return jsonify({"status":"fail"})

    login_time = datetime.utcnow()

    doctor_collection.update_one(
        {"_id": doctor["_id"]},
        {"$set":{
            "available":True,
            "login_time":login_time,
            "logout_time":""
        }}
    )

    return jsonify({
        "status":"success",
        "doctor_id":str(doctor["_id"]),
        "specialization":doctor["specialization"],
        "login_time":str(login_time)
    })

@app.route("/login")
def login_page():
    return send_from_directory(".", "login.html")

@app.route("/doctor_logout", methods=["POST"])
def doctor_logout():

    data = request.json

    doctor_id = data.get("doctor_id")

    logout_time = datetime.utcnow()

    doctor_collection.update_one(
        {"_id":ObjectId(doctor_id)},
        {
            "$set":{
                "available":False,
                "logout_time":logout_time
            }
        }
    )

    return jsonify({
        "status":"logout",
        "logout_time":str(logout_time)
    })

# ---------------- PATIENT LIST ----------------

@app.route("/patients/<specialization>")
def patients(specialization):

    data=[]

    patients_list = collection.find().sort("created_at",-1)

    for p in patients_list:

        data.append({

            "name":p.get("name","Patient"),

            "token":str(p.get("_id"))[-4:],

            "status":"Waiting"

        })

    return jsonify(data)



# ---------------- LATEST SCAN ----------------

@app.route("/latest")
def latest():

    last = collection.find_one(sort=[("created_at",-1)])

    if not last:

        return jsonify({})

    return jsonify({

        "patient_id":str(last["_id"]),

        "inventory":last.get("inventory_status",[])

    })
# ---------------- ANALYZE (NO AUTO SEND) ----------------
@app.route("/analyze", methods=["POST"])
def analyze():

    images = request.files.getlist("images")

    if not images:
        return jsonify({"error": "No images uploaded"}), 400

    image_base64_list = [image_to_base64(img) for img in images]

    prompt = """
Extract medicine names from prescription.

Return JSON only:

{
 "medicines":[
  {
   "medicine_name":"",
   "strength":""
  }
 ],
 "total_medicines":0
}
"""

    response = chat(
        model="qwen3-vl:235b-instruct-cloud",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": image_base64_list
            }
        ]
    )

    try:
        result_json = json.loads(response.message.content)
    except Exception:
        return jsonify({
            "error": "Invalid JSON from AI",
            "raw": response.message.content
        })

    medicines = result_json.get("medicines", [])

    inventory_result = check_inventory(medicines)

    # Save initial scan result (without pharmacy dispatch)
    document = {
        "extracted_medicines": medicines,
        "inventory_status": inventory_result,
        "approved_medicines": [],
        "created_at": datetime.utcnow()
    }

    inserted = collection.insert_one(document)

    return jsonify({
        "status": "review_required",
        "patient_id": str(inserted.inserted_id),
        "inventory": inventory_result
    })


# ---------------- DOCTOR APPROVAL ----------------
@app.route("/approve", methods=["POST"])
def approve():

    data = request.json
    patient_id = data.get("patient_id")
    approved_medicines = data.get("medicines", [])

    if not approved_medicines:
        return jsonify({"error": "No medicines selected"}), 400

    dispatch_results = []

    for med in approved_medicines:
        pharmacy_status = send_to_pharmacy(med)
        med["pharmacy_dispatch"] = pharmacy_status
        dispatch_results.append(med)

    # Update MongoDB record
    collection.update_one(
        {"_id": collection.find_one({"_id": collection.find_one()["_id"]})["_id"]},
        {"$set": {"approved_medicines": dispatch_results}}
    )

    return jsonify({
        "status": "sent_to_pharmacy",
        "details": dispatch_results
    })


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
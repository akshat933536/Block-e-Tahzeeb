from flask import Flask, render_template, request
from pymongo import MongoClient
from ollama import chat
import datetime
import threading
import time

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["hospital_ai"]

doctors_collection = db["doctors"]
patients_collection = db["patients"]


# ---------------- AI Classification ----------------

def classify_symptom(symptom_text):

    response = chat(
        model='deepseek-v3.1:671b-cloud',
        messages=[
            {
                'role': 'system',
                'content': '''
Return ONLY one specialization from this list:

Cardiology
Neurology
Orthopedic
Dermatology
Pediatrics
General
ENT
Gynecology

No extra words.
'''
            },
            {
                'role': 'user',
                'content': symptom_text
            }
        ],
    )

    result = response.message.content.strip()

    print("AI Returned:", result)

    return result



# ---------------- Doctor Allocation ----------------

def allocate_doctor(specialization):

    doctor = doctors_collection.find_one({
        "specialization": specialization,
        "available": True
    })

    if doctor:
        doctors_collection.update_one(
            {"_id": doctor["_id"]},
            {"$set": {"available": False}}
        )

        # Start timer
        threading.Thread(
            target=doctor_timer,
            args=(doctor["_id"], specialization),
            daemon=True
        ).start()

    return doctor



# ---------------- 5 Minute Timer ----------------

def doctor_timer(doctor_id, specialization):

    print("Doctor Busy for 5 min")

    time.sleep(300)   # 5 minutes

    doctors_collection.update_one(
        {"_id": doctor_id},
        {"$set": {"available": True}}
    )

    print("Doctor Available Again")

    notify_next_patient(specialization)



# ---------------- Notify Next Patient ----------------

def notify_next_patient(specialization):

    next_patient = patients_collection.find_one(
        {
            "specialization": specialization,
            "notified": {"$ne": True}
        },
        sort=[("token", 1)]
    )

    if next_patient:

        patients_collection.update_one(
            {"_id": next_patient["_id"]},
            {"$set": {"notified": True}}
        )

        print("Next Patient Turn:", next_patient["name"])


        # Future SMS system
        # send_sms(next_patient["mobile"])



# ---------------- Routes ----------------

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        symptom = request.form['symptom']
        mobile = request.form.get('mobile')

        specialization = classify_symptom(symptom)

        doctor = doctors_collection.find_one({
            "specialization": specialization
        })

        token_number = patients_collection.count_documents({}) + 1

        # Count patients already waiting for same doctor
        waiting_count = patients_collection.count_documents({
            "specialization": specialization,
            "completed": {"$ne": True}
        })

        waiting_time = waiting_count * 5   # 5 min per patient


        patient_data = {

            "name": name,
            "age": age,
            "gender": gender,
            "symptom": symptom,
            "mobile": mobile,

            "specialization": specialization,

            "doctor_allocated": doctor["name"],

            "token": token_number,

            "waiting_number": waiting_count + 1,

            "waiting_time": waiting_time,

            "completed": False,

            "timestamp": datetime.datetime.now()

        }

        patients_collection.insert_one(patient_data)


        # First Patient → Start Doctor Timer
        if waiting_count == 0:

            doctors_collection.update_one(
                {"_id": doctor["_id"]},
                {"$set": {"available": False}}
            )

            threading.Thread(
                target=doctor_timer,
                args=(doctor["_id"], specialization),
                daemon=True
            ).start()



        return f"""

        <h2>Registration Successful</h2>

        <p>Patient: {name}</p>

        <p>Doctor: {doctor['name']}</p>

        <p>Specialization: {specialization}</p>

        <p>Token Number: {token_number}</p>

        <p>Queue Position: {waiting_count + 1}</p>

        <p>Estimated Waiting Time: {waiting_time} Minutes</p>

        """
        
    return render_template('index.html')



if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5002)
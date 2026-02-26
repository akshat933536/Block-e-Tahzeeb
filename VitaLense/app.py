from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from ollama import chat
import datetime
import base64

app = Flask(__name__)

# ---------------- MongoDB ----------------

client = MongoClient("mongodb://localhost:27017/")
db = client["hospital_ai"]

doctors_collection = db["doctors"]
patients_collection = db["patients"]


# ---------------- AI Analysis ----------------

def ai_medical_response(symptom_text):

    response = chat(
        model='deepseek-v3.1:671b-cloud',
        messages=[
            {
                'role': 'system',
                'content': """
You are a medical AI assistant.

Return in format:

Disease:
Doctor:
Precautions:
Immediate Steps:

Keep simple.
"""
            },
            {
                'role': 'user',
                'content': symptom_text
            }
        ],
    )

    return response.message.content.strip()



# ---------------- Extract Doctor Type ----------------

def extract_doctor(ai_text):

    ai_text = ai_text.lower()

    if "dentist" in ai_text:
        return "Dentist"

    elif "cardio" in ai_text:
        return "Cardiologist"

    elif "skin" in ai_text:
        return "Dermatologist"

    elif "neuro" in ai_text:
        return "Neurologist"

    else:
        return "General"



# ---------------- Home Page ----------------

@app.route('/')
def home():

    return render_template("index.html")



# ---------------- Submit Form ----------------

@app.route('/submit', methods=['POST'])

def submit():

    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    mobile = request.form['mobile']
    symptom = request.form['symptom']


    # Photo Upload

    photo = request.files['photo']

    image_base64=""

    if photo:

        image_base64=base64.b64encode(photo.read()).decode('utf-8')


    # AI Analysis

    ai_result = ai_medical_response(symptom)


    # Doctor Type

    specialization = extract_doctor(ai_result)


    # Find Doctor

    doctor = doctors_collection.find_one({
        "specialization":specialization
    })


    if doctor:

        doctor_name=doctor["name"]

    else:

        doctor_name="Not Available"



    # Save Patient

    patient_data={

        "name":name,
        "age":age,
        "gender":gender,
        "mobile":mobile,

        "symptom":symptom,

        "ai_result":ai_result,

        "specialization":specialization,

        "doctor":doctor_name,

        "photo":image_base64,

        "timestamp":datetime.datetime.now()

    }


    patients_collection.insert_one(patient_data)



    # Response for Output Box

    return jsonify({

        "name":name,
        "doctor":doctor_name,
        "specialization":specialization,
        "ai_result":ai_result

    })



# ---------------- Doctor Dashboard ----------------

@app.route('/doctor')

def doctor():

    patients=list(
        patients_collection.find().sort("timestamp",-1)
    )

    return render_template(
        "doctor.html",
        patients=patients
    )



# ---------------- Run Server ----------------

if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )
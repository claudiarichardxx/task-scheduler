from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
from utils.data_retriever import DataRetriever
from utils.scheduling_logic import generate_and_save_schedule_with_overflow
import os
import json

# Init Firebase Admin

json_str = os.environ.get('FIREBASE_CREDENTIALS')
cred_dict = json.loads(json_str)
cred = credentials.Certificate(cred_dict)

# cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
CORS(app)

@app.route('/update_schedule', methods=['POST'])
def update_schedule():

    data = request.get_json()
    email = data.get('email')
    date_key = data.get('date')

    if not email or not date_key:
        return jsonify({"error": "Missing email or date"}), 400

    # Retrieve user data
    retriever = DataRetriever(email, date_key, db)
    tasks, available_hours, daily_mandatory, previous_overflow = retriever.get_scheduling_info()
    generate_and_save_schedule_with_overflow(retriever.db, email, tasks, available_hours, daily_mandatory, previous_overflow=previous_overflow)


    return jsonify({
        "status": "success"
    })



if __name__ == '__main__':
    app.run(debug=True)
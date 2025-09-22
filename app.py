from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
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

    # 1. Get tasks for the date
    tasks_doc = db.collection('users').document(email).collection('tasks').document(date_key).get()
    tasks = tasks_doc.to_dict().get('tasks', []) if tasks_doc.exists else []

    # 2. Get available hours from user doc
    user_doc = db.collection('users').document(email).get()
    available_hours = user_doc.to_dict().get('available_hours', [])

    # 3. Filter available hours for the given day
    # Assuming date_key is YYYYMMDD and available_hours has 'day' like 'Mon', 'Tue', etc.
    import datetime
    day_name = datetime.datetime.strptime(date_key, "%Y%m%d").strftime("%a")
    day_slots = [slot for slot in available_hours if slot['day'] == day_name]

    # 4. Allocate tasks into available slots (simple sequential allocation)
    schedule_events = []
    task_index = 0

    for slot in day_slots:
        start_time = slot['start']
        end_time = slot['end']

        # For now, just assign one task per slot in order
        if task_index < len(tasks):
            schedule_events.append({
                "taskid": tasks[task_index]['taskid'],
                "time": start_time
            })
            task_index += 1

    # 5. Push schedule to Firestore
    db.collection('users').document(email).collection('schedules').document(date_key).set({
        "events": schedule_events
    })

    return jsonify({
        "status": "success",
        "scheduled_events": schedule_events
    })

if __name__ == '__main__':
    app.run(debug=True)
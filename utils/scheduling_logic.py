import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_tasks_and_schedule(email, date_key):
    user_ref = db.collection('users').document(email)

    # Get tasks
    task_doc = user_ref.collection('tasks').document(date_key).get()
    tasks = task_doc.to_dict().get('tasks', []) if task_doc.exists else []

    # Get schedule
    schedule_doc = user_ref.collection('schedules').document(date_key).get()
    schedule = schedule_doc.to_dict().get('events', []) if schedule_doc.exists else []

    return {
        "tasks": tasks,
        "schedule": schedule
    }



def merge_schedule_with_tasks(tasks, schedule):
    task_map = {t['taskid']: t for t in tasks}
    merged = []
    for event in schedule:
        tid = event['taskid']
        merged.append({
            "time": event['time'],
            **task_map.get(tid, {})
        })
    return merged

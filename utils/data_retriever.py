import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
import os
import json

class DataRetriever:

    def __init__(self, email, date, db):
        self.email = email
        self.date = date
        self.db = db

    
    def get_scheduling_info(self):

        tasks_doc = self.db.collection('users').document(self.email).collection('tasks').document(self.date).get()
        tasks = tasks_doc.to_dict().get('tasks', []) if tasks_doc.exists else []
        user_doc = self.db.collection('users').document(self.email).get()
        available_hours = user_doc.to_dict().get('available_hours', [])
        daily_mandatory =  user_doc.to_dict().get('daily_mandatory', [])
        previous_overflow = user_doc.to_dict().get('overflow', [])

        return tasks, available_hours, daily_mandatory, previous_overflow
        


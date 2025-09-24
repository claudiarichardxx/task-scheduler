from datetime import datetime



def generate_and_save_schedule_with_overflow(db, email, tasks, available_hours, mandatory, overrides=None, previous_overflow=None):

    today = datetime.now().strftime("%a")  # e.g. 'Tue'
    date_str = datetime.now().strftime("%Y%m%d")  # e.g. '2025-09-23'

    # Step 1: Merge today's availability
    windows = available_hours.get(today, [])
    blocks = mandatory.copy()

    if overrides and date_str in overrides:
        blocks.extend(overrides[date_str])

    blocks.sort(key=lambda b: b['start'])

    # Step 2: Build timeline with mandatory blocks
    timeline = []
    for window in windows:
        cursor = window['start']
        end = window['end']

        for block in blocks:
            if block['start'] >= cursor and block['start'] < end:
                if block['start'] > cursor:
                    timeline.append({'type': 'free', 'start': cursor, 'end': block['start']})
                timeline.append({
                    'type': 'activity',
                    'label': block['label'],
                    'start': block['start'],
                    'end': block['start'] + block['duration']
                })
                cursor = block['start'] + block['duration']

        if cursor < end:
            timeline.append({'type': 'free', 'start': cursor, 'end': end})

    # Step 3: Merge tasks + overflow and sort
    all_tasks = [t for t in tasks if not t['done']]
    if previous_overflow:
        all_tasks.extend(previous_overflow)

    all_tasks.sort(key=lambda t: (-t['priority'], t['eta']))

    scheduled_tasks = []
    remaining_tasks = []

    for slot in timeline:
        if slot['type'] != 'free':
            continue

        slot_start = slot['start']
        slot_end = slot['end']
        slot_duration = slot_end - slot_start

        i = 0
        while i < len(all_tasks):
            task = all_tasks[i]
            eta = task['eta']

            if eta <= slot_duration:
                scheduled_tasks.append({
                    'type': 'task',
                    'title': task['title'],
                    'taskid': task['taskid'],
                    'start': slot_start,
                    'end': slot_start + eta,
                    'difficulty': task['difficulty'],
                    'priority': task['priority']
                })
                slot_start += eta
                slot_duration -= eta
                all_tasks.pop(i)
            elif eta > slot_duration and eta >= 1:
                # Split task
                scheduled_tasks.append({
                    'type': 'task',
                    'title': task['title'] + ' (partial)',
                    'taskid': task['taskid'],
                    'start': slot_start,
                    'end': slot_end,
                    'difficulty': task['difficulty'],
                    'priority': task['priority']
                })
                task['eta'] = round(eta - slot_duration, 2)
                slot_duration = 0
                slot_start = slot_end
                i += 1
            else:
                i += 1

        if slot_duration > 0:
            scheduled_tasks.append({
                'type': 'free',
                'start': slot_start,
                'end': slot_end
            })

    # Step 4: Combine mandatory + scheduled
    final_schedule = [b for b in timeline if b['type'] == 'activity'] + scheduled_tasks
    final_schedule.sort(key=lambda b: b['start'])

    # Step 5: Save to Firestore
    doc_ref = db.collection('users').document(email).collection('schedules').document(date_str)
    doc_ref.set({
        'schedule': final_schedule,
    })

    doc_ref = db.collection('users').document(email)
    doc_ref.update({
        'overflow': all_tasks  # Save remaining unscheduled tasks in user_doc
    })

    print(f"✅ Schedule saved for {email} on {date_str}")
    print(f"🧠 Overflow tasks: {len(all_tasks)}")

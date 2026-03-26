import nepali_datetime
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

def bs_to_ad(bs_date_str):
    bs_date_str = str(bs_date_str).replace('/', '-')
    y, m, d = map(int, bs_date_str.split('-'))
    np_date = nepali_datetime.date(y, m, d)
    return np_date.to_datetime_date()

def ad_to_bs(ad_date):
    np_date = nepali_datetime.date.from_datetime_date(ad_date)
    return np_date.strftime('%Y-%m-%d')

def get_micro_chunks(subject_name: str, focus_area: str, allocated_mins: float, session_mins: float, break_mins: float, plan_type: str = "study", current_time: datetime = None):
    plan = []
    remaining = float(allocated_mins)
    
    phases = []
    if plan_type == "intensive":
        phases = ["Rapid Concept Scan", "Past Paper Blitz", "Formula Drill", "High-Yield Review"]
    elif plan_type == "study":
        phases = ["Deep Work: Concepts", "Active Recall", "Past Paper Sprint", "Feynman Review"]
    else:
        phases = ["Spaced Revision", "Weak Point Polish", "Flashcard Drill"]
        
    sessions_count = 0
    
    while remaining > 0:
        # Check for meals
        current_hour = current_time.hour
        if current_hour == 8 and not any('Breakfast' in p['activity'] for p in plan):
            end_time = current_time + timedelta(minutes=45)
            plan.append({"time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", "activity": "Breakfast & Hydration", "type": "meal", "minutes": 45})
            current_time = end_time
            continue
        elif current_hour == 13 and not any('Lunch' in p['activity'] for p in plan):
            end_time = current_time + timedelta(minutes=60)
            plan.append({"time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", "activity": "Lunch & Mindful Rest", "type": "meal", "minutes": 60})
            current_time = end_time
            continue
        elif current_hour == 20 and not any('Dinner' in p['activity'] for p in plan):
            end_time = current_time + timedelta(minutes=60)
            plan.append({"time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", "activity": "Dinner & Family Time", "type": "meal", "minutes": 60})
            current_time = end_time
            continue
            
        dur = min(session_mins, remaining)
        if dur < 15: # if less than 15 mins left, just append it to a break or skip
            break
            
        end_time = current_time + timedelta(minutes=dur)
        phase = phases[sessions_count % len(phases)]
        plan.append({
            "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
            "activity": f"{phase}: {focus_area} ({subject_name})",
            "type": "study" if plan_type == "intensive" else plan_type,
            "minutes": int(dur),
            "subject": subject_name
        })
        current_time = end_time
        remaining -= dur
        sessions_count += 1
        
        if remaining > 15:
            # Add break
            b_dur = break_mins if sessions_count % 3 != 0 else 45 # long break every 3 sessions
            end_time = current_time + timedelta(minutes=b_dur)
            plan.append({
                "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "activity": "Deep Rest / Buffer" if b_dur == 45 else "Micro-Break (20-20-20)",
                "type": "break",
                "minutes": int(b_dur)
            })
            current_time = end_time

    return plan, current_time

def generate_study_plan(exams_list: List[Dict], daily_study_hours: float = 8.0, session_mins: float = 30.0, break_mins: float = 5.0, start_time: str = "06:00", topic_mastery_map: Optional[Dict] = None):
    prepared_exams = []
    topic_mastery_map = topic_mastery_map or {}
    
    for ex in exams_list:
        try:
            date_str = str(ex['date']).replace('/', '-')
            year = int(date_str.split('-')[0])
            if year > 2060:
                ad_date = bs_to_ad(date_str)
            else:
                ad_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
            chapters = ex.get('chapters', [])
            prepared_exams.append({
                'name': ex['name'],
                'ad_date': ad_date,
                'chapters': chapters,
                'difficulty': int(ex.get('difficulty', 2)),
                'total_topics': len(chapters) if chapters else 1
            })
        except: continue
        
    prepared_exams.sort(key=lambda x: x['ad_date'])
    laptop_now = datetime.now()
    today_ad = laptop_now.date()
    
    if not prepared_exams:
        return {"status": "error", "message": "No exams found"}

    last_exam_ad = prepared_exams[-1]['ad_date']
    all_dates = []
    temp_date = today_ad
    while temp_date <= last_exam_ad:
        all_dates.append(temp_date)
        temp_date += timedelta(days=1)
        
    final_days = []
    
    # Last studied tracker for revision
    last_studied_date = {} # subject_name -> date
    revision_queue = [] # list of {subject, date_to_revise, type}
    
    # Chapter progress tracker
    subject_progress = {ex['name']: 0 for ex in prepared_exams}
    
    for i, date in enumerate(all_dates):
        d_status = "today" if date == today_ad else "upcoming"
        effective_start_time = start_time
        if d_status == "today":
            now_time = datetime.now()
            start_dt = datetime.strptime(start_time, "%H:%M")
            if now_time.time() > start_dt.time():
                next_hour = now_time.hour + 1 if now_time.minute > 0 else now_time.hour
                if next_hour >= 23: next_hour = 22
                effective_start_time = f"{next_hour:02d}:00"
                
        daily_mins_avail = daily_study_hours * 60.0
        if d_status == "today" and effective_start_time != start_time:
            start_h = int(effective_start_time.split(':')[0])
            daily_mins_avail = max(120.0, min(daily_mins_avail, float(24 - start_h) * 60.0))
            
        current_dt = datetime.combine(date, datetime.strptime(effective_start_time, "%H:%M").time())
        day_tasks = []
        
        # 1. Check if it's an exam day
        exam_today = next((ex for ex in prepared_exams if ex['ad_date'] == date), None)
        if exam_today:
            end_c = current_dt + timedelta(minutes=90)
            day_tasks.append({"time": f"{current_dt.strftime('%H:%M')} - {end_c.strftime('%H:%M')}", "activity": f"Final Polish: {exam_today['name']}", "type": "study", "minutes": 90, "subject": exam_today['name']})
            current_dt = end_c
            end_c = current_dt + timedelta(minutes=180)
            day_tasks.append({"time": f"{current_dt.strftime('%H:%M')} - {end_c.strftime('%H:%M')}", "activity": "OFFICIAL EXAM", "type": "exam", "minutes": 180, "subject": exam_today['name']})
            current_dt = end_c
            
            # Post-exam recovery
            end_c = current_dt + timedelta(minutes=120)
            day_tasks.append({"time": f"{current_dt.strftime('%H:%M')} - {end_c.strftime('%H:%M')}", "activity": "Post-Exam Recovery", "type": "break", "minutes": 120})
            current_dt = end_c
            daily_mins_avail -= 390
            
        if daily_mins_avail <= 0:
            final_days.append({
                "id": f"day-{i}", "bs_date": ad_to_bs(date), "ad_date": str(date), "day_of_week": date.strftime("%A"),
                "is_exam_day": bool(exam_today), "status": d_status, "subject": exam_today['name'] if exam_today else "None",
                "tasks": day_tasks
            })
            continue

        # 2. Select Top Subject for the Day
        next_exams = [e for e in prepared_exams if e['ad_date'] > date]
        if not next_exams and not exam_today:
            final_days.append({
                "id": f"day-{i}", "bs_date": ad_to_bs(date), "ad_date": str(date), "day_of_week": date.strftime("%A"),
                "is_exam_day": bool(exam_today), "status": d_status, "subject": "None", "tasks": day_tasks
            })
            continue

        selected_subject = None
        is_intensive_mode = False
        
        if exam_today:
            selected_subject = exam_today['name']
        else:
            # 2a. Check for Lockdown Phase (Exam within 7 days)
            lockdown_subject = None
            min_days = 99
            for ex in next_exams:
                d_left = (ex['ad_date'] - date).days
                if d_left <= 7 and d_left < min_days:
                    min_days = d_left
                    lockdown_subject = ex['name']
            
            if lockdown_subject:
                selected_subject = lockdown_subject
                is_intensive_mode = True
            else:
                # 2b. 'Wise' Selection (weighted by topics left, difficulty, and stale penalty)
                subject_scores = []
                
                for ex in next_exams:
                    s_name = ex['name']
                    days_left = max(1, (ex['ad_date'] - date).days)
                    diff = float(ex['difficulty'])
                    
                    # Remaining Topics
                    rem_topics = max(1, len(ex.get('chapters', [])) - subject_progress.get(s_name, 0))
                    
                    # Stale Penalty (encourage rotation)
                    # If this was studied yesterday AND we have other subjects, penalize it heavily to force rotation
                    last_subject = final_days[-1]['subject'] if final_days else None
                    rotation_penalty = 1.0
                    if s_name == last_subject and len(next_exams) > 1:
                        rotation_penalty = 0.1 # Force a switch
                    
                    days_since_last = 7
                    if s_name in last_studied_date:
                        days_since_last = (date - last_studied_date[s_name]).days
                    stale_boost = min(3.0, 1.0 + (days_since_last * 0.4))
                    
                    mastery_data = topic_mastery_map.get(s_name, {})
                    avg_m = sum(float(v) for v in mastery_data.values()) / len(mastery_data) / 100.0 if mastery_data else 0.0
                    
                    # Perfected Score Formula with Rotation Penalty
                    score = (diff * rem_topics * (1.2 - avg_m) * stale_boost * rotation_penalty) / days_left
                    subject_scores.append({"ex": ex, "score": score})
                
                if subject_scores:
                    best_item = max(subject_scores, key=lambda x: x['score'])
                    selected_subject = best_item['ex']['name']

        # 3. Process Revisions (ONLY for the selected subject)
        if selected_subject:
            revisions_today = [r for r in revision_queue if r['date'] == date and r['subject'] == selected_subject]
            for rev in revisions_today:
                if daily_mins_avail < 30: break
                rev_mins = min(90, daily_mins_avail * 0.3) # Dedicate up to 30% for revision if needed
                chunks, current_dt = get_micro_chunks(rev['subject'], "Spaced Revision", rev_mins, session_mins, break_mins, "revision", current_dt)
                day_tasks.extend(chunks)
                daily_mins_avail -= rev_mins
            
        # 4. Allocate remaining time to the ONE Selected Subject
        if selected_subject and daily_mins_avail >= 30:
            # Find the full exam object for the selected subject
            target_ex = next((e for e in prepared_exams if e['name'] == selected_subject), None)
            if target_ex:
                chaps = target_ex['chapters']
                idx = subject_progress[selected_subject]
                focus = str(chaps[idx % len(chaps)]) if chaps else "Core Concepts"
                
                # Increment progress for next time this subject is picked
                subject_progress[selected_subject] += 1
                
                # No 4-hour cap; use all available time
                p_type = "intensive" if is_intensive_mode else "study"
                chunks, current_dt = get_micro_chunks(selected_subject, focus, daily_mins_avail, session_mins, break_mins, p_type, current_dt)
                day_tasks.extend(chunks)
                
                # Schedule future revisions
                if selected_subject not in last_studied_date or last_studied_date[selected_subject] != date:
                    revision_queue.append({"subject": selected_subject, "date": date + timedelta(days=1), "type": "rev-1"})
                    revision_queue.append({"subject": selected_subject, "date": date + timedelta(days=3), "type": "rev-2"})
                    revision_queue.append({"subject": selected_subject, "date": target_ex['ad_date'] - timedelta(days=1), "type": "rev-3"})
                
                last_studied_date[selected_subject] = date
                
        # Buffer at end of day
        end_c = current_dt + timedelta(minutes=15)
        day_tasks.append({"time": f"{current_dt.strftime('%H:%M')} - {end_c.strftime('%H:%M')}", "activity": "Reflection & Next Day Prep", "type": "buffer", "minutes": 15})
        
        final_days.append({
            "id": f"day-{i}",
            "bs_date": ad_to_bs(date),
            "ad_date": str(date),
            "day_of_week": date.strftime("%A"),
            "is_exam_day": bool(exam_today),
            "status": d_status,
            "subject": selected_subject if selected_subject else "Break/Buffer",
            "tasks": day_tasks
        })

    return {
        "status": "success",
        "days": final_days,
        "summary": { "total_days": len(all_dates), "subjects_covered": list(set(ex['name'] for ex in exams_list)) }
    }

import nepali_datetime
from datetime import datetime, timedelta

def bs_to_ad(bs_date_str):
    y, m, d = map(int, bs_date_str.split('-'))
    np_date = nepali_datetime.date(y, m, d)
    return np_date.to_datetime_date()

def ad_to_bs(ad_date):
    np_date = nepali_datetime.date.from_datetime_date(ad_date)
    return np_date.strftime('%Y-%m-%d')

def get_micro_plan(subject_name, focus_area, daily_hours, session_mins, break_mins, is_exam=False, start_time_str="06:00"):
    """
    Generates a high-precision plan with realistic daily routines (Meals, Buffer, Variety).
    """
    plan = []
    
    if is_exam:
        return [
            {"time": "05:00 - 06:30", "activity": f"Final Formula Polish: {subject_name}", "type": "study", "minutes": 90},
            {"time": "07:00 - 08:00", "activity": "Energy Loading (Breakfast)", "type": "break", "minutes": 60},
            {"time": "10:00 - 13:00", "activity": "OFFICIAL EXAM SESSION", "type": "exam", "minutes": 180},
            {"time": "14:00 - 15:30", "activity": "Post-Exam Recovery & Meal", "type": "full-break", "minutes": 90},
            {"time": "16:00 - 18:00", "activity": "Next Subject Pre-Scan", "type": "study", "minutes": 120}
        ]

    remaining_minutes = daily_hours * 60
    current_time = datetime.strptime(start_time_str, "%H:%M")
    
    accumulated_study = 0
    sessions_count = 0
    
    # Study phases for variety
    phases = ["Deep Work: Concepts", "Active Recall Session", "Past Paper Sprint", "Feynman Technique Review"]
    
    while remaining_minutes > 0:
        # Check for Meal Breaks
        hour = current_time.hour
        if hour == 8 and not any(p['type'] == 'meal' and 'Breakfast' in p['activity'] for p in plan):
            end_time = current_time + timedelta(minutes=45)
            plan.append({"time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", "activity": "Breakfast & Hydration", "type": "meal", "minutes": 45})
            current_time = end_time
            continue
        elif hour == 13 and not any(p['type'] == 'meal' and 'Lunch' in p['activity'] for p in plan):
            end_time = current_time + timedelta(minutes=60)
            plan.append({"time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", "activity": "Lunch & Mindful Rest", "type": "meal", "minutes": 60})
            current_time = end_time
            continue
        elif hour == 20 and not any(p['type'] == 'meal' and 'Dinner' in p['activity'] for p in plan):
            end_time = current_time + timedelta(minutes=60)
            plan.append({"time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}", "activity": "Dinner & Family Time", "type": "meal", "minutes": 60})
            current_time = end_time
            continue

        # Study Session
        duration = min(session_mins, remaining_minutes)
        end_time = current_time + timedelta(minutes=duration)
        phase = phases[sessions_count % len(phases)]
        
        plan.append({
            "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
            "activity": f"{phase}: {focus_area}",
            "type": "study",
            "minutes": duration
        })
        
        remaining_minutes -= duration
        accumulated_study += duration
        sessions_count += 1
        current_time = end_time
        
        if remaining_minutes <= 0: break
        
        # Decide break type: Short or Full Recovery
        if accumulated_study >= 180: # Every 3 hours of study, take a longer reset
            long_break = 60
            end_time = current_time + timedelta(minutes=long_break)
            plan.append({
                "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "activity": "Full Reset (Walk/Nap/Shower)",
                "type": "full-break",
                "minutes": long_break
            })
            accumulated_study = 0
        else:
            duration = break_mins
            end_time = current_time + timedelta(minutes=duration)
            plan.append({
                "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "activity": "Micro-Break (20-20-20 Rule)",
                "type": "break",
                "minutes": duration
            })
        current_time = end_time
        
    # Add Reflection/Buffer at the end
    end_time = current_time + timedelta(minutes=15)
    plan.append({
        "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
        "activity": "Daily Reflection & Tomorrow's Goal",
        "type": "buffer",
        "minutes": 15
    })
            
    return plan

def generate_study_plan(exams_list, daily_study_hours=8, session_mins=90, break_mins=15, start_time="06:00", topic_mastery_map=None):
    """
    v17 Adaptive Planner:
    - Factors in 'topic_mastery_map' { 'Subject': { 'Topic': score } }
    - Mastery < 40 increases repetition frequency.
    - Consistency adjustments based on predicted cognitive load.
    """
    prepared_exams = []
    for ex in exams_list:
        try:
            ad_date = bs_to_ad(ex['date'])
            prepared_exams.append({
                **ex,
                'ad_date': ad_date,
                'chapters': ex.get('chapters', []),
                'difficulty': int(ex.get('difficulty', 2))
            })
        except:
            continue
    
    prepared_exams.sort(key=lambda x: x['ad_date'])
    
    # v17: Use Nepal Time (UTC+5:45) for accurate 'Today'
    nepal_now = datetime.utcnow() + timedelta(hours=5, minutes=45)
    today_ad = nepal_now.date()
    
    last_exam_ad = prepared_exams[-1]['ad_date']
    
    all_dates = []
    temp_date = today_ad
    while temp_date <= last_exam_ad:
        all_dates.append(temp_date)
        temp_date += timedelta(days=1)
    
    final_days = []
    chapter_idx_map = {ex['name']: 0 for ex in prepared_exams}
    subject_day_count = {ex['name']: 0 for ex in prepared_exams}
    exam_map = {ex['ad_date']: ex for ex in prepared_exams}

    for i, date in enumerate(all_dates):
        if date in exam_map:
            ex = exam_map[date]
            if date < today_ad:
                day_status = "completed"
            elif date == today_ad:
                day_status = "today"
            else:
                day_status = "upcoming"

            final_days.append({
                "id": f"day-{i}",
                "bs_date": ad_to_bs(date),
                "ad_date": str(date),
                "is_exam_day": True,
                "status": day_status,
                "subject": ex['name'],
                "tasks": get_micro_plan(ex['name'], "EXAM PREP", daily_study_hours, session_mins, break_mins, is_exam=True, start_time_str=start_time)
            })
            continue

        next_exam = next((ex for ex in prepared_exams if ex['ad_date'] > date), None)
        if not next_exam: continue

        # v17 ADAPTIVE PRIORITY ENGINE
        candidates = []
        for ex in prepared_exams:
            days_left = (ex['ad_date'] - date).days
            if days_left <= 0: continue
            
            # 1. Base proximity weight
            proximity = 100 / (days_left + 0.5)
            
            # 2. Difficulty weight
            diff_weight = 1 + (ex['difficulty'] * 0.3)
            
            # 3. Mastery weight (v17)
            # Higher weight if mastery is low. 
            avg_mastery = 50 
            if topic_mastery_map and ex['name'] in topic_mastery_map:
                scores = list(topic_mastery_map[ex['name']].values())
                if scores: avg_mastery = sum(scores) / len(scores)
            
            mastery_multiplier = 1.0 + ((100 - avg_mastery) / 100.0) 
            
            # 4. Burnout balancing (Reduction if subject was studied 3 days in a row)
            repetition_penalty = 1.0
            if subject_day_count[ex['name']] > 0:
                repetition_penalty = 1.0 / (subject_day_count[ex['name']] * 0.5 + 1)

            score = proximity * diff_weight * mastery_multiplier * repetition_penalty
            candidates.append({"ex": ex, "score": score})
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        study_sub = candidates[0]['ex']
        subject_day_count[study_sub['name']] += 1

        # Topic Selection based on Mastery (Prioritize weak topics)
        chaps = study_sub['chapters']
        weak_topic = None
        if topic_mastery_map and study_sub['name'] in topic_mastery_map:
            # Find topic with lowest mastery
            sorted_topics = sorted(topic_mastery_map[study_sub['name']].items(), key=lambda x: x[1])
            if sorted_topics: weak_topic = sorted_topics[0][0]

        if weak_topic:
            focus_area = weak_topic
        else:
            focus_area = chaps[chapter_idx_map[study_sub['name']] % len(chaps)] if chaps else "Core Systems"
            chapter_idx_map[study_sub['name']] += 1

        # Burnout Prevention Check (Scaling hours based on cumulative fatigue)
        daily_ceiling = 12
        load_factor = sum(subject_day_count.values()) / (i + 1) # Avg study intensity
        adjusted_hours = daily_study_hours
        if load_factor > 0.8: # Sustained high pressure
            adjusted_hours = max(4, daily_study_hours - 1)
        
        if study_sub['difficulty'] == 3: adjusted_hours = min(daily_ceiling, adjusted_hours + 1)

        if date < today_ad:
            day_status = "completed"
        elif date == today_ad:
            day_status = "today"
        else:
            day_status = "upcoming"

        final_days.append({
            "id": f"day-{i}",
            "bs_date": ad_to_bs(date),
            "ad_date": str(date),
            "is_exam_day": False,
            "status": day_status,
            "subject": study_sub['name'],
            "daily_focus": focus_area,
            "mastery_focus": True if weak_topic else False,
            "tasks": get_micro_plan(study_sub['name'], focus_area, adjusted_hours, session_mins, break_mins, start_time_str=start_time)
        })
        
    return {
        "status": "success",
        "days": final_days,
        "summary": { "total_days": len(all_dates), "subjects_covered": list(set(ex['name'] for ex in exams_list)) }
    }


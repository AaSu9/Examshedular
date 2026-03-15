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
        micro_plan = [
            {"time": "05:00 - 06:30", "activity": f"Final Formula Polish: {subject_name}", "type": "study", "minutes": 90},
            {"time": "07:00 - 08:00", "activity": "Energy Loading (Breakfast)", "type": "break", "minutes": 60},
            {"time": "10:00 - 13:00", "activity": "OFFICIAL EXAM SESSION", "type": "exam", "minutes": 180},
            {"time": "14:00 - 15:30", "activity": "Post-Exam Recovery & Meal", "type": "full-break", "minutes": 90},
            {"time": "16:00 - 18:00", "activity": "Next Subject Pre-Scan", "type": "study", "minutes": 120}
        ]
        return micro_plan

    remaining_minutes = float(daily_hours) * 60.0
    session_mins_float = float(session_mins)
    current_time = datetime.strptime(start_time_str, "%H:%M")
    
    accumulated_study = 0.0
    sessions_count = 0
    
    # Study phases for variety
    phases = ["Deep Work: Concepts", "Active Recall Session", "Past Paper Sprint", "Feynman Technique Review"]
    
    while remaining_minutes > 0.0:
        # Check for Meal Breaks
        current_hour = int(current_time.hour)
        if current_hour == 8:
            has_breakfast = False
            for p in plan:
                if p.get('type') == 'meal' and 'Breakfast' in str(p.get('activity', '')):
                    has_breakfast = True
                    break
            if not has_breakfast:
                end_time = current_time + timedelta(minutes=45)
                plan.append({
                    "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                    "activity": "Breakfast & Hydration",
                    "type": "meal",
                    "minutes": 45
                })
                current_time = end_time
                continue
        elif current_hour == 13:
            has_lunch = False
            for p in plan:
                if p.get('type') == 'meal' and 'Lunch' in str(p.get('activity', '')):
                    has_lunch = True
                    break
            if not has_lunch:
                end_time = current_time + timedelta(minutes=60)
                plan.append({
                    "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                    "activity": "Lunch & Mindful Rest",
                    "type": "meal",
                    "minutes": 60
                })
                current_time = end_time
                continue
        elif current_hour == 20:
            has_dinner = False
            for p in plan:
                if p.get('type') == 'meal' and 'Dinner' in str(p.get('activity', '')):
                    has_dinner = True
                    break
            if not has_dinner:
                end_time = current_time + timedelta(minutes=60)
                plan.append({
                    "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                    "activity": "Dinner & Family Time",
                    "type": "meal",
                    "minutes": 60
                })
                current_time = end_time
                continue

        # Study Session
        duration_val = float(min(session_mins_float, remaining_minutes))
        end_time = current_time + timedelta(minutes=duration_val)
        phase = phases[int(sessions_count) % len(phases)]
        
        plan.append({
            "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
            "activity": f"{phase}: {focus_area}",
            "type": "study",
            "minutes": int(duration_val)
        })
        
        remaining_minutes = float(remaining_minutes) - float(duration_val)
        accumulated_study = accumulated_study + duration_val
        sessions_count = sessions_count + 1
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
    
    # Distribution
    subject_total_chaps = {}
    for ex_item in prepared_exams:
        subject_total_chaps[str(ex_item['name'])] = len(ex_item.get('chapters', []))
    
    final_days = []
    chapter_idx_map = {}
    subject_day_count = {}
    for ex_item in prepared_exams:
        chapter_idx_map[str(ex_item['name'])] = 0
        subject_day_count[str(ex_item['name'])] = 0
    
    exam_map = {ex['ad_date']: ex for ex in prepared_exams}

    for i, date in enumerate(all_dates):
        if date in exam_map:
            ex = exam_map[date]
            day_status = "upcoming"
            if date < today_ad: day_status = "completed"
            elif date == today_ad: day_status = "today"

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

        # Find next impending exams
        next_impending = [ex for ex in prepared_exams if ex['ad_date'] > date]
        if not next_impending: continue
        
        # Priority Logic
        candidates = []
        for ex_obj in next_impending:
            if not isinstance(ex_obj, dict): continue
            
            days_left = float((ex_obj['ad_date'] - date).days)
            urgency_score = 1.0 / (days_left + 0.1)
            
            s_name = str(ex_obj.get('name', ''))
            
            # Explicitly guard dict types
            if not isinstance(subject_total_chaps, dict): subject_total_chaps = {}
            if not isinstance(chapter_idx_map, dict): chapter_idx_map = {}
            
            tot_chaps = float(subject_total_chaps.get(s_name, 1.0))
            done_chaps = float(chapter_idx_map.get(s_name, 0.0))
            rem_chaps = max(1.0, tot_chaps - done_chaps)
            cov_score = rem_chaps / tot_chaps
            
            diff_score = 1.0 + (float(ex_obj.get('difficulty', 2)) * 0.2)
            
            mast_score = 1.5 # Default mastery weight
            if isinstance(topic_mastery_map, dict) and s_name in topic_mastery_map:
                m_data = topic_mastery_map[s_name]
                if isinstance(m_data, dict) and m_data:
                    avg_m = sum([float(v) for v in m_data.values()]) / len(m_data)
                    mast_score = 1.0 + ((100.0 - avg_m) / 100.0)
            
            final_score = urgency_score * cov_score * diff_score * mast_score
            
            if float(subject_day_count.get(s_name, 0.0)) > 2.0:
                final_score *= 0.5
            
            candidates.append({"ex": ex_obj, "score": final_score})
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best_ex = candidates[0]['ex']
        best_name = str(best_ex.get('name', ''))
        subject_day_count[best_name] = int(subject_day_count.get(best_name, 0)) + 1
        
        for k in list(subject_day_count.keys()):
            if k != best_name: subject_day_count[k] = 0

        # Topic Selection
        study_chaps = list(best_ex.get('chapters', []))
        f_area = "Fundamental Concepts"
        
        if isinstance(topic_mastery_map, dict) and best_name in topic_mastery_map:
            m_data = topic_mastery_map[best_name]
            if isinstance(m_data, dict) and m_data:
                low_topic = sorted(m_data.items(), key=lambda x: x[1])[0]
                if float(low_topic[1]) < 40.0:
                    f_area = str(low_topic[0])
                elif study_chaps:
                    c_idx = int(chapter_idx_map.get(best_name, 0))
                    f_area = str(study_chaps[c_idx % len(study_chaps)])
                    chapter_idx_map[best_name] = c_idx + 1
        elif study_chaps:
            c_idx = int(chapter_idx_map.get(best_name, 0))
            f_area = str(study_chaps[c_idx % len(study_chaps)])
            chapter_idx_map[best_name] = c_idx + 1

        d_status = "upcoming"
        if date < today_ad: d_status = "completed"
        elif date == today_ad: d_status = "today"

        # Hours Weighting
        w_hours = float(daily_study_hours)
        b_diff = int(best_ex.get('difficulty', 2))
        if b_diff == 3: w_hours *= 1.5
        elif b_diff == 1: w_hours *= 0.7
        w_hours = min(14.0, w_hours)

        final_days.append({
            "id": f"day-{i}",
            "bs_date": ad_to_bs(date),
            "ad_date": str(date),
            "is_exam_day": False,
            "status": d_status,
            "subject": best_name,
            "daily_focus": f_area,
            "tasks": get_micro_plan(best_name, f_area, w_hours, session_mins, break_mins, start_time_str=start_time)
        })
        
    return {
        "status": "success",
        "days": final_days,
        "summary": { "total_days": len(all_dates), "subjects_covered": list(set(ex['name'] for ex in exams_list)) }
    }


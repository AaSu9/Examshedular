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

def get_micro_plan(subject_name: str, focus_area: str, daily_hours: float, session_mins: float, break_mins: float, is_exam: bool = False, start_time_str: str = "06:00"):
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

    remaining_minutes: float = float(daily_hours) * 60.0
    session_mins_float: float = float(session_mins)
    current_time = datetime.strptime(start_time_str, "%H:%M")
    
    accumulated_study: float = 0.0
    sessions_count: int = 0
    
    phases = ["Deep Work: Concepts", "Active Recall Session", "Past Paper Sprint", "Feynman Technique Review"]
    
    while float(remaining_minutes) > 0.0:
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

        duration_val = float(min(float(session_mins_float), float(remaining_minutes)))
        end_time = current_time + timedelta(minutes=duration_val)
        phase = phases[int(sessions_count) % len(phases)]
        
        plan.append({
            "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
            "activity": f"{phase}: {focus_area}",
            "type": "study",
            "minutes": int(duration_val)
        })
        
        remaining_minutes -= duration_val
        accumulated_study += duration_val
        sessions_count += 1
        current_time = end_time
        
        if remaining_minutes <= 0: break
        
        if accumulated_study >= 180.0:
            long_break = 60
            end_time = current_time + timedelta(minutes=long_break)
            plan.append({
                "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "activity": "Full Reset (Walk/Nap/Shower)",
                "type": "full-break",
                "minutes": long_break
            })
            accumulated_study = 0.0
            current_time = end_time
        else:
            duration_break = float(break_mins)
            end_time = current_time + timedelta(minutes=duration_break)
            plan.append({
                "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "activity": "Micro-Break (20-20-20 Rule)",
                "type": "break",
                "minutes": int(duration_break)
            })
            current_time = end_time
        
    end_time = current_time + timedelta(minutes=15)
    plan.append({
        "time": f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
        "activity": "Daily Reflection & Tomorrow's Goal",
        "type": "buffer",
        "minutes": 15
    })
    return plan

def generate_study_plan(exams_list: List[Dict], daily_study_hours: float = 8.0, session_mins: float = 90.0, break_mins: float = 15.0, start_time: str = "06:00", topic_mastery_map: Optional[Dict] = None):
    prepared_exams = []
    for ex in exams_list:
        try:
            # Detect if it's a Nepali BS date (Bikram Sambat)
            date_str = str(ex['date']).replace('/', '-')
            year = int(date_str.split('-')[0])
            if year > 2060:
                ad_date = bs_to_ad(date_str)
            else:
                ad_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            prepared_exams.append({
                **ex,
                'ad_date': ad_date,
                'chapters': ex.get('chapters', []),
                'difficulty': int(ex.get('difficulty', 2))
            })
        except:
            continue
    
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
    
    subject_total_chaps = {}
    chapter_idx_map: Dict[str, Any] = {}
    subject_day_count = {}
    subject_total_allocated = {}
    
    for ex_item in prepared_exams:
        s_name = str(ex_item['name'])
        subject_total_chaps[s_name] = len(ex_item.get('chapters', []))
        chapter_idx_map[s_name] = 0
        subject_day_count[s_name] = 0
        subject_total_allocated[s_name] = 0
    
    exam_map = {ex['ad_date']: ex for ex in prepared_exams}
    final_days = []

    for i, date in enumerate(all_dates):
        if date in exam_map:
            ex = exam_map[date]
            d_st = "today" if date == today_ad else "upcoming"
            
            effective_start_time = start_time
            if d_st == "today":
                now_time = datetime.now()
                start_dt = datetime.strptime(start_time, "%H:%M")
                if now_time.time() > start_dt.time():
                    next_hour = now_time.hour + 1 if now_time.minute > 0 else now_time.hour
                    if next_hour >= 23: next_hour = 22
                    effective_start_time = f"{next_hour:02d}:00"
                    
            final_days.append({
                "id": f"day-{i}",
                "bs_date": ad_to_bs(date),
                "ad_date": str(date),
                "is_exam_day": True,
                "status": d_st,
                "subject": ex['name'],
                "tasks": get_micro_plan(ex['name'], "EXAM PREP", daily_study_hours, session_mins, break_mins, is_exam=True, start_time_str=effective_start_time)
            })
            continue

        next_exams = [e for e in prepared_exams if e['ad_date'] > date]
        if not next_exams: continue
        
        candidates = []
        for ex_obj in next_exams:
            s_name = str(ex_obj.get('name', ''))
            days_left = float((ex_obj['ad_date'] - date).days)
            urgency = 1.0 / (days_left + 1.5)
            
            tot = float(subject_total_chaps.get(s_name, 1.0))
            done = float(chapter_idx_map.get(s_name, 0.0))
            cov = max(1.0, tot - done) / tot
            
            # Boosted difficulty multiplier to ensure difficult subjects get more days
            diff = 1.0 + (float(ex_obj.get('difficulty', 2)) * 0.8)
            mast = 1.5
            if topic_mastery_map and s_name in topic_mastery_map:
                m_data = topic_mastery_map[s_name]
                if m_data:
                    avg_m = sum([float(v) for v in m_data.values()]) / len(m_data)
                    mast = 1.0 + ((100.0 - avg_m) / 100.0)
            
            alloc_pen = 1.0 / (float(subject_total_allocated.get(s_name, 0)) + 1.0)
            score = urgency * cov * diff * mast * alloc_pen
            if float(subject_day_count.get(s_name, 0)) >= 2.0: score *= 0.1
            candidates.append({"ex": ex_obj, "score": score})
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best_ex = candidates[0]['ex']
        best_name = str(best_ex.get('name', ''))
        subject_day_count[best_name] = int(subject_day_count.get(best_name, 0)) + 1
        subject_total_allocated[best_name] = int(subject_total_allocated.get(best_name, 0)) + 1
        for k in list(subject_day_count.keys()):
            if k != best_name: subject_day_count[k] = 0

        study_chaps = list(best_ex.get('chapters', []))
        f_area = "Fundamental Concepts"
        
        if topic_mastery_map and best_name in topic_mastery_map:
            m_data = topic_mastery_map[best_name]
            if m_data:
                low_topic = sorted(m_data.items(), key=lambda x: x[1])[0]
                if float(low_topic[1]) < 40.0:
                    f_area = str(low_topic[0])
                elif study_chaps:
                    c_idx = int(chapter_idx_map.get(best_name, 0))
                    f_area = str(study_chaps[c_idx % len(study_chaps)])
                    chapter_idx_map[best_name] = c_idx + 1
        elif study_chaps:
            c_idx_ext = int(chapter_idx_map.get(best_name, 0))
            f_area = str(study_chaps[c_idx_ext % len(study_chaps)])
            chapter_idx_map[best_name] = c_idx_ext + 1

        d_status = "today" if date == today_ad else "upcoming"
        
        effective_start_time = start_time
        if d_status == "today":
            now_time = datetime.now()
            start_dt = datetime.strptime(start_time, "%H:%M")
            if now_time.time() > start_dt.time():
                next_hour = now_time.hour + 1 if now_time.minute > 0 else now_time.hour
                if next_hour >= 23: next_hour = 22
                effective_start_time = f"{next_hour:02d}:00"
                
        w_hours = float(daily_study_hours)
        b_diff = int(best_ex.get('difficulty', 2))
        if b_diff == 3: w_hours *= 1.5
        w_hours = min(14.0, w_hours)

        if d_status == "today" and effective_start_time != start_time:
            # Adjust today's available study hours based on the later start time
            start_h = int(effective_start_time.split(':')[0])
            w_hours = max(2.0, min(w_hours, float(24 - start_h)))

        final_days.append({
            "id": f"day-{i}",
            "bs_date": ad_to_bs(date),
            "ad_date": str(date),
            "is_exam_day": False,
            "status": d_status,
            "subject": best_name,
            "daily_focus": f_area,
            "tasks": get_micro_plan(best_name, f_area, w_hours, session_mins, break_mins, start_time_str=effective_start_time)
        })
        
    return {
        "status": "success",
        "days": final_days,
        "summary": { "total_days": len(all_dates), "subjects_covered": list(set(ex['name'] for ex in exams_list)) }
    }

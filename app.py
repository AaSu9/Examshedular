from flask import Flask, render_template, request, jsonify
from planner import generate_study_plan
from syllabus_db import get_all_metadata, get_chapters
import nepali_datetime
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    # Return available selections from SQLite
    data = get_all_metadata()
    # Add Current BS Date for defaults
    now = datetime.now()
    try:
        np_now = nepali_datetime.date.from_datetime_date(now.date())
        data['today_bs'] = np_now.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Date conversion error: {e}")
        data['today_bs'] = "2082-09-05" # Modernized fallback to current period
    return jsonify(data)

@app.route('/api/generate-schedule', methods=['POST'])
def generate_schedule():
    try:
        data = request.json
        exams = data.get('exams', [])
        
        # Automatic Syllabus injection if not provided
        univ = data.get('university')
        fac = data.get('faculty')
        course = data.get('course')
        sem = data.get('semester')

        for ex in exams:
            if not ex.get('chapters') or len(ex['chapters']) == 0:
                ex['chapters'] = get_chapters(univ, fac, course, sem, ex['name'])
        
        total_hours = int(data.get('daily_hours', 8))
        session_mins = int(data.get('session_mins', 90))
        break_mins = int(data.get('break_mins', 15))
        start_time = data.get('start_time', "06:00")
        
        if not exams:
            return jsonify({"error": "No exams provided"}), 400
        
        schedule = generate_study_plan(
            exams, 
            daily_study_hours=total_hours,
            session_mins=session_mins,
            break_mins=break_mins,
            start_time=start_time
        )
        return jsonify(schedule)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/replan-day', methods=['POST'])
def replan_day():
    try:
        from planner import get_micro_plan
        data = request.json
        subject = data.get('subject')
        focus = data.get('focus', 'Revision')
        hours = int(data.get('hours', 8))
        session_mins = int(data.get('session_mins', 90))
        break_mins = int(data.get('break_mins', 15))
        start_time = data.get('start_time', "06:00")
        
        # Mark as holiday if hours <= 0
        if hours <= 0:
            return jsonify({"tasks": [{"time": "00:00 - 23:59", "activity": "HOLIDAY / REST DAY", "type": "break", "minutes": 1440}]})

        tasks = get_micro_plan(subject, focus, hours, session_mins, break_mins, start_time_str=start_time)
        return jsonify({"tasks": tasks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from planner import generate_study_plan
from syllabus_db import get_all_metadata, get_chapters, get_db_connection
import nepali_datetime
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # Random key for sessions

@app.route('/')
def index():
    return render_template('index.html')

# --- AUTH ROUTES ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing fields"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        existing = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            return jsonify({"error": "Username already taken"}), 400
            
        hashed_pw = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Account created! You can now login."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({"success": True, "user": {"username": user['username']}})
            
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "username": session.get('username')})
    return jsonify({"logged_in": False})

# --- DATA SYNC ROUTES ---
@app.route('/api/sync/schedules', methods=['GET'])
def get_schedules():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    rows = conn.execute('SELECT name, data, inputs FROM saved_schedules WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    
    schedules = []
    for row in rows:
        schedules.append({
            "name": row['name'],
            "data": json.loads(row['data']),
            "inputs": json.loads(row['inputs']) if row['inputs'] else {}
        })
    return jsonify(schedules)

@app.route('/api/sync/save', methods=['POST'])
def save_schedule():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    name = data.get('name')
    schedule_data = data.get('data')
    wizard_inputs = data.get('inputs')
    
    conn = get_db_connection()
    # Check if schedule with this name exists for this user (overwrite)
    existing = conn.execute('SELECT id FROM saved_schedules WHERE user_id = ? AND name = ?', (session['user_id'], name)).fetchone()
    
    if existing:
        conn.execute('UPDATE saved_schedules SET data = ?, inputs = ? WHERE id = ?', 
                     (json.dumps(schedule_data), json.dumps(wizard_inputs), existing['id']))
    else:
        conn.execute('INSERT INTO saved_schedules (user_id, name, data, inputs) VALUES (?, ?, ?, ?)', 
                     (session['user_id'], name, json.dumps(schedule_data), json.dumps(wizard_inputs)))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/sync/delete', methods=['POST'])
def delete_schedule():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    name = request.json.get('name')
    conn = get_db_connection()
    conn.execute('DELETE FROM saved_schedules WHERE user_id = ? AND name = ?', (session['user_id'], name))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

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

@app.route('/admin')
def admin_portal():
    # Only 'admin' user can access
    if 'user_id' not in session or session.get('username') != 'admin':
        return "Access Revoked: Imperial Clearance required.", 403
        
    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.id, u.username, u.created_at, COUNT(s.id) as timeline_count 
        FROM users u 
        LEFT JOIN saved_schedules s ON u.id = s.user_id 
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

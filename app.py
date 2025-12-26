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
    
    # v17: Use Nepal Time for dynamic status updates
    nepal_now = datetime.utcnow() + timedelta(hours=5, minutes=45)
    today_ad_str = nepal_now.date().strftime("%Y-%m-%d")

    schedules = []
    for row in rows:
        sch_data = json.loads(row['data'])
        
        # Legacy Patch: Inject ad_date if missing
        if 'days' in sch_data:
            for day in sch_data['days']:
                if 'ad_date' not in day and 'bs_date' in day:
                    try:
                        # Convert BS string "2082-01-01" to AD
                        y, m, d = map(int, day['bs_date'].split('-'))
                        import nepali_datetime
                        np_date = nepali_datetime.date(y, m, d)
                        day['ad_date'] = str(np_date.to_datetime_date())
                    except:
                        pass
                
                # Update Status on the fly based on ad_date
                try:
                    if 'ad_date' in day:
                        if day['ad_date'] < today_ad_str:
                            day['status'] = 'completed'
                        elif day['ad_date'] == today_ad_str:
                            day['status'] = 'today'
                        else:
                            day['status'] = 'upcoming'
                except Exception as e:
                    print(f"Status update error: {e}")

        schedules.append({
            "name": row['name'],
            "data": sch_data,
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

        # v17: Fetch Topic Mastery for Adaptive Planning
        topic_mastery_map = {}
        if 'user_id' in session:
            conn = get_db_connection()
            mastery_data = conn.execute('SELECT subject, topic, mastery_score FROM topic_mastery WHERE user_id = ?', (session['user_id'],)).fetchall()
            conn.close()
            for m in mastery_data:
                if m['subject'] not in topic_mastery_map:
                    topic_mastery_map[m['subject']] = {}
                topic_mastery_map[m['subject']][m['topic']] = m['mastery_score']
        
        schedule = generate_study_plan(
            exams, 
            daily_study_hours=total_hours,
            session_mins=session_mins,
            break_mins=break_mins,
            start_time=start_time,
            topic_mastery_map=topic_mastery_map
        )
        return jsonify(schedule)
    except Exception as e:
        import traceback
        traceback.print_exc()
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
    # Only 'Aashish Ghimire' user can access
    if 'user_id' not in session or session.get('username') != 'Aashish Ghimire':
        return "Access Revoked: Imperial Clearance required for Commander Aashish.", 403
        
    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.id, u.username, u.created_at, COUNT(s.id) as timeline_count 
        FROM users u 
        LEFT JOIN saved_schedules s ON u.id = s.user_id 
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''').fetchall()
    
    # Global Metrics
    stats = conn.execute('SELECT COUNT(*) FROM saved_schedules').fetchone()[0]
    conn.close()
    return render_template('admin.html', users=users, total_schedules=stats)

@app.route('/admin/api/reset-password', methods=['POST'])
def admin_reset_password():
    if 'user_id' not in session or session.get('username') != 'Aashish Ghimire':
        return jsonify({"error": "Forbidden"}), 403
    
    target_id = request.json.get('user_id')
    new_password = request.json.get('new_password')
    if not target_id or not new_password:
        return jsonify({"error": "Missing parameters"}), 400
        
    from werkzeug.security import generate_password_hash
    hashed = generate_password_hash(new_password)
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, target_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/admin/api/delete-user', methods=['POST'])
def admin_delete_user():
    if 'user_id' not in session or session.get('username') != 'Aashish Ghimire':
        return jsonify({"error": "Forbidden"}), 403
    
    target_id = request.json.get('user_id')
    if not target_id:
        return jsonify({"error": "No ID provided"}), 400
        
    conn = get_db_connection()
    # Delete schedules first (FFK)
    conn.execute('DELETE FROM saved_schedules WHERE user_id = ?', (target_id,))
    # Delete user
    conn.execute('DELETE FROM users WHERE id = ?', (target_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/v17/log-session', methods=['POST'])
def log_session_v17():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    uid = session['user_id']
    sub = data.get('subject')
    topic = data.get('topic')
    score = data.get('focus_score', 100)
    
    conn = get_db_connection()
    # 1. Log session stats
    conn.execute('''
        INSERT INTO session_stats (user_id, subject, topic, duration_mins, focus_score, distraction_count, idle_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (uid, sub, topic, data.get('duration_mins'), score, data.get('distractions'), data.get('idle_seconds')))
    
    # 2. Update Mastery (Simple linear growth based on focus score)
    # If focus score is high, mastery increases faster.
    mastery_gain = 5 if score > 80 else (2 if score > 50 else 0)
    
    # Check if topic exists
    existing = conn.execute('SELECT mastery_score FROM topic_mastery WHERE user_id = ? AND subject = ? AND topic = ?', (uid, sub, topic)).fetchone()
    
    if existing:
        new_mastery = min(100, existing[0] + mastery_gain)
        conn.execute('UPDATE topic_mastery SET mastery_score = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ? AND subject = ? AND topic = ?', 
                     (new_mastery, uid, sub, topic))
    else:
        conn.execute('INSERT INTO topic_mastery (user_id, subject, topic, mastery_score) VALUES (?, ?, ?, ?)', 
                     (uid, sub, topic, mastery_gain))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "mastery_gain": mastery_gain})

@app.route('/api/v17/analytics', methods=['GET'])
def get_analytics_v17():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    uid = session['user_id']
    conn = get_db_connection()
    
    # 1. Focus Score Avg
    focus_data = conn.execute('SELECT AVG(focus_score) FROM session_stats WHERE user_id = ?', (uid,)).fetchone()
    avg_focus = focus_data[0] if focus_data[0] else 0
    
    # 2. Burnout Risk (Based on session count in last 7 days)
    recent_count = conn.execute('SELECT COUNT(*) FROM session_stats WHERE user_id = ? AND timestamp > datetime("now", "-7 days")', (uid,)).fetchone()[0]
    burnout = "LOW"
    if recent_count > 20: burnout = "HIGH"
    elif recent_count > 12: burnout = "MED"
    
    # 3. Mastery Map
    mastery_rows = conn.execute('SELECT subject, topic, mastery_score FROM topic_mastery WHERE user_id = ?', (uid,)).fetchall()
    mastery_map = {}
    for r in mastery_rows:
        if r['subject'] not in mastery_map:
            mastery_map[r['subject']] = {}
        mastery_map[r['subject']][r['topic']] = r['mastery_score']
        
    conn.close()
    return jsonify({
        "avg_focus": avg_focus,
        "burnout_risk": burnout,
        "mastery": mastery_map
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

 #   - - -   G A M I F I C A T I O N   &   S O C I A L   A P I   ( v 1 7   R e f i n e d )   - - - 
 
 @ a p p . r o u t e ( ' / a p i / v 1 7 / s y n c - x p ' ,   m e t h o d s = [ ' P O S T ' ] ) 
 d e f   s y n c _ x p ( ) : 
         i f   ' u s e r _ i d '   n o t   i n   s e s s i o n : 
                 r e t u r n   j s o n i f y ( { ' e r r o r ' :   ' U n a u t h o r i z e d ' } ) ,   4 0 1 
         
         d a t a   =   r e q u e s t . j s o n 
         x p   =   d a t a . g e t ( ' x p ' ,   0 ) 
         s t r e a k   =   d a t a . g e t ( ' s t r e a k ' ,   0 ) 
         
         c o n n   =   g e t _ d b _ c o n n e c t i o n ( ) 
         c o n n . e x e c u t e ( ' U P D A T E   u s e r s   S E T   x p   =   ? ,   s t r e a k   =   ?   W H E R E   i d   =   ? ' ,   ( x p ,   s t r e a k ,   s e s s i o n [ ' u s e r _ i d ' ] ) ) 
         c o n n . c o m m i t ( ) 
         c o n n . c l o s e ( ) 
         r e t u r n   j s o n i f y ( { ' s u c c e s s ' :   T r u e } ) 
 
 @ a p p . r o u t e ( ' / a p i / v 1 7 / l e a d e r b o a r d ' ,   m e t h o d s = [ ' G E T ' ] ) 
 d e f   g e t _ l e a d e r b o a r d ( ) : 
         c o n n   =   g e t _ d b _ c o n n e c t i o n ( ) 
         #   G e t   T o p   1 0   U s e r s   b y   X P 
         t o p _ u s e r s   =   c o n n . e x e c u t e ( ' S E L E C T   u s e r n a m e ,   x p ,   s t r e a k ,   a v a t a r ,   i s _ p r o   F R O M   u s e r s   O R D E R   B Y   x p   D E S C   L I M I T   1 0 ' ) . f e t c h a l l ( ) 
         
         #   G e t   C u r r e n t   U s e r   R a n k 
         u s e r _ r a n k   =   - 1 
         i f   ' u s e r _ i d '   i n   s e s s i o n : 
                 #   H a n d l e   c a s e   w h e r e   u s e r   m i g h t   n o t   e x i s t   o r   X P   i s   n u l l 
                 t r y : 
                           r a n k _ q u e r y   =   c o n n . e x e c u t e ( ' S E L E C T   C O U N T ( * )   F R O M   u s e r s   W H E R E   x p   >   ( S E L E C T   x p   F R O M   u s e r s   W H E R E   i d   =   ? ) ' ,   ( s e s s i o n [ ' u s e r _ i d ' ] , ) ) . f e t c h o n e ( ) 
                           u s e r _ r a n k   =   r a n k _ q u e r y [ 0 ]   +   1 
                 e x c e p t : 
                           p a s s 
 
         c o n n . c l o s e ( ) 
         
         l e a d e r b o a r d   =   [ ] 
         f o r   u   i n   t o p _ u s e r s : 
                 l e a d e r b o a r d . a p p e n d ( { 
                         ' u s e r n a m e ' :   u [ ' u s e r n a m e ' ] , 
                         ' x p ' :   u [ ' x p ' ] , 
                         ' s t r e a k ' :   u [ ' s t r e a k ' ] , 
                         ' a v a t a r ' :   u [ ' a v a t a r ' ] , 
                         ' i s _ p r o ' :   b o o l ( u [ ' i s _ p r o ' ] ) 
                 } ) 
                 
         r e t u r n   j s o n i f y ( { 
                 ' l e a d e r b o a r d ' :   l e a d e r b o a r d , 
                 ' u s e r _ r a n k ' :   u s e r _ r a n k 
         } ) 
  
 
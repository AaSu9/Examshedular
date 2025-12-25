// STATE
let db = {};
let selectedSubjects = [];
let timerInterval = null;
let secondsRemaining = 5400; // Default 90m
let totalSecondsInSession = 5400;
let focusModeActive = false;
let completedDays = JSON.parse(localStorage.getItem('padsala_completed_days') || "[]");
let focusXP = parseInt(localStorage.getItem('padsala_xp') || "0");
let concentrationStreak = parseInt(localStorage.getItem('padsala_streak') || "0");
let savedSchedules = JSON.parse(localStorage.getItem('padsala_saved_schedules') || "[]");
let currentSchedule = null;
let wizardInputs = JSON.parse(localStorage.getItem('padsala_wizard_inputs') || "{}");
let isLoggedIn = false;
let currentUsername = "";

const RANKS = [
    { min: 0, title: "INITIATE" },
    { min: 500, title: "ADEPT" },
    { min: 2000, title: "SCHOLAR" },
    { min: 5000, title: "ARCHITECT" },
    { min: 10000, title: "GRANDMASTER" }
];

// NAVIGATION
function switchView(view) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

    document.getElementById(`view-${view}`).classList.add('active');
    document.getElementById(`nav-${view}`).classList.add('active');

    // Special logic for Dashboard
    if (view === 'dashboard' && currentSchedule) {
        renderBlueprint(currentSchedule);
    }
}

// STEP NAVIGATION
function initiateNewProtocol() {
    selectedSubjects = [];
    document.getElementById('schedule-name').value = "";
    document.getElementById('subject-selection-zone').style.display = 'none';

    // Repopulate base dropdown
    populateDropdown('select-university', Object.keys(db));

    navigateTo(2);
}

function navigateTo(step) {
    document.querySelectorAll('.step-container').forEach(el => el.classList.remove('active'));
    document.getElementById(`step-${step}`).classList.add('active');

    document.querySelectorAll('.step-indicator').forEach((el, idx) => {
        if (idx + 1 <= step) el.classList.add('active');
        else el.classList.remove('active');
    });
}

// DATA INIT
async function initWizard() {
    try {
        // 1. Check Auth Status
        const authRes = await fetch('/api/auth/status');
        const authData = await authRes.json();
        isLoggedIn = authData.logged_in;
        if (isLoggedIn) {
            currentUsername = authData.username;
            updateAuthUI();
            await syncSchedules(); // Pull from server
        }

        const res = await fetch('/api/metadata');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        db = await res.json();

        // Always ensure dropdowns are ready for a new plan
        populateDropdown('select-university', Object.keys(db));

        // Initial View Determination
        if (savedSchedules.length > 0) {
            currentSchedule = savedSchedules[0];
            renderGallery();
            renderBlueprint(currentSchedule);
            // Land on Dashboard only if there's no "current session" in Home
            // But let them stay on Home for the "System Ready" feel
            switchView('home');
        } else {
            populateDropdown('select-university', Object.keys(db));
            switchView('home');
        }
    } catch (e) {
        console.error("Sync Failed", e);
    }
}

function populateDropdown(id, items) {
    const el = document.getElementById(id);
    if (!el) {
        console.error(`Element with id '${id}' not found!`);
        return;
    }
    if (!items || items.length === 0) {
        el.innerHTML = '<option value="">No options available</option>';
        return;
    }
    el.innerHTML = '<option value="">Select Option</option>' + items.map(i => `<option value="${i}">${i}</option>`).join('');
    console.log(`Populated ${id} with ${items.length} items`);
}

function updateFaculties() {
    const u = document.getElementById('select-university').value;
    populateDropdown('select-faculty', Object.keys(db[u] || {}));
    updateCourses();
}
function updateCourses() {
    const u = document.getElementById('select-university').value;
    const f = document.getElementById('select-faculty').value;
    populateDropdown('select-course', Object.keys(db[u]?.[f] || {}));
    updateSemesters();
}
function updateSemesters() {
    const u = document.getElementById('select-university').value;
    const f = document.getElementById('select-faculty').value;
    const c = document.getElementById('select-course').value;
    const filtered = Object.keys(db[u]?.[f]?.[c] || {}).filter(s => !s.startsWith('Elective'));
    populateDropdown('select-semester', filtered);
    updateSubjects();
}

function updateSubjects() {
    const u = document.getElementById('select-university').value;
    const f = document.getElementById('select-faculty').value;
    const c = document.getElementById('select-course').value;
    const s = document.getElementById('select-semester').value;

    if (u && f && c && s && db[u]?.[f]?.[c]?.[s]) {
        document.getElementById('subject-selection-zone').style.display = 'block';
        const subjects = Object.keys(db[u][f][c][s]);
        document.getElementById('subjects-grid').innerHTML = subjects.map(name => `
            <div class="glass-card" style="padding: 1rem; cursor: pointer; border: 1px solid ${selectedSubjects.includes(name) ? '#8b5cf6' : 'rgba(255,255,255,0.1)'}" onclick="toggleSubject(this, '${name}')">
                <span style="font-weight: 600;">${name}</span>
            </div>
        `).join('');
    }
}

function toggleSubject(el, name) {
    if (selectedSubjects.includes(name)) selectedSubjects = selectedSubjects.filter(s => s !== name);
    else selectedSubjects.push(name);
    updateSubjects();
}

function prepareDateInputs() {
    navigateTo(3);
    const container = document.getElementById('exam-date-inputs');
    container.innerHTML = selectedSubjects.map(s => `
        <div class="glass-card" style="padding: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
            <span style="font-weight: 700;">${s}</span>
            <input type="text" class="exam-date-input" data-subject="${s}" value="2082-09-15" style="width: 200px;">
        </div>
    `).join('');
}

async function generateSchedule() {
    const exams = Array.from(document.querySelectorAll('.exam-date-input')).map(i => ({
        name: i.dataset.subject,
        date: i.value,
        difficulty: 2
    }));

    try {
        const inputs = {
            university: document.getElementById('select-university').value,
            faculty: document.getElementById('select-faculty').value,
            course: document.getElementById('select-course').value,
            semester: document.getElementById('select-semester').value,
            daily_hours: document.getElementById('daily-hours').value,
            session_mins: document.getElementById('session-duration').value,
            break_mins: document.getElementById('break-duration').value,
            start_time: document.getElementById('start-time').value,
            exams: exams
        };

        const res = await fetch('/api/generate-schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(inputs)
        });
        const data = await res.json();

        // PERSIST MULTIPLE
        const name = document.getElementById('schedule-name').value || `Timeline ${savedSchedules.length + 1}`;
        const newEntry = { name, data, inputs };

        savedSchedules.push(newEntry);
        localStorage.setItem('padsala_saved_schedules', JSON.stringify(savedSchedules));

        currentSchedule = data;
        wizardInputs = inputs;

        renderGallery();
        renderBlueprint(data);
        switchView('dashboard');
    } catch (e) { alert("Compute Error"); }
}

function renderGallery() {
    const gallery = document.getElementById('timeline-gallery');
    if (!gallery) return;
    gallery.innerHTML = savedSchedules.map((s, idx) => `
        <div class="gallery-item ${currentSchedule === s.data ? 'active' : ''}" 
             onclick="loadTimeline(${idx})">
            <i data-lucide="layout-template" style="width: 14px;"></i>
            ${s.name}
        </div>
    `).join('');

    if (savedSchedules.length < 5) {
        gallery.innerHTML += `
            <div class="gallery-item" onclick="switchView('home')" 
                 style="border: 1px dashed var(--primary); color: var(--primary); opacity: 0.8;">
                <i data-lucide="plus-circle" style="width: 14px;"></i>
                New Plan
            </div>
        `;
    }
    lucide.createIcons();
}

function loadTimeline(idx) {
    currentSchedule = savedSchedules[idx].data;
    wizardInputs = savedSchedules[idx].inputs;
    renderGallery();
    renderBlueprint(currentSchedule);
}

function resetPlan() {
    if (confirm("Delete this specific timeline?")) {
        savedSchedules = savedSchedules.filter(s => s.data !== currentSchedule);
        localStorage.setItem('padsala_saved_schedules', JSON.stringify(savedSchedules));
        if (savedSchedules.length > 0) {
            loadTimeline(0);
        } else {
            location.reload();
        }
    }
}

function renderBlueprint(data) {
    // Both containers
    const dashContainer = document.getElementById('blueprint-content');
    const homeContainer = document.getElementById('home-blueprint-content');

    let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
            <h2>Master Timeline</h2>
            <button class="control-btn" onclick="resetPlan()" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.2)">
                <i data-lucide="refresh-cw"></i> Reset Protocol
            </button>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 2rem;">`;

    data.days.forEach((day, idx) => {
        const isHoliday = day.tasks.length === 1 && day.tasks[0].activity.includes("HOLIDAY");
        const isCompleted = day.status === 'completed';
        const isToday = day.status === 'today';

        // Dynamic Border Calculation
        let borderColor = 'rgba(255,255,255,0.1)';
        if (day.is_exam_day) borderColor = '#ef4444';
        else if (isToday) borderColor = 'var(--primary)';

        // Opacity for past days
        const cardStyle = `padding: 2rem; border-color: ${borderColor}; ${isCompleted ? 'opacity: 0.5; filter: grayscale(1);' : ''} ${isToday ? 'box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);' : ''}`;

        html += `
        <div class="glass-card" style="${cardStyle}">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <span style="opacity: 0.7;">${day.bs_date}</span>
                    ${isCompleted ? '<span style="font-size: 0.7rem; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;">DONE</span>' : ''}
                    ${isToday ? '<span style="font-size: 0.7rem; background: var(--primary); color: white; padding: 2px 6px; border-radius: 4px;">TODAY</span>' : ''}
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    ${!isCompleted ? `<button class="control-btn" style="padding: 4px 8px; font-size: 0.7rem; height: auto;" onclick="editDayHours(${idx})">
                        <i data-lucide="clock" style="width: 12px; height: 12px;"></i> Adjust
                    </button>` : ''}
                    <span style="font-weight: 700; color: #a78bfa;">${day.subject}</span>
                </div>
            </div>
            <h3 style="margin-bottom: 1.5rem;">${day.daily_focus || 'Focus Session'}</h3>
            <div id="day-tasks-${idx}">
                ${day.tasks.map(t => `
                    <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; ${isHoliday || isCompleted ? 'opacity: 0.7' : 'cursor: pointer;'}" 
                         ${!isHoliday && !isCompleted ? `onclick="enterFocus('${day.subject}', '${t.activity.replace(/'/g, "\\'")}', ${t.minutes})"` : ''}>
                        <span style="color: #d946ef; font-weight: 700; margin-right: 1rem;">${t.time}</span>
                        ${t.activity}
                    </div>
                `).join('')}
            </div>
        </div>`;
    });
    html += `</div>`;
    dashContainer.innerHTML = html;
    if (homeContainer) homeContainer.innerHTML = html;
    lucide.createIcons();
}

let currentEditingDayIdx = null;

function openAdjustModal(dayIdx) {
    currentEditingDayIdx = dayIdx;
    const day = currentSchedule.days[dayIdx];

    // Set initial values
    document.getElementById('adjust-hours-range').value = 8;
    document.getElementById('label-hours-val').innerText = "8 Hours";
    document.getElementById('adjust-start-time').value = wizardInputs.start_time || "06:00";

    document.getElementById('adjust-modal').classList.add('active');
}

function closeAdjustModal() {
    document.getElementById('adjust-modal').classList.remove('active');
    currentEditingDayIdx = null;
}

document.getElementById('btn-save-adjust').onclick = async () => {
    if (currentEditingDayIdx === null) return;

    const h = parseInt(document.getElementById('adjust-hours-range').value);
    const startTime = document.getElementById('adjust-start-time').value;
    const day = currentSchedule.days[currentEditingDayIdx];

    try {
        const res = await fetch('/api/replan-day', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject: day.subject,
                focus: day.daily_focus || "Revision",
                hours: h,
                session_mins: wizardInputs.session_mins || 90,
                break_mins: wizardInputs.break_mins || 15,
                start_time: startTime
            })
        });
        const result = await res.json();

        day.tasks = result.tasks;
        // Sync the correct schedule in the list
        const schedEntry = savedSchedules.find(s => s.data === currentSchedule);
        if (schedEntry) localStorage.setItem('padsala_saved_schedules', JSON.stringify(savedSchedules));

        renderBlueprint(currentSchedule);
        closeAdjustModal();
    } catch (e) { alert("Adjustment Error"); }
};

async function editDayHours(dayIdx) {
    openAdjustModal(dayIdx);
}

// v17: COGNITIVE BIOMETRICS & HARD FOCUS
let focusBiometrics = {
    distractions: 0,
    idleSeconds: 0,
    tabSwitches: 0,
    lastActive: Date.now()
};

function initBiometrics() {
    focusBiometrics = { distractions: 0, idleSeconds: 0, tabSwitches: 0, lastActive: Date.now() };

    // Tab Visibility Tracking
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && timerInterval) {
            focusBiometrics.tabSwitches++;
            triggerFocusWarning("Commander, your focus is drifting! Return to the bridge.");
        }
    });

    // Idle Detection
    window.onmousemove = window.onkeypress = () => {
        focusBiometrics.lastActive = Date.now();
    };
}

function triggerFocusWarning(msg) {
    const overlay = document.getElementById('focus-mode');
    overlay.style.boxShadow = 'inset 0 0 100px rgba(239, 68, 68, 0.3)';
    setTimeout(() => overlay.style.boxShadow = 'none', 1000);
}

// FOCUS GALAXY LOGIC v17
function enterFocus(sub, task, minutes = 90) {
    document.getElementById('focus-mode').style.display = 'flex';
    document.getElementById('focus-title').innerText = sub;
    document.getElementById('focus-task').innerText = task;

    // v17: Fullscreen enforcement
    if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(() => { });
    }

    secondsRemaining = minutes * 60;
    totalSecondsInSession = secondsRemaining;

    initBiometrics();
    updateTimerUI();
    updateStatsUI();
}

function updateTimerUI() {
    const m = Math.floor(secondsRemaining / 60);
    const s = secondsRemaining % 60;
    document.getElementById('vault-timer').innerText = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;

    const fill = document.getElementById('timer-ring-fill');
    // Circumference 2 * PI * 155 = ~974
    if (fill) fill.style.strokeDashoffset = 974 - (secondsRemaining / totalSecondsInSession) * 974;
}

// AUDIO ENGINE v17
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playTone(freq, type, duration) {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
}

function toggleTimer() {
    const btn = document.getElementById('btn-play-pause');
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
        btn.innerHTML = `<i data-lucide="play"></i> Resume`;
        document.getElementById('bar-play-icon').setAttribute('data-lucide', 'play');
    } else {
        if (audioCtx.state === 'suspended') audioCtx.resume();

        timerInterval = setInterval(() => {
            if (secondsRemaining > 0) {
                secondsRemaining--;

                // AUDITORY CUES
                // 1. Tik-Tik every second (Subconscious Rhythm)
                playTone(800, 'sine', 0.05);

                // 2. 5-Minute Warning (Double Beep)
                if (secondsRemaining === 300) {
                    playTone(600, 'square', 0.2);
                    setTimeout(() => playTone(600, 'square', 0.2), 300);
                    triggerFocusWarning("5 Minutes Remaining - Final Push!");
                }

                // Track Idle Time
                if (Date.now() - focusBiometrics.lastActive > 30000) {
                    focusBiometrics.idleSeconds++;
                }
                updateTimerUI();
            } else {
                finishSession();
            }
        }, 1000);
        btn.innerHTML = `<i data-lucide="pause"></i> Focus Active`;
        document.getElementById('bar-play-icon').setAttribute('data-lucide', 'pause');

        if (document.getElementById('yt-input').value) loadYT();
    }
    lucide.createIcons();
}

function finishSession() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;

    // v17: Audio Notification & Flow Exit
    try {
        const audio = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg");
        audio.play();
    } catch (e) { }

    if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => { });
    }

    // Calculate Focus Score (v17)
    const factor = (focusBiometrics.tabSwitches * 10) + (focusBiometrics.idleSeconds / 10);
    const score = Math.max(0, 100 - factor);
    window.lastFocusScore = score;

    // Trigger Neural Encoding Modal
    document.getElementById('neural-modal').classList.add('active');
}

async function submitNeural() {
    const reflection = document.getElementById('neural-input').value;
    if (!reflection || reflection.length < 5) return alert("Please encode your session details (min 5 characters).");

    const score = window.lastFocusScore || 100;
    const sub = document.getElementById('focus-title').innerText;
    const task = document.getElementById('focus-task').innerText;

    // v17: Save Biometrics to Server
    if (isLoggedIn) {
        try {
            await fetch('/api/v17/log-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    subject: sub,
                    topic: task,
                    duration_mins: Math.round(totalSecondsInSession / 60),
                    focus_score: score,
                    distractions: focusBiometrics.tabSwitches,
                    idle_seconds: focusBiometrics.idleSeconds,
                    reflection: reflection
                })
            });
        } catch (e) { }
    }

    focusXP += Math.round(20 * (score / 100));
    concentrationStreak++;

    // PERSIST
    localStorage.setItem('padsala_xp', focusXP);
    localStorage.setItem('padsala_streak', concentrationStreak);

    // Close Modals
    document.getElementById('neural-modal').classList.remove('active');
    document.getElementById('neural-input').value = ""; // Clear for next time

    alert(`Session Neural-Encoded! Focus Score: ${Math.round(score)}%`);
    exitFocus();
    updateStatsUI();
}

function exitFocus() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
    document.getElementById('focus-mode').style.display = 'none';
}

function updateStatsUI() {
    document.getElementById('stat-streak').innerText = concentrationStreak;
    document.getElementById('stat-xp').innerText = focusXP;
    const rank = RANKS.slice().reverse().find(r => focusXP >= r.min)?.title || "INITIATE";
    document.getElementById('stat-rank').innerText = rank;
}

// YOUTUBE STREAM v17 (Distraction-Free)
function loadYT() {
    const q = document.getElementById('yt-input').value;
    if (!q) return;

    let url = q.includes('http')
        ? `https://www.youtube.com/embed/${q.split('v=')[1]?.split('&')[0] || q.split('/').pop()}?autoplay=1&rel=0&modestbranding=1`
        : `https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q + " lecture")}&rel=0&modestbranding=1&autoplay=1`;

    document.getElementById('yt-frame').innerHTML = `<iframe width="100%" height="100%" src="${url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
}

function playPreset(type) {
    if (type === 'lofi') document.getElementById('yt-input').value = 'lofi hip hop radio';
    if (type === 'rain') document.getElementById('yt-input').value = 'rain sounds for sleeping';
    loadYT();
    if (!timerInterval) toggleTimer(); // Auto-start timer on music preset
}

// AUTHENTICATION LOGIC
function togglePassword(id) {
    const el = document.getElementById(id);
    el.type = el.type === 'password' ? 'text' : 'password';
}

function openAuthModal() {
    document.getElementById('auth-modal').classList.add('active');
}
function closeAuthModal() {
    document.getElementById('auth-modal').classList.remove('active');
}
function toggleAuthForm(type) {
    document.getElementById('login-form').style.display = type === 'login' ? 'block' : 'none';
    document.getElementById('register-form').style.display = type === 'register' ? 'block' : 'none';
    document.getElementById('auth-modal-title').innerText = type === 'login' ? 'Access Protocol' : 'New Identity';
}

async function handleAuth(type) {
    const username = document.getElementById(type === 'login' ? 'login-username' : 'reg-username').value;
    const password = document.getElementById(type === 'login' ? 'login-password' : 'reg-password').value;

    if (!username || !password) return alert("Credentials required");

    try {
        const res = await fetch(`/api/auth/${type}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (data.success) {
            if (type === 'login') {
                isLoggedIn = true;
                currentUsername = data.user.username;
                updateAuthUI();
                await syncSchedules();
                closeAuthModal();
                location.reload(); // Refresh to clean state
            } else {
                alert("Account initialized! Please login.");
                toggleAuthForm('login');
            }
        } else {
            alert(data.error || "Access Denied");
        }
    } catch (e) { alert("Comm Error"); }
}

function updateAuthUI() {
    const statusEl = document.getElementById('auth-status');
    const welcomeUser = document.getElementById('welcome-username');
    const homeSummary = document.getElementById('home-active-summary');
    const homeCount = document.getElementById('home-protocol-count');

    if (isLoggedIn) {
        statusEl.innerHTML = `
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="color: var(--primary); font-weight: 700;">@${currentUsername}</span>
                <button class="control-btn" style="padding: 4px 8px;" onclick="location.href='/api/auth/logout'">Logout</button>
            </div>
        `;
        if (welcomeUser) welcomeUser.innerText = currentUsername;
    }

    // Multi-Timeline Summary on Home
    if (savedSchedules.length > 0) {
        if (homeSummary) homeSummary.style.display = 'block';
        if (homeCount) homeCount.innerText = savedSchedules.length;
    } else {
        if (homeSummary) homeSummary.style.display = 'none';
    }
}

async function syncSchedules() {
    try {
        const res = await fetch('/api/sync/schedules');
        if (res.ok) {
            const data = await res.json();
            if (data.length > 0) {
                savedSchedules = data;
                localStorage.setItem('padsala_saved_schedules', JSON.stringify(data));
            }
        }
    } catch (e) { console.error("Sync error", e); }
}

async function saveToServer(name, data, inputs) {
    if (!isLoggedIn) return;
    try {
        await fetch('/api/sync/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, data, inputs })
        });
    } catch (e) { console.error("Cloud save failed", e); }
}

async function deleteFromServer(name) {
    if (!isLoggedIn) return;
    try {
        await fetch('/api/sync/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
    } catch (e) { console.error("Cloud delete failed", e); }
}

// Update generateSchedule to use server sync
const originalGenerateSchedule = generateSchedule;
generateSchedule = async function () {
    await originalGenerateSchedule();
    if (isLoggedIn && savedSchedules.length > 0) {
        const latest = savedSchedules[savedSchedules.length - 1];
        await saveToServer(latest.name, latest.data, latest.inputs);
    }
};

// Update resetPlan to use server sync
const originalResetPlan = resetPlan;
resetPlan = async function () {
    const nameToDelete = savedSchedules.find(s => s.data === currentSchedule)?.name;
    await originalResetPlan();
    if (isLoggedIn && nameToDelete) {
        await deleteFromServer(nameToDelete);
    }
};

// PWA Registration
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js');
}

// ATMOSPHERIC SNOW SYSTEM
function initSnow() {
    const container = document.getElementById('snow-container');
    if (!container) return;

    const count = 40;
    for (let i = 0; i < count; i++) {
        const snow = document.createElement('div');
        snow.className = 'snow-particle';

        const size = Math.random() * 4 + 2;
        const left = Math.random() * 100;
        const delay = Math.random() * 10;
        const duration = Math.random() * 15 + 10;

        snow.style.width = `${size}px`;
        snow.style.height = `${size}px`;
        snow.style.left = `${left}%`;
        snow.style.top = `-20px`;
        snow.style.animationDelay = `${delay}s`;
        snow.style.animationDuration = `${duration}s`;

        container.appendChild(snow);
    }
}

const originalSwitchView = switchView;
switchView = (viewId) => {
    originalSwitchView(viewId);
    if (viewId === 'analytics') fetchMirrorData();
};

async function fetchMirrorData() {
    if (!isLoggedIn) return;
    try {
        const res = await fetch('/api/v17/analytics');
        const data = await res.json();

        // Populate Stats
        document.getElementById('mirror-focus-score').innerText = `${Math.round(data.avg_focus)}%`;
        document.getElementById('mirror-burnout').innerText = data.burnout_risk;
        document.getElementById('mirror-burnout').style.color =
            data.burnout_risk === 'HIGH' ? '#ef4444' : (data.burnout_risk === 'MED' ? '#fbbf24' : '#22c55e');

        // Populate Mastery Grid
        const grid = document.getElementById('mastery-grid');
        grid.innerHTML = "";

        for (const [sub, topics] of Object.entries(data.mastery)) {
            const subTitle = document.createElement('div');
            subTitle.className = 'focus-card-header';
            subTitle.style.marginBottom = '0.5rem';
            subTitle.innerText = sub.toUpperCase();
            grid.appendChild(subTitle);

            for (const [topic, score] of Object.entries(topics)) {
                const row = document.createElement('div');
                row.style.marginBottom = '1rem';
                row.innerHTML = `
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom: 5px;">
                        <span>${topic}</span>
                        <span>${score}%</span>
                    </div>
                    <div style="height:6px; background:rgba(255,255,255,0.05); border-radius:3px; overflow:hidden;">
                        <div style="width:${score}%; height:100%; background:linear-gradient(90deg, #8b5cf6, #d946ef); box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);"></div>
                    </div>
                `;
                grid.appendChild(row);
            }
        }
        if (Object.keys(data.mastery).length === 0) {
            grid.innerHTML = `<div style="text-align:center; opacity:0.5; padding: 2rem;">No cognitive data recorded. Start a Vault session.</div>`;
        }
    } catch (e) {
        console.error("Mirror sync failure", e);
    }
}

// BOOT ENGINE
window.onload = () => {
    initWizard();
    initSnow();
};

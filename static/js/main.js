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
        const res = await fetch('/api/metadata');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        db = await res.json();

        // Check for existing schedules
        if (savedSchedules.length > 0) {
            console.log("Loading persisted gallery...");
            currentSchedule = savedSchedules[0];
            renderGallery();
            renderBlueprint(currentSchedule);
            switchView('dashboard');
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
        <button class="nav-link ${currentSchedule === s.data ? 'active' : ''}" 
                onclick="loadTimeline(${idx})" 
                style="white-space: nowrap; border: 1px solid rgba(255,255,255,0.1)">
            ${s.name}
        </button>
    `).join('');

    if (savedSchedules.length < 5) {
        gallery.innerHTML += `
            <button class="nav-link" onclick="switchView('home')" style="border: 1px dashed var(--primary); color: var(--primary)">
                + New Timeline
            </button>
        `;
    }
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
        html += `
        <div class="glass-card" style="padding: 2rem; border-color: ${day.is_exam_day ? '#ef4444' : 'rgba(255,255,255,0.1)'}">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <span style="opacity: 0.7;">${day.bs_date}</span>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <button class="control-btn" style="padding: 4px 8px; font-size: 0.7rem; height: auto;" onclick="editDayHours(${idx})">
                        <i data-lucide="clock" style="width: 12px; height: 12px;"></i> Adjust
                    </button>
                    <span style="font-weight: 700; color: #a78bfa;">${day.subject}</span>
                </div>
            </div>
            <h3 style="margin-bottom: 1.5rem;">${day.daily_focus || 'Focus Session'}</h3>
            <div id="day-tasks-${idx}">
                ${day.tasks.map(t => `
                    <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; ${isHoliday ? 'opacity: 0.5' : 'cursor: pointer;'}" 
                         ${!isHoliday ? `onclick="enterFocus('${day.subject}', '${t.activity.replace(/'/g, "\\'")}', ${t.minutes})"` : ''}>
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

// FOCUS GALAXY LOGIC
function enterFocus(sub, task, minutes = 90) {
    document.getElementById('focus-mode').style.display = 'flex';
    document.getElementById('focus-title').innerText = sub;
    document.getElementById('focus-task').innerText = task;

    secondsRemaining = minutes * 60;
    totalSecondsInSession = secondsRemaining;

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

function toggleTimer() {
    const btn = document.getElementById('btn-play-pause');
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
        btn.innerHTML = `<i data-lucide="play"></i> Start`;
        document.getElementById('bar-play-icon').setAttribute('data-lucide', 'play');
    } else {
        timerInterval = setInterval(() => {
            if (secondsRemaining > 0) {
                secondsRemaining--;
                updateTimerUI();
            } else {
                finishSession();
            }
        }, 1000);
        btn.innerHTML = `<i data-lucide="pause"></i> Pause`;
        document.getElementById('bar-play-icon').setAttribute('data-lucide', 'pause');

        // Auto-play music if input has value
        if (document.getElementById('yt-input').value) loadYT();
    }
    lucide.createIcons();
}

function finishSession() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
    focusXP += 20;
    concentrationStreak++;
    localStorage.setItem('padsala_xp', focusXP);
    localStorage.setItem('padsala_streak', concentrationStreak);
    alert("Session Complete +20 XP");
    exitFocus();
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

// YOUTUBE STREAM
function loadYT() {
    const q = document.getElementById('yt-input').value;
    if (!q) return;

    let url = q.includes('http')
        ? `https://www.youtube.com/embed/${q.split('v=')[1]?.split('&')[0] || q.split('/').pop()}?autoplay=1`
        : `https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(q)}`;

    document.getElementById('yt-frame').innerHTML = `<iframe width="100%" height="100%" src="${url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
}

function playPreset(type) {
    if (type === 'lofi') document.getElementById('yt-input').value = 'lofi hip hop radio';
    if (type === 'rain') document.getElementById('yt-input').value = 'rain sounds for sleeping';
    loadYT();
    if (!timerInterval) toggleTimer(); // Auto-start timer on music preset
}

// PWA Registration
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js');
}

window.onload = initWizard;

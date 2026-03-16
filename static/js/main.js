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
    { min: 0, title: "Beginner" },
    { min: 500, title: "Student Monk" },
    { min: 2000, title: "Focus Warrior" },
    { min: 5000, title: "Knowledge Seeker" },
    { min: 10000, title: "Master Scholar" },
    { min: 25000, title: "Superhuman Scholar" }
];
const STUDY_TIPS = [
    "Read actively. Try explaining the concept to yourself.",
    "Use the Feynman technique: explain this topic as if teaching a beginner.",
    "If stuck for 5 minutes, move to another subtopic.",
    "Write one key takeaway every 10 minutes.",
    "Close your eyes for 10 seconds to refresh your brain."
];
const STUDY_STICKERS = ["📚 Knowledge Loading...", "🧠 Brain Power Increasing", "🔥 Focus Mode Active", "🎯 Stay Locked In", "✨ You Are Doing Great", "💡 Concept Unlocked"];

// REWARD SYSTEM (Confetti & Effects)
function triggerConfetti() {
    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 10000 };

    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
            return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);
        // since particles fall down, start a bit higher than random
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
        confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
    }, 250);
}

// NAVIGATION
function switchView(view) {
    // Protect Routes
    if ((view === 'dashboard' || view === 'leaderboard' || view === 'analytics') && !isLoggedIn) {
        openAuthModal();
        // Option to display a toast here
        return;
    }

    const previousView = document.querySelector('.view-section.active');
    if (previousView) {
        previousView.style.opacity = '0';
        previousView.style.transform = 'translateY(-10px)';
    }

    setTimeout(() => {
        document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

        const targetView = document.getElementById(`view-${view}`);
        targetView.classList.add('active');
        targetView.style.opacity = '1';
        targetView.style.transform = 'translateY(0)';
        document.getElementById(`nav-${view}`).classList.add('active');

        if (view === 'dashboard') {
            if (currentSchedule) {
                document.getElementById('dashboard-ready').style.display = 'block';
                document.getElementById('dashboard-empty').style.display = 'none';
                renderBlueprint(currentSchedule);
                updateDashboardStats();
            } else {
                document.getElementById('dashboard-ready').style.display = 'none';
                document.getElementById('dashboard-empty').style.display = 'block';
            }
        } else if (view === 'leaderboard') {
            loadLeaderboard();
        } else if (view === 'analytics') {
            syncMirrors();
        }
        
        // Premium touch: Auto-scroll to top on view change
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 200);
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
            currentSchedule = savedSchedules[0].data;
            wizardInputs = savedSchedules[0].inputs || {};
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
    const allSems = Object.keys(db[u]?.[f]?.[c] || {});
    // Filter out elective groups from the semester dropdown — they are shown inline
    const regularSems = allSems.filter(s => !s.startsWith('Elective'));
    populateDropdown('select-semester', regularSems);
    updateSubjects();
}

function updateSubjects() {
    const u = document.getElementById('select-university').value;
    const f = document.getElementById('select-faculty').value;
    const c = document.getElementById('select-course').value;
    const s = document.getElementById('select-semester').value;

    if (u && f && c && s && db[u]?.[f]?.[c]?.[s]) {
        document.getElementById('subject-selection-zone').style.display = 'block';
        const semSubjects = db[u][f][c][s];
        const courseData = db[u][f][c];
        
        let html = '';

        Object.keys(semSubjects).forEach(name => {
            const info = semSubjects[name];

            // Check if this subject is an elective GROUP placeholder (e.g. "Elective I")
            if (name.startsWith('Elective') && courseData[name]) {
                // Render as expandable elective picker
                const chosenElective = selectedSubjects.find(sub => sub._group === name);
                html += `
                    <div class="elective-group" style="grid-column: 1 / -1; border: 2px dashed #d946ef; border-radius: 16px; padding: 1.2rem; background: linear-gradient(135deg, rgba(217,70,239,0.05), rgba(139,92,246,0.05));">
                        <div onclick="toggleElectivePanel('${name}')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: 800; color: #d946ef; font-size: 1rem;">✦ ${name} — Choose One</div>
                                <div style="font-size: 0.75rem; opacity: 0.7; margin-top: 2px;">
                                    ${chosenElective ? `✅ Selected: <strong>${chosenElective.name}</strong>` : 'Click to select your elective subject'}
                                </div>
                            </div>
                            <div id="elective-arrow-${name.replace(/\s/g,'-')}" style="font-size: 1.4rem; transition: transform 0.3s;">▼</div>
                        </div>
                        <div id="elective-panel-${name.replace(/\s/g,'-')}" style="display:none; margin-top: 1rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.8rem;">
                            ${Object.keys(courseData[name]).map(eName => `
                                <div onclick="pickElective('${name}', '${eName.replace(/'/g,"\\'")}', ${courseData[name][eName].difficulty || 2})"
                                     style="padding: 0.9rem; border-radius: 12px; cursor: pointer; text-align: center; font-size: 0.85rem; font-weight: 600; transition: all 0.2s;
                                            background: ${chosenElective?.name === eName ? '#d946ef' : 'rgba(255,255,255,0.08)'};
                                            color: ${chosenElective?.name === eName ? 'white' : 'inherit'};
                                            border: 1.5px solid ${chosenElective?.name === eName ? '#d946ef' : 'rgba(217,70,239,0.3)'};
                                            transform: ${chosenElective?.name === eName ? 'scale(1.03)' : 'scale(1)'}"
                                     onmouseover="this.style.borderColor='#d946ef'"
                                     onmouseout="this.style.borderColor='${chosenElective?.name === eName ? '#d946ef' : 'rgba(217,70,239,0.3)'}'">
                                    ${eName}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else {
                // Regular subject card
                const isSelected = selectedSubjects.some(sub => sub.name === name);
                const subObj = selectedSubjects.find(sub => sub.name === name) || { difficulty: info.difficulty || 2 };
                html += `
                    <div class="glass-card subject-card ${isSelected ? 'selected' : ''}" 
                         style="padding: 1.2rem; border: 1px solid ${isSelected ? 'var(--primary)' : 'var(--glass-border)'}; position: relative; transition: all 0.3s; cursor:pointer;"
                         onclick="toggleSubject(event, '${name.replace(/'/g, "\\'")}', ${info.difficulty || 2})">
                        <div style="font-weight: 700; margin-bottom: 0.8rem; color: ${isSelected ? 'var(--primary)' : 'inherit'}">${name}</div>
                        <div class="difficulty-picker" onclick="event.stopPropagation()" style="display: flex; gap: 4px;">
                            ${[1, 2, 3].map(d => `
                                <div onclick="setSubDifficulty('${name.replace(/'/g, "\\'")}', ${d})" 
                                     style="flex: 1; height: 6px; border-radius: 3px; background: ${subObj.difficulty >= d ? (d === 3 ? '#ef4444' : d === 2 ? '#fbbf24' : '#22c55e') : '#e2e8f0'}; cursor: pointer;">
                                </div>
                            `).join('')}
                        </div>
                        <div style="font-size: 0.65rem; margin-top: 4px; opacity: 0.6;">
                            LEVEL: ${subObj.difficulty === 3 ? 'HARD' : subObj.difficulty === 2 ? 'MED' : 'EASY'}
                        </div>
                    </div>
                `;
            }
        });

        document.getElementById('subjects-grid').innerHTML = html;
    }
}

function toggleElectivePanel(groupName) {
    const panelId = 'elective-panel-' + groupName.replace(/\s/g, '-');
    const arrowId = 'elective-arrow-' + groupName.replace(/\s/g, '-');
    const panel = document.getElementById(panelId);
    const arrow = document.getElementById(arrowId);
    if (!panel) return;
    const isOpen = panel.style.display !== 'none';
    panel.style.display = isOpen ? 'none' : 'grid';
    if (arrow) arrow.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
}

function pickElective(groupName, subjectName, difficulty) {
    // Remove any previous selection from this elective group
    selectedSubjects = selectedSubjects.filter(s => s._group !== groupName);
    // Add the new selection
    selectedSubjects.push({ name: subjectName, difficulty, is_elective: true, _group: groupName });
    updateSubjects();
}

function setSubDifficulty(name, diff) {
    const sub = selectedSubjects.find(s => s.name === name);
    if (sub) {
        sub.difficulty = diff;
    } else {
        // Find in DB to get elective info
        const u = document.getElementById('select-university').value;
        const f = document.getElementById('select-faculty').value;
        const c = document.getElementById('select-course').value;
        const s = document.getElementById('select-semester').value;
        const info = db[u][f][c][s][name];
        selectedSubjects.push({ name, difficulty: diff, is_elective: info.is_elective });
    }
    updateSubjects();
}

function toggleSubject(event, name, defaultDiff) {
    if (event.target.closest('.difficulty-picker')) return;
    
    const existingIdx = selectedSubjects.findIndex(s => s.name === name);
    if (existingIdx !== -1) {
        selectedSubjects.splice(existingIdx, 1);
    } else {
        const u = document.getElementById('select-university').value;
        const f = document.getElementById('select-faculty').value;
        const c = document.getElementById('select-course').value;
        const s = document.getElementById('select-semester').value;
        const info = db[u][f][c][s][name];
        selectedSubjects.push({ name, difficulty: info.difficulty || defaultDiff || 2, is_elective: info.is_elective });
    }
    updateSubjects();
}

function prepareDateInputs() {
    navigateTo(3);
    const container = document.getElementById('exam-date-inputs');
    
    // Default to today or the BS date from DB
    const defaultBS = db.today_bs || "2081-12-30"; 
    
    container.innerHTML = selectedSubjects.map(s => `
        <div class="glass-card" style="padding: 1.5rem; display: flex; align-items: center; justify-content: space-between; border: 1px solid #e2e8f0; background: white; border-radius: 16px;">
            <div>
                <div style="font-weight: 800; font-size: 1.1rem;">${s.name}</div>
                <div style="font-size: 0.75rem; opacity: 0.6;">DIFF: ${s.difficulty === 3 ? 'HARD' : s.difficulty === 2 ? 'MED' : 'EASY'}</div>
            </div>
            <input type="text" 
                   class="exam-date-input nepali-datepicker" 
                   data-subject="${s.name}" 
                   data-difficulty="${s.difficulty}" 
                   value="${defaultBS}" 
                   placeholder="YYYY-MM-DD (BS)"
                   style="width: 180px; padding: 0.5rem; border-radius: 8px; border: 1px solid var(--border);">
        </div>
    `).join('');

    // Initialize the pickers
    setTimeout(() => {
        document.querySelectorAll('.nepali-datepicker').forEach(el => {
            $(el).nepaliDatePicker({
                ndpYear: true,
                ndpMonth: true,
                ndpYearCount: 20
            });
        });
    }, 100);
}

async function generateSchedule() {
    const exams = Array.from(document.querySelectorAll('.exam-date-input')).map(i => ({
        name: i.dataset.subject,
        date: i.value,
        difficulty: parseInt(i.dataset.difficulty)
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

// DASHBOARD UI LOGIC v17
let dashboardViewMode = 'focus'; // 'focus' | 'calendar'

function setDashboardView(mode) {
    dashboardViewMode = mode;
    renderBlueprint(currentSchedule);
}

function renderBlueprint(data) {
    if (!data || !data.days) return;

    // Both containers
    const dashContainer = document.getElementById('blueprint-content');

    // Dynamic Date Calculation (Client Side)
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const dayDate = String(today.getDate()).padStart(2, '0');
    const clientDateStr = `${year}-${month}-${dayDate}`;

    // 1. HEADER (Segmented Control)
    let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
            <div class="view-toggle">
                <button class="view-btn ${dashboardViewMode === 'focus' ? 'active' : ''}" onclick="setDashboardView('focus')">
                    <i data-lucide="target" style="width: 16px; display:inline; vertical-align:middle; margin-right:4px;"></i> Focus
                </button>
                <button class="view-btn ${dashboardViewMode === 'calendar' ? 'active' : ''}" onclick="setDashboardView('calendar')">
                    <i data-lucide="calendar" style="width: 16px; display:inline; vertical-align:middle; margin-right:4px;"></i> Calendar
                </button>
            </div>
            
            <button class="control-btn" onclick="resetPlan()" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.2)">
                <i data-lucide="refresh-cw"></i> Reset
            </button>
        </div>`;

    // 2. VIEW RENDERER (With Gallery Injection)
    let galleyHtml = '';
    if (savedSchedules.length > 0) {
        galleyHtml = `
        <div class="timeline-gallery-scroll" style="display: flex; gap: 0.8rem; overflow-x: auto; padding-bottom: 0.5rem; margin-bottom: 1.5rem; -webkit-overflow-scrolling: touch;">
            ${savedSchedules.map((s, i) => `
                <div onclick="loadTimeline(${i})" 
                     style="padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.75rem; font-weight: 600; cursor: pointer; white-space: nowrap; transition: all 0.2s; border: 1px solid ${currentSchedule === s.data ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}; background: ${currentSchedule === s.data ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.03)'}; color: ${currentSchedule === s.data ? 'white' : 'var(--text-muted)'}; box-shadow: ${currentSchedule === s.data ? '0 0 10px rgba(139, 92, 246, 0.2)' : 'none'};">
                     ${s.name}
                </div>
            `).join('')}
            
            <div onclick="switchView('home'); initiateNewProtocol();" 
                 style="padding: 0.5rem 1rem; border-radius: 8px; font-size: 0.75rem; font-weight: 600; cursor: pointer; white-space: nowrap; border: 1px dashed var(--primary); color: var(--primary); background: rgba(139, 92, 246, 0.05);">
                + New Plan
            </div>
        </div>
        `;
    }

    if (dashboardViewMode === 'calendar') {
        html += galleyHtml + renderCalendarGrid(data.days, clientDateStr);
    } else {
        html += galleyHtml + renderFocusCard(data.days, clientDateStr);
    }

    dashContainer.innerHTML = html;

    // Remove old FAB if exists
    const oldFab = document.getElementById('btn-calendar-expand');
    if (oldFab) oldFab.remove();

    lucide.createIcons();
}

const SUBJECT_COLORS = [
    '#d946ef', // Pink
    '#06b6d4', // Cyan
    '#f97316', // Orange
    '#eab308', // Yellow
    '#3b82f6', // Blue
    '#8b5cf6'  // Purple
];

function getSubjectColor(subject) {
    if (!subject) return '#a78bfa';
    let hash = 0;
    for (let i = 0; i < subject.length; i++) {
        hash = subject.charCodeAt(i) + ((hash << 5) - hash);
    }
    const idx = Math.abs(hash) % SUBJECT_COLORS.length;
    return SUBJECT_COLORS[idx];
}

function renderCalendarGrid(days, clientDateStr) {
    let gridHtml = `
    <div class="calendar-wrapper">
        <div class="calendar-header">
            <div>SUN</div><div>MON</div><div>TUE</div><div>WED</div><div>THU</div><div>FRI</div><div>SAT</div>
        </div>
        <div class="calendar-grid">
    `;

    days.forEach((day, idx) => {
        let isCompleted = false;
        let isToday = false;
        if (day.ad_date) {
            if (day.ad_date < clientDateStr) isCompleted = true;
            else if (day.ad_date === clientDateStr) isToday = true;
        }

        const statusClass = isToday ? 'is-today' : (isCompleted ? 'is-completed' : '');
        const examClass = day.is_exam_day ? 'is-exam' : '';
        const subColor = getSubjectColor(day.subject);

        // Extract day number from AD date if possible, else BS
        let dayNum = day.bs_date.split('-')[2];
        if (day.ad_date) dayNum = day.ad_date.split('-')[2];

        // Green for Exams (User Request)
        const examIndicator = day.is_exam_day
            ? `<div style="font-size:0.6rem; color:#22c55e; font-weight:800; text-shadow: 0 0 10px rgba(34, 197, 94, 0.4);">EXAM DAY</div>`
            : '';

        gridHtml += `
            <div class="calendar-day ${statusClass} ${examClass}" onclick="editDayHours(${idx})" 
                 style="${day.is_exam_day ? 'border-color: #22c55e; background: rgba(34, 197, 94, 0.1);' : ''}">
                <div class="cal-date" style="${isToday ? '' : 'opacity:0.6'}">${dayNum}</div>
                <div class="cal-subject" style="color: ${subColor};">${day.subject}</div>
                ${examIndicator}
            </div>
        `;
    });

    gridHtml += `</div></div>`;
    return gridHtml;
}

function renderFocusCard(days, clientDateStr) {
    let html = `<div style="display: grid; place-items: center;">`;
    let activeDay = null;
    let activeIdx = -1;

    // Find Today
    days.forEach((day, idx) => {
        if (day.ad_date === clientDateStr) {
            activeDay = day;
            activeIdx = idx;
        }
    });

    // Fallback: If today not found (e.g., schedule ended), show last day or a message
    if (!activeDay) {
        // Try finding first upcoming
        activeDay = days.find(d => d.ad_date > clientDateStr);
        if (!activeDay) {
            return `<div style="text-align:center; padding: 4rem; opacity:0.5;">Protocol Completed. <br>Relax.</div>`;
        }
        activeIdx = days.indexOf(activeDay);
    }

    const day = activeDay;
    const isHoliday = day.tasks.length === 1 && day.tasks[0].activity.includes("HOLIDAY");

    html += `
        <div class="glass-card element-enter" style="width: 100%; max-width: 600px; padding: 2.5rem; border: 2px solid var(--primary); box-shadow: 0 0 40px rgba(139, 92, 246, 0.2);">
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 0.9rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 0.5rem;">Current Protocol</div>
                <h2 style="font-size: 2.5rem; margin: 0; color: white;">${day.bs_date}</h2>
                <div style="color: #a78bfa; font-weight: 700; font-size: 1.2rem; margin-top: 0.5rem;">${day.subject}</div>
            </div>

            <div style="display: flex; flex-direction: column; gap: 1rem;">
                ${day.tasks.map(t => `
                    <div style="background: rgba(255,255,255,0.05); padding: 1.2rem; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; ${isHoliday ? 'opacity: 0.7' : 'cursor: pointer; transition: transform 0.2s;'}" 
                         ${!isHoliday ? `onclick="enterFocus('${day.subject}', '${t.activity.replace(/'/g, "\\'")}', ${t.minutes})"` : ''}
                         onmouseover="this.style.background='rgba(255,255,255,0.1)'; this.style.transform='scale(1.02)'"
                         onmouseout="this.style.background='rgba(255,255,255,0.05)'; this.style.transform='scale(1)'">
                        
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-weight: 700; font-size: 1.1rem;">${t.activity}</span>
                            <span style="font-size: 0.8rem; opacity: 0.6;">${t.type.toUpperCase()}</span>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #d946ef; font-weight: 700;">${t.time}</div>
                            <div style="font-size: 0.8rem; opacity: 0.6;">${t.minutes}m</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
             <div style="margin-top: 2rem; text-align: center;">
                 <button class="control-btn" onclick="editDayHours(${activeIdx})" style="font-size: 0.8rem;">
                    <i data-lucide="clock"></i> Adjust Schedule
                </button>
             </div>
        </div>
    </div>`;

    return html;
}
// Auto-Scroll to Today
setTimeout(() => {
    const todayEl = document.getElementById('active-day-card');
    if (todayEl) {
        todayEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}, 500);

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
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN
            },
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
let audioCtx = null;

function getAudioCtx() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioCtx;
}

function playTone(freq, type, duration) {
    const ctx = getAudioCtx();
    if (ctx.state === 'suspended') ctx.resume();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);

    gain.gain.setValueAtTime(0.3, ctx.currentTime); // Louder (0.3)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + duration);
}

function toggleTimer() {
    const btn = document.getElementById('btn-play-pause');
    const ctx = getAudioCtx();

    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
        btn.innerHTML = `<i data-lucide="play"></i> Resume Session`;
    } else {
        if (ctx.state === 'suspended') ctx.resume();

        timerInterval = setInterval(() => {
            if (secondsRemaining > 0) {
                secondsRemaining--;

                // XP Gain: 10 XP per minute = ~0.166 XP per second
                focusXP += (10 / 60);
                
                // Randomly spawn sticker every ~45 seconds
                if (Math.random() < (1 / 45)) spawnSticker();
                
                // Randomly show smart tip every 10 minutes (600 seconds)
                if (secondsRemaining % 600 === 0 && secondsRemaining !== totalSecondsInSession) showSmartTip();

                // Auditory Cues (Subtle)
                if (secondsRemaining % 60 === 0) playTone(800, 'triangle', 0.1); 

                if (secondsRemaining === 300) {
                    triggerFocusWarning("Commander, 5 minutes left! Stay locked in.");
                    if (typeof voiceSystem !== 'undefined') voiceSystem.trigger('warning_5m');
                }

                if (Date.now() - focusBiometrics.lastActive > 30000) {
                    focusBiometrics.idleSeconds++;
                }

                updateTimerUI();
                updateFocusStatsUI();
            } else {
                finishSession();
            }
        }, 1000);
        btn.innerHTML = `<i data-lucide="pause"></i> Session Active`;
    }
    if (lucide) lucide.createIcons();
}

function updateFocusStatsUI() {
    const xpEl = document.getElementById('stat-xp');
    if (xpEl) xpEl.innerText = Math.floor(focusXP);
}

function finishSession() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;

    localStorage.setItem('padsala_xp', Math.floor(focusXP));
    
    // Streak logic (basic)
    if (!localStorage.getItem('last_study_date')) {
        concentrationStreak = 1;
    } else {
        const last = new Date(localStorage.getItem('last_study_date'));
        const now = new Date();
        const diff = (now - last) / (1000 * 60 * 60 * 24);
        if (diff < 1.5 && diff > 0.5) {
            concentrationStreak++;
        } else if (diff > 1.5) {
             concentrationStreak = 1;
        }
    }
    localStorage.setItem('last_study_date', new Date().toISOString());
    localStorage.setItem('padsala_streak', concentrationStreak);

    if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => { });
    }

    // Reward feedback
    alert(`Session Complete!\nXP Gained: ${Math.floor(focusXP)}\nRank: ${getCurrentRank().title}`);
    switchView('dashboard');
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

    // v17: Push to Server (Gamification)
    syncXP();

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

// SOCIAL ENGINE v17
async function syncXP() {
    if (!isLoggedIn) return;
    try {
        await fetch('/api/v17/sync-xp', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN
            },
            body: JSON.stringify({ xp: focusXP, streak: concentrationStreak })
        });
    } catch (e) { console.error("XP Sync Fail", e); }
}

async function fetchLeaderboard() {
    try {
        const res = await fetch('/api/v17/leaderboard');
        const data = await res.json();
        renderLeaderboard(data.leaderboard, data.user_rank);
        // Switch view if not already
        // switchView('leaderboard') - purely called by UI button
    } catch (e) {
        console.error("LB Error", e);
    }
}

function renderLeaderboard(users, myRank) {
    const list = document.getElementById('leaderboard-list');
    if (!list) return;

    list.innerHTML = users.map((u, idx) => {
        const isMe = u.username === currentUsername;
        let medal = '';
        if (idx === 0) medal = '🥇';
        if (idx === 1) medal = '🥈';
        if (idx === 2) medal = '🥉';

        return `
        <div class="glass-card" style="display: flex; align-items: center; justify-content: space-between; padding: 1rem; margin-bottom: 0.5rem; ${isMe ? 'border-color: var(--primary); background: rgba(139, 92, 246, 0.1);' : ''}">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-weight: 800; width: 30px; color: ${idx < 3 ? '#fbbf24' : 'grey'};">${medal || idx + 1}</div>
                <div style="width: 40px; height: 40px; border-radius: 50%; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-weight: bold;">
                    ${u.username[0].toUpperCase()}
                </div>
                <div>
                    <div style="font-weight: 700; ${u.is_pro ? 'color: #3b82f6;' : ''}">
                        ${u.username} ${u.is_pro ? '⚡' : ''}
                    </div>
                    <div style="font-size: 0.7rem; opacity: 0.6;">Streak: ${u.streak} 🔥</div>
                </div>
            </div>
            <div style="font-weight: 800; color: var(--primary);">${u.xp} XP</div>
        </div>
        `;
    }).join('');

    if (myRank > 10) {
        list.innerHTML += `
            <div style="text-align: center; padding: 1rem; opacity: 0.5; margin-top: 1rem;">
                ... <br> You are Rank #${myRank}
            </div>
        `;
    }
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
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN
            },
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
                
                // v18: Handle Admin Redirect
                if (data.redirect) {
                    location.href = data.redirect;
                } else {
                    location.reload(); 
                }
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
                <button class="control-btn" style="padding: 4px 8px;" onclick="location.href='/accounts/logout/'">Logout</button>
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
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN
            },
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
    if (viewId === 'leaderboard') fetchLeaderboard();
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

// VOICE SYSTEM v17 (Behavioral Sound Designer)
class VoiceEngine {
    constructor() {
        this.enabled = true;
        this.mode = 'serious'; // serious | light | silent
        this.volume = 0.8;
        this.cooldowns = {};
        this.lang = 'ne-NP';

        // SCRIPT LIBRARY (Senior Dai Persona)
        this.scripts = {
            'login_day': { serious: "आउ है, पढ्न बस।", light: "ल है, आज अलिकति कडा मेहनत।" },
            'app_load': { serious: "Padsala तयार छ।", light: "पढ् सालाँ!" },
            'plan_generated': { serious: "आजको बाटो तय भयो।", light: "Step by step, सकिन्छ।" },
            'task_start': { serious: "यहीबाट सुरु गर।", light: "पहिलो कदम!" },
            'vault_enter': { serious: "अब ध्यान दे।", light: "Vault सुरु!" },
            'tab_switch': { serious: "फर्क।", light: "यहाँ बस!" },
            'warning_5m': { serious: "अलिकति अझै, अन्तिम जोर।", light: "Last 5 minutes, give your best!" },
            'session_done': { serious: "राम्रै गरिस्। आजको लक्ष्य पूरा।", light: "Well done, take a break." },
            'neural_open': { serious: "के सिकिस्? मनमा बसाल।", light: "Quick recall, what stuck?" },
            'neural_submit': { serious: "यही याद रहोस्। Strong बन्यो।", light: "Saved to memory." }
        };

        this.loadSettings();
    }

    loadSettings() {
        const saved = localStorage.getItem('padsala_voice_config');
        if (saved) {
            const config = JSON.parse(saved);
            this.enabled = config.enabled;
            this.mode = config.mode;
            this.volume = config.volume;
        }
        this.updateUI();
    }

    saveSettings() {
        localStorage.setItem('padsala_voice_config', JSON.stringify({
            enabled: this.enabled,
            mode: this.mode,
            volume: this.volume
        }));
    }

    trigger(key) {
        if (!this.enabled || this.mode === 'silent') return;

        // Cooldown Logic (30 mins) - exception for "tab_switch" (immediate correction)
        const now = Date.now();
        const cooldownTime = key === 'tab_switch' ? 5000 : 30 * 60 * 1000;

        if (this.cooldowns[key] && (now - this.cooldowns[key] < cooldownTime)) {
            return;
        }

        const text = this.scripts[key][this.mode] || this.scripts[key]['serious'];
        this.speak(key, text);
        this.cooldowns[key] = now;
    }

    speak(key, text) {
        // Resume Audio Context if suspended (Browser Policy Fix)
        const ctx = getAudioCtx();
        if (ctx.state === 'suspended') {
            ctx.resume().then(() => this._playAudio(key, text));
        } else {
            this._playAudio(key, text);
        }
    }

    _playAudio(key, text) {
        // 1. Try playing OGG file first (Preferred)
        const audio = new Audio(`/static/audio/voi_${key}_${this.mode}.ogg`);
        audio.volume = this.volume;

        audio.play().catch(e => {
            console.warn("Audio file missing, using TTS fallback", e);
            // 2. Fallback to Browser TTS
            if ('speechSynthesis' in window) {
                const u = new SpeechSynthesisUtterance(text);
                // Attempt to use a Hindi/Indian English voice for better Nepali accent approximation
                const voices = window.speechSynthesis.getVoices();
                // Prioritize Google Hindi or any Hindi voice
                const preferredVoice = voices.find(v => v.name.includes('Google Hindi') || v.lang.includes('hi')) || voices[0];

                if (preferredVoice) {
                    u.voice = preferredVoice;
                    // Hindi voice reads Nepali text reasonably well
                    u.lang = 'hi-IN';
                } else {
                    u.lang = 'ne-NP';
                }

                u.volume = this.volume;
                u.rate = 0.85; // Slow, deliberate (Senior Dai style)
                u.pitch = 0.9; // Slightly deep
                window.speechSynthesis.speak(u);
            }
        });
    }

    // Call this on first user interaction
    warmup() {
        const ctx = getAudioCtx();
        if (ctx.state === 'suspended') ctx.resume();
        // Silent TTS warmup to load voices
        if ('speechSynthesis' in window) window.speechSynthesis.getVoices();
    }

    // UI Controls
    toggle(val) { this.enabled = val; this.saveSettings(); }
    setMode(val) {
        this.mode = val;
        this.saveSettings();
        document.querySelectorAll('.preset-grid button').forEach(b => b.classList.remove('active'));
        document.getElementById(`mode-${val}`).classList.add('active');
    }
    setVolume(val) { this.volume = parseFloat(val); this.saveSettings(); }

    updateUI() {
        if (document.getElementById('voice-toggle')) {
            document.getElementById('voice-toggle').checked = this.enabled;
            document.getElementById('voice-volume').value = this.volume;
            document.querySelectorAll('.preset-grid button').forEach(b => b.classList.remove('active'));
            if (document.getElementById(`mode-${this.mode}`))
                document.getElementById(`mode-${this.mode}`).classList.add('active');
        }
    }
}

const voiceSystem = new VoiceEngine();

function toggleSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal.style.display === 'flex') {
        modal.querySelector('.modal-content').classList.remove('animate-in');
        modal.style.display = 'none';
    } else {
        modal.style.display = 'flex';
        modal.querySelector('.modal-content').classList.add('animate-in');
        voiceSystem.updateUI();
    }
}

// Global Visibility Listener for Discipline
document.addEventListener("visibilitychange", () => {
    if (document.hidden && focusModeActive) {
        focusBiometrics.tabSwitches++;
        triggerFocusWarning("Don't Switch Tabs! Focus Score Dropping.");
        voiceSystem.trigger('tab_switch');
    }
});

// BOOT ENGINE
window.onload = () => {
    initWizard();
    initSnow();
    voiceSystem.trigger('app_load');
};

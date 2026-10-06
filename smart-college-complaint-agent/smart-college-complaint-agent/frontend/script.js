// Student Complaint Portal Client Script - Smart College Support

let selectedPhotoBase64 = null;
let selectedPhotoFilename = null;
let currentStudent = null;

document.addEventListener("DOMContentLoaded", () => {
    initStudentAuth();

    const submitBtn = document.getElementById("submitBtn");
    if (submitBtn) {
        submitBtn.addEventListener("click", handleComplaintSubmit);
    }

    // Set up Drag and Drop on dropzone
    const dropzone = document.getElementById("photoDropzone");
    if (dropzone) {
        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });
        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("dragover");
        });
        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                const fileInput = document.getElementById("complaintPhoto");
                fileInput.files = e.dataTransfer.files;
                handlePhotoSelect(fileInput);
            }
        });
    }

    // Load initial student complaints count
    loadMyComplaints();
});

// ==========================================
// AUTHENTICATION & SESSION
// ==========================================

function initStudentAuth() {
    const authBar = document.getElementById("studentAuthBar");
    const rawStu = localStorage.getItem("vcet_student");

    if (rawStu) {
        try {
            currentStudent = JSON.parse(rawStu);
        } catch (e) {
            currentStudent = null;
        }
    }

    if (currentStudent && currentStudent.username) {
        if (authBar) {
            authBar.innerHTML = `
                <div class="user-pill">
                    <span class="online-indicator"></span>
                    <span>Student: <strong>${escapeHtml(currentStudent.username)}</strong></span>
                    <button class="logout-link" onclick="logoutStudent()">Logout</button>
                </div>
            `;
        }
        const nameInput = document.getElementById("studentName");
        if (nameInput) {
            nameInput.value = currentStudent.username;
        }
    } else {
        if (authBar) {
            authBar.innerHTML = `
                <a href="/student-login" class="login-link-btn">🔐 Student Login (VCET26)</a>
            `;
        }
        const nameInput = document.getElementById("studentName");
        if (nameInput && !nameInput.value) {
            nameInput.value = "VCET26";
        }
    }
}

function logoutStudent() {
    localStorage.removeItem("vcet_student");
    localStorage.removeItem("vcet_token");
    window.location.href = "/student-login";
}

// ==========================================
// TABS SWITCHING
// ==========================================

function switchPortalTab(tabName) {
    const secSubmit = document.getElementById("sectionSubmit");
    const secTrack = document.getElementById("sectionTrack");
    const btnSubmit = document.getElementById("tabSubmitBtn");
    const btnTrack = document.getElementById("tabTrackBtn");

    if (tabName === "submit") {
        secSubmit.style.display = "block";
        secTrack.style.display = "none";
        btnSubmit.classList.add("active");
        btnTrack.classList.remove("active");
    } else {
        secSubmit.style.display = "none";
        secTrack.style.display = "block";
        btnSubmit.classList.remove("active");
        btnTrack.classList.add("active");
        loadMyComplaints();
    }
}

// ==========================================
// PHOTO UPLOAD HANDLING (OPTIONAL)
// ==========================================

function handlePhotoSelect(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];

    // Check size (< 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert("Selected image is larger than 5MB. Please choose a smaller photo.");
        input.value = "";
        return;
    }

    selectedPhotoFilename = file.name;
    const reader = new FileReader();
    reader.onload = (e) => {
        selectedPhotoBase64 = e.target.result;
        document.getElementById("dropzonePrompt").style.display = "none";
        const previewBox = document.getElementById("photoPreviewContainer");
        const previewImg = document.getElementById("photoPreviewImg");
        const previewName = document.getElementById("photoPreviewName");

        previewImg.src = selectedPhotoBase64;
        previewName.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
        previewBox.style.display = "flex";
    };
    reader.readAsDataURL(file);
}

function removeSelectedPhoto(event) {
    if (event) event.stopPropagation();
    selectedPhotoBase64 = null;
    selectedPhotoFilename = null;
    const fileInput = document.getElementById("complaintPhoto");
    if (fileInput) fileInput.value = "";

    document.getElementById("photoPreviewContainer").style.display = "none";
    document.getElementById("dropzonePrompt").style.display = "block";
}

// ==========================================
// PRESET & SUBMISSION
// ==========================================

function fillExample() {
    document.getElementById("studentName").value = currentStudent ? currentStudent.username : "VCET26";
    document.getElementById("location").value = "CSE Department - Cloud Lab 1";
    document.getElementById("category").value = "Network";
    document.getElementById("complaint").value = "Core Cisco switch in Cloud Lab 1 has lost power. Entire lab network is down and semester practical exams are scheduled in 45 minutes.";
}

async function handleComplaintSubmit() {
    const studentName = document.getElementById("studentName").value.trim();
    const location = document.getElementById("location").value.trim();
    const category = document.getElementById("category").value;
    const complaint = document.getElementById("complaint").value.trim();

    if (!studentName || !location || !complaint) {
        alert("Please fill in all mandatory fields (Student Roll/Name, Location, and Complaint description).");
        return;
    }

    const btn = document.getElementById("submitBtn");
    const btnText = document.getElementById("btnText");
    const btnSpinner = document.getElementById("btnSpinner");

    // UI Loading State
    btn.disabled = true;
    btnText.textContent = "Agent Analyzing & Routing Complaint...";
    btnSpinner.style.display = "inline-block";

    try {
        const payload = {
            student: studentName,
            location: location,
            category: category || undefined,
            complaint: complaint,
            photo_data: selectedPhotoBase64 || undefined
        };

        const response = await fetch("/api/complaints", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to submit complaint.");
        }

        const res = await response.json();
        const data = res.data;

        // Render Results
        renderComplaintResult(data);

        // Reset optional photo uploader
        removeSelectedPhoto();

        // Fetch student notifications
        fetchStudentNotifications(studentName);

        // Update tracking complaints count badge
        loadMyComplaints();

    } catch (err) {
        alert("Submission Error: " + err.message);
    } finally {
        btn.disabled = false;
        btnText.textContent = "⚡ Process with AI Agent";
        btnSpinner.style.display = "none";
    }
}

function renderComplaintResult(data) {
    const resultBox = document.getElementById("resultBox");
    resultBox.style.display = "block";

    const comp = data.complaint || {};
    const incident = data.incident || {};
    const staff = data.assigned_staff || {};

    document.getElementById("resTicketId").textContent = comp.id || "CMP-";
    document.getElementById("resDepartment").textContent = data.department || comp.department || "General";
    document.getElementById("resStaff").textContent = (staff.name ? `${staff.name} (${staff.role})` : comp.assigned_staff) || "Unassigned";

    // Priority Badge
    const prioEl = document.getElementById("resPriority");
    const priority = data.priority || comp.priority || "Medium";
    prioEl.textContent = priority.toUpperCase();
    prioEl.className = `priority-tag priority-${priority.toLowerCase()}`;

    // Status Badge
    const statusEl = document.getElementById("resStatus");
    const status = comp.status || "Submitted";
    statusEl.textContent = status;
    statusEl.className = `status-tag status-${status.toLowerCase().replace(/\s+/g, '-')}`;

    // Incident ID
    document.getElementById("resIncident").textContent = incident.incident_id || "Unique Incident";

    // Attached Photo in Result
    const photoBox = document.getElementById("resPhotoBox");
    const photoImg = document.getElementById("resPhotoImg");
    if (comp.photo_url) {
        photoImg.src = comp.photo_url;
        photoBox.style.display = "block";
    } else {
        photoBox.style.display = "none";
    }

    // Agent message
    document.getElementById("resAgentMessage").textContent = data.response_message || "Complaint registered and routed to designated department.";

    // Render Execution Timeline
    const timelineEl = document.getElementById("agentTimeline");
    timelineEl.innerHTML = "";

    const traces = data.agent_trace || [];
    traces.forEach((step, idx) => {
        const stepDiv = document.createElement("div");
        stepDiv.className = "timeline-item";
        stepDiv.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <span class="timeline-stage">${escapeHtml(step.stage || 'STAGE ' + (idx + 1))}</span>
                <h5>${escapeHtml(step.title || 'Step ' + (idx + 1))}</h5>
                <p>${escapeHtml(step.detail || '')}</p>
            </div>
        `;
        timelineEl.appendChild(stepDiv);
    });

    // Scroll to results
    resultBox.scrollIntoView({ behavior: "smooth" });
}

// ==========================================
// TRACK MY COMPLAINTS
// ==========================================

async function loadMyComplaints() {
    const stu = currentStudent ? currentStudent.username : (document.getElementById("studentName") ? document.getElementById("studentName").value.trim() : "VCET26");
    const targetStudent = stu || "VCET26";

    const listContainer = document.getElementById("myComplaintsList");
    const badge = document.getElementById("myTicketBadge");

    try {
        const res = await fetch(`/api/complaints?student_id=${encodeURIComponent(targetStudent)}`);
        if (!res.ok) return;
        const data = await res.json();
        const complaints = data.complaints || [];

        if (badge) badge.textContent = complaints.length;

        if (!listContainer) return;

        if (complaints.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <p>📭 No complaints found for student <strong>${escapeHtml(targetStudent)}</strong>.</p>
                    <button class="preset-btn" onclick="switchPortalTab('submit')">Submit Your First Grievance</button>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = complaints.map(c => renderComplaintTrackingCard(c)).join("");

    } catch (err) {
        if (listContainer) {
            listContainer.innerHTML = `<p class="text-center text-muted">Error loading complaints: ${escapeHtml(err.message)}</p>`;
        }
    }
}

function renderComplaintTrackingCard(c) {
    const priority = (c.priority || "Medium").toUpperCase();
    const status = c.status || "Submitted";
    const timeline = c.timeline || {};
    const subAt = formatDateTime(timeline.submitted_at || c.created_at);
    const deptSeenAt = timeline.department_seen_at ? formatDateTime(timeline.department_seen_at) : null;
    const mgmtSeenAt = timeline.management_seen_at ? formatDateTime(timeline.management_seen_at) : null;
    const actionAt = timeline.action_started_at ? formatDateTime(timeline.action_started_at) : null;
    const resolvedAt = timeline.resolved_at ? formatDateTime(timeline.resolved_at) : null;
    const durationFmt = timeline.resolution_duration_formatted || (c.resolution_duration ? c.resolution_duration : null);

    const hasPhoto = Boolean(c.photo_url);

    return `
        <div class="tracking-card" id="track-${c.id}">
            <div class="tracking-card-header">
                <div class="tracking-id-group">
                    <span class="ticket-id-tag">${escapeHtml(c.id)}</span>
                    <span class="priority-tag priority-${priority.toLowerCase()}">${priority}</span>
                    <span class="status-tag status-${status.toLowerCase().replace(/\s+/g, '-')}">${status}</span>
                </div>
                <div class="tracking-time-info">
                    <span class="text-muted">Submitted: ${subAt}</span>
                </div>
            </div>

            <div class="tracking-body">
                <div class="tracking-desc-col">
                    <p class="tracking-desc">${escapeHtml(c.complaint || '')}</p>
                    <div class="tracking-meta-chips">
                        <span class="meta-chip">🏢 <strong>${escapeHtml(c.department || 'General Administration')}</strong></span>
                        <span class="meta-chip">📍 ${escapeHtml(c.location || 'General Campus')}</span>
                        <span class="meta-chip">👤 Staff: ${escapeHtml(c.assigned_staff || 'Queued')}</span>
                        ${c.category ? `<span class="meta-chip">🏷️ ${escapeHtml(c.category)}</span>` : ''}
                    </div>
                </div>

                ${hasPhoto ? `
                    <div class="tracking-photo-col">
                        <img src="${c.photo_url}" alt="Complaint Photo" class="tracking-thumb" onclick="openImageModal('${c.photo_url}')" title="Click to view full image">
                        <small class="photo-hint">📷 Click to enlarge</small>
                    </div>
                ` : ''}
            </div>

            <!-- Complete 5-Stage Lifecycle Timeline -->
            <div class="lifecycle-timeline-container">
                <div class="lifecycle-header">
                    <h4>⏱️ Complete Grievance Lifecycle Timeline</h4>
                    ${durationFmt ? `<span class="duration-badge">⚡ Resolved in: <strong>${escapeHtml(durationFmt)}</strong></span>` : ''}
                </div>

                <div class="stages-tracker">
                    <!-- Stage 1: Submitted -->
                    <div class="stage-step completed">
                        <div class="stage-icon">📝</div>
                        <div class="stage-label">Submitted</div>
                        <div class="stage-time">${subAt}</div>
                    </div>

                    <!-- Stage 2: Department Seen -->
                    <div class="stage-step ${deptSeenAt ? 'completed' : 'pending'}">
                        <div class="stage-icon">👁️</div>
                        <div class="stage-label">Dept Seen</div>
                        <div class="stage-time">${deptSeenAt || 'Awaiting View'}</div>
                    </div>

                    <!-- Stage 3: Management Seen -->
                    <div class="stage-step ${mgmtSeenAt ? 'completed' : 'pending'}">
                        <div class="stage-icon">🛡️</div>
                        <div class="stage-label">Management Seen</div>
                        <div class="stage-time">${mgmtSeenAt || 'Pending Review'}</div>
                    </div>

                    <!-- Stage 4: Action Started -->
                    <div class="stage-step ${actionAt ? 'completed' : 'pending'}">
                        <div class="stage-icon">🛠️</div>
                        <div class="stage-label">Action Started</div>
                        <div class="stage-time">${actionAt || 'Pending Start'}</div>
                    </div>

                    <!-- Stage 5: Resolved -->
                    <div class="stage-step ${resolvedAt ? 'completed resolved-step' : 'pending'}">
                        <div class="stage-icon">✅</div>
                        <div class="stage-label">Resolved</div>
                        <div class="stage-time">${resolvedAt || 'In Progress'}</div>
                    </div>
                </div>
            </div>

            ${c.resolution_notes ? `
                <div class="resolution-notes-callout">
                    <strong>Resolution Notes:</strong> ${escapeHtml(c.resolution_notes)}
                </div>
            ` : ''}
        </div>
    `;
}

// ==========================================
// NOTIFICATIONS & MODALS
// ==========================================

async function fetchStudentNotifications(studentName) {
    try {
        const res = await fetch(`/api/notifications?student_id=${encodeURIComponent(studentName)}`);
        if (!res.ok) return;
        const data = await res.json();
        const notifList = document.getElementById("notifList");
        const notifsPanel = document.getElementById("studentNotifs");

        if (data.notifications && data.notifications.length > 0) {
            notifsPanel.style.display = "block";
            notifList.innerHTML = data.notifications.map(n => `
                <div class="notif-item ${n.read ? 'read' : 'unread'}">
                    <span class="notif-time">${formatDateTime(n.created_at)}</span>
                    <p>${escapeHtml(n.message)}</p>
                </div>
            `).join("");
        }
    } catch (e) {
        console.error("Could not fetch notifications:", e);
    }
}

function openImageModal(imgSrc) {
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImg");
    if (modal && modalImg) {
        modalImg.src = imgSrc;
        modal.style.display = "flex";
    }
}

function closeImageModal() {
    const modal = document.getElementById("imageModal");
    if (modal) modal.style.display = "none";
}

function formatDateTime(isoStr) {
    if (!isoStr) return "-";
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) +
            " " + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return isoStr;
    }
}

function escapeHtml(text) {
    if (!text) return "";
    return text.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
// Management & Department Dashboard Client Script - Smart College Support

let allComplaints = [];
let currentScope = "management"; // "management" or "department"
let selectedDepartment = "all";
let dashboardAnalytics = {};

document.addEventListener("DOMContentLoaded", () => {
    loadDashboardData();
    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

async function loadDashboardData() {
    await Promise.all([
        fetchDashboardAnalytics(),
        fetchComplaints(),
        fetchIncidents(),
        fetchNotifications()
    ]);
}

// ==========================================
// SCOPE & PERSPECTIVE SWITCHING
// ==========================================

function switchViewScope(scope) {
    currentScope = scope;
    const btnMgmt = document.getElementById("btnScopeMgmt");
    const btnDept = document.getElementById("btnScopeDept");
    const deptWrapper = document.getElementById("deptSelectorWrapper");

    if (scope === "management") {
        btnMgmt.classList.add("active");
        btnDept.classList.remove("active");
        deptWrapper.style.display = "none";
        selectedDepartment = "all";
        document.getElementById("deptSelect").value = "all";
    } else {
        btnMgmt.classList.remove("active");
        btnDept.classList.add("active");
        deptWrapper.style.display = "flex";
        selectedDepartment = document.getElementById("deptSelect").value || "all";
    }

    fetchComplaints();
}

function onDepartmentSelected(dept) {
    selectedDepartment = dept;
    fetchComplaints();
}

function switchAnalyticsTab(tab) {
    const panes = ["analyticsDateTab", "analyticsDeptTab", "analyticsTimeTab"];
    const pills = ["pillDateBtn", "pillDeptBtn", "pillTimeBtn"];

    panes.forEach(p => {
        const el = document.getElementById(p);
        if (el) el.style.display = "none";
    });
    pills.forEach(p => {
        const el = document.getElementById(p);
        if (el) el.classList.remove("active");
    });

    if (tab === "date") {
        document.getElementById("analyticsDateTab").style.display = "block";
        document.getElementById("pillDateBtn").classList.add("active");
    } else if (tab === "dept") {
        document.getElementById("analyticsDeptTab").style.display = "block";
        document.getElementById("pillDeptBtn").classList.add("active");
    } else if (tab === "time") {
        document.getElementById("analyticsTimeTab").style.display = "block";
        document.getElementById("pillTimeBtn").classList.add("active");
    }
}

// ==========================================
// DYNAMIC ANALYTICS FETCH & RENDER
// ==========================================

async function fetchDashboardAnalytics() {
    try {
        const res = await fetch("/api/stats/dashboard");
        if (!res.ok) return;
        const json = await res.json();
        dashboardAnalytics = json.analytics || {};

        renderKPIRibbon(dashboardAnalytics);
        renderDateWiseAnalytics(dashboardAnalytics.date_wise || []);
        renderDepartmentWiseAnalytics(dashboardAnalytics.department_wise || {}, dashboardAnalytics.total_complaints || 1);
        renderTimeWiseAnalytics(dashboardAnalytics.time_wise || {});
    } catch (err) {
        console.error("Error loading dashboard analytics:", err);
    }
}

function renderKPIRibbon(stats) {
    document.getElementById("todayCount").textContent = stats.today_received ?? 0;
    document.getElementById("totalCount").textContent = stats.total_complaints ?? 0;
    document.getElementById("pendingCount").textContent = stats.total_pending ?? 0;
    document.getElementById("resolvedCount").textContent = stats.total_resolved ?? 0;
    document.getElementById("avgDuration").textContent = stats.avg_resolution_time || "N/A";

    const dateLabel = document.getElementById("todayDateLabel");
    if (dateLabel) {
        const today = new Date();
        dateLabel.textContent = today.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    }
}

function renderDateWiseAnalytics(dateList) {
    const tbody = document.getElementById("dateWiseTableBody");
    if (!tbody) return;

    if (!dateList || dateList.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No date-wise records available yet.</td></tr>`;
        return;
    }

    tbody.innerHTML = dateList.map(item => {
        const ratio = item.received > 0 ? Math.round((item.resolved / item.received) * 100) : 0;
        return `
            <tr>
                <td><strong>📅 ${escapeHtml(item.date)}</strong></td>
                <td><span class="count-badge count-received">${item.received} Received</span></td>
                <td><span class="count-badge count-resolved">${item.resolved} Resolved</span></td>
                <td><span class="count-badge count-pending">${item.pending} Active</span></td>
                <td>
                    <div class="progress-bar-wrapper">
                        <div class="progress-bar-fill" style="width: ${ratio}%"></div>
                        <span class="progress-text">${ratio}%</span>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

function renderDepartmentWiseAnalytics(deptMap, total) {
    const container = document.getElementById("deptWiseCardsContainer");
    if (!container) return;

    const entries = Object.entries(deptMap);
    if (entries.length === 0) {
        container.innerHTML = `<p class="text-muted text-center">No department data available.</p>`;
        return;
    }

    container.innerHTML = entries.map(([dept, count]) => {
        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
        return `
            <div class="dept-card">
                <div class="dept-card-top">
                    <h4>🏢 ${escapeHtml(dept)}</h4>
                    <span class="dept-count-badge">${count} Complaints</span>
                </div>
                <div class="progress-bar-wrapper">
                    <div class="progress-bar-fill" style="width: ${pct}%"></div>
                </div>
                <small class="text-muted">${pct}% of all campus grievances</small>
            </div>
        `;
    }).join("");
}

function renderTimeWiseAnalytics(timeData) {
    const periodsContainer = document.getElementById("timePeriodsList");
    const hourlyContainer = document.getElementById("timeHourlyList");

    if (periodsContainer && timeData.periods) {
        periodsContainer.innerHTML = Object.entries(timeData.periods).map(([period, count]) => `
            <div class="period-item">
                <span class="period-title">${escapeHtml(period)}</span>
                <span class="period-count">${count} complaints</span>
            </div>
        `).join("");
    }

    if (hourlyContainer && timeData.hourly) {
        const maxVal = Math.max(...timeData.hourly.map(h => h.count), 1);
        hourlyContainer.innerHTML = timeData.hourly.map(h => {
            const hHeight = Math.max(12, Math.round((h.count / maxVal) * 80));
            return `
                <div class="hour-bar-col" title="${h.hour}: ${h.count} tickets">
                    <div class="hour-bar" style="height: ${hHeight}px; ${h.count > 0 ? 'background: #3b82f6;' : 'background: #cbd5e1;'}"></div>
                    <span class="hour-label">${h.hour.split(':')[0]}h</span>
                </div>
            `;
        }).join("");
    }
}

// ==========================================
// COMPLAINTS TABLE & TIMELINES
// ==========================================

async function fetchComplaints() {
    const status = document.getElementById("statusFilter") ? document.getElementById("statusFilter").value : "all";
    const priority = document.getElementById("priorityFilter") ? document.getElementById("priorityFilter").value : "all";
    const search = document.getElementById("searchInput") ? document.getElementById("searchInput").value.trim() : "";

    let url = `/api/complaints?status=${encodeURIComponent(status)}&priority=${encodeURIComponent(priority)}`;

    // Add department filter if active
    if (selectedDepartment && selectedDepartment !== "all") {
        url += `&department=${encodeURIComponent(selectedDepartment)}`;
    }

    if (search) {
        url += `&search=${encodeURIComponent(search)}`;
    }

    try {
        const res = await fetch(url);
        if (!res.ok) return;
        const json = await res.json();
        allComplaints = json.complaints || [];

        renderComplaintsTable(allComplaints);
        const countBadge = document.getElementById("complaintCountBadge");
        if (countBadge) countBadge.textContent = `${json.count} Tickets`;
    } catch (err) {
        console.error("Error loading complaints:", err);
    }
}

function handleSearch() {
    fetchComplaints();
}

function renderComplaintsTable(complaints) {
    const tbody = document.getElementById("complaintTableBody");
    if (!tbody) return;

    if (complaints.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center">No complaints matching the criteria.</td></tr>`;
        return;
    }

    tbody.innerHTML = complaints.map(c => {
        const priority = (c.priority || "Medium").toUpperCase();
        const status = c.status || "Submitted";
        const timeline = c.timeline || {};
        const subDateStr = timeline.submitted_at ? formatDateTime(timeline.submitted_at) : (c.created_at ? formatDateTime(c.created_at) : "-");
        const hasPhoto = Boolean(c.photo_url);

        return `
            <tr id="row-${c.id}">
                <td>
                    <strong>${escapeHtml(c.id)}</strong><br>
                    <small class="text-muted">🕒 ${subDateStr}</small>
                </td>
                <td>
                    <strong>${escapeHtml(c.student || 'Unknown')}</strong><br>
                    <small class="location-tag">📍 ${escapeHtml(c.location || 'N/A')}</small>
                </td>
                <td class="complaint-desc-cell">
                    <p class="desc-text">${escapeHtml(c.complaint || '')}</p>
                    ${c.category ? `<span class="category-pill">${escapeHtml(c.category)}</span>` : ''}
                </td>
                <td class="text-center">
                    ${hasPhoto ? `
                        <img src="${c.photo_url}" alt="Complaint Photo" class="table-photo-thumb" onclick="openImageModal('${c.photo_url}')" title="Click to view full photo">
                    ` : `<span class="text-muted text-no-photo">—</span>`}
                </td>
                <td>
                    <span class="dept-name">🏢 ${escapeHtml(c.department || 'General Administration')}</span><br>
                    <small class="staff-tag">👤 ${escapeHtml(c.assigned_staff || 'Queued')}</small>
                </td>
                <td>
                    <span class="priority-tag priority-${priority.toLowerCase()}">${priority}</span>
                </td>
                <td>
                    <select class="status-select status-${status.toLowerCase().replace(/\s+/g, '-')}" onchange="changeStatus('${c.id}', this.value)">
                        <option value="Submitted" ${status === 'Submitted' ? 'selected' : ''}>Submitted</option>
                        <option value="Seen" ${status === 'Seen' ? 'selected' : ''}>Seen</option>
                        <option value="Assigned" ${status === 'Assigned' ? 'selected' : ''}>Assigned</option>
                        <option value="Action Started" ${status === 'Action Started' ? 'selected' : ''}>Action Started</option>
                        <option value="In Progress" ${status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                        <option value="Resolved" ${status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                        <option value="Escalated" ${status === 'Escalated' ? 'selected' : ''}>Escalated</option>
                    </select>
                    <br>
                    <button class="btn-xs btn-timeline" onclick="viewComplaintTimeline('${c.id}')">⏱️ View Timeline</button>
                </td>
                <td class="action-cell">
                    <div class="action-buttons-stack">
                        ${!timeline.department_seen_at && currentScope === 'department' ? `
                            <button class="btn-sm btn-seen" onclick="markSeen('${c.id}', 'department')">👁️ Dept Seen</button>
                        ` : ''}
                        ${!timeline.management_seen_at && currentScope === 'management' ? `
                            <button class="btn-sm btn-seen" onclick="markSeen('${c.id}', 'management')">🛡️ Mgmt Seen</button>
                        ` : ''}
                        ${status !== 'Action Started' && status !== 'Resolved' && status !== 'In Progress' ? `
                            <button class="btn-sm btn-action" onclick="changeStatus('${c.id}', 'Action Started')">🛠️ Start Action</button>
                        ` : ''}
                        ${status !== 'Resolved' ? `
                            <button class="btn-sm btn-resolve" onclick="changeStatus('${c.id}', 'Resolved')">✓ Resolve</button>
                        ` : ''}
                        ${status !== 'Escalated' ? `
                            <button class="btn-sm btn-escalate" onclick="manualEscalate('${c.id}')">⚡ Escalate</button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

// ==========================================
// ACTIONS: SEEN, STATUS, ESCALATION
// ==========================================

async function markSeen(complaintId, role) {
    try {
        const res = await fetch(`/api/complaints/${complaintId}/seen`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role: role })
        });
        if (!res.ok) throw new Error("Failed to record seen timestamp");
        loadDashboardData();
    } catch (e) {
        alert("Error: " + e.message);
    }
}

async function changeStatus(complaintId, newStatus) {
    try {
        let notes = "";
        if (newStatus === "Resolved") {
            notes = prompt("Enter resolution notes:", "Grievance resolved and verified by department team.") || "Resolved";
        }

        const res = await fetch(`/api/complaints/${complaintId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus, resolution_notes: notes })
        });

        if (!res.ok) throw new Error("Failed to update status");
        loadDashboardData();
    } catch (e) {
        alert("Error updating status: " + e.message);
    }
}

async function manualEscalate(complaintId) {
    const reason = prompt("Enter reason for escalation:", "High academic / facility urgency reported");
    if (reason === null) return;

    try {
        const res = await fetch(`/api/complaints/${complaintId}/escalate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reason: reason || "Manual escalation" })
        });

        if (!res.ok) throw new Error("Failed to escalate");
        alert(`Complaint ${complaintId} has been escalated to Critical priority.`);
        loadDashboardData();
    } catch (e) {
        alert("Error escalating complaint: " + e.message);
    }
}

async function runSLACheck() {
    const btn = document.getElementById("slaBtn");
    btn.disabled = true;
    btn.textContent = "Scanning SLA tickets...";

    try {
        const res = await fetch("/api/escalation/run-check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ hours_threshold: 24 })
        });

        const data = await res.json();
        if (data.escalated_count > 0) {
            alert(`SLA Check Complete: ${data.escalated_count} overdue ticket(s) automatically escalated to Critical.`);
        } else {
            alert("SLA Check Complete: No complaints are currently overdue.");
        }
        loadDashboardData();
    } catch (e) {
        alert("Error running SLA check: " + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "⚡ Run SLA Escalation Sweep";
    }
}

// ==========================================
// TIMELINE MODAL
// ==========================================

function viewComplaintTimeline(complaintId) {
    const complaint = allComplaints.find(c => c.id === complaintId);
    if (!complaint) return;

    // Automatically record management view if in management scope
    if (currentScope === "management" && (!complaint.timeline || !complaint.timeline.management_seen_at)) {
        markSeen(complaintId, "management");
    } else if (currentScope === "department" && (!complaint.timeline || !complaint.timeline.department_seen_at)) {
        markSeen(complaintId, "department");
    }

    const t = complaint.timeline || {};
    const subAt = formatDateTime(t.submitted_at || complaint.created_at);
    const deptSeenAt = t.department_seen_at ? formatDateTime(t.department_seen_at) : null;
    const mgmtSeenAt = t.management_seen_at ? formatDateTime(t.management_seen_at) : null;
    const actionAt = t.action_started_at ? formatDateTime(t.action_started_at) : null;
    const resolvedAt = t.resolved_at ? formatDateTime(t.resolved_at) : null;
    const durationFmt = t.resolution_duration_formatted || (complaint.resolution_duration ? complaint.resolution_duration : null);

    const bodyEl = document.getElementById("timelineModalBody");
    bodyEl.innerHTML = `
        <div class="modal-ticket-header">
            <h3>⏱️ Complete Resolution Timeline: ${escapeHtml(complaint.id)}</h3>
            <span class="status-tag status-${(complaint.status || 'Pending').toLowerCase().replace(/\s+/g, '-')}">${complaint.status}</span>
        </div>

        <div class="ticket-quick-info">
            <p><strong>Student:</strong> ${escapeHtml(complaint.student || 'Unknown')} &bull; <strong>Department:</strong> ${escapeHtml(complaint.department || 'General')}</p>
            <p><strong>Issue:</strong> ${escapeHtml(complaint.complaint || '')}</p>
            ${complaint.photo_url ? `
                <div class="modal-photo-preview">
                    <strong>Attached Photo:</strong><br>
                    <img src="${complaint.photo_url}" alt="Complaint Photo" class="modal-thumb" onclick="openImageModal('${complaint.photo_url}')">
                </div>
            ` : ''}
        </div>

        <div class="detailed-stages-list">
            <!-- Stage 1 -->
            <div class="stage-row completed">
                <div class="stage-badge">1</div>
                <div class="stage-info">
                    <h4>📝 Complaint Submitted</h4>
                    <span class="stage-timestamp">${subAt}</span>
                    <p class="stage-subtext">Received and registered into system with initial AI routing.</p>
                </div>
            </div>

            <!-- Stage 2 -->
            <div class="stage-row ${deptSeenAt ? 'completed' : 'pending'}">
                <div class="stage-badge">2</div>
                <div class="stage-info">
                    <h4>👁️ Department Viewed / Seen</h4>
                    <span class="stage-timestamp">${deptSeenAt || 'Awaiting Department Review'}</span>
                    <p class="stage-subtext">Viewed by assigned department staff (${escapeHtml(complaint.department)}).</p>
                </div>
            </div>

            <!-- Stage 3 -->
            <div class="stage-row ${mgmtSeenAt ? 'completed' : 'pending'}">
                <div class="stage-badge">3</div>
                <div class="stage-info">
                    <h4>🛡️ Management Viewed / Seen</h4>
                    <span class="stage-timestamp">${mgmtSeenAt || 'Awaiting Management Review'}</span>
                    <p class="stage-subtext">Monitored by Campus Management Administration.</p>
                </div>
            </div>

            <!-- Stage 4 -->
            <div class="stage-row ${actionAt ? 'completed' : 'pending'}">
                <div class="stage-badge">4</div>
                <div class="stage-info">
                    <h4>🛠️ Action Started</h4>
                    <span class="stage-timestamp">${actionAt || 'Action not yet started'}</span>
                    <p class="stage-subtext">Staff assigned and physical or technical remediation commenced.</p>
                </div>
            </div>

            <!-- Stage 5 -->
            <div class="stage-row ${resolvedAt ? 'completed resolved-row' : 'pending'}">
                <div class="stage-badge">5</div>
                <div class="stage-info">
                    <h4>✅ Grievance Resolved</h4>
                    <span class="stage-timestamp">${resolvedAt || 'Awaiting resolution completion'}</span>
                    <p class="stage-subtext">Issue remediated and confirmed with student notification dispatched.</p>
                </div>
            </div>
        </div>

        ${durationFmt ? `
            <div class="modal-duration-footer">
                <span>⏱️ Total Resolution Time:</span>
                <strong>${escapeHtml(durationFmt)}</strong>
            </div>
        ` : ''}

        <div class="modal-actions-footer">
            <button class="action-btn secondary" onclick="closeTimelineModal()">Close</button>
        </div>
    `;

    document.getElementById("timelineModal").style.display = "flex";
}

function closeTimelineModal() {
    const modal = document.getElementById("timelineModal");
    if (modal) modal.style.display = "none";
}

// ==========================================
// INCIDENTS & NOTIFICATIONS
// ==========================================

async function fetchIncidents() {
    try {
        const res = await fetch("/api/incidents");
        if (!res.ok) return;
        const json = await res.json();
        const container = document.getElementById("incidentsContainer");
        if (!container) return;

        const incidents = json.incidents || [];
        document.getElementById("incidentCount").textContent = incidents.length;

        if (incidents.length === 0) {
            container.innerHTML = `<p class="text-muted">No incident clusters formed yet.</p>`;
            return;
        }

        container.innerHTML = incidents.map(inc => `
            <div class="incident-card-item">
                <div class="incident-header">
                    <strong>${escapeHtml(inc.incident_id)}</strong>
                    <span class="incident-badge">${escapeHtml(inc.category || 'General')}</span>
                </div>
                <p><strong>Affected Students (${(inc.affected_students || []).length}):</strong> ${(inc.affected_students || []).join(", ")}</p>
                <p><strong>Linked Tickets (${(inc.complaints || []).length}):</strong> ${(inc.complaints || []).join(", ")}</p>
            </div>
        `).join("");
    } catch (e) {
        console.error("Error loading incidents:", e);
    }
}

async function fetchNotifications() {
    try {
        const res = await fetch("/api/notifications");
        if (!res.ok) return;
        const json = await res.json();
        const feed = document.getElementById("activityFeed");
        if (!feed) return;

        const notifs = json.notifications || [];
        if (notifs.length === 0) {
            feed.innerHTML = `<p class="text-muted">No recent notifications logged.</p>`;
            return;
        }

        feed.innerHTML = notifs.slice(0, 10).map(n => `
            <div class="feed-item">
                <div class="feed-time">${formatDateTime(n.created_at)}</div>
                <div class="feed-body">
                    <strong>To: ${escapeHtml(n.student_id)}</strong>
                    <p>${escapeHtml(n.message)}</p>
                </div>
            </div>
        `).join("");
    } catch (e) {
        console.error("Error loading notifications:", e);
    }
}

// ==========================================
// PHOTO MODAL
// ==========================================

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

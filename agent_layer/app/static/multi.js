(function () {
  "use strict";
  const API = "";
  const $ = (id) => document.getElementById(id);
  const state = { actorId: new URLSearchParams(location.search).get("student") || localStorage.getItem("tender.student") || "S01", token: null, groups: [], group: null, events: [], model: null, roster: {}, timer: null };
  function esc(value) { return String(value == null ? "" : value).replace(/[&<>"']/g, (x) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[x])); }
  function toast(message, error) { const el = $("toast"); el.textContent = message; el.className = "toast show" + (error ? " error" : ""); clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => { el.className = "toast"; }, 3000); }
  async function ensureSession() {
    if (state.token) return state.token;
    const response = await fetch(API + "/auth/demo-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_id: state.actorId, role: "learner", learner_id: state.actorId }) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "无法连接");
    state.token = data.token; $("connectionText").textContent = "已连接";
    return state.token;
  }
  async function api(path, options, token) {
    options = options || {};
    token = token || await ensureSession();
    const headers = Object.assign({}, options.headers || {}, { Authorization: "Bearer " + token, "X-Tender-Actor": state.actorId, "X-Tender-Role": "learner", "X-Tender-Learner": state.actorId });
    const response = await fetch(API + path, Object.assign({}, options, { headers }));
    const raw = await response.text();
    let data = null;
    if (raw) { try { data = JSON.parse(raw); } catch (_) { data = null; } }
    if (!response.ok) throw new Error((data && (data.detail || data.message)) || ("请求失败：" + response.status));
    return data || {};
  }
  async function loadRoster() {
    try {
      const response = await fetch(API + "/students");
      if (!response.ok) return;
      const rows = await response.json();
      (Array.isArray(rows) ? rows : []).forEach((item) => { const id = item.student_id || item.id; if (id) state.roster[id] = item.name || id; });
      try { const account = JSON.parse(localStorage.getItem("tender.account") || "null"); if (account && account.studentId) state.roster[account.studentId] = account.displayName || state.roster[account.studentId] || account.studentId; } catch (_) {}
    } catch (_) {}
  }
  function actorName(id) { return state.roster[id] || id; }
  function timeLabel(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("zh-CN", {month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}); }
  function renderGroups() {
    const list = $("groupList");
    if (!state.groups.length) { list.innerHTML = '<div class="empty-small">还没有多人场景<br>点右上角＋创建</div>'; return; }
    list.innerHTML = state.groups.map((group) => '<button class="group-item' + (state.group && state.group.group_id === group.group_id ? " active" : "") + '" data-group="' + esc(group.group_id) + '"><strong>' + esc(group.purpose) + '</strong><span>' + esc((group.role || "member") + " · " + timeLabel(group.updated_at)) + '</span></button>').join("");
    list.querySelectorAll("[data-group]").forEach((button) => button.onclick = () => selectGroup(button.dataset.group));
  }
  async function loadGroups(selectId) {
    const data = await api("/group-sessions");
    state.groups = Array.isArray(data.sessions) ? data.sessions : [];
    const target = selectId || (state.group && state.group.group_id) || (state.groups[0] && state.groups[0].group_id);
    if (target) await selectGroup(target, false); else renderEmpty();
  }
  function renderEmpty() {
    state.group = null; state.events = []; state.model = null;
    $("groupTitle").textContent = "还没有多人场景";
    $("groupSubtitle").textContent = "创建一个群后，这里会显示群体公开数据。";
    $("inviteBtn").disabled = true; $("groupCode").textContent = "—";
    $("memberCount").textContent = "0"; $("eventStat").textContent = "0"; $("branchStat").textContent = "0"; $("decisionState").textContent = "—"; $("sideMemberCount").textContent = "0";
    $("memberList").innerHTML = '<div class="empty-small">暂无成员</div>';
    $("groupModel").innerHTML = '<p>暂无数据</p>';
    $("eventList").innerHTML = '<p>暂无数据</p>';
    renderGroups();
  }
  async function selectGroup(groupId) {
    try {
      const [group, events, model] = await Promise.all([api("/group-sessions/" + encodeURIComponent(groupId)), api("/group-sessions/" + encodeURIComponent(groupId) + "/events?limit=100"), api("/group-sessions/" + encodeURIComponent(groupId) + "/model")]);
      state.group = group; state.events = (events.events || []).slice().reverse(); state.model = model;
      $("groupTitle").textContent = group.purpose;
      $("groupSubtitle").textContent = (group.member_count || 0) + " 位成员 · 仅展示群公开数据";
      $("inviteBtn").disabled = false; $("groupCode").textContent = group.group_id;
      $("memberCount").textContent = group.member_count || 0;
      $("eventStat").textContent = model.public_event_count || 0;
      $("branchStat").textContent = (model.shared_branches || []).length;
      $("decisionState").textContent = model.decision_state || "—";
      $("sideMemberCount").textContent = group.member_count || 0;
      renderGroups(); renderMembers(); renderModel(); renderEvents();
    } catch (error) { toast("多人数据加载失败：" + error.message, true); }
  }
  function renderMembers() {
    const members = state.group.members || [];
    $("memberList").innerHTML = members.map((member) => '<div class="member"><b>' + esc(actorName(member.actor_id)) + '</b><small>' + esc(member.role) + '</small></div>').join("") || '<div class="empty-small">暂无成员</div>';
  }
  function renderModel() {
    const model = state.model || {};
    $("groupModel").innerHTML = [
      ["公开事件", model.public_event_count || 0],
      ["开放问题", model.open_questions || 0],
      ["已确认承诺", model.commitment_count || 0],
      ["决策", model.decision_count || 0],
      ["参与均衡", model.participation_balance == null ? "证据不足" : model.participation_balance],
      ["私人模型访问", model.private_member_models_accessed ? "异常" : "未访问"]
    ].map(([label,value]) => '<div class="detail-item"><span>' + label + '</span><b>' + esc(value) + '</b></div>').join("");
  }
  function renderEvents() {
    const events = state.events.slice(-20).reverse();
    $("eventList").innerHTML = events.map((event) => {
      const content = (event.payload && event.payload.content) || (event.payload && event.payload.summary) || event.event_type || "群公开事件";
      return '<div class="event-row"><time>' + esc(timeLabel(event.created_at)) + '</time><span><b>' + esc(actorName(event.actor_id)) + '</b> · ' + esc(content) + '</span></div>';
    }).join("") || '<p>暂无公开事件。</p>';
  }
  async function createGroup(event) {
    event.preventDefault();
    const purpose = $("groupPurpose").value.trim();
    if (!purpose) { toast("先填写群目标。", true); return; }
    $("createGroupBtn").disabled = true;
    try {
      const group = await api("/group-sessions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ platform: "group_chat", purpose: purpose }) });
      $("newGroupForm").hidden = true; $("groupPurpose").value = "";
      await loadGroups(group.group_id); toast("多人场景已创建。");
    } catch (error) { toast("创建失败：" + error.message, true); }
    finally { $("createGroupBtn").disabled = false; }
  }
  async function copyGroupId() {
    if (!state.group) return;
    try { await navigator.clipboard.writeText(state.group.group_id); toast("群号已复制。"); } catch (_) { toast(state.group.group_id); }
  }
  function bind() {
    $("newGroupToggle").onclick = () => { $("newGroupForm").hidden = !$("newGroupForm").hidden; if (!$("newGroupForm").hidden) $("groupPurpose").focus(); };
    $("newGroupForm").onsubmit = createGroup;
    $("inviteBtn").onclick = copyGroupId;
  }
  async function boot() {
    bind(); await loadRoster();
    try { await loadGroups(); $("connectionText").textContent = "已连接"; } catch (error) { $("connectionText").textContent = "连接失败"; toast(error.message, true); }
    state.timer = setInterval(() => { if (!document.hidden && state.group) selectGroup(state.group.group_id); }, 8000);
  }
  boot();
})();

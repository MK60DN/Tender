var API = "";
var state = { students: [], currentStudent: (localStorage.getItem("tender.student") || "S01"), agents: [], currentAgent: "fixed_mentalization_companion", currentPage: "learner", fixedAgentIds: [], agentBusy: false, tender: {}, learner: {}, mentalization: {}, overview: {}, last: null, ambient: {active: false, card: null, lastActivity: Date.now(), focusStart: Date.now(), switches: [], timer: null, busy: false, monitoringBound: false, scenario: "gaokao_registration"}, roles: [], currentRole: (localStorage.getItem("tender.role") || "learner"), roleInfo: null, workbenchThreads: [], currentWorkbenchThread: null, authToken: null, authBusy: null };

function $(id) { return document.getElementById(id); }
function authActor() {
  return state.currentRole === "parent" ? "P-" + state.currentStudent : state.currentStudent;
}
function ensureSession() {
  if (state.authToken) return Promise.resolve(state.authToken);
  if (state.authBusy) return state.authBusy;
  state.authBusy = fetch(API + "/auth/demo-session", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({actor_id: authActor(), role: state.currentRole || "learner", learner_id: state.currentStudent})
  }).then(function (r) {
    return r.json().then(function (data) {
      if (!r.ok) throw new Error(data.detail || "无法建立会话");
      state.authToken = data.token;
      state.authBusy = null;
      return data.token;
    });
  }).catch(function (e) { state.authBusy = null; throw e; });
  return state.authBusy;
}
function api(path, opts) {
  opts = opts || {};
  return ensureSession().then(function (token) {
    var headers = Object.assign({}, opts.headers || {});
    var actor = authActor();
    headers["Authorization"] = "Bearer " + token;
    headers["X-Tender-Actor"] = actor;
    headers["X-Tender-Role"] = state.currentRole || "learner";
    headers["X-Tender-Learner"] = state.currentStudent;
    var requestOptions = Object.assign({}, opts, {headers: headers});
    return fetch(API + path, requestOptions);
  }).then(function (r) {
    return r.text().then(function (raw) {
      var data = null;
      if (raw) {
        try { data = JSON.parse(raw); } catch (e) { data = null; }
      }
      if (!r.ok) {
        var detail = data && (data.detail || data.message);
        if (!detail && r.status === 403) detail = "尚未获得这项能力的使用授权";
        if (!detail && r.status === 404) detail = "暂时没有找到这项内容";
        if (!detail && r.status >= 500) detail = "服务暂时不可用，请稍后重试";
        throw new Error(detail || ("请求未完成（" + r.status + "）"));
      }
      if (!raw) return {};
      if (data === null) throw new Error("服务返回了无法读取的数据");
      return data;
    });
  });
}
function on(id, eventName, handler) {
  var el = $(id); if (el) el.addEventListener(eventName, handler);
}
function setBusy(id, busy) {
  var el = $(id);
  if (!el) return;
  el.disabled = !!busy;
  el.setAttribute("aria-busy", busy ? "true" : "false");
}
function supportLabel(value) {
  if (value === "agent-runtime") return "Tender 实时支持";
  if (value === "structured_fallback" || value === "legacy") return "Tender 安全回退";
  return "Tender 心智化支持";
}
function supportMeta() { return "已关联当前状态与授权证据"; }
function categoryLabel(value) {
  var labels = {mentalization:"心智化", emotion_cognition:"认知情绪调节", metacognition:"元认知", family_support:"家庭支持", learning_support:"学习支持", career:"生涯发展", health:"健康", nutrition:"营养", neurocognitive:"神经认知", safety:"安全保护"};
  return labels[value] || value || "能力";
}
function eventLabel(value) {
  var labels = {head_teacher_note:"学习观察记录", mentalization_snapshot:"心智状态快照", agent_reflection:"学习反思", student_reflection:"学习反思", advisor_route:"专业支持路由", assessment_result:"学习结果", learning_task_completed:"任务完成", parent_support:"家庭支持记录"};
  return labels[value] || "学习记录";
}
function evidenceLabel(e) {
  var summary = e && e.summary ? String(e.summary) : "";
  if (!summary || (e && summary === e.event_type) || /^[a-z0-9_:-]+$/i.test(summary)) return eventLabel(e && e.event_type);
  return summary;
}
function renderAssistantMarkup(text) {
  var safe = esc(text || "");
  safe = safe.replace(/^#{1,6}\s*(.+)$/gm, '<span class="message-heading">$1</span>');
  safe = safe.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/^-\s+/gm, '• ');
  return safe;
}
function fmt(v, d) {
  if (v === null || v === undefined) return "-";
  if (typeof v === "number") return v.toFixed(d === undefined ? 3 : d);
  return String(v);
}
function clamp(v) { v = Number(v); if (isNaN(v)) return 0; return Math.max(0, Math.min(1, v)); }
function esc(s) {
  return String(s === null || s === undefined ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}
function setStatus(ok, text) {
  var dot = $("statusDot");
  if (dot) dot.style.background = ok ? "var(--ok)" : "var(--danger)";
  var t = $("statusText"); if (t) t.textContent = text;
}
function switchPage(page) {
  if (state.roleInfo && state.roleInfo.nav) { var allowed = state.roleInfo.nav.some(function (n) { return n.page === page; }); if (!allowed) { page = state.roleInfo.default_page || "learner"; } }
  var target = $("page-" + page);
  if (!target) page = "learner";
  state.currentPage = page;
  var pages = document.querySelectorAll(".page");
  for (var i = 0; i < pages.length; i++) pages[i].classList.remove("active");
  target = $("page-" + page); if (target) { target.classList.add("active"); target.scrollTop = 0; }
  var navs = document.querySelectorAll(".nav");
  for (var j = 0; j < navs.length; j++) {
    var active = navs[j].getAttribute("data-page") === page;
    navs[j].classList.toggle("active", active);
    if (active) navs[j].setAttribute("aria-current", "page"); else navs[j].removeAttribute("aria-current");
  }
  if ($("clearChatBtn")) $("clearChatBtn").hidden = page !== "agent";
  var titles = { learner: "此刻与我", timeline: "心智时间线", market: "Agent 市场", parent: "家庭端", tutor: "教师工作台（兼容）", subjectteacher: "教师工作台", dorm: "宿管端", institution: "机构管理端", workflow: "产品工作流", headteacher: "班主任工作台", sales: "销售作战台", lifelong: "学习路径", agent: "心智化伙伴", dashboard: "总览", student: "学习证据", teacher: "教师", daoql: "DAOQL", reports: "报告", workbench: "协作任务", advisor: "专业顾问工作台" };
  var title = titles[page] || "Tender";
  $("pageTitle").textContent = title;
  document.title = "Tender · " + title;
  if (page === "learner") { loadLearnerHome(); }
  if (page === "timeline") { loadTimeline(); }
  if (page === "market") { loadAgentMarket(); }
  if (page === "parent") { loadParentHome(); }
  if (page === "tutor") { loadTutorHome(); }
  if (page === "subjectteacher") { loadSubjectTeacher(); }
  if (page === "dorm") { loadDorm(); }
  if (page === "institution") { loadInstitutionHome(); }
  if (page === "workflow") { loadWorkflow(); }
  if (page === "headteacher") { loadHeadTeacher(); }
  if (page === "sales") { loadSales(); }
  if (page === "lifelong") { loadLifelong(); }
  if (page === "dashboard") { loadOverview(); loadTender(); }
  if (page === "student") { loadTender(); }
  if (page === "teacher") { loadTeacher(); }
  if (page === "daoql") { loadDaoql(); }
  if (page === "reports") { loadReports(); }
  if (page === "workbench") { loadWorkbench(); }
  if (page === "advisor") { loadAdvisorHome(); }
}
function roleById(id) {
  for (var i = 0; i < state.roles.length; i++) if (state.roles[i].id === id) return state.roles[i];
  return null;
}
function renderRoleNav(role) {
  var nav = $("nav"); nav.innerHTML = "";
  (role.nav || []).forEach(function (item) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "nav" + (item.page === role.default_page ? " active" : "");
    b.setAttribute("data-page", item.page);
    b.setAttribute("aria-controls", "page-" + item.page);
    if (item.page === role.default_page) b.setAttribute("aria-current", "page");
    b.innerHTML = "<span aria-hidden='true'>" + esc(item.icon || "·") + "</span> " + esc(item.label || item.page);
    b.onclick = function () { switchPage(item.page); };
    nav.appendChild(b);
  });
}
function applyRole(roleId) {
  if (roleId === "tutor" || roleId === "subject_teacher") roleId = "teacher";
  var role = roleById(roleId) || roleById("learner");
  if (!role) return;
  state.currentRole = role.id; state.roleInfo = role; state.authToken = null; localStorage.setItem("tender.role", role.id);
  $("roleSelect").value = role.id;
  $("roleSelect").disabled = false;
  $("roleScope").textContent = role.scope || "";
  renderRoleNav(role);
  switchPage(role.default_page || "learner");
}
function loadRoles() {
  return api("/roles?surface=consumer").then(function (r) {
    state.roles = r.roles || [];
    var sel = $("roleSelect"); sel.innerHTML = "";
    if (!state.roles.length) {
      var empty = document.createElement("option"); empty.value = ""; empty.textContent = "暂无可进入的角色"; sel.appendChild(empty);
      $("roleScope").textContent = "产品入口尚未准备好，请稍后刷新。";
      return;
    }
    state.roles.forEach(function (role) {
      var o = document.createElement("option");
      o.value = role.id; o.textContent = role.name + " · " + role.audience;
      sel.appendChild(o);
    });
    sel.onchange = function () { applyRole(sel.value); };
    applyRole(state.currentRole);
    sel.disabled = false;
  });
}
function reloadCurrentPage() {
  switchPage(state.currentPage || (state.roleInfo && state.roleInfo.default_page) || "learner");
}
function loadCurrentRoleHome() {
  if (state.currentRole === "parent") return loadParentHome();
  if (state.currentRole === "teacher") return loadSubjectTeacher();
  if (["health_advisor","nutrition_advisor","neurocognitive_advisor","psychology_advisor","learning_science_advisor","career_advisor","safety_advisor"].indexOf(state.currentRole) >= 0) return loadAdvisorHome();
  if (state.currentRole === "dorm_supervisor") return loadDorm();
  if (state.currentRole === "institution") return loadInstitutionHome();
  if (state.currentRole === "head_teacher") return loadHeadTeacher();
  if (state.currentRole === "sales") return loadSales();
  return loadLearnerHome();
}
function loadStudents() {
  return api("/students").then(function (x) {
    state.students = Array.isArray(x) ? x : [];
    var sel = $("studentSelect"); sel.innerHTML = "";
    if (!state.students.length) {
      var empty = document.createElement("option"); empty.value = ""; empty.textContent = "暂无学习者";
      sel.appendChild(empty); sel.disabled = true;
      setStatus(false, "暂无可用的学习者记录");
      return;
    }
    state.students.forEach(function (s) {
      var o = document.createElement("option"); o.value = s.student_id;
      o.textContent = s.student_id + " · " + s.name + " (" + s.class + ")"; sel.appendChild(o);
    });
    if (!state.students.some(function (s) { return s.student_id === state.currentStudent; })) {
      state.currentStudent = state.students[0].student_id;
    }
    sel.value = state.currentStudent;
    sel.disabled = false;
    if ($("contextStudent")) $("contextStudent").textContent = state.currentStudent;
    sel.onchange = function () {
      state.currentStudent = sel.value;
      state.authToken = null;
      localStorage.setItem("tender.student", state.currentStudent);
      if ($("contextStudent")) $("contextStudent").textContent = state.currentStudent;
      reloadCurrentPage();
    };
  });
}
function timelineTime(value) {
  if (!value) return "时间未记录";
  return String(value).replace("T", " ").slice(0, 19);
}
function loadTimeline() {
  var sid = state.currentStudent;
  if ($("timelineStudent")) $("timelineStudent").textContent = sid;
  if ($("timelineList")) {
    $("timelineList").setAttribute("aria-busy", "true");
    $("timelineList").innerHTML = '<p class="muted">正在读取时间线…</p>';
  }
  if ($("timelineCausal")) $("timelineCausal").innerHTML = '<p class="muted">正在读取因果链…</p>';
  return api("/learner/mentalization/timeline/" + encodeURIComponent(sid)).then(function (r) {
    var points = Array.isArray(r.points) ? r.points : [];
    var links = Array.isArray(r.causal_links) ? r.causal_links : [];
    $("timelineList").innerHTML = points.length ? points.slice().reverse().map(function (p) {
      var emo = p.emotion && typeof p.emotion === "object" ? p.emotion : {};
      var stateNow = p.state && typeof p.state === "object" ? p.state : {};
      return '<div class="ctx-block timeline-entry"><div class="kv"><span>' + esc(timelineTime(p.timestamp)) + '</span><b>' + esc(eventLabel(p.event_type)) + '</b></div>' +
        '<p><b>' + esc(p.summary || "状态记录") + '</b> · 置信度 ' + (Number(p.confidence || 0) * 100).toFixed(0) + '%</p>' +
        '<p class="muted">情绪：' + esc(emo.label || "未观测") + ' · 掌握度 ' + fmt(stateNow.mastery) + ' · 元认知偏差 ' + fmt(stateNow.jol_bias) + '</p></div>';
    }).join("") : '<p class="muted">还没有时间点。点击“记录此刻”形成第一条认知—情绪快照。</p>';
    $("timelineCausal").innerHTML = links.length ? links.map(function (x) {
      var source = x.source_id || x.source || "";
      var target = x.target_id || x.target || "";
      return '<div class="kv"><span>' + esc(x.relation_label || x.relation || "关联") + '</span><b>' + esc(String(source).slice(-8) || "起点") + ' → ' + esc(String(target).slice(-8) || "结果") + '</b></div>';
    }).join("") : '<p class="muted">暂时没有足够的支持—结果链。继续记录反思与后续表现后会出现。</p>';
    if ($("timelineStatus")) $("timelineStatus").textContent = points.length ? "已更新，共 " + points.length + " 条状态记录。" : "还没有状态记录。";
  }).catch(function (e) {
    if ($("timelineList")) $("timelineList").innerHTML = '<p class="error-text">时间线暂时无法加载。</p>';
    if ($("timelineCausal")) $("timelineCausal").innerHTML = '<p class="error-text">因果链暂时无法读取。</p>';
    if ($("timelineStatus")) $("timelineStatus").textContent = "加载失败：" + e.message;
  }).finally(function () {
    if ($("timelineList")) $("timelineList").setAttribute("aria-busy", "false");
  });
}
function recordMentalizationSnapshot() {
  var sid = state.currentStudent;
  if (!sid) { $("timelineStatus").textContent = "请先选择学习者。"; return; }
  setBusy("recordSnapshotBtn", true);
  $("timelineStatus").textContent = "正在记录此刻…";
  api("/learner/mentalization/snapshot/" + encodeURIComponent(sid), {method: "POST"}).then(function (r) {
    var snapshot = r.snapshot || {};
    $("timelineStatus").textContent = "已记录：" + (snapshot.summary || "状态快照");
    return loadTimeline();
  }).catch(function (e) { $("timelineStatus").textContent = "记录失败：" + e.message; })
    .finally(function () { setBusy("recordSnapshotBtn", false); });
}
function renderAgentCards(host, agents, options) {
  options = options || {};
  if (!host) return;
  agents = Array.isArray(agents) ? agents : [];
  host.innerHTML = agents.length ? agents.map(function (a) {
    var owned = (options.owned || {})[a.agent_id];
    var isOwner = a.owner_id && a.owner_id === state.currentStudent;
    var action = "";
    if (options.fixed) {
      action = '<button class="ghost chat-agent" type="button" data-agent="' + esc(a.agent_id) + '">与它对话</button>';
    } else if (options.market) {
      action = isOwner ? '<span class="pill">我的上架</span><button class="ghost use-agent" type="button" data-agent="' + esc(a.agent_id) + '" data-name="' + esc(a.name) + '">试用我的 Agent</button>' :
        owned ? '<span class="pill accent">已授权</span>' :
        '<button class="ghost buy-agent" type="button" data-agent="' + esc(a.agent_id) + '" data-name="' + esc(a.name) + '" data-price="' + esc(a.price || 0) + '">购买授权 ¥' + fmt(a.price || 0, 0) + '</button>';
      if (owned && !isOwner) action += '<button class="ghost use-agent" type="button" data-agent="' + esc(a.agent_id) + '" data-name="' + esc(a.name) + '">调用专家</button>';
    } else if (options.usable && owned) {
      action = '<button class="ghost use-agent" type="button" data-agent="' + esc(a.agent_id) + '" data-name="' + esc(a.name) + '">调用专家</button>';
    }
    return '<div class="ctx-block agent-card"><div class="agent-card-head"><span class="agent-name">' + esc(a.name || "专家 Agent") + '</span><b>' + esc(categoryLabel(a.category_label || a.category)) + '</b></div><p class="muted">' + esc(a.description || "这项能力会在授权范围内提供支持。") + '</p><div class="agent-card-actions">' + action + '</div></div>';
  }).join("") : '<p class="muted">' + esc(options.emptyText || "暂无内容。") + '</p>';
}
function bindAgentMarketActions() {
  var buttons = document.querySelectorAll('.buy-agent');
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].onclick = function () {
      purchaseExpertAgent(this.getAttribute("data-agent"), this.getAttribute("data-name"), Number(this.getAttribute("data-price") || 0), this);
    };
  }
  var chats = document.querySelectorAll('.chat-agent');
  for (var j = 0; j < chats.length; j++) chats[j].onclick = function () { openFixedAgent(this.getAttribute("data-agent")); };
  var uses = document.querySelectorAll('.use-agent');
  for (var k = 0; k < uses.length; k++) uses[k].onclick = function () { invokeSelectedAgent(this.getAttribute("data-agent"), this.getAttribute("data-name"), this); };
}
function openFixedAgent(agentId) {
  if (!agentId) return;
  state.currentAgent = agentId;
  if ($("agentSelect")) $("agentSelect").value = agentId;
  switchPage("agent");
  if ($("agentMessage")) $("agentMessage").focus();
}
function setAgentMarketNote(text) {
  if ($("agentMarketStatus")) $("agentMarketStatus").textContent = text;
}
function loadAgentMarket() {
  var sid = state.currentStudent;
  if (!sid) { setAgentMarketNote("请先选择学习者。"); return Promise.resolve(); }
  var query = encodeURIComponent(($("agentSearch").value || "").trim());
  if ($("agentMarketList")) $("agentMarketList").setAttribute("aria-busy", "true");
  setAgentMarketNote("正在加载常驻支持与专家能力…");
  var runtimeRequest = api("/agent-runtime/status").catch(function () { return null; });
  return Promise.all([api("/agents/fixed"), api("/agents/marketplace?query=" + query), api("/agents/entitlements/" + encodeURIComponent(sid)), runtimeRequest]).then(function (all) {
    var fixed = Array.isArray(all[0].agents) ? all[0].agents : [];
    var market = Array.isArray(all[1].expert_agents) ? all[1].expert_agents : [];
    var ent = all[2] || {};
    var runtime = all[3];
    state.fixedAgentIds = fixed.map(function (a) { return a.agent_id; });
    $("agentRuntimeStatusLine").textContent = runtime && runtime.model_ready ? "固定支持与专家能力已就绪；协作结果会关联授权证据。" : "固定支持已就绪；专家能力可能使用安全回退方式完成。";
    var owned = {};
    fixed.forEach(function (a) { owned[a.agent_id] = true; });
    (ent.purchased_agents || []).forEach(function (p) { owned[p.agent_id] = true; });
    renderAgentCards($("fixedAgentList"), fixed, {fixed: true, emptyText: "常驻支持暂时不可用。"});
    var purchased = (ent.purchased_agents || []).map(function (p) { return p.agent || p; }).filter(Boolean);
    renderAgentCards($("agentEntitlements"), purchased, {usable: true, owned: owned, emptyText: "还没有购买或授权使用的专家 Agent。"});
    renderAgentCards($("agentMarketList"), market, {market: true, owned: owned, emptyText: query ? "没有找到匹配的专家 Agent。" : "市场暂时没有可用的专家 Agent。"});
    bindAgentMarketActions();
    setAgentMarketNote(market.length ? "共 " + market.length + " 项专家能力可供查看。" : "专家能力市场暂时为空。");
  }).catch(function (e) {
    if ($("fixedAgentList")) $("fixedAgentList").innerHTML = '<p class="error-text">常驻支持暂时无法加载。</p>';
    if ($("agentEntitlements")) $("agentEntitlements").innerHTML = '<p class="error-text">授权能力暂时无法读取。</p>';
    if ($("agentMarketList")) $("agentMarketList").innerHTML = '<p class="error-text">专家市场暂时无法加载。</p>';
    setAgentMarketNote("市场加载失败：" + e.message);
  }).finally(function () {
    if ($("agentMarketList")) $("agentMarketList").setAttribute("aria-busy", "false");
  });
}
function generateExpertAgent() {
  var need = ($("agentNeed").value || "").trim();
  if (!state.currentStudent) { $("agentGenerateStatus").textContent = "请先选择学习者。"; return; }
  if (!need) { $("agentGenerateStatus").textContent = "先描述你希望 Agent 解决什么问题。"; return; }
  var rawPrice = Number($("agentPrice").value || 0);
  if (!isFinite(rawPrice) || rawPrice < 0) { $("agentGenerateStatus").textContent = "售价需要填写为非负数字。"; return; }
  var price = Math.round(rawPrice * 100);
  setBusy("generateAgentBtn", true);
  $("agentGenerateStatus").textContent = "正在生成并校验 AgentSpec…";
  api("/agents/generate", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({
    owner_id: state.currentStudent, need: need, name: $("agentName").value || "", category: $("agentCategory").value,
    price_cents: price, visibility: $("agentVisibility").value
  })}).then(function (r) {
    var agent = r.agent || {};
    state.lastGeneratedAgent = {agent_id: agent.agent_id, name: agent.name || "刚生成的专家 Agent"};
    $("agentGenerateStatus").textContent = "已生成 " + state.lastGeneratedAgent.name + "；当前状态：" + (agent.status || "待审核") + "。";
    if ($("generatedAgentActions")) $("generatedAgentActions").hidden = false;
    $("agentNeed").value = ""; $("agentName").value = ""; $("agentPrice").value = "";
    return loadAgentMarket();
  }).catch(function (e) { $("agentGenerateStatus").textContent = "生成失败：" + e.message; })
    .finally(function () { setBusy("generateAgentBtn", false); });
}
function invokeSelectedAgent(agentId, agentName, button) {
  if (!agentId) return;
  if (!state.currentStudent) { setAgentMarketNote("请先选择学习者。"); return; }
  if (button) { button.disabled = true; button.setAttribute("aria-busy", "true"); }
  setAgentMarketNote("正在调用" + (agentName ? "「" + agentName + "」" : "专家") + "…");
  var prompt = (($("agentInvokePrompt") || {}).value || "").trim() || "请基于当前授权摘要，给出一个最低必要支持。";
  api("/agents/" + encodeURIComponent(agentId) + "/invoke", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({
    student_id: state.currentStudent, actor_id: state.currentStudent, message: prompt, intent: "mentalization_support"
  })}).then(function (r) {
    var a = r.action || {};
    if ($("agentInvokeResult")) $("agentInvokeResult").hidden = false;
    if ($("agentInvokeText")) $("agentInvokeText").textContent = a.text || a.summary || "专家已返回建议。";
    if ($("agentInvokeNext")) $("agentInvokeNext").textContent = a.next_action ? "下一步：" + a.next_action : "下一步：选择最小的一步开始。";
    if ($("agentInvokeBoundary")) $("agentInvokeBoundary").textContent = a.boundary || "建议仅用于学习支持，不构成诊断。";
    setAgentMarketNote("调用完成；结果已写入你的授权范围。");
  }).catch(function (e) {
    setAgentMarketNote("调用失败：" + e.message);
  }).finally(function () {
    if (button) { button.disabled = false; button.setAttribute("aria-busy", "false"); }
  });
}
function purchaseExpertAgent(agentId, agentName, price, button) {
  if (!agentId || !state.currentStudent) return;
  var label = agentName || "这项专家能力";
  if (!window.confirm("确认购买「" + label + "」的使用授权（¥" + Number(price || 0).toFixed(2) + "）吗？")) return;
  if (button) { button.disabled = true; button.setAttribute("aria-busy", "true"); }
  setAgentMarketNote("正在开通授权…");
  api("/agents/" + encodeURIComponent(agentId) + "/purchase", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({buyer_id: state.currentStudent})})
    .then(function (r) {
      setAgentMarketNote(r.already_owned ? "这项能力已经在你的授权范围内。" : "购买成功，授权已生效。");
      return loadAgentMarket();
    }).catch(function (e) {
      setAgentMarketNote("购买失败：" + e.message);
    }).finally(function () {
      if (button) { button.disabled = false; button.setAttribute("aria-busy", "false"); }
    });
}
function agencyStorageKey() { return "tender.agency." + (state.currentStudent || "unknown"); }
function getAgencyDraft() {
  return {
    goal: ($("agencyGoal") && $("agencyGoal").value || "").trim(),
    reason: ($("agencyReason") && $("agencyReason").value || "").trim(),
    action: ($("agencyAction") && $("agencyAction").value || "").trim(),
    responsibility: ($("agencyResponsibility") && $("agencyResponsibility").value || "").trim(),
    result: ($("agencyResult") && $("agencyResult").value || "").trim(),
    outcome: ($("agencyOutcome") && $("agencyOutcome").value || "").trim(),
    reflection: ($("learnerReflection") && $("learnerReflection").value || "").trim()
  };
}
function saveAgencyDraft() {
  try { localStorage.setItem(agencyStorageKey(), JSON.stringify(getAgencyDraft())); } catch (e) { /* local draft is optional */ }
  updateDiscoveryLoop();
}
function loadAgencyDraft() {
  var draft = {};
  try { draft = JSON.parse(localStorage.getItem(agencyStorageKey()) || "{}") || {}; } catch (e) { draft = {}; }
  var fields = {agencyGoal:"goal", agencyReason:"reason", agencyAction:"action", agencyResponsibility:"responsibility", agencyResult:"result", agencyOutcome:"outcome", learnerReflection:"reflection"};
  Object.keys(fields).forEach(function (id) { if ($(id)) $(id).value = typeof draft[fields[id]] === "string" ? draft[fields[id]] : ""; });
  updateDiscoveryLoop();
}
function updateDiscoveryLoop() {
  if (!$("discoveryLoop")) return;
  var draft = getAgencyDraft();
  var hypothesis = state.mentalization && state.mentalization.summary ? String(state.mentalization.summary).trim() : "";
  var done = {
    goal: !!draft.goal,
    hypothesis: !!hypothesis,
    action: !!draft.action,
    result: !!(draft.result || draft.outcome),
    responsibility: !!draft.responsibility,
    update: !!draft.reflection
  };
  var labels = {goal:"选择目标", hypothesis:"理解局部假设", action:"采取最小行动", result:"记录真实结果", responsibility:"确认责任归属", update:"写下下一轮更新"};
  var order = ["goal", "hypothesis", "action", "result", "responsibility", "update"];
  var firstIncomplete = null;
  order.forEach(function (key) { if (!done[key] && !firstIncomplete) firstIncomplete = key; });
  var steps = document.querySelectorAll("[data-discovery-step]");
  for (var i = 0; i < steps.length; i++) {
    var key = steps[i].getAttribute("data-discovery-step");
    steps[i].classList.toggle("done", !!done[key]);
    steps[i].classList.toggle("current", key === firstIncomplete);
    if (key === firstIncomplete) steps[i].setAttribute("aria-current", "step"); else steps[i].removeAttribute("aria-current");
  }
  if ($("discoveryHypothesis")) $("discoveryHypothesis").textContent = hypothesis || "等待状态解释";
  if ($("discoveryState")) $("discoveryState").textContent = firstIncomplete ? "下一步：" + labels[firstIncomplete] : "可记录本轮发现";
}
function initAgencyForm() {
  if (!$("agencyForm")) return;
  var ids = ["agencyGoal", "agencyReason", "agencyAction", "agencyResponsibility", "agencyResult", "agencyOutcome", "learnerReflection"];
  ids.forEach(function (id) {
    var el = $(id); if (!el) return;
    el.addEventListener("input", saveAgencyDraft);
    el.addEventListener("change", saveAgencyDraft);
  });
  loadAgencyDraft();
}
function renderMentalization(m) {
  var host = $("learnerMentalization"); if (!host) return;
  m = m || {};
  state.mentalization = m;
  var emotion = m.emotion_context && typeof m.emotion_context === "object" ? m.emotion_context : {};
  var snapshot = m.state_snapshot && typeof m.state_snapshot === "object" ? m.state_snapshot : {};
  var hyps = Array.isArray(m.hypotheses) ? m.hypotheses : [];
  var hypothesisHtml = hyps.slice(0, 3).map(function (h) {
    var evidence = Array.isArray(h.evidence) ? h.evidence : (h.evidence ? [h.evidence] : []);
    return '<li><b>' + esc(h.label || "待验证假设") + '</b>（' + (Number(h.score || 0) * 100).toFixed(0) + '%）' + (evidence.length ? '<span class="muted"> ' + esc(evidence.join("；")) + '</span>' : '') + '</li>';
  }).join("");
  host.innerHTML = '<div class="kv"><span>当前假设</span><b>' + esc(m.summary || "等待更多记录") + '</b></div>' +
    '<div class="kv"><span>置信度</span><b>' + (m.confidence === undefined ? "-" : (Number(m.confidence) * 100).toFixed(0) + "%") + '</b></div>' +
    '<div class="kv"><span>情绪上下文</span><b>' + esc(emotion.label || "未观测") + '</b></div>' +
    '<div class="kv"><span>证据事件</span><b>' + (snapshot.event_count === undefined ? 0 : snapshot.event_count) + '</b></div>' +
    '<h4>可检验假设</h4><ul class="actions">' + (hypothesisHtml || '<li class="muted">暂时没有足够证据形成假设。</li>') + '</ul>' +
    '<p class="muted">' + esc(m.boundary || "状态假设不是临床诊断。") + '</p>';
  updateDiscoveryLoop();
}
function submitLearnerReflection() {
  var draft = getAgencyDraft();
  if (!draft.goal) { $("learnerReflectionStatus").textContent = "先写下这次选择追求的目标。"; $("agencyGoal").focus(); return; }
  if (!draft.action) { $("learnerReflectionStatus").textContent = "写下最小行动，才能进行现实检验。"; $("agencyAction").focus(); return; }
  if (!draft.outcome) { $("learnerReflectionStatus").textContent = "记录真实结果，才能完成这一轮发现。"; $("agencyOutcome").focus(); return; }
  if (!draft.reflection) { $("learnerReflectionStatus").textContent = "写下结果与反思，才能完成这一轮更新。"; $("learnerReflection").focus(); return; }
  saveAgencyDraft();
  var hypothesis = ($("discoveryHypothesis") && $("discoveryHypothesis").textContent || "等待状态解释").trim();
  var responsibilityLabels = {self:"学习者本人", shared:"学习者与支持者共同承担", support:"学习者在支持下承担"};
  var options = [
    {id:"selected", label:draft.goal},
    {id:"alternative", label:"保留其他可能路径，先观察"}
  ];
  var mentalization = state.mentalization || {};
  var supports = Array.isArray(mentalization.support_options) ? mentalization.support_options : [];
  if (supports.length) options.push({id:"suggested", label:supports[0].label || "采用系统建议的最小支持"});
  setBusy("learnerReflectionBtn", true);
  $("learnerReflectionStatus").textContent = "正在创建发现型学习循环…";
  api("/decision-loops", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      learner_id: state.currentStudent,
      goal: draft.goal,
      options: options,
      selected_option_id: "selected",
      choice_reason: draft.reason || "用户主动选择该目标",
      state: {mentalization_summary: hypothesis, draft_goal: draft.goal}
    })
  }).then(function (created) {
    var loopId = created.decision_loop.loop_id;
    $("learnerReflectionStatus").textContent = "循环已创建，正在记录行动…";
    return api("/decision-loops/" + encodeURIComponent(loopId) + "/actions", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        action: draft.action,
        expected_outcome: draft.outcome || "形成可观察的下一步结果",
        state: {mentalization_summary: hypothesis, chosen_option: "selected"}
      })
    });
  }).then(function (acted) {
    var loopId = acted.decision_loop.loop_id;
    $("learnerReflectionStatus").textContent = "行动已记录，正在回写真实结果与责任…";
    return api("/decision-loops/" + encodeURIComponent(loopId) + "/results", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        actual_result: draft.outcome,
        responsibility_owner: responsibilityLabels[draft.responsibility] || "学习者本人",
        reflection: draft.reflection,
        state: {mentalization_summary: hypothesis, final_reflection: draft.reflection}
      })
    });
  }).then(function (completed) {
    var loopId = completed.decision_loop.loop_id;
    var answer = [
      "【目标】" + draft.goal,
      "【选择理由】" + (draft.reason || "未填写"),
      "【局部假设】" + hypothesis,
      "【最小行动】" + draft.action,
      "【真实结果】" + draft.outcome,
      "【责任归属】" + (responsibilityLabels[draft.responsibility] || "学习者本人"),
      "【结果与反思】" + draft.reflection
    ].join("\n");
    return api("/learner/reflection/" + encodeURIComponent(state.currentStudent), {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({prompt: "发现型学习循环完成：" + loopId, answer: answer})
    }).then(function (reflection) { return {loopId: loopId, reflection: reflection}; });
  }).then(function (result) {
    $("learnerReflectionStatus").textContent = "本轮发现已写入结构化决策循环、时间线和因果链。";
    renderMentalization(result.reflection.mentalization || {});
    try { localStorage.removeItem(agencyStorageKey()); } catch (e) {}
    ["agencyGoal","agencyReason","agencyAction","agencyResponsibility","agencyOutcome","learnerReflection"].forEach(function (id) { if ($(id)) $(id).value = ""; });
    if ($("agencyResult")) $("agencyResult").value = "done";
    updateDiscoveryLoop();
    return loadLearnerHome();
  }).catch(function (e) { $("learnerReflectionStatus").textContent = "记录失败：" + e.message; })
    .finally(function () { setBusy("learnerReflectionBtn", false); });
}
function loadCognitiveConstructs() {
  var host = $("cognitiveConstructs");
  if (!host) return Promise.resolve();
  return api("/cognition/constructs").then(function (catalog) {
    var items = catalog.constructs || [];
    host.innerHTML = items.map(function (item) {
      return '<article class="construct-item"><div class="construct-top"><span class="construct-name">' + esc(item.name) + '</span><span class="construct-grade">' + esc(item.evidence_grade || "待校准") + '</span></div><p>' + esc(item.definition) + '</p><small>' + esc((item.requires || []).join(" · ")) + '</small></article>';
    }).join("") || '<p class="muted">认知构念模型尚未返回内容。</p>';
  }).catch(function () {
    host.innerHTML = '<p class="muted">认知构念模型暂时不可用；页面其他功能不受影响。</p>';
  });
}
function loadLearnerHome() {
  var sid = state.currentStudent;
  loadCognitiveConstructs();
  if ($("agencyForm")) { state.mentalization = {}; loadAgencyDraft(); }
  return api("/learner/home/" + sid).then(function (r) {
    state.learner = r;
    var p = r.profile || {}, passport = r.passport || {}, skills = passport.skills || {};
    var meta = passport.metacognition || {}, portability = r.portability || {}, plan = r.plan || {};
    $("learnerIntro").innerHTML = (p.name ? p.name + "，" : "") + "Tender 只维护当前决定所需的局部认知—情绪假设；你选择目标、采取行动、承担结果，再用真实反馈更新它。<br><span class=\"intro-en\">Tender keeps only the local cognitive–emotional hypotheses needed for the current decision. You choose the goal, act, own the outcome, and update the model with real feedback.</span>";
    $("learnerTenderId").textContent = r.tender_id || ("TENDER-" + sid);
    $("learnerStage").textContent = r.current_stage || p.class || "学段未标注";
    $("learnerOwnership").textContent = r.data_ownership || "数据归学习者";
    $("learnerPortability").textContent = portability.score === undefined ? "-" : (Number(portability.score) * 100).toFixed(0) + "%";
    $("learnerPortabilityNote").textContent = (portability.label || "数据可携带度") + "：" + (portability.note || "只表示记录覆盖程度，不评价学习者。");
    $("learnerMastery").textContent = fmt(skills.mastery);
    $("learnerEvents").textContent = passport.learning_events === undefined ? "-" : passport.learning_events;
    $("learnerBias").textContent = fmt(meta.jol_bias);
    $("learnerHesitation").textContent = fmt(meta.hesitation);
    renderMentalization(r.mentalization || {});
    $("learnerActions").innerHTML = (plan.next_actions || []).map(function (a) { return "<li>" + esc(a) + "</li>"; }).join("") || '<li class="muted">保持当前节奏，做迁移题</li>';
    $("learnerPlanNote").textContent = "预计 " + (plan.estimated_minutes || 10) + " 分钟 · " + (plan.mode || "连续记录、最低必要提示与可撤回授权");
    var coach = r.ai_coach || {};
    $("learnerCoach").innerHTML = '<div class="kv"><span>支持状态</span><b>Tender 心智化支持</b></div>' +
      '<div class="kv"><span>连续记录</span><b>已关联</b></div>' +
      '<p class="muted">' + esc(coach.suggestion || "先预测，再作答，后复盘。") + '</p>' +
      '<p class="muted">' + esc(coach.prompt || "") + '</p>';
    var evidence = passport.evidence || [];
    $("learnerPassport").innerHTML = '<div class="kv"><span>学习事件</span><b>' + (passport.learning_events || 0) + '</b></div>' +
      '<div class="kv"><span>作品证据</span><b>' + ((passport.portfolio || {}).evidence_count || evidence.length) + '</b></div>' +
      '<div class="kv"><span>分阶段授权</span><b>可撤销</b></div>' +
      '<div class="kv"><span>数据导出</span><b>' + ((r.privacy || {}).exportable ? "支持" : "待接入") + '</b></div>' +
      (evidence.length ? '<h4>最近证据</h4><ul class="actions">' + evidence.slice(-3).reverse().map(function (e) { return '<li>' + esc(evidenceLabel(e)) + '</li>'; }).join("") + '</ul>' : '<p class="muted">还没有足够事件形成护照证据。</p>');
    var support = r.support_network || [];
    $("learnerSupportNetwork").innerHTML = support.length ? support.map(function (a) { return '<div class="ctx-block"><div class="kv"><span>' + esc(a.name) + '</span><b>' + esc(a.status || "按需调用") + '</b></div><p class="muted">' + esc(a.focus || "") + '</p></div>'; }).join("") : '<p class="muted">当前只需要 Tender 陪伴；专业支持会在需要时出现。</p>';
    $("learnerMarketplaceNote").textContent = (r.marketplace || {}).note || "专业支持网络按需开放。";
    var credentials = passport.credentials || [];
    $("learnerCredentials").innerHTML = credentials.length ? credentials.map(function (c) { return '<div class="kv"><span>' + esc(c.name || c) + '</span><b>可验证</b></div>'; }).join("") : '<div class="kv"><span>凭证钱包</span><b>待积累</b></div><p class="muted">反思、项目和可验证成果会在完成学习闭环后进入这里。</p>';
    var community = r.community || {};
    $("learnerCommunity").innerHTML = (community.groups || []).length ? community.groups.map(function (g) { return '<div class="kv"><span>' + esc(g.name || g) + '</span><b>已加入</b></div>'; }).join("") : '<p class="muted">' + esc(community.note || "学习小组 / 同伴互评待接入") + '</p>' + '<p class="muted">默认先发展自己，再按需协作；不强迫抱团。</p>';
  }).catch(function (e) {
    if ($("learnerMentalization")) $("learnerMentalization").innerHTML = '<p class="error-text">此刻状态暂时无法读取，请稍后刷新。</p>';
    if ($("learnerActions")) $("learnerActions").innerHTML = '<li class="muted">支持建议暂时不可用。</li>';
    if ($("learnerCoach")) $("learnerCoach").innerHTML = '<p class="muted">学习伙伴暂时不可用。</p>';
    setStatus(false, "学习者首页加载失败：" + e.message);
  });
}
function loadParentHome() {
  var sid = state.currentStudent;
  return api("/roles/parent/home?student_id=" + encodeURIComponent(sid)).then(function (r) {
    var d = r.data || {}, child = d.child || {}, passport = child.passport || {};
    var skills = passport.skills || {}, meta = passport.metacognition || {}, report = d.parent_report || {};
    $("parentChildLabel").textContent = ((child.profile || {}).name || sid) + " · " + ((child.profile || {}).class || "当前子女");
    $("parentMastery").textContent = fmt(skills.mastery);
    $("parentEvents").textContent = passport.learning_events || 0;
    $("parentBias").textContent = fmt(meta.jol_bias);
    $("parentHesitation").textContent = fmt(meta.hesitation);
    var evidence = passport.evidence || [];
    $("parentEvidence").innerHTML = evidence.length ? '<ul class="actions">' + evidence.slice(-4).reverse().map(function (e) { return "<li>" + esc(evidenceLabel(e)) + "</li>"; }).join("") + "</ul>" : '<p class="muted">暂无可展示的学习证据。</p>';
    var actions = [report.one_home_action || "每天用 10 分钟做一次先预测、再作答、后复盘。", "先问孩子卡在哪里，不直接用一次成绩贴标签。", "发现情绪变化时，先确认需求，再讨论学习方法。"];
    $("parentActions").innerHTML = actions.map(function (a) { return "<li>" + esc(a) + "</li>"; }).join("");
    $("parentPrivacy").innerHTML = '<div class="kv"><span>原始对话</span><b>不展示</b></div><div class="kv"><span>完整行为链</span><b>不展示</b></div><div class="kv"><span>授权范围</span><b>仅子女成长证据</b></div><div class="kv"><span>授权撤回</span><b>支持</b></div><p class="muted">家长端看趋势和建议，不代替孩子做全部决定。</p>';
    $("parentReportView").textContent = JSON.stringify(report, null, 2);
  }).catch(function (e) { setStatus(false, "家长端加载失败：" + e.message); });
}

function loadTutorHome() {
  var sid = state.currentStudent;
  var cls = sid.charAt(0) === "A" ? "文科班" : "理科班";
  return api("/roles/tutor/home?student_id=" + encodeURIComponent(sid) + "&class_id=" + encodeURIComponent(cls)).then(function (r) {
    var d = r.data || {}, report = d.teacher_report || {}, learner = d.sample_learner || {};
    var passport = learner.passport || {}, evidence = passport.evidence || [];
    $("tutorClassLabel").textContent = cls;
    $("tutorStudents").textContent = report.n_students || 0;
    $("tutorMastery").textContent = fmt(report.class_mastery_mean);
    $("tutorPriority").textContent = (report.top_intervention || []).length;
    var rows = (report.top_intervention || []).map(function (x) { return "<tr><td>" + esc(x.student_id) + "</td><td>" + fmt(x.mastery) + "</td><td>" + fmt(x.jol_bias) + "</td><td>" + fmt(x.hesitation) + "</td></tr>"; }).join("");
    $("tutorPriorityList").innerHTML = '<div class="table-wrap"><table><tr><th>学生</th><th>掌握度</th><th>JOL 偏差</th><th>犹豫</th></tr>' + rows + '</table></div>';
    var plan = [report.suggestion || "先处理低掌握 + 高犹豫的学生。"];
    (learner.plan || {}).next_actions && (learner.plan.next_actions).forEach(function (a) { plan.push(a); });
    $("tutorPlan").innerHTML = plan.map(function (a) { return "<li>" + esc(a) + "</li>"; }).join("");
    $("tutorStudentEvidence").innerHTML = evidence.length ? '<div class="kv"><span>学生</span><b>' + esc(sid) + '</b></div><div class="kv"><span>学习事件</span><b>' + (passport.learning_events || 0) + '</b></div><ul class="actions">' + evidence.slice(-3).reverse().map(function (e) { return "<li>" + esc(evidenceLabel(e)) + "</li>"; }).join("") + "</ul>" : '<p class="muted">暂无可展示的学生证据。</p>';
    $("tutorMarketplace").innerHTML = '<div class="kv"><span>教师身份</span><b>独立教师</b></div><div class="kv"><span>市场状态</span><b>计划项</b></div><p class="muted">' + esc((learner.marketplace || {}).note || "独立教师市场待接入；当前只展示授权范围。") + '</p>';
  }).catch(function (e) { setStatus(false, "独立教师端加载失败：" + e.message); });
}

function statusOptions(selected) {
  var opts = [["in_school", "在校"], ["dorm", "在寝"], ["leave", "请假"], ["external_training", "外出集训"], ["commuting", "跑校"], ["absent", "未归/异常"], ["unknown", "未登记"]];
  return opts.map(function (x) { return '<option value="' + x[0] + '"' + (x[0] === selected ? ' selected' : '') + '>' + x[1] + '</option>'; }).join("");
}
function loadSubjectTeacher() {
  var cls = $("stClassSelect") ? $("stClassSelect").value : "理科班";
  var mode = $("stTeacherMode") ? $("stTeacherMode").value : "independent";
  return api("/roles/teacher/home?class_id=" + encodeURIComponent(cls) + "&teacher_mode=" + encodeURIComponent(mode)).then(function (r) {
    var d = r.data || {}, tasks = d.tasks || [], board = d.status_board || {};
    $("stClassLabel").textContent = (d.teacher_mode_meta && d.teacher_mode_meta.label) || (mode === "independent" ? "独立教师" : "机构任课教师");
    $("stTasks").textContent = tasks.length;
    $("stPending").textContent = tasks.filter(function (x) { return x.status !== "completed"; }).length;
    $("stStudents").textContent = (d.students || []).length;
    $("stStatusPending").textContent = (board.pending_verification_ids || []).length;
    $("stTaskList").innerHTML = tasks.length ? tasks.map(function (t) {
      var done = t.status === "completed";
      return '<div class="ctx-block"><div class="kv"><span>' + esc(t.subject) + ' · ' + esc(t.teacher_id) + '</span><b>' + esc(t.status) + '</b></div><p><b>' + esc(t.title) + '</b></p><p class="muted">' + esc(t.instructions || "") + '</p><p class="muted">截止：' + esc(t.due_at || "未设置") + '</p>' + (done ? '<p class="muted">已完成：' + esc(t.completed_by || "") + ' ' + esc(t.completion_note || "") + '</p>' : '<button class="ghost st-complete" data-task="' + esc(t.task_event_id) + '">标记班主任已完成</button>') + '</div>';
    }).join("") : '<p class="muted">还没有派发任务。</p>';
    var btns = document.querySelectorAll(".st-complete");
    for (var i = 0; i < btns.length; i++) btns[i].onclick = function () { completeTeachingTask(this.getAttribute("data-task")); };
    $("stStatusBoard").innerHTML = (board.students || []).slice(0, 12).map(function (s) { return '<div class="kv"><span>' + esc(s.student_id) + ' · ' + esc(s.name) + '</span><b>' + esc(s.status_label) + '</b></div>'; }).join("");
  }).catch(function (e) { setStatus(false, "教师工作台加载失败：" + e.message); });
}
function createTeachingTask() {
  var cls = $("stClassSelect").value, subject = $("stTaskSubject").value.trim(), title = $("stTaskTitle").value.trim();
  var instructions = $("stTaskInstructions").value.trim(), due = $("stTaskDue").value.trim();
  if (!subject || !title) { $("stTaskStatus").textContent = "请填写学科和任务标题。"; return; }
  $("stCreateTaskBtn").disabled = true; $("stTaskStatus").textContent = "正在派单…";
  api("/teaching/tasks/" + encodeURIComponent(cls), {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({class_id: cls, teacher_id: "current_teacher", subject: subject, title: title, instructions: instructions, due_at: due || null, student_ids: []})})
    .then(function () { $("stTaskStatus").textContent = "已派单，班主任端会收到待办。"; $("stTaskTitle").value = ""; $("stTaskInstructions").value = ""; $("stTaskDue").value = ""; loadSubjectTeacher(); })
    .catch(function (e) { $("stTaskStatus").textContent = "派单失败：" + e.message; })
    .finally(function () { $("stCreateTaskBtn").disabled = false; });
}
function completeTeachingTask(taskEventId) {
  var cls = $("stClassSelect").value;
  api("/teaching/tasks/" + encodeURIComponent(cls) + "/" + encodeURIComponent(taskEventId) + "/complete", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({completed_by: "head_teacher", note: "班主任端确认完成"})})
    .then(function () { loadSubjectTeacher(); })
    .catch(function (e) { setStatus(false, "任务完成失败：" + e.message); });
}
function loadDorm() {
  var cls = $("dormClassSelect") ? $("dormClassSelect").value : "理科班";
  return api("/roles/dorm_supervisor/home?class_id=" + encodeURIComponent(cls)).then(function (r) {
    var d = r.data || {}, board = d.status_board || {}, counts = board.counts || {};
    $("dormExpected").textContent = (board.expected_in_dorm_ids || []).length;
    $("dormChecked").textContent = counts.dorm || 0;
    $("dormExceptions").textContent = (board.exception_ids || []).length;
    $("dormPending").textContent = (board.pending_verification_ids || []).length;
    $("dormBoard").innerHTML = '<div class="table-wrap"><table><tr><th>学生</th><th>状态</th><th>更新时间</th><th>操作</th></tr>' + (board.students || []).map(function (s) {
      return '<tr><td>' + esc(s.student_id) + ' · ' + esc(s.name || "") + '</td><td><select class="dorm-status" data-student="' + esc(s.student_id) + '">' + statusOptions(s.status) + '</select></td><td>' + esc((s.updated_at || "未登记").slice(0, 19)) + '</td><td><button class="ghost dorm-save" data-student="' + esc(s.student_id) + '">确认</button></td></tr>';
    }).join("") + '</table></div>';
    var savers = document.querySelectorAll(".dorm-save");
    for (var i = 0; i < savers.length; i++) savers[i].onclick = function () { saveDormStatus(this.getAttribute("data-student")); };
    $("dormReport").innerHTML = '<div class="kv"><span>应查在寝</span><b>' + (board.expected_in_dorm_ids || []).length + '</b></div><div class="kv"><span>已确认在寝</span><b>' + (counts.dorm || 0) + '</b></div><div class="kv"><span>异常</span><b>' + (board.exception_ids || []).length + '</b></div><div class="kv"><span>待核验</span><b>' + (board.pending_verification_ids || []).length + '</b></div><p class="muted">unknown 不等于在寝；确认后再生成正式巡查报告。</p>';
  }).catch(function (e) { setStatus(false, "宿管端加载失败：" + e.message); });
}
function saveDormStatus(studentId) {
  var cls = $("dormClassSelect").value;
  var sel = document.querySelector('.dorm-status[data-student="' + studentId + '"]');
  if (!sel) return;
  api("/student-status/" + encodeURIComponent(cls), {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({student_id: studentId, status: sel.value, note: "宿管端人工核对"})})
    .then(function () { loadDorm(); })
    .catch(function (e) { setStatus(false, "状态更新失败：" + e.message); });
}
var WEEKDAY_LABELS = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"};
function renderInstitutionPerformance(items) {
  var rows = (items || []).map(function (p) {
    var score = p.score === null || p.score === undefined ? "证据不足" : fmt(p.score, 1);
    var load = p.workload || {};
    return '<tr><td>' + esc(p.head_teacher_label) + '</td><td>' + score + '</td><td>' + esc(p.level) + '</td><td>' + (Number(p.data_coverage || 0) * 100).toFixed(0) + '%</td><td>' + (load.risk_alerts || 0) + ' 风险 / ' + (load.teaching_tasks || 0) + ' 任务</td><td>' + (load.pending_parent_messages || 0) + '</td></tr>';
  }).join("");
  $("institutionPerformance").innerHTML = '<div class="table-wrap"><table><tr><th>班主任</th><th>复核分</th><th>状态</th><th>证据覆盖</th><th>工作量</th><th>待确认家长消息</th></tr>' + rows + '</table></div>';
  var first = (items || [])[0] || {};
  var metrics = (first.metrics || []).map(function (m) { return '<div class="kv"><span>' + esc(m.label) + '</span><b>' + (m.value === null ? "证据不足" : (Number(m.value) * 100).toFixed(0) + '%') + '</b></div>'; }).join("");
  var excluded = (first.excluded_dimensions || []).join("、");
  $("institutionPerformanceNote").innerHTML = metrics + '<p class="muted">' + esc(first.decision_rule || "仅用于复核和支持，不自动用于处罚或公开排名。") + '</p><p class="muted">不纳入：' + esc(excluded) + '</p>';
}
function renderInstitutionSchedule(items) {
  var rows = (items || []).map(function (x) {
    return '<tr><td>' + esc(WEEKDAY_LABELS[x.weekday] || x.weekday) + '</td><td>' + esc(x.start_time) + '–' + esc(x.end_time) + '</td><td>' + esc(x.teacher_name || x.teacher_id) + '</td><td>' + esc(x.class_id) + '</td><td>' + esc(x.course) + '</td><td>' + esc(x.room || "-") + '</td></tr>';
  }).join("");
  $("institutionSchedule").innerHTML = items && items.length ? '<div class="table-wrap"><table><tr><th>日</th><th>时间</th><th>教师</th><th>班级</th><th>课程</th><th>教室</th></tr>' + rows + '</table></div>' : '<p class="muted">还没有排课记录；新增排课时会自动检查教师时间冲突。</p>';
}
function loadInstitutionSchedule() {
  var cls = $("institutionScheduleClass").value;
  return api("/institution/schedule?class_id=" + encodeURIComponent(cls)).then(function (r) { renderInstitutionSchedule(r.items || []); })
    .catch(function (e) { setStatus(false, "排课加载失败：" + e.message); });
}
function createInstitutionSchedule() {
  var teacherId = $("instTeacherId").value.trim(), teacherName = $("instTeacherName").value.trim();
  var cls = $("instScheduleClass").value, weekday = Number($("instWeekday").value);
  var start = $("instStartTime").value.trim(), end = $("instEndTime").value.trim();
  var course = $("instCourse").value.trim(), room = $("instRoom").value.trim();
  if (!teacherId || !start || !end || !course) { $("institutionScheduleStatus").textContent = "请填写教师、时间和课程。"; return; }
  $("institutionScheduleBtn").disabled = true; $("institutionScheduleStatus").textContent = "正在检查教师时间冲突…";
  api("/institution/schedule", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({teacher_id: teacherId, teacher_name: teacherName, class_id: cls, weekday: weekday, start_time: start, end_time: end, course: course, room: room})})
    .then(function (r) { $("institutionScheduleStatus").textContent = "排课成功：" + r.item.course + " · " + r.item.start_time + "–" + r.item.end_time; loadInstitutionSchedule(); })
    .catch(function (e) { $("institutionScheduleStatus").textContent = "排课失败：" + e.message; })
    .finally(function () { $("institutionScheduleBtn").disabled = false; });
}
function money(v) { return "¥" + Number(v || 0).toFixed(2); }
function renderFinanceRules(rules) {
  if (!rules) { $("financeRules").innerHTML = '<p class="muted">规则加载中…</p>'; return; }
  $("financeRules").innerHTML = '<div class="kv"><span>班课教师</span><b>70 元/人/节</b></div><div class="kv"><span>教师一对一</span><b>480 / 500 / 600 元/节</b></div><div class="kv"><span>助教底薪</span><b>1 班 3000；2 班及以上 4000</b></div><div class="kv"><span>助教班课</span><b>60 / 80 / 100 / 120 元/节</b></div><div class="kv"><span>助教一对一</span><b>100 元/节</b></div><div class="kv"><span>班主任底薪</span><b>3000 元</b></div><div class="kv"><span>转介绍</span><b>学生付费 5%</b></div><div class="kv"><span>拉新</span><b>1000—5000 元/人</b></div><p class="muted">' + esc(rules.note || '规则仅供参考，实际结算需财务复核。') + '</p>';
}
function estimateFinance() {
  var body = {
    group_students: Number($("finGroupStudents").value || 0),
    group_sessions: Number($("finGroupSessions").value || 0),
    one_on_one_tier: Number($("finOneTier").value || 500),
    one_on_one_sessions: Number($("finOneSessions").value || 0),
    assistant_class_count: Number($("finAssistantClasses").value || 1),
    assistant_sessions_60: Number($("finAsst60").value || 0),
    assistant_sessions_80: Number($("finAsst80").value || 0),
    assistant_sessions_100: Number($("finAsst100").value || 0),
    assistant_sessions_120: Number($("finAsst120").value || 0),
    assistant_one_on_one_sessions: Number($("finAsstOne").value || 0),
    referral_payment_base: Number($("finReferralBase").value || 0),
    new_student_count: Number($("finNewStudents").value || 0),
    new_student_bonus_per_person: Number($("finNewBonus").value || 1000)
  };
  $("financeEstimateBtn").disabled = true; $("financeStatus").textContent = "正在计算…";
  api("/institution/finance/estimate", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)})
    .then(function (r) {
      $("financeTeacherPay").textContent = money(r.teacher.total);
      $("financeAssistantPay").textContent = money(r.assistant.total);
      $("financeHeadPay").textContent = money(r.head_teacher.total);
      $("financeTotal").textContent = money(r.grand_total);
      $("financeBreakdown").textContent = JSON.stringify(r, null, 2);
      $("financeStatus").textContent = "预算已生成；状态：estimate_only，不是工资单。";
    })
    .catch(function (e) { $("financeStatus").textContent = "计算失败：" + e.message; })
    .finally(function () { $("financeEstimateBtn").disabled = false; });
}
function loadWorkflow() {
  return api("/workflow/board").then(function (d) {
    $("wfRequirements").textContent = (d.counts && d.counts.requirements) || 0;
    $("wfPendingReviews").textContent = (d.counts && d.counts.pending_reviews) || 0;
    $("wfIncidents").textContent = (d.counts && d.counts.incidents) || 0;
    $("wfDelays").textContent = (d.counts && d.counts.delays) || 0;
    var stages = d.stages || [], current = stages.filter(function (x) { return x.status !== "done"; })[0];
    $("wfCurrentStage").textContent = current ? current.label : "已到复盘";
    $("wfStages").innerHTML = stages.map(function (s) { return '<div class="kv"><span>' + esc(s.label) + '</span><b>' + (s.status === "done" ? "已完成" : "待办") + '</b></div>'; }).join("");
    $("wfRequirementsList").innerHTML = (d.requirements || []).length ? d.requirements.map(function (r) { return '<div class="ctx-block"><div class="kv"><span>' + esc(r.priority) + ' · ' + esc(r.owner) + '</span><b>' + esc(r.status) + '</b></div><p><b>' + esc(r.title) + '</b></p><p class="muted">' + esc(r.evidence || "") + '</p></div>'; }).join("") : '<p class="muted">还没有需求，先创建一条。</p>';
    var opts = (d.requirements || []).map(function (r) { return '<option value="' + esc(r.requirement_id) + '">' + esc(r.title) + '</option>'; }).join("");
    $("wfReviewRequirement").innerHTML = opts || '<option value="">请先创建需求</option>';
    var logs = [];
    (d.incidents || []).forEach(function (x) { logs.push('<div class="kv"><span>事故 · ' + esc(x.severity) + '</span><b>' + esc(x.title) + '</b></div>'); });
    (d.delays || []).forEach(function (x) { logs.push('<div class="kv"><span>延期</span><b>' + esc(x.title) + '</b></div>'); });
    (d.acceptances || []).forEach(function (x) { logs.push('<div class="kv"><span>验收</span><b>' + esc(x.release_name) + ' · ' + esc(x.conclusion) + '</b></div>'); });
    $("wfLogs").innerHTML = logs.join("") || '<p class="muted">暂无事故、延期或验收记录。</p>';
  }).catch(function (e) { setStatus(false, "产品工作流加载失败：" + e.message); });
}
function createWorkflowRequirement() {
  var title = $("wfReqTitle").value.trim();
  if (!title) { $("wfReqStatus").textContent = "请填写需求标题。"; return; }
  $("wfReqBtn").disabled = true; $("wfReqStatus").textContent = "正在创建…";
  api("/workflow/requirements", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({title: title, owner: $("wfReqOwner").value.trim() || "product", priority: $("wfReqPriority").value, evidence: $("wfReqEvidence").value.trim(), stage: "discovery"})})
    .then(function () { $("wfReqStatus").textContent = "需求已创建。"; $("wfReqTitle").value = ""; $("wfReqEvidence").value = ""; loadWorkflow(); })
    .catch(function (e) { $("wfReqStatus").textContent = "创建失败：" + e.message; })
    .finally(function () { $("wfReqBtn").disabled = false; });
}
function createWorkflowReview() {
  var rid = $("wfReviewRequirement").value;
  if (!rid) { $("wfReviewStatus").textContent = "请先创建需求。"; return; }
  $("wfReviewBtn").disabled = true;
  api("/workflow/reviews", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({requirement_id: rid, review_type: $("wfReviewType").value, decision: $("wfReviewDecision").value, owner: "reviewer", notes: $("wfReviewNotes").value.trim()})})
    .then(function () { $("wfReviewStatus").textContent = "评审已记录。"; $("wfReviewNotes").value = ""; loadWorkflow(); })
    .catch(function (e) { $("wfReviewStatus").textContent = "记录失败：" + e.message; })
    .finally(function () { $("wfReviewBtn").disabled = false; });
}
function createWorkflowIncident() {
  var title = $("wfIncidentTitle").value.trim(); if (!title) { $("wfIncidentStatus").textContent = "请填写事故标题。"; return; }
  $("wfIncidentBtn").disabled = true;
  api("/workflow/incidents", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({title: title, severity: $("wfIncidentSeverity").value, impact: $("wfIncidentImpact").value.trim(), owner: "product", action: $("wfIncidentAction").value.trim()})})
    .then(function () { $("wfIncidentStatus").textContent = "事故已记录，请继续完成复盘。"; $("wfIncidentTitle").value = ""; loadWorkflow(); })
    .catch(function (e) { $("wfIncidentStatus").textContent = "记录失败：" + e.message; })
    .finally(function () { $("wfIncidentBtn").disabled = false; });
}
function createWorkflowDelay() {
  var title = $("wfDelayTitle").value.trim(), reason = $("wfDelayReason").value.trim(); if (!title || !reason) { $("wfDelayStatus").textContent = "请填写延期事项和原因。"; return; }
  $("wfDelayBtn").disabled = true;
  api("/workflow/delays", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({title: title, reason: reason, impact: "", mitigation: $("wfDelayMitigation").value.trim(), owner: "product"})})
    .then(function () { $("wfDelayStatus").textContent = "延期已记录，请重新评估排期。"; $("wfDelayTitle").value = ""; $("wfDelayReason").value = ""; loadWorkflow(); })
    .catch(function (e) { $("wfDelayStatus").textContent = "记录失败：" + e.message; })
    .finally(function () { $("wfDelayBtn").disabled = false; });
}
function createWorkflowAcceptance() {
  var name = $("wfReleaseName").value.trim(); if (!name) { $("wfAcceptanceStatus").textContent = "请填写版本名。"; return; }
  var checklist = {function: $("wfCheckFunction").checked, data: $("wfCheckData").checked, permission: $("wfCheckPermission").checked, ai_safety: $("wfCheckAI").checked, rollback: $("wfCheckRollback").checked};
  var all = Object.keys(checklist).every(function (k) { return checklist[k]; });
  $("wfAcceptanceBtn").disabled = true;
  api("/workflow/acceptance", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({release_name: name, owner: "product", checklist: checklist, conclusion: all ? "approved" : "changes"})})
    .then(function () { $("wfAcceptanceStatus").textContent = all ? "验收通过，可进入发布。" : "仍有检查项未完成，暂不可发布。"; loadWorkflow(); })
    .catch(function (e) { $("wfAcceptanceStatus").textContent = "记录失败：" + e.message; })
    .finally(function () { $("wfAcceptanceBtn").disabled = false; });
}
function loadInstitutionHome() {
  return api("/roles/institution/home").then(function (r) {
    var d = r.data || {}, ov = d.overview || {}, org = d.org_report || {};
    $("institutionEvents").textContent = ov.events || 0;
    $("institutionStudents").textContent = ov.students || 0;
    $("institutionAgents").textContent = ov.agents || 0;
    $("institutionRag").textContent = (ov.rag && ov.rag.n_chunks) || 0;
    $("institutionOrg").textContent = JSON.stringify(org, null, 2);
    $("institutionMatrix").innerHTML = state.roles.map(function (role) { return '<div class="kv"><span>' + esc(role.name) + '</span><b>' + esc(role.scope) + '</b></div>'; }).join("");
    $("institutionCompliance").innerHTML = '<div class="kv"><span>服务端 RBAC</span><b>待接入</b></div><div class="kv"><span>K12 监护人授权</span><b>已定义</b></div><div class="kv"><span>原始对话隔离</span><b>已定义</b></div><div class="kv"><span>数据导出/撤回</span><b>已具备</b></div><div class="kv"><span>审计日志</span><b>已具备</b></div>';
    $("institutionConnectors").innerHTML = '<div class="kv"><span>LMS</span><b>待接入</b></div><div class="kv"><span>排课</span><b>待接入</b></div><div class="kv"><span>财务</span><b>待接入</b></div><div class="kv"><span>CRM / 销售</span><b>可选</b></div><p class="muted">机构接入的是服务和质量指标，不是学习者身份和数据所有权。</p>';
    renderInstitutionPerformance(d.performance || []);
    renderInstitutionSchedule(d.schedule || []);
    renderFinanceRules(d.finance_rules || {});
  }).catch(function (e) { setStatus(false, "机构管理端加载失败：" + e.message); });
}
function loadAgents() {
  return api("/agents/fixed").then(function (r) {
    state.agents = Array.isArray(r.agents) ? r.agents : [];
    state.fixedAgentIds = state.agents.map(function (a) { return a.agent_id; });
    var sel = $("agentSelect"); sel.innerHTML = "";
    if (!state.agents.length) {
      var empty = document.createElement("option"); empty.value = ""; empty.textContent = "常驻支持暂不可用";
      sel.appendChild(empty); sel.disabled = true;
      return;
    }
    state.agents.forEach(function (a) {
      var o = document.createElement("option"); o.value = a.agent_id; o.textContent = a.name; sel.appendChild(o);
    });
    if (state.fixedAgentIds.indexOf(state.currentAgent) < 0) state.currentAgent = state.fixedAgentIds[0];
    sel.value = state.currentAgent;
    sel.disabled = false;
    sel.onchange = function () { state.currentAgent = sel.value; };
  }).catch(function (e) {
    if ($("agentSelect")) {
      $("agentSelect").innerHTML = '<option value="">常驻支持暂不可用</option>';
      $("agentSelect").disabled = true;
    }
    setStatus(false, "支持列表加载失败：" + e.message);
  });
}
function loadOverview() {
  return api("/overview").then(function (x) {
    state.overview = x;
    $("kpiEvents").textContent = x.events; $("kpiAgents").textContent = x.agents;
    $("kpiStudents").textContent = x.students; $("kpiRag").textContent = (x.rag && x.rag.n_chunks) || 0;
  });
}
function loadTender() {
  var sid = state.currentStudent;
  return api("/tender/state/" + sid).then(function (x) {
    state.tender = x; renderTender(x);
    return api("/reports/student/" + sid);
  }).then(function (r) {
    $("studentReport").textContent = JSON.stringify(r, null, 2);
    $("nextActions").innerHTML = (r.next_actions || []).map(function (a) { return "<li>" + esc(a) + "</li>"; }).join("");
    return api("/reports/parent/" + sid);
  }).then(function (p) {
    $("parentReport").textContent = JSON.stringify(p, null, 2);
  }).catch(function (e) { setStatus(false, "加载失败：" + e.message); });
}
function renderTender(t) {
  var k = t.knowledge || {}, c = t.cognitive || {}, m = t.metacognition || {}, b = t.baseline || {}, g = t.group || {};
  $("sMastery").textContent = fmt(k.mastery); $("sTheta").textContent = fmt(c.theta);
  $("sBias").textContent = fmt(m.jol_bias); $("sHesitation").textContent = fmt(m.hesitation);
  $("sFit").textContent = fmt(b.arrangement_fit); $("sGroup").textContent = fmt(g.clustering) + " / " + fmt(g.bridge_ratio);
  renderRadar(t); renderRhythm(b.rhythm || {});
}
function renderRadar(t) {
  var k = t.knowledge || {}, c = t.cognitive || {}, m = t.metacognition || {}, b = t.baseline || {};
  var axes = [
    { label: "掌握", v: clamp(k.mastery) },
    { label: "θ", v: clamp((Number(c.theta || 0) + 3) / 6) },
    { label: "校准", v: clamp(1 - Math.min(Math.abs(Number(m.jol_bias || 0)), 1)) },
    { label: "稳定", v: clamp(1 - Number(m.hesitation || 0)) },
    { label: "匹配", v: clamp(b.arrangement_fit) }
  ];
  var cx = 150, cy = 150, R = 105, n = axes.length, svg = "";
  var i, a, r, pts;
  for (r = 1; r <= 4; r++) {
    pts = [];
    for (i = 0; i < n; i++) { a = -Math.PI / 2 + 2 * Math.PI * i / n; pts.push((cx + R * r / 4 * Math.cos(a)).toFixed(1) + "," + (cy + R * r / 4 * Math.sin(a)).toFixed(1)); }
    svg += '<polygon points="' + pts.join(" ") + '" fill="none" stroke="#2e2e33" stroke-width="1"/>';
  }
  for (i = 0; i < n; i++) {
    a = -Math.PI / 2 + 2 * Math.PI * i / n;
    var x = cx + R * Math.cos(a), y = cy + R * Math.sin(a);
    svg += '<line x1="' + cx + '" y1="' + cy + '" x2="' + x.toFixed(1) + '" y2="' + y.toFixed(1) + '" stroke="#2e2e33"/>';
    var lx = cx + (R + 22) * Math.cos(a), ly = cy + (R + 22) * Math.sin(a);
    svg += '<text x="' + lx.toFixed(1) + '" y="' + ly.toFixed(1) + '" fill="#9a9aa5" font-size="11" text-anchor="middle" dominant-baseline="middle">' + axes[i].label + '</text>';
  }
  pts = [];
  for (i = 0; i < n; i++) { a = -Math.PI / 2 + 2 * Math.PI * i / n; var v = axes[i].v; pts.push((cx + R * v * Math.cos(a)).toFixed(1) + "," + (cy + R * v * Math.sin(a)).toFixed(1)); }
  svg += '<polygon points="' + pts.join(" ") + '" fill="rgba(16,163,127,.22)" stroke="#10a37f" stroke-width="2"/>';
  $("radarChart").innerHTML = svg;
}
function renderRhythm(r) {
  var vals = [
    { k: "日内强度 R24", v: Number(r["日内强度R24"] || 0) },
    { k: "周内强度 R168", v: Number(r["周内强度R168"] || 0) },
    { k: "节律平衡 B", v: Number(r["节律平衡B"] || 0) }
  ];
  var max = Math.max(1, Math.max.apply(null, vals.map(function (x) { return x.v; })));
  $("rhythmBars").innerHTML = vals.map(function (x) {
    var w = Math.max(2, Math.min(100, x.v / max * 100));
    return '<div class="bar-row"><span>' + x.k + '</span><div class="bar"><i style="width:' + w.toFixed(1) + '%"></i></div><b>' + fmt(x.v, 3) + '</b></div>';
  }).join("");
}
function appendMessage(role, text, meta) {
  var wrap = document.createElement("div"); wrap.className = "msg " + role;
  var av = document.createElement("div"); av.className = "avatar"; av.textContent = role === "user" ? "你" : "T";
  var bubble = document.createElement("div"); bubble.className = "bubble";
  if (role === "assistant") bubble.innerHTML = renderAssistantMarkup(text); else bubble.textContent = text;
  if (meta) { var m = document.createElement("div"); m.className = "meta"; m.textContent = meta; bubble.appendChild(m); }
  wrap.appendChild(av); wrap.appendChild(bubble); $("chatMessages").appendChild(wrap);
  $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
  return wrap;
}

function renderAdvisorRoute(route) {
  var box = $("advisorRouteChips"); if (!box) return;
  var experts = (route && route.selected_experts) || [];
  var html = experts.map(function (e) {
    var cls = "advisor-chip" + (e.id === "safety_advisor" ? " safety" : "");
    var scope = e.scope_status === "needs_consent" ? " · 需授权" : "";
    return '<span class="' + cls + '" title="' + esc((e.reason || []).join("、") + " / " + (e.scope || "")) + '">' +
      esc(e.icon || "·") + " " + esc(e.name) + ' <small>' + Math.round(Number(e.weight || 0) * 100) + "%" + scope + '</small></span>';
  }).join("");
  if (!html) html = '<span class="advisor-chip muted">总协调者</span>';
  if ((route && route.monitoring_experts || []).indexOf("safety_advisor") >= 0 && !experts.some(function (e) { return e.id === "safety_advisor"; })) {
    html += '<span class="advisor-chip muted">! 安全后台监控</span>';
  }
  box.innerHTML = html;
  var old = box.parentNode.querySelector(".advisor-route-note"); if (old) old.remove();
  var note = document.createElement("span"); note.className = "advisor-route-note";
  note.textContent = route && route.safety_level === "emergency" ? "紧急规则命中 · 人工升级" : "摘要协作 · 不共享原始数据";
  box.parentNode.appendChild(note);
}
function routeAdvisorForMessage(message) {
  var consent = ["minimal_safety_signals", "aggregated_tender_state", "subject_evidence", "assessment_evidence", "learning_passport_evidence"];
  var body = JSON.stringify({message: message, student_id: state.currentStudent, role: state.currentRole, consent_scopes: consent});
  return api("/advisors/route", {method:"POST", headers:{"Content-Type":"application/json"}, body:body})
    .then(function (route) { state.lastAdvisorRoute = route; renderAdvisorRoute(route); return route; })
    .catch(function () { renderAdvisorRoute({selected_experts:[], monitoring_experts:["safety_advisor"], safety_level:"normal"}); return null; });
}

function renderChatWelcome() {
  var host = $("chatMessages"); if (!host) return;
  host.innerHTML = '<div class="welcome"><div class="welcome-mark">T</div><h1>有什么想一起想清楚的？</h1><p>Tender 会结合你的连续记录、此刻状态和可引用的学习证据回答；它不是心理或医学诊断。</p><div class="quick"><button type="button" data-q="我不确定这题对不对，你能帮我看看该从哪里想吗？">我不确定这题对不对</button><button type="button" data-q="我这次预测能对 8 题，但实际只对了 5 题，为什么？">为什么我总高估自己</button><button type="button" data-q="我现在卡住了，帮我拆出一个五分钟后就能开始的小步骤。">帮我拆出下一步</button></div></div>';
  bindQuickPrompts();
}
function bindQuickPrompts() {
  var quick = document.querySelectorAll(".quick button");
  for (var i = 0; i < quick.length; i++) {
    quick[i].onclick = function () {
      if (state.agentBusy) return;
      $("agentMessage").value = this.getAttribute("data-q") || "";
      sendAgent();
    };
  }
}
function sendAgent() {
  if (state.agentBusy) return;
  var msg = ($("agentMessage").value || "").trim();
  if (!msg) { $("agentMessage").focus(); return; }
  if (!state.currentStudent) { appendMessage("assistant", "请先选择学习者。"); return; }
  var agentId = ($("agentSelect") && $("agentSelect").value) || state.currentAgent;
  if (!agentId || (state.fixedAgentIds.length && state.fixedAgentIds.indexOf(agentId) < 0)) {
    appendMessage("assistant", "常驻支持暂时不可用，请稍后刷新。");
    return;
  }
  state.agentBusy = true;
  $("agentMessage").value = "";
  $("composerState").textContent = "Tender 正在整理支持建议…";
  setBusy("sendAgentBtn", true);
  appendMessage("user", msg);
  var typing = appendMessage("assistant", "正在结合连续记录与授权证据…");
  var body = JSON.stringify({ student_id: state.currentStudent, message: msg, intent: "general" });
  routeAdvisorForMessage(msg).then(function () {
    return api("/agents/" + encodeURIComponent(agentId) + "/invoke", { method: "POST", headers: { "Content-Type": "application/json" }, body: body });
  }).then(function (r) {
    var action = r.action || {};
    var text = action.text || "这次没有得到可展示的回复，请再试一次。";
    typing.remove();
    appendMessage("assistant", text, "已结合当前状态与授权证据 · 不是诊断");
    var llm = r.llm || {};
    $("agentProvider").textContent = supportLabel(llm.provider);
    $("agentModel").textContent = supportMeta();
    $("agentSafety").textContent = (r.safety && r.safety.allowed === false) ? "已拦截" : "通过";
    $("agentApproval").textContent = (r.policy && r.policy.requires_human_approval) ? "需要人工确认" : "无需人工确认";
    var src = Array.isArray(action.rag_sources) ? action.rag_sources : [];
    $("agentSources").innerHTML = src.length ? src.map(function (source) {
      var label = source && typeof source === "object" ? (source.title || source.source || "学习证据") : source;
      return "<li>" + esc(label) + "</li>";
    }).join("") : '<li class="muted">本轮没有新增引用来源</li>';
    setStatus(true, "已连接");
  }).catch(function (e) {
    if (typing && typing.parentNode) typing.remove();
    appendMessage("assistant", "这次没能完成支持建议：" + e.message);
    setStatus(false, "支持请求未完成");
  }).finally(function () {
    state.agentBusy = false;
    $("composerState").textContent = "就绪";
    setBusy("sendAgentBtn", false);
  });
}


function advisorMeta(role) {
  var m = {
    health_advisor:{eyebrow:"HEALTH ADVISOR · 健康顾问",title:"健康顾问工作台",intro:"看睡眠、活动、身体状态与健康筛查信号；异常必须转介校医或医生。"},
    nutrition_advisor:{eyebrow:"NUTRITION ADVISOR · 营养顾问",title:"营养顾问工作台",intro:"把膳食记录转换成营养模式评分，优先做一项可执行的替换。"},
    neurocognitive_advisor:{eyebrow:"NEUROCOGNITIVE ADVISOR · 神经认知顾问",title:"神经认知顾问工作台",intro:"观察记忆、执行功能与注意画像，帮助调整任务负荷和提示层级。"},
    psychology_advisor:{eyebrow:"PSYCHOLOGY ADVISOR · 心理学顾问",title:"心理学顾问工作台",intro:"识别压力与支持需求，提供低压力求助入口，不输出临床诊断。"},
    learning_science_advisor:{eyebrow:"LEARNING SCIENCE ADVISOR · 学习科学顾问",title:"学习解释台",intro:"整合 Tender 状态、RoleMind 与专业顾问信号，解释 Bloch 球和量子认知模型。"},
    career_advisor:{eyebrow:"CAREER ADVISOR · 生涯与职业顾问",title:"生涯与职业顾问工作台",intro:"用学习护照和能力证据探索职业方向与转衔路径，不承诺就业，也不替用户决定人生。"},
    safety_advisor:{eyebrow:"SAFETY ADVISOR · 安全与保护顾问",title:"安全与保护顾问工作台",intro:"识别霸凌、诈骗、不当关系、自伤和突发风险，优先保护当事人并升级给合格的成人或专业机构。"}
  };
  return m[role] || {eyebrow:"PROFESSIONAL ADVISOR · 专业顾问",title:"专业顾问工作台",intro:"基于公开数据与授权证据提供支持建议。"};
}
function loadAdvisorHome() {
  var role = state.currentRole;
  var meta = advisorMeta(role);
  $("advisorEyebrow").textContent = meta.eyebrow;
  $("advisorTitle").textContent = meta.title;
  $("advisorIntro").textContent = meta.intro;
  return api("/roles/" + encodeURIComponent(role) + "/home?student_id=" + encodeURIComponent(state.currentStudent) + "&class_id=" + encodeURIComponent(($("wbClassSelect") && $("wbClassSelect").value) || "理科班")).then(function (r) {
    var a = (r.data && r.data.advisor) || {};
    var ev = a.evidence || {};
    $("advisorModelStatus").textContent = a.model_status || "待校准";
    $("advisorEvents").textContent = ev.event_count || "-";
    $("advisorMastery").textContent = fmt((ev.knowledge || {}).mastery);
    $("advisorSignal").textContent = a.tier || a.signal || "等待记录";
    $("advisorTier").textContent = a.tier || "等待记录";
    $("advisorBoundary").textContent = a.boundary || "筛查与支持，不做诊断。";
    $("advisorRecommendations").innerHTML = (a.recommendations || []).map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") || '<li class="muted">暂无建议。</li>';
    $("advisorModel").textContent = JSON.stringify(a.metrics || a.fusion_config || a.model_status || a, null, 2);
    $("advisorEvidence").textContent = JSON.stringify(ev, null, 2);
    var profiles = a.profiles || [];
    $("advisorProfiles").innerHTML = profiles.length ? profiles.map(function (p) {
      return '<div class="kv"><span>' + esc(p.label || ("profile " + p.cluster)) + '</span><b>n=' + esc(p.n) + '</b></div><p class="muted">' + esc(JSON.stringify(p).slice(0, 260)) + '</p>';
    }).join("") : '<div class="kv"><span>当前信号</span><b>' + esc(a.signal || "-") + '</b></div><p class="muted">群组画像来自公开研究数据，必须用本地授权数据重新校准。</p>';
  }).catch(function (e) { setStatus(false, "顾问工作台加载失败：" + e.message); });
}

function canAuthorWorkbench() {
  return ["teacher", "head_teacher", "institution", "health_advisor", "nutrition_advisor", "neurocognitive_advisor", "psychology_advisor", "learning_science_advisor", "career_advisor", "safety_advisor"].indexOf(state.currentRole) >= 0;
}
function wbStatusText(status) {
  return ({draft:"草稿",waiting_approval:"等待审批",completed:"已完成",needs_revision:"需修改",stopped:"已停止"})[status] || status || "未知";
}
function wbArtifactText(a) {
  var c = a.content || {};
  if (a.artifact_type === "lesson_plan") {
    return (c.assignment || "") + " " + ((c.teaching_steps || []).join(" → "));
  }
  if (a.artifact_type === "assessment_brief") {
    return "掌握度 " + fmt(c.mastery) + "；JOL 偏差 " + fmt(c.jol_bias) + "；优先级：" + (c.priority || "-");
  }
  if (a.artifact_type === "student_cards") {
    return (c.cards || []).map(function (x) { return x.title + "：" + x.text; }).join(" ");
  }
  if (a.artifact_type === "family_report" || a.artifact_type === "external_communication") {
    return (c.recipient_label ? "接收方：" + c.recipient_label + "；" : "") + (c.sections || []).map(function (x) { return x.label + "：" + x.text; }).join(" ");
  }
  if (a.artifact_type === "safety_check") {
    return (c.checks || []).map(function (x) { return x.name + "=" + x.status; }).join("；");
  }
  return JSON.stringify(c).slice(0, 240);
}
function renderWorkbenchList() {
  var box = $("wbThreadList");
  if (!box) return;
  var threads = state.workbenchThreads || [];
  if (!threads.length) {
    box.innerHTML = '<div class="wb-empty">还没有协作线程。老师可在左侧发起；学生和家长只看到与自己有权限关联的已交付内容。</div>';
    return;
  }
  box.innerHTML = threads.map(function (t) {
    var active = state.currentWorkbenchThread && state.currentWorkbenchThread.thread_id === t.thread_id ? " active" : "";
    return '<button class="wb-thread' + active + '" data-thread="' + esc(t.thread_id) + '">' +
      '<strong>' + esc(t.title) + '</strong>' +
      '<span>' + esc(t.student_id) + ' · ' + esc(t.class_id) + ' · 对外：' + esc(t.audience_label || '家长') + '</span>' +
      '<div class="wb-thread-foot"><span>' + esc(wbStatusText(t.status)) + '</span><span>' + (t.run_count || 0) + ' runs · ' + (t.pending_approvals || 0) + ' 待批</span></div>' +
      '</button>';
  }).join("");
  var buttons = box.querySelectorAll(".wb-thread");
  for (var i = 0; i < buttons.length; i++) buttons[i].onclick = function () { loadWorkbenchThread(this.getAttribute("data-thread")); };
}
function renderWorkbenchDetail(d) {
  state.currentWorkbenchThread = d;
  $("wbThreadTitle").textContent = d.title || "未命名任务";
  $("wbThreadObjective").textContent = d.objective || "";
  var badge = $("wbThreadBadge"); badge.textContent = wbStatusText(d.status); badge.className = "wb-status-badge " + (d.status || "");
  $("wbThreadMeta").innerHTML = '<span>学生 ' + esc(d.student_id) + '</span><span>班级 ' + esc(d.class_id) + '</span><span>对外对象 ' + esc(d.audience_label || '家长') + '</span><span>创建角色 ' + esc(d.created_by_role) + '</span><span>' + esc(d.created_at || "") + '</span>';
  var runs = d.runs || [];
  $("wbRunList").innerHTML = runs.length ? runs.map(function (r) {
    return '<div class="wb-run">' +
      '<div class="wb-agent-icon">' + esc((r.agent_name || r.agent_id || "A").slice(0,1)) + '</div>' +
      '<div class="wb-run-body"><div class="wb-run-head"><strong>' + esc(r.agent_name) + '</strong><span>' + esc(r.status) + ' · ' + esc(r.model_version || "") + '</span></div>' +
      '<p>' + esc(r.summary) + '</p><div class="wb-plan">' + (r.plan || []).map(function (x) { return '<span>' + esc(x) + '</span>'; }).join("") + '</div></div></div>';
  }).join("") : '<div class="wb-empty">还没有执行记录。发起一次协作任务后，这里会显示过程与结果。</div>';
  var artifacts = d.artifacts || [];
  $("wbArtifacts").innerHTML = artifacts.length ? artifacts.map(function (a) {
    return '<div class="wb-artifact"><h4>' + esc(a.title) + '</h4><p>' + esc(wbArtifactText(a)) + '</p><span class="wb-artifact-status ' + esc(a.status) + '">' + esc(a.status) + '</span></div>';
  }).join("") : '<p class="muted">暂无 Artifact。</p>';
  var approvals = d.approvals || [];
  $("wbApprovals").innerHTML = approvals.length ? approvals.map(function (a) {
    var actions = "";
    if (a.status === "pending" && canAuthorWorkbench()) {
      actions = '<div class="wb-approval-actions"><button class="send" data-approve="' + esc(a.approval_id) + '">批准</button><button class="ghost" data-revise="' + esc(a.approval_id) + '">退回修改</button><button class="danger" data-reject="' + esc(a.approval_id) + '">拒绝</button></div>';
    }
    return '<div class="wb-approval"><strong>' + esc(a.approver_role) + ' · ' + esc(a.status) + '</strong><p>Artifact ' + esc(a.artifact_id) + (a.reason ? ' · ' + esc(a.reason) : '') + '</p>' + actions + '</div>';
  }).join("") : '<p class="muted">暂无审批。低风险动作自动执行，高风险动作必须等待老师。</p>';
  var approveBtns = $("wbApprovals").querySelectorAll("[data-approve],[data-revise],[data-reject]");
  for (var i = 0; i < approveBtns.length; i++) {
    approveBtns[i].onclick = function () {
      var decision = this.hasAttribute("data-approve") ? "approved" : (this.hasAttribute("data-revise") ? "changes_requested" : "rejected");
      decideWorkbenchApproval(this.getAttribute("data-approve") || this.getAttribute("data-revise") || this.getAttribute("data-reject"), decision);
    };
  }
  $("wbStopBtn").disabled = !canAuthorWorkbench() || ["completed", "stopped"].indexOf(d.status) >= 0;
  $("wbThreadNote").textContent = d.visibility_note || (d.pending_approvals ? "有 " + d.pending_approvals + " 个高风险动作待负责人审批。" : "所有输出保留证据与审计记录。");
  renderWorkbenchList();
}
function loadWorkbenchThread(threadId) {
  if (!threadId) return Promise.resolve();
  return api("/workbench/threads/" + encodeURIComponent(threadId) + "?viewer_role=" + encodeURIComponent(state.currentRole)).then(function (d) { renderWorkbenchDetail(d); })
    .catch(function (e) { setStatus(false, "协作线程加载失败：" + e.message); });
}
function loadWorkbench() {
  var can = canAuthorWorkbench();
  var card = $("wbTitle") ? $("wbTitle").closest(".wb-create-card") : null;
  if (card) card.style.display = can ? "block" : "none";
  var q = "/workbench/threads?limit=40";
  if (state.currentRole === "learner" || state.currentRole === "parent") {
    q += "&student_id=" + encodeURIComponent(state.currentStudent);
  } else if ($("wbClassSelect")) {
    q += "&class_id=" + encodeURIComponent($("wbClassSelect").value);
  }
  return api(q).then(function (r) {
    state.workbenchThreads = r.threads || [];
    renderWorkbenchList();
    var currentId = state.currentWorkbenchThread && state.currentWorkbenchThread.thread_id;
    var exists = currentId && state.workbenchThreads.some(function (t) { return t.thread_id === currentId; });
    if (exists) return loadWorkbenchThread(currentId);
    if (state.workbenchThreads.length) return loadWorkbenchThread(state.workbenchThreads[0].thread_id);
    state.currentWorkbenchThread = null;
    $("wbThreadTitle").textContent = can ? "发起你的第一个协作任务" : "暂无与你相关的协作";
    $("wbThreadObjective").textContent = can ? "输入任务目标，Agent 会围绕同一份学习证据协作。" : "老师发布并批准的内容会出现在这里。";
    $("wbThreadBadge").textContent = "未选择"; $("wbThreadBadge").className = "wb-status-badge";
    $("wbThreadMeta").innerHTML = ""; $("wbRunList").innerHTML = '<div class="wb-empty">暂无执行记录。</div>';
    $("wbArtifacts").innerHTML = '<p class="muted">暂无 Artifact。</p>'; $("wbApprovals").innerHTML = '<p class="muted">暂无审批。</p>';
  }).catch(function (e) { setStatus(false, "协作工作台加载失败：" + e.message); });
}
function launchWorkbench() {
  if (!canAuthorWorkbench()) return;
  var title = $("wbTitle").value.trim(), objective = $("wbObjective").value.trim();
  if (!title || !objective) { $("wbLaunchStatus").textContent = "请填写标题和目标。"; return; }
  $("wbLaunchBtn").disabled = true; $("wbLaunchStatus").textContent = "正在创建线程并分派 Agent…";
  var audienceRole = $("wbAudienceRole").value;
  var customLabel = $("wbAudienceCustom").value.trim();
  var purpose = $("wbAudiencePurpose").value.trim();
  var tone = $("wbAudienceTone").value;
  var body = JSON.stringify({title:title, objective:objective, student_id:state.currentStudent, class_id:$("wbClassSelect").value, created_by_role:state.currentRole, task_type:"grammar_cloze", audience_role:audienceRole, audience_config:{recipient_label:customLabel, purpose:purpose, tone:tone}});
  api("/workbench/threads", {method:"POST", headers:{"Content-Type":"application/json"}, body:body})
    .then(function (t) { return api("/workbench/threads/" + encodeURIComponent(t.thread_id) + "/orchestrate", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({focus_students:[state.currentStudent]})}); })
    .then(function (d) { $("wbLaunchStatus").textContent = "协作已完成第一轮，等待负责人审批。"; renderWorkbenchDetail(d); return loadWorkbench(); })
    .catch(function (e) { $("wbLaunchStatus").textContent = "启动失败：" + e.message; })
    .finally(function () { $("wbLaunchBtn").disabled = false; });
}
function decideWorkbenchApproval(approvalId, decision) {
  api("/workbench/approvals/" + encodeURIComponent(approvalId) + "/decide", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({decision:decision, reason:"负责人在工作台完成审批", actor:state.currentRole})})
    .then(function (d) { $("wbLaunchStatus").textContent = decision === "approved" ? "已批准，线程完成。" : "已退回，线程需要修改。"; renderWorkbenchDetail(d); return loadWorkbench(); })
    .catch(function (e) { setStatus(false, "审批失败：" + e.message); });
}
function stopWorkbench() {
  if (!state.currentWorkbenchThread) return;
  api("/workbench/threads/" + encodeURIComponent(state.currentWorkbenchThread.thread_id) + "/stop", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({reason:"负责人手动停止", actor:state.currentRole})})
    .then(function (d) { renderWorkbenchDetail(d); return loadWorkbench(); })
    .catch(function (e) { setStatus(false, "停止失败：" + e.message); });
}

function loadHeadTeacher() {
  var cls = $("htClassSelect") ? $("htClassSelect").value : "理科班";
  return api("/reports/head_teacher/" + encodeURIComponent(cls)).then(function (r) {
    var shift = r.shift || {}, schedule = shift.schedule || [];
    $("htCurrentBlock").textContent = shift.current_block || "非标准时段";
    $("htCurrentTime").textContent = shift.current_time ? shift.current_time.replace("T", " ").slice(0, 19) + " · Asia/Shanghai" : "按 Asia/Shanghai 显示";
    $("htPriority").textContent = (r.priority || []).length;
    $("htMessages").textContent = (r.parent_messages || []).length;
    $("htHomework").textContent = (r.homework && r.homework.agent_processed) || 0;
    $("htRisks").textContent = (r.risk_alerts || []).length;
    $("htTimeline").innerHTML = schedule.length ? schedule.map(function (x) {
      var statusText = x.status === "current" ? "当前" : (x.status === "done" ? "已过" : "待办");
      return '<div class="timeline-item ' + esc(x.status) + '"><div class="timeline-time">' + esc(x.start) + '–' + esc(x.end) + '</div><div class="timeline-body"><b>' + esc(x.title) + '</b><span>' + esc(x.category) + ' · ' + esc(x.deliverable) + '</span><small>' + (x.human_required ? "需人工确认" : "可自动") + ' · ' + statusText + '</small></div></div>';
    }).join("") : '<p class="muted">暂无排期。</p>';
    var rows = (r.priority || []).map(function (x) {
      return "<tr><td>" + esc(x.student_id) + "</td><td>" + esc((x.reasons || []).join("、")) + "</td><td>" + fmt(x.mastery) + "</td><td>" + fmt(x.hesitation) + "</td><td>" + fmt(x.risk) + "</td></tr>";
    }).join("");
    $("htPriorityList").innerHTML = '<div class="table-wrap"><table><tr><th>学生</th><th>原因</th><th>掌握度</th><th>犹豫</th><th>风险分</th></tr>' + rows + '</table></div>';
    var tickets = (r.collaboration && r.collaboration.tickets) || [];
    $("htTickets").innerHTML = tickets.map(function (t) {
      return '<div class="ctx-block"><div class="kv"><span>' + esc(t.ticket_id) + ' · ' + esc(t.owner) + '</span><b>' + esc(t.status) + '</b></div><p><b>' + esc(t.title) + '</b></p><p class="muted">协作：' + esc(t.collaborator) + ' · 截止：' + esc(t.due) + '</p><p class="muted">边界：' + esc(t.boundary) + '</p></div>';
    }).join("") || '<p class="muted">暂无协作工单。</p>';
    var care = r.care_board || [];
    $("htCare").innerHTML = care.map(function (x) {
      return '<div class="ctx-block"><div class="kv"><span>' + esc(x.student_id || "全班") + '</span><b>' + esc(x.type) + '</b></div><p class="muted">信号：' + esc(x.signal) + '</p><p>' + esc(x.suggested_action) + '</p></div>';
    }).join("");
    $("htParentMessages").innerHTML = (r.parent_messages || []).map(function (m) {
      return '<div class="ctx-block"><div class="kv"><span>' + esc(m.student_id) + '</span><b>' + esc(m.status) + '</b></div><p class="muted">' + esc(m.draft) + '</p><button class="ghost copy-draft" data-draft="' + esc(m.draft) + '">复制草稿</button></div>';
    }).join("") || '<p class="muted">暂无待确认消息</p>';
    var copyBtns = document.querySelectorAll(".copy-draft");
    for (var ci = 0; ci < copyBtns.length; ci++) { copyBtns[ci].onclick = function () { if (navigator.clipboard) navigator.clipboard.writeText(this.getAttribute("data-draft")); }; }
    var h = r.homework || {};
    $("htHomeworkCard").innerHTML = '<div class="kv"><span>答题事件</span><b>' + (h.answer_events || 0) + '</b></div><div class="kv"><span>Agent 已处理</span><b>' + (h.agent_processed || 0) + '</b></div><div class="kv"><span>班主任需复核</span><b>' + (h.teacher_review || 0) + '</b></div><p class="muted">客观题与语法填空可由 Assessment Agent 先批，班主任只处理高价值反馈。</p>';
    var c = r.teacher_coordination || {};
    $("htCoord").innerHTML = '<p class="muted">' + esc(c.summary || "") + '</p><div class="kv"><span>对齐名单</span><b>' + esc((c.focus || []).join("、")) + '</b></div><div class="kv"><span>风险提醒</span><b>' + (r.risk_alerts || []).length + '</b></div><p class="muted">预计节省 ' + (r.time_saved_minutes || 0) + ' 分钟/天；这是流程估算，不是绩效承诺。</p>';
    $("htHandoffs").innerHTML = (r.handoff_templates || []).map(function (x) { return '<div class="kv"><span>' + esc(x.scenario) + '</span><b>' + esc((x.required || []).join(" / ")) + '</b></div>'; }).join("");
    $("htAutomation").innerHTML = '<h4>自动化机会</h4>' + (r.automation_opportunities || []).map(function (x) { return '<div class="kv"><span>' + esc(x.name) + '</span><b>' + esc(x.status) + '</b></div>'; }).join("");
    var fin = r.finance || {};
    $("htFinance").innerHTML = '<div class="kv"><span>校内消费/代收</span><b>' + esc(fin.status || "not_connected") + '</b></div><p class="muted">' + esc(fin.note || "") + '</p>';
    var studentSel = $("htNoteStudent");
    studentSel.innerHTML = "";
    (state.students || []).forEach(function (s) {
      if (cls === "all" || s.class === cls) {
        var o = document.createElement("option"); o.value = s.student_id; o.textContent = s.student_id + " · " + s.name; studentSel.appendChild(o);
      }
    });
    if (studentSel.querySelector('option[value="' + state.currentStudent + '"]')) studentSel.value = state.currentStudent;
    $("htNote").textContent = r.note || "";
  }).catch(function (e) { setStatus(false, "班主任工作台加载失败：" + e.message); });
}

function submitHeadTeacherNote() {
  var cls = $("htClassSelect") ? $("htClassSelect").value : "理科班";
  var sid = $("htNoteStudent").value, category = $("htNoteCategory").value, text = $("htNoteText").value.trim();
  if (!sid || !text) { $("htNoteStatus").textContent = "请选择学生并填写事实。"; return; }
  $("htNoteBtn").disabled = true; $("htNoteStatus").textContent = "正在写入 DAOQL…";
  api("/head_teacher/" + encodeURIComponent(cls) + "/notes", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({student_id: sid, category: category, text: text})})
    .then(function (r) { $("htNoteStatus").textContent = r.note || "已记录事实。"; $("htNoteText").value = ""; })
    .catch(function (e) { $("htNoteStatus").textContent = "写入失败：" + e.message; })
    .finally(function () { $("htNoteBtn").disabled = false; });
}
function loadLifelong() {
  var p1 = api("/lifelong/stages").then(function (r) {
    var stages = r.stages || [];
    $("lifelongGrid").innerHTML = stages.map(function (x) {
      return '<div class="card" style="margin:0"><h3>' + esc(x.stage) + '</h3>' +
        '<p class="muted"><b>目标：</b>' + esc(x.focus) + '</p>' +
        '<p class="muted"><b>痛点：</b>' + esc(x.pain) + '</p>' +
        '<p class="muted"><b>Agent：</b>' + esc((x.agents || []).join("、")) + '</p>' +
        '<p class="muted"><b>指标：</b>' + esc((x.metrics || []).join("、")) + '</p>' +
        '<p class="muted"><b>干预：</b>' + esc((x.intervention || []).join("、")) + '</p></div>';
    }).join("");
    $("passportText").textContent = (r.passport || "") + "。包含：学习事件、能力图谱、项目作品、证书、论文/发表、导师评价、职业里程碑；分阶段授权、可撤销、可验证。";
  });
  var p2 = api("/lifelong/transitions").then(function (r) {
    var ts = r.transitions || [];
    $("transitionGrid").innerHTML = ts.map(function (t) {
      return '<div class="card" style="margin:0"><h3>' + esc(t.from) + ' → ' + esc(t.to) + '</h3>' +
        '<p class="muted"><b>问题：</b>' + esc(t.problem) + '</p>' +
        '<p class="muted"><b>动作：</b>' + esc(t.action) + '</p></div>';
    }).join("");
  });
  var p3 = api("/lifelong/passport/" + state.currentStudent).then(function (r) {
    var skills = r.skills || {}; var meta = r.metacognition || {};
    $("passportView").innerHTML = '<div class="kv"><span>学习者</span><b>' + esc(r.learner_id) + '</b></div>' +
      '<div class="kv"><span>当前阶段</span><b>' + esc(r.current_stage) + '</b></div>' +
      '<div class="kv"><span>掌握度</span><b>' + fmt(skills.mastery) + '</b></div>' +
      '<div class="kv"><span>JOL 偏差</span><b>' + fmt(meta.jol_bias) + '</b></div>' +
      '<div class="kv"><span>犹豫</span><b>' + fmt(meta.hesitation) + '</b></div>' +
      '<p class="muted">' + esc(r.note || "") + '</p>';
  });
  return Promise.all([p1, p2, p3]);
}
function loadSales() {
  var cls = $("classSelect") ? $("classSelect").value : "理科班";
  return api("/sales/ammunition/" + encodeURIComponent(cls)).then(function (r) {
    var k = r.kpis || {};
    $("salesActions").textContent = (r.actions || []).length;
    $("salesRenewal").textContent = k.renewal_opportunities || 0;
    $("salesChurn").textContent = k.churn_risks || 0;
    $("salesReferral").textContent = k.referral_leads || 0;
    var rows = (r.actions || []).map(function (a) {
      return '<tr><td>' + esc(a.priority) + '</td><td>' + esc(a.student_id) + '</td><td>' + esc(a.type) + '</td><td>' + esc(a.signal) + '</td><td>' + esc(a.action) + '</td><td><button class="ghost copy-text" data-text="' + esc(a.script) + '">复制话术</button></td></tr>';
    }).join("");
    $("salesActionList").innerHTML = '<div class="table-wrap"><table><tr><th>优先级</th><th>学生</th><th>类型</th><th>信号</th><th>动作</th><th>话术</th></tr>' + rows + '</table></div>';
    $("salesStudentPages").innerHTML = (r.student_pages || []).map(function (x) {
      return '<div class="ctx-block"><div class="kv"><span>' + esc(x.student_id) + '</span><b>续费概率 ' + fmt(x.renewal_probability) + '</b></div><p class="muted">掌握度 ' + fmt(x.progress.mastery) + '；JOL 偏差 ' + fmt(x.progress.jol_bias) + '；出勤 ' + esc(x.attendance) + '</p><p class="muted">' + esc(x.script) + '</p></div>';
    }).join("");
    var cp = r.class_page || {};
    $("salesClassPage").innerHTML = '<div class="kv"><span>班级人数</span><b>' + (cp.n_students || 0) + '</b></div><div class="kv"><span>平均掌握度</span><b>' + fmt(cp.avg_mastery) + '</b></div><div class="kv"><span>续费机会</span><b>' + (cp.renewal_opportunities || 0) + '</b></div><div class="kv"><span>流失风险</span><b>' + (cp.churn_risks || 0) + '</b></div><div class="kv"><span>转介绍线索</span><b>' + (cp.referral_leads || 0) + '</b></div>';
    var sc = r.scripts || {};
    $("salesScripts").innerHTML = Object.keys(sc).map(function (key) {
      return '<div class="ctx-block"><div class="kv"><span>' + esc(key) + '</span><b>话术</b></div><p class="muted">' + esc(sc[key]) + '</p><button class="ghost copy-text" data-text="' + esc(sc[key]) + '">复制</button></div>';
    }).join("");
    bindCopy();
  });
}
function bindCopy() {
  var btns = document.querySelectorAll(".copy-text");
  for (var i = 0; i < btns.length; i++) {
    btns[i].onclick = function () { if (navigator.clipboard) navigator.clipboard.writeText(this.getAttribute("data-text")); };
  }
}

function loadTeacher() {
  var cls = $("classSelect").value;
  return api("/reports/teacher/" + encodeURIComponent(cls)).then(function (r) {
    $("tStudents").textContent = r.n_students; $("tMastery").textContent = fmt(r.class_mastery_mean);
    $("tTop").textContent = (r.top_intervention || []).length;
    $("teacherSuggestion").textContent = r.suggestion || "";
    var rows = (r.top_intervention || []).map(function (x) {
      return "<tr><td>" + esc(x.student_id) + "</td><td>" + fmt(x.mastery) + "</td><td>" + fmt(x.jol_bias) + "</td><td>" + fmt(x.hesitation) + "</td></tr>";
    }).join("");
    $("teacherTop").innerHTML = '<div class="table-wrap"><table><tr><th>学生</th><th>掌握度</th><th>JOL 偏差</th><th>犹豫</th></tr>' + rows + '</table></div>';
  });
}
function loadDaoql() {
  var sid = state.currentStudent;
  return api("/daoql/events/" + sid).then(function (x) {
    var rows = x.slice(-30).reverse().map(function (e) {
      return "<tr><td>" + esc(e.event_id) + "</td><td>" + esc(e.event_type) + "</td><td>" + esc(e.timestamp) + "</td><td>" + esc(JSON.stringify(e.payload)).slice(0, 80) + "</td></tr>";
    }).join("");
    $("eventsTable").innerHTML = "<tr><th>事件 ID</th><th>类型</th><th>时间</th><th>载荷</th></tr>" + rows;
  }).then(function () {
    return api("/audit?limit=20");
  }).then(function (x) {
    var rows = x.map(function (a) { return "<tr><td>" + esc(a.actor) + "</td><td>" + esc(a.action) + "</td><td>" + esc(a.target) + "</td><td>" + esc(a.created_at) + "</td></tr>"; }).join("");
    $("auditTable").innerHTML = "<tr><th>Actor</th><th>Action</th><th>Target</th><th>时间</th></tr>" + rows;
  });
}
function runPath() {
  var s = $("pathSource").value.trim(), t = $("pathTarget").value.trim(); if (!s || !t) return;
  api("/daoql/causal_path?source=" + encodeURIComponent(s) + "&target=" + encodeURIComponent(t))
    .then(function (x) { $("pathResult").textContent = JSON.stringify(x, null, 2); })
    .catch(function (e) { $("pathResult").textContent = e.message; });
}
function loadReports() {
  api("/reports/org").then(function (x) { $("orgReport").textContent = JSON.stringify(x, null, 2); });
}
function runRag() {
  var q = $("ragQuery").value.trim(); if (!q) return;
  api("/rag/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: q, top_k: 5 }) })
    .then(function (x) { $("ragResult").textContent = JSON.stringify(x, null, 2); });
}
function clearChat() {
  renderChatWelcome();
  if ($("agentMessage")) $("agentMessage").focus();
}

function ambientSignals() {
  var now = Date.now();
  var meta = (((state.learner || {}).passport || {}).metacognition) || {};
  var recent = state.ambient.switches.filter(function (ts) { return now - ts < 120000; });
  return {
    scenario: state.ambient.scenario,
    idle_seconds: Math.max(0, (now - state.ambient.lastActivity) / 1000),
    focus_minutes: Math.max(0, (now - state.ambient.focusStart) / 60000),
    visibility_switches: recent.length,
    hesitation: Number(meta.hesitation || 0),
    repeated_errors: 0
  };
}
function renderAmbientCard(card) {
  var host = $("ambientFeed");
  if (!host || !card) return;
  state.ambient.card = card;
  host.innerHTML = '<article class="ambient-card"><div class="ambient-card-kicker">TENDER · 此刻</div><div class="ambient-card-text">' + esc(card.text) + '</div><div class="ambient-card-action">' + esc(card.action || "做一个最小动作") + '</div><div class="ambient-card-why">为什么出现：' + esc(card.why || "") + '</div><div class="ambient-feedback"><button type="button" data-feedback="useful">有用</button><button type="button" data-feedback="wrong">不是这样</button><button type="button" data-feedback="silence">静默 30 分钟</button></div></article>';
  var buttons = host.querySelectorAll('[data-feedback]');
  for (var i = 0; i < buttons.length; i++) buttons[i].onclick = function () { sendAmbientFeedback(this.getAttribute('data-feedback')); };
}
function ambientWelcome() {
  var host = $("ambientFeed");
  if (!host) return;
  host.innerHTML = '<div class="ambient-card"><div class="ambient-card-kicker">TENDER · QUIET MODE</div><div class="ambient-card-text">我在。平时不打扰，只在可能值得出手时出现一条提示。</div><div class="ambient-card-action">点击右上角“隐私与控制”，可以先看监测范围或手动试一条。</div><div class="ambient-card-why">当前只监测页面可见性、空闲时间和窗口切换，不读取屏幕内容。</div></div>';
}
function requestAmbientCard(force, explicitNeed, extraSignals) {
  if (!state.ambient.active || state.ambient.busy || (state.ambient.card && !force)) return Promise.resolve();
  state.ambient.busy = true;
  var signals = ambientSignals();
  if (extraSignals) Object.keys(extraSignals).forEach(function (k) { signals[k] = extraSignals[k]; });
  if (explicitNeed) signals.explicit_need = true;
  return api('/ambient/plan/' + encodeURIComponent(state.currentStudent), {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({signals: signals, force: !!force})
  }).then(function (r) {
    var status = r.status || 'quiet';
    if (r.card) {
      renderAmbientCard(r.card);
      if ($('ambientStatusText')) $('ambientStatusText').textContent = 'Tender 发现了一个值得提醒的状态';
    } else {
      var labels = {quiet: 'Tender 正在安静观察', cooling_down: '刚提醒过，先不重复打扰', silenced: '当前处于静默时段', daily_limit: '今天提示额度已用完'};
      if ($('ambientStatusText')) $('ambientStatusText').textContent = labels[status] || 'Tender 正在观察';
    }
    return r;
  }).catch(function (e) {
    if ($('ambientStatusText')) $('ambientStatusText').textContent = '弹幕辅助暂时不可用：' + e.message;
  }).finally(function () { state.ambient.busy = false; });
}
function sendAmbientFeedback(feedback) {
  var card = state.ambient.card;
  if (!card || state.ambient.busy) return;
  state.ambient.busy = true;
  api('/ambient/feedback/' + encodeURIComponent(state.currentStudent), {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({card_id: card.card_id, feedback: feedback})
  }).then(function (r) {
    var el = document.querySelector('.ambient-card');
    if (el) el.classList.add('leaving');
    setTimeout(function () {
      state.ambient.card = null;
      if ($('ambientFeed')) $('ambientFeed').innerHTML = '<div class="ambient-dismissed">' + (feedback === 'silence' ? '已静默 30 分钟。需要我时再打开。' : feedback === 'wrong' ? '记下了，这会修正下一次判断。' : '记下了，我会减少无效打扰。') + '</div>';
      if ($('ambientStatusText')) $('ambientStatusText').textContent = r.silence_until ? '静默至 ' + new Date(r.silence_until).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) : '继续安静观察';
    }, 220);
  }).catch(function (e) {
    if ($('ambientStatusText')) $('ambientStatusText').textContent = '反馈失败：' + e.message;
  }).finally(function () { state.ambient.busy = false; });
}
function bindAmbientMonitoring() {
  if (state.ambient.monitoringBound) return;
  state.ambient.monitoringBound = true;
  function activity() { state.ambient.lastActivity = Date.now(); }
  document.addEventListener('mousemove', activity, {passive: true});
  document.addEventListener('keydown', activity, {passive: true});
  document.addEventListener('pointerdown', activity, {passive: true});
  document.addEventListener('visibilitychange', function () {
    state.ambient.switches.push(Date.now());
    state.ambient.switches = state.ambient.switches.filter(function (ts) { return Date.now() - ts < 300000; });
    activity();
  });
  window.addEventListener('blur', function () { state.ambient.switches.push(Date.now()); });
  window.addEventListener('focus', activity);
}
function enterAmbientMode() {
  state.ambient.active = true;
  state.ambient.card = null;
  state.ambient.lastActivity = Date.now();
  state.ambient.focusStart = Date.now();
  state.ambient.switches = [];
  if ($("ambientScenario")) $("ambientScenario").value = state.ambient.scenario;
  bindAmbientMonitoring();
  if ($('ambientSurface')) $('ambientSurface').hidden = false;
  document.body.classList.add('ambient-active');
  ambientWelcome();
  if (state.ambient.timer) clearInterval(state.ambient.timer);
  state.ambient.timer = setInterval(function () { if (!state.ambient.card) requestAmbientCard(false, false); }, 12000);
}
function exitAmbientMode() {
  try { sessionStorage.setItem("tender.ambient.disabled", "1"); } catch (e) {}
  state.ambient.active = false;
  if (state.ambient.timer) { clearInterval(state.ambient.timer); state.ambient.timer = null; }
  if ($('ambientSurface')) $('ambientSurface').hidden = true;
  if ($('ambientControls')) $('ambientControls').hidden = true;
  document.body.classList.remove('ambient-active');
}
function triggerAmbientDemo() {
  state.ambient.card = null;
  if ($('ambientFeed')) $('ambientFeed').innerHTML = '';
  var extra = state.ambient.scenario === "gaokao_registration" ? {scenario:"gaokao_registration", deadline_hours:12, missing_items:1, confirmation_pending:true} : {scenario:"score_improvement", days_to_target:7, weak_skill_count:2};
  requestAmbientCard(true, false, extra);
}
function updateAmbientScenario() {
  if (!$('ambientScenario')) return;
  state.ambient.scenario = $('ambientScenario').value;
  if ($('ambientScenarioHint')) $('ambientScenarioHint').textContent = state.ambient.scenario === "gaokao_registration" ? "截止事项、材料确认和流程状态" : "错点、卡点、最小练习和结果验证";
}

function refreshAll() {
  setBusy("refreshBtn", true);
  setStatus(true, "正在刷新…");
  return loadStudents().then(function () {
    return loadOverview();
  }).then(function () {
    switchPage(state.currentPage || "learner");
    setStatus(true, "已刷新");
  }).catch(function (e) {
    setStatus(false, "刷新失败：" + e.message);
  }).finally(function () {
    setBusy("refreshBtn", false);
  });
}
document.addEventListener("DOMContentLoaded", function () {
  on("refreshBtn", "click", refreshAll);
  on("ambientModeBtn", "click", function () { try { sessionStorage.removeItem("tender.ambient.disabled"); } catch (e) {} enterAmbientMode(); });
  on("ambientExitBtn", "click", exitAmbientMode);
  on("ambientControlsBtn", "click", function () { if ($("ambientControls")) $("ambientControls").hidden = !$("ambientControls").hidden; });
  on("ambientCloseControls", "click", function () { if ($("ambientControls")) $("ambientControls").hidden = true; });
  on("ambientDemoBtn", "click", triggerAmbientDemo);
  on("ambientScenario", "change", updateAmbientScenario);
  on("clearChatBtn", "click", clearChat);
  on("sendAgentBtn", "click", sendAgent);
  on("loadTeacherBtn", "click", loadTeacher);
  on("loadHeadTeacherBtn", "click", loadHeadTeacher);
  on("htClassSelect", "change", loadHeadTeacher);
  on("htNoteBtn", "click", submitHeadTeacherNote);
  on("loadSubjectTeacherBtn", "click", loadSubjectTeacher);
  on("stClassSelect", "change", loadSubjectTeacher);
  on("stTeacherMode", "change", loadSubjectTeacher);
  on("stCreateTaskBtn", "click", createTeachingTask);
  on("loadDormBtn", "click", loadDorm);
  on("dormClassSelect", "change", loadDorm);
  on("loadInstitutionScheduleBtn", "click", loadInstitutionSchedule);
  on("institutionScheduleClass", "change", loadInstitutionSchedule);
  on("institutionScheduleBtn", "click", createInstitutionSchedule);
  on("financeEstimateBtn", "click", estimateFinance);
  on("wfReqBtn", "click", createWorkflowRequirement);
  on("wfReviewBtn", "click", createWorkflowReview);
  on("wfIncidentBtn", "click", createWorkflowIncident);
  on("wfDelayBtn", "click", createWorkflowDelay);
  on("wfAcceptanceBtn", "click", createWorkflowAcceptance);
  on("wbLaunchBtn", "click", launchWorkbench);
  if ($("wbAudienceRole")) $("wbAudienceRole").onchange = function () { $("wbAudienceCustom").style.display = this.value === "custom" ? "block" : "none"; };
  if ($("wbAudienceCustom")) $("wbAudienceCustom").style.display = "none";
  on("wbRefreshBtn", "click", loadWorkbench);
  on("wbStopBtn", "click", stopWorkbench);
  on("loadAdvisorBtn", "click", loadAdvisorHome);
  on("pathBtn", "click", runPath);
  on("ragBtn", "click", runRag);
  on("learnerExportBtn", "click", function () { if (state.currentStudent) window.location.href = "/learner/export/" + encodeURIComponent(state.currentStudent); });
  on("learnerReflectionBtn", "click", submitLearnerReflection);
  initAgencyForm();
  on("recordSnapshotBtn", "click", recordMentalizationSnapshot);
  on("refreshTimelineBtn", "click", loadTimeline);
  on("generateAgentBtn", "click", generateExpertAgent);
  on("refreshMarketBtn", "click", loadAgentMarket);
  on("tryGeneratedAgentBtn", "click", function () {
    var generated = state.lastGeneratedAgent || {};
    if (generated.agent_id) invokeSelectedAgent(generated.agent_id, generated.name);
  });
  on("refreshGeneratedMarketBtn", "click", loadAgentMarket);
  on("agentSearch", "keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); loadAgentMarket(); } });
  on("agentInvokePrompt", "keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("agentSearch").focus(); }
  });
  on("learnerAskBtn", "click", function () {
    var prompt = (state.learner.ai_coach || {}).prompt || "帮我看看下一步应该怎么开始？";
    switchPage("agent");
    $("agentMessage").value = prompt;
    sendAgent();
  });
  on("agentMessage", "keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendAgent(); } });
  bindQuickPrompts();
  Promise.all([loadStudents(), loadRoles()]).then(function () {
    setStatus(true, "已连接");
    try { if (!sessionStorage.getItem("tender.ambient.disabled")) enterAmbientMode(); } catch (e) { enterAmbientMode(); }
  }).catch(function (e) { setStatus(false, "连接失败：" + e.message); });
});





(function () {
  "use strict";

  const API = "";
  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  const WORKBENCH_AGENTS = [
    { id: "coordinator", name: "协调者", scope: "拆解任务、分派、汇总、等待审批", short: "CO", color: "mint" },
    { id: "content_curator", name: "内容 Agent", scope: "题库、讲义、重点词汇和句型抽取", short: "CN", color: "violet" },
    { id: "assessment", name: "评估 Agent", scope: "批改、错因统计和学习状态更新", short: "AS", color: "blue" },
    { id: "student_tutor", name: "学生教练", scope: "最小提示、复盘和复习安排", short: "ST", color: "mint" },
    { id: "external_communication", name: "对外沟通", scope: "按接收方角色生成待审批草稿", short: "EX", color: "amber" },
    { id: "safety_guardrail", name: "安全护栏", scope: "隐私、排名、越权和风险语言检查", short: "SG", color: "rose" }
  ];
  const NODE_POSITIONS = {
    content_curator: { x: 19, y: 19 },
    assessment: { x: 81, y: 19 },
    student_tutor: { x: 17, y: 77 },
    external_communication: { x: 83, y: 77 },
    safety_guardrail: { x: 50, y: 92 }
  };
  const EDGES = [
    ["coordinator", "content_curator"],
    ["coordinator", "assessment"],
    ["assessment", "student_tutor"],
    ["assessment", "external_communication"],
    ["external_communication", "safety_guardrail"]
  ];
  const EVENT_LABELS = {
    agent_thread_created: "协作线程建立",
    agent_run_completed: "Agent 回合完成",
    agent_artifact_created: "产出物生成",
    agent_approval_requested: "等待人工审批",
    agent_approval_decided: "审批完成",
    agent_handoff: "Agent 交接",
    agent_thread_stopped: "线程已停止",
    subjective_experience_summary: "主观体验摘要",
    subjective_experience_node: "体验节点",
    head_teacher_note: "学习观察",
    mentalization_snapshot: "心智状态快照",
    ambient_card_shown: "环境辅助提示",
    ambient_dialogue_reply: "Agent 回复",
    assessment_result: "学习结果",
    learning_task_completed: "学习任务完成"
  };

  const state = {
    studentId: params.get("student") || localStorage.getItem("tender.student") || "",
    role: "admin",
    token: null,
    authBusy: null,
    fixedAgents: [],
    threads: [],
    selectedThread: null,
    selectedAgentId: "coordinator",
    filter: "all",
    context: null,
    ambient: null,
    experimental: null,
    busy: false,
    lastLoadedAt: null,
    pollTimer: null,
    toastTimer: null
  };

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, (x) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[x]));
  }

  const DEMO_ROLES = ["admin", "auditor", "learner", "parent", "advisor"];

  async function createDemoSession(role) {
    const response = await fetch(API + "/auth/demo-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor_id: state.studentId, role: role, learner_id: state.studentId })
    });
    let data = {};
    try { data = await response.json(); } catch (_) { data = {}; }
    if (!response.ok) {
      const error = new Error(typeof data.detail === "string" ? data.detail : "无法建立本地会话");
      error.status = response.status;
      error.code = data.detail;
      throw error;
    }
    return data;
  }

  function ensureSession() {
    if (state.token) return Promise.resolve(state.token);
    if (state.authBusy) return state.authBusy;
    const preferred = DEMO_ROLES.includes(state.role) ? state.role : "admin";
    const candidates = [preferred, "admin", "auditor", "learner"].filter((role, index, all) => all.indexOf(role) === index);
    state.authBusy = (async () => {
      let lastError = null;
      for (const role of candidates) {
        try {
          const data = await createDemoSession(role);
          state.role = role;
          state.token = data.token;
          return data.token;
        } catch (error) {
          lastError = error;
          if (error.code !== "invalid_role") break;
        }
      }
      throw lastError || new Error("无法建立本地会话");
    })().catch((error) => {
      state.token = null;
      state.authBusy = null;
      throw error;
    });
    return state.authBusy;
  }

  function api(path, options) {
    options = options || {};
    return ensureSession().then((token) => {
      const headers = Object.assign({}, options.headers || {});
      headers.Authorization = "Bearer " + token;
      headers["X-Tender-Actor"] = state.studentId;
      headers["X-Tender-Role"] = state.role;
      headers["X-Tender-Learner"] = state.studentId;
      return fetch(API + path, Object.assign({}, options, { headers })).then(async (response) => {
        const raw = await response.text();
        let data = null;
        if (raw) {
          try { data = JSON.parse(raw); } catch (_) { data = null; }
        }
        if (response.status === 401 && !options.authRetried) {
          state.token = null;
          state.authBusy = null;
          return api(path, Object.assign({}, options, { authRetried: true }));
        }
        if (!response.ok) {
          const detail = data && (data.detail || data.message);
          throw new Error(typeof detail === "string" ? detail : (detail ? JSON.stringify(detail) : "请求未完成（" + response.status + "）"));
        }
        return data || {};
      });
    });
  }

  async function loadStudents() {
    try {
      const accounts = JSON.parse(localStorage.getItem("tender.accounts") || "[]");
      const rows = Array.isArray(accounts) ? accounts.filter((item) => item && item.studentId) : [];
      if (!rows.length) return;
      const select = $("studentSelect");
      select.innerHTML = rows.map((item) => '<option value="' + esc(item.studentId) + '">' + esc((item.displayName || item.studentId) + " · " + item.studentId) + "</option>").join("");
      if (!rows.some((item) => item.studentId === state.studentId)) state.studentId = rows[0].studentId;
      select.value = state.studentId;
    } catch (_) {}
  }

  function setConnector(text, ok) {
    $("connectorText").textContent = text;
    const dot = document.querySelector(".connector-pill .pulse-dot");
    if (dot) dot.style.background = ok === false ? "var(--rose)" : "var(--mint)";
  }

  function showToast(message, isError) {
    const toast = $("toast");
    toast.textContent = message;
    toast.className = "toast show" + (isError ? " error" : "");
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => { toast.className = "toast"; }, 4200);
  }

  function ageText(value) {
    if (!value) return "刚刚";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
    if (seconds < 60) return seconds + " 秒前";
    if (seconds < 3600) return Math.floor(seconds / 60) + " 分钟前";
    if (seconds < 86400) return Math.floor(seconds / 3600) + " 小时前";
    return Math.floor(seconds / 86400) + " 天前";
  }

  function shortDate(value) {
    if (!value) return "未知时间";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  }

  function statusGroup(status) {
    if (status === "waiting_approval" || status === "needs_revision") return "waiting";
    if (status === "completed") return "completed";
    if (status === "stopped") return "stopped";
    return "working";
  }

  function statusLabel(status) {
    return ({ draft: "待执行", waiting_approval: "等待审批", completed: "已交付", needs_revision: "需修改", stopped: "已停止", working: "执行中", waiting: "需要我", idle: "待命" })[status] || status || "待命";
  }

  function agentById(id) {
    return WORKBENCH_AGENTS.find((agent) => agent.id === id) || null;
  }

  function runForAgent(thread, agentId) {
    if (!thread || !Array.isArray(thread.runs)) return null;
    return thread.runs.find((run) => run.agent_id === agentId) || null;
  }

  function pendingApprovalForAgent(thread, agentId) {
    if (!thread || !Array.isArray(thread.approvals)) return null;
    return thread.approvals.find((item) => item.status === "pending" && item.requested_by === agentId) || null;
  }

  function statusForAgent(agentId, thread) {
    if (!thread) return agentId === "coordinator" ? "idle" : "idle";
    if (thread.status === "stopped") return "stopped";
    if (thread.status === "needs_revision") {
      if (agentId === "external_communication") return "waiting";
      if (runForAgent(thread, agentId)) return "completed";
      return "idle";
    }
    if (thread.status === "waiting_approval") {
      if (pendingApprovalForAgent(thread, agentId)) return "waiting";
      if (runForAgent(thread, agentId)) return "completed";
      return "idle";
    }
    if (thread.status === "completed") return runForAgent(thread, agentId) ? "completed" : "idle";
    if (thread.status === "draft") return agentId === "coordinator" ? "working" : "idle";
    return runForAgent(thread, agentId) ? "completed" : "idle";
  }

  function outputSummary(value) {
    if (value == null) return "暂无输出";
    if (typeof value === "string") return value.length > 220 ? value.slice(0, 220) + "…" : value;
    if (typeof value === "object") {
      if (value.experimental_api && value.experimental_api.text) return value.experimental_api.text;
      const keys = ["decision", "goal", "summary", "assignment", "priority", "recommendation", "decision_text"];
      for (const key of keys) {
        if (value[key]) return typeof value[key] === "string" ? value[key] : JSON.stringify(value[key]);
      }
      return JSON.stringify(value, null, 2).slice(0, 420);
    }
    return String(value);
  }

  function eventSummary(event) {
    if (!event) return "暂无摘要";
    const summary = event.summary;
    if (summary && typeof summary === "object") {
      if (summary.primary_region) return summary.primary_region.name + (summary.primary_region.evidence && summary.primary_region.evidence.length ? " · " + summary.primary_region.evidence.join("、") : "");
      if (summary.memory_type) return summary.memory_type.label || summary.memory_type.kind || "体验节点";
      if (summary.text) return String(summary.text);
      if (summary.summary) return String(summary.summary);
      const compact = JSON.stringify(summary);
      return compact === "{}" ? EVENT_LABELS[event.event_type] || event.event_type : compact;
    }
    if (summary) return String(summary);
    return EVENT_LABELS[event.event_type] || event.event_type || "本地事件";
  }

  function renderMetrics() {
    const threads = state.threads;
    const workingThreads = threads.filter((item) => statusGroup(item.status) === "working").length;
    const completedThreads = threads.filter((item) => statusGroup(item.status) === "completed").length;
    const waitingApprovals = threads.reduce((sum, item) => sum + (item.pending_approvals || 0), 0);
    const exp = state.experimental || {};
    $("metricWaiting").textContent = waitingApprovals;
    $("metricWaitingSub").textContent = waitingApprovals ? "有结果等待确认" : "当前无待办";
    $("metricWorking").textContent = workingThreads;
    $("metricCompleted").textContent = completedThreads;
    $("metricAgents").textContent = exp.configured ? (exp.model || "已连接") : "未配置";
    $("metricAgentsSub").textContent = exp.configured ? (exp.provider || "实验模型已连接") : "检查实验 API 配置";
    const apiChip = $("experimentalRuntimeChip");
    if (apiChip) {
      apiChip.textContent = exp.configured ? "实验 API · " + (exp.model || "ready") : "实验 API · 未配置";
      apiChip.title = exp.notice || "实验 API 状态";
    }
    $("agentDutySummary").textContent = (state.fixedAgents.length + WORKBENCH_AGENTS.length) + " 个 Agent 在岗";
    $("sessionSummary").textContent = waitingApprovals + " 项待处理 · " + completedThreads + " 个已交付";
    $("liveTimestamp").textContent = state.lastLoadedAt ? "更新于 " + state.lastLoadedAt.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "等待数据";
    $("countAll").textContent = threads.length;
    $("countWorking").textContent = workingThreads;
    $("countWaiting").textContent = threads.filter((item) => statusGroup(item.status) === "waiting").length;
    $("countCompleted").textContent = completedThreads;
    $("countStopped").textContent = threads.filter((item) => statusGroup(item.status) === "stopped").length;
    [["metricWaitingCard", "waiting"], ["metricWorkingCard", "working"], ["metricCompletedCard", "completed"]].forEach(([id, filter]) => {
      const card = $(id);
      if (card) card.dataset.active = state.filter === filter ? "true" : "false";
    });
    renderCommandSummary(waitingApprovals, workingThreads, completedThreads);
  }

  function renderCommandSummary(waitingApprovals, workingThreads, completedThreads) {
    const waitingThread = state.threads.find((item) => statusGroup(item.status) === "waiting") || null;
    const workingThread = state.threads.find((item) => statusGroup(item.status) === "working") || null;
    const completedThread = state.threads.find((item) => statusGroup(item.status) === "completed") || null;
    let title = "还没有协作线程。";
    let subtitle = "先发起一轮，系统会显示谁在工作、谁在等你。";
    let primary = "发起协作";
    let target = null;
    if (waitingThread) {
      const waitingThreadCount = state.threads.filter((item) => statusGroup(item.status) === "waiting").length;
      title = waitingThreadCount + " 个线程等待你处理。";
      subtitle = "当前查看「" + waitingThread.title + "」；处理后会进入下一个待办。";
      primary = "处理审批";
      target = waitingThread.thread_id;
    } else if (workingThread) {
      title = "Agent 正在执行。";
      subtitle = "「" + workingThread.title + "」完成后会进入“需要我”。";
      primary = "查看进度";
      target = workingThread.thread_id;
    } else if (completedThread) {
      title = "最近一轮已交付。";
      subtitle = "「" + completedThread.title + "」已完成，可直接查看结果。";
      primary = "查看结果";
      target = completedThread.thread_id;
    }
    $("pageTitle").textContent = title;
    $("commandSubtitle").textContent = subtitle;
    $("commandEyebrow").textContent = waitingApprovals ? "ACTION REQUIRED · 需要你" : "TODAY · 当前状态";
    $("primaryActionBtn").textContent = primary;
    $("primaryActionBtn").onclick = async () => {
      if (!target) return runDemo();
      if (waitingThread) setFilter("waiting");
      else if (workingThread) setFilter("working");
      else setFilter("completed");
      await loadThread(target);
      if (waitingThread) {
        const queue = document.querySelector(".sessions-panel");
        if (queue) queue.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    };
    $("inspectBtn").textContent = waitingThread ? "查看线程" : "查看拓扑";
    $("inspectBtn").onclick = () => {
      const targetNode = waitingThread ? document.querySelector(".sessions-panel") : document.querySelector(".battle-stage");
      if (targetNode) targetNode.scrollIntoView({ behavior: "smooth", block: "start" });
    };
  }

  function renderNetwork() {
    const thread = state.selectedThread;
    const nodes = $("agentNodes");
    nodes.innerHTML = WORKBENCH_AGENTS.filter((agent) => agent.id !== "coordinator").map((agent) => {
      const pos = NODE_POSITIONS[agent.id] || { x: 50, y: 50 };
      const status = statusForAgent(agent.id, thread);
      const run = runForAgent(thread, agent.id);
      const selected = state.selectedAgentId === agent.id ? " selected" : "";
      return '<button class="agent-node' + selected + '" type="button" data-agent-id="' + esc(agent.id) + '" data-status="' + esc(status) + '" style="--x:' + pos.x + '%;--y:' + pos.y + '%" aria-label="查看 ' + esc(agent.name) + '">' +
        '<span class="node-name">' + esc(agent.short) + " · " + esc(agent.name) + '<i class="node-status" aria-hidden="true"></i></span>' +
        '<span class="node-role">' + esc(agent.scope) + "</span>" +
        '<span class="node-foot"><b>' + esc(statusLabel(status)) + "</b><span>" + (run ? "RUN " + esc(String(run.seq).padStart(2, "0")) : "STANDBY") + "</span></span>" +
        "</button>";
    }).join("");

    const hub = $("hubNode");
    hub.setAttribute("data-status", statusForAgent("coordinator", thread));
    hub.classList.toggle("selected", state.selectedAgentId === "coordinator");
    hub.setAttribute("aria-label", "查看协调者 Agent，当前" + statusLabel(statusForAgent("coordinator", thread)));

    const positions = Object.assign({}, NODE_POSITIONS, { coordinator: { x: 50, y: 46 } });
    const svg = $("networkLines");
    svg.innerHTML = EDGES.map(([from, to]) => {
      const a = positions[from];
      const b = positions[to];
      const fromStatus = statusForAgent(from, thread);
      const toStatus = statusForAgent(to, thread);
      let cls = "idle";
      if (toStatus === "waiting" || fromStatus === "waiting") cls = "waiting";
      else if (toStatus === "working" || fromStatus === "working" || toStatus === "completed" || fromStatus === "completed") cls = "active";
      return '<line x1="' + a.x + '" y1="' + a.y + '" x2="' + b.x + '" y2="' + b.y + '" class="' + cls + '"></line>';
    }).join("");

    nodes.querySelectorAll("[data-agent-id]").forEach((node) => {
      node.addEventListener("click", () => selectAgent(node.getAttribute("data-agent-id")));
    });
    hub.onclick = () => selectAgent("coordinator");
    hub.onkeydown = (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectAgent("coordinator"); } };
    $("networkNote").textContent = thread ? "当前线程：" + thread.title : "当前没有选中线程 · 显示待命拓扑";
  }

  function renderSignalFeed() {
    const events = ((state.context && state.context.recent_events) || []).slice(-10).reverse();
    const box = $("signalList");
    if (!events.length) {
      box.innerHTML = '<div class="empty-mini">最近还没有可显示的 DAOQL 事件。</div>';
      return;
    }
    box.innerHTML = events.map((event) => {
      const label = EVENT_LABELS[event.event_type] || event.event_type || "本地事件";
      return '<article class="signal-item"><div class="signal-meta"><span>' + esc(label) + "</span><span>" + esc(ageText(event.timestamp)) + '</span></div><div class="signal-text">' + esc(eventSummary(event)) + "</div></article>";
    }).join("");
  }

  function filteredThreads() {
    if (state.filter === "all") return state.threads;
    return state.threads.filter((thread) => statusGroup(thread.status) === state.filter);
  }

  function renderSessions() {
    const list = $("sessionList");
    const filtered = filteredThreads();
    if (!state.threads.length) {
      list.innerHTML = '<div class="empty-state"><div class="empty-orbit" aria-hidden="true"></div><h3>还没有 Agent 协作线程</h3><p>发起一轮协作，首屏会显示需要你处理的动作。</p><div class="empty-actions"><button class="btn primary" type="button" data-demo="1">运行一轮协作</button><a class="btn" href="/ui/#workbench">打开学习工作台</a></div></div>';
      bindSessionActions();
      return;
    }
    if (!filtered.length) {
      list.innerHTML = '<div class="empty-state"><div class="empty-orbit" aria-hidden="true"></div><h3>此分组为空</h3><p>切换到“全部会话”查看其他线程。</p><button class="btn" type="button" data-clear-filter="1">查看全部</button></div>';
      bindSessionActions();
      return;
    }
    list.innerHTML = filtered.map((thread) => {
      const selected = state.selectedThread && state.selectedThread.thread_id === thread.thread_id ? " selected" : "";
      const group = statusGroup(thread.status);
      const chain = group === "waiting" ? ["CO", "AS", "EX", "SG"] : (group === "completed" ? ["CO", "CN", "AS", "ST", "EX", "SG"] : ["CO", "CN", "AS"]);
      return '<button class="session-row' + selected + '" type="button" data-thread="' + esc(thread.thread_id) + '" data-status="' + esc(thread.status) + '">' +
        '<span class="session-symbol" aria-hidden="true">' + (group === "waiting" ? "!" : group === "completed" ? "✓" : group === "stopped" ? "×" : "◌") + "</span>" +
        '<span class="session-main"><span class="session-title">' + esc(thread.title) + '</span><span class="session-sub">' + esc(thread.objective || "未填写任务目标") + "</span></span>" +
        '<span class="session-chain" aria-label="Agent 链路">' + chain.map((short) => '<i class="mini-agent">' + esc(short) + "</i>").join("") + "</span>" +
        '<span class="session-meta"><b>' + esc(statusLabel(thread.status)) + "</b>" + esc((thread.run_count || 0) + " 回合 · " + ageText(thread.updated_at)) + "</span>" +
        '<span class="session-arrow" aria-hidden="true">›</span></button>';
    }).join("");
    bindSessionActions();
  }

  function bindSessionActions() {
    const list = $("sessionList");
    list.querySelectorAll("[data-thread]").forEach((button) => {
      button.addEventListener("click", () => loadThread(button.getAttribute("data-thread")));
    });
    const demo = list.querySelector("[data-demo]");
    if (demo) demo.addEventListener("click", runDemo);
    const clear = list.querySelector("[data-clear-filter]");
    if (clear) clear.addEventListener("click", () => setFilter("all"));
  }

  function renderPeek() {
    const thread = state.selectedThread;
    const agent = agentById(state.selectedAgentId) || agentById("coordinator");
    const status = statusForAgent(agent.id, thread);
    const run = runForAgent(thread, agent.id);
    const approval = pendingApprovalForAgent(thread, agent.id);
    const fixed = state.fixedAgents.find((item) => item.agent_id === agent.id);
    $("peekTitle").textContent = agent.name;
    const badge = $("peekStatus");
    badge.textContent = statusLabel(status);
    badge.className = "status-badge " + status;
    const dataScopes = fixed && fixed.data_scopes ? fixed.data_scopes : defaultScopes(agent.id);
    const body = [];
    body.push('<p class="peek-description">' + esc(agent.scope || (fixed && fixed.description) || "Tender 协作 Agent") + "</p>");
    body.push('<div class="detail-section"><div class="detail-label">CURRENT ACTION</div><p class="detail-value">' + esc(run ? run.summary : (approval ? "草稿已生成，等待人工审批。" : "待命。当前没有需要此 Agent 执行的动作。")) + "</p></div>");
    const experimental = run && run.output && run.output.experimental_api;
    if (experimental) {
      const expText = experimental.text || experimental.boundary || "实验 API 未返回内容。";
      body.push('<div class="detail-section"><div class="detail-label">EXPERIMENTAL API</div><p class="detail-value">' + esc(expText) + '</p><div class="scope-list"><span class="scope">' + esc(experimental.provider || "unknown") + '</span><span class="scope">' + esc(experimental.model || "unknown") + '</span><span class="scope">' + esc(experimental.latency_ms != null ? experimental.latency_ms + " ms" : experimental.status || "status") + '</span></div><p class="detail-value">' + esc(experimental.boundary || "") + "</p></div>");
    }
    body.push('<div class="detail-section"><div class="detail-label">AUTHORIZED CONTEXT</div><div class="scope-list">' + dataScopes.map((scope) => '<span class="scope">' + esc(scope) + "</span>").join("") + "</div></div>");
    if (run && !experimental) {
      body.push('<div class="detail-section"><div class="detail-label">LATEST OUTPUT</div><p class="detail-value">' + esc(outputSummary(run.output)) + "</p></div>");
    }
    $("peekBody").innerHTML = body.join("");

    const actions = [];
    actions.push('<a class="btn small" href="/ui/#workbench">打开学习工作台</a>');
    if (approval) {
      actions.push('<button class="btn small primary" type="button" id="peekApproveBtn">批准</button>');
      actions.push('<button class="btn small danger" type="button" id="peekRejectBtn">退回</button>');
    }
    if (thread) actions.push('<button class="btn small amber" type="button" id="focusThreadBtn">查看线程摘要</button>');
    if (thread && thread.status !== "completed" && thread.status !== "stopped") actions.push('<button class="btn small danger" type="button" id="stopThreadBtn">停止本线程</button>');
    $("peekActions").innerHTML = actions.join("");
    if ($("peekApproveBtn")) $("peekApproveBtn").onclick = () => decideApproval(approval.approval_id, "approved");
    if ($("peekRejectBtn")) $("peekRejectBtn").onclick = () => decideApproval(approval.approval_id, "changes_requested");
    if ($("focusThreadBtn")) $("focusThreadBtn").onclick = () => focusThreadSummary(thread);
    if ($("stopThreadBtn")) $("stopThreadBtn").onclick = () => stopSelectedThread();
  }

  function defaultScopes(agentId) {
    const scopes = {
      coordinator: ["task", "policy", "handoff"],
      content_curator: ["authorized_curriculum", "item_bank"],
      assessment: ["learning_results", "tender_state"],
      student_tutor: ["approved_student_cards", "learning_evidence"],
      external_communication: ["approved_summary", "recipient_profile"],
      safety_guardrail: ["minimal_safety_signals", "artifact_check"]
    };
    return scopes[agentId] || ["authorized_summary"];
  }

  function focusThreadSummary(thread) {
    state.selectedAgentId = "coordinator";
    renderNetwork();
    renderPeek();
    $("peekBody").scrollTop = 0;
    showToast("已定位到线程「" + thread.title + "」的协调者视图。");
  }

  function renderApprovals() {
    const thread = state.selectedThread;
    const approvals = thread && Array.isArray(thread.approvals) ? thread.approvals.filter((item) => item.status === "pending") : [];
    $("queueCount").textContent = approvals.length + " 项";
    const box = $("approvalList");
    if (!approvals.length) {
      box.innerHTML = '<div class="empty-mini">当前没有待审批动作。</div>';
      return;
    }
    box.innerHTML = approvals.map((approval) => {
      const artifact = thread.artifacts.find((item) => item.artifact_id === approval.artifact_id);
      return '<div class="queue-item"><div class="queue-copy"><strong>' + esc(artifact ? artifact.title : "待审批草稿") + '</strong><span>' + esc(agentById(approval.requested_by) ? agentById(approval.requested_by).name : approval.requested_by) + " 请求 · " + esc(ageText(approval.created_at)) + '</span></div><div class="queue-actions"><button class="btn small danger" type="button" data-approval="' + esc(approval.approval_id) + '" data-decision="changes_requested">退回</button><button class="btn small primary" type="button" data-approval="' + esc(approval.approval_id) + '" data-decision="approved">批准</button></div></div>';
    }).join("");
    box.querySelectorAll("[data-approval]").forEach((button) => {
      button.addEventListener("click", () => decideApproval(button.getAttribute("data-approval"), button.getAttribute("data-decision")));
    });
  }

  function renderTimeline() {
    const thread = state.selectedThread;
    const box = $("timelineList");
    if (!thread) {
      box.innerHTML = '<div class="empty-mini">选择线程后显示 Agent 交接与产出轨迹。</div>';
      return;
    }
    const events = [];
    (thread.runs || []).forEach((run) => events.push({ type: "run", at: run.created_at, title: "Agent " + String(run.seq).padStart(2, "0") + " · " + run.agent_name, text: run.summary }));
    (thread.handoffs || []).forEach((handoff) => events.push({ type: "handoff", at: handoff.created_at, title: "交接 · " + (agentById(handoff.from_agent) || {}).name + " → " + (agentById(handoff.to_agent) || {}).name, text: handoff.reason }));
    events.sort((a, b) => String(a.at).localeCompare(String(b.at)));
    if (!events.length) {
      box.innerHTML = '<div class="empty-mini">线程尚未执行；运行一轮协作后会显示 6 个 Agent 回合。</div>';
      return;
    }
    box.innerHTML = events.map((event) => '<div class="timeline-item"><div class="timeline-time">' + esc(shortDate(event.at)) + '</div><div class="timeline-node" aria-hidden="true"></div><div class="timeline-copy"><b>' + esc(event.title) + "</b><span>" + esc(event.text || "已记录") + "</span></div></div>").join("");
  }

  function renderAll() {
    renderMetrics();
    renderNetwork();
    renderSignalFeed();
    renderSessions();
    renderPeek();
    renderApprovals();
    renderTimeline();
  }

  function selectAgent(agentId) {
    state.selectedAgentId = agentId;
    renderNetwork();
    renderPeek();
  }

  function setFilter(filter) {
    state.filter = filter;
    document.querySelectorAll("#filterNav [data-filter]").forEach((button) => {
      const active = button.getAttribute("data-filter") === filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    renderSessions();
  }

  async function loadThread(threadId) {
    if (!threadId) return;
    try {
      const detail = await api("/workbench/threads/" + encodeURIComponent(threadId) + "?viewer_role=teacher");
      state.selectedThread = detail;
      const pending = (detail.approvals || []).find((item) => item.status === "pending");
      state.selectedAgentId = pending ? pending.requested_by : "coordinator";
      renderAll();
    } catch (error) {
      showToast("无法读取线程：" + error.message, true);
    }
  }

  async function loadData(options) {
    options = options || {};
    if (state.busy && options.silent) return;
    state.busy = true;
    if (!options.silent) setConnector("正在同步本地运行时", true);
    try {
      const [fixedResult, threadsResult, contextResult, ambientResult, experimentalResult] = await Promise.all([
        api("/agents/fixed"),
        api("/workbench/threads?limit=40&student_id=" + encodeURIComponent(state.studentId)),
        api("/tender/context/" + encodeURIComponent(state.studentId)),
        api("/ambient/status/" + encodeURIComponent(state.studentId)),
        api("/workbench/experimental/status")
      ]);
      state.fixedAgents = Array.isArray(fixedResult.agents) ? fixedResult.agents : [];
      state.threads = Array.isArray(threadsResult.threads) ? threadsResult.threads : [];
      state.context = contextResult || {};
      state.ambient = ambientResult || {};
      state.experimental = experimentalResult || {};
      if (state.selectedThread) {
        const exists = state.threads.some((item) => item.thread_id === state.selectedThread.thread_id);
        if (exists) {
          state.selectedThread = await api("/workbench/threads/" + encodeURIComponent(state.selectedThread.thread_id) + "?viewer_role=teacher");
          const pending = (state.selectedThread.approvals || []).find((item) => item.status === "pending");
          state.selectedAgentId = pending ? pending.requested_by : state.selectedAgentId;
        } else {
          state.selectedThread = null;
        }
      }
      if (!state.selectedThread && state.threads.length) {
        state.selectedThread = await api("/workbench/threads/" + encodeURIComponent(state.threads[0].thread_id) + "?viewer_role=teacher");
        const pending = (state.selectedThread.approvals || []).find((item) => item.status === "pending");
        state.selectedAgentId = pending ? pending.requested_by : "coordinator";
      }
      state.lastLoadedAt = new Date();
      setConnector("本地运行时已连接", true);
      renderAll();
      if (!options.silent) showToast("指挥台已同步最新状态。");
    } catch (error) {
      setConnector("本地运行时未连接", false);
      showToast("同步失败：" + error.message, true);
    } finally {
      state.busy = false;
    }
  }

  async function runDemo() {
    const button = $("runDemoBtn");
    button.disabled = true;
    setConnector("正在分派 Agent 团队", true);
    try {
      const now = new Date();
      const label = now.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
      const created = await api("/workbench/threads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: state.studentId + " · 心智化支持回合 " + label,
          objective: "读取当前学习证据，完成分诊、内容、评估、教练、沟通与安全检查；只生成待审批草稿，不自动发送。",
          student_id: state.studentId,
          class_id: "理科班",
          created_by_role: "admin",
          task_type: "mentalization_support",
          audience_role: "parent",
          audience_config: { recipient_label: "家长", purpose: "同步学习支持建议", tone: "清晰、克制、不制造焦虑" },
          context: { source: "agent_command_center", use_experimental_api: true }
        })
      });
      await api("/workbench/threads/" + encodeURIComponent(created.thread_id) + "/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ focus_students: [state.studentId], context_overrides: { use_experimental_api: true } })
      });
      state.selectedThread = await api("/workbench/threads/" + encodeURIComponent(created.thread_id) + "?viewer_role=teacher");
      state.selectedAgentId = "external_communication";
      setFilter("all");
      await loadData({ silent: true });
      showToast("一轮实验协作已完成：6 个 Agent 回合、5 次交接、1 个待审批草稿。");
    } catch (error) {
      showToast("启动失败：" + error.message, true);
    } finally {
      button.disabled = false;
    }
  }

  async function decideApproval(approvalId, decision) {
    try {
      await api("/workbench/approvals/" + encodeURIComponent(approvalId) + "/decide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision: decision, reason: decision === "approved" ? "指挥台人工批准" : "指挥台要求修改", actor: "admin" })
      });
      await loadData({ silent: true });
      showToast(decision === "approved" ? "草稿已批准。" : "草稿已退回修改。");
    } catch (error) {
      showToast("审批失败：" + error.message, true);
    }
  }

  async function stopSelectedThread() {
    if (!state.selectedThread) return;
    try {
      await api("/workbench/threads/" + encodeURIComponent(state.selectedThread.thread_id) + "/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "负责人在 Agent 指挥台手动停止", actor: "admin" })
      });
      await loadData({ silent: true });
      showToast("线程已停止；历史轨迹仍保留。");
    } catch (error) {
      showToast("停止失败：" + error.message, true);
    }
  }

  function bindEvents() {
    document.querySelectorAll("#filterNav [data-filter]").forEach((button) => {
      button.addEventListener("click", () => setFilter(button.getAttribute("data-filter")));
    });
    $("refreshBtn").addEventListener("click", () => loadData());
    $("runDemoBtn").addEventListener("click", runDemo);
    $("metricWaitingCard").addEventListener("click", () => setFilter("waiting"));
    $("metricWorkingCard").addEventListener("click", () => setFilter("working"));
    $("metricCompletedCard").addEventListener("click", () => setFilter("completed"));
    $("studentSelect").addEventListener("change", (event) => {
      state.studentId = event.target.value;
      state.token = null;
      state.threads = [];
      state.selectedThread = null;
      state.selectedAgentId = "coordinator";
      localStorage.setItem("tender.student", state.studentId);
      loadData();
    });
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) loadData({ silent: true });
    });
  }

  async function boot() {
    bindEvents();
    await loadStudents();
    await loadData();
    state.pollTimer = window.setInterval(() => {
      if (!document.hidden) loadData({ silent: true });
    }, 8000);
  }

  boot();
})();

(function () {
  "use strict";
  const API = "";
  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  const studentId = params.get("student") || localStorage.getItem("tender.student") || "S01";
  const state = { token: null, busy: false, lastCard: null, lane: 0, timers: [] };
  function toast(message, error) { const el = $("toast"); el.textContent = message; el.className = "toast show" + (error ? " error" : ""); clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => { el.className = "toast"; }, 3000); }
  async function ensureSession() {
    if (state.token) return state.token;
    const response = await fetch(API + "/auth/demo-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_id: studentId, role: "learner", learner_id: studentId }) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "无法连接");
    state.token = data.token;
    return state.token;
  }
  async function api(path, options) {
    options = options || {};
    const token = state.token || await ensureSession();
    const response = await fetch(API + path, Object.assign({}, options, { headers: Object.assign({}, options.headers || {}, { Authorization: "Bearer " + token, "X-Tender-Actor": studentId, "X-Tender-Role": "learner", "X-Tender-Learner": studentId }) }));
    const raw = await response.text();
    let data = null;
    if (raw) { try { data = JSON.parse(raw); } catch (_) { data = null; } }
    if (!response.ok) throw new Error((data && (data.detail || data.message)) || ("请求失败：" + response.status));
    return data || {};
  }
  function setConnection(text, error) { $("connectionText").textContent = text; const dot = document.querySelector(".ambient-status i"); if (dot) dot.style.background = error ? "var(--danger)" : "var(--green)"; }
  function clearLane(lane) { lane.innerHTML = ""; }
  function renderAgents(room) {
    const host = $("agentOrbits");
    if (!Array.isArray(room) || !room.length) { host.innerHTML = "<span>Agent 待命</span>"; return; }
    host.innerHTML = room.slice(0, 8).map((agent) => '<span class="agent-dot" title="' + String(agent.name || "").replace(/"/g, "&quot;") + '">' + String(agent.mark || agent.name || "A").slice(0, 1) + "</span>").join("");
  }
  function makeCard(message, card, laneIndex) {
    const el = document.createElement("article");
    el.className = "danmaku-card";
    const name = message.name || card.agent_name || "Tender";
    const mark = message.mark || card.agent_mark || "T";
    const text = message.text || card.text || "";
    const action = card.action || "先做一个小动作";
    el.innerHTML = '<div class="danmaku-meta"><span>' + mark + " · " + name + '</span><span>此刻</span></div><div class="danmaku-text"></div><div class="danmaku-action"><span class="action-copy"></span><span class="danmaku-feedback"><button data-feedback="useful">有用</button><button data-feedback="wrong">不是这样</button><button data-feedback="silence">静默</button></span></div>';
    el.querySelector(".danmaku-text").textContent = text;
    el.querySelector(".action-copy").textContent = action;
    el.querySelectorAll("[data-feedback]").forEach((button) => button.onclick = () => sendFeedback(button.dataset.feedback));
    const lane = laneIndex === 0 ? $("lane1") : $("lane2");
    clearLane(lane);
    lane.appendChild(el);
    setTimeout(() => { if (el.parentElement === lane) clearLane(lane); }, 21000);
  }
  function renderPlanCard(card) {
    state.lastCard = card;
    const messages = Array.isArray(card.ensemble_messages) && card.ensemble_messages.length ? card.ensemble_messages : [{ name: card.agent_name, mark: card.agent_mark, text: card.text }];
    makeCard(messages[0], card, 0);
    if (messages[1]) makeCard(messages[1], card, 1);
    $("queueNote").textContent = messages.length > 2 ? (messages.length - 2) + " 条排队" : "";
  }
  async function requestCard(force) {
    if (state.busy) return;
    state.busy = true; setConnection("正在判断是否需要出现");
    const scenario = $("scenarioSelect").value;
    try {
      const result = await api("/ambient/plan/" + encodeURIComponent(studentId), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ signals: { scenario: scenario, explicit_need: true, idle_seconds: 0, focus_minutes: 0, visibility_switches: 0, hesitation: 0, repeated_errors: 0 }, force: !!force }) });
      if (result.card) { renderPlanCard(result.card); setConnection("弹幕辅助运行中"); }
      else { setConnection(result.status === "silenced" ? "当前静默中" : "正在安静观察"); toast("当前没有需要打扰你的提示。"); }
    } catch (error) { setConnection("环境辅助不可用", true); toast(error.message, true); }
    finally { state.busy = false; }
  }
  async function sendFeedback(feedback) {
    if (!state.lastCard || state.busy) return;
    state.busy = true;
    try {
      await api("/ambient/feedback/" + encodeURIComponent(studentId), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ card_id: state.lastCard.card_id, feedback: feedback }) });
      clearLane($("lane1")); clearLane($("lane2")); state.lastCard = null;
      setConnection(feedback === "silence" ? "已静默 30 分钟" : "已记录反馈");
      toast(feedback === "silence" ? "已静默 30 分钟。" : "已记录，下次会更准确。");
    } catch (error) { toast("反馈失败：" + error.message, true); }
    finally { state.busy = false; }
  }
  async function reply() {
    const input = $("replyInput");
    const message = input.value.trim();
    if (!message || !state.lastCard || state.busy) return;
    state.busy = true; $("replyBtn").disabled = true; setConnection("Agent 正在回应");
    try {
      const result = await api("/ambient/reply/" + encodeURIComponent(studentId), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ card_id: state.lastCard.card_id, message: message, scenario: $("scenarioSelect").value }) });
      const card = result.reply_card || {};
      const messages = Array.isArray(card.ensemble_messages) && card.ensemble_messages.length ? card.ensemble_messages : [{ name: card.agent_name || "Tender", mark: card.agent_mark || "T", text: card.text || "我在。" }];
      makeCard(messages[0], card, 0);
      if (messages[1]) makeCard(messages[1], card, 1);
      input.value = ""; setConnection("弹幕辅助运行中");
    } catch (error) { toast("回复失败：" + error.message, true); setConnection("环境辅助不可用", true); }
    finally { state.busy = false; $("replyBtn").disabled = false; }
  }
  function initStates() {
    $("privacyBtn").onclick = () => { $("privacyPanel").hidden = !$("privacyPanel").hidden; };
    $("privacyCloseBtn").onclick = () => { $("privacyPanel").hidden = true; };
    $("closeAmbientBtn").onclick = () => { try { sessionStorage.setItem("tender.ambient.disabled", "1"); } catch (_) {} location.href = "/ui/single.html"; };
    $("demoBtn").onclick = () => requestCard(true);
    $("replyBtn").onclick = reply;
    $("replyInput").addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); reply(); } });
  }
  async function boot() {
    initStates();
    try {
      await ensureSession();
      const persona = await api("/ambient/persona/" + encodeURIComponent(studentId));
      renderAgents(persona.room || []);
      setConnection("弹幕辅助运行中");
      setTimeout(() => requestCard(true), 500);
    } catch (error) { setConnection("连接失败", true); toast(error.message, true); }
  }
  boot();
})();

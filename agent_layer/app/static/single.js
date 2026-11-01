(function () {
  "use strict";
  const API = "";
  const $ = (id) => document.getElementById(id);
  const studentId = new URLSearchParams(location.search).get("student") || localStorage.getItem("tender.student") || "S01";
  const account = (() => { try { return JSON.parse(localStorage.getItem("tender.account") || "null"); } catch (_) { return null; } })();
  const displayName = localStorage.getItem("tender.displayName") || (account && account.displayName) || studentId;
  const state = { token: null, busy: false };
  function toast(message, error) { const el = $("toast"); el.textContent = message; el.className = "toast show" + (error ? " error" : ""); clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => { el.className = "toast"; }, 3200); }
  async function ensureSession() {
    if (state.token) return state.token;
    const response = await fetch(API + "/auth/demo-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_id: studentId, role: "learner", learner_id: studentId }) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "无法连接");
    state.token = data.token; $("connectionText").textContent = "已连接";
    return state.token;
  }
  async function api(path, options) {
    options = options || {};
    const token = await ensureSession();
    const response = await fetch(API + path, Object.assign({}, options, { headers: Object.assign({}, options.headers || {}, { Authorization: "Bearer " + token, "X-Tender-Actor": studentId, "X-Tender-Role": "learner", "X-Tender-Learner": studentId }) }));
    const raw = await response.text();
    let data = null;
    if (raw) { try { data = JSON.parse(raw); } catch (_) { data = null; } }
    if (!response.ok) throw new Error((data && (data.detail || data.message)) || ("请求失败：" + response.status));
    return data || {};
  }
  function pct(value) { return value == null ? "—" : Math.round(Number(value) * 100) + "%"; }
  function rows(items) { return items.map(([label,value]) => '<div class="detail-item"><span>' + label + '</span><b>' + String(value == null ? "—" : value) + '</b></div>').join(""); }
  function eventLabel(event) { const map = { head_teacher_note:"学习观察", subjective_experience_summary:"体验摘要", subjective_experience_node:"体验节点", ambient_card_shown:"环境辅助提示", ambient_dialogue_reply:"辅助对话", agent_run_completed:"Agent 运行完成", agent_approval_decided:"审批结果", assessment_result:"学习结果" }; return map[event.event_type] || event.event_type || "事件"; }
  function eventSummary(event) { const s = event.summary; if (s && typeof s === "object") { if (s.memory_type) return s.memory_type.label || "体验节点"; if (s.primary_region) return s.primary_region.name || "体验摘要"; if (s.text) return String(s.text); if (s.summary) return String(s.summary); const text = JSON.stringify(s); return text === "{}" ? eventLabel(event) : text.slice(0, 120); } return s ? String(s) : eventLabel(event); }
  async function load() {
    $("actorLabel").textContent = displayName + " · " + studentId;
    try {
      const [home, context] = await Promise.all([api("/learner/home/" + encodeURIComponent(studentId)), api("/tender/context/" + encodeURIComponent(studentId))]);
      const passport = home.passport || {}, skills = passport.skills || {}, meta = passport.metacognition || {}, mental = home.mentalization || {};
      const digest = context.digest || {}, pre = context.preassessment || {}, world = pre.world_interface || {}, entry = world.world_entry || {};
      const storedEntry = (() => { try { return JSON.parse(localStorage.getItem("tender.worldEntry." + studentId) || "null"); } catch (_) { return null; } })();
      $("stateHypothesis").textContent = mental.summary || "证据不足，先继续记录真实学习过程。";
      $("stateConfidence").textContent = mental.confidence == null ? "置信度：待积累" : "置信度 " + pct(mental.confidence);
      $("worldEntry").textContent = (storedEntry && storedEntry.label) || entry.label || "尚未形成";
      $("worldEntryStep").textContent = (storedEntry && storedEntry.first_step) || entry.first_step || "完成一次基础测评后生成";
      $("mastery").textContent = pct(skills.mastery);
      $("eventCount").textContent = passport.learning_events || context.event_count || 0;
      $("hesitation").textContent = pct(meta.hesitation);
      const attention = pre.attention_profile || {};
      $("attentionView").innerHTML = rows([
        ["容易吸引注意", (attention.capture_hypotheses || [])[0] || "暂无足够证据"],
        ["有助于维持", (attention.sustain_hypotheses || [])[0] || "暂无足够证据"],
        ["注意泄漏", (attention.leakage_hypotheses || [])[0] || "暂无足够证据"],
        ["恢复方式", (attention.recovery_preferences || [])[0] || "暂无足够证据"]
      ]);
      const knowledge = context.knowledge || {}, matches = knowledge.matches || [];
      $("knowledgeView").innerHTML = rows([
        ["学科", knowledge.subject_name || digest.knowledge_subject || "未确定"],
        ["当前节点", (matches[0] || {}).name || digest.knowledge_node || "尚未匹配"],
        ["掌握估计", pct((matches[0] || {}).mastery)],
        ["知识画像", knowledge.available ? "已关联" : "证据不足"]
      ]);
      const events = (context.recent_events || []).slice(-10).reverse();
      $("recentView").innerHTML = events.map((event) => '<div class="event-row"><time>' + new Date(event.timestamp).toLocaleString("zh-CN", {month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}) + '</time><span><b>' + eventLabel(event) + '</b> · ' + eventSummary(event) + '</span></div>').join("") || '<p>还没有保存可展示的事件。</p>';
      $("technicalView").textContent = "上下文版本：" + (context.context_version || "—") + " · 事件总数：" + (context.event_count || 0) + " · 状态置信度：" + pct(mental.confidence) + " · 大五基线：" + (pre.available ? "已建立" : "未建立");
    } catch (error) { $("connectionText").textContent = "连接失败"; $("stateHypothesis").textContent = "暂时无法读取模型"; toast(error.message, true); }
  }
  async function exportData() {
    if (state.busy) return;
    state.busy = true; $("exportBtn").disabled = true;
    try {
      const token = await ensureSession();
      const response = await fetch(API + "/learner/export/" + encodeURIComponent(studentId), { headers: { Authorization: "Bearer " + token } });
      if (!response.ok) throw new Error("导出失败");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a"); link.href = url; link.download = "tender-" + studentId + ".json"; link.click(); URL.revokeObjectURL(url);
      toast("数据已导出。");
    } catch (error) { toast(error.message, true); }
    finally { state.busy = false; $("exportBtn").disabled = false; }
  }
  $("exportBtn").onclick = exportData;
  $("logoutBtn").onclick = () => { ["tender.account", "tender.student", "tender.displayName"].forEach((key) => localStorage.removeItem(key)); location.href = "/ui/login.html"; };
  load();
})();

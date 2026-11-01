(function () {
  "use strict";
  const API = "";
  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  let next = params.get("next") || "/ui/single.html";
  if (next === "/ui" || next === "/ui/") next = "/ui/single.html";
  const state = { students: [], account: null, busy: false };

  function esc(value) { return String(value == null ? "" : value).replace(/[&<>"']/g, (x) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[x])); }
  function setStatus(message) { $("loginStatus").textContent = message || ""; }
  function accountStorageKey(id) { return "tender.onboarding." + id; }
  function generateId() { return "U-" + Date.now().toString(36).toUpperCase(); }

  async function loadStudents() {
    try {
      const response = await fetch(API + "/students");
      if (!response.ok) throw new Error("无法读取学习者");
      state.students = await response.json();
    } catch (_) { state.students = []; }
    const select = $("learnerSelect");
    const saved = JSON.parse(localStorage.getItem("tender.account") || "null");
    select.innerHTML = '<option value="__new__">创建新学习者</option>' + state.students.map((item) => '<option value="' + esc(item.student_id) + '">' + esc(item.student_id + " · " + item.name) + "</option>").join("");
    select.disabled = false;
    if (saved && saved.studentId && state.students.some((item) => item.student_id === saved.studentId)) {
      select.value = saved.studentId;
    } else if (state.students.length) {
      select.value = state.students[0].student_id;
    }
    updateNewNameVisibility();
  }
  function updateNewNameVisibility() {
    const isNew = $("learnerSelect").value === "__new__";
    $("newNameField").hidden = !isNew;
    if (isNew) $("newName").focus();
  }
  async function login(event) {
    event.preventDefault();
    if (state.busy) return;
    if (!$("loginConsent").checked) { setStatus("请先确认 Tender 的用途。"); return; }
    const selected = $("learnerSelect").value;
    const isNew = selected === "__new__";
    const displayName = isNew ? $("newName").value.trim() : ((state.students.find((item) => item.student_id === selected) || {}).name || selected);
    if (isNew && displayName.length < 1) { setStatus("先填写怎么称呼你。"); $("newName").focus(); return; }
    const studentId = isNew ? generateId() : selected;
    if (!studentId) { setStatus("请选择学习者。"); return; }
    state.busy = true; $("loginBtn").disabled = true; $("loginBtn").textContent = "正在进入…"; setStatus("");
    try {
      const response = await fetch(API + "/auth/demo-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_id: studentId, role: "learner", learner_id: studentId }) });
      const session = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(session.detail || "登录失败");
      const account = { studentId: studentId, displayName: displayName, stage: $("stageSelect").value, createdAt: new Date().toISOString() };
      localStorage.setItem("tender.account", JSON.stringify(account));
      localStorage.setItem("tender.student", studentId);
      localStorage.setItem("tender.displayName", displayName);
      localStorage.setItem("tender.onboarding.next", next);
      const profileResponse = await fetch(API + "/preassessment/profile/" + encodeURIComponent(studentId), { headers: { Authorization: "Bearer " + session.token } });
      if (profileResponse.ok) {
        localStorage.setItem(accountStorageKey(studentId), "complete");
        location.replace(next || ("/ui/single.html?student=" + encodeURIComponent(studentId)));
      } else {
        localStorage.removeItem(accountStorageKey(studentId));
        location.replace("/ui/preassessment.html?student=" + encodeURIComponent(studentId) + "&onboarding=1");
      }
    } catch (error) {
      setStatus(error.message || "登录失败，请稍后再试。");
      $("loginBtn").disabled = false; $("loginBtn").textContent = "继续";
    } finally { state.busy = false; }
  }
  function bind() {
    $("learnerSelect").addEventListener("change", updateNewNameVisibility);
    $("loginForm").addEventListener("submit", login);
  }
  bind();
  loadStudents();
})();

(function () {
  "use strict";
  const API = "";
  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  let next = params.get("next") || "/ui/single.html";
  if (next === "/ui" || next === "/ui/") next = "/ui/single.html";
  const state = { accounts: [], busy: false };
  function esc(value) { return String(value == null ? "" : value).replace(/[&<>"']/g, (x) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[x])); }
  function setStatus(message) { $("loginStatus").textContent = message || ""; }
  function readAccounts() { try { const rows = JSON.parse(localStorage.getItem("tender.accounts") || "[]"); return Array.isArray(rows) ? rows.filter((item) => item && item.studentId) : []; } catch (_) { return []; } }
  function saveAccount(account) { const rows = readAccounts().filter((item) => item.studentId !== account.studentId); rows.unshift(account); localStorage.setItem("tender.accounts", JSON.stringify(rows.slice(0, 12))); }
  function generateId() { return "U-" + Date.now().toString(36).toUpperCase() + Math.random().toString(36).slice(2, 6).toUpperCase(); }
  function renderAccounts() {
    state.accounts = readAccounts();
    const select = $("learnerSelect");
    select.innerHTML = '<option value="__new__">创建新的学习者</option>' + state.accounts.map((item) => '<option value="' + esc(item.studentId) + '">' + esc((item.displayName || item.studentId) + " · " + item.studentId) + "</option>").join("");
    select.disabled = false;
    select.value = "__new__";
    updateNewNameVisibility();
  }
  function updateNewNameVisibility() { const isNew = $("learnerSelect").value === "__new__"; $("newNameField").hidden = !isNew; if (isNew) $("newName").focus(); }
  async function login(event) {
    event.preventDefault();
    if (state.busy) return;
    if (!$("loginConsent").checked) { setStatus("请先确认 Tender 的用途。"); return; }
    const selected = $("learnerSelect").value;
    const isNew = selected === "__new__";
    const previous = state.accounts.find((item) => item.studentId === selected) || {};
    const displayName = isNew ? $("newName").value.trim() : (previous.displayName || selected);
    if (isNew && displayName.length < 1) { setStatus("先填写怎么称呼你。"); $("newName").focus(); return; }
    const studentId = isNew ? generateId() : selected;
    state.busy = true; $("loginBtn").disabled = true; $("loginBtn").textContent = "正在进入…"; setStatus("");
    try {
      const response = await fetch(API + "/auth/demo-session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ actor_id: studentId, role: "learner", learner_id: studentId }) });
      const session = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(session.detail || "登录失败");
      const account = { studentId, displayName, createdAt: previous.createdAt || new Date().toISOString(), lastUsedAt: new Date().toISOString() };
      saveAccount(account);
      localStorage.setItem("tender.account", JSON.stringify(account));
      localStorage.setItem("tender.student", studentId);
      localStorage.setItem("tender.displayName", displayName);
      localStorage.setItem("tender.onboarding.next", next);
      const headers = { Authorization: "Bearer " + session.token };
      const [profileResponse, worldResponse] = await Promise.all([
        fetch(API + "/preassessment/profile/" + encodeURIComponent(studentId), { headers }),
        fetch(API + "/learner/world-setup/" + encodeURIComponent(studentId), { headers })
      ]);
      if (profileResponse.ok) localStorage.setItem("tender.onboarding." + studentId, "complete"); else localStorage.removeItem("tender.onboarding." + studentId);
      if (worldResponse.ok) {
        const world = await worldResponse.json();
        localStorage.setItem("tender.worldSetup." + studentId, "complete");
        if (world.world_context) localStorage.setItem("tender.worldContext." + studentId, JSON.stringify(world.world_context));
      } else {
        localStorage.removeItem("tender.worldSetup." + studentId);
      }
      if (!worldResponse.ok) {
        location.replace("/ui/world-setup.html?student=" + encodeURIComponent(studentId) + "&onboarding=1");
      } else if (!profileResponse.ok) {
        location.replace("/ui/preassessment.html?student=" + encodeURIComponent(studentId) + "&onboarding=1");
      } else {
        location.replace(next || ("/ui/single.html?student=" + encodeURIComponent(studentId)));
      }
    } catch (error) {
      setStatus(error.message || "登录失败，请稍后再试。");
      $("loginBtn").disabled = false; $("loginBtn").textContent = "继续";
    } finally { state.busy = false; }
  }

  async function shutdownLocal() {
    if (!confirm("关闭 Tender 后，本地后台服务和桌面弹幕都会停止。重新使用需要再次启动服务。继续吗？")) return;
    try {
      const session = await fetch(API + "/auth/demo-session", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({actor_id: "local-ui", role: "learner", learner_id: "local-ui"})});
      const data = await session.json().catch(() => ({}));
      if (!session.ok) throw new Error(data.detail || "无法建立本地会话");
      await fetch(API + "/system/shutdown", {method: "POST", headers: {Authorization: "Bearer " + data.token}});
      document.body.innerHTML = '<main style="min-height:100vh;display:grid;place-items:center;background:#edf3ef;color:#17211c;text-align:center;font-family:Microsoft YaHei,sans-serif"><div style="max-width:520px;padding:38px;border:1px solid #d4ddd7;border-radius:24px;background:#fffefa"><h1>Tender 已关闭</h1><p>后台服务和桌面弹幕已经停止。这个网页可以关闭；下次使用时请重新启动 Tender。</p></div></main>';
    } catch (error) { alert("关闭失败：" + (error.message || "服务可能已经停止")); }
  }


  function clearDeviceAccounts() {
    if (!confirm("只清除这台设备上的登录记录与本地标记，不删除后台学习数据。继续吗？")) return;
    Object.keys(localStorage).filter((key) => key.startsWith("tender.")).forEach((key) => localStorage.removeItem(key));
    location.reload();
  }

  $("clearAccountsBtn").addEventListener("click", clearDeviceAccounts);
  $("shutdownBtn").addEventListener("click", shutdownLocal);
  $("learnerSelect").addEventListener("change", updateNewNameVisibility);
  $("loginForm").addEventListener("submit", login);
  renderAccounts();
})();

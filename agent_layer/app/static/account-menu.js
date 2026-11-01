(function () {
  "use strict";
  const API = "";
  const account = (() => { try { return JSON.parse(localStorage.getItem("tender.account") || "null"); } catch (_) { return null; } })();
  const studentId = (account && account.studentId) || localStorage.getItem("tender.student") || "";
  if (!studentId) return;
  const displayName = (account && account.displayName) || localStorage.getItem("tender.displayName") || studentId;
  function esc(value) { return String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
  const host = document.createElement("div");
  host.className = "tender-account";
  host.innerHTML = '<button type="button" aria-haspopup="menu" aria-expanded="false"><span class="ta-avatar">' + esc(displayName.slice(0, 1).toUpperCase()) + '</span><span class="ta-name">' + esc(displayName) + '</span><span class="ta-caret">▼</span></button><div class="tender-account-menu" role="menu" hidden><header><b>' + esc(displayName) + '</b><span>' + esc(studentId) + ' · 当前学习者</span></header><button type="button" data-action="logout" role="menuitem">退出账号</button><button type="button" data-action="delete" class="danger" role="menuitem">删除此学习者数据</button><button type="button" data-action="shutdown" class="shutdown" role="menuitem">关闭 Tender 服务</button></div>';
  function mount() { const target = document.querySelector(".topbar") || document.querySelector("header.site-header") || document.querySelector("header"); if (target) { target.appendChild(host); if (getComputedStyle(target).position === "static") target.style.position = "relative"; } else { host.classList.add("floating"); document.body.appendChild(host); } }
  async function sessionToken() { const response = await fetch(API + "/auth/demo-session", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({actor_id: studentId, role: "learner", learner_id: studentId})}); const data = await response.json().catch(() => ({})); if (!response.ok) throw new Error(data.detail || "无法建立身份会话"); return data.token; }
  async function logout() { try { const token = await sessionToken(); await fetch(API + "/auth/logout", {method: "POST", headers: {Authorization: "Bearer " + token}}); } catch (_) {} ["tender.account", "tender.student", "tender.displayName", "tender.onboarding.next"].forEach((key) => localStorage.removeItem(key)); location.replace("/ui/login.html"); }
  async function deleteData() {
    if (!confirm("这会永久删除 " + displayName + " 的学习事件、画像和世界坐标。账号本身可以重新创建，但数据不能恢复。继续吗？")) return;
    const confirmation = prompt("请输入学习者编号 " + studentId + " 以确认永久删除：");
    if (confirmation !== studentId) { alert("编号不一致，没有删除。"); return; }
    try {
      const token = await sessionToken();
      const response = await fetch(API + "/learner/data/" + encodeURIComponent(studentId) + "/delete", {method: "POST", headers: {"Content-Type": "application/json", Authorization: "Bearer " + token}, body: JSON.stringify({confirmation, acknowledge_irreversible: true})});
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error((data.detail && (data.detail.error || data.detail)) || "删除失败");
      ["tender.onboarding." + studentId, "tender.worldEntry." + studentId, "tender.worldSetup." + studentId, "tender.preassessment.draft"].forEach((key) => localStorage.removeItem(key));
      const accounts = (() => { try { return JSON.parse(localStorage.getItem("tender.accounts") || "[]"); } catch (_) { return []; } })();
      localStorage.setItem("tender.accounts", JSON.stringify(accounts.filter((item) => item.studentId !== studentId)));
      ["tender.account", "tender.student", "tender.displayName"].forEach((key) => localStorage.removeItem(key));
      alert("该学习者的数据已删除。"); location.replace("/ui/login.html");
    } catch (error) { alert(error.message || "删除失败"); }
  }
  async function shutdown() {
    if (!confirm("关闭 Tender 后，网页、后台服务和桌面弹幕都会停止。重新使用需要再次启动服务。继续吗？")) return;
    try { const token = await sessionToken(); await fetch(API + "/system/shutdown", {method: "POST", headers: {Authorization: "Bearer " + token}}); const screen = document.createElement("div"); screen.className = "tender-closed-screen"; screen.innerHTML = '<div><h1>Tender 已关闭</h1><p>后台服务和桌面弹幕已经停止。这个网页可以关闭；下次使用时请重新启动 Tender。</p></div>'; document.body.appendChild(screen); } catch (error) { alert("关闭失败：" + (error.message || "服务可能已经停止")); }
  }
  function toggle(force) { const menu = host.querySelector(".tender-account-menu"); const button = host.querySelector(":scope > button"); const open = force == null ? menu.hidden : force; menu.hidden = !open; button.setAttribute("aria-expanded", open ? "true" : "false"); }
  host.querySelector(":scope > button").addEventListener("click", (event) => { event.stopPropagation(); toggle(); });
  host.querySelector('[data-action="logout"]').addEventListener("click", logout);
  host.querySelector('[data-action="delete"]').addEventListener("click", deleteData);
  host.querySelector('[data-action="shutdown"]').addEventListener("click", shutdown);
  document.addEventListener("click", () => toggle(false));
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") toggle(false); });
  mount();
})();

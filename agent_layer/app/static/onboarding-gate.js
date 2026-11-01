(function () {
  const params = new URLSearchParams(location.search);
  if (params.get("preview") === "1") return;
  let account = null;
  try { account = JSON.parse(localStorage.getItem("tender.account") || "null"); } catch (_) { account = null; }
  const studentId = params.get("student") || (account && account.studentId) || localStorage.getItem("tender.student") || "";
  if (!account || !account.studentId || !studentId) {
    location.replace("/ui/login.html?next=" + encodeURIComponent(location.pathname + location.search));
    return;
  }
  localStorage.setItem("tender.student", studentId);
  if (localStorage.getItem("tender.onboarding." + studentId) !== "complete") {
    location.replace("/ui/preassessment.html?student=" + encodeURIComponent(studentId) + "&onboarding=1");
  }
})();

(() => {
  "use strict";
  const course = window.TENDER_COURSE;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const STORAGE_LANG = "tender-academy-language-v1";
  const STORAGE_PROGRESS = "tender-academy-progress-v1";
  const UI = {
    zh: {
      brandSub: "心智化学习系统教学", progress: "学习进度", curriculum: "课程目录", courseTitle: "45 分钟理解 Tender",
      courseIntro: "从预测加工、语言证据和心智化，到知识森林与 Agent 协作。", search: "搜索课程",
      whitepaper: "阅读白皮书 V1.5", heroTitle: "理解一个人的心智，而不是只给他一个分数。",
      heroTitleEn: "Understand a mind, not just a score.", heroBody: "这门课解释 Tender 如何把语言、行为、作答和真实结果组织成可更正的状态假设，并说明系统明确不做什么。",
      start: "开始课程", resume: "继续上次学习", statLessons: "双语模块", statMinutes: "分钟", statNodes: "知识节点", statTests: "自动测试",
      forWhoEyebrow: "适合谁", forWhoTitle: "适合谁", outcomeEyebrow: "学习成果", outcomeTitle: "学完能做什么",
      boundaryEyebrow: "边界", boundaryTitle: "最重要的边界", boundaryBody: "Tender 不是诊断、不是读心，也不把语言模型输出当事实。高风险信号进入人工保护流程。",
      modulesEyebrow: "课程模块", modulesTitle: "课程路径", modulesIntro: "按顺序学习，也可以直接从左侧进入任一模块。",
      back: "返回课程首页", prev: "上一课", next: "下一课", markComplete: "标记为已完成", completed: "已完成", objectives: "本课目标",
      footer: "Tender Academy 是教学材料，不是临床诊断或教育效果承诺。", correct: "回答正确", wrong: "再想一次", minute: "分钟",
      lessonCompleted: "本课已完成", lessonReopened: "已恢复为未完成", noLesson: "没有找到课程"
    },
    en: {
      brandSub: "Mentalization learning system course", progress: "Progress", curriculum: "CURRICULUM", courseTitle: "Understand Tender in 45 minutes",
      courseIntro: "From predictive processing, language evidence and mentalization to the knowledge forest and Agent collaboration.", search: "Search lessons",
      whitepaper: "Read Whitepaper V1.5", heroTitle: "Understand a mind, not just a score.",
      heroTitleEn: "理解一个人的心智，而不是只给他一个分数。", heroBody: "This course explains how Tender turns language, behavior, answers and real outcomes into revisable state hypotheses—and what the system explicitly does not do.",
      start: "Start course", resume: "Resume learning", statLessons: "Bilingual modules", statMinutes: "Minutes", statNodes: "Knowledge nodes", statTests: "Automated tests",
      forWhoEyebrow: "FOR WHOM", forWhoTitle: "Who this is for", outcomeEyebrow: "OUTCOMES", outcomeTitle: "What you will learn",
      boundaryEyebrow: "BOUNDARY", boundaryTitle: "The most important boundary", boundaryBody: "Tender is not diagnosis or mind reading, and language-model output is not fact. High-risk signals enter a human protection flow.",
      modulesEyebrow: "MODULES", modulesTitle: "Course path", modulesIntro: "Study in order, or jump directly to any module from the sidebar.",
      back: "Back to course home", prev: "Previous", next: "Next", markComplete: "Mark complete", completed: "Completed", objectives: "Objectives",
      footer: "Tender Academy is teaching material, not clinical diagnosis or an educational-effect claim.", correct: "Correct", wrong: "Try again", minute: "min",
      lessonCompleted: "Lesson completed", lessonReopened: "Marked incomplete", noLesson: "No lesson found", format: "Format"
    }
  };
  const state = {
    lang: localStorage.getItem(STORAGE_LANG) || (((navigator.language || "zh").toLowerCase().startsWith("zh")) ? "zh" : "en"),
    lessonIndex: null,
    completed: new Set(JSON.parse(localStorage.getItem(STORAGE_PROGRESS) || "[]"))
  };
  // Correct precedence for first-run language selection.
  if (!localStorage.getItem(STORAGE_LANG)) {
    state.lang = (navigator.language || "zh").toLowerCase().startsWith("zh") ? "zh" : "en";
  }
  const t = (value) => typeof value === "string" ? value : value?.[state.lang] || value?.zh || value?.en || "";
  const ui = (key) => UI[state.lang][key] || key;
  const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch]));

  function saveProgress() {
    localStorage.setItem(STORAGE_PROGRESS, JSON.stringify([...state.completed]));
  }

  function applyStaticLanguage() {
    document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
    $("#langToggle").textContent = state.lang === "zh" ? "EN" : "中文";
    $("#langToggle").setAttribute("aria-label", state.lang === "zh" ? "Switch to English" : "切换到中文");
    $$('[data-i18n]').forEach((node) => { node.textContent = ui(node.dataset.i18n); });
    $$('[data-i18n-placeholder]').forEach((node) => { node.placeholder = ui(node.dataset.i18nPlaceholder); });
    document.title = state.lang === "zh" ? "Tender Academy · 心智化学习系统教学" : "Tender Academy · Mentalization Learning System";
  }

  function totalCompleted() {
    return course.lessons.filter((lesson) => state.completed.has(lesson.id)).length;
  }

  function updateProgress() {
    const count = totalCompleted();
    $("#globalProgress").value = count;
    $("#globalProgress").textContent = `${count}/${course.lessons.length}`;
    $("#progressText").textContent = `${count}/${course.lessons.length}`;
    $("#resumeBtn").hidden = count === 0;
    $$(".lesson-link").forEach((button) => {
      button.classList.toggle("done", state.completed.has(button.dataset.lesson));
    });
    if (state.lessonIndex !== null) renderCompleteButton();
  }

  function renderHomeLists() {
    $("#audienceList").innerHTML = course.audience.map((item) => `<li>${escapeHTML(t(item))}</li>`).join("");
    $("#outcomeList").innerHTML = course.outcomes.map((item) => `<li>${escapeHTML(t(item))}</li>`).join("");
  }

  function renderNav(filter = "") {
    const query = filter.trim().toLowerCase();
    const rows = course.lessons.map((lesson, index) => ({ lesson, index })).filter(({ lesson }) => {
      if (!query) return true;
      return [t(lesson.title), t(lesson.summary), lesson.id].join(" ").toLowerCase().includes(query);
    });
    $("#lessonNav").innerHTML = rows.map(({ lesson, index }) => `
      <button class="lesson-link ${state.lessonIndex === index ? "active" : ""} ${state.completed.has(lesson.id) ? "done" : ""}" data-lesson="${escapeHTML(lesson.id)}" type="button">
        <span class="nav-index">${state.completed.has(lesson.id) ? "✓" : String(index + 1).padStart(2, "0")}</span>
        <span class="nav-copy"><strong>${escapeHTML(t(lesson.title))}</strong><small>${escapeHTML(t(lesson.level))}</small></span>
        <span class="nav-time">${escapeHTML(lesson.time)}</span>
      </button>`).join("") || `<p class="muted">${escapeHTML(ui("noLesson"))}</p>`;
    $$(".lesson-link", $("#lessonNav")).forEach((button) => button.addEventListener("click", () => openLessonById(button.dataset.lesson)));
  }

  function renderCards() {
    $("#moduleCards").innerHTML = course.lessons.map((lesson, index) => `
      <button class="module-card" type="button" data-lesson="${escapeHTML(lesson.id)}">
        <span class="num">${String(index + 1).padStart(2, "0")} · ${escapeHTML(t(lesson.level))}</span>
        <h3>${escapeHTML(t(lesson.title))}</h3>
        <p>${escapeHTML(t(lesson.summary))}</p>
        <footer><span>${escapeHTML(lesson.time)}</span><span>${state.completed.has(lesson.id) ? "✓ " + escapeHTML(ui("completed")) : ""}</span></footer>
      </button>`).join("");
    $$(".module-card").forEach((button) => button.addEventListener("click", () => openLessonById(button.dataset.lesson)));
  }

  function renderBlock(block) {
    const title = block.title ? `<h2>${escapeHTML(t(block.title))}</h2>` : "";
    if (block.type === "concept") return `<section class="content-block">${title}<p>${escapeHTML(t(block.body))}</p></section>`;
    if (block.type === "list") return `<section class="content-block">${title}<ul>${block.items.map((item) => `<li>${escapeHTML(t(item))}</li>`).join("")}</ul></section>`;
    if (block.type === "table") return `<section class="content-block">${title}<div style="overflow:auto"><table class="data-table"><thead><tr>${block.headers.map((h) => `<th>${escapeHTML(t(h))}</th>`).join("")}</tr></thead><tbody>${block.rows.map((row) => `<tr>${row.map((cell) => `<td>${escapeHTML(t(cell))}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>`;
    if (block.type === "boundary") return `<aside class="boundary content-block"><strong>${state.lang === "zh" ? "边界：" : "Boundary: "}</strong>${escapeHTML(t(block.body))}</aside>`;
    if (block.type === "action") return `<aside class="action-box content-block"><strong>${escapeHTML(t(block.title))}</strong><span>${escapeHTML(t(block.body))}</span></aside>`;
    if (block.type === "quiz") {
      return `<section class="quiz content-block"><h3>${escapeHTML(t(block.question))}</h3><div class="quiz-options">${block.options.map((option, index) => `<button class="quiz-option" data-answer="${index}" type="button">${escapeHTML(t(option))}</button>`).join("")}</div><div class="quiz-feedback" aria-live="polite"></div></section>`;
    }
    return "";
  }

  function renderCompleteButton() {
    const lesson = course.lessons[state.lessonIndex];
    const done = state.completed.has(lesson.id);
    $("#completeBtn").textContent = done ? (state.lang === "zh" ? "✓ 已完成" : "✓ Completed") : ui("markComplete");
    $("#completeBtn").classList.toggle("primary", !done);
    $("#completeBtn").classList.toggle("secondary", done);
  }

  function bindQuiz() {
    $$(".quiz", $("#lessonContent")).forEach((quiz) => {
      const lesson = course.lessons[state.lessonIndex];
      const block = lesson.blocks.find((item) => item.type === "quiz" && t(item.question) === $("h3", quiz)?.textContent);
      $$(".quiz-option", quiz).forEach((button) => button.addEventListener("click", () => {
        if (!block) return;
        const selected = Number(button.dataset.answer);
        $$(".quiz-option", quiz).forEach((item) => item.classList.remove("correct", "wrong"));
        button.classList.add(selected === block.answer ? "correct" : "wrong");
        const feedback = $(".quiz-feedback", quiz);
        feedback.textContent = selected === block.answer ? `${ui("correct")} — ${t(block.why)}` : `${ui("wrong")} — ${t(block.why)}`;
      }));
    });
  }

  function renderLesson() {
    const index = state.lessonIndex;
    if (index === null || !course.lessons[index]) return showHome();
    const lesson = course.lessons[index];
    $("#homeView").hidden = true;
    $("#lessonView").hidden = false;
    $("#lessonNumber").textContent = `${String(index + 1).padStart(2, "0")} / ${String(course.lessons.length).padStart(2, "0")}`;
    $("#lessonLevel").textContent = t(lesson.level);
    $("#lessonTime").textContent = lesson.time;
    $("#lessonContent").innerHTML = `
      <span class="eyebrow">${escapeHTML(ui("curriculum"))} · ${String(index + 1).padStart(2, "0")}</span>
      <h1>${escapeHTML(t(lesson.title))}<em>${escapeHTML(state.lang === "zh" ? lesson.title.en : lesson.title.zh)}</em></h1>
      <p class="lesson-summary">${escapeHTML(t(lesson.summary))}</p>
      <div class="objective-box"><span>${escapeHTML(ui("objectives"))}</span><ul>${lesson.objectives.map((item) => `<li>${escapeHTML(t(item))}</li>`).join("")}</ul></div>
      ${lesson.blocks.map(renderBlock).join("")}`;
    bindQuiz();
    renderCompleteButton();
    $("#prevBtn").disabled = index === 0;
    $("#nextBtn").disabled = index === course.lessons.length - 1;
    renderNav($("#lessonSearch").value);
    updateProgress();
    $("#courseMain").scrollTop = 0;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openLessonById(id) {
    const index = course.lessons.findIndex((lesson) => lesson.id === id);
    if (index < 0) return;
    state.lessonIndex = index;
    history.replaceState(null, "", `#${encodeURIComponent(id)}`);
    renderLesson();
  }

  function showHome() {
    state.lessonIndex = null;
    $("#homeView").hidden = false;
    $("#lessonView").hidden = true;
    history.replaceState(null, "", location.pathname + location.search);
    renderNav($("#lessonSearch").value);
    renderCards();
    updateProgress();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function startCourse() {
    const firstIncomplete = course.lessons.findIndex((lesson) => !state.completed.has(lesson.id));
    openLessonById(course.lessons[firstIncomplete >= 0 ? firstIncomplete : 0].id);
  }

  function toggleComplete() {
    if (state.lessonIndex === null) return;
    const lesson = course.lessons[state.lessonIndex];
    if (state.completed.has(lesson.id)) {
      state.completed.delete(lesson.id);
      toast(ui("lessonReopened"));
    } else {
      state.completed.add(lesson.id);
      toast(ui("lessonCompleted"));
    }
    saveProgress();
    updateProgress();
    renderNav($("#lessonSearch").value);
    renderCards();
  }

  function toast(message) {
    const node = $("#toast");
    node.textContent = message;
    node.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => node.classList.remove("show"), 1800);
  }

  function setLanguage(lang) {
    state.lang = lang;
    localStorage.setItem(STORAGE_LANG, lang);
    applyStaticLanguage();
    renderHomeLists();
    renderNav($("#lessonSearch").value);
    renderCards();
    if (state.lessonIndex !== null) renderLesson();
  }

  function init() {
    applyStaticLanguage();
    renderHomeLists();
    renderNav();
    renderCards();
    updateProgress();
    $("#langToggle").addEventListener("click", () => setLanguage(state.lang === "zh" ? "en" : "zh"));
    $("#printBtn").addEventListener("click", () => window.print());
    $("#startBtn").addEventListener("click", startCourse);
    $("#resumeBtn").addEventListener("click", startCourse);
    $("#backBtn").addEventListener("click", showHome);
    $("#completeBtn").addEventListener("click", toggleComplete);
    $("#prevBtn").addEventListener("click", () => { if (state.lessonIndex > 0) openLessonById(course.lessons[state.lessonIndex - 1].id); });
    $("#nextBtn").addEventListener("click", () => { if (state.lessonIndex < course.lessons.length - 1) openLessonById(course.lessons[state.lessonIndex + 1].id); });
    $("#lessonSearch").addEventListener("input", (event) => renderNav(event.target.value));
    const hash = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (hash) openLessonById(hash);
  }

  init();
})();

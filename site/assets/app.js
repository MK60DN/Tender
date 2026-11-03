(() => {
  "use strict";
  const course = window.TENDER_COURSE;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const STORAGE_LANG = "tender-academy-language-v1";
  const STORAGE_PROGRESS = "tender-academy-progress-v1";
  const UI = {
    zh: {
      brandSub: "心智化学习系统教学", progress: "学习进度", curriculum: "课程目录", courseTitle: "108 分钟理解 Tender",
      courseIntro: "从预测加工、语言证据和心智化，到知识森林与 Agent 协作。", search: "搜索课程",
      whitepaper: "阅读白皮书 V2.2", heroTitle: "理解一个人的心智，也让他更好地进入世界和关系。",
      heroTitleEn: "Understand a mind, and help it enter the world and relationships.", heroBody: "这门课解释 Tender 如何从自我理解走向世界行动、关系协商和群体协作，并在每一步保留证据、授权和人的选择。",
      start: "开始课程", resume: "继续上次学习", statLessons: "双语模块", statMinutes: "分钟", statNodes: "知识节点", statTests: "自动测试",
      forWhoEyebrow: "适合谁", forWhoTitle: "适合谁", outcomeEyebrow: "学习成果", outcomeTitle: "学完能做什么",
      boundaryEyebrow: "边界", boundaryTitle: "最重要的边界", boundaryBody: "Tender 不是诊断、不是读心，也不把语言模型输出当事实。高风险信号进入人工保护流程。",
      modulesEyebrow: "课程模块", modulesTitle: "课程路径", modulesIntro: "按顺序学习，也可以直接从左侧进入任一模块。",
      back: "返回课程首页", prev: "上一课", next: "下一课", markComplete: "标记为已完成", completed: "已完成", objectives: "本课目标",
      footer: "Tender Academy 是教学材料，不是临床诊断或教育效果承诺。", correct: "回答正确", wrong: "再想一次", minute: "分钟",
      lessonCompleted: "本课已完成", lessonReopened: "已恢复为未完成", noLesson: "没有找到课程"
    },
    en: {
      brandSub: "Mentalization learning system course", progress: "Progress", curriculum: "CURRICULUM", courseTitle: "Understand Tender in 108 minutes",
      courseIntro: "From predictive processing, language evidence and mentalization to the knowledge forest and Agent collaboration.", search: "Search lessons",
      whitepaper: "Read Whitepaper V2.2", heroTitle: "Understand a mind, and help it enter the world and relationships.",
      heroTitleEn: "理解一个人的心智，也让他更好地进入世界和关系。", heroBody: "This course explains how Tender moves from self-understanding to action in the world, relational negotiation and group collaboration, while preserving evidence, consent and human choice.",
      start: "Start course", resume: "Resume learning", statLessons: "Bilingual modules", statMinutes: "Minutes", statNodes: "Knowledge nodes", statTests: "Automated tests",
      forWhoEyebrow: "FOR WHOM", forWhoTitle: "Who this is for", outcomeEyebrow: "OUTCOMES", outcomeTitle: "What you will learn",
      boundaryEyebrow: "BOUNDARY", boundaryTitle: "The most important boundary", boundaryBody: "Tender is not diagnosis or mind reading, and language-model output is not fact. High-risk signals enter a human protection flow.",
      modulesEyebrow: "MODULES", modulesTitle: "Course path", modulesIntro: "Study in order, or jump directly to any module from the sidebar.",
      back: "Back to course home", prev: "Previous", next: "Next", markComplete: "Mark complete", completed: "Completed", objectives: "Objectives",
      footer: "Tender Academy is teaching material, not clinical diagnosis or an educational-effect claim.", correct: "Correct", wrong: "Try again", minute: "min",
      lessonCompleted: "Lesson completed", lessonReopened: "Marked incomplete", noLesson: "No lesson found", format: "Format"
    }
  };
  Object.assign(UI.zh, { daoqlWhitepaper: "DAOQL 数据活水白皮书", waterEyebrow: "LIVING WHITEPAPER · V1.0", waterTitle: "从数据垄断到数据活水", waterBody: "Tender × DAOQL：面向发现式智能的分布式社会组织与数字经济学。支持 GitHub 协作编辑与版本追踪。", waterCta: "阅读并协作编辑 →", heroPurpose: "Tender 的长期使命：帮助人类演化。", teachingManual: "零基础教学手册", teachingManualSub: "从零开始理解环境、数据、模型、Agent、验收与最新架构",  manualsEyebrow: "DOCUMENTS", manualsTitle: "白皮书与手册", manualsIntro: "四份核心手册、动态黄金比实验与节律相位实验都在这里，可以直接下载。", whitepaperShort: "项目白皮书", whitepaperSub: "预测加工、心智化、世界树、双链路与多模态有限观测", productManual: "产品手册", productManualSub: "产品全过程、四层价值回路、界面上下文 MCP 与媒体插件", userManual: "用户手册", userManualSub: "第一次启用、桌面弹幕、纠正、隐私与安全",  archEyebrow: "WHITEPAPER ARCHITECTURE", archTitle: "白皮书架构导航", archIntro: "点击任意层，进入对应课程。世界、观测、体验与行动是不同层。", archWorld: "世界与黑盒 API", archWorldSub: "平台、设备、人物、行动与结果", archDaoql: "DAOQL 客观层", archDaoqlSub: "事件、来源、因果、授权与审计", archBloch: "有限接触面", archBlochSub: "人类实际能观测和测量的证据", archBridge: "Agent Bridge", archBridgeSub: "把客观事件翻译为可更正的主观体验", archTree: "生命树树冠", archTreeSub: "注意、记忆、语言、内省、情绪与身体", archAngels: "天使 Agent", archAngelsSub: "围绕树冠提供专业支持", archFlower: "开花", archFlowerSub: "表达、提问、教学、协作、试验、发表", archResult: "结果", archResultSub: "作品、反馈、机会、失败与新问题", archForest: "知识森林", archForestSub: "全部知识体系构成的生态", archNote: "白皮书不是一组功能列表，而是一棵从 DAOQL 客观根系、Agent Bridge 树干进入体验树冠，再通过开花与结果回到世界的生长链。" });
  Object.assign(UI.en, { daoqlWhitepaper: "DAOQL living whitepaper", waterEyebrow: "LIVING WHITEPAPER · V1.0", waterTitle: "From data monopoly to data as flowing water", waterBody: "Tender × DAOQL: distributed social organization and data economics for discoverative intelligence. GitHub-based review and version tracking.", waterCta: "Read and co-edit →", heroPurpose: "Tender's long-term purpose: help humanity evolve.", teachingManual: "Teaching manual", teachingManualSub: "Start from zero with the environment, data, models, Agents, acceptance and latest architecture",  manualsEyebrow: "DOCUMENTS", manualsTitle: "Whitepaper and manuals", manualsIntro: "Four core manuals, the dynamic golden-bias experiment and the rhythm-phase experiment are available here for direct download.", whitepaperShort: "Project whitepaper", whitepaperSub: "Predictive processing, mentalizing, world tree, dual-chain collaboration and multimodal limited observation", productManual: "Product manual", productManualSub: "Full product process, four value loops, screen-context MCP and media plugins", userManual: "User guide", userManualSub: "First-run setup, desktop ambient mode, correction, privacy and safety",  archEyebrow: "WHITEPAPER ARCHITECTURE", archTitle: "Architecture map", archIntro: "Click any layer to enter the matching lesson. World, observation, experience and action are distinct layers.", archWorld: "World and black-box APIs", archWorldSub: "Platforms, devices, people, actions and outcomes", archDaoql: "DAOQL objective layer", archDaoqlSub: "Events, provenance, causality, authorization and audit", archBloch: "Limited observation surface", archBlochSub: "Evidence people can actually observe and measure", archBridge: "Agent Bridge", archBridgeSub: "Translates objective events into correctable subjective experience", archTree: "Life-tree canopy", archTreeSub: "Attention, memory, language, reflection, emotion and body", archAngels: "Angel Agents", archAngelsSub: "Provide expertise around the canopy", archFlower: "Flowering", archFlowerSub: "Expression, questioning, teaching, collaboration, trials and publishing", archResult: "Outcomes", archResultSub: "Works, feedback, opportunity, failure and new questions", archForest: "Knowledge forest", archForestSub: "The ecosystem formed by all knowledge systems", archNote: "The whitepaper is not a feature list. It is a world tree: DAOQL roots and an Agent Bridge trunk feed the experience canopy, which returns to the world through flowering and outcomes." });
  Object.assign(UI.zh, {"evidenceEyebrow":"REPRODUCIBLE EVIDENCE","evidenceTitle":"把实验数字放在结论旁边","evidenceIntro":"四组可复核结果：机制模拟、节律检测、公开数据基准与安全识别。每组都同时展示样本量、优势、失败项和适用边界。","evGoldenTag":"MECHANISM SIMULATION","evGoldenMetric":"+6.3 pp","evGoldenTitle":"行动恢复率提升","evGoldenBody":"动态黄金比相对无调节：94.7% vs 88.4%（+6.3 个百分点，95% CI +5.4 至 +7.3）。相对固定 50:50，行动恢复基本持平，但提醒负担从 63.7 降到 33.1，约减少 48%。","evGoldenMeta":"4 臂 × 1,000 名合成学习者 × 84 天；合成机制验证，不是真人疗效。","evRhythmTag":"SYNTHETIC DETECTOR TEST","evRhythmMetric":"95.3%","evRhythmTitle":"周期检出率","evRhythmBody":"周期估计平均误差 0.45 天；稳定周期误报率 7.0%，固定“每周”规则的误报率为 100%。","evRhythmMeta":"5 种真实周期 × 80 组 + 400 组非周期序列 + 400 组相位序列。","evSafetyTag":"PUBLIC SAFETY BASELINE","evSafetyMetric":"0.9919","evSafetyTitle":"诈骗/垃圾信息 AUC","evSafetyBody":"1,393 条样本上 AP 0.9773、F1 0.9405。网络霸凌子集仅 AUC 0.75，说明高风险场景仍需规则与人工升级。","evSafetyMeta":"低层文本信号，不替代自伤、暴力、虐待与紧急事件的人工处置。","evLearningTag":"PUBLIC LEARNING DATA","evLearningMetric":"273,364","evLearningTitle":"学生作答记录","evLearningBody":"ASSISTments 2009：4,128 名学习者、81 个技能。角色特征模型 AUC 0.972、Brier 0.0544；这是行为预测，不是读心。","evLearningMeta":"与 BKT 和 logistic 基线分表报告；不用单次高分替代跨数据集验证。","evCompareTitle":"同场比较，不隐藏没赢的部分","evColExperiment":"实验","evColSample":"样本","evColResult":"主结果","evColBoundary":"边界","evFailureTag":"WHAT DID NOT WIN","evFailureTitle":"失败结果也进入发布","evFailure1":"动态黄金比的严格带内时间低于固定 50:50。","evFailure2":"知识追踪当前未超过 logistic 基线（AUC 0.6853 vs 0.7058）。","evFailure3":"网络霸凌识别 AUC 0.75，仍需人工路径。","evFailure4":"尚无真人随机对照实验证明提分或心智成熟效果。","evFailureNote":"专业系统的可信度来自可复核、可反驳和愿意披露失败，而不是只展示最好看的数字。"});
  Object.assign(UI.en, {"evidenceEyebrow":"REPRODUCIBLE EVIDENCE","evidenceTitle":"Put experimental numbers next to the conclusion","evidenceIntro":"Four reproducible result groups: mechanism simulation, rhythm detection, public-data baselines and safety recognition. Each shows sample size, benefits, failures and boundaries together.","evGoldenTag":"MECHANISM SIMULATION","evGoldenMetric":"+6.3 pp","evGoldenTitle":"Higher action recovery","evGoldenBody":"Dynamic golden bias vs no regulation: 94.7% vs 88.4% (+6.3 pp, 95% CI +5.4 to +7.3). Against fixed 50:50, recovery is similar while reminder burden falls from 63.7 to 33.1, about 48% lower.","evGoldenMeta":"4 arms × 1,000 synthetic learners × 84 days; mechanism validation, not human efficacy.","evRhythmTag":"SYNTHETIC DETECTOR TEST","evRhythmMetric":"95.3%","evRhythmTitle":"Period detection rate","evRhythmBody":"Mean period error is 0.45 days; stable-period false positives are 7.0%, versus 100% for a fixed weekly rule.","evRhythmMeta":"5 true periods × 80 series + 400 aperiodic series + 400 phase series.","evSafetyTag":"PUBLIC SAFETY BASELINE","evSafetyMetric":"0.9919","evSafetyTitle":"Scam/spam AUC","evSafetyBody":"On 1,393 samples: AP 0.9773 and F1 0.9405. Cyberbullying AUC is only 0.75, so high-risk cases still require rules and human escalation.","evSafetyMeta":"Low-level text signals do not replace human handling of self-harm, violence, abuse or emergencies.","evLearningTag":"PUBLIC LEARNING DATA","evLearningMetric":"273,364","evLearningTitle":"Student answer records","evLearningBody":"ASSISTments 2009: 4,128 learners and 81 skills. The role-feature model reaches AUC 0.972 and Brier 0.0544; this predicts behavior, not minds.","evLearningMeta":"Compared separately with BKT and logistic baselines; one high score does not replace cross-dataset validation.","evCompareTitle":"Same-table comparison without hiding losses","evColExperiment":"Experiment","evColSample":"Sample","evColResult":"Main result","evColBoundary":"Boundary","evFailureTag":"WHAT DID NOT WIN","evFailureTitle":"Failures are published too","evFailure1":"Dynamic golden bias spends less time strictly inside the band than fixed 50:50.","evFailure2":"Knowledge tracing is below the logistic baseline (AUC 0.6853 vs 0.7058).","evFailure3":"Cyberbullying detection AUC is 0.75 and still needs a human path.","evFailure4":"No randomized human trial yet establishes score gains or mentalization outcomes.","evFailureNote":"Credibility comes from reproducibility, falsifiability and disclosed failures, not from showing only the best-looking number. External comparisons require the same data, metrics and held-out set; without a shared protocol, we do not claim universal superiority."});
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
    $("#globalProgress").max = course.lessons.length;
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

  $$(".arch-node, .arch-mini").forEach((button) => button.addEventListener("click", () => openLessonById(button.dataset.lesson)));
  init();
})();

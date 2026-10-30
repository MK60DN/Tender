(() => {
  const course = window.TENDER_COURSE;
  if (!course || !Array.isArray(course.lessons)) return;

  for (const lesson of course.lessons) {
    lesson.blocks = (lesson.blocks || []).filter((block) => block.type !== "formula");
  }

  const predictive = course.lessons.find((lesson) => lesson.id === "predictive-mentalizing");
  if (predictive) {
    predictive.objectives = [
      { zh: "区分人—世界问题与人—人问题", en: "Distinguish person–world from person–person problems" },
      { zh: "理解预测、行动和反馈之间的关系", en: "Understand how prediction, action and feedback fit together" }
    ];
    const boundary = predictive.blocks.find((block) => block.type === "boundary");
    if (boundary) {
      boundary.body = {
        zh: "不同来源的证据不能等权相信；行动选择也不能只剩做题。系统必须允许恢复、求助、暂停和退出。",
        en: "Evidence from different sources should not be trusted equally; action choices must not be limited to doing exercises. Recovery, help-seeking, pausing and exit must remain available."
      };
    }
    predictive.blocks.unshift({
      type: "concept",
      title: { zh: "预测—行动—反馈", en: "Prediction, action and feedback" },
      body: {
        zh: "人会先预期接下来会发生什么，再通过行动获得真实反馈。反馈与预期不一致时，人可以调整理解、换一种行动，或承认当前信息不足。系统记录和校准这个过程，而不是给出一条不可更改的结论。",
        en: "A person anticipates what will happen, acts, and receives real feedback. When feedback differs from expectation, the person can revise understanding, change the action, or acknowledge missing information. The system records and calibrates this process rather than issuing an irreversible conclusion."
      }
    });
  }

  const stateLesson = course.lessons.find((lesson) => lesson.id === "state");
  if (stateLesson) {
    stateLesson.summary = {
      zh: "状态由语言、行为、作答、结果、历史与情境共同形成，并持续保留不确定性。",
      en: "State is formed from language, behavior, answers, outcomes, history and context—with uncertainty retained."
    };
    stateLesson.objectives = [
      { zh: "理解多源证据如何共同形成状态假设", en: "Understand how multiple evidence sources form a state hypothesis" },
      { zh: "解释为什么模型输出必须可更正", en: "Explain why model outputs must remain correctable" }
    ];
    stateLesson.blocks.unshift({
      type: "concept",
      title: { zh: "多源证据一起说话", en: "Multiple sources speak together" },
      body: {
        zh: "系统不会只看一句话、一次点击或一道题。它会同时参考用户怎么表达、实际做了什么、答题结果怎样、后来发生了什么、过去有没有类似模式，以及当时的任务和关系情境。任何单一来源都只能提供部分证据。",
        en: "The system does not rely on one sentence, one click or one answer. It considers how the user expressed something, what they actually did, how they answered, what happened next, whether similar patterns existed before, and the task and relationship context. Any single source provides only partial evidence."
      }
    });
  }
})();

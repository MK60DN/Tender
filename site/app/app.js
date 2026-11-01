(function(){
  "use strict";
  const KEY="tender.github.demo.v1";
  const $=(id)=>document.getElementById(id);
  const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||"{}")}catch(_){return {}}};
  const state={data:load(),stage:"",grade:"",subjects:[],targets:[],question:0,responses:[],danmakuTimers:[]};
  const stages=["初中","高中","大学","研究生","职业早期","其他"];
  const grades={"初中":["初一","初二","初三"],"高中":["高一","高二","高三"],"大学":["大一","大二","大三","大四","大五及以上"],"研究生":["硕士一年级","硕士二年级","硕士三年级","博士阶段"],"职业早期":["工作 0–2 年","工作 3–5 年","工作 5 年以上"],"其他":["其他"]};
  const subjects={"初中":["语文","数学","英语","物理","化学","生物","历史","地理","道德与法治"],"高中":["语文","数学","英语","物理","化学","生物","历史","地理","政治","高考报名"],"大学":["专业核心课","数学与统计","编程与数据","英语","学术写作","实验与项目","职业规划"],"研究生":["研究方向","文献阅读","研究方法","学术写作","数据分析","实验与项目"],"职业早期":["岗位技能","行业知识","编程与数据","管理协作","英语","资格认证"],"其他":["语文","数学","英语","编程与数据","职业技能","兴趣探索"]};
  const questions=[
    "面对一个新任务时，我通常先看具体材料和现实条件。",
    "任务没有明确结构时，我会先停下来整理自己的理解。",
    "我容易同时打开很多方向，难以决定先做哪一个。",
    "被评价或可能出错时，我会明显紧张并推迟行动。",
    "短任务和可见进展比长期计划更能帮助我开始。",
    "我通常能从过去的类似经验中找到下一步。",
    "我需要先理解这件事为什么重要，才愿意持续投入。",
    "连续工作一段时间后，我知道怎样让自己恢复。"
  ];
  const agents=[["策略","学习策略师","任务拆解与优先级"],["学科","学科专家","知识点与先修关系"],["认知","神经认知师","注意、负荷与恢复"],["心理","心理调节师","焦虑、回避与动机"],["营养","营养健康师","睡眠、饮食与能量"],["生涯","生涯规划师","目标专业与长期路径"],["安全","安全保护官","隐私、风险与求助边界"],["元认知","元认知教练","策略监控与复盘"]];
  function save(){localStorage.setItem(KEY,JSON.stringify(state.data));}
  function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
  function toast(text){const el=$("toast");el.textContent=text;el.classList.add("show");clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove("show"),2600);}
  function setView(name){["loginView","worldView","assessmentView","dashboardView"].forEach(id=>$(id).hidden=id!==name);window.scrollTo({top:0,behavior:"smooth"});}
  function accountUI(){const user=state.data.user;const show=Boolean(user&&state.data.signedIn);$("accountWrap").hidden=!show;if(!user)return;$("avatar").textContent=(user.name||"T").slice(0,1).toUpperCase();$("accountName").textContent=user.name;$("menuName").textContent=user.name;$("menuId").textContent=user.id;}
  function renderStageOptions(){ $("stageSelect").innerHTML=stages.map(x=>'<option>'+esc(x)+'</option>').join(""); $("stageSelect").value=state.stage||state.data.world?.stage||"高中"; renderGrades(); renderSubjects(); if(state.data.world){$("schoolInput").value=state.data.world.school||"";$("majorInput").value=state.data.world.major||"";$("goalInput").value=state.data.world.goal||"";state.subjects=[...(state.data.world.subjects||[])];state.targets=[...(state.data.world.target_subjects||[])];renderSubjects();} }
  function renderGrades(){const s=$("stageSelect").value; $("gradeSelect").innerHTML=(grades[s]||[]).map(x=>'<option>'+esc(x)+'</option>').join(""); if(state.data.world&&state.data.world.grade&&(grades[s]||[]).includes(state.data.world.grade))$("gradeSelect").value=state.data.world.grade;}
  function chipList(host,items,selected,target){$(host).innerHTML=items.map(x=>'<button type="button" class="chip '+(target?'target ':'')+(selected.includes(x)?'sel':'')+'" data-v="'+esc(x)+'" data-target="'+(target?1:0)+'">'+esc(x)+'</button>').join("");$(host).querySelectorAll("button").forEach(b=>b.onclick=()=>toggleChip(b.dataset.v,b.dataset.target==="1"));}
  function renderSubjects(){const s=$("stageSelect").value;const items=subjects[s]||subjects["其他"];state.subjects=state.subjects.filter(x=>items.includes(x));state.targets=state.targets.filter(x=>items.includes(x));chipList("subjectChips",items,state.subjects,false);chipList("targetChips",items,state.targets,true);}
  function toggleChip(v,target){const arr=target?state.targets:state.subjects;const i=arr.indexOf(v);if(i>=0)arr.splice(i,1);else{if(target&&arr.length>=3){toast("当前重点最多选择 3 项");return;}if(!target&&arr.length>=10){toast("主要科目最多选择 10 项");return;}arr.push(v);}if(!target)state.targets=state.targets.filter(x=>state.subjects.includes(x));renderSubjects();}
  function startWorld(){if(!state.data.user)return;state.stage=state.data.user.stage||"高中";setView("worldView");renderStageOptions();accountUI();}
  function goNext(){if(!state.data.signedIn||!state.data.user){setView("loginView");accountUI();return;}if(!state.data.world){startWorld();return;}if(!state.data.assessment){startAssessment();return;}renderDashboard();}
  function startAssessment(){state.question=0;state.responses=[];setView("assessmentView");renderQuestion();accountUI();}
  function renderQuestion(){const q=questions[state.question];$("questionText").textContent=q;$("questionCount").textContent=(state.question+1)+" / "+questions.length;$("progressBar").style.width=(state.question/questions.length*100)+"%";$("scaleButtons").innerHTML=[1,2,3,4,5].map(n=>'<button type="button" data-n="'+n+'">'+n+'</button>').join("");$("scaleButtons").querySelectorAll("button").forEach(b=>b.onclick=()=>answer(Number(b.dataset.n)));}
  function answer(n){state.responses[state.question]=n;state.question++;if(state.question<questions.length){renderQuestion();return;}finishAssessment();}
  function finishAssessment(){const sum=state.responses.reduce((a,b)=>a+b,0);const avg=sum/questions.length;const support=avg<2.6?"当前更需要缩小任务、降低启动成本，并明确一次只做一件事。":avg>3.7?"当前资源较充足，适合增加主动输出、迁移和创造任务。":"当前适合在结构化支持与自主探索之间保持弹性，先用短行动验证判断。";state.data.assessment={completedAt:new Date().toISOString(),responses:state.responses,avg:Math.round(avg*100)/100,support};save();renderDashboard();toast("支持偏好已生成");}
  function worldRows(w){return [["阶段",(w.stage||"—")+" · "+(w.grade||"—")],["学校 / 专业",[w.school,w.major].filter(Boolean).join(" · ")||"未填写"],["学习范围",(w.subjects||[]).join("、")||"未选择"],["当前重点",(w.target_subjects||[]).join("、")||"尚未指定"],["当前目标",w.goal||"先建立稳定学习节奏"]];}
  function rows(items){return items.map(([k,v])=>'<div class="kv"><span>'+esc(k)+'</span><b>'+esc(v)+'</b></div>').join("");}
  function renderDashboard(){const u=state.data.user,w=state.data.world,a=state.data.assessment;if(!u||!w||!a){goNext();return;}$("greeting").textContent=u.name+"，今天先做一个最小步骤。";$("worldSummary").innerHTML=rows(worldRows(w));$("supportSummary").innerHTML='<p><b>当前假设</b></p><p>'+esc(a.support)+'</p><p class="muted">这是一份可更正的支持假设，不是人格、能力、心理或医学诊断。</p>';$("agentRoom").innerHTML=agents.map(x=>'<div class="agent"><i>'+esc(x[0])+'</i><div><b>'+esc(x[1])+'</b><small>'+esc(x[2])+'</small></div></div>').join("");setView("dashboardView");accountUI();showDanmaku();}
  function card(agent,text,action){return '<div class="danmaku-card"><b>'+esc(agent[0])+' · '+esc(agent[1])+'</b><p>'+esc(text)+'</p><small>'+esc(action)+'</small></div>';}
  function showDanmaku(){state.danmakuTimers.forEach(clearTimeout);state.danmakuTimers=[];$("lane1").innerHTML="";$("lane2").innerHTML="";const w=state.data.world||{};const focus=(w.target_subjects||[])[0]||(w.subjects||[])[0]||"当前任务";const goal=w.goal||"今天的最小目标";$("lane1").innerHTML=card(agents[0],"先只处理「"+focus+"」的一个最小步骤，不打开新的分支。","现在做 10 分钟");state.danmakuTimers.push(setTimeout(()=>{$("lane2").innerHTML=card(agents[7],"做完后写一句：刚才的方法对「"+goal+"」有没有用？","30 秒复盘");},1200));}
  function logout(){state.data.signedIn=false;save();$("accountMenu").hidden=true;setView("loginView");accountUI();toast("已退出账号，数据仍保留在本机");}
  function deleteData(){if(!confirm("清除当前浏览器中的 Tender 演示数据？这个操作不能恢复。"))return;localStorage.removeItem(KEY);state.data={};state.subjects=[];state.targets=[];accountUI();setView("loginView");toast("本机演示数据已清除");}
  $("loginForm").addEventListener("submit",e=>{e.preventDefault();const name=$("nameInput").value.trim();if(!name){toast("先填写昵称");return;}if(!$("consentInput").checked){toast("请先确认用途");return;}state.data={signedIn:true,user:{id:"DEMO-"+Date.now().toString(36).toUpperCase(),name,createdAt:new Date().toISOString()}};save();startWorld();});
  $("stageSelect").addEventListener("change",()=>{renderGrades();renderSubjects();});
  $("worldForm").addEventListener("submit",e=>{e.preventDefault();if(!state.subjects.length){toast("至少选择一个学习科目");return;}state.data.world={stage:$("stageSelect").value,grade:$("gradeSelect").value,school:$("schoolInput").value.trim(),major:$("majorInput").value.trim(),subjects:[...state.subjects],target_subjects:[...state.targets],goal:$("goalInput").value.trim()};save();startAssessment();});
  $("logoutWorldBtn").onclick=logout;$("accountBtn").onclick=e=>{e.stopPropagation();$("accountMenu").hidden=!$("accountMenu").hidden;};document.addEventListener("click",()=>{$("accountMenu").hidden=true;});$("logoutBtn").onclick=logout;$("deleteBtn").onclick=deleteData;$("editWorldBtn").onclick=startWorld;$("replayDanmaku").onclick=showDanmaku;
  if(state.data.signedIn&&state.data.user){goNext();}else{setView("loginView");accountUI();}
})();

(function(){
  "use strict";
  const $=(id)=>document.getElementById(id);
  const params=new URLSearchParams(location.search);
  const account=(()=>{try{return JSON.parse(localStorage.getItem("tender.account")||"null")}catch(_){return null}})();
  const studentId=params.get("student")||(account&&account.studentId)||localStorage.getItem("tender.student")||"";
  if(!account||!studentId){location.replace("/ui/login.html?next="+encodeURIComponent("/ui/world-setup.html"));return;}
  const stageOptions=["小学","初中","高中","大学","研究生","职业早期","其他"];
  const grades={
    "小学":["一年级","二年级","三年级","四年级","五年级","六年级"],
    "初中":["初一","初二","初三"],"高中":["高一","高二","高三"],
    "大学":["大一","大二","大三","大四","大五及以上"],
    "研究生":["硕士一年级","硕士二年级","硕士三年级","博士阶段"],
    "职业早期":["工作 0–2 年","工作 3–5 年","工作 5 年以上"],"其他":["其他"]
  };
  const subjects={
    "小学":["语文","数学","英语","科学","道德与法治","艺术","体育"],
    "初中":["语文","数学","英语","物理","化学","生物","历史","地理","道德与法治","信息技术"],
    "高中":["语文","数学","英语","物理","化学","生物","历史","地理","政治","信息技术","高考报名"],
    "大学":["专业核心课","数学与统计","编程与数据","英语","学术写作","实验与项目","人文社科","职业规划"],
    "研究生":["研究方向","文献阅读","研究方法","学术写作","数据分析","实验与项目","教学能力"],
    "职业早期":["岗位技能","行业知识","编程与数据","管理协作","英语","资格认证","求职与转岗"],
    "其他":["语文","数学","英语","编程与数据","职业技能","兴趣探索","其他"]
  };
  let selectedSubjects=[]; let selectedTargets=[];
  const existing=(()=>{try{return JSON.parse(localStorage.getItem("tender.worldContext."+studentId)||"null")}catch(_){return null}})();
  function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
  function renderStages(){ $("stageSelect").innerHTML=stageOptions.map(x=>'<option>'+esc(x)+'</option>').join(""); $("stageSelect").value=(existing&&existing.stage)||(account.stage||"高中"); renderGrades(); renderSubjects(); }
  function renderGrades(){ const stage=$("stageSelect").value; $("gradeSelect").innerHTML=(grades[stage]||[]).map(x=>'<option>'+esc(x)+'</option>').join(""); if(existing&&grades[stage]&&grades[stage].includes(existing.grade)) $("gradeSelect").value=existing.grade; }
  function renderChips(hostId,items,selected,target){ $(hostId).innerHTML=items.map(item=>'<button type="button" class="chip '+(target?'target ':'')+(selected.includes(item)?'sel':'')+'" data-value="'+esc(item)+'" data-target="'+(target?'1':'0')+'">'+esc(item)+'</button>').join(""); $(hostId).querySelectorAll("button").forEach(btn=>btn.addEventListener("click",()=>toggle(btn.dataset.value,btn.dataset.target==="1"))); }
  function toggle(value,target){ const list=target?selectedTargets:selectedSubjects; const index=list.indexOf(value); if(index>=0) list.splice(index,1); else { if(target&&list.length>=3){$("status").textContent="最想提升的方向最多选择 3 项。";return;} if(!target&&list.length>=10){$("status").textContent="主要科目最多选择 10 项。";return;} list.push(value); } if(!target) selectedTargets=selectedTargets.filter(x=>selectedSubjects.includes(x)); $("status").textContent=""; renderSubjects(); showPreview(); }
  function renderSubjects(){ const stage=$("stageSelect").value; const items=subjects[stage]||subjects["其他"]; selectedSubjects=selectedSubjects.filter(x=>items.includes(x)); selectedTargets=selectedTargets.filter(x=>items.includes(x)); renderChips("subjectChips",items,selectedSubjects,false); renderChips("targetChips",items,selectedTargets,true); $("majorField").classList.toggle("hidden",!["大学","研究生","职业早期"].includes(stage)); }
  function payload(){return {stage:$("stageSelect").value,grade:$("gradeSelect").value,school:$("schoolInput").value.trim(),major:$("majorInput").value.trim(),subjects:selectedSubjects,target_subjects:selectedTargets,goal:$("goalInput").value.trim(),learning_mode:$("modeSelect").value};}
  function showPreview(){ const d=payload(); if(!d.subjects.length)return; $("preview").classList.add("show"); $("preview").innerHTML='<b>你的客观世界坐标</b><p>'+esc(d.stage)+' · '+esc(d.grade)+(d.major?' · '+esc(d.major):'')+'</p><p>学习范围：'+esc(d.subjects.join('、'))+'</p><p>当前目标：'+(d.target_subjects.length?esc(d.target_subjects.join('、')):'先建立基础')+(d.goal?' · '+esc(d.goal):'')+'</p>'; }
  async function token(){const r=await fetch("/auth/demo-session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({actor_id:studentId,role:"learner",learner_id:studentId})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"无法建立会话");return d.token;}
  async function hydrate(){ if(!existing){ try{const t=await token();const r=await fetch("/learner/world-setup/"+encodeURIComponent(studentId),{headers:{Authorization:"Bearer "+t}});if(r.ok){const d=await r.json();const w=d.world_context||{};if(w.stage){$("stageSelect").value=w.stage;renderGrades();$("gradeSelect").value=w.grade||$("gradeSelect").value;$("schoolInput").value=w.school||"";$("majorInput").value=w.major||"";selectedSubjects=w.subjects||[];selectedTargets=w.target_subjects||[];$("goalInput").value=w.goal||"";$("modeSelect").value=w.learning_mode||"自主学习";renderSubjects();showPreview();}}}catch(_){}} else { $("schoolInput").value=existing.school||"";$("majorInput").value=existing.major||"";selectedSubjects=existing.subjects||[];selectedTargets=existing.target_subjects||[];$("goalInput").value=existing.goal||"";$("modeSelect").value=existing.learning_mode||"自主学习";renderSubjects();showPreview(); } }
  $("stageSelect").addEventListener("change",()=>{renderGrades();renderSubjects();showPreview();}); $("gradeSelect").addEventListener("change",showPreview); $("goalInput").addEventListener("input",showPreview);
  $("worldForm").addEventListener("submit",async(event)=>{ event.preventDefault();$("status").textContent=""; if(!selectedSubjects.length){$("status").textContent="至少选择一个主要学习科目或能力领域。";return;} $("saveBtn").disabled=true;$("saveBtn").textContent="正在保存…"; try{ const t=await token();const body={world_context:payload(),consent:true}; const r=await fetch("/learner/world-setup/"+encodeURIComponent(studentId),{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+t},body:JSON.stringify(body)}); const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"保存失败"); localStorage.setItem("tender.worldSetup."+studentId,"complete");localStorage.setItem("tender.worldContext."+studentId,JSON.stringify(d.world_context)); const profile=await fetch("/preassessment/profile/"+encodeURIComponent(studentId),{headers:{Authorization:"Bearer "+t}}); if(profile.ok){localStorage.setItem("tender.onboarding."+studentId,"complete");location.replace("/ui/single.html?student="+encodeURIComponent(studentId));}else{location.replace("/ui/preassessment.html?student="+encodeURIComponent(studentId)+"&onboarding=1");} }catch(error){$("status").textContent=error.message||"保存失败";$("saveBtn").disabled=false;$("saveBtn").textContent="保存世界坐标，继续测评";} });
  renderStages();hydrate();
})();

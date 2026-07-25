const userId = "demo_family_001";
const sessionId = `demo_session_${Date.now()}`;
const venueId = "nuanquan_ancient_town";

const scenarios = {
  family: {
    message: "我第一次来暖泉古镇，带孩子，下午还有两个小时，怎么逛比较合适？",
    location: "暖泉古镇入口",
    spotId: null,
    eventType: "enter_venue",
    groupType: "family",
    availableTime: 120,
    persona: "亲子家庭 / 初次到访",
    interest: "西古堡、剪纸、轻松路线",
    mode: "chat",
    trace: {
      context: "入口场景 + 第一次到访 + 带孩子 + 剩余约 2 小时。",
      memory: "写入亲子家庭、轻松游览、非遗互动的初始偏好。",
      tool: "调用路线推荐工具，返回初次到访或亲子非遗路线。",
      trust: "推荐理由展示路线覆盖古堡、街巷、非遗与商业记忆。"
    }
  },
  xigubao: {
    message: "请介绍暖泉古镇的西古堡",
    location: "西古堡",
    spotId: "spot_xigubao",
    eventType: "dwell",
    dwellSeconds: 240,
    persona: "文化兴趣 / 点位停留",
    interest: "西古堡、古堡建筑",
    mode: "rag",
    trace: {
      context: "用户位于西古堡，提出文化讲解需求。",
      memory: "提升古堡建筑、文保内容、深度讲解偏好。",
      tool: "调用 Graph RAG，从暖泉知识图谱检索西古堡节点和证据。",
      trust: "展示来源引用，避免模型自由发挥。"
    }
  },
  papercut: {
    message: "孩子对剪纸挺感兴趣，我们想多看看非遗相关的内容。",
    location: "蔚县剪纸体验点",
    spotId: "spot_papercut_experience",
    eventType: "enter_spot",
    groupType: "family",
    persona: "亲子家庭 / 非遗兴趣",
    interest: "蔚县剪纸、亲子任务、文创",
    mode: "chat",
    trace: {
      context: "用户从古堡游览转向剪纸体验点，兴趣发生变化。",
      memory: "增强剪纸、非遗、亲子互动偏好。",
      tool: "调用推荐工具，返回剪纸点位、识别纹样任务和剪纸文创。",
      trust: "推荐解释围绕非遗体验，不做硬销售。"
    }
  },
  dashuhua: {
    message: "晚上想看打树花，应该怎么安排？",
    location: "暖泉古镇",
    spotId: "spot_dashuhua_stage",
    eventType: "enter_spot",
    groupType: "family",
    persona: "夜游 / 摄影兴趣",
    interest: "打树花、夜游、拍照",
    mode: "chat",
    trace: {
      context: "用户表达夜游表演意图，场景从白天游览切换到夜间活动。",
      memory: "写入打树花、夜游、摄影兴趣信号。",
      tool: "调用路线推荐与 Graph RAG 主题知识，推荐夜游打树花路线。",
      trust: "动态运营信息提示以现场或官方为准。"
    }
  },
  products: {
    message: "有什么适合带走的纪念品？",
    location: "蔚县剪纸体验点",
    spotId: "spot_papercut_experience",
    eventType: "leaving",
    visitStage: "leaving",
    persona: "离场前 / 文创消费",
    interest: "剪纸、打树花、伴手礼",
    mode: "products",
    trace: {
      context: "用户进入消费服务阶段，位置靠近剪纸体验和文创场景。",
      memory: "结合此前亲子、剪纸、打树花兴趣。",
      tool: "调用文创推荐，返回剪纸作品、书签、打树花纪念品等。",
      trust: "解释商品与文化主题的关联，保持低打扰。"
    }
  }
};

const messagesEl = document.querySelector("#messages");
const apiStateEl = document.querySelector("#apiState");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const currentLocationEl = document.querySelector("#currentLocation");
const currentPersonaEl = document.querySelector("#currentPersona");
const currentInterestEl = document.querySelector("#currentInterest");
const contextTraceEl = document.querySelector("#contextTrace");
const memoryTraceEl = document.querySelector("#memoryTrace");
const toolTraceEl = document.querySelector("#toolTrace");
const trustTraceEl = document.querySelector("#trustTrace");
const sessionMemoryTraceEl = document.querySelector("#sessionMemoryTrace");
const serviceFlowTraceEl = document.querySelector("#serviceFlowTrace");
const proactiveCardEl = document.querySelector("#proactiveCard");
const acceptDecisionEl = document.querySelector("#acceptDecision");
const dismissDecisionEl = document.querySelector("#dismissDecision");
let currentDecision = null;

function setApiState(text, kind = "") {
  apiStateEl.textContent = text;
  apiStateEl.className = `api-state ${kind}`.trim();
}

function addMessage(role, content, cards = []) {
  const template = document.querySelector("#messageTemplate");
  const node = template.content.firstElementChild.cloneNode(true);
  node.classList.add(role);
  node.querySelector(".message-role").textContent = role === "user" ? "游客" : role === "system" ? "系统提示" : "数字人";
  const body = node.querySelector(".message-body");
  body.textContent = content;
  if (cards.length) {
    const list = document.createElement("div");
    list.className = "card-list";
    cards.forEach((card) => {
      const item = document.createElement("div");
      item.className = "result-card";
      const title = document.createElement("strong");
      title.textContent = card.title;
      const detail = document.createElement("span");
      detail.textContent = card.detail;
      item.append(title, detail);
      list.appendChild(item);
    });
    body.appendChild(list);
  }
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function updateScene(scenario) {
  currentLocationEl.textContent = scenario.location;
  currentPersonaEl.textContent = scenario.persona;
  currentInterestEl.textContent = scenario.interest;
  contextTraceEl.textContent = scenario.trace.context;
  memoryTraceEl.textContent = scenario.trace.memory;
  toolTraceEl.textContent = scenario.trace.tool;
  trustTraceEl.textContent = scenario.trace.trust;
  document.querySelectorAll(".map-node").forEach((node) => {
    node.classList.toggle("active", scenario.location.includes(node.dataset.location));
  });
}

function updateProactiveCard(decision) {
  currentDecision = decision && decision.status === "trigger" ? decision : null;
  proactiveCardEl.classList.toggle("empty", !currentDecision);
  proactiveCardEl.querySelector("strong").textContent = currentDecision ? currentDecision.title : "等待用户状态变化";
  proactiveCardEl.querySelector("p").textContent = currentDecision
    ? currentDecision.message
    : "当用户进入点位、停留或表达兴趣后，这里会出现轻提示。";
  acceptDecisionEl.textContent = currentDecision?.primary_button || "接受";
  dismissDecisionEl.textContent = currentDecision?.secondary_button || "先不用";
}

function updateServiceFlow(eventType, memory, decision) {
  const state = memory
    ? `${memory.visit_stage || "entry"} / ${memory.current_spot_id || "未进入点位"}`
    : "等待状态";
  const action = decision?.status === "trigger" ? decision.action : "observe";
  const mode = decision?.mode || "silent";
  serviceFlowTraceEl.textContent = `状态变化：${eventType} -> 当前状态：${state} -> 决策：${action} -> 服务触发：${mode}`;
}

function updateSessionMemory(memory) {
  if (!memory) {
    sessionMemoryTraceEl.textContent = "还没有本次游览记忆。";
    return;
  }
  const spots = memory.visited_spots?.length ? memory.visited_spots.join("、") : "暂无";
  const interests = Object.entries(memory.interest_signals || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([key]) => key)
    .join("、") || "暂无";
  const skipped = memory.dismissed_actions?.length ? memory.dismissed_actions.join("、") : "暂无";
  sessionMemoryTraceEl.textContent = `已到访：${spots}。兴趣：${interests}。已跳过：${skipped}。`;
}

async function recordSessionEvent(scenario) {
  const eventType = scenario.eventType || "chat";
  const payload = {
    user_id: userId,
    session_id: sessionId,
    venue_id: venueId,
    event_type: eventType,
    spot_id: scenario.spotId,
    content: eventType === "chat" ? scenario.message : null,
    value: eventType === "dwell" ? scenario.dwellSeconds || 0 : null,
    metadata: {
      source: "frontend_demo",
      group_type: scenario.groupType || "",
      visit_stage: scenario.visitStage || "",
      available_time_minutes: scenario.availableTime || 0,
      dwell_seconds: scenario.dwellSeconds || 0
    }
  };
  if (eventType === "leaving") {
    payload.value = "leaving";
  }
  const response = await fetch("/api/v1/session/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  updateSessionMemory(data.session_memory);
  updateProactiveCard(data.next_decision);
  updateServiceFlow(eventType, data.session_memory, data.next_decision);
  return data;
}

async function recordAction(action, accepted) {
  const response = await fetch("/api/v1/session/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      venue_id: venueId,
      event_type: accepted ? "accept" : "skip",
      value: action,
      metadata: { action, source: "frontend_demo" }
    })
  });
  const data = await response.json();
  updateSessionMemory(data.session_memory);
  updateProactiveCard(data.next_decision);
  updateServiceFlow(accepted ? "accept" : "skip", data.session_memory, data.next_decision);
}

function recommendationCardsFromStrings(recommendations = []) {
  return recommendations.map((text) => {
    const [head, ...rest] = text.split(":");
    return { title: rest.length ? head : "推荐", detail: rest.length ? rest.join(":").trim() : text };
  });
}

function recommendationCards(data = {}) {
  const cards = data.recommendation_cards || [];
  if (!cards.length) return recommendationCardsFromStrings(data.recommendations || []);
  return cards.map((card) => ({
    title: `${card.title}${card.subtitle ? ` · ${card.subtitle}` : ""}`,
    detail: [card.description, card.reason ? `推荐理由：${card.reason}` : "", card.action_label ? `动作：${card.action_label}` : ""]
      .filter(Boolean)
      .join("\n")
  }));
}

function citationCards(citations = []) {
  return citations.map((item) => ({
    title: `${item.node || "证据来源"} · ${item.confidence || "medium"}`,
    detail: `${item.source || "当前 P0 数据草案"}\n来源类型：${item.source_type || "scene_package"}`
  }));
}

async function runScenario(key) {
  const scenario = scenarios[key];
  updateScene(scenario);
  addMessage("user", scenario.message);
  setApiState("调用中");
  try {
    await recordSessionEvent(scenario);
    if (scenario.mode === "rag") {
      const params = new URLSearchParams({ query: scenario.message });
      const response = await fetch(`/api/v1/knowledge/grounded-answer?${params}`);
      const data = await response.json();
      addMessage("assistant", data.answer, citationCards(data.citations));
      trustTraceEl.textContent = `${data.evidence_summary || "已返回引用"} 可信度：${data.confidence_label || "中等"}。`;
    } else if (scenario.mode === "products") {
      const params = new URLSearchParams({ venue_id: venueId, location: scenario.location });
      const response = await fetch(`/api/v1/users/${userId}/recommendations?${params}`);
      const data = await response.json();
      addMessage("assistant", "我会优先推荐与剪纸、打树花和古堡记忆有关的轻量文创，以下是当前可演示的推荐结果。", recommendationCards(data));
      await recordSessionEvent({ ...scenario, eventType: "chat" });
    } else {
      const response = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, session_id: sessionId, venue_id: venueId, message: scenario.message, location: scenario.location })
      });
      const data = await response.json();
      addMessage("assistant", data.answer || "已生成推荐。", recommendationCards(data));
      if (data.memory_summary) memoryTraceEl.textContent = `Memory 摘要：${data.memory_summary.slice(-140)}`;
      await recordSessionEvent({ ...scenario, eventType: "chat" });
    }
    setApiState("已连接", "ok");
  } catch (error) {
    setApiState("连接失败", "error");
    addMessage("system", "未能连接后端服务。请确认 uvicorn 已启动，并访问 http://127.0.0.1:8000/demo。");
  }
}

async function sendCustomMessage(message) {
  scenarios.custom = {
    ...scenarios.family,
    message,
    location: currentLocationEl.textContent,
    eventType: "chat",
    trace: {
      context: "用户自由输入，沿用当前场景和位置。",
      memory: "系统将根据对话文本更新短期记忆和画像。",
      tool: "调用 /api/v1/chat，返回推荐和解释。",
      trust: "如涉及文化讲解，可进一步通过 Graph RAG 查看证据。"
    }
  };
  await runScenario("custom");
}

document.querySelectorAll("[data-scenario]").forEach((button) => button.addEventListener("click", () => runScenario(button.dataset.scenario)));
document.querySelectorAll(".map-node").forEach((button) => {
  button.addEventListener("click", () => {
    currentLocationEl.textContent = button.dataset.location;
    document.querySelectorAll(".map-node").forEach((node) => node.classList.remove("active"));
    button.classList.add("active");
  });
});
chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  chatInput.value = "";
  sendCustomMessage(message);
});
acceptDecisionEl.addEventListener("click", async () => {
  if (!currentDecision) return;
  await recordAction(currentDecision.action, true);
  addMessage("user", currentDecision.primary_button || "接受");
  if (currentDecision.action === "offer_deep_explanation") {
    const query = currentDecision.payload?.knowledge_query || currentDecision.message;
    const params = new URLSearchParams({ query });
    const response = await fetch(`/api/v1/knowledge/grounded-answer?${params}`);
    const data = await response.json();
    addMessage("assistant", data.answer, citationCards(data.citations));
    trustTraceEl.textContent = `${data.evidence_summary || "已返回引用"} 可信度：${data.confidence_label || "中等"}。`;
  } else {
    addMessage("assistant", "好，我会按这个方向继续帮你安排。", []);
  }
});
dismissDecisionEl.addEventListener("click", async () => {
  if (!currentDecision) return;
  const action = currentDecision.action;
  await recordAction(action, false);
  addMessage("user", "先不用");
  addMessage("assistant", "好的，我先不打扰你。你继续逛，我会记住这次选择。");
});

addMessage("system", "欢迎进入暖泉古镇情境感知数字人 Demo。请点击左侧场景按钮，或直接输入游客问题。");
setApiState("待连接");

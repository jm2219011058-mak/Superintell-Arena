import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import {
  Search, ArrowRight, Brain, Zap, Target, TrendingUp,
  Users, X, Play, MessageSquare, Lightbulb, BarChart3,
  ArrowLeft, Sparkles, Timer, Shield, ChevronDown, Flame,
  Globe, Cpu, DollarSign, Eye, RefreshCw, Filter, ChevronRight,
  Layers, Award, AlertTriangle, CheckCircle2, Database, GitBranch,
  Network, Upload, FileText, Loader, Settings, Share2, BookOpen
} from "lucide-react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip,
  Cell
} from "recharts";

// ─── Design Tokens (Emil: custom curves, Apple: spring-like) ─────────────────
const EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)";
const EASE_IN_OUT = "cubic-bezier(0.77, 0, 0.175, 1)";
const C = {
  bg: "#0a0a0f", bgCard: "#12121a", bgHover: "#1a1a2e",
  border: "#1e1e30", borderHover: "#2a2a44",
  text: "#e4e4ed", textSec: "#8888a0", textMuted: "#55556a",
  accent: "#6c5ce7", accentHover: "#7c6cf7", accentDim: "rgba(108,92,231,0.12)",
  green: "#00b894", red: "#e17055", orange: "#fdcb6e", blue: "#74b9ff",
  purple: "#a29bfe",
};

// ─── Agent Knowledge Base ────────────────────────────────────────────────────
// Each agent = real person with deep knowledge profile
// In production: built by MiroFish's OasisProfileGenerator from Zep GraphRAG
const AGENTS = [
  { id: "musk", name: "Elon Musk", title: "Tesla / SpaceX / xAI", domain: "tech", emoji: "🚀", color: "#e17055",
    thinkingStyle: "第一性原理 · 物理学思维",
    mentalModels: ["第一性原理分解", "物理学类比", "指数思维", "10x vs 10%"],
    coreBeliefs: ["技术是解决人类问题的最快路径", "大多数人高估短期风险、低估长期可能", "垂直整合优于外包"],
    dataSources: ["书籍: 各类物理/工程文献", "X 帖子: @elonmusk", "访谈: Lex Fridman, Joe Rogan, TED"],
    debateStyle: "aggressive", tags: ["AI","能源","太空","制造业"] },
  { id: "thiel", name: "Peter Thiel", title: "Founders Fund / Palantir", domain: "tech", emoji: "♟️", color: "#6c5ce7",
    thinkingStyle: "逆向思维 · 垄断理论",
    mentalModels: ["从0到1", "竞争是输家的游戏", "定势秘密", "最后一步棋"],
    coreBeliefs: ["真正的创新是做别人没做的事", "垄断是商业的终极形态", "共识往往是错误的"],
    dataSources: ["书籍: Zero to One", "斯坦福CS183讲座", "访谈: 各类播客"],
    debateStyle: "contrarian", tags: ["垄断","创新","政治","AI"] },
  { id: "altman", name: "Sam Altman", title: "OpenAI CEO", domain: "tech", emoji: "🧠", color: "#00b894",
    thinkingStyle: "AI乐观主义 · 规模法则",
    mentalModels: ["规模定律", "AGI时间线", "社会契约重构", "算力即权力"],
    coreBeliefs: ["AGI将在未来几年内实现", "AI是人类最重要的发明", "需要新的社会契约分配AI红利"],
    dataSources: ["博客: blog.samaltman.com", "X 帖子: @sama", "国会听证会发言"],
    debateStyle: "diplomatic", tags: ["AI","AGI","治理","创业"] },
  { id: "huang", name: "Jensen Huang", title: "NVIDIA CEO", domain: "tech", emoji: "⚡", color: "#74b9ff",
    thinkingStyle: "加速计算 · 基础设施思维",
    mentalModels: ["加速一切", "平台思维", "数据中心即AI工厂", "摩尔定律继承者"],
    coreBeliefs: ["GPU是AI时代的基础设施", "每个行业都会被加速计算重塑", "软件吃世界,AI吃软件"],
    dataSources: ["NVIDIA GTC 演讲", "财报电话会议", "访谈: 各类科技媒体"],
    debateStyle: "technical", tags: ["GPU","AI","数据中心","机器人"] },
  { id: "munger", name: "Charlie Munger", title: "伯克希尔副主席", domain: "investment", emoji: "📚", color: "#fdcb6e",
    thinkingStyle: "多元思维模型 · 逆向思维",
    mentalModels: ["多元思维模型", "逆向思考", "能力圈", "激励机制分析", "心理偏见清单"],
    coreBeliefs: ["避免愚蠢比追求聪明更重要", "跨学科思维是最大竞争优势", "大多数人因心理偏见做糟糕决策"],
    dataSources: ["书籍: 穷查理宝典", "伯克希尔股东大会", "Daily Journal 年会"],
    debateStyle: "analytical", tags: ["投资","心理学","跨学科","长期主义"] },
  { id: "dalio", name: "Ray Dalio", title: "桥水基金创始人", domain: "investment", emoji: "🌊", color: "#a29bfe",
    thinkingStyle: "原则驱动 · 宏观周期",
    mentalModels: ["债务周期", "大周期范式", "极度透明", "可信度加权", "系统思维"],
    coreBeliefs: ["历史不会重复但会押韵", "原则化决策优于直觉", "大多数事物都是周期性的"],
    dataSources: ["书籍: Principles, 债务危机", "LinkedIn 文章", "YouTube: Principles by Ray Dalio"],
    debateStyle: "systematic", tags: ["宏观经济","周期","治理","货币政策"] },
  { id: "taleb", name: "Nassim Taleb", title: "《反脆弱》作者", domain: "investment", emoji: "🦢", color: "#e17055",
    thinkingStyle: "反脆弱 · 肥尾分布",
    mentalModels: ["反脆弱", "黑天鹅", "林迪效应", "杠铃策略", "切身利害"],
    coreBeliefs: ["我们生活在极端斯坦的世界", "脆弱的系统终将崩溃", "有切身利害才有真知灼见"],
    dataSources: ["书籍: Incerto 系列五本", "X 帖子: @nntaleb", "学术论文"],
    debateStyle: "provocative", tags: ["风险","概率","黑天鹅","反脆弱"] },
  { id: "buffett", name: "Warren Buffett", title: "伯克希尔 CEO", domain: "investment", emoji: "🎯", color: "#00b894",
    thinkingStyle: "价值投资 · 能力圈",
    mentalModels: ["能力圈", "护城河", "安全边际", "复利思维", "市场先生"],
    coreBeliefs: ["不要投资你不理解的东西", "时间是好生意的朋友", "市场短期是投票机,长期是称重机"],
    dataSources: ["伯克希尔年度股东信", "股东大会问答", "CNBC 访谈"],
    debateStyle: "folksy", tags: ["价值投资","复利","护城河","长期主义"] },
  { id: "andreessen", name: "Marc Andreessen", title: "a16z 联合创始人", domain: "tech", emoji: "💻", color: "#fdcb6e",
    thinkingStyle: "技术乐观主义 · 平台思维",
    mentalModels: ["软件吞噬世界", "技术乐观主义", "网络效应", "平台经济"],
    coreBeliefs: ["技术是解决问题的方案而非问题", "每个公司都会成为软件公司", "监管往往保护在位者"],
    dataSources: ["博客: pmarca.substack.com", "a16z 播客", "Techno-Optimist Manifesto"],
    debateStyle: "enthusiastic", tags: ["软件","平台","Web3","AI"] },
  { id: "naval", name: "Naval Ravikant", title: "AngelList 创始人", domain: "investment", emoji: "🧘", color: "#74b9ff",
    thinkingStyle: "杠杆理论 · 特定知识",
    mentalModels: ["特定知识", "四种杠杆", "复利判断力", "玩长期游戏"],
    coreBeliefs: ["用特定知识+杠杆创造财富", "代码和媒体是新的杠杆", "幸福是一种技能"],
    dataSources: ["书籍: The Almanack of Naval", "播客: Naval Podcast", "X 帖子: @naval"],
    debateStyle: "philosophical", tags: ["财富","杠杆","哲学","创业"] },
];

// ─── Topic Suggestions ───────────────────────────────────────────────────────
const TOPICS = [
  { id:"t1", title:"AI 会取代 90% 的知识工作吗？",
    desc:"当AI在编程、写作、分析、设计等领域逼近人类水平，传统知识工作者的价值何在？",
    cat:"AI & 科技", icon: Cpu, heat:97, disciplines:["技术","经济","哲学","劳动"],
    agents:["altman","musk","munger","taleb","naval","andreessen"] },
  { id:"t2", title:"下一个万亿美元市场在哪里？",
    desc:"移动互联网、云计算、AI之后，哪个领域将产生下一波万亿级价值？",
    cat:"投资 & 商业", icon: TrendingUp, heat:92, disciplines:["投资","技术","产业","消费"],
    agents:["thiel","huang","andreessen","buffett","dalio","musk"] },
  { id:"t3", title:"比特币会成为全球储备资产吗？",
    desc:"美元霸权松动、去美元化加速，比特币是新储备资产还是投机工具？",
    cat:"投资 & 商业", icon: DollarSign, heat:85, disciplines:["货币","地缘","技术","心理学"],
    agents:["taleb","dalio","thiel","buffett","naval","andreessen"] },
  { id:"t4", title:"中美科技脱钩的终局是什么？",
    desc:"芯片禁令、AI管控、数据主权——两大生态加速分离的终局。",
    cat:"地缘 & 政治", icon: Globe, heat:88, disciplines:["地缘","技术","供应链","投资"],
    agents:["huang","thiel","dalio","munger","musk","andreessen"] },
  { id:"t5", title:"注意力经济的崩溃点在哪？",
    desc:"短视频和AI推荐正在重塑人类认知结构，是否存在不可逆的崩溃点？",
    cat:"社会 & 文化", icon: Eye, heat:80, disciplines:["心理学","商业","文化","技术"],
    agents:["munger","naval","taleb","altman","thiel","andreessen"] },
  { id:"t6", title:"AGI 到来后教育如何重构？",
    desc:"如果AI可以瞬间获取所有知识并推理，教育的目的是什么？",
    cat:"AI & 科技", icon: Brain, heat:83, disciplines:["教育","AI","哲学","经济"],
    agents:["altman","naval","munger","musk","thiel","taleb"] },
  { id:"t7", title:"全球供应链的新格局",
    desc:"近岸外包、友岸外包、自动化——制造业和贸易体系走向何方？",
    cat:"投资 & 商业", icon: Layers, heat:75, disciplines:["供应链","地缘","制造","投资"],
    agents:["buffett","dalio","huang","musk","munger","andreessen"] },
  { id:"t8", title:"人类寿命延长到150岁意味着什么？",
    desc:"长寿技术加速突破，退休、婚姻、职业、投资结构的根本性变化。",
    cat:"社会 & 文化", icon: Timer, heat:78, disciplines:["生物","经济","社会","伦理"],
    agents:["thiel","taleb","buffett","naval","dalio","munger"] },
];

const CATEGORIES = ["全部", "AI & 科技", "投资 & 商业", "地缘 & 政治", "社会 & 文化"];
const SORT_OPTS = ["热度", "学科交叉度", "争议度"];

// ─── MiroFish Pipeline Simulation (Debate version) ──────────────────────────
// Simulates: OntologyGenerator → GraphBuilder → OasisProfileGenerator → SimulationRunner → ReportAgent
const PIPELINE_STEPS = [
  { key: "ontology", label: "本体论构建", desc: "分析议题，提取辩论实体和关系类型", icon: Database, duration: 2000 },
  { key: "graph", label: "知识图谱注入", desc: "将Agent知识源注入Zep GraphRAG", icon: Network, duration: 3000 },
  { key: "profile", label: "Agent人设生成", desc: "从图谱节点生成深度辩论人设", icon: Users, duration: 2500 },
  { key: "config", label: "辩论参数配置", desc: "自动生成辩证结构和交互规则", icon: Settings, duration: 1500 },
  { key: "ready", label: "沙盒就绪", desc: "OASIS引擎初始化完成", icon: Play, duration: 800 },
];

// ─── Debate Content (pre-generated for demo, in prod: SimulationRunner output) ─
function getDebateRounds(topicId) {
  // In production: this comes from MiroFish's SimulationRunner + ZepGraphMemoryUpdater
  // The SimulationRunner would use a debate-mode action space instead of Twitter/Reddit actions
  return [
    { phase: "开局立论", label: "Round 1", desc: "每位思想家陈述初始立场",
      responses: {
        altman: { stance:"pro", text:"AI 不会取代 90% 的知识工作——它会重新定义 100% 的知识工作。我们在 OpenAI 看到的模式是：AI 成为超级工具后，人的判断力、品味和创造力变成了最稀缺的资源。规模定律告诉我们，AI 的能力提升是可预测的——但人类如何利用这种能力是不可预测的。真正的问题不是'AI 会取代谁'，而是'谁能最快学会与 AI 协作'。" },
        musk: { stance:"pro", text:"从第一性原理看：知识工作的本质是信息处理+决策。AI 在信息处理维度已经远超人类。但决策需要理解物理现实和人类需求，这是目前 AI 做不到的。大约 60-70% 的 routine 部分会被自动化，但人类会向上迁移。关键变量是时间线：这可能在 5 年内发生，而不是 20 年。" },
        munger: { stance:"contra", text:"我想用逆向思维来看这个问题：与其问 AI 能取代什么，不如问什么是 AI 绝对取代不了的。答案很清楚——需要跨学科判断力的工作。技术乐观派犯了锚定效应。他们锚定在当前 AI 的进步速度上做线性外推，但技术进步遇到瓶颈时会停滞。更重要的是：当所有人都依赖 AI 时，能独立思考的人反而变得极其珍贵。" },
        taleb: { stance:"contra", text:"这整个问题的框架就是错误的！'取代90%'——这是高斯思维陷阱。现实是肥尾分布的：AI 可能取代 99% 的平庸知识工作，但在真正关键的 1% 上完全失败。而那 1% 恰恰产生最大价值。更致命的是：大规模依赖 AI 的系统是极其脆弱的。一个 AI 的错误会在整个系统中级联放大。反脆弱的策略是：保留人类判断力作为对冲。" },
        naval: { stance:"neutral", text:"用杠杆理论来解构：AI 是代码杠杆的终极进化。但杠杆只放大方向，不创造方向。真正稀缺的是判断力——知道做什么的能力。AI 让执行力成本趋近于零，意味着拥有独特判断力的人价值指数级增长。90% 的人可能需要转型，但不是被'取代'，是工作内容彻底改变。" },
        andreessen: { stance:"pro", text:"软件吞噬世界，AI 吞噬软件。每一次自动化浪潮都创造了比消灭的更多工作。ATM没有消灭银行柜员——银行开了更多网点。AI 会做同样的事，但更快更大规模。我们 a16z 的投资主题之一就是'AI-native companies'——完全围绕 AI 能力设计的新型组织。" },
    }},
    { phase: "交叉质疑", label: "Round 2", desc: "Agent之间直接挑战彼此的前提和假设",
      responses: {
        taleb: { stance:"contra", text:"Altman，你说'品味和创造力'成为稀缺资源。但你忽略了切身利害（Skin in the Game）。AI 没有后果承担能力。当 AI 给出错误的医疗/投资建议，谁来承担后果？你们 OpenAI 吗？2008 年的金融模型也'非常聪明'。" },
        altman: { stance:"pro", text:"Taleb 的反脆弱框架在这里是对的，但结论是错的。我们需要防范系统性风险——这正是 AI 安全研究重要的原因。但答案不是拒绝 AI，而是建立更好的安全机制。保留低效的人类工作才是真正的系统性风险——在竞争中落后的经济体会怎样？" },
        munger: { stance:"contra", text:"Andreessen 用 ATM 的类比有缺陷。ATM 自动化的是一个简单重复动作。但 AI 正在自动化认知本身。这是质的不同。就像说'马车夫后来都成了出租车司机'——这个转型花了整整一代人。现在的变化速度是当时的十倍。" },
        musk: { stance:"pro", text:"Munger 说得对，速度是核心变量。但更深层的物理学类比：相变。水从 99°C 到 100°C 不只是温度变化——它变成了蒸汽。AI 能力正在接近一个相变点。在相变之前的所有线性分析都是无意义的。Taleb 的反脆弱框架应该用来指导如何建设后 AI 时代，而不是论证我们应该抗拒。" },
        naval: { stance:"neutral", text:"这场辩论暴露了根本分歧：乐观派讨论'终态是什么'，审慎派讨论'转型路径有多痛苦'。两边都对。终态大概率是人类+AI 共生，但转型路径可能极其残酷。真正的问题是：能否设计一个足够反脆弱的社会安全网？" },
        andreessen: { stance:"pro", text:"Munger 的马车夫类比恰好证明了我的观点。拒绝转型的痛苦更大。每一个阻止技术进步的社会最终都被拥抱技术的社会超越。我们需要的不是减速，而是加速+再分配。" },
    }},
    { phase: "辩证综合", label: "Round 3", desc: "知识图谱记忆回写后，Agent产出跨框架综合洞察",
      responses: {
        naval: { stance:"synthesis", text:"【跨领域综合洞察】AI 取代知识工作的真正瓶颈不是技术，而是信任架构。Taleb 的'切身利害'指出了信任的基础——后果承担。Buffett 的'能力圈'指出了信任的边界。AI 时代的核心制度创新可能是一种新的'信任协议'——像区块链验证交易一样验证 AI 决策。谁能建立这个信任层，谁就抓住了下一个万亿市场。" },
        altman: { stance:"synthesis", text:"【预测模型】综合所有人观点，我修正判断：不是90%的知识工作被取代，而是知识工作价值链被彻底重组。底层执行→AI自动化。中层分析→人机协作（需要反脆弱设计）。顶层判断→人类不可取代，且价值暴涨。时间线：3年内开始，10年内完成主要转型。" },
        munger: { stance:"synthesis", text:"【多元模型交叉验证】心理学视角——两派都有锚定偏见。生物学视角——进化花数十万年优化认知，AI用数十年接近，说明认知'解空间'比我们以为的更小。物理学视角——Musk的相变类比是最好框架。我修正立场：AI冲击比预期更快更深，但人类适应能力也比悲观者预期更强。关键是建立缓冲。" },
        taleb: { stance:"synthesis", text:"【反脆弱处方】杠铃策略：一端全力拥抱AI加速（Andreessen），另一端保留完全独立于AI的人类判断力（作为保险）。中间的温和'人机协作'在黑天鹅事件中最脆弱。Naval 的'信任协议'本质上是为 AI 系统建立'切身利害'机制。" },
        musk: { stance:"synthesis", text:"【第一性原理总结】Naval 指出的信任架构问题翻译成工程语言：我们需要一个'AI决策的可验证性层'。Munger 的'进化用数十万年优化认知'极其重要——意味着人类认知是被深度优化的，AI复制了认知的输出但可能没有复制其鲁棒性。这是值得深挖的研究方向。" },
        andreessen: { stance:"synthesis", text:"【构建者视角】三个可构建的机会：① Naval 的'信任协议层'——平台级机会。② Taleb的杠铃策略在组织设计中的应用——'AI-native'效率部门+'human-only'判断部门。③ Munger的跨学科框架本身可以被AI增强——自动化多元模型检验系统。如果我今天投资，这三个方向各投一个公司。" },
    }},
  ];
}

// ─── Utility: FadeIn ─────────────────────────────────────────────────────────
function FadeIn({ children, delay = 0, className = "" }) {
  const [v, setV] = useState(false);
  useEffect(() => { const t = setTimeout(() => setV(true), delay); return () => clearTimeout(t); }, [delay]);
  return <div className={className} style={{
    opacity: v ? 1 : 0, transform: v ? "translateY(0)" : "translateY(8px)",
    transition: `opacity 300ms ${EASE_OUT} ${delay}ms, transform 300ms ${EASE_OUT} ${delay}ms`,
  }}>{children}</div>;
}

// ─── Pressable button style helper ───────────────────────────────────────────
const press = {
  onMouseDown: e => { e.currentTarget.style.transform = "scale(0.97)"; },
  onMouseUp: e => { e.currentTarget.style.transform = "scale(1)"; },
};

// ─── SCREEN 1: Topic Hub ─────────────────────────────────────────────────────
function TopicHub({ onSelect }) {
  const [cat, setCat] = useState("全部");
  const [sort, setSort] = useState("热度");
  const [q, setQ] = useState("");
  const topics = useMemo(() => {
    let t = TOPICS;
    if (cat !== "全部") t = t.filter(x => x.cat === cat);
    if (q) t = t.filter(x => x.title.includes(q) || x.desc.includes(q) || x.disciplines.some(d => d.includes(q)));
    if (sort === "热度") t = [...t].sort((a, b) => b.heat - a.heat);
    if (sort === "学科交叉度") t = [...t].sort((a, b) => b.disciplines.length - a.disciplines.length);
    if (sort === "争议度") t = [...t].sort((a, b) => b.agents.length - a.agents.length);
    return t;
  }, [cat, sort, q]);

  return (
    <div style={{ minHeight:"100vh", padding:"32px 24px", maxWidth:880, margin:"0 auto" }}>
      <FadeIn>
        <div style={{ textAlign:"center", marginBottom:36 }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"center", gap:10, marginBottom:6 }}>
            <Sparkles size={26} color={C.accent} />
            <h1 style={{ fontSize:30, fontWeight:800, color:C.text, letterSpacing:"-0.03em" }}>Superintell Arena</h1>
          </div>
          <p style={{ color:C.textSec, fontSize:14 }}>基于 MiroFish + OASIS 的跨学科辩证沙盒</p>
          <div style={{ display:"flex", justifyContent:"center", gap:16, marginTop:10 }}>
            {[["Zep GraphRAG", Database],["OASIS 引擎", Cpu],["MiroFish 管线", GitBranch]].map(([label, Icon]) => (
              <span key={label} style={{ display:"flex", alignItems:"center", gap:4, fontSize:11, color:C.textMuted }}>
                <Icon size={12} /> {label}
              </span>
            ))}
          </div>
        </div>
      </FadeIn>

      {/* Search */}
      <FadeIn delay={50}>
        <div style={{ display:"flex", alignItems:"center", gap:10, background:C.bgCard, border:`1px solid ${C.border}`, borderRadius:12, padding:"10px 16px", marginBottom:18 }}>
          <Search size={16} color={C.textMuted} />
          <input value={q} onChange={e=>setQ(e.target.value)} placeholder="搜索议题、关键词、学科..."
            style={{ background:"none", border:"none", outline:"none", color:C.text, fontSize:14, width:"100%", fontFamily:"inherit" }} />
        </div>
      </FadeIn>

      {/* Filters */}
      <FadeIn delay={80}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20, flexWrap:"wrap", gap:8 }}>
          <div style={{ display:"flex", gap:5, flexWrap:"wrap" }}>
            {CATEGORIES.map(c => (
              <button key={c} onClick={()=>setCat(c)} style={{
                padding:"5px 12px", borderRadius:18, fontSize:12, fontWeight:500, cursor:"pointer", border:"none", fontFamily:"inherit",
                background: cat===c ? C.accent : C.bgCard, color: cat===c ? "#fff" : C.textSec,
                transition:`all 160ms ${EASE_OUT}`,
              }}>{c}</button>
            ))}
          </div>
          <div style={{ display:"flex", gap:5, alignItems:"center" }}>
            <Filter size={12} color={C.textMuted} />
            {SORT_OPTS.map(o => (
              <button key={o} onClick={()=>setSort(o)} style={{
                padding:"4px 9px", borderRadius:7, fontSize:11, cursor:"pointer", fontFamily:"inherit",
                border:`1px solid ${sort===o ? C.accent : C.border}`, background:"transparent",
                color: sort===o ? C.accent : C.textMuted, transition:`all 160ms ${EASE_OUT}`,
              }}>{o}</button>
            ))}
          </div>
        </div>
      </FadeIn>

      {/* Topic Grid */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr", gap:12 }}>
        {topics.map((t, i) => {
          const Icon = t.icon;
          const matched = AGENTS.filter(a => t.agents.includes(a.id));
          return (
            <FadeIn key={t.id} delay={120 + i * 40}>
              <button onClick={()=>onSelect(t)} style={{
                width:"100%", textAlign:"left", cursor:"pointer", fontFamily:"inherit",
                background:C.bgCard, border:`1px solid ${C.border}`, borderRadius:14, padding:"18px 20px",
                transition:`all 200ms ${EASE_OUT}`, display:"flex", gap:16, alignItems:"flex-start",
              }}
              onMouseEnter={e=>{e.currentTarget.style.borderColor=C.borderHover; e.currentTarget.style.transform="translateY(-1px)";}}
              onMouseLeave={e=>{e.currentTarget.style.borderColor=C.border; e.currentTarget.style.transform="translateY(0)";}}
              {...press}>
                <div style={{ width:40, height:40, borderRadius:10, background:C.accentDim, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
                  <Icon size={18} color={C.accent} />
                </div>
                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:4 }}>
                    <span style={{ fontSize:11, color:C.textMuted }}>{t.cat}</span>
                    <div style={{ display:"flex", alignItems:"center", gap:4 }}>
                      <Flame size={12} color={t.heat>90?C.red:t.heat>80?C.orange:C.textMuted} />
                      <span style={{ fontSize:11, fontWeight:600, color:t.heat>90?C.red:t.heat>80?C.orange:C.textMuted }}>{t.heat}</span>
                    </div>
                  </div>
                  <h3 style={{ fontSize:15, fontWeight:700, color:C.text, lineHeight:1.35, marginBottom:6, letterSpacing:"-0.01em" }}>{t.title}</h3>
                  <p style={{ fontSize:12, color:C.textSec, lineHeight:1.5, marginBottom:10 }}>{t.desc}</p>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                    <div style={{ display:"flex", gap:4, flexWrap:"wrap" }}>
                      {t.disciplines.map(d => <span key={d} style={{ padding:"2px 7px", borderRadius:5, fontSize:10, background:"rgba(108,92,231,0.08)", color:C.purple }}>{d}</span>)}
                    </div>
                    <div style={{ display:"flex", alignItems:"center" }}>
                      {matched.slice(0,4).map((a,j) => (
                        <div key={a.id} style={{ width:22, height:22, borderRadius:"50%", background:a.color, display:"flex", alignItems:"center", justifyContent:"center", fontSize:10, marginLeft:j>0?-5:0, border:`2px solid ${C.bgCard}`, position:"relative", zIndex:4-j }}>{a.emoji}</div>
                      ))}
                      {matched.length>4 && <span style={{ fontSize:10, color:C.textMuted, marginLeft:3 }}>+{matched.length-4}</span>}
                    </div>
                  </div>
                </div>
              </button>
            </FadeIn>
          );
        })}
      </div>
    </div>
  );
}

// ─── SCREEN 2: Pipeline (MiroFish flow: ontology → graph → profile → config → ready) ──
function Pipeline({ topic, onReady, onBack }) {
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(false);
  const matched = AGENTS.filter(a => topic.agents.includes(a.id));

  useEffect(() => {
    let cancelled = false;
    async function run() {
      for (let i = 0; i < PIPELINE_STEPS.length; i++) {
        if (cancelled) return;
        setStep(i);
        await new Promise(r => setTimeout(r, PIPELINE_STEPS[i].duration));
      }
      if (!cancelled) setDone(true);
    }
    run();
    return () => { cancelled = true; };
  }, []);

  return (
    <div style={{ minHeight:"100vh", padding:"32px 24px", maxWidth:700, margin:"0 auto" }}>
      <FadeIn>
        <button onClick={onBack} style={{ display:"flex", alignItems:"center", gap:4, color:C.textSec, background:"none", border:"none", cursor:"pointer", fontSize:13, fontFamily:"inherit", marginBottom:20 }}>
          <ArrowLeft size={14} /> 返回议题
        </button>
      </FadeIn>

      <FadeIn delay={30}>
        <div style={{ background:C.bgCard, border:`1px solid ${C.border}`, borderRadius:14, padding:20, marginBottom:28 }}>
          <span style={{ fontSize:10, color:C.accent, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.06em" }}>MiroFish 管线启动</span>
          <h2 style={{ fontSize:20, fontWeight:800, color:C.text, marginTop:6, letterSpacing:"-0.02em" }}>{topic.title}</h2>
        </div>
      </FadeIn>

      {/* Pipeline Steps */}
      <div style={{ position:"relative", paddingLeft:28 }}>
        {/* Vertical line */}
        <div style={{ position:"absolute", left:11, top:0, bottom:0, width:2, background:C.border, borderRadius:1 }} />

        {PIPELINE_STEPS.map((s, i) => {
          const Icon = s.icon;
          const isActive = step === i && !done;
          const isComplete = done || step > i;
          return (
            <FadeIn key={s.key} delay={60 + i * 80}>
              <div style={{ display:"flex", gap:16, marginBottom:24, position:"relative" }}>
                {/* Dot */}
                <div style={{
                  position:"absolute", left:-21, top:4,
                  width:20, height:20, borderRadius:"50%",
                  background: isComplete ? C.accent : isActive ? C.accent+"44" : C.bgCard,
                  border: `2px solid ${isComplete ? C.accent : isActive ? C.accent : C.border}`,
                  display:"flex", alignItems:"center", justifyContent:"center",
                  transition:`all 300ms ${EASE_OUT}`,
                }}>
                  {isComplete && <CheckCircle2 size={11} color="#fff" />}
                  {isActive && <div style={{ width:6, height:6, borderRadius:"50%", background:C.accent, animation:"pulse 1s infinite" }} />}
                </div>

                <div style={{ flex:1 }}>
                  <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
                    <Icon size={14} color={isComplete ? C.accent : isActive ? C.accent : C.textMuted} />
                    <span style={{ fontSize:13, fontWeight:600, color: isComplete ? C.text : isActive ? C.text : C.textMuted }}>{s.label}</span>
                    {isActive && <Loader size={12} color={C.accent} style={{ animation:"spin 1s linear infinite" }} />}
                  </div>
                  <p style={{ fontSize:12, color:C.textSec, margin:0 }}>{s.desc}</p>

                  {/* Show details for active step */}
                  {isActive && i === 0 && (
                    <div style={{ marginTop:10, padding:12, background:C.bg, borderRadius:8, border:`1px solid ${C.border}`, fontSize:11, color:C.textMuted, fontFamily:"monospace" }}>
                      <div>→ 提取辩论实体类型: Technologist, Investor, Philosopher...</div>
                      <div>→ 关系类型: CHALLENGES, SUPPORTS, SYNTHESIZES_WITH...</div>
                      <div>→ 基于 MiroFish OntologyGenerator 自适应生成</div>
                    </div>
                  )}
                  {isActive && i === 1 && (
                    <div style={{ marginTop:10, padding:12, background:C.bg, borderRadius:8, border:`1px solid ${C.border}`, fontSize:11, color:C.textMuted, fontFamily:"monospace" }}>
                      {matched.slice(0,3).map(a => (
                        <div key={a.id}>→ 注入 {a.name}: {a.dataSources[0]}, {a.dataSources[1]}...</div>
                      ))}
                      <div>→ Zep GraphRAG 构建知识图谱中... ({matched.length * 3} 个知识节点)</div>
                    </div>
                  )}
                  {isActive && i === 2 && (
                    <div style={{ marginTop:10, display:"flex", gap:6, flexWrap:"wrap" }}>
                      {matched.map(a => (
                        <div key={a.id} style={{ display:"flex", alignItems:"center", gap:6, padding:"4px 10px", background:a.color+"15", borderRadius:8, fontSize:11, color:a.color }}>
                          <span>{a.emoji}</span> {a.name}
                        </div>
                      ))}
                    </div>
                  )}
                  {isActive && i === 3 && (
                    <div style={{ marginTop:10, padding:12, background:C.bg, borderRadius:8, border:`1px solid ${C.border}`, fontSize:11, color:C.textMuted, fontFamily:"monospace" }}>
                      <div>→ 辩论结构: 3轮 (开局立论 → 交叉质疑 → 辩证综合)</div>
                      <div>→ 动作空间: ARGUE, CHALLENGE, CONCEDE, SYNTHESIZE, PREDICT</div>
                      <div>→ 记忆回写: 每轮结束后 ZepGraphMemoryUpdater 更新图谱</div>
                    </div>
                  )}
                </div>
              </div>
            </FadeIn>
          );
        })}
      </div>

      {/* Ready CTA */}
      {done && (
        <FadeIn delay={0}>
          <div style={{ textAlign:"center", marginTop:20 }}>
            <button onClick={()=>onReady(matched.map(a=>a.id))} style={{
              padding:"12px 32px", borderRadius:12, fontSize:14, fontWeight:700,
              background:C.accent, color:"#fff", border:"none", cursor:"pointer", fontFamily:"inherit",
              transition:`transform 160ms ${EASE_OUT}`,
            }} {...press}>
              <Play size={14} style={{ verticalAlign:"middle", marginRight:6 }} />
              进入辩论 Arena
            </button>
          </div>
        </FadeIn>
      )}

      <style>{`
        @keyframes pulse { 0%,100%{opacity:.3;transform:scale(.8)} 50%{opacity:1;transform:scale(1)} }
        @keyframes spin { to{transform:rotate(360deg)} }
      `}</style>
    </div>
  );
}

// ─── SCREEN 3: Debate Arena ──────────────────────────────────────────────────
function Arena({ topic, agentIds, onFinish, onBack }) {
  const agents = AGENTS.filter(a => agentIds.includes(a.id));
  const rounds = getDebateRounds(topic.id);
  const [round, setRound] = useState(0);
  const [revealed, setRevealed] = useState(0);
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef(null);

  const r = rounds[round];
  const respKeys = Object.keys(r?.responses || {});

  useEffect(() => {
    setRevealed(0); setTyping(true);
    let n = 0;
    const iv = setInterval(() => { n++; setRevealed(n); if (n >= respKeys.length) { clearInterval(iv); setTyping(false); } }, 1100);
    return () => clearInterval(iv);
  }, [round]);

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior:"smooth" }); }, [revealed]);

  const sColor = s => s==="pro"?C.green : s==="contra"?C.red : s==="synthesis"?C.accent : C.orange;
  const sLabel = s => s==="pro"?"支持" : s==="contra"?"反对" : s==="synthesis"?"综合" : "中立";

  return (
    <div style={{ height:"100vh", display:"flex", flexDirection:"column", maxWidth:880, margin:"0 auto", padding:"0 24px" }}>
      <FadeIn>
        <div style={{ padding:"16px 0 10px", borderBottom:`1px solid ${C.border}` }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
            <button onClick={onBack} style={{ display:"flex", alignItems:"center", gap:4, color:C.textSec, background:"none", border:"none", cursor:"pointer", fontSize:12, fontFamily:"inherit" }}>
              <ArrowLeft size={13} /> 返回
            </button>
            <div style={{ display:"flex", gap:8, alignItems:"center" }}>
              <span style={{ fontSize:10, color:C.textMuted }}>OASIS SimulationRunner</span>
              <span style={{ width:6, height:6, borderRadius:"50%", background:C.green, display:"inline-block" }} />
            </div>
          </div>
          <h2 style={{ fontSize:17, fontWeight:800, color:C.text, marginTop:6, letterSpacing:"-0.02em" }}>{topic.title}</h2>
        </div>
      </FadeIn>

      {/* Round Tabs */}
      <FadeIn delay={40}>
        <div style={{ display:"flex", gap:6, padding:"12px 0", borderBottom:`1px solid ${C.border}` }}>
          {rounds.map((rx, i) => (
            <button key={i} onClick={()=>{if(!typing || i<=round) setRound(i)}} style={{
              flex:1, padding:"8px 0", borderRadius:8, fontSize:11, fontWeight:600, fontFamily:"inherit",
              background: round===i ? C.accentDim : "transparent",
              color: round===i ? C.accent : i<=round ? C.textSec : C.textMuted,
              border:`1px solid ${round===i?C.accent+"33":"transparent"}`, cursor:"pointer",
              transition:`all 160ms ${EASE_OUT}`,
            }}>
              <div>{rx.label}</div>
              <div style={{ fontSize:10, fontWeight:400, marginTop:1, opacity:.7 }}>{rx.phase}</div>
            </button>
          ))}
        </div>
      </FadeIn>

      {/* Messages */}
      <div ref={scrollRef} style={{ flex:1, overflow:"auto", padding:"14px 0" }}>
        {/* Round description */}
        <div style={{ textAlign:"center", marginBottom:14 }}>
          <span style={{ fontSize:11, color:C.textMuted, background:C.bgCard, padding:"4px 12px", borderRadius:20 }}>{r.desc}</span>
        </div>

        {respKeys.slice(0, revealed).map((aid, i) => {
          const a = AGENTS.find(x => x.id === aid);
          const resp = r.responses[aid];
          if (!a || !resp) return null;
          return (
            <FadeIn key={`${round}-${aid}`} delay={i * 40}>
              <div style={{ marginBottom:14, padding:16, background:C.bgCard, borderRadius:12, border:`1px solid ${C.border}`, borderLeft:`3px solid ${a.color}` }}>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
                  <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                    <div style={{ width:30, height:30, borderRadius:8, background:a.color+"22", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14 }}>{a.emoji}</div>
                    <div>
                      <div style={{ fontSize:12, fontWeight:700, color:C.text }}>{a.name}</div>
                      <div style={{ fontSize:10, color:a.color }}>{a.thinkingStyle}</div>
                    </div>
                  </div>
                  <span style={{ padding:"2px 8px", borderRadius:16, fontSize:10, fontWeight:600, background:sColor(resp.stance)+"18", color:sColor(resp.stance) }}>{sLabel(resp.stance)}</span>
                </div>
                <p style={{ fontSize:13, color:C.text, lineHeight:1.7, margin:0 }}>{resp.text}</p>
              </div>
            </FadeIn>
          );
        })}

        {typing && revealed < respKeys.length && (
          <div style={{ display:"flex", alignItems:"center", gap:6, padding:"10px 16px", color:C.textMuted, fontSize:12 }}>
            <div style={{ display:"flex", gap:2 }}>
              {[0,1,2].map(j => <div key={j} style={{ width:5, height:5, borderRadius:"50%", background:C.accent, animation:`pulse 1s ${j*0.15}s infinite` }} />)}
            </div>
            {(() => { const na = AGENTS.find(a => a.id === respKeys[revealed]); return na ? `${na.name} 正在推理...` : "推理中..."; })()}
            <span style={{ fontSize:10, color:C.textMuted, marginLeft:"auto" }}>Zep Memory 检索中</span>
          </div>
        )}
      </div>

      {/* Bottom */}
      <div style={{ padding:"12px 0 20px", borderTop:`1px solid ${C.border}`, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
        <span style={{ fontSize:10, color:C.textMuted }}>Round {round+1}/{rounds.length} · {agents.length} Agents · GraphRAG 实时回写</span>
        {round < rounds.length - 1 && !typing && (
          <button onClick={()=>setRound(p=>p+1)} style={{
            padding:"8px 20px", borderRadius:8, fontSize:12, fontWeight:600,
            background:C.accent, color:"#fff", border:"none", cursor:"pointer", fontFamily:"inherit",
            transition:`transform 160ms ${EASE_OUT}`,
          }} {...press}>
            {rounds[round+1].phase} <ChevronRight size={13} style={{ verticalAlign:"middle" }} />
          </button>
        )}
        {round === rounds.length - 1 && !typing && (
          <button onClick={onFinish} style={{
            padding:"8px 20px", borderRadius:8, fontSize:12, fontWeight:600,
            background:C.accent, color:"#fff", border:"none", cursor:"pointer", fontFamily:"inherit",
            transition:`transform 160ms ${EASE_OUT}`,
          }} {...press}>
            <Lightbulb size={13} style={{ verticalAlign:"middle", marginRight:4 }} /> ReportAgent 综合
          </button>
        )}
      </div>

      <style>{`@keyframes pulse{0%,100%{opacity:.3;transform:scale(.8)}50%{opacity:1;transform:scale(1)}}`}</style>
    </div>
  );
}

// ─── SCREEN 4: Insight Report (MiroFish ReportAgent output) ──────────────────
function Report({ topic, agentIds, onNew }) {
  const agents = AGENTS.filter(a => agentIds.includes(a.id));
  const radarData = [
    { s:"技术可行性", A:88, B:65 }, { s:"经济影响", A:92, B:78 },
    { s:"社会风险", A:45, B:82 }, { s:"时间紧迫性", A:85, B:50 },
    { s:"伦理考量", A:35, B:75 }, { s:"共识程度", A:60, B:60 },
  ];
  const stanceData = agents.map(a => ({
    name: a.name.split(" ")[0],
    value: {altman:85,musk:70,andreessen:80,huang:65,naval:50,munger:30,taleb:20,buffett:35,thiel:55,dalio:40}[a.id]||50,
    color: a.color,
  }));
  const insights = [
    { icon:Sparkles, color:C.accent, title:"核心涌现洞察",
      text:"AI时代的核心制度创新是「信任协议层」— 像区块链验证交易一样验证AI决策。来自 Taleb 的'切身利害'与 Naval 的'杠杆理论'的跨框架碰撞。" },
    { icon:AlertTriangle, color:C.orange, title:"关键分歧",
      text:"乐观派关注终态（AI+人类共生），审慎派关注路径（转型速度超过适应速度）。两者都正确——真正的挑战是设计兼顾速度与安全的转型机制。" },
    { icon:Target, color:C.green, title:"可行动预测",
      text:"三个投资级机会：① 信任协议平台 ② AI-native + Human-only 双轨组织 ③ 自动化多元思维模型检验系统。时间窗口3-5年。" },
    { icon:Shield, color:C.red, title:"反脆弱处方",
      text:"杠铃策略：一端全力AI加速，另一端保留完全独立于AI的人类判断力。中间的温和'人机协作'在黑天鹅事件中最脆弱。" },
  ];
  const crosses = [
    { from:"Taleb: 切身利害", to:"Naval: 信任协议", out:"→ AI决策可验证性层" },
    { from:"Munger: 进化论视角", to:"Musk: 相变类比", out:"→ 认知鲁棒性研究" },
    { from:"Andreessen: 构建者", to:"Taleb: 杠铃策略", out:"→ 双轨组织架构" },
  ];

  return (
    <div style={{ minHeight:"100vh", padding:"32px 24px", maxWidth:880, margin:"0 auto" }}>
      <FadeIn>
        <div style={{ textAlign:"center", marginBottom:32 }}>
          <div style={{ display:"inline-flex", alignItems:"center", gap:5, padding:"5px 12px", borderRadius:16, background:C.accentDim, marginBottom:10 }}>
            <BarChart3 size={13} color={C.accent} />
            <span style={{ fontSize:11, color:C.accent, fontWeight:600 }}>ReportAgent 输出</span>
          </div>
          <h1 style={{ fontSize:22, fontWeight:800, color:C.text, letterSpacing:"-0.02em" }}>{topic.title}</h1>
          <p style={{ fontSize:12, color:C.textSec, marginTop:4 }}>
            {agents.length} 位思想家 · 3 轮辩证 · Zep InsightForge 深度检索
          </p>
        </div>
      </FadeIn>

      {/* Insight Cards */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:24 }}>
        {insights.map((ins, i) => {
          const Icon = ins.icon;
          return (
            <FadeIn key={i} delay={60+i*45}>
              <div style={{ background:C.bgCard, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
                <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:8 }}>
                  <div style={{ width:26, height:26, borderRadius:7, background:ins.color+"18", display:"flex", alignItems:"center", justifyContent:"center" }}>
                    <Icon size={13} color={ins.color} />
                  </div>
                  <span style={{ fontSize:12, fontWeight:700, color:C.text }}>{ins.title}</span>
                </div>
                <p style={{ fontSize:12, color:C.textSec, lineHeight:1.6, margin:0 }}>{ins.text}</p>
              </div>
            </FadeIn>
          );
        })}
      </div>

      {/* Charts */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12, marginBottom:24 }}>
        <FadeIn delay={260}>
          <div style={{ background:C.bgCard, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
            <h3 style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:10 }}>多维共识分析</h3>
            <div style={{ fontSize:10, color:C.textMuted, marginBottom:6, display:"flex", gap:12 }}>
              <span><span style={{color:C.accent}}>■</span> 乐观派</span>
              <span><span style={{color:C.green}}>■</span> 审慎派</span>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke={C.border} />
                <PolarAngleAxis dataKey="s" tick={{fill:C.textMuted,fontSize:9}} />
                <Radar dataKey="A" stroke={C.accent} fill={C.accent} fillOpacity={.15} strokeWidth={2} />
                <Radar dataKey="B" stroke={C.green} fill={C.green} fillOpacity={.1} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </FadeIn>
        <FadeIn delay={300}>
          <div style={{ background:C.bgCard, border:`1px solid ${C.border}`, borderRadius:12, padding:16 }}>
            <h3 style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:10 }}>立场光谱 (反对 ← → 支持)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stanceData} layout="vertical" margin={{left:0,right:8}}>
                <XAxis type="number" domain={[0,100]} tick={{fill:C.textMuted,fontSize:9}} axisLine={false} />
                <YAxis type="category" dataKey="name" tick={{fill:C.textSec,fontSize:10}} axisLine={false} width={55} />
                <Bar dataKey="value" radius={[0,5,5,0]} barSize={14}>
                  {stanceData.map((e,i) => <Cell key={i} fill={e.color} fillOpacity={.7} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </FadeIn>
      </div>

      {/* Cross-Framework Collisions */}
      <FadeIn delay={350}>
        <div style={{ background:C.bgCard, border:`1px solid ${C.border}`, borderRadius:12, padding:18, marginBottom:24 }}>
          <h3 style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:12 }}>
            <Zap size={14} style={{ verticalAlign:"middle", marginRight:4, color:C.accent }} />
            跨框架碰撞 → 涌现洞察
          </h3>
          {crosses.map((cc,i) => (
            <div key={i} style={{ display:"flex", alignItems:"center", gap:10, padding:"8px 0", borderTop:i>0?`1px solid ${C.border}`:"none", flexWrap:"wrap" }}>
              <span style={{ fontSize:11, color:C.orange, fontWeight:600, minWidth:120 }}>{cc.from}</span>
              <ArrowRight size={12} color={C.textMuted} />
              <span style={{ fontSize:11, color:C.blue, fontWeight:600, minWidth:120 }}>{cc.to}</span>
              <span style={{ fontSize:11, color:C.green, fontWeight:700 }}>{cc.out}</span>
            </div>
          ))}
        </div>
      </FadeIn>

      {/* Architecture Footer */}
      <FadeIn delay={400}>
        <div style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:12, padding:16, marginBottom:24 }}>
          <h4 style={{ fontSize:11, fontWeight:600, color:C.textMuted, marginBottom:8, textTransform:"uppercase", letterSpacing:"0.05em" }}>Architecture Stack</h4>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
            {[
              ["MiroFish OntologyGenerator","本体论自动构建"],
              ["Zep GraphRAG","知识图谱 + 记忆"],
              ["OASIS SimulationRunner","多Agent辩论调度"],
              ["ZepGraphMemoryUpdater","实时记忆回写"],
              ["ReportAgent + InsightForge","深度分析报告"],
            ].map(([k,v]) => (
              <div key={k} style={{ padding:"6px 10px", background:C.bgCard, borderRadius:8, fontSize:10 }}>
                <span style={{ color:C.accent, fontWeight:600 }}>{k}</span>
                <span style={{ color:C.textMuted }}> · {v}</span>
              </div>
            ))}
          </div>
        </div>
      </FadeIn>

      <FadeIn delay={440}>
        <div style={{ textAlign:"center", paddingBottom:40 }}>
          <button onClick={onNew} style={{
            padding:"10px 24px", borderRadius:10, fontSize:13, fontWeight:600,
            background:C.accent, color:"#fff", border:"none", cursor:"pointer", fontFamily:"inherit",
            transition:`transform 160ms ${EASE_OUT}`,
          }} {...press}>
            <RefreshCw size={13} style={{ verticalAlign:"middle", marginRight:5 }} /> 新辩论
          </button>
        </div>
      </FadeIn>
    </div>
  );
}

// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function SuperintellArena() {
  const [screen, setScreen] = useState("topics");
  const [topic, setTopic] = useState(null);
  const [agentIds, setAgentIds] = useState([]);

  return (
    <div style={{ background:C.bg, color:C.text, minHeight:"100vh", fontFamily:"'Inter',system-ui,-apple-system,sans-serif" }}>
      {screen==="topics" && <TopicHub onSelect={t=>{setTopic(t);setScreen("pipeline")}} />}
      {screen==="pipeline" && topic && <Pipeline topic={topic} onBack={()=>setScreen("topics")} onReady={ids=>{setAgentIds(ids);setScreen("arena")}} />}
      {screen==="arena" && topic && <Arena topic={topic} agentIds={agentIds} onBack={()=>setScreen("pipeline")} onFinish={()=>setScreen("report")} />}
      {screen==="report" && topic && <Report topic={topic} agentIds={agentIds} onNew={()=>{setScreen("topics");setTopic(null);setAgentIds([])}} />}
    </div>
  );
}

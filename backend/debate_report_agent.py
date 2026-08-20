"""
DebateReportAgent — extends MiroFish's ReportAgent
for cross-disciplinary debate synthesis instead of social media analysis.

MiroFish original: ReACT pattern + 3 Zep retrieval tools
  (InsightForge, PanoramaSearch, QuickSearch)

Debate version: same ReACT pattern + debate-specific analysis steps:
  - Cross-framework collision detection
  - Emergent insight extraction
  - Stance spectrum analysis
  - Actionable prediction synthesis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json


# ─── Report Data Structures ──────────────────────────────────────────────────

@dataclass
class CrossFrameworkCollision:
    """When two mental models from different domains produce a novel insight."""
    framework_a: str
    framework_b: str
    thinker_a: str
    thinker_b: str
    bridge_concept: str
    emergent_insight: str
    novelty_score: float  # 0-1, how novel vs. restatement
    actionability: float  # 0-1, how actionable


@dataclass
class StancePosition:
    """Agent's position on the spectrum for the debate topic."""
    agent_id: str
    agent_name: str
    stance_score: float    # 0 (strongly against) to 100 (strongly for)
    key_argument: str
    frameworks_used: List[str]
    evolved_during_debate: bool = False
    concessions_made: List[str] = field(default_factory=list)


@dataclass
class PredictionCluster:
    """Grouped predictions from multiple agents."""
    prediction: str
    supporters: List[str]        # agent names who agree
    dissenters: List[str]        # agent names who disagree
    confidence_range: tuple      # (min, max) across agents
    time_horizon: str
    conditions: List[str]
    falsifiable: bool


@dataclass
class InsightCard:
    """A key insight from the debate, ready for display."""
    category: str    # "核心涌现洞察", "关键分歧", "可行动预测", "反脆弱处方"
    title: str
    content: str
    source_agents: List[str]
    confidence: float
    icon: str        # for frontend rendering


@dataclass
class DebateReport:
    """Complete report output. Rendered by the frontend Report screen."""
    topic: str
    agent_count: int
    round_count: int

    # Core analysis
    insights: List[InsightCard]
    stance_spectrum: List[StancePosition]
    cross_collisions: List[CrossFrameworkCollision]
    predictions: List[PredictionCluster]

    # Multi-dimensional consensus analysis (for radar chart)
    consensus_dimensions: Dict[str, Dict[str, float]]
    # e.g. {"技术可行性": {"optimist": 88, "cautious": 65}, ...}

    # Metadata
    retrieval_steps: List[dict]     # ReACT step log
    zep_queries_made: int
    generation_time_ms: int


# ─── Zep Retrieval Tools (same as MiroFish) ──────────────────────────────────

class DebateZepToolsService:
    """
    Wraps MiroFish's ZepToolsService with debate-specific queries.

    Original tools:
    - InsightForge: deep hybrid retrieval with sub-queries
    - PanoramaSearch: breadth search including expired content
    - QuickSearch: fast surface-level search

    Debate additions:
    - CrossFrameworkSearch: find edges between different-domain entities
    - TensionSearch: find CONTRADICTS/CHALLENGES relationships
    """

    def __init__(self, zep_client=None):
        self.zep_client = zep_client

    async def insight_forge(self, query: str, topic: str) -> dict:
        """
        Deep hybrid retrieval with sub-query decomposition.
        MiroFish original: decomposes query into sub-queries,
        searches graph + vector, merges results.
        """
        if not self.zep_client:
            return {"results": [], "sub_queries": [query]}
        # In production: call Zep API
        pass

    async def panorama_search(self, query: str) -> dict:
        """Breadth search across all graph content, including older memories."""
        if not self.zep_client:
            return {"results": []}
        pass

    async def quick_search(self, query: str) -> dict:
        """Fast surface-level search for specific facts."""
        if not self.zep_client:
            return {"results": []}
        pass

    async def cross_framework_search(self, framework_a: str, framework_b: str) -> dict:
        """
        NEW: Search for edges/connections between two frameworks.
        Queries Zep graph for SYNTHESIZES_WITH, CROSS_POLLINATES relationships.
        """
        if not self.zep_client:
            return {"edges": [], "bridge_concepts": []}
        pass

    async def tension_search(self, topic: str) -> dict:
        """
        NEW: Find all CONTRADICTS and CHALLENGES relationships for a topic.
        Returns structured tension map.
        """
        if not self.zep_client:
            return {"tensions": []}
        pass


# ─── ReACT-mode Report Generator ─────────────────────────────────────────────

REPORT_SYSTEM_PROMPT = """You are the DebateReportAgent for Superintell Arena.
Your job: analyze a completed cross-disciplinary debate and produce a synthesis report.

You have access to these tools:
- InsightForge(query): Deep retrieval from Zep knowledge graph
- PanoramaSearch(query): Broad search across all debate memory
- QuickSearch(query): Fast lookup for specific facts
- CrossFrameworkSearch(framework_a, framework_b): Find cross-domain connections
- TensionSearch(topic): Map all contradictions and challenges

Use ReACT pattern:
Thought: [what you need to find out]
Action: [tool name]
Input: [tool input]
Observation: [tool output]
... repeat ...
Final Answer: [structured report JSON]

Your analysis must include:
1. EMERGENT INSIGHTS: Novel ideas that no single agent held alone
2. CROSS-FRAMEWORK COLLISIONS: Where different mental models produced unexpected bridges
3. STANCE SPECTRUM: Where each agent landed and how they evolved
4. PREDICTION CLUSTERS: Grouped predictions with confidence ranges
5. ACTIONABLE TAKEAWAYS: What a decision-maker should do with this
"""


class DebateReportAgent:
    """
    Generates comprehensive debate analysis reports.

    Extends MiroFish's ReportAgent:
    - Same ReACT pattern with tool use
    - Same Zep retrieval backend
    - New analysis types: cross-framework collisions, emergent insights,
      stance spectrum, prediction clusters
    """

    def __init__(self, llm_client=None, zep_tools: Optional[DebateZepToolsService] = None):
        self.llm_client = llm_client
        self.zep_tools = zep_tools or DebateZepToolsService()
        self.step_log: List[dict] = []

    async def generate_report(self, topic: str, rounds: list,
                               agents: list) -> DebateReport:
        """
        Generate a full debate report.

        In production: runs ReACT loop with LLM + Zep tools.
        Demo mode: builds report from pre-computed analysis.
        """
        import time
        start = time.time()

        if self.llm_client:
            report = await self._react_loop(topic, rounds, agents)
        else:
            report = self._build_demo_report(topic, rounds, agents)

        report.generation_time_ms = int((time.time() - start) * 1000)
        return report

    async def _react_loop(self, topic: str, rounds: list, agents: list) -> DebateReport:
        """
        Full ReACT loop for report generation.
        Mirrors MiroFish's ReportAgent._run_react_loop()
        """
        # Step 1: Retrieve cross-framework connections
        self._log_step("Thought", "Need to find cross-framework collisions")
        cross_results = await self.zep_tools.cross_framework_search("*", "*")
        self._log_step("Observation", f"Found {len(cross_results.get('edges', []))} connections")

        # Step 2: Map tensions
        self._log_step("Thought", "Need to map all contradictions and challenges")
        tensions = await self.zep_tools.tension_search(topic)
        self._log_step("Observation", f"Found {len(tensions.get('tensions', []))} tensions")

        # Step 3: Deep insight retrieval
        self._log_step("Thought", "Deep retrieval for emergent insights")
        insights = await self.zep_tools.insight_forge(
            f"What novel insights emerged from the debate on: {topic}?", topic
        )
        self._log_step("Observation", f"Retrieved {len(insights.get('results', []))} insights")

        # Step 4: Synthesize into report via LLM
        self._log_step("Thought", "Synthesizing all findings into structured report")
        # ... LLM synthesis call ...

        return self._build_demo_report(topic, rounds, agents)  # placeholder

    def _build_demo_report(self, topic: str, rounds: list, agents: list) -> DebateReport:
        """Build a demonstration report without LLM/Zep."""
        agent_names = [a.name if hasattr(a, 'name') else str(a) for a in agents]

        insights = [
            InsightCard("核心涌现洞察", "信任协议层",
                "AI时代的核心制度创新是'信任协议层'——像区块链验证交易一样验证AI决策。",
                ["Naval Ravikant", "Nassim Taleb"], 0.85, "sparkles"),
            InsightCard("关键分歧", "终态 vs 路径",
                "乐观派关注终态(AI+人类共生)，审慎派关注路径(转型速度超过适应速度)。",
                ["Sam Altman", "Charlie Munger"], 0.92, "alert"),
            InsightCard("可行动预测", "三个投资级机会",
                "① 信任协议平台 ② 双轨组织架构 ③ 自动化多元模型检验系统",
                ["Marc Andreessen", "Peter Thiel"], 0.78, "target"),
            InsightCard("反脆弱处方", "杠铃策略",
                "一端全力AI加速，另一端保留完全独立于AI的人类判断力。",
                ["Nassim Taleb"], 0.88, "shield"),
        ]

        cross_collisions = [
            CrossFrameworkCollision(
                "切身利害(Skin in the Game)", "杠杆理论",
                "Nassim Taleb", "Naval Ravikant",
                "信任协议", "AI决策可验证性层", 0.9, 0.85),
            CrossFrameworkCollision(
                "进化论视角", "相变类比",
                "Charlie Munger", "Elon Musk",
                "认知鲁棒性", "人类认知深度优化假说", 0.8, 0.6),
            CrossFrameworkCollision(
                "构建者视角", "杠铃策略",
                "Marc Andreessen", "Nassim Taleb",
                "组织设计", "AI-native+Human-only双轨架构", 0.85, 0.9),
        ]

        return DebateReport(
            topic=topic,
            agent_count=len(agents),
            round_count=len(rounds) if rounds else 3,
            insights=insights,
            stance_spectrum=[],  # populated from actual debate data
            cross_collisions=cross_collisions,
            predictions=[],
            consensus_dimensions={
                "技术可行性": {"optimist": 88, "cautious": 65},
                "经济影响": {"optimist": 92, "cautious": 78},
                "社会风险": {"optimist": 45, "cautious": 82},
                "时间紧迫性": {"optimist": 85, "cautious": 50},
                "伦理考量": {"optimist": 35, "cautious": 75},
                "共识程度": {"optimist": 60, "cautious": 60},
            },
            retrieval_steps=self.step_log,
            zep_queries_made=len(self.step_log),
            generation_time_ms=0,
        )

    def _log_step(self, step_type: str, content: str):
        self.step_log.append({"type": step_type, "content": content})

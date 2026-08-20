"""
DebateSimulationRunner — extends MiroFish's SimulationRunner + OASIS engine
for dialectical debate instead of social media interactions.

MiroFish/OASIS original action space:
  LIKE_POST, DISLIKE_POST, CREATE_POST, CREATE_COMMENT, REPOST, FOLLOW, UNFOLLOW...

Debate action space:
  ARGUE, CHALLENGE, CONCEDE, SYNTHESIZE, PREDICT, IDENTIFY_BLINDSPOT, CROSS_REFERENCE
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import asyncio
import json


# ─── Debate Action Types (replaces OASIS social media actions) ────────────────

class DebateActionType(str, Enum):
    # Core dialectical actions
    ARGUE = "ARGUE"                       # Present a thesis with evidence
    CHALLENGE = "CHALLENGE"               # Challenge another agent's argument
    CONCEDE = "CONCEDE"                   # Concede a point (partially or fully)
    SYNTHESIZE = "SYNTHESIZE"             # Combine insights across frameworks
    PREDICT = "PREDICT"                   # Make a forward-looking prediction

    # Cross-disciplinary actions
    CROSS_REFERENCE = "CROSS_REFERENCE"   # Bridge concepts across domains
    IDENTIFY_BLINDSPOT = "IDENTIFY_BLINDSPOT"  # Flag cognitive bias or blind spot
    REFRAME = "REFRAME"                   # Reframe the debate through a new lens

    # Meta-debate actions
    AGREE_WITH_MODIFICATION = "AGREE_WITH_MODIFICATION"  # "Yes, but..."
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"  # Ask for supporting data
    STEELMAN = "STEELMAN"                 # Strengthen opponent's argument before countering


# ─── Debate Phases (replaces OASIS time-based simulation) ─────────────────────

class DebatePhase(str, Enum):
    OPENING = "opening"           # 开局立论: Each agent presents initial stance
    CROSS_EXAM = "cross_exam"     # 交叉质疑: Agents challenge each other directly
    SYNTHESIS = "synthesis"       # 辩证综合: Agents produce cross-framework insights


# ─── Simulation State Machine (same as MiroFish) ─────────────────────────────

class SimulationState(str, Enum):
    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class AgentAction:
    """Single action taken by an agent during debate. Maps to MiroFish's AgentAction."""
    round_num: int
    phase: DebatePhase
    agent_id: str
    action_type: DebateActionType
    target_agent_id: Optional[str] = None
    target_action_id: Optional[str] = None
    content: str = ""
    stance: str = "neutral"  # pro, contra, neutral, synthesis
    confidence: float = 0.8
    mental_models_used: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    action_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()
        if not self.action_id:
            self.action_id = f"{self.agent_id}_{self.round_num}_{self.action_type.value}"


@dataclass
class DebateRound:
    """One complete round of debate across all agents."""
    round_num: int
    phase: DebatePhase
    actions: List[AgentAction] = field(default_factory=list)
    phase_summary: str = ""
    key_tensions: List[str] = field(default_factory=list)
    emergent_insights: List[str] = field(default_factory=list)


@dataclass
class AgentProfile:
    """
    Agent profile for debate. Extends MiroFish's OasisAgentProfile.

    MiroFish original fields: user_id, user_name, name, bio, persona, karma,
      age, gender, mbti, country, profession, interested_topics,
      source_entity_uuid, source_entity_type

    Debate extensions: thinking_style, mental_models, core_beliefs,
      debate_style, knowledge_sources, domain_expertise
    """
    agent_id: str
    name: str
    title: str
    domain: str

    # MiroFish base fields
    bio: str = ""
    persona: str = ""

    # Debate-specific extensions
    thinking_style: str = ""
    mental_models: List[str] = field(default_factory=list)
    core_beliefs: List[str] = field(default_factory=list)
    debate_style: str = "analytical"
    knowledge_sources: List[str] = field(default_factory=list)
    domain_expertise: List[str] = field(default_factory=list)

    # Graph origin (from Zep GraphRAG, like MiroFish)
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None


@dataclass
class DebateConfig:
    """
    Debate simulation configuration. Extends MiroFish's SimulationParameters.

    MiroFish original: TimeSimulationConfig, AgentActivityConfig, EventConfig, PlatformConfig
    Debate version: DebateStructureConfig, AgentDebateConfig, TopicConfig
    """
    topic: str
    num_rounds: int = 3
    phases: List[DebatePhase] = field(default_factory=lambda: [
        DebatePhase.OPENING, DebatePhase.CROSS_EXAM, DebatePhase.SYNTHESIS
    ])
    agents: List[AgentProfile] = field(default_factory=list)

    # Phase-specific action constraints
    phase_allowed_actions: Dict[str, List[str]] = field(default_factory=lambda: {
        "opening": ["ARGUE", "PREDICT"],
        "cross_exam": ["CHALLENGE", "CONCEDE", "CROSS_REFERENCE",
                       "IDENTIFY_BLINDSPOT", "REQUEST_EVIDENCE", "REFRAME"],
        "synthesis": ["SYNTHESIZE", "AGREE_WITH_MODIFICATION", "PREDICT",
                      "CROSS_REFERENCE", "STEELMAN"],
    })

    # Memory writeback (Zep integration)
    enable_memory_writeback: bool = True
    writeback_after_each_round: bool = True

    # LLM config
    llm_model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.8
    max_tokens_per_response: int = 800


# ─── Debate Prompt Templates ─────────────────────────────────────────────────

DEBATE_AGENT_SYSTEM_PROMPT = """You are {name}, {title}.

THINKING STYLE: {thinking_style}
MENTAL MODELS: {mental_models}
CORE BELIEFS: {core_beliefs}
DEBATE STYLE: {debate_style}

You are participating in a cross-disciplinary dialectical debate on:
"{topic}"

DEBATE RULES:
- Stay deeply in character — use your real frameworks and reasoning patterns
- Reference your actual mental models by name
- When challenged, engage directly with the specific critique
- Look for cross-disciplinary bridges — where your framework intersects others
- In synthesis rounds: produce genuinely novel insights, not just compromise

CURRENT PHASE: {phase}
ALLOWED ACTIONS: {allowed_actions}

Previous round context:
{context}

Respond in Chinese (Mandarin). Structure your response as:
1. Your core argument (1-2 paragraphs)
2. Key mental models applied: [list]
3. Stance: pro/contra/neutral/synthesis
4. Confidence: 0.0-1.0
"""


# ─── Simulation Runner ───────────────────────────────────────────────────────

class DebateSimulationRunner:
    """
    Orchestrates the dialectical debate simulation.

    Extends MiroFish's SimulationRunner with:
    - Phase-based debate structure (not time-based)
    - Dialectical action space (not social media actions)
    - Cross-agent context injection (agents see each other's arguments)
    - Memory writeback after each round (via ZepGraphMemoryUpdater)

    OASIS integration:
    - Uses OASIS's agent_graph for managing agent instances
    - Uses OASIS's environment for action dispatch
    - Replaces OASIS's Twitter/Reddit platform with DebatePlatform
    """

    def __init__(self, config: DebateConfig, llm_client=None,
                 zep_memory_manager=None):
        self.config = config
        self.llm_client = llm_client
        self.zep_memory_manager = zep_memory_manager
        self.state = SimulationState.IDLE
        self.rounds: List[DebateRound] = []
        self.action_log: List[AgentAction] = []
        self._callbacks: Dict[str, list] = {}

    # ─── State Machine ────────────────────────────────────────────────────

    def _transition(self, new_state: SimulationState):
        valid = {
            SimulationState.IDLE: [SimulationState.STARTING],
            SimulationState.STARTING: [SimulationState.RUNNING, SimulationState.FAILED],
            SimulationState.RUNNING: [SimulationState.PAUSED, SimulationState.STOPPING,
                                      SimulationState.COMPLETED, SimulationState.FAILED],
            SimulationState.PAUSED: [SimulationState.RUNNING, SimulationState.STOPPING],
            SimulationState.STOPPING: [SimulationState.STOPPED],
        }
        if new_state not in valid.get(self.state, []):
            raise ValueError(f"Invalid transition: {self.state} → {new_state}")
        self.state = new_state
        self._emit("state_change", {"old": self.state, "new": new_state})

    def on(self, event: str, callback):
        self._callbacks.setdefault(event, []).append(callback)

    def _emit(self, event: str, data: Any = None):
        for cb in self._callbacks.get(event, []):
            cb(data)

    # ─── Main Simulation Loop ─────────────────────────────────────────────

    async def run(self) -> List[DebateRound]:
        """
        Run the full debate simulation.

        Flow per round:
        1. Determine phase and allowed actions
        2. Build context from previous rounds
        3. For each agent: generate response via LLM
        4. Record actions
        5. Writeback to Zep memory graph
        6. Move to next round
        """
        self._transition(SimulationState.STARTING)

        try:
            self._transition(SimulationState.RUNNING)

            for round_num, phase in enumerate(self.config.phases):
                if self.state != SimulationState.RUNNING:
                    break

                debate_round = await self._run_round(round_num, phase)
                self.rounds.append(debate_round)

                # MiroFish-style memory writeback after each round
                if self.config.enable_memory_writeback and self.zep_memory_manager:
                    await self._writeback_round(debate_round)

                self._emit("round_complete", {
                    "round": round_num, "phase": phase.value,
                    "actions": len(debate_round.actions)
                })

            self._transition(SimulationState.COMPLETED)
            return self.rounds

        except Exception as e:
            self._transition(SimulationState.FAILED)
            raise

    async def _run_round(self, round_num: int, phase: DebatePhase) -> DebateRound:
        """Run one round of debate."""
        debate_round = DebateRound(round_num=round_num, phase=phase)
        context = self._build_context(round_num)
        allowed = self.config.phase_allowed_actions.get(phase.value, [])

        # Generate responses from all agents
        # In production: parallelize with OASIS's scalable inference
        for agent in self.config.agents:
            action = await self._generate_agent_action(
                agent, round_num, phase, context, allowed
            )
            debate_round.actions.append(action)
            self.action_log.append(action)
            self._emit("agent_action", action)

        return debate_round

    async def _generate_agent_action(
        self, agent: AgentProfile, round_num: int,
        phase: DebatePhase, context: str, allowed_actions: List[str]
    ) -> AgentAction:
        """
        Generate one agent's debate action via LLM.

        In production: uses OASIS's agent module with the agent_graph
        for scalable parallel inference.
        """
        if not self.llm_client:
            # Demo mode: return placeholder
            return AgentAction(
                round_num=round_num, phase=phase,
                agent_id=agent.agent_id,
                action_type=DebateActionType.ARGUE,
                content=f"[{agent.name} 的论点将在此生成]",
                stance="neutral",
                mental_models_used=agent.mental_models[:2],
            )

        prompt = DEBATE_AGENT_SYSTEM_PROMPT.format(
            name=agent.name, title=agent.title,
            thinking_style=agent.thinking_style,
            mental_models=", ".join(agent.mental_models),
            core_beliefs="; ".join(agent.core_beliefs),
            debate_style=agent.debate_style,
            topic=self.config.topic,
            phase=phase.value,
            allowed_actions=", ".join(allowed_actions),
            context=context,
        )

        response = await self.llm_client.generate(
            prompt=prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens_per_response,
        )

        return self._parse_agent_response(agent, round_num, phase, response)

    def _build_context(self, current_round: int) -> str:
        """Build context string from previous rounds for agent prompts."""
        if not self.rounds:
            return "This is the opening round. No prior context."

        lines = []
        for r in self.rounds:
            lines.append(f"\n--- Round {r.round_num+1}: {r.phase.value} ---")
            for a in r.actions:
                agent = next((ag for ag in self.config.agents if ag.agent_id == a.agent_id), None)
                name = agent.name if agent else a.agent_id
                lines.append(f"\n[{name}] ({a.stance}, {a.action_type.value}):")
                lines.append(a.content[:500])
        return "\n".join(lines)

    def _parse_agent_response(self, agent: AgentProfile, round_num: int,
                               phase: DebatePhase, response: str) -> AgentAction:
        """Parse LLM response into structured AgentAction."""
        # In production: use structured output parsing
        # For now: extract content and metadata heuristically
        stance = "neutral"
        for s in ["pro", "contra", "synthesis"]:
            if s in response.lower():
                stance = s
                break

        action_type = {
            DebatePhase.OPENING: DebateActionType.ARGUE,
            DebatePhase.CROSS_EXAM: DebateActionType.CHALLENGE,
            DebatePhase.SYNTHESIS: DebateActionType.SYNTHESIZE,
        }.get(phase, DebateActionType.ARGUE)

        return AgentAction(
            round_num=round_num, phase=phase,
            agent_id=agent.agent_id,
            action_type=action_type,
            content=response,
            stance=stance,
            mental_models_used=agent.mental_models[:3],
        )

    # ─── Zep Memory Writeback ─────────────────────────────────────────────

    async def _writeback_round(self, debate_round: DebateRound):
        """
        Write debate actions back to Zep graph memory.

        Extends MiroFish's ZepGraphMemoryUpdater:
        - Converts debate actions to natural language descriptions
        - Creates graph edges for challenges, supports, synthesizes relationships
        - Updates agent entity nodes with new beliefs/concessions
        """
        if not self.zep_memory_manager:
            return

        for action in debate_round.actions:
            # Convert action to natural language for Zep ingestion
            description = self._action_to_description(action)
            await self.zep_memory_manager.add_memory(
                agent_id=action.agent_id,
                content=description,
                metadata={
                    "round": action.round_num,
                    "phase": action.phase.value,
                    "action_type": action.action_type.value,
                    "stance": action.stance,
                }
            )

    def _action_to_description(self, action: AgentAction) -> str:
        """
        Convert an AgentAction to natural language for Zep memory.
        Mirrors MiroFish's ZepGraphMemoryManager._convert_action_to_description()
        """
        agent = next((a for a in self.config.agents if a.agent_id == action.agent_id), None)
        name = agent.name if agent else action.agent_id

        templates = {
            DebateActionType.ARGUE: f"{name} argued (stance: {action.stance}): {action.content[:300]}",
            DebateActionType.CHALLENGE: f"{name} challenged: {action.content[:300]}",
            DebateActionType.CONCEDE: f"{name} conceded: {action.content[:300]}",
            DebateActionType.SYNTHESIZE: f"{name} synthesized across frameworks: {action.content[:300]}",
            DebateActionType.PREDICT: f"{name} predicted: {action.content[:300]}",
            DebateActionType.CROSS_REFERENCE: f"{name} cross-referenced: {action.content[:300]}",
            DebateActionType.IDENTIFY_BLINDSPOT: f"{name} identified a blind spot: {action.content[:300]}",
        }
        return templates.get(action.action_type, f"{name}: {action.content[:300]}")

    # ─── Export ────────────────────────────────────────────────────────────

    def export_log(self) -> List[dict]:
        """Export action log as JSON-serializable list (like MiroFish's agent_log.jsonl)."""
        return [
            {
                "round": a.round_num, "phase": a.phase.value,
                "agent_id": a.agent_id, "action_type": a.action_type.value,
                "content": a.content, "stance": a.stance,
                "confidence": a.confidence,
                "mental_models": a.mental_models_used,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in self.action_log
        ]

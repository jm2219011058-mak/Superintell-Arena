"""
Debate Mode API Routes
Cross-disciplinary dialectical debate endpoints for Superintell Arena.

Wires up DebateOntologyGenerator, DebateSimulationRunner, and DebateReportAgent
to the Flask backend, following MiroFish route patterns.
"""

import uuid
import asyncio
import threading
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from flask import request, jsonify

from . import debate_bp
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.debate')


# ============== In-Memory Session Store ==============
# Active debate simulations keyed by session_id.
# Each entry holds the runner instance, config, status, and results.

_active_sessions: Dict[str, Dict[str, Any]] = {}


def _get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an active debate session by ID."""
    return _active_sessions.get(session_id)


def _get_or_create_event_loop():
    """Get or create an asyncio event loop for the current thread."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


# ============== Topic Analysis Endpoint ==============

@debate_bp.route('/topic', methods=['POST'])
def analyze_topic():
    """
    Accept a user-submitted debate topic and return structured suggestions.

    Request (JSON):
        {
            "topic": "Will AGI arrive before 2030?",
            "num_thinkers": 5        // optional, default 5
        }

    Returns:
        {
            "success": true,
            "data": {
                "topic": "...",
                "suggested_thinkers": [...],
                "suggested_frameworks": [...],
                "suggested_phases": [...],
                "default_config": {...}
            }
        }
    """
    try:
        data = request.get_json() or {}

        topic = data.get('topic', '').strip()
        if not topic:
            return jsonify({
                "success": False,
                "error": "Debate topic is required"
            }), 400

        num_thinkers = data.get('num_thinkers', 5)

        from ..services.simulation_runner import (
            DebateConfig, DebateAgentProfile, DebatePhase
        )

        # Build default thinker suggestions based on topic keywords
        default_thinkers = [
            DebateAgentProfile(
                agent_id="thinker_charlie_munger",
                name="Charlie Munger",
                title="Vice Chairman of Berkshire Hathaway",
                domain="Investing & Mental Models",
                thinking_style="Multidisciplinary lattice of mental models",
                mental_models=["Inversion", "Circle of Competence",
                               "Margin of Safety", "Lollapalooza Effect"],
                core_beliefs=["Avoid foolishness rather than seeking brilliance",
                              "Mental models from multiple disciplines"],
                debate_style="socratic",
            ),
            DebateAgentProfile(
                agent_id="thinker_nassim_taleb",
                name="Nassim Nicholas Taleb",
                title="Author & Risk Analyst",
                domain="Risk & Probability",
                thinking_style="Anti-fragile reasoning, fat-tail awareness",
                mental_models=["Antifragility", "Skin in the Game",
                               "Black Swan", "Barbell Strategy"],
                core_beliefs=["Fragile systems will break",
                              "Decentralization over centralization"],
                debate_style="aggressive_contrarian",
            ),
            DebateAgentProfile(
                agent_id="thinker_naval_ravikant",
                name="Naval Ravikant",
                title="Angel Investor & Philosopher",
                domain="Technology & Philosophy",
                thinking_style="First-principles, leverage-maximizing",
                mental_models=["Specific Knowledge", "Leverage",
                               "Judgment", "Accountability"],
                core_beliefs=["Technology is leverage for individuals",
                              "Seek wealth, not money"],
                debate_style="analytical",
            ),
            DebateAgentProfile(
                agent_id="thinker_sam_altman",
                name="Sam Altman",
                title="CEO of OpenAI",
                domain="AI & Startups",
                thinking_style="Optimistic builder, exponential thinker",
                mental_models=["Exponential Growth", "Network Effects",
                               "Talent Density", "Mission Alignment"],
                core_beliefs=["AGI will be net positive for humanity",
                              "Build fast, iterate faster"],
                debate_style="visionary",
            ),
            DebateAgentProfile(
                agent_id="thinker_marc_andreessen",
                name="Marc Andreessen",
                title="Co-founder of a16z",
                domain="Technology & Venture Capital",
                thinking_style="Techno-optimist, contrarian builder",
                mental_models=["Software Eating the World",
                               "Network Effects", "Platform Thinking"],
                core_beliefs=["Technology is the primary driver of progress",
                              "Build, don't criticize"],
                debate_style="aggressive_optimist",
            ),
        ]

        suggested_thinkers = default_thinkers[:num_thinkers]

        # Build framework suggestions from ontology defaults
        from ..services.ontology_generator import DEFAULT_DEBATE_ENTITY_TYPES
        suggested_frameworks = [
            {"name": et.name, "description": et.description}
            for et in DEFAULT_DEBATE_ENTITY_TYPES
            if et.name == "Framework"
        ]

        # Default config template
        default_config = {
            "topic": topic,
            "num_rounds": 3,
            "phases": [p.value for p in DebatePhase],
            "llm_model": Config.LLM_MODEL_NAME or "claude-sonnet-4-20250514",
            "temperature": 0.8,
            "max_tokens_per_response": 800,
            "enable_memory_writeback": True,
        }

        return jsonify({
            "success": True,
            "data": {
                "topic": topic,
                "suggested_thinkers": [
                    {
                        "agent_id": t.agent_id,
                        "name": t.name,
                        "title": t.title,
                        "domain": t.domain,
                        "thinking_style": t.thinking_style,
                        "mental_models": t.mental_models,
                        "core_beliefs": t.core_beliefs,
                        "debate_style": t.debate_style,
                    }
                    for t in suggested_thinkers
                ],
                "suggested_frameworks": suggested_frameworks,
                "suggested_phases": [p.value for p in DebatePhase],
                "default_config": default_config,
            }
        })

    except Exception as e:
        logger.error(f"Topic analysis failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Ontology Generation Endpoint ==============

@debate_bp.route('/ontology/generate', methods=['POST'])
def generate_debate_ontology():
    """
    Generate a debate ontology from a topic.

    Request (JSON):
        {
            "topic": "Will AGI arrive before 2030?",
            "use_llm": false   // optional, default false (use defaults for speed)
        }

    Returns:
        {
            "success": true,
            "data": {
                "topic": "...",
                "entity_types": [...],
                "relationship_types": [...],
                "topic_specific_notes": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        topic = data.get('topic', '').strip()
        if not topic:
            return jsonify({
                "success": False,
                "error": "Debate topic is required"
            }), 400

        use_llm = data.get('use_llm', False)

        from ..services.ontology_generator import DebateOntologyGenerator

        # Initialize LLM client if requested
        llm_client = None
        if use_llm:
            from ..utils.llm_client import LLMClient
            try:
                llm_client = LLMClient()
            except Exception as e:
                logger.warning(f"LLM client init failed, falling back to defaults: {e}")
                llm_client = None

        generator = DebateOntologyGenerator(llm_client=llm_client)

        if use_llm and llm_client:
            # Async LLM-based generation
            loop = _get_or_create_event_loop()
            ontology = loop.run_until_complete(generator.generate_ontology(topic))
        else:
            # Fast default ontology
            ontology = generator.generate_default_ontology(topic)

        # Convert to serializable dict
        result = {
            "topic": ontology.topic,
            "entity_types": [
                {
                    "name": et.name,
                    "description": et.description,
                    "properties": et.properties,
                    "is_fallback": et.is_fallback,
                }
                for et in ontology.entity_types
            ],
            "relationship_types": [
                {
                    "name": rt.name,
                    "source_types": rt.source_types,
                    "target_types": rt.target_types,
                    "description": rt.description,
                    "properties": rt.properties,
                }
                for rt in ontology.relationship_types
            ],
            "topic_specific_notes": ontology.topic_specific_notes,
        }

        # Also provide Zep-compatible format
        result["zep_format"] = generator.to_zep_format(ontology)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Debate ontology generation failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Simulation Endpoints ==============

@debate_bp.route('/simulation/start', methods=['POST'])
def start_debate_simulation():
    """
    Start a debate simulation with the given config.

    Request (JSON):
        {
            "topic": "Will AGI arrive before 2030?",
            "agents": [                          // optional, uses defaults if omitted
                {
                    "agent_id": "thinker_xxx",
                    "name": "Charlie Munger",
                    "title": "...",
                    "domain": "...",
                    "thinking_style": "...",
                    "mental_models": [...],
                    "core_beliefs": [...],
                    "debate_style": "socratic"
                }
            ],
            "num_rounds": 3,                     // optional, default 3
            "phases": ["opening", "cross_exam", "synthesis"],  // optional
            "temperature": 0.8,                  // optional
            "max_tokens_per_response": 800,      // optional
            "enable_memory_writeback": true       // optional
        }

    Returns:
        {
            "success": true,
            "data": {
                "session_id": "debate_xxxx",
                "status": "starting",
                "topic": "...",
                "agent_count": 5,
                "num_rounds": 3,
                "phases": [...]
            }
        }
    """
    try:
        data = request.get_json() or {}

        topic = data.get('topic', '').strip()
        if not topic:
            return jsonify({
                "success": False,
                "error": "Debate topic is required"
            }), 400

        from ..services.simulation_runner import (
            DebateConfig, DebateAgentProfile, DebatePhase,
            DebateSimulationRunner
        )

        # Parse agents
        agents_data = data.get('agents', [])
        agents = []
        for ad in agents_data:
            agents.append(DebateAgentProfile(
                agent_id=ad.get('agent_id', f"thinker_{uuid.uuid4().hex[:8]}"),
                name=ad.get('name', 'Unknown Thinker'),
                title=ad.get('title', ''),
                domain=ad.get('domain', ''),
                bio=ad.get('bio', ''),
                persona=ad.get('persona', ''),
                thinking_style=ad.get('thinking_style', ''),
                mental_models=ad.get('mental_models', []),
                core_beliefs=ad.get('core_beliefs', []),
                debate_style=ad.get('debate_style', 'analytical'),
                knowledge_sources=ad.get('knowledge_sources', []),
                domain_expertise=ad.get('domain_expertise', []),
            ))

        # If no agents provided, use defaults from topic endpoint
        if not agents:
            # Provide sensible defaults
            agents = [
                DebateAgentProfile(
                    agent_id="thinker_default_1", name="Analyst Alpha",
                    title="Systems Thinker", domain="Systems Analysis",
                    thinking_style="First-principles analytical",
                    mental_models=["Systems Thinking", "Feedback Loops"],
                    core_beliefs=["Complexity requires structured analysis"],
                    debate_style="analytical",
                ),
                DebateAgentProfile(
                    agent_id="thinker_default_2", name="Contrarian Beta",
                    title="Devil's Advocate", domain="Critical Thinking",
                    thinking_style="Contrarian, stress-testing",
                    mental_models=["Inversion", "Pre-mortem Analysis"],
                    core_beliefs=["Conventional wisdom is often wrong"],
                    debate_style="aggressive_contrarian",
                ),
            ]

        # Parse phases
        phases_raw = data.get('phases', [])
        phases = []
        for p in phases_raw:
            try:
                phases.append(DebatePhase(p))
            except ValueError:
                pass
        if not phases:
            phases = [DebatePhase.OPENING, DebatePhase.CROSS_EXAM,
                      DebatePhase.SYNTHESIS]

        # Build config
        config = DebateConfig(
            topic=topic,
            num_rounds=data.get('num_rounds', 3),
            phases=phases,
            agents=agents,
            enable_memory_writeback=data.get('enable_memory_writeback', True),
            llm_model=data.get('llm_model',
                               Config.LLM_MODEL_NAME or "claude-sonnet-4-20250514"),
            temperature=data.get('temperature', 0.8),
            max_tokens_per_response=data.get('max_tokens_per_response', 800),
        )

        # Initialize LLM client (optional - runs in demo mode without it)
        llm_client = None
        if Config.LLM_API_KEY:
            from ..utils.llm_client import LLMClient
            try:
                llm_client = LLMClient()
            except Exception as e:
                logger.warning(f"LLM client init failed, running in demo mode: {e}")

        # Create runner
        runner = DebateSimulationRunner(
            config=config,
            llm_client=llm_client,
        )

        # Generate session ID
        session_id = f"debate_{uuid.uuid4().hex[:12]}"

        # Store session
        _active_sessions[session_id] = {
            "session_id": session_id,
            "runner": runner,
            "config": config,
            "status": "starting",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None,
            "rounds": [],
            "action_log": [],
        }

        # Run simulation in background thread
        def run_debate():
            session = _active_sessions.get(session_id)
            if not session:
                return

            try:
                session["status"] = "running"
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                rounds = loop.run_until_complete(runner.run())

                session["rounds"] = [
                    {
                        "round_num": r.round_num,
                        "phase": r.phase.value,
                        "actions": [a.to_dict() for a in r.actions],
                        "phase_summary": r.phase_summary,
                        "key_tensions": r.key_tensions,
                        "emergent_insights": r.emergent_insights,
                    }
                    for r in rounds
                ]
                session["action_log"] = runner.export_log()
                session["status"] = "completed"
                session["completed_at"] = datetime.now().isoformat()
                logger.info(f"Debate simulation completed: {session_id}")

            except Exception as e:
                logger.error(f"Debate simulation failed: {session_id}, error={str(e)}")
                session["status"] = "failed"
                session["error"] = str(e)

        thread = threading.Thread(target=run_debate, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "status": "starting",
                "topic": topic,
                "agent_count": len(agents),
                "num_rounds": config.num_rounds,
                "phases": [p.value for p in config.phases],
            }
        })

    except Exception as e:
        logger.error(f"Failed to start debate simulation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@debate_bp.route('/simulation/status/<session_id>', methods=['GET'])
def get_debate_status(session_id: str):
    """
    Get the status and rounds of a debate simulation.

    Returns:
        {
            "success": true,
            "data": {
                "session_id": "debate_xxxx",
                "status": "running|completed|failed",
                "topic": "...",
                "agent_count": 5,
                "current_round": 2,
                "total_rounds": 3,
                "rounds": [...],
                "started_at": "...",
                "completed_at": "...",
                "error": null
            }
        }
    """
    try:
        session = _get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": f"Debate session not found: {session_id}"
            }), 404

        runner = session.get("runner")
        config = session.get("config")

        # Determine current round from runner state
        current_round = len(session.get("rounds", []))
        if runner and hasattr(runner, 'rounds'):
            current_round = len(runner.rounds)

        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "status": session["status"],
                "topic": config.topic if config else "",
                "agent_count": len(config.agents) if config else 0,
                "current_round": current_round,
                "total_rounds": len(config.phases) if config else 0,
                "rounds": session.get("rounds", []),
                "action_log": session.get("action_log", []),
                "started_at": session.get("started_at"),
                "completed_at": session.get("completed_at"),
                "error": session.get("error"),
            }
        })

    except Exception as e:
        logger.error(f"Failed to get debate status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@debate_bp.route('/simulation/stop/<session_id>', methods=['POST'])
def stop_debate_simulation(session_id: str):
    """
    Stop a running debate simulation.

    Returns:
        {
            "success": true,
            "data": {
                "session_id": "debate_xxxx",
                "status": "stopped",
                "rounds_completed": 2
            }
        }
    """
    try:
        session = _get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": f"Debate session not found: {session_id}"
            }), 404

        runner = session.get("runner")
        if not runner:
            return jsonify({
                "success": False,
                "error": "No runner found for this session"
            }), 400

        if session["status"] not in ("starting", "running"):
            return jsonify({
                "success": False,
                "error": f"Cannot stop session in status: {session['status']}"
            }), 400

        # Transition runner to stopping state
        from ..services.simulation_runner import RunnerStatus
        try:
            runner._transition(RunnerStatus.STOPPING)
            runner._transition(RunnerStatus.STOPPED)
        except ValueError:
            # May already be in a terminal state
            pass

        session["status"] = "stopped"
        session["completed_at"] = datetime.now().isoformat()

        # Capture whatever rounds completed so far
        if runner.rounds:
            session["rounds"] = [
                {
                    "round_num": r.round_num,
                    "phase": r.phase.value,
                    "actions": [a.to_dict() for a in r.actions],
                    "phase_summary": r.phase_summary,
                    "key_tensions": r.key_tensions,
                    "emergent_insights": r.emergent_insights,
                }
                for r in runner.rounds
            ]
            session["action_log"] = runner.export_log()

        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "status": "stopped",
                "rounds_completed": len(session.get("rounds", [])),
            }
        })

    except Exception as e:
        logger.error(f"Failed to stop debate simulation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Report Endpoints ==============

@debate_bp.route('/report/generate/<session_id>', methods=['POST'])
def generate_debate_report(session_id: str):
    """
    Generate a debate analysis report for a completed session.

    Request (JSON):
        {
            "force_regenerate": false    // optional
        }

    Returns:
        {
            "success": true,
            "data": {
                "session_id": "debate_xxxx",
                "status": "generating",
                "message": "Report generation started"
            }
        }
    """
    try:
        session = _get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": f"Debate session not found: {session_id}"
            }), 404

        data = request.get_json() or {}
        force_regenerate = data.get('force_regenerate', False)

        # Check if report already exists
        if not force_regenerate and session.get("report"):
            return jsonify({
                "success": True,
                "data": {
                    "session_id": session_id,
                    "status": "completed",
                    "message": "Report already generated",
                    "already_generated": True,
                }
            })

        # Session must be completed or stopped to generate report
        if session["status"] not in ("completed", "stopped"):
            return jsonify({
                "success": False,
                "error": f"Cannot generate report for session in status: {session['status']}. "
                         f"Simulation must be completed or stopped first."
            }), 400

        config = session.get("config")
        runner = session.get("runner")

        # Initialize report agent
        from ..services.report_agent import DebateReportAgent, DebateZepToolsService

        llm_client = None
        if Config.LLM_API_KEY:
            from ..utils.llm_client import LLMClient
            try:
                llm_client = LLMClient()
            except Exception as e:
                logger.warning(f"LLM client init failed for report: {e}")

        zep_tools = None
        if Config.ZEP_API_KEY:
            try:
                zep_tools = DebateZepToolsService()
            except Exception as e:
                logger.warning(f"Zep tools init failed for report: {e}")

        report_agent = DebateReportAgent(
            llm_client=llm_client,
            zep_tools=zep_tools,
        )

        # Mark report as generating
        session["report_status"] = "generating"

        # Generate report in background
        def run_report_generation():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                agents = config.agents if config else []
                rounds = runner.rounds if runner else []

                report = loop.run_until_complete(
                    report_agent.generate_report(
                        topic=config.topic if config else "",
                        rounds=rounds,
                        agents=agents,
                    )
                )

                # Serialize the report
                session["report"] = {
                    "topic": report.topic,
                    "agent_count": report.agent_count,
                    "round_count": report.round_count,
                    "insights": [
                        {
                            "category": i.category,
                            "title": i.title,
                            "content": i.content,
                            "source_agents": i.source_agents,
                            "confidence": i.confidence,
                            "icon": i.icon,
                        }
                        for i in report.insights
                    ],
                    "stance_spectrum": [
                        {
                            "agent_id": s.agent_id,
                            "agent_name": s.agent_name,
                            "stance_score": s.stance_score,
                            "key_argument": s.key_argument,
                            "frameworks_used": s.frameworks_used,
                            "evolved_during_debate": s.evolved_during_debate,
                            "concessions_made": s.concessions_made,
                        }
                        for s in report.stance_spectrum
                    ],
                    "cross_collisions": [
                        {
                            "framework_a": c.framework_a,
                            "framework_b": c.framework_b,
                            "thinker_a": c.thinker_a,
                            "thinker_b": c.thinker_b,
                            "bridge_concept": c.bridge_concept,
                            "emergent_insight": c.emergent_insight,
                            "novelty_score": c.novelty_score,
                            "actionability": c.actionability,
                        }
                        for c in report.cross_collisions
                    ],
                    "predictions": [
                        {
                            "prediction": p.prediction,
                            "supporters": p.supporters,
                            "dissenters": p.dissenters,
                            "confidence_range": list(p.confidence_range),
                            "time_horizon": p.time_horizon,
                            "conditions": p.conditions,
                            "falsifiable": p.falsifiable,
                        }
                        for p in report.predictions
                    ],
                    "consensus_dimensions": report.consensus_dimensions,
                    "retrieval_steps": report.retrieval_steps,
                    "zep_queries_made": report.zep_queries_made,
                    "generation_time_ms": report.generation_time_ms,
                }
                session["report_status"] = "completed"
                logger.info(f"Debate report generated: {session_id}")

            except Exception as e:
                logger.error(f"Debate report generation failed: {session_id}, error={str(e)}")
                session["report_status"] = "failed"
                session["report_error"] = str(e)

        thread = threading.Thread(target=run_report_generation, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "status": "generating",
                "message": "Report generation started",
            }
        })

    except Exception as e:
        logger.error(f"Failed to start report generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@debate_bp.route('/report/<session_id>', methods=['GET'])
def get_debate_report(session_id: str):
    """
    Get the generated debate report for a session.

    Returns:
        {
            "success": true,
            "data": {
                "session_id": "debate_xxxx",
                "report_status": "completed|generating|failed",
                "report": {
                    "topic": "...",
                    "insights": [...],
                    "stance_spectrum": [...],
                    "cross_collisions": [...],
                    "predictions": [...],
                    "consensus_dimensions": {...},
                    ...
                }
            }
        }
    """
    try:
        session = _get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": f"Debate session not found: {session_id}"
            }), 404

        report_status = session.get("report_status", "not_started")
        report = session.get("report")

        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "report_status": report_status,
                "report": report,
                "report_error": session.get("report_error"),
            }
        })

    except Exception as e:
        logger.error(f"Failed to get debate report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

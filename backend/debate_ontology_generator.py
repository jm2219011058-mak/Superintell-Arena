"""
DebateOntologyGenerator — extends MiroFish's OntologyGenerator
for dialectical debate instead of social media simulation.

MiroFish original: generates 10 entity types for social media (Person, Organization, etc.)
This version: generates entity types for intellectual debate (Thinker, Framework, Argument, etc.)
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json


# ─── Ontology Schema ─────────────────────────────────────────────────────────

DEBATE_ONTOLOGY_SYSTEM_PROMPT = """You are an ontology architect for a cross-disciplinary dialectical debate system.

Given a debate topic, design an ontology with exactly 10 entity types and their relationship types.
The ontology must capture the intellectual structure needed for deep dialectical synthesis.

REQUIRED ENTITY TYPES (first 2 are fallback, always present):

1. Thinker — A real-world intellectual figure participating in the debate.
   Properties: name, domain, thinking_style, mental_models[], core_beliefs[], debate_style

2. Framework — A mental model or analytical framework used by thinkers.
   Properties: name, originator, domain, key_principles[], limitations[]

3-10: Design 8 additional entity types specific to the debate topic. These should capture:
   - Arguments (thesis, antithesis, synthesis)
   - Evidence types (empirical, theoretical, historical)
   - Predictions and their confidence levels
   - Cross-disciplinary bridges (where two frameworks collide)
   - Blind spots and cognitive biases identified
   - Emergent insights (novel combinations not in any single thinker's repertoire)
   - Stakes and consequences
   - Action items / investable opportunities

REQUIRED RELATIONSHIP TYPES:
- CHALLENGES: Thinker/Argument challenges another Argument
- SUPPORTS: Thinker/Evidence supports an Argument
- SYNTHESIZES_WITH: Framework combines with another Framework
- CONTRADICTS: Argument contradicts another Argument
- EMERGES_FROM: Insight emerges from collision of multiple Frameworks
- PREDICTS: Thinker/Framework predicts a consequence
- IDENTIFIES_BLINDSPOT: Thinker identifies blindspot in another's Framework
- CONCEDES_TO: Thinker concedes a point to another Thinker
- BUILDS_ON: Argument builds on another Argument
- CROSS_POLLINATES: Framework cross-pollinates with Framework from different domain

Output as JSON with structure:
{
  "entity_types": [...],
  "relationship_types": [...],
  "topic_specific_notes": "..."
}
"""


@dataclass
class EntityType:
    name: str
    description: str
    properties: List[str]
    is_fallback: bool = False


@dataclass
class RelationshipType:
    name: str
    source_types: List[str]
    target_types: List[str]
    description: str
    properties: List[str] = field(default_factory=list)


@dataclass
class DebateOntology:
    topic: str
    entity_types: List[EntityType]
    relationship_types: List[RelationshipType]
    topic_specific_notes: str = ""


# ─── Default Ontology (used when LLM generation is skipped) ──────────────────

DEFAULT_ENTITY_TYPES = [
    EntityType("Thinker", "A real-world intellectual figure",
               ["name","domain","thinking_style","mental_models","core_beliefs","debate_style"], True),
    EntityType("Framework", "A mental model or analytical framework",
               ["name","originator","domain","key_principles","limitations"], True),
    EntityType("Thesis", "A primary argument or position",
               ["claim","confidence","evidence_basis","domain"]),
    EntityType("Antithesis", "A counter-argument challenging a thesis",
               ["claim","target_thesis","attack_vector","strength"]),
    EntityType("Synthesis", "A higher-order integration of thesis and antithesis",
               ["claim","source_theses","novel_insight","cross_domain"]),
    EntityType("Evidence", "Empirical, theoretical, or historical evidence",
               ["type","source","strength","domain","replicability"]),
    EntityType("Prediction", "A forward-looking claim with confidence interval",
               ["claim","time_horizon","confidence","conditions","falsifiable"]),
    EntityType("BlindSpot", "An identified cognitive blind spot or bias",
               ["bias_type","affected_thinker","identified_by","severity"]),
    EntityType("EmergentInsight", "Novel insight from cross-framework collision",
               ["insight","source_frameworks","novelty_score","actionability"]),
    EntityType("Opportunity", "An actionable opportunity identified through debate",
               ["description","domain","time_window","risk_level","identified_by"]),
]

DEFAULT_RELATIONSHIP_TYPES = [
    RelationshipType("CHALLENGES", ["Thinker","Antithesis"], ["Thesis","Framework"],
                     "Directly challenges a position or framework"),
    RelationshipType("SUPPORTS", ["Thinker","Evidence"], ["Thesis","Synthesis"],
                     "Provides support for a position"),
    RelationshipType("SYNTHESIZES_WITH", ["Framework"], ["Framework"],
                     "Combines with another framework to produce synthesis"),
    RelationshipType("CONTRADICTS", ["Thesis","Antithesis"], ["Thesis","Antithesis"],
                     "Directly contradicts another argument"),
    RelationshipType("EMERGES_FROM", ["EmergentInsight","Synthesis"], ["Framework","Thesis"],
                     "Emerges from the collision of multiple inputs"),
    RelationshipType("PREDICTS", ["Thinker","Framework"], ["Prediction"],
                     "Makes a forward-looking prediction"),
    RelationshipType("IDENTIFIES_BLINDSPOT", ["Thinker"], ["BlindSpot"],
                     "Identifies a cognitive blind spot"),
    RelationshipType("CONCEDES_TO", ["Thinker"], ["Thinker"],
                     "Concedes a point during debate", ["conceded_claim","round"]),
    RelationshipType("BUILDS_ON", ["Thesis","Synthesis"], ["Thesis","Synthesis"],
                     "Extends or builds upon a prior argument"),
    RelationshipType("CROSS_POLLINATES", ["Framework"], ["Framework"],
                     "Cross-domain framework fertilization", ["bridge_concept"]),
]


class DebateOntologyGenerator:
    """
    Extends MiroFish's OntologyGenerator for dialectical debate.

    MiroFish original flow:
      topic → LLM(ONTOLOGY_SYSTEM_PROMPT) → 10 entity types for social media

    Debate flow:
      topic → LLM(DEBATE_ONTOLOGY_SYSTEM_PROMPT) → 10 entity types for debate
      OR: use DEFAULT_ENTITY_TYPES for fast startup
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def generate_default_ontology(self, topic: str) -> DebateOntology:
        """Fast path: use pre-defined debate ontology without LLM call."""
        return DebateOntology(
            topic=topic,
            entity_types=DEFAULT_ENTITY_TYPES,
            relationship_types=DEFAULT_RELATIONSHIP_TYPES,
            topic_specific_notes=f"Default ontology for: {topic}"
        )

    async def generate_ontology(self, topic: str) -> DebateOntology:
        """
        Full path: use LLM to generate topic-specific ontology.
        Falls back to default if LLM is unavailable.
        """
        if not self.llm_client:
            return self.generate_default_ontology(topic)

        prompt = f"""Topic for dialectical debate: {topic}

Design an ontology following the schema. The entity types should capture
the specific intellectual dimensions most relevant to this topic."""

        try:
            response = await self.llm_client.generate(
                system=DEBATE_ONTOLOGY_SYSTEM_PROMPT,
                prompt=prompt,
                response_format="json"
            )
            parsed = json.loads(response)
            return self._parse_ontology(topic, parsed)
        except Exception:
            return self.generate_default_ontology(topic)

    def _parse_ontology(self, topic: str, data: dict) -> DebateOntology:
        entity_types = [
            EntityType(
                name=et["name"],
                description=et.get("description", ""),
                properties=et.get("properties", []),
                is_fallback=et.get("is_fallback", False)
            )
            for et in data.get("entity_types", [])
        ]
        relationship_types = [
            RelationshipType(
                name=rt["name"],
                source_types=rt.get("source_types", []),
                target_types=rt.get("target_types", []),
                description=rt.get("description", ""),
                properties=rt.get("properties", [])
            )
            for rt in data.get("relationship_types", [])
        ]
        return DebateOntology(
            topic=topic,
            entity_types=entity_types,
            relationship_types=relationship_types,
            topic_specific_notes=data.get("topic_specific_notes", "")
        )

    def to_zep_format(self, ontology: DebateOntology) -> dict:
        """Convert to Zep GraphRAG ontology format for graph construction."""
        return {
            "entity_types": [
                {"name": et.name, "description": et.description, "properties": et.properties}
                for et in ontology.entity_types
            ],
            "relationship_types": [
                {"name": rt.name, "source_types": rt.source_types,
                 "target_types": rt.target_types, "description": rt.description}
                for rt in ontology.relationship_types
            ]
        }

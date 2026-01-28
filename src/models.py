"""
Pydantic models for data validation and type safety
"""
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class Persona(BaseModel):
    """User persona model"""
    name: str = Field(description="Persona name in Russian")
    name_en: str = Field(description="Persona name in English")
    age: int = Field(ge=1, le=100, description="Age of persona")
    tech_level: Literal["низкий", "средний", "высокий"] = Field(
        description="Technical proficiency level"
    )
    characteristics: List[str] = Field(
        description="List of behavioral characteristics"
    )
    goals: List[str] = Field(
        min_items=1,
        description="Primary goals when using the system"
    )
    pain_points: List[str] = Field(
        description="Common frustration points"
    )
    devices: List[Literal["mobile", "tablet", "desktop"]] = Field(
        min_items=1,
        description="Devices commonly used"
    )
    time_pressure: Literal["низкое", "среднее", "высокое"] = Field(
        description="Time pressure when using the system"
    )
    system_prompt: str = Field(
        min_length=50,
        description="System prompt for LLM to adopt this persona"
    )

    def to_prompt(self) -> str:
        """Convert persona to a prompt for LLM"""
        return self.system_prompt

    def get_detailed_context(self) -> str:
        """Get detailed context about the persona"""
        return f"""
Персона: {self.name}
Возраст: {self.age}
Уровень технической подготовки: {self.tech_level}

Характеристики:
{chr(10).join(f"- {char}" for char in self.characteristics)}

Цели:
{chr(10).join(f"- {goal}" for goal in self.goals)}

Болевые точки:
{chr(10).join(f"- {pain}" for pain in self.pain_points)}

Используемые устройства: {', '.join(self.devices)}
Уровень срочности задач: {self.time_pressure}
"""


class AuditConfig(BaseModel):
    """Configuration for a UX audit session"""
    url: str = Field(description="URL to audit")
    task: str = Field(
        min_length=10,
        description="Task to complete (e.g., 'Find course schedule')"
    )
    persona: str = Field(
        description="Persona key (student, applicant, teacher)"
    )
    max_steps: Optional[int] = Field(
        default=15,
        ge=1,
        le=50,
        description="Maximum steps for behavioral simulation"
    )
    viewport_width: Optional[int] = Field(
        default=1920,
        ge=320,
        description="Browser viewport width"
    )
    viewport_height: Optional[int] = Field(
        default=1080,
        ge=568,
        description="Browser viewport height"
    )

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @validator('persona')
    def validate_persona(cls, v):
        """Validate persona exists"""
        valid_personas = ['student', 'applicant', 'teacher']
        if v not in valid_personas:
            raise ValueError(f'Persona must be one of: {valid_personas}')
        return v


class VisualIssue(BaseModel):
    """Visual issue detected by Module A"""
    title: str = Field(description="Issue title")
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(
        description="Severity level"
    )
    heuristic: str = Field(
        description="Nielsen heuristic violated"
    )
    location: str = Field(
        description="Grid location: single cell (e.g., 'C4') or range (e.g., 'B3-C4', 'A1-D2')"
    )
    description: str = Field(
        description="Detailed description of the issue"
    )
    recommendation: str = Field(
        description="How to fix the issue"
    )
    screenshot_path: Optional[str] = Field(
        default=None,
        description="Path to annotated screenshot"
    )

    @validator('location')
    def validate_location(cls, v):
        """Validate grid location format (e.g., 'C4' or 'B3-C4')"""
        import re
        # Pattern: single cell (A1, B2, C3) or range (A1-B2, C3-D4)
        pattern = r'^[A-Z]\d+(-[A-Z]\d+)?$'
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid location format: '{v}'. Use single cell (e.g., 'C4') or range (e.g., 'B3-C4')"
            )
        return v


class BehaviorStep(BaseModel):
    """Single step in behavioral simulation"""
    step_id: int = Field(ge=1, description="Step number")
    screenshot: str = Field(description="Screenshot filename")
    dom_snapshot: str = Field(description="Simplified DOM snapshot")
    agent_thought: str = Field(
        description="Agent's reasoning about current state"
    )
    action_taken: str = Field(
        description="Action performed (click, scroll, type, etc.)"
    )
    status: Literal["success", "failure", "blocked"] = Field(
        description="Action execution status"
    )
    url: str = Field(description="Current page URL")
    sentiment: Optional[Literal["POSITIVE", "NEUTRAL", "NEGATIVE"]] = Field(
        default=None,
        description="Sentiment of agent thought"
    )


class AccessibilityIssue(BaseModel):
    """Accessibility issue from Module C"""
    id: str = Field(description="Issue ID from axe-core")
    impact: Literal["minor", "moderate", "serious", "critical"] = Field(
        description="Impact level"
    )
    description: str = Field(description="Issue description")
    help: str = Field(description="How to fix")
    help_url: str = Field(description="Documentation URL")
    tags: List[str] = Field(description="WCAG tags")
    nodes: List[Dict[str, Any]] = Field(
        description="Affected DOM nodes"
    )


class AuditReport(BaseModel):
    """Final audit report from Module E"""
    session_id: str = Field(description="Audit session ID")
    url: str = Field(description="Audited URL")
    persona: str = Field(description="Persona used")
    overall_score: int = Field(
        ge=0,
        le=100,
        description="Overall UX score (0-100)"
    )
    visual_issues: List[VisualIssue] = Field(
        default_factory=list,
        description="Issues from Module A"
    )
    behavior_log: List[BehaviorStep] = Field(
        default_factory=list,
        description="Steps from Module B"
    )
    accessibility_issues: List[AccessibilityIssue] = Field(
        default_factory=list,
        description="Issues from Module C"
    )
    critical_issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Cross-module critical issues"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Prioritized recommendations"
    )
    generated_at: str = Field(description="Report generation timestamp")


def get_persona_model(persona_key: str, personas_dict: Dict[str, Dict]) -> Persona:
    """
    Convert personas dictionary to validated Pydantic model

    Args:
        persona_key: Key like 'student', 'applicant', 'teacher'
        personas_dict: Dictionary of personas from config

    Returns:
        Validated Persona model
    """
    if persona_key not in personas_dict:
        raise ValueError(f"Persona '{persona_key}' not found")

    persona_data = personas_dict[persona_key]
    return Persona(**persona_data)


if __name__ == "__main__":
    # Test persona model
    from src.config import PERSONAS

    print("Testing Persona models...\n")

    for key in ["student", "applicant", "teacher"]:
        persona = get_persona_model(key, PERSONAS)
        print(f"✓ {persona.name} validated successfully")
        print(persona.get_detailed_context())
        print("-" * 60)

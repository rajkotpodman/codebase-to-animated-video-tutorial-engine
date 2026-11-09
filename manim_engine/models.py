"""Data models and schemas for structured architecture diagrams."""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    """Categorization of architectural components."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    QUEUE = "queue"
    CACHE = "cache"
    GATEWAY = "gateway"
    STORAGE = "storage"
    AUTH = "auth"
    SERVICE = "service"
    CLIENT = "client"


class NodeModel(BaseModel):
    """Architectural component node definition."""

    id: str = Field(..., description="Unique alphanumeric identifier for the component")
    label: str = Field(..., description="Display title for the node, e.g. 'API Gateway'")
    kind: NodeType = Field(default=NodeType.BACKEND, description="Component archetype")
    tech: Optional[str] = Field(default=None, description="Technology stack subtitle, e.g. 'FastAPI', 'PostgreSQL'")
    layer: Optional[int] = Field(
        default=None, description="Horizontal/Vertical tier layer index (0=Client, 1=Gateway, 2=Backend, etc.)"
    )
    position: Optional[List[float]] = Field(default=None, description="Explicit [x, y, z] coordinates in Manim units")
    color: Optional[str] = Field(default=None, description="Custom primary hex color code, e.g. '#3B82F6'")
    badge: Optional[str] = Field(default=None, description="Optional badge text, e.g. 'Primary', 'v2', 'Cluster'")
    details: Optional[List[str]] = Field(
        default=None, description="Key features or responsibilities listed on the card"
    )

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None and len(v) not in (2, 3):
            raise ValueError("Position must be a 2D or 3D coordinate list [x, y] or [x, y, z]")
        if v is not None and len(v) == 2:
            return [v[0], v[1], 0.0]
        return v


class ConnectionModel(BaseModel):
    """Data flow connection or network relation between nodes."""

    id: Optional[str] = Field(default=None, description="Optional connection identifier")
    source_id: str = Field(..., description="ID of origin node")
    target_id: str = Field(..., description="ID of destination node")
    label: Optional[str] = Field(default=None, description="Edge annotation label, e.g. 'HTTPS /ingest'")
    protocol: Optional[str] = Field(
        default=None, description="Network protocol badge, e.g. 'REST', 'gRPC', 'SQL', 'WSS'"
    )
    bidirectional: bool = Field(default=False, description="Whether data flows back and forth")
    animated: bool = Field(default=True, description="Whether to render animated flowing data packets")
    curvature: float = Field(default=0.0, description="Curvature angle for curved arrow paths (-1.0 to 1.0)")
    color: Optional[str] = Field(default=None, description="Custom line color hex code")
    packet_color: Optional[str] = Field(default="#00FFA3", description="Hex color of the animated data packets")
    packet_speed: float = Field(default=1.0, description="Relative speed multiplier for packet animation")
    packet_count: int = Field(default=2, description="Number of packets traversing the connection")


class SceneConfig(BaseModel):
    """Rendering configuration and styling for the Manim scene."""

    title: str = Field(default="System Architecture & Code Flow", description="Main header text")
    subtitle: Optional[str] = Field(default="Interactive Component Topology", description="Subheader caption")
    theme: Literal["midnight", "dark", "cyberpunk", "nord", "clean_white"] = Field(
        default="midnight",
        description="Color palette theme for background and UI elements",
    )
    background_color: str = Field(default="#0A0E17", description="Background hex color")
    duration_per_flow: float = Field(default=2.5, description="Seconds spent animating each connection data pulse")
    intro_duration: float = Field(default=1.5, description="Intro sequence duration in seconds")
    outro_duration: float = Field(default=1.5, description="Outro sequence hold duration in seconds")
    show_grid: bool = Field(default=False, description="Whether to render coordinate grid guides for debugging")
    camera_zoom: float = Field(default=1.0, description="Camera zoom level")


class ArchitectureDiagramData(BaseModel):
    """Complete root payload for generating a dynamic Manim architecture animation."""

    config: SceneConfig = Field(default_factory=SceneConfig)
    nodes: List[NodeModel] = Field(default_factory=list)
    connections: List[ConnectionModel] = Field(default_factory=list)

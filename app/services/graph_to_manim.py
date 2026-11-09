"""Manim Flowchart Mapping & Scene Generation Utility.

Translates AST-extracted codebase graphs from graph_service.py into coordinate-based
Manim architecture models, positioning boxes, curved dependency arrows, and flowing
data packet animations.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from app.services.graph_service import CodebaseGraph, GraphEdge, GraphNode
from manim_engine.models import (
    ArchitectureDiagramData,
    ConnectionModel,
    NodeModel,
    NodeType,
    SceneConfig,
)
from manim_engine.base_template import THEME_PALETTES, NODE_TYPE_STYLES, ManimRenderService

logger = logging.getLogger("graph_to_manim")


# -----------------------------------------------------------------------------
# Flowchart Layout Configuration
# -----------------------------------------------------------------------------

DEFAULT_CANVAS_BOUNDS = {
    "x_min": -5.2,
    "x_max": 5.2,
    "y_top": 2.0,
    "y_bottom": -2.6,
    "card_width": 2.2,
    "card_height": 1.4,
}


# -----------------------------------------------------------------------------
# Graph to Manim Mapper
# -----------------------------------------------------------------------------


class GraphToManimMapper:
    """Translates CodebaseGraph models into coordinate-anchored Manim architecture diagrams."""

    def __init__(
        self,
        theme: Literal["midnight", "dark", "cyberpunk", "nord"] = "midnight",
        canvas_bounds: Optional[Dict[str, float]] = None,
    ) -> None:
        self.theme_name = theme if theme in THEME_PALETTES else "midnight"
        self.theme = THEME_PALETTES[self.theme_name]
        self.bounds = canvas_bounds or DEFAULT_CANVAS_BOUNDS

    def map_to_architecture_data(
        self,
        graph_input: Union[CodebaseGraph, Dict[str, Any], str, Path],
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> ArchitectureDiagramData:
        """Map CodebaseGraph into an ArchitectureDiagramData payload with explicit coordinates.

        Args:
            graph_input: CodebaseGraph instance, dictionary, JSON string, or JSON file path
            title: Optional custom scene title
            subtitle: Optional custom scene subtitle

        Returns:
            ArchitectureDiagramData with calculated positions, styled nodes, and curved edges.
        """
        graph = self._coerce_codebase_graph(graph_input)

        # 1. Group nodes by horizontal architectural layers (0=Client to 4=Database)
        layers_map: Dict[int, List[GraphNode]] = {}
        for node in graph.nodes:
            layers_map.setdefault(node.layer, []).append(node)

        # 2. Compute non-overlapping 2D coordinates for each node
        node_positions = self._compute_layer_coordinates(layers_map)

        # 3. Create Manim NodeModels
        manim_nodes: List[NodeModel] = []
        node_id_set = {n.id for n in graph.nodes}

        for gn in graph.nodes:
            style = NODE_TYPE_STYLES.get(gn.kind, NODE_TYPE_STYLES[NodeType.BACKEND])
            pos = node_positions.get(gn.id, [0.0, 0.0, 0.0])

            # Details list highlighting classes/methods
            details = list(gn.details[:2]) if gn.details else []
            if not details and gn.classes:
                details.append(f"Class: {gn.classes[0]}")
            if not details and gn.functions:
                details.append(f"Def: {gn.functions[0]}()")

            node_model = NodeModel(
                id=gn.id,
                label=gn.label,
                kind=gn.kind,
                tech=gn.tech or gn.language.capitalize(),
                layer=gn.layer,
                position=pos,
                color=style["primary_color"],
                badge=style["icon_symbol"],
                details=details,
            )
            manim_nodes.append(node_model)

        # 4. Map edges to curved / animated ConnectionModels
        manim_connections: List[ConnectionModel] = []
        for edge in graph.edges:
            # Only connect nodes present in the active set
            if edge.source_id in node_id_set and edge.target_id in node_id_set:
                src_pos = node_positions.get(edge.source_id, [0.0, 0.0, 0.0])
                tgt_pos = node_positions.get(edge.target_id, [0.0, 0.0, 0.0])

                # Determine trajectory curvature to avoid cutting through intermediate cards
                curvature = self._calculate_edge_curvature(src_pos, tgt_pos)

                # Packet color based on source layer
                src_node = next((n for n in graph.nodes if n.id == edge.source_id), None)
                packet_col = self._get_packet_color(src_node)

                label_text = edge.symbols[0] if edge.symbols else edge.label
                conn_model = ConnectionModel(
                    id=edge.id,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    label=label_text,
                    protocol=edge.protocol,
                    curvature=curvature,
                    color=self.theme["arrow_color"],
                    packet_color=packet_col,
                    animated=True,
                    packet_speed=1.0,
                )
                manim_connections.append(conn_model)

        # 5. Build final SceneConfig
        scene_title = title or f"{graph.repo_name} Codebase Graph"
        scene_subtitle = (
            subtitle
            or f"AST Architecture Flow ({graph.total_files} Modules, {len(manim_connections)} Dependencies)"
        )

        return ArchitectureDiagramData(
            config=SceneConfig(
                title=scene_title,
                subtitle=scene_subtitle,
                theme=self.theme_name,
                background_color=self.theme["background"],
                duration_per_flow=2.5,
                intro_duration=1.5,
                outro_duration=2.0,
            ),
            nodes=manim_nodes,
            connections=manim_connections,
        )

    # -------------------------------------------------------------------------
    # Coordinate Calculation Algorithms
    # -------------------------------------------------------------------------

    def _compute_layer_coordinates(
        self, layers_map: Dict[int, List[GraphNode]]
    ) -> Dict[str, List[float]]:
        """Distribute nodes across balanced columns and staggered vertical rows."""
        positions: Dict[str, List[float]] = {}
        active_layers = sorted(layers_map.keys())
        total_layers = len(active_layers)

        x_min = self.bounds["x_min"]
        x_max = self.bounds["x_max"]
        y_top = self.bounds["y_top"]
        y_bottom = self.bounds["y_bottom"]

        # Calculate horizontal step per active layer
        x_step = (x_max - x_min) / max(1, total_layers - 1) if total_layers > 1 else 0.0

        for col_idx, layer_key in enumerate(active_layers):
            nodes_in_col = layers_map[layer_key]
            x_coord = x_min + (col_idx * x_step) if total_layers > 1 else 0.0
            count = len(nodes_in_col)

            # Available vertical span
            y_span = abs(y_top - y_bottom)
            y_spacing = min(1.8, y_span / max(1, count)) if count > 1 else 0.0
            # Center the vertical stack around Y = -0.2 (compensating for top header)
            start_y = ((count - 1) * y_spacing / 2.0) - 0.2 if count > 1 else -0.2

            for row_idx, node in enumerate(nodes_in_col):
                y_coord = start_y - (row_idx * y_spacing) if count > 1 else -0.2
                positions[node.id] = [round(x_coord, 2), round(y_coord, 2), 0.0]

        return positions

    @staticmethod
    def _calculate_edge_curvature(src_pos: List[float], tgt_pos: List[float]) -> float:
        """Calculate curve angle for arrows to prevent cutting across intermediate cards."""
        delta_x = tgt_pos[0] - src_pos[0]
        delta_y = tgt_pos[1] - src_pos[1]

        # 1. Backwards dependency (loops from right to left)
        if delta_x < -0.5:
            # Curve around top or bottom depending on vertical position
            return -0.45 if src_pos[1] >= 0 else 0.45

        # 2. Multi-column leap (skips across at least one intermediate column)
        if delta_x > 3.0:
            return 0.35 if delta_y >= 0 else -0.35

        # 3. Same column connection (vertical dependency)
        if abs(delta_x) < 0.3:
            return 0.40

        # Direct adjacent column: straight arrow
        return 0.0

    @staticmethod
    def _get_packet_color(node: Optional[GraphNode]) -> str:
        """Choose animated packet glow color based on node kind."""
        if not node:
            return "#00FFA3"
        kind_colors = {
            NodeType.FRONTEND: "#38BDF8",  # Cyan
            NodeType.CLIENT: "#38BDF8",
            NodeType.GATEWAY: "#A855F7",   # Purple
            NodeType.BACKEND: "#6366F1",   # Indigo
            NodeType.SERVICE: "#4ADE80",   # Lime Green
            NodeType.QUEUE: "#F59E0B",     # Amber
            NodeType.CACHE: "#F43F5E",     # Rose
            NodeType.DATABASE: "#10B981",  # Emerald
            NodeType.STORAGE: "#10B981",
        }
        return kind_colors.get(node.kind, "#00FFA3")

    # -------------------------------------------------------------------------
    # Input Coercion Helper
    # -------------------------------------------------------------------------

    @staticmethod
    def _coerce_codebase_graph(input_data: Union[CodebaseGraph, Dict[str, Any], str, Path]) -> CodebaseGraph:
        """Ensure input is converted into a validated CodebaseGraph instance."""
        if isinstance(input_data, CodebaseGraph):
            return input_data

        if isinstance(input_data, dict):
            return CodebaseGraph.model_validate(input_data)

        if isinstance(input_data, (str, Path)) and os.path.exists(str(input_data)):
            raw_text = Path(input_data).read_text(encoding="utf-8")
            parsed = json.loads(raw_text)
            return CodebaseGraph.model_validate(parsed)

        if isinstance(input_data, str):
            parsed = json.loads(input_data)
            return CodebaseGraph.model_validate(parsed)

        raise ValueError(f"Unsupported graph input format: {type(input_data)}")


# -----------------------------------------------------------------------------
# Manim Community Flowchart Scene Code Generator
# -----------------------------------------------------------------------------


def generate_manim_flowchart_scene_code(
    graph_input: Union[CodebaseGraph, Dict[str, Any], str, Path],
    scene_name: str = "CodebaseGraphFlowScene",
    theme: Literal["midnight", "dark", "cyberpunk", "nord"] = "midnight",
    target_duration: Optional[float] = None,
) -> str:
    """Generate complete, standalone Manim Community v0.18+ Python script.

    Args:
        graph_input: CodebaseGraph, dictionary, or JSON file path
        scene_name: Class name for the generated Manim Scene
        theme: Color palette theme
        target_duration: Optional target audio runtime to scale the hold sequence dynamically

    Returns:
        Complete Python script string ready for compilation with `manim`.
    """
    mapper = GraphToManimMapper(theme=theme)
    arch_data = mapper.map_to_architecture_data(graph_input)
    theme_palette = THEME_PALETTES.get(theme, THEME_PALETTES["midnight"])

    # Calculate outro hold duration to match target audio duration dynamically
    conn_count = len([c for c in arch_data.connections if c.animated])
    base_duration = 1.5 + 0.5 + 2.2 + 0.8 + 2.0 + 1.2 + (conn_count * 4.0)
    if target_duration and target_duration > base_duration:
        outro_hold = round(target_duration - base_duration, 1)
    else:
        outro_hold = 6.0

    # Prepare node representations
    nodes_code_list = []
    for n in arch_data.nodes:
        nodes_code_list.append(
            f"            '{n.id}': {{\n"
            f"                'label': '{n.label}',\n"
            f"                'tech': '{n.tech or ''}',\n"
            f"                'pos': {n.position},\n"
            f"                'color': '{n.color}',\n"
            f"                'badge': '{n.badge or ''}',\n"
            f"                'details': {n.details},\n"
            f"            }},"
        )
    nodes_repr = "{\n" + "\n".join(nodes_code_list) + "\n        }"

    # Prepare connection representations
    conn_code_list = []
    for c in arch_data.connections:
        conn_code_list.append(
            f"            {{\n"
            f"                'source_id': '{c.source_id}',\n"
            f"                'target_id': '{c.target_id}',\n"
            f"                'label': '{c.label or ''}',\n"
            f"                'protocol': '{c.protocol or 'IMPORT'}',\n"
            f"                'curvature': {c.curvature},\n"
            f"                'color': '{c.color or theme_palette['arrow_color']}',\n"
            f"                'packet_color': '{c.packet_color}',\n"
            f"            }},"
        )
    conns_repr = "[\n" + "\n".join(conn_code_list) + "\n        ]"

    script = f'''"""Interactive Codebase Architecture Flowchart Scene."""

from manim import *

class {scene_name}(Scene):
    def construct(self):
        # 1. Environment & Background
        self.camera.background_color = "{theme_palette['background']}"

        # 2. Scene Header & Metadata
        title_text = "{arch_data.config.title}"
        subtitle_text = "{arch_data.config.subtitle}"

        title = Text(title_text, font_size=28, color="{theme_palette['title_color']}", weight=BOLD)
        subtitle = Text(subtitle_text, font_size=15, color="{theme_palette['subtitle_color']}")
        header = VGroup(title, subtitle).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header.to_corner(UL, buff=0.6)

        self.play(FadeIn(header, shift=DOWN * 0.3), run_time=1.5)
        self.wait(0.5)

        # 3. Node Definitions
        nodes_dict = {nodes_repr}

        # 4. Construct Node Cards
        node_mobjects = {{}}
        node_groups = []

        for node_id, info in nodes_dict.items():
            pos = info['pos']
            col = info['color']
            bg_col = "{theme_palette['card_bg']}"

            card = RoundedRectangle(
                corner_radius=0.15,
                width=2.2,
                height=1.35,
                color=col,
                stroke_width=2.5,
                fill_color=bg_col,
                fill_opacity=0.92
            )
            card.move_to(pos)

            txt_title = Text(info['label'], font_size=14, color="{theme_palette['text_primary']}", weight=SEMIBOLD)
            txt_title.move_to(card.get_top() + DOWN * 0.35)

            txt_tech = Text(info['tech'], font_size=11, color=col)
            txt_tech.next_to(txt_title, DOWN, buff=0.1)

            card_elements = [card, txt_title, txt_tech]
            if info['details']:
                detail_txt = Text(info['details'][0], font_size=10, color="{theme_palette['text_secondary']}")
                detail_txt.next_to(txt_tech, DOWN, buff=0.1)
                card_elements.append(detail_txt)

            card_group = VGroup(*card_elements)
            node_mobjects[node_id] = card_group
            node_groups.append(card_group)

        # Staggered entrance animation for node cards
        if node_groups:
            self.play(
                LaggedStart(*[FadeIn(mob, shift=UP * 0.3) for mob in node_groups], lag_ratio=0.15),
                run_time=2.5
            )
            self.wait(1.0)

        # 5. Connect Dependencies with Directed & Curved Arrows
        connections_data = {conns_repr}
        arrows = []
        labels = []

        for conn in connections_data:
            src_id = conn['source_id']
            tgt_id = conn['target_id']

            if src_id in node_mobjects and tgt_id in node_mobjects:
                src_mob = node_mobjects[src_id]
                tgt_mob = node_mobjects[tgt_id]
                curv = conn['curvature']
                arr_col = conn['color']

                if curv != 0.0:
                    arr = CurvedArrow(
                        src_mob.get_right() if curv >= 0 else src_mob.get_bottom(),
                        tgt_mob.get_left() if curv >= 0 else tgt_mob.get_bottom(),
                        angle=curv,
                        color=arr_col,
                        stroke_width=2.2
                    )
                else:
                    arr = Arrow(
                        src_mob.get_right(),
                        tgt_mob.get_left(),
                        buff=0.12,
                        color=arr_col,
                        stroke_width=2.5,
                        max_tip_length_to_length_ratio=0.18
                    )

                lbl_mob = None
                if conn['label']:
                    lbl_mob = Text(conn['label'][:20], font_size=10, color=arr_col)
                    lbl_mob.next_to(arr.get_center(), UP, buff=0.08)
                    labels.append(lbl_mob)

                arrows.append((arr, conn))

        # Render arrows appearing
        if arrows:
            arrow_mobs = [a[0] for a in arrows]
            self.play(
                LaggedStart(*[Create(a) for a in arrow_mobs], lag_ratio=0.12),
                *[FadeIn(l) for l in labels],
                run_time=2.0
            )
            self.wait(1.2)

            # Animate flowing data packets along dependencies
            packet_dots = []
            for arr, conn in arrows:
                pkt = Dot(radius=0.08, color=conn['packet_color'])
                pkt.move_to(arr.get_start())
                packet_dots.append((pkt, arr))

            if packet_dots:
                self.play(*[FadeIn(p[0]) for p in packet_dots], run_time=0.4)
                self.play(
                    *[MoveAlongPath(p[0], p[1]) for p in packet_dots],
                    run_time=3.2,
                    rate_func=linear
                )
                self.play(*[FadeOut(p[0]) for p in packet_dots], run_time=0.4)

        # 6. Outro Hold Sequence (Keeps visual elements on screen - prevents black screen)
        self.wait({outro_hold})
'''
    return script


# -----------------------------------------------------------------------------
# Direct Rendering Helper
# -----------------------------------------------------------------------------


def render_graph_flowchart(
    graph_input: Union[CodebaseGraph, Dict[str, Any], str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    quality: Literal["l", "m", "h", "k"] = "h",
    fps: int = 30,
    theme: Literal["midnight", "dark", "cyberpunk", "nord"] = "midnight",
) -> Path:
    """Convenience function to translate a graph and render the resulting Manim flowchart to MP4.

    Args:
        graph_input: CodebaseGraph, dictionary, or JSON file path
        output_dir: Directory where the MP4 video should be saved
        quality: Video render quality ('l', 'm', 'h', 'k')
        fps: Framerate for rendering (default 30)
        theme: Visual palette theme

    Returns:
        Path to the rendered MP4 file.
    """
    code = generate_manim_flowchart_scene_code(graph_input, theme=theme)
    render_service = ManimRenderService()
    return render_service.render(
        input_data=code,
        output_dir=output_dir,
        quality=quality,
        fps=fps,
    )


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------


def main() -> None:
    """CLI runner to convert a codebase graph JSON into a Manim scene script or video."""
    parser = argparse.ArgumentParser(description="Map CodebaseGraph to Manim Flowchart Scene")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to codebase graph JSON file")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output Python script path")
    parser.add_argument("--render", "-r", action="store_true", help="Compile and render to MP4 video")
    parser.add_argument("--quality", "-q", choices=["l", "m", "h", "k"], default="h", help="Render video quality")
    parser.add_argument("--theme", "-t", choices=["midnight", "dark", "cyberpunk", "nord"], default="midnight")
    parser.add_argument("--media-dir", type=str, default="output_videos", help="Directory for rendered MP4s")

    args = parser.parse_args()

    code = generate_manim_flowchart_scene_code(args.input, theme=args.theme)

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(code, encoding="utf-8")
        print(f"[+] Manim flowchart script written to: {out_path}")

    if args.render:
        print(f"[*] Rendering Manim flowchart scene at quality -q{args.quality}...")
        mp4_path = render_graph_flowchart(args.input, output_dir=args.media_dir, quality=args.quality, theme=args.theme)
        print(f"[✔] Flowchart video rendered successfully: {mp4_path}")


if __name__ == "__main__":
    main()


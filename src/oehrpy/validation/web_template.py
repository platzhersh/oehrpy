"""Web Template parser and FLAT path enumerator."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from oehrpy.validation.platforms import get_dialect
from oehrpy.validation.required_fields import STRUCTURAL_RM_TYPES, VALID_SUFFIXES


@dataclass
class WebTemplateNode:
    """Metadata for a single node in the Web Template tree."""

    id: str
    name: str
    rm_type: str
    path: str
    aql_path: str = ""
    min: int = 0
    max: int = 1
    original_name: str | None = None
    localized_names: dict[str, str] = field(default_factory=dict)
    children: list[WebTemplateNode] = field(default_factory=list)

    @property
    def is_multi_occurrence(self) -> bool:
        """Whether this node can appear multiple times (max > 1 or unbounded)."""
        return self.max == -1 or self.max > 1

    @property
    def is_leaf(self) -> bool:
        """Whether this is a leaf data type (not structural)."""
        return self.rm_type not in STRUCTURAL_RM_TYPES


@dataclass
class ParsedWebTemplate:
    """Result of parsing a Web Template JSON."""

    tree_id: str
    template_id: str
    nodes: dict[str, WebTemplateNode] = field(default_factory=dict)
    children_map: dict[str, list[str]] = field(default_factory=dict)

    def get_node(self, path: str) -> WebTemplateNode | None:
        """Get a node by its full FLAT path."""
        return self.nodes.get(path)

    def get_children_ids(self, path: str) -> list[str]:
        """Get the child node IDs for a given parent path."""
        node = self.nodes.get(path)
        if node is None:
            return []
        return [child.id for child in node.children]


def _detect_rename(node_data: dict[str, Any], node_id: str) -> str | None:
    """Detect if a node was renamed from its original archetype name.

    Returns the original name if a rename was detected, None otherwise.
    """
    # Check localizedNames for a name that differs from the id
    localized_names: dict[str, str] = node_data.get("localizedNames", {})
    if localized_names:
        localized: str | None = localized_names.get("en") or next(
            iter(localized_names.values()), None
        )
        if localized:
            slug = _slugify(localized)
            if slug != node_id:
                return localized

    # Check explicit originalName field (some web template formats)
    original_name: str | None = node_data.get("originalName")
    if original_name:
        slug = _slugify(original_name)
        if slug != node_id:
            return original_name

    return None


def _slugify(name: str) -> str:
    """Convert a human-readable name to a FLAT path slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[\s/]+", "_", slug)
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    return slug


def parse_web_template(web_template: dict[str, Any]) -> ParsedWebTemplate:
    """Parse a Web Template JSON into a structured representation.

    Args:
        web_template: The full Web Template JSON dict (with a "tree" key).

    Returns:
        A ParsedWebTemplate with all nodes indexed by their FLAT paths.
    """
    tree = web_template.get("tree")
    if tree is None:
        msg = "Web Template JSON must contain a 'tree' key"
        raise ValueError(msg)

    tree_id = tree.get("id", "")
    template_id = web_template.get("templateId") or web_template.get("template_id") or tree_id

    result = ParsedWebTemplate(tree_id=tree_id, template_id=template_id)

    def traverse(node_data: dict[str, Any], prefix: str) -> WebTemplateNode:
        node_id = node_data.get("id", "")
        current_path = f"{prefix}/{node_id}" if prefix else node_id
        rm_type = node_data.get("rmType") or node_data.get("rm_type") or ""
        name = node_data.get("name") or node_id
        localized_names = node_data.get("localizedNames", {})

        original_name = _detect_rename(node_data, node_id)

        node = WebTemplateNode(
            id=node_id,
            name=name,
            rm_type=rm_type,
            path=current_path,
            aql_path=node_data.get("aqlPath", ""),
            min=node_data.get("min", 0),
            max=node_data.get("max", 1),
            original_name=original_name,
            localized_names=localized_names,
        )

        result.nodes[current_path] = node

        children_data = node_data.get("children", [])
        for child_data in children_data:
            child_node = traverse(child_data, current_path)
            node.children.append(child_node)

        return node

    traverse(tree, "")
    return result


def enumerate_valid_paths(
    parsed: ParsedWebTemplate,
    platform: str = "ehrbase",
) -> list[str]:
    """Enumerate all valid FLAT paths from a parsed Web Template.

    Args:
        parsed: A parsed Web Template.
        platform: The CDR platform dialect ("ehrbase" or "better").

    Returns:
        Sorted list of all valid FLAT paths.
    """
    dialect = get_dialect(platform)  # type: ignore[arg-type]
    paths: list[str] = []

    for node_path, node in parsed.nodes.items():
        if node.rm_type in STRUCTURAL_RM_TYPES:
            # Structural nodes are valid as path prefixes but not as leaf paths
            continue

        suffixes = VALID_SUFFIXES.get(node.rm_type)
        if suffixes is None:
            # Unknown RM type — accept the bare path
            paths.append(node_path)
            continue

        # The bare path is always valid for leaf types
        paths.append(node_path)

        # Add suffixed variants
        for suffix in suffixes:
            paths.append(node_path + suffix)

        # For Better platform, also generate :0 indexed variants
        if dialect.index_single_occurrence:
            indexed_path = _add_index_to_path(node_path)
            if indexed_path != node_path:
                paths.append(indexed_path)
                for suffix in suffixes:
                    paths.append(indexed_path + suffix)

    paths.sort()
    return paths


def _add_index_to_path(path: str) -> str:
    """Add :0 index notation to the last segment of a path."""
    parts = path.rsplit("/", 1)
    if len(parts) == 2:
        return f"{parts[0]}/{parts[1]}:0"
    return f"{parts[0]}:0"

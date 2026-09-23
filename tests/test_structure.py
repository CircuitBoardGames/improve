"""The fork's forge gate: what the ClaudeCode hub relies on when it vendors this pack (hub#1476).

The pack is markdown, so there is no code to unit-test. What CAN break a consumer is structural:
a manifest that no longer parses, a skill whose frontmatter lost its name or description (the
harness then never lists it), a relative link to a reference file that was renamed, or a provenance
marker the hub's drift check cannot read. Each test below fails on exactly one of those.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path}: no frontmatter"
    head = text[4:text.index("\n---", 4)]
    return dict(re.findall(r"^([a-z_]+):[ \t]*(.*)$", head, re.M))


def test_manifests_parse_and_name_the_plugin():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert plugin["name"] and re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"]), plugin
    assert plugin["name"] in [p["name"] for p in market["plugins"]], market


def test_every_skill_has_a_name_matching_its_directory_and_a_description():
    assert SKILLS, "no skills/*/SKILL.md found"
    for s in SKILLS:
        fm = _frontmatter(s)
        assert fm.get("name") == s.parent.name, (s, fm.get("name"))
        assert len(fm.get("description", "").strip()) > 20, (s, "description missing or empty")


def test_relative_links_in_skills_resolve():
    checked = 0
    for md in sorted((ROOT / "skills").rglob("*.md")):
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            checked += 1
            assert (md.parent / target).exists(), f"{md.relative_to(ROOT)} -> {target}"
    assert checked, "no relative links found: the check measured nothing"


def test_upstream_provenance_marker_is_readable():
    m = json.loads((ROOT / ".upstream-provenance.json").read_text())
    assert m["true_upstream"].startswith("https://github.com/"), m
    assert m["true_upstream_branch"], m
    assert re.fullmatch(r"[0-9a-f]{40}", m["last_synced_upstream_sha"]), m

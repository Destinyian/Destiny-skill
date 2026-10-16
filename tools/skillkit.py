#!/usr/bin/env python3
"""skillkit - conventions, validation and evolution tooling for this skill library.

Zero dependencies (Python 3.10+ stdlib only), by design: this library must be usable
on machines where installing something is the thing that is broken.

Subcommands
-----------
  index [--write]        sync generated fields into skills.json (and the README index)
  check                  validate the whole library; exit code 1 when an ERROR is found
  cluster                human report: domains, clusters, collisions, oversized, zombies
  new <name>             scaffold a new skill directory + skills.json entry
  evidence <skill>       append an evidence entry to <skill>/EVIDENCE.md

Exit codes: 0 = clean (warnings allowed), 1 = at least one ERROR, 2 = usage error.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "skills.json"

# --- limits and patterns -----------------------------------------------------
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PY_SCRIPT_RE = re.compile(r"^[a-z][a-z0-9_]*\.py$")
JS_SCRIPT_RE = re.compile(r"^[a-z][a-z0-9-]*\.js$")
SKILL_FILE = "SKILL.md"
ROOT_ALLOWED = {SKILL_FILE, "EVIDENCE.md", "CHANGELOG.md", "scripts", "references", "examples", "assets"}

MAX_NAME = 64
MAX_DESCRIPTION = 500
MAX_FRONTMATTER = 1024
MAX_BODY_LINES = 500
SOFT_BODY_LINES = 300
MIN_TRIGGERS = 3
JACCARD_WARN = 0.35
MIN_HUB_CHILDREN = 2
MAX_HUB_LINES = 60

REQUIRED_ROOT_FILES = ["README.md", "CONVENTIONS.md", "EVOLUTION.md", "LICENSE", "skills.json", "tools/skillkit.py"]

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"oauth2:[A-Za-z0-9]{16,}",
    r"(?i)\bbearer\s+[A-Za-z0-9_\-.]{24,}",
    r"(?i)\b(?:password|passwd|secret|api[_-]?key)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}",
]

PATH_REF_RE = re.compile(r"(?<![\w/\-.\\])((?:scripts|references|examples|assets)/[A-Za-z0-9_./\-]+)")
FILE_REF_RE = re.compile(r"^([A-Za-z0-9_\-]+\.(?:py|js))$")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
FENCED_BLOCK_RE = re.compile(r"^```.*?^```", re.M | re.S)
CJK_RE = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]")
DESCRIPTION_OPENING_RE = re.compile(r"^use (?:when|before|after|while|if|during)\b")

# A script's own usage text is where the "renamed but not everywhere" class of bug lives, so the
# header (module docstring) and every `python x.py` / `node x.js` invocation are checked.
SCRIPT_TOKEN_RE = re.compile(r"(?<![\w./\\-])([A-Za-z0-9_\-]+\.(?:py|js))")
USAGE_HINT_RE = re.compile(r"\b(?:python3?|py|node)\s+[\"']?([A-Za-z0-9_\-]+\.(?:py|js))")
TITLE_TOKEN_RE = re.compile(r'^\s*(?:"""|\'\'\'|#|\*|//)?\s*([A-Za-z0-9_\-]+\.(?:py|js))\b')
HEADER_LINES = 3
BODY_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{5,}")
BODY_STOPWORDS = set(
    """should because before between through without anything something everything problem problems
    instead number numbers change changes example examples output outputs result results return
    returns string strings value values field fields method methods function functions python script
    scripts window browser renderer renderers element elements container document default channel
    request response server client config configuration message messages object objects option
    options struct class types check checks using used useful render rendering canvas context
    buffer uniforms shader shaders vertex fragment texture textures camera scene scenes particle
    particles physics frame frames pointer gesture gestures user users click clicks drag dragging
    state states event events handler handlers target targets source sources store stores level
    table tables record records profile profiles file files path paths time times line lines begin
    handle private public static const let var async await actual actually""".split()
)
BODY_OVERLAP_BASELINE = 0.13

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "when", "use", "used", "you", "your", "its", "it's",
    "are", "was", "were", "has", "have", "had", "not", "but", "from", "into", "than", "then", "them",
    "they", "what", "which", "who", "will", "would", "can", "could", "should", "must", "may", "might",
    "one", "two", "all", "any", "also", "only", "over", "after", "before", "because", "instead",
    "covers", "including", "reads", "checks", "classifies", "maps", "extracts", "traces", "verifies",
    "audits", "drives", "keeps", "rather", "without", "inside", "outside", "about", "their", "there",
}


# --- model -------------------------------------------------------------------
class Skill:
    def __init__(self, path: Path, raw: str):
        self.path = path
        self.dir_name = path.name
        self.raw = raw
        fm, lines_total, fm_chars = parse_frontmatter(raw)
        self.frontmatter = fm
        self.name = (fm.get("name") or "").strip()
        self.description = (fm.get("description") or "").strip()
        self.frontmatter_chars = fm_chars
        self.body_lines = lines_total
        self.scripts = sorted(p.name for p in (path / "scripts").glob("*") if p.is_file()) if (path / "scripts").is_dir() else []
        self.files = sorted(p.name for p in path.iterdir() if p.is_file())
        self.evidence_count = count_evidence(path / "EVIDENCE.md")
        self.has_cjk = bool(CJK_RE.search(strip_fenced(INLINE_CODE_RE.sub(" ", raw))))

    @property
    def trigger_tokens(self):
        tokens = re.findall(r"[a-z0-9][a-z0-9\-]{3,}", self.description.lower())
        return {t for t in tokens if t not in STOPWORDS}


def parse_frontmatter(raw: str) -> tuple[dict, int, int]:
    """Return (fields, total_lines, frontmatter_chars). Tolerates folded values."""
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, len(lines), 0
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, len(lines), 0
    fm_text = "\n".join(lines[1:end])
    fields: dict[str, str] = {}
    key = None
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = m.group(2).strip()
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, len(lines), len(fm_text)


def count_evidence(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("## "))


def strip_fenced(raw: str) -> str:
    return FENCED_BLOCK_RE.sub(" ", raw)


def referenced_paths(raw: str) -> set[str]:
    """Paths named in inline code spans.

    Only inline code is treated as a reference: fenced blocks are examples (a snippet of the site
    being audited legitimately mentions assets/app.js, which is not a file in this repo).
    """
    refs: set[str] = set()
    for span in INLINE_CODE_RE.findall(raw):
        span = span.strip()
        m = PATH_REF_RE.search(span)
        if m:
            refs.add(m.group(1).rstrip(".,;:)`"))
        elif FILE_REF_RE.match(span):
            refs.add(span)
    return refs


def resolve_reference(ref: str, skill: "Skill", skills: list["Skill"]) -> str | None:
    """Return 'local', the owning skill name for a cross-skill reference, or None if missing."""
    if (skill.path / ref).exists():
        return "local"
    if "/" not in ref and (skill.path / "scripts" / ref).exists():
        return "local"
    for other in skills:
        if other.name != skill.name and ((other.path / ref).exists() or (other.path / "scripts" / ref).exists()):
            return other.name
    return None


def script_name_problems(path: Path, all_script_names: set[str]) -> list[str]:
    """Scripts that tell the reader to run a file that does not exist anywhere in the library.

    Only two positions count, because both are instructions to the reader:
      * an invocation: python foo.py, node foo.js (anywhere in the file)
      * the title line of the module docstring / header (a bare foo.py at the start of one of the
        first 3 lines)

    Prose mentions of third-party libraries (`three.js`, `anime.js`) are not invocations and are
    deliberately ignored: a rule that flags them trains the reader to ignore the checker.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    title_lines = "\n".join(text.splitlines()[:HEADER_LINES])
    suspects = set(USAGE_HINT_RE.findall(text)) | {
        m.group(1) for m in (TITLE_TOKEN_RE.match(line) for line in title_lines.splitlines()) if m
    }
    return sorted(s for s in suspects if s != path.name and s not in all_script_names)


def body_identifiers(skill: "Skill") -> set[str]:
    body = skill.raw.split("---", 2)[-1]
    return {t.lower() for t in BODY_IDENT_RE.findall(body) if t.lower() not in BODY_STOPWORDS}


def discover_skills() -> list[Skill]:
    out = []
    for child in sorted(ROOT.iterdir()):
        if not child.is_dir() or child.name in {".git", "tools", "templates", "journal"}:
            continue
        f = child / SKILL_FILE
        if f.is_file():
            out.append(Skill(child, f.read_text(encoding="utf-8")))
    return out


def load_index() -> dict:
    if not INDEX_PATH.is_file():
        return {"version": 1, "skills": []}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def index_by_name(index: dict) -> dict[str, dict]:
    return {e.get("name"): e for e in index.get("skills", [])}


# --- validation --------------------------------------------------------------
def validate(skills: list[Skill], index: dict) -> list[tuple[str, str, str, str]]:
    """Return [(level, code, subject, message)] with level in {ERROR, WARN}."""
    problems: list[tuple[str, str, str, str]] = []

    def err(code, subject, msg):
        problems.append(("ERROR", code, subject, msg))

    def warn(code, subject, msg):
        problems.append(("WARN", code, subject, msg))

    for rel in REQUIRED_ROOT_FILES:
        if not (ROOT / rel).is_file():
            err("E00", "repo", f"missing required file: {rel}")

    idx = index_by_name(index)
    seen_names: dict[str, str] = {}
    all_script_names = {p.name for sk in skills for p in (sk.path / "scripts").glob("*") if p.is_file()}

    for s in skills:
        # E01 naming
        if not NAME_RE.match(s.dir_name):
            err("E01", s.dir_name, "directory is not kebab-case (^[a-z][a-z0-9]*(-[a-z0-9]+)*$)")
        if len(s.dir_name) > MAX_NAME:
            err("E01", s.dir_name, f"directory name longer than {MAX_NAME} chars")
        if s.name != s.dir_name:
            err("E02", s.dir_name, f"frontmatter name '{s.name}' != directory name")
        if s.name in seen_names:
            err("E02", s.dir_name, f"duplicate skill name (also in {seen_names[s.name]})")
        seen_names[s.name] = s.dir_name

        # E03 frontmatter / description
        if not s.description:
            err("E03", s.dir_name, "missing description")
        else:
            if not DESCRIPTION_OPENING_RE.match(s.description.lower()):
                err("E03", s.dir_name, "description must open with 'Use when/before/after/while/if/during'")
            if len(s.description) > MAX_DESCRIPTION:
                err("E03", s.dir_name, f"description {len(s.description)} chars > {MAX_DESCRIPTION}")
            if re.search(r"\b(I|we)\b\s+(can|will|help|recommend)\b", s.description):
                warn("W06", s.dir_name, "description should be third person")
        if s.frontmatter_chars > MAX_FRONTMATTER:
            err("E03", s.dir_name, f"frontmatter {s.frontmatter_chars} chars > {MAX_FRONTMATTER}")

        # E04 size
        if s.body_lines > MAX_BODY_LINES:
            err("E04", s.dir_name, f"{s.body_lines} lines > {MAX_BODY_LINES}: split the skill")
        elif s.body_lines > SOFT_BODY_LINES:
            warn("W04", s.dir_name, f"{s.body_lines} lines (soft limit {SOFT_BODY_LINES}): consider references/")

        # E05 unexpected files at skill root
        for f in sorted(p.name for p in s.path.iterdir() if p.is_file()):
            if f not in ROOT_ALLOWED:
                err("E05", s.dir_name, f"unexpected file at skill root: {f} (use scripts/ references/ examples/ assets/)")

        # E06 script naming
        for sc in s.scripts:
            if not (PY_SCRIPT_RE.match(sc) or JS_SCRIPT_RE.match(sc)):
                err("E06", s.dir_name, f"script name '{sc}' is not snake_case.py or kebab-case.js (verb first)")

        # E07 dangling references named in inline code (fenced blocks are examples, not references)
        for ref in sorted(referenced_paths(s.raw)):
            where = resolve_reference(ref, s, skills)
            if where is None:
                err("E07", s.dir_name, f"SKILL.md references missing path: {ref}")
            elif where != "local":
                warn("W07", s.dir_name, f"references another skill's file: {ref} (in {where})")

        # E13 a script must not tell the reader to run a file that does not exist
        for sc in s.scripts:
            for bad in script_name_problems(s.path / "scripts" / sc, all_script_names):
                err("E13", s.dir_name, f"scripts/{sc} names '{bad}', which exists nowhere in the library")

        # E08 secrets
        for pat in SECRET_PATTERNS:
            if re.search(pat, s.raw):
                err("E08", s.dir_name, f"possible secret in SKILL.md (pattern {pat})")

        # W01 language
        if s.has_cjk:
            warn("W01", s.dir_name, "SKILL.md contains CJK; skill bodies are English by convention")

        # index presence + maturity rules
        entry = idx.get(s.name)
        if not entry:
            err("E09", s.dir_name, "missing from skills.json (run: skillkit.py index --write)")
            continue

        # W03 zombie: no evidence of its own and no journal reference either
        if s.evidence_count == 0 and not entry.get("evidence_refs"):
            warn("W03", s.dir_name, "no evidence entries and no evidence_refs - is this skill alive?")

        maturity = entry.get("maturity", "draft")
        if maturity not in {"draft", "verified", "field-tested", "routed"}:
            err("E10", s.dir_name, f"unknown maturity '{maturity}'")
        if maturity != "draft" and not entry.get("verified_on"):
            err("E10", s.dir_name, f"maturity '{maturity}' requires verified_on")
        if maturity in {"field-tested", "routed"} and s.evidence_count == 0 and not entry.get("evidence_refs"):
            err("E10", s.dir_name, f"maturity '{maturity}' requires an evidence entry or evidence_refs")
        if maturity == "routed" and not entry.get("referenced_by"):
            err("E10", s.dir_name, "maturity 'routed' requires referenced_by")
        role = entry.get("role", "skill")
        if role not in {"skill", "hub"}:
            err("E16", s.dir_name, f"unknown role '{role}' (expected skill | hub)")
        elif role == "hub":
            children = [
                o.name
                for o in skills
                if o.name != s.name
                and (idx.get(o.name) or {}).get("cluster") == entry.get("cluster")
                and o.name in (entry.get("related") or [])
            ]
            if len(children) < MIN_HUB_CHILDREN:
                err("E16", s.dir_name, f"a hub must route >= {MIN_HUB_CHILDREN} skills of its own cluster; found {children}")
            if s.body_lines > MAX_HUB_LINES:
                err("E16", s.dir_name, f"hub body is {s.body_lines} lines > {MAX_HUB_LINES}: a router is a table, not a manual")
            if s.scripts:
                err("E16", s.dir_name, "a hub holds no scripts - the tool belongs to the child owning the technique")

        trigs = entry.get("triggers") or []
        if len(trigs) < MIN_TRIGGERS:
            warn("W05", s.dir_name, f"only {len(trigs)} triggers (want >= {MIN_TRIGGERS})")
        for extra in entry.get("related", []):
            if extra not in {x.dir_name for x in skills}:
                err("E11", s.dir_name, f"related skill '{extra}' does not exist")
            elif extra not in s.raw:
                err("E14", s.dir_name, f"related lists '{extra}' but SKILL.md never mentions it")
        for other in sorted(x.dir_name for x in skills):
            if other != s.name and other in s.raw and other not in (entry.get("related") or []):
                err("E14", s.dir_name, f"SKILL.md mentions '{other}' but related does not list it")

    for name in idx:
        if name not in seen_names:
            err("E09", str(name), "skills.json has an entry with no directory on disk")

    # E15 referenced_by is generated: it must be the exact inverse of related
    for s in skills:
        expected = sorted(o.name for o in skills if s.name in ((idx.get(o.name) or {}).get("related") or []))
        actual = sorted((idx.get(s.name) or {}).get("referenced_by") or [])
        if expected != actual:
            err("E15", s.dir_name, f"referenced_by should be {expected} (generated); stored {actual}")

    # E12 duplicate triggers across skills
    trigger_owner: dict[str, list[str]] = {}
    for s in skills:
        entry = idx.get(s.name) or {}
        for t in entry.get("triggers") or []:
            trigger_owner.setdefault(normalize_trigger(t), []).append(s.name)
    for trig, owners in sorted(trigger_owner.items()):
        if len(owners) > 1:
            err("E12", trig, f"trigger claimed by several skills: {', '.join(sorted(owners))}")

    # W02 description overlap
    names = sorted(s.name for s in skills)
    for i, a in enumerate(skills):
        for b in skills[i + 1:]:
            j = jaccard(a.trigger_tokens, b.trigger_tokens)
            if j >= JACCARD_WARN:
                warn("W02", f"{a.name} ~ {b.name}", f"description token overlap {j:.2f} (possible discovery collision)")

    return problems


def normalize_trigger(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# --- index -------------------------------------------------------------------
def computed_entry(s: Skill, previous: dict | None) -> dict:
    prev = previous or {}
    entry = {
        "name": s.name,
        "path": s.dir_name,
        "domain": prev.get("domain", "unclassified"),
        "cluster": prev.get("cluster", "unclassified"),
        "role": prev.get("role", "skill"),
        "maturity": prev.get("maturity", "draft"),
        "verified_on": prev.get("verified_on"),
        "triggers": prev.get("triggers", []),
        "related": prev.get("related", []),
        "referenced_by": prev.get("referenced_by", []),
        "evidence_refs": prev.get("evidence_refs", []),
        "description": s.description,
        "body_lines": s.body_lines,
        "scripts": [f"scripts/{x}" for x in s.scripts],
        "evidence_count": s.evidence_count,
    }
    return entry


def sync_index(write: bool, update_readme: bool) -> int:
    skills = discover_skills()
    index = load_index()
    prev = index_by_name(index)
    entries = [computed_entry(s, prev.get(s.name)) for s in skills]
    # referenced_by is derived, never authored: it is the inverse of related
    for e in entries:
        e["referenced_by"] = sorted(o["name"] for o in entries if e["name"] in (o.get("related") or []))
    drift = []
    for e in entries:
        old = prev.get(e["name"])
        if old is None:
            drift.append(f"+ {e['name']}")
            continue
        for k, v in e.items():
            if old.get(k) != v:
                drift.append(f"~ {e['name']}.{k}")
    for name in prev:
        if name not in {e["name"] for e in entries}:
            drift.append(f"- {name}")

    if drift:
        print("index drift:")
        for d in drift:
            print("  " + d)
    else:
        print("index is in sync")

    if write:
        index["version"] = index.get("version", 1)
        index["generated_by"] = "tools/skillkit.py index --write"
        index["skills"] = entries
        INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {INDEX_PATH.relative_to(ROOT)} ({len(entries)} skills)")
        if update_readme:
            write_readme_index(entries, index)
    return 0


def write_readme_index(entries: list[dict], index: dict) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = "<!-- SKILLS:START -->", "<!-- SKILLS:END -->"
    if start not in text or end not in text:
        print("README has no SKILLS markers; skipping README index")
        return
    lines = [start, "", "| Skill | Domain / cluster | Maturity | Verified | Scripts | Evidence |", "|---|---|---|---|---|---|"]
    order = sorted(entries, key=lambda e: (e["domain"], e["cluster"], e["name"]))
    for e in order:
        scripts = ", ".join(f"`{p}`" for p in e["scripts"]) or "—"
        lines.append(
            f"| [{e['name']}]({e['path']}/) | {e['domain']} / {e['cluster']} | {e['maturity']} | "
            f"{e['verified_on'] or '—'} | {scripts} | {e['evidence_count']} |"
        )
    lines += ["", end]
    new_text = re.sub(re.escape(start) + r".*?" + re.escape(end), "\n".join(lines), text, flags=re.S)
    readme.write_text(new_text, encoding="utf-8", newline="\n")
    print("updated README index between markers")


# --- report ------------------------------------------------------------------
def report() -> int:
    skills = discover_skills()
    index = load_index()
    idx = index_by_name(index)
    print(f"skills: {len(skills)}\n")

    groups: dict[tuple[str, str], list[Skill]] = {}
    for s in skills:
        e = idx.get(s.name) or {}
        groups.setdefault((e.get("domain", "?"), e.get("cluster", "?")), []).append(s)

    for (domain, cluster), members in sorted(groups.items()):
        print(f"[{domain} / {cluster}]")
        for s in members:
            e = idx.get(s.name) or {}
            print(
                f"  {s.name:<38} {e.get('maturity','?'):<12} body={s.body_lines:<4} "
                f"scripts={len(s.scripts)} evidence={s.evidence_count}"
            )
        print()

    print("cluster sizes (routers excluded - the hub rule counts members, not the router):")
    for (domain, cluster), members in sorted(groups.items()):
        hubs = [m for m in members if (idx.get(m.name) or {}).get("role") == "hub"]
        count = len(members) - len(hubs)
        if hubs:
            print(f"  {domain}/{cluster}: {count} member(s) + hub {', '.join(h.name for h in hubs)}")
        elif count >= 3:
            print(f"  {domain}/{cluster}: {count}  <-- consider a hub")
        else:
            print(f"  {domain}/{cluster}: {count}")

    print("\npossible overlaps (description token Jaccard >= %.2f):" % JACCARD_WARN)
    found = False
    for i, a in enumerate(skills):
        for b in skills[i + 1:]:
            j = jaccard(a.trigger_tokens, b.trigger_tokens)
            if j >= JACCARD_WARN:
                found = True
                print(f"  {j:.2f}  {a.name} ~ {b.name}")
    if not found:
        print("  none")

    print(f"\nbody overlap, top 5 (review prompt, NOT a gate; measured baseline max {BODY_OVERLAP_BASELINE}):")
    idents = {s.name: body_identifiers(s) for s in skills}
    ranked = sorted(
        (
            (jaccard(idents[a.name], idents[b.name]), a.name, b.name)
            for i, a in enumerate(skills)
            for b in skills[i + 1:]
        ),
        reverse=True,
    )[:5]
    for j, a, b in ranked:
        print(f"  {j:.3f}  {a} ~ {b}{'   <-- review' if j >= BODY_OVERLAP_BASELINE else ''}")

    print("\nmaintenance:")
    for s in skills:
        entry = idx.get(s.name) or {}
        notes = []
        if s.body_lines > SOFT_BODY_LINES:
            notes.append(f"body {s.body_lines} lines")
        if s.evidence_count == 0 and not entry.get("evidence_refs"):
            notes.append("no evidence")
        if not notes:
            continue
        print(f"  {s.name:<38} {', '.join(notes)}")
    if not any(
        s.body_lines > SOFT_BODY_LINES or (s.evidence_count == 0 and not (idx.get(s.name) or {}).get("evidence_refs"))
        for s in skills
    ):
        print("  nothing to do")
    return 0


# --- scaffolding -------------------------------------------------------------
def new_skill(name: str) -> int:
    if not NAME_RE.match(name):
        print(f"error: '{name}' is not kebab-case")
        return 2
    target = ROOT / name
    if target.exists():
        print(f"error: {name} already exists")
        return 2
    template = (ROOT / "templates" / "skill" / SKILL_FILE).read_text(encoding="utf-8")
    (target / "scripts").mkdir(parents=True)
    (target / SKILL_FILE).write_text(template.replace("skill-name", name), encoding="utf-8")
    (target / "EVIDENCE.md").write_text(
        f"# Evidence - {name}\n\nAppend-only. One entry per real session that used this skill.\n"
        "See EVOLUTION.md for the entry format.\n",
        encoding="utf-8",
    )
    print(f"created {name}/ (SKILL.md, EVIDENCE.md, scripts/)")
    print("next: fill the description, then run  python tools/skillkit.py index --write")
    return 0


def add_evidence(name: str, scenario: str) -> int:
    target = ROOT / name
    if not (target / SKILL_FILE).is_file():
        print(f"error: no such skill: {name}")
        return 2
    path = target / "EVIDENCE.md"
    if not path.exists():
        path.write_text(f"# Evidence - {name}\n\nAppend-only. One entry per real session.\n", encoding="utf-8")
    commit = "unknown"
    try:
        import subprocess

        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10
        ).stdout.strip() or "unknown"
    except Exception:
        pass
    entry = (
        f"\n## {date.today().isoformat()} - {scenario or 'session'}\n"
        f"- class: gap | wrong-claim | stale | trigger-miss | noise\n"
        f"- expected (what the skill says): \n"
        f"- actual (what happened): \n"
        f"- evidence (command / output / counter): \n"
        f"- conclusion / action: \n"
        f"- commit: {commit}\n"
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry)
    print(f"appended evidence entry to {path.relative_to(ROOT)}")
    return 0


# --- cli ---------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, rest = argv[1], argv[2:]
    if cmd == "index":
        return sync_index("--write" in rest, "--no-readme" not in rest)
    if cmd == "check":
        skills, index = discover_skills(), load_index()
        problems = validate(skills, index)
        errors = [p for p in problems if p[0] == "ERROR"]
        warns = [p for p in problems if p[0] == "WARN"]
        for level, code, subject, msg in errors + warns:
            print(f"{level} {code} {subject}: {msg}")
        print(f"\n{len(errors)} error(s), {len(warns)} warning(s), {len(skills)} skill(s)")
        return 1 if errors else 0
    if cmd == "cluster":
        return report()
    if cmd == "new":
        if not rest:
            print("usage: skillkit.py new <kebab-case-name>")
            return 2
        return new_skill(rest[0])
    if cmd == "evidence":
        if not rest:
            print("usage: skillkit.py evidence <skill> [scenario]")
            return 2
        return add_evidence(rest[0], " ".join(rest[1:]))
    print(f"unknown command: {cmd}")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

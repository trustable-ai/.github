#!/usr/bin/env python3
"""Generate the static application starter index published at

    https://raw.githubusercontent.com/trustable-ai/.github/refs/heads/main/index.json

An application starter is a public repository of the trustable-ai organization
whose GitHub description begins with "Trustable:". The text after the marker
carries optional <key>=<value> parameters (currently only templates=) which are
stripped from the human-readable description.

Trustable reads the published index.json directly over raw.githubusercontent.com
and never calls the GitHub API. This script is the only thing that talks to the
API, and it runs here — with `gh`, so it uses the maintainer's credentials and
rate limit rather than the user's.

Usage:
    ./index.py             # regenerate index.json and show the diff
    ./index.py --push      # also commit and push it to trustable-ai/.github

See spec/15-starters.md in trustable-app.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

ORG = "trustable-ai"
DEFAULT_TEMPLATES = "trustable-ai/templates"
MARKER = "trustable:"
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")

# <key>=<value> tokens carried in the description. Values are unquoted and
# whitespace-delimited, which is all a GitHub description realistically holds.
KEY_VALUE = re.compile(r"\b([A-Za-z][A-Za-z0-9_-]*)=(\S+)")

# Same shape trustable-app accepts for notebook.repository: owner/repository.
REPO_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def run(args):
    """Run a command and return stdout, failing loudly."""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"error: {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def normalize_templates(value):
    """Normalize a templates= value to owner/repository.

    Accepts a bare owner/repo or a full GitHub URL. Returns None when the value
    cannot be understood, so the caller can fall back to the default.
    """
    value = (value or "").strip()
    for prefix in ("https://github.com/", "http://github.com/"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
            break
    if "://" in value:
        return None
    value = value.strip("/")
    if value.endswith(".git"):
        value = value[: -len(".git")]
    parts = value.split("/")
    if len(parts) != 2 or not all(REPO_SEGMENT.match(part) for part in parts):
        return None
    return f"{parts[0]}/{parts[1]}"


def parse_description(description):
    """Split "Trustable: <text>" into (text, params).

    Returns (None, None) when the description does not carry the marker, which
    is how non-starter repositories are filtered out.
    """
    trimmed = (description or "").strip()
    if trimmed[: len(MARKER)].lower() != MARKER:
        return None, None
    rest = trimmed[len(MARKER):]
    params = {key.lower(): value for key, value in KEY_VALUE.findall(rest)}
    text = " ".join(KEY_VALUE.sub(" ", rest).split())
    return text, params


def fetch_repositories():
    """List the org's public repositories with the gh CLI."""
    output = run([
        "gh", "api", "--paginate",
        f"orgs/{ORG}/repos?type=public&per_page=100",
    ])
    # --paginate concatenates one JSON array per page when the output is piped
    # through jq; without jq it returns a single stream of arrays. Decode
    # defensively so both shapes work.
    decoder = json.JSONDecoder()
    repositories = []
    position = 0
    while position < len(output):
        while position < len(output) and output[position].isspace():
            position += 1
        if position >= len(output):
            break
        page, position = decoder.raw_decode(output, position)
        repositories.extend(page)
    return repositories


def build_starters(repositories):
    starters = []
    for repo in repositories:
        if repo.get("private") or repo.get("archived") or repo.get("disabled"):
            continue
        text, params = parse_description(repo.get("description"))
        if text is None:
            continue
        name = (repo.get("name") or "").strip()
        full_name = (repo.get("full_name") or "").strip() or f"{ORG}/{name}"
        if not name:
            continue
        templates = normalize_templates(params.get("templates")) or DEFAULT_TEMPLATES
        starters.append({
            "name": name,
            "repo": full_name,
            "templates": templates,
            "description": text,
        })
    starters.sort(key=lambda item: item["name"])
    return starters


def git(args, cwd):
    return run(["git", "-C", cwd] + args)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--push", action="store_true",
                        help="commit and push index.json to trustable-ai/.github")
    args = parser.parse_args()

    repositories = fetch_repositories()
    starters = build_starters(repositories)
    if not starters:
        sys.exit("error: no starters found — refusing to publish an empty index")

    index = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "starters": starters,
    }

    previous = ""
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as handle:
            previous = handle.read()

    payload = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    with open(INDEX_PATH, "w", encoding="utf-8") as handle:
        handle.write(payload)

    print(f"{len(starters)} starters written to {INDEX_PATH}")
    for starter in starters:
        print(f"  {starter['name']:<16} {starter['repo']:<32} "
              f"templates={starter['templates']}")

    # "generated" changes on every run, so compare the starter list itself to
    # decide whether there is anything worth publishing.
    def starters_of(text):
        try:
            return json.loads(text).get("starters")
        except (ValueError, AttributeError):
            return None

    unchanged = starters_of(previous) == starters
    if unchanged:
        print("\nStarter list unchanged.")
    if not args.push:
        print("\nNot pushed. Re-run with --push to publish.")
        return
    if unchanged:
        print("Nothing to push.")
        return

    repo_dir = os.path.dirname(INDEX_PATH)
    git(["add", "index.json"], repo_dir)
    git(["commit", "-m", "Update application starter index"], repo_dir)
    git(["push"], repo_dir)
    print("\nPushed to trustable-ai/.github.")


if __name__ == "__main__":
    main()

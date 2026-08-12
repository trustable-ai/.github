#!/usr/bin/env python3
"""Generate the static application starter index published at

    https://raw.githubusercontent.com/trustable-ai/.github/refs/heads/main/index.json

An application starter is a public repository of the trustable-ai organization
whose GitHub description begins with "Trustable:". The text after the marker
carries <key>=<value> parameters (currently only templates=) which are stripped
from the human-readable description. Only a repository with a usable templates=
is a starter; one carrying the marker without it contributes applications only.

The repository holding the applications — the templates repository of a starter,
or the marked repository itself when it has no templates= — may publish an
_index.md listing them, one per line:

    - [<name>](<template>.md) <description>

Those lines become the "applications" object, grouped under the first "# "
heading of the file they came from. The linked file names the template, so the
application's repository is https://github.com/trustable-ai/<template> and its
icon URL is the same path with the extension swapped for .png. A repository
that does not exist and a missing icon are both warned about, not fatal.

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
import urllib.error
import urllib.request
from datetime import datetime, timezone

ORG = "trustable-ai"
MARKER = "trustable:"
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")

RAW_BASE = "https://raw.githubusercontent.com/{repo}/refs/heads/main/{path}"
APPLICATION_INDEX = "_index.md"

# An application's own repository, named by the template linked in _index.md:
# "- [Tetris](tetris.md)" lives in https://github.com/trustable-ai/tetris.
REPO_BASE = "https://github.com/{org}/{template}"

# Convention for a marked repository that carries no templates=: its
# applications live in a sibling repository with this suffix.
TEMPLATES_SUFFIX = "-templates"

# <key>=<value> tokens carried in the description. Values are unquoted and
# whitespace-delimited, which is all a GitHub description realistically holds.
KEY_VALUE = re.compile(r"\b([A-Za-z][A-Za-z0-9_-]*)=(\S+)")

# Same shape trustable-app accepts for notebook.repository: owner/repository.
REPO_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# One application per line: "- [<name>](<file>.md) <description>". The
# description is optional; anything else in the file is ignored.
APPLICATION_LINE = re.compile(r"^\s*[-*]\s*\[([^\]]+)\]\(([^)\s]+\.md)\)\s*(.*)$")

# The group name is the first top-level "# " heading of an _index.md.
GROUP_HEADING = re.compile(r"^#\s+(.*\S)\s*$")


def run(args):
    """Run a command and return stdout, failing loudly."""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"error: {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def normalize_templates(value):
    """Normalize a templates= value to owner/repository.

    Accepts a bare owner/repo or a full GitHub URL. Returns None when the value
    cannot be understood, which disqualifies the repository as a starter.
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


def raw_url(repo, path):
    """URL of a file on the main branch of repo, as raw.githubusercontent.com."""
    return RAW_BASE.format(repo=repo, path=path.lstrip("/"))


def fetch_raw(url):
    """Fetch a raw file, returning None when it is not published."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        sys.exit(f"error: GET {url} failed: {error.code} {error.reason}")
    except urllib.error.URLError as error:
        sys.exit(f"error: GET {url} failed: {error.reason}")


def raw_exists(url):
    """Whether a raw URL is published, via HEAD so no body is downloaded.

    A network failure is reported as missing rather than fatal: this only
    drives a warning, and it must not block regenerating the index.
    """
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=30):
            return True
    except (urllib.error.URLError, OSError):
        return False


def repo_exists(repo):
    """Whether owner/repository exists on GitHub, via the gh CLI.

    An anonymous HEAD on github.com cannot tell a missing repository from a
    private one, and both matter here: an application whose repository is
    private is as unusable to a user as one that was never created. `gh` is
    already a dependency and carries the maintainer's credentials, so it sees
    private repositories of the organization too.

    Returns True when the repository exists, False on a definite 404, and None
    when the answer is unknown (gh missing, not authenticated, network down) so
    a broken environment produces no misleading "does not exist" warnings.
    """
    result = subprocess.run(["gh", "api", f"repos/{repo}"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        return True
    if "404" in result.stderr or "Not Found" in result.stderr:
        return False
    return None


def parse_applications(text, templates_repo):
    """Parse a templates _index.md into (group, applications).

    The group is the first "# " heading with the marker removed; it is None
    when the file has none. The linked "<template>.md" names the template: the
    application's repository is https://github.com/<ORG>/<template>, and the
    icon is the same path with the extension swapped for .png, resolved against
    the templates repository.
    """
    group = None
    applications = []
    for line in (text or "").splitlines():
        if group is None:
            heading = GROUP_HEADING.match(line)
            if heading:
                group = " ".join(heading.group(1).split()) or None
        match = APPLICATION_LINE.match(line)
        if not match:
            continue
        name, path, description = match.groups()
        template = os.path.basename(path)[: -len(".md")]
        applications.append({
            "name": " ".join(name.split()),
            "repo": REPO_BASE.format(org=ORG, template=template),
            "icon": raw_url(templates_repo, path[: -len(".md")] + ".png"),
            "description": " ".join(description.split()),
        })
    return group, applications


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
    """Build the starter list and the applications each one's templates offer.

    A repository with a usable templates= is a starter, and its applications
    come from the templates repository. A repository carrying the marker
    *without* templates= is not a starter but still contributes applications,
    read from the conventional <name>-templates repository and falling back to
    the repository itself — that is how a plain collection of applications is
    published without offering a starter.

    A repository whose _index.md is absent contributes no applications.

    Applications are grouped under the first "# " heading of the _index.md they
    came from. Two repositories sharing a heading share the group.
    """
    starters = []
    groups = {}
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
        templates = normalize_templates(params.get("templates"))
        if templates:
            starters.append({
                "name": name,
                "repo": full_name,
                "templates": templates,
                "description": text,
            })
        else:
            print(f"  {full_name}: no templates=, applications only",
                  file=sys.stderr)
        # Without templates= the applications live in the conventional
        # <name>-templates repository, falling back to the repository itself.
        source = templates or f"{full_name}{TEMPLATES_SUFFIX}"
        listing = fetch_raw(raw_url(source, APPLICATION_INDEX))
        if listing is None and not templates:
            source = full_name
            listing = fetch_raw(raw_url(source, APPLICATION_INDEX))
        if listing is None:
            print(f"  {source}: no {APPLICATION_INDEX}", file=sys.stderr)
            continue
        group, entries = parse_applications(listing, source)
        if entries and group is None:
            group = name
            print(f"  {source}: no '# ' heading, grouping under {group}",
                  file=sys.stderr)
        for entry in entries:
            groups.setdefault(group, []).append(entry)
    starters.sort(key=lambda item: item["name"])
    applications = {
        group: sorted(entries, key=lambda item: (item["repo"], item["name"]))
        for group, entries in sorted(groups.items())
    }
    return starters, applications


def check_icons(applications):
    """Warn about applications whose icon is not published, across all groups.

    The icon URL is a convention derived from the .md path, so a missing image
    is a warning and not an error: the entry stays in the index and the image
    can be added to the templates repository later.
    """
    missing = [app for entries in applications.values() for app in entries
               if not raw_exists(app["icon"])]
    for app in missing:
        print(f"warning: {app['repo']}: no icon for {app['name']} — "
              f"{app['icon']}", file=sys.stderr)
    return missing


def check_repositories(applications):
    """Warn about applications whose repository does not exist, across all groups.

    The repository is a convention derived from the template name linked in
    _index.md, so a typo there — or a template listed before its repository was
    created — points at nothing. Like a missing icon this is a warning and not
    an error: the entry stays in the index and the repository can be created
    later without regenerating anything.

    Each distinct repository is probed once, since the same template may be
    listed by more than one _index.md.
    """
    urls = sorted({app["repo"] for entries in applications.values()
                   for app in entries})
    prefix = "https://github.com/"
    verdicts = {url: repo_exists(url[len(prefix):]) for url in urls}
    missing = {url for url, exists in verdicts.items() if exists is False}
    unknown = {url for url, exists in verdicts.items() if exists is None}
    for entries in applications.values():
        for app in entries:
            if app["repo"] in missing:
                print(f"warning: no repository for {app['name']} — "
                      f"{app['repo']}", file=sys.stderr)
    if unknown:
        print(f"warning: could not check {len(unknown)} repositories "
              f"(is gh authenticated?)", file=sys.stderr)
    return missing


def git(args, cwd):
    return run(["git", "-C", cwd] + args)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--push", action="store_true",
                        help="commit and push index.json to trustable-ai/.github")
    args = parser.parse_args()

    repositories = fetch_repositories()
    starters, applications = build_starters(repositories)
    if not starters:
        sys.exit("error: no starters found — refusing to publish an empty index")

    index = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "starters": starters,
        "applications": applications,
    }

    previous = ""
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as handle:
            previous = handle.read()

    payload = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    with open(INDEX_PATH, "w", encoding="utf-8") as handle:
        handle.write(payload)

    total = sum(len(entries) for entries in applications.values())
    print(f"{len(starters)} starters, {total} applications in "
          f"{len(applications)} groups written to {INDEX_PATH}")
    for starter in starters:
        print(f"  {starter['name']:<16} {starter['repo']:<32} "
              f"templates={starter['templates']}")
    missing_icons = check_icons(applications)
    missing_urls = {app["icon"] for app in missing_icons}
    missing_repos = check_repositories(applications)
    for group, entries in applications.items():
        print(f"  {group}:")
        for entry in entries:
            marks = ""
            if entry["repo"] in missing_repos:
                marks += " (no repo)"
            if entry["icon"] in missing_urls:
                marks += " (no icon)"
            print(f"    {entry['name']:<24} {entry['repo']:<48} "
                  f"{entry['description']}{marks}")
    if missing_icons:
        print(f"\n{len(missing_icons)} of {total} applications "
              f"have no icon published.")
    if missing_repos:
        broken = sum(1 for entries in applications.values() for app in entries
                     if app["repo"] in missing_repos)
        print(f"{broken} of {total} applications point at a repository "
              f"that does not exist.")

    # "generated" changes on every run, so compare the content itself to decide
    # whether there is anything worth publishing.
    def content_of(text):
        try:
            document = json.loads(text)
            return document.get("starters"), document.get("applications")
        except (ValueError, AttributeError):
            return None

    unchanged = content_of(previous) == (starters, applications)
    if unchanged:
        print("\nStarter and application lists unchanged.")
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

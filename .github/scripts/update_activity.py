"""Rewrite the README's Recent activity section from the GitHub API.

Lists the owner's most recently pushed public repositories (excluding this
profile repo and forks) with each one's latest commit, between the
START_SECTION:activity / END_SECTION:activity markers.
"""
import datetime
import json
import os
import re
import urllib.request

OWNER = os.environ["OWNER"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README = "README.md"
LIMIT = 6


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def ago(iso):
    when = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (datetime.datetime.now(datetime.timezone.utc) - when).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days} days ago"
    return when.strftime("%b %Y")


repos = get(f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=pushed&type=owner")
repos = [r for r in repos if not r["fork"] and not r["private"] and r["name"].lower() != OWNER.lower()]

lines = []
for repo in repos[:LIMIT]:
    commits = get(f"https://api.github.com/repos/{OWNER}/{repo['name']}/commits?per_page=1")
    if not commits:
        continue
    c = commits[0]
    message = c["commit"]["message"].splitlines()[0].strip()
    if len(message) > 72:
        message = message[:69].rstrip() + "..."
    message = message.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
    lines.append(
        f"{len(lines) + 1}. 🔨 **[{repo['name']}]({repo['html_url']})**: "
        f"[{message}]({c['html_url']}) · <sub>{ago(c['commit']['committer']['date'])}</sub>"
    )

block = "\n".join(lines) if lines else "_No recent public activity._"
text = open(README, encoding="utf-8").read()
updated = re.sub(
    r"(<!--START_SECTION:activity-->)(.*?)(<!--END_SECTION:activity-->)",
    lambda m: f"{m.group(1)}\n{block}\n{m.group(3)}",
    text,
    flags=re.S,
)
if updated != text:
    open(README, "w", encoding="utf-8", newline="\n").write(updated)
    print("README activity section updated")
else:
    print("No change")

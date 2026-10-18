"""The no-UI delivery: one edition as Markdown an agent can paste into the chat.

Labels reuse the page's interface keys (the `STRINGS` object in web/js/strings.js), so one agent-written strings.json
translates both the page and the digest. Keys starting with `digest.` exist only here.
"""
import datetime as dt
from zoneinfo import ZoneInfo

# Shared keys must match web/js/strings.js exactly; tests/test_digest.py checks that they do.
DEFAULT_STRINGS = {
    "why": "Why now", "fit": "Why for you", "explore": "Outside your profile",
    "verdict.try": "Worth trying", "verdict.watch": "Watch closely", "verdict.observe": "Keep an eye on",
    "effort.low": "Low, try it right away", "effort.medium": "Medium, needs setup", "effort.high": "High, needs a lab setup",
    "fact.effort": "Effort", "stars.approx": "~", "stars.none": "Stars not recorded",
    "demo.ready": "Verified demo", "demo.blocked": "Demo not ready", "demo.failed": "Demo failed verification",
    "edition.empty": "Nothing in this edition was worth picking.",
    "banner.title": "Sample picks",
    "digest.heading": "{title} · {day} · {count}",
    "digest.picks": "{n} picks", "digest.picks.one": "1 pick",
    "digest.stars": "{approx}{n} stars ({time})",
    "digest.try": "Try it: `{command}`",
    "digest.sample": "These ship with RepoMuse and were not picked for you.",
    "digest.reply": "Tell me what you think, for example \"1 useful, 3 not for me\", and I will remember it.",
}


def label(strings, key, **values):
    template = strings.get(key) or DEFAULT_STRINGS.get(key) or key
    for name, value in values.items():
        template = template.replace("{" + name + "}", str(value))
    return template


def observed(value, timezone):
    try:
        when = dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo(timezone))
    except Exception:
        return value
    return when.strftime("%Y-%m-%d %H:%M")


def demo_slug(demo):
    return demo["path"].strip("/").split("/")[1]


def render(edition, config, strings=None, sample=False):
    strings = strings or {}
    projects = edition["projects"]
    count = label(strings, "digest.picks.one" if len(projects) == 1 else "digest.picks", n=len(projects))
    lines = ["## " + label(strings, "digest.heading", title=config["title"], day=edition["day"], count=count), ""]
    if sample:
        lines += [f"_{label(strings, 'banner.title')}: {label(strings, 'digest.sample')}_", ""]
    if not projects:
        lines += [label(strings, "edition.empty"), ""]
    for number, project in enumerate(projects, 1):
        heading = f"### {number}. [{project['name']}](https://github.com/{project['repo']}) · " \
                  f"{label(strings, 'verdict.' + project['verdict'])}"
        lines += [heading, project["title"], ""]
        if project.get("fit"):
            lines.append(f"**{label(strings, 'fit')}** {project['fit']}  ")
        lines.append(f"**{label(strings, 'why')}** {project['reason']}  ")
        stars = project.get("stars")
        facts = [label(strings, "digest.stars", approx=label(strings, "stars.approx") if stars.get("approximate") else "",
                       n=f"{stars['count']:,}", time=observed(stars["observed_at"], config["timezone"]))
                 if stars else label(strings, "stars.none"),
                 project["license"]["name"],
                 f"{label(strings, 'fact.effort')}: {label(strings, 'effort.' + project['effort'])}"]
        if project.get("explore"):
            facts.append(label(strings, "explore"))
        lines.append(" · ".join(facts) + "  ")
        demo = project.get("demo")
        if demo and demo["status"] == "ready":
            command = f"python3 -m repomuse demo {demo_slug(demo)}"
            lines.append(f"**{label(strings, 'demo.ready')}** {demo['title']}. {label(strings, 'digest.try', command=command)}  ")
        elif demo:
            lines.append(f"**{label(strings, 'demo.' + demo['status'])}** {demo['evidence']}  ")
        lines.append("")
    if projects and not sample:
        lines.append(label(strings, "digest.reply"))
    return "\n".join(lines).rstrip() + "\n"


def pick_edition(data, day=None):
    editions = data["editions"]
    if not editions:
        raise ValueError("there are no editions yet")
    if day is None:
        return max(editions, key=lambda row: row["day"])
    for edition in editions:
        if edition["day"] == day:
            return edition
    raise ValueError(f"no edition for {day}")

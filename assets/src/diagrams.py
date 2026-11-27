"""Generate the case-study diagrams in light and dark themes.

Run: python3 assets/src/diagrams.py  (writes assets/<name>-{light,dark}.svg)
Edit text and layout here; never edit the generated SVG files by hand.
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent

THEMES = {
    "light": dict(
        bg="#ffffff", surface="#f6f8fa", card="#ffffff", ink="#1f2328", muted="#59636e",
        line="#d1d9e0", arrow="#818b98", server="#4f46e5", server_tint="#eef0fe",
        pi="#a21caf", pi_tint="#fbeefc", amber="#b45309", amber_tint="#fdf3e6",
        red="#c2410c", red_tint="#fdefe8", ok="#047857", ok_tint="#e6f4ee", on_accent="#ffffff",
    ),
    "dark": dict(
        bg="#0d1117", surface="#151b23", card="#1c2129", ink="#e6edf3", muted="#9198a1",
        line="#3d444d", arrow="#768390", server="#8f94fb", server_tint="#1b1d3d",
        pi="#e17ff0", pi_tint="#2c1530", amber="#f0a742", amber_tint="#2d2010",
        red="#f0805a", red_tint="#2e1812", ok="#3fb98a", ok_tint="#102a20", on_accent="#0d1117",
    ),
}

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"


class Svg:
    def __init__(self, w, h, title, t):
        self.w, self.h, self.t = w, h, t
        self.parts = []
        self.title = title

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size=14, color="ink", weight=400, anchor="start", extra=""):
        self.add(
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{self.t[color]}" text-anchor="{anchor}"{extra}>{escape(s)}</text>'
        )

    def lines(self, x, y, rows, size=14, color="muted", gap=20, **kw):
        for i, row in enumerate(rows):
            self.text(x, y + i * gap, row, size=size, color=color, **kw)

    def rect(self, x, y, w, h, fill="card", stroke="line", rx=12, dash=None, sw=1.2):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{self.t[fill]}" '
            f'stroke="{self.t[stroke]}" stroke-width="{sw}"{d}/>'
        )

    def path(self, d, color="arrow", width=1.8, dash=None, head=True, both=False):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#h-{color})"' if head else ""
        if both:
            m += f' marker-start="url(#h-{color})"'
        self.add(
            f'<path d="{d}" fill="none" stroke="{self.t[color]}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"{dd}{m}/>'
        )

    def card(self, x, y, w, h, title, body, accent, number=None, dash=None, size=14):
        self.rect(x, y, w, h, dash=dash)
        if not dash:
            self.add(f'<rect x="{x}" y="{y + 12}" width="4" height="{h - 24}" rx="2" fill="{self.t[accent]}"/>')
        tx = x + 20
        if number is not None:
            self.add(f'<circle cx="{x + 32}" cy="{y + 29}" r="13" fill="{self.t[accent]}"/>')
            self.text(x + 32, y + 34, str(number), size=13, color="on_accent", weight=700, anchor="middle")
            tx = x + 54
        title_rows = title.splitlines()
        self.lines(tx, y + 34, title_rows, size=16, gap=19, weight=650, color="muted" if dash else "ink")
        self.lines(x + 20, y + 62 + 19 * (len(title_rows) - 1), body, size=size)

    def render(self):
        markers = "".join(
            f'<marker id="h-{c}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{self.t[c]}"/></marker>'
            for c in ("arrow", "server", "pi", "amber", "red", "ok")
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" font-family="{FONT}">'
            f"<title>{escape(self.title)}</title><defs>{markers}</defs>"
            f'<rect width="{self.w}" height="{self.h}" rx="16" fill="{self.t["bg"]}" stroke="{self.t["line"]}"/>'
            + "".join(self.parts)
            + "</svg>\n"
        )



def header(s, title, subtitle):
    s.text(40, 54, title, size=26, weight=700)
    s.text(40, 82, subtitle, size=15, color="muted")


def legend(s, x, y, items):
    for color, label, dash in items:
        s.path(f"M{x} {y} H{x + 34}", color=color, width=2.6, dash=dash, head=False)
        s.text(x + 44, y + 5, label, size=13, color="muted")
        x += 54 + len(label) * 7.1


COLS = (40, 274, 508, 742, 976)
CW = 204


def scan_to_gate(t):
    s = Svg(1200, 640, "From QR scan to controller output and offline free-pass during a sustained disconnect", t)
    header(s, "From QR scan to controller output", "The partner platform authorizes individual member access. The device resolves the grant’s direction before requesting a pulse.")
    legend(s, 742, 50, [("amber", "platform", None), ("pi", "device agent", None), ("ok", "controller", None)])
    steps = [
        ("pi", "A fresh QR", ["The Pi requests and", "refreshes the QR over", "its own connection."]),
        ("amber", "Member scans", ["The member scans the", "QR in the platform’s", "mobile app."]),
        ("amber", "Platform decides", ["The platform checks its", "membership rules and", "sends an access grant."]),
        ("pi", "Validate grant", ["Resolve entry or exit.", "After a grant, request", "the next QR."]),
        ("ok", "Controller signalled", ["For a new pulse, signal", "the controller and show", "available member details."]),
    ]
    for i, (accent, title, body) in enumerate(steps):
        x = COLS[i]
        s.card(x, 112, CW, 122, title, body, accent)
        if i < 4:
            s.path(f"M{x + CW + 5} 173 H{COLS[i + 1] - 7}")

    # Link-loss timeline.
    s.text(40, 300, "When the link to the platform drops", size=16, weight=650)
    top, h = 330, 70
    segs = [
        (40, 222, "pi_tint", "pi", "QR on screen", ["Connected"]),
        (222, 403, "pi_tint", "pi", "Brief drop", ["No notice yet"]),
        (403, 692, "amber_tint", "amber", "Connecting notice", ["Retries at 1 s intervals by default"]),
        (692, 910, "ok_tint", "ok", "Offline free-pass", ["Staff see “offline mode”"]),
        (910, 1160, "pi_tint", "pi", "Offline request cleared", ["Other free-mode requests can remain"]),
    ]
    for x0, x1, fill, color, title, body in segs:
        s.rect(x0, top, x1 - x0, h, fill=fill, stroke=fill, rx=8)
        s.text(x0 + 14, top + 26, title, size=14, weight=650, color=color)
        s.text(x0 + 14, top + 48, " ".join(body), size=12.5, color="muted")
    for x, label in [(222, "link lost"), (692, "grace period ends"), (910, "stable connection restored")]:
        s.path(f"M{x} {top - 8} V{top + h + 8}", color="red" if x == 222 else ("ok" if x == 910 else "amber"), width=1.6, dash="4 4", head=False)
        s.text(x, top + h + 26, label, size=13, color="muted", anchor="middle")
    s.text(40, 470, "How the agent handles each request", size=16, weight=650)
    notes = [
        ("amber", "Member access", ["Only online member approvals depend on the", "partner platform. Staff can request free", "mode locally."]),
        ("pi", "Overlapping grants", ["A same-direction grant can extend an active", "pulse. The agent logs and ignores an", "opposing grant."]),
        ("ok", "Offline free-pass", ["A sustained disconnect triggers free passage.", "A stable reconnection clears the offline", "request independently of staff or platform mode."]),
    ]
    for i, (accent, title, body) in enumerate(notes):
        x = 40 + i * 380
        s.card(x, 490, 360, 120, title, body, accent, size=13.5)
    return s


def architecture(t):
    s = Svg(1200, 760, "Architecture of the turnstile device agent and its fleet operations", t)
    header(s, "Where everything runs", "One Raspberry Pi per turnstile. The platform link and telemetry start at the device; the collector never commands it.")
    s.rect(24, 104, 600, 600, fill="surface", dash="6 5", rx=16)
    s.rect(648, 104, 528, 270, fill="surface", dash="6 5", rx=16)
    s.rect(648, 398, 528, 306, fill="surface", dash="6 5", rx=16)
    s.text(44, 132, "CUSTOMER SITE · ONE PI PER TURNSTILE", size=12.5, color="muted", weight=700, extra=' letter-spacing="1"')
    s.text(668, 132, "PARTNER ACCESS PLATFORM", size=12.5, color="muted", weight=700, extra=' letter-spacing="1"')
    s.text(668, 426, "OPERATIONS · COMPANY CLOUD", size=12.5, color="muted", weight=700, extra=' letter-spacing="1"')

    s.card(48, 152, 552, 300, "Device agent · Raspberry Pi 3", ["Python, asyncio · systemd user service in the kiosk session"], "pi", size=13.5)
    rows = [
        "Protocol adapter · resolves grant direction",
        "Runtime: connection, QR lifecycle, offline policy",
        "Kiosk display: local web UI in Chromium",
        "Output port: Field GPIO · serial implementation",
        "Health, safe audit log, one-way reporter",
    ]
    for i, r in enumerate(rows):
        y = 220 + i * 44
        s.rect(70, y, 508, 36, fill="pi_tint", stroke="pi_tint", rx=8)
        s.text(86, y + 23, r, size=14)

    s.card(48, 488, 260, 96, "Turnstile", ["entry · exit · free pass"], "ok")
    s.card(340, 488, 260, 96, "Touch or HDMI display", ["QR, greeting, staff panel"], "muted")
    s.card(48, 604, 552, 76, "USB card reader (optional)", ["Sends a card code to the agent for a platform access request."], "muted", size=13)
    s.path("M324 602 V456", color="pi", width=2)
    s.path("M178 458 V482", color="ok", width=2.2)
    s.path("M470 458 V482", both=True)

    s.card(672, 152, 480, 196, "Access platform (third party)", ["members, packages, mobile app,", "access decisions"], "amber")
    s.path("M600 232 H666", color="amber", width=2.2, both=True)
    s.text(634, 222, "WSS", size=12.5, color="amber", anchor="middle")
    s.lines(692, 262, ["Device-initiated, authenticated per device;", "QR requests, access grants, free and", "maintenance modes."], size=13, gap=19)

    s.card(672, 446, 215, 112, "Collector", ["Heartbeats, logs, device registry", "Alarm eligibility and metrics"], "server", size=13)
    s.card(953, 446, 199, 112, "Prometheus", ["Scrapes metrics", "Evaluates alert rules"], "server", size=13)
    s.card(672, 590, 215, 90, "Alertmanager", ["Sends alerts to Telegram"], "server", size=13)
    s.card(953, 590, 199, 90, "Grafana", ["Queries fleet metrics"], "server", size=13)
    s.path("M600 410 H636 V500 H666", color="server", width=2.2)
    s.text(612, 398, "push", size=12.5, color="server")
    s.path("M949 505 H892", color="server", width=2)
    s.text(920, 492, "scrape", size=12.5, color="server", anchor="middle")
    s.path("M988 560 V574 H780 V585", color="server", width=2)
    s.path("M1054 587 V563", color="server", width=2)

    legend(s, 40, 734, [
        ("amber", "live access link", None),
        ("server", "one-way telemetry", None),
        ("ok", "physical output", None),
    ])
    s.text(1160, 739, "Operator access and releases go over a private Tailscale network.", size=12.5, color="muted", anchor="end")
    return s


def operations(t):
    s = Svg(1200, 560, "From a fresh card to a monitored device, and how releases reach it", t)
    header(s, "Life of a device", "In October 2026 I combined provisioning and verification into one resumable bench command.")
    legend(s, 860, 50, [("pi", "on the device", None), ("server", "operations", None)])
    steps = [
        ("pi", "Bench setup", ["Run the full command", "or stop at prepared", "or deferred."]),
        ("pi", "Platform check", ["On a full run, check", "the device’s credential", "before registration."]),
        ("server", "Registration", ["A pending registry entry", "does not arm device", "paging."]),
        ("pi", "Software handoff", ["READY or findings", "Then verify both", "directions on site."]),
        ("server", "Device paging", ["Arm after activation", "and burn-in, using", "venue hours."]),
    ]
    for i, (accent, title, body) in enumerate(steps):
        x = COLS[i]
        s.card(x, 112, CW, 122, title, body, accent, number=i + 1)
        if i < 4:
            s.path(f"M{x + CW + 5} 173 H{COLS[i + 1] - 7}")

    s.text(40, 296, "Every release since late June 2026", size=16, weight=650)
    rel = [
        ("server", "Exact tag", ["Transfer a verified bundle", "from the operator machine."]),
        ("pi", "Environment", ["Reuse a healthy match or", "prepare a hash-pinned", "candidate."]),
        ("pi", "Pre-switch checks", ["Check runtime and display.", "A failed check can leave", "the live environment intact."]),
        ("ok", "Activate and verify\nservice", ["Restart in the kiosk session.", "Check enabled and active."]),
        ("red", "Recover or redeploy\nknown-good tag", ["Attempt recovery. Operator", "selects the rollback tag."]),
    ]
    for i, (accent, title, body) in enumerate(rel):
        x = COLS[i]
        s.card(x, 316, CW, 126, title, body, accent, size=13)
        if i < 3:
            s.path(f"M{x + CW + 5} 377 H{COLS[i + 1] - 7}")
    s.path(f"M{COLS[3] + CW / 2} 446 V478 H{COLS[4] + CW / 2} V446", color="red", width=1.8, dash="4 4")
    s.text(960, 501, "If post-restart verification fails", size=13, color="red", anchor="middle")
    s.text(40, 528, "System package updates are a separate maintenance step.", size=13.5, color="muted")
    return s


MONTHS = ["May 2026", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
RELEASES = [  # (month index + day fraction, version, major)
    (0.18, "1.0", True), (0.21, "1.1", False), (1.40, "1.2", True), (1.80, "1.3", True), (1.87, "1.3.1", False),
    (2.10, "1.4", True), (2.17, "1.4.1", False), (2.43, "1.5", True), (2.45, "1.5.1", False), (2.47, "1.5.2", False),
    (2.50, "1.5.3", False), (2.52, "1.5.4", False), (3.47, "1.6", True), (3.70, "1.7", True), (3.83, "1.8", True),
    (4.38, "1.8.1", False), (5.25, "1.9", True), (5.67, "1.10", True), (5.77, "1.10.1", False), (5.83, "1.11", True),
]
CALLOUTS = [  # (x position in months, above the axis?, title, body, accent)
    (0.18, True, "v1.0–1.1 · first stable releases", "landscape, then portrait kiosk", "pi"),
    (1.40, False, "v1.2–1.3 · ready for the field", "health checks; bundle provisioning", "server"),
    (2.10, True, "v1.4–1.5 · resilience, new hardware", "reconnects; single-pin turnstiles", "pi"),
    (3.47, False, "v1.6–1.8 · card access, live screen", "entry and exit aware; relay profile", "pi"),
    (4.60, True, "19 Sep · ten-hour connectivity loss", "Eight devices entered offline free-pass.", "red"),
    (5.25, False, "v1.9–1.11 · a watched fleet", "alerting, one-command setup, staff panel", "server"),
]


def timeline(t):
    s = Svg(1200, 372, "Releases from May to October 2026", t)
    header(s, "Releases in the field", "Twenty stable releases from May to October 2026. I delivered field updates remotely.")
    x0, x1, axis = 70, 1150, 214
    step = (x1 - x0) / len(MONTHS)

    def X(m):
        return x0 + m * step

    s.path(f"M{x0} {axis} H{x1}", color="line", width=1.6, head=False)
    for i, name in enumerate(MONTHS):
        s.path(f"M{X(i)} {axis - 6} V{axis + 6}", color="line", width=1.2, head=False)
        s.text(X(i) + 8, axis + 24, name, size=13.5, color="muted")
    for m, above, title, body, accent in CALLOUTS:
        y = 118 if above else 262
        x = min(X(m) - 10, x1 - 262)
        if above:
            s.path(f"M{X(m):.1f} {y + 56} V{axis - 9}", color=accent, width=1.3, dash="3 3", head=False)
        else:
            s.path(f"M{X(m):.1f} {axis + 9} V{y}", color=accent, width=1.3, dash="3 3", head=False)
        s.rect(x, y, 262, 56, fill="card", stroke="line", rx=10)
        s.add(f'<rect x="{x}" y="{y + 10}" width="4" height="36" rx="2" fill="{t[accent]}"/>')
        s.text(x + 16, y + 23, title, size=13.5, weight=650)
        s.text(x + 16, y + 43, body, size=12.5, color="muted")
    for m, ver, major in RELEASES:
        r = 6.5 if major else 4
        s.add(f'<circle cx="{X(m):.1f}" cy="{axis}" r="{r}" fill="{t["pi"] if major else t["bg"]}" stroke="{t["pi"]}" stroke-width="2"/>')

    s.text(x0, 350, "Filled dots mark feature releases. Open dots mark fixes.", size=12.5, color="muted")
    return s

def main():
    for name, build in [("scan-to-gate", scan_to_gate), ("architecture", architecture), ("operations", operations), ("timeline", timeline)]:
        for theme, t in THEMES.items():
            (OUT / f"{name}-{theme}.svg").write_text(build(t).render(), encoding="utf-8")


if __name__ == "__main__":
    main()

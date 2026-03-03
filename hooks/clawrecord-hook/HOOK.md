---
name: clawrecord-hook
description: "ClawRecord gamification hook — tracks OpenClaw usage events for the gamification system"
metadata:
  {
    "openclaw": {
      "emoji": "🎮",
      "events": ["command", "message"],
      "export": "default",
      "requires": { "bins": ["node"] },
      "install": [{ "id": "workspace", "kind": "workspace", "label": "ClawRecord Hook" }]
    }
  }
---

# ClawRecord Hook

Captures OpenClaw usage events in real-time for the ClawRecord gamification system.

## Events Tracked

- `command` — session commands (`/new`, `/reset`, `/stop`)
- `message:received` — inbound user messages
- `message:sent` — outbound assistant responses

## Output

Appends JSONL to `~/.openclaw/logs/clawrecord.jsonl`.

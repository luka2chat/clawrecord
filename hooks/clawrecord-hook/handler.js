import * as fs from "node:fs/promises";
import * as path from "node:path";
import * as os from "node:os";

const resolveLogFile = () => {
  const stateDir =
    process.env.OPENCLAW_STATE_DIR || path.join(os.homedir(), ".openclaw");
  return path.join(stateDir, "logs", "clawrecord.jsonl");
};

const appendEvent = async (record) => {
  const logFile = resolveLogFile();
  await fs.mkdir(path.dirname(logFile), { recursive: true });
  await fs.appendFile(logFile, JSON.stringify(record) + "\n", "utf-8");
};

const handler = async (event) => {
  const base = {
    ts: event.timestamp?.toISOString?.() || new Date().toISOString(),
    session: event.sessionKey || "unknown",
  };

  try {
    if (event.type === "command") {
      await appendEvent({
        ...base,
        event: `command.${event.action}`,
        data: {
          action: event.action,
          source: event.context?.commandSource || "unknown",
          senderId: event.context?.senderId || "unknown",
        },
      });
    } else if (event.type === "message") {
      const isReceived = event.action === "received";
      await appendEvent({
        ...base,
        event: isReceived ? "message.received" : "message.sent",
        data: {
          direction: isReceived ? "inbound" : "outbound",
          from: event.context?.from,
          to: event.context?.to,
          channelId: event.context?.channelId,
          success: event.context?.success,
          contentLength: event.context?.content?.length || 0,
        },
      });
    }
  } catch (_err) {
    // Silently ignore write failures to avoid disrupting OpenClaw
  }
};

export default handler;

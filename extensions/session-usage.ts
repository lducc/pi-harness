/**
 * session-usage: status-bar Claude plan quota (from claude-bridge rate-limit
 * headers) and context size / prompt-cache guard. `/usage-now` prints both.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const PREFIX = "anthropic-ratelimit-unified-";
const THRESHOLDS = [150_000, 300_000, 500_000];

let quota: { h5?: number; h5Reset?: number; d7?: number; status?: string } | undefined;
let ctxText: string | undefined;
let crossed = 0;
let missWarned = false;

const pct = (v: string | undefined) => {
	if (v === undefined || isNaN(Number(v))) return undefined;
	const n = Number(v);
	return Math.round(n <= 1 ? n * 100 : n);
};

const k = (n: number) => (n >= 1_000_000 ? `${+(n / 1e6).toFixed(1)}M` : `${Math.round(n / 1000)}k`);

function quotaText() {
	if (!quota) return undefined;
	let s = "claude";
	if (quota.h5 !== undefined) {
		s += ` 5h ${quota.h5}%`;
		if (quota.h5Reset) {
			const t = new Date(quota.h5Reset * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
			s += ` (resets ${t})`;
		}
	}
	if (quota.d7 !== undefined) s += ` · 7d ${quota.d7}%`;
	if (quota.status && quota.status !== "allowed") s += " · LIMITED";
	return s;
}

export default function (pi: ExtensionAPI) {
	pi.on("after_provider_response", (event, ctx) => {
		const h = event.headers;
		const h5 = pct(h[`${PREFIX}5h-utilization`]);
		const d7 = pct(h[`${PREFIX}7d-utilization`]);
		if (h5 === undefined && d7 === undefined) return;
		quota = { h5, h5Reset: Number(h[`${PREFIX}5h-reset`]) || undefined, d7, status: h[`${PREFIX}status`] };
		ctx.ui.setStatus("claude", quotaText());
	});

	pi.on("agent_end", (_event, ctx) => {
		const usage = ctx.getContextUsage();
		const last = ctx.sessionManager
			.getEntries()
			.filter((e: any) => e.type === "message" && e.message.role === "assistant" && e.message.usage)
			.pop() as any;
		let hit: number | undefined;
		let prompt = 0;
		if (last) {
			const u = last.message.usage;
			prompt = u.input + u.cacheRead + u.cacheWrite;
			if (prompt > 0) hit = Math.round((100 * u.cacheRead) / prompt);
		}
		if (usage?.tokens) {
			ctxText = `ctx ${k(usage.tokens)}/${k(usage.contextWindow)}`;
			if (hit !== undefined) ctxText += ` · cache ${hit}%`;
			ctx.ui.setStatus("ctx", ctxText);
			while (crossed < THRESHOLDS.length && usage.tokens >= THRESHOLDS[crossed]) {
				crossed++;
				if (crossed === THRESHOLDS.length || usage.tokens < THRESHOLDS[crossed]) {
					ctx.ui.notify(`Context is ${k(usage.tokens)} tokens. Type the next task after /handoff, or clear the line to continue.`, "warning");
					// Prefill so starting a fresh session is one line, not a remembered command.
					if (!ctx.ui.getEditorText()) ctx.ui.setEditorText("/handoff ");
				}
			}
		}
		if (!missWarned && hit !== undefined && hit < 50 && prompt > 50_000) {
			missWarned = true;
			ctx.ui.notify(`Cache miss on a ${k(prompt)}-token prompt (hit ${hit}%).`, "warning");
		}
	});

	pi.registerCommand("usage-now", {
		description: "Show Claude plan quota and context usage",
		handler: async (_args, ctx) => {
			const q = quotaText() ?? "no Claude quota data yet; it arrives with the next claude-bridge response";
			ctx.ui.notify(`${q}\n${ctxText ?? "no context data yet"}`, "info");
		},
	});
}

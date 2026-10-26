/**
 * memory: puts the user's knowledge base in every session.
 *
 * Adds memory/me.md plus a one-line index of the other notes (from each note's
 * `description:` frontmatter) as a prompt section. The agent opens notes on demand.
 * `/memory off` leaves it out for this session, like a temporary chat.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, relative } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const DIR = join(homedir(), ".pi", "agent", "memory");
const SKIP = new Set(["me.md", "inbox.md", "rejected.md"]);

function notes(dir: string): string[] {
	return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
		const p = join(dir, e.name);
		if (e.isDirectory()) return notes(p);
		return e.name.endsWith(".md") && !SKIP.has(e.name) ? [p] : [];
	});
}

function description(path: string): string {
	return readFileSync(path, "utf8").match(/^description:\s*(.+)$/m)?.[1] ?? "";
}

function stripFrontmatter(text: string): string {
	return text.replace(/^---\n[\s\S]*?\n---\n/, "");
}

function build(): string | undefined {
	const me = join(DIR, "me.md");
	if (!existsSync(me)) return undefined;
	const index = notes(DIR)
		.sort()
		.map((p) => `- memory/${relative(DIR, p)}: ${description(p)}`)
		.join("\n");
	return `The user's memory lives in ~/.pi/agent/memory (an Obsidian vault folder). Their profile is below. Read a note from the index when the task touches its topic. Do not write to memory directly; propose additions to memory/inbox.md as the global rules say.

${stripFrontmatter(readFileSync(me, "utf8")).trim()}

Notes:
${index}`;
}

export default function (pi: ExtensionAPI) {
	let on = true;

	pi.on("before_agent_start", (event) => {
		const text = on ? build() : undefined;
		if (text) event.systemPromptOptions.sections.user_memory = text;
		else delete event.systemPromptOptions.sections.user_memory;
	});

	pi.registerCommand("memory", {
		description: "Turn the memory profile on or off for this session: /memory on|off",
		handler: async (args, ctx) => {
			on = args.trim() !== "off";
			ctx.ui.setStatus("memory", on ? undefined : ctx.ui.theme.fg("warning", "memory off"));
			ctx.ui.notify(on ? "Memory on" : "Memory off for this session", "info");
		},
	});
}

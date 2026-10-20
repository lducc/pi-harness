/**
 * exp-status: shows the `exp` experiment ledger in pi's status bar when the cwd
 * belongs to an exp project (an exp.toml in the cwd or a parent directory).
 *
 * Read-only: it only runs `exp board --json`. `/exp` prints the full board.
 */

import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const STATUS_KEY = "exp";

interface BoardRow {
	id: string;
	status: string;
	metric: number | null;
	best: boolean;
}

interface Board {
	primary: string;
	rows: BoardRow[];
}

function findProjectRoot(start: string): string | undefined {
	let dir = start;
	while (true) {
		if (existsSync(join(dir, "exp.toml"))) return dir;
		const parent = dirname(dir);
		if (parent === dir) return undefined;
		dir = parent;
	}
}

function runExp(cwd: string, args: string[]): Promise<string> {
	return new Promise((resolve, reject) => {
		execFile("exp", args, { cwd, timeout: 15_000 }, (error, stdout) => {
			if (error) reject(error);
			else resolve(stdout);
		});
	});
}

function summarize(board: Board): string {
	const running = board.rows.filter((row) => row.status === "running").length;
	const best = board.rows.find((row) => row.best);
	const parts = [`exp ${board.rows.length} runs`];
	if (running > 0) parts.push(`${running} running`);
	if (best && best.metric !== null) parts.push(`best ${best.id} ${board.primary}=${best.metric}`);
	return parts.join(" · ");
}

export default function (pi: ExtensionAPI) {
	async function refresh(ctx: any): Promise<void> {
		const root = findProjectRoot(ctx.cwd ?? process.cwd());
		if (!root) {
			ctx.ui.setStatus(STATUS_KEY, undefined);
			return;
		}
		try {
			const board = JSON.parse(await runExp(root, ["board", "--json"])) as Board;
			ctx.ui.setStatus(STATUS_KEY, ctx.ui.theme.fg("accent", summarize(board)));
		} catch {
			ctx.ui.setStatus(STATUS_KEY, ctx.ui.theme.fg("warning", "exp: board unavailable"));
		}
	}

	pi.on("session_start", async (_event, ctx) => refresh(ctx));
	pi.on("agent_end", async (_event, ctx) => refresh(ctx));

	pi.registerCommand("exp", {
		description: "Show the experiment board for this project",
		handler: async (_args, ctx) => {
			const root = findProjectRoot(ctx.cwd ?? process.cwd());
			if (!root) {
				ctx.ui.notify("No exp.toml in this directory or its parents. Run `exp init` first.", "info");
				return;
			}
			ctx.ui.notify(await runExp(root, ["board"]), "info");
			await refresh(ctx);
		},
	});
}

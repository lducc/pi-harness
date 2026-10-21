/**
 * review: spaced re-quiz.
 *
 * Every missed or "I don't know" `quiz` answer becomes a card in ~/learning/cards.jsonl.
 * `/review` shows up to 10 due cards in random order. You answer from memory first,
 * then see the answer and grade yourself. Free recall instead of options because
 * recognition is not retrieval.
 */

import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const CARDS = join(homedir(), "learning", "cards.jsonl");
const GAPS = [1, 3, 7, 21, 60]; // days; a card passed at the last gap is retired
const MAX_PER_SESSION = 10;

interface Card {
	q: string;
	a: string;
	why: string;
	created: string;
	session: string;
	step: number;
	due: string;
	done: boolean;
}

function today(offsetDays = 0): string {
	const d = new Date();
	d.setDate(d.getDate() + offsetDays);
	return d.toLocaleDateString("en-CA"); // YYYY-MM-DD in local time
}

function loadCards(): Card[] {
	if (!existsSync(CARDS)) return [];
	return readFileSync(CARDS, "utf8").split("\n").filter(Boolean).map((line) => JSON.parse(line));
}

function dueCards(cards: Card[]): Card[] {
	return cards.filter((c) => !c.done && c.due <= today());
}

export default function (pi: ExtensionAPI) {
	function showDue(ctx: any) {
		const n = dueCards(loadCards()).length;
		ctx.ui.setStatus("review", n > 0 ? ctx.ui.theme.fg("warning", `review ${n} due`) : undefined);
	}

	pi.on("session_start", async (_event, ctx) => showDue(ctx));

	pi.on("tool_result", async (event: any, ctx) => {
		if (event.toolName !== "quiz") return;
		const d = event.details;
		if (d?.status !== "answered" || d.correct) return;
		const key = new Set(d.correctIndices);
		const card: Card = {
			q: d.context ? `${d.question}\n${d.context}` : d.question,
			a: d.options.filter((o: any) => key.has(o.index)).map((o: any) => o.label).join("; "),
			why: d.explanation ?? "",
			created: today(),
			session: ctx.sessionManager.getSessionFile() ?? "",
			step: 0,
			due: today(GAPS[0]),
			done: false,
		};
		mkdirSync(dirname(CARDS), { recursive: true });
		appendFileSync(CARDS, `${JSON.stringify(card)}\n`);
	});

	pi.registerCommand("review", {
		description: "Re-quiz due cards from past quiz misses",
		handler: async (_args, ctx) => {
			const cards = loadCards();
			const due = dueCards(cards).sort(() => Math.random() - 0.5).slice(0, MAX_PER_SESSION);
			if (due.length === 0) {
				ctx.ui.notify("No cards due", "info");
				return;
			}
			let reviewed = 0;
			for (const card of due) {
				const recall = await ctx.ui.input(card.q, "Answer from memory");
				if (recall === undefined) break;
				const verdict = await ctx.ui.select(
					`Answer: ${card.a}\n${card.why}\n\nYou wrote: ${recall || "(nothing)"}`,
					["Got it", "Missed"],
				);
				if (verdict === undefined) break;
				card.step = verdict === "Got it" ? card.step + 1 : 0;
				card.done = card.step >= GAPS.length;
				if (!card.done) card.due = today(GAPS[card.step]);
				reviewed++;
			}
			writeFileSync(CARDS, cards.map((c) => JSON.stringify(c)).join("\n") + "\n");
			ctx.ui.notify(`Reviewed ${reviewed} of ${due.length}`, "info");
			showDue(ctx);
		},
	});
}

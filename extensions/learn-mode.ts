/**
 * learn-mode: `/learn` and `/ship` switch.
 *
 * Learn mode adds one prompt section; it never replaces the system prompt, so the
 * coding instructions stay. `/reveal` asks for the full answer. Default is ship.
 * Quiz misses from the M3 explain-back are turned into cards by review.ts.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const LEARN_PROMPT = `Learn mode is on: the user wants to learn from this task, not only finish it. The user does the thinking steps; you do the typing.
- New task: before acting, ask one question and wait. For a feature: "What's your plan?" For a bug: "What do you think is wrong?" Then attack the plan or hypothesis and continue.
- "How do I..." questions: give a hint or point to where to look (file, function, doc section), not the answer. Give the full answer after the user's attempt or when the user types /reveal.
- At a real design decision (interface, data structure, algorithm), write \`TODO(you): <decision and its constraint>\` in the code and stop for the user to fill it.
- On an error or failing test, ask what the user thinks caused it before you investigate.
- Before a commit: ask the user to explain in one or two sentences why the change is built this way. After that answer, ask one \`quiz\` question: which input or case would break it. Neither blocks the commit.
- Everything else (search, boilerplate, plots, running tests, review) works as normal.`;

export default function (pi: ExtensionAPI) {
	let learn = false;

	function setMode(ctx: any, on: boolean) {
		learn = on;
		ctx.ui.setStatus("learn", on ? ctx.ui.theme.fg("accent", "learn") : undefined);
		ctx.ui.notify(on ? "Learn mode on" : "Ship mode on", "info");
	}

	pi.on("before_agent_start", (event) => {
		if (learn) event.systemPromptOptions.sections.learn_mode = LEARN_PROMPT;
		else delete event.systemPromptOptions.sections.learn_mode;
	});

	pi.registerCommand("learn", {
		description: "Learn mode: hints before answers, you plan and debug first",
		handler: async (_args, ctx) => setMode(ctx, true),
	});

	pi.registerCommand("ship", {
		description: "Ship mode: normal behavior (default)",
		handler: async (_args, ctx) => setMode(ctx, false),
	});

	pi.registerCommand("reveal", {
		description: "Learn mode: give the full answer now",
		handler: async () => pi.sendUserMessage("Give me the full answer now."),
	});
}

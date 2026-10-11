**Figure: LLM kernel agent optimization loop.** A task specification drives
candidate generation and kernel optimization. Candidates are compiled and
benchmarked on the GPU; correctness and performance feedback then returns to
the agent for iterative refinement. The blue stage marks the proposed
optimization component, while the dashed red path denotes feedback rather than
the primary execution flow.

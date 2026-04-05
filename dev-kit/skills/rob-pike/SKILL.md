---
name: rob-pike
description: Rob Pike's 5 Rules of Programming — a decision framework that prevents premature optimization and enforces measurement-driven development. Use when the user says "optimize", "slow", "performance", "bottleneck", "speed up", "make faster", "too slow", or any request to improve code speed/efficiency. Also use when you notice yourself about to suggest a performance optimization without measurement data. This is a thinking discipline, not a tooling workflow.
---

# Rob Pike's 5 Rules of Programming

A decision framework that prevents premature optimization and enforces measurement-driven development. Activates before and during performance-related code changes to block the most common mistake developers and LLMs make: optimizing without evidence.

This is not about implementation discipline (that's `karpathy`) or debugging (that's `systematic-debugging`). This is about the decision to optimize — ensuring that every performance change is driven by measurement, not intuition.

## Hard Gates

These rules have no exceptions.

1. **Do not optimize without measurement data.** If you haven't profiled, you don't know where the time is spent. Any change without measurement data is a guess.
2. **Do not optimize unless one part dominates.** If no single area overwhelms the rest, there is nothing worth optimizing. Spreading small improvements across many areas rarely matters.
3. **Check n before choosing algorithm complexity.** If n is small (and it usually is), the simple approach wins. Always measure before reaching for a fancier algorithm.
4. **Do not add complexity without re-measuring.** After any optimization change, measure again to confirm improvement. If it didn't help, revert it.
5. **Do not optimize during implementation.** Write correct, simple code first. Optimization is a separate task that requires its own measurement cycle.

## When To Use

- When the user says "optimize", "slow", "performance", "bottleneck", "speed up", "make faster", or "too slow"
- When you notice yourself about to suggest a performance optimization without measurement data
- When considering algorithm or data structure changes for performance reasons
- When evaluating whether a reported performance issue warrants code changes

## When NOT To Use

- During initial implementation — write correct, simple code first
- When the user has not reported a performance problem
- When the code is correct and readable — don't optimize "just in case"
- For correctness issues (use `systematic-debugging` instead)
- For code quality issues (use `simplify-code` instead, or `clean-ai-slop` if the code was AI-generated)

## The Rules

1. **You can't tell where a program is going to spend its time.** Bottlenecks occur in surprising places. Don't guess — prove it.
2. **Measure.** Don't tune for speed until you've measured. Even then, don't unless one part of the code overwhelms the rest.
3. **Fancy algorithms are slow when n is small, and n is usually small.** Big-O doesn't matter when constants dominate. Use Rule 2 first.
4. **Fancy algorithms are buggier than simple ones.** Use simple algorithms and simple data structures.
5. **Data dominates.** Choose the right data structures and the algorithms become self-evident. "Write stupid code that uses smart objects."

## How to Apply

### Before Any Optimization

#### Step 0: Check for Existing Instrumentation

Before asking "have you measured?", determine whether measurement is even **possible** right now.

**Scan the codebase** for signs of existing instrumentation:
- Logging: look for logger imports, log calls, structured logging libraries
- Profiling: look for profiler imports, benchmark files, tracing setup
- Timing: look for duration measurements, stopwatch patterns, timing decorators
- APM/Observability: look for metrics exports, spans, trace contexts

**Then ask the user:**

1. If instrumentation **exists**: "I found logging/profiling in [locations]. Are there specific areas you suspect are slow, or should we look at what the existing measurements tell us?"
2. If instrumentation is **missing or sparse**: "There's no measurement in place to prove where time is being spent. Before optimizing anything — where do you suspect the bottleneck is? Let's add measurement there first, then let the data decide."

The goal is NOT to prescribe a specific tool — Claude already knows the right profiling approach for the language. The goal is to **make sure measurement exists before any optimization conversation continues.** If there is nothing to measure with, the first action is adding instrumentation, not changing code.

#### Step 1: Ask the Measurement Questions

Stop and ask these questions in order:

1. **"Have I measured?"** — If no, measure first. Any optimization without measurement data is premature. Use whatever profiling tool is natural for the project's language and ecosystem.
2. **"Does one part overwhelm the rest?"** — If no single area dominates, there is nothing worth optimizing. Small improvements spread across many areas rarely matter.
3. **"What's n?"** — If n is small (and it usually is), the simple O(n²) approach likely beats the clever O(n log n) one due to constants, cache behavior, and implementation complexity.
4. **"Is this a data structure problem?"** — Before changing the algorithm, consider whether a different data structure makes the problem trivial. The right structure often eliminates the need for a clever algorithm entirely.
5. **"Is the added complexity worth it?"** — Simple code that is 10% slower is almost always preferable to clever code that is fragile and hard to maintain.

## Anti-Patterns

| Impulse | Rule violated | Response |
|---|---|---|
| "This loop looks slow, let me optimize it" | Rule 1 | Have you profiled? The bottleneck may be elsewhere entirely. |
| "Let me add a cache here" | Rule 2 | Measure first. Does this path actually dominate runtime? |
| "Let me use a B-tree / trie / skip list" | Rule 3 | What's n? If small, a sorted slice + binary search wins. |
| "Let me implement a custom allocator" | Rule 4 | Start simple. Measure. Only get fancy if data forces you. |
| "The algorithm is O(n²), needs fixing" | Rule 3 | What's n? O(n²) with n=100 is 10μs. Measure first. |
| "Let me parallelize this" | Rule 2 | Is this actually CPU-bound? Measure. Often it's I/O. |

## Red Flags

Stop and reconsider if you catch yourself thinking:

- "This is obviously the bottleneck" — Rule 1 says you can't tell. Profile it.
- "The algorithm is O(n²), that's unacceptable" — What's n? Is n small? Have you measured?
- "Let me optimize this while I'm here" — Optimization is a separate task with its own measurement cycle
- "I don't need to profile, I know where the time goes" — You don't. Nobody does. That's Rule 1.
- "A few caches won't hurt" — Every cache adds complexity, invalidation logic, and potential bugs. Measure first.
- "This is too slow, let me rewrite it" — Rewrite for simplicity, not speed. Then measure.

## Minimal Checklist

Before and after any optimization change, verify:

- [ ] Measurement data exists identifying a specific bottleneck
- [ ] That bottleneck dominates overall runtime (not just a small fraction)
- [ ] I know what n is for the affected code path
- [ ] I considered whether a different data structure solves the problem more simply
- [ ] The proposed change is the simplest fix that addresses the measured problem
- [ ] I will re-measure after the change to confirm improvement

## Completion Standard

Optimization is disciplined when:

- Measurement data was collected before any code change
- The change targets a bottleneck that dominates runtime
- The simplest viable fix was chosen
- Post-change measurement confirms improvement
- No unnecessary complexity was introduced

If any of these are not met, the optimization needs revision.

## Transition

After optimization is complete:

- If the optimized code is harder to read → use `simplify-code` for general readability improvements, or `clean-ai-slop` if the code was AI-generated
- If the optimization introduced a bug → use `systematic-debugging` to investigate
- If the optimization didn't help → revert the change and report findings to the user
- If the code needs broader quality review → use `simplify-code`

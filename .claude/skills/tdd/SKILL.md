---
name: tdd
description: Test-driven development with red-green-refactor loop. Use when user wants to build/implement features, stories or fix bugs, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
---

# Test-Driven Development

## Philosophy

**Core principle**: Tests should verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't.

**Good tests** are integration-style: they exercise real code paths through public APIs. They describe _what_ the system does, not _how_ it does it. A good test reads like a specification - "user can checkout with valid cart" tells you exactly what capability exists. These tests survive refactors because they don't care about internal structure.

**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or verify through external means (like querying a database directly instead of using the interface). The warning sign: your test breaks when you refactor, but behavior hasn't changed. If you rename an internal function and tests fail, those tests were testing implementation, not behavior.


## Workflow

Before RED, use a sub-agent to do focused repository discovery:

- identify the relevant public interface or entry point
- find existing test files and conventions nearby
- summarize the smallest behavior slice to add next

Keep the main context focused on choosing the next behavior and making edits. Delegate repository research, test execution and failure analysis, and refactor scouting to sub-agents.

1. RED: Write ONE failing test that confirms ONE thing about the system.
2. GREEN: Write the minimal code to pass that test. Use a sub-agent to run the narrowest relevant test command, analyze the reason for any failure, and return a concise pass/fail summary to the main context that includes the likely cause and the next actionable fix.
3. REFRACTOR: Clean up code. Use a sub-agent to review the current implementation for targeted refactor opportunities that preserve behavior, then rerun the relevant tests after each refactor step and summarize any regressions.

For each remaining behavior, follow the above workflow. Don't write multiple tests at once, and don't write code for future tests until the current test passes.

### Refactor

Use a sub-agent during refactoring when you need a fresh pass on structure, duplication, or module boundaries without expanding the main context window.

In each refactor step, look for opportunities to improve design and maintainability:

- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Apply SOLID principles where natural
- [ ] Consider what new code reveals about existing code
- [ ] Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.
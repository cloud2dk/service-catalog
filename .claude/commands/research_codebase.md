# Research Codebase

You are tasked with conducting comprehensive research across the codebase to answer user questions by spawning parallel sub-agents and synthesizing their findings.

## Initial Setup:

When this command is invoked, respond with:
```
I'm ready to research the codebase. Please provide your research question or area of interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.

## Steps to follow after receiving the research query:

1. **Read any directly mentioned files first:**
   - If the user mentions specific files (tickets, docs, JSON), read them FULLY first
   - **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files
   - **CRITICAL**: Read these files yourself in the main context before spawning any sub-tasks
   - This ensures you have full context before decomposing the research

2. **Analyze and decompose the research question:**
   - Break down the user's query into composable research areas
   - Take time to think deeply about the underlying patterns, connections, and architectural implications the user might be seeking
   - Identify specific components, patterns, or concepts to investigate
   - Create a research plan using TodoWrite to track all subtasks
   - Consider which directories, files, or architectural patterns are relevant

3. **Spawn parallel sub-agent tasks for comprehensive research:**
   - Create multiple Task agents to research different aspects concurrently
   - We now have specialized agents that know how to do specific research tasks:

   **For codebase research:**
   - Use the **codebase-locator** agent to find WHERE files and components live
   - Use the **codebase-analyzer** agent to understand HOW specific code works
   - Use the **codebase-pattern-finder** agent if you need examples of similar implementations

   **For thoughts directory:**
   - Use the **thoughts-locator** agent to discover what documents exist about the topic
   - Use the **thoughts-analyzer** agent to extract key insights from specific documents (only the most relevant ones)

   **For web research (only if user explicitly asks):**
   - Use the **web-search-researcher** agent for external documentation

4. **Wait for all sub-agents to complete:**
   - Don't rush to conclusions or start writing before sub-agents finish
   - All parallel tasks must complete before synthesis

5. **Synthesize and analyze findings:**
   - Read and understand all sub-agent outputs
   - Look for patterns, connections, and insights across different sources
   - Identify gaps or areas needing follow-up investigation

6. **Generate comprehensive research document:**
   - Create a detailed research document with proper YAML frontmatter
   - Save to `thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-description.md`
   - Include all findings, references, and actionable insights
   - Generate GitHub permalinks for file references when possible

7. **Sync and present findings:**
   - Present the key findings to the user
   - Be ready to dive deeper into specific areas if requested

## Research Document Structure:

Use this template for research documents:

```yaml
---
date: YYYY-MM-DD
researcher: david
git_commit: [current_commit_hash]
branch: [current_branch]
tags: [relevant, tags, here]
status: completed
---

# Research: [Topic Description]

## Research Question
[The specific question being investigated]

## Summary
[Brief overview of key findings]

## Detailed Findings

### [Finding Category 1]
[Detailed analysis with file references]

### [Finding Category 2]
[More detailed analysis]

## Code References
- `file.py:123` - [Description of relevant code]
- `other.js:456` - [Another reference]

## Architecture Insights
[High-level patterns and architectural observations]

## Historical Context
[Information from thoughts directory or git history]

## Related Research
[Links to related documents or investigations]

## Open Questions
[Areas needing further investigation]
```

## Important Guidelines:

- **Always read mentioned files FULLY before spawning sub-agents**
- **Use parallel sub-agents for efficiency** - spawn multiple Task agents simultaneously
- **Include precise file:line references** in your research
- **Focus on both current code AND historical context** from thoughts directory
- **Handle follow-up questions** by appending to the same research document and updating frontmatter

## For follow-up research:
If the user asks follow-up questions about the same topic, append new findings to the existing research document and update the frontmatter with:
```yaml
last_updated: YYYY-MM-DD
last_updated_note: "Added investigation into [new area]"
```
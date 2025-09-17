---
type: research
date: 2025-09-17
author: david
status: completed
tags:
  - development-methodology
  - claude-commands
  - agent-framework
  - process-optimization
research_question: "How does HumanLayer's resource-plan-code cycle methodology work and what are the specific commands and agents that implement it?"
related_files:
  - ".claude/commands/"
  - ".claude/agents/"
repository_context: "cloud2dk/service-catalog"
---

# HumanLayer Resource-Plan-Code Methodology Research

## Research Question
How does HumanLayer's resource-plan-code cycle methodology work and what are the specific commands and agents that implement it?

## Summary
HumanLayer has developed a sophisticated 5-command development cycle supported by 6 specialized agents that transforms chaotic software development into a systematic, documentable, and repeatable process. The methodology emphasizes parallel agent processing, structured documentation, human oversight, and progressive enhancement across research → planning → implementation → commit → documentation phases.

## Detailed Findings

### Core Command Architecture

#### 1. `/research_codebase` Command
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/research_codebase.md`
- **Purpose**: Comprehensive codebase investigation using parallel sub-agents
- **Process**:
  1. Read explicitly mentioned files completely
  2. Decompose research question into subtasks
  3. Create research plan using TodoWrite
  4. Spawn parallel specialized agents
  5. Generate structured research document with YAML frontmatter
- **Key Agents Used**: codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer
- **Output Format**: Structured markdown with sections for Research Question, Summary, Detailed Findings, Code References, Architecture Insights, Historical Context, Related Research, Open Questions

#### 2. `/create_plan` Command
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/create_plan.md`
- **Purpose**: Collaborative, iterative technical planning
- **Process**:
  1. Context gathering - read ALL mentioned files
  2. Spawn parallel research tasks
  3. Present findings with design options
  4. Get user alignment on approach
  5. Create structured plan with specific template
  6. Iterate based on feedback
- **Key Principles**: "Be skeptical, be thorough, be practical"
- **Template Sections**: Overview, Current State Analysis, Desired End State, Implementation Phases, Success Criteria, Testing Strategy, Performance Considerations

#### 3. `/implement_plan` Command
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/implement_plan.md`
- **Purpose**: Progress-tracked plan execution with adaptation capability
- **Process**:
  1. Read entire plan and related files
  2. Create todo list for progress tracking
  3. Check off completed items in plan file
  4. Run verification (`make check test`) at natural stopping points
  5. Handle plan deviations with structured communication
- **Deviation Handling Format**:
  ```
  Issue in Phase [N]:
  Expected: [what plan says]
  Found: [actual situation]
  Why this matters: [explanation]
  ```

#### 4. `/commit` Command
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/commit.md`
- **Purpose**: Atomic commit management with thoughtful staging
- **Process**:
  1. Review conversation history
  2. Run `git status` and `git diff`
  3. Plan commits logically
  4. Get user approval
  5. Execute with precise `git add` (no `-A` or `.`)
- **Standards**: Imperative mood, explain "why", no AI attribution, atomic commits

#### 5. `/describe_pr` Command
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/describe_pr.md`
- **Purpose**: Comprehensive PR documentation generation
- **Process**: 9-step workflow using GitHub CLI
  1. Locate PR description template
  2. Identify specific PR
  3. Check existing descriptions
  4. Gather PR metadata via `gh` commands
  5. Perform deep code change analysis
  6. Verify and test changes
  7. Generate detailed description
  8. Save and sync description
  9. Update PR
- **Focus**: Explain "why" changes matter, user-facing impacts, technical details

### Specialized Agent Framework

#### 1. `codebase-locator` Agent
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/agents/codebase-locator.md`
- **Purpose**: Systematic file and component discovery
- **Methodology**: Broad keyword search → language-specific exploration → pattern matching
- **Key Principle**: "Don't read file contents - Just report locations"
- **Output**: Grouped file locations by type with full repository paths

#### 2. `codebase-analyzer` Agent
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/agents/codebase-analyzer.md`
- **Purpose**: Deep implementation analysis with surgical precision
- **Methodology**: Read entry points → follow code paths → understand key logic
- **Key Principle**: Focus on "how" not "what" or "why"
- **Output**: Overview, entry points, core implementation, data flow, key patterns with precise file:line references

#### 3. `codebase-pattern-finder` Agent
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/agents/codebase-pattern-finder.md`
- **Purpose**: Locate and extract reusable code patterns
- **Categories**: API patterns, data patterns, component patterns, testing patterns
- **Output**: Working code examples with context and best practices
- **Key Principle**: Show practical, working code with multiple implementation variations

#### 4. `thoughts-locator` Agent
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/agents/thoughts-locator.md`
- **Purpose**: Document discovery within structured thoughts/ directory
- **Search Scope**: shared/, personal dirs, global/, searchable/
- **Key Principle**: Efficient discovery and categorization, not content analysis
- **Output**: Grouped documents by type with brief descriptions

#### 5. `thoughts-analyzer` Agent
- **Location**: `https://github.com/humanlayer/humanlayer/blob/main/.claude/agents/thoughts-analyzer.md`
- **Purpose**: Extract high-value insights from documentation
- **Focus Areas**: Concrete decisions, trade-offs, constraints, lessons learned, action items
- **Key Principle**: Be a "curator of insights" not a document summarizer
- **Output**: Structured analysis with key decisions and actionable insights

#### 6. `web-search-researcher` Agent
- **Purpose**: External research capabilities (mentioned in research_codebase.md)
- **Integration**: Works with other agents for comprehensive investigation

## Code References

Key repository structure:
```
.claude/
├── commands/
│   ├── research_codebase.md
│   ├── create_plan.md
│   ├── implement_plan.md
│   ├── commit.md
│   └── describe_pr.md
└── agents/
    ├── codebase-analyzer.md
    ├── codebase-locator.md
    ├── codebase-pattern-finder.md
    ├── thoughts-analyzer.md
    ├── thoughts-locator.md
    └── web-search-researcher.md
```

## Architecture Insights

### Process Flow
1. **Research Phase**: Parallel agent investigation → structured documentation
2. **Planning Phase**: Collaborative plan creation → user feedback iteration
3. **Implementation Phase**: Plan-driven development → progress tracking → continuous verification
4. **Commit Phase**: Atomic commit planning → user approval → precise execution
5. **Documentation Phase**: Comprehensive PR description → template-based approach

### Key Design Patterns
- **Parallel Agent Coordination**: Multiple specialized agents work simultaneously
- **Structured Templates**: YAML frontmatter + consistent markdown sections
- **Progressive Enhancement**: Each phase builds on previous with checkbox tracking
- **Human-in-the-Loop**: Required approval for high-stakes operations
- **Skeptical Collaboration**: Question assumptions, verify understanding

### Priority System
```
TODO(0): Critical - never merge
TODO(1): High - architectural flaws, major bugs
TODO(2): Medium - minor bugs, missing features
TODO(3): Low - polish, tests, documentation
TODO(4): Questions/investigations needed
PERF: Performance optimization opportunities
```

## Historical Context

HumanLayer developed this methodology to address:
- **Chaotic Development**: Lack of systematic approach to complex software tasks
- **Context Loss**: Information scattered across conversations and iterations
- **Human Oversight**: Need for approval in high-stakes AI-assisted development
- **Scalability**: Process that works for small features to large architectural changes

## Related Research

- **Contributing Guidelines**: `https://github.com/humanlayer/humanlayer/blob/main/CONTRIBUTING.md`
- **Claude Instructions**: `https://github.com/humanlayer/humanlayer/blob/main/CLAUDE.md`
- **Development Conventions**: Priority-based TODO system, make-based workflow
- **Human-AI Collaboration**: Focus on agentic workflows with human oversight

## Open Questions

1. **Performance Optimization**: How to optimize parallel agent execution for large codebases?
2. **Customization**: How to adapt the methodology for different project types (infrastructure vs application development)?
3. **Integration**: How to integrate with existing CI/CD and development workflows?
4. **Scaling**: How does the methodology perform with very large teams or repositories?
5. **Tooling**: What additional tooling could enhance the agent coordination and documentation workflow?

## Implementation Guide: How to Extract and Implement HumanLayer System

### Step 1: Extract Command Files
**Source URLs** - Get complete markdown content from:
```
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/commands/research_codebase.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/commands/create_plan.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/commands/implement_plan.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/commands/commit.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/commands/describe_pr.md
```

**Implementation Method**:
1. Use WebFetch to get complete content of each command
2. Copy markdown content directly to `.claude/commands/[filename].md`
3. Adapt any HumanLayer-specific references (e.g., user directories)
4. Test command accessibility via Claude Code

### Step 2: Extract Agent Files
**Source URLs** - Get complete markdown content from:
```
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/agents/codebase-locator.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/agents/codebase-analyzer.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/agents/codebase-pattern-finder.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/agents/thoughts-locator.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/agents/thoughts-analyzer.md
https://raw.githubusercontent.com/humanlayer/humanlayer/main/.claude/agents/web-search-researcher.md
```

**Implementation Method**:
1. Create `.claude/agents/` directory
2. Use WebFetch to get complete content of each agent
3. Copy markdown content directly to `.claude/agents/[filename].md`
4. Adapt directory references (allison/ → david/)
5. Test agent spawning via Task tool

### Step 3: Key Command Implementations

#### `/research_codebase` Implementation Details
- **Entry Response**: "I'm ready to research the codebase. Please provide your research question..."
- **Process**: Read mentioned files FULLY → TodoWrite plan → spawn all 6 agents in parallel → synthesize results
- **Output**: Research document in `thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-description.md`
- **Critical**: Always read files before spawning sub-agents

#### `/create_plan` Implementation Details
- **Template Structure**: Must include Overview, Current State, Desired End State, Implementation Phases
- **Success Criteria**: Separate "Automated Verification" (commands) and "Manual Verification" (user testing)
- **Process**: Context gathering → research → plan outline approval → detailed writing → sync
- **Output**: Plan in `thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`

#### `/implement_plan` Implementation Details
- **Approach**: Read plan fully → update checkboxes → implement phase by phase → verify with `make check test`
- **Error Handling**: Structured format for plan-reality mismatches
- **Progress**: Update plan checkboxes as tasks complete
- **Verification**: Run success criteria after each phase

#### `/commit` Implementation Details
- **Critical Restrictions**: NO Claude attribution, NO co-author lines, user-authored commits only
- **Process**: Review changes → plan commits → get approval → execute with specific file staging
- **Message Style**: Imperative mood, focus on "why" not just "what"
- **Staging**: Use `git add [specific-files]` never `-A` or `.`

#### `/describe_pr` Implementation Details
- **Requirements**: Needs `thoughts/shared/pr_description.md` template file
- **Process**: Read template → identify PR → analyze changes → verify tests → generate description → update GitHub
- **GitHub Integration**: Uses `gh pr edit {number} --body-file` to update PR
- **Output**: Description saved to `thoughts/shared/prs/{number}_description.md`

### Step 4: Agent Implementation Details

#### Discovery Agents
- **`codebase-locator`**: Finds WHERE code lives using Grep, Glob, LS
- **`thoughts-locator`**: Discovers documents in thoughts/ directory structure
- **Key Pattern**: Focus on location discovery, NOT content analysis

#### Analysis Agents
- **`codebase-analyzer`**: Deep implementation analysis with precise file:line references
- **`thoughts-analyzer`**: Extract high-value insights from documents with aggressive filtering
- **Key Pattern**: Surgical precision analysis with concrete details

#### Pattern and Research Agents
- **`codebase-pattern-finder`**: Find similar implementations with actual code examples
- **`web-search-researcher`**: External web research with strategic search approaches
- **Key Pattern**: Provide concrete, reusable examples and authoritative sources

### Step 5: Directory Structure Requirements

**Must Create**:
```
.claude/
├── commands/          ✅ Exists
│   ├── research_codebase.md
│   ├── create_plan.md
│   ├── implement_plan.md
│   ├── commit.md
│   └── describe_pr.md
└── agents/            ❌ Create this
    ├── codebase-locator.md
    ├── codebase-analyzer.md
    ├── codebase-pattern-finder.md
    ├── thoughts-locator.md
    ├── thoughts-analyzer.md
    └── web-search-researcher.md

thoughts/              ✅ Exists + organized
├── shared/
│   ├── research/      ✅ Ready
│   ├── plans/         ✅ Ready
│   ├── tickets/       ✅ Ready
│   ├── prs/           ✅ Ready
│   └── pr_description.md  ❌ Need to create template
├── david/             ✅ Ready
├── global/            ✅ Ready
└── searchable/        ✅ Ready
```

### Step 6: Testing Implementation

**Command Testing**:
1. Test each command individually with simple tasks
2. Verify agent spawning works via Task tool
3. Confirm document creation in correct thoughts/ locations
4. Test parallel agent coordination

**Integration Testing**:
1. Complete research → plan → implement → commit → PR cycle
2. Verify thoughts directory organization and discovery
3. Test on actual infrastructure tasks (AWS, YAML, Python lambdas)

### Step 7: Customization for Infrastructure Projects

**Adapt for cloud2dk/service-catalog**:
- **Agent Focus**: Emphasize YAML, CloudFormation, Python lambda analysis
- **Service Structure**: Multi-service architecture awareness (monitoring, reporting, access)
- **AWS Context**: Include AWS service patterns in codebase-pattern-finder
- **GitHub Integration**: Ensure workflows and scripts are discoverable

## Implementation Recommendations

**Priority Order**:
1. **Extract and implement agents first** - Foundation for command system
2. **Implement `/research_codebase`** - Test agent coordination
3. **Implement `/create_plan`** - Verify planning workflow
4. **Complete remaining commands** - Build full cycle
5. **Integration testing** - Ensure end-to-end functionality
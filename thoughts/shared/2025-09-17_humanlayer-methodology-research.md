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

## Implementation Recommendations

For our cloud2dk/service-catalog repository:
1. **Start with Core Commands**: Implement all 5 commands first
2. **Create Agent Framework**: Implement all 6 specialized agents
3. **Directory Structure**: Set up proper thoughts/ organization
4. **Templates**: Create documentation templates for our infrastructure focus
5. **Integration Testing**: Test complete resource-plan-code cycles on real tasks
6. **Customization**: Adapt agents for AWS infrastructure and multi-service architecture
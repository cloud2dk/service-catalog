---
type: implementation_plan
date: 2025-09-17
author: david
status: in_progress
tags:
  - development-methodology
  - claude-commands
  - agent-framework
related_research:
  - "research/2025-09-17_humanlayer-methodology-research.md"
repository_context: "cloud2dk/service-catalog"
---

# Implementation Plan: HumanLayer Resource-Plan-Code Methodology

## Overview

Implement HumanLayer's structured development process consisting of 5 specialized commands (`/research_codebase`, `/create_plan`, `/implement_plan`, `/commit`, `/describe_pr`) and 6 supporting agents that integrate directly with the thoughts directory.

## Current State

### ✅ Completed Infrastructure
- **Repository**: `cloud2dk/service-catalog` - multi-service cloud infrastructure project
- **Basic Structure**: `.claude/` directory with `commands/` subdirectory
- **Settings**: Local configuration (`.claude/settings.local.json`)
- **Thoughts Structure**: Proper subdirectory organization:
  ```
  thoughts/
  ├── shared/
  │   ├── research/     ✅ Created + populated
  │   ├── plans/        ✅ Created + populated
  │   ├── tickets/      ✅ Created
  │   └── prs/          ✅ Created
  ├── david/
  │   ├── tickets/      ✅ Created
  │   └── notes/        ✅ Created
  ├── global/           ✅ Created
  └── searchable/       ✅ Created
  ```
- **Research**: Comprehensive methodology analysis completed

### ❌ Missing Components
- [ ] `.claude/agents/` directory structure
- [ ] Complete command implementations (5 commands)
- [ ] Agent implementations (6 agents)
- [ ] Integration between commands and thoughts directory

## Desired End State

### Command System
- **`/research_codebase`**: Spawns parallel agents → creates documents in `thoughts/shared/research/`
- **`/create_plan`**: Collaborative planning → creates plans in `thoughts/shared/plans/`
- **`/implement_plan`**: Progress tracking → updates plan checkboxes
- **`/commit`**: Atomic commits → proper git staging
- **`/describe_pr`**: PR documentation → creates docs in `thoughts/shared/prs/`

### Agent Framework
- **Discovery Agents**: `thoughts-locator`, `codebase-locator`
- **Analysis Agents**: `thoughts-analyzer`, `codebase-analyzer`
- **Pattern Agents**: `codebase-pattern-finder`
- **Research Agents**: `web-search-researcher`

## Implementation Phases

### Phase 1: Agent Infrastructure
- [ ] Create `.claude/agents/` directory structure
- [ ] Implement `thoughts-locator` agent (discovers documents in thoughts/)
- [ ] Implement `thoughts-analyzer` agent (extracts insights from documents)
- [ ] Test agent discovery across directory structure

### Phase 2: Codebase Agents
- [ ] Implement `codebase-locator` agent (finds files systematically)
- [ ] Implement `codebase-analyzer` agent (deep implementation analysis)
- [ ] Test coordination between thoughts and codebase agents

### Phase 3: Pattern and Research Agents
- [ ] Implement `codebase-pattern-finder` agent (pattern identification)
- [ ] Implement `web-search-researcher` agent (external research)
- [ ] Test parallel agent coordination

### Phase 4: Research Command
- [ ] Implement `/research_codebase` command
  - Spawns all 6 agents in parallel
  - Coordinates agent results
  - Creates structured documents in `thoughts/shared/research/`

### Phase 5: Planning Command
- [ ] Implement `/create_plan` command
  - Uses agents for context gathering
  - Creates plans in `thoughts/shared/plans/`
  - Integrates user feedback workflow

### Phase 6: Implementation and Development Commands
- [ ] Implement `/implement_plan` command (checkbox progress tracking)
- [ ] Implement `/commit` command (atomic commit management)
- [ ] Implement `/describe_pr` command (creates docs in `thoughts/shared/prs/`)

### Phase 7: Integration Testing
- [ ] End-to-end workflow testing
- [ ] Agent coordination verification
- [ ] Thoughts directory integration validation

## Success Criteria

### Agent Integration
- [ ] `thoughts-locator` successfully finds documents across all subdirectories
- [ ] `thoughts-analyzer` extracts insights from existing research documents
- [ ] Agents coordinate properly in parallel execution
- [ ] Commands create documents in correct thoughts/ locations

### Command Integration
- [ ] `/research_codebase` creates properly formatted documents in `thoughts/shared/research/`
- [ ] `/create_plan` creates plans in `thoughts/shared/plans/` with proper frontmatter
- [ ] `/describe_pr` creates PR docs in `thoughts/shared/prs/`
- [ ] All generated documents follow YAML frontmatter standards

### Workflow Verification
- [ ] Complete resource-plan-code cycle works end-to-end
- [ ] TodoWrite integration tracks progress accurately
- [ ] Human oversight approvals work for high-stakes operations
- [ ] Agent outputs provide precise file:line references

## Testing Strategy

### Agent Testing
- **Individual Testing**: Each agent tested in isolation
- **Parallel Coordination**: Multiple agents working simultaneously
- **Thoughts Integration**: Agents discovering and analyzing actual documents
- **Command Integration**: Agents called from commands successfully

### Integration Testing
- **Research Workflow**: Full research cycle with agent coordination
- **Plan Workflow**: Planning process with thoughts discovery
- **End-to-End**: Complete resource-plan-code cycle

### Infrastructure Testing
- **Directory Structure**: All subdirectories accessible by agents
- **File Formats**: YAML frontmatter parsing and generation
- **Cross-Service**: Testing on different service directories

---

## Implementation Checkboxes

### Phase 1: Agent Infrastructure (HIGHEST PRIORITY)
- [ ] Create `.claude/agents/` directory
- [ ] Implement `thoughts-locator` agent
- [ ] Implement `thoughts-analyzer` agent
- [ ] Test agents on current thoughts documents

### Phase 2: Codebase Agents
- [ ] Implement `codebase-locator` agent
- [ ] Implement `codebase-analyzer` agent

### Phase 3: Pattern and Research Agents
- [ ] Implement `codebase-pattern-finder` agent
- [ ] Implement `web-search-researcher` agent

### Phase 4: Command Implementation
- [ ] Implement `/research_codebase` with agent coordination
- [ ] Implement `/create_plan` with thoughts integration
- [ ] Implement `/implement_plan` with progress tracking

### Phase 5: Development Commands
- [ ] Implement `/commit` command
- [ ] Implement `/describe_pr` with thoughts integration

### Phase 6: Integration and Testing
- [ ] End-to-end workflow testing
- [ ] Agent coordination optimization
- [ ] Documentation and examples
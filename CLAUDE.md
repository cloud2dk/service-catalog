# Claude Code Configuration

## Commit Message Guidelines

When committing changes, use clean, professional commit messages without Claude Code branding.

**Do NOT include:**
- 🤖 Generated with [Claude Code](https://claude.ai/code)
- Co-Authored-By: Claude <noreply@anthropic.com>

**DO include:**
- Clear, concise description of changes
- Context about what was fixed or improved
- Technical details when relevant

## Example Good Commit Message

```
Fix Service Catalog scope handling for regionally-pinned products

Updated publish.sh and release.sh to respect the `scope` field in manifest.yaml:
- Global products (scope: global) continue deploying to all active regions
- Regionally-pinned products (e.g., scope: us-east-1) now only deploy to their specified region

This fixes the reporting workflow failure where usage-exports was incorrectly trying to deploy BCM Data Exports (us-east-1 only service) to all regions.
```
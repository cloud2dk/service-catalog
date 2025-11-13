# Bug Report: Security Hub Template Rendering Failure

**Date**: 2025-11-13  
**Investigation ID**: a6147e97-347a-4b62-a370-280777470f02  
**Severity**: High - Blocks all Security Hub events from reaching Freshservice  

## Issue Summary
Security Hub events are successfully processed by the `handle_securityhub_event()` method but fail during template rendering with "Object of type Undefined is not JSON serializable" error.

## Root Cause Analysis

### Error Details
```
TypeError: Object of type Undefined is not JSON serializable
File: /var/task/fresh_webhook/templates/event.html.j2, line 217
Template code: {{ event.detail|tojson(indent=2) }}
```

### Technical Root Cause
The template expects `event.detail` but `EventBridgeFields.to_dict()` doesn't provide a `detail` field. The template receives:

```python
{
    "account_id": "...",
    "region": "...", 
    "subject": "...",
    "source_event": {original_security_hub_event}  # Contains the detail field
    # ... other fields
}
```

When Jinja2 tries to access `event.detail` (which doesn't exist), it creates an `Undefined` object. The `tojson` filter then fails trying to serialize this `Undefined` object.

### Event Flow
1. ✅ Security Hub event received and routed correctly
2. ✅ `handle_securityhub_event()` processes event successfully  
3. ✅ `EventBridgeFields(self.event).to_dict()` creates fields dictionary
4. ❌ Template tries to access `event.detail` → gets `Undefined` object
5. ❌ `tojson` filter fails to serialize `Undefined` object

### Evidence from Logs
```
[HANDLER] Processing Security Hub Finding - source: aws.securityhub
[HANDLER] Security Hub - ID: arn:aws:securityhub:..., Severity: MEDIUM -> error
Sending event to Fresh Webhook
[ERROR] TypeError: Object of type Undefined is not JSON serializable
```

## Security Hub Event Structure
Security Hub events have standard JSON structure:
```json
{
  "version": "0",
  "source": "aws.securityhub", 
  "detail-type": "Security Hub Findings - Imported",
  "detail": {
    "findings": [
      {
        "Id": "arn:aws:securityhub:...",
        "Title": "...",
        "Severity": {"Label": "MEDIUM"},
        "Description": "...",
        "ProductFields": {...},
        "Resources": [...]
      }
    ]
  }
}
```

## Proposed Solutions

### Option 1: Fix Template (Recommended)
Change template line 217 from:
```jinja2
{{ event.detail|tojson(indent=2) }}
```
To:
```jinja2
{{ event.source_event.detail|tojson(indent=2) }}
```

**Pros**: Minimal change, maintains existing architecture  
**Cons**: Template becomes dependent on EventBridgeFields structure

### Option 2: Modify EventBridgeFields.to_dict()
Add `detail` field to the returned dictionary:
```python
def to_dict(self):
    return {
        # ... existing fields
        "detail": self.source_event.get("detail", {}),
        "source_event": self.source_event
    }
```

**Pros**: Template remains clean, backward compatible  
**Cons**: Duplicates data in the fields dictionary

### Option 3: Create Security Hub Specific Template
Create `securityhub_event.html.j2` template optimized for Security Hub events.

**Pros**: Clean separation, optimized for Security Hub structure  
**Cons**: More maintenance, template duplication

## Impact Assessment
- **Current**: All Security Hub events fail to reach Freshservice
- **Affected Events**: Security Hub findings, GuardDuty findings (routed through Security Hub)
- **Working Events**: CloudWatch alarms, direct GuardDuty events, SNS events

## Testing Validation
Tested with manual Security Hub finding creation:
```bash
aws securityhub batch-import-findings --findings '[{...}]'
```
Confirmed error occurs consistently with Security Hub events.

## Solution Implemented
Implemented a **modified Option 2** approach - updated `_send_to_fresh()` method to extract and pass `source_event` from fields dict to template.

### Changes Made
**File:** `fresh_webhook/event_dispatcher.py` (lines 41-67)
- Modified `_send_to_fresh()` to check if parameter contains `source_event` field
- Extracts raw EventBridge event from fields dict before passing to template
- Maintains backward compatibility with raw event passing

### Why This Approach
- Template designed for raw EventBridge structure (uses `event.source`, `event.detail`, etc.)
- Handlers pass fields dict containing `source_event` with the raw event
- Abstracted fields (`account_id`, `severity`, `node`) were never used by template
- Freshservice receives only HTML (Content-Type: text/html)
- Minimal code change, no breaking changes

## Root Cause - Original Design Flaw
**Not a regression** - This bug existed from initial implementation (commit fc30d4e).

The architecture had a mismatch:
- Template expects EventBridge event structure
- Handlers create abstracted fields dict via `EventBridgeFields.to_dict()`
- Template only received fields dict, couldn't access EventBridge fields
- Tests only validated HTTP 200 status, not HTML content correctness

## Related Investigation
- Previous issue: Missing `aws.securityhub` handler (RESOLVED)
- Current issue: Template rendering for Security Hub events (ACTIVE)

---

## ARCHITECTURAL CONCERN - Future Consideration

### Problem: Tight Coupling & Deployment Overhead
The current architecture requires **both infrastructure AND code deployments** for every new event type:

**Current Flow:**
1. EventBridge Rules (CloudFormation) → Filter events by pattern
2. All rules invoke same Lambda (`FreshServiceFunction`)
3. Lambda has hardcoded event routing (`event_dispatcher.py:206-214`)
4. Each event type needs custom handler method

**Adding New Event Type Requires:**
- ✏️ New EventBridge Rule in `event-management.yaml`
- ✏️ New handler method in `event_dispatcher.py`
- ✏️ Update hardcoded `sources` dictionary
- 🚀 Deploy CloudFormation stack
- 🚀 Deploy Lambda code

### Future Enhancement: Configuration-Driven Architecture
Move to a rule-driven pattern where:
- EventBridge rules pass metadata (severity mapping, field extraction patterns)
- Lambda uses generic handler with JSONPath-based field extraction
- New event types = CloudFormation change only, no code deployment
- Severity mapping and field extraction configurable via rule input transformers or SSM parameters

**Benefits:**
- Reduce deployment friction
- Faster onboarding of new event types
- Less code maintenance
- Configuration-as-code approach

**Scope:** Out of scope for current bug fix, but important architectural improvement for future iterations.

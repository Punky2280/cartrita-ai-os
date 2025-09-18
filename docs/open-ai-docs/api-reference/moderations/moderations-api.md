# Moderations API

> **Source**: https://platform.openai.com/docs/api-reference/moderations
> **Last Updated**: September 17, 2025

## Overview

Given a input text, outputs if the model classifies it as violating OpenAI's usage policies. The moderation endpoint is free to use when monitoring the inputs and outputs of OpenAI APIs.

## Create Moderation

Classifies if text violates OpenAI's Usage Policies.

### HTTP Request
```
POST https://api.openai.com/v1/moderations
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input` | string or array | Yes | The input text to classify. Can be a string or an array of strings. |
| `model` | string | No | Two content moderations models are available: `text-moderation-latest` and `text-moderation-stable`. |

### Available Models

| Model | Description |
|-------|-------------|
| `text-moderation-latest` | Currently points to `text-moderation-007`. Will be updated over time. |
| `text-moderation-stable` | Currently points to `text-moderation-007`. Will not be updated. |

### Example Requests

#### Basic Moderation Check
```python
from openai import OpenAI

client = OpenAI()

response = client.moderations.create(input="I want to kill them.")

moderation_result = response.results[0]

print(f"Flagged: {moderation_result.flagged}")
if moderation_result.flagged:
    print("Categories flagged:")
    for category, flagged in moderation_result.categories.__dict__.items():
        if flagged:
            print(f"  - {category}")
```

#### Check Multiple Texts
```python
from openai import OpenAI

client = OpenAI()

texts_to_check = [
    "I love this product!",
    "This is inappropriate content that should be flagged",
    "How are you doing today?",
    "I want to hurt someone"
]

response = client.moderations.create(input=texts_to_check)

for i, result in enumerate(response.results):
    print(f"\nText {i+1}: {texts_to_check[i][:50]}...")
    print(f"Flagged: {result.flagged}")

    if result.flagged:
        flagged_categories = [
            category for category, flagged in result.categories.__dict__.items()
            if flagged
        ]
        print(f"Flagged categories: {', '.join(flagged_categories)}")
```

#### Detailed Moderation Analysis
```python
from openai import OpenAI

client = OpenAI()

def analyze_content(text):
    """Perform detailed moderation analysis"""
    response = client.moderations.create(
        input=text,
        model="text-moderation-latest"
    )

    result = response.results[0]

    analysis = {
        "text": text,
        "flagged": result.flagged,
        "categories": {},
        "category_scores": {}
    }

    # Get category flags and scores
    for category in result.categories.__dict__:
        analysis["categories"][category] = getattr(result.categories, category)
        analysis["category_scores"][category] = getattr(result.category_scores, category)

    return analysis

# Example usage
text = "I'm frustrated with this service and want to complain."
analysis = analyze_content(text)

print(f"Text: {analysis['text']}")
print(f"Overall flagged: {analysis['flagged']}")
print("\nCategory Analysis:")

for category, flagged in analysis["categories"].items():
    score = analysis["category_scores"][category]
    status = "🚩 FLAGGED" if flagged else "✓ OK"
    print(f"  {category}: {status} (score: {score:.4f})")
```

#### cURL Example
```bash
curl https://api.openai.com/v1/moderations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "input": "Sample text to moderate"
  }'
```

### Response Object

```json
{
  "id": "modr-XXXXX",
  "model": "text-moderation-007",
  "results": [
    {
      "flagged": false,
      "categories": {
        "sexual": false,
        "hate": false,
        "harassment": false,
        "self-harm": false,
        "sexual/minors": false,
        "hate/threatening": false,
        "violence/graphic": false,
        "self-harm/intent": false,
        "self-harm/instructions": false,
        "harassment/threatening": false,
        "violence": false
      },
      "category_scores": {
        "sexual": 1.2282071e-06,
        "hate": 0.010696256,
        "harassment": 0.29842457,
        "self-harm": 1.5236925e-08,
        "sexual/minors": 5.7246268e-08,
        "hate/threatening": 0.0060676364,
        "violence/graphic": 4.435014e-06,
        "self-harm/intent": 8.098441e-10,
        "self-harm/instructions": 2.8498655e-11,
        "harassment/threatening": 0.63055265,
        "violence": 0.99011886
      }
    }
  ]
}
```

### Response Fields

#### Moderation Object
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | The unique identifier for the moderation request. |
| `model` | string | The model used to generate the moderation results. |
| `results` | array | A list of moderation objects. |

#### Moderation Result Object
| Field | Type | Description |
|-------|------|-------------|
| `flagged` | boolean | Whether the content violates OpenAI's usage policies. |
| `categories` | object | A list of the categories, and whether they are flagged or not. |
| `category_scores` | object | A list of the categories along with their scores as predicted by the model. |

### Moderation Categories

#### Content Categories

**violence**
- Content that depicts death, violence, or physical injury.

**violence/graphic**
- Content that depicts death, violence, or physical injury in graphic detail.

**harassment**
- Content that expresses, incites, or promotes harassing language towards any target.

**harassment/threatening**
- Harassment content that also includes violence or serious harm towards any target.

**hate**
- Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.

**hate/threatening**
- Hateful content that also includes violence or serious harm towards the targeted group.

**self-harm**
- Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.

**self-harm/intent**
- Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm.

**self-harm/instructions**
- Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts.

**sexual**
- Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).

**sexual/minors**
- Sexual content that includes an individual who is under 18 years old.

## Advanced Use Cases

### Content Moderation Pipeline
```python
from openai import OpenAI
import json
from datetime import datetime
from typing import List, Dict, Any

client = OpenAI()

class ContentModerator:
    def __init__(self, model="text-moderation-latest"):
        self.model = model
        self.client = client

        # Define severity thresholds
        self.thresholds = {
            "violence": 0.8,
            "harassment": 0.7,
            "hate": 0.6,
            "sexual": 0.8,
            "self-harm": 0.5
        }

    def moderate_content(self, content: str) -> Dict[str, Any]:
        """Moderate a single piece of content"""
        try:
            response = self.client.moderations.create(
                input=content,
                model=self.model
            )

            result = response.results[0]

            moderation_result = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "flagged": result.flagged,
                "model": response.model,
                "categories": {},
                "scores": {},
                "severity": "low",
                "action_required": False
            }

            # Process categories and scores
            high_risk_categories = []
            max_score = 0

            for category in result.categories.__dict__:
                flagged = getattr(result.categories, category)
                score = getattr(result.category_scores, category)

                moderation_result["categories"][category] = flagged
                moderation_result["scores"][category] = score

                # Check severity
                base_category = category.split('/')[0]
                threshold = self.thresholds.get(base_category, 0.5)

                if score > threshold:
                    high_risk_categories.append(category)

                max_score = max(max_score, score)

            # Determine severity and required action
            if high_risk_categories:
                moderation_result["severity"] = "high"
                moderation_result["action_required"] = True
                moderation_result["high_risk_categories"] = high_risk_categories
            elif max_score > 0.3:
                moderation_result["severity"] = "medium"

            return moderation_result

        except Exception as e:
            return {
                "content": content,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def moderate_batch(self, contents: List[str]) -> List[Dict[str, Any]]:
        """Moderate multiple pieces of content"""
        # OpenAI supports up to 1000 inputs per request
        batch_size = 1000
        all_results = []

        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]

            try:
                response = self.client.moderations.create(
                    input=batch,
                    model=self.model
                )

                for j, result in enumerate(response.results):
                    content = batch[j]
                    moderation_result = {
                        "content": content,
                        "timestamp": datetime.now().isoformat(),
                        "flagged": result.flagged,
                        "model": response.model,
                        "categories": {
                            category: getattr(result.categories, category)
                            for category in result.categories.__dict__
                        },
                        "scores": {
                            category: getattr(result.category_scores, category)
                            for category in result.category_scores.__dict__
                        }
                    }
                    all_results.append(moderation_result)

            except Exception as e:
                # Add error results for failed batch
                for content in batch:
                    all_results.append({
                        "content": content,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

        return all_results

    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary report from moderation results"""
        total_content = len(results)
        flagged_content = sum(1 for r in results if r.get("flagged", False))

        category_flags = {}
        category_scores = {}

        for result in results:
            if "categories" in result:
                for category, flagged in result["categories"].items():
                    category_flags[category] = category_flags.get(category, 0) + (1 if flagged else 0)

            if "scores" in result:
                for category, score in result["scores"].items():
                    if category not in category_scores:
                        category_scores[category] = []
                    category_scores[category].append(score)

        # Calculate average scores
        avg_scores = {
            category: sum(scores) / len(scores)
            for category, scores in category_scores.items()
        }

        return {
            "summary": {
                "total_content": total_content,
                "flagged_content": flagged_content,
                "flagged_percentage": (flagged_content / total_content * 100) if total_content > 0 else 0
            },
            "category_flags": category_flags,
            "average_scores": avg_scores,
            "generated_at": datetime.now().isoformat()
        }

# Example usage
moderator = ContentModerator()

# Single content moderation
content = "This is a test message that should be safe."
result = moderator.moderate_content(content)
print(f"Content flagged: {result['flagged']}")

# Batch moderation
contents = [
    "I love this product!",
    "This service is terrible",
    "How can I help you today?",
    "I want to hurt someone badly"
]

batch_results = moderator.moderate_batch(contents)
report = moderator.generate_report(batch_results)

print(f"Flagged {report['summary']['flagged_content']} out of {report['summary']['total_content']} messages")
```

### Real-time Chat Moderation
```python
from openai import OpenAI
import asyncio
from typing import Callable, Any

client = OpenAI()

class ChatModerator:
    def __init__(self):
        self.client = client
        self.moderation_callbacks = []

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback function for moderation results"""
        self.moderation_callbacks.append(callback)

    async def moderate_message(self, user_id: str, message: str,
                             channel_id: str = None) -> Dict[str, Any]:
        """Moderate a chat message in real-time"""
        try:
            response = self.client.moderations.create(input=message)
            result = response.results[0]

            moderation_data = {
                "user_id": user_id,
                "channel_id": channel_id,
                "message": message,
                "flagged": result.flagged,
                "timestamp": datetime.now().isoformat(),
                "categories": {
                    category: getattr(result.categories, category)
                    for category in result.categories.__dict__
                },
                "scores": {
                    category: getattr(result.category_scores, category)
                    for category in result.category_scores.__dict__
                }
            }

            # Determine action
            if result.flagged:
                # Check for immediate threats
                immediate_threats = ["violence", "self-harm/intent", "harassment/threatening"]
                high_risk = any(
                    getattr(result.categories, cat.replace('/', '_'), False)
                    for cat in immediate_threats
                )

                if high_risk:
                    moderation_data["action"] = "block_and_escalate"
                else:
                    moderation_data["action"] = "flag_for_review"
            else:
                moderation_data["action"] = "allow"

            # Notify callbacks
            for callback in self.moderation_callbacks:
                try:
                    callback(moderation_data)
                except Exception as e:
                    print(f"Callback error: {e}")

            return moderation_data

        except Exception as e:
            return {
                "user_id": user_id,
                "channel_id": channel_id,
                "message": message,
                "error": str(e),
                "action": "allow_with_error",
                "timestamp": datetime.now().isoformat()
            }

# Example callback functions
def log_moderation_result(data):
    """Log moderation results"""
    if data.get("flagged"):
        flagged_categories = [cat for cat, flagged in data["categories"].items() if flagged]
        print(f"⚠️  Flagged message from {data['user_id']}: {flagged_categories}")

def block_user_temporarily(data):
    """Implement temporary user blocking for severe violations"""
    if data.get("action") == "block_and_escalate":
        print(f"🚫 Blocking user {data['user_id']} temporarily")

def alert_moderators(data):
    """Send alerts to human moderators"""
    if data.get("action") in ["block_and_escalate", "flag_for_review"]:
        print(f"📢 Alert: Message from {data['user_id']} needs review")

# Usage example
moderator = ChatModerator()
moderator.add_callback(log_moderation_result)
moderator.add_callback(block_user_temporarily)
moderator.add_callback(alert_moderators)

# Simulate chat messages
async def simulate_chat():
    messages = [
        ("user123", "Hello everyone!"),
        ("user456", "I hate this place and everyone in it"),
        ("user789", "Can someone help me with this problem?"),
        ("user101", "I want to hurt myself")
    ]

    for user_id, message in messages:
        result = await moderator.moderate_message(user_id, message)
        print(f"Action for '{message}': {result.get('action', 'unknown')}")

# Run simulation
# asyncio.run(simulate_chat())
```

### Automated Content Policy Enforcement
```python
from openai import OpenAI
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

client = OpenAI()

class ViolationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ModerationPolicy:
    category: str
    threshold: float
    severity: ViolationSeverity
    action: str
    escalate: bool = False

class PolicyEnforcer:
    def __init__(self):
        self.client = client
        self.policies = self._define_policies()
        self.violation_history = {}

    def _define_policies(self) -> List[ModerationPolicy]:
        """Define content moderation policies"""
        return [
            # Violence policies
            ModerationPolicy("violence", 0.7, ViolationSeverity.HIGH, "remove_content", True),
            ModerationPolicy("violence/graphic", 0.5, ViolationSeverity.CRITICAL, "remove_and_warn", True),

            # Harassment policies
            ModerationPolicy("harassment", 0.6, ViolationSeverity.MEDIUM, "flag_content"),
            ModerationPolicy("harassment/threatening", 0.4, ViolationSeverity.HIGH, "remove_content", True),

            # Hate speech policies
            ModerationPolicy("hate", 0.5, ViolationSeverity.MEDIUM, "flag_content"),
            ModerationPolicy("hate/threatening", 0.3, ViolationSeverity.CRITICAL, "remove_and_warn", True),

            # Self-harm policies
            ModerationPolicy("self-harm", 0.3, ViolationSeverity.HIGH, "remove_and_support", True),
            ModerationPolicy("self-harm/intent", 0.2, ViolationSeverity.CRITICAL, "immediate_intervention", True),
            ModerationPolicy("self-harm/instructions", 0.3, ViolationSeverity.HIGH, "remove_content", True),

            # Sexual content policies
            ModerationPolicy("sexual", 0.8, ViolationSeverity.MEDIUM, "flag_content"),
            ModerationPolicy("sexual/minors", 0.1, ViolationSeverity.CRITICAL, "remove_and_report", True),
        ]

    def enforce_policies(self, content: str, user_id: str) -> Dict[str, Any]:
        """Enforce content policies and return actions to take"""
        response = self.client.moderations.create(input=content)
        result = response.results[0]

        violations = []
        actions = set()
        max_severity = ViolationSeverity.LOW

        # Check each policy
        for policy in self.policies:
            category_key = policy.category.replace('/', '_')
            score = getattr(result.category_scores, category_key, 0)

            if score > policy.threshold:
                violations.append({
                    "category": policy.category,
                    "score": score,
                    "threshold": policy.threshold,
                    "severity": policy.severity,
                    "action": policy.action,
                    "escalate": policy.escalate
                })

                actions.add(policy.action)

                # Track highest severity
                if policy.severity.value == "critical":
                    max_severity = ViolationSeverity.CRITICAL
                elif policy.severity.value == "high" and max_severity != ViolationSeverity.CRITICAL:
                    max_severity = ViolationSeverity.HIGH
                elif policy.severity.value == "medium" and max_severity in [ViolationSeverity.LOW]:
                    max_severity = ViolationSeverity.MEDIUM

        # Update violation history
        if violations:
            if user_id not in self.violation_history:
                self.violation_history[user_id] = []

            self.violation_history[user_id].append({
                "timestamp": datetime.now().isoformat(),
                "violations": violations,
                "content_preview": content[:100]
            })

        # Determine escalation based on history
        escalate_to_human = any(v["escalate"] for v in violations)
        repeat_offender = len(self.violation_history.get(user_id, [])) > 3

        return {
            "content": content,
            "user_id": user_id,
            "violations": violations,
            "actions": list(actions),
            "severity": max_severity.value,
            "escalate_to_human": escalate_to_human,
            "repeat_offender": repeat_offender,
            "recommended_action": self._get_recommended_action(actions, max_severity, repeat_offender)
        }

    def _get_recommended_action(self, actions: List[str], severity: ViolationSeverity,
                               repeat_offender: bool) -> str:
        """Determine the most appropriate action to take"""
        if "immediate_intervention" in actions:
            return "immediate_intervention"
        elif "remove_and_report" in actions:
            return "remove_and_report"
        elif severity == ViolationSeverity.CRITICAL or repeat_offender:
            return "escalate_to_human"
        elif "remove_and_warn" in actions:
            return "remove_and_warn"
        elif "remove_content" in actions:
            return "remove_content"
        elif "flag_content" in actions:
            return "flag_content"
        else:
            return "no_action"

    def get_user_violation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get violation history summary for a user"""
        history = self.violation_history.get(user_id, [])

        if not history:
            return {"user_id": user_id, "total_violations": 0}

        category_counts = {}
        severity_counts = {}

        for incident in history:
            for violation in incident["violations"]:
                category = violation["category"]
                severity = violation["severity"].value

                category_counts[category] = category_counts.get(category, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "user_id": user_id,
            "total_violations": len(history),
            "first_violation": history[0]["timestamp"],
            "last_violation": history[-1]["timestamp"],
            "category_breakdown": category_counts,
            "severity_breakdown": severity_counts,
            "risk_level": self._assess_user_risk(history)
        }

    def _assess_user_risk(self, history: List[Dict]) -> str:
        """Assess user risk level based on violation history"""
        if len(history) >= 10:
            return "high"
        elif len(history) >= 5:
            return "medium"
        elif len(history) >= 2:
            return "low"
        else:
            return "minimal"

# Example usage
enforcer = PolicyEnforcer()

# Test various content
test_content = [
    "I love this community!",
    "I hate everyone here and wish they would disappear",
    "I'm having thoughts of hurting myself",
    "This is completely inappropriate sexual content involving minors"
]

for content in test_content:
    result = enforcer.enforce_policies(content, f"user_{hash(content) % 1000}")
    print(f"\nContent: {content[:50]}...")
    print(f"Recommended action: {result['recommended_action']}")
    print(f"Severity: {result['severity']}")
    if result['violations']:
        print(f"Violations: {[v['category'] for v in result['violations']]}")
```

## Error Handling

### Common Errors and Solutions

```python
from openai import OpenAI
import openai

client = OpenAI()

def safe_moderate_content(text, model="text-moderation-latest"):
    """Moderate content with comprehensive error handling"""
    try:
        response = client.moderations.create(
            input=text,
            model=model
        )
        return {
            "success": True,
            "flagged": response.results[0].flagged,
            "categories": response.results[0].categories.__dict__,
            "scores": response.results[0].category_scores.__dict__
        }

    except openai.BadRequestError as e:
        if "input" in str(e).lower():
            return {"success": False, "error": "Input text too long or invalid"}
        else:
            return {"success": False, "error": f"Bad request: {e}"}

    except openai.RateLimitError:
        return {"success": False, "error": "Rate limit exceeded"}

    except openai.AuthenticationError:
        return {"success": False, "error": "Invalid API key"}

    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}

# Usage
result = safe_moderate_content("Test content to moderate")
if result["success"]:
    print(f"Flagged: {result['flagged']}")
else:
    print(f"Error: {result['error']}")
```

## Best Practices

### Implementation Guidelines
- Use moderation for all user-generated content
- Implement both preventive and reactive moderation
- Combine automated and human moderation
- Regularly review and update policies

### Performance Optimization
- Batch multiple texts when possible
- Cache moderation results for identical content
- Use appropriate model based on update needs
- Implement async processing for high volume

### Privacy and Security
- Don't log sensitive user content
- Implement proper access controls
- Use secure storage for moderation logs
- Comply with data protection regulations

### Integration Strategies
- Pre-moderation: Check before publishing
- Post-moderation: Check after publishing
- Real-time moderation: Check during interaction
- Batch moderation: Process historical content

---

*This documentation covers the complete Moderations API for content safety and policy enforcement. Use this API to build responsible AI applications with appropriate content filtering.*

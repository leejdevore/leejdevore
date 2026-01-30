# Agentic PRD: Personal Finance Agent

> **Module Name:** `Finance_Copilot`
> **Agency Level:** Reactive Assistant → Autonomous Agent (graduated)
> **Version:** 1.0

---

## Overview

| Mortal Speak | Agentic Translation |
|--------------|---------------------|
| "I want an app that helps me save money and not overspend." | A multi-modal agent that monitors financial activity, identifies patterns, and autonomously optimizes spending within user-defined constraints. |

---

## 1. The Mission (Objective)

### Mortal View
> "Help me understand where my money goes and stop me before I make dumb purchases."

### Agentic View

| Goal | Reward Function |
|------|-----------------|
| **Primary** | Maximize `savings_rate` while maintaining `quality_of_life_score > 0.7` |
| **Secondary** | Reduce `impulse_purchase_count` by 40% over 90 days |
| **Tertiary** | Surface `optimization_opportunities` (subscriptions, better rates, cashback) |

```
reward = (savings_rate * 0.5) + (qol_score * 0.3) + (opportunities_actioned * 0.2)
```

---

## 2. The Toolkit (Tools & Capabilities)

### Requirements

| Tool | Function | Provider |
|------|----------|----------|
| `Plaid_API` | Read transaction data, balances, account metadata | Plaid |
| `Categorization_Model` | Classify transactions (groceries, entertainment, etc.) | Internal NLP |
| `Notification_Service` | Push alerts to user devices | Firebase/APNs |
| `Budget_DB` | Store user budgets, goals, thresholds | PostgreSQL |
| `LLM_Reasoning` | Natural language interaction, explanation generation | Claude API |
| `Calendar_API` | Correlate spending with events (paydays, holidays) | Google Calendar |

### Permissions Matrix

| Tool | Read | Write | Execute | HITL Required |
|------|------|-------|---------|---------------|
| `Plaid_API` | ✅ | ❌ | ❌ | No |
| `Categorization_Model` | ✅ | ✅ | ✅ | No |
| `Notification_Service` | ❌ | ✅ | ✅ | No (rate-limited) |
| `Budget_DB` | ✅ | ✅ | ✅ | Yes (for goal changes) |
| `LLM_Reasoning` | ✅ | ❌ | ✅ | No |
| `Calendar_API` | ✅ | ❌ | ❌ | No |

---

## 3. Cognition (Reasoning Strategy)

### Logic Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT RECEIVED                           │
│              (new transaction, user query)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CLASSIFY & CONTEXTUALIZE                    │
│  • Categorize transaction                                   │
│  • Check against budget thresholds                          │
│  • Correlate with calendar (payday? holiday?)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    REASONING (ReAct)                        │
│  Thought: User spent $47 at restaurant. This month's        │
│           dining budget is at 89%. 11 days remaining.       │
│  Action:  Check dining pattern for this user.               │
│  Observe: User typically has 2 more dining events/month.    │
│  Thought: High probability of budget breach.                │
│  Action:  Generate soft warning notification.               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT DECISION                           │
│  • No action (within normal)                                │
│  • Soft nudge (approaching threshold)                       │
│  • Hard alert (threshold breached)                          │
│  • Suggestion (optimization opportunity found)              │
└─────────────────────────────────────────────────────────────┘
```

### Triggers

| Trigger | Source | Agent Response |
|---------|--------|----------------|
| `new_transaction` | Plaid webhook | Categorize → Evaluate → Notify if needed |
| `budget_threshold_80%` | Internal cron (daily) | Proactive warning |
| `user_query` | App interface | ReAct reasoning → Natural language response |
| `payday_detected` | Calendar + Transaction | Generate monthly summary + next month plan |
| `recurring_charge_change` | Transaction diff | Alert user to subscription price changes |

---

## 4. Guardrails (Constraints & Safety)

### Hard Limits

| Constraint | Rationale |
|------------|-----------|
| **NEVER initiate financial transactions** | Read-only access to banking. No transfers, no payments. |
| **NEVER share data with third parties** | All processing stays within system boundary. |
| **NEVER guilt or shame user** | Notifications must be supportive, not judgmental. Tone validation required. |
| **MAX 3 notifications/day** | Prevent notification fatigue. Prioritize by impact. |
| **NEVER store raw credentials** | OAuth tokens only, encrypted at rest. |

### Validation Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   AGENT      │───▶│  VALIDATOR   │───▶│   OUTPUT     │
│   OUTPUT     │    │   LAYER      │    │   TO USER    │
└──────────────┘    └──────────────┘    └──────────────┘
                           │
                    ┌──────┴──────┐
                    │  CHECKS:    │
                    │  • Tone     │
                    │  • Accuracy │
                    │  • Rate     │
                    │  • Privacy  │
                    └─────────────┘
```

| Check | Method | Failure Action |
|-------|--------|----------------|
| **Tone Validation** | Classifier model scores sentiment ≥ 0.6 (supportive) | Rewrite with softer template |
| **Accuracy** | Transaction categorization confidence ≥ 0.85 | Flag for user confirmation |
| **Rate Limit** | Counter < 3/day | Queue for tomorrow or combine with higher-priority alert |
| **Privacy** | No PII in logs or external calls | Redact before processing |

---

## 5. Memory & Context

### Short-Term Memory (Conversation Window)

| Data | TTL | Purpose |
|------|-----|---------|
| Current user query | Session | Maintain conversation coherence |
| Last 5 transactions | 24 hours | Immediate context for questions like "What did I spend today?" |
| Active budget status | Real-time | Quick threshold checks |
| Pending notifications | Until sent | Deduplication |

### Long-Term Memory (Persistent Storage)

| Data | Storage | Purpose |
|------|---------|---------|
| Transaction history | PostgreSQL | Trend analysis, pattern detection |
| User preferences | PostgreSQL | Notification timing, category priorities |
| Spending embeddings | Vector DB (Pinecone) | Semantic search ("Show me all coffee purchases") |
| Goal history | PostgreSQL | Track progress over time, celebrate milestones |
| Conversation summaries | Vector DB | Remember past advice given, avoid repetition |

### Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      QUERY ARRIVES                          │
│              "Why am I always broke by the 20th?"           │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │ Short-Term│   │ Long-Term │   │  Vector   │
       │  (Recent) │   │ (Patterns)│   │ (Semantic)│
       └───────────┘   └───────────┘   └───────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
       ┌─────────────────────────────────────────────────────┐
       │  SYNTHESIZED CONTEXT                                │
       │  • Last 30 days transactions                        │
       │  • Historical pattern: spending spikes on weekends  │
       │  • Similar past query: advised meal prepping (worked)│
       └─────────────────────────────────────────────────────┘
                              │
                              ▼
       ┌─────────────────────────────────────────────────────┐
       │  AGENT RESPONSE                                     │
       │  "Looking at your patterns, you tend to spend 60%   │
       │   of your dining budget in the first two weekends.  │
       │   Last time we discussed meal prepping—that helped. │
       │   Want me to set a weekend spending reminder?"      │
       └─────────────────────────────────────────────────────┘
```

---

## Graduation Path: Reactive → Autonomous

This agent is designed to **graduate** based on user trust signals:

| Level | Behavior | Unlock Condition |
|-------|----------|------------------|
| **L1: Observer** | Read-only insights, user initiates all queries | Default |
| **L2: Advisor** | Proactive notifications, suggestions | User enables notifications |
| **L3: Guardian** | Real-time spending alerts, subscription monitoring | 30 days active + user opt-in |
| **L4: Optimizer** | Auto-negotiate bills, find better rates (with approval) | 90 days + explicit consent per action |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Savings rate increase | +15% over 90 days | (Income - Spending) / Income |
| Notification engagement | >40% action rate | Actions taken / Notifications sent |
| User retention | >70% DAU/MAU | Active users ratio |
| Category accuracy | >90% | Correct categorizations / Total |
| NPS | >50 | Quarterly survey |

---

## Open Questions for Stakeholder Review

1. **Tone calibration**: How aggressive should "approaching budget" warnings be? (Suggested: A/B test gentle vs. direct)
2. **Data retention**: How long do we keep transaction history? (Suggested: 2 years, user-deletable)
3. **Multi-account**: Do we support joint accounts / family budgets in v1? (Suggested: v1.5)
4. **Offline mode**: What functionality exists without network? (Suggested: cached budget status only)

---

*Generated using the Agentic Architect Framework*

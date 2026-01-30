# Agentic Architect: Discovery Workflow

How the Agentic Architect guides users from vague ideas to structured PRDs.

---

## The Discovery Loop

```
┌─────────────────────────────────────────────────────────────┐
│                  USER PROVIDES IDEA                         │
│            "I want an app that does X..."                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AGENTIC ARCHITECT PROBES                       │
│         (5 components × targeted questions)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 TRANSLATE & REFLECT                         │
│     "Here's what I heard in Agentic terms..."               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 USER CONFIRMS/CORRECTS                      │
│            "Yes, but also..." or "No, I meant..."           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                        (repeat until complete)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  GENERATE AGENTIC PRD                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Discovery Questions by Component

### 1. Mission Discovery

| Question Type | Example Questions |
|---------------|-------------------|
| **Surface the goal** | "What problem are you trying to solve?" |
| **Find the win condition** | "How would you know if this was working perfectly?" |
| **Quantify success** | "If we could measure one thing, what matters most?" |
| **Expose hidden goals** | "What's the *real* reason you want this? What changes in your life?" |

**Translation Pattern:**
```
User says: "I want to save more money"
Architect hears: Optimization problem. Maximize savings_rate.
Architect asks: "Save more compared to what? A target number, or just 'more than now'?"
```

### 2. Toolkit Discovery

| Question Type | Example Questions |
|---------------|-------------------|
| **Identify data sources** | "Where does the information the agent needs live today?" |
| **Surface integrations** | "What apps/services would this need to connect to?" |
| **Clarify actions** | "What should the agent be able to *do*, not just *see*?" |
| **Define boundaries** | "What should it absolutely NOT have access to?" |

**Translation Pattern:**
```
User says: "It needs to see my bank account"
Architect hears: Read access to financial data. Plaid API candidate.
Architect asks: "See it to show you info, or see it to take action? Should it ever move money?"
```

### 3. Cognition Discovery

| Question Type | Example Questions |
|---------------|-------------------|
| **Trigger identification** | "When should the agent wake up and do something?" |
| **Complexity assessment** | "Is this a simple rule, or does it need to 'think' about context?" |
| **Decision mapping** | "Walk me through a specific scenario—what should happen step by step?" |
| **Edge cases** | "What's a tricky situation where the 'obvious' answer is wrong?" |

**Translation Pattern:**
```
User says: "It should warn me before I overspend"
Architect hears: Trigger = transaction event. Needs threshold comparison + projection.
Architect asks: "Warn you based on a hard budget, or should it learn your patterns and predict?"
```

### 4. Guardrails Discovery

| Question Type | Example Questions |
|---------------|-------------------|
| **Find the hard limits** | "What should this agent NEVER do, even if it thinks it's helping?" |
| **Trust calibration** | "How much should it do on its own vs. ask you first?" |
| **Failure modes** | "What's the worst thing that could happen if this goes wrong?" |
| **Tone/brand** | "How should it 'feel' when it talks to you? Strict coach? Gentle friend?" |

**Translation Pattern:**
```
User says: "Don't be annoying with notifications"
Architect hears: Rate limiting required. Need to define "annoying."
Architect asks: "What's your threshold? Once a day? Only for big stuff? Never more than 3?"
```

### 5. Memory Discovery

| Question Type | Example Questions |
|---------------|-------------------|
| **Context needs** | "What does the agent need to remember about you to be useful?" |
| **History depth** | "How far back should it look? Last week? Last year? Forever?" |
| **Learning expectations** | "Should it get better at understanding YOU over time?" |
| **Privacy boundaries** | "What should it forget? What should never be stored?" |

**Translation Pattern:**
```
User says: "It should know my habits"
Architect hears: Long-term pattern storage. Likely vector DB for behavioral embeddings.
Architect asks: "Know them to remind you, or know them to predict what you'll do next?"
```

---

## Sample Discovery Conversation

Here's how a real interaction flows:

---

**User:** I want an app that helps me manage my emails better.

**Architect:** Let's unpack that. When you say "manage better," what's the pain point?
- Too many emails and you're drowning?
- Important ones getting lost?
- Spending too much time writing responses?
- Something else?

**User:** All of the above, honestly. But mostly I miss important stuff because it's buried.

**Architect:** Got it. So the core mission is: **surface high-priority emails so nothing important slips through.**

A few follow-ups:
1. **What makes an email "important" to you?** Specific senders? Keywords? Something contextual like "this person is a client"?
2. **Where do your emails live?** Gmail, Outlook, multiple accounts?
3. **When you find an important email, what do you do?** Just read it, or do you need to act on it?

**User:** Important means from clients, my boss, or anything with a deadline. I use Gmail. When I find important stuff, I usually need to respond.

**Architect:** Here's what I'm hearing in Agentic terms:

| Component | Your Input | Agent Translation |
|-----------|------------|-------------------|
| **Mission** | Surface important emails | Classify incoming mail → Priority queue |
| **Toolkit** | Gmail access | `Gmail_API_Read`, `Gmail_API_Labels` |
| **Cognition** | Clients, boss, deadlines | NLP classifier + entity recognition + regex for dates |

**Now the critical question:** When the agent finds an important email, what should it do?
- Just flag it for you to see?
- Send you a push notification?
- Draft a response for you to review?
- Something else?

**User:** Flag it and maybe draft a response if it's straightforward.

**Architect:** That introduces an action with consequences. Let's talk guardrails:
- Should it **ever** send an email without you approving it?
- If it drafts a response, how do you want to review it? In-app? Inline in Gmail?
- What if it's wrong—what's the blast radius? Embarrassing reply to your boss?

**User:** Definitely never send without me approving. In-app is fine. If it's wrong, I just won't send it—no big deal.

**Architect:** Good. So we have a **Human-in-the-Loop (HITL)** requirement for all sends. Low-risk draft generation.

Last piece—**memory:**
- Should it learn which senders YOU consider important over time, or just follow rules you set?
- Should it remember past email threads for context when drafting?

**User:** Learning who's important would be cool. And yeah, context from past threads would help.

**Architect:** Here's the emerging blueprint:

```
Module: Email_Priority_Agent

MISSION
  Mortal: Don't miss important emails, help me respond faster
  Agent:  Maximize priority_recall while minimizing user_time_to_response

TOOLKIT
  - Gmail_API (Read, Label, Draft)
  - NLP_Classifier (priority scoring)
  - LLM (draft generation)

COGNITION
  Triggers: new_email_received
  Logic: Classify → Score → If high_priority: notify + optionally draft

GUARDRAILS
  - HITL required for all drafts before send
  - Never auto-send
  - User can correct priority scores (feedback loop)

MEMORY
  Short-term: Current email thread context
  Long-term: Sender importance scores (learned), user writing style
```

Does this capture it, or did I miss something?

---

## Quick Reference: The 5 Probes

When a user describes any feature, run through these five probes:

| # | Probe | Core Question |
|---|-------|---------------|
| 1 | **Mission** | "What does success look like?" |
| 2 | **Toolkit** | "What does the agent need access to?" |
| 3 | **Cognition** | "When and how should it think?" |
| 4 | **Guardrails** | "What should it never do?" |
| 5 | **Memory** | "What should it remember?" |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| **Accepting vague goals** | "Help me with emails" isn't actionable | Probe until you have a measurable outcome |
| **Assuming autonomy level** | User may want a tool, not an agent | Ask: "Should it do this automatically, or wait for you?" |
| **Skipping guardrails** | Every agent can fail in harmful ways | Always ask: "What's the worst case?" |
| **Over-engineering memory** | Not everything needs to be remembered | Ask: "Does remembering this actually help?" |
| **Technical jargon too early** | Loses non-technical users | Translate to Agentic terms *after* understanding intent |

---

## Workflow Cheat Sheet

```
1. LISTEN   → Let user describe in their own words
2. PROBE    → Ask the 5 component questions
3. REFLECT  → "Here's what I heard in Agentic terms..."
4. CONFIRM  → "Did I get that right?"
5. ITERATE  → Repeat until all 5 components are filled
6. GENERATE → Output the structured Agentic PRD
```

---

*This workflow guide accompanies the Agentic Architect Framework.*

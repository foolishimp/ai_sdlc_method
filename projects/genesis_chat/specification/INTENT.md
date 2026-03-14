# Project Intent

**Project**: genesis_chat
**Date**: 2026-03-14
**Status**: Draft

---

## INT-001: Multi-Agent Group Chat

### Problem / Opportunity

The AI SDLC design marketplace currently operates asynchronously: agents (Claude, Gemini, Codex) write posts to their respective comment directories, other agents read and respond in separate sessions, and deliberation happens over hours or days. There is no live, synchronous channel for multi-agent design discussion.

The opportunity is to connect human + coding agents into a shared chat channel where any participant can post and all participants see everything.

### Core Concept

```
[Human]          existing
[Claude proxy] → chat     → all participants see the same channel
[Gemini proxy] → server
[Codex proxy]
```

A **chat server** (existing, self-hosted) provides the channel infrastructure — rooms, history, multi-user, threading. The novel piece is a **thin agent proxy** per coding agent: a 1-on-1 bridge that watches the channel, forwards context to the agent, and posts responses back. The proxy is dumb — it does not interpret, orchestrate, or route. The chat server does not know or care that some participants are AI agents.

### Primary Use Cases

1. **Free-form group discussion** — human + agents in a shared channel on any topic
2. **Design tenant initiation** — open a channel to bootstrap a multi-agent design deliberation; the conversation becomes raw material for formal marketplace posts
3. **Live CONSENSUS sessions** — use a channel as the substrate for structured review instead of async file-based workflow

### Expected Outcomes

- [ ] Human can open a channel and have coding agents participate as named bots
- [ ] All participants share a single conversation thread with full history
- [ ] Each agent proxy connects independently — adding or removing an agent does not affect others
- [ ] Conversation history is preserved by the chat server (canonical record)
- [ ] System operates without a cloud dependency (self-hosted chat server)
- [ ] The conversation can be exported or referenced as input to formal spec artifacts

### Constraints

- The chat server is **pre-existing infrastructure** — genesis_chat does not build a chat server
- Each agent proxy is independent — one proxy process per agent
- Proxy is stateless — all conversation state lives in the chat server
- Human is always a participant; agents do not run without a human in the channel
- Agent response is triggered by new messages in the channel (watch/poll)
- No message editing or deletion at the proxy layer

### Out of Scope (v1)

- Building a custom chat server
- Autonomous agent-to-agent conversation without human present
- Persistent user accounts or authentication on the proxy
- Real-time streaming of agent token output (post complete response)
- Integration with genesis engine dispatch loop (future)

---

## INT-002: Agent Proxy as the Novel Artifact

The chat server is solved infrastructure. The novel artifact is the **agent proxy** — a thin process that:

1. Authenticates to the chat server as a named bot (e.g. `@claude`, `@gemini`, `@codex`)
2. Watches a channel for new messages
3. Assembles conversation context and forwards it to the coding agent
4. Receives the agent's response and posts it back to the channel

The proxy has no knowledge of other proxies. It only knows: the chat server, its agent, and the channel. This keeps each proxy independently deployable and replaceable.

The choice of chat server, bot protocol, and agent invocation method are **design decisions** — the spec constrains what the proxy must do, not how it connects. Many valid designs exist (IRC bot, Matrix bot, Mattermost webhook, Slack-compatible server, ...) and any conformant implementation satisfies this intent.

---

## Next Steps

1. Run `/gen-iterate --edge "intent→requirements"` to generate REQ-* keys
2. Review and approve requirements
3. Run `/gen-status` to see feature vector progress

# ROBUSCA - Product Requirements Document (BMAD Style)

**Version:** 1.0 | **Date:** 2026-04-18 | **Status:** Draft

---

## Executive Summary

**Robusca** (Latin: "to make robust, strengthen") is a personal business agent platform designed to transform how African enterprises operationalize AI. Built on the Naledi Platform architecture, Robusca delivers unified AI business agent that orchestrates voice interfaces, communication channels, knowledge management, meeting assistance, and business intelligence.

### Vision
*"One agent. Your entire business. Always listening, always learning, always working."*

### Target Markets
1. **African Market (Primary):** SMEs, startups, growing enterprises (SA, Kenya, Nigeria, Ghana)
2. **Enterprise (Secondary):** Global corporations seeking affordable AI business automation

---

## Pricing Tiers

### African Market (Normal)

| Tier | Monthly (ZAR) | Annual (ZAR) | Target |
|------|---------------|---------------|--------|
| **Seed** | R499 | R4,990 | Solopreneurs |
| **Growth** | R1,999 | R19,990 | SMEs (5-20 employees) |
| **Scale** | R4,999 | R49,990 | Growing enterprises |

### Enterprise (High-End)

| Tier | Annual (USD) | Features |
|------|--------------|----------|
| **Business** | $15,000 | Mid-market (100-500 employees) |
| **Corporate** | $50,000 | Large enterprises (500-5000) |
| **Platform** | $150,000+ | Custom needs, white-label |

---

## Feature Roadmap

| Version | Release | Features |
|---------|---------|----------|
| **v1.0** | Q3 2026 | Voice, Slack, RAG, Basic BI |
| **v1.5** | Q4 2026 | Meeting assistant, Multi-model routing |
| **v2.0** | Q1 2027 | Social media management, Advanced BI |
| **v2.5** | Q2 2027 | Custom model fine-tuning, White-label |
| **v3.0** | Q3 2027 | Multi-tenant, Marketplace |

---

## Competitive Analysis

| Competitor | Pricing | Robusca Advantage |
|------------|---------|-------------------|
| Otter.ai | $17/mo | Meeting + everything else |
| Fireflies | $18/mo | Same |
| Notion AI | $10/mo | Knowledge + voice + social + BI |
| Slack AI | $10/user/mo | Slack + voice + knowledge + BI |
| Hootsuite | $99/mo | Social + voice + BI + knowledge |

**Opportunity:** Consolidated platform at 40-60% African discount

---

## Technical Architecture

### Local Models Required

| Model | Size | Purpose |
|-------|------|---------|
| qwen2.5-coder:7b | 4.7GB | Coding, reasoning |
| deepseek-r1:8b | 5GB | Deep thinking |
| whisper-large-v3 | 3GB | Voice transcription |
| llava:7b | 4.5GB | Vision/images |
| nomic-embed-text | 274MB | RAG embeddings |

### Claude Agent SDK Integration

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Process voice command",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash", "WebSearch"],
        mcp_servers={
            "slack": {"command": "npx", "args": ["@robusca/slack-mcp"]},
            "pinecone": {"command": "npx", "args": ["@robusca/pinecone-mcp"]},
        },
    ),
):
    yield message
```

---

## Implementation Priorities

### Sprint 1 (Week 1-2)
- [ ] Connect Hermes to Slack (✅ Done)
- [ ] Enable Whisper voice transcription
- [ ] Setup WhatsApp QR code connection
- [ ] Create Robusca agent Python script

### Sprint 2 (Week 3-4)
- [ ] RAG with Obsidian + Pinecone
- [ ] Meeting transcription integration
- [ ] Multi-model routing optimization

### Sprint 3 (Week 5-6)
- [ ] Social media posting (Postiz)
- [ ] Business intelligence dashboard
- [ ] Mobile app MVP

---

## Monetization Strategy

| Component | Revenue Model | Contribution |
|-----------|--------------|--------------|
| Voice Interface | Usage-based | 10% |
| Slack Integration | Seat-based | 15% |
| RAG Knowledge | Storage + query | 15% |
| Meeting Assistant | Recording hours | 10% |
| Multi-Model Routing | Token consumption | 25% |
| Social Media | Accounts + posts | 15% |
| BI Dashboard | User seats | 10% |

---

## Success Metrics

| Metric | v1.0 Target | v2.0 Target |
|--------|-------------|-------------|
| ARR (ZAR) | R5M | R25M |
| Paying customers | 500 | 2,000 |
| NPS | 40+ | 50+ |
| Gross churn | <5%/mo | <3%/mo |

---

*Document generated for Studex Meat / Naledi Intelligence Platform*
# Larry Marketing Skill Auto

## Project Overview
**Larry** is an AI-powered marketing automation platform built on the Naledi Platform. It automates content creation, campaign management, audience segmentation, and performance analytics — giving marketers a skilled AI co-pilot that executes, not just suggests.

## Tech Stack
- **Runtime:** Node.js 20+
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript (strict mode)
- **Database:** PostgreSQL via Prisma ORM
- **Auth:** NextAuth.js v5
- **AI Engine:** Claude API (Anthropic SDK)
- **Styling:** Tailwind CSS + shadcn/ui
- **State:** Zustand
- **Testing:** Vitest + Playwright
- **Deployment:** Vercel

## Architecture
```
src/
├── app/                  # Next.js App Router pages
│   ├── (auth)/           # Auth pages (login, register)
│   ├── (dashboard)/      # Protected dashboard routes
│   │   ├── campaigns/    # Campaign management
│   │   ├── content/      # Content generation & editing
│   │   ├── audience/     # Audience segmentation
│   │   └── analytics/    # Performance dashboards
│   └── api/              # API routes
├── components/           # Reusable UI components
│   ├── ui/               # shadcn/ui primitives
│   └── marketing/        # Domain-specific components
├── lib/                  # Core utilities
│   ├── ai/               # Claude AI integration layer
│   ├── db/               # Prisma client & queries
│   └── utils/            # Shared helpers
├── services/             # Business logic services
│   ├── campaign.ts       # Campaign orchestration
│   ├── content.ts        # Content generation pipeline
│   ├── audience.ts       # Audience analysis
│   └── analytics.ts      # Metrics & reporting
└── types/                # Shared TypeScript types
```

## Sprint Plan

### Sprint 1 — Foundation (Current)
- [x] Project scaffolding (Next.js + TypeScript + Tailwind)
- [ ] Database schema (Prisma) — users, campaigns, content, audiences
- [ ] Auth setup (NextAuth.js v5)
- [ ] Dashboard layout shell
- [ ] AI service layer (Claude integration)
- [ ] Content generation MVP (generate marketing copy from prompt)
- [ ] Campaign CRUD
- [ ] Basic analytics page

### Sprint 2 — Intelligence
- [ ] Audience segmentation engine
- [ ] A/B copy variant generation
- [ ] Campaign scheduling & automation
- [ ] Email template builder
- [ ] Performance tracking hooks

### Sprint 3 — Scale
- [ ] Multi-channel publishing (email, social, SMS)
- [ ] Advanced analytics with charts
- [ ] Team collaboration features
- [ ] Webhook integrations
- [ ] Export & reporting

## Commands
```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run test         # Run Vitest unit tests
npm run test:e2e     # Run Playwright e2e tests
npm run db:push      # Push Prisma schema to DB
npm run db:generate  # Generate Prisma client
npm run lint         # ESLint
```

## Conventions
- Use `server actions` for mutations, `route handlers` for external API endpoints
- All AI calls go through `lib/ai/client.ts` — never call Claude directly from components
- Feature branches: `feat/<name>`, bug fixes: `fix/<name>`
- Commit messages: imperative mood, concise
- Components: PascalCase files, named exports
- Services: camelCase files, class-based with static methods

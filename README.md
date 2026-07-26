# Production-Grade GitHub-Based Candidate Evaluation Platform

A transparent, auditable platform for evaluating software engineering candidates based on time-boxed GitHub activity.

## Architectural Highlights & Key Features

1. **Window-Bounded Activity Sync** ([sync_service.py](file:///c:/Users/vedaa/OneDrive/Desktop/resume-project/github/sync_service.py)):
   - Never syncs commits or PRs outside the designated `[start_date, end_date]` window.
   - Prevents pre-existing repository history from leaking into candidate scoring.

2. **Immutable Scoring Ledger** ([db_trigger.sql](file:///c:/Users/vedaa/OneDrive/Desktop/resume-project/github/db_trigger.sql)):
   - Enforced at the **PostgreSQL DB layer** via a custom PL/pgSQL trigger function (`check_score_breakdown_immutability()`).
   - Prevents any `UPDATE` or `DELETE` on `score_breakdown` rows when `evaluations.status = 'locked'`.

3. **5-Signal Weighted Scoring Engine** ([scoring_engine.py](file:///c:/Users/vedaa/OneDrive/Desktop/resume-project/github/scoring_engine.py)):
   - **Consistency**: Active day ratio with heavy penalties for last 10% window commit concentration (>60%).
   - **PR Quality**: Line size normalization (ideal 50–500 LOC) and clean merge state.
   - **Review Cycles**: Penalty for repeated requested-changes rounds.
   - **Collaboration**: Activity on peer PRs (auto-redistributes weight to 0 for solo candidate evaluations).
   - **Code Churn / Stability**: Penalty for touching files 5+ times in <2 weeks.

4. **Background Sync & PDF Export**:
   - In-process APScheduler running rate-limit-safe GraphQL background sync every 15 minutes.
   - Server-side ReportLab PDF report generator for shareable candidate score cards.

## Quick Start (Docker)

```bash
cp .env.example .env
docker-compose up --build
```

Access Services:
- **API Documentation (Swagger/OpenAPI)**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000
- **Adminer DB Inspection**: http://localhost:8080

## Technical Pitch Summary for Interviews

> "We built an auditable candidate evaluation platform where scoring integrity is defensible legally and algorithmically. We enforced time window bounds at the GraphQL sync layer so legacy repo code never inflates scores, and locked final scores into an append-only PostgreSQL ledger backed by a database trigger that rejects any mutation once an evaluation closes."

# Requirements Document

## Introduction

The Legal Case Intelligence system for Kansas City is designed to deliver early, actionable litigation leads for small/mid-sized plaintiff firms in the KC metro area. The system automates the entire pipeline from document ingestion through enrichment, lead ranking, and weekly briefings, with clear citations and compliance with data access requirements. The system is multi-tenant by design using Row Level Security (RLS) and focuses on ADA Title III and Product Liability practice areas.

## Requirements

### Requirement 1: Document Ingestion and Storage

**User Story:** As a system operator, I want the system to automatically fetch and store legal documents from approved sources, so that we have a comprehensive repository of potential litigation leads.

#### Acceptance Criteria

1. WHEN a new document/feed item is available from an approved source (CourtListener, FDA, DOJ, state docket, local RSS) THEN the system SHALL fetch and persist the raw artifact in object storage with tenant-scoped prefixes and metadata
2. WHEN storing raw files THEN the system SHALL use the path convention `s3://tenant/<org_id>/raw/<date>/<source>/<doc>` with metadata including `source`, `jurisdiction`, `published_at`, `hash`
3. WHEN a raw artifact is stored THEN the system SHALL normalize it to clean text (OCR as needed) and persist normalized text to a versioned store
4. WHEN normalizing text THEN the system SHALL ensure text is available in `doc_text` with `token_count`, checksum matches, and retries/backoff logged on failure

### Requirement 2: Content Processing and Chunking

**User Story:** As a data engineer, I want documents to be processed into searchable chunks with relevant metadata, so that the system can efficiently retrieve relevant content for lead generation.

#### Acceptance Criteria

1. WHEN normalized text is ready THEN the system SHALL chunk content by semantic/heading boundaries and attach source/jurisdiction/practice-area hints in `meta`
2. WHEN creating chunks THEN the system SHALL ensure chunks are ≤ 2k tokens with `chunk.meta` including `source`, `court`, `date`, `practice_area_candidates`
3. WHEN chunks are created THEN the system SHALL compute embeddings using the configured model and deduplicate by `(hash + model)`
4. WHEN storing embeddings THEN the system SHALL upsert to `embedding` table with `org_id`, `chunk_id`, `model`, `vector` and skip duplicates

### Requirement 3: Lead Detection and Scoring

**User Story:** As an attorney, I want the system to automatically identify potential litigation opportunities and score them by relevance, so that I can focus on the most promising leads.

#### Acceptance Criteria

1. WHEN new content matches practice-area triggers THEN the system SHALL create a `lead` with title, summary stub, confidence score, jurisdiction, and `source_ids`
2. WHEN creating leads THEN the system SHALL record rule hits (regex/keywords) and vector matches, creating lead row with `status = 'new'`
3. WHEN evaluating a lead THEN the system SHALL compute a Signal Strength with a deterministic rubric (Source authority, Recency, Volume/velocity, Local relevance) and produce a single confidence value 0–1
4. WHEN scoring leads THEN the system SHALL store scorecard fields and ensure identical inputs yield identical scores
5. WHEN a lead is outside the firm's selected jurisdictions THEN the system SHALL suppress it by default but allow override in settings

### Requirement 4: Brief Generation and Citations

**User Story:** As an attorney, I want detailed briefs with proper citations for each lead, so that I can quickly understand the opportunity and verify the information.

#### Acceptance Criteria

1. WHEN a lead is promoted to briefing THEN the system SHALL generate a 5-bullet brief including (1) What happened; (2) Parties/statutes; (3) Jurisdiction & timing; (4) Why it fits the firm; (5) Next steps, with explicit citations to sources/chunk anchors
2. WHEN generating briefs THEN the system SHALL store brief with at least one citation per bullet and use hallucination guard to abstain if below threshold context
3. WHEN a user opens a lead THEN the system SHALL render "Why this fits us" grounded in firm KB (if provided) or practice-area profile; otherwise, show generic rationale
4. WHEN rendering explanations THEN the system SHALL show section with citations or a clear "insufficient evidence" disclaimer

### Requirement 5: Search and Retrieval

**User Story:** As an attorney, I want to search through leads and source documents efficiently, so that I can find relevant information quickly.

#### Acceptance Criteria

1. WHEN a candidate search runs THEN the system SHALL retrieve Top-K by vector similarity, then rerank with a cross-encoder or API reranker to Top-N (≤10) for LLM summarization
2. WHEN performing searches THEN the system SHALL log `TopK`, rerank scores, latency with N configurable per run
3. WHEN filtering searches THEN the system SHALL support filters for `practice_area`, `jurisdiction`, `confidence`, `date`, `status`

### Requirement 6: Dashboard and User Interface

**User Story:** As an attorney, I want an intuitive dashboard to view and manage leads, so that I can efficiently review potential litigation opportunities.

#### Acceptance Criteria

1. WHEN a user visits Leads Dashboard THEN the system SHALL list leads with filters for `practice_area`, `jurisdiction`, `confidence`, `date`, `status`
2. WHEN using dashboard filters THEN the system SHALL update filtering in ≤200ms (cached) with pagination present and empty state shown
3. WHEN a lead is viewed THEN the system SHALL display source documents with deep links (e.g., CourtListener URL) and page anchors
4. WHEN displaying source links THEN the system SHALL open external links in new tab and flag 404s

### Requirement 7: Notifications and Digests

**User Story:** As an attorney, I want regular email digests of new leads, so that I stay informed of opportunities without constantly checking the dashboard.

#### Acceptance Criteria

1. WHEN it's the scheduled digest time (daily/weekly) THEN the system SHALL email a brief with Top-10 leads and "what changed this week," with deep links back to Lead Detail
2. WHEN sending digests THEN the system SHALL deliver email to org users with `digest_opt_in=true` and support unsubscribe per user

### Requirement 8: Feedback and Learning

**User Story:** As an attorney, I want to provide feedback on lead quality, so that the system can improve its recommendations over time.

#### Acceptance Criteria

1. WHEN a user submits feedback (👍/👎 + note) THEN the system SHALL log it and surface as training signal for scoring/LLM prompts
2. WHEN storing feedback THEN the system SHALL persist `feedback` row and update Lead card with aggregate signal

### Requirement 9: Multi-Tenant Administration

**User Story:** As a firm administrator, I want to manage organization settings and ensure data isolation, so that our firm's data remains secure and properly configured.

#### Acceptance Criteria

1. WHEN an org is created via Clerk THEN the system SHALL map `clerk.org_id → organization.id` and enforce Postgres RLS across all tenant tables
2. WHEN implementing RLS THEN the system SHALL ensure RLS policies prevent cross-org reads/writes with automated tests to verify
3. WHEN an Admin updates Settings THEN the system SHALL persist selections for practice areas, jurisdictions, and keywords, and apply them on the next pipeline run
4. WHEN updating settings THEN the system SHALL ensure settings round-trip and create audit log entry

### Requirement 10: Observability and Cost Management

**User Story:** As a system administrator, I want to monitor system performance and costs, so that I can ensure efficient operation and budget compliance.

#### Acceptance Criteria

1. WHEN any LLM call runs THEN the system SHALL record tokens, latency, and cost to `prompt_run` and surface a per-org cost report
2. WHEN tracking costs THEN the system SHALL make daily cost totals visible and provide exported CSV with task/lead context
3. WHEN the pipeline fails at any stage THEN the system SHALL emit alerts and queue automatic retries with exponential backoff; manual re-run available
4. WHEN handling failures THEN the system SHALL make failures visible in UI with working re-run button and ensure idempotency prevents duplicate leads

### Requirement 11: Performance and Quality Standards

**User Story:** As a user, I want the system to perform reliably and deliver high-quality results, so that I can depend on it for my legal practice.

#### Acceptance Criteria

1. WHEN running daily pipeline (KC scope) THEN the system SHALL complete in ≤30 min with Lead card render ≤500ms P95
2. WHEN evaluating lead quality THEN the system SHALL achieve Precision@10 of "useful" leads ≥ 0.6 in pilot month 1
3. WHEN ensuring security THEN the system SHALL implement tenant isolation via RLS, S3 signed URLs, and audit logs for sensitive ops
4. WHEN accessing external sources THEN the system SHALL respect source ToS, prefer official APIs/feeds, and use configurable request rates
5. WHEN designing user interface THEN the system SHALL meet WCAG AA standards, be keyboard navigable, and include ARIA labels
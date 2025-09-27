# Implementation Plan

## Sprint 1 (Weeks 1-3): Core Infrastructure and Basic Pipeline

- [x] 1. Bootstrap Repo & Tenancy
  - Set up Next.js App Router with Clerk organizations integration
  - Create Postgres schema with Row Level Security (RLS)
  - Implement seed scripts for development data
  - _Requirements: 9.1, 9.2_

- [x] 2. Ingest API & Source Aggregation
  - Implemented api/ingest/run endpoint for document ingestion
  - Created lib/ingest module to aggregate and process sources
  - Set up document processing pipeline with proper metadata handling
  - _Requirements: 1.1, 1.2_

- [x] 3. Fix Clerk Organization Integration & Onboarding
  - Create organization mapping table or update existing schema
  - Implement firm onboarding flow for organizations without existing records
  - Test organization creation and user association
  - _Requirements: 9.1, 9.2_

- [x] 4. Simple Text Processing (API-First)
  - Create basic text processor for API responses (CourtListener, FDA, DOJ)
  - Handle JSON/XML to clean text conversion
  - Write normalized text to `doc_text` table with token counts
  - Skip OCR/PDF processing for MVP (move to later sprint)
  - _Requirements: 1.3, 1.4_

- [ ] 5. Chunker Implementation
  - Create semantic/heading-based text splitter
  - Attach metadata (source, court, date, practice area hints) to chunks
  - Ensure chunks are ≤ 2k tokens with stable ordering
  - Write comprehensive tests with fixture documents
  - _Requirements: 2.1, 2.2_

- [ ] 6. Embeddings Store (pgvector)
  - Implement embedding computation using configured model
  - Set up deduplication by `(hash + model)` combination
  - Create pgvector index for similarity queries
  - Verify similarity search returns expected neighbors
  - _Requirements: 2.3, 2.4_

- [ ] 7. Candidate Detection (Rules + Vectors)
  - Implement practice area triggers for ADA Title III and Product Liability
  - Combine regex pattern matching with vector similarity hits
  - Create lead records with proper scoring and metadata
  - Test with synthetic corpus to yield expected candidates
  - _Requirements: 3.1, 3.2_

- [ ] 8. Rerank & Brief Generation (LLM)
  - Implement Top-K to Top-N reranking using cross-encoder
  - Create brief generation prompt with 5-bullet structure
  - Integrate Langfuse for prompt tracing and monitoring
  - Add hallucination guard to abstain when context is insufficient
  - _Requirements: 4.1, 4.2, 5.1, 5.2_

- [x] 9. Leads Dashboard (List + Filters) - PRIORITY FOR MAGIC
  - Create lead list view with score chips and status indicators
  - Implement filters for practice area, jurisdiction, confidence, date, status
  - Add pagination and empty state handling
  - Optimize for P95 ≤500ms response time with caching
  - _Requirements: 6.1, 6.2_

- [x] 10. Lead Detail + Sources Panel - PRIORITY FOR MAGIC
  - Create detailed lead view with brief on left panel
  - Implement sources panel with deep links to original documents
  - Add feedback widget for thumbs up/down with notes
  - Handle missing or broken source links gracefully
  - _Requirements: 4.3, 4.4, 6.3, 6.4, 8.1, 8.2_

- [ ] 11. Admin Settings (Practice Areas/Jurisdictions)
  - Create settings page with toggles for practice areas and jurisdictions
  - Implement settings persistence and pipeline integration
  - Add audit logging for settings changes
  - Ensure settings changes affect next pipeline run
  - _Requirements: 9.3, 9.4_

## Sprint 2 (Weeks 4-6): Pipeline Orchestration and Advanced Features

- [ ] 12. Temporal/Dagster Orchestration
  - Set up daily 6am local time pipeline scheduling
  - Implement manual "Run now" admin action
  - Ensure idempotent pipeline runs to prevent duplicate leads
  - Add pipeline run visibility and retry/backoff mechanisms
  - _Requirements: 10.3, 10.4_

- [ ] 13. Digest Email (Weekly)
  - Create email template for Top-10 leads and weekly changes
  - Implement deep links back to lead details
  - Add per-user opt-in/opt-out functionality
  - Test email rendering across major email clients
  - _Requirements: 7.1, 7.2_

- [ ] 14. Cost & Telemetry Panel
  - Aggregate `prompt_run` data for tokens and cost tracking
  - Create daily cost graphs and per-lead breakdowns
  - Implement CSV export functionality for cost analysis
  - Integrate Langfuse trace explorer links
  - _Requirements: 10.1, 10.2_

- [ ] 15. Security Hardening
  - Implement S3 SSE-KMS encryption for stored documents
  - Add comprehensive audit logging for sensitive operations
  - Create RLS fuzz tests to verify tenant isolation
  - Run security penetration testing checklist
  - _Requirements: 11.3_

- [ ] 16. Performance & Precision Tuning
  - Implement caching for hot dashboard filters
  - Tune Top-K and Top-N parameters for optimal results
  - Evaluate Precision@10 using pilot feedback data
  - Optimize dashboard performance to meet P95 ≤500ms target
  - _Requirements: 11.1, 11.2_

- [ ] 17. Advanced Document Processing (OCR & Complex Formats)
  - Implement OCR processing for PDF and image documents
  - Create HTML cleaner for web-scraped content
  - Add support for complex document formats
  - Implement retry logic with exponential backoff for processing failures
  - _Requirements: 1.3, 1.4_

- [ ] 18. Source Integrations (MVP Set)
  - Integrate CourtListener API for court opinions and dockets
  - Connect FDA recalls API for product liability cases
  - Set up DOJ ADA enforcement updates feed
  - Implement Missouri Case.net compliant data access
  - Add curated RSS feeds for local legal news
  - Implement health checks and rate limiting for all sources
  - _Requirements: 11.4_

## Buffer (Weeks 7-8): Optimization and Polish

- [ ] 19. Scoring Rubric Iteration
  - Calibrate scoring weights using pilot user feedback
  - Add A/B testing toggles for scoring algorithm variations
  - Implement ablation testing to measure scoring improvements
  - Validate improved Precision@10 versus baseline scoring
  - _Requirements: 3.3, 3.4_

- [ ] 20. Firm Knowledge Base Upload (Optional)
  - Implement signed upload for firm-specific documents
  - Tag uploaded documents with `source=firm_kb`
  - Exclude firm KB from public RAG by default
  - Enhance "why this fits us" section with firm-specific context
  - _Requirements: 4.3, 4.4_

- [ ] 21. UX Polish & Accessibility
  - Add empty states and loading skeletons throughout UI
  - Implement score legend tooltips and help text
  - Ensure full keyboard navigation support
  - Add comprehensive ARIA labels for screen readers
  - Conduct WCAG AA accessibility audit
  - _Requirements: 11.5_

## Definitions of Done

### Testing Requirements
- **Unit Tests:** All chunker/scoring algorithms, API route handlers
- **Integration Tests:** Full pipeline end-to-end, database operations
- **E2E Tests:** Critical dashboard user flows, authentication
- **Performance Tests:** Load testing for concurrent users, API response times

### Observability Requirements
- **Tracing:** Every LLM call appears in Langfuse with proper input/output logging
- **Monitoring:** Error rates, response times, and cost metrics tracked
- **Alerting:** Pipeline failures trigger notifications with retry mechanisms

### Documentation Requirements
- **README:** Complete environment setup and development instructions
- **Runbooks:** Pipeline failure recovery procedures and troubleshooting
- **API Docs:** Comprehensive API documentation with examples

### Security Requirements
- **RLS Policies:** All tenant isolation policies reviewed and tested
- **Secrets Management:** All sensitive data stored in secure vault
- **IAM:** Least-privileged access policies for S3 and external services
- **Audit Trail:** Complete audit logging for all administrative a
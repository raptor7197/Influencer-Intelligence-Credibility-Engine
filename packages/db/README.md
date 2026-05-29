# Database Layer Scaffold

PostgreSQL-backed persistence layer for campaigns, discovery runs, influencer candidates, scoring evidence, and outreach drafts.

## Planned Structure
- `schema` - canonical table and entity definitions
- `migrations` - database migrations
- `sql` - raw SQL helpers and shared queries

## Notes
- This is scaffold only.
- Database persistence is required because campaigns are stored, not session-based.

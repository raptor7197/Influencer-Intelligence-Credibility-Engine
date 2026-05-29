# n8n Integration Scaffold

This directory contains the contract and adapter layer for the cloud-hosted n8n discovery workflow.

## Responsibilities
- Trigger discovery via webhook
- Track async discovery run state
- Normalize raw candidate output
- Feed downstream scoring jobs

## Notes
- n8n remains the Stage 1 discovery engine.
- Scoring is auto-triggered after discovery completes.
- Candidate cap is 20 per run.

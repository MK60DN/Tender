# Changelog

## v2.2.1 - 2026-11-02

- Added explicit account switching, logout, irreversible learner-data deletion and Tender shutdown controls.
- Replaced the public role workspace with a redirect to the learner data page and removed the legacy role UI assets.
- Added a required world-coordinate onboarding step for stage, grade, subjects, major, current focus and goal.
- Removed automatic demo-roster loading from login and multi-person screens.
- Added world-coordinate summaries to the assessment and personal data pages.
- Added regression tests for world setup, data deletion, local shutdown and removed role entry.
- Added a GitHub Pages static app and one-click full-backend paths through GitHub Codespaces and Render.
- Added Docker port adaptation, Render Blueprint configuration, a dev container, and deployment documentation.


## v2.2.0 - 2026-11-01

- Added local Screen Context MCP with explicit consent, expiry, revocation, visible-window enumeration, accessible text and optional in-memory screenshots.
- Added local multimedia MCP for RapidOCR, faster-whisper transcription, video-frame OCR, ffmpeg audio extraction and SAPI5 speech synthesis.
- Added `读界面` and `媒体` controls to the desktop danmaku overlay.
- Kept raw window text, screenshots and media content out of DAOQL; only coarse derived signals reach the ambient planner.
- Published Whitepaper V2.2, Product Manual V7.2, User Guide V7.2 and Teaching Manual V6.2.
- Expanded tests to 130 passing with one opt-in heavy-media test skipped.

## v1.6.1 - 2026-10-31

- Removed superseded whitepaper, product manual, user guide and teaching manual files from the active repository and teaching site.
- Removed the unrelated legacy analysis-engine snapshot from the active product repository; v1.6.0 remains the recoverable pre-cleanup snapshot.
- Rewrote the document index to list only current official documents.
- Kept historical release information in Git tags and this changelog rather than in user-facing document folders.

## v1.6.0 - 2026-10-31

- Defined one shared Tender Core with three delivery surfaces: full B2B education system, embedded B2B module, and C-end life interface.
- Rebuilt Whitepaper V1.6, Product Manual V6.20, User Guide V6.8, and Teaching Manual V5.3.
- Updated the bilingual teaching course to nine modules and unified all document links and version metadata.
- Preserved institutional and personal data boundaries: B2B deployment does not grant access to the personal learning passport.

## v1.5.0 - 2026-10-30

- Published Whitepaper V1.5 and the earlier bilingual teaching course.
- Added language-evidence extraction, knowledge forest and the initial repository release.
- Changed the project license to PolyForm Noncommercial 1.0.0.
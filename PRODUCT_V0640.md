# Upplevio v0.64.0 – Booking Link Safety Hardening

## Goal
Prevent unsafe, irrelevant or weakly inferred links from becoming booking links.

## Changes
- Explicit HTTP/HTTPS enforcement.
- Blocks javascript:, data:, mailto:, tel: and fragment-only hrefs.
- Blocks social-media destinations.
- Rejects unknown external hosts even when CTA text looks strong.
- Allows known ticket partners.
- Allows same official host/subdomain with strong Swedish booking CTA.
- Rejects generic/root homepages.
- Treats “Biljetter” as a medium-strength CTA requiring ticket-partner or ticket-like path evidence.
- Removes broad English “book” matching.
- Adds regression tests for all safety cases.

## Product principle
A missing booking link is preferable to a wrong or unsafe booking link.

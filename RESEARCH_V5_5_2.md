# V5.5.2 — Live-response repair and scope

The live Census 2024 ACS 1-year PUMS household API query returned 8,796 Maine household records and automatically appended `RT` and `state` fields. V5.5.1 requested `RT` explicitly and also filtered on `RT=H`, producing a duplicate column and triggering its fail-closed parser.

V5.5.2 removes `RT` from both household and person `get` lists while retaining `RT=H` and `RT=P` filters. It validates required columns, record types, geography, unique household identifiers, person identifiers, and person counts against household `NP` before writing raw extracts. Tests use the observed Census response header shape.

This is a live-interface compatibility fix, not a claim of independent API completeness. The conservative response-size guard remains. Reconcile state/year row counts and weights against official bulk ACS PUMS releases before publishing inference. Replicate weights and cross-year inflation/harmonization are not implemented. The Maine pilot must not be interpreted as a national historical estimate.

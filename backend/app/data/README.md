The NQR snapshot contains seven records fetched from the official NCVET register.
Each record retains its actual NQR code, numeric source URL, full alternative
entry routes, modules, awarding body, duration, level and validity date.

Refresh explicitly from `backend` with:

    ./venv/Scripts/python.exe scripts/refresh_nqr_catalogue.py

Review snapshot changes before deploying. Application startup imports the checked
snapshot without needing the NQR website to be online. This is a curated snapshot,
not an automatic live feed or a complete national catalogue. Expired records are
excluded from recommendations and the public catalogue, including saved matches.
Matching conservatively uses the school-entry route; it does not assume the user
has years of experience or prior vocational qualifications. Alternate routes remain
visible for review. Work preference and physical intensity defaults are internal
matching metadata, not assertions from NQR. Accessibility must be checked locally.

NQR approval does not verify a local provider, batch, seat, fee or enrollment.
The importer retires the previous twelve sample qualification IDs and archives
their sample batches, retaining history and references. It creates no local batches.
Register opens the official Skill India Digital Hub portal. Ask for help creates
a separate consented assistance request; neither action confirms admission.

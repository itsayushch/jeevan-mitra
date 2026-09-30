import sys
import os
import argparse
import logging
from app.database import get_db
from app.services.opportunity_expiry_service import OpportunityExpiryService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run(dry_run=False):
    with get_db() as conn:
        logger.info(f"Starting opportunity expiry job. Dry run: {dry_run}")
        expired = OpportunityExpiryService.process_expiries(conn, dry_run=dry_run)
        conn.commit()
        if not dry_run:
            logger.info(f"Successfully expired {len(expired)} opportunities: {expired}")
        else:
            logger.info(f"Would have expired {len(expired)} opportunities.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expire stale opportunities")
    parser.add_argument("--dry-run", action="store_true", help="Do not apply changes")
    args = parser.parse_args()
    run(dry_run=args.dry_run)

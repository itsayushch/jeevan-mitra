import sys
import json
from pathlib import Path

# Add backend root to path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from app.services.alert_service import OperationalAlertService


def main():
    print("Evaluating operational health and alert conditions...")
    report = OperationalAlertService.evaluate_all_alerts()
    print(json.dumps(report, indent=2))

    status = report.get("status")
    alert_count = report.get("alert_count", 0)

    if status == "CRITICAL":
        print(f"\n[ERROR] Critical operational alerts detected ({alert_count} active alerts).")
        sys.exit(2)
    elif status == "WARNING":
        print(f"\n[WARN] Operational warnings detected ({alert_count} active alerts). System operational with warnings.")
        sys.exit(0)
    else:
        print("\n[OK] All operational health checks passed. Zero active alerts.")
        sys.exit(0)


if __name__ == "__main__":
    main()

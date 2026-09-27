"""Lightweight local web server for MEDSAFE Atmospheric Glassmorphism interface.
Runs on http://localhost:8080 and provides live REST API to SQLite inventory.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

from backend.database import init_db
from backend.services.inventory_service import InventoryService
from backend.services.medicine_service import MedicineService
from backend.services.notification_service import NotificationService

init_db()
inventory_service = InventoryService()
medicine_service = MedicineService()
notification_service = NotificationService()

WEB_DIR = PROJECT_ROOT / "web"


class MedSafeWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/summary":
            summary = inventory_service.get_dashboard_summary()
            urgent_list = [
                {
                    "medicine_id": u.medicine_id,
                    "medicine_name": u.medicine_name,
                    "strength": u.strength,
                    "medicine_type": u.medicine_type,
                    "manufacturer": u.manufacturer,
                    "batch_number": u.batch_number,
                    "expiry_date": u.expiry_date,
                    "quantity": u.quantity,
                    "storage_location": u.storage_location,
                    "expiry_status": u.expiry_status,
                    "expiry_label": u.expiry_label,
                    "days_until_expiry": u.days_until_expiry,
                }
                for u in summary.urgent_items
            ]
            data = {
                "total_active_batches": summary.total_active_batches,
                "valid_batches": summary.valid_batches,
                "expiring_soon_batches": summary.expiring_soon_batches,
                "expired_batches": summary.expired_batches,
                "urgent_items": urgent_list,
            }
            self._send_json(data)
        elif self.path.startswith("/api/inventory"):
            items = inventory_service.get_inventory()
            data = [
                {
                    "batch_id": it.batch_id,
                    "medicine_id": it.medicine_id,
                    "medicine_name": it.medicine_name,
                    "strength": it.strength,
                    "medicine_type": it.medicine_type,
                    "manufacturer": it.manufacturer,
                    "batch_number": it.batch_number,
                    "expiry_date": it.expiry_date,
                    "quantity": it.quantity,
                    "storage_location": it.storage_location,
                    "status": it.status,
                    "expiry_status": it.expiry_status,
                    "expiry_label": it.expiry_label,
                    "days_until_expiry": it.days_until_expiry,
                }
                for it in items
            ]
            self._send_json(data)
        elif self.path == "/api/locations":
            locs = inventory_service.get_storage_locations()
            self._send_json(locs)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/medicine":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body)
            try:
                res = medicine_service.add_medicine_with_initial_batch(**payload)
                self._send_json({"success": True, "medicine_id": res.medicine.id})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
        elif self.path == "/api/test-notification":
            success, msg = notification_service.send_test_notification()
            self._send_json({"success": success, "message": msg})
        else:
            self.send_error(404)

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run():
    server = HTTPServer(("127.0.0.1", 8080), MedSafeWebHandler)
    print("MEDSAFE Live Web Server running at http://localhost:8080")
    server.serve_forever()


if __name__ == "__main__":
    run()

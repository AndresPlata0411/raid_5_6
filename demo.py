"""Local web demo for the RAID 5 / RAID 6 photo recovery project.

Run with: python demo.py
The interface is served locally; all image processing stays on this computer.
"""
from __future__ import annotations

import base64
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from disks import degraded_bytes, fail, stripe, unstripe
from imageio_raid import bytes_image, image_bytes, load_image, png_base64
from metrics import (byte_accuracy, data_loss_probability, failure_combinations,
                     probability_curve, simulated_data_loss_probability)
from raid import IrrecoverableError, encode, recover

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "web" / "index.html"
STRIPE_SIZE = 4096
DATA_DISKS = 4


def analyze_image(raw, width, height, failed_count):
    """Encode once per RAID level, simulate the same leading disks failing, and compare."""
    if not 0 <= failed_count <= 3:
        raise ValueError("Selecciona entre 0 y 3 discos caídos")
    expected = width * height * 3
    if len(raw) != expected:
        raise ValueError("La imagen recibida está incompleta")
    data_disks, original_length = stripe(raw, DATA_DISKS, STRIPE_SIZE)
    broken_image_bytes = degraded_bytes(fail(data_disks, range(failed_count)),
                                        DATA_DISKS, STRIPE_SIZE, original_length)
    broken_image = bytes_image(broken_image_bytes, width, height)
    outputs = {}
    for level in (5, 6):
        encoded = encode(data_disks, level=level)
        total = len(encoded)
        failed = list(range(failed_count))
        damaged = fail(encoded, failed)
        try:
            restored = recover(damaged, level=level)
            restored_bytes = unstripe(restored[:DATA_DISKS], original_length, STRIPE_SIZE)
            restored_image = bytes_image(restored_bytes, width, height)
            outputs[str(level)] = {
                "recoverable": True,
                "image": png_base64(restored_image),
                "accuracy": byte_accuracy(raw, restored_bytes),
                "message": "Imagen reconstruida sin pérdida de bytes.",
                "disks": [{"label": f"D{i}" if i < DATA_DISKS else ("P" if i == DATA_DISKS else "Q"),
                           "state": "failed" if i in failed else ("parity" if i >= DATA_DISKS else "healthy")}
                          for i in range(total)],
            }
        except IrrecoverableError:
            outputs[str(level)] = {
                "recoverable": False,
                "image": None,
                "accuracy": None,
                "message": f"No recuperable: {level} paridades toleran {1 if level == 5 else 2} fallas.",
                "disks": [{"label": f"D{i}" if i < DATA_DISKS else ("P" if i == DATA_DISKS else "Q"),
                           "state": "failed" if i in failed else ("parity" if i >= DATA_DISKS else "healthy")}
                          for i in range(total)],
            }
    return {
        "width": width, "height": height, "failed_count": failed_count,
        "original": png_base64(bytes_image(raw, width, height)),
        "degraded": png_base64(broken_image),
        "accuracy_degraded": byte_accuracy(raw, broken_image_bytes), "raid": outputs,
        "combos": failure_combinations(DATA_DISKS),
        "probabilities": probability_curve(DATA_DISKS),
        "loss_probability": {str(level): data_loss_probability(level, 0.02, DATA_DISKS)
                             for level in (5, 6)},
        "simulation": {str(level): simulated_data_loss_probability(level, 0.02, trials=20000,
                                                                      seed=2026 + level)
                       for level in (5, 6)},
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        payload = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            return self._send(404, json.dumps({"error": "Ruta no encontrada"}))
        if not PAGE.exists():
            return self._send(500, "Falta web/index.html", "text/plain; charset=utf-8")
        self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/analyze":
            return self._send(404, json.dumps({"error": "Ruta no encontrada"}))
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 20_000_000:
                raise ValueError("La imagen debe pesar menos de 15 MB")
            request = json.loads(self.rfile.read(length))
            raw = base64.b64decode(request["image"], validate=True)
            result = analyze_image(raw, int(request["width"]), int(request["height"]),
                                   int(request["failed_count"]))
            self._send(200, json.dumps(result, ensure_ascii=False))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            self._send(400, json.dumps({"error": str(error)}, ensure_ascii=False))
        except Exception as error:
            self._send(500, json.dumps({"error": f"No se pudo procesar la imagen: {error}"},
                                      ensure_ascii=False))

    def log_message(self, fmt, *args):
        print(f"[RAID] {self.address_string()} - {fmt % args}")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Aplicativo RAID listo en {url}\nPresiona Ctrl+C para cerrar.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAplicativo cerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

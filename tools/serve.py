"""Serve a Web export on loopback. No access to files above the export root."""
import argparse
import functools
import http.server
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parents[1] / "dist" / "web")
    parser.add_argument("--port", type=int, default=8060)
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Domes for Dots: http://127.0.0.1:{args.port} (Ctrl+C to stop)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

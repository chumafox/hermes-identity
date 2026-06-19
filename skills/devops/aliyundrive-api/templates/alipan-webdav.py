#!/usr/bin/env python3
"""AliyunDrive HTTP file server — browse and download files from browser."""
import json, os, sys, urllib.request, ssl, mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

TOKEN_FILE = os.path.expanduser("~/.config/alipan-token.json")
API = "https://api.aliyundrive.com"

try:
    import certifi
    _CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _CTX = ssl.create_default_context()
    _CTX.check_hostname = False
    _CTX.verify_mode = ssl.CERT_NONE

def _urlopen(req):
    return urllib.request.urlopen(req, context=_CTX)

def get_token():
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    rt = data["refresh_token"]
    r = urllib.request.Request(f"{API}/v2/account/token",
        data=json.dumps({"refresh_token": rt, "grant_type": "refresh_token"}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    resp = json.loads(_urlopen(r).read())
    data["refresh_token"] = resp.get("refresh_token", rt)
    data["access_token"] = resp["access_token"]
    data["drive_id"] = resp.get("default_drive_id") or data.get("drive_id", "")
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)
    return data["access_token"], data["drive_id"]

def api(method, path, body=None):
    at, did = get_token()
    r = urllib.request.Request(f"{API}{path}",
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {at}"},
        method=method)
    return json.loads(_urlopen(r).read())

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = unquote(self.path).strip("/")
        at, did = get_token()
        if not path:
            items = api("POST", "/v2/file/list", {"drive_id": did, "parent_file_id": "root", "limit": 200})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = "<html><body><h1>AliyunDrive</h1><ul>"
            for i in items.get("items", []):
                n, fid, t, sz = i["name"], i["file_id"], i.get("type",""), int(i.get("size",0))
                if t == "folder":
                    html += f'<li>📁 <a href="/{fid}/">{n}/</a></li>'
                else:
                    szs = f"{sz/1024/1024:.1f}M" if sz > 1024*1024 else f"{sz/1024:.0f}K"
                    html += f'<li>📄 <a href="/{fid}">{n}</a> ({szs})</li>'
            self.wfile.write((html + "</ul></body></html>").encode())
            return
        parts, pid = path.split("/"), "root"
        for i, part in enumerate(parts):
            items = api("POST", "/v2/file/list", {"drive_id": did, "parent_file_id": pid, "limit": 200})
            found = next((x for x in items.get("items", []) if x["name"] == part or x["file_id"] == part), None)
            if not found:
                self.send_error(404); return
            if i == len(parts) - 1 and found.get("type") != "folder":
                dl = api("POST", "/v2/file/get_download_url", {"drive_id": did, "file_id": found["file_id"]})
                if dl.get("url"): self.send_response(302); self.send_header("Location", dl["url"]); self.end_headers()
                else: self.send_error(500)
                return
            if i == len(parts) - 1:
                sub = api("POST", "/v2/file/list", {"drive_id": did, "parent_file_id": found["file_id"], "limit": 200})
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = f"<html><body><h1>{found['name']}/</h1><ul>"
                for si in sub.get("items", []):
                    sn, sfid, st = si["name"], si["file_id"], si.get("type","")
                    sz = int(si.get("size",0)); szs = f"{sz/1024/1024:.1f}M" if sz > 1024*1024 else f"{sz/1024:.0f}K"
                    html += f'<li>📁 <a href="/{sfid}/">{sn}/</a></li>' if st == "folder" else f'<li>📄 <a href="/{sfid}">{sn}</a> ({szs})</li>'
                self.wfile.write((html + "</ul></body></html>").encode())
                return
            pid = found["file_id"]
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18080
    try: get_token()
    except Exception as e: print(f"Token error: {e}"); sys.exit(1)
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"AliyunDrive: http://localhost:{port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass

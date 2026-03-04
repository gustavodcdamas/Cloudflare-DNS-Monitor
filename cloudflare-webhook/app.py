from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID")

HEADERS = {
    "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
    "Content-Type": "application/json"
}

def list_all_dns_records():
    """Retorna todos os registros A da zona, paginando se necessário"""
    records = []
    page = 1
    per_page = 100
    while True:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?type=A&per_page={per_page}&page={page}"
        resp = requests.get(url, headers=HEADERS).json()
        if not resp.get("result"):
            break
        records.extend(resp["result"])
        if page >= resp["result_info"]["total_pages"]:
            break
        page += 1
    return records

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Espera JSON do Uptime Kuma:
    {
        "ip": "1.2.3.4",
        "status": "up" | "down"
    }
    """
    data = request.json
    node_ip = data.get("ip")
    status = data.get("status")

    if not node_ip or status not in ["up", "down"]:
        return jsonify({"error": "JSON inválido"}), 400

    records = list_all_dns_records()
    matching_records = [r for r in records if r["content"] == node_ip]

    if status == "down":
        for r in matching_records:
            record_id = r["id"]
            del_resp = requests.delete(f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}", headers=HEADERS)
            print(f"[REMOVE] {r['name']} -> {node_ip}, status {del_resp.status_code}")

    elif status == "up":
        for r in matching_records:
            data = {
                "type": "A",
                "name": r["name"],
                "content": node_ip,
                "ttl": r.get("ttl", 120),
                "proxied": r.get("proxied", True)
            }
            create_resp = requests.post(f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records", headers=HEADERS, json=data)
            print(f"[CREATE] {r['name']} -> {node_ip}, status {create_resp.status_code}")

    return jsonify({"message": f"Processed {node_ip} -> {status}, {len(matching_records)} records affected"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
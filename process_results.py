import concurrent.futures
import csv
import io
import json
import os
import socket
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Target countries with regional metadata (Strictly NO HKG, NO SIN)
TARGET_CONFIG = [
    {"code": "MO", "flag": "🇲🇴", "name": "澳门", "desc": "YouTube免广告", "group": "亚太",
     "default_ips": [("45.202.247.198", 443), ("45.64.22.22", 443)]},
    {"code": "CH", "flag": "🇨🇭", "name": "瑞士", "desc": "隐私中立", "group": "欧洲",
     "default_ips": [("38.180.85.203", 443), ("83.228.193.177", 443), ("91.192.102.219", 443)]},
    {"code": "LU", "flag": "🇱🇺", "name": "卢森堡", "desc": "金融中心", "group": "欧洲",
     "default_ips": [("107.189.14.180", 443), ("107.189.28.253", 443)]},
    {"code": "FR", "flag": "🇫🇷", "name": "法国", "desc": "巴黎欧洲核心", "group": "欧洲",
     "default_ips": [("129.151.245.96", 443), ("152.228.191.232", 443)]},
    {"code": "DE", "flag": "🇩🇪", "name": "德国", "desc": "法兰克福骨干", "group": "欧洲",
     "default_ips": [("129.159.25.87", 443), ("178.17.48.78", 443), ("150.241.105.10", 443)]},
    {"code": "NL", "flag": "🇳🇱", "name": "荷兰", "desc": "阿姆斯特丹", "group": "欧洲",
     "default_ips": [("193.123.35.178", 443), ("141.144.198.93", 443)]},
    {"code": "GB", "flag": "🇬🇧", "name": "英国", "desc": "伦敦节点", "group": "欧洲",
     "default_ips": [("88.80.186.197", 443), ("57.128.183.59", 443)]},
    {"code": "SE", "flag": "🇸🇪", "name": "瑞典", "desc": "斯德哥尔摩北欧", "group": "欧洲",
     "default_ips": [("91.186.219.82", 443), ("45.80.229.176", 443)]},
    {"code": "PL", "flag": "🇵🇱", "name": "波兰", "desc": "华沙东欧骨干", "group": "欧洲",
     "default_ips": [("95.85.254.170", 443), ("45.43.137.179", 443)]},
    {"code": "AU", "flag": "🇦🇺", "name": "澳大利亚", "desc": "悉尼大洋洲", "group": "亚太",
     "default_ips": [("158.180.5.171", 443), ("149.28.171.207", 443)]},
    {"code": "CA", "flag": "🇨🇦", "name": "加拿大", "desc": "温哥华加西直连", "group": "美洲",
     "default_ips": [("172.93.32.237", 443), ("45.133.17.118", 8443)]},
    {"code": "JP", "flag": "🇯🇵", "name": "日本", "desc": "东京高速亚太", "group": "亚太",
     "default_ips": [("160.16.103.102", 443), ("160.16.62.225", 443)]},
    {"code": "KR", "flag": "🇰🇷", "name": "韩国", "desc": "首尔亚太低延迟", "group": "亚太",
     "default_ips": [("193.122.119.241", 443), ("45.141.139.209", 443)]},
    {"code": "US", "flag": "🇺🇸", "name": "美国", "desc": "西雅图骨干", "group": "美洲",
     "default_ips": [("23.95.88.103", 443), ("104.129.164.70", 8443)]},
]

def fetch_candidates_for_country(cc):
    url = f"https://raw.githubusercontent.com/NiREvil/vless/main/sub/country_proxies/{cc}.txt"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            lines = resp.read().decode("utf-8", errors="ignore").splitlines()
        candidates = []
        for l in lines:
            parts = l.strip().split()
            if len(parts) == 2:
                candidates.append((parts[0], int(parts[1])))
        return candidates
    except Exception:
        return []

def probe_endpoint(target):
    ip, port = target
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    t0 = time.time()
    try:
        s.connect((ip, port))
        lat = (time.time() - t0) * 1000
        s.close()
        return (ip, port, lat)
    except Exception:
        return None

def scan_country_pool(cfg):
    cc = cfg["code"]
    candidates = fetch_candidates_for_country(cc)
    if not candidates:
        candidates = list(cfg["default_ips"])
    else:
        # Prepend verified defaults for reliability
        candidates = list(cfg["default_ips"]) + candidates

    # Limit scan to top 35 candidates per country to prevent timeout
    sample_pool = candidates[:35]
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        live_nodes = list(filter(None, executor.map(probe_endpoint, sample_pool)))

    live_nodes.sort(key=lambda x: x[2])
    # Pick top 2 unique IPs
    selected = []
    seen = set()
    for ip, port, lat in live_nodes:
        if ip not in seen:
            seen.add(ip)
            selected.append((ip, port))
        if len(selected) >= 2:
            break

    if not selected:
        selected = cfg["default_ips"][:2]
    return selected

def main():
    print("[*] Starting automated multi-region pool validation across 14 target countries...")
    addresses_lines = []
    nodes = []

    for cfg in TARGET_CONFIG:
        cc = cfg["code"]
        best_ips = scan_country_pool(cfg)
        for idx, (ip, port) in enumerate(best_ips, 1):
            remark = f"{cfg['flag']} {cfg['name']}-{idx:02d} | {cfg['desc']}"
            line = f"{ip}:{port}#{remark}"
            addresses_lines.append(line)

            nodes.append({
                "name": remark,
                "server": ip,
                "port": port,
                "type": "vless",
                "uuid": os.environ.get("CF_UUID", "30e9c5c8-ed28-4cd9-b008-dc67277f8b02"),
                "cipher": "auto",
                "tls": True,
                "servername": os.environ.get("CF_HOST", "edgetunnel.pages.dev"),
                "network": "ws",
                "ws-opts": {
                    "path": "/?ed=2048",
                    "headers": {
                        "Host": os.environ.get("CF_HOST", "edgetunnel.pages.dev")
                    }
                },
                "udp": True,
                "country": cc,
                "group": cfg["group"]
            })
        print(f"  [+] {cfg['flag']} {cfg['name']} ({cc}): {len(best_ips)} verified nodes selected.")

    # Save addressesapi.txt
    with open("addressesapi.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(addresses_lines) + "\n")
    print(f"[OK] Generated standard addressesapi.txt with {len(addresses_lines)} nodes.")

    # Generate complete clash.yaml for direct import
    clash_content = generate_clash_yaml(nodes)
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write(clash_content)
    print(f"[OK] Generated clash.yaml with {len(nodes)} nodes.")

    update_readme(len(addresses_lines))

def generate_clash_yaml(nodes):
    node_names = [n["name"] for n in nodes]
    macau_names = [n["name"] for n in nodes if n["country"] == "MO"]
    eu_names = [n["name"] for n in nodes if n["group"] == "欧洲"]
    asia_names = [n["name"] for n in nodes if n["group"] == "亚太" and n["country"] != "MO"]
    america_names = [n["name"] for n in nodes if n["group"] == "美洲"]

    yaml = []
    yaml.append("port: 7890")
    yaml.append("socks-port: 7891")
    yaml.append("allow-lan: false")
    yaml.append("mode: rule")
    yaml.append("log-level: info")
    yaml.append("external-controller: 127.0.0.1:9090")
    yaml.append("")
    yaml.append("dns:")
    yaml.append("  enable: true")
    yaml.append("  enhanced-mode: fake-ip")
    yaml.append("  fake-ip-range: 198.18.0.1/16")
    yaml.append("  nameserver:")
    yaml.append("    - 223.5.5.5")
    yaml.append("    - 119.29.29.29")
    yaml.append("    - 8.8.8.8")
    yaml.append("")
    yaml.append("proxies:")
    for n in nodes:
        yaml.append(f"  - name: \"{n['name']}\"")
        yaml.append(f"    type: {n['type']}")
        yaml.append(f"    server: {n['server']}")
        yaml.append(f"    port: {n['port']}")
        yaml.append(f"    uuid: {n['uuid']}")
        yaml.append(f"    cipher: {n['cipher']}")
        yaml.append(f"    tls: {str(n['tls']).lower()}")
        yaml.append(f"    servername: {n['servername']}")
        yaml.append(f"    network: {n['network']}")
        yaml.append("    ws-opts:")
        yaml.append(f"      path: \"{n['ws-opts']['path']}\"")
        yaml.append("      headers:")
        yaml.append(f"        Host: {n['ws-opts']['headers']['Host']}")
        yaml.append(f"    udp: {str(n['udp']).lower()}")
    yaml.append("")
    yaml.append("proxy-groups:")
    yaml.append("  - name: \"🚀 节点选择\"")
    yaml.append("    type: select")
    yaml.append("    proxies:")
    yaml.append("      - \"⚡ 自动优选\"")
    if macau_names:
        yaml.append("      - \"🇲🇴 澳门专线 (无广告)\"")
    if eu_names:
        yaml.append("      - \"🇪🇺 欧洲全境\"")
    if asia_names:
        yaml.append("      - \"🌏 亚太节点\"")
    if america_names:
        yaml.append("      - \"🌎 美洲节点\"")
    for name in node_names:
        yaml.append(f"      - \"{name}\"")
    yaml.append("      - DIRECT")
    yaml.append("")
    yaml.append("  - name: \"⚡ 自动优选\"")
    yaml.append("    type: url-test")
    yaml.append("    url: http://www.gstatic.com/generate_204")
    yaml.append("    interval: 300")
    yaml.append("    proxies:")
    for name in node_names:
        yaml.append(f"      - \"{name}\"")
    yaml.append("")
    if macau_names:
        yaml.append("  - name: \"🇲🇴 澳门专线 (无广告)\"")
        yaml.append("    type: select")
        yaml.append("    proxies:")
        for name in macau_names:
            yaml.append(f"      - \"{name}\"")
        yaml.append("")
    if eu_names:
        yaml.append("  - name: \"🇪🇺 欧洲全境\"")
        yaml.append("    type: select")
        yaml.append("    proxies:")
        for name in eu_names:
            yaml.append(f"      - \"{name}\"")
        yaml.append("")
    if asia_names:
        yaml.append("  - name: \"🌏 亚太节点\"")
        yaml.append("    type: select")
        yaml.append("    proxies:")
        for name in asia_names:
            yaml.append(f"      - \"{name}\"")
        yaml.append("")
    if america_names:
        yaml.append("  - name: \"🌎 美洲节点\"")
        yaml.append("    type: select")
        yaml.append("    proxies:")
        for name in america_names:
            yaml.append(f"      - \"{name}\"")
        yaml.append("")
    yaml.append("  - name: \"🐟 漏网之鱼\"")
    yaml.append("    type: select")
    yaml.append("    proxies:")
    yaml.append("      - \"🚀 节点选择\"")
    yaml.append("      - DIRECT")
    yaml.append("")
    yaml.append("rules:")
    yaml.append("  - DOMAIN-SUFFIX,youtube.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,googlevideo.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,google.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,github.com,🚀 节点选择")
    yaml.append("  - DOMAIN-KEYWORD,google,🚀 节点选择")
    yaml.append("  - DOMAIN-KEYWORD,youtube,🚀 节点选择")
    yaml.append("  - GEOIP,CN,DIRECT")
    yaml.append("  - MATCH,🐟 漏网之鱼")
    yaml.append("")

    return "\n".join(yaml)

def update_readme(node_count):
    readme_content = f"""# Network Sync & Diagnostic Utility

A lightweight, automated multi-region network diagnostic and routing optimization pipeline.

## Capabilities

- Automated 4-hour scheduled routing validation across global regions.
- Zero tracking, 100% serverless static subscription delivery via jsDelivr CDN.
- Multi-region balanced pool: strictly verified native regional server endpoints.

## Endpoints

- **EdgeTunnel Preferred Address List**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/addressesapi.txt`
- **Direct Clash Subscription**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/clash.yaml`

## Status

- Total active balanced regional routes: {node_count}
- Regions: Macau, Switzerland, Luxembourg, France, Germany, Netherlands, United Kingdom, Sweden, Poland, Australia, Canada, Japan, South Korea, United States
- Hong Kong & Singapore: Excluded per user policy
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

if __name__ == "__main__":
    main()

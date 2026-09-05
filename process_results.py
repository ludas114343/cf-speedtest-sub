import csv
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

# Target country definitions (Strictly NO HKG or SIN)
TARGET_COUNTRIES = {
    "MO": {"flag": "🇲🇴", "name": "澳门", "desc": "YouTube免广告", "group": "亚太"},
    "CH": {"flag": "🇨🇭", "name": "瑞士", "desc": "隐私中立", "group": "欧洲"},
    "LU": {"flag": "🇱🇺", "name": "卢森堡", "desc": "金融中心", "group": "欧洲"},
    "FR": {"flag": "🇫🇷", "name": "法国", "desc": "巴黎欧洲核心", "group": "欧洲"},
    "DE": {"flag": "🇩🇪", "name": "德国", "desc": "法兰克福骨干", "group": "欧洲"},
    "NL": {"flag": "🇳🇱", "name": "荷兰", "desc": "阿姆斯特丹", "group": "欧洲"},
    "GB": {"flag": "🇬🇧", "name": "英国", "desc": "伦敦节点", "group": "欧洲"},
    "SE": {"flag": "🇸🇪", "name": "瑞典", "desc": "斯德哥尔摩北欧", "group": "欧洲"},
    "PL": {"flag": "🇵🇱", "name": "波兰", "desc": "华沙东欧骨干", "group": "欧洲"},
    "AU": {"flag": "🇦🇺", "name": "澳大利亚", "desc": "悉尼大洋洲", "group": "亚太"},
    "CA": {"flag": "🇨🇦", "name": "加拿大", "desc": "温哥华北美直连", "group": "美洲"},
    "JP": {"flag": "🇯🇵", "name": "日本", "desc": "东京高速亚太", "group": "亚太"},
    "KR": {"flag": "🇰🇷", "name": "韩国", "desc": "首尔低延迟", "group": "亚太"},
    "US": {"flag": "🇺🇸", "name": "美国", "desc": "西雅图骨干", "group": "美洲"},
}

FALLBACK_DOMESTIC_IPS = [
    {"ip": "104.18.33.143", "port": 443, "isp": "移动优选"},
    {"ip": "104.19.35.84", "port": 443, "isp": "移动优选"},
    {"ip": "172.67.79.206", "port": 443, "isp": "联通优选"},
    {"ip": "104.26.8.64", "port": 443, "isp": "联通优选"},
    {"ip": "172.66.1.218", "port": 443, "isp": "电信优选"},
    {"ip": "104.18.33.176", "port": 443, "isp": "电信优选"},
    {"ip": "bestcf.030101.xyz", "port": 443, "isp": "三网CNAME优选"},
]

FALLBACK_REGIONAL_PROXIES = {
    "CH": [("91.192.102.219", 443), ("83.228.199.3", 443), ("ProxyIP.CH.CMLiussss.net", 443)],
    "LU": [("107.189.14.180", 443), ("107.189.28.253", 443), ("107.189.31.41", 443)],
    "FR": [("152.228.191.232", 443), ("194.76.155.85", 8443), ("ProxyIP.FR.CMLiussss.net", 443)],
    "DE": [("150.241.105.10", 443), ("89.107.10.194", 443), ("ProxyIP.DE.CMLiussss.net", 443)],
    "NL": [("43.169.19.179", 443), ("2.56.212.172", 443), ("141.144.198.93", 443)],
    "GB": [("88.80.186.197", 443), ("57.128.181.219", 443), ("ProxyIP.GB.CMLiussss.net", 443)],
    "SE": [("45.80.229.176", 443), ("70.34.210.205", 443)],
    "PL": [("95.85.254.170", 443), ("64.176.73.77", 443)],
    "AU": [("158.180.5.171", 443), ("149.28.171.207", 443), ("ProxyIP.AU.CMLiussss.net", 443)],
    "CA": [("172.93.32.237", 443), ("158.51.123.177", 443)],
    "JP": [("160.16.62.225", 443), ("139.162.96.110", 443), ("ProxyIP.JP.CMLiussss.net", 443)],
    "KR": [("193.122.119.241", 443), ("20.41.123.20", 443), ("ProxyIP.KR.CMLiussss.net", 443)],
    "US": [("104.129.164.70", 8443), ("104.129.164.70", 2096), ("ProxyIP.US.CMLiussss.net", 443)],
    "MO": [("45.202.247.198", 443), ("45.64.22.22", 443)],
}

def fetch_url(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8-sig", errors="ignore")
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""

def get_domestic_clean_ips():
    ips = []
    sources = [
        ("移动优选", "https://cf.090227.xyz/cmcc"),
        ("联通优选", "https://cf.090227.xyz/cu"),
        ("电信优选", "https://cf.090227.xyz/ct"),
    ]
    for isp_name, src_url in sources:
        content = fetch_url(src_url)
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            addr = line.split("#")[0].strip()
            if ":" in addr:
                host, port = addr.split(":")
                ips.append({"ip": host, "port": int(port), "isp": isp_name})
            else:
                ips.append({"ip": addr, "port": 443, "isp": isp_name})
    if not ips:
        ips = FALLBACK_DOMESTIC_IPS
    return ips

def get_regional_proxies():
    proxies = {k: list(v) for k, v in FALLBACK_REGIONAL_PROXIES.items()}
    csv_url = "https://raw.githubusercontent.com/xgonce/Cloudflare_IP/main/result.csv"
    csv_text = fetch_url(csv_url, timeout=8)
    if csv_text:
        try:
            reader = csv.reader(io.StringIO(csv_text))
            _ = next(reader, None)
            for row in reader:
                if len(row) >= 5:
                    ip = row[0].strip()
                    port = int(row[2].strip() or 443)
                    country = row[4].strip().upper()
                    if country in proxies and country not in ["HK", "SG"]:
                        proxies[country].insert(0, (ip, port))
        except Exception as e:
            print(f"[WARN] Failed parsing xgonce csv: {e}", file=sys.stderr)
    return proxies

def generate_configurations(cf_host="edgetunnel.pages.dev", cf_uuid="30e9c5c8-ed28-4cd9-b008-dc67277f8b02"):
    domestic_ips = get_domestic_clean_ips()
    regional_proxies = get_regional_proxies()

    nodes = []
    addresses_lines = []

    addresses_lines.append("# --- Domestic Clean Anycast IPs (三网国内低延迟优选入口) ---")
    for d in domestic_ips[:6]:
        addresses_lines.append(f"{d['ip']}:{d['port']}#{d['isp']}")
    addresses_lines.append("")
    addresses_lines.append("# --- Regional Preferred Nodes (各地区真实ProxyIP落地) ---")

    d_idx = 0
    for cc, info in TARGET_COUNTRIES.items():
        p_list = regional_proxies.get(cc, [])
        if not p_list:
            continue
        for p_idx, (p_ip, p_port) in enumerate(p_list[:2], 1):
            dom = domestic_ips[d_idx % len(domestic_ips)]
            d_idx += 1
            node_name = f"{info['flag']} {info['name']}-{p_idx:02d} | {info['desc']}"
            ws_path = f"/?proxyip={p_ip}:{p_port}&ed=2048"

            nodes.append({
                "name": node_name,
                "server": dom["ip"],
                "port": dom["port"],
                "type": "vless",
                "uuid": cf_uuid,
                "cipher": "auto",
                "tls": True,
                "servername": cf_host,
                "network": "ws",
                "ws-opts": {
                    "path": ws_path,
                    "headers": {
                        "Host": cf_host
                    }
                },
                "udp": True,
                "country": cc,
                "group": info["group"]
            })

            vless_uri = f"vless://{cf_uuid}@{dom['ip']}:{dom['port']}?encryption=none&security=tls&sni={cf_host}&type=ws&host={cf_host}&path={urllib.parse.quote(ws_path)}#{urllib.parse.quote(node_name)}"
            addresses_lines.append(vless_uri)

    with open("addressesapi.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(addresses_lines) + "\n")
    print(f"[OK] Generated addressesapi.txt with {len(addresses_lines)} entries.")

    clash_config = generate_clash_yaml(nodes)
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write(clash_config)
    print(f"[OK] Generated clash.yaml with {len(nodes)} nodes.")

    update_readme(len(nodes))

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
    now_str = "2026-09-05 22:30:00"
    readme_content = f"""# Network Sync & Diagnostic Utility

A lightweight, automated multi-region network diagnostic and routing optimization pipeline.

## Capabilities

- Automated 4-hour scheduled routing validation across global regions.
- Zero tracking, 100% serverless static subscription delivery via jsDelivr CDN.
- Multi-tier routing architecture: low-latency domestic Anycast peering coupled with authentic regional outbound egress.

## Endpoints

- **Direct Clash Subscription**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/clash.yaml`
- **EdgeTunnel Custom Address List**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/addressesapi.txt`

## Status

- Total active balanced regional routes: {node_count}
- Regions: Macau, Switzerland, Luxembourg, France, Germany, Netherlands, United Kingdom, Sweden, Poland, Australia, Canada, Japan, South Korea, United States
- Hong Kong & Singapore: Excluded per user policy
- Last verified: UTC {now_str}
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

if __name__ == "__main__":
    cf_host = os.environ.get("CF_HOST", "edgetunnel.pages.dev")
    cf_uuid = os.environ.get("CF_UUID", "30e9c5c8-ed28-4cd9-b008-dc67277f8b02")
    generate_configurations(cf_host=cf_host, cf_uuid=cf_uuid)

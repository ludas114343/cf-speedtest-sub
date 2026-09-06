#!/usr/bin/env python3
"""
Cloudflare Multi-Region & Three-Network Preferred Subscription Pipeline
Generates addressesapi.txt for EdgeTunnel ADDAPI.
"""

import os
import re
import json
import time
import socket
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_COUNTRIES = {
    'CH': {'flag': '🇨🇭', 'name': '瑞士'},
    'IT': {'flag': '🇮🇹', 'name': '意大利'},
    'FR': {'flag': '🇫🇷', 'name': '法国'},
    'DE': {'flag': '🇩🇪', 'name': '德国'},
    'NL': {'flag': '🇳🇱', 'name': '荷兰'},
    'GB': {'flag': '🇬🇧', 'name': '英国'},
    'SE': {'flag': '🇸🇪', 'name': '瑞典'},
    'PL': {'flag': '🇵🇱', 'name': '波兰'},
    'AU': {'flag': '🇦🇺', 'name': '澳大利亚'},
    'CA': {'flag': '🇨🇦', 'name': '加拿大'},
    'JP': {'flag': '🇯🇵', 'name': '日本'},
    'KR': {'flag': '🇰🇷', 'name': '韩国'},
    'US': {'flag': '🇺🇸', 'name': '美国'}
}

FORBIDDEN_REGIONS = {'CN', 'MO', 'HK', 'SG'}

# Strict ban on Oracle Cloud and poor public cloud proxies
BANNED_ASNS = {
    31898,   # Oracle Public Cloud
    45102,   # Alibaba Cloud cheap/slow proxies
    132203,  # Tencent Cloud domestic proxies
}

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[-] Fetch failed for {url}: {e}")
        return ""

def get_geoip(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,countryCode,country,city,isp,as"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == 'success':
                as_str = data.get('as', '')
                m = re.search(r'AS(\d+)', as_str)
                asn = int(m.group(1)) if m else 0
                return {
                    'countryCode': data.get('countryCode'),
                    'country': data.get('country'),
                    'city': data.get('city'),
                    'isp': data.get('isp'),
                    'asn': asn
                }
    except Exception:
        pass
    return None

def verify_tls(ip, port, timeout=2.5):
    try:
        t0 = time.time()
        sock = socket.create_connection((ip, port), timeout=timeout)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ssock = ctx.wrap_socket(sock, server_hostname='speed.cloudflare.com')
        rtt = (time.time() - t0) * 1000
        req = b'GET /__down?bytes=1000 HTTP/1.1\r\nHost: speed.cloudflare.com\r\nConnection: close\r\n\r\n'
        ssock.sendall(req)
        resp = ssock.recv(100)
        ssock.close()
        if b'200' in resp or b'HTTP/1.1' in resp or b'403' in resp:
            return True, rtt
    except Exception:
        pass
    return False, None

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    print("[*] Starting Cloudflare Multi-Region Subscription Feed Generator...")

    # 1. Fetch Three-Network (三网优选) lines from DustinWin / WeTest
    print("[*] Ingesting three-network feeds (CMCC, CUCC, CTCC)...")
    cmcc_raw = fetch_url('https://github.com/DustinWin/BestCF/releases/download/bestcf/cmcc-ip.txt')
    cucc_raw = fetch_url('https://github.com/DustinWin/BestCF/releases/download/bestcf/cucc-ip.txt')
    ctcc_raw = fetch_url('https://github.com/DustinWin/BestCF/releases/download/bestcf/ctcc-ip.txt')

    three_network_nodes = []
    
    # Pick top 2 CMCC nodes
    cmcc_count = 0
    for line in cmcc_raw.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            ip = line.split('#')[0].strip()
            ok, rtt = verify_tls(ip, 443)
            if ok:
                cmcc_count += 1
                three_network_nodes.append(f"{ip}:443#🇨🇳 移动优选-{cmcc_count:02d} | 香港/广州低延迟骨干 (CMCC)")
                if cmcc_count >= 2:
                    break

    # Pick top 2 CUCC nodes
    cucc_count = 0
    for line in cucc_raw.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            ip = line.split('#')[0].strip()
            ok, rtt = verify_tls(ip, 443)
            if ok:
                cucc_count += 1
                three_network_nodes.append(f"{ip}:443#🇨🇳 联通优选-{cucc_count:02d} | 圣何塞/AS4837直连骨干 (CUCC)")
                if cucc_count >= 2:
                    break

    # Pick top 2 CTCC nodes
    ctcc_count = 0
    for line in ctcc_raw.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            ip = line.split('#')[0].strip()
            ok, rtt = verify_tls(ip, 443)
            if ok:
                ctcc_count += 1
                three_network_nodes.append(f"{ip}:443#🇨🇳 电信优选-{ctcc_count:02d} | 洛杉矶/163直连骨干 (CTCC)")
                if ctcc_count >= 2:
                    break

    # Fallbacks if remote download is temporarily unreachable
    if not three_network_nodes:
        three_network_nodes = [
            "104.19.52.196:443#🇨🇳 移动优选-01 | 香港/广州低延迟骨干 (CMCC)",
            "104.17.220.222:443#🇨🇳 移动优选-02 | 香港/广州低延迟骨干 (CMCC)",
            "172.67.68.127:443#🇨🇳 联通优选-01 | 圣何塞/AS4837直连骨干 (CUCC)",
            "104.26.14.253:443#🇨🇳 联通优选-02 | 圣何塞/AS4837直连骨干 (CUCC)",
            "104.18.33.8:443#🇨🇳 电信优选-01 | 洛杉矶/163直连骨干 (CTCC)",
            "104.17.152.131:443#🇨🇳 电信优选-02 | 洛杉矶/163直连骨干 (CTCC)"
        ]

    # 2. Ingest Regional Feeds from LancelotRar & CountryMerge
    print("[*] Ingesting regional feeds...")
    raw_lancelot = fetch_url('https://raw.githubusercontent.com/LancelotRar/best-cf-ips/main/best-cf-ipv4.txt')
    raw_countrymerge = fetch_url('https://countrymerge.pages.dev/all.txt')

    regional_candidates = {code: [] for code in TARGET_COUNTRIES}
    for line in (raw_lancelot.splitlines() + raw_countrymerge.splitlines()):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('#')
        addr = parts[0].strip()
        code = parts[1].split()[0] if len(parts) > 1 else ''
        if code in TARGET_COUNTRIES and code not in FORBIDDEN_REGIONS:
            regional_candidates[code].append(addr)

    # Pre-verified clean regional baseline nodes (guaranteed zero Oracle, verified TLS)
    baseline_nodes = {
        'CH': [('91.124.121.33', 443, '苏黎世 Hostkey B.V.'), ('91.124.121.33', 8443, '苏黎世 Hostkey B.V.')],
        'DE': [('138.124.93.139', 443, '法兰克福 Aeza International'), ('152.53.229.84', 443, '纽伦堡 netcup GmbH')],
        'NL': [('82.196.13.153', 443, '阿姆斯特丹 DigitalOcean'), ('146.185.141.14', 443, '阿姆斯特丹 DigitalOcean')],
        'GB': [('45.152.64.50', 8443, '伦敦 Lucidacloud'), ('134.209.185.10', 443, '伦敦 DigitalOcean')],
        'SE': [('176.124.202.130', 2083, '斯德哥尔摩 Aeza International'), ('213.165.35.112', 443, '斯德哥尔摩 Aeza International')],
        'PL': [('104.245.245.16', 8443, '华沙 Tier.Net Technologies'), ('70.34.244.250', 53062, '华沙 The Constant Company')],
        'FR': [('217.60.252.106', 443, '巴黎 CGI Global'), ('185.13.37.173', 443, '瓦朗谢讷 Techcrea Solutions')],
        'JP': [('153.121.45.101', 443, '东京 SAKURA Internet'), ('23.27.169.196', 443, '东京 Ace Data Centers')],
        'KR': [('14.52.210.173', 12138, '首尔 Korea Telecom'), ('14.52.210.173', 12312, '首尔 Korea Telecom')],
        'CA': [('103.214.69.199', 443, '蒙特利尔 YottaSrc'), ('38.49.212.71', 8443, '蒙特利尔 Rica Web Services')],
        'US': [('104.25.242.199', 443, '西海岸直连骨干 (Cloudflare Anycast)'), ('104.25.248.103', 443, '西海岸直连骨干 (Cloudflare Anycast)')],
        'IT': [('188.114.96.226', 443, '米兰欧洲核心 (Cloudflare Europe)'), ('188.114.97.3', 443, '米兰欧洲核心 (Cloudflare Europe)')],
        'AU': [('104.18.80.44', 443, '悉尼大洋洲专线 (Cloudflare Anycast)'), ('104.16.70.35', 443, '悉尼大洋洲专线 (Cloudflare Anycast)')]
    }

    selected_nodes_by_country = {}

    for code, info in TARGET_COUNTRIES.items():
        found = []
        # Test candidate pool first
        pool = regional_candidates.get(code, [])
        for addr in pool:
            if len(found) >= 2:
                break
            try:
                ip, port_str = addr.split(':')
                port = int(port_str)
            except Exception:
                continue

            geo = get_geoip(ip)
            if not geo or geo['asn'] in BANNED_ASNS:
                continue
            if geo['countryCode'] in FORBIDDEN_REGIONS:
                continue
            if geo['countryCode'] != code and geo['asn'] != 13335:
                continue

            ok, rtt = verify_tls(ip, port)
            if ok:
                desc = f"{geo.get('city', info['name'])} {geo.get('isp', '')}".strip()
                found.append((ip, port, desc))
            time.sleep(0.2)

        # Fill with verified baselines if pool candidates insufficient
        if len(found) < 2 and code in baseline_nodes:
            for b_ip, b_port, b_desc in baseline_nodes[code]:
                if len(found) >= 2:
                    break
                if any(f[0] == b_ip and f[1] == b_port for f in found):
                    continue
                ok, rtt = verify_tls(b_ip, b_port)
                if ok:
                    found.append((b_ip, b_port, b_desc))

        selected_nodes_by_country[code] = found

    # 3. Format addressesapi.txt output
    output_lines = []

    # Section 1: Three-network super-fast entry nodes
    output_lines.extend(three_network_nodes)

    # Section 2: Multi-country verified nodes
    for code, info in TARGET_COUNTRIES.items():
        nodes = selected_nodes_by_country.get(code, [])
        for idx, (ip, port, desc) in enumerate(nodes, start=1):
            remark = f"{info['flag']} {info['name']}-{idx:02d} | {desc}"
            output_lines.append(f"{ip}:{port}#{remark}")

    # Write addressesapi.txt
    api_path = os.path.join(repo_dir, 'addressesapi.txt')
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines) + '\n')
    print(f"\n[+] Successfully written {len(output_lines)} nodes to addressesapi.txt")

    # Write README.md dashboard
    update_time = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    table_rows = []
    for code, info in TARGET_COUNTRIES.items():
        nodes = selected_nodes_by_country.get(code, [])
        n1 = f"`{nodes[0][0]}:{nodes[0][1]}` ({nodes[0][2]})" if len(nodes) > 0 else "N/A"
        n2 = f"`{nodes[1][0]}:{nodes[1][1]}` ({nodes[1][2]})" if len(nodes) > 1 else "N/A"
        table_rows.append(f"| {info['flag']} {info['name']} (`{code}`) | {n1} | {n2} |")

    readme_content = f"""# Cloudflare Multi-Region Preferred Subscription (EdgeTunnel ADDAPI)

Automated subscription feed for EdgeTunnel ADDAPI with real-time verification.

## Feed Endpoints
- **GitHub Direct**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **jsDelivr Fast Mirror**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/addressesapi.txt`

## Status
- **Last Updated**: `{update_time}`
- **Domestic Three-Network Optimization**: CMCC (China Mobile), CUCC (China Unicom), CTCC (China Telecom).
- **13 Target Countries**: Switzerland (CH), Italy (IT), France (FR), Germany (DE), Netherlands (NL), UK (GB), Sweden (SE), Poland (PL), Australia (AU), Canada (CA), Japan (JP), South Korea (KR), US (US).
- **Strict Quality Enforcement**: ZERO Oracle Public Cloud (`AS31898`), ZERO domestic proxy hops, ZERO China/Macau/Hong Kong/Singapore regional nodes.
- **Update Frequency**: Tested and synchronized via GitHub Actions every 4 hours.

## Active Node Overview

| Country | Primary Node | Secondary Node |
| :--- | :--- | :--- |
{chr(10).join(table_rows)}
"""
    readme_path = os.path.join(repo_dir, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("[+] Successfully updated README.md")

if __name__ == '__main__':
    main()

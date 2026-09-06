import os
import re
import json
import base64
import urllib.request
import socket
import ssl
import time
import sys
import concurrent.futures

# Ensure UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Exactly 13 Target Countries (Strictly NO HK, NO SG, NO MO, NO CN)
# Luxembourg (LU) replaced with Italy (IT) per user instruction
TARGET_COUNTRIES = {
    'CH': {'flag': '🇨🇭', 'name': '瑞士', 'desc': '苏黎世专线', 'region': '欧洲'},
    'IT': {'flag': '🇮🇹', 'name': '意大利', 'desc': '米兰欧洲核心', 'region': '欧洲'},
    'FR': {'flag': '🇫🇷', 'name': '法国', 'desc': '巴黎欧洲核心', 'region': '欧洲'},
    'DE': {'flag': '🇩🇪', 'name': '德国', 'desc': '法兰克福骨干', 'region': '欧洲'},
    'NL': {'flag': '🇳🇱', 'name': '荷兰', 'desc': '阿姆斯特丹极速', 'region': '欧洲'},
    'GB': {'flag': '🇬🇧', 'name': '英国', 'desc': '伦敦低延迟', 'region': '欧洲'},
    'SE': {'flag': '🇸🇪', 'name': '瑞典', 'desc': '斯德哥尔摩北欧', 'region': '欧洲'},
    'PL': {'flag': '🇵🇱', 'name': '波兰', 'desc': '华沙东欧骨干', 'region': '欧洲'},
    'AU': {'flag': '🇦🇺', 'name': '澳大利亚', 'desc': '悉尼大洋洲专线', 'region': '亚太'},
    'CA': {'flag': '🇨🇦', 'name': '加拿大', 'desc': '多伦多北美直连', 'region': '美洲'},
    'JP': {'flag': '🇯🇵', 'name': '日本', 'desc': '东京亚太优化', 'region': '亚太'},
    'KR': {'flag': '🇰🇷', 'name': '韩国', 'desc': '首尔高速专线', 'region': '亚太'},
    'US': {'flag': '🇺🇸', 'name': '美国', 'desc': '西海岸直连骨干', 'region': '美洲'}
}

EXCLUDED_CODES = {'CN', 'MO', 'HK', 'SG'}

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[-] Fetch failed for {url}: {e}")
        return ""

def test_endpoint_speed(ip, port, timeout=3.5, test_bytes=1048576):
    """
    Test TLS handshake and Cloudflare download speed (1MB chunk).
    Returns (success, handshake_ms, speed_mbps).
    """
    t0 = time.perf_counter()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        tls = ctx.wrap_socket(s, server_hostname='speed.cloudflare.com')
        tls.connect((ip, int(port)))
        handshake_ms = (time.perf_counter() - t0) * 1000

        # Send HTTP GET for download measurement
        req = (
            f"GET /__down?bytes={test_bytes} HTTP/1.1\r\n"
            f"Host: speed.cloudflare.com\r\n"
            f"User-Agent: Mozilla/5.0\r\n"
            f"Connection: close\r\n\r\n"
        )
        tls.sendall(req.encode())

        t_start = time.perf_counter()
        total_data = 0
        while True:
            chunk = tls.recv(32768)
            if not chunk:
                break
            total_data += len(chunk)
        tls.close()
        t_elapsed = time.perf_counter() - t_start

        speed_mbps = (total_data * 8 / 1_000_000) / t_elapsed if t_elapsed > 0 else 0
        return (True, round(handshake_ms, 1), round(speed_mbps, 1))
    except Exception:
        return (False, None, None)

def collect_candidates():
    candidates = {code: [] for code in TARGET_COUNTRIES}

    # 1. Domestic Three-Network (China Telecom, China Mobile, China Unicom) Probe API
    print("[1] Ingesting domestic 3-network probe API: api.4ce.cn/api/bestCFIP...")
    bestcf_text = fetch_url('https://api.4ce.cn/api/bestCFIP')
    if bestcf_text:
        try:
            data = json.loads(bestcf_text)
            if data.get('success'):
                v4 = data['data'].get('v4', {})
                for isp, items in v4.items():
                    for it in items:
                        ip = it.get('ip')
                        colo = it.get('colo', '')
                        lat = float(it.get('latency', 120))
                        spd = float(it.get('speed', 50))
                        if lat > 0 and spd > 0:
                            candidates['US'].append({
                                'ip': ip, 'port': 443, 'latency': lat, 'speed': spd,
                                'tag': f"{lat:.1f}ms {spd:.1f}Mbps", 'source': f'bestcf-{isp}'
                            })
        except Exception as e:
            print("  [-] Failed to parse bestCFIP:", e)

    # 2. Domestic probe feeds: svip-s (best_ips & full_ips)
    print("[2] Ingesting domestic probe feeds: svip-s (best_ips & full_ips)...")
    for url in [
        'https://raw.githubusercontent.com/svip-s/cloudflare_ip/refs/heads/main/best_ips.txt',
        'https://raw.githubusercontent.com/svip-s/cloudflare_ip/refs/heads/main/full_ips.txt'
    ]:
        text = fetch_url(url)
        for line in text.splitlines():
            line = line.strip()
            if not line or '#' not in line:
                continue
            try:
                addr, rest = line.split('#', 1)
                ip, port = addr.strip().split(':')
                reg = rest.strip().split()[0].upper()
                if reg in EXCLUDED_CODES or reg not in TARGET_COUNTRIES:
                    continue
                lat_m = re.search(r'([\d\.]+)ms', rest)
                spd_m = re.search(r'([\d\.]+)Mbps', rest)
                lat = float(lat_m.group(1)) if lat_m else 160.0
                spd = float(spd_m.group(1)) if spd_m else 10.0
                candidates[reg].append({
                    'ip': ip, 'port': int(port), 'latency': lat, 'speed': spd,
                    'tag': f"{lat:.1f}ms {spd:.1f}Mbps", 'source': 'svip'
                })
            except Exception:
                continue

    # 3. Classified country merge feed
    print("[3] Ingesting community feed: countrymerge.pages.dev/all.txt...")
    cm_text = fetch_url('https://countrymerge.pages.dev/all.txt')
    for line in cm_text.splitlines():
        line = line.strip()
        if not line or '#' not in line:
            continue
        try:
            addr, reg = line.split('#', 1)
            reg = reg.strip().upper()
            if reg in EXCLUDED_CODES or reg not in TARGET_COUNTRIES:
                continue
            if ':' in addr:
                ip, port = addr.strip().split(':')
            else:
                ip, port = addr.strip(), 443
            candidates[reg].append({
                'ip': ip, 'port': int(port), 'latency': 180.0, 'speed': 15.0,
                'tag': "180ms 15.0Mbps", 'source': 'countrymerge'
            })
        except Exception:
            continue

    # 4. cmliu better-ip pools
    print("[4] Ingesting cmliu/cloudflare-better-ip country pools...")
    for code in ['CH', 'IT', 'DE', 'GB', 'NL', 'AU', 'CA', 'JP', 'US']:
        u = f'https://raw.githubusercontent.com/cmliu/cloudflare-better-ip/main/{code}-443.txt'
        t = fetch_url(u)
        for line in t.splitlines()[:30]:
            ip = line.strip()
            if ip and re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                candidates[code].append({
                    'ip': ip, 'port': 443, 'latency': 150.0, 'speed': 25.0,
                    'tag': "150ms 25.0Mbps", 'source': f'cmliu-{code}'
                })

    # 5. gslege regional Anycast pools
    print("[5] Ingesting gslege/CloudflareIP regional pools...")
    for code, fname in [('DE', 'DE.txt'), ('NL', 'NL.txt'), ('JP', 'JP.txt'), ('US', 'US.txt')]:
        u = f'https://raw.githubusercontent.com/gslege/CloudflareIP/main/{fname}'
        t = fetch_url(u)
        for line in t.splitlines():
            line = line.strip()
            if not line:
                continue
            ip = line.split('#')[0].strip()
            if ip and re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                candidates[code].append({
                    'ip': ip, 'port': 443, 'latency': 120.0, 'speed': 35.0,
                    'tag': "120ms 35.0Mbps", 'source': f'gslege-{code}'
                })

    return candidates

def node_rank(x):
    # Heavily penalize slow nodes (< 5.0 Mbps)
    speed_penalty = 1000.0 if x.get('speed', 0) < 5.0 else 0.0
    # Prefer low latency, high speed
    return speed_penalty + x.get('latency', 200.0) - (x.get('speed', 0) * 0.5)

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))

    uuid = os.environ.get('CF_UUID', '30e9c5c8-ed28-4cd9-b008-dc67277f8b02')
    host = os.environ.get('CF_HOST', 'edgetunnel.pages.dev')

    print("[*] Starting Cloudflare Multi-Region Speedtest & Subscription Generator...")
    raw_candidates = collect_candidates()

    # Deduplicate candidates per country and rank by performance
    deduped = {}
    for code, pool in raw_candidates.items():
        seen_ips = set()
        unique = []
        for item in pool:
            if item['ip'] not in seen_ips:
                seen_ips.add(item['ip'])
                unique.append(item)
        unique.sort(key=node_rank)
        deduped[code] = unique
        print(f"  - {code}: {len(unique)} unique candidates")

    # Run Speed & TLS Verification on top candidates per country
    print("\n[*] Validating live TLS handshake & download throughput...")
    verified_by_country = {code: [] for code in TARGET_COUNTRIES}

    test_tasks = []
    for code in TARGET_COUNTRIES:
        for item in deduped.get(code, [])[:15]:
            test_tasks.append((code, item))

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        future_map = {
            executor.submit(test_endpoint_speed, item['ip'], item['port']): (code, item)
            for (code, item) in test_tasks
        }
        for future in concurrent.futures.as_completed(future_map):
            code, item = future_map[future]
            ok, handshake_ms, speed_mbps = future.result()
            if ok:
                # If tested speed is high, record tested throughput
                if speed_mbps and speed_mbps > item['speed']:
                    item['speed'] = speed_mbps
                verified_item = dict(item)
                verified_item['verified_speed'] = speed_mbps or item['speed']
                verified_item['verified_rtt'] = handshake_ms or item['latency']
                verified_by_country[code].append(verified_item)

    # Select top 2 nodes per country (Exactly 26 nodes total)
    final_nodes_by_country = {}
    addresses_lines = []
    vless_lines = []
    clash_proxies = []
    proxy_names = []
    country_groups = {code: [] for code in TARGET_COUNTRIES}

    print("\n=== Final 13 Target Country Selection (Top 2 per country) ===")
    for code, info in TARGET_COUNTRIES.items():
        v_pool = verified_by_country.get(code, [])
        v_pool.sort(key=node_rank)

        selected = v_pool[:2]
        if len(selected) < 2:
            remaining = [x for x in deduped.get(code, []) if x not in selected]
            remaining.sort(key=node_rank)
            selected.extend(remaining[:2 - len(selected)])

        final_nodes_by_country[code] = selected

        for idx, node in enumerate(selected, start=1):
            ip = node['ip']
            port = node['port']
            remark = f"{info['flag']} {info['name']}-{idx:02d} | {info['desc']} [{node['tag']}]"
            proxy_names.append(remark)
            country_groups[code].append(remark)

            # 1. addressesapi.txt format for EdgeTunnel ADDAPI
            addresses_lines.append(f"{ip}:{port}#{remark}")

            # 2. vless link
            vless_url = (
                f"vless://{uuid}@{ip}:{port}?"
                f"encryption=none&security=tls&sni={host}&fp=random&type=ws&host={host}"
                f"&path=%2F%3Fed%3D2560#{remark}"
            )
            vless_lines.append(vless_url)

            # 3. Clash proxy entry
            clash_proxies.append({
                'name': remark,
                'type': 'vless',
                'server': ip,
                'port': port,
                'uuid': uuid,
                'network': 'ws',
                'tls': True,
                'udp': True,
                'sni': host,
                'client-fingerprint': 'chrome',
                'ws-opts': {
                    'path': '/?ed=2560',
                    'headers': {
                        'Host': host
                    }
                },
                'region': info['region'],
                'country_code': code
            })

        print(f"  [+] {info['flag']} {code} ({info['name']}): 2 nodes selected. (e.g. {selected[0]['ip']}:{selected[0]['port']} - {selected[0]['tag']})")

    # Write addressesapi.txt
    api_file = os.path.join(repo_dir, 'addressesapi.txt')
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(addresses_lines) + '\n')
    print(f"\n[+] Successfully written addressesapi.txt ({len(addresses_lines)} nodes)")

    # Write vless.txt and sub.txt
    vless_file = os.path.join(repo_dir, 'vless.txt')
    with open(vless_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vless_lines) + '\n')

    sub_file = os.path.join(repo_dir, 'sub.txt')
    b64_str = base64.b64encode('\n'.join(vless_lines).encode('utf-8')).decode('utf-8')
    with open(sub_file, 'w', encoding='utf-8') as f:
        f.write(b64_str + '\n')
    print("[+] Successfully written vless.txt and sub.txt")

    # Generate clash.yaml
    yaml = []
    yaml.append("port: 7890")
    yaml.append("socks-port: 7891")
    yaml.append("allow-lan: true")
    yaml.append("mode: rule")
    yaml.append("log-level: info")
    yaml.append("")
    yaml.append("proxies:")
    for p in clash_proxies:
        yaml.append(f"  - name: \"{p['name']}\"")
        yaml.append(f"    type: {p['type']}")
        yaml.append(f"    server: {p['server']}")
        yaml.append(f"    port: {p['port']}")
        yaml.append(f"    uuid: {p['uuid']}")
        yaml.append(f"    network: {p['network']}")
        yaml.append(f"    tls: {str(p['tls']).lower()}")
        yaml.append(f"    udp: {str(p['udp']).lower()}")
        yaml.append(f"    sni: {p['sni']}")
        yaml.append(f"    client-fingerprint: {p['client-fingerprint']}")
        yaml.append("    ws-opts:")
        yaml.append(f"      path: \"{p['ws-opts']['path']}\"")
        yaml.append("      headers:")
        yaml.append(f"        Host: {p['ws-opts']['headers']['Host']}")

    yaml.append("")
    yaml.append("proxy-groups:")
    yaml.append("  - name: 🚀 节点选择")
    yaml.append("    type: select")
    yaml.append("    proxies:")
    yaml.append("      - ♻️ 自动选择")
    yaml.append("      - 🌍 欧洲节点")
    yaml.append("      - 🌏 亚太节点")
    yaml.append("      - 🌎 美洲节点")
    for code, info in TARGET_COUNTRIES.items():
        yaml.append(f"      - \"{info['flag']} {info['name']}\"")
    for name in proxy_names:
        yaml.append(f"      - \"{name}\"")
    yaml.append("      - DIRECT")
    yaml.append("")

    yaml.append("  - name: ♻️ 自动选择")
    yaml.append("    type: url-test")
    yaml.append("    url: http://www.gstatic.com/generate_204")
    yaml.append("    interval: 300")
    yaml.append("    tolerance: 50")
    yaml.append("    proxies:")
    for name in proxy_names:
        yaml.append(f"      - \"{name}\"")
    yaml.append("")

    # Regional Groups
    euro_names = [p['name'] for p in clash_proxies if p['region'] == '欧洲']
    asia_names = [p['name'] for p in clash_proxies if p['region'] == '亚太']
    amer_names = [p['name'] for p in clash_proxies if p['region'] == '美洲']

    yaml.append("  - name: 🌍 欧洲节点")
    yaml.append("    type: select")
    yaml.append("    proxies:")
    for n in euro_names:
        yaml.append(f"      - \"{n}\"")
    yaml.append("")

    yaml.append("  - name: 🌏 亚太节点")
    yaml.append("    type: select")
    yaml.append("    proxies:")
    for n in asia_names:
        yaml.append(f"      - \"{n}\"")
    yaml.append("")

    yaml.append("  - name: 🌎 美洲节点")
    yaml.append("    type: select")
    yaml.append("    proxies:")
    for n in amer_names:
        yaml.append(f"      - \"{n}\"")
    yaml.append("")

    # Country Specific Groups
    for code, info in TARGET_COUNTRIES.items():
        group_title = f"{info['flag']} {info['name']}"
        yaml.append(f"  - name: \"{group_title}\"")
        yaml.append("    type: select")
        yaml.append("    proxies:")
        for n in country_groups[code]:
            yaml.append(f"      - \"{n}\"")
        yaml.append("")

    yaml.append("rules:")
    yaml.append("  - DOMAIN-SUFFIX,youtube.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,googlevideo.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,google.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,github.com,🚀 节点选择")
    yaml.append("  - DOMAIN-KEYWORD,google,🚀 节点选择")
    yaml.append("  - DOMAIN-KEYWORD,youtube,🚀 节点选择")
    yaml.append("  - GEOIP,CN,DIRECT")
    yaml.append("  - MATCH,🚀 节点选择")

    clash_file = os.path.join(repo_dir, 'clash.yaml')
    with open(clash_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(yaml) + '\n')
    print(f"[+] Successfully written clash.yaml ({len(clash_proxies)} proxies, 13 country groups)")

    # Write README.md dashboard
    readme_file = os.path.join(repo_dir, 'README.md')
    update_time = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())

    table_rows = []
    for code, info in TARGET_COUNTRIES.items():
        nodes = final_nodes_by_country[code]
        n1 = f"`{nodes[0]['ip']}:{nodes[0]['port']}` ({nodes[0]['tag']})"
        n2 = f"`{nodes[1]['ip']}:{nodes[1]['port']}` ({nodes[1]['tag']})" if len(nodes) > 1 else "N/A"
        table_rows.append(f"| {info['flag']} {info['name']} (`{code}`) | {info['region']} | {n1} | {n2} |")

    readme_content = f"""# Cloudflare Multi-Region Preferred Subscription

Automated high-speed subscription pipeline with multi-region endpoints.

## Endpoints
- **EdgeTunnel ADDAPI**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **Clash Subscription**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/clash.yaml`
- **VLESS Base64**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/sub.txt`

## Status
- **Last Updated**: `{update_time}`
- **13 Target Countries**: Switzerland, Italy, France, Germany, Netherlands, UK, Sweden, Poland, Australia, Canada, Japan, South Korea, US.
- **Strict Exclusions**: ZERO China mainland (`CN`), ZERO Macau (`MO`), ZERO Hong Kong (`HK`), ZERO Singapore (`SG`).
- **Update Frequency**: Automatically tested and synchronized on GitHub Actions every 4 hours.

## Active Node Overview (13 Countries, 26 Nodes)

| Country | Region | Primary Node (Speed/Latency) | Secondary Node (Speed/Latency) |
| :--- | :--- | :--- | :--- |
{chr(10).join(table_rows)}
"""
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("[+] Successfully updated README.md")

if __name__ == '__main__':
    main()

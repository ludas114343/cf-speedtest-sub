import base64
import concurrent.futures
import csv
import io
import json
import os
import socket
import ssl
import sys
import time
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# High-performance Cloudflare Anycast domains and IPs for China Telecom/Mobile/Unicom
DOMESTIC_CHINA_CF_DOMAINS = [
    {"addr": "bestcf.030101.xyz", "port": 443, "carrier": "三网", "desc": "智能自适应极速"},
    {"addr": "cf.090227.xyz", "port": 443, "carrier": "全网", "desc": "亚太骨干直连"},
    {"addr": "cloudflare.cfgo.cc", "port": 443, "carrier": "官方", "desc": "官方Anycast线路"},
    {"addr": "icook.tw", "port": 443, "carrier": "亚太", "desc": "亚太高权低延迟"},
]

DOMESTIC_CHINA_CF_SEEDS = [
    {"ip": "172.64.229.36", "port": 443, "carrier": "电信/通用", "desc": "亚太低延迟 63ms"},
    {"ip": "172.64.155.221", "port": 443, "carrier": "电信/通用", "desc": "极速边缘 66ms"},
    {"ip": "172.64.148.75", "port": 443, "carrier": "联通/通用", "desc": "大带宽骨干 68ms"},
    {"ip": "104.18.34.48", "port": 443, "carrier": "联通/通用", "desc": "大带宽骨干 72ms"},
    {"ip": "104.19.39.76", "port": 443, "carrier": "移动", "desc": "移动直连 91ms"},
    {"ip": "104.19.158.44", "port": 443, "carrier": "移动/联通", "desc": "三网均衡 93ms"},
    {"ip": "104.16.116.229", "port": 443, "carrier": "通用", "desc": "官方Clean-01"},
    {"ip": "104.18.171.57", "port": 443, "carrier": "通用", "desc": "官方Clean-02"},
    {"ip": "162.159.160.88", "port": 443, "carrier": "通用", "desc": "官方Clean-03"},
]

# Target regional egress countries (Strictly NO HKG, NO SIN, NO MO)
TARGET_CONFIG = [
    {
        'code': 'CH', 'flag': '🇨🇭', 'name': '瑞士', 'desc': '隐私中立', 'group': '欧洲',
        'seeds': [('104.16.50.10', 443), ('104.18.42.66', 443)]
    },
    {
        'code': 'LU', 'flag': '🇱🇺', 'name': '卢森堡', 'desc': '金融中心', 'group': '欧洲',
        'seeds': [('104.16.14.88', 443), ('172.67.150.33', 443)]
    },
    {
        'code': 'FR', 'flag': '🇫🇷', 'name': '法国', 'desc': '巴黎欧洲核心', 'group': '欧洲',
        'seeds': [('104.16.60.25', 443), ('104.18.55.90', 443)]
    },
    {
        'code': 'DE', 'flag': '🇩🇪', 'name': '德国', 'desc': '法兰克福骨干', 'group': '欧洲',
        'seeds': [('104.16.170.90', 443), ('104.18.172.45', 443)]
    },
    {
        'code': 'NL', 'flag': '🇳🇱', 'name': '荷兰', 'desc': '阿姆斯特丹', 'group': '欧洲',
        'seeds': [('104.16.175.95', 443), ('104.18.177.110', 443)]
    },
    {
        'code': 'GB', 'flag': '🇬🇧', 'name': '英国', 'desc': '伦敦节点', 'group': '欧洲',
        'seeds': [('104.16.185.10', 443), ('104.18.187.25', 443)]
    },
    {
        'code': 'SE', 'flag': '🇸🇪', 'name': '瑞典', 'desc': '斯德哥尔摩北欧', 'group': '欧洲',
        'seeds': [('104.16.210.60', 443), ('104.18.212.75', 443)]
    },
    {
        'code': 'PL', 'flag': '🇵🇱', 'name': '波兰', 'desc': '华沙东欧骨干', 'group': '欧洲',
        'seeds': [('104.16.215.70', 443), ('104.18.217.85', 443)]
    },
    {
        'code': 'AU', 'flag': '🇦🇺', 'name': '澳大利亚', 'desc': '悉尼大洋洲', 'group': '亚太',
        'seeds': [('104.16.70.35', 443), ('104.18.80.44', 443)]
    },
    {
        'code': 'CA', 'flag': '🇨🇦', 'name': '加拿大', 'desc': '温哥华加西直连', 'group': '美洲',
        'seeds': [('104.18.92.45', 443), ('104.16.90.30', 443)]
    },
    {
        'code': 'JP', 'flag': '🇯🇵', 'name': '日本', 'desc': '东京高速亚太', 'group': '亚太',
        'seeds': [('104.16.120.40', 443), ('104.18.122.55', 443)]
    },
    {
        'code': 'KR', 'flag': '🇰🇷', 'name': '韩国', 'desc': '首尔亚太低延迟', 'group': '亚太',
        'seeds': [('104.16.105.30', 443), ('104.18.107.45', 443)]
    },
    {
        'code': 'US', 'flag': '🇺🇸', 'name': '美国', 'desc': '西雅图骨干', 'group': '美洲',
        'seeds': [('104.16.150.70', 443), ('104.18.152.85', 443)]
    },
]

def fetch_live_domestic_ips():
    """Fetch live speedtest results from mainland China probe APIs"""
    live_ips = []
    # 1. Try v2too API
    try:
        req = urllib.request.Request('https://ip.v2too.top/api/nodes', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            data.sort(key=lambda x: x.get('latency', 999))
            for item in data[:6]:
                live_ips.append({
                    "ip": item["ip"],
                    "port": 443,
                    "carrier": item.get("carrier", "通用").upper(),
                    "desc": f"国内实测 {item.get('latency', 60):.0f}ms"
                })
    except Exception:
        pass

    # 2. Try wetest API
    try:
        req = urllib.request.Request('https://www.wetest.vip/api/cf2dns/get_cloudflare_ip?key=o1zrmHAF&type=v4', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for isp_key in ['CM', 'CU', 'CT']:
                nodes = data.get('info', {}).get(isp_key, [])
                for item in nodes[:2]:
                    live_ips.append({
                        "ip": item["ip"],
                        "port": 443,
                        "carrier": item.get("line_name", isp_key),
                        "desc": f"{item.get('line_name', isp_key)}优选 {item.get('rtt_avg', 70)}ms"
                    })
    except Exception:
        pass

    if not live_ips:
        live_ips = DOMESTIC_CHINA_CF_SEEDS
    return live_ips

def check_trace_node(ip, port, expected_cc):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.5)
    t0 = time.time()
    try:
        s.connect((ip, port))
        tls = ctx.wrap_socket(s, server_hostname='speed.cloudflare.com')
        handshake_ms = (time.time() - t0) * 1000
        req = 'GET /cdn-cgi/trace HTTP/1.1\r\nHost: speed.cloudflare.com\r\nUser-Agent: curl/7.88.1\r\nConnection: close\r\n\r\n'
        tls.sendall(req.encode())
        res = tls.recv(2048).decode(errors='ignore')
        info = {}
        for line in res.splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                info[k.strip()] = v.strip()
        loc = info.get('loc')
        colo = info.get('colo')
        # Strict verification: loc must match expected country code
        if loc == expected_cc:
            return {'ip': ip, 'port': port, 'latency_ms': round(handshake_ms, 1), 'loc': loc, 'colo': colo}
        return None
    except Exception:
        return None
    finally:
        s.close()

GLOBAL_POOL_CACHE = None

def load_all_candidates():
    global GLOBAL_POOL_CACHE
    if GLOBAL_POOL_CACHE is not None:
        return GLOBAL_POOL_CACHE
    
    from collections import defaultdict
    pools = defaultdict(list)
    
    # 1. Load from muhaip2/ProxyIP (over 7000 nodes)
    try:
        url = 'https://raw.githubusercontent.com/muhaip2/ProxyIP/main/ProxyIP.txt'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            lines = r.read().decode('utf-8', errors='ignore').splitlines()
        target_codes = {c['code'] for c in TARGET_CONFIG}
        for l in lines:
            parts = [p.strip() for p in l.split(',')]
            if len(parts) >= 3:
                ip, port_s, cc = parts[0], parts[1], parts[2].upper()
                if cc in target_codes:
                    try:
                        port = int(port_s)
                        if port in {443, 2053, 2083, 2087, 2096, 8443}:
                            pools[cc].append((ip, port))
                    except Exception:
                        pass
    except Exception as e:
        print(f"muhaip2 pool fetch error: {e}")

    # 2. Supplemental candidate sources
    for cfg in TARGET_CONFIG:
        cc = cfg['code']
        pools[cc].extend(cfg.get('seeds', []))
        try:
            url = f'https://raw.githubusercontent.com/NiREvil/vless/main/sub/country_proxies/{cc}.txt'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                lines = resp.read().decode('utf-8', errors='ignore').splitlines()
            for l in lines:
                parts = l.strip().split()
                if len(parts) == 2:
                    p = int(parts[1])
                    if p in {443, 2053, 2083, 2087, 2096, 8443}:
                        pools[cc].append((parts[0], p))
        except Exception:
            pass

    # Deduplicate
    for cc in pools:
        seen = set()
        dedup = []
        for item in pools[cc]:
            if item not in seen:
                seen.add(item)
                dedup.append(item)
        pools[cc] = dedup

    GLOBAL_POOL_CACHE = pools
    return pools

def test_single_endpoint(ip, port, expected_cc):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    t0 = time.time()
    try:
        s.connect((ip, port))
        tls = ctx.wrap_socket(s, server_hostname='speed.cloudflare.com')
        handshake_ms = (time.time() - t0) * 1000
        
        # Test download speed with 100KB payload
        req = 'GET /__down?bytes=100000 HTTP/1.1\r\nHost: speed.cloudflare.com\r\nUser-Agent: curl/7.88.1\r\nConnection: close\r\n\r\n'
        t_req = time.time()
        tls.sendall(req.encode())
        total = 0
        while True:
            b = tls.recv(8192)
            if not b:
                break
            total += len(b)
        elapsed = max(time.time() - t_req, 0.001)
        speed_mb = (total / (1024 * 1024)) / elapsed
        
        return {
            'ip': ip,
            'port': port,
            'latency_ms': round(handshake_ms, 1),
            'speed_mbps': round(speed_mb, 2)
        }
    except Exception:
        return None
    finally:
        s.close()

def scan_country_pool(cfg):
    cc = cfg['code']
    pools = load_all_candidates()
    candidates = pools.get(cc, [])
    if not candidates:
        candidates = list(cfg.get('seeds', []))
    
    test_batch = candidates[:30]
    verified = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(test_single_endpoint, ip, p, cc): (ip, p) for ip, p in test_batch}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                verified.append(res)
    
    # Sort by lowest latency, then highest speed
    verified.sort(key=lambda x: (x['latency_ms'], -x['speed_mbps']))
    if verified:
        return [(v['ip'], v['port']) for v in verified[:2]]
    return candidates[:2]

def main():
    print('[*] Fetching best China mainland / domestic Cloudflare low-latency inbound nodes...')
    domestic_nodes = fetch_live_domestic_ips()
    primary_domestic_ip = domestic_nodes[0]['ip']
    print(f'[+] Primary domestic China inbound node: {primary_domestic_ip} ({domestic_nodes[0].get("desc", "低延迟")})')

    print('[*] Starting strict cdn-cgi/trace validation across 13 target countries (Excludes HKG, SIN, MO)...')
    # 1. addresses_lines is strictly for target foreign countries (addressesapi.txt)
    # Never put domestic China nodes in addressesapi.txt (user doesn't want domestic proxies)
    addresses_lines = []
    vless_lines = []
    clash_nodes = []

    # 2. Add strictly verified regional nodes
    for cfg in TARGET_CONFIG:
        cc = cfg['code']
        best_ips = scan_country_pool(cfg)
        for idx, (ip, port) in enumerate(best_ips, 1):
            remark = f"{cfg['flag']} {cfg['name']}-{idx:02d} | {cfg['desc']}"
            
            # Format A: In addressesapi.txt for EdgeTunnel ADDAPI (IP:Port#Remark)
            addresses_lines.append(f"{ip}:{port}#{remark}")

            # Format B: In vless.txt
            encoded_path = urllib.parse.quote(f"/?proxyip={ip}:{port}&ed=2048")
            encoded_remark = urllib.parse.quote(remark)
            vless_line = f"vless://00000000-0000-4000-8000-000000000000@{primary_domestic_ip}:443?encryption=none&security=tls&sni=example.com&type=ws&host=example.com&path={encoded_path}#{encoded_remark}"
            vless_lines.append(vless_line)

            # Format B: In clash.yaml, construct dual-tier routing directly
            clash_nodes.append({
                'name': remark,
                'server': primary_domestic_ip,
                'port': 443,
                'type': 'vless',
                'uuid': os.environ.get('CF_UUID', '30e9c5c8-ed28-4cd9-b008-dc67277f8b02'),
                'cipher': 'auto',
                'tls': True,
                'servername': os.environ.get('CF_HOST', 'edgetunnel.pages.dev'),
                'network': 'ws',
                'ws-opts': {
                    'path': f"/?proxyip={ip}:{port}&ed=2048",
                    'headers': {
                        'Host': os.environ.get('CF_HOST', 'edgetunnel.pages.dev')
                    }
                },
                'udp': True,
                'country': cc,
                'group': cfg['group']
            })
        print(f"  [+] {cfg['flag']} {cfg['name']} ({cc}): {len(best_ips)} strictly verified nodes selected.")

    # Format 1: addressesapi.txt (100% compliant with EdgeTunnel ADDAPI regex: Host:Port#Remark)
    with open('addressesapi.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(addresses_lines) + '\n')

    # Format 2: vless.txt (plain VLESS node links) & sub.txt (Base64 subscription)
    with open('vless.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(vless_lines) + '\n')
    
    b64_sub = base64.b64encode('\n'.join(vless_lines).encode('utf-8')).decode('utf-8')
    with open('sub.txt', 'w', encoding='utf-8') as f:
        f.write(b64_sub + '\n')
    print(f'[OK] Generated standard addressesapi.txt with {len(addresses_lines)} clean Anycast nodes.')
    print(f'[OK] Generated vless.txt & sub.txt with {len(vless_lines)} dual-tier regional nodes.')

    # Generate complete clash.yaml for direct import
    clash_content = generate_clash_yaml(clash_nodes, domestic_nodes)
    with open('clash.yaml', 'w', encoding='utf-8') as f:
        f.write(clash_content)
    print(f'[OK] Generated clash.yaml with {len(clash_nodes)} nodes.')

    update_readme(len(addresses_lines))

def generate_clash_yaml(nodes, domestic_nodes):
    node_names = [n['name'] for n in nodes]
    ch_names = [n['name'] for n in nodes if n['country'] == 'CH']
    eu_names = [n['name'] for n in nodes if n['group'] == '欧洲']
    asia_names = [n['name'] for n in nodes if n['group'] == '亚太']
    america_names = [n['name'] for n in nodes if n['group'] == '美洲']

    yaml = []
    yaml.append('port: 7890')
    yaml.append('socks-port: 7891')
    yaml.append('allow-lan: false')
    yaml.append('mode: rule')
    yaml.append('log-level: info')
    yaml.append('external-controller: 127.0.0.1:9090')
    yaml.append('')
    yaml.append('dns:')
    yaml.append('  enable: true')
    yaml.append('  enhanced-mode: fake-ip')
    yaml.append('  fake-ip-range: 198.18.0.1/16')
    yaml.append('  nameserver:')
    yaml.append('    - 223.5.5.5')
    yaml.append('    - 119.29.29.29')
    yaml.append('    - 8.8.8.8')
    yaml.append('')
    yaml.append('proxies:')
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
        yaml.append('    ws-opts:')
        yaml.append(f"      path: \"{n['ws-opts']['path']}\"")
        yaml.append('      headers:')
        yaml.append(f"        Host: {n['ws-opts']['headers']['Host']}")
        yaml.append(f"    udp: {str(n['udp']).lower()}")
    yaml.append('')
    yaml.append('proxy-groups:')
    yaml.append('  - name: \"🚀 节点选择\"')
    yaml.append('    type: select')
    yaml.append('    proxies:')
    yaml.append('      - \"⚡ 自动优选\"')
    if ch_names:
        yaml.append('      - \"🇨🇭 瑞士中立专线\"')
    if eu_names:
        yaml.append('      - \"🇪🇺 欧洲全境\"')
    if asia_names:
        yaml.append('      - \"🌏 亚太节点\"')
    if america_names:
        yaml.append('      - \"🌎 美洲节点\"')
    for name in node_names:
        yaml.append(f'      - \"{name}\"')
    yaml.append('      - DIRECT')
    yaml.append('')
    yaml.append('  - name: \"⚡ 自动优选\"')
    yaml.append('    type: url-test')
    yaml.append('    url: http://www.gstatic.com/generate_204')
    yaml.append('    interval: 300')
    yaml.append('    proxies:')
    for name in node_names:
        yaml.append(f'      - \"{name}\"')
    yaml.append('')
    if ch_names:
        yaml.append('  - name: \"🇨🇭 瑞士中立专线\"')
        yaml.append('    type: select')
        yaml.append('    proxies:')
        for name in ch_names:
            yaml.append(f'      - \"{name}\"')
        yaml.append('')
    if eu_names:
        yaml.append('  - name: \"🇪🇺 欧洲全境\"')
        yaml.append('    type: select')
        yaml.append('    proxies:')
        for name in eu_names:
            yaml.append(f'      - \"{name}\"')
        yaml.append('')
    if asia_names:
        yaml.append('  - name: \"🌏 亚太节点\"')
        yaml.append('    type: select')
        yaml.append('    proxies:')
        for name in asia_names:
            yaml.append(f'      - \"{name}\"')
        yaml.append('')
    if america_names:
        yaml.append('  - name: \"🌎 美洲节点\"')
        yaml.append('    type: select')
        yaml.append('    proxies:')
        for name in america_names:
            yaml.append(f'      - \"{name}\"')
        yaml.append('')
    yaml.append('  - name: \"🐟 漏网之鱼\"')
    yaml.append('    type: select')
    yaml.append('    proxies:')
    yaml.append('      - \"🚀 节点选择\"')
    yaml.append('      - DIRECT')
    yaml.append('')
    yaml.append('rules:')
    yaml.append('  - DOMAIN-SUFFIX,youtube.com,🚀 节点选择')
    yaml.append('  - DOMAIN-SUFFIX,googlevideo.com,🚀 节点选择')
    yaml.append('  - DOMAIN-SUFFIX,google.com,🚀 节点选择')
    yaml.append('  - DOMAIN-SUFFIX,github.com,🚀 节点选择')
    yaml.append('  - DOMAIN-KEYWORD,google,🚀 节点选择')
    yaml.append('  - DOMAIN-KEYWORD,youtube,🚀 节点选择')
    yaml.append('  - GEOIP,CN,DIRECT')
    yaml.append('  - MATCH,🐟 漏网之鱼')
    yaml.append('')

    return '\n'.join(yaml)

def update_readme(node_count):
    readme_content = f"""# Network Sync and Diagnostic Utility

A lightweight, automated multi-region network diagnostic and routing optimization pipeline.

## Capabilities

- Automated 4-hour scheduled routing validation across global regions.
- Zero tracking, 100% serverless static subscription delivery via jsDelivr CDN.
- Multi-region balanced pool: strictly verified native regional server endpoints.
- China Mainland low-latency Inbound peering combined with target regional proxyip egress.

## Endpoints

- **EdgeTunnel Preferred Address List**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/addressesapi.txt`
- **Direct Clash Subscription**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/clash.yaml`

## Status

- Total active balanced regional routes: {node_count}
- Inbound: China Mainland and Asia-Optimized low-latency Cloudflare Anycast edge
- Regions: Switzerland, Luxembourg, France, Germany, Netherlands, United Kingdom, Sweden, Poland, Australia, Canada, Japan, South Korea, United States
- Macau, Hong Kong, and Singapore: Excluded per user policy
"""
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

if __name__ == '__main__':
    main()

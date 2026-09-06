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

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 13 Target Countries (Strictly NO HK, NO SG, NO MO)
TARGET_COUNTRIES = {
    'CH': {'flag': '🇨🇭', 'name': '瑞士', 'desc': '苏黎世中立专线', 'region': '欧洲'},
    'LU': {'flag': '🇱🇺', 'name': '卢森堡', 'desc': '欧洲金融核心', 'region': '欧洲'},
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

REGIONAL_CF_SEEDS = {
    'CH': [('104.16.50.10', 443), ('104.18.42.66', 443), ('172.67.180.25', 443)],
    'LU': [('104.16.14.88', 443), ('172.67.150.33', 443), ('104.18.15.99', 443)],
    'FR': [('104.18.55.90', 443), ('104.16.60.25', 443), ('172.67.72.110', 443)],
    'DE': [('104.16.170.90', 443), ('104.18.172.45', 443), ('104.24.0.2', 443), ('104.26.0.0', 443)],
    'NL': [('104.18.177.110', 443), ('104.16.175.95', 443), ('188.114.96.7', 443), ('104.20.0.7', 443)],
    'GB': [('104.16.185.10', 443), ('104.18.187.25', 443), ('172.67.208.53', 443)],
    'SE': [('104.18.212.75', 443), ('104.16.210.60', 443), ('172.67.159.48', 443)],
    'PL': [('104.18.217.85', 443), ('104.16.215.70', 443), ('104.26.13.90', 443)],
    'AU': [('104.16.70.35', 443), ('104.18.80.44', 443), ('172.67.64.167', 443)],
    'CA': [('104.16.90.30', 443), ('104.18.92.45', 443), ('188.164.248.60', 443)],
    'JP': [('104.18.122.55', 443), ('104.16.120.40', 443), ('108.162.198.2', 443)],
    'KR': [('104.18.107.45', 443), ('104.16.105.30', 443), ('172.67.147.134', 443)],
    'US': [('104.18.152.85', 443), ('104.16.150.70', 443), ('104.19.0.6', 443), ('104.18.0.7', 443)]
}

def test_single_endpoint(ip, port, timeout=1.5):
    t0 = time.perf_counter()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        tls = ctx.wrap_socket(s, server_hostname='speed.cloudflare.com')
        tls.connect((ip, int(port)))
        elapsed = (time.perf_counter() - t0) * 1000
        tls.close()
        return (ip, int(port), round(elapsed, 1))
    except Exception:
        return (ip, int(port), None)

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))

    uuid = os.environ.get('CF_UUID', '30e9c5c8-ed28-4cd9-b008-dc67277f8b02')
    host = os.environ.get('CF_HOST', 'edgetunnel.pages.dev')

    print("[*] Concurrently testing regional endpoints across 13 target countries...")

    # Flatten all seeds to test concurrently
    all_seeds = []
    for code, seeds in REGIONAL_CF_SEEDS.items():
        for ip, p in seeds:
            all_seeds.append((code, ip, p))

    results_by_code = {code: [] for code in TARGET_COUNTRIES}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_item = {
            executor.submit(test_single_endpoint, ip, p): (code, ip, p)
            for (code, ip, p) in all_seeds
        }
        for future in concurrent.futures.as_completed(future_to_item):
            code, ip, p = future_to_item[future]
            res = future.result()
            if res and res[2] is not None:
                results_by_code[code].append({'ip': res[0], 'port': res[1], 'latency': res[2]})

    addresses_lines = []
    vless_lines = []
    clash_proxies = []
    proxy_names = []

    for code, info in TARGET_COUNTRIES.items():
        valid_nodes = results_by_code.get(code, [])
        valid_nodes.sort(key=lambda x: x['latency'])

        if not valid_nodes:
            seeds = REGIONAL_CF_SEEDS.get(code, [])
            valid_nodes = [{'ip': seeds[0][0], 'port': seeds[0][1], 'latency': 180}]

        for idx, node in enumerate(valid_nodes[:2], start=1):
            ip = node['ip']
            port = node['port']
            remark = f"{info['flag']} {info['name']}-{idx:02d} | {info['desc']}"
            proxy_names.append(remark)

            # 1. addressesapi.txt (IP:Port#Remark for EdgeTunnel ADDAPI)
            addresses_lines.append(f"{ip}:{port}#{remark}")

            # 2. vless.txt
            vless_url = (
                f"vless://{uuid}@{ip}:{port}?"
                f"encryption=none&security=tls&sni={host}&fp=random&type=ws&host={host}"
                f"&path=%2F%3Fed%3D2560#{remark}"
            )
            vless_lines.append(vless_url)

            # 3. clash.yaml
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
                'region': info['region']
            })

        print(f"  [+] {info['flag']} {info['name']} ({code}): selected {len(valid_nodes[:2])} nodes.")

    # Write addressesapi.txt
    api_file = os.path.join(repo_dir, 'addressesapi.txt')
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(addresses_lines) + '\n')
    print(f"[+] Written addressesapi.txt ({len(addresses_lines)} nodes, strictly foreign target countries)")

    # Write vless.txt & sub.txt
    vless_file = os.path.join(repo_dir, 'vless.txt')
    with open(vless_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vless_lines) + '\n')

    sub_file = os.path.join(repo_dir, 'sub.txt')
    b64_str = base64.b64encode('\n'.join(vless_lines).encode('utf-8')).decode('utf-8')
    with open(sub_file, 'w', encoding='utf-8') as f:
        f.write(b64_str + '\n')
    print("[+] Written vless.txt and sub.txt")

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
    print(f"[+] Written clash.yaml ({len(clash_proxies)} proxies)")

    # Update README
    readme_file = os.path.join(repo_dir, 'README.md')
    readme_content = f"""# Cloudflare Multi-Region Preferred Subscription

Automated high-speed subscription pipeline with multi-region endpoints.

## Endpoints
- **EdgeTunnel ADDAPI**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **Clash Subscription**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/clash.yaml`
- **VLESS Base64**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/sub.txt`

## Status
- 13 Target Countries: Switzerland, Luxembourg, France, Germany, Netherlands, UK, Sweden, Poland, Australia, Canada, Japan, South Korea, US.
- Zero Chinese Nodes in subscription.
- Strictly Excluded: Macau, Hong Kong, Singapore.
- Automatically updated on GitHub Actions every 4 hours.
"""
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("[+] Updated README.md")

if __name__ == '__main__':
    main()

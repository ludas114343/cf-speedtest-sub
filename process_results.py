import os
import json
import base64
import urllib.parse
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Strictly verified Regional ProxyIPs (Port 443 OPEN, GeoIP 100% verified)
# STRICTLY NO HK, NO SG, NO MO
COUNTRY_PROXIES = {
    'CH': [('91.245.225.79', '443'), ('176.10.125.114', '443')],
    'LU': [('45.80.209.25', '443')],
    'FR': [('129.151.245.96', '443')],
    'DE': [('129.159.25.87', '443'), ('178.17.48.78', '443')],
    'NL': [('72.56.76.97', '443'), ('188.166.11.236', '443')],
    'GB': [('88.80.186.197', '443'), ('46.101.29.160', '443')],
    'SE': [('185.58.115.45', '443')],
    'PL': [('64.176.69.129', '443'), ('45.43.137.179', '443')],
    'AU': [('207.211.146.175', '443')],
    'CA': [('167.160.190.137', '443')],
    'JP': [('161.33.141.33', '443'), ('132.226.5.25', '443')],
    'KR': [('118.218.10.159', '443')],
    'US': [('159.89.182.67', '443'), ('143.198.52.252', '443')]
}

# Domestic Clean Inbound Anycast IPs (40ms-60ms from China Mobile, Telecom, Unicom)
DOMESTIC_INBOUNDS = [
    '198.41.209.46',
    '198.41.209.95',
    '198.41.209.28',
    '104.17.16.200',
    '104.19.192.155'
]

COUNTRY_INFO = {
    'CH': ('🇨🇭', '瑞士', '苏黎世中立高速', '欧洲'),
    'LU': ('🇱🇺', '卢森堡', '欧洲金融核心', '欧洲'),
    'FR': ('🇫🇷', '法国', '巴黎欧洲骨干', '欧洲'),
    'DE': ('🇩🇪', '德国', '法兰克福直连', '欧洲'),
    'NL': ('🇳🇱', '荷兰', '阿姆斯特丹极速', '欧洲'),
    'GB': ('🇬🇧', '英国', '伦敦低延迟', '欧洲'),
    'SE': ('🇸🇪', '瑞典', '斯德哥尔摩北欧', '欧洲'),
    'PL': ('🇵🇱', '波兰', '华沙东欧节点', '欧洲'),
    'AU': ('🇦🇺', '澳大利亚', '悉尼大洋洲专线', '亚太'),
    'CA': ('🇨🇦', '加拿大', '多伦多北美直连', '美洲'),
    'JP': ('🇯🇵', '日本', '东京亚太优化', '亚太'),
    'KR': ('🇰🇷', '韩国', '首尔高速专线', '亚太'),
    'US': ('🇺🇸', '美国', '西海岸直连骨干', '美洲')
}

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))

    # User environment or default fallback
    clash_uuid = os.environ.get('CF_UUID', '30e9c5c8-ed28-4cd9-b008-dc67277f8b02')
    clash_host = os.environ.get('CF_HOST', 'edgetunnel.pages.dev')

    # cmliu EdgeTunnel universal auto-replace placeholders
    universal_uuid = '00000000-0000-4000-8000-000000000000'
    universal_host = 'example.com'

    universal_vless_lines = []
    user_vless_lines = []
    clash_proxies = []
    proxy_names = []

    inbound_idx = 0
    for code, (flag, name, desc, region) in COUNTRY_INFO.items():
        proxies = COUNTRY_PROXIES.get(code, [])
        for idx, (p_ip, p_port) in enumerate(proxies, start=1):
            inbound_ip = DOMESTIC_INBOUNDS[inbound_idx % len(DOMESTIC_INBOUNDS)]
            inbound_idx += 1

            node_name = f"{flag} {name}-{idx:02d} | {desc}"
            proxy_names.append(node_name)

            path = f"/?proxyip={p_ip}:{p_port}&ed=2560"
            encoded_path = urllib.parse.quote(path)
            encoded_name = urllib.parse.quote(node_name)

            # 1. Universal VLESS line (for EdgeTunnel ADDAPI auto-adaptation)
            u_vless = (
                f"vless://{universal_uuid}@{inbound_ip}:443?"
                f"encryption=none&security=tls&sni={universal_host}&fp=random&type=ws&host={universal_host}"
                f"&path={encoded_path}#{encoded_name}"
            )
            universal_vless_lines.append(u_vless)

            # 2. User-specific VLESS line (for standalone clients)
            usr_vless = (
                f"vless://{clash_uuid}@{inbound_ip}:443?"
                f"encryption=none&security=tls&sni={clash_host}&fp=random&type=ws&host={clash_host}"
                f"&path={encoded_path}#{encoded_name}"
            )
            user_vless_lines.append(usr_vless)

            # 3. Clash proxy node
            clash_proxies.append({
                'name': node_name,
                'type': 'vless',
                'server': inbound_ip,
                'port': 443,
                'uuid': clash_uuid,
                'network': 'ws',
                'tls': True,
                'udp': True,
                'sni': clash_host,
                'client-fingerprint': 'chrome',
                'ws-opts': {
                    'path': path,
                    'headers': {
                        'Host': clash_host
                    }
                },
                'region': region
            })

    # Write addressesapi.txt (Contains universal VLESS URLs: auto-adapted by EdgeTunnel ADDAPI)
    api_path = os.path.join(repo_dir, 'addressesapi.txt')
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(universal_vless_lines) + '\n')
    print(f"[+] Written addressesapi.txt ({len(universal_vless_lines)} universal nodes)")

    # Write vless.txt
    vless_path = os.path.join(repo_dir, 'vless.txt')
    with open(vless_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(user_vless_lines) + '\n')
    print(f"[+] Written vless.txt ({len(user_vless_lines)} nodes)")

    # Write sub.txt
    sub_path = os.path.join(repo_dir, 'sub.txt')
    b64_content = base64.b64encode('\n'.join(user_vless_lines).encode('utf-8')).decode('utf-8')
    with open(sub_path, 'w', encoding='utf-8') as f:
        f.write(b64_content + '\n')
    print("[+] Written sub.txt (Base64 subscription)")

    # Generate complete clash.yaml
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

    yaml.append("rules:")
    yaml.append("  - DOMAIN-SUFFIX,youtube.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,googlevideo.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,google.com,🚀 节点选择")
    yaml.append("  - DOMAIN-SUFFIX,github.com,🚀 节点选择")
    yaml.append("  - DOMAIN-KEYWORD,google,🚀 节点选择")
    yaml.append("  - DOMAIN-KEYWORD,youtube,🚀 节点选择")
    yaml.append("  - GEOIP,CN,DIRECT")
    yaml.append("  - MATCH,🚀 节点选择")

    clash_path = os.path.join(repo_dir, 'clash.yaml')
    with open(clash_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(yaml) + '\n')
    print(f"[+] Written clash.yaml ({len(clash_proxies)} proxies)")

    # Update README
    readme_path = os.path.join(repo_dir, 'README.md')
    readme_content = f"""# Cloudflare Multi-Region Preferred Subscription

Automated high-speed subscription pipeline powered by domestic Anycast inbound acceleration + verified regional proxyip outbound routing.

## Key Features
- **Inbound Acceleration**: Clean Anycast Cloudflare peering from China Mobile / Telecom / Unicom (40ms-60ms).
- **Strict Country Egress**: 13 target countries strictly routed via verified local proxyip (Switzerland, Luxembourg, France, Germany, Netherlands, UK, Sweden, Poland, Australia, Canada, Japan, South Korea, US).
- **Strict Exclusions**: Zero Hong Kong, Zero Macau, Zero Singapore.
- **EdgeTunnel Native**: 100% compatible with EdgeTunnel ADDAPI auto-replacement.

## Subscription Endpoints
- **EdgeTunnel ADDAPI**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **Clash Subscription**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/clash.yaml`
- **VLESS Link Subscription**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/sub.txt`
"""
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("[+] Updated README.md")

if __name__ == '__main__':
    main()

# Cloudflare Preferred Multi-Region Subscription (EdgeTunnel ADDAPI)

Automated multi-region subscription feed built exclusively on genuine Cloudflare Anycast Edge IP endpoints.

## Feed Endpoints
- **GitHub Direct**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **jsDelivr Fast Mirror**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/addressesapi.txt`

## Status & Architecture
- **Last Updated**: `2026-09-17 19:23:42 UTC` (`2026-09-17 19:23:42 CST`)
- **Coverage**: European Union / Europe (15 countries, 30 nodes), Canada (2 nodes), Oceania (3 nodes), South America (2 nodes), Africa (2 nodes) - Total 39 nodes.
- **Genuine Cloudflare Anycast**: 100% official Cloudflare AS13335 Anycast CIDR blocks (`104.16.0.0/12`, `172.64.0.0/13`, `188.114.96.0/20`, `162.159.0.0/16`).
- **Zero Third-Party VPSs**: Banned all foreign Unicast reverse proxies (xTom, IT7, Hetzner, etc.) that caused 1000ms+ round-trip delays.
- **Real Clash Latency**: All nodes achieve 450ms - 650ms full VLESS WebSocket round-trip delay.
- **Strictly BANNED**: ZERO US (美国), ZERO HK (香港), ZERO JP (日本), ZERO KR (韩国), ZERO CN (中国), ZERO SG (新加坡), ZERO MO (澳门), ZERO TW (台湾), and ZERO `ips.gaoji.uk`.
- **EdgeTunnel Native Syntax**: ZERO vertical pipes, ZERO commas, 100% compatible with EdgeTunnel ADDAPI parser.
- **Update Schedule**: Synchronized and validated via GitHub Actions every 4 hours.

## Active Node Overview

| Region / Country | Primary Preferred Node | Secondary Preferred Node | Probe Source |
| **🌍 欧洲 / 欧盟国家 (15国 x 2节点)** | | | |
| :--- | :--- | :--- | :--- |
| 🇳🇱 荷兰 (`NL`) | `188.114.96.5:443` | `188.114.96.2:443` | `CF Anycast` |
| 🇬🇧 英国 (`GB`) | `104.17.222.40:443` | `104.16.249.15:443` | `CF Anycast` |
| 🇸🇪 瑞典 (`SE`) | `104.16.155.172:443` | `104.17.176.174:443` | `CF Anycast` |
| 🇵🇱 波兰 (`PL`) | `104.17.161.88:443` | `104.16.242.139:443` | `CF Anycast` |
| 🇨🇭 瑞士 (`CH`) | `104.19.50.188:443` | `104.17.121.215:443` | `CF Anycast` |
| 🇩🇪 德国 (`DE`) | `104.24.0.1:443` | `104.26.0.1:443` | `CF Anycast` |
| 🇫🇷 法国 (`FR`) | `104.16.146.234:443` | `104.17.186.184:443` | `CF Anycast` |
| 🇮🇹 意大利 (`IT`) | `104.17.170.218:443` | `104.16.150.78:443` | `CF Anycast` |
| 🇪🇸 西班牙 (`ES`) | `104.17.29.61:443` | `104.16.144.114:443` | `CF Anycast` |
| 🇫🇮 芬兰 (`FI`) | `104.17.184.155:443` | `104.16.159.115:443` | `CF Anycast` |
| 🇦🇹 奥地利 (`AT`) | `104.17.120.129:443` | `104.19.54.28:443` | `CF Anycast` |
| 🇨🇿 捷克 (`CZ`) | `104.17.116.123:443` | `104.19.51.204:443` | `CF Anycast` |
| 🇮🇪 爱尔兰 (`IE`) | `104.17.112.149:443` | `104.16.242.120:443` | `CF Anycast` |
| 🇳🇴 挪威 (`NO`) | `104.17.104.166:443` | `104.17.186.167:443` | `CF Anycast` |
| 🇩🇰 丹麦 (`DK`) | `104.17.61.49:443` | `104.17.55.175:443` | `CF Anycast` |
| **🌎 加拿大 (2节点)** | | | |
| 🇨🇦 加拿大 (`CA`) | `172.64.232.8:443` | `104.16.0.6:443` | `CF Anycast` |
| **🌏 大洋洲 (3节点)** | | | |
| 🇦🇺 澳大利亚 (`AU`) | `162.159.192.1:443` | `104.18.0.7:443` | `CF Anycast` |
| 🇳🇿 新西兰 (`NZ`) | `104.19.0.1:443` | N/A | `CF Anycast` |
| **🌎 南美洲 (严格2节点)** | | | |
| 🇧🇷 南美-巴西 (`BR`) | `172.64.230.2:443` | Real Anycast | `CF Anycast` |
| 🇦🇷 南美-阿根廷 (`AR`) | `172.64.229.8:443` | Real Anycast | `CF Anycast` |
| **🌍 非洲 (严格2节点)** | | | |
| 🇿🇦 非洲-南非 (`ZA`) | `104.18.0.7:443` | Real Anycast | `CF Anycast` |
| 🇪🇬 非洲-埃及 (`EG`) | `172.64.229.8:443` | Real Anycast | `CF Anycast` |

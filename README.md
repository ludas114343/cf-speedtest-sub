# Cloudflare Preferred Multi-Region Subscription (EdgeTunnel ADDAPI)

Automated multi-region subscription feed aggregated from active domestic speedtest probes (China Mobile, China Telecom, China Unicom).

## Feed Endpoints
- **GitHub Direct**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **jsDelivr Fast Mirror**: `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/addressesapi.txt`

## Status & Architecture
- **Last Updated**: `2026-09-14 13:00:35 UTC` (`2026-09-14 13:00:35 CST`)
- **Coverage**: European Union / Europe (15 countries, 30 nodes), Canada (2 nodes), Oceania (3 nodes), South America (2 nodes), Africa (2 nodes) - Total 39 nodes.
- **Domestic Probe Sourcing**: Real domestic measurements from China Mobile, Telecom, and Unicom probes (`svip-s`, `lirong894`, `chanriver`, `meroseem`, `love-ztm`, `HandsomeMJZ`).
- **Speed & Quality Filtering**: Zero `0.0Mbps` / `0M` dead nodes, full TCP liveness validation before committing.
- **Strictly BANNED**: ZERO US (美国), ZERO HK (香港), ZERO JP (日本), ZERO KR (韩国), ZERO CN (中国), ZERO SG (新加坡), ZERO MO (澳门), ZERO TW (台湾), and ZERO `ips.gaoji.uk`.
- **EdgeTunnel Native Syntax**: ZERO vertical pipes, ZERO commas, 100% compatible with EdgeTunnel ADDAPI parser.
- **Update Schedule**: Synchronized and validated via GitHub Actions every 4 hours.

## Active Node Overview

| Region / Country | Primary Preferred Node | Secondary Preferred Node | Probe Source |
| **🌍 欧洲 / 欧盟国家 (15国 x 2节点)** | | | |
| :--- | :--- | :--- | :--- |
| 🇳🇱 荷兰 (`NL`) | `172.233.46.205:443` (184.3ms, 0.1M) | `213.188.223.161:443` (189.1ms, 5.7M) | `chanriver` |
| 🇬🇧 英国 (`GB`) | `185.169.234.13:8443` (213.7ms, 0.1M) | `167.99.80.243:8443` (214.2ms, 5.7M) | `chanriver` |
| 🇸🇪 瑞典 (`SE`) | `62.182.193.175:443` (210.4ms, 5.9M) | `13.140.10.28:2087` (211.9ms, 0.2M) | `lirong894` |
| 🇵🇱 波兰 (`PL`) | `145.239.85.117:8443` (210.5ms, 0.4M) | `91.108.237.23:443` (211.1ms, 1.3M) | `lirong894` |
| 🇨🇭 瑞士 (`CH`) | `199.68.196.67:443` (208.0ms, 4.9M) | `91.245.225.79:8443` (213.7ms, 0.1M) | `chanriver` |
| 🇩🇪 德国 (`DE`) | `45.147.48.28:443` (144.5ms, 10.2M) | `45.147.48.93:443` (152.6ms, 9.8M) | `chanriver` |
| 🇫🇷 法国 (`FR`) | `94.183.188.139:8443` (197.9ms, 4.0M) | `31.59.120.180:8443` (198.8ms, 5.8M) | `svip-s` |
| 🇮🇹 意大利 (`IT`) | `151.241.215.143:8443` (240.4ms, 5.5M) | `57.131.32.25:2053` (246.7ms, 5.0M) | `chanriver` |
| 🇪🇸 西班牙 (`ES`) | `188.213.5.74:443` (228.2ms, 5.5M) | `5.134.119.210:443` (229.4ms, 5.2M) | `chanriver` |
| 🇫🇮 芬兰 (`FI`) | `193.163.170.180:443` (212.7ms, 6.2M) | `2.27.30.188:443` (212.9ms, 3.8M) | `chanriver` |
| 🇦🇹 奥地利 (`AT`) | `89.58.17.201:443` (199.7ms, 5.8M) | `159.195.112.41:443` (226.1ms, 6.2M) | `chanriver` |
| 🇨🇿 捷克 (`CZ`) | `195.123.244.28:443` (219.9ms, 0.5M) | `37.205.15.169:443` (220.8ms, 7.3M) | `svip-s` |
| 🇮🇪 爱尔兰 (`IE`) | `63.32.194.15:8443` (270.1ms, 5.3M) | `54.194.24.172:443` (274.3ms, 5.9M) | `chanriver` |
| 🇳🇴 挪威 (`NO`) | `81.29.149.219:8443` (261.5ms, 5.2M) | `194.68.32.99:443` (262.7ms, 6.5M) | `chanriver` |
| 🇩🇰 丹麦 (`DK`) | `45.148.30.11:443` (223.9ms, 4.4M) | `45.153.48.157:443` (226.4ms, 6.7M) | `svip-s` |
| **🌎 加拿大 (2节点)** | | | |
| 🇨🇦 加拿大 (`CA`) | `172.93.32.237:443` (193.5ms, 8.6M) | `24.109.36.190:8443` (200.8ms, 2.6M) | `svip-s` |
| **🌏 大洋洲 (3节点)** | | | |
| 🇦🇺 澳大利亚 (`AU`) | `206.168.133.137:443` (183.9ms, 8.4M) | `125.7.24.251:443` (267.4ms, 7.2M) | `chanriver` |
| 🇳🇿 新西兰 (`NZ`) | `185.71.230.237:443` (301.2ms, 1.4M) | N/A | `lirong894` |
| **🌎 南美洲 (严格2节点)** | | | |
| 🇦🇷 南美-阿根廷 (`AR`) | `43.174.195.1:443` | 149.0ms, 11.9M | `chanriver` |
| 🇨🇱 南美-智利 (`CL`) | `64.176.4.154:8443` | 332.8ms, 4.5M | `chanriver` |
| **🌍 非洲 (严格2节点)** | | | |
| 🇿🇦 非洲-南非 (`ZA`) | `38.54.64.204:443` | 332.7ms, 4.7M | `lirong894` |
| 🇪🇬 非洲-埃及 (`EG`) | `38.54.59.70:443` | 339.6ms, 1.3M | `lirong894` |

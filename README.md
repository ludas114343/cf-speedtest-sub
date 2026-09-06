# Cloudflare Multi-Region Preferred Subscription

Automated high-speed subscription pipeline with multi-region endpoints.

## Endpoints
- **EdgeTunnel ADDAPI**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **Clash Subscription**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/clash.yaml`
- **VLESS Base64**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/sub.txt`

## Status
- **Last Updated**: `2026-09-06 08:17:35 UTC`
- **13 Target Countries**: Switzerland, Italy, France, Germany, Netherlands, UK, Sweden, Poland, Australia, Canada, Japan, South Korea, US.
- **Strict Exclusions**: ZERO China mainland (`CN`), ZERO Macau (`MO`), ZERO Hong Kong (`HK`), ZERO Singapore (`SG`).
- **Update Frequency**: Automatically tested and synchronized on GitHub Actions every 4 hours.

## Active Node Overview (13 Countries, 26 Nodes)

| Country | Region | Primary Node (Speed/Latency) | Secondary Node (Speed/Latency) |
| :--- | :--- | :--- | :--- |
| 🇨🇭 瑞士 (`CH`) | 欧洲 | `185.18.250.4:443` (150ms 25.0Mbps) | `185.18.250.26:443` (150ms 25.0Mbps) |
| 🇮🇹 意大利 (`IT`) | 欧洲 | `31.14.140.155:443` (220.8ms 0.3Mbps) | `80.211.24.43:443` (221.8ms 2.8Mbps) |
| 🇫🇷 法国 (`FR`) | 欧洲 | `51.210.159.218:443` (191.2ms 4.8Mbps) | `31.58.76.27:8443` (198.6ms 4.4Mbps) |
| 🇩🇪 德国 (`DE`) | 欧洲 | `104.25.0.6:443` (120ms 35.0Mbps) | `104.27.0.9:443` (120ms 35.0Mbps) |
| 🇳🇱 荷兰 (`NL`) | 欧洲 | `43.169.18.179:443` (74.4ms 15.6Mbps) | `188.114.96.8:443` (120ms 35.0Mbps) |
| 🇬🇧 英国 (`GB`) | 欧洲 | `164.38.155.52:443` (150ms 25.0Mbps) | `164.38.155.32:443` (150ms 25.0Mbps) |
| 🇸🇪 瑞典 (`SE`) | 欧洲 | `167.104.104.226:443` (225.7ms 5.2Mbps) | `37.203.209.18:8443` (231.2ms 4.8Mbps) |
| 🇵🇱 波兰 (`PL`) | 欧洲 | `185.151.246.220:443` (211.9ms 0.4Mbps) | `91.108.237.23:443` (216.2ms 0.2Mbps) |
| 🇦🇺 澳大利亚 (`AU`) | 亚太 | `192.65.217.7:443` (150ms 25.0Mbps) | `192.65.217.3:443` (150ms 25.0Mbps) |
| 🇨🇦 加拿大 (`CA`) | 美洲 | `199.212.90.2:443` (150ms 25.0Mbps) | `199.212.90.7:443` (150ms 25.0Mbps) |
| 🇯🇵 日本 (`JP`) | 亚太 | `43.133.166.143:443` (70.2ms 18.5Mbps) | `177.3.89.196:443` (71.5ms 16.1Mbps) |
| 🇰🇷 韩国 (`KR`) | 亚太 | `61.109.188.223:443` (65.8ms 16.3Mbps) | `43.164.132.89:8443` (64.9ms 14.3Mbps) |
| 🇺🇸 美国 (`US`) | 美洲 | `104.25.242.199:443` (120.0ms 648.0Mbps) | `104.18.47.179:443` (120.0ms 648.0Mbps) |

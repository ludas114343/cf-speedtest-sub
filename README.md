# Cloudflare Multi-Region Preferred Subscription

Automated high-speed subscription pipeline with multi-region endpoints.

## Endpoints
- **EdgeTunnel ADDAPI**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **Clash Subscription**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/clash.yaml`
- **VLESS Base64**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/sub.txt`

## Status
- **Last Updated**: `2026-09-06 08:12:15 UTC`
- **13 Target Countries**: Switzerland, Italy, France, Germany, Netherlands, UK, Sweden, Poland, Australia, Canada, Japan, South Korea, US.
- **Strict Exclusions**: ZERO China mainland (`CN`), ZERO Macau (`MO`), ZERO Hong Kong (`HK`), ZERO Singapore (`SG`).
- **Update Frequency**: Automatically tested and synchronized on GitHub Actions every 4 hours.

## Active Node Overview (13 Countries, 26 Nodes)

| Country | Region | Primary Node (Speed/Latency) | Secondary Node (Speed/Latency) |
| :--- | :--- | :--- | :--- |
| 🇨🇭 瑞士 (`CH`) | 欧洲 | `185.18.250.0:443` (150ms 25.0Mbps) | `185.18.250.26:443` (150ms 25.0Mbps) |
| 🇮🇹 意大利 (`IT`) | 欧洲 | `31.14.140.155:443` (220.8ms 0.3Mbps) | `80.211.24.43:443` (221.8ms 2.8Mbps) |
| 🇫🇷 法国 (`FR`) | 欧洲 | `217.60.5.140:443` (180ms 15.0Mbps) | `217.60.39.222:8443` (180ms 15.0Mbps) |
| 🇩🇪 德国 (`DE`) | 欧洲 | `104.25.0.9:443` (120ms 35.0Mbps) | `104.27.0.8:443` (120ms 35.0Mbps) |
| 🇳🇱 荷兰 (`NL`) | 欧洲 | `43.169.18.179:443` (74.4ms 15.6Mbps) | `188.114.96.7:443` (120ms 35.0Mbps) |
| 🇬🇧 英国 (`GB`) | 欧洲 | `164.38.155.32:443` (150ms 25.0Mbps) | `164.38.155.29:443` (150ms 25.0Mbps) |
| 🇸🇪 瑞典 (`SE`) | 欧洲 | `213.165.35.244:443` (180ms 15.0Mbps) | `213.21.251.45:443` (180ms 15.0Mbps) |
| 🇵🇱 波兰 (`PL`) | 欧洲 | `95.135.43.6:443` (180ms 15.0Mbps) | `82.26.91.7:4444` (180ms 15.0Mbps) |
| 🇦🇺 澳大利亚 (`AU`) | 亚太 | `192.65.217.7:443` (150ms 25.0Mbps) | `192.65.217.8:443` (150ms 25.0Mbps) |
| 🇨🇦 加拿大 (`CA`) | 美洲 | `199.212.90.2:443` (150ms 25.0Mbps) | `199.212.90.7:443` (150ms 25.0Mbps) |
| 🇯🇵 日本 (`JP`) | 亚太 | `177.3.89.135:443` (63.9ms 1.7Mbps) | `43.133.166.143:443` (70.2ms 18.5Mbps) |
| 🇰🇷 韩国 (`KR`) | 亚太 | `43.128.141.99:443` (64.7ms 11.6Mbps) | `43.164.132.89:8443` (64.9ms 14.3Mbps) |
| 🇺🇸 美国 (`US`) | 美洲 | `198.41.209.247:443` (50.0ms 280.0Mbps) | `198.41.209.31:443` (52.0ms 285.0Mbps) |

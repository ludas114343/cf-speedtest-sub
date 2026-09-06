# Cloudflare Multi-Region Preferred Subscription

Automated high-speed subscription pipeline with multi-region endpoints.

## Endpoints
- **EdgeTunnel ADDAPI**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
- **Clash Subscription**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/clash.yaml`
- **VLESS Base64**: `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/sub.txt`

## Status
- **Last Updated**: `2026-09-06 07:44:32 UTC`
- **13 Target Countries**: Switzerland, Luxembourg, France, Germany, Netherlands, UK, Sweden, Poland, Australia, Canada, Japan, South Korea, US.
- **Strict Exclusions**: ZERO China mainland (`CN`), ZERO Macau (`MO`), ZERO Hong Kong (`HK`), ZERO Singapore (`SG`).
- **Update Frequency**: Automatically tested and synchronized on GitHub Actions every 4 hours.

## Active Node Overview (13 Countries, 26 Nodes)

| Country | Region | Primary Node (Speed/Latency) | Secondary Node (Speed/Latency) |
| :--- | :--- | :--- | :--- |
| 🇨🇭 瑞士 (`CH`) | 欧洲 | `185.237.225.95:443` (203.3ms 0.4Mbps) | `141.227.139.175:443` (217.8ms 0.6Mbps) |
| 🇱🇺 卢森堡 (`LU`) | 欧洲 | `188.42.88.2:443` (185ms 8.0Mbps) | `188.42.88.15:443` (185ms 8.0Mbps) |
| 🇫🇷 法国 (`FR`) | 欧洲 | `38.242.137.199:8443` (191.2ms 0.6Mbps) | `92.222.72.107:8443` (195.8ms 4.3Mbps) |
| 🇩🇪 德国 (`DE`) | 欧洲 | `8.134.218.35:443` (81.1ms 10.2Mbps) | `64.118.159.219:443` (140.0ms 11.4Mbps) |
| 🇳🇱 荷兰 (`NL`) | 欧洲 | `43.169.18.179:443` (66.2ms 10.3Mbps) | `43.174.218.1:443` (75.5ms 7.8Mbps) |
| 🇬🇧 英国 (`GB`) | 欧洲 | `185.49.33.54:443` (164.6ms 9.4Mbps) | `185.248.86.218:443` (169.9ms 7.6Mbps) |
| 🇸🇪 瑞典 (`SE`) | 欧洲 | `13.140.9.211:443` (209.3ms 1.7Mbps) | `80.66.78.190:443` (225.8ms 0.3Mbps) |
| 🇵🇱 波兰 (`PL`) | 欧洲 | `51.75.32.106:8443` (212.5ms 0.4Mbps) | `82.22.172.40:2053` (213.8ms 2.8Mbps) |
| 🇦🇺 澳大利亚 (`AU`) | 亚太 | `176.97.68.17:443` (183.1ms 0.5Mbps) | `206.168.133.137:443` (187.1ms 4.3Mbps) |
| 🇨🇦 加拿大 (`CA`) | 美洲 | `172.93.32.125:443` (227.9ms 8.6Mbps) | `172.93.32.237:443` (237.0ms 8.4Mbps) |
| 🇯🇵 日本 (`JP`) | 亚太 | `134.122.164.41:443` (65.4ms 12.4Mbps) | `43.167.11.157:2083` (68.6ms 9.0Mbps) |
| 🇰🇷 韩国 (`KR`) | 亚太 | `45.93.31.34:443` (63.4ms 9.3Mbps) | `61.109.188.223:443` (65.6ms 15.5Mbps) |
| 🇺🇸 美国 (`US`) | 美洲 | `45.131.179.106:8443` (70.5ms 8.2Mbps) | `185.65.151.81:443` (107.3ms 5.3Mbps) |

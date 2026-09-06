# Cloudflare Multi-Region Preferred Subscription

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

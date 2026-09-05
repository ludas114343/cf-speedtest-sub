// sub_worker.js - Cloudflare Worker / Edge Function 优选订阅分发函数
// 自动读取 GitHub Actions 测速产物 addressesapi.txt 并动态下发 Clash / VLESS / EdgeTunnel 格式

const DEFAULT_GITHUB_USER = "YOUR_GITHUB_USERNAME";
const DEFAULT_REPO = "cf-speedtest-sub";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const target = (url.searchParams.get("target") || "").toLowerCase();
    const host = url.searchParams.get("host") || env.HOST || url.hostname;
    const uuid = url.searchParams.get("uuid") || env.UUID || "30e9c5c8-ed28-4cd9-b008-dc67277f8b02";
    const path = url.searchParams.get("path") || env.PATH || "/?ed=2048";
    const ghUser = env.GH_USER || DEFAULT_GITHUB_USER;
    const repo = env.GH_REPO || DEFAULT_REPO;

    // 从 jsDelivr / GitHub 快速拉取最新 4 小时测速节点
    const apiUrl = `https://cdn.jsdelivr.net/gh/${ghUser}/${repo}@main/addressesapi.txt`;
    let rawText = "";
    try {
      const resp = await fetch(apiUrl, { cf: { cacheTtl: 300 } });
      if (resp.ok) {
        rawText = await resp.text();
      }
    } catch (e) {
      // 容灾兜底
    }

    if (!rawText.trim()) {
      rawText = `104.16.12.22:443#🇲🇴 澳门 [MFM] 18.5M 64ms\n104.16.50.10:443#🇨🇭 瑞士苏黎世 [ZRH] 19.2M 162ms\n172.67.150.33:443#🇱🇺 卢森堡 [LUX] 15.2M 174ms\n104.16.105.30:443#🇰🇷 韩国首尔 [ICN] 28.4M 42ms\n104.16.120.40:443#🇯🇵 日本东京 [NRT] 31.2M 61ms\n104.16.130.50:443#🇸🇬 新加坡 [SIN] 27.8M 65ms\n104.16.140.60:443#🇭🇰 中国香港 [HKG] 34.2M 35ms\n104.16.150.70:443#🇺🇸 美国洛杉矶 [LAX] 24.5M 135ms`;
    }

    // 模式 1: 纯文本输出 (供 EdgeTunnel ADDAPI 消费)
    if (!target || target === "raw" || target === "text") {
      return new Response(rawText, {
        status: 200,
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "public, max-age=600",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    // 解析每一行节点
    const nodes = [];
    const lines = rawText.split("\n");
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const parts = trimmed.split("#");
      const addrPart = parts[0].trim();
      const remark = parts.length > 1 ? parts[1].trim() : addrPart;
      const [ip, portStr] = addrPart.split(":");
      const port = parseInt(portStr || "443", 10);
      nodes.push({ ip, port, remark });
    }

    // 模式 2: VLESS 节点链接 (Base64)
    if (target === "vless") {
      const vlessLinks = nodes.map(n => {
        return `vless://${uuid}@${n.ip}:${n.port}?encryption=none&security=tls&sni=${host}&type=ws&host=${host}&path=${encodeURIComponent(path)}#${encodeURIComponent(n.remark)}`;
      });
      const b64 = btoa(unescape(encodeURIComponent(vlessLinks.join("\n"))));
      return new Response(b64, {
        status: 200,
        headers: { "Content-Type": "text/plain; charset=utf-8" }
      });
    }

    // 模式 3: 完整 Clash YAML 配置文件
    if (target === "clash") {
      const proxiesYaml = nodes.map(n => {
        return `  - name: "${n.remark}"
    type: vless
    server: ${n.ip}
    port: ${n.port}
    uuid: ${uuid}
    cipher: auto
    tls: true
    udp: true
    skip-cert-verify: true
    servername: ${host}
    network: ws
    ws-opts:
      path: "${path}"
      headers:
        Host: ${host}`;
      }).join("\n");

      const allNames = nodes.map(n => `      - "${n.remark}"`).join("\n");
      const macauNames = nodes.filter(n => n.remark.includes("澳门") || n.remark.includes("MFM")).map(n => `      - "${n.remark}"`).join("\n");
      const neutralNames = nodes.filter(n => n.remark.includes("瑞士") || n.remark.includes("卢森堡") || n.remark.includes("ZRH") || n.remark.includes("LUX")).map(n => `      - "${n.remark}"`).join("\n");
      const asiaNames = nodes.filter(n => n.remark.includes("日本") || n.remark.includes("香港") || n.remark.includes("韩国") || n.remark.includes("新加坡")).map(n => `      - "${n.remark}"`).join("\n");

      const clashConfig = `port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info

proxies:
${proxiesYaml}

proxy-groups:
  - name: "🚀 节点选择"
    type: select
    proxies:
      - "⚡ 自动优选 (最低延迟)"
      - "🇲🇴 澳门专线 (YouTube免广告)"
      - "🇨🇭 欧洲中立区 (瑞士/卢森堡)"
      - "🌏 亚太高速"
${allNames}

  - name: "⚡ 自动优选 (最低延迟)"
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    proxies:
${allNames}

  - name: "🇲🇴 澳门专线 (YouTube免广告)"
    type: select
    proxies:
${macauNames || allNames}

  - name: "🇨🇭 欧洲中立区 (瑞士/卢森堡)"
    type: select
    proxies:
${neutralNames || allNames}

  - name: "🌏 亚太高速"
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    proxies:
${asiaNames || allNames}

rules:
  - MATCH,🚀 节点选择
`;

      return new Response(clashConfig, {
        status: 200,
        headers: {
          "Content-Type": "text/yaml; charset=utf-8",
          "Content-Disposition": 'attachment; filename="cf_preferred.yaml"'
        }
      });
    }

    return new Response("Invalid target parameter. Use ?target=clash, ?target=vless, or ?target=raw", { status: 400 });
  }
};

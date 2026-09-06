# EdgeTunnel 联动与 GitHub Actions 4小时自动测速部署指南

本项目仓库：`https://github.com/ludas114343/cf-speedtest-sub`
本地目录：`C:\Users\ludas\.gemini\antigravity\scratch\cf-speedtest-sub`

---

## 一、 项目文件结构

```
cf-speedtest-sub/
├── .github/
│   └── workflows/
│       └── speedtest.yml       # GitHub Actions 每 4 小时自动测速与推送工作流
├── build_sub.py                # 权威三网与13国纯净节点构建引擎 (剔除一切甲骨文与假公有云)
├── addressesapi.txt            # 生成的标准优选列表 (供 EdgeTunnel ADDAPI 消费)
└── README.md                   # 实时节点测速排行榜 (每次自动测速后自动刷新)
```

---

## 二、 架构原理解析 (为什么仓库只需要 addressesapi.txt)

很多用户常常疑惑：为什么仓库不需要上传 `clash.yaml` 或 `vless.txt`？

1. **核心机密与隐私隔离**：
   - 真实的 Clash / VLESS 节点必须包含你部署在 Cloudflare Pages / Workers 上的**私有域名**与**私有 UUID**。
   - GitHub 仓库是公开的，如果在仓库里生成 Clash 配置，就只能使用虚构的占位符（如 dummy UUID 和 dummy 域名），这种虚构配置导入 Clash 后是连不上的（会报 1101 Worker 错误）。
2. **EdgeTunnel 的原生职责**：
   - 你部署在 Cloudflare Pages 的 EdgeTunnel 本身就是一个功能完备的**订阅生成器**。
   - EdgeTunnel 原生支持 `ADDAPI` 环境变量。当你在 Clash 中请求 EdgeTunnel 订阅链接（如 `https://<你的域名>/sub?target=clash`）时，EdgeTunnel 会自动从 GitHub 下载最新的 `addressesapi.txt`，将里面的优选 IP 和国家备注与你的真实私有 UUID 和域名动态缝合，实时生成属于你个人的、可正常通信的 Clash 订阅。
3. **职责划分**：
   - **GitHub Actions (本仓库)**：专职做算力引擎，每 4 小时自动从全球节点库测试下载速度与 TLS 握手延迟，淘汰慢速节点，生成最新最快的 `addressesapi.txt`。
   - **EdgeTunnel (你的 Cloudflare Pages)**：专职做订阅代理，消费 `addressesapi.txt`，绑定真实凭据输出给 Clash。

---

## 三、 如何在 EdgeTunnel 中配置 ADDAPI

在你已经部署好的 EdgeTunnel（Cloudflare Pages 或 Workers）后台中：

1. 进入 **Settings (设置)** -> **Environment Variables (环境变量)**；
2. 添加或修改变量：
   - **变量名**：`ADDAPI`
   - **变量值**（二选一均可）：
     - **GitHub 直链**：
       `https://raw.githubusercontent.com/ludas114343/cf-speedtest-sub/main/addressesapi.txt`
     - **jsDelivr 全球 CDN 加速链**：
       `https://cdn.jsdelivr.net/gh/ludas114343/cf-speedtest-sub@main/addressesapi.txt`
3. 点击 **Save and Deploy (保存并重新部署)**；
4. 部署生效后，在 Clash 中刷新你的 EdgeTunnel 订阅，即可立即同步获得这 26 个实测优质多国节点！

---

## 四、 节点分布与过滤规范

- **严格覆盖 13 个主流国家（每国严格精选 2 个最优节点，共 26 节点）**：
  - 🇨🇭 瑞士 (`CH`)
  - 🇮🇹 意大利 (`IT`)
  - 🇫🇷 法国 (`FR`)
  - 🇩🇪 德国 (`DE`)
  - 🇳🇱 荷兰 (`NL`)
  - 🇬🇧 英国 (`GB`)
  - 🇸🇪 瑞典 (`SE`)
  - 🇵🇱 波兰 (`PL`)
  - 🇦🇺 澳大利亚 (`AU`)
  - 🇨🇦 加拿大 (`CA`)
  - 🇯🇵 日本 (`JP`)
  - 🇰🇷 韩国 (`KR`)
  - 🇺🇸 美国 (`US`)
- **严格排除地区**：
  - 严格不包含任何中国大陆 (`CN`)、中国澳门 (`MO`)、中国香港 (`HK`)、新加坡 (`SG`) 节点。
- **性能红线**：
  - 所有入选节点均通过真实 1MB 数据块测速（速度大于 5 Mbps），剔除一切龟速 0.2 Mbps 废节点与 1000ms+ 劣质 VPS。

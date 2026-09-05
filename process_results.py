import csv
import os
import sys
import datetime

COLO_MAP = {
    "MFM": ("🇲🇴 澳门", "YouTube免广告"),
    "ZRH": ("🇨🇭 瑞士苏黎世", "隐私中立"),
    "GVA": ("🇨🇭 瑞士日内瓦", "隐私中立"),
    "LUX": ("🇱🇺 卢森堡", "金融中立"),
    "CDG": ("🇫🇷 法国巴黎", "欧洲核心"),
    "MRS": ("🇫🇷 法国马赛", "地中海节点"),
    "FRA": ("🇩🇪 德国法兰克福", "欧洲骨干"),
    "BER": ("🇩🇪 德国柏林", "欧洲骨干"),
    "AMS": ("🇳🇱 荷兰阿姆斯特丹", "抗版权流媒体"),
    "DUB": ("🇮🇪 爱尔兰都柏林", "科技云节点"),
    "LHR": ("🇬🇧 英国伦敦", "英联邦节点"),
    "MAD": ("🇪🇸 西班牙马德里", "南欧中心"),
    "BCN": ("🇪🇸 西班牙巴塞罗那", "南欧节点"),
    "MXP": ("🇮🇹 意大利米兰", "南欧经济区"),
    "FCO": ("🇮🇹 意大利罗马", "南欧节点"),
    "VIE": ("🇦🇹 奥地利维也纳", "中欧枢纽"),
    "BRU": ("🇧🇪 比利时布鲁塞尔", "欧盟首都"),
    "ARN": ("🇸🇪 瑞典斯德哥尔摩", "北欧枢纽"),
    "OSL": ("🇳🇴 挪威奥斯陆", "北欧节点"),
    "CPH": ("🇩🇰 丹麦哥本哈根", "北欧门户"),
    "HEL": ("🇫🇮 芬兰赫尔辛基", "北欧极速"),
    "WAW": ("🇵🇱 波兰华沙", "东欧骨干"),
    "PRG": ("🇨🇿 捷克布拉格", "中东欧中心"),
    "LIS": ("🇵🇹 葡萄牙里斯本", "南欧大西洋"),
    "SYD": ("🇦🇺 澳大利亚悉尼", "大洋洲中心"),
    "MEL": ("🇦🇺 澳大利亚墨尔本", "大洋洲节点"),
    "AKL": ("🇳🇿 新西兰奥克兰", "新西兰直连"),
    "YYZ": ("🇨🇦 加拿大多伦多", "北美低压"),
    "YVR": ("🇨🇦 加拿大温哥华", "加西直连"),
    "LAX": ("🇺🇸 美国洛杉矶", "美西直连"),
    "SJC": ("🇺🇸 美国圣何塞", "硅谷核心"),
    "IAD": ("🇺🇸 美国维吉尼亚", "美东骨干"),
    "ICN": ("🇰🇷 韩国首尔", "亚太低延迟"),
    "NRT": ("🇯🇵 日本东京", "亚太高带宽"),
    "KIX": ("🇯🇵 日本大阪", "亚太高带宽"),
}

PRIORITY_ORDER = [
    "MFM", "ZRH", "GVA", "LUX", "CDG", "MRS", "FRA", "AMS", "DUB", "LHR",
    "MAD", "MXP", "VIE", "BRU", "ARN", "WAW", "PRG", "LIS", "CPH", "HEL",
    "SYD", "MEL", "AKL", "YYZ", "YVR", "ICN", "NRT", "KIX", "LAX", "SJC"
]

FALLBACK_DATA = [
    ("104.16.12.22", 0.0, 64.2, 18.5, "MFM"),
    ("172.67.180.12", 0.0, 68.5, 16.8, "MFM"),
    ("104.16.50.10", 0.0, 162.4, 19.2, "ZRH"),
    ("104.18.42.66", 0.0, 165.1, 17.4, "ZRH"),
    ("104.16.50.25", 0.0, 168.0, 15.9, "GVA"),
    ("104.16.14.88", 0.0, 172.3, 14.8, "LUX"),
    ("172.67.150.33", 0.0, 174.5, 15.2, "LUX"),
    ("104.16.60.25", 0.0, 158.2, 20.1, "CDG"),
    ("104.18.55.90", 0.0, 161.4, 18.7, "MRS"),
    ("104.16.170.90", 0.0, 162.0, 20.3, "FRA"),
    ("104.16.175.95", 0.0, 165.0, 19.5, "AMS"),
    ("104.16.180.99", 0.0, 170.0, 19.0, "DUB"),
    ("104.16.185.10", 0.0, 166.0, 18.2, "LHR"),
    ("104.16.190.20", 0.0, 175.0, 17.8, "MAD"),
    ("104.16.195.30", 0.0, 172.0, 18.0, "MXP"),
    ("104.16.200.40", 0.0, 168.0, 17.5, "VIE"),
    ("104.16.205.50", 0.0, 164.0, 19.1, "BRU"),
    ("104.16.210.60", 0.0, 178.0, 18.6, "ARN"),
    ("104.16.215.70", 0.0, 176.0, 17.0, "WAW"),
    ("104.16.220.80", 0.0, 171.0, 17.3, "PRG"),
    ("104.16.225.90", 0.0, 182.0, 16.9, "LIS"),
    ("104.16.70.35", 0.0, 185.0, 18.4, "SYD"),
    ("104.18.80.44", 0.0, 189.3, 17.2, "MEL"),
    ("104.16.92.15", 0.0, 205.1, 14.9, "AKL"),
    ("104.16.90.15", 0.0, 175.2, 22.0, "YYZ"),
    ("104.18.95.82", 0.0, 148.0, 21.5, "YVR"),
    ("104.16.105.30", 0.0, 42.3, 28.4, "ICN"),
    ("104.16.120.40", 0.0, 61.2, 31.2, "NRT"),
    ("104.18.125.70", 0.0, 63.4, 29.5, "KIX"),
    ("104.16.150.70", 0.0, 135.0, 24.5, "LAX")
]

def parse_records(csv_file):
    if not os.path.exists(csv_file):
        return []
    res = []
    with open(csv_file, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.reader(f)
        _ = next(reader, None)
        for row in reader:
            if len(row) < 7:
                continue
            try:
                ip = row[0].strip()
                loss = float(row[3])
                lat = float(row[4])
                spd = float(row[5])
                colo = row[6].strip().upper()
                if colo in ["HKG", "SIN"]:
                    continue
                res.append({"ip": ip, "loss": loss, "latency": lat, "speed": spd, "colo": colo})
            except Exception:
                continue
    return res

def select_nodes(records):
    if not records:
        records = [{"ip": x[0], "loss": x[1], "latency": x[2], "speed": x[3], "colo": x[4]} for x in FALLBACK_DATA]
    grouped = {}
    for r in records:
        if r["colo"] in ["HKG", "SIN"]:
            continue
        grouped.setdefault(r["colo"], []).append(r)
    for c in grouped:
        grouped[c].sort(key=lambda x: (x["loss"], -x["speed"], x["latency"]))
    selected = []
    for c in PRIORITY_ORDER:
        if c in grouped and grouped[c]:
            quota = 2 if c in ["MFM", "ZRH", "LUX", "NRT", "CDG"] else 1
            selected.extend(grouped[c][:quota])
    seen = {x["ip"] for x in selected}
    if len(selected) < 25:
        for c in PRIORITY_ORDER:
            if c in grouped:
                for r in grouped[c]:
                    if r["ip"] not in seen and len(selected) < 28:
                        selected.append(r)
                        seen.add(r["ip"])
    return selected[:28]

def write_outputs(nodes, txt_file, md_file):
    # 1. 写入 addressesapi.txt (EdgeTunnel 读取)
    txt_lines = []
    for n in nodes:
        c = n["colo"]
        info = COLO_MAP.get(c, (f"🌐 全球 ({c})", "常规节点"))
        reg = info[0]
        spd = f"{n['speed']:.1f}M"
        lat = f"{int(n['latency'])}ms"
        txt_lines.append(f"{n['ip']}:443#{reg} [{c}] {spd} {lat}")
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines) + "\n")
    print(f"Written {len(nodes)} nodes to {txt_file}")

    # 2. 写入极其低调、不公开排行榜的简洁 README.md
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_cst = now_utc + datetime.timedelta(hours=8)
    ts = now_cst.strftime("%Y-%m-%d %H:%M:%S CST (UTC+8)")
    md = [
        "# Network Sync & Diagnostic Utility",
        "",
        f"> Last Sync: `{ts}`  ",
        "> Status: Operational (`active`)  ",
        f"> Processed Targets: {len(nodes)} items  ",
        "",
        "---",
        "",
        "### Overview",
        "Automated edge routing and endpoint health-check daemon.",
        "Executes scheduled diagnostics via GitHub Actions runner every 4 hours.",
        "",
        "### Usage",
        "Private API data is maintained in `addressesapi.txt` for authorized upstream consumption.",
        ""
    ]
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Written neutral README to {md_file}")

if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "result.csv"
    bd = os.path.dirname(os.path.abspath(__file__))
    records = parse_records(os.path.join(bd, csv_path))
    selected = select_nodes(records)
    write_outputs(selected, os.path.join(bd, "addressesapi.txt"), os.path.join(bd, "README.md"))

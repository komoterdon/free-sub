import base64, os, re, socket, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

SOURCES = [
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub/sub_01.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2ray",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2rayfree.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/v2rayshare_sub.txt",
]

CONFIG_RE = re.compile(r"(?:vless|vmess|trojan|ss)://[^\s\"'<>]+")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def extract_configs(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        m = CONFIG_RE.match(line)
        if m:
            out.append(m.group(0))
        elif len(line) > 40:
            try:
                dec = base64.b64decode(line + "=" * (-len(line) % 4)).decode("utf-8", "ignore")
                out.extend(CONFIG_RE.findall(dec))
            except Exception:
                pass
    return out


def host_port(link):
    after = link.split("://", 1)[1] if "://" in link else link
    if "@" in after:
        after = after.split("@", 1)[1]
    hostpart = after.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if ":" in hostpart:
        h, p = hostpart.rsplit(":", 1)
        if p.isdigit():
            return h, int(p)
    return None


def tcp_ok(hp, timeout=4):
    try:
        with socket.create_connection(hp, timeout=timeout):
            return True
    except Exception:
        return False


def main():
    all_links, counts = [], {}
    for url in SOURCES:
        try:
            links = extract_configs(fetch(url))
            counts[url.split("/")[-1]] = len(links)
            all_links.extend(links)
        except Exception:
            counts[url.split("/")[-1]] = 0
    seen, uniq = set(), []
    for l in all_links:
        key = host_port(l) or l
        if key not in seen:
            seen.add(key)
            uniq.append(l)
    ok = []
    with ThreadPoolExecutor(max_workers=60) as ex:
        for l, good in ex.map(lambda l: (l, bool(host_port(l)) and tcp_ok(host_port(l))), uniq):
            if good:
                ok.append(l)
    with open("sub.txt", "w") as f:
        f.write(base64.b64encode(("\n".join(ok)).encode()).decode())
    with open("raw.txt", "w") as f:
        f.write("\n".join(ok))
    html = """<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>کانفیگ رایگان</title>
<style>body{font-family:Tahoma;max-width:600px;margin:40px auto;padding:0 15px;line-height:1.8}code{background:#eee;padding:2px 6px;border-radius:4px;word-break:break-all}.box{border:1px solid #ccc;border-radius:8px;padding:12px;margin:10px 0}</style></head>
<body><h2>🌐 کانفیگ رایگان و تست‌شده</h2>
<div class="box">تعداد کانفیگ فعال: <b>%d</b><br>آخرین آپدیت: %s</div>
<h3>📱 طرز استفاده:</h3><p>۱. توی v2rayNG/PattNG برو <code>Subscription</code> → <code>Add</code></p>
<p>۲. این آدرس رو بذار: <code>https://komoterdon.github.io/free-sub/sub.txt</code></p>
<p>۳. ذخیره کن و آپدیت بزن.</p>
<p>⚠️ کانفیگ‌های رایگان موقتی‌ان — اگه کند/قطع شد، آپدیت بگیر.</p></body></html>""" % (len(ok), time.strftime("%Y-%m-%d %H:%M"))
    with open("index.html", "w") as f:
        f.write(html)
    print("working=%d collected=%d unique=%d counts=%s" % (len(ok), len(all_links), len(uniq), counts))


if __name__ == "__main__":
    main()

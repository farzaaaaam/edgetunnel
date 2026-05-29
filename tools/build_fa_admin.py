#!/usr/bin/env python3
"""Build Persian (fa) admin and login pages with extra-IP panel."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC_ADMIN = ROOT / "pages" / "admin.html"
SRC_LOGIN = ROOT / "pages" / "login.html"
OUT_ADMIN = ROOT / "admin" / "index.html"
OUT_LOGIN = ROOT / "login.html"

TRANSLATIONS = [
    ("⚡️ 优选订阅生成", "⚡️ تولید اشتراک بهینه"),
    ("设置页面", "صفحه تنظیمات"),
    (" 设置页面 - 管理后台", " - پنل مدیریت"),
    ("消息通知设置", "اعلان‌ها"),
    ("订阅转换配置", "تبدیل اشتراک"),
    ("Cloudflare CDN 访问设置", "تنظیمات CDN کلادفلر"),
    ("Encrypted Client Hello", "رمزنگاری ECH"),

    ("zh-CN", "fa"),
    ('lang="zh-CN"', 'lang="fa" dir="rtl"'),
    ("管理后台", "پنل مدیریت"),
    ("加载中...", "در حال بارگذاری..."),
    ("我是小白！我想简单点！", "حالت ساده"),
    ("重置配置", "بازنشانی تنظیمات"),
    ("退出登录", "خروج"),
    ("Workers/Pages 请求使用情况", "مصرف درخواست Workers/Pages"),
    ("Workers 请求", "درخواست Workers"),
    ("Pages 请求", "درخواست Pages"),
    ("日配额", "سهمیه روزانه"),
    ("每日请求数重置清零", "زمان تا بازنشانی سهمیه روزانه"),
    ("当前网络信息", "اطلاعات شبکه فعلی"),
    ("国内测试", "تست داخل کشور"),
    ("国外测试", "تست خارج"),
    ("墙外测试", "تست خارج از فیلتر"),
    ("获取节点链接", "دریافت لینک نود"),
    ("节点链接格式", "فرمت لینک نود"),
    ("复制节点", "کپی نود"),
    ("自适应订阅", "اشتراک خودکار"),
    ("复制订阅", "کپی اشتراک"),
    ("Base64订阅", "اشتراک Base64"),
    ("Clash订阅", "اشتراک Clash"),
    ("SingBox订阅", "اشتراک SingBox"),
    ("优选订阅模式", "حالت اشتراک بهینه"),
    ("优选订阅生成器（抄作业，直接使用大佬优选好的结果）", "مولد اشتراک (استفاده از لیست آماده دیگران)"),
    ("随机优选（根据订阅时的网络自动下发对应网络的官方优选）", "انتخاب تصادفی (بر اساس شبکه شما)"),
    ("自定义订阅（支持汇聚订阅）", "اشتراک سفارشی (ادغام چند منبع)"),
    ("随机优选数量", "تعداد IP تصادفی"),
    ("指定优选端口", "پورت ثابت"),
    ("随机端口", "پورت تصادفی"),
    ("自定义优选地址", "آدرس‌های بهینه سفارشی"),
    ("优选订阅生成器", "آدرس مولد اشتراک"),
    ("在线优选", "بهینه‌سازی آنلاین"),
    ("订阅接口", "رابط API"),
    ("链式代理", "پروکسی زنجیره‌ای"),
    ("取消", "انصراف"),
    ("保存", "ذخیره"),
    ("详细配置信息", "تنظیمات پیشرفته"),
    ("订阅名称", "نام اشتراک"),
    ("节点协议", "پروتکل"),
    ("加密方式", "روش رمزنگاری"),
    ("传输协议", "پروتکل انتقال"),
    ("跳过证书验证", "نادیده گرفتن گواهی"),
    ("随机伪装路径", "مسیر تصادفی"),
    ("查看操作日志", "مشاهده لاگ"),
    ("全部日志", "همه لاگ‌ها"),
    ("登录设置页面", "ورود به پنل"),
    ("密码", "رمز عبور"),
    ("登录", "ورود"),
    ("正在加载...", "در حال بارگذاری..."),
    ("保存自定义IP失败", "ذخیره IP سفارشی ناموفق بود"),
    ("加载自定义IP失败", "بارگذاری IP سفارشی ناموفق بود"),
    ("随机优选数量不能为空", "تعداد IP تصادفی نمی‌تواند خالی باشد"),
    ("自定义优选地址不能为空", "آدرس سفارشی نمی‌تواند خالی باشد"),
    ("设置页面 - 管理后台", "تنظیمات - پنل مدیریت"),
]

EXTRA_IP_HTML = '''
                    <div class="module" id="extraIpModule">
                        <div class="module-title non-collapsible">➕ IPهای اضافی (همراه با لیست تصادفی)</div>
                        <div class="module-content">
                            <p class="hint-text" style="margin-bottom:12px;opacity:.85;line-height:1.6">
                                هر خط یک آدرس مثل <code dir="ltr">94.182.108.17:40443</code>.
                                این IPها <strong>به‌علاوه</strong> IPهای تصادفی در اشتراک قرار می‌گیرند (مثلاً ۱۰ تصادفی + ۶ دستی = ۱۶ نود).
                            </p>
                            <div class="form-group">
                                <label for="extraIPs">لیست IP دستی</label>
                                <textarea id="extraIPs" rows="8" dir="ltr" style="font-family:monospace;width:100%"
                                    placeholder="94.182.108.17:40443&#10;94.183.153.138:40443"
                                    onchange="markModified('extra')"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="extraIpSourceUrl">یا لینک منبع IP (هر ۱۲ ساعت خودکار بررسی می‌شود)</label>
                                <input type="url" id="extraIpSourceUrl" dir="ltr" class="full-width" placeholder="https://example.com/extra-ips.txt?token=..."
                                    onchange="markModified('extra')">
                            </div>
                            <div class="form-group">
                                <label>لینک اشتراک‌گذاری (با تغییر IP دستی به‌روز می‌شود)</label>
                                <div style="display:flex;gap:8px;flex-wrap:wrap">
                                    <input type="text" id="extraIpShareUrl" readonly dir="ltr" style="flex:1;min-width:200px;font-family:monospace">
                                    <button type="button" class="btn btn-secondary" onclick="copyExtraShareUrl()">کپی لینک</button>
                                    <button type="button" class="btn btn-secondary" onclick="refreshExtraIpsFromUrl()">بررسی دستی لینک</button>
                                </div>
                                <small id="extraIpLastFetch" style="display:block;margin-top:8px;opacity:.7"></small>
                            </div>
                            <div class="module-footer">
                                <div class="btn-group">
                                    <button type="button" class="btn btn-primary" onclick="saveExtraIps()" id="saveExtraBtn">ذخیره IPهای اضافی</button>
                                </div>
                            </div>
                        </div>
                    </div>
'''

EXTRA_IP_JS = r'''
        async function loadExtraIpsPanel() {
            try {
                const res = await fetch('/admin/extra-ips.txt?_t=' + Date.now());
                if (!res.ok) return;
                const data = await res.json();
                const ta = document.getElementById('extraIPs');
                const urlIn = document.getElementById('extraIpSourceUrl');
                const share = document.getElementById('extraIpShareUrl');
                const info = document.getElementById('extraIpLastFetch');
                if (ta) ta.value = data.manual || '';
                if (urlIn) urlIn.value = data.meta?.sourceUrl || '';
                if (share) share.value = data.shareUrl || (currentConfig?.额外IP库?.分享链接 || '');
                if (info && data.meta?.lastFetch) {
                    info.textContent = 'آخرین بررسی لینک: ' + new Date(data.meta.lastFetch).toLocaleString('fa-IR');
                }
            } catch (e) { console.warn('loadExtraIps', e); }
        }

        async function saveExtraIps() {
            const manual = document.getElementById('extraIPs')?.value || '';
            const sourceUrl = document.getElementById('extraIpSourceUrl')?.value?.trim() || '';
            try {
                const r1 = await fetch('/admin/extra-ips.txt', { method: 'POST', body: manual });
                const j1 = await r1.json();
                if (!r1.ok) throw new Error(j1.error || 'save failed');
                await fetch('/admin/extra-ips-meta.json', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sourceUrl, intervalHours: 12 })
                });
                if (j1.shareUrl) {
                    const share = document.getElementById('extraIpShareUrl');
                    if (share) share.value = j1.shareUrl;
                }
                showToast('IPهای اضافی ذخیره شد (' + (j1.count || 0) + ' مورد)', 'success');
                document.getElementById('saveExtraBtn').disabled = true;
            } catch (e) {
                showToast('خطا: ' + e.message, 'error');
            }
        }

        async function refreshExtraIpsFromUrl() {
            try {
                const res = await fetch('/admin/extra-ips/refresh', { method: 'POST' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'refresh failed');
                showToast(data.refreshed ? ('به‌روز شد: ' + (data.count || 0) + ' IP') : ('هنوز زود است یا لینکی تنظیم نشده'), data.refreshed ? 'success' : 'info');
                await loadExtraIpsPanel();
            } catch (e) {
                showToast('بررسی لینک ناموفق: ' + e.message, 'error');
            }
        }

        function copyExtraShareUrl() {
            const el = document.getElementById('extraIpShareUrl');
            if (!el?.value) return showToast('لینکی وجود ندارد', 'error');
            navigator.clipboard.writeText(el.value).then(() => showToast('لینک کپی شد', 'success'));
        }
'''

def translate(text: str) -> str:
    """Translate UI strings only — skip <script> blocks to preserve config keys."""
    parts = re.split(r"(<script[\s\S]*?</script>)", text, flags=re.IGNORECASE)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
        else:
            chunk = part
            for old, new in TRANSLATIONS:
                chunk = chunk.replace(old, new)
            out.append(chunk)
    return "".join(out)

def build_admin(html: str) -> str:
    html = translate(html)
    if 'id="extraIpModule"' not in html:
        html = html.replace(
            '<div class="module" id="preferredSubscriptionModule">',
            EXTRA_IP_HTML + '\n            <div class="module" id="preferredSubscriptionModule">',
            1,
        )
    if 'async function loadExtraIpsPanel' not in html:
        html = html.replace('</script>\n</body>', EXTRA_IP_JS + '\n    </script>\n</body>', 1)
        # hook loadConfig
        html = html.replace(
            'await loadCustomIPs();',
            'await loadCustomIPs();\n                await loadExtraIpsPanel();',
        )
    return html

def build_login(html: str) -> str:
    return translate(html)

def main():
    OUT_ADMIN.parent.mkdir(parents=True, exist_ok=True)
    admin = build_admin(SRC_ADMIN.read_text(encoding="utf-8-sig"))
    OUT_ADMIN.write_text(admin, encoding="utf-8")
    login = build_login(SRC_LOGIN.read_text(encoding="utf-8-sig"))
    OUT_LOGIN.write_text(login, encoding="utf-8")
    print(f"Wrote {OUT_ADMIN} ({len(admin)} bytes)")
    print(f"Wrote {OUT_LOGIN} ({len(login)} bytes)")

if __name__ == "__main__":
    main()

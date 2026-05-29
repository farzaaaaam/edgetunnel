#!/usr/bin/env python3
"""Add extra IP features to _worker.js (preserves 获取静态管理页面)."""
from pathlib import Path
import re

WORKER = Path(__file__).resolve().parents[1] / "_worker.js"
t = WORKER.read_bytes().decode("utf-8-sig")
nl = "\r\n" if "\r\n" in t else "\n"

def ins(after, block, once_marker=None):
    global t
    if once_marker and once_marker in t:
        return
    if after not in t:
        raise SystemExit(f"anchor missing: {after[:80]!r}")
    t = t.replace(after, after + block.replace("\n", nl), 1)

HELPERS = """
const EXTRA_IP_KV = 'EXTRA_IP.txt';
const EXTRA_IP_MANUAL_KV = 'EXTRA_IP_MANUAL.txt';
const EXTRA_IP_REMOTE_KV = 'EXTRA_IP_REMOTE.txt';
const EXTRA_IP_META_KV = 'EXTRA_IP_META.json';

async function 获取额外IP公开TOKEN(hostname, userID) {
	return await MD5MD5(hostname + userID + '@extra_ips');
}

function 解析额外IP行(文本) {
	if (!文本 || !String(文本).trim()) return [];
	return String(文本).split(/[\\r\\n]+/).map(l => l.trim()).filter(l => l && !l.startsWith('#'));
}

async function 合并并保存额外IP(env, 手动文本, 远程文本) {
	const 合并 = [...new Set([...解析额外IP行(手动文本), ...解析额外IP行(远程文本)])];
	await env.KV.put(EXTRA_IP_KV, 合并.join('\\n'));
	return 合并;
}

async function 从URL拉取额外IP(来源URL) {
	const res = await fetch(来源URL, { headers: { 'User-Agent': 'edgetunnel-extra-ip-sync/1.0' } });
	if (!res.ok) throw new Error(`拉取失败 HTTP ${res.status}`);
	return await res.text();
}

async function 刷新额外IP来源(env, 强制 = false) {
	const metaTxt = await env.KV.get(EXTRA_IP_META_KV);
	if (!metaTxt) return { refreshed: false, reason: 'no_meta' };
	const meta = JSON.parse(metaTxt);
	if (!meta.sourceUrl) return { refreshed: false, reason: 'no_url' };
	const intervalMs = (meta.intervalHours || 12) * 3600000;
	if (!强制 && meta.lastFetch && Date.now() - meta.lastFetch < intervalMs) {
		return { refreshed: false, reason: 'not_due', nextInMs: intervalMs - (Date.now() - meta.lastFetch) };
	}
	const remoteText = await 从URL拉取额外IP(meta.sourceUrl);
	await env.KV.put(EXTRA_IP_REMOTE_KV, remoteText);
	const manual = await env.KV.get(EXTRA_IP_MANUAL_KV) || '';
	const 合并 = await 合并并保存额外IP(env, manual, remoteText);
	meta.lastFetch = Date.now();
	meta.lastCount = 合并.length;
	await env.KV.put(EXTRA_IP_META_KV, JSON.stringify(meta));
	return { refreshed: true, count: 合并.length, lastFetch: meta.lastFetch };
}

async function 自动刷新额外IP库(env) {
	try {
		return await 刷新额外IP来源(env, false);
	} catch (e) {
		console.error('[额外IP] 自动刷新失败:', e.message);
		return { refreshed: false, error: e.message };
	}
}

async function 获取额外IP列表(env, config_JSON) {
	if (config_JSON?.额外IP库?.启用 === false) return [];
	await 自动刷新额外IP库(env);
	const txt = await env.KV.get(EXTRA_IP_KV);
	return txt ? 解析额外IP行(txt) : [];
}
"""

if "EXTRA_IP_KV" not in t:
    anchor = f"const Pages静态页面 = 'https://edt-pages.github.io';{nl}"
    if "async function 获取静态管理页面" in t:
        anchor = f"async function 获取静态管理页面"  # insert before static page fn
        ins(
            f"const Pages静态页面 = 'https://edt-pages.github.io';{nl}",
            HELPERS,
        )
    else:
        ins(anchor, HELPERS)

ins(
    f"config_JSON = await 读取config_JSON(env, host, userID, UA);{nl}{nl}\t\t\t\t\tif (访问路径 === 'admin/init')",
    f"\t\t\t\t\tctx.waitUntil(自动刷新额外IP库(env));{nl}{nl}\t\t\t\t\t",
    "ctx.waitUntil(自动刷新额外IP库(env))",
)

POST = """
						} else if (区分大小写访问路径 === 'admin/extra-ips.txt') {
							try {
								const manualIPs = await request.text();
								await env.KV.put(EXTRA_IP_MANUAL_KV, manualIPs);
								const remote = await env.KV.get(EXTRA_IP_REMOTE_KV) || '';
								const 合并 = await 合并并保存额外IP(env, manualIPs, remote);
								ctx.waitUntil(请求日志记录(env, request, 访问IP, 'Save_Extra_IPs', config_JSON));
								const shareToken = await 获取额外IP公开TOKEN(host, userID);
								return new Response(JSON.stringify({
									success: true,
									message: '额外IP已保存',
									count: 合并.length,
									shareUrl: `${url.protocol}//${url.host}/extra-ips.txt?token=${shareToken}`,
								}), { status: 200, headers: { 'Content-Type': 'application/json;charset=utf-8' } });
							} catch (error) {
								return new Response(JSON.stringify({ error: '保存额外IP失败: ' + error.message }), { status: 500, headers: { 'Content-Type': 'application/json;charset=utf-8' } });
							}
						} else if (区分大小写访问路径 === 'admin/extra-ips-meta.json') {
							try {
								const body = await request.json();
								const metaTxt = await env.KV.get(EXTRA_IP_META_KV);
								const meta = metaTxt ? JSON.parse(metaTxt) : { intervalHours: 12 };
								if (body.sourceUrl !== undefined) meta.sourceUrl = body.sourceUrl ? String(body.sourceUrl).trim() : null;
								if (body.intervalHours !== undefined) meta.intervalHours = Math.max(1, parseInt(body.intervalHours, 10) || 12);
								if (body.enabled !== undefined) {
									config_JSON.额外IP库 = { ...config_JSON.额外IP库, 启用: !!body.enabled };
									await env.KV.put('config.json', JSON.stringify(config_JSON, null, 2));
								}
								await env.KV.put(EXTRA_IP_META_KV, JSON.stringify(meta));
								if (meta.sourceUrl) await 刷新额外IP来源(env, true);
								return new Response(JSON.stringify({ success: true, meta }), { status: 200, headers: { 'Content-Type': 'application/json;charset=utf-8' } });
							} catch (error) {
								return new Response(JSON.stringify({ error: '保存额外IP设置失败: ' + error.message }), { status: 500, headers: { 'Content-Type': 'application/json;charset=utf-8' } });
							}
						} else if (区分大小写访问路径 === 'admin/extra-ips/refresh') {
							try {
								const result = await 刷新额外IP来源(env, true);
								return new Response(JSON.stringify({ success: true, ...result }), { status: 200, headers: { 'Content-Type': 'application/json;charset=utf-8' } });
							} catch (error) {
								return new Response(JSON.stringify({ success: false, error: error.message }), { status: 500, headers: { 'Content-Type': 'application/json;charset=utf-8' } });
							}
"""

if "admin/extra-ips.txt" not in t or "Save_Extra_IPs" not in t:
    t = t.replace(
        f"\t\t\t\t\t\t}} else return new Response(JSON.stringify({{ error: '不支持的POST请求路径' }}), {{ status: 404, headers: {{ 'Content-Type': 'application/json;charset=utf-8' }} }});{nl}\t\t\t\t\t}} else if (访问路径 === 'admin/config.json')",
        "\t\t\t\t\t\t" + POST.replace("\n", nl) + f"\t\t\t\t\t\t}} else return new Response(JSON.stringify({{ error: '不支持的POST请求路径' }}), {{ status: 404, headers: {{ 'Content-Type': 'application/json;charset=utf-8' }} }});{nl}\t\t\t\t\t}} else if (访问路径 === 'admin/config.json')",
    )

GET = """
					} else if (区分大小写访问路径 === 'admin/extra-ips.txt') {
						const manual = await env.KV.get(EXTRA_IP_MANUAL_KV) || '';
						const shareToken = await 获取额外IP公开TOKEN(host, userID);
						const metaTxt = await env.KV.get(EXTRA_IP_META_KV);
						const meta = metaTxt ? JSON.parse(metaTxt) : { intervalHours: 12 };
						return new Response(JSON.stringify({
							manual,
							merged: await env.KV.get(EXTRA_IP_KV) || '',
							meta,
							shareUrl: `${url.protocol}//${url.host}/extra-ips.txt?token=${shareToken}`,
						}, null, 2), { status: 200, headers: { 'Content-Type': 'application/json;charset=utf-8' } });
"""

if "EXTRA_IP_MANUAL_KV" not in t.split("admin/cf.json")[0][-500:]:
    t = t.replace(
        f"\t\t\t\t\t}} else if (访问路径 === 'admin/cf.json') //{{CF配置文件{nl}\t\t\t\t\t\treturn new Response(JSON.stringify(request.cf, null, 2), {{ status: 200, headers: {{ 'Content-Type': 'application/json;charset=utf-8' }} }});{nl}\t\t\t\t\t}}{nl}{nl}\t\t\t\t\tctx.waitUntil(请求日志记录(env, request, 访问IP, 'Admin_Login', config_JSON));",
        GET.replace("\n", nl) + f"\t\t\t\t\t}} else if (访问路径 === 'admin/cf.json') //{{CF配置文件{nl}\t\t\t\t\t\treturn new Response(JSON.stringify(request.cf, null, 2), {{ status: 200, headers: {{ 'Content-Type': 'application/json;charset=utf-8' }} }});{nl}\t\t\t\t\t}}{nl}{nl}\t\t\t\t\tctx.waitUntil(请求日志记录(env, request, 访问IP, 'Admin_Login', config_JSON));",
    )

PUBLIC = f"""
				}} else if (访问路径 === 'extra-ips.txt') {{
					const 请求TOKEN = url.searchParams.get('token');
					const 公开TOKEN = await 获取额外IP公开TOKEN(host, userID);
					if (请求TOKEN !== 公开TOKEN) return new Response('Forbidden', {{ status: 403, headers: {{ 'Content-Type': 'text/plain; charset=utf-8' }} }});
					await 自动刷新额外IP库(env);
					const 内容 = await env.KV.get(EXTRA_IP_KV) || '';
					return new Response(内容, {{ status: 200, headers: {{ 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' }} }});
"""

if "访问路径 === 'extra-ips.txt'" not in t:
    t = t.replace(
        f"\t\t\t\t}} else if (访问路径 === 'logout' || uuidRegex.test(访问路径)) //{{清除cookie并跳转到登录页面",
        PUBLIC + f"\t\t\t\t}} else if (访问路径 === 'logout' || uuidRegex.test(访问路径)) //{{清除cookie并跳转到登录页面",
    )

# subscription merge
old_pat = re.compile(
    r"(\t+const 完整优选列表 = config_JSON\.优选订阅生成\.本地IP库\.随机IP \? \([\s\S]*?\)\[0\];)",
    re.MULTILINE,
)
if "获取额外IP列表(env, config_JSON)" not in t:
    def repl(m):
        block = m.group(1).replace("const 完整优选列表", "let 完整优选列表")
        ind = "\t" * 4
        return block + f"{nl}{ind}const 额外IP列表 = await 获取额外IP列表(env, config_JSON);{nl}{ind}if (额外IP列表.length) 完整优选列表 = [...new Set([...完整优选列表, ...额外IP列表])];"
    t, n = old_pat.subn(repl, t, count=1)
    if not n:
        raise SystemExit("subscription merge pattern not found")

if "async scheduled(event, env, ctx)" not in t:
    t = t.replace(
        f"\t\treturn new Response(await nginx(), {{ status: 200, headers: {{ 'Content-Type': 'text/html; charset=UTF-8' }} }});{nl}\t}}{nl}}};",
        f"\t\treturn new Response(await nginx(), {{ status: 200, headers: {{ 'Content-Type': 'text/html; charset=UTF-8' }} }});{nl}\t}},{nl}\tasync scheduled(event, env, ctx) {{{nl}\t\tctx.waitUntil(自动刷新额外IP库(env));{nl}\t}},{nl}}};",
    )

if "额外IP库:" not in t or "自动刷新间隔小时" not in t:
    ins(
        f"\t\t\tTOKEN: await MD5MD5(hostname + userID),{nl}\t\t}},{nl}\t\t订阅转换配置:",
        f"{nl}\t\t额外IP库: {{{nl}\t\t\t启用: true,{nl}\t\t\t来源URL: null,{nl}\t\t\t自动刷新间隔小时: 12,{nl}\t\t}},{nl}",
        "额外IP库:",
    )

CFG = f"""
\tif (!config_JSON.额外IP库) config_JSON.额外IP库 = {{ 启用: true, 来源URL: null, 自动刷新间隔小时: 12 }};
\tif (config_JSON.额外IP库.启用 === undefined) config_JSON.额外IP库.启用 = true;
\tif (!config_JSON.额外IP库.自动刷新间隔小时) config_JSON.额外IP库.自动刷新间隔小时 = 12;
\tconst 额外IP公开TOKEN = await 获取额外IP公开TOKEN(hostname, userID);
\tconfig_JSON.额外IP库.分享链接 = `https://${{host}}/extra-ips.txt?token=${{额外IP公开TOKEN}}`;
\ttry {{
\t\tconst metaTxt = await env.KV.get(EXTRA_IP_META_KV);
\t\tif (metaTxt) {{
\t\t\tconst meta = JSON.parse(metaTxt);
\t\t\tconfig_JSON.额外IP库.来源URL = meta.sourceUrl || config_JSON.额外IP库.来源URL;
\t\t\tconfig_JSON.额外IP库.上次刷新 = meta.lastFetch || null;
\t\t\tconfig_JSON.额外IP库.上次数量 = meta.lastCount || 0;
\t\t}}
\t}} catch (e) {{ }}

"""

if "额外IP公开TOKEN = await" not in t:
    t = t.replace(f"\tconst 初始化TG_JSON = {{ BotToken: null, ChatID: null }};", CFG.replace("\n", nl) + f"\tconst 初始化TG_JSON = {{ BotToken: null, ChatID: null }};")

WORKER.write_bytes(("\ufeff" + t).encode("utf-8"))
print("patched OK")

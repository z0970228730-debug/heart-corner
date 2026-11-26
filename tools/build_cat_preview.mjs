// Build a standalone, offline-friendly cat-house preview from the actual app.
import { readFile, writeFile, readdir, mkdir } from 'node:fs/promises';
import { resolve, dirname, extname, join } from 'node:path';
import { previewFixture } from './cat-preview-fixture.mjs';

const dest = resolve(process.argv[2] || 'cat-preview.html');
const root = resolve('public');
const mime = { '.webp': 'image/webp', '.mp4': 'video/mp4', '.mp3': 'audio/mpeg', '.svg': 'image/svg+xml' };
const assets = {};
for (const name of await readdir(join(root, 'assets'))) {
  if (!mime[extname(name)]) continue;
  assets[name] = `data:${mime[extname(name)]};base64,${(await readFile(join(root, 'assets', name))).toString('base64')}`;
}
const inline = s => s.replace(/<\/script/gi, '<\\/script');
let html = await readFile(join(root, 'index.html'), 'utf8');
let motion = await readFile(join(root, 'assets', 'cat-motion.js'), 'utf8');
let css = await readFile(join(root, 'assets', 'cat-motion.css'), 'utf8');
const qrcode = await readFile(join(root, 'assets', 'qrcode.js'), 'utf8');
const catAssets = Object.fromEntries(Object.entries(assets).filter(([name]) => /^cat-.*-v2\.webp$|^cat-rest\.webp$/.test(name)));
motion = motion.replace('src="assets/${image}"', 'src="${previewCatAsset(image)}"');
css = css.replace(/url\('([^']+)'\)/g, (all, name) => catAssets[name] ? `var(--preview-${name.replace('.', '-')})` : all);
html = html.replace('<script src="/assets/qrcode.js"></script>', () => `<script>${inline(qrcode)}</script>`)
  .replace('<link rel="stylesheet" href="assets/cat-motion.css">', () => `<style>${css}</style>`)
  .replace('<script src="assets/cat-motion.js"></script>', () => `<script>
const previewCatAssets = ${JSON.stringify(catAssets)};
const previewCatAsset = name => previewCatAssets[name] || '';
for (const [name, source] of Object.entries(previewCatAssets)) {
  document.documentElement.style.setProperty('--preview-' + name.replace('.', '-'), 'url("' + source + '")');
}
${inline(motion)}
</script>`)
  .replace(/<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^"]*">/g, '')
  .replace(/<div class="intro-screen"[\s\S]*?(?=<svg)/, '')
  .replace('const introDone=playIntro();', 'const introDone=Promise.resolve();')
  .replace(/  render\(\);\r?\n  const me=await api\('me'\);/, "  const me=await api('me');")
  .replaceAll('heart-corner-v2', 'heart-corner-v2-local-preview')
  .replace('<section class="house" id="house">', '<p style="background:#f9ead8;color:#805c49;border-radius:12px;padding:8px 12px;font-size:12px;margin:0;text-align:center">✧ 本機動畫預覽・小魚乾與芯幣均為示範資料</p><section class="house" id="house">');
html = html.replace(/\/?assets\/([\w.-]+)/g, (all, name) => assets[name] || all);
const mock = `<script>
const localCatPreview = (${previewFixture.toString()})();
if(!location.hash)location.hash='cat';
window.fetch = async (url, opts = {}) => {
  const path = String(url).split('/api/')[1];
  const result = localCatPreview.handle(path || '', opts.body ? JSON.parse(opts.body) : {});
  return new Response(JSON.stringify(result.data), {status: result.status, headers: {'content-type':'application/json'}});
};
</script>`;
html = html.replace('</head>', () => mock + '</head>');
await mkdir(dirname(dest), { recursive: true });
await writeFile(dest, html);
console.log('Standalone demo written:', dest);

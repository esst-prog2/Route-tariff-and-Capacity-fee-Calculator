// Record the demo for slide 2: a real run of the app's Route Tariff Calculator, three routes clicked
// on the map. Writes <out dir>/demo.webm and <out dir>/demo-steps.json (when each step starts and ends,
// in seconds), which tools/build_slides.py puts into the slide.
// Needs the app running (python -m streamlit run app.py --server.port 8599) and Chrome.
// Run: node tools/slides/record_demo.mjs <path to puppeteer-core> <out dir>
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";

const [, , puppeteerPath, outDir] = process.argv;
const puppeteer = createRequire(import.meta.url)(puppeteerPath);
mkdirSync(outDir, { recursive: true });

const APP = "http://localhost:8599/?embed=true";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const W = 960, H = 880;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, defaultViewport: { width: W, height: H, deviceScaleFactor: 1.5 } });
const page = await browser.newPage();
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
await page.goto(APP, { waitUntil: "networkidle2" });
await page.waitForSelector('[data-testid="stVegaLiteChart"] svg.marks', { timeout: 60000 });
await sleep(2500);

// A visible pointer: headless Chrome records no cursor, so one is drawn where the mouse is.
await page.evaluate(() => {
  const css = document.createElement("style");
  css.textContent = `
    #demo-cursor { position: fixed; left: 0; top: 0; width: 26px; height: 26px; z-index: 2147483647; pointer-events: none;
      transform: translate(-3px, -2px); filter: drop-shadow(0 1px 2px rgb(0 0 0 / .45)); }
    .demo-ring { position: fixed; width: 18px; height: 18px; margin: -11px 0 0 -11px; border: 3px solid #C8102E; border-radius: 50%;
      z-index: 2147483646; pointer-events: none; animation: demo-ring 600ms ease-out forwards; }
    @keyframes demo-ring { to { transform: scale(3.2); opacity: 0; } }`;
  document.head.appendChild(css);
  const c = document.createElement("div");
  c.id = "demo-cursor";
  c.innerHTML = '<svg viewBox="0 0 26 26" width="26" height="26"><path d="M3 2 L3 21 L8 16.5 L11.5 24 L15 22.5 L11.5 15 L18 15 Z" fill="#fff" stroke="#15181A" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  document.body.appendChild(c);
  document.addEventListener("mousemove", (e) => { c.style.left = e.clientX + "px"; c.style.top = e.clientY + "px"; }, true);
  document.addEventListener("mousedown", (e) => {
    const r = document.createElement("div");
    r.className = "demo-ring"; r.style.left = e.clientX + "px"; r.style.top = e.clientY + "px";
    document.body.appendChild(r); setTimeout(() => r.remove(), 700);
  }, true);
});

// the visible element (tabs keep hidden panels in the DOM)
const visible = (sel, text) =>
  page.evaluateHandle((sel, text) =>
    [...document.querySelectorAll(sel)].find((e) => e.offsetParent !== null && (!text || e.textContent.includes(text))) || null, sel, text);

// wait until Streamlit has finished rerunning
const settle = async () => {
  await sleep(250);
  for (let i = 0; i < 60; i++) {
    const busy = await page.evaluate(() => !!document.querySelector('[data-stale="true"]') || !!document.querySelector('[data-testid="stStatusWidget"] [data-testid="stStatusWidgetRunningIcon"]'));
    if (!busy) break;
    await sleep(100);
  }
  await sleep(200);
};

let mouse = { x: W * 0.8, y: H * 0.5 };
await page.mouse.move(mouse.x, mouse.y);
const glide = async (x, y, ms = 650) => {
  const steps = Math.max(8, Math.round(ms / 16)), from = { ...mouse };
  for (let i = 1; i <= steps; i++) {
    const t = i / steps, e = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
    await page.mouse.move(from.x + (x - from.x) * e, from.y + (y - from.y) * e);
    await sleep(16);
  }
  mouse = { x, y };
};
const clickAt = async (x, y) => { await glide(x, y); await sleep(150); await page.mouse.down(); await sleep(70); await page.mouse.up(); };

// smooth scroll of Streamlit's main area, so that `y` (a viewport y now) moves to `to`
const scrollBy = async (dy, ms = 800) => {
  await page.evaluate(async (dy, ms) => {
    const cands = [document.querySelector('[data-testid="stMain"]'), document.querySelector('[data-testid="stAppViewContainer"]'), document.scrollingElement];
    const s = cands.find((e) => e && e.scrollHeight > e.clientHeight + 5) || document.scrollingElement;
    const start = s.scrollTop, t0 = performance.now();
    await new Promise((done) => {
      const tick = (now) => {
        const t = Math.min(1, (now - t0) / ms), e = t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2;
        s.scrollTop = start + dy * e;
        t < 1 ? requestAnimationFrame(tick) : done();
      };
      requestAnimationFrame(tick);
    });
  }, dy, ms);
  await sleep(100);
};
const box = async (handle) => {
  const el = handle.asElement();
  if (!el) { await page.screenshot({ path: `${outDir}/failed.png` }); throw new Error("missing element, see failed.png"); }
  return el.boundingBox();
};
const scrollTopTo = async (handle, to = 16, ms) => scrollBy((await box(handle)).y - to, ms);
const scrollBottomTo = async (handle, to = H - 24, ms) => { const b = await box(handle); await scrollBy(b.y + b.height - to, ms); };

const marker = (name) => page.evaluateHandle((name) => {
  const chart = [...document.querySelectorAll('[data-testid="stVegaLiteChart"]')].find((e) => e.offsetParent);
  return [...chart.querySelectorAll("svg.marks [aria-label]")].find((e) => e.getAttribute("aria-label").includes(`Point: ${name};`)) || null;
}, name);
const routeText = () => page.evaluate(() =>
  ([...document.querySelectorAll("p")].find((e) => e.offsetParent && e.textContent.startsWith("Route:")) || {}).textContent || "");
const clickPoint = async (name) => {
  for (let attempt = 0; attempt < 3; attempt++) {  // a click that lands while the app reruns is lost: click again
    const b = await box(await marker(name));
    await clickAt(b.x + b.width / 2, b.y + b.height / 2);
    await settle();
    for (let i = 0; i < 20 && !(await routeText()).includes(name); i++) await sleep(150);
    if ((await routeText()).includes(name)) { await sleep(350); return; }
    console.error(`retry: ${name} (attempt ${attempt + 1}), route text now: ${await routeText()}`);
  }
  throw new Error(`clicking ${name} did not add it to the route`);
};
const chooseBeginning = async (code) => {
  const b = await box(await visible('input[aria-label^="Route beginning"]'));
  await clickAt(b.x + 40, b.y + b.height / 2);
  await sleep(350);
  await page.keyboard.type(code, { delay: 140 });
  await sleep(300);
  await page.keyboard.press("Enter");
  await settle();
  await sleep(300);
};
const typeRate = async (currency, value) => {
  const input = await visible(`input[aria-label="${currency} per 1 EUR"]`);
  await scrollBottomTo(input, H - 200, 900);
  const b = await box(input);
  await clickAt(b.x + 30, b.y + b.height / 2);
  await sleep(200);
  await page.keyboard.type(value, { delay: 160 });
  await page.keyboard.press("Tab");
  await settle();
};
const showTotal = async () => {
  const label = await visible("p", "Route total (EUR/MWh)");
  const tables = [];
  for (const d of await page.$$('[data-testid="stDataFrame"]')) if (await d.evaluate((e) => e.offsetParent !== null)) tables.push(d);
  await scrollBottomTo({ asElement: () => tables[tables.length - 1] }, H - 70, 1000);
  await sleep(1800);
  return label;
};
// the top of the page: choosing a new beginning clears the route and shortens the page, so anywhere lower would jump
const scroller = `[document.querySelector('[data-testid="stMain"]'), document.querySelector('[data-testid="stAppViewContainer"]'), document.scrollingElement].find((e) => e && e.scrollHeight > e.clientHeight + 5) || document.scrollingElement`;
const toTop = async () => scrollBy(-(await page.evaluate(`(${scroller}).scrollTop`)), 900);

// ---- before recording: close the sidebar, clear the route the app opens with, scroll to the map ----
// the sidebar holds only the tariff-file upload, which the demo does not use
await page.addStyleTag({ content: '[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] { display: none !important; }' });
await sleep(800);
const clear = await visible("button", "Clear");
await clear.asElement().evaluate((e) => e.click());
await settle();
await sleep(800);
await toTop();
await sleep(500);

// ---- the recording: six steps, the slide stops after each one ----
const recorder = await page.screencast({ path: `${outDir}/demo.webm` });
const t0 = Date.now();
const now = () => (Date.now() - t0) / 1000;
const steps = [];
const step = async (fn) => { const start = now(); await fn(); steps.push([+start.toFixed(2), +now().toFixed(2)]); };
await sleep(600);

await step(async () => { await clickPoint("Kireevo/Zaychar"); await clickPoint("Kiskundorozsma 2"); });
await step(async () => { await typeRate("HUF", "400"); await showTotal(); });
await step(async () => { await toTop(); await chooseBeginning("NL"); await clickPoint("VIP TTF-THE-H"); await clickPoint("VIP Brandov-GASPOOL"); });
await step(async () => { await typeRate("CZK", "25"); await showTotal(); });
await step(async () => { await toTop(); await chooseBeginning("HU"); await clickPoint("VIP Bereg"); await clickPoint("Uzhgorod/Velké Kapušany"); });
await step(async () => { await typeRate("HUF", "400"); await showTotal(); });

await sleep(400);
await recorder.stop();
const routes = await page.evaluate(() => [...document.querySelectorAll("h3")].filter((e) => e.offsetParent).map((e) => e.textContent));
writeFileSync(`${outDir}/demo-steps.json`, JSON.stringify({ steps, duration: +now().toFixed(2), last_route: routes }, null, 1));
console.log(JSON.stringify({ steps, duration: now(), routes }));
await browser.close();

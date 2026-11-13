// Capture the real app's screens for the promo video, at 2x pixel density.
// Needs the app running (python -m streamlit run app.py --server.port 8599) and Chrome.
// Run: node video/tools/capture_app.mjs <path to puppeteer-core> <out dir>
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";

const [, , puppeteerPath, outDir] = process.argv;
const puppeteer = createRequire(import.meta.url)(puppeteerPath);
mkdirSync(outDir, { recursive: true });

const APP = "http://localhost:8599/";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, defaultViewport: { width: 1280, height: 1000, deviceScaleFactor: 2 } });
const page = await browser.newPage();
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
await page.goto(APP, { waitUntil: "networkidle2" });
await page.waitForSelector('[data-testid="stVegaLiteChart"]', { timeout: 60000 });
await sleep(3000);

// the visible element (tabs keep hidden panels in the DOM)
const visible = (sel, text) =>
  page.evaluateHandle(
    (sel, text) =>
      [...document.querySelectorAll(sel)].find((e) => e.offsetParent !== null && (!text || e.textContent.includes(text))) || null,
    sel,
    text,
  );
const shot = async (handle, name, pad = 0) => {
  const el = handle.asElement();
  if (!el) throw new Error("missing element for " + name);
  await el.evaluate((e) => e.scrollIntoView({ block: "center" }));
  await sleep(500);
  const b = await el.boundingBox();
  await page.screenshot({ path: `${outDir}/${name}.png`, clip: { x: b.x - pad, y: b.y - pad, width: b.width + 2 * pad, height: b.height + 2 * pad }, captureBeyondViewport: true });
  console.log(name, Math.round(b.width), "x", Math.round(b.height), "css px");
};
// a clip from the top of one element to the bottom of another
const shotSpan = async (fromH, toH, name, pad = 12) => {
  const a = fromH.asElement(), z = toH.asElement();
  await a.evaluate((e) => e.scrollIntoView({ block: "start" }));
  await sleep(500);
  const ba = await a.boundingBox(), bz = await z.boundingBox();
  const x = Math.min(ba.x, bz.x) - pad, y = ba.y - pad;
  await page.screenshot({ path: `${outDir}/${name}.png`, clip: { x, y, width: Math.max(ba.width, bz.width) + 2 * pad, height: bz.y + bz.height - ba.y + 2 * pad }, captureBeyondViewport: true });
  console.log(name, "span");
};
const setSelect = async (label, text) => {
  const h = await visible(`input[aria-label^="${label}"]`);
  const el = h.asElement();
  await el.evaluate((e) => e.scrollIntoView({ block: "center" }));
  await el.click();
  await sleep(300);
  await page.keyboard.type(text);
  await sleep(500);
  await page.keyboard.press("Enter");
  await sleep(2500);
};
const setText = async (label, value) => {
  const h = await visible(`input[aria-label="${label}"]`);
  const el = h.asElement();
  await el.evaluate((e) => e.scrollIntoView({ block: "center" }));
  await el.click({ clickCount: 3 });
  await page.keyboard.type(value);
  await page.keyboard.press("Tab");
  await sleep(2500);
};
const clickButton = async (text) => {
  const h = await page.evaluateHandle((text) => [...document.querySelectorAll("button")].find((b) => b.offsetParent !== null && b.textContent.trim() === text) || null, text);
  await h.asElement().click();
  await sleep(2500);
};
const clickTab = async (text) => {
  const h = await page.evaluateHandle((text) => [...document.querySelectorAll('[role="tab"]')].find((b) => b.textContent.includes(text)) || null, text);
  await h.asElement().click();
  await sleep(2500);
};

const map = () => visible('[data-testid="stVegaLiteChart"]');

// ---- tab 1: three states of the real map, then the result ----
await shot(await map(), "map-s3-route");              // the app opens on this route
await clickButton("Clear");
await shot(await map(), "map-s1-start");              // BG only
await setSelect("Next point", "Kireevo");
await shot(await map(), "map-s2-first");              // BG > Kireevo/Zaychar
await setSelect("Next point", "Kiskundorozsma");
await shot(await map(), "map-s3b-route");             // the full route, after clicking it ourselves
await setText("HUF per 1 EUR", "400");               // the rate box appears once FGSZ is on the route
const heading = await visible("h3", "Kiskundorozsma");
const lastTable = async () => {
  let last = null;
  for (const d of await page.$$('[data-testid="stDataFrame"]')) { if (await d.evaluate((e) => e.offsetParent !== null)) last = d; }
  return last;
};
const routeEnd = await lastTable();
await shotSpan(heading, { asElement: () => routeEnd }, "result-route");

// ---- tab 2: the bundled point, 50,000 kWh/d, HUF 395.5 ----
await clickTab("Capacity Fee Calculator");
await setText("Requested capacity", "50000");
await setSelect("Unit", "kWh/d");
await setText("HUF per 1 EUR", "395.5");
const gca = await visible("h4", "Gas Connect Austria exit");
const gcaEnd = await visible('[data-testid="stDataFrame"]');
await shotSpan(gca, gcaEnd, "fee-gca");
const fgsz = await visible("h4", "FGSZ entry");
await fgsz.asElement().evaluate((e) => e.scrollIntoView({ block: "start" }));
await sleep(500);
const dfs = await page.$$('[data-testid="stDataFrame"]');
let lastVisible = null;
for (const d of dfs) { if (await d.evaluate((e) => e.offsetParent !== null)) lastVisible = d; }
await shotSpan(fgsz, { asElement: () => lastVisible }, "fee-fgsz");
const total = await visible('[data-testid="stMetric"]', "Bundle total");
await shot(total, "fee-total", 16);

// ---- tab 3: Eustream, Balassagyarmat SK>HU, Q4 2026, 100,000 kWh/h, booked, CEGHIX 30 ----
await clickTab("Bank Guarantee Calculator");
await setSelect("Network point", "Balassagyarmat SK");
await setText("Requested capacity", "100000");
await setText("CEGHIX (EUR/MWh)", "30");
await clickButton("Add to list");
await sleep(1500);
const guarTables = [];
for (const d of await page.$$('[data-testid="stDataFrame"]')) { if (await d.evaluate((e) => e.offsetParent !== null)) guarTables.push(d); }
console.log("visible tables on tab 3:", guarTables.length);
await shotSpan({ asElement: () => guarTables[0] }, { asElement: () => guarTables[guarTables.length - 1] }, "guarantee", 12);

await browser.close();
console.log("done");

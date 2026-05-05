import fs from "node:fs";
import { execSync } from "node:child_process";
import { chromium } from "playwright-core";

const baseUrl = process.env.BASE_URL || "http://127.0.0.1:4173/";

function commandPath(command) {
  try {
    return execSync(`command -v ${command}`, { encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch {
    return "";
  }
}

const executablePathCandidates = [
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  process.env.CHROME_PATH,
  process.env.BROWSER_PATH,
  commandPath("chromium"),
  commandPath("chromium-browser"),
  commandPath("google-chrome"),
  commandPath("google-chrome-stable"),
  commandPath("microsoft-edge"),
  commandPath("msedge"),
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
  "/usr/bin/google-chrome",
  "/usr/bin/google-chrome-stable",
  "/usr/bin/microsoft-edge",
  "/usr/bin/msedge",
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
].filter(Boolean);

const executablePath = executablePathCandidates.find((candidate) => {
  try {
    return fs.existsSync(candidate);
  } catch {
    return false;
  }
});

if (!executablePath) {
  throw new Error(
    "No Chromium/Chrome/Edge executable found. Set PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH or CHROME_PATH to a local browser binary.",
  );
}

const browser = await chromium.launch({
  executablePath,
  headless: true,
});

const page = await browser.newPage();
await page.goto(baseUrl, { waitUntil: "networkidle" });

await page.waitForSelector("video.video-local-player");

const videoState = await page.evaluate(async () => {
  const video = document.querySelector("video.video-local-player");
  if (!video) {
    return { ok: false, reason: "video_not_found" };
  }

  const sources = Array.from(video.querySelectorAll("source")).map((node) => node.getAttribute("src"));

  const canPlay = await new Promise((resolve) => {
    let done = false;
    const finish = (payload) => {
      if (done) return;
      done = true;
      resolve(payload);
    };

    const timeout = window.setTimeout(() => {
      finish({
        ok: video.readyState >= 2,
        readyState: video.readyState,
        currentSrc: video.currentSrc,
        sources,
        timeout: true,
      });
    }, 15000);

    video.addEventListener("canplay", () => {
      clearTimeout(timeout);
      finish({
        ok: true,
        readyState: video.readyState,
        currentSrc: video.currentSrc,
        sources,
        timeout: false,
      });
    }, { once: true });

    video.addEventListener("error", () => {
      clearTimeout(timeout);
      finish({
        ok: false,
        readyState: video.readyState,
        currentSrc: video.currentSrc,
        sources,
        timeout: false,
      });
    }, { once: true });

    video.load();
    if (video.readyState >= 2) {
      clearTimeout(timeout);
      finish({
        ok: true,
        readyState: video.readyState,
        currentSrc: video.currentSrc,
        sources,
        timeout: false,
      });
    }
  });

  return canPlay;
});

if (!videoState.ok) {
  throw new Error(`Video runtime check failed: ${JSON.stringify(videoState)}`);
}

const initialFrameState = await page.evaluate(async () => {
  const video = document.querySelector("video.video-local-player");
  if (!video) {
    return { ok: false, reason: "video_not_found" };
  }

  if (video.currentTime >= 0.95) {
    return { ok: true, currentTime: video.currentTime, duration: video.duration };
  }

  await new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      resolve();
    };

    video.addEventListener("seeked", finish, { once: true });
    video.currentTime = 1;
    window.setTimeout(finish, 4000);
  });

  return {
    ok: video.currentTime >= 0.95 && video.currentTime <= 1.5,
    currentTime: video.currentTime,
    duration: video.duration,
  };
});

if (!initialFrameState.ok) {
  throw new Error(`Initial frame check failed: ${JSON.stringify(initialFrameState)}`);
}

const playbackState = await page.evaluate(async () => {
  const video = document.querySelector("video.video-local-player");
  const select = document.getElementById("video-speed-select");
  if (!video || !select) {
    return { ok: false, reason: "missing_video_or_speed_control" };
  }

  const targetRate = "1.5";
  select.value = targetRate;
  select.dispatchEvent(new Event("change", { bubbles: true }));

  await new Promise((resolve) => window.setTimeout(resolve, 200));

  const targetTime = Math.min(10, Math.max(1, Math.floor((video.duration || 12) / 3)));

  await new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      resolve();
    };

    video.addEventListener("seeked", finish, { once: true });
    window.setTimeout(finish, 4000);
    video.currentTime = targetTime;
  });

  return {
    ok: Math.abs(video.playbackRate - Number(targetRate)) < 0.001 && video.currentTime >= Math.max(0.5, targetTime - 0.5),
    playbackRate: video.playbackRate,
    currentTime: video.currentTime,
    duration: video.duration,
  };
});

if (!playbackState.ok) {
  throw new Error(`Playback controls check failed: ${JSON.stringify(playbackState)}`);
}

const galleryInfo = await page.evaluate(() => {
  const cards = Array.from(document.querySelectorAll("#creation .creation-card"));
  return {
    count: cards.length,
    firstIsHero: cards[0]?.classList.contains("creation-card--hero") ?? false,
    activeText: cards[0]?.getAttribute("data-creation-text") ?? "",
  };
});

if (galleryInfo.count !== 5 || !galleryInfo.firstIsHero) {
  throw new Error(`Gallery runtime check failed: ${JSON.stringify(galleryInfo)}`);
}

const keepPhraseState = await page.evaluate(() => {
  const phrases = Array.from(document.querySelectorAll("#creation .keep-phrase")).map((node) => ({
    text: node.textContent?.trim() ?? "",
    wrapped: node.getClientRects().length > 1,
  }));
  return {
    count: phrases.length,
    wrappedCount: phrases.filter((item) => item.wrapped).length,
    phrases,
  };
});

if (keepPhraseState.wrappedCount !== 0) {
  throw new Error(`Keep phrase wrapping check failed: ${JSON.stringify(keepPhraseState)}`);
}

await page.click('#creation .creation-card:nth-child(2)');
const secondActive = await page.locator('#creation .creation-card:nth-child(2)').evaluate((node) => node.classList.contains("is-active"));
if (!secondActive) {
  throw new Error("Gallery click interaction failed.");
}

const tableInfo = await page.evaluate(() => {
  const sections = Array.from(document.querySelectorAll(".career-table-card"));
  return sections.map((section) => ({
    title: section.querySelector(".career-table-title")?.textContent?.trim() ?? "",
    rows: section.querySelectorAll("tbody tr").length,
  }));
});

if (tableInfo.length !== 2 || tableInfo[0].rows < 10 || tableInfo[1].rows < 5) {
  throw new Error(`Career table runtime check failed: ${JSON.stringify(tableInfo)}`);
}

console.log(JSON.stringify({ executablePath, baseUrl, videoState, initialFrameState, playbackState, galleryInfo, keepPhraseState, tableInfo }, null, 2));

await browser.close();

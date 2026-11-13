# SPEC: 30-second promo video, Route Tariff and Capacity Fee Calculator

Story (chosen by the user): the page's headline, click / see / know. Silent film; the words are on-screen captions.
Every pixel that claims to be the product is a real capture of the running app (`video/tools/capture_app.mjs`, 2x density, light theme). Every number is one the app shows and `tests/` asserts.

```text
GOAL:    Someone who has never heard of it understands in 30 s what it is for (the cost of moving gas
         across borders, answered by clicking), who it is for (gas traders), and that they can try it.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, MP4, silent.
TIME:    30.0 s x 30 fps = 900 frames.
LOOK:    the page's own world, "Capacity Map". Ground #D6E1E7 (the map's sea), panels white (the app's
         own screens), ink #15181A, ONE accent red #C8102E (the route, the click, the total, the button;
         nowhere else). No grain, no gradients, no glow, no vignette. Archivo from assets/fonts:
         display weight 800, width 78%, 104 px, tracking -1%, line height 0.98; body weight 600,
         width 100%, 40 px; small print 30 px. Product screens at 1.0 x their 2x capture (their text
         is 28 px), cropped to the piece the beat uses. Depth: panels carry a 0 14px 40px rgba(21,24,26,.16) shadow, nothing else.
OBJECTS: the real map (820 x 750 css px capture, three states), the real route table and totals, the real
         invoice and guarantee tables. One cursor: an ink arrow with a white edge, 64 px tall.
         A click is a red ring that grows from the point (60 -> 150 px, 0.35 s, power2.out).
MOTION:  enter = power3.out 0.5 s, move = power2.inOut 0.7 s, exit = power2.in 0.3 s, camera = expo.out 1.1 s.
         Cursor travels on a curve, 0.8 s per leg, clicks 0.15 s after arriving; the click causes the next thing
         on the same frame. Text blocks arrive line by line, 9 frames apart; no springs.
SHOTS:   (frames at 30 fps)
  1  0-102     Hook. Real map (BG only, no route) fills the left 62% of the frame, full height. Right column:
               "Bulgaria / to Hungary. / What does the / route cost?" (4 lines, 88 px). Frame 0 is already this.
               Hand-off: the map stays; the text column is wiped by the next scene's ground.
  2  102-240   Three operators. Left, 3 lines (96 px): "Three operators." / "Two currencies." / "Two units."
               Right, a ruled table that fills as each line lands: Bulgartransgaz EUR per kWh/d,
               Gastrans EUR per kWh/h, FGSZ HUF per kWh/h (README). Hand-off: the table rules wipe to the map.
  3  240-402   Click. The map returns (same position as shot 1) and pushes 1.5x onto the route. Caption right:
               "Click the / border points." The cursor enters, clicks Kireevo/Zaychar (map state 2, the point
               turns red), travels, clicks Kiskundorozsma 2 (state 3, route lit). Hand-off: the lit route
               stays and slides left as the table comes in.
  4  402-630   See. Left column: "See the / whole route / cost." and the running sum in 96 px tabular numerals:
               1.4431, + 0.8494, + 0.9684, + 0.4348, rule, 3.6957 (red). Right: the real points table (cropped to
               TSO, Point, Products, EUR/MWh) above the real totals table; a red outline marks each cost in turn,
               then the total, then "Saving 0.2956" (quarters instead of months). Hand-off: tables slide out left.
  5  630-804   Know. Title "Know what / to book:" top left, second line swaps "the invoices" -> "the guarantee".
               5a 630-720: the real Gas Connect Austria and FGSZ headers + total-cost rows stacked, red outline
               on 2,605.83 and 782,558. 5b 720-804: the real guarantee table, red outline on 280,104.80.
  6  804-900   End card. Map (lit route) right, same position as shot 1 mirrored. Left: wordmark band
               "Route Tariff and / Capacity Fee / Calculator", "Free. Real tariffs of 21 operators.",
               red button "Open the calculator", the app address below. The cursor clicks the button at 28.8 s
               (ring); everything holds still for the last 1.5 s.
BANNED:  a dark or navy void; glow, bloom, particles, gradients, glass; cream paper, serif display, italic accents,
         "01 / 02" labels, small mono caps, pill chips; three cards in a row, KPI grids, a title over a dimmed screenshot;
         everything centred; every element fading and sliding up the same way; a docked or corner logo; text that
         drifts after it lands; any invented UI (every screen is a real capture; the cursor and click ring are the
         only drawn objects); "unlock", "seamless", "effortless", "in seconds" (not measured).
QA (checked in the render): frame 0 (hook: map + the question, not black); 100 (hook end); 200 (table filled); 330 (cursor on Kireevo);
         400 (route lit, caption); 560 (total 3.6957 + outlines); 700 (invoices outlined); 780 (guarantee outlined);
         885 (end card, button ringed). Every caption >= 28 px, inside the 80% title-safe box; every number matches the app.
```

## After the first review (2026-11-13)
- Fixed: the second click ring showed before its click and the cursor sat on the map before entering (a fromTo's start values applied at creation; every later fromTo on an element now runs with immediateRender: false); the end-card address broke mid-word; the cursor covered the button label on the held last frame; the "Know" subtitles were too long to read in their time and were cut to "50,000 kWh/d, Q4 2026" and "100,000 kWh/h, Q4 2026, CEGHIX 30".
- Left as is: HyperFrames suggests one sub-composition file per scene (the film stays one file); "film_silent" (silent by the user's choice, captions only).
- Render: docs/video/promo.mp4, H.264 1920x1080, 30 fps, 30.0 s, 5.0 MB (quality "looks", CRF 16); poster docs/video/poster.jpg is frame 0.

// Browser playback test: node pipeline/tools/verify_playback.cjs output/<id>/<id>.mp4
// Needs Playwright (preinstalled in Claude cloud sessions; elsewhere: npm i -g playwright).
const { chromium } = require('playwright');
const http = require('http'); const fs = require('fs');
const file = process.argv[2];
const srv = http.createServer((req, res) => {
  if (req.url === '/') { res.setHeader('Content-Type','text/html'); res.end(`<video id=v src="/v.mp4" muted playsinline></video>`); return; }
  const stat = fs.statSync(file); const range = req.headers.range;
  if (range) { const [s, e] = range.replace('bytes=', '').split('-'); const start = +s, end = e ? +e : stat.size - 1;
    res.writeHead(206, {'Content-Range': `bytes ${start}-${end}/${stat.size}`, 'Accept-Ranges': 'bytes', 'Content-Length': end - start + 1, 'Content-Type': 'video/mp4'});
    fs.createReadStream(file, {start, end}).pipe(res); }
  else { res.writeHead(200, {'Content-Length': stat.size, 'Content-Type': 'video/mp4'}); fs.createReadStream(file).pipe(res); }
}).listen(8765, async () => {
  const b = await chromium.launch({args:['--no-proxy-server','--autoplay-policy=no-user-gesture-required']}); const p = await b.newPage(); await p.goto('http://127.0.0.1:8765/'); 
  const r = await p.evaluate(async () => { const v = document.getElementById('v');
    await new Promise((ok, no) => { if (v.readyState >= 1) return ok(); v.onloadedmetadata = ok; v.onerror = () => no(v.error && v.error.message); });
    await v.play(); await new Promise(r => setTimeout(r, 2500));
    return { duration: v.duration, w: v.videoWidth, h: v.videoHeight, currentTime: v.currentTime, paused: v.paused, canPlayH264: v.canPlayType('video/mp4; codecs="avc1.640028"') }; });
  console.log(JSON.stringify(r)); await b.close(); srv.close();
});

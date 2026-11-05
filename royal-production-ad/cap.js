const { chromium } = require('playwright');
const { spawn } = require('child_process');
(async () => {
  const [w,h,out,only] = [process.argv[2]|0, process.argv[3]|0, process.argv[4], process.argv[5]];
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.goto(`http://127.0.0.1:8765/${process.env.PAGE || 'ad.html'}?capture=1&w=${w}&h=${h}`); await p.evaluate(() => window.ready);
  if (only) { for (const t of only.split(',')) { await p.evaluate(t => render(+t), t); await p.screenshot({ path: `shot_${t}.png` }); } await b.close(); return; }
  const ff = spawn('ffmpeg', ['-y','-f','image2pipe','-framerate','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium', out], { stdio: ['pipe','ignore','inherit'] });
  const N = (+process.env.SECS || 15) * 30;
  for (let i = 0; i < N; i++) { await p.evaluate(t => render(t), i / 30); ff.stdin.write(await p.screenshot({ type: 'jpeg', quality: 95 })); }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
})();

/* Render deterministic posters. Requires playwright-core and Chromium/Chrome. */
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const {chromium} = require('playwright-core');

(async () => {
  const root = path.resolve(__dirname, '..');
  const chrome = process.env.CHROME_PATH ||
    (process.platform === 'darwin' ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : '/usr/bin/chromium');
  const browser = await chromium.launch({executablePath: chrome, headless: true});
  const page = await browser.newPage({viewport:{width:1200,height:1500}, deviceScaleFactor:4/3});
  await page.goto(pathToFileURL(path.join(root,'design/series.html')).href);
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.decode()));
  });
  fs.mkdirSync(path.join(root,'assets/series'),{recursive:true});
  const cases = JSON.parse(fs.readFileSync(path.join(root,'design/series.json'),'utf8'));
  const measurements = [];
  for (const c of cases) {
    const element=page.locator('[id="'+c.id+'"]');
    const check=await element.evaluate(el=>{
      const footer=el.querySelector('footer').getBoundingClientRect();
      const body=el.querySelector('.insight').getBoundingClientRect();
      const bounds=el.getBoundingClientRect();
      const overflowing=[...el.querySelectorAll('h1,p,b,small,span,img')].some(node=>{
        const r=node.getBoundingClientRect();
        return r.width>0 && (r.left<bounds.left+20 || r.right>bounds.right-20);
      });
      return {width:el.offsetWidth,height:el.offsetHeight,footer_gap:footer.top-body.bottom,
        horizontal_overflow:overflowing,
        images_ok:[...el.querySelectorAll('img')].every(i=>i.naturalWidth>0)};
    });
    if(check.footer_gap<10||check.horizontal_overflow||!check.images_ok)
      throw new Error('Poster layout failed: '+c.id+' '+JSON.stringify(check));
    await element.screenshot({path:path.join(root,'assets/series',c.id+'.png')});
    measurements.push({id:c.id,...check});
  }
  await page.setViewportSize({width:1200,height:530});
  const roster=JSON.parse(fs.readFileSync(path.join(root,'data/roster.json'),'utf8')).players;
  for(const p of roster){
    const source=pathToFileURL(path.join(root,'assets/profiles',p.key+'.svg')).href;
    await page.setContent('<html><style>body{margin:0}img{display:block;width:1200px;height:530px}</style><img src="'+source+'"></html>');
    await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()))});
    await page.screenshot({path:path.join(root,'assets/profiles',p.key+'.png')});
  }
  const thumbs=cases.map(c=>'<img src="'+pathToFileURL(path.join(root,'assets/series',c.id+'.png')).href+'">').join('');
  await page.setViewportSize({width:1800,height:560});
  await page.setContent('<html><style>*{box-sizing:border-box}body{margin:0;background:#e9e4da;padding:26px;display:flex;gap:20px;align-items:center;height:560px}img{width:333px;height:auto;box-shadow:0 12px 30px #29303925;border-radius:5px}</style>'+thumbs+'</html>');
  await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode()))});
  await page.screenshot({path:path.join(root,'assets/series/overview.png')});
  fs.mkdirSync(path.join(root,'checks'),{recursive:true});
  fs.writeFileSync(path.join(root,'checks/visual-layout.json'),JSON.stringify(measurements,null,2)+'\n');
  await browser.close();
  console.log('Rendered five 1600 × 2000 PNG posters, twelve profile PNGs and series overview.');
})().catch(err=>{console.error(err);process.exit(1)});

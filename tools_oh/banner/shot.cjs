const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1440,height:810}});
for(const v of ['op18','me06']){await p.goto('file://'+process.cwd()+'/banner.html?v='+v);await p.waitForTimeout(800);await p.screenshot({path:`oh-${v}.png`});}
await b.close()})()

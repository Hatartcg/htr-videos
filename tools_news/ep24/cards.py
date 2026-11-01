from PIL import Image, ImageDraw, ImageFont
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def card(fn, top, bot, lines, sizes, colors, rule):
    W,H=900,520; im=Image.new('RGB',(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H; d.line([(0,y),(W,y)],fill=tuple(int(top[i]*(1-t)+bot[i]*t) for i in range(3)))
    total=sum(s*1.25 for s in sizes)+30; y=(H-total)/2
    for k,(s,sz,c) in enumerate(zip(lines,sizes,colors)):
        f=ImageFont.truetype(FB,sz)
        while d.textlength(s,font=f)>820: sz-=4; f=ImageFont.truetype(FB,sz)
        w=d.textlength(s,font=f); d.text(((W-w)/2,y),s,font=f,fill=c); y+=sz*1.25
        if k==rule: d.line([(200,y+8),(700,y+8)],fill=(249,115,22),width=6); y+=30
    im.save('img/'+fn)
G=(16,60,40); G2=(20,110,70)
card('rayquaza_gold.png',(40,30,8),(120,90,20),['MEGA RAYQUAZA ex','GOLD','JAPANESE · STORM EMERALDA'],[84,96,40],[(255,255,255),(250,204,21),(226,232,240)],1)
card('delta.png',G,G2,['DELTA REIGN','MEGA EVOLUTION','NOV 6, 2026'],[110,54,44],[(255,255,255),(167,243,208),(226,232,240)],1)
card('megas.png',G,G2,['135+ CARDS','4 MEGA ex','RAYQUAZA · GOLURK','MALAMAR · GOLISOPOD'],[90,70,40,40],[(255,255,255),(250,204,21),(226,232,240),(226,232,240)],1)
card('stadium.png',(30,30,70),(70,40,120),['LEGENDARY','STADIUM','2 STADIUM CARDS = 1 ARTWORK'],[96,96,36],[(255,255,255),(255,255,255),(216,180,254)],1)
R=(60,10,10); R2=(130,25,25)
card('op18.png',R,R2,['OP-18','THE DOMINANCE OF GOD','NOV 20, 2026'],[130,52,44],[(255,255,255),(254,202,202),(226,232,240)],1)
card('anniv.png',R,R2,['4TH ANNIVERSARY','P-161 MONKEY.D.LUFFY','NOV 20 – DEC 17, 2026'],[80,48,44],[(255,255,255),(253,224,71),(226,232,240)],1)
card('tip.png',(10,50,50),(15,100,95),['SINGLES PRICES','MOVE A LOT','IN THE FIRST WEEKS'],[72,72,44],[(255,255,255),(255,255,255),(153,246,228)],1)

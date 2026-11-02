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
R=(60,10,10); R2=(130,25,25)
card('nami.png',(40,30,8),(120,90,20),['NAMI · EB-05','¥198,000','JAPANESE · CARDRUSH · OCT 31'],[84,110,38],[(255,255,255),(250,204,21),(226,232,240)],1)
card('eb05.png',R,R2,['EB-05','HEROINES EDITION VOL.2','ENGLISH · OCT 30, 2026'],[130,50,44],[(255,255,255),(254,202,202),(226,232,240)],1)
G=(16,60,40); G2=(20,110,70)
card('ptc.png',G,G2,['MEGA RAYQUAZA ex','PREMIUM TOURNAMENT COLLECTION','8 PACKS · 65 DRAGON SHIELD SLEEVES'],[80,40,38],[(255,255,255),(167,243,208),(226,232,240)],1)
card('ptc_date.png',G,G2,['$49.99','FEB 12, 2027','MEGA RAYQUAZA ex PTC'],[120,64,40],[(250,204,21),(255,255,255),(226,232,240)],1)
B=(20,25,70); B2=(50,60,140)
card('inkdark.png',B,B2,['INTO THE INKDARK','COLLECTOR BOOSTERS','$35 / PACK'],[84,58,54],[(255,255,255),(191,219,254),(250,204,21)],1)
card('illus.png',B,B2,['ILLUSTRIOUS','6 PER SET · ONLY 23 COPIES EACH','SERIALIZED'],[110,40,44],[(255,255,255),(250,204,21),(191,219,254)],1)
card('tip.png',(10,50,50),(15,100,95),['JAPANESE ≠ ENGLISH','CHECK THE LANGUAGE','BEFORE YOU BUY'],[72,64,44],[(255,255,255),(255,255,255),(153,246,228)],1)

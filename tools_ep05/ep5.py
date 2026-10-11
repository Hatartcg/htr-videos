import sys, os, json, math, subprocess
sys.path.insert(0,'/home/claude/news')
import numpy as np
from PIL import Image, ImageDraw
import ep, cv2
from ep import text_img,put,eo,ebk,rrect,bg,W,H,FPS,clamp
PK=(255,170,0); OP=(239,68,68); YG=(139,92,246); LO=(20,184,166); TO=(34,197,94); PINK=(236,72,153); GOLD=(250,204,21)
# (kind, accent, character, data)
NA=(249,115,22)
S=[
 ("hook",PK,"pokemon",dict(top="أغلى تشارزرد انباع بالتاريخ",big="$1,700,000",sub="مزاد – مارس 2026")),
 ("price",PK,"pokemon",dict(chip="Pokémon TCG",tag="مو النسخة الإنجليزية!",name=["Charizard – 1996 Japanese","Base Set · No Rarity"],price="PSA 10",note="أغلى تشارزرد انباع بمزاد",src="المصدر: Sports Illustrated / Yahoo Finance")),
 ("hook",PINK,"intro",dict(top="أخبار وأسعار",big="TCG",sub="12 أكتوبر 2026")),
 ("news",NA,"naruto",dict(chip="Naruto Card Game",title=["يونيو 2027"],date="إطلاق عالمي بنفس الوقت",facts=[("من Bandai Card Games",44,True)])),
 ("news",NA,"naruto",dict(chip="Naruto Card Game",title=["3 Starter Decks"],date="ناروتو · ساسكي · غارا",facts=[("أول ديكات اللعبة",44,True)])),
 ("news",OP,"onepiece",dict(chip="One Piece",title=["Dracule Mihawk","OP14-020"],date="ممنوع من اليوم",facts=[("في البطولات الرسمية – 12 أكتوبر",40,True)])),
 ("cta",PINK,"intro",dict(q="مين تبي تلعب فيه؟",sub="ناروتو · ساسكي · غارا")),
]
DUR=[6.0]*len(S)
if os.path.exists("timing.json"): DUR=json.load(open("timing.json"))
SEG=[];t=0.0
for n,(k,acc,ch,dd) in enumerate(S): SEG.append(dict(s=t,e=t+DUR[n],acc=acc,kind=k,idx=n)); t+=DUR[n]
TOT=t; ep.SEG=SEG
def prep(n):
    a=cv2.imread(f'/home/claude/brand/char2/{n}_keyed.png',cv2.IMREAD_UNCHANGED); m=a[...,3]
    ys,xs=np.where(m>128); top,bot=ys.min(),ys.max(); cx=np.where(m[top+100:top+300]>128)[1].mean(); sc=1500.0/(bot-top)
    im=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGRA2RGBA)); im=im.resize((int(im.width*sc),int(im.height*sc)),Image.LANCZOS)
    return im,int(cx*sc),int(top*sc)
CH={n:prep(n) for n in set(x[2] for x in S)}
yy2,xx2=np.mgrid[0:900,0:900]; GL=Image.fromarray((np.clip(1-np.hypot(xx2-450,yy2-450)/450,0,1)**1.5*110).astype(np.uint8))
ENV=np.load("env.npy") if os.path.exists("env.npy") else None
def pulse(t):
    if ENV is not None: return float(ENV[min(len(ENV)-1,int(t*FPS))])
    return 0.5+0.5*math.sin(t*9.0)*(0.5+0.5*math.sin(t*1.9))
import glob
def load_img(i):
    fs=sorted(glob.glob(f"img/{i:02d}.*"))
    if not fs: return None
    im=Image.open(fs[0]).convert("RGBA"); h=600; w=int(im.width*h/im.height)
    if w>460: w=460; h=int(im.height*w/im.width)
    im=im.resize((w,h),Image.LANCZOS)
    m=Image.new("L",(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),18,fill=255)
    a=np.minimum(np.array(im.getchannel('A')),np.array(m)); im.putalpha(Image.fromarray(a)); return im
CARD={i:load_img(i) for i in range(len(S))}
def chip(img,txt,acc,y,a):
    c=text_img(txt,52,(255,255,255,255),False,0); put(img,rrect(c.width+70,84,42,acc+(255,)),W/2,y,a); put(img,c,W/2,y,a)
def frame(t):
    i=next((n for n,s in enumerate(SEG) if s["s"]<=t<s["e"]),len(SEG)-1); sg=SEG[i]; acc=tuple(int(v) for v in ep.accent(t))
    k,_,chn,dd=S[i]
    img=bg(t); d=ImageDraw.Draw(img); lt=t-sg["s"]; fo=clamp((sg["e"]-t)/0.25) if i<len(SEG)-1 else 1.0
    d.rectangle((0,0,int(W*t/TOT),9),fill=(125,211,252))
    cim,ccx,ctop=CH[chn]; inx=eo(lt/0.5); card=CARD.get(i); sx=230 if card is not None else 0; outa=clamp((sg["e"]-t)/0.2) if i<len(SEG)-1 else 1.0; al=inx*outa
    gm=GL.point(lambda v:int(v*al)); img.paste(Image.new("RGB",(900,900),acc),(int(W/2-450),1250),gm)
    am=cim.getchannel('A').point(lambda v:int(v*al)); bob=3*math.sin(t*2.2)+5*pulse(t)
    img.paste(cim.convert('RGB'),(int(W/2+sx-ccx+(1-inx)*380),int(1010-ctop+bob)),am)
    if card is not None:
        ca=eo((lt-0.4)/0.4)*outa; ang=-7+2*math.sin(t*1.3); z=0.85+0.15*ebk((lt-0.4)/0.5)
        c2=card.resize((int(card.width*z),int(card.height*z)),Image.LANCZOS)
        gl=Image.new("RGBA",(c2.width+80,c2.height+80),(0,0,0,0)); ImageDraw.Draw(gl).rounded_rectangle((20,20,c2.width+60,c2.height+60),30,fill=acc+(140,))
        from PIL import ImageFilter
        gl=gl.filter(ImageFilter.GaussianBlur(22)); gl.alpha_composite(c2,(40,40)); gl=gl.rotate(ang,resample=Image.BICUBIC,expand=True)
        al2=gl.getchannel('A').point(lambda v:int(v*ca)); cx,cy=330,1330+int(8*math.sin(t*1.7))
        img.paste(gl.convert('RGB'),(int(cx-gl.width/2),int(cy-gl.height/2)),al2)
    pa=eo(lt/0.3)*fo
    if k=="hook":
        put(img,text_img(dd["top"],66,(255,255,255,255),True,4),W/2,420,eo(lt/0.4))
        z=1.0+0.25*(1-ebk((lt-0.3)/0.6)); put(img,text_img(dd["big"],190 if len(dd["big"])<6 else 140,GOLD+(255,),False,8),W/2,620,eo((lt-0.3)/0.3),z)
        put(img,text_img(dd["sub"],56,(125,211,252,255),True,0),W/2,820,eo((lt-1.2)/0.4))
    elif k=="price":
        put(img,rrect(940,660,56,(16,20,52,236),acc+(255,),8),W/2,670,pa,0.92+0.08*ebk(lt/0.4))
        chip(img,dd["chip"],acc,400,eo((lt-0.2)/0.3)*fo)
        put(img,text_img(dd["tag"],50,(255,255,255,255),True,0),W/2,500,eo((lt-0.35)/0.3)*fo)
        for j,ln in enumerate(dd["name"]): put(img,text_img(ln,(64 if len(ln)<20 else 52) if j==0 else 46,(235,238,255,255),False,2),W/2,590+j*70,eo((lt-0.5)/0.35)*fo)
        z=1.0+0.3*(1-ebk((lt-0.9)/0.5)); put(img,text_img(dd["price"],150,GOLD+(255,),False,6),W/2,785,eo((lt-0.9)/0.3)*fo,z)
        put(img,text_img(dd["note"],42,acc+(255,),True,0),W/2,915,eo((lt-1.5)/0.4)*fo)
        if dd.get("src"): put(img,text_img(dd["src"],30,(170,176,205,255),True,0),W/2,968,eo((lt-1.8)/0.4)*fo)
    elif k=="news":
        put(img,rrect(940,650,56,(16,20,52,236),acc+(255,),8),W/2,665,pa,0.92+0.08*ebk(lt/0.4))
        chip(img,dd["chip"],acc,420,eo((lt-0.2)/0.3)*fo)
        put(img,text_img("جديد",40,(255,255,255,255),True,0),W-170,300,pa)
        title=dd["title"]; tsz=84 if len(title)==1 else 66
        for j,ln in enumerate(title): put(img,text_img(ln,tsz,(255,255,255,255),False,3),W/2,545+j*(tsz+8),eo((lt-0.45)/0.35)*fo)
        ty=545+(len(title)-1)*(tsz+8)
        put(img,text_img(dd["date"],64,acc+(255,),True,0),W/2,ty+110,ebk((lt-0.8)/0.4)*fo)
        for j,(tx,sz,rtl) in enumerate(dd["facts"]): put(img,text_img(tx,sz,(235,238,255,255),rtl,0),W/2,ty+210+j*78,eo((lt-1.2-0.4*j)/0.35)*fo)
    else:
        put(img,text_img(dd.get("q","وش أغلى كرت عندك؟"),84,(255,255,255,255),True,5),W/2,480,ebk(lt/0.5))
        put(img,text_img(dd.get("sub","اكتبه بالتعليقات"),64,(125,211,252,255),True,0),W/2,650,eo((lt-0.4)/0.4))
        put(img,text_img("اكتب اختيارك بالتعليقات",48,acc+(255,),True,0),W/2,790,eo((lt-0.9)/0.4))
    d.rectangle((0,1806,W,1920),fill=(10,12,34)); d.rectangle((0,1806,W,1812),fill=acc)
    put(img,text_img("أخبار وأسعار TCG",46,(255,255,255,255),True,0),300,1862)
    if lt<0.2 and i>0: img=Image.blend(img,Image.new("RGB",(W,H),(255,255,255)),int(150*(1-lt/0.2))/255)
    return img
if __name__=="__main__":
    if sys.argv[1]=="test":
        ts=[float(x) for x in sys.argv[2:]]; ims=[frame(x).resize((360,640)) for x in ts]
        sh=Image.new("RGB",(360*len(ims),640)); [sh.paste(im,(360*n,0)) for n,im in enumerate(ims)]; sh.save("test.png"); print(TOT)
    else:
        p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p","base_news5.mp4"],stdin=subprocess.PIPE)
        for n in range(int(TOT*FPS)):
            p.stdin.write(frame(n/FPS).tobytes())
            if n%150==0: print(n,flush=True)
        p.stdin.close(); p.wait(); print("done")

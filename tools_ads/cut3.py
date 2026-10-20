from PIL import Image
import numpy as np, cv2
F='/home/claude/htr-videos/fetch/'
def cut(im, thr=170, sat=40, minfrac=.02):
    a=np.array(im.convert('RGB')).astype(np.int32); h,w=a.shape[:2]
    light=(a.min(2)>thr)&((a.max(2)-a.min(2))<sat)
    n,lab=cv2.connectedComponents(light.astype(np.uint8),connectivity=4)
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bg=np.isin(lab,list(border)); fg=(~bg).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(fg,connectivity=8); keep=np.zeros_like(fg)
    for i in range(1,n):
        if st[i,4]>minfrac*h*w: keep[lab==i]=1
    keep=cv2.morphologyEx(keep,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)); keep=cv2.erode(keep,np.ones((3,3),np.uint8))
    al=cv2.GaussianBlur(keep.astype(np.float32),(0,0),.9)
    o=Image.fromarray(np.dstack([a.astype(np.uint8),(al*255).astype(np.uint8)]),'RGBA'); return o.crop(o.getbbox())
def save(o,k): o.thumbnail((900,900)); o.save(f'img/{k}.png'); print(k,o.size)
# riftbound box + pack
r=Image.open(F+'rift_box2.jpg').convert('RGB'); W,H=r.size
save(cut(r.crop((0,0,int(W*.62),H))),'rift')
save(cut(r.crop((int(W*.67),0,W,H))),'pk_rift')
# 30th packs
c=Image.open(F+'celeb_etb2.png').convert('RGB'); save(cut(c.crop((90,235,520,440)),thr=246,sat=255,minfrac=.01),'pk_30')
# op16 packs (left part)
o=Image.open(F+'site/p_op16.img').convert('RGB'); W,H=o.size; save(cut(o.crop((0,0,int(W*.335),H))),'pk_op16'); save(cut(o.crop((int(W*.385),0,W,H))),'op16box')
# ygo: drop binder on top
y=Image.open('img/ygo_full.png'); yc=y.crop((0,int(y.height*.43),y.width,y.height)); save(yc.crop(yc.getbbox()),'ygo')
# eb05 pack on black bg
e=Image.open(F+'eb05en_pb1.webp').convert('RGB'); a=np.array(e); m=(a.max(2)>30).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(m); i=1+np.argmax(st[1:,4]); x,yy,w,h=st[i,:4]
save(e.crop((x+2,yy+2,x+w-2,yy+h-2)).convert('RGBA'),'pk_eb05')

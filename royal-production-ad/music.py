import numpy as np, wave
sr=44100; T=15; n=sr*T; t=np.arange(n)/sr; out=np.zeros((n,2))
rng=np.random.default_rng(1)
def add(sig,start,gain=1.0,pan=0.0):
    i=int(start*sr); j=min(n,i+len(sig)); s=sig[:j-i]*gain
    out[i:j,0]+=s*(1-pan)/1; out[i:j,1]+=s*(1+pan)/1
def env(L,a,d):
    tt=np.arange(int(L*sr))/sr; return np.minimum(1,tt/a)*np.exp(-tt/d)
def kick():
    L=.5; tt=np.arange(int(L*sr))/sr; f=45+110*np.exp(-tt*28)
    return np.sin(2*np.pi*np.cumsum(f)/sr)*env(L,.002,.16)
def boom():
    L=3; tt=np.arange(int(L*sr))/sr; f=35+70*np.exp(-tt*6)
    s=np.sin(2*np.pi*np.cumsum(f)/sr)*env(L,.003,.9)
    nz=rng.standard_normal(len(tt)); nz=np.convolve(nz,np.ones(40)/40,'same')*env(L,.002,.25)
    return s+nz*1.2
def whoosh(L=.8):
    nz=rng.standard_normal(int(L*sr)); tt=np.arange(len(nz))/sr
    k=np.convolve(nz,np.ones(25)/25,'same'); hp=nz-k
    shape=np.sin(np.pi*tt/L)**2
    return (k*.8+hp*.25)*shape
def shutter():
    s=np.zeros(int(.25*sr))
    for d in (0,.07):
        nz=rng.standard_normal(int(.03*sr))*np.exp(-np.arange(int(.03*sr))/sr/.006)
        i=int(d*sr); s[i:i+len(nz)]+=nz
    return s
def hat():
    nz=rng.standard_normal(int(.08*sr)); nz=nz-np.convolve(nz,np.ones(6)/6,'same')
    return nz*np.exp(-np.arange(len(nz))/sr/.02)
# pad: Am - F - C - G  (each 3.4s-ish), saw-ish detuned chords
def note(f,L):
    tt=np.arange(int(L*sr))/sr; s=0
    for dt in (-.4,0,.4):
        for h in range(1,7): s=s+np.sin(2*np.pi*(f+dt)*h*tt)/h**1.6
    a=np.minimum(1,tt/.6)*np.minimum(1,(L-tt)/.6)
    return s*a
chords=[(0,[110,130.81,164.81,220]),(3.2,[87.31,130.81,174.61,220]),(6.6,[130.81,164.81,196,261.63]),(10,[98,146.83,196,246.94,293.66])]
for i,(st,ch) in enumerate(chords):
    L=(chords[i+1][0] if i+1<len(chords) else 15)-st+.6
    for f in ch: add(note(f,L),st,.018)
    add(note(ch[0]/2,L),st,.05)
# rhythm 120bpm starting at 1.0s, stops at 9.4, then final
bpm=120; b=60/bpm
for k in range(int((9.4-1.0)/b)+1):
    tk=1.0+k*b
    add(kick(),tk,.55)
    add(hat(),tk+b/2,.12,pan=.3)
    if k>=6: add(hat(),tk+b/4,.06,pan=-.3); add(hat(),tk+3*b/4,.06,pan=-.3)
# riser into logo
L=1.6; tt=np.arange(int(L*sr))/sr; f=200+1800*(tt/L)**2
riser=np.sin(2*np.pi*np.cumsum(f)/sr)*(tt/L)**2*.25+rng.standard_normal(len(tt))*(tt/L)**3*.25
add(riser,8.4,.5)
for tw in (2.75,6.15): add(whoosh(),tw,.5)
add(shutter(),3.1,.6); add(shutter(),6.5,.6); add(shutter(),9.9,.4)
add(boom(),3.15,.5); add(boom(),6.55,.5); add(boom(),9.95,.9)
# master: fades + soft clip
fade=np.ones(n); fade[:int(.3*sr)]=np.linspace(0,1,int(.3*sr)); fade[-int(1.2*sr):]=np.linspace(1,0,int(1.2*sr))
out*=fade[:,None]; out=np.tanh(out*1.3); out/=np.abs(out).max()*1.12
w=wave.open('music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
w.writeframes((out*32767).astype('<i2').tobytes()); w.close()

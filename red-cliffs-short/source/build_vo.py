import numpy as np, wave, json, subprocess, sys
SR=24000
def rd(p):
    w=wave.open(p); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; return a
segs=[];times=[];t=0.0
lead=np.zeros(int(0.35*SR))
out=[lead]; t=0.35
for i in range(1,14):
    a=rd(f'vo/s{i:02d}.wav')
    env=np.abs(a)>0.01; idx=np.where(env)[0]
    a=a[max(0,idx[0]-int(0.04*SR)):min(len(a),idx[-1]+int(0.08*SR))]
    times.append([round(t,3),round(t+len(a)/SR,3)])
    out.append(a); gap=0.55 if i<13 else 1.6
    out.append(np.zeros(int(gap*SR))); t+=len(a)/SR+gap
v=np.concatenate(out); v=v/np.max(np.abs(v))*0.89
w=wave.open('vo/voiceover.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((v*32767).astype(np.int16).tobytes()); w.close()
json.dump({'scenes':times,'total':round(t,3)},open('vo/timing.json','w'),indent=1)
print(times, t)

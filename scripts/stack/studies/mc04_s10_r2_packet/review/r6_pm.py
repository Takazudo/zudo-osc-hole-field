import math
GBW=2.5e6; R=50e3
for cs in (0,5.96,10,20, 26.16*0.2):
    C=(8+cs)*1e-12; fp=1/(2*math.pi*R*C)
    u=(-fp**2+math.sqrt(fp**4+4*fp**2*(GBW/2)**2))/2; fc=math.sqrt(u)
    print(round(cs,2),'pF node',round(C*1e12,2),'pole kHz',round(fp/1e3,1),'fc kHz',round(fc/1e3,1),'PM',round(90-math.degrees(math.atan(fc/fp)),1))

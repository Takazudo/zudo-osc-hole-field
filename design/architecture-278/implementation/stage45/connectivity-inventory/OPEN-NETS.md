# Stage45 inherited local routing inventory

Generated from the accepted Stage44 snapshot. All 117 opens remain failures.
Groups separated by ` / ` are disconnected native components. A large group
is abbreviated here; `inventory.json` contains every pad, coordinate and mate.
The edge count is the minimum links needed, not an approved routing tree.

| Semantic net | Missing links | Class | Disconnected pad groups |
|---|---:|---|---|
| AGND | 14 | ground | 1156 pads (main component; see JSON) / R8270:2 / R8173:2 / R8273:2 / R8105:2 / C2248:2 / RB2214:2 / J900047:6 / C8142:2 / R8107:2 / U2205:10, U2205:11, U2205:14, U2205:15, U2205:16, U2205:9 / U8202:14, U8202:15, U8202:16 / RB2315:2 / J900027:4 / J900027:2 |
| /O2/SIN_SCALED | 1 | local feed on interface net | J900035:3 / U1216:12 |
| /O2/1V_BUFFER | 1 | local feed on interface net | U1218:1, U1218:2 / J900033:1 |
| /F2/BP_TIP | 1 | local circuit | J706:T / RB2209:2 |
| /M5A/4_BUFFER | 1 | local feed on interface net | J900017:5 / U8112:13, U8112:14 |
| /F2/IN_BUFFER | 2 | local feed on interface net | U2219:3 / U2217:1, U2217:2 / J900007:3 |
| /O1/SYNC_BUFFER | 1 | local feed on interface net | U1116:8, U1116:9 / J900031:5 |
| /H1/TRIGGER_BUFFERED | 1 | local feed on interface net | J900013:3 / U106:1, U106:10, U106:2 |
| /F1/C9dddda_ENABLE | 1 | local circuit | R2109:1, R2110:2 / U2103:1 |
| /M5B/REFN5 | 1 | local feed on interface net | U8214:2 / J900027:3 |
| /M5B/C819409_SENSE | 1 | local circuit | D8212:3, U8215:3 / R8248:2 |
| /X1/SELECTOR_REMOTE | 1 | local feed on interface net | U3305:10 / J900055:1 |
| /M5B/3_BUFFER | 1 | local feed on interface net | U8212:8, U8212:9 / J900023:5 |
| /O2/TRI_SCALED | 1 | local feed on interface net | U1217:3 / J900035:7 |
| /O2/PUL_SCALED | 1 | local feed on interface net | J900033:5 / U1217:10 |
| /M5A/C02cf7e_DRIVE | 1 | local circuit | R8167:1 / U8115:6, U8115:7 |
| /M5A/2_BUFFER | 1 | local feed on interface net | J900015:5 / U8112:6, U8112:7 |
| /O1/SAW_SCALED | 1 | local feed on interface net | U1117:5 / J900031:1 |
| /F1/GAIN_PROTECTED | 1 | local circuit | U2105:2 / R2119:1, R2120:1 |
| /F2/RES_BUFFER | 1 | local feed on interface net | U2217:8, U2217:9, U2219:10 / J900007:7 |
| /F3/FREQ_BUFFER | 1 | local feed on interface net | U2317:6, U2317:7, U2319:5 / J900009:5 |
| /O2/PWM_BUFFER | 1 | local feed on interface net | J900033:7 / U1216:6, U1216:7 |
| /M5A/REFN5 | 1 | local feed on interface net | U8114:2 / J900019:7 |
| /M5B/Cf1bc56_SENSE | 2 | local circuit | D8228:1 / R8272:1, U8216:6 / D8226:2 |
| /F2/Cb6d8fd_LED_A | 1 | local circuit | D702:2 / D2230:1, D2231:1 |
| /M5B/5_GAIN | 1 | local feed on interface net | J900025:7 / U8216:10 |
| /X1/A_BUFFER | 2 | local feed on interface net | U3305:1, U3305:2 / U3304:3 / J900053:1 |
| /F2/C85710f_ENABLE | 1 | local circuit | U2204:1 / R2213:1, R2214:2 |
| /O2/FM_BUFFER | 1 | local feed on interface net | J900033:3 / U1216:1, U1216:2 |
| /M5B/5_TIP | 1 | local circuit | U8206:3 / J1005:T |
| /O1/1V_BUFFER | 1 | local feed on interface net | J900029:1 / U1118:1, U1118:2 |
| /M5B/3_TIP | 1 | local circuit | J1003:T / U8204:3 |
| /M5A/1_PROTECTED | 2 | local circuit | R8108:1 / U8102:2 / R8107:1 |
| /F3/IN_PROTECTED | 2 | local circuit | U2302:2 / R2307:1 / R2308:1 |
| /M5B/1_BUFFER | 1 | local feed on interface net | U8212:1, U8212:2 / J900021:5 |
| /F3/DRY_CORE | 1 | local feed on interface net | J900009:3 / U2318:12 |
| /M5B/4_TIP | 1 | local circuit | J1004:T / U8205:3 |
| /M5B/5_PROTECTED | 1 | local circuit | R8247:1, R8248:1 / U8206:2 |
| /F1/GAIN_BUFFER | 2 | local feed on interface net | U2119:12 / U2117:13, U2117:14 / J900001:7 |
| /M5A/5_GAIN | 1 | local feed on interface net | J900019:3 / U8116:10 |
| /O1/SIN_SCALED | 1 | local feed on interface net | U1116:12 / J900031:3 |
| /M5A/3_PROTECTED | 2 | local circuit | R8127:1 / R8128:1 / U8104:2 |
| /M5A/C6236f5_SENSE | 1 | local circuit | D8122:2, D8124:1, R8171:1 / U8116:2 |
| /F2/FREQ_BUFFER | 1 | local feed on interface net | U2217:6, U2217:7, U2219:5 / J900005:5 |
| /M5A/1_BUFFER | 1 | local feed on interface net | J900015:1 / U8112:1, U8112:2 |
| /M5B/Cf1bc56_DRIVE | 1 | local circuit | D8225:2, D8227:1 / U8216:7 |
| /M5A/SUM_PRELEVEL | 1 | local feed on interface net | J900021:3 / U8117:3 |
| /F3/HP_CORE | 1 | local feed on interface net | J900011:1 / U2318:10 |
| /F3/BP_CORE | 1 | local feed on interface net | J900009:1 / U2318:5 |
| /M5B/C8568b9_SENSE | 1 | local circuit | R8208:2, U8212:3 / D8208:3 |
| /M5A/5_BUFFER | 1 | local feed on interface net | J900019:1 / U8115:1, U8115:2 |
| /O2/SYNC_BUFFER | 1 | local feed on interface net | J900035:5 / U1216:8, U1216:9 |
| /F2/BP_CORE | 1 | local feed on interface net | U2218:5 / J900005:1 |
| /O2/SAW_SCALED | 1 | local feed on interface net | U1217:5 / J900035:1 |
| /F1/FREQ_BUFFER | 1 | local feed on interface net | U2117:6, U2117:7, U2119:5 / J900001:5 |
| /F1/DRY_CORE | 1 | local feed on interface net | U2118:12 / J900001:3 |
| /M5B/SUM_PRELEVEL | 1 | local feed on interface net | U8217:3 / J900027:7 |
| /M5A/SUM_POSTLEVEL | 2 | local feed on interface net | U8115:5 / J900021:1 / U8116:12 |
| /F3/IN_BUFFER | 1 | local feed on interface net | J900011:3 / U2317:1, U2317:2, U2319:3 |
| /M5B/Cf1bc56_LED_K | 2 | local circuit | D8228:2 / D8227:2 / D1004:1 |
| /F1/IN_BUFFER | 1 | local feed on interface net | U2117:1, U2117:2, U2119:3 / J900003:3 |
| /F2/C56c9d6_DRIVE | 1 | local circuit | U2218:13, U2218:14 / RB2212:1 |
| /F3/Cb3d4a2_LED_A | 1 | local circuit | D2325:1, D2326:1 / D801:2 |
| /X1/B_BUFFER | 1 | local feed on interface net | U3304:5, U3305:6, U3305:7 / J900053:3 |
| /M5B/SUM_POSTLEVEL | 2 | local feed on interface net | U8215:5 / U8216:12 / J900027:5 |
| /M5B/2_BUFFER | 1 | local feed on interface net | U8212:6, U8212:7 / J900023:1 |
| /F2/GAIN_BUFFER | 1 | local feed on interface net | U2217:13, U2217:14, U2219:12 / J900005:7 |
| /M5B/2_GAIN | 1 | local feed on interface net | U8215:12 / J900023:3 |
| /O1/PWM_BUFFER | 1 | local feed on interface net | U1116:6, U1116:7 / J900029:7 |
| /M5A/C6236f5_DRIVE | 1 | local circuit | D8121:2, D8123:1 / U8116:1 |
| /F3/LP_CORE | 1 | local feed on interface net | J900011:5 / U2318:3 |
| /X2/B_BUFFER | 2 | local feed on interface net | J900057:1 / U3405:6, U3405:7 / U3404:5 |
| /H2/TRIGGER_BUFFERED | 1 | local feed on interface net | U206:1, U206:10, U206:2 / J900013:7 |
| /M5B/3_GAIN | 1 | local feed on interface net | U8216:3 / J900023:7 |
| /M5B/C81f845_ENABLE | 1 | local circuit | R8245:1, R8246:2 / U8206:1 |
| /H2/IN_BUFFERED | 1 | local feed on interface net | U206:12, U206:6, U206:7 / J900013:5 |
| /M5B/4_GAIN | 1 | local feed on interface net | J900025:3 / U8216:5 |
| /F2/LP_TIP | 1 | local circuit | RB2207:2 / J705:T |
| /H1/IN_BUFFERED | 1 | local feed on interface net | J900013:1 / U106:12, U106:6, U106:7 |
| /M5A/REF5 | 1 | local feed on interface net | J900019:5 / U8113:3 |
| /F1/HP_TIP | 1 | local circuit | RB2111:2 / J607:T |
| /M5B/C6a2619_CLIP_N | 1 | local circuit | D10061:1, U8213:1 / U8214:1 |
| /F3/C945bba_SENSE | 1 | local circuit | D2303:3, U2317:10 / R2316:2 |
| /X2/A_BUFFER | 2 | local feed on interface net | J900055:3 / U3405:1, U3405:2 / U3404:3 |
| /F2/Cb6d8fd_LED_K | 1 | local circuit | D2232:2, D2233:2 / D702:1 |
| /M5B/1_GAIN | 1 | local feed on interface net | U8215:10 / J900021:7 |
| /M5A/C819409_SENSE | 2 | local circuit | R8148:2 / D8112:3 / U8115:3 |
| /F3/GAIN_BUFFER | 2 | local feed on interface net | U2317:13, U2317:14 / U2319:12 / J900009:7 |
| /F2/DRY_CORE | 1 | local feed on interface net | U2218:12 / J900005:3 |
| /O1/FM_BUFFER | 1 | local feed on interface net | U1116:1, U1116:2 / J900029:3 |

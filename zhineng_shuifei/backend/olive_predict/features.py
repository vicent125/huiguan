"""Shared training/inference features. All inputs end at the forecast origin."""
from pathlib import Path
import numpy as np
import pandas as pd
RAW_COLS=['vwc_m3_m3','soil_temp_c','bulk_ec_ds_m']
def daily_from_raw(raw):
    raw=raw.copy()
    raw['timestamp']=pd.to_datetime(raw['timestamp'],errors='raise')
    raw=raw.sort_values(['site_id','timestamp'])
    raw['date']=raw.timestamp.dt.floor('D')
    for c in RAW_COLS:raw[c]=pd.to_numeric(raw[c],errors='coerce')
    rows=[]
    for (site,dt),g in raw.groupby(['site_id','date'],sort=True):
        rec={'site_id':site,'date':dt,'n_obs':len(g),'last_minute':int(g.timestamp.iloc[-1].hour*60+g.timestamp.iloc[-1].minute)}
        rec['eligible_day']=bool(len(g)>=72 and not g.timestamp.duplicated().any() and g[RAW_COLS].count().min()>=72
            and g.vwc_m3_m3.between(0,.8).all() and g.soil_temp_c.between(-40,65).all() and g.bulk_ec_ds_m.between(0,20).all() and rec['last_minute']>=1410)
        for c in RAW_COLS:
            a=g[c]
            rec[c]=a.mean()
            rec[c+'_last']=a.iloc[-1]
            rec[c+'_min']=a.min();rec[c+'_max']=a.max();rec[c+'_std']=a.std()
            evening=g.loc[g.timestamp.dt.hour>=18,c]
            rec[c+'_evening_mean']=evening.mean()
            rec[c+'_evening_change']=evening.iloc[-1]-evening.iloc[0] if len(evening)>=2 else np.nan
        rec['vwc_day_change']=g.vwc_m3_m3.iloc[-1]-g.vwc_m3_m3.iloc[0]
        rec['vwc_end_minus_mean']=rec['vwc_m3_m3_last']-rec['vwc_m3_m3']
        rows.append(rec)
    return pd.DataFrame(rows)

def frame_features(daily):
    frames=[]
    for site,g in daily.groupby('site_id',sort=True):
        g=g.copy();g['date']=pd.to_datetime(g['date']);g=g.set_index('date').sort_index()
        if g.index.duplicated().any():raise ValueError('duplicate site/date')
        g=g.asfreq('D')
        # Identical core and enhanced targets; 15 valid consecutive history days.
        f=g[[c for c in g if c not in ['site_id','eligible_day','n_obs','last_minute']]].copy()
        for c in RAW_COLS:
            for lag in [1,2,3,7,14]:f[f'{c}_lag{lag}']=g[c].shift(lag)
            for w in [3,7,14]:
                f[f'{c}_mean{w}']=g[c].rolling(w,min_periods=w).mean()
                f[f'{c}_std{w}']=g[c].rolling(w,min_periods=w).std()
            f[f'{c}_change1']=g[c].diff()
        f['vwc_last_lag1']=g.vwc_m3_m3_last.shift(1)
        f['sin_doy']=np.sin(2*np.pi*g.index.dayofyear/365.25);f['cos_doy']=np.cos(2*np.pi*g.index.dayofyear/365.25)
        f['site2']=(site=='Site2')*1.0
        f['history_valid']=g.eligible_day.fillna(False).astype(int).rolling(15,min_periods=15).min().eq(1)
        f['date']=f.index;f['site_id']=site
        for h in [1,2,3]:
            f[f'target_{h}']=g.vwc_m3_m3.shift(-h).where(f.history_valid & g.eligible_day.shift(-h).eq(True))
        frames.append(f)
    return pd.concat(frames).reset_index(drop=True)
def feature_sets(frame):
    core=RAW_COLS+['vwc_m3_m3_lag1','vwc_m3_m3_lag2','vwc_m3_m3_lag7','vwc_m3_m3_mean7','vwc_m3_m3_change1','sin_doy','cos_doy']
    compact=core+['site2','vwc_m3_m3_last','vwc_m3_m3_evening_mean','vwc_m3_m3_evening_change','vwc_m3_m3_std','vwc_day_change','vwc_end_minus_mean','vwc_last_lag1']
    rich=[c for c in frame if c not in ['date','site_id','history_valid','target_1','target_2','target_3']]
    return {'core':core,'compact':compact,'rich':rich}

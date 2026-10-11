"""Production inference, sharing the exact feature builder with training."""
from pathlib import Path
from functools import lru_cache
from datetime import date,timedelta
import warnings
import numpy as np,pandas as pd,joblib
from .features import daily_from_raw,frame_features,RAW_COLS

@lru_cache(maxsize=9)
def _load(path,mtime_ns):
    return joblib.load(path)  # trusted local files only; never accept model uploads

def predict_features(artifact,df):
    if artifact['kind']=='baseline':
        return df[artifact['column']].to_numpy()
    preds=[]
    for member in artifact['members']:
        anchor=df['vwc_m3_m3' if member['spec']['anchor']=='mean' else 'vwc_m3_m3_last'].to_numpy()
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='X does not have valid feature names, but LGBMRegressor was fitted with feature names')
            delta=member['model'].predict(df[member['columns']])
        preds.append(np.clip(anchor+member['alpha']*delta,0,.8))
    return np.average(preds,axis=0,weights=artifact['weights'])

def _number(x,name,lo,hi):
    if isinstance(x,bool):raise ValueError(f'{name}: numeric value required')
    try:x=float(x)
    except (TypeError,ValueError):raise ValueError(f'{name}: numeric value required')
    if not np.isfinite(x) or not lo<=x<=hi:raise ValueError(f'{name}: out of range')
    return x

def prepare_history(data):
    """Return one model row or an explicit missing-data result."""
    site=data['site_id'];asof=date.fromisoformat(data['as_of_date'])
    expected=pd.date_range(asof-timedelta(days=14),asof,freq='D')
    if data.get('history_15min'):
        records=data['history_15min']
        if not isinstance(records,list) or not all(isinstance(r,dict) for r in records):
            raise ValueError('history_15min must be a list of objects')
        raw=pd.DataFrame(records)
        if not {'timestamp',*RAW_COLS}.issubset(raw.columns):
            raise ValueError('history_15min requires timestamp,vwc_m3_m3,soil_temp_c,bulk_ec_ds_m')
        if 'site_id' in raw and not raw.site_id.eq(site).all():raise ValueError('mixed sites in history_15min')
        raw['site_id']=site
        raw['timestamp']=pd.to_datetime(raw.timestamp,errors='raise')
        if raw.timestamp.dt.tz is not None:
            raw['timestamp']=raw.timestamp.dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
        if raw.timestamp.isna().any():raise ValueError('null timestamp')
        if (raw.timestamp>=pd.Timestamp(asof)+pd.Timedelta(days=1)).any():raise ValueError('future observation beyond as_of_date')
        raw=raw[raw.timestamp>=expected[0]].copy()
        if raw.timestamp.duplicated().any():raise ValueError('duplicate timestamps')
        if ((raw.timestamp.dt.minute%15!=0)|(raw.timestamp.dt.second!=0)).any():
            raise ValueError('expected quarter-hour measurements')
        daily=daily_from_raw(raw)
    elif data.get('history_daily'):
        records=data['history_daily']
        if not isinstance(records,list) or not all(isinstance(r,dict) for r in records):
            raise ValueError('history_daily must be a list of objects')
        daily=pd.DataFrame(records).copy()
        if 'date' not in daily:raise ValueError('history_daily requires date')
        if 'site_id' in daily and not daily.site_id.eq(site).all():raise ValueError('mixed sites in history_daily')
        daily['site_id']=site;daily['date']=pd.to_datetime(daily.date,errors='raise')
        if daily.date.isna().any():raise ValueError('null date')
        if (daily.date>pd.Timestamp(asof)).any():raise ValueError('future daily record')
        if daily.date.duplicated().any():raise ValueError('duplicate daily dates')
        daily=daily[daily.date>=expected[0]].sort_values('date').copy()
        needed=['n_obs','last_minute','eligible_day','vwc_day_change','vwc_end_minus_mean']
        for c in RAW_COLS:needed.extend([c,c+'_last',c+'_min',c+'_max',c+'_std',c+'_evening_mean',c+'_evening_change'])
        missing=[c for c in needed if c not in daily]
        if missing:return None,{'status':'needs_inputs','daily':[],'missing':missing,'hint':'Use history_15min or aggregates from daily_from_raw; old day means alone are insufficient.'}
        for _,r in daily.iterrows():
            count=_number(r['n_obs'],'n_obs',72,96)
            if count!=int(count):raise ValueError('n_obs must be integer')
            _number(r['last_minute'],'last_minute',1410,1439)
            if not isinstance(r['eligible_day'],(bool,np.bool_)) or not bool(r['eligible_day']):
                raise ValueError('eligible_day must be true from verified daily aggregation')
            for c,low,high in [('vwc_m3_m3',0,.8),('soil_temp_c',-40,65),('bulk_ec_ds_m',0,20)]:
                for suffix in ['', '_last','_min','_max','_evening_mean']:_number(r[c+suffix],c+suffix,low,high)
                _number(r[c+'_std'],c+'_std',0,high-low)
                _number(r[c+'_evening_change'],c+'_evening_change',low-high,high-low)
                if not r[c+'_min']<=r[c]<=r[c+'_max']:raise ValueError('daily mean outside min/max')
            _number(r['vwc_day_change'],'vwc_day_change',-.8,.8)
            _number(r['vwc_end_minus_mean'],'vwc_end_minus_mean',-.8,.8)
    else:
        return None,{'status':'needs_inputs','daily':[],'missing':['15 complete consecutive days of history_15min or enriched history_daily']}
    if len(daily)!=15 or not pd.DatetimeIndex(daily.sort_values('date').date).equals(expected):
        raise ValueError('history must contain 15 consecutive days ending at as_of_date')
    if not daily.eligible_day.eq(True).all():
        raise ValueError('history contains incomplete, stale or out-of-range sensor days')
    feature=frame_features(daily).tail(1)
    if not feature.history_valid.iloc[0]:raise ValueError('invalid model history')
    return feature,None

def moisture_forecast(data,days,model_dir):
    if data.get('region')!='雅安' or data.get('site_id') not in ['Site1','Site2']:
        return {'status':'outside_training_sites','daily':[],'missing':['local validation and exact site mapping; Xichang has not been validated']}
    feature,missing=prepare_history(data)
    if missing:return missing
    asof=date.fromisoformat(data['as_of_date']);rows=[];drift=set()
    for h in range(1,days+1):
        path=Path(model_dir)/f'moisture_h{h}.joblib'
        if not path.exists():return {'status':'model_missing','daily':[],'missing':[str(path)]}
        artifact=_load(str(path.resolve()),path.stat().st_mtime_ns)
        if artifact.get('history_days')!=15:raise ValueError('Model mismatch: use optimized v2.1 artifacts')
        for c,(low,high) in artifact.get('feature_bounds',{}).items():
            if not low<=float(feature[c].iloc[0])<=high:drift.add(c)
        pred=float(predict_features(artifact,feature)[0])
        if not np.isfinite(pred):raise ValueError('model returned nonfinite prediction')
        q=artifact['q90_by_site'][data['site_id']]
        members=[{'family':m['spec']['family'],'features':m['spec']['features'],'shrinkage_weight':m['alpha']} for m in artifact.get('members',[])]
        rows.append({'date':(asof+timedelta(days=h)).isoformat(),'vwc_m3_m3':round(pred,6),'lower90':round(max(0,pred-q),6),'upper90':round(min(.8,pred+q),6),'model':artifact['winner'],'members':members})
    return {'status':'historical_model_needs_local_confirmation','daily':rows,'out_of_training_range_features':sorted(drift),'warning':'2023H2 was previously viewed and is a recheck, not a new blind test. Soil moisture is not a causal no-irrigation forecast. Coordinates, crop and sensor calibration require confirmation; nominal intervals may under-cover.'}

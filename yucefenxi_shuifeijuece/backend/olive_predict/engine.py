"""Olive prediction and explicit-unit water/nutrient budgets. No actuator calls."""
from pathlib import Path
from datetime import date,timedelta
import calendar,json,math
from functools import lru_cache

class InputError(ValueError): pass

def number(value,name,lo=None,hi=None):
    if isinstance(value,bool): raise InputError(f'{name} must be numeric')
    try: x=float(value)
    except (ValueError,TypeError): raise InputError(f'{name} must be numeric')
    if not math.isfinite(x) or (lo is not None and x<lo) or (hi is not None and x>hi):
        raise InputError(f'{name} outside permitted range')
    return x

def require(obj,keys):return [k for k in keys if obj.get(k) is None]

def water_budget(data,days):
    cfg=data.get('water') or {}
    required=['root_zone_vwc','field_capacity_vwc','wilting_point_vwc','root_depth_m','irrigation_efficiency','depletion_fraction','kc','max_gross_mm_day','effective_rain_fraction']
    missing=require(cfg,required)
    if missing:return {'status':'needs_inputs','missing':missing,'daily':[]}
    if cfg.get('root_zone_representative') is not True:return {'status':'needs_inputs','missing':['root_zone_representative=true after root-zone calibration'],'daily':[]}
    theta=number(cfg['root_zone_vwc'],'root_zone_vwc',0,.8);fc=number(cfg['field_capacity_vwc'],'field_capacity_vwc',.01,.8);wp=number(cfg['wilting_point_vwc'],'wilting_point_vwc',0,.8)
    if fc<=wp:raise InputError('field_capacity_vwc must exceed wilting_point_vwc')
    z=number(cfg['root_depth_m'],'root_depth_m',.05,3);eff=number(cfg['irrigation_efficiency'],'irrigation_efficiency',.05,1)
    p=number(cfg['depletion_fraction'],'depletion_fraction',.01,.99);kc=number(cfg['kc'],'kc',0,2)
    cap=number(cfg['max_gross_mm_day'],'max_gross_mm_day',0,200);rf=number(cfg['effective_rain_fraction'],'effective_rain_fraction',0,1)
    forecast=data.get('weather_forecast',[])
    if len(forecast)<days:return {'status':'needs_inputs','missing':['dated daily weather_forecast: et0_mm and rain_mm'],'daily':[]}
    start=date.fromisoformat(data['as_of_date']);taw=(fc-wp)*z*1000;depletion=max(0,(fc-theta)*z*1000);rows=[]
    area=number(data['area_m2'],'area_m2',.01) if data.get('area_m2') is not None else None
    for i in range(days):
        f=forecast[i];expected=start+timedelta(days=i+1)
        if f.get('date')!=expected.isoformat():raise InputError('weather_forecast dates must be consecutive days after as_of_date')
        eto=number(f.get('et0_mm'),'et0_mm',0,30);rain=number(f.get('rain_mm'),'rain_mm',0,1000)
        etc=eto*kc;rain_effective=rain*rf
        before=max(0,depletion+etc-rain_effective)
        gross=min(cap,before/eff) if before>p*taw else 0.0
        net=gross*eff;after=max(0,before-net)
        rows.append({'date':expected.isoformat(),'etc_mm':round(etc,4),'effective_rain_mm':round(rain_effective,4),'gross_irrigation_mm':round(gross,4),'net_irrigation_mm':round(net,4),'irrigation_l':None if area is None else round(gross*area,3),'root_vwc_after':round(max(0,fc-after/(1000*z)),6),'remaining_depletion_mm':round(after,4),'unmet_mm_due_to_cap':round(max(0,before-net-p*taw),4),'below_wilting_point':after>taw})
        depletion=after
    return {'status':'scenario_estimate','method':'FAO56_single_bucket_user_calibrated_parameters','daily':rows,'warning':'Daily scheduling approximation; Kc, rooting depth, effective rain and water limits need orchard calibration. No causal ML irrigation response has been learned.'}

def fertilizer_budget(data,days,water):
    cfg=data.get('fertilizer') or {};keys=['annual_budget_kg_ha','applied_ytd_kg_ha','monthly_fractions','max_daily_kg_ha','water_nutrients_mg_l']
    missing=require(cfg,keys)
    if missing or cfg.get('plan_confirmed') is not True:return {'status':'needs_inputs','missing':missing+([] if cfg.get('plan_confirmed') is True else ['plan_confirmed=true: local leaf/soil diagnosis']),'daily':[]}
    names=['N','P2O5','K2O'];annual={};applied={};fractions={};caps={};water_c={}
    for n in names:
        annual[n]=number(cfg['annual_budget_kg_ha'].get(n),f'annual.{n}',0,1000)
        applied[n]=number(cfg['applied_ytd_kg_ha'].get(n),f'applied.{n}',0)
        caps[n]=number(cfg['max_daily_kg_ha'].get(n),f'max_daily.{n}',0,100)
        water_c[n]=number(cfg['water_nutrients_mg_l'].get(n),f'water_nutrients.{n}',0,10000)
        f=cfg['monthly_fractions'].get(n,[])
        if len(f)!=12:raise InputError(f'monthly_fractions.{n} requires 12 values')
        fractions[n]=[number(v,f'fraction.{n}',0,1) for v in f]
        if abs(sum(fractions[n])-1)>1e-6:raise InputError(f'monthly_fractions.{n} must sum to 1')
    if any(water_c.values()) and not water['daily']:return {'status':'needs_inputs','missing':['water schedule required to credit water nutrients'],'daily':[]}
    rows=[];start=date.fromisoformat(data['as_of_date']);area=number(data['area_m2'],'area_m2',.01) if data.get('area_m2') is not None else None
    for i in range(days):
        dt=start+timedelta(days=i+1)
        if dt.year!=start.year:return {'status':'needs_inputs','missing':['next year nutrient budget; request must stay in one budget year'],'daily':[]}
        gross=water['daily'][i]['gross_irrigation_mm'] if water['daily'] else 0
        need={};credits={}
        for n in names:
            credits[n]=gross*water_c[n]*.01
            elapsed=sum(fractions[n][:dt.month-1])+fractions[n][dt.month-1]*dt.day/calendar.monthrange(dt.year,dt.month)[1]
            scheduled=annual[n]*elapsed
            need[n]=max(0,min(caps[n],scheduled-applied[n]-credits[n],annual[n]-applied[n]-credits[n]))
            applied[n]+=need[n]+credits[n]
        rec={'date':dt.isoformat(),'nutrients_kg_ha':{k:round(v,6) for k,v in need.items()},'water_credit_kg_ha':{k:round(v,6) for k,v in credits.items()},'nutrients_kg_field':None if area is None else {k:round(v*area/10000,6) for k,v in need.items()}}
        products=data.get('fertilizer_products')
        if products:
            import numpy as np
            from scipy.optimize import linprog
            matrix=np.array([[number(prod.get('fractions',{}).get(n),f'product fraction {n}',0,1) for prod in products] for n in names])
            if np.any(matrix.sum(axis=0)>1+1e-6):raise InputError('product nutrient fractions sum exceeds 1')
            costs=[number(prod.get('cost_per_kg'), 'cost_per_kg',.000001) for prod in products]
            solved=linprog(costs,A_eq=matrix,b_eq=[need[n] for n in names],bounds=(0,None),method='highs')
            rec['product_status']='solved_exact_nutrient_balance' if solved.success else 'infeasible_use_other_products'
            rec['products_kg_ha']=None if not solved.success else {prod['name']:round(float(v),6) for prod,v in zip(products,solved.x)}
        rows.append(rec)
    return {'status':'budget_schedule_not_ml_optimum','basis':'User-confirmed nutrient budget, dated cumulative schedule, prior applications and water credits; EC is not an NPK measurement. Water concentrations must already be in N/P2O5/K2O equivalent mg/L.','daily':rows}

from .ml import moisture_forecast

def predict(data,model_dir=None):
    if not isinstance(data,dict):raise InputError('JSON object required')
    for key in ['water','fertilizer']:
        if data.get(key) is not None and not isinstance(data[key],dict):
            raise InputError(f'{key} must be an object')
    for key in ['weather_forecast','history_daily','history_15min','fertilizer_products']:
        if key in data and (not isinstance(data[key],list) or not all(isinstance(r,dict) for r in data[key])):
            raise InputError(f'{key} must be a list of objects')
    fc=data.get('fertilizer') or {}
    for key in ['annual_budget_kg_ha','applied_ytd_kg_ha','monthly_fractions','max_daily_kg_ha','water_nutrients_mg_l']:
        if key in fc and not isinstance(fc[key],dict):
            raise InputError(f'fertilizer.{key} must be an object')
    products=data.get('fertilizer_products',[])
    names=[r.get('name') for r in products]
    if products and (any(not isinstance(n,str) or not n for n in names) or len(set(names))!=len(names)):
        raise InputError('fertilizer product names must be unique nonempty strings')
    if any(not isinstance(r.get('fractions'),dict) for r in products):
        raise InputError('fertilizer product fractions must be objects')
    try: date.fromisoformat(data.get('as_of_date',''))
    except (TypeError,ValueError):raise InputError('as_of_date requires YYYY-MM-DD, the last complete local day')
    days=number(data.get('days',3),'days',1,3)
    if not days.is_integer():raise InputError('days must be integer')
    days=int(days)
    if data.get('region') not in ['雅安','西昌']:raise InputError('region must be 雅安 or 西昌')
    if model_dir is None:model_dir=Path(__file__).resolve().parents[2]/'models'
    moisture=moisture_forecast(data,days,model_dir);water=water_budget(data,days);fert=fertilizer_budget(data,days,water)
    result={'schema_version':'2.1','region':data['region'],'crop_id':data.get('crop_id'),'growth_stage':data.get('growth_stage','unknown'),'as_of_date':data['as_of_date'],'moisture_forecast':moisture,'irrigation':water,'fertilizer':fert,'units':{'vwc':'m3/m3','irrigation':'mm gross over whole orchard area','nutrients':'kg/ha as N,P2O5,K2O'},'can_auto_execute':False}
    # Legacy response keys: retain shapes, never convert missing into zero.
    result.update(dates=[(date.fromisoformat(data['as_of_date'])+timedelta(days=i+1)).isoformat() for i in range(days)],predicted_soil_moisture=[r['vwc_m3_m3']*100 for r in moisture['daily']] or [None]*days,predicted_water_need=[r['gross_irrigation_mm'] for r in water['daily']] or [None]*days,predicted_fertilizer_need=[None]*days,drought_analysis='请结合根区持水量和萎蔫点判断；不使用统一含水量阈值',basis='土壤水分时间验证模型；灌水采用根区水量平衡；施肥采用已确认养分预算',weather_desc=json.dumps(data.get('weather_forecast',[]),ensure_ascii=False))
    return result

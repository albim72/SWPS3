from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

def sales_quality(frame):
    """Report overlapping flags; keep raw input unchanged."""
    d=frame.copy()
    flags=pd.DataFrame(index=d.index)
    flags['duplikat_pozycji']=d.duplicated('line_id',keep='first')
    flags['bledna_data']=pd.to_datetime(d.order_date,errors='coerce').isna()
    flags['bledna_ilosc']=d.quantity.isna() | d.quantity.le(0)
    flags['bledna_cena']=d.unit_price.isna() | d.unit_price.le(0)
    flags['bledny_rabat']=d.discount.isna() | ~d.discount.between(0,1)
    calc=d.quantity*d.unit_price*(1-d.discount)
    flags['niespojna_kwota']=~np.isclose(d.net,calc,atol=.005,rtol=0)
    flags['niespojny_koszt']=~np.isclose(d.cost,d.quantity*d.unit_cost,atol=.005,rtol=0)
    return flags

def to_cents(series):
    # Generator writes exactly two decimal places. No float rounding required.
    s=series.astype(str).str.strip()
    ok=s.str.fullmatch(r'[0-9]+,[0-9]{2}',na=False)
    if not ok.all():raise ValueError('Niepoprawny zapis kwoty: '+str(s[~ok].head().tolist()))
    return s.str.replace(',','',regex=False).astype('int64')

def aggregate_chunks(path,chunksize=17003):
    # Supports this generator's schema. Does not claim general cross-chunk deduplication.
    n=units=net_cents=price_cents_sum=0
    grouped={}
    for part in pd.read_csv(path,sep=';',encoding='utf-8-sig',dtype=str,
                            keep_default_na=False,chunksize=chunksize):
        q=pd.to_numeric(part['ilość sztuk'],errors='raise').astype('int64')
        price=to_cents(part['cena netto'])
        net=to_cents(part['wartość netto'])
        if not q.gt(0).all() or not net.eq(q*price).all():
            raise ValueError('Niespójność ilość × cena albo niepoprawna ilość')
        n+=len(part);units+=int(q.sum());net_cents+=int(net.sum());price_cents_sum+=int(price.sum())
        sub=pd.DataFrame({'kategoria':part['kategoria'],'net_cents':net,'units':q})
        for key,row in sub.groupby('kategoria').agg(n=('units','size'),units=('units','sum'),net_cents=('net_cents','sum')).iterrows():
            old=grouped.setdefault(key,{'n':0,'units':0,'net_cents':0})
            for col in old:old[col]+=int(row[col])
    if n==0:raise ValueError('Pusty plik')
    return {'rows':n,'units':units,'net_cents':net_cents,'price_cents_sum':price_cents_sum,
            'mean_unit_price_pln':price_cents_sum/n/100,
            'quantity_weighted_price_pln':net_cents/units/100,
            'groups':pd.DataFrame.from_dict(grouped,orient='index').sort_index()}

class AmountCapper(BaseEstimator,TransformerMixin):
    """Learn a threshold from TRAIN rows only, preserving the input frame."""
    def __init__(self,quantile=.995):self.quantile=quantile
    def fit(self,X,y=None):
        self.upper_=float(X['amount'].quantile(self.quantile))
        return self
    def transform(self,X):
        d=X.copy();d['amount']=d['amount'].clip(upper=self.upper_);return d

def make_transactions(n=3000,seed=22):
    # Simplified synthetic counterpart of data_science_pipeline.py.
    rng=np.random.default_rng(seed)
    amount=np.round(rng.lognormal(5.5,.8,n),2)
    income=np.round(np.maximum(rng.normal(8500,3500,n),1800),2)
    age=rng.integers(18,81,n).astype(float)
    device=rng.choice(['mobile','desktop','tablet'],n,p=[.58,.34,.08])
    past=rng.choice([0,1,2,3],n,p=[.92,.06,.015,.005])
    score=-4.8+.8*(amount>1500)+1.0*(amount>4000)+.25*(device=='mobile')+1.4*past
    target=rng.binomial(1,1/(1+np.exp(-score)))
    d=pd.DataFrame({'transaction_id':['T%05d'%i for i in range(n)],
        'created_at':pd.date_range('2026-10-01',periods=n,freq='h'),
        'age':age,'income':income,'amount':amount,'device_type':device,
        'past_chargebacks':past,'is_fraud':target,
        'refund_after_event':np.where(target,amount,0)})
    d.loc[rng.choice(n,n//20,replace=False),'income']=np.nan
    d.loc[rng.choice(n,n//25,replace=False),'age']=np.nan
    d.loc[rng.choice(n,max(1,n//200),replace=False),'amount']*=12
    return d

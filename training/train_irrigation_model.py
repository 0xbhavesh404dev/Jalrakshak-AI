#!/usr/bin/env python3
"""Train/evaluate only on a supplied labelled CSV; never synthesizes labels."""
import argparse
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.ml import FEATURES, TARGET


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv",help="CSV of real or expert-labelled observations")
    parser.add_argument("--label-source",choices=("measured", "expert"),required=True,
                        help="Provenance of irrigation_needed labels")
    parser.add_argument("--output",default="models/irrigation_rf.joblib")
    args=parser.parse_args()
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score,confusion_matrix,precision_recall_fscore_support
        from sklearn.dummy import DummyClassifier
        import joblib
    except ImportError as exc:
        raise SystemExit("Install optional ML packages first: python -m pip install scikit-learn joblib") from exc

    data=pd.read_csv(args.csv)
    required={"timestamp","field_id",TARGET,*FEATURES}
    missing=sorted(required-set(data.columns))
    if missing: raise SystemExit(f"CSV is missing required columns: {', '.join(missing)}")
    data["timestamp"]=pd.to_datetime(data["timestamp"],utc=True,errors="coerce")
    if data["timestamp"].isna().any(): raise SystemExit("CSV has invalid timestamps")
    if data["field_id"].isna().any() or (data["field_id"].astype(str).str.strip()=="").any():
        raise SystemExit("CSV has missing field_id values")
    for column in (*FEATURES,TARGET): data[column]=pd.to_numeric(data[column],errors="coerce")
    missing_counts=data[[*FEATURES,TARGET]].isna().sum()
    if missing_counts.any():
        details=", ".join(f"{name}={int(count)}" for name,count in missing_counts.items() if count)
        raise SystemExit(f"Missing or nonnumeric feature/label values: {details}")
    if not set(data[TARGET].unique()).issubset({0,1}): raise SystemExit("irrigation_needed labels must be 0 or 1")
    data=data.sort_values("timestamp").reset_index(drop=True)
    split=int(len(data)*.8)
    if split<2 or len(data)-split<1: raise SystemExit("Need at least 3 rows for a chronological train/test split")
    train,test=data.iloc[:split],data.iloc[split:]
    if train[TARGET].nunique()<2: raise SystemExit("Training period needs both label classes")
    x_train,x_test=train.loc[:,FEATURES],test.loc[:,FEATURES]
    y_train,y_test=train[TARGET].astype(int),test[TARGET].astype(int)
    model=RandomForestClassifier(n_estimators=300,min_samples_leaf=3,class_weight="balanced",random_state=42,n_jobs=-1)
    model.fit(x_train,y_train)
    threshold_baseline=(x_test["soil_moisture_percent"]<30).astype(int)
    predictions=model.predict(x_test)
    def metrics(actual,predicted):
        p,r,f,_=precision_recall_fscore_support(actual,predicted,average="binary",zero_division=0)
        return {"accuracy":float(accuracy_score(actual,predicted)),"precision":float(p),"recall":float(r),"f1":float(f),
                "confusion_matrix_labels_0_1":confusion_matrix(actual,predicted,labels=[0,1]).tolist()}
    metadata={"features":list(FEATURES),"target":TARGET,"label_source":args.label_source,
        "label_definition":"1 means irrigate; 0 means do not irrigate, as labelled by the supplied data source",
        "training_rows":len(train),"test_rows":len(test),"train_end_utc":train.timestamp.max().isoformat(),
        "test_start_utc":test.timestamp.min().isoformat(),"evaluation":"chronological 80/20 split; later rows held out",
        "random_forest":metrics(y_test,predictions),"threshold_baseline_soil_moisture_below_30_percent":metrics(y_test,threshold_baseline),
        "note":"Metrics describe this supplied dataset only; they do not establish field performance or optimal policy."}
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,output)
    output.with_suffix(".metrics.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print(json.dumps(metadata,indent=2))
    print(f"Saved model: {output} (only load artifacts you trust)")


if __name__=="__main__": main()

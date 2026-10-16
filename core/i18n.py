STRINGS={
"en":{"dashboard":"Dashboard","farm":"Farm","wait":"WAIT","disclaimer":"This is an estimate. Check the soil in the field before irrigating and follow local agricultural advice.","ml_unavailable":"ML forecast unavailable — the weather-based water-balance projection is still available."},
"te":{"dashboard":"డాష్‌బోర్డ్","farm":"వ్యవసాయ క్షేత్రం","wait":"వేచి ఉండండి","disclaimer":"ఇది ఒక అంచనా మాత్రమే. నీరు పెట్టే ముందు పొలంలోని మట్టిని పరిశీలించి స్థానిక వ్యవసాయ సలహా పాటించండి.","ml_unavailable":"ML అంచనా అందుబాటులో లేదు — వాతావరణ ఆధారిత నీటి సమతుల్య అంచనా అందుబాటులో ఉంది."},
"hi":{"dashboard":"डैशबोर्ड","farm":"खेत","wait":"प्रतीक्षा करें","disclaimer":"यह एक अनुमान है। सिंचाई से पहले खेत की मिट्टी जांचें और स्थानीय कृषि सलाह का पालन करें।","ml_unavailable":"ML पूर्वानुमान उपलब्ध नहीं है — मौसम आधारित जल संतुलन अनुमान उपलब्ध है."}}
def t(key,lang="en",**params): return STRINGS.get(lang,STRINGS["en"]).get(key,STRINGS["en"].get(key,key)).format(**params)

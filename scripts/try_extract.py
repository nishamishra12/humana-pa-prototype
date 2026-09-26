import os, json
from dotenv import load_dotenv; load_dotenv(".env")
from unstructured_transform_client import TransformClient
c = TransformClient(api_key=os.environ["UNSTRUCTURED_API_KEY"], server_url="https://transform.unstructured.io")
schema = {"type":"object","properties":{
  "procedure":{"type":"string","description":"Requested procedure"},
  "requested_setting":{"type":"string","description":"inpatient, outpatient or observation"},
  "comorbidities":{"type":"array","items":{"type":"string"}},
  "expected_length_of_stay_days":{"type":["number","null"],"description":"null if not stated"},
  "post_op_monitoring_needs":{"type":"string"}},
  "required":["procedure","requested_setting","comorbidities","expected_length_of_stay_days","post_op_monitoring_needs"],
  "additionalProperties":False}
with open("packets/john_doe_lumbar_fusion_incomplete.pdf","rb") as f:
    try:
        r = c.parse.run(input=f, output="elements", schema=schema)
    except Exception as e:
        print("ERR", type(e).__name__, str(e)[:500]); raise SystemExit
print("status:", r.status)
print("extracted_data:", json.dumps([x.to_dict() if hasattr(x,'to_dict') else str(x) for x in (r.extracted_data or [])], indent=1)[:2500])
print("warnings:", r.warnings)

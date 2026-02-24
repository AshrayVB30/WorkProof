import os
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'

import paddle
paddle.device.set_device('cpu')

from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import requests
import io

ocr_engine = PaddleOCR(use_textline_orientation=True, lang='en')

url = "http://109.199.108.38:2069/?q=QUNUQVNUeHg4MGltZzA3NDMuanBlZzs1NzM7NkJpN3dpaFA"
response = requests.get(url, timeout=30)
img = Image.open(io.BytesIO(response.content)).convert("RGB")
img_np = np.array(img)

result = ocr_engine.predict(img_np)
if result:
    res_obj = result[0]
    print(f"Keys: {list(res_obj.keys())}")
    
    for key in res_obj.keys():
        val = res_obj[key]
        print(f"Key: {key}, Type: {type(val)}")
        if isinstance(val, (list, tuple)):
            print(f"  Length: {len(val)}")
            if len(val) > 0:
                print(f"  Sample[0]: {str(val[0])[:200]}")
        elif isinstance(val, (str, int, float, bool)):
            print(f"  Value: {val}")
        else:
             print(f"  Stringified: {str(val)[:200]}")

import base64
import requests
import io
import os
import zipfile
import numpy as np
from Pyfhel import Pyfhel, PyCtxt

#base_url = 'http://he-poc.herokuapp.com'
base_url = 'http://127.0.0.1:5007'

def ConfigHE(n_exp, scale_exp, qi_n):
  HE = Pyfhel()
  HE.contextGen(scheme='ckks', n=2**n_exp, scale = 2**scale_exp, qi = [scale_exp]*qi_n)
  HE.keyGen()
  HE.relinKeyGen()
  HE.rotateKeyGen()

  s_context = HE.to_bytes_context()
  s_public_key = HE.to_bytes_public_key()
  s_relin_key = HE.to_bytes_relin_key()
  s_rotate_key = HE.to_bytes_rotate_key()

  # s_context_b64 = base64.b64encode(s_context)
  # s_public_key_b64 = base64.b64encode(s_public_key)
  # s_relin_key_b64 = base64.b64encode(s_relin_key)
  # s_rotate_key_b64 = base64.b64encode(s_rotate_key)

  zip_buffer = io.BytesIO()
  with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
    for file_name, data in [
      ('ctx', io.BytesIO(s_context)), 
      ('pub', io.BytesIO(s_public_key)), 
      ('relin', io.BytesIO(s_relin_key)), 
      ('rotate', io.BytesIO(s_rotate_key))]:
      zip_file.writestr(file_name, data.getvalue())

  cwd = os.getcwd()
  print(cwd)
  with open(f'{cwd}/keys.zip', 'wb') as f:
    f.write(zip_buffer.getvalue())
  
  zip_buffer.seek(0)
  HE_buffer = zip_buffer

  return HE, HE_buffer
  
def main():
  print('Enter n_exp [13]:')
  n_exp = int(input() or 13)

  print('Enter scale_exp [30]:')
  scale_exp = int(input() or 30)

  print('Enter qi_n [3]:')
  qi_n = int(input() or 3)

  HE, HE_buffer = ConfigHE(n_exp, scale_exp, qi_n)

  #return send_file(zip_buffer, attachment_filename='filename.zip', as_attachment=True)
  #return { "ctx": len(s_context_b64), "pub": len(s_public_key_b64), "relin": len(s_relin_key_b64), "rotate": len(s_rotate_key_b64) }

  try:
    files = {'file': HE_buffer}
    response = requests.post(f'{base_url}/configure-ckks', files=files)
    if response.status_code != 200:
      print(f"Response status: {response.status_code}, exiting...")
      return

    json = response.json()
    message = json['message']
    print(f"Response message: [{message}]")
  except Exception as ex:
    print(f"Request exception: {ex}")

if __name__ == "__main__":
  main()
else:
  print("Wrong usage")

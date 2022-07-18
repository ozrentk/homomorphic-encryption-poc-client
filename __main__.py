import base64
import requests
import io
import os
import zipfile
import numpy as np
from Pyfhel import Pyfhel, PyCtxt

base_url = 'http://he-poc.herokuapp.com'
#base_url = 'http://127.0.0.1:5007'

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

def ConfigHEServer(HE_buffer):
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

def main():
  print('Enter n_exp [13]:')
  n_exp = int(input() or 13)

  print('Enter scale_exp [30]:')
  scale_exp = int(input() or 30)

  print('Enter qi_n [3]:')
  qi_n = int(input() or 3)

  HE, HE_buffer = ConfigHE(n_exp, scale_exp, qi_n)

  ConfigHEServer(HE_buffer)
  
  while True:  
    print('Enter number of random frac\'s sent to server [5]:')
    frac_n = int(input() or 5)

    print('Enter seed [1012976]:')
    seed_n = int(input() or 1012976)

    np.random.seed(seed_n)
    np.set_printoptions(suppress=True)

    x = np.around(np.random.uniform(0, 1000, frac_n), 2)
    print(f"Vector 1: {x}")
    s_cx = HE.encrypt(x).to_bytes()
    b64_cx = base64.b64encode(s_cx).decode()

    y = np.around(np.random.uniform(0, 1000, frac_n), 2)
    print(f"Vector 2: {y}")
    s_cy = HE.encrypt(y).to_bytes()
    b64_cy = base64.b64encode(s_cy).decode()

    try:
      json_data = {"n1": b64_cx, "n2": b64_cy}
      response = requests.post(f'{base_url}/compute-add', json=json_data)
      if response.status_code != 200:
        print(f"Response status: {response.status_code}, exiting...")
        return

      json = response.json()
      message = json['message']

      b64_cres = json['result']
      b64_res = base64.b64decode(b64_cres)
      cres = PyCtxt(pyfhel=HE, bytestring=b64_res)
      res = HE.decryptFrac(cres)

      print(f"Response message: [{message}]")

      trunc_res = res[:frac_n]
      d = np.column_stack((x + y, trunc_res))
      print(f"Comparison")
      print(d)

    except Exception as ex:
      print(f"Request exception: {ex}")
  
    print("Again? [Y/n]")
    again = input() or "y"

    if again == "n":
        break

if __name__ == "__main__":
  main()
else:
  print("Wrong usage")

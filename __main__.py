import requests

base_url = 'http://he-poc.herokuapp.com/'

def main():
  try:
    response = requests.get(base_url)
    if response.status_code != 200:
      print(f"Response status: {response.status_code}, exiting...")
      return;

    json = response.json()
    print(json)
  except Exception as ex:
    print(f"Request exception: {ex}")

if __name__ == "__main__":
  main()
else:
  print("Wrong usage")


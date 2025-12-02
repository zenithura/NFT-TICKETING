import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
pk = os.getenv("PRIVATE_KEY")
if not pk:
    print("No Private Key")
else:
    w3 = Web3()
    account = w3.eth.account.from_key(pk)
    print(f"Server Address: {account.address}")

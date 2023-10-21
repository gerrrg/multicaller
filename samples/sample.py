from multicaller import multicaller
import os
import json
from web3 import Web3

chainId = 137;
rpcEndpoint = "https://polygon-rpc.com";

web3 = Web3(Web3.HTTPProvider(rpcEndpoint));
mc = multicaller.multicaller(_chainId=chainId, _web3=web3, _maxRetries=3, _allowFailure=True);

with open('abi/ERC20.json') as f:
	erc20Abi = json.load(f);

tokenAddresses = [	"0x9a71012b13ca4d3d0cdc72a177df3ef03b0e76a3",
					"0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
					"0xd6df932a45c0f255f85145f286ea0b292b21c90b",
					"0x6f7C932e7684666C9fd1d44527765433e01fF61d",
					"0x263534a4fe3cb249df46810718b7b612a30ebbff"
				];

balancerVault = web3.to_checksum_address("0xba12222222228d8ba445958a75a0704d566bf2c8");

for tokenAddress in tokenAddresses:
	mc.addCall(tokenAddress, erc20Abi, 'symbol');
	mc.addCall(tokenAddress, erc20Abi, 'name');
	mc.addCall(tokenAddress, erc20Abi, 'decimals');
	mc.addCall(tokenAddress, erc20Abi, 'balanceOf', args=[balancerVault]);
(data, successes) = mc.execute();

# print results
itemsPerLine = 4;
itemCount = 0;
first = True;
allLines = [];
line = [];
for element in data:
	if itemCount % itemsPerLine == 0 and not first:
		allLines.append("\t".join(line));
		line = [];

	for subelement in element:
		line.append(str(subelement));
	itemCount += 1;
	first = False;

print();
print("\tSYM\tName\t\tDec\tAmount in Balancer Vault (wei)");
print("\t---\t----\t\t---\t------------------------------");
for line in allLines:
	print("\t" + line);
print();


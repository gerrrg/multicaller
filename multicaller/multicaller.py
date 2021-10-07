import os
import json
import pkgutil
from web3 import Web3
from web3._utils.abi import get_abi_output_types

class multicaller(object):
	addressByChainId = {
		1: '0xeefba1e63905ef1d7acba5a8513c70307c1ce441',
		4: '0x42Ad527de7d4e9d9d011aC45B31D8551f8Fe9821',
	    5: '0x3b2A02F22fCbc872AF77674ceD303eb269a46ce3',
	    42: '0x2cc8688C5f75E365aaEEb4ea8D6a480405A48D2A',
		56: '0x1Ee38d535d541c55C9dae27B12edf090C608E6Fb',
		100: '0xb5b692a88BDFc81ca69dcB1d924f59f0413A602a',
		128: '0xc9a9F768ebD123A00B52e7A0E590df2e9E998707',
	    137: '0xa1B2b503959aedD81512C37e9dce48164ec6a94d',
		250: '0xb828C456600857abd4ed6C32FAcc607bD0464F4F',
	    42161: '0x269ff446d9892c9e19082564df3f5e8741e190a1'
	};

	def __init__(self, _chainId, _web3=None, _rpcEndpoint=None):
		if _web3 is None and _rpcEndpoint is None:
			print("[ERROR] You must provide a Web3 instance or an RPC Endpoint.");
			print();
			quit();

		if not _web3 is None:
			self.web3 = _web3;
		else:
			self.web3 = Web3(Web3.HTTPProvider(_rpcEndpoint));

		if not _chainId in self.addressByChainId.keys():
			print("[ERROR} Chain id", _chainId, "not supported!")
			print();
			quit();
		self.chainId = _chainId;
		self.mcContract = self.loadMultiCall();
		self.reset();

	def loadMultiCall(self):
		multicallAddress = self.getMultiCallAddress();
		abiPath = os.path.join('abi/multiCall.json');
		f = pkgutil.get_data(__name__, abiPath).decode();
		abi = json.loads(f);
		multiCall = self.web3.eth.contract(self.web3.toChecksumAddress(multicallAddress), abi=abi);
		return(multiCall);

	def getMultiCallAddress(self):
		return(self.addressByChainId[self.chainId])

	def addCall(self, address, abi, functionName, args=None):
		contract = self.web3.eth.contract(self.web3.toChecksumAddress(address), abi=abi);
		callData = contract.encodeABI(fn_name=functionName, args=args);
		self.payload.append((self.web3.toChecksumAddress(address), callData));
		fn = contract.get_function_by_name(fn_name=functionName);
		self.decoders.append(get_abi_output_types(fn.abi));

	def execute(self):
		output = self.mcContract.functions.aggregate(self.payload).call();
		outputDataRaw = output[1];
		outputData = [];
		for rawOutput, decoder in zip(outputDataRaw, self.decoders):
			outputData.append(self.web3.codec.decode_abi(decoder, rawOutput));
		self.reset();
		return(outputData);

	def reset(self):
		self.payload = [];
		self.decoders = [];

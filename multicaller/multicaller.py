import os
import json
import pkgutil
from web3 import Web3
from web3._utils.abi import get_abi_output_types
from functools import cache

def split(a, n):
    k, m = divmod(len(a), n)
    return (list(a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n)));

class multicaller(object):
	addressByChainId = {
		1:	'0xeefba1e63905ef1d7acba5a8513c70307c1ce441',
		4:	'0x42Ad527de7d4e9d9d011aC45B31D8551f8Fe9821',
		5:	'0x3b2A02F22fCbc872AF77674ceD303eb269a46ce3',
		42:	'0x2cc8688C5f75E365aaEEb4ea8D6a480405A48D2A',
		56:	'0x1Ee38d535d541c55C9dae27B12edf090C608E6Fb',
		100:	'0xb5b692a88BDFc81ca69dcB1d924f59f0413A602a',
		128:	'0xc9a9F768ebD123A00B52e7A0E590df2e9E998707',
		137:	'0xa1B2b503959aedD81512C37e9dce48164ec6a94d',
		250:	'0xb828C456600857abd4ed6C32FAcc607bD0464F4F',
		42161:	'0x269ff446d9892c9e19082564df3f5e8741e190a1'
	};

	def __init__(self, _chainId, _web3=None, _rpcEndpoint=None, _batches=1, _maxRetries=20, _verbose=False):
		if _web3 is None and _rpcEndpoint is None:
			print("[ERROR] You must provide a Web3 instance or an RPC Endpoint.");
			print();
			quit();

		self.batches = _batches;
		self.verbose = _verbose;
		self.maxRetries = _maxRetries;

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

	@cache
	def getContract(self, address, abiString):
		abi = self.stringToList(abiString);
		contract = self.web3.eth.contract(self.web3.toChecksumAddress(address), abi=abi);
		return(contract);

	@cache
	def getCallData(self, contract, functionName, argsString):
		args = self.stringToList(argsString);
		callData = contract.encodeABI(fn_name=functionName, args=args);
		return(callData);

	@cache
	def getFunction(self, contract, functionName):
		fn = contract.get_function_by_name(fn_name=functionName);
		return(fn);

	@cache
	def decodeData(self, decoder, rawOutput):
		return(self.web3.codec.decode_abi(self.stringToList(decoder), rawOutput));

	def listToString(self, inputList):
		outputString = json.dumps(inputList);
		return(outputString);

	def stringToList(self, inputString):
		outputList = json.loads(inputString);
		return(outputList);

	def addCall(self, address, abi, functionName, args=None):
		contract = self.getContract(address, self.listToString(abi));
		callData = self.getCallData(contract, functionName, self.listToString(args));
		fn = self.getFunction(contract, functionName);

		self.payload.append((self.web3.toChecksumAddress(address), callData));
		self.decoders.append(get_abi_output_types(fn.abi));

	def execute(self):
		retries = 0;
		outputData = None;
		while retries < self.maxRetries:
			retries += 1;
			if self.verbose:
				print("Attempt", retries, "of", self.maxRetries);
				print("Executing with", self.batches, "batches!");
			sublistsPayload = split(self.payload, self.batches);
			sublistsDecoder = split(self.decoders, self.batches);

			try:
				outputData = [];
				for sublistPayload, sublistDecoder in zip(sublistsPayload, sublistsDecoder):

					success = False;
					internalRetries = 0;
					maxInternalRetries = 3;
					while not success and internalRetries < maxInternalRetries:
						try:
							output = self.mcContract.functions.aggregate(sublistPayload).call();
							outputDataRaw = output[1];
							for rawOutput, decoder in zip(outputDataRaw, sublistDecoder):
								outputData.append(self.decodeData(self.listToString(decoder), rawOutput));
							success = True;
						except OverflowError:
							internalRetries += 1;
							print("Internal retry", internalRetries, "of", maxInternalRetries);
					if internalRetries >= maxInternalRetries:
						raise OverflowError;

				break;
			except OverflowError:
				self.batches += 1;
				print("Too many requests in one batch. Reattempting with", self.batches, "batches...");
			except Exception as e:
				print("Attempt", retries, "of", self.maxRetries, "failed. Retrying...");
				print(e.message, e.args);

		self.reset();
		return(outputData);

	def reset(self):
		self.payload = [];
		self.decoders = [];

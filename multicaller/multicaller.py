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

	multicall3Address = "0xca11bde05977b3631167028862be2a173976ca11";

	# _chainId is no longer used, but is left as an argument for backwards compatibility
	def __init__(self, _chainId=None, _web3=None, _rpcEndpoint=None, _batches=1, _maxRetries=20, _verbose=False, _allowFailure=False):
		if _web3 is None and _rpcEndpoint is None:
			print("[ERROR] You must provide a Web3 instance or an RPC Endpoint.");
			print();
			quit();

		self.batches = _batches;
		self.verbose = _verbose;
		self.maxRetries = _maxRetries;
		self.allowFailure = _allowFailure;

		if not _web3 is None:
			self.web3 = _web3;
		else:
			self.web3 = Web3(Web3.HTTPProvider(_rpcEndpoint));

		self.mcContract = self.loadMultiCall();
		self.reset();

	def loadMultiCall(self):
		multicallAddress = self.getMultiCallAddress();
		path = 'abi/multicall3.json';
		abiPath = os.path.join(path);
		f = pkgutil.get_data(__name__, abiPath).decode();
		abi = json.loads(f);
		multiCall = self.web3.eth.contract(self.web3.toChecksumAddress(multicallAddress), abi=abi);
		return(multiCall);

	def getMultiCallAddress(self):
		return(self.multicall3Address);

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

	def iterArgs(self, args):
		isTuple = False;
		if isinstance(args, tuple):
			isTuple = True;
			args = list(args);

		if isinstance(args, list):
			for i in range(len(args)):
				arg = args[i];
				if isinstance(arg, list) or isinstance(arg, tuple):
					args[i] = self.iterArgs(arg);
				if isinstance(arg, bytes):
					args[i] = arg.hex();

		if isTuple:
			args = tuple(args)
		return(args)

	def listToString(self, inputList):
		inputList = self.iterArgs(inputList);
		outputString = json.dumps(inputList);
		return(outputString);

	def stringToList(self, inputString):
		if inputString is None:
			return(None);
		outputList = json.loads(inputString);
		return(outputList);

	def addCall(self, address, abi, functionName, args=None):
		if not args is None:
			args = self.listToString(args);

		contract = self.getContract(address, self.listToString(abi));
		callData = self.getCallData(contract, functionName, args);
		fn = self.getFunction(contract, functionName);

		payload = None;
		if self.allowFailure:
			payload = (self.web3.toChecksumAddress(address), True, callData);
		else:
			payload = (self.web3.toChecksumAddress(address), callData);

		self.payload.append(payload);
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
				batchSuccesses = [];
				for sublistPayload, sublistDecoder in zip(sublistsPayload, sublistsDecoder):
					success = False;
					internalRetries = 0;
					maxInternalRetries = 3;
					while not success and internalRetries < maxInternalRetries:
						try:
							successes = None;
							output = None;
							if self.allowFailure:
								outputMc3 = self.mcContract.functions.aggregate3(sublistPayload).call();
								output = list(map(list, zip(*outputMc3))); #convert (list of tuples) to (list of two parallel lists)
								successes = output[0];
							else:
								output = self.mcContract.functions.aggregate(sublistPayload).call();
								successes = [True] * len(output[1]);

							outputDataRaw = output[1];
							for rawOutput, decoder, currSuccess in zip(outputDataRaw, sublistDecoder, successes):

								# don't bother attempting to decode data if the call failed
								currOutputData = None;
								if currSuccess:
									currOutputData = self.decodeData(self.listToString(decoder), rawOutput);

								outputData.append(currOutputData);
								batchSuccesses.append(currSuccess);

							success = True;
						except OverflowError:
							internalRetries += 1;
							print("Internal retry", internalRetries, "of", maxInternalRetries);
						except Exception as e:
							print(e)
							print("One or more of the calls failed. Please try again after removing the failing call(s).")
							self.reset();
							raise e;
					if internalRetries >= maxInternalRetries:
						raise OverflowError;

				break;
			except OverflowError:
				self.batches += 1;
				print("Too many requests in one batch. Reattempting with", self.batches, "batches...");
			except Exception as e:
				print("Attempt", retries, "of", self.maxRetries, "failed. Retrying...");
				# self.reset();
				# raise e;
		self.reset();
		return(outputData, batchSuccesses);

	def reset(self):
		self.payload = [];
		self.decoders = [];

import re
import copy
from os.path import splitext
import random
import argparse
import sys

ver = "0.1"

class NoValidPathError(Exception):
	"Exception for when Dijkstra's Algorithm fails to find a route between nodes"
	pass
	
def _breakdownflag(flag):
	"Split a bitfield into a list of components"
	n = 0
	out = []
	while 1:
		if 2**n > flag: return out
		if flag & 2**n: out.append(2**n)
		n += 1
	
class NameCandidate(object):
	def __init__(self, name, reqs):
		self.name = name
		self.reqterrain = 0
		self.reqmodifiers = 0
		self.specialreqs = []
		self.used = False
		for req in reqs:
			req = req.strip()
			if req.lower() == "plains":
				pass
			elif req.lower() == "sea":
				self.reqterrain += 4
			elif req.lower() == "freshwater":
				self.reqterrain += 8
			elif req.lower() in ("highlands", "gorge"):
				self.reqterrain += 16
			elif req.lower() == "swamp":
				self.reqterrain += 32
			elif req.lower() == "waste":
				self.reqterrain += 64
			elif req.lower() in ("forest", "kelpforest"):
				self.reqterrain += 128
			elif req.lower() == "farm":
				self.reqterrain += 256
			elif req.lower() == "deepsea":
				self.reqterrain += 2048
			elif req.lower() == "cave":
				self.reqterrain += 4096
			elif req.lower() == "mountains":
				self.reqterrain += 4194304
				
			elif req.lower() == "small":
				self.reqmodifiers += 1
			elif req.lower() == "large":
				self.reqmodifiers += 2
			elif req.lower() == "nostart":
				self.reqmodifiers += 512
			elif req.lower() == "manysites":
				self.reqmodifiers += 1024
			elif req.lower() == "throne":
				self.reqmodifiers += 16777216
			elif req.lower() == "start":
				self.reqmodifiers += 33554432
			elif req.lower() == "nothrone":
				self.reqmodifiers += 67108864
			elif req.lower() == "warmer":
				self.reqmodifiers += 536870912
			elif req.lower() == "colder":
				self.reqmodifiers += 1073741824
			elif req.lower() == "inland":
				self.specialreqs.append("inland")
			else:
				raise ValueError(f"Unknown req for {self.name}: {req}")
	def applicable(self, terrainmask, neighbourmasks):
		if self.used: return False
		for flag in _breakdownflag(self.reqterrain):
			#print(f"{self.name} checking for {flag}")
			if not (terrainmask & flag):
				return False
				
		if "inland" in self.specialreqs:
			for mask in neighbourmasks:
				if mask & 4 or mask & 2048:
					return False
		
		# True if we have no modifier requirements
		# any one of these being met is fine
		if self.reqmodifiers > 0:
			for flag in _breakdownflag(self.reqmodifiers):
				if (terrainmask & flag):
					return True
			return False
		return True
		

class Map(object):
	def __init__(self, fp):
		self.fp = fp
		self.terrains = {}
		self.connections = {}
		self.renames = {}
		
		self._distancecache = {}
		
		with open(fp, "r") as f:
			for line in f:
				m = re.search(r"#terrain (\d*) (\d*)", line)
				if m is not None:
					provid = int(m.groups()[0])
					terraintype = int(m.groups()[1])
					self.terrains[provid] = terraintype
					continue
				m = re.search(r"#neighbour (\d*) (\d*)", line)
				if m is not None:
					provone = int(m.groups()[0])
					provtwo = int(m.groups()[1])
					if provone not in self.connections: self.connections[provone] = []
					if provtwo not in self.connections: self.connections[provtwo] = []
					
					self.connections[provone].append(provtwo)
					self.connections[provtwo].append(provone)
					
	def getDist(self, provone, provtwo):
		# simple result cache for speed, this could be used to optimise the algorithm further but it is probably not needed for this script!
		cachekey = f"{provone},{provtwo}"
		if cachekey in self._distancecache:
			return self._distancecache[cachekey]
	
		# I guess Dijkstra's algorithm with equal edge lengths is the way to go here
		provs = copy.copy(list(self.connections.keys()))
		visitedstates = {}
		nodedistances = {}
		for prov in provs:
			visitedstates[prov] = False
			nodedistances[prov] = None
		nodedistances[provone] = 0
		
		currnode = provone
		
		while 1:
			#print(f"currnode: {currnode}")
			if currnode == provtwo:
				retval = nodedistances[currnode]
				self._distancecache[cachekey] = retval
				# set the reverse distance as the same in the cache too
				self._distancecache[f"{provtwo},{provone}"] = retval
				#print(f"Dijkstra's {provone}->{provtwo} = {retval}")
				return retval
				
			for connection in self.connections[currnode]:
				if nodedistances[connection] is None:
					nodedistances[connection] = nodedistances[currnode] + 1
				else:
					nodedistances[connection] = min(nodedistances[connection], nodedistances[currnode] + 1)
			visitedstates[currnode] = True
			
			nextbestdist = None
			nextbestnode = None
			for node in nodedistances:
				dist = nodedistances[node]
				if dist is not None:
					if visitedstates[node] == False and (nextbestdist is None or dist < nextbestdist):
						nextbestnode = copy.copy(node)
						nextbestdist = copy.copy(dist)
					
			if nextbestnode is None:
				raise NoValidPathError(f"Failed to find path between {provone} and {provtwo}")
				
			currnode = nextbestnode
	def renameProvs(self, namecandidates, **options):
		provs = list(self.connections.keys())
		mindist = options.get("mindistance", 3)
		for prov in provs:
			if random.random() < options.get("renamechance", 0.03):
				renameok = True
				for renamedprov in self.renames:
					if self.getDist(renamedprov, prov) <= mindist:
						renameok = False
						break
				if renameok:
					print(f"Renaming province {prov}...")
					names = []
					neighbourmasks = []
					for neighbour in self.connections[prov]:
						neighbourmasks.append(self.terrains[neighbour])
					for namecandidate in namecandidates:
						if namecandidate.applicable(self.terrains[prov], neighbourmasks):
							names.append(namecandidate)
					if len(names) > 0:
						pick = random.choice(names)
						pick.used = True
						self.renames[prov] = pick.name
					
	def writeMap(self):
		with open(self.fp, "r") as oldf:
			split = splitext(self.fp)
			outfp = split[0]+"_edit" + split[1]
			with open(outfp, "w") as outf:
				writtenedits = False
				for line in oldf:
					if not writtenedits and "#terrain" in line:
						# Insert edits before #terrain lines
						for prov, name in self.renames.items():
							outf.write("#landname {} {}{}{}\n".format(prov, '"', name, '"'))
						writtenedits = True
					outf.write(line)
					
# Stuff to make this usable on a non-CL basis
class Option(object):
	def __init__(self, optname, help="", type=None, default=None):
		self.optname = optname
		self.type = type
		self.help = help
		self.default = default
	def toArgparse(self, parser):
		parser.add_argument(self.optname, help=self.help, type=self.type, default=self.default)
	def askInConsole(self):
		print("\n\n-----------------------")
		s = self.help
		if self.type is bool:
			s += " [y/n]"
		print(s)
		if self.type is bool:
			if self.default:
				print("Default: y")
			else:
				print("Default: n")
		elif self.type in [float, int]:
			print(f"Default: {self.default}")
		else:
			if self.default is None:
				print("Default: <NONE>")
			else:
				print(f"Default: {self.default}")
		valid = False
		print("")
		r = input()
		if r.strip() == "":
			return(self.default)
		if self.type is float:
			try:
				return(float(r))
			except:
				print("Could not convert input to a number. Try again!\n")
				return self.askInConsole()
		if self.type is int:
			try:
				return(int(r))
			except:
				print("Could not convert input to a number. Try again!\n")
				return self.askInConsole()
		if self.type is bool:
			if r.lower() == "y":
				return True
			elif r.lower() == "n":
				return False
			print("Please enter y or n.")
			return self.askInConsole()
		
		else:
			return r

def rename(**options):
	namecandidates = []
	print("Reading namelist...")
	with open(options["namelist"]) as f:
		for line in f:
			if line.strip() == "": continue
			components = line.split("\t")
			namecandidates.append(NameCandidate(components[0], components[1:]))
			
	print("Parsing map...")
	map = Map(options["map"])
	print("Performing renaming...")
	map.renameProvs(namecandidates, **options)
	print("Writing map output...")
	map.writeMap()
	
def main():
	opts = []
	opts.append(Option("-namelist", help="File containing a list of names to use to rename provinces with", type=str, default="namelist.txt"))
	opts.append(Option("-renamechance", help="Chance to rename each province", type=float, default=0.03))
	opts.append(Option("-mindistance", help="Prevent renaming of provinces if they are this far apart (or less) from another renamed province", type=int, default=2))
	opts.append(Option("-map", help="Dominions .map file to modify", type=str, default=""))

	if len(sys.argv) > 1:
		parser = argparse.ArgumentParser(prog=f"ProvinceRenamer v{ver}", description="A tool to randomly rename provinces on Dominions 5 maps!",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)
		for opt in opts:
			opt.toArgparse(parser)
		
		parser.add_argument("-run", help="Pass this if you want to run commmand line mode and not be forced into guided interactive!", default=None)
		args = parser.parse_args()
		rename(**vars(args))
	else:
		print(f"ProvinceRenamer v{ver}: A tool to randomly rename provinces on Dominions 5 maps!")
		print("This program can also be run from command line, pass -h for info.")
		print("Pressing ENTER without writing anything will accept the option's default value.")
		args = {}
		for opt in opts:
			# opt.optname has a leading hyphen
			args[opt.optname[1:]] = opt.askInConsole()
		
		print("Performing renaming...")
		rename(**args)
		print("Complete. Press ENTER to exit.")
		input()
	
if __name__ == "__main__":
	main()
						
						

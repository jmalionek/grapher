#Joseph Malionek
#Grapher v1.3
#Updated for python 3.11, only lightly tested though


import decimal as dec
import tkinter as tk
import math
import cmath
import string
import operator as op
import time
import colorsys

class Grapher:
	#things to add:
	#axes?
	#manual or non-manual upper bound for imaginary
	#label which tells you which mode you are in
	#key-bindings to change mode
	
	def __init__(self,width = 600,height = 600):
		self.root = tk.Tk()
		self.canvas = tk.Canvas(self.root, width = width, height = height, bd = 1, relief = tk.SUNKEN)
		self.canvas.grid(row = 0,rowspan = 20)
		self.h = height
		self.w = width
		self.im = tk.PhotoImage(width = self.w,height = self.h)
		
		#menus
		self.menubar = tk.Menu(self.root)
		self.colorMenu = tk.Menu(self.menubar,tearoff = 0)
		names = ["Heat Map","Rainbow 1","Rainbow 2","Rainbow 3","Greyscale"]
		self.colors = [num2Heat,num2Rain,num2Rain2,num2Rain3,num2Greyscale]
		self.colorVar = tk.IntVar()
		for i in range(len(names)):
			self.colorMenu.add_radiobutton(label=names[i],var = self.colorVar,value = i)
		self.menubar.add_cascade(menu = self.colorMenu,label = "Color Palette")
		self.root.config(menu = self.menubar)
		self.graphMenu = tk.Menu(self.menubar,tearoff = 0)
		graphs = ["Cartesian","Polar","Parametric","Complex"]
		self.graphVar = tk.IntVar()
		self.graphVar.trace("w",self.changeGraphType)
		for i in range(len(graphs)):
			self.graphMenu.add_radiobutton(label = graphs[i],var = self.graphVar,value = i)
		self.menubar.add_cascade(menu = self.graphMenu,label = "Graph Type")
		
		self.labels = {}
		self.entries = {}
		
		def line(name,lab,row,bind):
			(lab,name) = ([lab],[name]) if isinstance(lab,str) else (lab,name)
			for i in range(len(lab)):
				label = tk.Label(self.root,text = lab[i])
				label.grid(row = row,column = 1+2*i)
				ent = tk.Entry(self.root,width = [30,10][len(lab)-1])
				ent.grid(row = row,column = 2+2*i,columnspan = [3,1][len(lab)-1])
				ent.bind("<Return>",bind)
				self.labels[name[i]]=label
				self.entries[name[i]]=ent
		
		temp = ["func","para","graph"]+[[x+"min",x+"max"] for x in "xyz"]
		names = temp+["zext","name","addFunc","addFunc"]
		temp = ["f(x(,y))=","y(t)=","Graph it!"]+[[x+"min=",x+"max="] for x in "xyz"]
		labels = temp+["Manual Z extents","name=","f(x)=","Add to Lib"]
		comms = [self.graphHandle]*6+[None]+[self.addHandle]*3
		buttons = {}
		bts = [2,9]
		for i in range(len(names)):
			if i in bts:
				buttons[names[i]] = tk.Button(self.root,text = labels[i],command = comms[i])
				buttons[names[i]].grid(row = i,column = 1,columnspan = 4)
			elif comms[i]==None:
				self.useZextent = tk.IntVar()
				self.zCheck = tk.Checkbutton(self.root,text = labels[i],var = self.useZextent)
				self.zCheck.grid(row = i,column = 1,columnspan = 4)
			else:
				line(names[i],labels[i],i,comms[i])
		for i in "xyz":
			for j in ["min","max"]:
				self.entries[i+j].insert(0,-10 if j=="min" else 10)

		#miscellaneous
		self.get = lambda thing: self.realParser.exp2num(self.entries[thing].get())
		self.ext = lambda thing: self.get(thing+"max")-self.get(thing+"min")
		self.ext2 = lambda thing: (self.get(thing+"min"),self.get(thing+"max"))
		self.entries["func"].focus_set()
		self.parser = FuncParser()
		self.realParser = self.parser
		self.compParser = CompFuncParser()
		self.colorMenu.invoke(0)
		self.graphMenu.invoke(0)
		
		self.root.mainloop()
	
	def graphOthers(self,funcx,funcy=None):
		tic = time.perf_counter()
		if funcy == None:
			temp = funcx
			funcx = lambda theta: temp(theta)*math.cos(theta)
			funcy = lambda theta: temp(theta)*math.sin(theta)
		step = min(self.ext("y"),self.ext("x"))/max(self.h,self.w)
		ts = my_range(self.get("zmin"),self.get("zmax"),step)
		vals = []
		for t in ts:
			try:
				vals.append([funcx(t),funcy(t)])
			except(ArithmeticError,ValueError):
				vals.append([float("nan"),float("nan")])
		self.graphPairs(vals)
		print("time elapsed",time.perf_counter()-tic)

	def graph1D(self,func):
		xs = my_range(self.get("xmin"),self.get("xmax"),(self.ext("x")/self.w))
		conv = lambda x: -self.h*(x-self.get("ymin"))/(self.ext("y"))+self.h
		funcvalues = [[float("nan")]*2 for x in range(self.w+1)]
		for i in range(len(xs)):
			try:
				funcvalues[i] = [xs[i],func(xs[i])]
			except(ArithmeticError,ValueError):
				pass
		self.graphPairs(funcvalues)

	def graphComp(self,func):
		tic = time.perf_counter()
		funcvalues = [[None for x in range(self.h+1)] for y in range(self.w+1)]
		xs = my_range(self.get("xmin"),self.get("xmax"),(self.ext("x"))/self.w)
		ys = my_range(self.get("ymin"),self.get("ymax"),(self.ext("y"))/self.h)
		for i in range(len(xs)):
			for j in range(len(ys)):
				try:
					value = func(complex(xs[i],ys[j]))
				except (ArithmeticError,ValueError):
					value = complex("NAN")
				funcvalues[i][j] = value
		self.fillvalues = funcvalues
		bound = self.get("zmax")
		bound2 = self.get("zmin")
		for i in range(len(xs)):
			for j in range(len(ys)):
				self.im.put(comp2ArgRad(funcvalues[i][j],bound,bound2),(i,self.h-j))
		self.canvas.create_image(self.h/2+1,self.w/2+1,image = self.im)
		print("time elapsed",time.perf_counter()-tic)
	
	def graph2D(self,func):
		tic = time.perf_counter()
		funcvalues = [[None for x in range(self.h+1)] for y in range(self.w+1)]
		xs = my_range(self.get("xmin"),self.get("xmax"),(self.ext("x"))/self.w)
		ys = my_range(self.get("ymin"),self.get("ymax"),(self.ext("y"))/self.h)
		biggest = float("-inf")
		smallest = float("inf")
		for i in range(len(xs)):
			for j in range(len(ys)):
				try:
					value = func(xs[i],ys[j])
				except (ArithmeticError,ValueError):
					value = float("NAN")
				funcvalues[i][j] = value
				biggest = value if value >biggest else biggest
				smallest = value if value <smallest else smallest
		if self.useZextent.get():
			smallest = self.get("zmin")
			biggest = self.get("zmax")
		for i in range(len(xs)):
			for j in range(len(ys)):
				self.im.put(self.colors[self.colorVar.get()](funcvalues[i][j],[smallest,biggest]),(i,self.h-j))
		self.canvas.create_image(self.h/2+1,self.w/2+1,image = self.im)
		print("time elapsed",time.perf_counter()-tic)
	
	def graphPairs(self,vals):
		convx = lambda x: self.w*(x-self.get("xmin"))/(self.get("xmax")-self.get("xmin"))
		convy = lambda y: -self.h*(y-self.get("ymin"))/(self.get("ymax")-self.get("ymin"))+self.h
		for i in range(len(vals)-1):
			if self.isGoodLine(vals[i],vals[i+1]):
				self.canvas.create_line(convx(vals[i][0]),convy(vals[i][1]),convx(vals[i+1][0]),convy(vals[i+1][1]))
	
	def isGoodLine(self,val1,val2):
		oneInBounds = (self.get("xmin")<=val1[0]<=self.get("xmax") and self.get("ymin")<=val1[1]<=self.get("ymax"))
		twoInBounds = (self.get("xmin")<=val2[0]<=self.get("xmax") and self.get("ymin")<=val2[1]<=self.get("ymax"))
		return (twoInBounds or oneInBounds) and not math.isnan(sum(val1)+sum(val2))
		
	def graph0D(self,exp):
		exp = "could not parse expression" if exp == None else exp
		self.canvas.create_text(self.h/2,self.w/2,text = make_pretty(exp),justify = tk.CENTER)
		
	def graphHandle(self,others = None):
		tic = time.perf_counter()
		self.canvas.delete("all")
		try:
			if self.graphVar.get() in [0,3]:
				self.parser.xChar = "x"
				self.parser.yChar = "y"
				s = self.entries["func"].get()
				if self.parser.hasChar(s,"y"):
					func = self.parser.str2func2(s)
					self.graph2D(func)
				elif self.parser.hasChar(s,"x"):
					if self.graphVar.get() == 0:
						self.graph1D(self.parser.str2func1(s))
					else:
						self.graphComp(self.parser.str2func1(s))
				else:
					#~ "went in to parse"
					try:
						thing = self.parser.exp2num(s)
					except(ArithmeticError,ValueError) as e:
						thing = e
					self.graph0D(thing)
			elif self.graphVar.get() == 2 or self.graphVar.get() == 1:
				self.parser.xChar = "t"
				funcx = self.parser.str2func1(self.entries["func"].get())
				funcy = self.parser.str2func1(self.entries["para"].get()) if self.graphVar.get() == 2 else None
				self.graphOthers(funcx,funcy)
		except Exception as e:
			if isinstance(e,MyException):
				self.graph0D(e)
			else:
				raise e
			
	def addHandle(self,others = None):
		char,self.parser.xChar = self.parser.xChar,"x"
		s = self.entries["addFunc"].get()
		try:
			if self.parser.hasChar(s,"x"):
				self.parser.addFunc(self.entries["name"].get(),s)
			else:
				self.parser.addConst(self.entries["name"].get(),s)
		except Exception as e:
			if isinstance(e,MyException):
				self.canvas.delete("all")
				self.graph0D(e)
			else:
				raise e
		self.entries["addFunc"].delete(0,tk.END)
		self.entries["name"].delete(0,tk.END)
		self.parser.xChar = char
		
	def changeGraphType(self,*others):
		ind = self.graphVar.get()
		funclabels = ["f(x(,y))=","r(t)=","x(t)","f(x)="]
		labels = {"x":["x"]*3+["re(x)"],"y":["y"]*3+["im(x)"]}
		labels["z"] = ["z",chr(920),"t","rad"]
		if ind != 2:
			self.entries["para"].grid_remove()
			self.labels["para"].grid_remove()
		else:
			self.entries["para"].grid(row = 1, column = 2,columnspan = 3)
			self.labels["para"].grid(row = 1, column = 1)
		if ind == 3:
			self.parser = self.compParser
		else:
			self.parser = self.realParser
		for ext in ["min","max"]:
			for dim in "xyz":
				self.labels[dim+ext].config(text = labels[dim][ind]+ext)
		self.labels["func"].config(text = funclabels[ind])

class FuncParser:
	#Things to make it more efficient:
	#turn into tree that can be reduced?
	#get rid of identity functions
	#add specialized simplifiers like x^2,sin(x), x/x
	
	#Thins to add:
	def __init__(self):
		self.chars = ["-+","/*","^"]
		self.ops = [[op.sub,op.add],[op.truediv,op.mul],[pow]]
		self.pres = ["sin","cos","tan","ln","sqrt","abs"]
		self.unaries = [math.sin,math.cos,math.tan,math.log,math.sqrt,abs]
		self.constDict = {"e":math.e,"pi":math.pi}
		self.xChar = "x"
		self.yChar = "y"
	
	def addFunc(self,name,func):
		self.pres.append(name)
		if callable(func):
			self.unaries.append(func)
		else:
			self.unaries.append(self.str2func1(func))
		print(name+"(x)="+func)
	
	def addConst(self,name,value):
		self.constDict[name] = self.exp2num(value)
		print(name+"="+value)

	def str2func1(self,mystring):
		mystring = self.fixString(mystring)
		if mystring == self.xChar:
			return lambda x:x
		if not self.hasChar(mystring,self.xChar):
			temp = self.exp2num(mystring)
			return lambda x:temp
		charDict = self.charsOutOfParens(mystring)
		thing = self.opAndSplit(mystring)
		if thing != None:
			func1 = self.str2func1(thing[1])
			func2 = self.str2func1(thing[2])
			return lambda x: thing[0](func1(x),func2(x))
		for index in range(len(self.pres)):
			if mystring.startswith(self.pres[index]):
				func = self.str2func1(mystring[len(self.pres[index]):])
				return lambda x: self.unaries[index](func(x))
		raise ParseError("Could not parse Expression",mystring)
	
	def str2func2(self,mystring):
		mystring = self.fixString(mystring)
		if mystring == self.xChar:
			return lambda x,y:x
		if mystring == self.yChar:
			return lambda x,y:y
		if not self.hasChar(mystring,self.xChar) and not self.hasChar(mystring,self.yChar):
			temp = self.exp2num(mystring)
			return lambda x,y:temp
		thing = self.opAndSplit(mystring)
		if thing != None:
			func1 = self.str2func2(thing[1])
			func2 = self.str2func2(thing[2])
			return lambda x,y: thing[0](func1(x,y),func2(x,y))
		for index in range(len(self.pres)):
			if mystring.startswith(self.pres[index]):
				func = self.str2func2(mystring[len(self.pres[index]):])
				return lambda x,y: self.unaries[index](func(x,y))
		raise ParseError("Could not parse expression",mystring)

	def exp2num(self,mystring):
		mystring = self.fixString(mystring)
		if mystring in self.constDict:
			return self.constDict[mystring]
		try:
			x = float(mystring)
			return x
		except ValueError:
			thing = self.opAndSplit(mystring)
			if thing != None:
				exp1 = self.exp2num(thing[1])
				exp2 = self.exp2num(thing[2])
				return thing[0](exp1,exp2)
			for index in range(len(self.pres)):
				if mystring.startswith(self.pres[index]):
					thing = self.exp2num(mystring[len(self.pres[index]):])
					return self.unaries[index](thing)
		raise ParseError("Could not parse expression",mystring)

	def opAndSplit(self,mystring):
		charDict = self.charsOutOfParens(mystring)
		for groupIndex in range(len(self.chars)): 
			charList = [-1]*len(self.chars[groupIndex])
			for charIndex in range(len(self.chars[groupIndex])):
				if self.chars[groupIndex][charIndex] in charDict:
					charList[charIndex] = charDict[self.chars[groupIndex][charIndex]]
			if max(charList) != -1:
				maxind = max(charList)
				ind = charList.index(maxind)
				splat = self.splitAt(mystring,maxind)
				return self.ops[groupIndex][ind],splat[0],splat[1]

	def hasChar(self,mystring,char):
		tic = time.perf_counter()
		indList = self.indicesOf(mystring,char)
		if indList == []:
			return False
		funcList = []
		for word in self.pres + list(self.constDict.keys()):
			if char in word:
				funcList.append([word,self.indicesOf(word,char)])
		for index in indList:
			accounted = False
			for pair in funcList:
				shouldBreak = False
				for funcIndex in pair[1]:
					a = index-funcIndex
					b = a+len(pair[0])
					if a>= 0 and b <len(mystring) and mystring[a:index-funcIndex+len(pair[0])]==pair[0]:
						accounted = True
						shouldBreak = True
						break
				if shouldBreak:
					break
			if not accounted:
				return True
		return False
		
		
	def fixString(self,mystring):
		#mystring = filter(lambda x: x not in string.whitespace,mystring)
		mystring = ''.join(mystring.split())
		mystring = mystring.lower()
		if len(mystring)==0:
			raise ParseError("""
Wrong number of arguments for binary or unary 
operator, if you're unsure whether you are 
using + or - as unary operators correctly, 
put parentheses around the expression just to make sure""")
		while mystring[0] == "(" and mystring[-1] == ")":
			mystring = mystring[1:-1]
		if mystring[0] == "-" or mystring[0] == "+":
			mystring = "0"+mystring
		return mystring
		
	def charsOutOfParens(self,mystring):
		paren = 0
		charDict = {}
		for index in range(len(mystring)):
			letter = mystring[index]
			if letter in "()":
				paren+={"(":1,")":-1}[letter]
			elif paren == 0: 
				charDict[letter]=index
		if paren != 0:
			raise ParseError("You have unmatched parentheses")
		return charDict
	
	def indicesOf(self,mystring,char):
		indList = []
		for ind in range(len(mystring)):
			if mystring[ind] == char:
				indList.append(ind)
		return indList
	
	def splitAt(self,s,index):
		return [s[0:index],s[index+1:]]

class CompFuncParser(FuncParser):
	def __init__(self):
		FuncParser.__init__(self)
		conj = lambda x: complex(x.real,-x.imag)
		real = lambda x: x.real
		imag = lambda x: x.imag
		self.unaries = [cmath.sin,cmath.cos,cmath.tan,cmath.log,cmath.sqrt,abs,conj,real,real,imag,imag]
		self.pres.extend(["conj","re","real","imag","im"])
		self.constDict["i"] = 1j
		
	def exp2num(self,mystring):
		mystring = self.fixString(mystring)
		try:
			return complex(mystring)
		except ValueError:
			return FuncParser.exp2num(self,mystring)

def my_range(a,b,c = 1):
	if c*(b-a) <= 0:
		raise RangeError("You will not reach b from a with this step. step={0}, range = [{1},{2}]".format(c,a,b))
	theList= []
	count = 0
	while count*c+a<=b:
		theList.append(count*c+a)
		count= count+1
	return theList

def make_pretty(exp):
	re = lambda x: str(int(x)) if float(x) == int(x) else str(x)
	im= lambda x: "i" if x == 1 else re(x)+'i'
	if isinstance(exp,str) or isinstance(exp,Exception):
		return exp
	try:
		return re(exp)
	except:
		if exp == 0:
			return "0"
		elif exp.real == 0:
			return im(exp.imag)
		elif exp.imag == 0:
			return re(exp.real)
		else:
			return re(exp.real)+"+"+im(exp.imag)


#-----------------------COLORS---------------------------


def stretcher(bounds,num):
	if bounds[0]==bounds[1]:
		return 0
	else:
		return (num-bounds[0])/float(bounds[1] - bounds[0])*255

def peaker(bounds,num):
	if bounds[0] == bounds[1]:
		return 0
	else:
		return -511*abs((num-bounds[0])/float(bounds[1]-bounds[0])-.5)+255

#black is lowest, white is the highest
def num2Greyscale(num,bounds = [0,1]):
	a = stretcher(bounds,num)
	return tuple2color(a,a,a)

#blue is lowest, red is highest
def num2Heat(num,bounds = [0,1]):
	return tuple2color(stretcher(bounds,num),0,255-stretcher(bounds,num))
#red then to pure green, then to blue
def num2Rain(num,bounds = [0,1]):
	return tuple2color((255-2*stretcher(bounds,num)),peaker(bounds,num),2*stretcher(bounds,num)-255)
#red to blue, passing through light green (like above, but not as dominated by green)
def num2Rain2(num,bounds = [0,1]):
	return tuple2color(255-stretcher(bounds,num),peaker(bounds,num),stretcher(bounds,num))
#red to blue, passing through pure green (live num2Rain, but not as dominated by green)
def num2Rain3(num,bounds = [0,1]):
	return tuple2color(255-2*stretcher(bounds,num),2*peaker(bounds,num)-255,2*stretcher(bounds,num)-255)
#red value is real, blue vale is complex
def comp2Heat(num,bounds1,bounds2):
	return tuple2color(stretcher(bounds1,num.real),0,stretcher(bounds2,num.imag))
def comp2ArgRad(num,bound,bound2=0):
	if not abs(num)>bound2:
		return "#000000"
	bound2 = max(bound2,0)
	a = (abs(num)-bound2)/abs(bound-bound2)
	hue = cmath.phase(num)/math.pi/2+1
	thing = colorsys.hsv_to_rgb(hue,1,min(1,a))
	return tuple2color(255*thing[0],255*thing[1],255*thing[2])
	#~ return tuple2color([255*x for x in colorsys.hsv_to_rgb(hue,1,min(1,a))])
def fixTuple(tup):
	tup = (max(0,tup[0]),max(0,tup[1]),max(0,tup[2]))
	tup = (min(255,tup[0]),min(255,tup[1]),min(255,tup[2]))
	return tup

def tuple2color(a, b= None, c = None):
	a, b, c = fixTuple((a,b,c))
	a, b, c = tuple(hex(int(val))[2:] for val in (a,b,c))
	a, b, c = tuple('0' + val if len(val) == 1 else val for val in (a,b,c))
	return "#" + ''.join((a,b,c))
	#return "#%02x%02x%02x" % fixTuple(a) if b == None else "#%02x%02x%02x" % fixTuple((a,b,c))

#------------------------Exceptions-------------------------
class MyException(Exception):
	pass

class ParseError(MyException):
	def __str__(self):
		if len(self.args)>1:
			return self.args[0]+": "+self.args[1]
		return self.args[0]

class RangeError(MyException):
	pass

def main3():
	num = 1-1.1j
	print(cmath.phase(num))
	print(comp2ArgRad(1-1.1j,1))
	
def main2():
	parser = FuncParser()
	func = parser.str2func2("x+y")
	mylist = map(float,range(-5,5))
	print(map(func,mylist,mylist))
	print(map(lambda x,y:x+y,mylist,mylist))
	
def main():
	graphy = Grapher()

if __name__ == "__main__":
	main()

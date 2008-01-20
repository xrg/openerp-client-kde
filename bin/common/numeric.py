# This module includes

## This function converts a string into an integer allowing
#  operations (+, -, /, *).
#  
#  The formula is calculated and the output is returned by 
#  the function. If the formula contains floating point 
#  values or results they're converted into integer at the end.
def textToInteger(text):
	chars=['+', '-', '/', '*', '.', '(', ')', ',']
	chars=chars + [str(x) for x in range(10)]
	text = text.replace(',', '.')
	try:
		return int(eval(text))
	except:
		return False

## This function converts a string into a float allowing
#  operations (+, -, /, *).
#  
#  The formula is calculated and the output is returned by 
#  the function. 
def textToFloat(text):
	chars=['+', '-', '/', '*', '.', '(', ')', ',']
	chars=chars + [str(x) for x in range(10)]
	text = text.replace(',', '.')
	try:
		return float(eval(text))
	except:
		return False


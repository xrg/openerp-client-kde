# This module includes

## @brief This function converts a string into an integer allowing
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

## @brief This function converts a string into a float allowing
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

def floatToText(number, digits=None):
	if digits:
		# Digits might come from the server as a tuple, list or a string
		# So: (14,2), [14,2], '(14,2)' and '[14,2]' are all valid forms
		if isinstance(digits,list) or isinstance(digits,tuple):
			d=str(digits[1])
		else:
			d=digits.split(',')[1].strip(' )]')
	else:
		d='2'
	return ('%.' + d + 'f') % number


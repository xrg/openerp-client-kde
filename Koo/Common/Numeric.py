##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

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

## @brief This function converts a float into text. By default the number
# of decimal digits is 2.
def floatToText(number, digits=None):
	if not number:
		number = 0.0
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


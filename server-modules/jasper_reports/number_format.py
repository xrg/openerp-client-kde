# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 NaN Projectes de Programari Lliure, S.L.
#                         All Rights Reserved.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from decimal import Decimal
import math

SUPPORTED_LANGS = ('en_US', 'es_ES', 'ca_ES')

TENS_UNITS_SEP = {
    'en_US': u"-",
    'es_ES': u" y ", 
    'ca_ES': u"-",
}
CURRENCY_DECIMALS_SEP = {
    'en_US': u"with", 
    'es_ES': u"con", 
    'ca_ES': u"amb",
}
NOT_CURRENCY_DECIMALS_SEP = {
    'en_US': u"dot", 
    'es_ES': u"coma", 
    'ca_ES': u"coma",
}

CURRENCY_INTEGER_NAME = {
    0: {'en_US': u"Euros", 'es_ES': u"Euros", 'ca_ES': u"Euros"},
    1: {'en_US': u"Euro", 'es_ES': u"Euro", 'ca_ES': u"Euro"},
    2: {'en_US': u"Euros", 'es_ES': u"Euros", 'ca_ES': u"Euros"},
}
CURRENCY_DECIMALS_NAME = {
    0: {'en_US': u"Cents", 'es_ES': u"Céntimos", 'ca_ES': u"Cèntims"},
    1: {'en_US': u"Cent", 'es_ES': u"Céntimo", 'ca_ES': u"Cèntim"},
    2: {'en_US': u"Cents", 'es_ES': u"Céntimos", 'ca_ES': u"Cèntims"},
}

TENS = {
    20: {'en_US': u"Twenty", 'es_ES': u"Venti", 'ca_ES': u"Vint"},
    30: {'en_US': u"Thirty", 'es_ES': u"Treinta", 'ca_ES': u"Trenta"},
    40: {'en_US': u"Forty", 'es_ES': u"Cuarenta", 'ca_ES': u"Quaranta"},
    50: {'en_US': u"Fifty", 'es_ES': u"Cincuenta", 'ca_ES': u"Cinquanta"},
    60: {'en_US': u"Sixty", 'es_ES': u"Sesenta", 'ca_ES': u"Seixanta"},
    70: {'en_US': u"Seventy", 'es_ES': u"Setenta", 'ca_ES': u"Setanta"},
    80: {'en_US': u"Eighty", 'es_ES': u"Ochenta", 'ca_ES': u"Vuitanta"},
    90: {'en_US': u"Ninety", 'es_ES': u"Noventa", 'ca_ES': u"Noranta"},
}

HUNDREDS = {
    100: {'en_US': u"One Hundred", 'es_ES': u"Ciento", 'ca_ES': u"Cent"},
    200: {'en_US': u"Two Hundred", 'es_ES': u"Doscientos", 'ca_ES': u"Dos-cents"},
    300: {'en_US': u"Three Hundred", 'es_ES': u"Trescientos", 'ca_ES': u"Tres-ents"},
    400: {'en_US': u"Four Hundred", 'es_ES': u"Cuatrocientos", 'ca_ES': u"Quatre-cents"},
    500: {'en_US': u"Five Hundred", 'es_ES': u"Quinientos", 'ca_ES': u"Cinc-cents"},
    600: {'en_US': u"Six Hundred", 'es_ES': u"Seiscientos", 'ca_ES': u"Sis-cents"},
    700: {'en_US': u"Seven Hundred", 'es_ES': u"Setecientos", 'ca_ES': u"Set-cents"},
    800: {'en_US': u"Eight Hundred", 'es_ES': u"Ochocientos", 'ca_ES': u"Vuit-cents"},
    900: {'en_US': u"Nine Hundred", 'es_ES': u"Novecientos", 'ca_ES': u"Nou-cents"},
}

GREATER = {
    1000: {'en_US': u"One Thousand", 'es_ES': u"Mil", 'ca_ES': u"Mil"},
    1000000: {'en_US': u"One Million", 'es_ES': u"Millones", 'ca_ES': u"Milions"},
}

UNITS = TENS.copy()
UNITS.update(HUNDREDS)
UNITS.update(GREATER)
UNITS.update({
    0: {'en_US': u"Zero", 'es_ES': u"Cero", 'ca_ES': u"Zero"},
    1: {'en_US': u"One", 'es_ES': u"Un", 'ca_ES': u"Un"},
    2: {'en_US': u"Two",'es_ES': u"Dos", 'ca_ES': u"Dos"},
    3: {'en_US': u"Three",'es_ES': u"Tres", 'ca_ES': u"Tres"},
    4: {'en_US': u"Four",'es_ES': u"Cuatro", 'ca_ES': u"Quatre"},
    5: {'en_US': u"Five",'es_ES': u"Cinco", 'ca_ES': u"Cinc"},
    6: {'en_US': u"Six",'es_ES': u"Seis", 'ca_ES': u"Sis"},
    7: {'en_US': u"Seven",'es_ES': u"Siete", 'ca_ES': u"Set"},
    8: {'en_US': u"Eight",'es_ES': u"Ocho", 'ca_ES': u"Vuit"},
    9: {'en_US': u"Nine",'es_ES': u"Nueve", 'ca_ES': u"Nou"},
    10: {'en_US': u"Ten",'es_ES': u"Diez", 'ca_ES': u"Deu"},
    11: {'en_US': u"Eleven",'es_ES': u"Once", 'ca_ES': u"Onze"},
    12: {'en_US': u"Twelve",'es_ES': u"Doce", 'ca_ES': u"Dotze"},
    13: {'en_US': u"Thirteen",'es_ES': u"Trece", 'ca_ES': u"Tretze"},
    14: {'en_US': u"Fourteen",'es_ES': u"Catorce", 'ca_ES': u"Catorze"},
    15: {'en_US': u"Fifteen",'es_ES': u"Quince", 'ca_ES': u"Quinze"},
    16: {'en_US': u"Sixteen",'es_ES': u"Dieciséis", 'ca_ES': u"Setze"},
    17: {'en_US': u"Seventeen",'es_ES': u"Diecisiete", 'ca_ES': u"Disset"},
    18: {'en_US': u"Eighteen",'es_ES': u"Dieciocho", 'ca_ES': u"Divuit"},
    19: {'en_US': u"Nineteen",'es_ES': u"Diecinueve", 'ca_ES': u"Dinou"},
    # When the values is exactly '20', is so called
    20: {'es_ES': u"Veinte", 'ca_ES': u"Vint"},
    21: {'es_ES': u"Veintiún", 'ca_ES': u"Vint-i-un"},
    22: {'es_ES': u"Veintidós", 'ca_ES': u"Vint-i-dos"},
    23: {'es_ES': u"Veintitrés", 'ca_ES': u"Vint-i-tres"},
    24: {'es_ES': u"Veinticuatro", 'ca_ES': u"Vint-i-quatre"},
    25: {'es_ES': u"Veinticinco", 'ca_ES': u"Vint-i-cinc"},
    26: {'es_ES': u"Veintiséis", 'ca_ES': u"Vint-i-sis"},
    27: {'es_ES': u"Veintisiete", 'ca_ES': u"Vint-i-set"},
    28: {'es_ES': u"Veintiocho", 'ca_ES': u"Vint-i-vuit"},
    29: {'es_ES': u"Veintinueve", 'ca_ES': u"Vint-i-nou"},
    # When the values is exactly '100', is so called
    100: {'en_US': u"Hundred", 'es_ES': u"Cien", 'ca_ES': u"Cent"},
    1000: {'en_US': u"Thousand", 'es_ES': u"Mil", 'ca_ES': u"Mil"},
    1000000: {'en_US': u"Million", 'es_ES': u"Un Millón", 'ca_ES': u"Un Milió"},
})


def integer_to_literal(input_int, lang_code):
    assert type(input_int) == int, "Invalid type of parameter. Expected 'int' "\
            "but found %s" % str(type(input_int))
    assert lang_code and lang_code in SUPPORTED_LANGS, "The Language Code " \
            "is not supported. The suported languages are: %s" \
                    % ", ".join(SUPPORTED_LANGS[:-1]) + " and " + \
                            SUPPORTED_LANGS[-1]
    
    if input_int in UNITS and lang_code in UNITS[input_int]:
        return UNITS[input_int][lang_code]
    
    million = int(math.floor(Decimal(str(input_int)) / 1000000))
    thousands = input_int - million * 1000000
    thousands = int(math.floor(Decimal(str(thousands)) / 1000))
    hundreds = input_int - million * 1000000 - thousands * 1000
    
    
    def __convert_hundreds(input_hundred):
        assert (input_hundred and 
                type(input_hundred) == int and 
                input_hundred < 1000), "Invalid Hundred input"
        
        if input_hundred in UNITS and lang_code in UNITS[input_hundred]:
            return [UNITS[input_hundred][lang_code]]
        
        res = []
        
        hundreds_value = (input_hundred / 100) * 100
        if hundreds_value:
            res.append(HUNDREDS[hundreds_value][lang_code])
            input_hundred -= hundreds_value
            if not input_hundred:
                return res
        
        if input_hundred in UNITS and lang_code in UNITS[input_hundred]:
            # values <= 30 or X0
            res.append(UNITS[input_hundred][lang_code])
            return res
        
        # XY; X >= 3 and y != 0
        tens_value = (input_hundred / 10) * 10
        units_value = input_hundred - tens_value
        if TENS_UNITS_SEP and lang_code in TENS_UNITS_SEP:
            res.append(TENS[tens_value][lang_code] + TENS_UNITS_SEP[lang_code] +
                    UNITS[units_value][lang_code])
        else:
            res.append(TENS[tens_value][lang_code])
            res.append(UNITS[units_value][lang_code])
        
        return res
    
    converted = []
    if million:
        if million == 1:
            converted.append(UNITS[1000000][lang_code])
        else:
            converted += __convert_hundreds(million)
            converted.append(GREATER[1000000][lang_code])
        
        input_int -= million * 1000000
    
    if thousands:
        if thousands == 1:
            converted.append(UNITS[1000][lang_code])
        else:
            converted += __convert_hundreds(thousands)
            converted.append(GREATER[1000][lang_code])
    
    if hundreds:
        # exactly 100 is already contempleted
        converted += __convert_hundreds(hundreds)
    return u" ".join(converted)


def number_to_literal(input_number, lang_code, rounding=0.01, is_currency=True):
    assert lang_code and lang_code in SUPPORTED_LANGS, "The Language Code " \
            "is not supported. The suported languages are: %s" \
                    % ", ".join(SUPPORTED_LANGS[:-1]) + " and " + \
                            SUPPORTED_LANGS[-1]
    
    PREC = Decimal(str(rounding))
    
    input_number = Decimal(str(input_number)).quantize(PREC)
    
    number_int = int(math.floor(input_number))
    decimals = int((input_number - number_int) * (1 / PREC))
    
    res = []
    res.append(integer_to_literal(number_int, lang_code))
    
    if is_currency:
        if (number_int in CURRENCY_INTEGER_NAME and 
                lang_code in CURRENCY_INTEGER_NAME[number_int]):
            res.append(CURRENCY_INTEGER_NAME[number_int][lang_code])
        else:
            res.append(CURRENCY_INTEGER_NAME[2][lang_code])
        
        if decimals:
            res.append(CURRENCY_DECIMALS_SEP[lang_code])
    elif decimals:
        res.append(NOT_CURRENCY_DECIMALS_SEP[lang_code])
    
    if decimals:
        res.append(integer_to_literal(decimals, lang_code))
        if is_currency:
            if (decimals in CURRENCY_DECIMALS_NAME and 
                    lang_code in CURRENCY_DECIMALS_NAME[decimals]):
                res.append(CURRENCY_DECIMALS_NAME[decimals][lang_code])
            else:
                res.append(CURRENCY_DECIMALS_NAME[2][lang_code])
    
    return " ".join(res)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


from collections import defaultdict
from datetime import datetime
from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall, split as regex_split

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from google_trans_new import google_translator
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang


class AmountToText(models.Model):
    _name = "amount.to.text"
    _description = "Amount to text"

    """ language acronyms {'af': 'afrikaans', 'sq': 'albanian', 'am': 'amharic', 'ar': 'arabic', 'hy': 'armenian', 'az': 'azerbaijani', 'eu': 'basque', 'be': 'belarusian', 'bn': 'bengali', 'bs': 'bosnian', 'bg': 'bulgarian', 'ca': 'catalan', 
    'ceb': 'cebuano', 'ny': 'chichewa', 'zh-cn': 'chinese (simplified)', 'zh-tw': 'chinese (traditional)', 'co': 'corsican', 'hr': 'croatian', 'cs': 'czech', 'da': 'danish', 'nl': 'dutch', 'en': 'english', 'eo': 'esperanto', 'et': 'estonian', 'tl': 'filipino', 'fi': 'finnish', 'fr': 'french', 'fy': 'frisian', 'gl': 'galician', 'ka': 'georgian', 'de': 'german', 'el': 'greek', 'gu': 'gujarati', 'ht': 'haitian creole', 'ha': 'hausa', 'haw': 'hawaiian', 'iw': 'hebrew', 'he': 'hebrew', 'hi': 'hindi', 'hmn': 'hmong', 'hu': 'hungarian', 'is': 'icelandic', 'ig': 'igbo', 'id': 'indonesian', 'ga': 'irish', 'it': 'italian', 'ja': 'japanese', 'jw': 'javanese', 'kn': 'kannada', 'kk': 'kazakh', 'km': 'khmer', 'ko': 'korean', 'ku': 'kurdish (kurmanji)', 'ky': 'kyrgyz', 'lo': 'lao', 'la': 'latin', 'lv': 'latvian', 'lt': 'lithuanian', 'lb': 'luxembourgish', 'mk': 'macedonian', 'mg': 'malagasy', 'ms': 'malay', 'ml': 'malayalam', 'mt': 'maltese', 'mi': 'maori', 'mr': 'marathi', 'mn': 'mongolian', 'my': 'myanmar (burmese)', 'ne': 'nepali', 'no': 'norwegian', 'or': 'odia', 'ps': 'pashto', 'fa': 'persian', 'pl': 'polish', 'pt': 'portuguese', 'pa': 'punjabi', 'ro': 'romanian', 'ru': 'russian', 'sm': 'samoan', 'gd': 'scots gaelic', 'sr': 'serbian', 'st': 'sesotho', 'sn': 'shona', 'sd': 'sindhi', 'si': 'sinhala', 'sk': 'slovak', 'sl': 'slovenian', 'so': 'somali', 'es': 'spanish', 'su': 'sundanese', 'sw': 'swahili', 'sv': 'swedish', 'tg': 'tajik', 'ta': 'tamil', 'te': 'telugu', 'th': 'thai', 'tr': 'turkish', 'tk': 'turkmen', 'uk': 'ukrainian',
    'ur': 'urdu', 'ug': 'uyghur', 'uz': 'uzbek', 'vi': 'vietnamese', 'cy': 'welsh', 'xh': 'xhosa', 'yi': 'yiddish', 'yo': 'yoruba', 'zu': 'zulu'}"""
   
    def number_to_amount(self,number,currency,language):
        muz=(' ','Onze', 'Douze', 'Treize',
              'Quatorze', 'Quinze', 'Seize', 'Dix-Sept', 'Dix-Huit', 'Dix-Neuf' )
        to_19_fr = ( 'Zéro',  'Un',   'Deux',  'Trois', 'Quatre',   'Cinq',   'Six',
              'Sept', 'Huit', 'Neuf', 'Dix',   'Onze', 'Douze', 'Treize',
              'Quatorze', 'Quinze', 'Seize', 'Dix-Sept', 'Dix-Huit', 'Dix-Neuf' )
        tens_fr  = ( 'Vingt', 'Trente', 'Quarante', 'Cinquante', 'Soixante', 'Soixante-Dix', 'Quatre-Vingt', 'Quatre-Vingt Dix')
        denom_fr = ( '',
              'Mille',     'Million(s)',         'Milliards',       'Billions',       'Quadrillions',
              'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
              'Décillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
              'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Icosillion', 'Vigintillion' )
        
        def _convert_nn_fr(val):
            """ convertion des valeurs < 100 en Français
            """
            if val < 20:
                return to_19_fr[val]
            for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_fr)):
                  if dval + 10 > val:
                        if val % 10:
                              if(val>70 and val <= 79):
                                   dcap='Soixante'
                                   return dcap + '-' +muz[val % 10]
                              
                              if(val>90 and val <=99 ):
                                    dcap='Quatre-vingt'
                                    return dcap + '-' +muz[val % 10]
                              else:
                                      return dcap + '-' +to_19_fr[val % 10]
                        return(dcap)
        def _convert_nnn_fr(val):
            """ convert a value < 1000 to french
            
                special cased because it is the level that kicks 
                off the < 100 special case.  The rest are more general.  This also allows you to
                get strings in the form of 'forty-five hundred' if called directly.
            """
            word = ''
            (mod, rem) = (val % 100, val // 100)
            b = val // 100
            if rem > 0:
                 if b == 1 :
                       word= 'Cent'
                 else:
                       word = to_19_fr[rem] + ' Cent'
            if mod > 0:
                    word += ' '
            if mod > 0:
                word += _convert_nn_fr(mod)
            return word
        def french_number(val):
            if val < 100:
                return _convert_nn_fr(val)
            if val < 1000:
                 return _convert_nnn_fr(val)
            for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_fr))):
                if dval > val:
                    mod = 1000 ** didx
                    l = val // mod
                    r = val - (l * mod)
                    if (l ==1 ) and (denom_fr[didx] == 'Mille'):
                        ret = denom_fr[didx]
                    else:
                          ret = _convert_nnn_fr(l) + ' ' + denom_fr[didx]
                    if r > 0:
                        ret = ret + ' ' + french_number(r)
                    return ret
        number = '%.2f' %number
        list = str(number).split('.')
        muzamil=(french_number(abs(int(list[0]))))
        start_word = muzamil
        end_word =' '
        curr=currency
        cents_number = int(list[1])
        cents_name = (cents_number > 1) and ' '+curr or curr
        final_result = start_word +end_word +cents_name +' et '+ str(cents_number)
        translator = google_translator()  
        final_result = translator.translate(final_result,lang_src='fr', lang_tgt=language)
        cen_var=translator.translate('Centimes',lang_src='fr', lang_tgt=language)
        return(final_result+' '+cen_var)

   



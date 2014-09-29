# coding= utf-8


import requests

from lxml import html
from osv import osv, fields
import xml.etree.ElementTree as ET


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'vat': fields.char('TIN', size=11, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements.")
    }

    def button_check_vat(self, cr, uid, ids, context=None):

        link = 'http://www.sunat.gob.pe/w/wapS01Alias?ruc=20509849316'
        cliente = requests.get(link)

        cliente = cliente.text.replace('\r', '').replace('\n', '').replace('\t', '')
        #root = ET.fromstring(cliente)
        root = html.fromstring(cliente)
        print root[2].attrib
        print root[2][0][0].text_content()
        print root[2][0][7].text_content()
        print root[2][0][9].text_content()

        return True


res_partner()

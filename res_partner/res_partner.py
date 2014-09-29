# coding= utf-8


import requests

from lxml import html
from osv import osv, fields
import xml.etree.ElementTree as ET


class res_partner(osv.osv):
    _inherit = 'res.partner'

    def on_change_ruc(self, cr, uid, ids, vat, context=None):
        if len(vat) == 11:
            link = 'http://www.sunat.gob.pe/w/wapS01Alias?ruc=%s' % vat
            cliente = requests.get(link)
            cliente = cliente.text.replace('\r', '').replace('\n', '').replace('\t', '')
            root = html.fromstring(cliente)
            print root[2].attrib
            print root[2][0][0].text_content()
            print root[2][0][7].text_content()
            print root[2][0][9].text_content()
            name = root[2][0][0].text_content().split('-')
            return {
                'value': {'name': name[1][1:-1]}
            }
        return {}

    _columns = {
        'vat': fields.char('TIN', size=11, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements.")
    }


res_partner()

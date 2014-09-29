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
            name = root[2][0][0].text_content().split('-')
            if root[2].attrib['id'] == 'frstcard':
                name = root[2][0][0].text_content().split('-')
                street = root[2][0][9].text_content()
                return {
                    'value': {'name': name[1][1:-1],
                              'street': street[9:]}
                }
            else:
                return {
                    'value': {'name': "El numero Ruc ingresado es invalido"}
                }
        return {'value': {'name': False, 'street': False}}

    _columns = {
        'vat': fields.char('TIN', size=11, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements.")
    }


res_partner()

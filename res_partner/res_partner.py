# coding= utf-8


import requests

from lxml import html
from openerp import tools, api
from openerp.osv import osv, fields
from openerp.tools.translate import _
import xml.etree.ElementTree as ET


class res_partner(osv.Model):
    _inherit = 'res.partner'

    @api.multi
    def on_change_ruc(self, vat):
        if vat:
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
                    raise osv.except_osv(
                        _('Error'),
                        _('Ruc no existe'))
            return {'value': {'name': False, 'street': False}}
        return False

    _columns = {
        'vat': fields.char('TIN', size=11, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements.")
    }


res_partner()

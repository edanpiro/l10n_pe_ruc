# coding= utf-8


import requests
import pytesseract
import StringIO

from PIL import Image
from bs4 import BeautifulSoup
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.constrains('vat')
    def _check_vat(self):
        partner = self.search([('is_company', '=', True), '!', ('id', '=', self.id)])
        vat = [obj.vat for obj in partner]
        if self.vat in vat:
            raise ValidationError('El numero de documento ya existe')

    @api.multi
    def button_check(self):
        vat = self.vat
        if vat:
            if len(vat) == 11:
                names = None
                street = None
                factor = '5432765432'
                sum = 0
                dig_check = False
                try:
                    int(vat)
                except:
                    raise except_orm(_('Error !'),
                                     _('El documento no debe tener letras'))
                for f in range(0, 10):
                    sum += int(factor[f]) * int(vat[f])

                subtraction = 11 - (sum % 11)
                if subtraction == 10:
                    dig_check = 0
                elif subtraction == 11:
                    dig_check = 1
                else:
                    dig_check = subtraction
                if int(vat[10]) == dig_check:
                    session = requests.session()
                    url = 'http://www.sunat.gob.pe/cl-ti-itmrconsruc/captcha?accion=image'
                    name_image = '/tmp/captcha.jpeg'
                    request_image = session.get(url, stream=True)
                    with open(name_image, 'wb') as f:
                        for chunk in request_image.iter_content():
                            f.write(chunk)
                    captcha_val = pytesseract.image_to_string(Image.open(name_image))
                    captcha_val = captcha_val.strip().upper()

                    if captcha_val.isalpha():
                        consult = session.get("http://www.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorRuc&razSoc=&nroRuc="+vat+"&nrodoc=&contexto=rrrrrrr&tQuery=on&search1="+vat+"&codigo="+captcha_val+"&tipdoc=1&search2=&coddpto=&codprov=&coddist=&search3=")
                        text_error = 'Surgieron problemas al procesar la consulta'
                        text_consult = consult.text
                        if text_error in text_consult:
                            raise except_orm(_('Error !'),
                                             _('Consulte nuevamente'))
                        else:
                            text_consult = StringIO.StringIO(text_consult).readlines()
                            temp = 0
                            for li in text_consult:
                                if temp == 1:
                                    soup = BeautifulSoup(li)
                                    street = soup.td.string.replace('  ', '')
                                    break
                                if li.find("Domicilio Fiscal:") != -1:
                                    temp = 1
                            for li in text_consult:
                                if li.find("desRuc") != -1:
                                    soup = BeautifulSoup(li)
                                    names = soup.input['value']
                                    break
                            self.write({'names': names, 'name': names, 'street': street})
                    else:
                        raise except_orm(_('Error !'),
                                         _('Captcha no reconocido, intente nuevamente'))
                else:
                    raise except_orm(_('Error !'),
                                     _('El RUC ingresado no es correcto'))
            else:
                raise except_orm(_('Error !'),
                                 _('Debe tener 11 digitos'))
        return False

    document_type = fields.Selection(
        [('0', 'OTROS TIPOS DE DOCUMENTOS'),
         ('1', 'DOCUMENTO NACIONAL DE IDENTIDAD (DNI)'),
         ('4', 'CARNET DE EXTRANJERIA'),
         ('6', 'REGISTRO UNICO DE CONTRIBUYENTES'),
         ('7', 'PASAPORTE'),
         ('A', 'CEDULA DIPLOMÁTICA DE IDENTIDAD')],
        'Documento', default='6'
    )

    vat = fields.Char('TIN', size=11, help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements.")

# coding= utf-8


import requests
import pytesseract
import StringIO
import logging

from PIL import Image
from bs4 import BeautifulSoup
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.constrains('vat')
    def _check_vat(self):
        for obj in self:
            if obj.is_company:
                partner = self.search([('is_company', '=', True),
                                       '!', ('id', '=', self.id)])
                vat = [obj.vat for obj in partner]
                if self.vat in vat:
                    raise ValidationError('El numero de documento ya existe')

    def _get_captcha(self, type):
        s = requests.session()
        if type == '6':
            try:
                r = s.get('http://www.sunat.gob.pe/cl-ti-itmrconsruc/captcha?accion=image')
            except s.exceptions.RequestException as e:
                return (False, e)
            img = Image.open(StringIO.StringIO(r.content))
            captcha_val = pytesseract.image_to_string(img)
            captcha_val = captcha_val.strip().upper()
            return (s, captcha_val)
        elif type == '1':
            try:
                r = s.get('https://cel.reniec.gob.pe/valreg/codigo.do')
            except s.exceptions.RequestException as e:
                return (False, e)
            img = Image.open(StringIO.StringIO(r.content))
            img = img.convert("RGBA")
            pixdata = img.load()
            for y in xrange(img.size[1]):
                for x in xrange(img.size[0]):
                    red, green, blue, alplha=pixdata[x, y]
                    if blue < 100:
                        pixdata[x, y] = (255, 255, 255, 255)
            temp_captcha_val = pytesseract.image_to_string(img)
            temp_captcha_val = temp_captcha_val.strip().upper()
            captcha_val = ''
            for i in range(len(temp_captcha_val)):
                if temp_captcha_val[i].isalpha() or temp_captcha_val[i].isdigit():
                    captcha_val = captcha_val + temp_captcha_val[i]
            return (s, captcha_val.upper())


    @api.multi
    def button_check(self):
        vat = self.vat
        document_type = self.document_type
        res = {}
        if vat and document_type == '6':
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
                if not int(vat[10]) == dig_check:
                    raise except_orm(_('Connection error !'),
                                     _('The RUC entered is incorrect'))
                for i in range(10):
                    consulta, captcha_val = self._get_captcha(document_type)
                    if not consulta:
                        res['warning'] = {}
                        res['warning']['title'] = _('Connection error')
                        res['warning']['message'] = _('The server is not available! try again!')
                        return res
                    if captcha_val.isalpha():
                        break
                get = consulta.get("http://www.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorRuc&razSoc="+
                                   "&nroRuc="+vat+"&nrodoc=&contexto=rrrrrrr&tQuery=on&search1="+vat+
                                   "&codigo="+captcha_val+"&tipdoc=1&search2=&coddpto=&codprov=&coddist=&search3=")
                texto_error = 'Surgieron problemas al procesar la consulta'
                texto_consulta=get.text
                if texto_error in (texto_consulta):
                    raise except_orm(_('Error !'),
                                     _('Consulte nuevamente'))
                else:
                    texto_consulta=StringIO.StringIO(texto_consulta).readlines()

                    temp = 0
                    tnombre = tdireccion = tncomercial = tnstate = False

                    for li in texto_consulta:
                        if temp == 1:
                            soup = BeautifulSoup(li)
                            tdireccion = soup.td.string
                            district = ' '.join(tdireccion.split('-')[-1].split())
                            province = ' '.join(tdireccion.split('-')[-2].split())
                            tdireccion = ' '.join(tdireccion.split())
                            tdireccion = ' '.join(tdireccion.split('-')[0:-2])

                            district_obj = self.env['res.country.district']
                            dist_id = district_obj.search([('name', '=', district),
                                                           ('province_id.name', '=', province)], limit=1)

                            if dist_id:
                                res.update({
                                    'district_id': dist_id.id,
                                    'province_id': dist_id.province_id.id,
                                    'state_id': dist_id.province_id.state_id.id,
                                    'country_id': dist_id.province_id.state_id.country_id.id,
                                    'zip': dist_id.code[2:]
                                })
                                logging.getLogger('Server2').info('res:%s' % res)
                            break

                        if li.find('Domicilio Fiscal:') != -1:
                            temp = 1
                    for li in texto_consulta:
                        if li.find("desRuc") != -1:
                            soup = BeautifulSoup(li)
                            tnombre = soup.input['value']
                            break

                    temp = 0
                    for li in texto_consulta:
                        if temp == 1:
                            soup = BeautifulSoup(li)
                            tncomercial = soup.td.string
                            if tncomercial == '-':
                                tncomercial = tnombre
                            break

                        if li.find("Nombre Comercial:") != -1:
                            temp = 1

                    temp = 0
                    for li in texto_consulta:
                        if temp == 1:
                            soup = BeautifulSoup(li)
                            tactive = soup.td.string
                            if tactive != 'ACTIVO':
                                raise except_orm(_('Advertencia!'),
                                                _('El RUC ingresado no esta ACTIVO'))
                            break

                        if li.find("Estado del Contribuyente:") != -1:
                            temp = 1
                    temp = 0
                    for li in texto_consulta:
                        if temp >= 1:
                            temp += 1

                        if temp == 4:
                            soup = BeautifulSoup(li)
                            if soup.p:
                                tstate = str(soup.p.string)
                                tstate = tstate[0:6]
                                if tstate == 'HABIDO':
                                    tstate = 'habido'
                            else:
                                tstate = 'nhabido'
                            break

                        if li.find("Condici&oacute;n del Contribuyente:") != -1:
                            temp = 1
                    res.update({
                        'names': tncomercial,
                        'name': tncomercial,
                        'street': tdireccion,
                        'is_company': True
                    })
                    self.write(res)
        else:
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

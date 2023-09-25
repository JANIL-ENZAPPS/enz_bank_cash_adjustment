from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError


class PosPayment(models.Model):
    _inherit = "pos.payment"

    pos_order_id = fields.Many2one('pos.order', string='Order',required=False)
    not_actual = fields.Boolean()
    company_id = fields.Many2one('res.company', string='Company', related='payment_method_id.company_id')  # TODO: add store=True in master
    new_session_id = fields.Many2one('pos.session')



    @api.constrains('payment_method_id')
    def _check_payment_method_id(self):
        for payment in self:
            if self.not_actual == False:
                if payment.payment_method_id not in payment.session_id.config_id.payment_method_ids:
                    raise ValidationError(_('The payment method selected is not allowed in the config of the POS session.'))


class PosChangePayments(models.TransientModel):
    _name = 'pos.change.payments'
    _description = 'POS Change Payments'

    session_id = fields.Many2one('pos.session')
    payment_lines = fields.One2many('pos.change.payments.lines','change_id')
    total = fields.Float()
    actual_total = fields.Float()


    def post_payments(self):
        if self.total == self.actual_total:
            bank = 0
            cash = 0
            for payments in self.payment_lines:
                if payments.difference != 0:
                    self.env['pos.payment'].create({
                        'not_actual':True,
                        # 'session_id':self.session_id.id,
                        'new_session_id':self.session_id.id,
                        'amount':payments.difference,
                        'payment_method_id':payments.method_id.id,
                        'name':"Fix Difference in " + self.session_id.name,
                        'company_id':self.session_id.company_id.id,
                    })
                    if payments.method_id.name == 'Bank':
                        bank = bank + payments.difference
                    if payments.method_id.name == 'Cash':
                        cash = cash + payments.difference
            if bank and cash != 0:
                print("Bank : ",bank)
                print("Cash : ",cash)
                if bank > 0:
                    journal_id = self.env['account.journal'].search(
                        [('name', '=', 'Bank'), ('company_id', '=', self.env.user.company_id.id)]).id
                    debit_account_id = self.env['account.account'].search([('name', '=', 'Bank Suspense Account')])
                    credit_account_id = self.env['account.account'].search([('name', '=', 'Cash')])
                    journal_list_1 = []
                    journal_line_two = (0, 0, {
                        'account_id': debit_account_id.id,
                        'name': self.session_id.name,
                        'debit': bank,
                    })
                    journal_list_1.append(journal_line_two)
                    journal_line_one = (0, 0, {
                        'account_id': credit_account_id.id,
                        'name': self.session_id.name,
                        'credit': bank,
                    })
                    journal_list_1.append(journal_line_one)
                    bank_move_id = self.env['account.move'].create({
                        'date': self.session_id.start_at.date(),
                        'ref': self.session_id.name,
                        'journal_id': journal_id,
                        'line_ids': journal_list_1,
                    })
                    bank_move_id.action_post()
                else:
                    journal_id = self.env['account.journal'].search(
                        [('name', '=', 'Cash'), ('company_id', '=', self.env.user.company_id.id)]).id
                    credit_account_id = self.env['account.account'].search([('name', '=', 'Bank Suspense Account')])
                    debit_account_id = self.env['account.account'].search([('name', '=', 'Cash')])
                    journal_list_1 = []
                    journal_line_two = (0, 0, {
                        'account_id': debit_account_id.id,
                        'name': self.session_id.name,
                        'debit': cash,
                    })
                    journal_list_1.append(journal_line_two)
                    journal_line_one = (0, 0, {
                        'account_id': credit_account_id.id,
                        'name': self.session_id.name,
                        'credit': cash,
                    })
                    journal_list_1.append(journal_line_one)
                    cash_move_id = self.env['account.move'].create({
                        'date': self.session_id.start_at.date(),
                        'ref': self.session_id.name,
                        'journal_id': journal_id,
                        'line_ids': journal_list_1,
                    })
                    cash_move_id.action_post()

        else:
            raise UserError("Total Amount is Not equal to Editted Amount")

    @api.onchange('session_id')
    def payment_methods(self):
        payments_list = []
        total_amount = 0
        if self.session_id:
            payments = self.env['pos.payment'].search(['|',('session_id','=',self.session_id.id),('new_session_id','=',self.session_id.id)])
            for methods in payments.mapped('payment_method_id'):
                amount = sum(self.env['pos.payment'].search([('session_id', '=', self.session_id.id),('payment_method_id','=',methods.id)]).mapped('amount'))
                amount = amount + sum(self.env['pos.payment'].search([('new_session_id','=',self.session_id.id),('payment_method_id','=',methods.id)]).mapped('amount'))
                payments_line = (0,0,{
                    'method_id':methods.id,
                    'amount':amount,
                    'actual_amount':amount,
                })
                payments_list.append(payments_line)
                total_amount = total_amount + amount
            self.payment_lines = payments_list
            self.actual_total = total_amount
            self.total = total_amount
        else:
            self.payment_lines = payments_list

    @api.onchange('payment_lines')
    def compute_amount(self):
        self.actual_total = sum(self.payment_lines.mapped('actual_amount'))

class PosChangePaymentsLines(models.TransientModel):
    _name = 'pos.change.payments.lines'
    _description = 'POS Change Payments Lines'

    change_id = fields.Many2one('pos.change.payments')
    method_id = fields.Many2one('pos.payment.method')
    amount = fields.Float()
    actual_amount = fields.Float()
    difference = fields.Float()

    @api.onchange('actual_amount','amount')
    def check_difference(self):
        self.difference = self.actual_amount - self.amount
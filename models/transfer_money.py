from odoo import fields, models, _, api
from datetime import datetime, date


class TransferMoney(models.Model):
    _name = 'transfer.money'
    _inherit = "mail.thread"
    _description = 'Transfer Money'

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('money.transfer.seq') or _('New')
        return super(TransferMoney, self).create(vals)

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    date = fields.Date(default=fields.Date.context_today, required=1,tracking=True)
    ref = fields.Char(string="Description",tracking=True)
    form_account_id = fields.Many2one('account.account',tracking=True)
    to_account_id = fields.Many2one('account.account',tracking=True)
    amount = fields.Float(tracking=True)
    move_id = fields.Many2one('account.move')
    stmt_id = fields.Many2one('account.bank.statement')
    adjustment_id = fields.Many2one('bank.cash.adjustment')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], default='draft',tracking=True)
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    cash_transfer = fields.Boolean()

    # Draft Second
    def reset_draft(self):
        account_ids = self.env['account.journal'].search(
            [('type', '=', 'bank'), ('company_id', '=', self.company_id.id)]).mapped('default_account_id').ids
        if self.to_account_id.id in account_ids and self.form_account_id not in account_ids:
            journ = self.env['account.journal'].search([('default_account_id', '=', self.to_account_id.id)])
            if self.env['account.bank.statement'].search([]):
                if self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)]):
                    bal = self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)])[
                        0].balance_end_real
                else:
                    bal = 0
            else:
                credit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_credit_account_id.id)]).mapped(
                    'debit'))
                debit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_debit_account_id.id)]).mapped(
                    'debit'))
                bal = debit - credit
            # bank_move_line = self.move_id.line_ids.filtered(lambda a: a.name == self.name + ' - ' + self.to_account_id.name)
            stmt = self.env['account.bank.statement'].create({'name': journ.company_id.partner_id.name,
                                                              'balance_start': bal,
                                                              'journal_id': journ.id,
                                                              'balance_end_real': bal + -self.amount

                                                              })
            payment_list = []
            product_line = (0, 0, {
                'date': datetime.today().date(),
                'name': self.name,
                'partner_id': journ.company_id.partner_id.id,
                'payment_ref': self.ref,
                'amount': -self.amount
            })
            payment_list.append(product_line)
            if stmt:
                stmt.line_ids = payment_list
                stmt.button_post()
                stmt.move_line_ids = False
                stmt.write({'state': 'confirm'})
        elif self.form_account_id.id in account_ids and self.to_account_id not in account_ids:
            journ = self.env['account.journal'].search([('default_account_id', '=', self.form_account_id.id)])
            if self.env['account.bank.statement'].search([]):
                if self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)]):
                    bal = self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)])[
                        0].balance_end_real
                else:
                    bal = 0
            else:
                credit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_credit_account_id.id)]).mapped(
                    'debit'))
                debit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_debit_account_id.id)]).mapped(
                    'debit'))
                bal = debit - credit
            # bank_move_line = self.move_id.line_ids.filtered(lambda a: a.name == self.name + ' - ' + self.to_account_id.name)
            stmt = self.env['account.bank.statement'].create({'name': journ.company_id.partner_id.name,
                                                              'balance_start': bal,
                                                              'journal_id': journ.id,
                                                              'balance_end_real': bal + self.amount

                                                              })
            payment_list = []
            product_line = (0, 0, {
                'date': datetime.today().date(),
                'name': self.name,
                'partner_id': journ.company_id.partner_id.id,
                'payment_ref': self.ref,
                'amount': self.amount
            })
            payment_list.append(product_line)
            if stmt:
                stmt.line_ids = payment_list
                stmt.button_post()
                stmt.move_line_ids = False
                stmt.write({'state': 'confirm'})
                self.stmt_id = stmt.id
        else:
            self.move_id.button_draft()
        self.state = 'draft'

    # # Draft First
    # def reset_draft(self):
    #     self.state = 'draft'
    #     self.move_id.button_draft()

    # Post Second
    def post(self):
        account_ids = self.env['account.journal'].search(
            [('type', '=', 'bank'), ('company_id', '=', self.company_id.id)]).mapped('default_account_id').ids
        if self.to_account_id.id in account_ids and self.form_account_id not in account_ids:
            journ = self.env['account.journal'].search([('default_account_id', '=', self.to_account_id.id)])
            if self.env['account.bank.statement'].search([]):
                if self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)]):
                    bal = self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)])[
                        0].balance_end_real
                else:
                    bal = 0
            else:
                credit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_credit_account_id.id)]).mapped(
                    'debit'))
                debit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_debit_account_id.id)]).mapped(
                    'debit'))
                bal = debit - credit
            # bank_move_line = self.move_id.line_ids.filtered(lambda a: a.name == self.name + ' - ' + self.to_account_id.name)
            stmt = self.env['account.bank.statement'].create({'name': journ.company_id.partner_id.name,
                                                              'balance_start': bal,
                                                              'journal_id': journ.id,
                                                              'balance_end_real': bal + self.amount

                                                              })
            payment_list = []
            product_line = (0, 0, {
                'date': datetime.today().date(),
                'name': self.name,
                'partner_id': journ.company_id.partner_id.id,
                'payment_ref': self.ref,
                'amount': self.amount
            })
            payment_list.append(product_line)
            if stmt:
                stmt.line_ids = payment_list
                stmt.button_post()
                stmt.move_line_ids = False
                stmt.write({'state': 'confirm'})
                self.stmt_id = stmt.id
        elif self.form_account_id.id in account_ids and self.to_account_id not in account_ids:
            journ = self.env['account.journal'].search([('default_account_id', '=', self.form_account_id.id)])
            if self.env['account.bank.statement'].search([]):
                if self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)]):
                    bal = self.env['account.bank.statement'].search(
                        [('company_id', '=', journ.company_id.id), ('journal_id', '=', journ.id)])[
                        0].balance_end_real
                else:
                    bal = 0
            else:
                credit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_credit_account_id.id)]).mapped(
                    'debit'))
                debit = sum(self.env['account.move.line'].search(
                    [('account_id', '=', journ.payment_debit_account_id.id)]).mapped(
                    'debit'))
                bal = debit - credit
            # bank_move_line = self.move_id.line_ids.filtered(lambda a: a.name == self.name + ' - ' + self.to_account_id.name)
            stmt = self.env['account.bank.statement'].create({'name': journ.company_id.partner_id.name,
                                                              'balance_start': bal,
                                                              'journal_id': journ.id,
                                                              'balance_end_real': bal + -self.amount

                                                              })
            payment_list = []
            product_line = (0, 0, {
                'date': datetime.today().date(),
                'name': self.name,
                'partner_id': journ.company_id.partner_id.id,
                'payment_ref': self.ref,
                'amount': -self.amount
            })
            payment_list.append(product_line)
            if stmt:
                stmt.line_ids = payment_list
                stmt.button_post()
                stmt.move_line_ids = False
                stmt.write({'state': 'confirm'})
                self.stmt_id = stmt.id
        else:
            if self.amount > 0:
                journal_id = self.env['account.journal'].search(
                    [('name', '=', 'Bank'), ('company_id', '=', self.env.user.company_id.id)]).id
                journal_list_1 = []
                journal_line_two = (0, 0, {
                    'account_id': self.to_account_id.id,
                    'name': self.name,
                    'debit': self.amount,
                })
                journal_list_1.append(journal_line_two)
                journal_line_one = (0, 0, {
                    'account_id': self.form_account_id.id,
                    'name': self.name,
                    'credit': self.amount,
                })
                journal_list_1.append(journal_line_one)
                self.move_id = self.env['account.move'].create({
                    'date': self.date,
                    'ref': self.name,
                    'journal_id': journal_id,
                    'line_ids': journal_list_1,
                }).id
                self.move_id.action_post()
                self.state = 'posted'
        self.state = 'posted'

    # Post First
    # def post(self):
    #     if self.form_account_id and self.to_account_id:
    #         if self.amount > 0:
    #             journal_id = self.env['account.journal'].search(
    #                 [('name', '=', 'Bank'), ('company_id', '=', self.env.user.company_id.id)]).id
    #             journal_list_1 = []
    #             journal_line_two = (0, 0, {
    #                 'account_id': self.to_account_id.id,
    #                 'name': self.name,
    #                 'debit': self.amount,
    #             })
    #             journal_list_1.append(journal_line_two)
    #             journal_line_one = (0, 0, {
    #                 'account_id': self.form_account_id.id,
    #                 'name': self.name,
    #                 'credit': self.amount,
    #             })
    #             journal_list_1.append(journal_line_one)
    #             self.move_id = self.env['account.move'].create({
    #                 'date': self.date,
    #                 'ref': self.name,
    #                 'journal_id': journal_id,
    #                 'line_ids': journal_list_1,
    #             }).id
    #             self.move_id.action_post()
    #             self.state = 'posted'

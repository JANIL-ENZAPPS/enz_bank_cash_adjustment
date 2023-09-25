from odoo import fields,models,_,api
from odoo.exceptions import UserError

class BankCashAdjustment(models.Model):
    _name = 'bank.cash.adjustment'
    _inherit = "mail.thread"
    _description = 'Bank Cash Adjustment'
    _order = 'id desc'

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('adjustment.seq') or _('New')
        return super(BankCashAdjustment, self).create(vals)

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    date = fields.Date(default=fields.Date.context_today,required=1,tracking=True)
    from_date = fields.Date(tracking=True)
    to_date = fields.Date(tracking=True)
    account_id = fields.Many2one('account.account',tracking=True)
    # bank_account_id = fields.Many2one('account.account')
    opening_balance = fields.Float(tracking=True)
    closing_balance = fields.Float(tracking=True)
    # amount = fields.Float()
    state = fields.Selection([('draft','Draft'),('verified','Verified'),('completed','Completed')],default='draft',tracking=True)
    company_id = fields.Many2one("res.company",string="Company",required=True,default=lambda self: self.env.company)
    transfer_count = fields.Integer(compute="compute_transfer_count")
    cash_transfer_count = fields.Integer(compute="compute_cash_transfer_count")

    def reset_draft(self):
        transfers = self.env['transfer.money'].search([('adjustment_id','=',self.id)])
        if transfers:
            post_count = 0
            for transfer in transfers:
                if transfer.state == 'posted':
                    post_count += 1
            if post_count > 0:
                raise UserError("Please Draft all the Transfers Related To This Adjustment To Draft State")
        self.state = 'draft'

    def completed(self):
        self.state = 'completed'

    def compute_transfer_count(self):
        for line in self:
            line.transfer_count = len(self.env['transfer.money'].search([('adjustment_id','=',line.id),('cash_transfer','=',False)]))

    def compute_cash_transfer_count(self):
        for line in self:
            line.cash_transfer_count = len(self.env['transfer.money'].search([('adjustment_id','=',line.id),('cash_transfer','=',True)]))

    def verified(self):
        self.state = 'verified'


    @api.onchange('date')
    def compute_account_id(self):
        if not self.account_id:
            account_id = self.env['account.account'].search([('name', '=', 'Bank Suspense Account'),('company_id','=',self.company_id.id)])
            self.account_id = account_id[-1].id


    def show_transfers(self):
        transfers = self.env['transfer.money'].search([('adjustment_id','=',self.id),('cash_transfer','=',False)]).ids
        return {
            'name': _('Transfer Money'),
            'domain':[('id','in',transfers)],
            'view_type': 'form',
            'res_model': 'transfer.money',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def show_cash_transfers(self):
        transfers = self.env['transfer.money'].search([('adjustment_id','=',self.id),('cash_transfer','=',True)]).ids
        return {
            'name': _('Transfer Money'),
            'domain':[('id','in',transfers)],
            'view_type': 'form',
            'res_model': 'transfer.money',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def create_cash_transfer(self):
        cash = self.env['account.account'].search([('name','=','Cash'),('company_id','=',self.company_id.id)])
        if cash:
            cash = cash[-1]
        else:
            cash = None
        return {
            'name': _('Transfer Money'),
            'view_type': 'form',
            'res_model': 'transfer.money',
            'view_id': False,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'context':{
                'default_adjustment_id':self.id,
                'default_to_account_id':cash.id,
                'default_form_account_id':self.account_id.id,
                'default_cash_transfer':True,
            }
        }


    def create_transfer(self):
        return {
            'name': _('Transfer Money'),
            'view_type': 'form',
            'res_model': 'transfer.money',
            'view_id': False,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'context':{
                'default_adjustment_id':self.id,
                'default_form_account_id':self.account_id.id,
            }
        }


    @api.onchange('from_date','to_date','account_id')
    def old_balance(self):
        balance = 0
        if self.account_id.id:
            if self.from_date and self.to_date:
                olds = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '<', self.from_date),
                         ('move_id.state', '=', 'posted')])
                balance = sum(olds.mapped('debit')) + sum(olds.mapped('credit'))
        self.opening_balance = balance

    @api.onchange('from_date','to_date','account_id','opening_balance')
    def total_balance(self):
        if self.account_id.id:
            moves = 0
            if self.from_date and self.to_date:
                moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')]).mapped('balance'))
            # else:
            #     moves = sum(self.env['account.move.line'].search(
            #             [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
            #              ('full_reconcile_id', '=', False)]).mapped('balance'))
            self.closing_balance = moves + self.opening_balance

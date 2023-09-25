from odoo import fields,models,_,api

class BnkStmt(models.TransientModel):
    _name = 'bank.stmt'
    _description = 'Bank Statement'



    journal_id = fields.Many2one('account.journal')
    account_id = fields.Many2one('account.account')
    from_date = fields.Date()
    to_date = fields.Date()
    balance = fields.Float()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('company.branches', string='Branch', domain="[('company_id','=',company_id)]")

    @api.onchange('journal_id')
    def compute_account(self):
        if self.journal_id:
            self.account_id = self.journal_id.default_account_id.id
        else:
            self.account_id = None

    @api.onchange('account_id', 'from_date', 'to_date')
    def compute_balance(self):
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                    self.balance = sum(moves.mapped('balance'))
                else:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')])
                    self.balance = sum(moves.mapped('balance'))
            else:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted')])
                self.balance = sum(moves.mapped('balance'))

    def create_report(self):
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')])
            else:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted')])
            view_id = self.env.ref('account.view_move_line_tree_grouped_general').id
            action_vals = {
                'name': _('Balance'),
                'domain': [('id', 'in', moves.ids)],
                'view_type': 'form',
                'res_model': 'account.move.line',
                'view_id': view_id,
                'view_mode': 'tree',
                'type': 'ir.actions.act_window',
            }
            return action_vals

    def print_reports(self):
        return self.env.ref('enz_bank_cash_adjustment.bankaccountstmt_report_id').report_action(self)

    def old_balance(self):
        balance = 0
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    olds = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '<', self.from_date),
                         ('move_id.state', '=', 'posted'), ('branch_id', '=', self.branch_id.id)])
                    balance = sum(olds.mapped('debit')) + sum(olds.mapped('credit'))
                else:
                    olds = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '<', self.from_date),
                         ('move_id.state', '=', 'posted')])
                    balance = sum(olds.mapped('debit')) + sum(olds.mapped('credit'))
        return balance

    def print_all(self):
        moves = []
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')])
            else:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted')])
            return moves

    def total_debit(self):
        moves = 0
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)]).mapped('debit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')]).mapped('debit'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('branch_id', '=', self.branch_id.id)]).mapped('debit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False)]).mapped('debit'))
            return moves

    def total_credit(self):
        moves = 0
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)]).mapped('credit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')]).mapped('credit'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('branch_id', '=', self.branch_id.id)]).mapped('credit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False)]).mapped('credit'))
            return moves

    def total_balance_lines(self):
        moves = 0
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')]).mapped('balance'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False)]).mapped('balance'))
            return moves

    def total_balance(self):
        moves = 0
        if self.account_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')]).mapped('balance'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('account_id', '=', self.account_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False)]).mapped('balance'))
            moves = moves + self.old_balance()
            return moves
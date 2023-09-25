from odoo import fields,models,_,api

class PartnerStmt(models.TransientModel):
    _name = 'partner.stmt'
    _description = 'Partner Statement'


    partner_id = fields.Many2one('res.partner')
    from_date = fields.Date()
    to_date = fields.Date()
    balance = fields.Float()
    branch_id = fields.Many2one('company.branches', string='Branch', domain="[('company_id','=',company_id)]")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    @api.onchange('partner_id', 'from_date', 'to_date')
    def compute_balance(self):
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)])
                    self.balance = sum(moves.mapped('balance'))
                else:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])])
                    self.balance = sum(moves.mapped('balance'))
            else:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])])
                self.balance = sum(moves.mapped('balance'))

    def create_report(self):
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')])
            else:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted')])
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
        return self.env.ref('enz_bank_cash_adjustment.stmt_report_id').report_action(self)

    def old_balance(self):
        balance = 0
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    olds = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '<', self.from_date),
                         ('move_id.state', '=', 'posted'),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)])
                    balance = sum(olds.mapped('debit')) + sum(olds.mapped('credit'))
                else:
                    olds = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '<', self.from_date),
                         ('move_id.state', '=', 'posted'),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])])
                    balance = sum(olds.mapped('debit')) + sum(olds.mapped('credit'))
        return balance

    def print_all(self):
        moves = []
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted')])
            else:
                if self.branch_id:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('branch_id', '=', self.branch_id.id)])
                else:
                    moves = self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted')])
            return moves

    def total_debit(self):
        moves = 0
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('debit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('debit'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('debit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('debit'))
            return moves

    def total_credit(self):
        moves = 0
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('credit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('credit'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('credit'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('credit'))
            return moves

    def total_balance_lines(self):
        moves = 0
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('balance'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('balance'))
            return moves

    def total_balance(self):
        moves = 0
        if self.partner_id.id:
            if self.from_date and self.to_date:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                         ('date', '<=', self.to_date), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False),
                         ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('balance'))
            else:
                if self.branch_id:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable']),
                         ('branch_id', '=', self.branch_id.id)]).mapped('balance'))
                else:
                    moves = sum(self.env['account.move.line'].search(
                        [('partner_id', '=', self.partner_id.id), ('move_id.state', '=', 'posted'),
                         ('full_reconcile_id', '=', False), ('balance', '!=', 0), ('account_id.reconcile', '=', True),
                         ('account_id.internal_type', 'in', ['payable', 'receivable'])]).mapped('balance'))
            moves = moves + self.old_balance()
            return moves
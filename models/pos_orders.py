from odoo import fields, api, models
from datetime import datetime, date


class PosSession(models.Model):
    _inherit = 'pos.session'

    bank_move_id = fields.Many2one('account.move')

    def create_bank_move(self):
        amount = 0
        for line in self.move_id.line_ids:
            if line.account_id.name == 'Account Receivable (PoS)':
                label1, label2 = line.name.split('-')
                if label2 == ' Bank':
                    amount = line.debit
        if amount > 0:
            journal_id = self.env['account.journal'].search(
                [('name', '=', 'Bank'), ('company_id', '=', self.env.user.company_id.id)]).id
            debit_account_id = self.env['account.account'].search([('name', '=', 'Bank Suspense Account')])
            credit_account_id = self.env['account.account'].search([('name', '=', 'Account Receivable (PoS)')])
            journal_list_1 = []
            journal_line_two = (0, 0, {
                'account_id': debit_account_id.id,
                'name': self.name,
                'debit': amount,
            })
            journal_list_1.append(journal_line_two)
            journal_line_one = (0, 0, {
                'account_id': credit_account_id.id,
                'name': self.name,
                'credit': amount,
            })
            journal_list_1.append(journal_line_one)
            bank_move_id = self.env['account.move'].create({
                'date': self.start_at.date(),
                'ref': self.name,
                'journal_id': journal_id,
                'line_ids': journal_list_1,
            })
            bank_move_id.action_post()
            self.bank_move_id = bank_move_id.id

    def action_pos_session_validate(self):
        rec = super(PosSession, self).action_pos_session_validate()
        self.create_bank_move()
        return rec

    def action_pos_session_closing_control(self):
        rec = super(PosSession, self).action_pos_session_closing_control()
        self.create_bank_move()
        return rec


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('name', 'journal_id', 'state')
    def _check_unique_sequence_number(self):
        moves = self.filtered(lambda move: move.state == 'posted')
        if not moves:
            return

        self.flush(['name', 'journal_id', 'move_type', 'state'])

        # /!\ Computed stored fields are not yet inside the database.
        self._cr.execute('''
            SELECT move2.id, move2.name
            FROM account_move move
            INNER JOIN account_move move2 ON
                move2.name = move.name
                AND move2.journal_id = move.journal_id
                AND move2.move_type = move.move_type
                AND move2.id != move.id
            WHERE move.id IN %s AND move2.state = 'posted'
        ''', [tuple(moves.ids)])
        res = self._cr.fetchall()
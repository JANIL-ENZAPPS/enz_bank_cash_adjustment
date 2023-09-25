from odoo import fields,models,_

class PosSession(models.Model):
    _inherit = 'pos.session'


    def action_show_payments_list(self):
        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.payment',
            'view_mode': 'tree,form',
            'domain': ['|',('session_id', '=', self.id),('new_session_id','=',self.id)],
            'context': {'search_default_group_by_payment_method': 1}
        }

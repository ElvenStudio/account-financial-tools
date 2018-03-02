# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def action_renumber(self, number_next=1, update_related_invoice_number=False):

        sequence_ids_seen = []
        for move in self:
            fiscalyear_id = move.period_id.fiscalyear_id.id
            sequence = move.journal_id.sequence_id.get_sequence_id_for_fiscalyear_id(fiscalyear_id)
            if sequence.id not in sequence_ids_seen:
                sequence.write({'number_next': number_next})
                sequence_ids_seen.append(sequence.id)

            # Generate (using our own get_id) and write the new move number
            new_number = sequence.with_context(fyscalyear_id=fiscalyear_id).next_by_id(sequence.id)

            # Note: We can't just do a "move_obj.write(cr, uid, [move.id], {'name': new_name})"
            # cause it might raise a ``You can't do this modification on a confirmed entry`` exception.
            self._cr.execute('UPDATE account_move SET name=%s WHERE id=%s', (new_number, move.id))
            self.invalidate_cache()

        if update_related_invoice_number:
            invoices = self.env['account.invoice'].search([('move_id', 'in', self.ids)])
            invoices.renumber_invoices_from_move_id()

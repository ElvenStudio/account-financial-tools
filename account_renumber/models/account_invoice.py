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

from openerp import models, api, _
from  openerp.exceptions import ValidationError

# import logging
# _log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _detach_move_from_invoices(self, start_invoice, invoice_list):
        """
        Detach the move from invoice. 
        If the number on the move_id is already used into another invoice (in invoice_list) 
        then detach the linked invoice too.
        :param start_invoice: the first invoice to check
        :param invoice_list: the list of other invoice to check with the start invoice move_id number
        :return: a list of tuple [(account.invoice, account.move)] with all the invoice detached and the related account.move
        """
        new_number = start_invoice.move_id.name

        # check if another invoice has the same number
        external_invoice = self.search(
            [
                ('number', '=', new_number),
                ('id', 'not in', invoice_list.ids)
            ]
        )

        if external_invoice:
            raise ValidationError(_(
                'Cannot renumber invoice %s, '
                'because the new number is the same of the invoice %s. '
                'Extend periods to renumber correctly all invoices.' % start_invoice.number, external_invoice.number))

        detached_move_number = start_invoice.move_id.name
        detached_invoice = [(start_invoice, start_invoice.move_id)]
        start_invoice.write({'move_id': False})

        linked_invoice = invoice_list.filtered(lambda i: i.number == detached_move_number)
        if linked_invoice:
            detached_invoice += self._detach_move(linked_invoice, invoice_list)

        return detached_invoice

    @api.multi
    def renumber_invoices_from_move_id(self):
        """
        Update invoices number, getting it from the related account.move move_id.
        """
        updated_invoice_ids = []
        for invoice in self:
            if invoice.id not in updated_invoice_ids and invoice.move_id and invoice.number != invoice.move_id.name:
                # In order to update the invoice number,
                # the only way is to detach the move_id from the invoice
                # and reattach it.
                #
                # The invoice number then can be replaced with the new one.
                # Trying to set the invoice number as empty or False
                # will raise an SQL Constraint error!
                detached_invoices = self.env['account.invoice']._detach_move_from_invoices(invoice, self)

                for detached_invoice, move in detached_invoices:
                    # update ref move field,
                    # because it can differ from the new one assigned
                    move.write({'ref': move.name})

                    # reattach move_id to the invoice,
                    # and update the number fields
                    detached_invoice.write({
                        'number': move.name,
                        'internal_number': move.name,
                        'move_id': move.id}
                    )

                    # avoid to recheck the invoice in the main loop
                    updated_invoice_ids.append(detached_invoice.id)

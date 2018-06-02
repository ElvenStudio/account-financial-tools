# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
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
from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


class wizard_renumber(orm.TransientModel):
    _name = "wizard.renumber"
    _description = "Account renumber wizard"
    _columns = {
        'journal_ids': fields.many2many(
            'account.journal',
            'account_journal_wzd_renumber_rel',
            'wizard_id', 'journal_id',
            required=True,
            help="Journals to renumber",
            string="Journals"
        ),

        'period_ids': fields.many2many(
            'account.period',
            'account_period_wzd_renumber_rel',
            'wizard_id', 'period_id',
            required=True,
            help='Fiscal periods to renumber',
            string="Periods",
            ondelete='null'
        ),

        'number_next': fields.integer(
            _('First Number'),
            required=True,
            help=_("Journal sequences will start counting on this number")
        ),

        'update_related_invoice_number': fields.boolean(
            _('Update related invoice'),
            help=_('Update the invoice number when moves refer to an invoice journal.')
        ),

        'update_related_voucher_number': fields.boolean(
            _('Update related voucher'),
            help=_('Update the voucher number when moves refer to a voucher.')
        ),

        'state': fields.selection(
            [
                ('init', 'Initial'),
                ('renumber', 'Renumbering')
            ],
            readonly=True
        )
    }

    _defaults = {
        'update_related_invoice_number': False,
        'number_next': 1,
        'state': 'init'
    }

    ##########################################################################
    # Renumber form/action
    ##########################################################################

    def renumber(self, cr, uid, ids, context=None):
        """
        Action that renumbers all the posted moves on the given
        journal and periods, and returns their ids.
        """
        form = self.browse(cr, uid, ids[0], context=context)
        period_ids = [x.id for x in form.period_ids]
        journal_ids = [x.id for x in form.journal_ids]
        number_next = form.number_next or 1
        update_related_invoice_number = form.update_related_invoice_number or False
        update_related_voucher_number = form.update_related_voucher_number or False

        if not (period_ids and journal_ids):
            raise orm.except_orm(_('No Data Available'), _('No records found for your selection!'))

        _logger.debug("Searching for account moves to renumber.")
        move_obj = self.pool['account.move']
        move_domain = [('journal_id', 'in', journal_ids), ('period_id', 'in', period_ids), ('state', '=', 'posted')]
        move_ids = move_obj.search(cr, uid, move_domain, limit=0, order='date,id', context=context)

        if not move_ids:
            raise orm.except_orm(_('No Data Available'), _('No account moves found for your selection!'))

        _logger.debug("Renumbering %d account moves.", len(move_ids))
        moves = move_obj.browse(cr, uid, move_ids, context=context)
        moves.action_renumber(number_next, update_related_invoice_number, update_related_voucher_number)
        _logger.debug("%d account moves renumbered.", len(move_ids))

        form.write({'state': 'renumber'})
        data_obj = self.pool['ir.model.data']
        view_ref = data_obj.get_object_reference(cr, uid, 'account', 'view_move_tree')
        view_id = view_ref and view_ref[1] or False,
        res = {
            'type': 'ir.actions.act_window',
            'name': _("Renumbered account moves"),
            'res_model': 'account.move',
            'domain': ("[('journal_id','in',%s), ('period_id','in',%s), "
                       "('state','=','posted')]"
                       % (journal_ids, period_ids)),
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': view_id,
            'context': context,
            'target': 'current',
        }
        return res

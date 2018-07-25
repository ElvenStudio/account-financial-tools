# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 - 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountMoveTemplate(models.Model):
    _name = 'account.move.template'
    _inherit = 'account.document.template'

    @api.model
    def _company_get(self):
        return self.env['res.company']._company_default_get(
            object='account.move.template'
        )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=_('Company'),
        required=True,
        change_default=True,
        default=_company_get,
    )
    template_line_ids = fields.One2many(
        comodel_name='account.move.template.line',
        inverse_name='template_id',
        string=_('Template Lines')
    )

    cross_journals = fields.Boolean(string=_('Cross-Journals'))

    cross_partners = fields.Boolean(string=_('Cross-Partners'))

    transitory_acc_id = fields.Many2one(
        comodel_name='account.account',
        string=_('Transitory account'),
        required=False
    )

    note = fields.Text()

    @api.one
    @api.constrains('cross_partners')
    def _check_template_move_line_partners(self):
        error_message = _(
            'You cannot unset the cross-partners flag because '
            'the move line %s has a partner. Please remove it first.'
        )
        
        if not self.cross_partners:
            for line in self.template_line_ids:
                if line.partner_id:
                    raise ValidationError(error_message % line.name)


class AccountMoveTemplateLine(models.Model):
    _name = 'account.move.template.line'
    _inherit = 'account.document.template.line'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string=_('Journal'),
        required=True
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string=_('Account'),
        required=True,
        ondelete="cascade"
    )
    move_line_type = fields.Selection(
        [('cr', 'Credit'), ('dr', 'Debit')],
        string=_('Move Line Type'),
        required=True
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=_('Analytic Account'),
        ondelete="cascade"
    )
    template_id = fields.Many2one(
        comodel_name='account.move.template',
        string=_('Template')
    )
    account_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string=_('Tax')
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string=_('Partner'),
        required=False,
        ondelete="cascade"
    )

    cross_partner = fields.Boolean(
        string=_('Cross-Partner'),
        related='template_id.cross_partners'
    )

    _sql_constraints = [
        (
            'sequence_template_uniq',
            'unique (template_id,sequence)',
            _('The sequence of the line must be unique per template !')
        )
    ]

    @api.constrains('journal_id')
    def _check_different_journal(self):
        # Check that the journal on these lines are different/same in the case
        # of cross journals/single journal
        journal_ids = []
        all_journal_ids = []
        error_message = _(
            u'If the template is "cross-journals", the Journals must be '
            u'different, if the template does not "cross-journals" the '
            u'Journals must be the same!'
        )
        for move_template in self.template_id:
            if move_template.template_line_ids:
                for template_line in move_template.template_line_ids:
                    all_journal_ids.append(template_line.journal_id.id)
                    if template_line.journal_id.id not in journal_ids:
                        journal_ids.append(template_line.journal_id.id)
                if move_template.cross_journals:
                    if len(all_journal_ids) != len(journal_ids):
                        raise ValidationError(error_message)
                elif len(journal_ids) != 1:
                    raise ValidationError(error_message)

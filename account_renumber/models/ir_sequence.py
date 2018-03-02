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


from openerp import models, api


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.multi
    def get_sequence_id_for_fiscalyear_id(self, fiscalyear_id):
        """
        Based on ir_sequence.get_id from the account module.
        Allows us to get the real sequence for the given fiscal year.
        :param fiscalyear_id: the fiscal year used to find the correct sequence
        :return: the sequence related to the fiscalyear, self otherwise.
        """
        self.ensure_one()

        for line in self.fiscal_ids:
            if line.fiscalyear_id.id == fiscalyear_id:
                return line.sequence_id

        # if no subsequence are defined, return the main one.
        return self

# Copyright (c) 2015-2023 Odoo S.A.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from .taxcloud_request import TaxCloudRequest

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_account_taxcloud_tc = fields.Boolean(string="Account TaxCloud")
    taxcloud_api_id = fields.Char(
        related="company_id.taxcloud_api_id", string="TaxCloud API ID", readonly=False
    )
    taxcloud_api_key = fields.Char(
        related="company_id.taxcloud_api_key", string="TaxCloud API KEY", readonly=False
    )
    tic_category_id = fields.Many2one(
        related="company_id.tic_category_id", string="Default TIC Code", readonly=False
    )

    def sync_taxcloud_category(self):
        Category = self.env["product.tic.category"]
        request = TaxCloudRequest(self.taxcloud_api_id, self.taxcloud_api_key)
        res = request.get_tic_category()

        if res.get("error_message"):
            raise ValidationError(
                _("Unable to retrieve taxes from TaxCloud: ")
                + "\n"
                + res["error_message"]
            )
        _logger.info(
            "fetched %s TICs from Taxcloud, saving in database", len(res["data"])
        )

        for category in res["data"]:
            if not Category.search([("code", "=", category["TICID"])], limit=1):
                Category.create(
                    {"code": category["TICID"], "description": category["Description"]}
                )
        if not self.env.company.tic_category_id:
            self.env.company.tic_category_id = Category.search(
                [("code", "=", 0)], limit=1
            )
        return True

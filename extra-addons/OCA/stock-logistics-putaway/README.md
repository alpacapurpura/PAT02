
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/stock-logistics-putaway&target_branch=18.0)
[![Pre-commit Status](https://github.com/OCA/stock-logistics-putaway/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/OCA/stock-logistics-putaway/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/OCA/stock-logistics-putaway/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/OCA/stock-logistics-putaway/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/OCA/stock-logistics-putaway/branch/18.0/graph/badge.svg)](https://codecov.io/gh/OCA/stock-logistics-putaway)
[![Translation Status](https://translation.odoo-community.org/widgets/stock-logistics-putaway-18-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/stock-logistics-putaway-18-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Stock Put-away

Enhance the way put-aways are computed on move lines for properly storing the products in the stock.

Are you looking for modules related to logistics? Or would like to contribute
to? There are many repositories with specific purposes. Have a look at this
[README](https://github.com/OCA/wms/blob/18.0/README.md).

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[stock_picking_putaway_recompute](stock_picking_putaway_recompute/) | 18.0.1.0.0 | <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | This module allows to recompute the picking operations putaways if configurations have changed
[stock_putaway_hook](stock_putaway_hook/) | 18.0.1.0.0 |  | Add hooks allowing modules to add more putaway strategies
[stock_storage_type](stock_storage_type/) | 18.0.1.4.1 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> <a href='https://github.com/rousseldenis'><img src='https://github.com/rousseldenis.png' width='32' height='32' style='border-radius:50%;' alt='rousseldenis'/></a> | Manage packages and locations storage types
[stock_storage_type_buffer](stock_storage_type_buffer/) | 18.0.1.0.1 |  | Exclude storage locations from put-away if their buffer is full
[stock_storage_type_putaway_abc](stock_storage_type_putaway_abc/) | 18.0.1.0.1 |  | Advanced storage strategy ABC for WMS

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.

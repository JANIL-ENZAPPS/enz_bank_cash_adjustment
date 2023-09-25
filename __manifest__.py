# -*- coding: utf-8 -*-
{
    'name': "Bank Cash Adjustment",
    'author':
        'Enzapps',
    'summary': """
    This is a module is for Bank Cash Adjustment
""",

    'description': """
        This is a module is for Bank Cash Adjustment
    """,
    'website': "www.enzapps.com",
    'category': 'base',
    'version': '14.0',
    'depends': ['base','contacts','account','point_of_sale'],
    "images": ['static/description/icon.png'],
    'data': [
        'data/account.xml',
        'reports/header.xml',
        'reports/report_view.xml',
        'reports/report.xml',
        'security/ir.model.access.csv',
        'wizards/change_payments.xml',
        'views/bank_cash_adjustment.xml',
        'views/transfer_money.xml',
        'views/partnet_stmt.xml',
        'views/account_stmt.xml',
        'views/bank_stmt.xml',
        'views/session.xml',
],
    'demo': [
    ],
    'installable': True,
    'application': True,
}

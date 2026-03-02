{
    "name": "Caribbean – Gastos de Transporte",
    "version": "18.0.1.0.0",
    "category": "Accounting/Expenses",
    "summary": "Extensión de gastos para transporte Caribbean",
    "author": "Caribbean",
    "website": "https://www.caribbeanport.com.gt",
    "license": "LGPL-3",

    "depends": [
        "base",
        "account",
        "hr_expense",
        "fleet",
    ],

    "data": [
        # ======================
        # SECURITY
        # ======================
        "security/ir.model.access.csv",

        # ======================
        # DATA (CRON / CONFIG)
        # ======================
        "data/sequence.xml",
        "data/cron_internal_financing.xml",
        
        
        # ======================
        # VIEWS
        # ======================
        "views/hr_expense_view.xml",
        "views/maintenance_view.xml",
        "views/res_company_view.xml",

        # ======================
        # REPORTS
        # ======================
        "reports/expense_report.xml",
        "reports/expense_report_template.xml",
        "report/loan_amortization_report.xml",
    ],

    "installable": True,
    "application": False,
}
"""USAC E-Rate invoices and authorized disbursements (FCC Forms 472/474, USAC Socrata): invoice line processed within 30 days.

Label y = 1 if inv_line_completion_date - inv_received_date <= 30 days (calendar month, fixed before any build).
The dataset lists only lines authorized for disbursement (not pending or cancelled), so lines that never
complete are absent; the DEV window ends 16 months before the fetch to limit right-truncation. Known at
receipt: invoice type, submission method, service provider id, applicant type and state, service type and
category, funding year, billing frequency, requested amounts, discount rate. Excluded: line status, decision
codes/descriptions, approved amount, completion date (only in the label).
Window (protocol): 24 months [2023-07-01, 2025-07-01) (count 572k <= 800k).
"""

from sources._socrata_common import make_module

CFG = {
    "name": "usac_erate_invoices",
    "domain": "datahub.usac.org",
    "rid": "jpiu-tj8h",
    "open_col": "inv_received_date",
    "close_col": "inv_line_completion_date",
    "thresh_days": 30,
    "window": ("2023-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "Universal Service Administrative Company (E-Rate, FCC)",
    "license": "USAC open data (public data portal, datahub.usac.org)",
    "page": "https://datahub.usac.org/d/jpiu-tj8h",
    "task": "binary: E-Rate invoice line processed within 30 days of receipt",
    "label_text": "inv_line_completion_date - inv_received_date <= 30 days (lines are only listed once authorized)",
    "features_note": "invoice type, submission method, SPIN, applicant type/state, service type/category, funding year, bill frequency, requested amounts, discount rate",
    "cat": {
        "invoice_type": "invoice_type",
        "submission": "submission_method",
        "spin": "inv_service_provider_id_number_spin",
        "applicant_type": "applicant_type",
        "state": "billed_entity_state",
        "service_type": "service_type",
        "category": "chosen_category_of_service",
        "funding_year": "funding_year",
        "bill_frequency": "bill_frequency",
    },
    "extra_num": {
        "requested_total": "inv_total_requested_amt",
        "requested_line": "requested_inv_line_amt",
        "discount_rate": "discount_rate",
    },
}
globals().update(make_module(CFG))

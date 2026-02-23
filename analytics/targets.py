"""
analytics/targets.py – Price target calculator for +N% net of brokerage fees
"""


def compute_target(
    entry_price: float,
    investment_amt: float = 100.0,
    gross_target_pct: float = 0.045,
    flat_fee: float = 1.99,
    pct_fee: float = 0.005,
    fee_mode: str = "flat",
) -> float:
    """
    Computes the target selling price to achieve `gross_target_pct` return
    after deducting brokerage fees on both buy and sell legs.

    Args:
        entry_price:      current buy price per share
        investment_amt:   total capital to invest (€)
        gross_target_pct: target gross return (e.g. 0.045 for 4.5%)
        flat_fee:         flat fee per trade (€), e.g. 1.99
        pct_fee:          percentage fee per trade (e.g. 0.005 = 0.5%)
        fee_mode:         'flat' or 'pct'

    Returns:
        target sell price per share (float)
    """
    if fee_mode == "flat":
        fee_buy  = flat_fee
        fee_sell = flat_fee
    else:
        fee_buy  = investment_amt * pct_fee
        fee_sell = investment_amt * (1 + gross_target_pct) * pct_fee

    # Number of shares bought
    qty = (investment_amt - fee_buy) / entry_price

    # Total money received at target
    total_out = investment_amt * (1 + gross_target_pct) + fee_sell

    # Target price per share
    target_price = total_out / qty if qty > 0 else entry_price * (1 + gross_target_pct)

    return round(target_price, 4)


def compute_net_gain(
    entry_price: float,
    exit_price: float,
    qty: float,
    flat_fee: float = 1.99,
    fee_mode: str = "flat",
    pct_fee: float = 0.005,
) -> float:
    """Returns net P&L after fees."""
    gross = (exit_price - entry_price) * qty
    if fee_mode == "flat":
        fees  = 2 * flat_fee
    else:
        fees  = (entry_price * qty * pct_fee) + (exit_price * qty * pct_fee)
    return round(gross - fees, 2)


def compute_breakeven(investment_amt: float, flat_fee: float = 1.99,
                      fee_mode: str = "flat", pct_fee: float = 0.005) -> float:
    """Returns minimum required gross return % to breakeven after fees."""
    if fee_mode == "flat":
        total_fees = 2 * flat_fee
    else:
        total_fees = investment_amt * pct_fee * 2
    return round((total_fees / investment_amt) * 100, 2)


if __name__ == "__main__":
    price  = 100.0
    target = compute_target(price, 100, 0.045, 1.99)
    be     = compute_breakeven(100, 1.99)
    print(f"Prix actuel  : {price:.2f} €")
    print(f"Prix cible   : {target:.4f} €  (objectif 4.5% brut sur 100€)")
    print(f"Seuil rentab.: +{be:.2f}% (frais compris)")

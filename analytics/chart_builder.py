"""
analytics/chart_builder.py – Plotly candlestick chart with Entry / TP / SL overlays
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── Palette ───────────────────────────────────────────────────────────────────
COLORS = {
    "up":      "#26a69a",   # candle haussière (vert teal)
    "down":    "#ef5350",   # candle baissière (rouge)
    "entry":   "#4ade80",   # ligne verte entrée
    "tp":      "#fbbf24",   # ligne or pointillée TP
    "sl":      "#f87171",   # ligne rouge SL
    "volume":  "#334155",   # barres volume
    "cac":     "#94a3b8",   # benchmark CAC 40
    "portf":   "#a855f7",   # portefeuille
    "bg":      "rgba(0,0,0,0)",
    "grid":    "rgba(255,255,255,0.06)",
    "text":    "#cbd5e1",
}


def build_candlestick(
    df: pd.DataFrame,
    ticker: str,
    entry: float,
    tp: float,
    sl: float,
    weekly: bool = False,
    show_volume: bool = True,
) -> go.Figure:
    """
    Builds a Plotly candlestick chart with Entry / TP / Stop-Loss overlays.

    Args:
        df:       OHLCV DataFrame (index = DatetimeIndex)
        ticker:   Stock label
        entry:    Entry price (green line)
        tp:       Take-Profit price (golden dashed)
        sl:       Stop-Loss price (red line)
        weekly:   If True, resample to weekly candles
        show_volume: show volume sub-chart

    Returns:
        Plotly Figure
    """
    if df is None or df.empty:
        return go.Figure()

    ohlcv = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    if weekly:
        ohlcv = ohlcv.resample("W").agg({
            "Open":  "first",
            "High":  "max",
            "Low":   "min",
            "Close": "last",
            "Volume":"sum",
        }).dropna()

    rows = 2 if show_volume else 1
    row_heights = [0.75, 0.25] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    # ── Candlesticks ──────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=ohlcv.index,
        open=ohlcv["Open"], high=ohlcv["High"],
        low=ohlcv["Low"],   close=ohlcv["Close"],
        increasing_line_color=COLORS["up"],
        decreasing_line_color=COLORS["down"],
        increasing_fillcolor=COLORS["up"],
        decreasing_fillcolor=COLORS["down"],
        name=ticker,
        showlegend=True,
    ), row=1, col=1)

    # ── Entry line ────────────────────────────────────────────────────────────
    fig.add_hline(
        y=entry, line_color=COLORS["entry"],
        line_width=1.8, line_dash="solid",
        annotation_text=f" Entrée {entry:.2f} €",
        annotation_font_color=COLORS["entry"],
        annotation_position="right",
        row=1, col=1,
    )

    # ── Take-Profit line ──────────────────────────────────────────────────────
    fig.add_hline(
        y=tp, line_color=COLORS["tp"],
        line_width=1.8, line_dash="dot",
        annotation_text=f" TP {tp:.2f} €  (+{(tp/entry-1)*100:.1f}%)",
        annotation_font_color=COLORS["tp"],
        annotation_position="right",
        row=1, col=1,
    )

    # ── Stop-Loss line ────────────────────────────────────────────────────────
    fig.add_hline(
        y=sl, line_color=COLORS["sl"],
        line_width=1.8, line_dash="solid",
        annotation_text=f" SL {sl:.2f} €  ({(sl/entry-1)*100:.1f}%)",
        annotation_font_color=COLORS["sl"],
        annotation_position="right",
        row=1, col=1,
    )

    # ── Volume bars ───────────────────────────────────────────────────────────
    if show_volume:
        colors_vol = [
            COLORS["up"] if c >= o else COLORS["down"]
            for c, o in zip(ohlcv["Close"], ohlcv["Open"])
        ]
        fig.add_trace(go.Bar(
            x=ohlcv.index,
            y=ohlcv["Volume"],
            marker_color=colors_vol,
            opacity=0.6,
            name="Volume",
            showlegend=False,
        ), row=2, col=1)

    # ── Layout ────────────────────────────────────────────────────────────────
    pct = (tp / entry - 1) * 100
    sl_pct = (sl / entry - 1) * 100
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        margin=dict(l=10, r=120, t=50, b=10),
        height=480,
        title=dict(
            text=f"<b>{ticker}</b>   TP <span style='color:{COLORS['tp']}'>+{pct:.1f}%</span>  ·  SL <span style='color:{COLORS['sl']}'>{sl_pct:.1f}%</span>",
            font=dict(size=15, color=COLORS["text"]),
        ),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.04, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor=COLORS["grid"], showgrid=True),
        yaxis=dict(gridcolor=COLORS["grid"], showgrid=True, ticksuffix=" €"),
        xaxis2=dict(gridcolor=COLORS["grid"], showgrid=True) if show_volume else {},
        yaxis2=dict(gridcolor=COLORS["grid"], showgrid=True) if show_volume else {},
    )

    # EMA 20 overlay
    try:
        ema20 = ohlcv["Close"].ewm(span=20).mean()
        fig.add_trace(go.Scatter(
            x=ema20.index, y=ema20,
            mode="lines", line=dict(color="#60a5fa", width=1.2, dash="dot"),
            name="EMA 20", opacity=0.8,
        ), row=1, col=1)
    except Exception:
        pass

    return fig


def build_portfolio_vs_cac(
    portfolio_series: pd.Series,
    cac_series: pd.Series,
    label_portfolio: str = "Mon Portefeuille",
) -> go.Figure:
    """
    Compares portfolio performance to CAC 40, both normalized to 100.
    """
    fig = go.Figure()

    def normalize(s: pd.Series) -> pd.Series:
        s = s.dropna()
        return (s / s.iloc[0]) * 100 if not s.empty else s

    pf_norm  = normalize(portfolio_series)
    cac_norm = normalize(cac_series)

    fig.add_trace(go.Scatter(
        x=pf_norm.index, y=pf_norm,
        mode="lines", name=label_portfolio,
        line=dict(color=COLORS["portf"], width=2.5),
        fill="tozeroy", fillcolor="rgba(168,85,247,0.08)",
    ))

    fig.add_trace(go.Scatter(
        x=cac_norm.index, y=cac_norm,
        mode="lines", name="CAC 40",
        line=dict(color=COLORS["cac"], width=1.8, dash="dot"),
    ))

    fig.add_hline(y=100, line_color="rgba(255,255,255,0.2)", line_dash="dash")

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        height=300,
        margin=dict(l=10, r=20, t=40, b=10),
        title="Performance relative – Portefeuille vs CAC 40 (base 100)",
        xaxis=dict(gridcolor=COLORS["grid"]),
        yaxis=dict(gridcolor=COLORS["grid"], ticksuffix=" pts"),
        legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)"),
    )
    return fig

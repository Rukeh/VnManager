import customtkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import Counter

from app.ui.shared.theme import *


def _all_vns(data: dict) -> list:
    """Returns a deduplicated list of all VNs across all categories."""
    seen = set()
    result = []
    for vns in data.get("vns", {}).values():
        for vn in vns:
            if vn["id"] not in seen:
                seen.add(vn["id"])
                result.append(vn)
    return result


def _style_ax(ax, fig) -> None:
    """Applies the pink theme to a matplotlib axes and figure."""
    fig.patch.set_facecolor(CARD_BG)
    ax.set_facecolor(CARD_BG)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT_MUTED)
    ax.yaxis.label.set_color(TEXT_MUTED)
    ax.title.set_color(PINK_DARK)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)


def _chart_card(parent) -> customtkinter.CTkFrame:
    """Returns a styled card frame for embedding a chart into."""
    frame = customtkinter.CTkFrame(
        parent, fg_color=CARD_BG,
        border_width=1, border_color=BORDER, corner_radius=14,
    )
    frame.pack(side="left", fill="both", expand=True, padx=6, pady=6)
    return frame


def _embed(frame, fig) -> None:
    """Embeds a matplotlib Figure into a CTk frame via TkAgg."""
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=2, pady=2)


def build_stats_dashboard(parent, data: dict) -> None:
    """
    Clears parent and builds the full statistics dashboard into it.
    Args:
        parent: A CTkScrollableFrame to render into.
        data:   The full application state dict.
    """
    for w in parent.winfo_children():
        w.destroy()

    all_vns = _all_vns(data)
    categories = data.get("categories", [])
    vns_by_cat = data.get("vns", {})

    # ── Summary stat cards ────────────────────────────────────────────────────
    summary = customtkinter.CTkFrame(parent, fg_color="transparent")
    summary.pack(fill="x", padx=10, pady=(16, 4))

    total_vns = len(all_vns)
    total_cats = len(categories)
    rated = [v for v in all_vns if v.get("rating")]
    avg_rating = (sum(v["rating"] for v in rated) / len(rated) / 10) if rated else None
    total_min = sum(v.get("length_minutes") or 0 for v in all_vns)

    for value, label in [
        (str(total_vns), "Total VNs"),
        (str(total_cats), "Categories"),
        (f"★  {avg_rating:.2f}" if avg_rating else "N/A", "Avg Rating"),
        (f"~{total_min // 60}h" if total_min else "N/A", "Est. Reading"),
    ]:
        card = customtkinter.CTkFrame(
            summary, fg_color=CARD_BG,
            border_width=1, border_color=BORDER, corner_radius=16,
        )
        card.pack(side="left", fill="both", expand=True, padx=6)
        customtkinter.CTkLabel(
            card, text=value,
            font=("Nunito", 22, "bold"), text_color=PINK_DARK,
        ).pack(pady=(16, 2))
        customtkinter.CTkLabel(
            card, text=label,
            font=FONT_SMALL, text_color=TEXT_MUTED,
        ).pack(pady=(0, 16))

    if not all_vns:
        customtkinter.CTkLabel(
            parent,
            text="Add some VNs to your library to see statistics ♡",
            font=FONT_BODY, text_color=TEXT_MUTED,
        ).pack(pady=60)
        return

    # ── Row 1: VNs per category  |  Rating distribution ──────────────────────
    row1 = customtkinter.CTkFrame(parent, fg_color="transparent")
    row1.pack(fill="x", padx=4)

    cat_data = [(c, len(vns_by_cat.get(c, []))) for c in categories if vns_by_cat.get(c)]
    if cat_data:
        cat_sorted = sorted(cat_data, key=lambda x: x[1])
        cnames, cvals = zip(*cat_sorted)
        fig1 = Figure(figsize=(5, max(2.5, len(cnames) * 0.5 + 1.2)), dpi=88)
        ax1 = fig1.add_subplot(111)
        _style_ax(ax1, fig1)
        bars = ax1.barh(list(cnames), list(cvals), color=PINK, height=0.55, edgecolor=BG)
        ax1.set_title("VNs per Category", fontsize=11, fontweight="bold", pad=8)
        ax1.bar_label(bars, padding=4, color=TEXT, fontsize=8)
        ax1.grid(axis="x", color=BORDER, linewidth=0.7, linestyle="--")
        ax1.set_axisbelow(True)
        fig1.tight_layout(pad=1.5)
        _embed(_chart_card(row1), fig1)

    ratings = [v["rating"] / 10 for v in all_vns if v.get("rating")]
    if ratings:
        fig2 = Figure(figsize=(5, 3), dpi=88)
        ax2 = fig2.add_subplot(111)
        _style_ax(ax2, fig2)
        ax2.hist(ratings, bins=10, range=(1, 10), color=PINK, edgecolor=BG, rwidth=0.85)
        ax2.set_title("VNDB Rating Distribution", fontsize=11, fontweight="bold", pad=8)
        ax2.set_xlabel("Rating (/10)")
        ax2.set_ylabel("# VNs")
        ax2.grid(axis="y", color=BORDER, linewidth=0.7, linestyle="--")
        ax2.set_axisbelow(True)
        fig2.tight_layout(pad=1.5)
        _embed(_chart_card(row1), fig2)

    # ── Row 2: Top tags  |  Length distribution ───────────────────────────────
    row2 = customtkinter.CTkFrame(parent, fg_color="transparent")
    row2.pack(fill="x", padx=4)

    tag_counter = Counter()
    for vn in all_vns:
        for tag in (vn.get("tags") or []):
            if not tag.get("lie") and tag.get("spoiler", 0) == 0:
                tag_counter[tag["name"]] += 1

    if tag_counter:
        top = tag_counter.most_common(15)
        tnames, tvals = zip(*reversed(top))
        n = len(tnames)
        grad = [PINK_LIGHT, PINK_LIGHT, PINK_LIGHT, "#f9a8d4", "#f9a8d4",
                "#f9a8d4", PINK, PINK, PINK, PINK, PINK,
                "#ec4899", "#ec4899", PINK_DARK, PINK_DARK]
        bar_colors = list(reversed(grad[:n]))
        fig3 = Figure(figsize=(5, 5), dpi=88)
        ax3 = fig3.add_subplot(111)
        _style_ax(ax3, fig3)
        bars3 = ax3.barh(list(tnames), list(tvals), color=bar_colors, height=0.65, edgecolor=BG)
        ax3.set_title("Top Tags in Library", fontsize=11, fontweight="bold", pad=8)
        ax3.bar_label(bars3, padding=4, color=TEXT, fontsize=8)
        ax3.grid(axis="x", color=BORDER, linewidth=0.7, linestyle="--")
        ax3.set_axisbelow(True)
        ax3.tick_params(axis="y", labelsize=8)
        fig3.tight_layout(pad=1.5)
        _embed(_chart_card(row2), fig3)

    length_labels = {
        1: "Very short\n(<2h)", 2: "Short\n(2–10h)",
        3: "Medium\n(10–30h)", 4: "Long\n(30–50h)", 5: "Very long\n(>50h)",
    }
    pink_shades = {1: PINK_LIGHT, 2: "#f9a8d4", 3: PINK, 4: "#ec4899", 5: PINK_DARK}
    len_counter = Counter(vn.get("length") for vn in all_vns if vn.get("length"))
    if len_counter:
        keys = sorted(len_counter)
        fig4 = Figure(figsize=(5, 4), dpi=88)
        ax4 = fig4.add_subplot(111)
        _style_ax(ax4, fig4)
        lvals = [len_counter[k] for k in keys]
        ax4.bar(
            [length_labels[k] for k in keys], lvals,
            color=[pink_shades[k] for k in keys],
            width=0.55, edgecolor=BG,
        )
        ax4.set_title("Length Distribution", fontsize=11, fontweight="bold", pad=8)
        ax4.set_ylabel("# VNs")
        ax4.grid(axis="y", color=BORDER, linewidth=0.7, linestyle="--")
        ax4.set_axisbelow(True)
        for i, v in enumerate(lvals):
            ax4.text(i, v + 0.05, str(v), ha="center", va="bottom", fontsize=9, color=TEXT)
        fig4.tight_layout(pad=1.5)
        _embed(_chart_card(row2), fig4)

    # ── Row 3: Languages (full width) ─────────────────────────────────────────
    lang_counter = Counter()
    for vn in all_vns:
        for lang in (vn.get("languages") or []):
            lang_counter[lang] += 1

    if lang_counter:
        top_langs = lang_counter.most_common(12)
        lnames2, lvals2 = zip(*top_langs)
        fig5 = Figure(figsize=(10, 2.8), dpi=88)
        ax5 = fig5.add_subplot(111)
        _style_ax(ax5, fig5)
        ax5.bar(lnames2, lvals2, color=PINK, width=0.55, edgecolor=BG)
        ax5.set_title("Languages Available", fontsize=11, fontweight="bold", pad=8)
        ax5.set_ylabel("# VNs")
        ax5.grid(axis="y", color=BORDER, linewidth=0.7, linestyle="--")
        ax5.set_axisbelow(True)
        for i, v in enumerate(lvals2):
            ax5.text(i, v + 0.05, str(v), ha="center", va="bottom", fontsize=9, color=TEXT)
        fig5.tight_layout(pad=1.5)
        row3 = customtkinter.CTkFrame(parent, fg_color="transparent")
        row3.pack(fill="x", padx=4, pady=(0, 8))
        _embed(_chart_card(row3), fig5)

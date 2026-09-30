from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

LOG_PATH = Path("data/logs.jsonl")
OUTPUT_PATH = Path("submission/evidence/11-dashboard-overview.png")


def load_logs() -> list[dict]:
    if not LOG_PATH.exists():
        print(f"File {LOG_PATH} không tồn tại!")
        return []
    records = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    return records


def main():
    records = load_logs()
    if not records:
        print("Chưa có dữ liệu log trong data/logs.jsonl. Hãy chạy load_test.py trước!")
        return

    df = pd.DataFrame(records)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts")

    # Tạo lưới 6 panel (3 hàng, 2 cột)
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle("Day 13 LLMOps Observability Dashboard (Time Window: Last 60 Minutes)", fontsize=16, fontweight="bold")

    sent = df[df["event"] == "response_sent"].copy()
    received = df[df["event"] == "request_received"].copy()
    failed = df[df["event"] == "request_failed"].copy()

    # Nhóm theo phút (1Min)
    sent_min = sent.set_index("ts").resample("1min")
    recv_min = received.set_index("ts").resample("1min")
    failed_min = failed.set_index("ts").resample("1min")

    time_idx = recv_min.size().index

    # ─────────────────────────────────────────────────────────────
    # Panel 1: Latency & TTFT
    # ─────────────────────────────────────────────────────────────
    ax1 = axes[0, 0]
    if not sent.empty:
        p50 = sent_min["latency_ms"].quantile(0.50)
        p95 = sent_min["latency_ms"].quantile(0.95)
        p99 = sent_min["latency_ms"].quantile(0.99)
        ttft_p95 = sent_min["ttft_ms"].quantile(0.95)

        ax1.plot(time_idx, p50, label="Latency P50", marker="o", markersize=3)
        ax1.plot(time_idx, p95, label="Latency P95", marker="s", markersize=3)
        ax1.plot(time_idx, p99, label="Latency P99", linestyle="--")
        ax1.plot(time_idx, ttft_p95, label="TTFT P95", linestyle=":")
    ax1.axhline(3000, color="red", linestyle="--", linewidth=1.5, label="SLO Threshold (3000ms)")
    ax1.set_title("1. Latency & TTFT (ms)")
    ax1.set_ylabel("Duration (ms)")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # ─────────────────────────────────────────────────────────────
    # Panel 2: Traffic
    # ─────────────────────────────────────────────────────────────
    ax2 = axes[0, 1]
    traffic = recv_min.size()
    ax2.plot(time_idx, traffic, color="tab:blue", marker="o", label="Requests Count")
    ax2.set_title("2. Traffic (Requests / min)")
    ax2.set_ylabel("Request count")
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(True, linestyle=":", alpha=0.6)

    # ─────────────────────────────────────────────────────────────
    # Panel 3: Error Rate & Retrieval Success Rate
    # ─────────────────────────────────────────────────────────────
    ax3 = axes[1, 0]
    recv_count = recv_min.size()
    fail_count = failed_min.size().reindex(time_idx, fill_value=0)
    error_rate = (fail_count / recv_count.replace(0, 1)) * 100

    # Tỷ lệ tool_success == True
    tool_events = df[df["tool_success"].notnull()].set_index("ts").resample("1min")
    tool_success = tool_events["tool_success"].apply(lambda s: (s == True).sum() / len(s) * 100 if len(s) > 0 else 100)
    tool_success = tool_success.reindex(time_idx, fill_value=100)

    ax3.plot(time_idx, error_rate, color="tab:red", label="Error Rate (%)", marker="x")
    ax3.plot(time_idx, tool_success, color="tab:green", label="Retrieval Success (%)", linestyle="-.")
    ax3.axhline(2.0, color="red", linestyle="--", linewidth=1.2, label="Max Error Guardrail (2%)")
    ax3.axhline(90.0, color="green", linestyle=":", linewidth=1.2, label="Min Retrieval Guardrail (90%)")
    ax3.set_title("3. Errors & Retrieval Success (%)")
    ax3.set_ylabel("Percentage (%)")
    ax3.set_ylim(-5, 105)
    ax3.legend(loc="center left", fontsize=8)
    ax3.grid(True, linestyle=":", alpha=0.6)

    # ─────────────────────────────────────────────────────────────
    # Panel 4: Cost
    # ─────────────────────────────────────────────────────────────
    ax4 = axes[1, 1]
    if not sent.empty:
        cost_min = sent_min["cost_usd"].sum().reindex(time_idx, fill_value=0)
        cum_cost = cost_min.cumsum()
        ax4.plot(time_idx, cost_min, color="tab:purple", label="Cost / min ($)", marker=".")
        ax4.plot(time_idx, cum_cost, color="tab:orange", linestyle="--", label="Cumulative Cost ($)")
    ax4.axhline(2.5, color="red", linestyle="--", linewidth=1.2, label="Daily Budget ($2.5)")
    ax4.set_title("4. Cost Over Time (USD)")
    ax4.set_ylabel("USD ($)")
    ax4.legend(loc="upper left", fontsize=8)
    ax4.grid(True, linestyle=":", alpha=0.6)

    # ─────────────────────────────────────────────────────────────
    # Panel 5: Tokens
    # ─────────────────────────────────────────────────────────────
    ax5 = axes[2, 0]
    if not sent.empty:
        tokens_in = sent_min["tokens_in"].sum().reindex(time_idx, fill_value=0)
        tokens_out = sent_min["tokens_out"].sum().reindex(time_idx, fill_value=0)
        ax5.plot(time_idx, tokens_in, label="Input Tokens", marker="o", markersize=3)
        ax5.plot(time_idx, tokens_out, label="Output Tokens", marker="s", markersize=3)
    ax5.set_title("5. Token Consumption")
    ax5.set_ylabel("Token count")
    ax5.legend(loc="upper left", fontsize=8)
    ax5.grid(True, linestyle=":", alpha=0.6)

    # ─────────────────────────────────────────────────────────────
    # Panel 6: Quality Proxy
    # ─────────────────────────────────────────────────────────────
    ax6 = axes[2, 1]
    if not sent.empty:
        quality = sent_min["quality_score"].mean().reindex(time_idx, fill_value=0.8)
        ax6.plot(time_idx, quality, color="tab:cyan", marker="o", label="Mean Quality Score")
    ax6.axhline(0.75, color="red", linestyle="--", linewidth=1.2, label="Min Quality Guardrail (0.75)")
    ax6.set_title("6. Quality Proxy Score (0.0 - 1.0)")
    ax6.set_ylabel("Score")
    ax6.set_ylim(0.0, 1.05)
    ax6.legend(loc="lower left", fontsize=8)
    ax6.grid(True, linestyle=":", alpha=0.6)

    # Định dạng trục thời gian
    for ax in axes.flat:
        ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=150)
    print(f"Đã xuất dashboard thành công ra: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
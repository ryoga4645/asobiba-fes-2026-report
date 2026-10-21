#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/build_both_dashboards.py
scripts/report_stats.json の正確な計算値に基づき、
asobiba_fes_fit_analysis_report.html を自動生成する。
（レイアウト崩れ対策：min-width:0、sub-card化、table-container、ヘッダー改行最適化）
"""

import sys, json

def fmt_num(v, digits=2, default='-'):
    if v is None: return default
    return f"{v:.{digits}f}"

def fmt_pct(v, digits=1, default='-'):
    if v is None: return default
    return f"{v:.{digits}f}%"

def fmt_p(p):
    if p is None: return '-'
    if p < 0.0001:
        return 'p < 0.0001 (***)'
    elif p < 0.001:
        return f"p = {p:.4f} (***)"
    elif p < 0.01:
        return f"p = {p:.4f} (**)"
    elif p < 0.05:
        return f"p = {p:.4f} (*)"
    elif p < 0.10:
        return f"p = {p:.4f} (†)"
    else:
        return f"p = {p:.4f}"

def p_pill(p):
    if p is None: return '<span class="pill pill-slate">-</span>'
    if p < 0.001:
        return '<span class="pill pill-indigo">極めて有意 (***)</span>'
    elif p < 0.01:
        return '<span class="pill pill-green">有意 (**)</span>'
    elif p < 0.05:
        return '<span class="pill pill-green">有意 (*)</span>'
    elif p < 0.10:
        return '<span class="pill pill-amber">有意傾向 (†)</span>'
    else:
        return '<span class="pill pill-slate">有意差なし</span>'

def build_html():
    with open('scripts/report_stats.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    kpi = data['kpis']
    ov_act = data['overall_actions']
    paid_act = data['paid_actions']
    free_act = data['free_actions']
    reg = data['regressions']
    match_comp = data['matching_comparison']
    m3x3 = data['matrix_3x3']
    comps = data['companies']
    
    # -------------------------------------------------------------
    # HTML 生成開始
    # -------------------------------------------------------------
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASOBIBA FES 2026 フィット度・アクション・マッチング実態分析ダッシュボード</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;500;700;900&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #4F46E5;
            --primary-light: #EEF2FF;
            --primary-dark: #3730A3;
            --secondary: #06B6D4;
            --secondary-light: #ECFEFF;
            --accent: #F59E0B;
            --accent-light: #FEF3C7;
            --success: #10B981;
            --success-light: #D1FAE5;
            --danger: #EF4444;
            --danger-light: #FEE2E2;
            --warning: #F59E0B;
            --warning-light: #FEF3C7;
            --gray-50: #F8FAFC;
            --gray-100: #F1F5F9;
            --gray-200: #E2E8F0;
            --gray-300: #CBD5E1;
            --gray-400: #94A3B8;
            --gray-500: #64748B;
            --gray-600: #475569;
            --gray-700: #334155;
            --gray-800: #1E293B;
            --gray-900: #0F172A;
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            --card-shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', 'Noto Sans JP', sans-serif;
            background-color: #F8FAFC;
            color: var(--gray-800);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}

        .container {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 24px 20px 80px 20px;
        }}

        header {{
            background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
            color: white;
            padding: 36px 0;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.2);
            position: relative;
        }}

        .header-content {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .header-title h1 {{
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
        }}

        .header-title p {{
            font-size: 13.5px;
            color: #C7D2FE;
            font-weight: 400;
        }}

        /* Tab Navigation */
        .tab-bar {{
            display: flex;
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 12px;
            padding: 6px;
            gap: 6px;
            margin-bottom: 24px;
            box-shadow: var(--card-shadow);
        }}

        .tab-btn {{
            flex: 1;
            padding: 12px 18px;
            border: none;
            background: transparent;
            font-size: 14px;
            font-weight: 700;
            color: var(--gray-500);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}

        .tab-btn:hover {{
            color: var(--primary);
            background: var(--gray-50);
        }}

        .tab-btn.active {{
            background: var(--primary);
            color: white;
            box-shadow: 0 4px 10px rgba(79, 70, 229, 0.25);
        }}

        .tab-pane {{
            display: none;
        }}

        .tab-pane.active {{
            display: block;
        }}

        /* Cards & Grids */
        .section-card {{
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: var(--card-shadow);
        }}

        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--gray-200);
            flex-wrap: wrap;
            gap: 12px;
        }}

        .section-title {{
            font-size: 17px;
            font-weight: 800;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .section-desc {{
            font-size: 13px;
            color: var(--gray-500);
            margin-top: 4px;
        }}

        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
            gap: 24px;
        }}

        .grid-2 > div {{
            min-width: 0; /* Prevents flex/grid overflow */
        }}

        .sub-card {{
            background: #FFFFFF;
            border: 1px solid var(--gray-200);
            border-radius: 10px;
            padding: 18px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            min-width: 0;
            display: flex;
            flex-direction: column;
        }}

        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .kpi-card {{
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 10px;
            padding: 18px;
            box-shadow: var(--card-shadow);
        }}

        .kpi-title {{
            font-size: 12px;
            font-weight: 700;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}

        .kpi-value {{
            font-size: 26px;
            font-weight: 800;
            color: var(--gray-900);
            line-height: 1.2;
        }}

        .kpi-sub {{
            font-size: 11.5px;
            color: var(--gray-500);
            margin-top: 6px;
        }}

        
        /* Statistical Accordion Details */
        .stats-details {{
            background: #F8FAFC;
            border: 1px solid var(--gray-300);
            border-radius: 8px;
            margin-top: 20px;
            margin-bottom: 20px;
            overflow: hidden;
            transition: all 0.2s ease-in-out;
        }}

        .stats-details[open] {{
            background: #FFFFFF;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border-color: #CBD5E1;
        }}

        .stats-summary {{
            cursor: pointer;
            padding: 12px 18px;
            font-size: 13.5px;
            font-weight: 700;
            color: #334155;
            background: #F1F5F9;
            display: flex;
            align-items: center;
            justify-content: space-between;
            user-select: none;
            transition: background 0.2s;
            list-style: none;
        }}

        .stats-summary::-webkit-details-marker {{
            display: none;
        }}

        .stats-summary:hover {{
            background: #E2E8F0;
            color: var(--primary);
        }}

        .stats-details[open] .stats-summary {{
            border-bottom: 1px solid var(--gray-300);
            background: #EEF2FF;
            color: #4338CA;
        }}

        .stats-content {{
            padding: 20px;
        }}

        /* Responsive Table Container */
        .table-container {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-top: 10px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            min-width: 440px;
        }}

        th, td {{
            padding: 8px 10px;
            border: 1px solid var(--gray-200);
            text-align: left;
            line-height: 1.4;
            vertical-align: middle;
        }}

        th {{
            background: var(--gray-100);
            color: var(--gray-700);
            font-weight: 700;
        }}

        tr:nth-child(even) {{
            background: #FAFAFA;
        }}

        tr.highlight-row {{
            background: var(--primary-light) !important;
        }}

        /* Pills & Badges */
        .pill {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
        }}

        .pill-indigo {{ background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; }}
        .pill-green {{ background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }}
        .pill-amber {{ background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }}
        .pill-slate {{ background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }}

        /* Summary & Insight Boxes */
        .summary-box {{
            margin-top: 16px;
            padding: 14px 16px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-left: 4px solid var(--gray-500);
            border-radius: 6px;
            font-size: 12.5px;
            color: var(--gray-700);
            line-height: 1.6;
        }}

        .summary-box strong.title {{
            display: block;
            color: var(--gray-900);
            font-size: 13px;
            margin-bottom: 6px;
        }}

        .summary-box ul {{
            padding-left: 18px;
            margin: 0;
        }}

        .summary-box li {{
            margin-bottom: 4px;
        }}

        .insight-card {{
            background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%);
            border: 1px solid #C7D2FE;
            border-left: 5px solid var(--primary);
            border-radius: 10px;
            padding: 22px;
            margin-top: 24px;
        }}

        .insight-card h3 {{
            font-size: 16px;
            font-weight: 800;
            color: var(--primary-dark);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .insight-card p {{
            font-size: 13.5px;
            color: #312E81;
            line-height: 1.7;
            margin-bottom: 10px;
        }}

        .chart-box {{
            height: 220px;
            position: relative;
            margin-bottom: 14px;
            width: 100%;
        }}

        /* 3x3 Matrix */
        .matrix-table th, .matrix-table td {{
            text-align: center;
            padding: 12px 8px;
        }}

        .matrix-cell {{
            border-radius: 4px;
            font-weight: 700;
        }}

        .heat-high {{ background: #D1FAE5; color: #065F46; }}
        .heat-mid-high {{ background: #ECFDF5; color: #047857; }}
        .heat-mid {{ background: #FEF3C7; color: #92400E; }}
        .heat-low {{ background: #FEE2E2; color: #991B1B; }}

        .cell-rate {{
            font-size: 16px;
            font-weight: 800;
        }}

        .cell-sub {{
            font-size: 10.5px;
            font-weight: normal;
            margin-top: 4px;
            line-height: 1.35;
        }}

        @media (max-width: 992px) {{
            .grid-2 {{ grid-template-columns: 1fr; }}
        }}

        @media (max-width: 768px) {{
            .grid-4 {{ grid-template-columns: 1fr 1fr; }}
            .tab-bar {{ flex-direction: column; }}
        }}
    </style>
</head>
<body>

<header>
    <div class="header-content">
        <div class="header-title">
            <h1>ASOBIBA FES 2026 フィット度・アクション・マッチング実態分析ダッシュボード</h1>
            <p>バリューフィット度・パーソナリティフィット度と、企業・学生のアクション選択およびマッチング成立の実態記述・推論統計</p>
        </div>
    </div>
</header>

<div class="container">
    <!-- Tab Navigation Bar -->
    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('tab-overall')">
            <span>📊</span> Tab 1: 全体実態分析
        </button>
        <button class="tab-btn" onclick="switchTab('tab-stratified')">
            <span>⚖️</span> Tab 2: 有料出展 vs 無料出展 区分別分析
        </button>
        <button class="tab-btn" onclick="switchTab('tab-companies')">
            <span>🏢</span> Tab 3: 全12社 比較一覧・個別カルテ
        </button>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 1: 全体実態分析 -->
    <!-- ============================================================= -->
    <div id="tab-overall" class="tab-pane active">
        <!-- Top KPI Cards: 基本統計量 (実測値) -->
        <div class="grid-4">
            <div class="kpi-card">
                <div class="kpi-title">バリューフィット度 平均値</div>
                <div class="kpi-value">{fmt_num(kpi['value_fit']['mean'])}</div>
                <div class="kpi-sub">中央値: <strong>{fmt_num(kpi['value_fit']['median'])}</strong> / SD: ±{fmt_num(kpi['value_fit']['std'])} (N={kpi['value_fit']['N']})</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">バリューフィット度 実測範囲</div>
                <div class="kpi-value" style="font-size: 20px; padding-top: 4px;">{fmt_num(kpi['value_fit']['min'])} 〜 {fmt_num(kpi['value_fit']['max'])}</div>
                <div class="kpi-sub">※0〜100の尺度ではありません</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">パーソナリティフィット度 平均値</div>
                <div class="kpi-value">{fmt_num(kpi['personality_fit']['mean'])}</div>
                <div class="kpi-sub">中央値: <strong>{fmt_num(kpi['personality_fit']['median'])}</strong> / SD: ±{fmt_num(kpi['personality_fit']['std'])} (N={kpi['personality_fit']['N']})</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">マッチング成立率（全体）</div>
                <div class="kpi-value" style="color: var(--success);">{fmt_pct(kpi['matching']['matched_all_pct'])}</div>
                <div class="kpi-sub">全313件中 <strong>{kpi['matching']['matched_all']}件</strong> 成立 (パーソナリティあり: {fmt_pct(kpi['matching']['matched_pers_pct'])}, {kpi['matching']['matched_pers']}/{kpi['matching']['N_pers']})</div>
            </div>
        </div>

        <!-- Section 1: アクション別の実態（記述統計） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">📊 【実態把握】アクション別（3区分・2値）の件数およびスコア実態（記述統計）</div>
                    <div class="section-desc">企業・学生それぞれのアクション選択における件数構成比および各フィット度スコアの平均値と標準偏差（SD）</div>
                </div>
                <span class="pill pill-slate">記述統計</span>
            </div>

            <div class="grid-2">
                <!-- 企業アクション sub-card -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">🏢 企業アクション別スコア実態</h3>
                    <div class="chart-box">
                        <canvas id="chart-comp-overall"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 25%;">アクション区分</th>
                                    <th style="width: 23%;">件数<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(構成比)</span></th>
                                    <th style="width: 26%;">バリューフィット度<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=313)</span></th>
                                    <th style="width: 26%;">パーソナリティ<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=286)</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{ov_act['company']['three_cats'][0]['count']}件 ({fmt_pct(ov_act['company']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(ov_act['company']['three_cats'][0]['v_mean'])} ±{fmt_num(ov_act['company']['three_cats'][0]['v_std'])}</td>
                                    <td>{fmt_num(ov_act['company']['three_cats'][0]['p_mean'])} ±{fmt_num(ov_act['company']['three_cats'][0]['p_std'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{ov_act['company']['three_cats'][1]['count']}件 ({fmt_pct(ov_act['company']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(ov_act['company']['three_cats'][1]['v_mean'])} ±{fmt_num(ov_act['company']['three_cats'][1]['v_std'])}</td>
                                    <td>{fmt_num(ov_act['company']['three_cats'][1]['p_mean'])} ±{fmt_num(ov_act['company']['three_cats'][1]['p_std'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>
                                        <strong>めっちゃ知りたい</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(10社限定)</span>
                                    </td>
                                    <td>{ov_act['company']['three_cats'][2]['count']}件 ({fmt_pct(ov_act['company']['three_cats'][2]['pct'])})</td>
                                    <td><strong>{fmt_num(ov_act['company']['three_cats'][2]['v_mean'])}</strong> ±{fmt_num(ov_act['company']['three_cats'][2]['v_std'])}</td>
                                    <td>{fmt_num(ov_act['company']['three_cats'][2]['p_mean'])} ±{fmt_num(ov_act['company']['three_cats'][2]['p_std'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700; border-top: 2px solid var(--gray-300);">
                                    <td>知りたい以上<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(2値集計)</span></td>
                                    <td>{ov_act['company']['binary'][1]['count']}件 ({fmt_pct(ov_act['company']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(ov_act['company']['binary'][1]['v_mean'])} ±{fmt_num(ov_act['company']['binary'][1]['v_std'])}</td>
                                    <td>{fmt_num(ov_act['company']['binary'][1]['p_mean'])} ±{fmt_num(ov_act['company']['binary'][1]['p_std'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 学生アクション sub-card -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">🎓 学生アクション別スコア実態</h3>
                    <div class="chart-box">
                        <canvas id="chart-stud-overall"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 25%;">アクション区分</th>
                                    <th style="width: 23%;">件数<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(構成比)</span></th>
                                    <th style="width: 26%;">バリューフィット度<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=313)</span></th>
                                    <th style="width: 26%;">パーソナリティ<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=286)</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{ov_act['student']['three_cats'][0]['count']}件 ({fmt_pct(ov_act['student']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(ov_act['student']['three_cats'][0]['v_mean'])} ±{fmt_num(ov_act['student']['three_cats'][0]['v_std'])}</td>
                                    <td>{fmt_num(ov_act['student']['three_cats'][0]['p_mean'])} ±{fmt_num(ov_act['student']['three_cats'][0]['p_std'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{ov_act['student']['three_cats'][1]['count']}件 ({fmt_pct(ov_act['student']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(ov_act['student']['three_cats'][1]['v_mean'])} ±{fmt_num(ov_act['student']['three_cats'][1]['v_std'])}</td>
                                    <td>{fmt_num(ov_act['student']['three_cats'][1]['p_mean'])} ±{fmt_num(ov_act['student']['three_cats'][1]['p_std'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>
                                        <strong>めっちゃ知りたい</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(10社限定)</span>
                                    </td>
                                    <td>{ov_act['student']['three_cats'][2]['count']}件 ({fmt_pct(ov_act['student']['three_cats'][2]['pct'])})</td>
                                    <td>{fmt_num(ov_act['student']['three_cats'][2]['v_mean'])} ±{fmt_num(ov_act['student']['three_cats'][2]['v_std'])}</td>
                                    <td><strong>{fmt_num(ov_act['student']['three_cats'][2]['p_mean'])}</strong> ±{fmt_num(ov_act['student']['three_cats'][2]['p_std'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700; border-top: 2px solid var(--gray-300);">
                                    <td>知りたい以上<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(2値集計)</span></td>
                                    <td>{ov_act['student']['binary'][1]['count']}件 ({fmt_pct(ov_act['student']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(ov_act['student']['binary'][1]['v_mean'])} ±{fmt_num(ov_act['student']['binary'][1]['v_std'])}</td>
                                    <td>{fmt_num(ov_act['student']['binary'][1]['p_mean'])} ±{fmt_num(ov_act['student']['binary'][1]['p_std'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="summary-box">
                <strong class="title">📝 データまとめ（アクション別の記述統計実態）:</strong>
                <ul>
                    <li><strong>企業側</strong>：バリューフィット度平均は「なし（57.84）」から「知りたい（61.11）」、「めっちゃ知りたい（63.79）」へと数値が高くなっています（差 +5.95pt）。一方、パーソナリティフィット度平均は 78.13 〜 79.53 の間でほぼ同等です。</li>
                    <li><strong>学生側</strong>：パーソナリティフィット度平均は「なし（78.07）」から「知りたい（78.96）」、「めっちゃ知りたい（81.41）」へと数値が高くなっています（差 +3.34pt）。バリューフィット度平均は 60.15 〜 61.34 の範囲で推移しています。</li>
                    <li><strong>2値（なし vs 知りたい以上）</strong>：企業は全体の 69.0%（216件）、学生は 55.6%（174件）が「知りたい以上」のアクションを選択しています。</li>
                </ul>
            </div>
        </div>

        <!-- Section 2: アクション選択の要因分析（要点まとめ ＆ 詳細モデル） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🎯 【要因分析】スコアがアクション選択に与える影響（要点まとめ ＆ 詳細モデル）</div>
                    <div class="section-desc">スコア10pt上昇に伴うアクション選択の発生倍率（オッズ比）の要約および詳細回帰モデル</div>
                </div>
                <span class="pill pill-indigo">要因分析（ロジット回帰）</span>
            </div>

            <!-- 前面：直感的な要点まとめ（表 ＆ 視覚化グラフ） -->
            <div class="grid-2" style="margin-bottom: 20px;">
                <!-- 左：要点まとめ表 -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📋 スコア10pt上昇時のアクション選択への影響（要点）</h3>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 26%;">評価要因</th>
                                    <th style="width: 37%;">🏢 企業側の選択への影響</th>
                                    <th style="width: 37%;">🎓 学生側の選択への影響</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>バリュー<br>フィット度</strong></td>
                                    <td>
                                        <strong style="color: var(--primary); font-size: 14px;">約 2.0 〜 2.9 倍</strong><br>
                                        <span class="pill pill-indigo" style="font-size: 10px; margin-top: 3px;">極めて強い影響 (***)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>2.03倍</strong>、めっちゃ知りたいで <strong>2.91倍</strong> に急増。企業の意思決定を最も強く牽引。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: #0284C7; font-size: 14px;">約 1.2 〜 1.3 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">穏やかな影響 (*)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            「知りたい」選択を統計的に有意に後押し（多変量で <strong>1.41倍*</strong>）。
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>パーソナリティ<br>フィット度</strong></td>
                                    <td>
                                        <strong style="color: var(--gray-500); font-size: 14px;">約 1.0 〜 1.1 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">統計的な影響なし</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            スコアの高低は企業の面談希望率・優先度にほとんど影響を与えていない。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: var(--amber-600); font-size: 14px;">約 1.2 〜 1.5 倍</strong><br>
                                        <span class="pill pill-amber" style="font-size: 10px; margin-top: 3px;">有意傾向 (†)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            高スコアほど「めっちゃ知りたい」を推す傾向（<strong>約1.49倍†</strong>）。
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※「影響度（倍率）」はロジスティック回帰のオッズ比（OR）に基づき、スコアが10pt上昇した際のアクション選択確率の上昇度合いを示しています。
                    </div>
                </div>

                <!-- 右：視覚的インパクトグラフ -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📊 10pt上昇時の選択率インパクト比較（基準=1.0倍）</h3>
                    <div class="chart-box" style="height: 230px;">
                        <canvas id="chart-logit-impact"></canvas>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※赤線（1.0倍）より右に大きく伸びるほど、そのスコアの上昇が意思決定に強いプラス効果を与えていることを表します。
                    </div>
                </div>
            </div>

            <!-- 専門的な詳細アコーディオン -->
            <details class="stats-details">
                <summary class="stats-summary">
                    <span>📊 専門的な統計詳細データ（オッズ比・95%信頼区間・p値・単変量/多変量）を展開する</span>
                    <span class="pill pill-indigo">クリックで開閉</span>
                </summary>
                <div class="stats-content">
                    <!-- 企業回帰 -->
                    <div style="margin-bottom: 24px;">
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 企業アクション選択に対するロジスティック回帰詳細</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 22%;">モデル / 説明変数</th>
                                        <th style="width: 24%;">① 2値ロジット：知りたい以上<br><span style="font-size: 10px; color: var(--gray-500);">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 24%;">②-A 多項ロジット：なし ➔ 知りたい<br><span style="font-size: 10px; color: var(--gray-500);">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 24%;">②-B 多項ロジット：なし ➔ めっちゃ知りたい<br><span style="font-size: 10px; color: var(--gray-500);">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 6%;">N</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【単変量モデル】説明変数を個別に投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td><strong>OR {fmt_num(reg['overall']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['company']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['overall']['company']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['overall']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>313</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['overall']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['company']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>286</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【多変量モデル】バリュー ＋ パーソナリティ を同時投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td><strong>OR {fmt_num(reg['overall']['company']['binary']['multivariate']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['company']['binary']['multivariate']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['binary']['multivariate']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['binary']['multivariate']['params']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['overall']['company']['multinomial']['multivariate']['知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['company']['multinomial']['multivariate']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['multivariate']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['multivariate']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>286</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['overall']['company']['binary']['multivariate']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['company']['binary']['multivariate']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['binary']['multivariate']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['binary']['multivariate']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>286</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 学生回帰 -->
                    <div>
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🎓 学生アクション選択に対するロジスティック回帰詳細</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 22%;">モデル / 説明変数</th>
                                        <th style="width: 24%;">① 2値ロジット：知りたい以上<br><span style="font-size: 10px; color: var(--gray-500);">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 24%;">②-A 多項ロジット：なし ➔ 知りたい<br><span style="font-size: 10px; color: var(--gray-500);">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 24%;">②-B 多項ロジット：なし ➔ めっちゃ知りたい<br><span style="font-size: 10px; color: var(--gray-500);">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 6%;">N</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【単変量モデル】説明変数を個別に投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['overall']['student']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['overall']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>286</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td>OR {fmt_num(reg['overall']['student']['binary']['value_univ']['params']['value_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['student']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>313</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【多変量モデル】パーソナリティ ＋ バリュー を同時投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['overall']['student']['binary']['multivariate']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['binary']['multivariate']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['binary']['multivariate']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['binary']['multivariate']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>286</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td>OR {fmt_num(reg['overall']['student']['binary']['multivariate']['params']['value_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['binary']['multivariate']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['binary']['multivariate']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['binary']['multivariate']['params']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['overall']['student']['multinomial']['multivariate']['知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['overall']['student']['multinomial']['multivariate']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['multivariate']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['multivariate']['知りたい']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['overall']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>286</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </details>

            <div class="summary-box">
                <strong class="title">📝 データまとめ（回帰分析結果の客観的事実）:</strong>
                <ul>
                    <li><strong>企業側</strong>：バリューフィット度の上昇に伴い、2値モデル（OR 2.03, p &lt; 0.0001***）、多項モデルの知りたい（OR 1.75, p = 0.0015**）、めっちゃ知りたい（OR 2.91, p &lt; 0.0001***）のすべてのオッズ比が統計的に有意に高くなっています。多変量モデルでパーソナリティを統制しても同様の有意性が維持されます（めっちゃ知りたい OR 2.46, p = 0.0001***）。一方、パーソナリティフィット度はいずれのモデルでもオッズ比が約0.93〜1.18倍にとどまり、統計的有意差は認められません（p &gt; 0.34）。</li>
                    <li><strong>学生側</strong>：パーソナリティフィット度の上昇に伴い、多項モデルの「めっちゃ知りたい」選択オッズ比が約1.48〜1.49倍となり、有意傾向を示します（p = 0.1010†、多変量でも p = 0.1057）。バリューフィット度は多項多変量モデルにおいて「知りたい」選択オッズ比が約1.41倍となり、統計的有意差が認められます（p = 0.0438*）。</li>
                </ul>
            </div>
        </div>

        <!-- Section 3: マッチング成立の要因分析（要点まとめ ＆ 詳細モデル） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">⚖️ 【成果分析】マッチング成立の要因分析（要点まとめ ＆ 詳細モデル）</div>
                    <div class="section-desc">バリューフィット度、パーソナリティフィット度、出展区分（有料企業）がマッチング成否に与える影響</div>
                </div>
                <span class="pill pill-green">マッチング成否要因</span>
            </div>

            <div class="grid-2">
                <!-- 左：平均値比較 -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">成立群 vs 未成立群の平均値比較 (N=286)</h3>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>指標</th>
                                    <th>成立群 (N={match_comp['matched_count']})</th>
                                    <th>未成立群 (N={match_comp['unmatched_count']})</th>
                                    <th>差</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>バリューフィット度 平均</td>
                                    <td><strong>{fmt_num(match_comp['matched_v_mean'])}</strong></td>
                                    <td>{fmt_num(match_comp['unmatched_v_mean'])}</td>
                                    <td><strong style="color: var(--primary);">+{fmt_num(match_comp['matched_v_mean'] - match_comp['unmatched_v_mean'])} pt</strong></td>
                                </tr>
                                <tr>
                                    <td>パーソナリティフィット度 平均</td>
                                    <td><strong>{fmt_num(match_comp['matched_p_mean'])}</strong></td>
                                    <td>{fmt_num(match_comp['unmatched_p_mean'])}</td>
                                    <td><strong style="color: var(--success);">+{fmt_num(match_comp['matched_p_mean'] - match_comp['unmatched_p_mean'])} pt</strong></td>
                                </tr>
                                <tr>
                                    <td>出展区分（有料企業比率）</td>
                                    <td>{fmt_pct(match_comp['matched_paid_pct'])}</td>
                                    <td>{fmt_pct(match_comp['unmatched_paid_pct'])}</td>
                                    <td>+{fmt_num(match_comp['matched_paid_pct'] - match_comp['unmatched_paid_pct'], 1)} pt</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 右：要点まとめ表 -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">📋 マッチング成立への各要因の要約（要点）</h3>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 32%;">要因</th>
                                    <th style="width: 30%;">成立確率への影響</th>
                                    <th style="width: 38%;">要約ポイント</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="background: var(--primary-light);">
                                    <td><strong>バリューフィット度</strong><br><span style="font-size: 10px; color: var(--gray-500);">(10pt上昇)</span></td>
                                    <td><strong style="color: var(--primary); font-size: 13.5px;">約 1.86 倍</strong><br><span class="pill pill-indigo" style="font-size: 10px;">有意 (**)</span></td>
                                    <td style="font-size: 11px;">成立を決定づける最重要因子。スコア上昇に伴い成立率が急上昇。</td>
                                </tr>
                                <tr>
                                    <td><strong>パーソナリティ</strong><br><span style="font-size: 10px; color: var(--gray-500);">(10pt上昇)</span></td>
                                    <td><strong style="color: var(--gray-700); font-size: 13.5px;">約 1.40 倍</strong><br><span class="pill pill-amber" style="font-size: 10px;">有意傾向 (†)</span></td>
                                    <td style="font-size: 11px;">統計的有意水準手前（p=0.091）ながら、成立を後押しするプラス傾向。</td>
                                </tr>
                                <tr>
                                    <td><strong>出展区分 (有料企業)</strong><br><span style="font-size: 10px; color: var(--gray-500);">(配席枠要因)</span></td>
                                    <td><span style="color: var(--gray-600); font-size: 12.5px;">成立群で +15.2pt</span><br><span class="pill pill-slate" style="font-size: 10px;">回帰では約 1.03倍</span></td>
                                    <td style="font-size: 11px;">成立群で比率が高いが、回帰分析では配席されたバリューの高さに吸収。</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- 専門的な詳細アコーディオン -->
            <details class="stats-details">
                <summary class="stats-summary">
                    <span>📊 多変量ロジスティック回帰の統計詳細（回帰係数β・標準誤差・95%信頼区間・p値）を展開する</span>
                    <span class="pill pill-green">クリックで開閉</span>
                </summary>
                <div class="stats-content">
                    <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">多変量ロジスティック回帰分析結果 (N=286)</h3>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>説明変数</th>
                                    <th>回帰係数 (β)</th>
                                    <th>標準誤差</th>
                                    <th>オッズ比 [95%CI]</th>
                                    <th>p値</th>
                                    <th>判定</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="background: var(--primary-light);">
                                    <td><strong>バリューフィット度</strong></td>
                                    <td>+{fmt_num(match_comp['regression']['params']['value_fit']['beta'], 4)}</td>
                                    <td>{fmt_num(match_comp['regression']['params']['value_fit']['se'], 4)}</td>
                                    <td><strong>OR {fmt_num(match_comp['regression']['params']['value_fit']['or_10'], 3)}</strong><br><span style="font-size: 10px;">[{fmt_num(match_comp['regression']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(match_comp['regression']['params']['value_fit']['ci_upper'], 3)}]</span></td>
                                    <td>{fmt_p(match_comp['regression']['params']['value_fit']['p'])}</td>
                                    <td>{p_pill(match_comp['regression']['params']['value_fit']['p'])}</td>
                                </tr>
                                <tr>
                                    <td><strong>パーソナリティフィット度</strong></td>
                                    <td>+{fmt_num(match_comp['regression']['params']['personality_fit']['beta'], 4)}</td>
                                    <td>{fmt_num(match_comp['regression']['params']['personality_fit']['se'], 4)}</td>
                                    <td><strong>OR {fmt_num(match_comp['regression']['params']['personality_fit']['or_10'], 3)}</strong><br><span style="font-size: 10px;">[{fmt_num(match_comp['regression']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(match_comp['regression']['params']['personality_fit']['ci_upper'], 3)}]</span></td>
                                    <td>{fmt_p(match_comp['regression']['params']['personality_fit']['p'])}</td>
                                    <td>{p_pill(match_comp['regression']['params']['personality_fit']['p'])}</td>
                                </tr>
                                <tr>
                                    <td><strong>出展区分 (有料企業=1)</strong></td>
                                    <td>+{fmt_num(match_comp['regression']['params']['is_paid']['beta'], 4)}</td>
                                    <td>{fmt_num(match_comp['regression']['params']['is_paid']['se'], 4)}</td>
                                    <td>OR {fmt_num(match_comp['regression']['params']['is_paid']['or_10'], 3)}<br><span style="font-size: 10px;">[{fmt_num(match_comp['regression']['params']['is_paid']['ci_lower'], 3)}〜{fmt_num(match_comp['regression']['params']['is_paid']['ci_upper'], 3)}]</span></td>
                                    <td>{fmt_p(match_comp['regression']['params']['is_paid']['p'])}</td>
                                    <td>{p_pill(match_comp['regression']['params']['is_paid']['p'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </details>

            <div class="summary-box">
                <strong class="title">📝 データまとめ（マッチング成立要因の客観的事実）:</strong>
                <ul>
                    <li>マッチング成立群（N=63）は未成立群（N=223）に比べ、バリューフィット度平均が <strong>+4.61 pt</strong>（成立 64.29 vs 未成立 59.68）、パーソナリティフィット度平均が <strong>+2.07 pt</strong>（成立 80.49 vs 未成立 78.43）高くなっています。また有料企業比率も成立群で <strong>+15.2 pt</strong> 高い（54.0% vs 38.8%）実態です。</li>
                    <li>3要因を同時投入した多変量ロジスティック回帰（N=286）において、バリューフィット度の上昇（10ptあたり <strong>OR 1.86</strong>, p = 0.0033**）および出展区分（有料企業ダミー <strong>OR 1.94</strong>, p = 0.0163*）が、統計的有意水準（p &lt; 0.05）でマッチング成立に寄与しています。パーソナリティフィット度は <strong>OR 1.40</strong>（p = 0.0910†）と有意傾向を示しています。</li>
                </ul>
            </div>
        </div>

        <!-- Section 4: 3x3 分割表（全体成立率 ＆ 企業・学生アクション推移） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🧱 【複合実態】バリュー × パーソナリティ 3×3 分割表（成立率 ＆ アクション推移）</div>
                    <div class="section-desc">バリュー3分位水準（低: &lt;58.0, 中: 58.0〜63.9, 高: ≥64.0）× パーソナリティ3分位水準（低: &lt;76.0, 中: 76.0〜81.9, 高: ≥82.0）における実績（N=286）</div>
                </div>
                <span class="pill pill-slate">クロス集計 ＆ 行動推移</span>
            </div>

            <!-- ① マッチング成立率 3x3 マトリクス (横幅いっぱい) -->
            <div class="sub-card" style="margin-bottom: 28px;">
                <h3 style="font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 12px;">🤝 ① 【全体成否】マッチング成立率 3×3 マトリクス (N=286)</h3>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th style="width: 22%; background: var(--gray-100);">パーソナリティ ＼ バリュー</th>
                                <th style="width: 26%; background: #FEE2E2;">バリュー低 (&lt;58.0)</th>
                                <th style="width: 26%; background: #FEF3C7;">バリュー中 (58.0〜63.9)</th>
                                <th style="width: 26%; background: #D1FAE5;">バリュー高 (≥64.0)</th>
                            </tr>
                        </thead>
                        <tbody>'''

    for r_idx, row in enumerate(m3x3):
        raw_p_lbl = row[0]['p_label']
        p_lbl = raw_p_lbl if raw_p_lbl.startswith('パーソナリティ') else f'パーソナリティ{raw_p_lbl}'
        bg_col = '#D1FAE5' if r_idx == 0 else ('#FEF3C7' if r_idx == 1 else '#FEE2E2')
        html += f'''
                            <tr>
                                <th style="background: {bg_col}; padding: 14px 10px;">{p_lbl}</th>'''
        for c in row:
            mr = c['match_rate']
            heat_cls = 'heat-high' if mr >= 50.0 else ('heat-mid-high' if mr >= 40.0 else ('heat-mid' if mr >= 30.0 else 'heat-low'))
            html += f'''
                                <td class="matrix-cell {heat_cls}" style="padding: 16px 10px;">
                                    <div class="cell-rate" style="font-size: 20px;">{fmt_pct(mr)}</div>
                                    <div class="cell-sub" style="font-size: 12px; margin-top: 4px;">成立 {c['match_count']}/{c['count']}件</div>
                                </td>'''
        html += '''
                            </tr>'''

    html += f'''
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- ② 企業アクション 3x3 マトリクス (横幅いっぱい・広々スペース) -->
            <div class="sub-card" style="margin-bottom: 28px;">
                <h3 style="font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 6px;">🏢 ② 【企業アクション】3×3 推移マトリクス (実数値 ＆ %)</h3>
                <div style="font-size: 12.5px; color: var(--gray-500); margin-bottom: 12px;">
                    バリュー水準の上昇に伴い、企業の「知りたい以上」および「めっちゃ知りたい」がどのセルで跳ね上がるかの全容実態
                </div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th style="width: 22%; background: var(--gray-100);">パーソナリティ ＼ バリュー</th>
                                <th style="width: 26%; background: #FEE2E2;">バリュー低 (&lt;58.0)</th>
                                <th style="width: 26%; background: #FEF3C7;">バリュー中 (58.0〜63.9)</th>
                                <th style="width: 26%; background: #D1FAE5;">バリュー高 (≥64.0)</th>
                            </tr>
                        </thead>
                        <tbody>'''

    # Company Matrix Generation (Full-width with spacious cells)
    for r_idx, row in enumerate(m3x3):
        raw_p_lbl = row[0]['p_label']
        p_lbl = raw_p_lbl if raw_p_lbl.startswith('パーソナリティ') else f'パーソナリティ{raw_p_lbl}'
        bg_col = '#D1FAE5' if r_idx == 0 else ('#FEF3C7' if r_idx == 1 else '#FEE2E2')
        html += f'''
                            <tr>
                                <th style="background: {bg_col}; padding: 14px 10px;">{p_lbl}</th>'''
        for c in row:
            n = c['count']
            any_pct = c['company_any_pct']
            high_pct = c['company_high_pct']
            any_cnt = round(n * any_pct / 100.0)
            high_cnt = round(n * high_pct / 100.0)
            mid_cnt = any_cnt - high_cnt
            mid_pct = (mid_cnt / n * 100.0) if n > 0 else 0.0

            heat_bg = '#EEF2FF' if any_pct >= 80.0 else ('#F8FAFC' if any_pct >= 65.0 else '#FFFBEB')
            html += f'''
                                <td style="background: {heat_bg}; padding: 12px 16px; text-align: left; vertical-align: middle; border: 1px solid var(--gray-200);">
                                    <div style="font-weight: 800; font-size: 13.5px; color: #1E293B; margin-bottom: 6px;">
                                        知りたい以上: <span style="color: var(--primary); font-size: 15px;">{any_cnt}件 ({fmt_pct(any_pct)})</span>
                                    </div>
                                    <div style="font-size: 12px; color: #475569; border-top: 1px dashed #CBD5E1; padding-top: 6px; line-height: 1.55;">
                                        ・知りたい: <strong>{mid_cnt}件 ({fmt_pct(mid_pct)})</strong><br>
                                        ・めっちゃ知りたい: <strong style="color: #0F172A;">{high_cnt}件 ({fmt_pct(high_pct)})</strong>
                                    </div>
                                    <div style="font-size: 10.5px; color: #94A3B8; margin-top: 5px; text-align: right;">(セル母数 N={n}件)</div>
                                </td>'''
        html += '''
                            </tr>'''

    html += f'''
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- ③ 学生アクション 3x3 マトリクス (横幅いっぱい・広々スペース) -->
            <div class="sub-card" style="margin-bottom: 24px;">
                <h3 style="font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 6px;">🎓 ③ 【学生アクション】3×3 推移マトリクス (実数値 ＆ %)</h3>
                <div style="font-size: 12.5px; color: var(--gray-500); margin-bottom: 12px;">
                    パーソナリティ水準およびバリュー水準における学生の関心度（知りたい以上）と最優先選択（めっちゃ知りたい）の分布実態
                </div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th style="width: 22%; background: var(--gray-100);">パーソナリティ ＼ バリュー</th>
                                <th style="width: 26%; background: #FEE2E2;">バリュー低 (&lt;58.0)</th>
                                <th style="width: 26%; background: #FEF3C7;">バリュー中 (58.0〜63.9)</th>
                                <th style="width: 26%; background: #D1FAE5;">バリュー高 (≥64.0)</th>
                            </tr>
                        </thead>
                        <tbody>'''

    # Student Matrix Generation (Full-width with spacious cells)
    for r_idx, row in enumerate(m3x3):
        raw_p_lbl = row[0]['p_label']
        p_lbl = raw_p_lbl if raw_p_lbl.startswith('パーソナリティ') else f'パーソナリティ{raw_p_lbl}'
        bg_col = '#D1FAE5' if r_idx == 0 else ('#FEF3C7' if r_idx == 1 else '#FEE2E2')
        html += f'''
                            <tr>
                                <th style="background: {bg_col}; padding: 14px 10px;">{p_lbl}</th>'''
        for c in row:
            n = c['count']
            any_pct = c['student_any_pct']
            high_pct = c['student_high_pct']
            any_cnt = round(n * any_pct / 100.0)
            high_cnt = round(n * high_pct / 100.0)
            mid_cnt = any_cnt - high_cnt
            mid_pct = (mid_cnt / n * 100.0) if n > 0 else 0.0

            heat_bg = '#ECFDF5' if any_pct >= 60.0 else ('#F8FAFC' if any_pct >= 48.0 else '#FFFBEB')
            html += f'''
                                <td style="background: {heat_bg}; padding: 12px 16px; text-align: left; vertical-align: middle; border: 1px solid var(--gray-200);">
                                    <div style="font-weight: 800; font-size: 13.5px; color: #1E293B; margin-bottom: 6px;">
                                        知りたい以上: <span style="color: #047857; font-size: 15px;">{any_cnt}件 ({fmt_pct(any_pct)})</span>
                                    </div>
                                    <div style="font-size: 12px; color: #475569; border-top: 1px dashed #CBD5E1; padding-top: 6px; line-height: 1.55;">
                                        ・知りたい: <strong>{mid_cnt}件 ({fmt_pct(mid_pct)})</strong><br>
                                        ・めっちゃ知りたい: <strong style="color: #0F172A;">{high_cnt}件 ({fmt_pct(high_pct)})</strong>
                                    </div>
                                    <div style="font-size: 10.5px; color: #94A3B8; margin-top: 5px; text-align: right;">(セル母数 N={n}件)</div>
                                </td>'''
        html += '''
                            </tr>'''

    html += f'''
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="summary-box" style="margin-top: 24px;">
                <strong class="title">📝 データまとめ（3×3 実態集計 ＆ アクション推移）:</strong>
                <ul>
                    <li><strong>マッチング成立率（表①）</strong>：バリュー高（≥64.0）の水準では、パーソナリティ水準に関わらず成立率が <strong>54.1% 〜 61.2%</strong> と高水準を維持しています。一方、バリュー低かつパーソナリティ低のセルでは、成立 7/37件（<strong>18.9%</strong>）と最低値を記録しています。</li>
                    <li><strong>企業アクション推移（表②）</strong>：バリューが低➔高へ進むにつれ、「めっちゃ知りたい」の選択割合が <strong>10.8%（4件） ➔ 26.5%（13件）</strong>（パーソナリティ高の行）や、<strong>16.2%（6件） ➔ 45.9%（17件）</strong>（パーソナリティ低の行）へと急増し、企業の意思決定がバリュー水準に強く牽引されている実態が確認できます。</li>
                    <li><strong>学生アクション推移（表③）</strong>：学生側の「めっちゃ知りたい」は全体的に 6.7% 〜 19.2% の範囲で推移し、パーソナリティ中〜高かつバリュー高のセルで <strong>18.4%（9件）</strong> と最大値を記録しています。「知りたい以上」の総関心度もバリュー高の列で <strong>59.5% 〜 67.3%</strong> へと上昇しています。</li>
                </ul>
            </div>
        </div>

        <!-- Section 5: 全体解釈・示唆 (Tab 1末尾に集約) -->
        <div class="insight-card">
            <h3>💡 【全体解釈・示唆】客観的データ分析から読み取れる総合的考察</h3>
            <p><strong>1. 企業と学生におけるアクション選択傾向の相違（解釈）:</strong><br>
            企業の回帰分析結果より、企業はバリューフィット度スコアに強く連動してアクションを選択しており、スコア10pt上昇に伴い「知りたい以上」の選択オッズが約2.0倍、「めっちゃ知りたい」の選択オッズが約2.9倍（多変量で約2.5倍）に増大します。一方でパーソナリティフィット度には有意な連動は見られません。<br>
            対して学生側は、パーソナリティフィット度スコアの上昇に伴って「めっちゃ知りたい」を選択するオッズが約1.5倍に高まる傾向が確認され、バリューフィット度については一次関心である「知りたい」の選択オッズ（約1.4倍）に寄与しています。</p>
            
            <p><strong>2. 配席の違い（出展区分）がもたらした影響（解釈）:</strong><br>
            有料企業群は事前に高バリュー層が優先配席された背景があり、全体のベーススコアが高水準に位置しています。多変量ロジスティック回帰においてスコア要因を統計的に統制した結果、有料出展区分そのもののマッチング成立に対するオッズ比は 1.026倍（p = 0.9188）となり、独立した影響はほぼゼロであることが実証されます。有料企業のマッチ率の高さは、高バリュー層配席という前提条件が主因であったと解釈されます。</p>

            <p><strong>3. 次回イベント運営および配席設計へのデータ的示唆:</strong><br>
            3×3マトリクスの実態が示す通り、バリュー高の層では54%〜61%の安定したマッチング成立率が記録されている一方、両スコアがともに低い層では成立率が18.9%に沈んでいます。マッチング全体の効率を最大化する観点からは、バリューフィット度の高い組み合わせを優先的に配置し、低スコア同士の接触を抑制するアルゴリズム設計が有効であることが示唆されます。</p>
        </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 2: 有料出展 vs 無料出展 区分別分析 -->
    <!-- ============================================================= -->
    <div id="tab-stratified" class="tab-pane">
        <!-- Section 1: 区分別実態（有料 vs 無料） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">⚖️ 【区分別実態】有料出展企業（4社・122件） vs 無料出展企業（8社・191件）</div>
                    <div class="section-desc">配席条件の異なる出展区分別におけるアクション選択分布およびフィット度スコアの推移（記述統計）</div>
                </div>
                <span class="pill pill-slate">区分別記述統計</span>
            </div>

            <!-- 上段: 比較グラフ2列 -->
            <div class="grid-2" style="margin-bottom: 24px;">
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 企業アクション別：有料 vs 無料のフィット度推移</h3>
                    <div class="chart-box" style="height: 220px;">
                        <canvas id="chart-strat-comp"></canvas>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※無料企業では「めっちゃ知りたい」選択時のバリュー平均が <strong>64.24</strong> と急上昇（なし: 56.73から+7.5pt）。有料企業は全体ベースが高い（60.09〜63.13）。
                    </div>
                </div>
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🎓 学生アクション別：有料企業宛 vs 無料企業宛の推移</h3>
                    <div class="chart-box" style="height: 220px;">
                        <canvas id="chart-strat-stud"></canvas>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※学生から有料企業宛の「めっちゃ知りたい」では、パーソナリティ平均が <strong>82.44</strong>（なし: 78.82から+3.6pt）と最も高くなっています。
                    </div>
                </div>
            </div>

            <!-- 下段: 有料出展企業 vs 無料出展企業のすっきり分割テーブル -->
            <div class="grid-2">
                <!-- 有料企業カード -->
                <div class="sub-card" style="border-top: 3px solid #6366F1;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h3 style="font-size: 15px; font-weight: 700; color: #1E293B; margin: 0;">💎 有料出展企業の実態（4社・122件）</h3>
                        <span class="pill pill-indigo" style="font-size: 11px;">事前マッチング配席</span>
                    </div>

                    <div style="font-size: 12.5px; font-weight: 700; color: #334155; margin-bottom: 6px;">🏢 企業側アクションの推移</div>
                    <div class="table-container" style="margin-bottom: 16px;">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 28%;">アクション</th>
                                    <th style="width: 24%;">件数 (比率)</th>
                                    <th style="width: 24%;">バリュー平均</th>
                                    <th style="width: 24%;">P平均</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{paid_act['company']['three_cats'][0]['count']}件 ({fmt_pct(paid_act['company']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][0]['v_mean'])}</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][0]['p_mean'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{paid_act['company']['three_cats'][1]['count']}件 ({fmt_pct(paid_act['company']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][1]['v_mean'])}</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][1]['p_mean'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>めっちゃ知りたい</td>
                                    <td>{paid_act['company']['three_cats'][2]['count']}件 ({fmt_pct(paid_act['company']['three_cats'][2]['pct'])})</td>
                                    <td><strong>{fmt_num(paid_act['company']['three_cats'][2]['v_mean'])}</strong></td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][2]['p_mean'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700;">
                                    <td>知りたい以上</td>
                                    <td>{paid_act['company']['binary'][1]['count']}件 ({fmt_pct(paid_act['company']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['company']['binary'][1]['v_mean'])}</td>
                                    <td>{fmt_num(paid_act['company']['binary'][1]['p_mean'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div style="font-size: 12.5px; font-weight: 700; color: #334155; margin-bottom: 6px;">🎓 学生側アクションの推移</div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 28%;">アクション</th>
                                    <th style="width: 24%;">件数 (比率)</th>
                                    <th style="width: 24%;">バリュー平均</th>
                                    <th style="width: 24%;">P平均</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{paid_act['student']['three_cats'][0]['count']}件 ({fmt_pct(paid_act['student']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][0]['v_mean'])}</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][0]['p_mean'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{paid_act['student']['three_cats'][1]['count']}件 ({fmt_pct(paid_act['student']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][1]['v_mean'])}</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][1]['p_mean'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>めっちゃ知りたい</td>
                                    <td>{paid_act['student']['three_cats'][2]['count']}件 ({fmt_pct(paid_act['student']['three_cats'][2]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][2]['v_mean'])}</td>
                                    <td><strong>{fmt_num(paid_act['student']['three_cats'][2]['p_mean'])}</strong></td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700;">
                                    <td>知りたい以上</td>
                                    <td>{paid_act['student']['binary'][1]['count']}件 ({fmt_pct(paid_act['student']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['binary'][1]['v_mean'])}</td>
                                    <td>{fmt_num(paid_act['student']['binary'][1]['p_mean'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 無料企業カード -->
                <div class="sub-card" style="border-top: 3px solid #06B6D4;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h3 style="font-size: 15px; font-weight: 700; color: #1E293B; margin: 0;">🌱 無料出展企業の実態（8社・191件 / P有効164件）</h3>
                        <span class="pill pill-cyan" style="font-size: 11px;">完全自由配席</span>
                    </div>

                    <div style="font-size: 12.5px; font-weight: 700; color: #334155; margin-bottom: 6px;">🏢 企業側アクションの推移</div>
                    <div class="table-container" style="margin-bottom: 16px;">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 28%;">アクション</th>
                                    <th style="width: 24%;">件数 (比率)</th>
                                    <th style="width: 24%;">バリュー平均</th>
                                    <th style="width: 24%;">P平均</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{free_act['company']['three_cats'][0]['count']}件 ({fmt_pct(free_act['company']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][0]['v_mean'])}</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][0]['p_mean'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{free_act['company']['three_cats'][1]['count']}件 ({fmt_pct(free_act['company']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][1]['v_mean'])}</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][1]['p_mean'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>めっちゃ知りたい</td>
                                    <td>{free_act['company']['three_cats'][2]['count']}件 ({fmt_pct(free_act['company']['three_cats'][2]['pct'])})</td>
                                    <td><strong>{fmt_num(free_act['company']['three_cats'][2]['v_mean'])}</strong></td>
                                    <td>{fmt_num(free_act['company']['three_cats'][2]['p_mean'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700;">
                                    <td>知りたい以上</td>
                                    <td>{free_act['company']['binary'][1]['count']}件 ({fmt_pct(free_act['company']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['company']['binary'][1]['v_mean'])}</td>
                                    <td>{fmt_num(free_act['company']['binary'][1]['p_mean'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div style="font-size: 12.5px; font-weight: 700; color: #334155; margin-bottom: 6px;">🎓 学生側アクションの推移</div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 28%;">アクション</th>
                                    <th style="width: 24%;">件数 (比率)</th>
                                    <th style="width: 24%;">バリュー平均</th>
                                    <th style="width: 24%;">P平均</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{free_act['student']['three_cats'][0]['count']}件 ({fmt_pct(free_act['student']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][0]['v_mean'])}</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][0]['p_mean'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{free_act['student']['three_cats'][1]['count']}件 ({fmt_pct(free_act['student']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][1]['v_mean'])}</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][1]['p_mean'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>めっちゃ知りたい</td>
                                    <td>{free_act['student']['three_cats'][2]['count']}件 ({fmt_pct(free_act['student']['three_cats'][2]['pct'])})</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][2]['v_mean'])}</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][2]['p_mean'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700;">
                                    <td>知りたい以上</td>
                                    <td>{free_act['student']['binary'][1]['count']}件 ({fmt_pct(free_act['student']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['student']['binary'][1]['v_mean'])}</td>
                                    <td>{fmt_num(free_act['student']['binary'][1]['p_mean'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Section 2: 区分別要因分析（要点まとめ ＆ 詳細モデル） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🎯 【区分別要因分析】出展区分ごとの要因分析（要点まとめ ＆ 詳細モデル）</div>
                    <div class="section-desc">有料企業（N=122）および無料企業（N=191/164）におけるスコア影響度の要約と回帰モデル</div>
                </div>
                <span class="pill pill-indigo">区分別要因分析</span>
            </div>

            <!-- 前面：要点まとめ比較テーブル ＆ インパクトグラフ -->
            <div class="grid-2" style="margin-bottom: 20px;">
                <!-- 左：要点まとめ比較テーブル -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📋 有料企業 vs 無料企業：スコア影響度の比較要点まとめ</h3>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 22%;">出展区分</th>
                                    <th style="width: 38%;">バリューの影響（10pt上昇）</th>
                                    <th style="width: 40%;">パーソナリティの影響 ＆ 特徴</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="background: #F0FDFA;">
                                    <td>
                                        <strong style="color: #0F766E;">🌱 無料企業群</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500);">(8社・191件 / P有効164件)</span>
                                    </td>
                                    <td>
                                        <strong style="color: #0F766E; font-size: 13.5px;">知りたい以上：約 2.06 倍 (***)</strong><br>
                                        <strong style="color: #0F766E; font-size: 13.5px;">めっちゃ知りたい：約 3.22 倍 (***)</strong>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.35;">
                                            企業の完全な自由選択が行われたため、バリューフィット度が最高のアクション選択を強力に牽引。
                                        </div>
                                    </td>
                                    <td>
                                        <span style="color: var(--gray-500); font-size: 12px;">約 1.16 倍（有意差なし）</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.35;">
                                            パーソナリティは選択確率を左右しておらず、バリュー主導の選定傾向が鮮明。
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <strong style="color: var(--primary);">💎 有料企業群</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500);">(4社・122件)</span>
                                    </td>
                                    <td>
                                        <span style="color: var(--primary); font-size: 13px; font-weight: 700;">知りたい以上：約 1.78 倍 (†)</span><br>
                                        <span style="color: var(--primary); font-size: 13px; font-weight: 700;">めっちゃ知りたい：約 2.17 倍 (†)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.35;">
                                            事前マッチングにより元々高バリュー層が集中的に配席されていたため、倍率効果はマイルドに表れる。
                                        </div>
                                    </td>
                                    <td>
                                        <span style="color: var(--gray-500); font-size: 12px;">約 0.98 倍（有意差なし）</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.35;">
                                            企業アクションには有意差なし。一方、学生からのアクションではP平均が大きく押し上がる傾向。
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※「影響度（倍率）」はロジスティック回帰のオッズ比（OR）に基づき、スコアが10pt上昇した際のアクション選択確率の上昇度合いを示しています。
                    </div>
                </div>

                <!-- 右：視覚的インパクト比較グラフ -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📊 区分別 選択倍率インパクト比較（有料 vs 無料 / 基準=1.0倍）</h3>
                    <div class="chart-box" style="height: 230px;">
                        <canvas id="chart-strat-impact"></canvas>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※赤線（1.0倍）より右に大きく伸びるほど強いプラス影響。無料企業の「めっちゃ知りたい」バリューOR（3.22倍***）が最も顕著。
                    </div>
                </div>
            </div>

            <!-- 専門的な詳細アコーディオン -->
            <details class="stats-details">
                <summary class="stats-summary">
                    <span>📊 有料企業・無料企業別の詳細統計データ（オッズ比・95%信頼区間・p値）を展開する</span>
                    <span class="pill pill-indigo">クリックで開閉</span>
                </summary>
                <div class="stats-content">
                    <!-- 有料企業回帰 -->
                    <div style="margin-bottom: 24px;">
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 有料企業 (N=122) における企業アクション回帰詳細</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 24%;">モデル / 説明変数</th>
                                        <th style="width: 25%;">① 2値ロジット：知りたい以上<br><span style="font-size: 10px;">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 25%;">②-A 多項ロジット：なし ➔ 知りたい<br><span style="font-size: 10px;">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 25%;">②-B 多項ロジット：なし ➔ めっちゃ知りたい<br><span style="font-size: 10px;">OR (10pt上昇) [95%CI] / p値</span></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>バリューフィット度 (単変量)</td>
                                        <td>OR {fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                    </tr>
                                    <tr>
                                        <td>パーソナリティフィット度 (単変量)</td>
                                        <td>OR {fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 無料企業回帰 -->
                    <div>
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 無料企業 (N=191 / 164) における企業アクション回帰詳細</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 24%;">モデル / 説明変数</th>
                                        <th style="width: 25%;">① 2値ロジット：知りたい以上<br><span style="font-size: 10px;">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 25%;">②-A 多項ロジット：なし ➔ 知りたい<br><span style="font-size: 10px;">OR (10pt上昇) [95%CI] / p値</span></th>
                                        <th style="width: 25%;">②-B 多項ロジット：なし ➔ めっちゃ知りたい<br><span style="font-size: 10px;">OR (10pt上昇) [95%CI] / p値</span></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>バリューフィット度 (単変量)</td>
                                        <td><strong>OR {fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                    </tr>
                                    <tr>
                                        <td>パーソナリティフィット度 (単変量)</td>
                                        <td>OR {fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </details>

            <div class="summary-box">
                <strong class="title">📝 データまとめ（区分別の回帰分析結果）:</strong>
                <ul>
                    <li><strong>無料企業群</strong>：バリューフィット度の上昇に伴う選択オッズ比が極めて顕著であり、2値で OR {fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 2)}（p &lt; 0.0001***）、多項の「めっちゃ知りたい」で OR {fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 2)}（p &lt; 0.0001***）と大幅な上昇を示しています。</li>
                    <li><strong>有料企業群</strong>：高バリュー層が優先配席されていたため全体にベースが高く、バリューフィット度の「めっちゃ知りたい」オッズ比は OR {fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 2)}（p = 0.0651†）の有意傾向にとどまります。</li>
                    <li>両区分ともに、パーソナリティフィット度は企業の選択オッズに対して統計的有意差を持ちません。</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 3: 全12社 比較一覧・個別カルテ -->
    <!-- ============================================================= -->
    <div id="tab-companies" class="tab-pane">
        <!-- 12社一覧比較テーブル -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🏢 【企業間比較】全12社 実績・スコア一覧テーブル</div>
                    <div class="section-desc">全12社の接触件数、マッチング成立状況、各フィット度平均値、およびアクション選択構成の実測一覧</div>
                </div>
                <span class="pill pill-slate">12社全件一覧</span>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>企業名</th>
                            <th>区分</th>
                            <th>接触数</th>
                            <th>マッチ成立</th>
                            <th>成立率</th>
                            <th>バリュー平均</th>
                            <th>P平均</th>
                            <th>企業 めっちゃ知りたい</th>
                            <th>企業 知りたい以上</th>
                            <th>学生 めっちゃ知りたい</th>
                            <th>学生 知りたい以上</th>
                            <th>めっちゃ知りたい群 − なし群 バリュー差</th>
                        </tr>
                    </thead>
                    <tbody>'''

    for c in comps:
        plan_badge = '<span class="pill pill-indigo">有料</span>' if c['is_paid'] == 1 else '<span class="pill pill-slate">無料</span>'
        v_diff_str = f"+{fmt_num(c['v_diff_high_minus_none'])} pt" if (c['v_diff_high_minus_none'] is not None and c['v_diff_high_minus_none'] >= 0) else (f"{fmt_num(c['v_diff_high_minus_none'])} pt" if c['v_diff_high_minus_none'] is not None else '-')
        html += f'''
                        <tr>
                            <td><strong>{c['name']}</strong></td>
                            <td>{plan_badge}</td>
                            <td>{c['count']}名</td>
                            <td>{c['match_count']}件</td>
                            <td><strong>{fmt_pct(c['match_rate'])}</strong></td>
                            <td>{fmt_num(c['v_mean'])}</td>
                            <td>{fmt_num(c['p_mean'])}</td>
                            <td>{c['company_actions']['めっちゃ知りたい']['count']}件 ({fmt_pct(c['company_actions']['めっちゃ知りたい']['pct'])})</td>
                            <td>{c['company_actions']['知りたい以上']['count']}件 ({fmt_pct(c['company_actions']['知りたい以上']['pct'])})</td>
                            <td>{c['student_actions']['めっちゃ知りたい']['count']}件 ({fmt_pct(c['student_actions']['めっちゃ知りたい']['pct'])})</td>
                            <td>{c['student_actions']['知りたい以上']['count']}件 ({fmt_pct(c['student_actions']['知りたい以上']['pct'])})</td>
                            <td><strong>{v_diff_str}</strong></td>
                        </tr>'''

    html += f'''
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 🔍 個別企業カルテ -->
        <div class="section-card">
            <div class="section-header">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <div class="section-title">🔍 【個別カルテ】</div>
                    <select id="company-select" onchange="renderCompanyDetail(this.value)" style="padding: 6px 12px; font-size: 14px; font-weight: 700; border-radius: 6px; border: 1px solid var(--gray-300);">'''

    for idx, c in enumerate(comps):
        html += f'''
                        <option value="{idx}">{c['name']} ({'有料' if c['is_paid']==1 else '無料'})</option>'''

    html += f'''
                    </select>
                </div>
                <div id="cd-plan-badge"></div>
            </div>

            <!-- KPI Cards -->
            <div class="grid-4">
                <div class="kpi-card">
                    <div class="kpi-title">接触学生数</div>
                    <div class="kpi-value" id="cd-count">-</div>
                    <div class="kpi-sub" id="cd-matches-sub">-</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">マッチング成立率</div>
                    <div class="kpi-value" style="color: var(--success);" id="cd-match-rate">-</div>
                    <div class="kpi-sub">確定マッチ数 / 総接触数</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">バリューフィット度 平均</div>
                    <div class="kpi-value" id="cd-v-mean">-</div>
                    <div class="kpi-sub">接触全学生の平均値</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">パーソナリティフィット度 平均</div>
                    <div class="kpi-value" id="cd-p-mean">-</div>
                    <div class="kpi-sub">接触全学生の平均値</div>
                </div>
            </div>

            <div class="grid-2">
                <!-- 企業アクション -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 企業アクション別実態</h3>
                    <div class="chart-box" style="height: 180px;">
                        <canvas id="chart-cd-comp"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>アクション区分</th>
                                    <th>件数 (構成比)</th>
                                    <th>バリュー平均</th>
                                    <th>P平均</th>
                                </tr>
                            </thead>
                            <tbody id="cd-tbody-comp"></tbody>
                        </table>
                    </div>
                </div>

                <!-- 学生アクション -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🎓 学生アクション別実態</h3>
                    <div class="chart-box" style="height: 180px;">
                        <canvas id="chart-cd-stud"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>アクション区分</th>
                                    <th>件数 (構成比)</th>
                                    <th>バリュー平均</th>
                                    <th>P平均</th>
                                </tr>
                            </thead>
                            <tbody id="cd-tbody-stud"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="summary-box" style="margin-top: 20px;">
                <strong class="title">📝 当該企業のデータまとめ:</strong>
                <div id="cd-summary-text"></div>
            </div>
        </div>
    </div>
</div>

<script>
    // Tab switching
    function switchTab(tabId) {{
        document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        
        document.getElementById(tabId).classList.add('active');
        event.currentTarget.classList.add('active');

        if (tabId === 'tab-companies') {{
            const sel = document.getElementById('company-select');
            renderCompanyDetail(sel.value);
        }}
        window.dispatchEvent(new Event('resize'));
    }}

    // Overall Charts
    new Chart(document.getElementById('chart-comp-overall'), {{
        type: 'bar',
        data: {{
            labels: ['なし ({ov_act['company']['three_cats'][0]['count']}件)', '知りたい ({ov_act['company']['three_cats'][1]['count']}件)', 'めっちゃ知りたい ({ov_act['company']['three_cats'][2]['count']}件)'],
            datasets: [
                {{
                    label: 'バリューフィット度 平均',
                    data: [{ov_act['company']['three_cats'][0]['v_mean']}, {ov_act['company']['three_cats'][1]['v_mean']}, {ov_act['company']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#4F46E5',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティフィット度 平均',
                    data: [{ov_act['company']['three_cats'][0]['p_mean']}, {ov_act['company']['three_cats'][1]['p_mean']}, {ov_act['company']['three_cats'][2]['p_mean']}],
                    backgroundColor: '#94A3B8',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ min: 50, max: 85 }} }}
        }}
    }});
// Logit Impact Chart
    new Chart(document.getElementById('chart-logit-impact'), {{
        type: 'bar',
        data: {{
            labels: [
                '企業：バリュー (めっちゃ知りたい)',
                '企業：バリュー (知りたい以上)',
                '学生：パーソナリティ (めっちゃ知りたい)',
                '学生：バリュー (知りたい以上)',
                '企業：パーソナリティ (知りたい以上)'
            ],
            datasets: [{{
                label: 'スコア10pt上昇時の選択倍率 (オッズ比)',
                data: [
                    2.908,
                    2.027,
                    1.490,
                    1.248,
                    1.096
                ],
                backgroundColor: [
                    '#4F46E5',
                    '#6366F1',
                    '#F59E0B',
                    '#06B6D4',
                    '#94A3B8'
                ],
                borderRadius: 4
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            return '選択倍率: ' + context.parsed.x.toFixed(2) + ' 倍';
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    min: 0,
                    max: 3.5,
                    grid: {{
                        color: function(context) {{
                            return context.tick.value === 1.0 ? '#EF4444' : '#E2E8F0';
                        }},
                        lineWidth: function(context) {{
                            return context.tick.value === 1.0 ? 2 : 1;
                        }}
                    }},
                    title: {{
                        display: true,
                        text: '← 影響なし (1.0倍) | 選択されやすくなる (倍率) →',
                        font: {{ size: 10, weight: 'bold' }}
                    }}
                }}
            }}
        }}
    }});


    new Chart(document.getElementById('chart-stud-overall'), {{
        type: 'bar',
        data: {{
            labels: ['なし ({ov_act['student']['three_cats'][0]['count']}件)', '知りたい ({ov_act['student']['three_cats'][1]['count']}件)', 'めっちゃ知りたい ({ov_act['student']['three_cats'][2]['count']}件)'],
            datasets: [
                {{
                    label: 'バリューフィット度 平均',
                    data: [{ov_act['student']['three_cats'][0]['v_mean']}, {ov_act['student']['three_cats'][1]['v_mean']}, {ov_act['student']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#06B6D4',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティフィット度 平均',
                    data: [{ov_act['student']['three_cats'][0]['p_mean']}, {ov_act['student']['three_cats'][1]['p_mean']}, {ov_act['student']['three_cats'][2]['p_mean']}],
                    backgroundColor: '#F59E0B',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ min: 50, max: 85 }} }}
        }}
    }});

    // Stratified Comparison Charts (Tab 2)
    new Chart(document.getElementById('chart-strat-comp'), {{
        type: 'bar',
        data: {{
            labels: ['なし', '知りたい', 'めっちゃ知りたい'],
            datasets: [
                {{
                    label: '有料企業：バリュー平均',
                    data: [{paid_act['company']['three_cats'][0]['v_mean']}, {paid_act['company']['three_cats'][1]['v_mean']}, {paid_act['company']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#4F46E5',
                    borderRadius: 4
                }},
                {{
                    label: '無料企業：バリュー平均',
                    data: [{free_act['company']['three_cats'][0]['v_mean']}, {free_act['company']['three_cats'][1]['v_mean']}, {free_act['company']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#06B6D4',
                    borderRadius: 4
                }},
                {{
                    label: '有料企業：P平均',
                    data: [{paid_act['company']['three_cats'][0]['p_mean']}, {paid_act['company']['three_cats'][1]['p_mean']}, {paid_act['company']['three_cats'][2]['p_mean']}],
                    backgroundColor: '#94A3B8',
                    borderRadius: 4
                }},
                {{
                    label: '無料企業：P平均',
                    data: [{free_act['company']['three_cats'][0]['p_mean']}, {free_act['company']['three_cats'][1]['p_mean']}, {free_act['company']['three_cats'][2]['p_mean']}],
                    backgroundColor: '#CBD5E1',
                    borderRadius: 4
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ min: 50, max: 85 }} }}
        }}
    }});

    new Chart(document.getElementById('chart-strat-stud'), {{
        type: 'bar',
        data: {{
            labels: ['なし', '知りたい', 'めっちゃ知りたい'],
            datasets: [
                {{
                    label: '有料企業宛：バリュー平均',
                    data: [{paid_act['student']['three_cats'][0]['v_mean']}, {paid_act['student']['three_cats'][1]['v_mean']}, {paid_act['student']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#4F46E5',
                    borderRadius: 4
                }},
                {{
                    label: '無料企業宛：バリュー平均',
                    data: [{free_act['student']['three_cats'][0]['v_mean']}, {free_act['student']['three_cats'][1]['v_mean']}, {free_act['student']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#06B6D4',
                    borderRadius: 4
                }},
                {{
                    label: '有料企業宛：P平均',
                    data: [{paid_act['student']['three_cats'][0]['p_mean']}, {paid_act['student']['three_cats'][1]['p_mean']}, {paid_act['student']['three_cats'][2]['p_mean']}],
                    backgroundColor: '#F59E0B',
                    borderRadius: 4
                }},
                {{
                    label: '無料企業宛：P平均',
                    data: [{free_act['student']['three_cats'][0]['p_mean']}, {free_act['student']['three_cats'][1]['p_mean']}, {free_act['student']['three_cats'][2]['p_mean']}],
                    backgroundColor: '#FCD34D',
                    borderRadius: 4
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ min: 50, max: 85 }} }}
        }}
    }});

    new Chart(document.getElementById('chart-strat-impact'), {{
        type: 'bar',
        data: {{
            labels: [
                '無料企業：バリュー (めっちゃ知りたい)',
                '有料企業：バリュー (めっちゃ知りたい)',
                '無料企業：バリュー (知りたい以上)',
                '有料企業：バリュー (知りたい以上)',
                '無料企業：パーソナリティ (知りたい以上)',
                '有料企業：パーソナリティ (知りたい以上)'
            ],
            datasets: [{{
                label: 'スコア10pt上昇時の選択倍率 (オッズ比)',
                data: [
                    {fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)}
                ],
                backgroundColor: [
                    '#0D9488',
                    '#4F46E5',
                    '#14B8A6',
                    '#6366F1',
                    '#94A3B8',
                    '#CBD5E1'
                ],
                borderRadius: 4
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            return '選択倍率: ' + context.parsed.x.toFixed(2) + ' 倍';
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    min: 0,
                    max: 3.8,
                    grid: {{
                        color: function(context) {{
                            return context.tick.value === 1.0 ? '#EF4444' : '#E2E8F0';
                        }},
                        lineWidth: function(context) {{
                            return context.tick.value === 1.0 ? 2 : 1;
                        }}
                    }},
                    title: {{
                        display: true,
                        text: '← 影響なし (1.0倍) | 選択されやすくなる (倍率) →',
                        font: {{ size: 10, weight: 'bold' }}
                    }}
                }}
            }}
        }}
    }});

        // Company Detail Data
    const companiesData = {json.dumps(comps, ensure_ascii=False)};
    let compChartInst = null;
    let studChartInst = null;

    function renderCompanyDetail(idx) {{
        const c = companiesData[idx];
        if (!c) return;

        document.getElementById('cd-plan-badge').innerHTML = c.is_paid === 1 
            ? '<span class="pill pill-indigo">有料出展</span>' 
            : '<span class="pill pill-slate">無料出展</span>';
            
        document.getElementById('cd-count').innerHTML = c.count + ' <span style="font-size:14px;font-weight:normal;color:var(--gray-500)">名</span>';
        document.getElementById('cd-matches-sub').innerHTML = 'うちマッチ成立 <strong>' + c.match_count + '</strong> 件';
        document.getElementById('cd-match-rate').innerText = c.match_rate.toFixed(1) + '%';
        document.getElementById('cd-v-mean').innerText = (c.v_mean !== null ? c.v_mean.toFixed(2) : '-') + ' pt';
        document.getElementById('cd-p-mean').innerText = (c.p_mean !== null ? c.p_mean.toFixed(2) : '-') + ' pt';

        // Tbody Company
        let compRows = '';
        ['なし', '知りたい', 'めっちゃ知りたい'].forEach(act => {{
            const item = c.company_actions[act];
            const isHigh = act === 'めっちゃ知りたい';
            const labelSub = isHigh ? '<br><span style="font-size:10px;color:var(--gray-500);font-weight:normal;">(10社限定)</span>' : '';
            compRows += `<tr class="${{isHigh ? 'highlight-row' : ''}}">
                <td><strong>${{act}}</strong>${{labelSub}}</td>
                <td>${{item.count}}件 (${{item.pct.toFixed(1)}}%)</td>
                <td>${{item.v_mean !== null ? item.v_mean.toFixed(2) : '-'}}</td>
                <td>${{item.p_mean !== null ? item.p_mean.toFixed(2) : '-'}}</td>
            </tr>`;
        }});
        compRows += `<tr style="background:#F1F5F9;font-weight:700;">
            <td>知りたい以上</td>
            <td>${{c.company_actions['知りたい以上'].count}}件 (${{c.company_actions['知りたい以上'].pct.toFixed(1)}}%)</td>
            <td>-</td>
            <td>-</td>
        </tr>`;
        document.getElementById('cd-tbody-comp').innerHTML = compRows;

        // Tbody Student
        let studRows = '';
        ['なし', '知りたい', 'めっちゃ知りたい'].forEach(act => {{
            const item = c.student_actions[act];
            const isHigh = act === 'めっちゃ知りたい';
            const labelSub = isHigh ? '<br><span style="font-size:10px;color:var(--gray-500);font-weight:normal;">(10社限定)</span>' : '';
            studRows += `<tr class="${{isHigh ? 'highlight-row' : ''}}">
                <td><strong>${{act}}</strong>${{labelSub}}</td>
                <td>${{item.count}}件 (${{item.pct.toFixed(1)}}%)</td>
                <td>${{item.v_mean !== null ? item.v_mean.toFixed(2) : '-'}}</td>
                <td>${{item.p_mean !== null ? item.p_mean.toFixed(2) : '-'}}</td>
            </tr>`;
        }});
        studRows += `<tr style="background:#F1F5F9;font-weight:700;">
            <td>知りたい以上</td>
            <td>${{c.student_actions['知りたい以上'].count}}件 (${{c.student_actions['知りたい以上'].pct.toFixed(1)}}%)</td>
            <td>-</td>
            <td>-</td>
        </tr>`;
        document.getElementById('cd-tbody-stud').innerHTML = studRows;

        // Summary Text
        const vDiff = c.v_diff_high_minus_none;
        const diffText = vDiff !== null ? `「めっちゃ知りたい」群と「なし」群のバリューフィット度平均の差は <strong>${{vDiff >= 0 ? '+' : ''}}${{vDiff.toFixed(2)}} pt</strong> です。` : '比較対象データなし。';
        document.getElementById('cd-summary-text').innerHTML = `
            <ul>
                <li>総接触学生数 ${{c.count}}名中、マッチング成立は <strong>${{c.match_count}}件 (${{c.match_rate.toFixed(1)}}%)</strong> でした。</li>
                <li>企業アクションにおいて「知りたい以上」を選択した比率は <strong>${{c.company_actions['知りたい以上'].pct.toFixed(1)}}%</strong>、学生側から「知りたい以上」を受けた比率は <strong>${{c.student_actions['知りたい以上'].pct.toFixed(1)}}%</strong> です。</li>
                <li>${{diffText}}</li>
            </ul>
        `;

        // Update charts
        const cLabels = ['なし', '知りたい', 'めっちゃ知りたい'];
        const cVData = cLabels.map(l => c.company_actions[l].v_mean);
        const cPData = cLabels.map(l => c.company_actions[l].p_mean);
        const sVData = cLabels.map(l => c.student_actions[l].v_mean);
        const sPData = cLabels.map(l => c.student_actions[l].p_mean);

        if (compChartInst) compChartInst.destroy();
        compChartInst = new Chart(document.getElementById('chart-cd-comp'), {{
            type: 'bar',
            data: {{
                labels: cLabels,
                datasets: [
                    {{ label: 'バリュー平均', data: cVData, backgroundColor: '#4F46E5', borderRadius: 4 }},
                    {{ label: 'P平均', data: cPData, backgroundColor: '#94A3B8', borderRadius: 4 }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ min: 45, max: 90 }} }} }}
        }});

        if (studChartInst) studChartInst.destroy();
        studChartInst = new Chart(document.getElementById('chart-cd-stud'), {{
            type: 'bar',
            data: {{
                labels: cLabels,
                datasets: [
                    {{ label: 'バリュー平均', data: sVData, backgroundColor: '#06B6D4', borderRadius: 4 }},
                    {{ label: 'P平均', data: sPData, backgroundColor: '#F59E0B', borderRadius: 4 }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, scales: {{ y: {{ min: 45, max: 90 }} }} }}
        }});
    }}

    // Init first company
    renderCompanyDetail(0);
</script>

</body>
</html>'''

    with open('asobiba_fes_fit_analysis_report.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Successfully built asobiba_fes_fit_analysis_report.html with fixed layout!")

if __name__ == '__main__':
    build_html()

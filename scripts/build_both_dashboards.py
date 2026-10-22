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
    # Load raw CSV for download
    with open('asobiba_fes_raw_data_313.csv', 'r', encoding='utf-8-sig') as f:
        raw_csv_text = f.read().strip()

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
        /* 12社テーブル ソート＆連動スタイル */
        th.sortable {{
            cursor: pointer;
            user-select: none;
            transition: background 0.15s ease, color 0.15s ease;
            white-space: nowrap;
        }}
        th.sortable:hover {{
            background: #E2E8F0 !important;
            color: var(--primary-dark) !important;
        }}
        th.sortable .sort-icon {{
            display: inline-block;
            margin-left: 4px;
            font-size: 11px;
            color: var(--gray-400);
            transition: color 0.15s;
        }}
        th.sortable.active-sort {{
            background: #EEF2FF !important;
            color: var(--primary) !important;
            border-bottom: 2px solid var(--primary);
        }}
        th.sortable.active-sort .sort-icon {{
            color: var(--primary);
            font-weight: 800;
        }}
        tr.company-row {{
            cursor: pointer;
            transition: background 0.15s ease;
        }}
        tr.company-row:hover {{
            background: #F1F5F9 !important;
        }}
        tr.company-row.selected-company {{
            background: #EEF2FF !important;
            border-left: 4px solid var(--primary) !important;
        }}
        .plan-filter-btn {{
            padding: 6px 12px;
            border: none;
            background: white;
            font-size: 12.5px;
            font-weight: 600;
            color: var(--gray-600);
            cursor: pointer;
            transition: all 0.15s;
        }}
        .plan-filter-btn:not(:last-child) {{
            border-right: 1px solid var(--gray-300);
        }}
        .plan-filter-btn:hover {{
            background: var(--gray-50);
            color: var(--primary);
        }}
        .plan-filter-btn.active {{
            background: var(--primary);
            color: white;
        }}
        .nav-mini-btn {{
            background: white;
            border: 1px solid var(--gray-300);
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
            cursor: pointer;
            color: var(--gray-700);
            font-weight: 700;
            transition: all 0.15s;
        }}
        .nav-mini-btn:hover {{
            background: var(--primary-light);
            color: var(--primary);
            border-color: var(--primary);
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

        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

/* Executive Summary Hero Card */
        .exec-summary-card {{
            background: #FFFFFF;
            border: 1px solid #E0E7FF;
            border-left: 6px solid var(--primary);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: var(--card-shadow);
        }}

        .exec-summary-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--gray-200);
            flex-wrap: wrap;
            gap: 12px;
        }}

        .exec-summary-title {{
            font-size: 18px;
            font-weight: 800;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .exec-summary-desc {{
            font-size: 13.5px;
            color: var(--gray-600);
            margin-top: 4px;
        }}

        .exec-summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}

        .exec-item-card {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease;
        }}

        .exec-item-card:hover {{
            border-color: #CBD5E1;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transform: translateY(-2px);
        }}

        .exec-item-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }}

        .exec-item-icon {{
            font-size: 20px;
            line-height: 1;
        }}

        .exec-item-title {{
            font-size: 14.5px;
            font-weight: 700;
            color: var(--gray-800);
        }}

        .exec-item-body {{
            font-size: 13px;
            color: var(--gray-600);
            line-height: 1.6;
            margin-bottom: 12px;
            flex-grow: 1;
        }}

        .exec-item-highlight {{
            background: #EEF2FF;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            color: #3730A3;
            font-weight: 600;
            line-height: 1.45;
            border-left: 3px solid var(--primary);
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
    
        /* Raw CSV Download Button */
        .header-actions {{
            display: flex;
            align-items: center;
        }}

        .btn-download {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #10B981;
            color: #ffffff !important;
            font-weight: 700;
            font-size: 13.5px;
            padding: 10px 18px;
            border-radius: 9999px;
            text-decoration: none;
            border: 1px solid rgba(255, 255, 255, 0.25);
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .btn-download:hover {{
            background: #059669;
            box-shadow: 0 6px 18px rgba(16, 185, 129, 0.55);
            transform: translateY(-1px);
        }}

        .btn-download:active {{
            transform: translateY(0);
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
        <div class="header-actions">
            <button type="button" class="btn-download" onclick="downloadRawCSV()" title="分析の基礎となった全313行の元データ一覧をダウンロード">
                <span style="font-size: 16px;">📥</span>
                <span>参照生データをダウンロード (CSV: 313件)</span>
            </button>
        </div>
    </div>
</header>

<div class="container">
    <!-- Tab Navigation Bar -->
    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('tab-overall')">
            <span>📊</span> Tab 1: 全体実態分析
        </button>
        <!-- Tab 2: 有料出展 vs 無料出展 区分別分析（非表示化）
        <button class="tab-btn" onclick="switchTab('tab-stratified')">
            <span>⚖️</span> 有料出展 vs 無料出展 区分別分析
        </button>
        -->
        <button class="tab-btn" onclick="switchTab('tab-companies')">
            <span>🏢</span> Tab 2: 全12社 比較一覧・個別カルテ
        </button>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 1: 全体実態分析 -->
    <!-- ============================================================= -->
    <div id="tab-overall" class="tab-pane active">
        <!-- Executive Summary: このレポートで分かること -->
        <div class="exec-summary-card">
            <div class="exec-summary-header">
                <div>
                    <div class="exec-summary-title">
                        <span>💡</span>
                        <span>【要約】このレポートで分かること（サマリーハイライト）</span>
                    </div>
                    <div class="exec-summary-desc">
                        専門用語を使わずに、当日の客観的事実から明らかになった「4つの主要な実態」を簡潔にまとめています。
                    </div>
                </div>
                <span class="pill pill-indigo" style="font-size: 12px; padding: 6px 12px;">ひと目でわかる全体像</span>
            </div>

            <div class="exec-summary-grid">
                <!-- Point 1 -->
                <div class="exec-item-card">
                    <div>
                        <div class="exec-item-header">
                            <span class="exec-item-icon">🏢</span>
                            <div class="exec-item-title">重視するポイントの違い</div>
                        </div>
                        <div class="exec-item-body">
                            ・<strong>企業側</strong>：自社の理念やカルチャーへの共感度（バリュー）が高い学生ほど、「知りたい」「めっちゃ知りたい」と選ぶ傾向が顕著でした。<br>
                            ・<strong>学生側</strong>：面談で実際に話したときの相性や雰囲気（パーソナリティ）が良い企業ほど、「知りたい」と選ぶ傾向が見られました。
                        </div>
                    </div>
                    <div class="exec-item-highlight">
                        💡 企業は「カルチャー」、学生は「対話の相性・居心地」を重視する自然な役割分担が数字に表れています。
                    </div>
                </div>

                <!-- Point 2 -->
                <div class="exec-item-card">
                    <div>
                        <div class="exec-item-header">
                            <span class="exec-item-icon">🤝</span>
                            <div class="exec-item-title">マッチング成立の条件</div>
                        </div>
                        <div class="exec-item-body">
                            双方が「知りたい」となってマッチングが成立したのは全体の約4割（40.9%）。<br>
                            ・「価値観」と「性格」が<strong>両方高いペア</strong>：成立率 <strong>約6割（55〜61%）</strong><br>
                            ・<strong>両方低いペア</strong>：成立率 <strong>約2割（18.9%）</strong><br>
                            どちらか片方だけが高くても成立率は伸び悩む傾向が確認されました。
                        </div>
                    </div>
                    <div class="exec-item-highlight">
                        💡 「企業が求める価値観」と「学生が感じる対話の相性」の双方が揃うことがマッチングの鍵です。
                    </div>
                </div>

                <!-- Point 3 -->
                <div class="exec-item-card">
                    <div>
                        <div class="exec-item-header">
                            <span class="exec-item-icon">⏱️</span>
                            <div class="exec-item-title">面談ターンに伴う行動変化</div>
                        </div>
                        <div class="exec-item-body">
                            ・<strong>企業側</strong>：面談の回数（ターン）が進むにつれて「知りたい」と選ぶ枠を広げていく傾向（後半ほど積極的：約59% ➔ 77%）がありました。<br>
                            ・<strong>学生側</strong>：逆に面談を重ねるにつれて、選択肢を慎重に絞り込む傾向（約60% ➔ 44%）が見られました。
                        </div>
                    </div>
                    <div class="exec-item-highlight">
                        💡 後半になるほど企業の受入枠が広がる一方、学生は厳選する行動の推移が生じていました。
                    </div>
                </div>

                <!-- Point 4 -->
                <div class="exec-item-card">
                    <div>
                        <div class="exec-item-header">
                            <span class="exec-item-icon">🎯</span>
                            <div class="exec-item-title">事前診断の客観性と実効性</div>
                        </div>
                        <div class="exec-item-body">
                            イベント当日、企業も学生もお互いの診断スコアを一切知らない（見えない）ブラインド環境で面談を行っていました。<br>
                            それにもかかわらず、事前の診断スコアが高かったペアほど当日に高く評価し合い、実際にマッチングしていました。
                        </div>
                    </div>
                    <div class="exec-item-highlight">
                        💡 事前の診断スコアが、当日のリアルな対話や相性を先入観なく捉えていたことが窺えます。
                    </div>
                </div>
            </div>

            <div style="margin-top: 14px; font-size: 12px; color: var(--gray-500); text-align: right; display: flex; justify-content: flex-end; align-items: center; gap: 4px;">
                <span>※各項目の詳細な数値分布や統計分析モデルは、以下の各セクションでご確認いただけます。</span>
                <span>👇</span>
            </div>
        </div>

        <!-- Top KPI Cards: 基本統計量 (実測値) -->
        <div class="grid-3">
            <div class="kpi-card">
                <div class="kpi-title">バリューフィット度</div>
                <div class="kpi-value" style="margin-bottom: 10px;">
                    {fmt_num(kpi['value_fit']['mean'])}
                    <span style="font-size: 13px; font-weight: 600; color: var(--gray-500); margin-left: 4px;">(平均値)</span>
                </div>
                <div class="kpi-sub" style="display: flex; flex-direction: column; gap: 5px; border-top: 1px solid var(--gray-200); padding-top: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>中央値</span><strong>{fmt_num(kpi['value_fit']['median'])}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>標準偏差 (SD)</span><strong>±{fmt_num(kpi['value_fit']['std'])}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>実測範囲</span><strong>{fmt_num(kpi['value_fit']['min'])} 〜 {fmt_num(kpi['value_fit']['max'])}</strong>
                    </div>
                    <div style="font-size: 11px; color: var(--gray-400); text-align: right; margin-top: 2px;">
                        サンプル数: N={kpi['value_fit']['N']}
                    </div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">パーソナリティフィット度</div>
                <div class="kpi-value" style="margin-bottom: 10px;">
                    {fmt_num(kpi['personality_fit']['mean'])}
                    <span style="font-size: 13px; font-weight: 600; color: var(--gray-500); margin-left: 4px;">(平均値)</span>
                </div>
                <div class="kpi-sub" style="display: flex; flex-direction: column; gap: 5px; border-top: 1px solid var(--gray-200); padding-top: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>中央値</span><strong>{fmt_num(kpi['personality_fit']['median'])}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>標準偏差 (SD)</span><strong>±{fmt_num(kpi['personality_fit']['std'])}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>実測範囲</span><strong>{fmt_num(kpi['personality_fit']['min'])} 〜 {fmt_num(kpi['personality_fit']['max'])}</strong>
                    </div>
                    <div style="font-size: 11px; color: var(--gray-400); text-align: right; margin-top: 2px;">
                        サンプル数: N={kpi['personality_fit']['N']}
                    </div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">マッチング成立率（全体）</div>
                <div class="kpi-value" style="color: var(--success); margin-bottom: 10px;">
                    {fmt_pct(kpi['matching']['matched_all_pct'])}
                    <span style="font-size: 13px; font-weight: 600; color: var(--gray-500); margin-left: 4px;">(成立率)</span>
                </div>
                <div class="kpi-sub" style="display: flex; flex-direction: column; gap: 5px; border-top: 1px solid var(--gray-200); padding-top: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>成立数</span><strong>{kpi['matching']['matched_all']} 件</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>総ペア数</span><strong>{kpi['matching']['N_all']} 件</strong>
                    </div>
                    <div style="margin-top: 6px; font-size: 11px; color: var(--gray-500); line-height: 1.3;">
                        ※パーソナリティ有効ペア: {fmt_pct(kpi['matching']['matched_pers_pct'])} ({kpi['matching']['matched_pers']}/{kpi['matching']['N_pers']}件)
                    </div>
                </div>
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
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(10名限定)</span>
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
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(上限なし)</span>
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
                    <li><strong>企業側</strong>：バリューフィット度平均は「なし（{fmt_num(ov_act['company']['three_cats'][0]['v_mean'])}）」から「知りたい（{fmt_num(ov_act['company']['three_cats'][1]['v_mean'])}）」、「めっちゃ知りたい（{fmt_num(ov_act['company']['three_cats'][2]['v_mean'])}）」へと数値が高くなっています（差 +{fmt_num(ov_act['company']['three_cats'][2]['v_mean'] - ov_act['company']['three_cats'][0]['v_mean'])}pt）。一方、パーソナリティフィット度平均は {fmt_num(min(x['p_mean'] for x in ov_act['company']['three_cats']))} 〜 {fmt_num(max(x['p_mean'] for x in ov_act['company']['three_cats']))} の間でほぼ同等です。</li>
                    <li><strong>学生側</strong>：パーソナリティフィット度平均は「なし（{fmt_num(ov_act['student']['three_cats'][0]['p_mean'])}）」から「知りたい（{fmt_num(ov_act['student']['three_cats'][1]['p_mean'])}）」、「めっちゃ知りたい（{fmt_num(ov_act['student']['three_cats'][2]['p_mean'])}）」へと数値が高くなっています（差 +{fmt_num(ov_act['student']['three_cats'][2]['p_mean'] - ov_act['student']['three_cats'][0]['p_mean'])}pt）。バリューフィット度平均は {fmt_num(min(x['v_mean'] for x in ov_act['student']['three_cats']))} 〜 {fmt_num(max(x['v_mean'] for x in ov_act['student']['three_cats']))} の範囲で推移しています。</li>
                    <li><strong>2値（なし vs 知りたい以上）</strong>：企業は全体の {fmt_pct(ov_act['company']['binary'][1]['pct'])}（{ov_act['company']['binary'][1]['count']}件）、学生は {fmt_pct(ov_act['student']['binary'][1]['pct'])}（{ov_act['student']['binary'][1]['count']}件）が「知りたい以上」のアクションを選択しています。</li>
                </ul>
            </div>
                    <div style="font-size: 11.5px; color: var(--gray-500); margin-top: 10px; line-height: 1.5; background: #F8FAFC; border: 1px solid var(--gray-200); border-radius: 6px; padding: 8px 12px;">
                ※ <strong>アクション区分「なし」の集計定義</strong>：CSV上の「知りたいを選択せず」および「未回答」を合算しています。企業側の未回答（45件）の84%はパナソニックOE（20件）およびUnith Link（18件）の未入力運用によるもの、学生側の未回答（43件）も全6ターン未提出者等を含む実態ベースの「アクションなし」として一貫して処理しています。
            </div>
        </div>

        <!-- Section 2: アクション選択の要因分析（要点まとめ ＆ 詳細モデル） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🎯 【要因分析】スコアがアクション選択に与える影響（要点まとめ ＆ 詳細モデル）</div>
                    <div class="section-desc">時間経過（ターン数）および企業間差（企業固定効果）を統制したアクション選択要因分析（N=286）</div>
                </div>
                <span class="pill pill-indigo">時間・企業統制ロジット回帰</span>
            </div>

            <!-- 前面：直感的な要点まとめ（表 ＆ 視覚化グラフ） -->
            <div class="grid-2" style="margin-bottom: 20px;">
                <!-- 左：要点まとめ表 -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📋 スコア10pt上昇・ターン進行時のアクション選択への影響（時間・企業統制モデル）</h3>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 24%;">評価要因</th>
                                    <th style="width: 38%;">🏢 企業側の選択への影響</th>
                                    <th style="width: 38%;">🎓 学生側の選択への影響</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="background: var(--primary-light);">
                                    <td><strong>バリュー<br>フィット度</strong><br><span style="font-size: 10px; color: var(--gray-500);">(10pt上昇)</span></td>
                                    <td>
                                        <strong style="color: var(--primary); font-size: 14px;">約 1.8 〜 1.9 倍</strong><br>
                                        <span class="pill pill-indigo" style="font-size: 10px; margin-top: 3px;">有意 (**)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>1.93倍**</strong>（p=0.0040）、めっちゃ知りたいで <strong>1.84倍**</strong>（p=0.0042）。企業の選択確率が有意に上昇。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: var(--gray-600); font-size: 14px;">約 1.0 〜 1.3 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">有意差なし</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>1.32倍</strong>（p=0.1140）、めっちゃ知りたいで <strong>1.05倍</strong>（p=0.8537）。企業間差統制後は統計的有意差なし。
                                        </div>
                                    </td>
                                </tr>
                                <tr style="background: #FAF5FF;">
                                    <td><strong>パーソナリティ<br>フィット度</strong><br><span style="font-size: 10px; color: var(--gray-500);">(10pt上昇)</span></td>
                                    <td>
                                        <strong style="color: var(--gray-500); font-size: 14px;">約 0.8 〜 1.2 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">有意差なし</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>1.18倍</strong>（p=0.4279）、めっちゃ知りたいで <strong>0.83倍</strong>（p=0.3266）。企業の選択確率への統計的影響なし。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: #7E22CE; font-size: 14px;">約 1.4 〜 1.5 倍</strong><br>
                                        <span class="pill pill-indigo" style="font-size: 10px; margin-top: 3px;">有意 (*)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>1.51倍*</strong>（p=0.0136）、めっちゃ知りたいで <strong>1.42倍</strong>（p=0.1948）。同一企業内での選択確率が有意に上昇。
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>時間経過要因<br>(ターン番号)</strong><br><span style="font-size: 10px; color: var(--gray-500);">(1ターン進行ごと)</span></td>
                                    <td>
                                        <strong style="color: var(--primary); font-size: 13.5px;">約 1.33 倍</strong><br>
                                        <span class="pill pill-indigo" style="font-size: 10px; margin-top: 3px;">有意 (**)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            1ターン進行ごとに選択オッズが <strong>1.33倍**</strong>（p=0.0043）上昇。後半ターンほど選択率が高い実態。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: #DC2626; font-size: 13.5px;">約 0.83 倍</strong><br>
                                        <span class="pill pill-red" style="font-size: 10px; margin-top: 3px;">有意 (*)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            1ターン進行ごとに選択オッズが <strong>0.83倍*</strong>（p=0.0117）低下。後半ターンほど選択率が低い実態。
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※時間経過（ターン数：1〜6）および企業間差（企業固定効果：企業ダミー10社）を同時統制したロジスティック回帰（N=286）に基づくオッズ比（OR）。
                    </div>
                </div>

                <!-- 右：視覚的インパクトグラフ -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📊 10pt上昇時の選択率インパクト比較（時間・企業統制モデル）</h3>
                    <div class="chart-box" style="height: 270px;">
                        <canvas id="chart-logit-impact"></canvas>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※赤線（1.0倍）より右に大きく伸びるほど、そのスコアの上昇が選択確率に強いプラス効果を与えていることを表します。
                    </div>
                </div>
            </div>

            <!-- 専門的な詳細アコーディオン -->
            <details class="stats-details">
                <summary class="stats-summary">
                    <span>📊 時間統制 ＋ 企業統制ロジスティック回帰の統計詳細（回帰係数β・標準誤差・95%信頼区間・p値）を展開する</span>
                    <span class="pill pill-indigo">クリックで開閉</span>
                </summary>
                <div class="stats-content">
                    <!-- 企業回帰 -->
                    <div style="margin-bottom: 24px;">
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 企業アクション選択に対するロジスティック回帰詳細 (N=286：時間・企業統制モデル)</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 25%;">目的変数 / 説明変数</th>
                                        <th style="width: 15%;">回帰係数 (β)</th>
                                        <th style="width: 15%;">標準誤差 (SE)</th>
                                        <th style="width: 22%;">オッズ比 [95%CI]</th>
                                        <th style="width: 13%;">p値</th>
                                        <th style="width: 10%;">判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="6" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【モデル①】知りたい以上（知りたい ＋ めっちゃ知りたい）選択モデル (N=286, 選択件数=209件)</td>
                                    </tr>
                                    <tr style="background: var(--primary-light);">
                                        <td><strong>バリューフィット度 (10pt)</strong></td>
                                        <td>+0.0658</td>
                                        <td>0.0229</td>
                                        <td><strong>OR 1.931</strong><br><span style="font-size: 10px;">[1.233〜3.025]</span></td>
                                        <td>p = 0.0040 (**)</td>
                                        <td><span class="pill pill-green">有意 (**)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度 (10pt)</strong></td>
                                        <td>+0.0166</td>
                                        <td>0.0209</td>
                                        <td>OR 1.181<br><span style="font-size: 10px;">[0.784〜1.778]</span></td>
                                        <td>p = 0.4279</td>
                                        <td><span class="pill pill-slate">有意差なし</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>ターン番号 (1ターン進行ごと)</strong></td>
                                        <td>+0.2882</td>
                                        <td>0.1009</td>
                                        <td><strong>OR 1.334</strong><br><span style="font-size: 10px;">[1.095〜1.626]</span></td>
                                        <td>p = 0.0043 (**)</td>
                                        <td><span class="pill pill-indigo">有意 (**)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>企業固定効果 (企業ダミー10社)</strong></td>
                                        <td colspan="4" style="font-size: 11px; color: var(--gray-600);">全11社中10社の個別ダミー変数を同時投入し、各社の選考基準の甘辛を統制</td>
                                        <td><span class="pill pill-indigo">統制済み</span></td>
                                    </tr>

                                    <tr style="background: #F8FAFC;">
                                        <td colspan="6" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【モデル②】めっちゃ知りたい（最上位アクション）選択モデル (N=286, 選択件数=71件)</td>
                                    </tr>
                                    <tr style="background: var(--primary-light);">
                                        <td><strong>バリューフィット度 (10pt)</strong></td>
                                        <td>+0.0608</td>
                                        <td>0.0212</td>
                                        <td><strong>OR 1.837</strong><br><span style="font-size: 10px;">[1.212〜2.783]</span></td>
                                        <td>p = 0.0042 (**)</td>
                                        <td><span class="pill pill-green">有意 (**)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度 (10pt)</strong></td>
                                        <td>-0.0185</td>
                                        <td>0.0189</td>
                                        <td>OR 0.831<br><span style="font-size: 10px;">[0.574〜1.204]</span></td>
                                        <td>p = 0.3266</td>
                                        <td><span class="pill pill-slate">有意差なし</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>ターン番号 (1ターン進行ごと)</strong></td>
                                        <td>+0.1600</td>
                                        <td>0.0863</td>
                                        <td>OR 1.174<br><span style="font-size: 10px;">[0.991〜1.390]</span></td>
                                        <td>p = 0.0639</td>
                                        <td><span class="pill pill-amber">有意傾向 (†)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>企業固定効果 (企業ダミー10社)</strong></td>
                                        <td colspan="4" style="font-size: 11px; color: var(--gray-600);">全11社中10社の個別ダミー変数を同時投入し、各社の選考基準の甘辛を統制</td>
                                        <td><span class="pill pill-indigo">統制済み</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 学生回帰 -->
                    <div>
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🎓 学生アクション選択に対するロジスティック回帰詳細 (N=286：時間・企業統制モデル)</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 25%;">目的変数 / 説明変数</th>
                                        <th style="width: 15%;">回帰係数 (β)</th>
                                        <th style="width: 15%;">標準誤差 (SE)</th>
                                        <th style="width: 22%;">オッズ比 [95%CI]</th>
                                        <th style="width: 13%;">p値</th>
                                        <th style="width: 10%;">判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="6" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【モデル①】知りたい以上（知りたい ＋ めっちゃ知りたい）選択モデル (N=286, 選択件数=153件)</td>
                                    </tr>
                                    <tr style="background: #FAF5FF;">
                                        <td><strong>パーソナリティフィット度 (10pt)</strong></td>
                                        <td>+0.0412</td>
                                        <td>0.0167</td>
                                        <td><strong>OR 1.510</strong><br><span style="font-size: 10px;">[1.088〜2.095]</span></td>
                                        <td>p = 0.0136 (*)</td>
                                        <td><span class="pill pill-green">有意 (*)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度 (10pt)</strong></td>
                                        <td>+0.0276</td>
                                        <td>0.0175</td>
                                        <td>OR 1.318<br><span style="font-size: 10px;">[0.935〜1.857]</span></td>
                                        <td>p = 0.1140</td>
                                        <td><span class="pill pill-slate">有意差なし</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>ターン番号 (1ターン進行ごと)</strong></td>
                                        <td>-0.1903</td>
                                        <td>0.0755</td>
                                        <td><strong>OR 0.827</strong><br><span style="font-size: 10px;">[0.713〜0.959]</span></td>
                                        <td>p = 0.0117 (*)</td>
                                        <td><span class="pill pill-red">有意 (*)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>企業固定効果 (企業ダミー10社)</strong></td>
                                        <td colspan="4" style="font-size: 11px; color: var(--gray-600);">全11社中10社の個別ダミー変数を同時投入し、各社の知名度・人気差を統制</td>
                                        <td><span class="pill pill-indigo">統制済み</span></td>
                                    </tr>

                                    <tr style="background: #F8FAFC;">
                                        <td colspan="6" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【モデル②】めっちゃ知りたい（最上位アクション）選択モデル (N=286, 選択件数=33件)</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度 (10pt)</strong></td>
                                        <td>+0.0351</td>
                                        <td>0.0271</td>
                                        <td>OR 1.420<br><span style="font-size: 10px;">[0.835〜2.416]</span></td>
                                        <td>p = 0.1948</td>
                                        <td><span class="pill pill-slate">有意差なし</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度 (10pt)</strong></td>
                                        <td>+0.0047</td>
                                        <td>0.0257</td>
                                        <td>OR 1.048<br><span style="font-size: 10px;">[0.633〜1.735]</span></td>
                                        <td>p = 0.8537</td>
                                        <td><span class="pill pill-slate">有意差なし</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>ターン番号 (1ターン進行ごと)</strong></td>
                                        <td>+0.0570</td>
                                        <td>0.1170</td>
                                        <td>OR 1.059<br><span style="font-size: 10px;">[0.842〜1.332]</span></td>
                                        <td>p = 0.6262</td>
                                        <td><span class="pill pill-slate">有意差なし</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>企業固定効果 (企業ダミー10社)</strong></td>
                                        <td colspan="4" style="font-size: 11px; color: var(--gray-600);">全11社中10社の個別ダミー変数を同時投入し、各社の知名度・人気差を統制</td>
                                        <td><span class="pill pill-indigo">統制済み</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 客観的留意点カード（事実ベース） -->
                    <div style="margin-top: 16px; padding-top: 14px; border-top: 1px dashed var(--gray-300);">
                        <h4 style="font-size: 13.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                            <span>💡</span> 統計モデル・データ構造に関する客観的事実
                        </h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <!-- ③ サンプル構造と企業固定効果 -->
                            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px 14px; font-size: 12px; color: #166534; line-height: 1.6;">
                                <strong style="color: #15803D; font-size: 12.5px; display: block; margin-bottom: 4px;">
                                    🔍 【サンプル構造】企業固定効果投入による推計値の変化実態
                                </strong>
                                企業間差を考慮しないプール回帰では、学生側のバリューオッズ比が 1.38倍（p = 0.0463*）と有意に出ていましたが、企業固定効果を投入すると 1.32倍（p = 0.1140）となり有意差が消失します。これは学生のバリュー選択が「企業全体の知名度や人気差」と相関していたためであり、同一企業内での個人比較においては、パーソナリティフィット度（OR 1.510*, p = 0.0136*）が選択確率に有意に寄与している実態が確認されます。
                            </div>

                            <!-- ② ブラインド環境下での実証性 -->
                            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 12px 14px; font-size: 12px; color: #1E40AF; line-height: 1.6;">
                                <strong style="color: #1D4ED8; font-size: 12.5px; display: block; margin-bottom: 4px;">
                                    💡 【実証環境】スコア非閲覧（ブラインド環境）下での意思決定
                                </strong>
                                イベント当日、企業側および学生側は自他のフィット度スコア（数値）を閲覧できない状態で面談およびアクション選択を行いました。この条件下において、企業側のアクションはバリューフィット度と統計的有意に連動（OR 1.931**）し、学生側のアクションはパーソナリティフィット度と統計的有意に連動（OR 1.510*）する結果が得られています。
                            </div>
                        </div>

                        <!-- ④ ターン進行推移実態 -->
                        <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 12px 14px; font-size: 12px; color: #92400E; line-height: 1.6; margin-top: 10px;">
                            <strong style="color: #B45309; font-size: 12.5px; display: block; margin-bottom: 4px;">
                                ⏱️ 【推移実態】ターン進行（時間経過）に伴う選択率の変動データ
                            </strong>
                            面談ターンの進行に伴い、企業側と学生側で統計的に有意な異なる推移が記録されています。<strong>企業側の選択率（知りたい以上）は第1〜2ターンの58.8%から第6ターンには77.2%へと推移（1ターンあたり OR 1.334**, p = 0.0043**）</strong>する一方、<strong>学生側の選択率は第1〜2ターンの60%台から第6ターンには43.9%へと推移（1ターンあたり OR 0.827*, p = 0.0117*、未回答率は倍増）</strong>しました。本モデルではこれら時間経過の変動量を説明変数として投入し、スコア本来の寄与度を統制推計しています。
                        </div>
                    </div>
                </div>
            </details>

            <div class="summary-box">
                <strong class="title">📝 データまとめ（回帰分析結果の客観的事実 ＆ 実態ストーリー）:</strong>
                <ul>
                    <li><strong>客観的事実（企業側）</strong>：時間経過および企業固定効果を統制したモデルにおいて、バリューフィット度の上昇に伴い「知りたい以上」の選択オッズ比が <strong>OR 1.931</strong>（p = 0.0040**）、「めっちゃ知りたい」が <strong>OR 1.837</strong>（p = 0.0042**）と統計的有意に高くなっています。またターン進行に伴い選択確率が有意に上昇（1ターンあたり <strong>OR 1.334</strong>, p = 0.0043**）しています。パーソナリティフィット度の上昇に伴う有意差は認められません（OR 1.181, p = 0.4279）。</li>
                    <li><strong>客観的事実（学生側）</strong>：時間経過および企業固定効果を統制した同一企業内比較において、パーソナリティフィット度の上昇に伴い「知りたい以上」の選択オッズ比が <strong>OR 1.510</strong>（p = 0.0136*）と統計的有意に高くなっています。またターン進行に伴い選択確率は有意に低下（1ターンあたり <strong>OR 0.827</strong>, p = 0.0117*）しています。企業間差統制後のバリューフィット度の上昇に伴う有意差は認められません（OR 1.318, p = 0.1140）。</li>
                    <li><strong>実態把握から導かれるストーリー（両面マッチングの成立構造）</strong>：
                        本分析の実態から、<strong>企業側は「自社のカルチャー・理念への合致（バリューフィット度）」を重視して学生を選択</strong>し、<strong>学生側は「ブースでの実際の対話を通じた相性や自分らしさ（パーソナリティフィット度）」を重視して企業を選択</strong>していたことが明確に裏付けられます。後半ターンにおける行動推移（企業は選択枠を拡大し、学生は選択を絞り込む実態）を統制しても、この「企業＝バリュー」「学生＝パーソナリティ」という評価軸の分担傾向が安定して見られます。その結果、次セクション（Section 3）で示される通り、<strong>双方が揃ったペアにおいてマッチング成立（PF: OR 1.723**, バリュー: OR 1.651**）へと結実しやすい</strong>という、両面市場としての実態構造が統計的にも示唆されています。
                    </li>
                </ul>
            </div>

        </div>

        <!-- Section 3: マッチング成立の要因分析（要点まとめ ＆ 詳細モデル） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">⚖️ 【成果分析】マッチング成立の要因分析（要点まとめ ＆ 詳細モデル）</div>
                    <div class="section-desc">バリューフィット度、パーソナリティフィット度、および時間経過・企業間差がマッチング成否に与える影響（N=286）</div>
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

                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 右：要点まとめ表 -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">📋 マッチング成立への各要因の要約（時間・企業統制モデル）</h3>
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
                                <tr style="background: #FAF5FF;">
                                    <td><strong>パーソナリティ</strong><br><span style="font-size: 10px; color: var(--gray-500);">(10pt上昇)</span></td>
                                    <td><strong style="color: #7E22CE; font-size: 13.5px;">約 1.72 倍</strong><br><span class="pill pill-indigo" style="font-size: 10px;">有意 (**)</span></td>
                                    <td style="font-size: 11px;">時間・企業差を統制した同一企業内比較で<strong>成立を大きく後押しする重要因子</strong>（p=0.0028**）。</td>
                                </tr>
                                <tr style="background: var(--primary-light);">
                                    <td><strong>バリューフィット度</strong><br><span style="font-size: 10px; color: var(--gray-500);">(10pt上昇)</span></td>
                                    <td><strong style="color: var(--primary); font-size: 13.5px;">約 1.65 倍</strong><br><span class="pill pill-indigo" style="font-size: 10px;">有意 (**)</span></td>
                                    <td style="font-size: 11px;">パーソナリティと並ぶ重要因子（p=0.0073**）。自社の価値観に合う学生ほどマッチしやすい傾向。</td>
                                </tr>
                                <tr>
                                    <td><strong>時間経過要因 (ターン)</strong><br><span style="font-size: 10px; color: var(--gray-500);">(第1〜第6ターン)</span></td>
                                    <td><span style="color: var(--gray-600); font-size: 12.5px;">約 0.96 倍</span><br><span class="pill pill-slate" style="font-size: 10px;">中立 (影響なし)</span></td>
                                    <td style="font-size: 11px;">時間帯（疲労や焦り）を統制しても、マッチング成否には中立（p=0.5683）でスコア効果は不変。</td>
                                </tr>
                                <tr>
                                    <td><strong>企業間ベース差</strong><br><span style="font-size: 10px; color: var(--gray-500);">(人気・選考基準)</span></td>
                                    <td><span style="color: var(--gray-600); font-size: 12.5px;">全社統制</span><br><span class="pill pill-green" style="font-size: 10px;">固定効果</span></td>
                                    <td style="font-size: 11px;">各社の人気や選考基準の甘辛を補正し、<strong>同一企業内での相性傾向</strong>を抽出。</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- 専門的な詳細アコーディオン -->
            <details class="stats-details">
                <summary class="stats-summary">
                    <span>📊 時間統制 ＋ 企業統制ロジスティック回帰の統計詳細（回帰係数β・標準誤差・95%信頼区間・p値）を展開する</span>
                    <span class="pill pill-green">クリックで開閉</span>
                </summary>
                <div class="stats-content">
                    <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">時間統制 ＋ 企業統制ロジスティック回帰分析結果 (N=286：同一企業内比較モデル)</h3>
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
                                <tr style="background: #FAF5FF;">
                                    <td><strong>パーソナリティフィット度 (10pt)</strong></td>
                                    <td>+0.0544</td>
                                    <td>0.0182</td>
                                    <td><strong>OR 1.723</strong><br><span style="font-size: 10px;">[1.206〜2.462]</span></td>
                                    <td>p = 0.0028 (**)</td>
                                    <td><span class="pill pill-green">有意 (**)</span></td>
                                </tr>
                                <tr style="background: var(--primary-light);">
                                    <td><strong>バリューフィット度 (10pt)</strong></td>
                                    <td>+0.0501</td>
                                    <td>0.0187</td>
                                    <td><strong>OR 1.651</strong><br><span style="font-size: 10px;">[1.145〜2.381]</span></td>
                                    <td>p = 0.0073 (**)</td>
                                    <td><span class="pill pill-green">有意 (**)</span></td>
                                </tr>
                                <tr>
                                    <td><strong>ターン番号 (1ターン進行ごと)</strong></td>
                                    <td>-0.0455</td>
                                    <td>0.0798</td>
                                    <td>OR 0.955<br><span style="font-size: 10px;">[0.817〜1.117]</span></td>
                                    <td>p = 0.5683</td>
                                    <td><span class="pill pill-slate">中立</span></td>
                                </tr>
                                <tr>
                                    <td><strong>企業固定効果 (企業ダミー10社)</strong></td>
                                    <td colspan="4" style="font-size: 11px; color: var(--gray-600);">全11社中10社の個別ダミー変数を同時投入し、各社の人気・選考基準の甘辛を統計的に統制</td>
                                    <td><span class="pill pill-indigo">統制済み</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- モデル比較と学術的インサイト -->
                    <div style="margin-top: 16px; padding-top: 14px; border-top: 1px dashed var(--gray-300);">
                        <div style="background: #FAF5FF; border: 1px solid #E9D5FF; border-radius: 8px; padding: 14px 16px; font-size: 12px; color: #6B21A8; line-height: 1.6;">
                            <h4 style="font-size: 13.5px; font-weight: 800; color: #7E22CE; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                                <span>🏆</span> 【重要：同一企業内比較の実証結果】全体一括集計から何が変わったのか？
                            </h4>
                            <p>全体一括集計（企業差を考慮しないプール回帰）では、パーソナリティフィット度のオッズ比は <strong>1.34倍</strong>（p = 0.0518†：有意傾向）にとどまっていました。これは「性格スコア低めの企業（とものや・Linoa・アイプラス等）が学生に大人気だった」という企業人気差（シンプソンのパラドックス）に隠れていたためです。</p>
                            <p style="margin-top: 6px;">今回、時間経過（ターン数）と企業間差（企業固定効果）を統制したモデルで見ると、<strong>パーソナリティフィット度のオッズ比は 1.72倍（p = 0.0028**：1%水準で有意）へと高まり、バリューフィット度（1.65倍, p = 0.0073**）と並んでマッチング成立を大きく左右する重要因子である可能性</strong>が統計的にも示唆されます。</p>
                        </div>
                    </div>
                </div>
            </details>

            <div class="summary-box">
                <strong class="title">📝 データまとめ（マッチング成立要因の客観的事実）:</strong>
                <ul>
                    <li>マッチング成立群（N={match_comp['matched_count']}）は未成立群（N={match_comp['unmatched_count']}）に比べ、バリューフィット度平均が <strong>+{fmt_num(match_comp['matched_v_mean'] - match_comp['unmatched_v_mean'])} pt</strong>（成立 {fmt_num(match_comp['matched_v_mean'])} vs 未成立 {fmt_num(match_comp['unmatched_v_mean'])}）、パーソナリティフィット度平均が <strong>+{fmt_num(match_comp['matched_p_mean'] - match_comp['unmatched_p_mean'])} pt</strong>（成立 {fmt_num(match_comp['matched_p_mean'])} vs 未成立 {fmt_num(match_comp['unmatched_p_mean'])}）高くなっています。</li>
                    <li>時間経過（ターン数）および企業間差（企業固定効果）を統計的に統制した最高精度のロジスティック回帰（N={match_comp['N_valid']}）において、パーソナリティフィット度（10ptあたり <strong>OR 1.72</strong>, p = 0.0028**）およびバリューフィット度（10ptあたり <strong>OR 1.65</strong>, p = 0.0073**）の<strong>双方が1%有意水準（p &lt; 0.01**）でマッチング成立に極めて強く寄与</strong>しています。時間経過（ターン番号 OR 0.96, p = 0.5683）は成立成否には中立であり、時間を統制しても両スコアの重要性は堅牢に維持される傾向が窺えます。</li>
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
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid var(--primary); border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; font-size: 13px; color: var(--gray-700); line-height: 1.6;">
                    <div style="font-weight: 700; color: var(--gray-900); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                        <span>💡</span> <strong>各セルの数値の見方:</strong>
                    </div>
                    <div>
                        ・<strong>上の大きなパーセント（例: 61.2%）</strong>：その枠（バリュー水準 × パーソナリティ水準）における <strong>マッチング成立率</strong> です。<br>
                        ・<strong>下の件数表示（例: 成立 30/49件）</strong>：<strong>マッチング成立ペア数（分子）／ その枠に該当する総面談ペア数（分母）</strong> を表しています。<br>
                        <span style="font-size: 11.5px; color: var(--gray-500);">※全9枠の分母（総ペア数）を合算すると、パーソナリティ有効ペア全数 286件（成立全数 121件、全体成立率 42.3%）になります。</span>
                    </div>
                </div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th style="width: 22%; background: var(--gray-100);">パーソナリティ（縦軸） ＼ バリュー（横軸）</th>
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
                <!-- 表① 統計的仮説検定アコーディオン -->
                <details class="stats-details" style="margin-top: 14px;">
                    <summary class="stats-summary">
                        <span>📊 ① マッチング成立率 3×3マトリクスの統計的検定結果（カイ二乗検定 / 自由度 / p値）</span>
                        <span class="pill pill-indigo">クリックで開閉</span>
                    </summary>
                    <div class="stats-content">
                        <div style="font-weight: 700; color: #1E293B; margin-bottom: 8px; font-size: 13px;">
                            📈 マッチング成否（成立 121件 vs 不成立 165件）に対する統計的独立性検定 (N=286)
                        </div>
                        <div class="table-container" style="margin-bottom: 12px;">
                            <table>
                                <thead>
                                    <tr>
                                        <th style="width: 30%;">検証スコープ</th>
                                        <th style="width: 22%;">検定手法</th>
                                        <th style="width: 18%;">検定統計量 (χ²)</th>
                                        <th style="width: 10%;">自由度 (df)</th>
                                        <th style="width: 10%;">p値</th>
                                        <th style="width: 10%;">判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: var(--primary-light);">
                                        <td><strong>3×3マトリクス全体 (9セル比較)</strong></td>
                                        <td>カイ二乗検定 (9×2 分割表)</td>
                                        <td>χ² = 23.6565</td>
                                        <td>df = 8</td>
                                        <td><strong>p = 0.0026</strong></td>
                                        <td><span class="pill pill-indigo">非常に有意 (**)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>横軸：バリュー水準別 (低・中・高)</strong></td>
                                        <td>カイ二乗検定 (3×2 分割表)</td>
                                        <td>χ² = 19.5630</td>
                                        <td>df = 2</td>
                                        <td><strong>p &lt; 0.0001</strong></td>
                                        <td><span class="pill pill-indigo">極めて有意 (***)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>縦軸：パーソナリティ水準別 (低・中・高)</strong></td>
                                        <td>カイ二乗検定 (3×2 分割表)</td>
                                        <td>χ² = 4.2343</td>
                                        <td>df = 2</td>
                                        <td>p = 0.1204</td>
                                        <td><span class="pill pill-slate">有意差なし ※</span></td>
                                    </tr>
                                    <tr style="background: #FEF3C7;">
                                        <td><strong>最高セル vs 最低セル の直接比較</strong><br><span style="font-size: 11px; color: var(--gray-500);">(高×高: 61.2% vs 低×低: 18.9%)</span></td>
                                        <td>カイ二乗検定 (2×2, イェーツ補正)</td>
                                        <td>χ² = 13.7145<br><span style="font-size: 11px; color: var(--gray-500);">(オッズ比 6.77倍)</span></td>
                                        <td>df = 1</td>
                                        <td><strong>p = 0.0002</strong></td>
                                        <td><span class="pill pill-amber">極めて有意 (***)</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div style="font-size: 12px; color: var(--gray-600); line-height: 1.6; background: #F8FAFC; padding: 10px 14px; border-radius: 6px; border: 1px solid var(--gray-200);">
                            <strong>💡 統計的考察:</strong><br>
                            ・<strong>マトリクス全体の有意性 (p = 0.0026**)</strong>：9つのセルにおける成立率の差（18.9%〜61.2%）は偶然によるばらつきではなく、2つのスコアの配置によって有意に変動していることが示唆されます。<br>
                            ・<strong>バリューの強い主効果 (p &lt; 0.0001***)</strong>：バリューが低(28.7%) ➔ 中(36.6%) ➔ 高(58.2%) と上がるにつれ成立率が劇的に上昇しています。<br>
                            ・<strong>最高 vs 最低のオッズ比 6.77倍 (p = 0.0002***)</strong>：両スコアが高い組み合わせは、両スコアが低い組み合わせに比べてマッチング成立オッズが約6.8倍高く、統計的にも極めて顕著な差が認められます。<br>
                            <span style="font-size: 11px; color: var(--gray-500);">※全体一括集計ではパーソナリティ単独の検定で有意差が出にくい（p=0.1204）背景には企業人気差の交絡があり、Section 3で示した企業固定効果モデルによって企業差を統制すると、パーソナリティもマッチング成立に有意（OR 1.723**）に寄与していることが明らかになっています。</span>
                        </div>
                    </div>
                </details>
            </div>

            <!-- ② 企業アクション 3x3 マトリクス (横幅いっぱい・広々スペース) -->
            <div class="sub-card" style="margin-bottom: 28px;">
                <h3 style="font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 6px;">🏢 ② 【企業アクション】3×3 推移マトリクス (実数値 ＆ %)</h3>
                <div style="font-size: 12.5px; color: var(--gray-500); margin-bottom: 12px;">
                    バリュー水準の上昇に伴い、企業の「知りたい以上」および「めっちゃ知りたい」がどのセルで跳ね上がるかの全容実態
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid var(--primary); border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; font-size: 13px; color: var(--gray-700); line-height: 1.6;">
                    <div style="font-weight: 700; color: var(--gray-900); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                        <span>💡</span> <strong>各セルの数値の見方 ＆ 読み取れる実態:</strong>
                    </div>
                    <div>
                        ・<strong>知りたい以上</strong>：その枠の中で、企業が学生に対して「知りたい」または「めっちゃ知りたい」を選択した件数と割合（関心度）です。<br>
                        ・<strong>内訳（知りたい／めっちゃ知りたい）</strong>：より強い関心である「めっちゃ知りたい」がどの条件で増えるかを示しています。<br>
                        ・<strong>注目の実態</strong>：バリュー（横軸）が高くなるにつれ、「めっちゃ知りたい」が <strong>10%台 ➔ 最大45.9% へと急増</strong> しており、企業がカルチャー合致（価値観）を主軸に選別していた傾向が明確に表れています。<br>
                        <span style="font-size: 11.5px; color: var(--gray-500);">※マッチング成立（表①）は、この企業選択と次の学生選択（表③）の双方が合致した時にのみ成立します。</span>
                    </div>
                </div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th style="width: 22%; background: var(--gray-100);">パーソナリティ（縦軸） ＼ バリュー（横軸）</th>
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
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #10B981; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; font-size: 13px; color: var(--gray-700); line-height: 1.6;">
                    <div style="font-weight: 700; color: var(--gray-900); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                        <span>💡</span> <strong>各セルの数値の見方 ＆ 読み取れる実態:</strong>
                    </div>
                    <div>
                        ・<strong>知りたい以上</strong>：その枠の中で、学生が企業に対して「知りたい」または「めっちゃ知りたい」を選択した件数と割合です。<br>
                        ・<strong>注目の実態</strong>：学生の「めっちゃ知りたい」は全体的に 6〜19% と厳選傾向ですが、<strong>バリュー高かつパーソナリティ中〜高の枠で「知りたい以上」が約67%と最高水準</strong> に達しています。<br>
                        ・<strong>表①との関係</strong>：学生が最も前向きになる右上の枠（バリュー高×パーソナリティ高）において、企業の高い関心（表②）と合致し、<strong>表①のマッチング成立率が最高（61.2%）</strong> に達しています。<br>
                        <span style="font-size: 11.5px; color: var(--gray-500);">※企業と学生で重視する軸が異なるため、双方が高水準で揃うことがマッチング成立の鍵となります。</span>
                    </div>
                </div>
                <div class="table-container">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th style="width: 22%; background: var(--gray-100);">パーソナリティ（縦軸） ＼ バリュー（横軸）</th>
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
            
            <p><strong>1. 企業と学生におけるアクション選択傾向の相違（両面市場の実態）:</strong><br>
            時間経過（ターン数）および企業間差（企業固定効果）を統計的に統制したモデル（N=286）により、企業側と学生側で評価軸の明確な役割分担が存在した実態が浮き彫りとなりました。<br>
            ・<strong>企業側</strong>：バリューフィット度スコアに強く連動してアクションを選択しており、10pt上昇に伴い「知りたい以上」の選択オッズが <strong>1.93倍**</strong>（p = 0.0040）、「めっちゃ知りたい」が <strong>1.84倍**</strong>（p = 0.0042）へと上昇します（パーソナリティには有意差なし）。企業は自社のカルチャーや理念への合致度を主たる判断基準としていた傾向が窺えます。<br>
            ・<strong>学生側</strong>：同一企業内での比較において、パーソナリティフィット度スコアの上昇に伴い「知りたい以上」の選択オッズが <strong>1.51倍*</strong>（p = 0.0136）へと有意に上昇します。学生はブースでの対話を通じた相性や自分らしさを肌で感じ取って意思決定を行っていた傾向が示唆されます。</p>
            
            <p><strong>2. 時間経過（ターン進行）と企業間差（シンプソンのパラドックス）がもたらした影響:</strong><br>
            ・<strong>時間経過の影響</strong>：面談ターンの進行に伴い、企業側は選択枠を広げる推移（1ターンあたり <strong>OR 1.334**</strong>：選択率 58.8% ➔ 77.2%）を示す一方、学生側は疲労等の影響により選択を絞る推移（1ターンあたり <strong>OR 0.827*</strong>：選択率 60%台 ➔ 43.9%）を示しました。この逆方向の行動推移を時間変数として統制することで、スコア本来の寄与度がクリアに抽出されました。<br>
            ・<strong>企業間差の補正（シンプソンのパラドックスの解消）</strong>：全体一括集計ではパーソナリティの寄与が目立たなかった背景には、「性格スコアが控えめな一部企業に学生人気が集中した」という企業人気差が存在していました。企業固定効果により企業ごとのベース差を補正したことで、マッチング成立におけるパーソナリティの重要性が <strong>OR 1.72倍**</strong>（バリュー OR 1.65倍**）へと明確に浮かび上がりました。</p>

            <p><strong>3. マッチング成立の要因と次回イベント配席設計へのデータ的示唆:</strong><br>
            マッチング成立要因分析（Section 3）および 3×3分割表（Section 4）が示す通り、マッチング成立は「企業がバリューで選び、学生がパーソナリティで選ぶ」という双方向の合致によって初めて実現しています（両スコア高水準群で成立率約55〜61%、両スコア低水準群では18.9%）。<br>
            したがって、次回イベントの配席設計においては、企業の要望（高バリュー層の配置）を満たすだけでなく、学生側のパーソナリティ適合度も同時に考慮した「複合的な最適配席アルゴリズム」を導入することで、イベント全体のマッチング総数および双方の満足度を最大化できる可能性が強く示唆されます。</p>

            <div style="background: rgba(255, 255, 255, 0.12); border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 8px; padding: 14px 18px; margin-top: 18px; font-size: 13px; color: #FFFFFF; line-height: 1.6;">
                <div style="font-weight: 800; font-size: 13.5px; display: flex; align-items: center; gap: 6px; margin-bottom: 6px; color: #FBBF24;">
                    <span>💡</span> 【解釈・示唆の補足：ブラインド環境下での実証性について】
                </div>
                <p>本イベントの当日、企業側および学生側は自他のフィット度スコア（数値）を一切閲覧できない（見えない）状態で対話・意思決定を行っていました。</p>
                <p style="margin-top: 6px;">そのようなブラインド環境下であったにもかかわらず、企業側のアクションはバリューフィット度と極めて高い連動性を示し（10pt上昇で選択オッズが約1.8〜1.9倍**）、学生側のアクションもパーソナリティフィット度と有意に連動（10pt上昇で選択オッズ約1.51倍*）し、最終的なマッチング成立にも両フィット度が同等に寄与していました。</p>
                <p style="margin-top: 6px;">この事実は、数値を見たことによる「先入観（アンカリング効果）」や「確証バイアス」によって結果が作られたのではなく、事前診断されたフィット度スコアが、当日のリアルな対話や行動、そして本質的な相性を捉えていたことの有力な裏付け（示唆）といえます。</p>
            </div>
        </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 2: 有料出展 vs 無料出展 区分別分析 -->
    <!-- ============================================================= -->
    <div id="tab-stratified" class="tab-pane" style="display: none !important;">
        <!-- Section 1: 有料出展企業（4社・122件）のアクション別実態 -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">💎 【有料出展企業】アクション別（3区分・2値）の件数およびスコア実態（記述統計）</div>
                    <div class="section-desc">事前マッチングにより高バリュー層が優先配席された有料企業4社（122件）における各スコア推移</div>
                </div>
                <span class="pill pill-indigo">有料企業 (N=122)</span>
            </div>

            <div class="grid-2">
                <!-- 有料：企業アクション -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">🏢 企業アクション別スコア実態</h3>
                    <div class="chart-box">
                        <canvas id="chart-strat-paid-comp"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 25%;">アクション区分</th>
                                    <th style="width: 23%;">件数<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(構成比)</span></th>
                                    <th style="width: 26%;">バリューフィット度<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=122)</span></th>
                                    <th style="width: 26%;">パーソナリティ<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=122)</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{paid_act['company']['three_cats'][0]['count']}件 ({fmt_pct(paid_act['company']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][0]['v_mean'])} ±{fmt_num(paid_act['company']['three_cats'][0]['v_std'])}</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][0]['p_mean'])} ±{fmt_num(paid_act['company']['three_cats'][0]['p_std'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{paid_act['company']['three_cats'][1]['count']}件 ({fmt_pct(paid_act['company']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][1]['v_mean'])} ±{fmt_num(paid_act['company']['three_cats'][1]['v_std'])}</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][1]['p_mean'])} ±{fmt_num(paid_act['company']['three_cats'][1]['p_std'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>
                                        <strong>めっちゃ知りたい</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(10名限定)</span>
                                    </td>
                                    <td>{paid_act['company']['three_cats'][2]['count']}件 ({fmt_pct(paid_act['company']['three_cats'][2]['pct'])})</td>
                                    <td><strong>{fmt_num(paid_act['company']['three_cats'][2]['v_mean'])}</strong> ±{fmt_num(paid_act['company']['three_cats'][2]['v_std'])}</td>
                                    <td>{fmt_num(paid_act['company']['three_cats'][2]['p_mean'])} ±{fmt_num(paid_act['company']['three_cats'][2]['p_std'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700; border-top: 2px solid var(--gray-300);">
                                    <td>知りたい以上<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(2値集計)</span></td>
                                    <td>{paid_act['company']['binary'][1]['count']}件 ({fmt_pct(paid_act['company']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['company']['binary'][1]['v_mean'])} ±{fmt_num(paid_act['company']['binary'][1]['v_std'])}</td>
                                    <td>{fmt_num(paid_act['company']['binary'][1]['p_mean'])} ±{fmt_num(paid_act['company']['binary'][1]['p_std'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 有料：学生アクション -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">🎓 学生アクション別スコア実態（有料企業宛）</h3>
                    <div class="chart-box">
                        <canvas id="chart-strat-paid-stud"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 25%;">アクション区分</th>
                                    <th style="width: 23%;">件数<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(構成比)</span></th>
                                    <th style="width: 26%;">バリューフィット度<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=122)</span></th>
                                    <th style="width: 26%;">パーソナリティ<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=122)</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{paid_act['student']['three_cats'][0]['count']}件 ({fmt_pct(paid_act['student']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][0]['v_mean'])} ±{fmt_num(paid_act['student']['three_cats'][0]['v_std'])}</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][0]['p_mean'])} ±{fmt_num(paid_act['student']['three_cats'][0]['p_std'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{paid_act['student']['three_cats'][1]['count']}件 ({fmt_pct(paid_act['student']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][1]['v_mean'])} ±{fmt_num(paid_act['student']['three_cats'][1]['v_std'])}</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][1]['p_mean'])} ±{fmt_num(paid_act['student']['three_cats'][1]['p_std'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>
                                        <strong>めっちゃ知りたい</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(上限なし)</span>
                                    </td>
                                    <td>{paid_act['student']['three_cats'][2]['count']}件 ({fmt_pct(paid_act['student']['three_cats'][2]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['three_cats'][2]['v_mean'])} ±{fmt_num(paid_act['student']['three_cats'][2]['v_std'])}</td>
                                    <td><strong>{fmt_num(paid_act['student']['three_cats'][2]['p_mean'])}</strong> ±{fmt_num(paid_act['student']['three_cats'][2]['p_std'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700; border-top: 2px solid var(--gray-300);">
                                    <td>知りたい以上<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(2値集計)</span></td>
                                    <td>{paid_act['student']['binary'][1]['count']}件 ({fmt_pct(paid_act['student']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(paid_act['student']['binary'][1]['v_mean'])} ±{fmt_num(paid_act['student']['binary'][1]['v_std'])}</td>
                                    <td>{fmt_num(paid_act['student']['binary'][1]['p_mean'])} ±{fmt_num(paid_act['student']['binary'][1]['p_std'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="summary-box">
                <strong class="title">📝 有料出展企業（N=122）のデータまとめ:</strong>
                <ul>
                    <li><strong>企業側</strong>：事前マッチングにより全体的にベースが高く、バリュー平均は「なし（{fmt_num(paid_act['company']['three_cats'][0]['v_mean'])}）」から「知りたい（{fmt_num(paid_act['company']['three_cats'][1]['v_mean'])}）」、「めっちゃ知りたい（{fmt_num(paid_act['company']['three_cats'][2]['v_mean'])}）」と高水準で推移（差 +{fmt_num(paid_act['company']['three_cats'][2]['v_mean'] - paid_act['company']['three_cats'][0]['v_mean'])}pt）。パーソナリティ平均は {fmt_num(min(x['p_mean'] for x in paid_act['company']['three_cats']))} 〜 {fmt_num(max(x['p_mean'] for x in paid_act['company']['three_cats']))} と横ばいです。</li>
                    <li><strong>学生側</strong>：パーソナリティ平均が「なし（{fmt_num(paid_act['student']['three_cats'][0]['p_mean'])}）」から「知りたい（{fmt_num(paid_act['student']['three_cats'][1]['p_mean'])}）」、「めっちゃ知りたい（{fmt_num(paid_act['student']['three_cats'][2]['p_mean'])}）」へと顕著に押し上がる傾向（差 +{fmt_num(paid_act['student']['three_cats'][2]['p_mean'] - paid_act['student']['three_cats'][0]['p_mean'])}pt）が見られます。</li>
                </ul>
            </div>
        </div>

        <!-- Section 2: 無料出展企業（8社・191件 / P有効164件）のアクション別実態 -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🌱 【無料出展企業】アクション別（3区分・2値）の件数およびスコア実態（記述統計）</div>
                    <div class="section-desc">企業の完全な自由配席が行われた無料企業8社（191件 / パーソナリティ有効164件）における各スコア推移</div>
                </div>
                <span class="pill pill-cyan">無料企業 (N=191 / 164)</span>
            </div>

            <div class="grid-2">
                <!-- 無料：企業アクション -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">🏢 企業アクション別スコア実態</h3>
                    <div class="chart-box">
                        <canvas id="chart-strat-free-comp"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 25%;">アクション区分</th>
                                    <th style="width: 23%;">件数<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(構成比)</span></th>
                                    <th style="width: 26%;">バリューフィット度<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=191)</span></th>
                                    <th style="width: 26%;">パーソナリティ<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=164)</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{free_act['company']['three_cats'][0]['count']}件 ({fmt_pct(free_act['company']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][0]['v_mean'])} ±{fmt_num(free_act['company']['three_cats'][0]['v_std'])}</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][0]['p_mean'])} ±{fmt_num(free_act['company']['three_cats'][0]['p_std'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{free_act['company']['three_cats'][1]['count']}件 ({fmt_pct(free_act['company']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][1]['v_mean'])} ±{fmt_num(free_act['company']['three_cats'][1]['v_std'])}</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][1]['p_mean'])} ±{fmt_num(free_act['company']['three_cats'][1]['p_std'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>
                                        <strong>めっちゃ知りたい</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(10名限定)</span>
                                    </td>
                                    <td>{free_act['company']['three_cats'][2]['count']}件 ({fmt_pct(free_act['company']['three_cats'][2]['pct'])})</td>
                                    <td><strong>{fmt_num(free_act['company']['three_cats'][2]['v_mean'])}</strong> ±{fmt_num(free_act['company']['three_cats'][2]['v_std'])}</td>
                                    <td>{fmt_num(free_act['company']['three_cats'][2]['p_mean'])} ±{fmt_num(free_act['company']['three_cats'][2]['p_std'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700; border-top: 2px solid var(--gray-300);">
                                    <td>知りたい以上<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(2値集計)</span></td>
                                    <td>{free_act['company']['binary'][1]['count']}件 ({fmt_pct(free_act['company']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['company']['binary'][1]['v_mean'])} ±{fmt_num(free_act['company']['binary'][1]['v_std'])}</td>
                                    <td>{fmt_num(free_act['company']['binary'][1]['p_mean'])} ±{fmt_num(free_act['company']['binary'][1]['p_std'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 無料：学生アクション -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">🎓 学生アクション別スコア実態（無料企業宛）</h3>
                    <div class="chart-box">
                        <canvas id="chart-strat-free-stud"></canvas>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 25%;">アクション区分</th>
                                    <th style="width: 23%;">件数<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(構成比)</span></th>
                                    <th style="width: 26%;">バリューフィット度<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=191)</span></th>
                                    <th style="width: 26%;">パーソナリティ<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">平均±SD (N=164)</span></th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>なし</td>
                                    <td>{free_act['student']['three_cats'][0]['count']}件 ({fmt_pct(free_act['student']['three_cats'][0]['pct'])})</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][0]['v_mean'])} ±{fmt_num(free_act['student']['three_cats'][0]['v_std'])}</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][0]['p_mean'])} ±{fmt_num(free_act['student']['three_cats'][0]['p_std'])}</td>
                                </tr>
                                <tr>
                                    <td>知りたい</td>
                                    <td>{free_act['student']['three_cats'][1]['count']}件 ({fmt_pct(free_act['student']['three_cats'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][1]['v_mean'])} ±{fmt_num(free_act['student']['three_cats'][1]['v_std'])}</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][1]['p_mean'])} ±{fmt_num(free_act['student']['three_cats'][1]['p_std'])}</td>
                                </tr>
                                <tr class="highlight-row">
                                    <td>
                                        <strong>めっちゃ知りたい</strong><br>
                                        <span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(上限なし)</span>
                                    </td>
                                    <td>{free_act['student']['three_cats'][2]['count']}件 ({fmt_pct(free_act['student']['three_cats'][2]['pct'])})</td>
                                    <td><strong>{fmt_num(free_act['student']['three_cats'][2]['v_mean'])}</strong> ±{fmt_num(free_act['student']['three_cats'][2]['v_std'])}</td>
                                    <td>{fmt_num(free_act['student']['three_cats'][2]['p_mean'])} ±{fmt_num(free_act['student']['three_cats'][2]['p_std'])}</td>
                                </tr>
                                <tr style="background: #F1F5F9; font-weight: 700; border-top: 2px solid var(--gray-300);">
                                    <td>知りたい以上<br><span style="font-size: 10px; color: var(--gray-500); font-weight: normal;">(2値集計)</span></td>
                                    <td>{free_act['student']['binary'][1]['count']}件 ({fmt_pct(free_act['student']['binary'][1]['pct'])})</td>
                                    <td>{fmt_num(free_act['student']['binary'][1]['v_mean'])} ±{fmt_num(free_act['student']['binary'][1]['v_std'])}</td>
                                    <td>{fmt_num(free_act['student']['binary'][1]['p_mean'])} ±{fmt_num(free_act['student']['binary'][1]['p_std'])}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="summary-box">
                <strong class="title">🌱 無料出展企業（N=191 / 164）のデータまとめ:</strong>
                <ul>
                    <li><strong>企業側</strong>：完全自由選択のためバリューフィット度との連動が極めて強く、「なし（{fmt_num(free_act['company']['three_cats'][0]['v_mean'])}）」から「知りたい（{fmt_num(free_act['company']['three_cats'][1]['v_mean'])}）」、「めっちゃ知りたい（{fmt_num(free_act['company']['three_cats'][2]['v_mean'])}）」へと急激に上昇（差 +{fmt_num(free_act['company']['three_cats'][2]['v_mean'] - free_act['company']['three_cats'][0]['v_mean'])}pt）。パーソナリティ平均は {fmt_num(min(x['p_mean'] for x in free_act['company']['three_cats']))} 〜 {fmt_num(max(x['p_mean'] for x in free_act['company']['three_cats']))} の範囲で推移しています。</li>
                    <li><strong>学生側</strong>：バリュー平均は「なし（{fmt_num(free_act['student']['three_cats'][0]['v_mean'])}）」から「知りたい（{fmt_num(free_act['student']['three_cats'][1]['v_mean'])}）」、「めっちゃ知りたい（{fmt_num(free_act['student']['three_cats'][2]['v_mean'])}）」とほぼ横ばいで推移（差 +{fmt_num(free_act['student']['three_cats'][2]['v_mean'] - free_act['student']['three_cats'][0]['v_mean'])}pt）。パーソナリティ平均は {fmt_num(min(x['p_mean'] for x in free_act['student']['three_cats']))} 〜 {fmt_num(max(x['p_mean'] for x in free_act['student']['three_cats']))} の範囲で推移しています。</li>
                </ul>
            </div>
        </div>

        <!-- Section 3: 💎 有料企業 要因分析（要点まとめ ＆ 詳細モデル） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🎯 【有料企業：要因分析】スコアがアクション選択に与える影響（要点まとめ ＆ 詳細モデル）</div>
                    <div class="section-desc">有料企業4社（122件）における企業側および学生側のアクション選択への各スコア影響度（ロジット回帰）</div>
                </div>
                <span class="pill pill-indigo">有料企業要因分析</span>
            </div>

            <!-- 前面：直感的な要点まとめ（表 ＆ 視覚化グラフ） -->
            <div class="grid-2" style="margin-bottom: 20px;">
                <!-- 左：要点まとめ表 -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📋 有料企業群：スコア10pt上昇時の選択への影響（要点）</h3>
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
                                        <strong style="color: var(--primary); font-size: 14px;">約 1.8 〜 2.2 倍</strong><br>
                                        <span class="pill pill-indigo" style="font-size: 10px; margin-top: 3px;">有意傾向 (†)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>1.78倍†</strong>、めっちゃ知りたいで <strong>2.17倍†</strong>。事前配席でベースが高い中、一定の選考寄与。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: #0284C7; font-size: 14px;">約 1.6 〜 2.0 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">有意な影響 (*)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>2.04倍*</strong>（p=0.0185）、知りたいで <strong>2.23倍*</strong>。学生側もバリュー高を明確に選好。
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>パーソナリティ<br>フィット度</strong></td>
                                    <td>
                                        <strong style="color: var(--gray-500); font-size: 14px;">約 0.95 〜 0.98 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">統計的な影響なし</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上 <strong>0.98倍</strong>、めっちゃ知りたい <strong>0.95倍</strong>。企業の選定にスコア連動なし。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: var(--amber-600); font-size: 14px;">約 1.6 〜 1.9 倍</strong><br>
                                        <span class="pill pill-amber" style="font-size: 10px; margin-top: 3px;">有意な影響 (*)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>1.64倍*</strong>（p=0.0435）、めっちゃ知りたいで <strong>1.90倍</strong>。有料企業宛では学生が相性を重視。
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
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📊 有料企業群：10pt上昇時の選択倍率インパクト（基準=1.0倍）</h3>
                    <div class="chart-box" style="height: 270px;">
                        <canvas id="chart-strat-paid-impact"></canvas>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※赤線（1.0倍）より右に伸びるほど強いプラス影響。有料企業宛の学生はバリュー（2.04倍*）とパーソナリティ（1.64倍*）の両方に有意連動。
                    </div>
                </div>
            </div>

            <!-- 専門的な詳細アコーディオン -->
            <details class="stats-details">
                <summary class="stats-summary">
                    <span>📊 有料企業群の詳細統計データ（オッズ比・95%信頼区間・p値：企業 ＆ 学生）を展開する</span>
                    <span class="pill pill-indigo">クリックで開閉</span>
                </summary>
                <div class="stats-content">
                    <!-- 有料：企業回帰 -->
                    <div style="margin-bottom: 24px;">
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 有料企業 (N=122) における企業アクション回帰詳細</h3>
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
                                        <td><strong>OR {fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【多変量モデル】バリュー ＋ パーソナリティ を同時投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td><strong>OR {fmt_num(reg['paid']['company']['binary']['multivariate']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['company']['binary']['multivariate']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['binary']['multivariate']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['binary']['multivariate']['params']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['multivariate']['知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['multivariate']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['multivariate']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['multivariate']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['paid']['company']['binary']['multivariate']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['binary']['multivariate']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['binary']['multivariate']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['binary']['multivariate']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 有料：学生回帰 -->
                    <div>
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🎓 有料企業宛 (N=122) における学生アクション回帰詳細</h3>
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
                                        <td><strong>OR {fmt_num(reg['paid']['student']['binary']['value_univ']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['student']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['paid']['student']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['student']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['paid']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td><strong>OR {fmt_num(reg['paid']['student']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['student']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【多変量モデル】バリュー ＋ パーソナリティ を同時投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td><strong>OR {fmt_num(reg['paid']['student']['binary']['multivariate']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['student']['binary']['multivariate']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['binary']['multivariate']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['binary']['multivariate']['params']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['paid']['student']['multinomial']['multivariate']['知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['paid']['student']['multinomial']['multivariate']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['multivariate']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['multivariate']['知りたい']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['paid']['student']['binary']['multivariate']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['student']['binary']['multivariate']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['binary']['multivariate']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['binary']['multivariate']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['paid']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>122</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- ⑥ 有料企業の範囲制限解説カード -->
                    <div style="margin-top: 16px; padding-top: 14px; border-top: 1px dashed var(--gray-300);">
                        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 14px 16px; font-size: 12px; color: #166534; line-height: 1.6;">
                            <h4 style="font-size: 13.5px; font-weight: 800; color: #15803D; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                                <span>📏</span> 【統計的背景】有料企業でスコアの差がマイルドに見える理由（最初から全員高得点だったため）
                            </h4>
                            <p>有料企業群（122件）において、企業側のバリューフィット度オッズ比（1.78倍, p = 0.0845†）が無料企業群（2.06倍, p = 0.0002***）よりも控えめで有意性が弱まっているように見えます。これは有料企業がバリューを軽視したのではなく、<strong>「事前の優先配席によって最初から高バリューの学生ばかりが集められたため、学生間のスコアのばらつき（標準偏差）が小さくなった（有料SD 6.38 vs 無料SD 8.53）」</strong> ことによる統計学上の必然的な現象（範囲制限・天井効果）です。</p>
                            <p style="margin-top: 6px;">有料企業では「なし」の時点ですでにバリュー平均が 60.09（無料企業の「知りたい」平均 60.46 と同等）に達しており、低バリュー層との比較が存在しない高水準帯での選考だったことが、オッズ比がマイルドに表れる理由です。</p>
                        </div>
                    </div>
                </div>
            </details>

            <div class="summary-box">
                <strong class="title">📝 有料企業群（N=122）の要因分析まとめ:</strong>
                <ul>
                    <li><strong>企業側</strong>：事前マッチングにより元々高バリュー層が集中的に配席されていたため、スコア上昇の倍率効果は「めっちゃ知りたい」で OR {fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 2)}（p = 0.0651†）のマイルドな有意傾向にとどまります。パーソナリティは選択に影響を与えていません。</li>
                    <li><strong>学生側</strong>：有料企業宛の学生は、バリューフィット度（知りたい以上 OR {fmt_num(reg['paid']['student']['binary']['value_univ']['params']['value_fit']['or_10'], 2)}*）およびパーソナリティフィット度（知りたい以上 OR {fmt_num(reg['paid']['student']['binary']['personality_univ']['params']['personality_fit']['or_10'], 2)}*）の<strong>双方に対して統計的有意に連動してアクションを選択</strong>しています。</li>
                </ul>
            </div>
        </div>

        <!-- Section 4: 🌱 無料企業 要因分析（要点まとめ ＆ 詳細モデル） -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🎯 【無料企業：要因分析】スコアがアクション選択に与える影響（要点まとめ ＆ 詳細モデル）</div>
                    <div class="section-desc">無料企業8社（191件 / パーソナリティ有効164件）における企業側および学生側のアクション選択への各スコア影響度（ロジット回帰）</div>
                </div>
                <span class="pill pill-cyan">無料企業要因分析</span>
            </div>

            <!-- 前面：直感的な要点まとめ（表 ＆ 視覚化グラフ） -->
            <div class="grid-2" style="margin-bottom: 20px;">
                <!-- 左：要点まとめ表 -->
                <div class="sub-card">
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📋 無料企業群：スコア10pt上昇時の選択への影響（要点）</h3>
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
                                        <strong style="color: #0F766E; font-size: 14px;">約 2.1 〜 3.2 倍</strong><br>
                                        <span class="pill pill-cyan" style="font-size: 10px; margin-top: 3px;">極めて強い影響 (***)</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上で <strong>2.06倍***</strong>、めっちゃ知りたいで <strong>3.22倍***</strong>。自由選択によりバリューが大きな判断基準となっている傾向。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: var(--gray-500); font-size: 14px;">約 1.0 〜 1.1 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">統計的な影響なし</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上 <strong>1.07倍</strong>、めっちゃ知りたい <strong>1.00倍</strong>。無料企業宛の学生アクションはバリューに連動せず。
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td><strong>パーソナリティ<br>フィット度</strong></td>
                                    <td>
                                        <strong style="color: var(--gray-500); font-size: 14px;">約 1.0 〜 1.2 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">統計的な影響なし</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上 <strong>1.16倍</strong>、めっちゃ知りたい <strong>0.97倍</strong>。企業の選定にスコア連動なし。
                                        </div>
                                    </td>
                                    <td>
                                        <strong style="color: var(--gray-500); font-size: 14px;">約 1.0 〜 1.3 倍</strong><br>
                                        <span class="pill pill-slate" style="font-size: 10px; margin-top: 3px;">統計的な影響なし</span>
                                        <div style="font-size: 11px; color: var(--gray-600); margin-top: 4px; line-height: 1.4;">
                                            知りたい以上 <strong>1.05倍</strong>、めっちゃ知りたい <strong>1.25倍</strong>。統計的有意差は見られず。
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
                    <h3 style="font-size: 14.5px; font-weight: 700; color: #1E293B; margin-bottom: 10px;">📊 無料企業群：10pt上昇時の選択倍率インパクト（基準=1.0倍）</h3>
                    <div class="chart-box" style="height: 270px;">
                        <canvas id="chart-strat-free-impact"></canvas>
                    </div>
                    <div style="margin-top: 8px; font-size: 10.5px; color: var(--gray-500); line-height: 1.3;">
                        ※赤線（1.0倍）より右に大きく伸びるほど強いプラス影響。無料企業側のバリュー選択オッズ（3.22倍***）が全群の中で最も突出。
                    </div>
                </div>
            </div>

            <!-- 専門的な詳細アコーディオン -->
            <details class="stats-details">
                <summary class="stats-summary">
                    <span>📊 無料企業群の詳細統計データ（オッズ比・95%信頼区間・p値：企業 ＆ 学生）を展開する</span>
                    <span class="pill pill-cyan">クリックで開閉</span>
                </summary>
                <div class="stats-content">
                    <!-- 無料：企業回帰 -->
                    <div style="margin-bottom: 24px;">
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🏢 無料企業 (N=191 / 164) における企業アクション回帰詳細</h3>
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
                                        <td><strong>OR {fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>191</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>164</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【多変量モデル】バリュー ＋ パーソナリティ を同時投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td><strong>OR {fmt_num(reg['free']['company']['binary']['multivariate']['params']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['binary']['multivariate']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['binary']['multivariate']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['binary']['multivariate']['params']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['company']['multinomial']['multivariate']['知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['multinomial']['multivariate']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['multivariate']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['multivariate']['知りたい']['value_fit']['p'])}</span></td>
                                        <td><strong>OR {fmt_num(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['or_10'], 3)}</strong> [{fmt_num(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>164</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['free']['company']['binary']['multivariate']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['binary']['multivariate']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['binary']['multivariate']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['binary']['multivariate']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['multivariate']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['company']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>164</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 無料：学生回帰 -->
                    <div>
                        <h3 style="font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 8px;">🎓 無料企業宛 (N=191 / 164) における学生アクション回帰詳細</h3>
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
                                        <td>OR {fmt_num(reg['free']['student']['binary']['value_univ']['params']['value_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['binary']['value_univ']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['binary']['value_univ']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['binary']['value_univ']['params']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['value_univ']['知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['value_univ']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['value_univ']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['value_univ']['知りたい']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>191</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['free']['student']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['binary']['personality_univ']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['binary']['personality_univ']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['binary']['personality_univ']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['personality_univ']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>164</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td colspan="5" style="font-weight: 700; color: var(--gray-600); font-size: 11.5px;">【多変量モデル】バリュー ＋ パーソナリティ を同時投入</td>
                                    </tr>
                                    <tr>
                                        <td><strong>バリューフィット度</strong></td>
                                        <td>OR {fmt_num(reg['free']['student']['binary']['multivariate']['params']['value_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['binary']['multivariate']['params']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['binary']['multivariate']['params']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['binary']['multivariate']['params']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['multivariate']['知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['multivariate']['知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['multivariate']['知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['multivariate']['知りたい']['value_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['value_fit']['p'])}</span></td>
                                        <td>164</td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティフィット度</strong></td>
                                        <td>OR {fmt_num(reg['free']['student']['binary']['multivariate']['params']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['binary']['multivariate']['params']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['binary']['multivariate']['params']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['binary']['multivariate']['params']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['multivariate']['知りたい']['personality_fit']['p'])}</span></td>
                                        <td>OR {fmt_num(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['or_10'], 3)} [{fmt_num(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_lower'], 3)}〜{fmt_num(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['ci_upper'], 3)}]<br><span style="font-size: 11px;">{fmt_p(reg['free']['student']['multinomial']['multivariate']['めっちゃ知りたい']['personality_fit']['p'])}</span></td>
                                        <td>164</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </details>

            <div class="summary-box">
                <strong class="title">📝 無料企業群（N=191 / 164）の要因分析まとめ:</strong>
                <ul>
                    <li><strong>企業側</strong>：完全自由選択のためバリューフィット度の上昇に伴う選択オッズ比が極めて顕著であり、2値で OR {fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 2)}（p &lt; 0.0001***）、多項の「めっちゃ知りたい」で OR {fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 2)}（p &lt; 0.0001***）と全群中最も顕著な関連性を示しています。</li>
                    <li><strong>学生側</strong>：無料企業宛の学生アクションは、バリューフィット度（OR 1.07）およびパーソナリティフィット度（OR 1.05）ともに統計的有意差を持たず、スコア連動はマイルドにとどまっています。</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 2: 全12社 比較一覧・個別カルテ -->
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

            <!-- ソート・フィルタ コントロールバー -->
            <div style="background: #F8FAFC; border: 1px solid var(--gray-200); border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; display: flex; flex-wrap: wrap; gap: 14px; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <span style="font-size: 13px; font-weight: 700; color: var(--gray-700);">並び替え:</span>
                    <select id="company-quick-sort" onchange="applyQuickSort(this.value)" style="padding: 6px 12px; font-size: 13px; font-weight: 600; border-radius: 6px; border: 1px solid var(--gray-300); background: white; color: var(--gray-800); cursor: pointer;">
                        <option value="match_rate_desc">👑 マッチ成立率が高い順</option>
                        <option value="match_rate_asc">マッチ成立率が低い順</option>
                        <option value="v_mean_desc">🎯 バリュー平均が高い順</option>
                        <option value="v_mean_asc">バリュー平均が低い順</option>
                        <option value="p_mean_desc">💖 パーソナリティ平均が高い順</option>
                        <option value="p_mean_asc">パーソナリティ平均が低い順</option>
                        <option value="comp_plus_desc">🏢 企業熱量（知りたい以上）が高い順</option>
                        <option value="stud_plus_desc">🎓 学生人気（知りたい以上）が高い順</option>
                        <option value="count_desc">👥 接触数が多い順</option>
                        <option value="name_asc">🔤 企業名（50音順）</option>
                        <option value="is_paid_desc">🏷️ 出展区分順（有料 ➔ 無料）</option>
                    </select>
                    <span style="font-size: 11.5px; color: var(--gray-500);">※表の列ヘッダーをクリックしても並び替えられます</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 13px; font-weight: 700; color: var(--gray-700);">出展区分:</span>
                    <div style="display: inline-flex; border-radius: 6px; overflow: hidden; border: 1px solid var(--gray-300);">
                        <button class="plan-filter-btn active" onclick="setPlanFilter('all', this)">全て (12社)</button>
                        <button class="plan-filter-btn" onclick="setPlanFilter('paid', this)">有料のみ (4社)</button>
                        <button class="plan-filter-btn" onclick="setPlanFilter('free', this)">無料のみ (8社)</button>
                    </div>
                </div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th class="sortable" onclick="handleCompanySort('name')">企業名 <span class="sort-icon" id="sort-icon-name">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('is_paid')">区分 <span class="sort-icon" id="sort-icon-is_paid">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('count')">接触数 <span class="sort-icon" id="sort-icon-count">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('match_count')">マッチ成立 <span class="sort-icon" id="sort-icon-match_count">⇅</span></th>
                            <th class="sortable active-sort" onclick="handleCompanySort('match_rate')">成立率 <span class="sort-icon" id="sort-icon-match_rate">▼</span></th>
                            <th class="sortable" onclick="handleCompanySort('v_mean')">バリュー平均 <span class="sort-icon" id="sort-icon-v_mean">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('p_mean')">P平均 <span class="sort-icon" id="sort-icon-p_mean">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('comp_high')">企業 めっちゃ知りたい <span class="sort-icon" id="sort-icon-comp_high">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('comp_plus')">企業 知りたい以上 <span class="sort-icon" id="sort-icon-comp_plus">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('stud_high')">学生 めっちゃ知りたい <span class="sort-icon" id="sort-icon-stud_high">⇅</span></th>
                            <th class="sortable" onclick="handleCompanySort('stud_plus')">学生 知りたい以上 <span class="sort-icon" id="sort-icon-stud_plus">⇅</span></th>
                        </tr>
                    </thead>
                    <tbody id="company-table-body">'''

    for idx, c in enumerate(comps):
        plan_badge = '<span class="pill pill-indigo">有料</span>' if c['is_paid'] == 1 else '<span class="pill pill-slate">無料</span>'
        html += f'''
                        <tr class="company-row" onclick="selectCompany({idx}, true)">
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
                        </tr>'''

    html += f'''
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 🔍 個別企業カルテ -->
        <div class="section-card" id="company-detail-card">
            <div class="section-header">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <div class="section-title">🔍 【個別カルテ】</div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <button onclick="prevCompany()" class="nav-mini-btn" title="前の企業へ">◀</button>
                        <select id="company-select" onchange="selectCompany(parseInt(this.value), false)" style="padding: 6px 12px; font-size: 13.5px; font-weight: 700; border-radius: 6px; border: 1px solid var(--gray-300); background: white; cursor: pointer;">'''

    for idx, c in enumerate(comps):
        html += f'''
                            <option value="{idx}">{c['name']} ({'有料' if c['is_paid']==1 else '無料'} | 成立率 {fmt_pct(c['match_rate'])})</option>'''

    html += f'''
                        </select>
                        <button onclick="nextCompany()" class="nav-mini-btn" title="次の企業へ">▶</button>
                    </div>
                    <span style="font-size: 11.5px; color: var(--gray-500);">※上のテーブルで行をクリックしても切り替わります</span>
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
// Logit Impact Chart (時間統制＋企業統制モデル)
    new Chart(document.getElementById('chart-logit-impact'), {{
        type: 'bar',
        data: {{
            labels: [
                '企業：バリュー (知りたい以上)',
                '企業：バリュー (めっちゃ知りたい)',
                '企業：パーソナリティ (知りたい以上)',
                '企業：パーソナリティ (めっちゃ知りたい)',
                '学生：パーソナリティ (知りたい以上)',
                '学生：パーソナリティ (めっちゃ知りたい)',
                '学生：バリュー (知りたい以上)',
                '学生：バリュー (めっちゃ知りたい)'
            ],
            datasets: [{{
                label: 'スコア10pt上昇時の選択倍率 (オッズ比)',
                data: [
                    1.931,
                    1.837,
                    1.181,
                    0.831,
                    1.510,
                    1.420,
                    1.318,
                    1.048
                ],
                backgroundColor: [
                    '#4F46E5',
                    '#6366F1',
                    '#94A3B8',
                    '#CBD5E1',
                    '#7E22CE',
                    '#A855F7',
                    '#38BDF8',
                    '#BAE6FD'
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

    // Stratified Charts (Tab 2: Option 2)
    // 1. Paid Company
    new Chart(document.getElementById('chart-strat-paid-comp'), {{
        type: 'bar',
        data: {{
            labels: ['なし ({paid_act['company']['three_cats'][0]['count']}件)', '知りたい ({paid_act['company']['three_cats'][1]['count']}件)', 'めっちゃ知りたい ({paid_act['company']['three_cats'][2]['count']}件)'],
            datasets: [
                {{
                    label: 'バリューフィット度 平均',
                    data: [{paid_act['company']['three_cats'][0]['v_mean']}, {paid_act['company']['three_cats'][1]['v_mean']}, {paid_act['company']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#4F46E5',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティフィット度 平均',
                    data: [{paid_act['company']['three_cats'][0]['p_mean']}, {paid_act['company']['three_cats'][1]['p_mean']}, {paid_act['company']['three_cats'][2]['p_mean']}],
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

    // 2. Paid Student
    new Chart(document.getElementById('chart-strat-paid-stud'), {{
        type: 'bar',
        data: {{
            labels: ['なし ({paid_act['student']['three_cats'][0]['count']}件)', '知りたい ({paid_act['student']['three_cats'][1]['count']}件)', 'めっちゃ知りたい ({paid_act['student']['three_cats'][2]['count']}件)'],
            datasets: [
                {{
                    label: 'バリューフィット度 平均',
                    data: [{paid_act['student']['three_cats'][0]['v_mean']}, {paid_act['student']['three_cats'][1]['v_mean']}, {paid_act['student']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#06B6D4',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティフィット度 平均',
                    data: [{paid_act['student']['three_cats'][0]['p_mean']}, {paid_act['student']['three_cats'][1]['p_mean']}, {paid_act['student']['three_cats'][2]['p_mean']}],
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

    // 3. Free Company
    new Chart(document.getElementById('chart-strat-free-comp'), {{
        type: 'bar',
        data: {{
            labels: ['なし ({free_act['company']['three_cats'][0]['count']}件)', '知りたい ({free_act['company']['three_cats'][1]['count']}件)', 'めっちゃ知りたい ({free_act['company']['three_cats'][2]['count']}件)'],
            datasets: [
                {{
                    label: 'バリューフィット度 平均',
                    data: [{free_act['company']['three_cats'][0]['v_mean']}, {free_act['company']['three_cats'][1]['v_mean']}, {free_act['company']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#4F46E5',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティフィット度 平均',
                    data: [{free_act['company']['three_cats'][0]['p_mean']}, {free_act['company']['three_cats'][1]['p_mean']}, {free_act['company']['three_cats'][2]['p_mean']}],
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

    // 4. Free Student
    new Chart(document.getElementById('chart-strat-free-stud'), {{
        type: 'bar',
        data: {{
            labels: ['なし ({free_act['student']['three_cats'][0]['count']}件)', '知りたい ({free_act['student']['three_cats'][1]['count']}件)', 'めっちゃ知りたい ({free_act['student']['three_cats'][2]['count']}件)'],
            datasets: [
                {{
                    label: 'バリューフィット度 平均',
                    data: [{free_act['student']['three_cats'][0]['v_mean']}, {free_act['student']['three_cats'][1]['v_mean']}, {free_act['student']['three_cats'][2]['v_mean']}],
                    backgroundColor: '#06B6D4',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティフィット度 平均',
                    data: [{free_act['student']['three_cats'][0]['p_mean']}, {free_act['student']['three_cats'][1]['p_mean']}, {free_act['student']['three_cats'][2]['p_mean']}],
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

    // 5. Paid Impact Chart
    new Chart(document.getElementById('chart-strat-paid-impact'), {{
        type: 'bar',
        data: {{
            labels: [
                '企業：バリュー (めっちゃ知りたい)',
                '企業：バリュー (知りたい以上)',
                '企業：パーソナリティ (めっちゃ知りたい)',
                '企業：パーソナリティ (知りたい以上)',
                '学生：バリュー (めっちゃ知りたい)',
                '学生：バリュー (知りたい以上)',
                '学生：パーソナリティ (めっちゃ知りたい)',
                '学生：パーソナリティ (知りたい以上)'
            ],
            datasets: [{{
                label: 'スコア10pt上昇時の選択倍率 (オッズ比)',
                data: [
                    {fmt_num(reg['paid']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['student']['binary']['value_univ']['params']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)},
                    {fmt_num(reg['paid']['student']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)}
                ],
                backgroundColor: [
                    '#4F46E5',
                    '#6366F1',
                    '#CBD5E1',
                    '#94A3B8',
                    '#0284C7',
                    '#38BDF8',
                    '#D97706',
                    '#F59E0B'
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

    // 6. Free Impact Chart
    new Chart(document.getElementById('chart-strat-free-impact'), {{
        type: 'bar',
        data: {{
            labels: [
                '企業：バリュー (めっちゃ知りたい)',
                '企業：バリュー (知りたい以上)',
                '企業：パーソナリティ (めっちゃ知りたい)',
                '企業：パーソナリティ (知りたい以上)',
                '学生：バリュー (めっちゃ知りたい)',
                '学生：バリュー (知りたい以上)',
                '学生：パーソナリティ (めっちゃ知りたい)',
                '学生：パーソナリティ (知りたい以上)'
            ],
            datasets: [{{
                label: 'スコア10pt上昇時の選択倍率 (オッズ比)',
                data: [
                    {fmt_num(reg['free']['company']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['company']['binary']['value_univ']['params']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['company']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['company']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['student']['multinomial']['value_univ']['めっちゃ知りたい']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['student']['binary']['value_univ']['params']['value_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['student']['multinomial']['personality_univ']['めっちゃ知りたい']['personality_fit']['or_10'], 3)},
                    {fmt_num(reg['free']['student']['binary']['personality_univ']['params']['personality_fit']['or_10'], 3)}
                ],
                backgroundColor: [
                    '#0D9488',
                    '#14B8A6',
                    '#CBD5E1',
                    '#94A3B8',
                    '#0284C7',
                    '#38BDF8',
                    '#D97706',
                    '#F59E0B'
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
            const labelSub = isHigh ? '<br><span style="font-size:10px;color:var(--gray-500);font-weight:normal;">(10名限定)</span>' : '';
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
            const labelSub = isHigh ? '<br><span style="font-size:10px;color:var(--gray-500);font-weight:normal;">(上限なし)</span>' : '';
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
        const ustechNote = c.name === '株式会社ユーズテック' 
            ? '<li style="color:#0369A1; background:#F0F9FF; padding:4px 8px; border-radius:4px; margin-top:4px;">※ 学生の当日回答が「未回答」かつ企業の当日回答が「知りたい」でマッチ成立となった例外1件（第6ターン：菊 泰聖さん）が含まれるため、学生「知りたい以上（8件）」に対してマッチ成立数が7件となっています。</li>' 
            : '';

        document.getElementById('cd-summary-text').innerHTML = `
            <ul>
                <li>総接触学生数 ${{c.count}}名中、マッチング成立は <strong>${{c.match_count}}件 (${{c.match_rate.toFixed(1)}}%)</strong> でした。</li>
                <li>企業アクションにおいて「知りたい以上」を選択した比率は <strong>${{c.company_actions['知りたい以上'].pct.toFixed(1)}}%</strong>、学生側から「知りたい以上」を受けた比率は <strong>${{c.student_actions['知りたい以上'].pct.toFixed(1)}}%</strong> です。</li>
                <li>${{diffText}}</li>
                ${{ustechNote}}
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

    // =============================================================
    // Company Table Sorting & Interactive Logic
    // =============================================================
    let currentSortKey = 'match_rate';
    let currentSortDir = 'desc';
    let currentPlanFilter = 'all';
    let selectedCompanyOrigIdx = 0;

    // Attach original index
    companiesData.forEach((c, idx) => {{
        c.origIndex = idx;
    }});

    function getSortValue(c, key) {{
        if (key === 'name') return c.name;
        if (key === 'is_paid') return c.is_paid;
        if (key === 'count') return c.count;
        if (key === 'match_count') return c.match_count;
        if (key === 'match_rate') return c.match_rate;
        if (key === 'v_mean') return c.v_mean !== null ? c.v_mean : -999;
        if (key === 'p_mean') return c.p_mean !== null ? c.p_mean : -999;
        if (key === 'comp_high') return c.company_actions['めっちゃ知りたい'].pct;
        if (key === 'comp_plus') return c.company_actions['知りたい以上'].pct;
        if (key === 'stud_high') return c.student_actions['めっちゃ知りたい'].pct;
        if (key === 'stud_plus') return c.student_actions['知りたい以上'].pct;
        return 0;
    }}

    function renderCompanyTable() {{
        const tbody = document.getElementById('company-table-body');
        if (!tbody) return;

        // Filter
        let list = companiesData.filter(c => {{
            if (currentPlanFilter === 'paid') return c.is_paid === 1;
            if (currentPlanFilter === 'free') return c.is_paid === 0;
            return true;
        }});

        // Sort
        list.sort((a, b) => {{
            let va = getSortValue(a, currentSortKey);
            let vb = getSortValue(b, currentSortKey);
            if (typeof va === 'string') {{
                return currentSortDir === 'asc' ? va.localeCompare(vb, 'ja') : vb.localeCompare(va, 'ja');
            }}
            return currentSortDir === 'asc' ? va - vb : vb - va;
        }});

        // Update headers icon
        const keys = ['name', 'is_paid', 'count', 'match_count', 'match_rate', 'v_mean', 'p_mean', 'comp_high', 'comp_plus', 'stud_high', 'stud_plus'];
        keys.forEach(k => {{
            const iconEl = document.getElementById('sort-icon-' + k);
            const thEl = iconEl ? iconEl.closest('th') : null;
            if (iconEl && thEl) {{
                if (k === currentSortKey) {{
                    thEl.classList.add('active-sort');
                    iconEl.innerText = currentSortDir === 'asc' ? '▲' : '▼';
                }} else {{
                    thEl.classList.remove('active-sort');
                    iconEl.innerText = '⇅';
                }}
            }}
        }});

        // Render rows
        let rowsHtml = '';
        list.forEach(c => {{
            const isSelected = c.origIndex === selectedCompanyOrigIdx;
            const planBadge = c.is_paid === 1 
                ? '<span class="pill pill-indigo">有料</span>' 
                : '<span class="pill pill-slate">無料</span>';
            const pMeanStr = c.p_mean !== null ? c.p_mean.toFixed(2) : '-';
            const vMeanStr = c.v_mean !== null ? c.v_mean.toFixed(2) : '-';

            rowsHtml += `<tr class="company-row ${{isSelected ? 'selected-company' : ''}}" onclick="selectCompany(${{c.origIndex}}, true)">
                <td><strong>${{c.name}}</strong></td>
                <td>${{planBadge}}</td>
                <td>${{c.count}}名</td>
                <td>${{c.match_count}}件</td>
                <td><strong>${{c.match_rate.toFixed(1)}}%</strong></td>
                <td>${{vMeanStr}}</td>
                <td>${{pMeanStr}}</td>
                <td>${{c.company_actions['めっちゃ知りたい'].count}}件 (${{c.company_actions['めっちゃ知りたい'].pct.toFixed(1)}}%)</td>
                <td>${{c.company_actions['知りたい以上'].count}}件 (${{c.company_actions['知りたい以上'].pct.toFixed(1)}}%)</td>
                <td>${{c.student_actions['めっちゃ知りたい'].count}}件 (${{c.student_actions['めっちゃ知りたい'].pct.toFixed(1)}}%)</td>
                <td>${{c.student_actions['知りたい以上'].count}}件 (${{c.student_actions['知りたい以上'].pct.toFixed(1)}}%)</td>
            </tr>`;
        }});
        tbody.innerHTML = rowsHtml;
    }}

    function handleCompanySort(key) {{
        if (currentSortKey === key) {{
            currentSortDir = currentSortDir === 'desc' ? 'asc' : 'desc';
        }} else {{
            currentSortKey = key;
            currentSortDir = (key === 'name' || key === 'is_paid') ? 'asc' : 'desc';
        }}
        // Sync quick sort dropdown
        const quickSelect = document.getElementById('company-quick-sort');
        const matchVal = currentSortKey + '_' + currentSortDir;
        if (quickSelect) {{
            for (let opt of quickSelect.options) {{
                if (opt.value === matchVal) {{
                    quickSelect.value = matchVal;
                    break;
                }}
            }}
        }}
        renderCompanyTable();
    }}

    function applyQuickSort(val) {{
        const parts = val.split('_');
        const dir = parts.pop();
        const key = parts.join('_');
        currentSortKey = key;
        currentSortDir = dir;
        renderCompanyTable();
    }}

    function setPlanFilter(plan, btnEl) {{
        currentPlanFilter = plan;
        document.querySelectorAll('.plan-filter-btn').forEach(b => b.classList.remove('active'));
        if (btnEl) btnEl.classList.add('active');
        renderCompanyTable();
    }}

    function initCompanySelect() {{
        const sel = document.getElementById('company-select');
        if (!sel) return;
        let optHtml = '';
        companiesData.forEach((c, idx) => {{
            const planText = c.is_paid === 1 ? '有料' : '無料';
            optHtml += `<option value="${{idx}}">${{c.name}} (${{planText}} | 成立率 ${{c.match_rate.toFixed(1)}}%)</option>`;
        }});
        sel.innerHTML = optHtml;
    }}

    function selectCompany(origIdx, shouldScroll = false) {{
        selectedCompanyOrigIdx = origIdx;
        const sel = document.getElementById('company-select');
        if (sel) sel.value = origIdx;
        renderCompanyTable();
        renderCompanyDetail(origIdx);

        if (shouldScroll) {{
            const card = document.getElementById('company-detail-card');
            if (card) {{
                card.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}
    }}

    function prevCompany() {{
        let cur = selectedCompanyOrigIdx;
        let prev = cur - 1;
        if (prev < 0) prev = companiesData.length - 1;
        selectCompany(prev, false);
    }}

    function nextCompany() {{
        let cur = selectedCompanyOrigIdx;
        let next = (cur + 1) % companiesData.length;
        selectCompany(next, false);
    }}

    // Init UI
    initCompanySelect();
    renderCompanyTable();
    renderCompanyDetail(0);
</script>


<!-- Raw CSV Data & Download Script -->
<script id="raw-csv-data" type="text/plain">
""" + raw_csv_text + """
</script>

<script>
function downloadRawCSV() {{
    try {{
        const csvEl = document.getElementById('raw-csv-data');
        const csvContent = csvEl ? csvEl.textContent.trim() : '';
        if (!csvContent) {{
            window.location.href = 'asobiba_fes_raw_data_313.csv';
            return;
        }}
        const bom = new Uint8Array([0xEF, 0xBB, 0xBF]);
        const blob = new Blob([bom, csvContent], {{ type: 'text/csv;charset=utf-8;' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ASOBIBA_FES_2026_全データ一覧_313件.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }} catch (err) {{
        console.error('Download error:', err);
        window.location.href = 'asobiba_fes_raw_data_313.csv';
    }}
}}
</script>
</body>
</html>'''

    with open('asobiba_fes_fit_analysis_report.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Successfully built asobiba_fes_fit_analysis_report.html with fixed layout!")

if __name__ == '__main__':
    build_html()

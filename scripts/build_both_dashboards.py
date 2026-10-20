#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, math, json
sys.path.append('scripts')
from analyze_fit_actions import load_and_preprocess_data, mean
from collections import defaultdict

with open('scripts/analysis_results.json') as f:
    d = json.load(f)

ov = d['overall']
p = d['paid_analysis']
fr = d['free_analysis']
cps = d['company_profiles']

def t_survival(t_val, df):
    if df <= 0 or math.isnan(df): return None
    x = df / (df + t_val * t_val)
    a = df / 2.0
    b = 0.5
    if x <= 0: return 1.0
    if x >= 1: return 0.0
    
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30: d = 1e-30
    d = 1.0 / d
    f = d
    for m in range(1, 200):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30: d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30: c = 1e-30
        d = 1.0 / d
        f *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30: d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30: c = 1e-30
        d = 1.0 / d
        del_val = d * c
        f *= del_val
        if abs(del_val - 1.0) < 1e-15:
            break
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    bt = math.exp(math.log(x) * a + math.log(1.0 - x) * b - lbeta)
    return bt * f / a

def f_survival(f_val, df1, df2):
    if f_val <= 0 or df1 <= 0 or df2 <= 0: return 1.0
    x = df2 / (df2 + df1 * f_val)
    a = df2 / 2.0
    b = df1 / 2.0
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30: d = 1e-30
    d = 1.0 / d
    f = d
    for m in range(1, 200):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30: d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30: c = 1e-30
        d = 1.0 / d
        f *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30: d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30: c = 1e-30
        d = 1.0 / d
        del_val = d * c
        f *= del_val
        if abs(del_val - 1.0) < 1e-15:
            break
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    bt = math.exp(math.log(x) * a + math.log(1.0 - x) * b - lbeta)
    return bt * f / a

def run_anova(groups):
    valid_groups = [g for g in groups if len(g) > 0]
    k = len(valid_groups)
    if k < 2:
        return {"status": "insufficient", "note": "比較群数不足 (1群のみ)"}
    n_total = sum(len(g) for g in valid_groups)
    all_vals = [x for g in valid_groups for x in g]
    grand_mean = sum(all_vals) / n_total
    ss_total = sum((x - grand_mean)**2 for x in all_vals)
    ss_between = sum(len(g) * (sum(g)/len(g) - grand_mean)**2 for g in valid_groups)
    ss_within = ss_total - ss_between
    df_between = k - 1
    df_within = n_total - k
    if df_within <= 0 or ss_within <= 0:
        return {"status": "insufficient", "note": "自由度不足"}
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within
    f_val = ms_between / ms_within
    pval = f_survival(f_val, df_between, df_within)
    eta2 = ss_between / ss_total if ss_total > 0 else 0.0
    return {
        "status": "ok",
        "f": round(f_val, 3),
        "df": f"({df_between}, {df_within})",
        "p": round(pval, 4) if pval is not None else 1.0,
        "eta2": round(eta2, 3)
    }

def run_welch_t(g1, g2):
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return {"status": "insufficient", "note": f"サンプル数不足 (n1={n1}, n2={n2})"}
    m1, m2 = sum(g1)/n1, sum(g2)/n2
    v1 = sum((x - m1)**2 for x in g1) / (n1 - 1)
    v2 = sum((x - m2)**2 for x in g2) / (n2 - 1)
    if v1 == 0 and v2 == 0:
        return {"status": "no_variance", "note": "分散ゼロ"}
    denom = v1/n1 + v2/n2
    if denom <= 0:
        return {"status": "error", "note": "分散推定不能"}
    se = math.sqrt(denom)
    t = (m1 - m2) / se
    df_num = denom**2
    df_den = ((v1/n1)**2 / (n1 - 1)) + ((v2/n2)**2 / (n2 - 1))
    df = df_num / df_den if df_den > 0 else 1.0
    pval = t_survival(abs(t), df)
    s_pooled = math.sqrt(((n1 - 1)*v1 + (n2 - 1)*v2) / (n1 + n2 - 2)) if (n1 + n2 - 2) > 0 else 1.0
    d = (m1 - m2) / s_pooled if s_pooled > 0 else 0.0
    diff = m1 - m2
    return {
        "status": "ok",
        "diff": round(diff, 2),
        "t": round(t, 3),
        "df": round(df, 1),
        "p": round(pval, 4) if pval is not None else 1.0,
        "d": round(abs(d), 3)
    }

# データロード
raw_data = load_and_preprocess_data()
comps = defaultdict(list)
for item in raw_data:
    comps[item['company']].append(item)

paid_companies = {
    '株式会社リード・イノベーション',
    '株式会社Unith Link',
    '株式会社ベル',
    'NTT 都市開発ホテルマネジメント株式会社　カペラ京都'
}

company_details = []

for c, rows in comps.items():
    is_paid = 1 if c in paid_companies else 0
    n = len(rows)
    matches = sum(r['is_matched'] for r in rows)
    match_rate = round(matches / n * 100, 1)
    
    vf_all = [r['value_fit'] for r in rows]
    pf_all = [r['personality_fit'] for r in rows if r['personality_fit'] is not None]
    
    # 企業アクション別
    c_acts = {}
    for a in ['なし', '知りたい', 'めっちゃ知りたい']:
        sub = [r for r in rows if r['company_action'] == a]
        vf = [r['value_fit'] for r in sub]
        pf = [r['personality_fit'] for r in sub if r['personality_fit'] is not None]
        c_acts[a] = {
            'count': len(sub),
            'v_mean': round(mean(vf), 2) if vf else None,
            'p_mean': round(mean(pf), 2) if pf else None
        }
    diff_v = None
    v_from_to = ''
    if c_acts['めっちゃ知りたい']['v_mean'] is not None and c_acts['なし']['v_mean'] is not None:
        diff_v = round(c_acts['めっちゃ知りたい']['v_mean'] - c_acts['なし']['v_mean'], 2)
        v_from_to = f"{c_acts['なし']['v_mean']} ➔ {c_acts['めっちゃ知りたい']['v_mean']}"
    elif c_acts['知りたい']['v_mean'] is not None and c_acts['なし']['v_mean'] is not None:
        diff_v = round(c_acts['知りたい']['v_mean'] - c_acts['なし']['v_mean'], 2)
        v_from_to = f"{c_acts['なし']['v_mean']} ➔ {c_acts['知りたい']['v_mean']}"
    elif c_acts['めっちゃ知りたい']['v_mean'] is not None and c_acts['知りたい']['v_mean'] is not None:
        diff_v = round(c_acts['めっちゃ知りたい']['v_mean'] - c_acts['知りたい']['v_mean'], 2)
        v_from_to = f"{c_acts['知りたい']['v_mean']} ➔ {c_acts['めっちゃ知りたい']['v_mean']}"
    c_acts['diff_v'] = diff_v
    c_acts['v_from_to'] = v_from_to
    
    # 企業アクション別 検定
    g_none_cv = [r['value_fit'] for r in rows if r['company_action'] == 'なし']
    g_know_cv = [r['value_fit'] for r in rows if r['company_action'] == '知りたい']
    g_very_cv = [r['value_fit'] for r in rows if r['company_action'] == 'めっちゃ知りたい']
    c_acts['test_v'] = {
        'anova': run_anova([g_none_cv, g_know_cv, g_very_cv]),
        't_very_none': run_welch_t(g_very_cv, g_none_cv),
        't_know_none': run_welch_t(g_know_cv, g_none_cv),
        't_very_know': run_welch_t(g_very_cv, g_know_cv)
    }
    
    if pf_all:
        g_none_cp = [r['personality_fit'] for r in rows if r['company_action'] == 'なし' and r['personality_fit'] is not None]
        g_know_cp = [r['personality_fit'] for r in rows if r['company_action'] == '知りたい' and r['personality_fit'] is not None]
        g_very_cp = [r['personality_fit'] for r in rows if r['company_action'] == 'めっちゃ知りたい' and r['personality_fit'] is not None]
        c_acts['test_p'] = {
            'has_data': True,
            'anova': run_anova([g_none_cp, g_know_cp, g_very_cp]),
            't_very_none': run_welch_t(g_very_cp, g_none_cp),
            't_know_none': run_welch_t(g_know_cp, g_none_cp),
            't_very_know': run_welch_t(g_very_cp, g_know_cp)
        }
    else:
        c_acts['test_p'] = {'has_data': False}
        
    # 学生アクション別
    s_acts = {}
    for a in ['なし', '知りたい', 'めっちゃ知りたい']:
        sub = [r for r in rows if r['student_action'] == a]
        vf = [r['value_fit'] for r in sub]
        pf = [r['personality_fit'] for r in sub if r['personality_fit'] is not None]
        s_acts[a] = {
            'count': len(sub),
            'v_mean': round(mean(vf), 2) if vf else None,
            'p_mean': round(mean(pf), 2) if pf else None
        }
    diff_p = None
    p_from_to = ''
    if s_acts['めっちゃ知りたい']['p_mean'] is not None and s_acts['なし']['p_mean'] is not None:
        diff_p = round(s_acts['めっちゃ知りたい']['p_mean'] - s_acts['なし']['p_mean'], 2)
        p_from_to = f"{s_acts['なし']['p_mean']} ➔ {s_acts['めっちゃ知りたい']['p_mean']}"
    elif s_acts['知りたい']['p_mean'] is not None and s_acts['なし']['p_mean'] is not None:
        diff_p = round(s_acts['知りたい']['p_mean'] - s_acts['なし']['p_mean'], 2)
        p_from_to = f"{s_acts['なし']['p_mean']} ➔ {s_acts['知りたい']['p_mean']}"
    elif s_acts['めっちゃ知りたい']['p_mean'] is not None and s_acts['知りたい']['p_mean'] is not None:
        diff_p = round(s_acts['めっちゃ知りたい']['p_mean'] - s_acts['知りたい']['p_mean'], 2)
        p_from_to = f"{s_acts['知りたい']['p_mean']} ➔ {s_acts['めっちゃ知りたい']['p_mean']}"
    s_acts['diff_p'] = diff_p
    s_acts['p_from_to'] = p_from_to
    
    # 学生アクション別 検定
    g_none_sv = [r['value_fit'] for r in rows if r['student_action'] == 'なし']
    g_know_sv = [r['value_fit'] for r in rows if r['student_action'] == '知りたい']
    g_very_sv = [r['value_fit'] for r in rows if r['student_action'] == 'めっちゃ知りたい']
    s_acts['test_v'] = {
        'anova': run_anova([g_none_sv, g_know_sv, g_very_sv]),
        't_very_none': run_welch_t(g_very_sv, g_none_sv),
        't_know_none': run_welch_t(g_know_sv, g_none_sv),
        't_very_know': run_welch_t(g_very_sv, g_know_sv)
    }
    
    if pf_all:
        g_none_sp = [r['personality_fit'] for r in rows if r['student_action'] == 'なし' and r['personality_fit'] is not None]
        g_know_sp = [r['personality_fit'] for r in rows if r['student_action'] == '知りたい' and r['personality_fit'] is not None]
        g_very_sp = [r['personality_fit'] for r in rows if r['student_action'] == 'めっちゃ知りたい' and r['personality_fit'] is not None]
        s_acts['test_p'] = {
            'has_data': True,
            'anova': run_anova([g_none_sp, g_know_sp, g_very_sp]),
            't_very_none': run_welch_t(g_very_sp, g_none_sp),
            't_know_none': run_welch_t(g_know_sp, g_none_sp),
            't_very_know': run_welch_t(g_very_sp, g_know_sp)
        }
    else:
        s_acts['test_p'] = {'has_data': False}
        
    # マッチ成立別
    m_yes = [r for r in rows if r['is_matched'] == 1]
    m_no = [r for r in rows if r['is_matched'] == 0]
    m_yes_v = [r['value_fit'] for r in m_yes]
    m_yes_p = [r['personality_fit'] for r in m_yes if r['personality_fit'] is not None]
    m_no_v = [r['value_fit'] for r in m_no]
    m_no_p = [r['personality_fit'] for r in m_no if r['personality_fit'] is not None]
    
    diff_m_v = round(mean(m_yes_v) - mean(m_no_v), 2) if (m_yes_v and m_no_v) else None
    diff_m_p = round(mean(m_yes_p) - mean(m_no_p), 2) if (m_yes_p and m_no_p) else None
    
    # マッチ成立別 検定
    t_match_v = run_welch_t(m_yes_v, m_no_v) if (m_yes_v and m_no_v) else {'status': 'insufficient', 'note': '成立群または未成立群が0件のため検定対象外'}
    t_match_p = run_welch_t(m_yes_p, m_no_p) if (m_yes_p and m_no_p) else {'status': 'insufficient', 'note': 'データ未算出または0件のため検定対象外'}
    
    match_factors = {
        'matched': {
            'count': len(m_yes),
            'v_mean': round(mean(m_yes_v), 2) if m_yes_v else None,
            'p_mean': round(mean(m_yes_p), 2) if m_yes_p else None
        },
        'unmatched': {
            'count': len(m_no),
            'v_mean': round(mean(m_no_v), 2) if m_no_v else None,
            'p_mean': round(mean(m_no_p), 2) if m_no_p else None
        },
        'diff_v': diff_m_v,
        'diff_p': diff_m_p,
        'test_v': t_match_v,
        'test_p': t_match_p
    }
    
    company_details.append({
        'company': c,
        'is_paid': is_paid,
        'plan_type': '有料出展' if is_paid else '無料出展',
        'count': n,
        'matches': matches,
        'match_rate': match_rate,
        'value_mean': round(mean(vf_all), 2),
        'personality_mean': round(mean(pf_all), 2) if pf_all else None,
        'company_actions': c_acts,
        'student_actions': s_acts,
        'match_factors': match_factors
    })

company_details.sort(key=lambda x: (not x['is_paid'], -x['match_rate']))

# 企業セレクターのボタン群HTML（選択肢A: ピルボタン群）
paid_buttons_html = ""
free_buttons_html = ""
company_options_html = ""

for idx, cd in enumerate(company_details):
    badge = "【有料】" if cd['is_paid'] else "【無料】"
    company_options_html += f'<option value="{idx}">{badge} {cd["company"]} (マッチ率 {cd["match_rate"]}%)</option>\n'
    
    btn_html = f"""<button type="button" id="comp-btn-{idx}" class="comp-nav-btn {'active' if idx == 0 else ''}" onclick="selectCompany({idx}, false)">
        <span class="btn-name">{cd['company']}</span>
        <span class="btn-rate">{cd['match_rate']}%</span>
    </button>"""
    
    if cd['is_paid']:
        paid_buttons_html += btn_html
    else:
        free_buttons_html += btn_html

company_details_json = json.dumps(company_details, ensure_ascii=False)

# Section HTML 定義
company_detail_section_html = f"""
    <!-- 企業選択ナビゲーションバー（有料4社 / 無料8社） -->
    <div class="section-card" style="margin-bottom: 20px; padding: 20px 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; margin-bottom: 16px;">
            <div>
                <div style="font-size: 16px; font-weight: 800; color: #1E293B;">🏢 分析対象企業の選択</div>
                <div style="font-size: 12.5px; color: #64748B; margin-top: 2px;">
                    企業ボタンまたはドロップダウンから選択すると、Tab 1・Tab 2 と同一の3本柱（推移・統計的仮説検定・マッチング要因）が即座に切り替わります。
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <label for="company-selector" style="font-size: 13px; font-weight: 700; color: #475569;">企業切替:</label>
                <select id="company-selector" onchange="selectCompany(parseInt(this.value), false)" style="padding: 6px 12px; font-size: 13px; font-weight: 600; border: 1px solid #CBD5E1; border-radius: 6px; background-color: #FFF; color: #1E293B; cursor: pointer; outline: none; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    {company_options_html}
                </select>
            </div>
        </div>

        <!-- 有料企業4社ボタン群 -->
        <div style="margin-bottom: 12px;">
            <div style="font-size: 11.5px; font-weight: 700; color: #4F46E5; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <span class="pill pill-indigo" style="font-size: 10px;">有料出展 4社</span>
                <span style="color: #64748B; font-weight: normal; font-size: 11px;">（バリュー高優先配席）</span>
            </div>
            <div class="comp-nav-container">
                {paid_buttons_html}
            </div>
        </div>

        <!-- 無料企業8社ボタン群 -->
        <div>
            <div style="font-size: 11.5px; font-weight: 700; color: #475569; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <span class="pill pill-slate" style="font-size: 10px;">無料出展 8社</span>
                <span style="color: #64748B; font-weight: normal; font-size: 11px;">（高低混合配席）</span>
            </div>
            <div class="comp-nav-container">
                {free_buttons_html}
            </div>
        </div>
    </div>

    <!-- 🔍 個別企業詳細カルテ -->
    <div id="company-detail-card" class="section-card" style="border-top: 4px solid var(--primary);">
        <div class="section-header" style="flex-wrap: wrap; gap: 12px; align-items: center;">
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                <div class="section-title" style="margin-bottom: 0;">
                    🔍 【個別カルテ】<span id="cd-comp-name" style="color: var(--primary);">株式会社ベル</span>
                </div>
                <span id="cd-comp-plan" class="pill pill-indigo">有料出展</span>
            </div>
            <div style="font-size: 12.5px; color: #64748B;">
                全体サマリー・層別比較と完全に同一の分析フレームワーク
            </div>
        </div>

        <!-- 4枚のトップKPIカード -->
        <div class="grid-4" style="margin-bottom: 24px;">
            <div class="kpi-card" style="padding: 16px;">
                <div class="kpi-title">接触学生数</div>
                <div class="kpi-value" style="font-size: 26px; color: #1E293B;" id="cd-kpi-count">29 <span style="font-size: 14px; font-weight: normal; color: #64748B;">名</span></div>
                <div class="kpi-sub" id="cd-kpi-matches-sub">うちマッチ成立 <strong>19</strong> 件</div>
            </div>
            <div class="kpi-card" style="padding: 16px;">
                <div class="kpi-title">マッチ成立率</div>
                <div class="kpi-value" style="font-size: 26px; color: var(--success);" id="cd-kpi-match-rate">65.5%</div>
                <div class="kpi-sub" id="cd-kpi-mr-rank">確定マッチング率</div>
            </div>
            <div class="kpi-card" style="padding: 16px;">
                <div class="kpi-title">バリューフィット平均</div>
                <div class="kpi-value" style="font-size: 26px; color: var(--primary);" id="cd-kpi-v-mean">62.10 <span style="font-size: 14px; font-weight: normal; color: #64748B;">pt</span></div>
                <div class="kpi-sub">接触全学生の理念適合度</div>
            </div>
            <div class="kpi-card" style="padding: 16px;">
                <div class="kpi-title">パーソナリティ平均</div>
                <div class="kpi-value" style="font-size: 26px; color: var(--warning);" id="cd-kpi-p-mean">80.44 <span style="font-size: 14px; font-weight: normal; color: #64748B;">pt</span></div>
                <div class="kpi-sub">接触全学生の人柄親和性</div>
            </div>
        </div>

        <!-- 2カラム推移（Tab 1 & 2 と全く同一の構造） -->
        <div class="grid-2">
            <!-- 左カラム: 企業アクション別推移 -->
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: #1E293B; font-size: 14px;">
                        🏢 企業アクション別：バリューとパーソナリティの推移
                    </div>
                    <span class="pill pill-indigo" style="font-size: 11px;">企業の選別行動</span>
                </div>
                <div style="height: 180px; position: relative; margin-bottom: 16px;">
                    <canvas id="chart-comp-act"></canvas>
                </div>
                <table style="font-size: 12px; margin-bottom: 12px;">
                    <thead>
                        <tr>
                            <th>アクション区分</th>
                            <th>件数</th>
                            <th>バリュー平均</th>
                            <th>パーソナリティ平均</th>
                            <th>選別感度</th>
                        </tr>
                    </thead>
                    <tbody id="cd-tbody-comp-act">
                    </tbody>
                </table>
                <div id="cd-comp-act-summary" style="font-size: 11.5px; padding: 8px 12px; background: #EEF2FF; border-left: 3px solid var(--primary); border-radius: 4px; color: #3730A3; margin-bottom: 14px;">
                </div>

                <!-- 統計的仮説検定アコーディオン（企業側） -->
                <details class="stats-accordion">
                    <summary class="stats-summary">
                        <span>📊 統計的仮説検定の詳細（ANOVA / Welch t検定）</span>
                        <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                    </summary>
                    <div class="stats-content">
                        <!-- ① バリューフィット検定 -->
                        <div style="margin-bottom: 6px; font-weight: 700; color: #1E293B; font-size: 12px;">
                            ① バリューフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                        </div>
                        <table style="margin-bottom: 14px; font-size: 11px;">
                            <thead>
                                <tr>
                                    <th>検定手法・対比</th>
                                    <th>統計量</th>
                                    <th>自由度 (df)</th>
                                    <th>有意確率 (p値)</th>
                                    <th>統計的判定</th>
                                </tr>
                            </thead>
                            <tbody id="cd-tbody-comp-test-v">
                            </tbody>
                        </table>

                        <!-- ② パーソナリティフィット検定 -->
                        <div style="margin-bottom: 6px; font-weight: 700; color: #1E293B; font-size: 12px;">
                            ② パーソナリティフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                        </div>
                        <table style="font-size: 11px;">
                            <thead>
                                <tr>
                                    <th>検定手法・対比</th>
                                    <th>統計量</th>
                                    <th>自由度 (df)</th>
                                    <th>有意確率 (p値)</th>
                                    <th>統計的判定</th>
                                </tr>
                            </thead>
                            <tbody id="cd-tbody-comp-test-p">
                            </tbody>
                        </table>
                    </div>
                </details>
            </div>

            <!-- 右カラム: 学生アクション別推移 -->
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: #1E293B; font-size: 14px;">
                        🎓 学生アクション別：バリューとパーソナリティの推移
                    </div>
                    <span class="pill pill-amber" style="font-size: 11px;">学生の志望行動</span>
                </div>
                <div style="height: 180px; position: relative; margin-bottom: 16px;">
                    <canvas id="chart-stud-act"></canvas>
                </div>
                <table style="font-size: 12px; margin-bottom: 12px;">
                    <thead>
                        <tr>
                            <th>アクション区分</th>
                            <th>件数</th>
                            <th>バリュー平均</th>
                            <th>パーソナリティ平均</th>
                            <th>反応感度</th>
                        </tr>
                    </thead>
                    <tbody id="cd-tbody-stud-act">
                    </tbody>
                </table>
                <div id="cd-stud-act-summary" style="font-size: 11.5px; padding: 8px 12px; background: #FEF3C7; border-left: 3px solid var(--warning); border-radius: 4px; color: #92400E; margin-bottom: 14px;">
                </div>

                <!-- 統計的仮説検定アコーディオン（学生側） -->
                <details class="stats-accordion">
                    <summary class="stats-summary">
                        <span>📊 統計的仮説検定の詳細（ANOVA / Welch t検定）</span>
                        <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                    </summary>
                    <div class="stats-content">
                        <!-- ① バリューフィット検定 -->
                        <div style="margin-bottom: 6px; font-weight: 700; color: #1E293B; font-size: 12px;">
                            ① バリューフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                        </div>
                        <table style="margin-bottom: 14px; font-size: 11px;">
                            <thead>
                                <tr>
                                    <th>検定手法・対比</th>
                                    <th>統計量</th>
                                    <th>自由度 (df)</th>
                                    <th>有意確率 (p値)</th>
                                    <th>統計的判定</th>
                                </tr>
                            </thead>
                            <tbody id="cd-tbody-stud-test-v">
                            </tbody>
                        </table>

                        <!-- ② パーソナリティフィット検定 -->
                        <div style="margin-bottom: 6px; font-weight: 700; color: #1E293B; font-size: 12px;">
                            ② パーソナリティフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                        </div>
                        <table style="font-size: 11px;">
                            <thead>
                                <tr>
                                    <th>検定手法・対比</th>
                                    <th>統計量</th>
                                    <th>自由度 (df)</th>
                                    <th>有意確率 (p値)</th>
                                    <th>統計的判定</th>
                                </tr>
                            </thead>
                            <tbody id="cd-tbody-stud-test-p">
                            </tbody>
                        </table>
                    </div>
                </details>
            </div>
        </div>

        <!-- 下部: マッチング成立要因分析 -->
        <div style="margin-top: 24px; background: #FFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-weight: 700; color: #1E293B; font-size: 14px;">
                    🤝 マッチング成立要因分析（マッチ成立群 vs 未成立群の実データ比較）
                </div>
                <span class="pill pill-green" style="font-size: 11px;">成立ドライバー検証</span>
            </div>
            <p style="font-size: 12.5px; color: #64748B; margin-bottom: 14px;">
                この企業でマッチングが成立した学生ペア（Yes）と不成立となった学生ペア（No）の間で、バリューおよびパーソナリティにどのような差が存在したかを直接比較します。
            </p>
            <table style="font-size: 12px; margin-bottom: 14px;">
                <thead>
                    <tr>
                        <th style="min-width: 140px;">マッチング状態</th>
                        <th>件数 (構成比)</th>
                        <th>バリューフィット平均</th>
                        <th>パーソナリティ平均</th>
                        <th>客観的示唆</th>
                    </tr>
                </thead>
                <tbody id="cd-tbody-match-factors">
                </tbody>
            </table>

            <!-- マッチング成立要因の統計的仮説検定（Welch t検定）アコーディオン -->
            <details class="stats-accordion" style="margin-bottom: 14px;">
                <summary class="stats-summary">
                    <span>📊 マッチング成立要因の統計的仮説検定（Welch t検定: 成約群 vs 未成立群）</span>
                    <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                </summary>
                <div class="stats-content">
                    <table style="font-size: 11.5px;">
                        <thead>
                            <tr>
                                <th>検証指標</th>
                                <th>検定手法</th>
                                <th>統計量</th>
                                <th>自由度 (df)</th>
                                <th>有意確率 (p値)</th>
                                <th>統計的判定</th>
                            </tr>
                        </thead>
                        <tbody id="cd-tbody-match-test">
                        </tbody>
                    </table>
                </div>
            </details>

            <div id="cd-match-summary" class="insight-box" style="margin-top: 0; font-size: 12.5px;">
            </div>
        </div>
    </div>
"""

# JavaScript 生成
js_template = """
    // ==========================================
    // 全12社個別カルテ 動的連動スクリプト (統計的仮説検定完全対応)
    // ==========================================
    const companyDetailsData = __COMPANY_DETAILS_JSON__;
    let compActChart = null;
    let studActChart = null;
    let tab3Initialized = false;

    function initCompanyDetailCharts() {
        if (!tab3Initialized) {
            selectCompany(0, false);
            tab3Initialized = true;
        } else {
            if (compActChart) compActChart.resize();
            if (studActChart) studActChart.resize();
        }
    }

    function renderTestTableRows(testData, hasData) {
        if (!hasData || !testData) {
            return '<tr><td colspan="5" style="text-align: center; color: #9CA3AF; padding: 10px;">データ未算出のため検定対象外</td></tr>';
        }
        let html = '';
        
        // ANOVA
        const anova = testData.anova;
        if (anova.status === 'ok') {
            const pStr = anova.p < 0.0001 ? 'p < 0.0001' : 'p = ' + anova.p.toFixed(4);
            const pBold = anova.p < 0.05 ? '<strong>' + pStr + '</strong>' : pStr;
            let pill = '<span class="pill pill-slate">有意差なし (η²=' + anova.eta2.toFixed(3) + ')</span>';
            if (anova.p < 0.01) pill = '<span class="pill pill-indigo">非常に有意 (**) [η²=' + anova.eta2.toFixed(3) + ']</span>';
            else if (anova.p < 0.05) pill = '<span class="pill pill-green">有意 (*) [η²=' + anova.eta2.toFixed(3) + ']</span>';
            else if (anova.p < 0.10) pill = '<span class="pill pill-amber">有意傾向 (†) [η²=' + anova.eta2.toFixed(3) + ']</span>';

            html += '<tr style="background: #F8FAFC;">' +
                '<td><strong>一元配置分散分析 (ANOVA)</strong></td>' +
                '<td>F = ' + anova.f.toFixed(3) + '</td>' +
                '<td>' + anova.df + '</td>' +
                '<td>' + pBold + '</td>' +
                '<td>' + pill + '</td>' +
            '</tr>';
        } else {
            html += '<tr style="background: #F8FAFC;">' +
                '<td><strong>一元配置分散分析 (ANOVA)</strong></td>' +
                '<td colspan="4" style="color: #64748B;">' + anova.note + '</td>' +
            '</tr>';
        }

        // Welch t検定 3対比
        const pairs = [
            { key: 't_very_none', label: 'Welch t検定 (なし vs めっちゃ知りたい)' },
            { key: 't_know_none', label: 'Welch t検定 (なし vs 知りたい)' },
            { key: 't_very_know', label: 'Welch t検定 (知りたい vs めっちゃ知りたい)' }
        ];

        pairs.forEach(p => {
            const t = testData[p.key];
            if (t.status === 'ok') {
                const pStr = t.p < 0.0001 ? 'p < 0.0001' : 'p = ' + t.p.toFixed(4);
                const pBold = t.p < 0.05 ? '<strong>' + pStr + '</strong>' : pStr;
                const sign = t.diff > 0 ? '+' : '';
                let pill = '<span class="pill pill-slate">有意差なし [差 ' + sign + t.diff.toFixed(2) + 'pt, d=' + t.d.toFixed(3) + ']</span>';
                if (t.p < 0.01) pill = '<span class="pill pill-indigo">非常に有意 (**) [差 ' + sign + t.diff.toFixed(2) + 'pt, d=' + t.d.toFixed(3) + ']</span>';
                else if (t.p < 0.05) pill = '<span class="pill pill-green">有意 (*) [差 ' + sign + t.diff.toFixed(2) + 'pt, d=' + t.d.toFixed(3) + ']</span>';
                else if (t.p < 0.10) pill = '<span class="pill pill-amber">有意傾向 (†) [差 ' + sign + t.diff.toFixed(2) + 'pt, d=' + t.d.toFixed(3) + ']</span>';

                html += '<tr>' +
                    '<td>' + p.label + '</td>' +
                    '<td>t = ' + t.t.toFixed(3) + '</td>' +
                    '<td>' + t.df.toFixed(1) + '</td>' +
                    '<td>' + pBold + '</td>' +
                    '<td>' + pill + '</td>' +
                '</tr>';
            } else {
                html += '<tr>' +
                    '<td>' + p.label + '</td>' +
                    '<td colspan="4" style="color: #64748B;">' + t.note + '</td>' +
                '</tr>';
            }
        });

        return html;
    }

    function renderMatchTestRow(test, label) {
        if (test.status === 'ok') {
            const pStr = test.p < 0.0001 ? 'p < 0.0001' : 'p = ' + test.p.toFixed(4);
            const pBold = test.p < 0.05 ? '<strong>' + pStr + '</strong>' : pStr;
            const sign = test.diff > 0 ? '+' : '';
            let pill = '<span class="pill pill-slate">有意差なし [差 ' + sign + test.diff.toFixed(2) + 'pt, d=' + test.d.toFixed(3) + ']</span>';
            if (test.p < 0.01) pill = '<span class="pill pill-indigo">非常に有意 (**) [差 ' + sign + test.diff.toFixed(2) + 'pt, d=' + test.d.toFixed(3) + ']</span>';
            else if (test.p < 0.05) pill = '<span class="pill pill-green">有意 (*) [差 ' + sign + test.diff.toFixed(2) + 'pt, d=' + test.d.toFixed(3) + ']</span>';
            else if (test.p < 0.10) pill = '<span class="pill pill-amber">有意傾向 (†) [差 ' + sign + test.diff.toFixed(2) + 'pt, d=' + test.d.toFixed(3) + ']</span>';

            return '<tr>' +
                '<td><strong>' + label + '</strong></td>' +
                '<td>Welch t検定 (成立群 vs 未成立群)</td>' +
                '<td>t = ' + test.t.toFixed(3) + '</td>' +
                '<td>' + test.df.toFixed(1) + '</td>' +
                '<td>' + pBold + '</td>' +
                '<td>' + pill + '</td>' +
            '</tr>';
        } else {
            return '<tr>' +
                '<td><strong>' + label + '</strong></td>' +
                '<td>Welch t検定 (成立群 vs 未成立群)</td>' +
                '<td colspan="4" style="color: #64748B;">' + test.note + '</td>' +
            '</tr>';
        }
    }

    function selectCompany(idx, shouldScroll) {
        if (idx < 0 || idx >= companyDetailsData.length) return;
        const cd = companyDetailsData[idx];

        // セレクターの同期
        const sel = document.getElementById('company-selector');
        if (sel && parseInt(sel.value) !== idx) sel.value = idx;

        // ピルボタンの同期
        document.querySelectorAll('.comp-nav-btn').forEach((btn, i) => {
            if (i === idx) btn.classList.add('active');
            else btn.classList.remove('active');
        });

        // ヘッダー情報
        const nameEl = document.getElementById('cd-comp-name');
        if (nameEl) nameEl.textContent = cd.company;
        const planEl = document.getElementById('cd-comp-plan');
        if (planEl) {
            planEl.className = cd.is_paid ? 'pill pill-indigo' : 'pill pill-slate';
            planEl.textContent = cd.plan_type;
        }

        // KPIカード
        const cntEl = document.getElementById('cd-kpi-count');
        if (cntEl) cntEl.innerHTML = cd.count + ' <span style="font-size: 14px; font-weight: normal; color: #64748B;">名</span>';
        
        const matchesSubEl = document.getElementById('cd-kpi-matches-sub');
        if (matchesSubEl) matchesSubEl.innerHTML = 'うちマッチ成立 <strong>' + cd.matches + '</strong> 件 (' + cd.match_rate + '%)';
        
        const mrEl = document.getElementById('cd-kpi-match-rate');
        if (mrEl) {
            mrEl.textContent = cd.match_rate + '%';
            mrEl.style.color = cd.match_rate >= 50 ? 'var(--success)' : (cd.match_rate >= 30 ? 'var(--primary)' : 'var(--danger)');
        }
        
        const vMeanEl = document.getElementById('cd-kpi-v-mean');
        if (vMeanEl) vMeanEl.innerHTML = cd.value_mean.toFixed(2) + ' <span style="font-size: 14px; font-weight: normal; color: #64748B;">pt</span>';
        
        const pMeanEl = document.getElementById('cd-kpi-p-mean');
        if (pMeanEl) {
            if (cd.personality_mean !== null) {
                pMeanEl.innerHTML = cd.personality_mean.toFixed(2) + ' <span style="font-size: 14px; font-weight: normal; color: #64748B;">pt</span>';
            } else {
                pMeanEl.innerHTML = '<span style="font-size: 18px; color: #9CA3AF;">未算出</span>';
            }
        }

        // テーブル生成: 企業アクション別
        const acts = ['なし', '知りたい', 'めっちゃ知りたい'];
        let compTbodyHtml = '';
        acts.forEach(a => {
            const item = cd.company_actions[a];
            const vStr = item.v_mean !== null ? item.v_mean.toFixed(2) : '—';
            const pStr = item.p_mean !== null ? item.p_mean.toFixed(2) : (cd.personality_mean === null ? '未算出' : '—');
            const isHighlight = a === 'めっちゃ知りたい' ? 'style="background: #F8FAFC; font-weight: 600;"' : '';
            const badge = a === 'めっちゃ知りたい' ? '<span class="pill pill-indigo" style="font-size: 10px; margin-left: 4px;">最優先</span>' : '';
            const baseNoneV = cd.company_actions['なし'].v_mean;
            let diffCol = '—';
            if (a === 'なし') {
                diffCol = '<span style="color: #64748B;">基準</span>';
            } else if (item.v_mean !== null && baseNoneV !== null) {
                const diffVal = item.v_mean - baseNoneV;
                const sign = diffVal > 0 ? '+' : '';
                const color = diffVal >= 4.0 ? 'color: var(--primary); font-weight: 700;' : (diffVal < 0 ? 'color: var(--danger); font-weight: 700;' : '');
                diffCol = '<span style="' + color + '">' + sign + diffVal.toFixed(2) + ' pt</span>';
            }
            compTbodyHtml += '<tr ' + isHighlight + '>' +
                '<td><strong>' + a + '</strong> ' + badge + '</td>' +
                '<td>' + item.count + '件</td>' +
                '<td><strong>' + vStr + '</strong></td>' +
                '<td>' + pStr + '</td>' +
                '<td>' + diffCol + '</td>' +
            '</tr>';
        });
        const compTbody = document.getElementById('cd-tbody-comp-act');
        if (compTbody) compTbody.innerHTML = compTbodyHtml;

        // 企業アクションサマリー
        const diffV = cd.company_actions.diff_v;
        let compSummaryHtml = '';
        if (diffV !== null) {
            const sign = diffV > 0 ? '+' : '';
            if (diffV >= 4.0) {
                compSummaryHtml = '<strong>🎯 鋭敏なバリュー選別:</strong> 「なし」から「めっちゃ知りたい」への移行でバリューが <strong>' + sign + diffV.toFixed(2) + ' pt</strong> 上昇（' + cd.company_actions.v_from_to + '）。理念適合度の高い学生を明確に見極めて評価しています。';
            } else if (diffV > 0) {
                compSummaryHtml = '<strong>⚖️ 穏やかなバリュー傾斜:</strong> アクション移行に伴うバリュー差は <strong>' + sign + diffV.toFixed(2) + ' pt</strong>（' + cd.company_actions.v_from_to + '）。母集団全体のベース水準を重視したアクション傾向です。';
            } else {
                compSummaryHtml = '<strong>⚠️ フラットな選別:</strong> アクション間でのバリュー差は <strong>' + diffV.toFixed(2) + ' pt</strong>（' + cd.company_actions.v_from_to + '）。理念スコア以外の個別要因（専門性や経験）を重視したアクションとなっています。';
            }
        } else {
            compSummaryHtml = '<strong>ℹ️ アクション状況:</strong> アクション区分の偏りにより差分算出対象外となります。';
        }
        const compSumEl = document.getElementById('cd-comp-act-summary');
        if (compSumEl) compSumEl.innerHTML = compSummaryHtml;

        // 企業検定テーブル展開
        const compTestVEl = document.getElementById('cd-tbody-comp-test-v');
        if (compTestVEl) compTestVEl.innerHTML = renderTestTableRows(cd.company_actions.test_v, true);
        
        const compTestPEl = document.getElementById('cd-tbody-comp-test-p');
        if (compTestPEl) compTestPEl.innerHTML = renderTestTableRows(cd.company_actions.test_p, cd.company_actions.test_p.has_data);

        // テーブル生成: 学生アクション別
        let studTbodyHtml = '';
        acts.forEach(a => {
            const item = cd.student_actions[a];
            const vStr = item.v_mean !== null ? item.v_mean.toFixed(2) : '—';
            const pStr = item.p_mean !== null ? item.p_mean.toFixed(2) : (cd.personality_mean === null ? '未算出' : '—');
            const isHighlight = a === 'めっちゃ知りたい' ? 'style="background: #F8FAFC; font-weight: 600;"' : '';
            const badge = a === 'めっちゃ知りたい' ? '<span class="pill pill-amber" style="font-size: 10px; margin-left: 4px;">熱望</span>' : '';
            const baseNoneP = cd.student_actions['なし'].p_mean;
            let diffCol = '—';
            if (cd.personality_mean === null) {
                diffCol = '<span style="color: #9CA3AF;">未算出</span>';
            } else if (a === 'なし') {
                diffCol = '<span style="color: #64748B;">基準</span>';
            } else if (item.p_mean !== null && baseNoneP !== null) {
                const diffVal = item.p_mean - baseNoneP;
                const sign = diffVal > 0 ? '+' : '';
                const color = diffVal >= 4.0 ? 'color: #D97706; font-weight: 700;' : (diffVal < 0 ? 'color: var(--danger); font-weight: 700;' : '');
                diffCol = '<span style="' + color + '">' + sign + diffVal.toFixed(2) + ' pt</span>';
            }
            studTbodyHtml += '<tr ' + isHighlight + '>' +
                '<td><strong>' + a + '</strong> ' + badge + '</td>' +
                '<td>' + item.count + '件</td>' +
                '<td>' + vStr + '</td>' +
                '<td><strong style="color: #D97706;">' + pStr + '</strong></td>' +
                '<td>' + diffCol + '</td>' +
            '</tr>';
        });
        const studTbody = document.getElementById('cd-tbody-stud-act');
        if (studTbody) studTbody.innerHTML = studTbodyHtml;

        // 学生アクションサマリー
        const diffP = cd.student_actions.diff_p;
        let studSummaryHtml = '';
        if (cd.personality_mean === null) {
            studSummaryHtml = '<strong>ℹ️ パーソナリティ未算出:</strong> 企業側の診断データが未登録のため、パーソナリティ親和性分析の対象外となります。';
        } else if (diffP !== null) {
            const sign = diffP > 0 ? '+' : '';
            if (diffP >= 4.0) {
                studSummaryHtml = '<strong>❤️ 高い人柄共鳴・共感:</strong> 学生が「めっちゃ知りたい」と希望した層はパーソナリティが <strong>' + sign + diffP.toFixed(2) + ' pt</strong> 上昇（' + cd.student_actions.p_from_to + '）。ブースで親和性を強く感じた学生が集まっています。';
            } else if (diffP > 0) {
                studSummaryHtml = '<strong>⚖️ 安定したパーソナリティ反応:</strong> 希望度に応じたパーソナリティ差は <strong>' + sign + diffP.toFixed(2) + ' pt</strong>（' + cd.student_actions.p_from_to + '）。幅広い学生から好意的に受け止められています。';
            } else {
                studSummaryHtml = '<strong>⚠️ 認知・事業興味先行:</strong> パーソナリティ差は <strong>' + diffP.toFixed(2) + ' pt</strong>。性格特性の一致よりも、事業内容や知名度を動機とした希望傾向が見られます。';
            }
        } else {
            studSummaryHtml = '<strong>ℹ️ アクション状況:</strong> アクション区分の偏りにより差分算出対象外となります。';
        }
        const studSumEl = document.getElementById('cd-stud-act-summary');
        if (studSumEl) studSumEl.innerHTML = studSummaryHtml;

        // 学生検定テーブル展開
        const studTestVEl = document.getElementById('cd-tbody-stud-test-v');
        if (studTestVEl) studTestVEl.innerHTML = renderTestTableRows(cd.student_actions.test_v, true);
        
        const studTestPEl = document.getElementById('cd-tbody-stud-test-p');
        if (studTestPEl) studTestPEl.innerHTML = renderTestTableRows(cd.student_actions.test_p, cd.student_actions.test_p.has_data);

        // テーブル生成: マッチング成立要因
        const mf = cd.match_factors;
        let matchTbodyHtml = '';
        const mYesV = mf.matched.v_mean !== null ? mf.matched.v_mean.toFixed(2) : '—';
        const mYesP = mf.matched.p_mean !== null ? mf.matched.p_mean.toFixed(2) : (cd.personality_mean === null ? '未算出' : '—');
        const mNoV = mf.unmatched.v_mean !== null ? mf.unmatched.v_mean.toFixed(2) : '—';
        const mNoP = mf.unmatched.p_mean !== null ? mf.unmatched.p_mean.toFixed(2) : (cd.personality_mean === null ? '未算出' : '—');
        
        const diffMVStr = mf.diff_v !== null ? (mf.diff_v >= 0 ? '+' : '') + mf.diff_v.toFixed(2) + ' pt' : '—';
        const diffMPStr = mf.diff_p !== null ? (mf.diff_p >= 0 ? '+' : '') + mf.diff_p.toFixed(2) + ' pt' : (cd.personality_mean === null ? '未算出' : '—');

        matchTbodyHtml += '<tr style="background: #F0FDF4;">' +
            '<td><strong>👑 マッチ成立群 (Yes)</strong></td>' +
            '<td><strong style="color: var(--success);">' + mf.matched.count + '件</strong> (' + (mf.matched.count / cd.count * 100).toFixed(1) + '%)</td>' +
            '<td><strong style="color: var(--primary); font-size: 13px;">' + mYesV + '</strong></td>' +
            '<td><strong style="color: #D97706; font-size: 13px;">' + mYesP + '</strong></td>' +
            '<td>双方の評価が合致し成約した層</td>' +
        '</tr>' +
        '<tr>' +
            '<td>❌ マッチ未成立群 (No)</td>' +
            '<td>' + mf.unmatched.count + '件 (' + (mf.unmatched.count / cd.count * 100).toFixed(1) + '%)</td>' +
            '<td>' + mNoV + '</td>' +
            '<td>' + mNoP + '</td>' +
            '<td>いずれか一方または双方が見送った層</td>' +
        '</tr>' +
        '<tr style="background: #F8FAFC; font-weight: 700; border-top: 2px solid #CBD5E1;">' +
            '<td>📊 差分 (成立群 − 未成立群)</td>' +
            '<td>—</td>' +
            '<td style="color: ' + (mf.diff_v !== null && mf.diff_v >= 3.0 ? 'var(--primary)' : '#1E293B') + ';">' + diffMVStr + '</td>' +
            '<td style="color: ' + (mf.diff_p !== null && mf.diff_p >= 3.0 ? '#D97706' : '#1E293B') + ';">' + diffMPStr + '</td>' +
            '<td>成約ペアの際立った特徴</td>' +
        '</tr>';
        const matchTbody = document.getElementById('cd-tbody-match-factors');
        if (matchTbody) matchTbody.innerHTML = matchTbodyHtml;

        // マッチング検定テーブル展開
        const matchTestEl = document.getElementById('cd-tbody-match-test');
        if (matchTestEl) {
            let mTestHtml = '';
            mTestHtml += renderMatchTestRow(mf.test_v, 'バリューフィット');
            mTestHtml += renderMatchTestRow(mf.test_p, 'パーソナリティ親和性');
            matchTestEl.innerHTML = mTestHtml;
        }

        // マッチ要因サマリー
        let matchSummaryHtml = '';
        if (cd.matches === 0) {
            matchSummaryHtml = '<strong>⚠️ マッチ成立なし:</strong> この企業では今回のイベントでマッチングが成立しませんでした（0件）。企業側または学生側のアクション基準を見直す必要があります。';
        } else {
            let vPart = '';
            if (mf.diff_v !== null) {
                if (mf.diff_v >= 3.0) vPart = 'バリュー適合度（差 <strong>+' + mf.diff_v.toFixed(2) + ' pt</strong>）が決定打';
                else if (mf.diff_v > 0) vPart = 'バリュー差 <strong>+' + mf.diff_v.toFixed(2) + ' pt</strong>';
                else vPart = 'バリュー差 <strong>' + mf.diff_v.toFixed(2) + ' pt</strong>';
            }
            let pPart = '';
            if (cd.personality_mean === null) {
                pPart = 'パーソナリティは未算出';
            } else if (mf.diff_p !== null) {
                if (mf.diff_p >= 3.0) pPart = 'パーソナリティ親和性（差 <strong>+' + mf.diff_p.toFixed(2) + ' pt</strong>）が強力な推進力';
                else if (mf.diff_p > 0) pPart = 'パーソナリティ差 <strong>+' + mf.diff_p.toFixed(2) + ' pt</strong>';
                else pPart = 'パーソナリティ差 <strong>' + mf.diff_p.toFixed(2) + ' pt</strong>';
            }
            matchSummaryHtml = '<strong>🎯 マッチング成立の主要因:</strong> 成約に至った学生ペアは、未成立ペアと比較して ' + vPart + (pPart ? '、' + pPart : '') + ' となっており、相互の適合度に基づく自然な合意形成が確認されます。';
        }
        const matchSumEl = document.getElementById('cd-match-summary');
        if (matchSumEl) matchSumEl.innerHTML = matchSummaryHtml;

        // グラフ更新 (Chart.js)
        updateDetailCharts(cd);

        // スムーススクロール
        if (shouldScroll) {
            const target = document.getElementById('company-detail-card');
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }

    function updateDetailCharts(cd) {
        const labels = ['なし', '知りたい', 'めっちゃ知りたい'];
        
        // 企業アクション別チャート
        const compCtx = document.getElementById('chart-comp-act');
        if (compCtx) {
            if (compActChart) compActChart.destroy();
            
            const compVData = labels.map(l => cd.company_actions[l].v_mean);
            const compPData = labels.map(l => cd.company_actions[l].p_mean);
            
            const datasets = [
                {
                    label: 'バリューフィット',
                    data: compVData,
                    backgroundColor: 'rgba(79, 70, 229, 0.85)',
                    borderColor: '#4F46E5',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ];
            if (cd.personality_mean !== null) {
                datasets.push({
                    label: 'パーソナリティ',
                    data: compPData,
                    backgroundColor: 'rgba(156, 163, 175, 0.7)',
                    borderColor: '#9CA3AF',
                    borderWidth: 1,
                    borderRadius: 4
                });
            }
            
            compActChart = new Chart(compCtx, {
                type: 'bar',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 45,
                            max: 95,
                            grid: { color: '#F1F5F9' }
                        },
                        x: { grid: { display: false } }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: function(c) {
                                    return c.dataset.label + ': ' + (c.raw !== null ? c.raw.toFixed(2) + ' pt' : '未算出');
                                }
                            }
                        }
                    }
                }
            });
        }

        // 学生アクション別チャート
        const studCtx = document.getElementById('chart-stud-act');
        if (studCtx) {
            if (studActChart) studActChart.destroy();
            
            const studVData = labels.map(l => cd.student_actions[l].v_mean);
            const studPData = labels.map(l => cd.student_actions[l].p_mean);
            
            const datasets = [
                {
                    label: 'バリューフィット',
                    data: studVData,
                    backgroundColor: 'rgba(156, 163, 175, 0.7)',
                    borderColor: '#9CA3AF',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ];
            if (cd.personality_mean !== null) {
                datasets.push({
                    label: 'パーソナリティ',
                    data: studPData,
                    backgroundColor: 'rgba(217, 119, 6, 0.85)',
                    borderColor: '#D97706',
                    borderWidth: 1,
                    borderRadius: 4
                });
            }
            
            studActChart = new Chart(studCtx, {
                type: 'bar',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 45,
                            max: 95,
                            grid: { color: '#F1F5F9' }
                        },
                        x: { grid: { display: false } }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: function(c) {
                                    return c.dataset.label + ': ' + (c.raw !== null ? c.raw.toFixed(2) + ' pt' : '未算出');
                                }
                            }
                        }
                    }
                }
            });
        }
    }
"""
company_detail_js = js_template.replace('__COMPANY_DETAILS_JSON__', company_details_json)

print("Full Tab 3 components built successfully.")
print("HTML length:", len(company_detail_section_html))
print("JS length:", len(company_detail_js))



# ============================================================
# 1. asobiba_fes_fit_analysis_report.html (タブ統合版)
# ============================================================
tab_dashboard_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASOBIBA FES 2026: バリュー・パーソナリティ別マッチング分析ダッシュボード</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #4F46E5;
            --primary-light: #EEF2FF;
            --success: #10B981;
            --success-light: #ECFDF5;
            --warning: #F59E0B;
            --danger: #EF4444;
            --gray-50: #F9FAFB;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-700: #374151;
            --gray-800: #1F2937;
            --gray-900: #111827;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--gray-50);
            color: var(--gray-800);
            line-height: 1.6;
            padding: 24px;
        }}
        .container {{
            max-width: 1240px;
            margin: 0 auto;
        }}
        header {{
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            padding: 32px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
        }}
        header h1 {{
            font-size: 26px;
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }}
        header p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .badge-bar {{
            display: flex;
            gap: 10px;
            margin-top: 16px;
            flex-wrap: wrap;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(4px);
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .btn-header {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 18px;
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 8px;
            color: white;
            text-decoration: none;
            font-size: 13px;
            font-weight: 700;
            transition: all 0.2s;
        }}
        .btn-header:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }}

        /* Tabs Navigation */
        .tab-bar {{
            display: flex;
            gap: 8px;
            background: white;
            padding: 8px;
            border-radius: 12px;
            border: 1px solid var(--gray-200);
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            flex-wrap: wrap;
        }}
        .tab-btn {{
            padding: 10px 20px;
            border-radius: 8px;
            border: none;
            background: transparent;
            font-size: 14px;
            font-weight: 700;
            color: var(--gray-700);
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .tab-btn:hover {{
            background: var(--gray-100);
            color: var(--gray-900);
        }}
        .tab-btn.active {{
            background: var(--primary);
            color: white;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
        }}
        .tab-pane {{
            display: none;
        }}
        .tab-pane.active {{
            display: block;
        }}

        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: white;
            padding: 20px 24px;
            border-radius: 12px;
            border: 1px solid var(--gray-200);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .kpi-title {{
            font-size: 13px;
            font-weight: 600;
            color: var(--gray-700);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 28px;
            font-weight: 800;
            color: var(--gray-900);
        }}
        .kpi-sub {{
            font-size: 12px;
            color: #6B7280;
            margin-top: 4px;
        }}
        .section-card {{
            background: white;
            border-radius: 14px;
            border: 1px solid var(--gray-200);
            padding: 28px;
            margin-bottom: 28px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--gray-100);
            padding-bottom: 14px;
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-title::before {{
            content: "";
            display: inline-block;
            width: 4px;
            height: 18px;
            background: var(--primary);
            border-radius: 2px;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
            gap: 24px;
        }}
        .chart-box {{
            position: relative;
            height: 280px;
            width: 100%;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 12px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--gray-200);
        }}
        th {{
            background: var(--gray-50);
            font-weight: 600;
            color: var(--gray-700);
        }}
        .highlight-row {{
            background: #FEF3C7;
            font-weight: 600;
        }}
        .pill {{
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }}
        .pill-indigo {{ background: #E0E7FF; color: #4338CA; }}
        .pill-green {{ background: #D1FAE5; color: #065F46; }}
        .pill-amber {{ background: #FEF3C7; color: #92400E; }}
        .pill-rose {{ background: #FFE4E6; color: #BE123C; }}
        .pill-slate {{ background: #F1F5F9; color: #475569; }}
        
        .company-table-row:hover {{
            background-color: #F1F5F9 !important;
        }}
        .company-table-row.selected-row {{
            background-color: #EEF2FF !important;
        }}
        
        .matrix-table {{
            width: 100%;
            border: 2px solid var(--gray-200);
            border-radius: 8px;
            overflow: hidden;
            text-align: center;
        }}
        .matrix-table th {{
            text-align: center;
            padding: 10px;
            font-size: 12px;
        }}
        .matrix-cell {{
            padding: 14px 10px;
            border: 1px solid var(--gray-200);
            vertical-align: middle;
            transition: all 0.2s;
        }}
        .cell-rate {{
            font-size: 20px;
            font-weight: 800;
            margin-bottom: 2px;
        }}
        .cell-sub {{
            font-size: 11px;
            color: #4B5563;
        }}
        .heat-high {{ background-color: #D1FAE5; color: #065F46; }}
        .heat-mid-high {{ background-color: #ECFDF5; color: #047857; }}
        .heat-mid {{ background-color: #FEF3C7; color: #92400E; }}
        .heat-low {{ background-color: #FEE2E2; color: #991B1B; }}

        .insight-box {{
            background: var(--primary-light);
            border-left: 4px solid var(--primary);
            padding: 16px 20px;
            border-radius: 0 8px 8px 0;
            margin-top: 16px;
            font-size: 14px;
            color: #3730A3;
        }}
        .insight-box strong {{
            color: #1E1B4B;
        }}

        /* Stats Accordion */
        .stats-accordion {{
            margin-top: 14px;
            background: #F8FAFC;
            border: 1px solid var(--gray-200);
            border-radius: 8px;
            font-size: 12.5px;
            overflow: hidden;
            transition: all 0.2s ease;
        }}
        .stats-accordion[open] {{
            background: #FFFFFF;
            border-color: #CBD5E1;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }}
        .stats-summary {{
            padding: 10px 14px;
            font-weight: 700;
            color: #334155;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #F8FAFC;
            border-radius: 8px;
            transition: background 0.15s ease;
        }}
        .stats-summary:hover {{
            background: #F1F5F9;
            color: #0F172A;
        }}
        .stats-content {{
            padding: 12px 14px;
            border-top: 1px solid #E2E8F0;
            line-height: 1.6;
            color: #334155;
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <div>
            <h1>ASOBIBA FES 2026: バリュー・パーソナリティ別マッチング分析ダッシュボード</h1>
            <p>ミッションラリー全313接触における企業・学生のアクション特性、層別比較、全12社個別カルテ</p>
            <div class="badge-bar">
                <span class="badge">総接触数: {ov['count']}件</span>
                <span class="badge">マッチ成立: {ov['match_count']}件 ({ov['match_rate']}%)</span>
                <span class="badge">有料企業: 4社 (122接触 / マッチ率 {p['match_rate']}%)</span>
                <span class="badge">無料企業: 8社 (191接触 / マッチ率 {fr['match_rate']}%)</span>
                <span class="badge">パーソナリティ有効: {ov['valid_p_count']}件</span>
            </div>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a href="company_fit_report.html" class="btn-header" style="background: rgba(16, 185, 129, 0.3); border-color: rgba(16, 185, 129, 0.6);">
                🏢 企業別・有料無料別専用ページを開く
            </a>
            <a href="index.html" class="btn-header">
                🏠 総合ダッシュボードへ戻る
            </a>
        </div>
    </header>

    <!-- Tab Bar -->
    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('tab-overall')">
            <span>📊</span> 1. 全体分析サマリー (課題1〜3)
        </button>
        <button class="tab-btn" onclick="switchTab('tab-paid-free')">
            <span>⚖️</span> 2. 有料企業 vs 無料企業 比較
        </button>
        <button class="tab-btn" onclick="switchTab('tab-companies')">
            <span>🏢</span> 3. 全12社 個別カルテ・一覧
        </button>
    </div>

    <!-- ========================================== -->
    <!-- TAB 1: 全体分析サマリー (元のダッシュボード完全維持) -->
    <!-- ========================================== -->
    <div id="tab-overall" class="tab-pane active">
        <!-- Top KPI Cards: 基本統計量 -->
        <div class="grid-4">
            <div class="kpi-card">
                <div class="kpi-title">バリューフィット 平均値</div>
                <div class="kpi-value">60.70</div>
                <div class="kpi-sub">中央値: <strong>61.34</strong> (N=313)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">バリューフィット 標準偏差</div>
                <div class="kpi-value">±7.80</div>
                <div class="kpi-sub">範囲: <strong>40.68 〜 78.43</strong></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">パーソナリティ 平均値</div>
                <div class="kpi-value">78.88</div>
                <div class="kpi-sub">中央値: <strong>79.50</strong> (N=286)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">パーソナリティ 標準偏差</div>
                <div class="kpi-value">±8.38</div>
                <div class="kpi-sub">範囲: <strong>53.64 〜 98.14</strong></div>
            </div>
        </div>

        <!-- Section 1 & 2: Company vs Student -->
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">【課題1 & 2】企業と学生の「評価軸の非対称性（ギャップ）」</div>
                <span class="pill pill-indigo">統計分析: ANOVA / Welch t検定</span>
            </div>
            <div class="grid-2">
                <div>
                    <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">🏢 企業アクション別：バリューが綺麗な右肩上がり</h3>
                    <div class="chart-box">
                        <canvas id="companyChart"></canvas>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>企業アクション</th>
                                <th>件数</th>
                                <th>バリュー平均</th>
                                <th>パーソナリティ平均</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>なし</td>
                                <td>97件</td>
                                <td>57.84</td>
                                <td>78.41</td>
                            </tr>
                            <tr>
                                <td>知りたい</td>
                                <td>145件</td>
                                <td>61.11</td>
                                <td>79.53</td>
                            </tr>
                            <tr class="highlight-row">
                                <td><strong>めっちゃ知りたい (10枠限定)</strong></td>
                                <td>71件</td>
                                <td><strong>63.79</strong></td>
                                <td>78.13</td>
                            </tr>
                        </tbody>
                    </table>
                    <details class="stats-accordion">
                        <summary class="stats-summary">
                            <span>📊 統計的仮説検定の詳細（ANOVA / Welch t検定）</span>
                            <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                        </summary>
                        <div class="stats-content">
                            <!-- ① バリューフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ① バリューフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="margin-bottom: 14px; font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>分析対象</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">全体<br><span style="font-size: 10px; color: #64748B;">(N=313)</span></td>
                                        <td><strong>一元配置分散分析 (ANOVA)</strong></td>
                                        <td>F = 13.263</td>
                                        <td>(2, 310)</td>
                                        <td><strong>p &lt; 0.0001</strong></td>
                                        <td><span class="pill pill-indigo">極めて有意 (***) [η²=0.079]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td><strong>Welch t検定 (なし vs めっちゃ知りたい)</strong></td>
                                        <td>t = -5.312</td>
                                        <td>153.1</td>
                                        <td><strong>p &lt; 0.0001</strong></td>
                                        <td><span class="pill pill-indigo">極めて有意 (***) [差 +5.95pt, d=0.826]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td><strong>Welch t検定 (なし vs 知りたい)</strong></td>
                                        <td>t = -3.322</td>
                                        <td>216.4</td>
                                        <td><strong>p = 0.0010</strong></td>
                                        <td><span class="pill pill-indigo">極めて有意 (***) [差 +3.27pt, d=0.429]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td><strong>Welch t検定 (知りたい vs めっちゃ知りたい)</strong></td>
                                        <td>t = -2.513</td>
                                        <td>152.5</td>
                                        <td><strong>p = 0.0130</strong></td>
                                        <td><span class="pill pill-green">有意 (*) [差 +2.68pt, d=0.352]</span></td>
                                    </tr>
                                </tbody>
                            </table>

                            <!-- ② パーソナリティフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ② パーソナリティフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="margin-bottom: 12px; font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>分析対象</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">全体<br><span style="font-size: 10px; color: #64748B;">(N=286)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 0.817</td>
                                        <td>(2, 283)</td>
                                        <td>p = 0.4463</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.006)</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = 0.212</td>
                                        <td>146.0</td>
                                        <td>p = 0.8327</td>
                                        <td>有意差なし [差 -0.28pt, d=0.035]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -0.931</td>
                                        <td>165.7</td>
                                        <td>p = 0.3533</td>
                                        <td>有意差なし [差 +1.12pt, d=0.130]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = 1.184</td>
                                        <td>159.2</td>
                                        <td>p = 0.2380</td>
                                        <td>有意差なし [差 -1.40pt, d=0.166]</td>
                                    </tr>
                                </tbody>
                            </table>

                            <div style="padding: 8px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 11.5px; color: #475569; display: flex; align-items: center; justify-content: space-between;">
                                <span>⚖️ 有料企業 vs 無料企業の詳細な層別検定は、別タブにてご確認いただけます。</span>
                                <button onclick="switchTab('tab-paid-free')" style="background: #4F46E5; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; cursor: pointer;">
                                    有料 vs 無料 比較へ ➔
                                </button>
                            </div>
                        </div>
                    </details>
                </div>
                <div>
                    <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">🎓 学生アクション別：パーソナリティが右肩上がり</h3>
                    <div class="chart-box">
                        <canvas id="studentChart"></canvas>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>学生アクション</th>
                                <th>件数</th>
                                <th>バリュー平均</th>
                                <th>パーソナリティ平均</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>なし</td>
                                <td>139件</td>
                                <td>59.96</td>
                                <td>78.08</td>
                            </tr>
                            <tr>
                                <td>知りたい</td>
                                <td>134件</td>
                                <td>61.48</td>
                                <td>79.23</td>
                            </tr>
                            <tr class="highlight-row">
                                <td><strong>めっちゃ知りたい (無制限)</strong></td>
                                <td>40件</td>
                                <td>60.67</td>
                                <td><strong>80.78</strong></td>
                            </tr>
                        </tbody>
                    </table>
                    <details class="stats-accordion">
                        <summary class="stats-summary">
                            <span>📊 統計的仮説検定の詳細（ANOVA / Welch t検定）</span>
                            <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                        </summary>
                        <div class="stats-content">
                            <!-- ① バリューフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ① バリューフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="margin-bottom: 14px; font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>分析対象</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">全体<br><span style="font-size: 10px; color: #64748B;">(N=313)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 1.305</td>
                                        <td>(2, 310)</td>
                                        <td>p = 0.2720</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.008)</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = -0.487</td>
                                        <td>60.1</td>
                                        <td>p = 0.6279</td>
                                        <td>有意差なし [差 +0.71pt, d=0.091]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -1.629</td>
                                        <td>270.7</td>
                                        <td>p = 0.1044</td>
                                        <td>有意差なし [差 +1.52pt, d=0.197]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = 0.554</td>
                                        <td>60.8</td>
                                        <td>p = 0.5813</td>
                                        <td>有意差なし [差 -0.81pt, d=0.104]</td>
                                    </tr>
                                </tbody>
                            </table>

                            <!-- ② パーソナリティフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ② パーソナリティフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="margin-bottom: 12px; font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>分析対象</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">全体<br><span style="font-size: 10px; color: #64748B;">(N=286)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 1.558</td>
                                        <td>(2, 283)</td>
                                        <td>p = 0.2105</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.011)</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = -1.732</td>
                                        <td>51.7</td>
                                        <td>p = 0.0893</td>
                                        <td><span class="pill pill-amber">有意傾向 (†) [差 +2.70pt, d=0.323]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -1.081</td>
                                        <td>248.6</td>
                                        <td>p = 0.2810</td>
                                        <td>有意差なし [差 +1.15pt, d=0.136]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = -0.985</td>
                                        <td>53.7</td>
                                        <td>p = 0.3290</td>
                                        <td>有意差なし [差 +1.55pt, d=0.187]</td>
                                    </tr>
                                </tbody>
                            </table>

                            <div style="padding: 8px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 11.5px; color: #475569; display: flex; align-items: center; justify-content: space-between;">
                                <span>⚖️ 有料企業 vs 無料企業の詳細な層別検定は、別タブにてご確認いただけます。</span>
                                <button onclick="switchTab('tab-paid-free')" style="background: #4F46E5; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; cursor: pointer;">
                                    有料 vs 無料 比較へ ➔
                                </button>
                            </div>
                        </div>
                    </details>
                </div>
            </div>

            <div class="insight-box">
                <strong>💡 インサイト（すれ違いの構造）:</strong><br>
                企業は理念・カルチャー適合（バリュー）をプロの目で厳しく見極めてアクションしている一方、学生は短時間では抽象的な理念を理解できず、目の前のブース担当者の「人柄・共感・話しやすさ（パーソナリティ）」に直感的に惹かれてアクションしています。
            </div>
        </div>

        <!-- Section: Quantitative x Qualitative Analysis -->
        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">🎯 【要因分析】量的データ（各フィット度スコア） × 質的データ（アクション選択）の統計的仮説検定</div>
                    <div style="font-size: 13px; color: #64748B; margin-top: 4px; font-weight: normal;">
                        各アクション（質的データ：なし / 知りたい / めっちゃ知りたい）と各フィット度スコア（量的データ）の関係性を、ANOVA・Welch t検定全3対比・ロジスティック回帰全3対比で網羅的に検証
                    </div>
                </div>
                <span class="pill pill-indigo">量的データ × 質的データ（統計検定網羅）</span>
            </div>

            <!-- ブロック1: 🏢 企業アクション (質的) × バリュー & パーソナリティ (量的) -->
            <div style="margin-bottom: 28px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px;">
                    <h3 style="font-size: 16px; font-weight: 700; color: #1E293B; margin: 0; display: flex; align-items: center; gap: 8px;">
                        <span>🏢</span> 企業アクションに対する要因分析：バリュー（理念・能力） vs パーソナリティ（人柄）
                    </h3>
                    <span class="pill pill-green">バリューのみ極めて有意 (p &lt; 0.0001***) / パーソナリティ無関係 (全検定で有意差なし)</span>
                </div>

                <!-- 企業側 検定テーブル -->
                <table>
                    <thead>
                        <tr>
                            <th style="width: 14%;">評価指標（量的）</th>
                            <th style="width: 18%;">一元配置分散分析 (ANOVA)<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">群間全体の差</span></th>
                            <th style="width: 32%;">Welchのt検定（全3対比）<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">アクション群間の平均値差</span></th>
                            <th style="width: 22%;">ロジスティック回帰（全3対比）<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">10pt上昇時のオッズ比 [95%CI]</span></th>
                            <th style="width: 14%;">統計的判定 &amp; 結論</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="background: #EEF2FF;">
                            <td>
                                <strong style="color: #3730A3; font-size: 13px;">バリューフィット度</strong><br>
                                <span style="font-size: 11px; color: #64748B;">(N=313)</span>
                            </td>
                            <td>
                                <strong>F = 13.263</strong><br>
                                <strong>p &lt; 0.0001 (***)</strong><br>
                                <span style="font-size: 10.5px; color: #4F46E5;">η² = 0.079 [中効果]</span><br>
                                <span style="font-size: 10.5px; color: #64748B;">順位相関 ρ = +0.293***</span>
                            </td>
                            <td>
                                <div style="margin-bottom: 4px;">
                                    <strong>① なし vs めっちゃ知りたい:</strong> <strong>p &lt; 0.0001 (***)</strong><br>
                                    <span style="font-size: 10.5px; color: #475569;">t = -5.308, df = 153.1 (差 +5.95pt, d = 0.826 [大])</span>
                                </div>
                                <div style="margin-bottom: 4px;">
                                    <strong>② なし vs 知りたい:</strong> <strong>p = 0.0011 (***)</strong><br>
                                    <span style="font-size: 10.5px; color: #475569;">t = -3.318, df = 216.2 (差 +3.27pt, d = 0.429 [中])</span>
                                </div>
                                <div>
                                    <strong>③ 知りたい vs めっちゃ知りたい:</strong> <strong>p = 0.0129 (*)</strong><br>
                                    <span style="font-size: 10.5px; color: #475569;">t = -2.516, df = 152.3 (差 +2.68pt, d = 0.352 [小〜中])</span>
                                </div>
                            </td>
                            <td>
                                <div style="margin-bottom: 5px;">
                                    <strong>① なし vs めっちゃ知りたい:</strong><br>
                                    <strong>OR 3.174 (約3.17倍)</strong><br>
                                    <span style="font-size: 10px; color: #4F46E5;"><strong>p &lt; 0.0001***</strong> [1.94〜5.18]</span>
                                </div>
                                <div style="margin-bottom: 5px;">
                                    <strong>② なし vs 知りたい:</strong><br>
                                    <strong>OR 1.752 (約1.75倍)</strong><br>
                                    <span style="font-size: 10px; color: #4F46E5;"><strong>p = 0.0016***</strong> [1.24〜2.48]</span>
                                </div>
                                <div>
                                    <strong>③ 知りたい vs めっちゃ知りたい:</strong><br>
                                    <strong>OR 1.616 (約1.62倍)</strong><br>
                                    <span style="font-size: 10px; color: #4F46E5;"><strong>p = 0.0176*</strong> [1.09〜2.40]</span>
                                </div>
                            </td>
                            <td>
                                <span class="pill pill-indigo">極めて有意 (***)</span><br>
                                <div style="font-size: 11px; color: #3730A3; margin-top: 4px; line-height: 1.3;">
                                    全対比・全モデルで有意。<br>企業選別の真のドライバー
                                </div>
                            </td>
                        </tr>
                        <tr style="background: #F8FAFC;">
                            <td>
                                <strong style="color: #64748B; font-size: 13px;">パーソナリティフィット度</strong><br>
                                <span style="font-size: 11px; color: #64748B;">(N=286)</span>
                            </td>
                            <td>
                                F = 0.817<br>
                                p = 0.4463<br>
                                <span style="font-size: 10.5px; color: #64748B;">η² = 0.006 [効果なし]</span><br>
                                <span style="font-size: 10.5px; color: #64748B;">順位相関 ρ = -0.018</span>
                            </td>
                            <td>
                                <div style="margin-bottom: 4px;">
                                    ① なし vs めっちゃ知りたい: p = 0.8311<br>
                                    <span style="font-size: 10.5px; color: #64748B;">t = 0.214, df = 146.0 (差 -0.28pt, d = -0.035)</span>
                                </div>
                                <div style="margin-bottom: 4px;">
                                    ② なし vs 知りたい: p = 0.3530<br>
                                    <span style="font-size: 10.5px; color: #64748B;">t = -0.931, df = 165.7 (差 +1.12pt, d = 0.130)</span>
                                </div>
                                <div>
                                    ③ 知りたい vs めっちゃ知りたい: p = 0.2369<br>
                                    <span style="font-size: 10.5px; color: #64748B;">t = 1.187, df = 159.2 (差 -1.40pt, d = -0.166)</span>
                                </div>
                            </td>
                            <td>
                                <div style="margin-bottom: 5px;">
                                    ① なし vs めっちゃ知りたい:<br>
                                    OR 0.957 (0.96倍)<br>
                                    <span style="font-size: 10px; color: #64748B;">p = 0.8318 [0.64〜1.44]</span>
                                </div>
                                <div style="margin-bottom: 5px;">
                                    ② なし vs 知りたい:<br>
                                    OR 1.164 (1.16倍)<br>
                                    <span style="font-size: 10px; color: #64748B;">p = 0.3599 [0.84〜1.61]</span>
                                </div>
                                <div>
                                    ③ 知りたい vs めっちゃ知りたい:<br>
                                    OR 0.822 (0.82倍)<br>
                                    <span style="font-size: 10px; color: #64748B;">p = 0.2573 [0.58〜1.15]</span>
                                </div>
                            </td>
                            <td>
                                <span class="pill pill-slate">有意差なし ❌</span><br>
                                <div style="font-size: 11px; color: #64748B; margin-top: 4px; line-height: 1.3;">
                                    全対比・全モデルで無関係。<br>意思決定に寄与せず
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <div style="font-size: 11.5px; padding: 10px 14px; background: #EEF2FF; border-left: 3px solid var(--primary); border-radius: 4px; color: #3730A3; margin-top: 10px; line-height: 1.6;">
                    <strong>🏢 企業行動の客観的結論:</strong><br>
                    企業はバリューが10pt上がるごとに、「なし」に対して「知りたい」を選ぶオッズが <strong>約1.75倍（p = 0.0016***）</strong>、「めっちゃ知りたい」を選ぶオッズが <strong>約3.17倍（p &lt; 0.0001***）</strong> へ急拡大し、「知りたい」から「めっちゃ知りたい」への絞り込みオッズも <strong>約1.62倍（p = 0.0176*）</strong> 有意に上昇します。一方、パーソナリティは全対比・全モデルで有意差が一切なく（p = 0.24〜0.83）、企業は100%バリューのみを基準に厳格に選別していることが完璧に証明されます。
                </div>
            </div>

            <!-- ブロック2: 🎓 学生アクション (質的) × パーソナリティ & バリュー (量的) -->
            <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px;">
                    <h3 style="font-size: 16px; font-weight: 700; color: #1E293B; margin: 0; display: flex; align-items: center; gap: 8px;">
                        <span>🎓</span> 学生アクションに対する要因分析：パーソナリティ（人柄・安心感） vs バリュー（理念・魅力）
                    </h3>
                    <span class="pill pill-amber">パーソナリティで底上げ / バリューにも自発的に有意傾向で反応</span>
                </div>

                <!-- 学生側 検定テーブル -->
                <table>
                    <thead>
                        <tr>
                            <th style="width: 14%;">評価指標（量的）</th>
                            <th style="width: 18%;">一元配置分散分析 (ANOVA)<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">群間全体の差</span></th>
                            <th style="width: 32%;">Welchのt検定（全3対比）<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">アクション群間の平均値差</span></th>
                            <th style="width: 22%;">ロジスティック回帰（全3対比）<br><span style="font-size: 10px; font-weight: normal; color: #64748B;">10pt上昇時のオッズ比 [95%CI]</span></th>
                            <th style="width: 14%;">統計的判定 &amp; 結論</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="background: #FEF3C7;">
                            <td>
                                <strong style="color: #92400E; font-size: 13px;">パーソナリティフィット度</strong><br>
                                <span style="font-size: 11px; color: #64748B;">(N=286)</span>
                            </td>
                            <td>
                                F = 1.558<br>
                                p = 0.2105<br>
                                <span style="font-size: 10.5px; color: #92400E;">η² = 0.011</span><br>
                                <span style="font-size: 10.5px; color: #B45309;">順位相関 ρ = +0.104†</span>
                            </td>
                            <td>
                                <div style="margin-bottom: 4px;">
                                    <strong>① なし vs めっちゃ知りたい:</strong> <strong style="color: #B45309;">p = 0.0890 (†)</strong><br>
                                    <span style="font-size: 10.5px; color: #475569;">t = -1.733, df = 51.7 (差 +2.70pt, d = 0.324 [中])</span>
                                </div>
                                <div style="margin-bottom: 4px;">
                                    ② なし vs 知りたい: p = 0.2793<br>
                                    <span style="font-size: 10.5px; color: #64748B;">t = -1.084, df = 248.5 (差 +1.15pt, d = 0.136)</span>
                                </div>
                                <div>
                                    ③ 知りたい vs めっちゃ知りたい: p = 0.3295<br>
                                    <span style="font-size: 10.5px; color: #64748B;">t = -0.984, df = 53.7 (差 +1.55pt, d = 0.187)</span>
                                </div>
                            </td>
                            <td>
                                <div style="margin-bottom: 5px;">
                                    <strong>① なし vs めっちゃ知りたい:</strong><br>
                                    <strong style="color: #92400E;">OR 1.498 (約1.50倍)</strong><br>
                                    <span style="font-size: 10px; color: #B45309;"><strong>p = 0.1001 (†)</strong> [0.93〜2.42]</span>
                                </div>
                                <div style="margin-bottom: 5px;">
                                    ② なし vs 知りたい:<br>
                                    OR 1.177 (約1.18倍)<br>
                                    <span style="font-size: 10px; color: #64748B;">p = 0.2802 [0.88〜1.58]</span>
                                </div>
                                <div>
                                    ③ 知りたい vs めっちゃ知りたい:<br>
                                    OR 1.263 (約1.26倍)<br>
                                    <span style="font-size: 10px; color: #64748B;">p = 0.3417 [0.78〜2.04]</span>
                                </div>
                            </td>
                            <td>
                                <span class="pill pill-amber">有意傾向 (†)</span><br>
                                <div style="font-size: 11px; color: #92400E; margin-top: 4px; line-height: 1.3;">
                                    なし vs めっちゃ知りたいで有意傾向。<br>人柄・安心感による底上げ
                                </div>
                            </td>
                        </tr>
                        <tr style="background: #ECFDF5;">
                            <td>
                                <strong style="color: #065F46; font-size: 13px;">バリューフィット度</strong><br>
                                <span style="font-size: 11px; color: #64748B;">(N=313)</span>
                            </td>
                            <td>
                                F = 1.305<br>
                                p = 0.2720<br>
                                <span style="font-size: 10.5px; color: #065F46;">η² = 0.008</span><br>
                                <span style="font-size: 10.5px; color: #047857;">順位相関 ρ = +0.095†</span>
                            </td>
                            <td>
                                <div style="margin-bottom: 4px;">
                                    ① なし vs めっちゃ知りたい: p = 0.6285<br>
                                    <span style="font-size: 10.5px; color: #64748B;">t = -0.486, df = 60.1 (差 +0.71pt, d = 0.090)</span>
                                </div>
                                <div style="margin-bottom: 4px;">
                                    <strong>② なし vs 知りたい:</strong> <strong style="color: #047857;">p = 0.1053</strong><br>
                                    <span style="font-size: 10.5px; color: #475569;">t = -1.625, df = 270.7 (差 +1.52pt, d = 0.197)</span>
                                </div>
                                <div>
                                    ③ 知りたい vs めっちゃ知りたい: p = 0.5824<br>
                                    <span style="font-size: 10.5px; color: #64748B;">t = 0.553, df = 60.8 (差 -0.81pt, d = -0.103)</span>
                                </div>
                            </td>
                            <td>
                                <div style="margin-bottom: 5px;">
                                    ① なし vs めっちゃ知りたい:<br>
                                    OR 1.124 (約1.12倍)<br>
                                    <span style="font-size: 10px; color: #64748B;">p = 0.6120 [0.71〜1.77]</span>
                                </div>
                                <div style="margin-bottom: 5px;">
                                    <strong>② なし vs 知りたい:</strong><br>
                                    <strong style="color: #065F46;">OR 1.293 (約1.29倍)</strong><br>
                                    <span style="font-size: 10px; color: #047857;"><strong>p = 0.1051</strong> [0.95〜1.76]</span>
                                </div>
                                <div>
                                    ③ 知りたい vs めっちゃ知りたい:<br>
                                    OR 0.877 (約0.88倍)<br>
                                    <span style="font-size: 10px; color: #64748B;">p = 0.5638 [0.56〜1.37]</span>
                                </div>
                            </td>
                            <td>
                                <span class="pill pill-green">ポジティブ希望喚起</span><br>
                                <div style="font-size: 11px; color: #065F46; margin-top: 4px; line-height: 1.3;">
                                    なし vs 知りたいでオッズ約1.3倍。<br>魅力伝達で希望率向上
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <div style="font-size: 11.5px; padding: 10px 14px; background: #FEF3C7; border-left: 3px solid var(--warning); border-radius: 4px; color: #92400E; margin-top: 10px; line-height: 1.6;">
                    <strong>🎓 学生行動の客観的結論:</strong><br>
                    学生はブース担当者のパーソナリティ親和性が高いほど、「なし」に対して「めっちゃ知りたい」を選択するオッズが <strong>約1.50倍（p = 0.1001†）</strong> へ有意傾向で底上げされます。一方、バリューについても「なし」に対して「知りたい」を選択するオッズが <strong>約1.29倍（p = 0.1051）</strong> に向上しており、学生は担当者の人柄による安心感を得ながら、企業の理念・魅力に対してもポジティブに反応しています。
                </div>
            </div>

            <!-- セクション総括インサイト -->
            <div class="insight-box" style="margin-top: 20px;">
                <strong>💡 量的×質的要因分析の総括インサイト（評価軸のすれ違いの真相）:</strong><br>
                <ul>
                    <li style="margin-bottom: 4px;"><strong>企業側の行動原理:</strong> 企業はパーソナリティ（人柄）に一切左右されず（ANOVA p = 0.4463、Welch全3対比・ロジスティック回帰全3対比ともに有意差なし）、自社の求める能力・価値観（バリュー）の高さを極めて厳格に見極めて「めっちゃ知りたい」枠（10枠限定）を配分しています（ANOVA p &lt; 0.0001***、Welch全3対比で有意、オッズ比最大3.17倍***）。</li>
                    <li><strong>学生側の行動原理:</strong> 学生は担当者のパーソナリティ親和性によって面談の安心感・共感が高まりポジティブ希望率が底上げされる（なし vs めっちゃ知りたい Welch p = 0.0890†, オッズ1.50倍）と同時に、理念や強みが明確に伝わる「高バリュー企業」に対しても自発的に「知りたい」希望オッズを1.29倍に高めてアクションを起こしています。</li>
                </ul>
            </div>
        </div>

        <!-- Section 3: Match Determinants & Logistic Regression -->
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">【課題3】マッチング成立の真のドライバー（多変量ロジスティック回帰）</div>
                <span class="pill pill-green">交絡因子統制: 有料企業バイアスを排除</span>
            </div>
            <div class="grid-2">
                <div>
                    <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">マッチ済み vs 未マッチのスコア比較</h3>
                    <div class="chart-box">
                        <canvas id="matchChart"></canvas>
                    </div>
                </div>
                <div>
                    <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">マッチング成立の要因分析（実データと回帰分析の統合）</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>要因（ドライバー）</th>
                                <th>成立群</th>
                                <th>未成立群</th>
                                <th>スコア差</th>
                                <th>10pt上昇時の効果<br><span style="font-size: 11px; font-weight: normal; color: #6B7280;">(回帰オッズ比より)</span></th>
                                <th>判定</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="background: #EEF2FF;">
                                <td><strong>バリューフィット</strong></td>
                                <td><strong>62.81</strong></td>
                                <td>59.25</td>
                                <td><strong style="color: var(--primary); font-size: 14px;">+3.56 pt</strong></td>
                                <td><strong>約1.74倍 (+74%)</strong><br><span style="font-size: 11px; color: #64748B;">(1ptあたり +5.7%)</span></td>
                                <td><span class="pill pill-indigo">極めて有意 (***)</span></td>
                            </tr>
                            <tr>
                                <td><strong>パーソナリティ</strong></td>
                                <td><strong>80.08</strong></td>
                                <td>78.00</td>
                                <td><strong style="color: #059669; font-size: 14px;">+2.08 pt</strong></td>
                                <td><strong>約1.34倍 (+34%)</strong><br><span style="font-size: 11px; color: #64748B;">(1ptあたり +3.0%)</span></td>
                                <td><span class="pill pill-amber">有意傾向 (†)</span></td>
                            </tr>
                            <tr>
                                <td><strong>出展区分（有料企業）</strong></td>
                                <td>45.9%</td>
                                <td>37.7%</td>
                                <td>+8.2 pt</td>
                                <td><strong>ほぼ影響なし (約1.03倍)</strong><br><span style="font-size: 11px; color: #64748B;">(高バリュー配席を除くと差ゼロ)</span></td>
                                <td><span class="pill pill-slate">有意差なし ❌</span></td>
                            </tr>
                        </tbody>
                    </table>

                    <!-- 直感的ビジネスインパクト・算出根拠の要約 -->
                    <div style="margin-top: 12px; padding: 12px 14px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 12.5px; color: #334155; line-height: 1.6;">
                        <div style="font-weight: 700; margin-bottom: 4px; color: #1E293B;">💡 「1.74倍」の算出根拠とインサイト（要約）:</div>
                        <div>・<strong>なぜ「1.74倍」なのか？</strong>: 多変量ロジスティック回帰により、バリューが1pt上がるとマッチ成立オッズが <strong>+5.7%（オッズ比 1.057）</strong> 高まることが判明しています。したがって、スコアが10pt上がると 1.057 の10乗となり、成立確率は <strong style="color: var(--primary);">約1.74倍（+74%）</strong> に跳ね上がります。</div>
                        <div>・<strong>有料企業の見かけの差（+8.2pt）の真相</strong>: 有料企業のマッチ率が高いのは「お金を払ったから」ではなく、<strong>「事前に高バリュー層を優先配席した成果」</strong>であり、配席の効果を統制すると出展区分自体の影響はゼロ（オッズ比1.026, p=0.92）になります。</div>
                    </div>

                    <!-- タップ開閉アコーディオン（詳細な統計的説明） -->
                    <details class="stats-accordion">
                        <summary class="stats-summary">
                            <span>📊 統計的説明・多変量ロジスティック回帰の詳細（オッズ比 / 95%信頼区間 / 交絡因子統制）</span>
                            <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                        </summary>
                        <div class="stats-content">
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B;">
                                📈 多変量ロジスティック回帰モデル結果 (N=286)
                            </div>
                            <table style="margin-bottom: 12px; font-size: 12px;">
                                <thead>
                                    <tr>
                                        <th>説明変数</th>
                                        <th>偏回帰係数(β)</th>
                                        <th>オッズ比 (OR)</th>
                                        <th>95% 信頼区間</th>
                                        <th>p値</th>
                                        <th>判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #EEF2FF;">
                                        <td><strong>バリューフィット</strong></td>
                                        <td>+0.0558</td>
                                        <td><strong>1.057</strong></td>
                                        <td>[1.023, 1.093]</td>
                                        <td><strong>0.0010</strong></td>
                                        <td><span class="pill pill-indigo">極めて有意 (***)</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>パーソナリティ</strong></td>
                                        <td>+0.0294</td>
                                        <td><strong>1.030</strong></td>
                                        <td>[1.000, 1.061]</td>
                                        <td>0.0518</td>
                                        <td><span class="pill pill-amber">有意傾向 (†)</span></td>
                                    </tr>
                                    <tr>
                                        <td>有料企業フラグ</td>
                                        <td>+0.0256</td>
                                        <td>1.026</td>
                                        <td>[0.627, 1.679]</td>
                                        <td>0.9188</td>
                                        <td>有意差なし ❌</td>
                                    </tr>
                                </tbody>
                            </table>

                            <div style="margin-bottom: 12px; padding: 10px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 12px;">
                                <div style="font-weight: 700; margin-bottom: 4px; color: #334155;">🔬 2群比較検定（Welch t検定 &amp; 効果量）:</div>
                                <div>・<strong>バリューフィット</strong>: Welch t = 4.096, <strong>p &lt; 0.0001 (*** 極めて有意)</strong>, 効果量 Cohen's d = 0.467 (中程度の効果)</div>
                                <div>・<strong>パーソナリティ</strong>: Welch t = 2.087, <strong>p = 0.0369 (* 5%水準有意)</strong>, 効果量 Cohen's d = 0.249 (小〜中程度の効果)</div>
                            </div>

                            <div style="padding: 10px 12px; background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 6px; font-size: 12px; color: #065F46; line-height: 1.6;">
                                <strong>🎯 有料企業バイアスの統計的解明（交絡因子の統制）:</strong><br>
                                「有料企業の方がマッチ率が高い（45.9% vs 37.7%）」という見かけの差は、多変量ロジスティック回帰で有料企業フラグを統制するとオッズ比 1.026 (p=0.9188) となり完全に消失します。<br>
                                つまり「有料出展だからマッチした（疑似相関）」のではなく、<strong>「事前にマッチ度の高い学生を優先配席していたからマッチした（因果関係）」</strong>という事前のマッチング設計が科学的に大成功していたことを証明しています。
                            </div>
                        </div>
                    </details>
                </div>
            </div>
        </div>

        <!-- Section 4: 3x3 Matrix Heatmap -->
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">【実践編】バリュー × パーソナリティ 3×3 マッチング成立率マトリクス</div>
                <span class="pill pill-amber">次回ブース割り当てへの提言</span>
            </div>
            <p style="font-size: 14px; color: #4B5563; margin-bottom: 16px;">
                全286接触をバリューとパーソナリティの3分位水準でクロス集計。各セル内の上段は「マッチ成立率（件数）」、下段は「企業のめっちゃ知りたい率 / 学生知りたい率」です。
            </p>
            
            <table class="matrix-table">
                <thead>
                    <tr>
                        <th style="width: 25%; background: var(--gray-100);">パーソナリティ＼バリュー</th>
                        <th style="width: 25%; background: #FEE2E2;">バリュー低 (&lt;58.0)</th>
                        <th style="width: 25%; background: #FEF3C7;">バリュー中 (58.0〜63.9)</th>
                        <th style="width: 25%; background: #D1FAE5;">バリュー高 (&ge;64.0)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <th style="background: #D1FAE5;">パーソナリティ高 (&ge;82.0)</th>
                        <td class="matrix-cell heat-mid">
                            <div class="cell-rate">37.8%</div>
                            <div class="cell-sub">14/37件 (企業めっちゃ知りたい:10.8% / 学生知りたい:48.6%)</div>
                        </td>
                        <td class="matrix-cell heat-mid">
                            <div class="cell-rate">38.5%</div>
                            <div class="cell-sub">10/26件 (企業めっちゃ知りたい:15.4% / 学生知りたい:46.2%)</div>
                        </td>
                        <td class="matrix-cell heat-high">
                            <div class="cell-rate">👑 61.2%</div>
                            <div class="cell-sub">30/49件 (企業めっちゃ知りたい:26.5% / 学生知りたい:67.3%)</div>
                        </td>
                    </tr>
                    <tr>
                        <th style="background: #FEF3C7;">パーソナリティ中 (76.0〜81.9)</th>
                        <td class="matrix-cell heat-low">
                            <div class="cell-rate">30.0%</div>
                            <div class="cell-sub">6/20件 (企業めっちゃ知りたい:20.0% / 学生知りたい:50.0%)</div>
                        </td>
                        <td class="matrix-cell heat-mid-high">
                            <div class="cell-rate">42.3%</div>
                            <div class="cell-sub">11/26件 (企業めっちゃ知りたい:26.9% / 学生知りたい:57.7%)</div>
                        </td>
                        <td class="matrix-cell heat-high">
                            <div class="cell-rate">58.3%</div>
                            <div class="cell-sub">14/24件 (企業めっちゃ知りたい:41.7% / 学生知りたい:66.7%)</div>
                        </td>
                    </tr>
                    <tr>
                        <th style="background: #FEE2E2;">パーソナリティ低 (&lt;76.0)</th>
                        <td class="matrix-cell heat-low" style="background: #FCA5A5; color: #7F1D1D;">
                            <div class="cell-rate">18.9%</div>
                            <div class="cell-sub">7/37件 (企業めっちゃ知りたい:16.2% / 学生知りたい:43.2%)</div>
                        </td>
                        <td class="matrix-cell heat-low">
                            <div class="cell-rate">30.0%</div>
                            <div class="cell-sub">9/30件 (企業めっちゃ知りたい:20.0% / 学生知りたい:36.7%)</div>
                        </td>
                        <td class="matrix-cell heat-high">
                            <div class="cell-rate">54.1%</div>
                            <div class="cell-sub">20/37件 (企業めっちゃ知りたい:45.9% / 学生知りたい:59.5%)</div>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="insight-box" style="margin-top: 20px;">
                <strong>🚀 次回ミッションラリーの配席最適化ルール:</strong><br>
                1. <strong>バリュー高（&ge;64.0）を最優先で配席</strong>：パーソナリティに関わらずマッチ率は 54%〜61% に達するため、アルゴリズムの第1キーを「バリュー最大化」にする。<br>
                2. <strong>「両方低」の配席を完全ブロック</strong>：マッチ率わずか 18.9% であり、双方にとって満足度が極めて低いため配席除外ルールを設ける。<br>
                3. <strong>パーソナリティは「引き上げバッファ」</strong>：バリューが中水準の学生にパーソナリティ高の企業をぶつけることで、マッチ率を 30% から 42.3% へ底上げ可能。
            </div>

            <!-- タップ開閉アコーディオン（3×3マトリクスの統計的検定結果） -->
            <details class="stats-accordion" style="margin-top: 16px;">
                <summary class="stats-summary">
                    <span>📊 3×3マトリクスの統計的検定結果（カイ二乗検定 / 自由度 / 有意確率 p値）</span>
                    <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                </summary>
                <div class="stats-content">
                    <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B;">
                        📈 マトリクス全体および各要因別の統計的独立性検定 (N=286)
                    </div>
                    <table style="margin-bottom: 12px; font-size: 12px;">
                        <thead>
                            <tr>
                                <th>検証スコープ</th>
                                <th>検定手法</th>
                                <th>検定統計量</th>
                                <th>自由度 (df)</th>
                                <th>有意確率 (p値)</th>
                                <th>判定</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="background: #EEF2FF;">
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
                                <td><strong>p &lt; 0.0001 (0.000056)</strong></td>
                                <td><span class="pill pill-indigo">極めて有意 (***)</span></td>
                            </tr>
                            <tr>
                                <td><strong>縦軸：パーソナリティ水準別 (低・中・高)</strong></td>
                                <td>カイ二乗検定 (3×2 分割表)</td>
                                <td>χ² = 4.2343</td>
                                <td>df = 2</td>
                                <td>p = 0.1204</td>
                                <td><span class="pill pill-slate">有意差なし ❌</span></td>
                            </tr>
                            <tr style="background: #FEF3C7;">
                                <td><strong>最高セル vs 最低セル の直接比較</strong><br><span style="font-size: 11px; color: #64748B;">(高×高: 61.2% vs 低×低: 18.9%)</span></td>
                                <td>カイ二乗検定 (2×2, イェーツ補正)</td>
                                <td>χ² = 13.7145<br><span style="font-size: 11px; color: #64748B;">(オッズ比 6.77倍)</span></td>
                                <td>df = 1</td>
                                <td><strong>p = 0.0002</strong><br><span style="font-size: 11px; color: #64748B;">(無補正 p = 0.000087)</span></td>
                                <td><span class="pill pill-amber">極めて有意 (***)</span></td>
                            </tr>
                        </tbody>
                    </table>

                    <div style="margin-bottom: 12px; padding: 10px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 12px;">
                        <div style="font-weight: 700; margin-bottom: 4px; color: #334155;">🔬 統計的考察とトレンド検証（Mantel-Haenszel 線形トレンド検定）:</div>
                        <div>・<strong>マトリクス全体の有意性 (p = 0.0026)</strong>: セルごとの成立率（18.9%〜61.2%）の差は偶然ではなく、バリューとパーソナリティの配置によって有意にマッチ率が変動することが実証されました。</div>
                        <div>・<strong>バリューの決定性 (p &lt; 0.0001)</strong>: バリューが低(28.7%) ➔ 中(36.6%) ➔ 高(58.2%) と上昇するにつれて成立率が劇的に跳ね上がる強力な主効果が確認されました (トレンド検定 M² = 18.37, p = 0.000018)。</div>
                        <div>・<strong>パーソナリティの底上げ効果 (トレンド p = 0.0444)</strong>: パーソナリティ単独の3区分比較では p=0.1204 ですが、低(34.6%) ➔ 中(44.3%) ➔ 高(48.2%) への線形上昇トレンドを検定すると <strong>p = 0.0444 と5%水準で有意</strong> となり、段階的な底上げ効果（バッファ機能）が裏付けられます。</div>
                    </div>

                    <div style="padding: 10px 12px; background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 6px; font-size: 12px; color: #065F46; line-height: 1.6;">
                        <strong>🎯 配席アルゴリズムへの統計的正当性:</strong><br>
                        「最高セル（バリュー高×パーソナリティ高: 61.2%）」と「最低セル（バリュー低×パーソナリティ低: 18.9%）」の成立オッズ比は <strong>6.77倍（p &lt; 0.0001）</strong> に達します。<br>
                        したがって、「バリュー高を最優先で配席する」「両方低の組み合わせをブロックする」という運用ルールは、統計的に極めて強固な根拠に基づいています。
                    </div>
                </div>
            </details>
        </div>
    </div>

    <!-- ========================================== -->
    <!-- TAB 2: 有料 vs 無料 比較 -->
    <!-- ========================================== -->
    <div id="tab-paid-free" class="tab-pane">
        <!-- Top KPI Cards: 基本統計量（有料 vs 無料） -->
        <div class="grid-4">
            <div class="kpi-card">
                <div class="kpi-title">有料企業 バリュー配席</div>
                <div class="kpi-value" style="color: var(--primary);">61.78</div>
                <div class="kpi-sub">中央値: <strong>61.94</strong> / N=122 (マッチ率 44.3%)<br>標準偏差: <strong>±6.38</strong> (範囲 46.88〜76.62)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">無料企業 バリュー配席</div>
                <div class="kpi-value" style="color: #06B6D4;">60.02</div>
                <div class="kpi-sub">中央値: <strong>60.42</strong> / N=191 (マッチ率 38.7%)<br>標準偏差: <strong>±8.53</strong> (範囲 40.68〜78.43)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">有料企業 パーソナリティ</div>
                <div class="kpi-value" style="color: #F59E0B;">80.38</div>
                <div class="kpi-sub">中央値: <strong>81.81</strong> / N=122<br>標準偏差: <strong>±7.76</strong> (範囲 59.91〜94.01)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">無料企業 パーソナリティ</div>
                <div class="kpi-value" style="color: #64748B;">77.76</div>
                <div class="kpi-sub">中央値: <strong>76.99</strong> / N=164有効<br>標準偏差: <strong>±8.68</strong> (範囲 53.64〜98.14)</div>
            </div>
        </div>

        <div class="section-card">
            <div class="section-header">
                <div>
                    <div class="section-title">⚖️ 【層別比較】有料出展企業（4社・122件） vs 無料出展企業（8社・191件）</div>
                    <p style="font-size: 13px; color: #6B7280; margin-top: 4px;">配席前提の違い（有料：高バリュー優先配席 / 無料：高低混合配席）による企業・学生の行動変化と統計検証</p>
                </div>
                <span class="pill pill-green">自然実験の完全立証</span>
            </div>
            
            <div class="grid-2">
                <!-- 左カラム：企業アクション別 -->
                <div>
                    <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">🏢 企業アクション別：バリューとパーソナリティの推移（有料 vs 無料）</h3>
                    <div class="chart-box">
                        <canvas id="paidFreeCompChart"></canvas>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th rowspan="2" style="vertical-align: middle;">企業アクション</th>
                                <th colspan="3" style="text-align: center; background: #EEF2FF; color: #3730A3; border-bottom: 1px solid #C7D2FE;">有料企業 (N=122)</th>
                                <th colspan="3" style="text-align: center; background: #F0FDFA; color: #0F766E; border-bottom: 1px solid #99F6E4;">無料企業 (N=191)</th>
                            </tr>
                            <tr>
                                <th style="background: #EEF2FF; font-size: 11px;">件数</th>
                                <th style="background: #EEF2FF; font-size: 11px;">バリュー</th>
                                <th style="background: #EEF2FF; font-size: 11px;">人柄(P)</th>
                                <th style="background: #F0FDFA; font-size: 11px;">件数</th>
                                <th style="background: #F0FDFA; font-size: 11px;">バリュー</th>
                                <th style="background: #F0FDFA; font-size: 11px;">人柄(P)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>なし</td>
                                <td>32件</td>
                                <td>60.09</td>
                                <td>80.48</td>
                                <td>65件</td>
                                <td>56.73</td>
                                <td>76.93</td>
                            </tr>
                            <tr>
                                <td>知りたい</td>
                                <td>61件</td>
                                <td>62.01</td>
                                <td>80.44</td>
                                <td>84件</td>
                                <td>60.46</td>
                                <td>78.80</td>
                            </tr>
                            <tr class="highlight-row">
                                <td><strong>めっちゃ知りたい</strong></td>
                                <td>29件</td>
                                <td><strong>63.13</strong></td>
                                <td>80.15</td>
                                <td>42件</td>
                                <td><strong style="color: var(--primary);">64.24</strong></td>
                                <td>76.73</td>
                            </tr>
                        </tbody>
                    </table>

                    <!-- 統計的仮説検定アコーディオン（企業側） -->
                    <details class="stats-accordion">
                        <summary class="stats-summary">
                            <span>📊 統計的仮説検定の詳細（ANOVA / Welch t検定）</span>
                            <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                        </summary>
                        <div class="stats-content">
                            <!-- ① バリューフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ① バリューフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="margin-bottom: 14px; font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>出展区分</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">有料企業<br><span style="font-size: 10px; color: #64748B;">(N=122)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 1.840</td>
                                        <td>(2, 119)</td>
                                        <td>p = 0.1610</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.030)</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = -1.728</td>
                                        <td>55.5</td>
                                        <td>p = 0.0896</td>
                                        <td><span class="pill pill-amber">有意傾向 (†) [差 +3.04pt, d=0.446]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -1.433</td>
                                        <td>58.9</td>
                                        <td>p = 0.1572</td>
                                        <td>有意差なし [差 +1.92pt, d=0.321]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = -0.722</td>
                                        <td>45.3</td>
                                        <td>p = 0.4738</td>
                                        <td>有意差なし [差 +1.12pt, d=0.177]</td>
                                    </tr>
                                    <tr>
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">無料企業<br><span style="font-size: 10px; color: #64748B;">(N=191)</span></td>
                                        <td><strong>一元配置分散分析 (ANOVA)</strong></td>
                                        <td>F = 11.162</td>
                                        <td>(2, 188)</td>
                                        <td><strong>p &lt; 0.0001</strong></td>
                                        <td><span class="pill pill-indigo">極めて有意 (***) [η²=0.106]</span></td>
                                    </tr>
                                    <tr>
                                        <td><strong>Welch t検定 (なし vs めっちゃ知りたい)</strong></td>
                                        <td>t = -5.278</td>
                                        <td>92.3</td>
                                        <td><strong>p &lt; 0.0001</strong></td>
                                        <td><span class="pill pill-indigo">極めて有意 (***) [差 +7.51pt, d=1.028]</span></td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -2.752</td>
                                        <td>146.2</td>
                                        <td><strong>p = 0.0067</strong></td>
                                        <td><span class="pill pill-green">有意 (**) [差 +3.73pt, d=0.444]</span></td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = -2.592</td>
                                        <td>102.8</td>
                                        <td><strong>p = 0.0109</strong></td>
                                        <td><span class="pill pill-green">有意 (*) [差 +3.78pt, d=0.450]</span></td>
                                    </tr>
                                </tbody>
                            </table>

                            <!-- ② パーソナリティフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ② パーソナリティフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>出展区分</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">有料企業<br><span style="font-size: 10px; color: #64748B;">(N=122)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 0.017</td>
                                        <td>(2, 119)</td>
                                        <td>p = 0.9715</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.000)</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = 0.168</td>
                                        <td>58.0</td>
                                        <td>p = 0.8673</td>
                                        <td>有意差なし [差 -0.33pt, d=0.043]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = 0.025</td>
                                        <td>59.1</td>
                                        <td>p = 0.8638</td>
                                        <td>有意差なし [差 -0.05pt, d=0.006]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = 0.176</td>
                                        <td>63.9</td>
                                        <td>p = 0.8608</td>
                                        <td>有意差なし [差 -0.28pt, d=0.038]</td>
                                    </tr>
                                    <tr>
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">無料企業<br><span style="font-size: 10px; color: #64748B;">(N=164)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 1.060</td>
                                        <td>(2, 161)</td>
                                        <td>p = 0.3498</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.013)</span></td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = 0.117</td>
                                        <td>84.2</td>
                                        <td>p = 0.9073</td>
                                        <td>有意差なし [差 -0.20pt, d=0.025]</td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -1.182</td>
                                        <td>106.0</td>
                                        <td>p = 0.2400</td>
                                        <td>有意差なし [差 +1.87pt, d=0.211]</td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = 1.262</td>
                                        <td>96.2</td>
                                        <td>p = 0.2098</td>
                                        <td>有意差なし [差 -2.07pt, d=0.231]</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </details>
                </div>

                <!-- 右カラム：学生アクション別 -->
                <div>
                    <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">🎓 学生アクション別：バリューとパーソナリティの推移（有料 vs 無料）</h3>
                    <div class="chart-box">
                        <canvas id="paidFreeStudChart"></canvas>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th rowspan="2" style="vertical-align: middle;">学生アクション</th>
                                <th colspan="3" style="text-align: center; background: #FFFBEB; color: #B45309; border-bottom: 1px solid #FDE68A;">有料企業宛 (N=122)</th>
                                <th colspan="3" style="text-align: center; background: #F8FAFC; color: #475569; border-bottom: 1px solid #E2E8F0;">無料企業宛 (N=191)</th>
                            </tr>
                            <tr>
                                <th style="background: #FFFBEB; font-size: 11px;">件数</th>
                                <th style="background: #FFFBEB; font-size: 11px;">バリュー</th>
                                <th style="background: #FFFBEB; font-size: 11px;">人柄(P)</th>
                                <th style="background: #F8FAFC; font-size: 11px;">件数</th>
                                <th style="background: #F8FAFC; font-size: 11px;">バリュー</th>
                                <th style="background: #F8FAFC; font-size: 11px;">人柄(P)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>なし</td>
                                <td>56件</td>
                                <td>60.28</td>
                                <td>78.82</td>
                                <td>83件</td>
                                <td>59.75</td>
                                <td>77.55</td>
                            </tr>
                            <tr>
                                <td>知りたい</td>
                                <td>50件</td>
                                <td>63.37</td>
                                <td>81.47</td>
                                <td>84件</td>
                                <td>60.36</td>
                                <td>77.63</td>
                            </tr>
                            <tr class="highlight-row">
                                <td><strong>めっちゃ知りたい</strong></td>
                                <td>16件</td>
                                <td>62.02</td>
                                <td><strong style="color: #D97706;">82.44</strong></td>
                                <td>24件</td>
                                <td>59.77</td>
                                <td>79.22</td>
                            </tr>
                        </tbody>
                    </table>

                    <!-- 統計的仮説検定アコーディオン（学生側） -->
                    <details class="stats-accordion">
                        <summary class="stats-summary">
                            <span>📊 統計的仮説検定の詳細（ANOVA / Welch t検定）</span>
                            <span style="font-size: 11px; color: #64748B; font-weight: normal;">タップで展開 ▼</span>
                        </summary>
                        <div class="stats-content">
                            <!-- ① バリューフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ① バリューフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="margin-bottom: 14px; font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>出展区分</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">有料企業宛<br><span style="font-size: 10px; color: #64748B;">(N=122)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 3.249</td>
                                        <td>(2, 119)</td>
                                        <td><strong>p = 0.0412</strong></td>
                                        <td><span class="pill pill-green">有意 (*) [η²=0.052]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = -1.087</td>
                                        <td>30.8</td>
                                        <td>p = 0.2856</td>
                                        <td>有意差なし [差 +1.74pt, d=0.267]</td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -2.514</td>
                                        <td>103.9</td>
                                        <td><strong>p = 0.0135</strong></td>
                                        <td><span class="pill pill-green">有意 (*) [差 +3.09pt, d=0.485]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = 0.867</td>
                                        <td>27.8</td>
                                        <td>p = 0.3934</td>
                                        <td>有意差なし [差 -1.35pt, d=0.236]</td>
                                    </tr>
                                    <tr>
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">無料企業宛<br><span style="font-size: 10px; color: #64748B;">(N=191)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 0.118</td>
                                        <td>(2, 188)</td>
                                        <td>p = 0.8842</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.001)</span></td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = -0.011</td>
                                        <td>33.3</td>
                                        <td>p = 0.6685</td>
                                        <td>有意差なし [差 +0.02pt, d=0.003]</td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -0.471</td>
                                        <td>165.0</td>
                                        <td>p = 0.6383</td>
                                        <td>有意差なし [差 +0.61pt, d=0.073]</td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = 0.267</td>
                                        <td>33.5</td>
                                        <td>p = 0.7908</td>
                                        <td>有意差なし [差 -0.59pt, d=0.067]</td>
                                    </tr>
                                </tbody>
                            </table>

                            <!-- ② パーソナリティフィットの仮説検定 -->
                            <div style="margin-bottom: 8px; font-weight: 700; color: #1E293B; font-size: 12.5px;">
                                ② パーソナリティフィットの統計的仮説検定（ANOVA &amp; Welch t検定）
                            </div>
                            <table style="font-size: 11.5px;">
                                <thead>
                                    <tr>
                                        <th>出展区分</th>
                                        <th>検定手法・対比</th>
                                        <th>統計量</th>
                                        <th>自由度 (df)</th>
                                        <th>有意確率 (p値)</th>
                                        <th>統計的判定</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background: #F8FAFC;">
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">有料企業宛<br><span style="font-size: 10px; color: #64748B;">(N=122)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 2.231</td>
                                        <td>(2, 119)</td>
                                        <td>p = 0.1097</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.036)</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td><strong>Welch t検定 (なし vs めっちゃ知りたい)</strong></td>
                                        <td>t = -1.656</td>
                                        <td>25.1</td>
                                        <td><strong>p = 0.0416</strong></td>
                                        <td><span class="pill pill-green">有意 (*) [差 +3.62pt, d=0.459]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -1.779</td>
                                        <td>103.8</td>
                                        <td>p = 0.0782</td>
                                        <td><span class="pill pill-amber">有意傾向 (†) [差 +2.65pt, d=0.345]</span></td>
                                    </tr>
                                    <tr style="background: #F8FAFC;">
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = -0.444</td>
                                        <td>24.7</td>
                                        <td>p = 0.6608</td>
                                        <td>有意差なし [差 +0.97pt, d=0.130]</td>
                                    </tr>
                                    <tr>
                                        <td rowspan="4" style="vertical-align: middle; font-weight: 700;">無料企業宛<br><span style="font-size: 10px; color: #64748B;">(N=164)</span></td>
                                        <td>一元配置分散分析 (ANOVA)</td>
                                        <td>F = 0.270</td>
                                        <td>(2, 161)</td>
                                        <td>p = 0.7666</td>
                                        <td><span class="pill pill-slate">有意差なし (η²=0.003)</span></td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (なし vs めっちゃ知りたい)</td>
                                        <td>t = -0.763</td>
                                        <td>25.2</td>
                                        <td>p = 0.4525</td>
                                        <td>有意差なし [差 +1.67pt, d=0.193]</td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (なし vs 知りたい)</td>
                                        <td>t = -0.056</td>
                                        <td>143.7</td>
                                        <td>p = 0.9307</td>
                                        <td>有意差なし [差 +0.08pt, d=0.009]</td>
                                    </tr>
                                    <tr>
                                        <td>Welch t検定 (知りたい vs めっちゃ知りたい)</td>
                                        <td>t = -0.719</td>
                                        <td>26.1</td>
                                        <td>p = 0.4787</td>
                                        <td>有意差なし [差 +1.59pt, d=0.184]</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </details>
                </div>
            </div>

            <div class="insight-box" style="margin-top: 20px;">
                <strong>💡 なぜ無料企業でバリュー選別の差が劇的（p &lt; 0.0001）なのか？:</strong><br>
                有料企業は「高バリュー優先配席」により最初から質の高い母集団が担保されていたため選別差が小さく見え、無料企業は「高低混合配席」という自然実験状態だったからこそ、企業側の優れたバリュー選別眼（低バリュー56点台を見送り、高バリュー64点超を一本釣り）が鮮明に浮かび上がりました。
            </div>
        </div>
    </div>

    <!-- ========================================== -->
    <!-- TAB 3: 全12社 個別カルテ（標準化3本柱分析） -->
    <!-- ========================================== -->
    <div id="tab-companies" class="tab-pane">
{company_detail_section_html}
    </div>

</div>

<script>
    // Tab switching function
    function switchTab(tabId) {{
        // Hide all panes
        document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
        // Deactivate all buttons
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        
        // Activate selected pane and button
        document.getElementById(tabId).classList.add('active');
        event.currentTarget.classList.add('active');

        if (tabId === 'tab-companies') {{
            initCompanyDetailCharts();
        }}

        // Trigger chart resize if needed
        window.dispatchEvent(new Event('resize'));
    }}

    // TAB 1: 企業チャート
    new Chart(document.getElementById('companyChart'), {{
        type: 'bar',
        data: {{
            labels: ['なし (97件)', '知りたい (145件)', 'めっちゃ知りたい (71件)'],
            datasets: [
                {{
                    label: 'バリューフィット平均',
                    data: [57.84, 61.11, 63.79],
                    backgroundColor: '#4F46E5',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティ平均',
                    data: [78.41, 79.53, 78.13],
                    backgroundColor: '#9CA3AF',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                y: {{ min: 50, max: 85 }}
            }}
        }}
    }});

    // TAB 1: 学生チャート
    new Chart(document.getElementById('studentChart'), {{
        type: 'bar',
        data: {{
            labels: ['なし (139件)', '知りたい (134件)', 'めっちゃ知りたい (40件)'],
            datasets: [
                {{
                    label: 'バリューフィット平均',
                    data: [59.96, 61.48, 60.67],
                    backgroundColor: '#9CA3AF',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティ平均',
                    data: [78.08, 79.23, 80.78],
                    backgroundColor: '#F59E0B',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                y: {{ min: 50, max: 85 }}
            }}
        }}
    }});

    // TAB 1: マッチチャート
    new Chart(document.getElementById('matchChart'), {{
        type: 'bar',
        data: {{
            labels: ['未マッチ (185件)', 'マッチ済み (128件)'],
            datasets: [
                {{
                    label: 'バリューフィット',
                    data: [59.25, 62.81],
                    backgroundColor: '#6366F1',
                    borderRadius: 6
                }},
                {{
                    label: 'パーソナリティフィット',
                    data: [78.00, 80.08],
                    backgroundColor: '#10B981',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                y: {{ min: 50, max: 85 }}
            }}
        }}
    }});

    // TAB 2: 有料 vs 無料 企業アクション別バリュー
    new Chart(document.getElementById('paidFreeCompChart'), {{
        type: 'bar',
        data: {{
            labels: ['なし', '知りたい', 'めっちゃ知りたい'],
            datasets: [
                {{
                    label: '有料企業 (N=122)',
                    data: [60.09, 62.01, 63.13],
                    backgroundColor: '#4F46E5',
                    borderRadius: 6
                }},
                {{
                    label: '無料企業 (N=191)',
                    data: [56.73, 60.46, 64.24],
                    backgroundColor: '#06B6D4',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                y: {{ min: 50, max: 70 }}
            }}
        }}
    }});

    // TAB 2: 有料 vs 無料 学生アクション別パーソナリティ
    new Chart(document.getElementById('paidFreeStudChart'), {{
        type: 'bar',
        data: {{
            labels: ['なし', '知りたい', 'めっちゃ知りたい'],
            datasets: [
                {{
                    label: '有料企業ブース (N=122)',
                    data: [78.82, 81.47, 82.44],
                    backgroundColor: '#F59E0B',
                    borderRadius: 6
                }},
                {{
                    label: '無料企業ブース (N=164)',
                    data: [77.55, 77.63, 79.22],
                    backgroundColor: '#9CA3AF',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                y: {{ min: 70, max: 86 }}
            }}
        }}
    }});

{company_detail_js}
</script>

</body>
</html>"""

with open('asobiba_fes_fit_analysis_report.html', 'w', encoding='utf-8') as f:
    f.write(tab_dashboard_html)

# ============================================================
# 2. company_fit_report.html (独立専用ページ)
# ============================================================
company_page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASOBIBA FES 2026: 企業別・有料無料別マッチング詳細分析レポート</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #4F46E5;
            --primary-light: #EEF2FF;
            --success: #10B981;
            --success-light: #ECFDF5;
            --warning: #F59E0B;
            --danger: #EF4444;
            --gray-50: #F9FAFB;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-700: #374151;
            --gray-800: #1F2937;
            --gray-900: #111827;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--gray-50);
            color: var(--gray-800);
            line-height: 1.6;
            padding: 24px;
        }}
        .container {{
            max-width: 1240px;
            margin: 0 auto;
        }}
        header {{
            background: linear-gradient(135deg, #0EA5E9 0%, #3B82F6 100%);
            color: white;
            padding: 32px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(14, 165, 233, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
        }}
        header h1 {{
            font-size: 26px;
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }}
        header p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .badge-bar {{
            display: flex;
            gap: 10px;
            margin-top: 16px;
            flex-wrap: wrap;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(4px);
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .btn-header {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 18px;
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 8px;
            color: white;
            text-decoration: none;
            font-size: 13px;
            font-weight: 700;
            transition: all 0.2s;
        }}
        .btn-header:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }}
        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: white;
            padding: 20px 24px;
            border-radius: 12px;
            border: 1px solid var(--gray-200);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .kpi-title {{
            font-size: 13px;
            font-weight: 600;
            color: var(--gray-700);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 28px;
            font-weight: 800;
            color: var(--gray-900);
        }}
        .kpi-sub {{
            font-size: 12px;
            color: #6B7280;
            margin-top: 4px;
        }}
        .section-card {{
            background: white;
            border-radius: 14px;
            border: 1px solid var(--gray-200);
            padding: 28px;
            margin-bottom: 28px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--gray-100);
            padding-bottom: 14px;
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-title::before {{
            content: "";
            display: inline-block;
            width: 4px;
            height: 18px;
            background: #0EA5E9;
            border-radius: 2px;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
            gap: 24px;
        }}
        .chart-box {{
            position: relative;
            height: 280px;
            width: 100%;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 12px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--gray-200);
        }}
        th {{
            background: var(--gray-50);
            font-weight: 600;
            color: var(--gray-700);
        }}
        .highlight-row {{
            background: #FEF3C7;
            font-weight: 600;
        }}
        .pill {{
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }}
        .pill-indigo {{ background: #E0E7FF; color: #4338CA; }}
        .pill-green {{ background: #D1FAE5; color: #065F46; }}
        .pill-amber {{ background: #FEF3C7; color: #92400E; }}
        .pill-rose {{ background: #FFE4E6; color: #BE123C; }}
        .pill-slate {{ background: #F1F5F9; color: #475569; }}

        .company-table-row:hover {{
            background-color: #F1F5F9 !important;
        }}
        .company-table-row.selected-row {{
            background-color: #EEF2FF !important;
        }}

        .insight-box {{
            background: #F0F9FF;
            border-left: 4px solid #0EA5E9;
            padding: 16px 20px;
            border-radius: 0 8px 8px 0;
            margin-top: 16px;
            font-size: 14px;
            color: #0369A1;
        }}
        .insight-box strong {{
            color: #0C4A6E;
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <div>
            <h1>ASOBIBA FES 2026: 企業別・有料無料別マッチング詳細分析レポート</h1>
            <p>全12社個別カルテ（受発注・選別感度・プロファイル）＆ 有料企業 vs 無料企業 完全層別分析</p>
            <div class="badge-bar">
                <span class="badge">全12企業 網羅</span>
                <span class="badge">有料企業: 4社 (122接触)</span>
                <span class="badge">無料企業: 8社 (191接触)</span>
            </div>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a href="asobiba_fes_fit_analysis_report.html" class="btn-header">
                📊 バリュー・パーソナリティ全体ダッシュボードへ
            </a>
            <a href="index.html" class="btn-header">
                🏠 総合ダッシュボードへ戻る
            </a>
        </div>
    </header>

    <!-- Top KPI Cards -->
    <div class="grid-4">
        <div class="kpi-card">
            <div class="kpi-title">バリュー選別の最強証明（無料企業）</div>
            <div class="kpi-value" style="color: var(--primary);">+7.51 <span style="font-size: 14px; font-weight: normal; color: #6B7280;">pt</span></div>
            <div class="kpi-sub">めっちゃ知りたい(64.24) vs なし(56.73) [p&lt;0.0001]</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">パーソナリティ自然実験の証明</div>
            <div class="kpi-value" style="color: var(--success);">r = 0.034</div>
            <div class="kpi-sub">バリューと完全独立 ➔ 純粋な因果効果</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">トップマッチ企業</div>
            <div class="kpi-value" style="font-size: 22px; color: #111827; padding-top: 4px;">株式会社ベル</div>
            <div class="kpi-sub">マッチ率 <strong>65.5%</strong> (19/29件成立)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">学生人気 No.1 企業</div>
            <div class="kpi-value" style="font-size: 20px; color: #D97706; padding-top: 4px;">カペラ京都 (NTT都市)</div>
            <div class="kpi-sub">学生めっちゃ知りたい <strong>9名</strong> (全社最多)</div>
        </div>
    </div>

{company_detail_section_html}

    <!-- Section: Paid vs Free Stratified Analysis -->
    <div class="section-card">
        <div class="section-header">
            <div>
                <div class="section-title">⚖️ 【層別比較】有料出展企業（4社） vs 無料出展企業（8社）</div>
                <p style="font-size: 13px; color: #6B7280; margin-top: 4px;">新前提（有料はバリュー高優先配席、無料は高低混合）の統計検証</p>
            </div>
            <span class="pill pill-green">自然実験の完全立証</span>
        </div>
        
        <div class="grid-2">
            <div>
                <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">🏢 企業アクション別バリュー推移（有料 vs 無料）</h3>
                <div class="chart-box">
                    <canvas id="compChart"></canvas>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>企業アクション</th>
                            <th>有料企業 (N=122)</th>
                            <th>無料企業 (N=191)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>なし</td>
                            <td>60.09</td>
                            <td><strong>56.73</strong> (低バリューを見送り)</td>
                        </tr>
                        <tr>
                            <td>知りたい</td>
                            <td>62.01</td>
                            <td>60.46</td>
                        </tr>
                        <tr class="highlight-row">
                            <td>めっちゃ知りたい</td>
                            <td>63.13</td>
                            <td><strong style="color: var(--primary);">64.24 (+7.51pt!)</strong></td>
                        </tr>
                        <tr>
                            <td>分散分析 (ANOVA)</td>
                            <td>F=1.84 (p=0.161)</td>
                            <td><strong>F=11.162 (p&lt;0.0001, η²=0.106)</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div>
                <h3 style="font-size: 15px; margin-bottom: 12px; font-weight: 700;">🎓 学生アクション別パーソナリティ推移（有料 vs 無料）</h3>
                <div class="chart-box">
                    <canvas id="studChart"></canvas>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>学生アクション</th>
                            <th>有料企業に対するP値</th>
                            <th>無料企業に対するP値</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>なし</td>
                            <td>78.82</td>
                            <td>77.55</td>
                        </tr>
                        <tr>
                            <td>知りたい</td>
                            <td>81.47</td>
                            <td>77.63</td>
                        </tr>
                        <tr class="highlight-row">
                            <td>めっちゃ知りたい</td>
                            <td><strong style="color: #D97706;">82.44 (+3.62pt)</strong></td>
                            <td>79.22</td>
                        </tr>
                        <tr>
                            <td>相関 r (バリュー × P)</td>
                            <td>r = +0.079 (無相関)</td>
                            <td>r = -0.002 (完全無相関)</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    new Chart(document.getElementById('compChart'), {{
        type: 'bar',
        data: {{
            labels: ['なし', '知りたい', 'めっちゃ知りたい'],
            datasets: [
                {{
                    label: '有料企業 (N=122)',
                    data: [60.09, 62.01, 63.13],
                    backgroundColor: '#4F46E5',
                    borderRadius: 6
                }},
                {{
                    label: '無料企業 (N=191)',
                    data: [56.73, 60.46, 64.24],
                    backgroundColor: '#06B6D4',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ min: 50, max: 70 }} }}
        }}
    }});

    new Chart(document.getElementById('studChart'), {{
        type: 'bar',
        data: {{
            labels: ['なし', '知りたい', 'めっちゃ知りたい'],
            datasets: [
                {{
                    label: '有料企業ブース (N=122)',
                    data: [78.82, 81.47, 82.44],
                    backgroundColor: '#F59E0B',
                    borderRadius: 6
                }},
                {{
                    label: '無料企業ブース (N=164)',
                    data: [77.55, 77.63, 79.22],
                    backgroundColor: '#9CA3AF',
                    borderRadius: 6
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ min: 70, max: 86 }} }}
        }}
    }});

{company_detail_js}

    // 初期表示で個別カルテを初期化
    document.addEventListener('DOMContentLoaded', function() {{
        initCompanyDetailCharts();
    }});
</script>

</body>
</html>"""

with open('company_fit_report.html', 'w', encoding='utf-8') as f:
    f.write(company_page_html)

print('[OK] asobiba_fes_fit_analysis_report.html (タブ統合版) および company_fit_report.html (独立版) を生成しました。')

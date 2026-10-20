#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASOBIBA FES 2026: バリューフィット・パーソナリティフィットとマッチング傾向の統計分析スクリプト
- 全体分析
- 有料企業 vs 無料企業 完全層別分析
- 全12社別 個別データ分析
外部ライブラリ非依存（Python標準ライブラリのみで動作）
"""

import csv
import glob
import math
import json
import os

# ==========================================
# 1. 統計・数学ヘルパー関数
# ==========================================

def normal_cdf(x):
    """標準正規分布の累積分布関数"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def mean(data):
    return sum(data) / len(data) if data else 0.0

def variance(data, ddof=1):
    n = len(data)
    if n <= ddof:
        return 0.0
    m = mean(data)
    return sum((x - m) ** 2 for x in data) / (n - ddof)

def std_dev(data, ddof=1):
    return math.sqrt(variance(data, ddof))

def median_and_quartiles(data):
    if not data:
        return 0.0, 0.0, 0.0
    s = sorted(data)
    n = len(s)
    
    def get_percentile(p):
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return s[int(k)]
        d0 = s[int(f)] * (c - k)
        d1 = s[int(c)] * (k - f)
        return d0 + d1

    return get_percentile(0.5), get_percentile(0.25), get_percentile(0.75)

def calc_stats(data):
    if not data:
        return {
            'count': 0, 'mean': 0.0, 'std': 0.0,
            'median': 0.0, 'q25': 0.0, 'q75': 0.0,
            'min': 0.0, 'max': 0.0
        }
    med, q25, q75 = median_and_quartiles(data)
    return {
        'count': len(data),
        'mean': round(mean(data), 2),
        'std': round(std_dev(data), 2),
        'median': round(med, 2),
        'q25': round(q25, 2),
        'q75': round(q75, 2),
        'min': round(min(data), 2),
        'max': round(max(data), 2)
    }

def welch_t_test(g1, g2):
    """Welchのt検定（分散の等質性を仮定しない）"""
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return {'t': 0.0, 'df': 0.0, 'p': 1.0, 'd': 0.0}
    m1, m2 = mean(g1), mean(g2)
    v1, v2 = variance(g1), variance(g2)
    
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return {'t': 0.0, 'df': 0.0, 'p': 1.0, 'd': 0.0}
    t = (m1 - m2) / se
    
    df = ((v1 / n1 + v2 / n2) ** 2) / (
        ((v1 / n1) ** 2) / (n1 - 1) + ((v2 / n2) ** 2) / (n2 - 1)
    )
    
    pooled_s = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    d = (m1 - m2) / pooled_s if pooled_s > 0 else 0.0
    
    z = abs(t)
    p = 2.0 * (1.0 - normal_cdf(z))
    
    return {'t': round(t, 3), 'df': round(df, 1), 'p': round(p, 4), 'd': round(d, 3)}

def mann_whitney_u(g1, g2):
    """マン・ホイットニーのU検定"""
    n1, n2 = len(g1), len(g2)
    if n1 == 0 or n2 == 0:
        return {'u': 0.0, 'z': 0.0, 'p': 1.0, 'r': 0.0}
    
    combined = [(x, 1) for x in g1] + [(x, 2) for x in g2]
    combined.sort(key=lambda item: item[0])
    
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
        
    r1 = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == 1)
    u1 = r1 - (n1 * (n1 + 1)) / 2.0
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    
    mu_u = (n1 * n2) / 2.0
    sigma_u = math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12.0)
    z = (u - mu_u) / sigma_u if sigma_u > 0 else 0.0
    p = 2.0 * (1.0 - normal_cdf(abs(z)))
    r = abs(z) / math.sqrt(n1 + n2)
    
    return {'u': round(u, 1), 'z': round(z, 3), 'p': round(p, 4), 'r': round(r, 3)}

def one_way_anova(groups):
    """一元配置分散分析（ANOVA）"""
    valid_groups = [g for g in groups if len(g) > 0]
    k = len(valid_groups)
    total_n = sum(len(g) for g in valid_groups)
    if k < 2 or total_n <= k:
        return {'f': 0.0, 'p': 1.0, 'df_between': 0, 'df_within': 0, 'eta_sq': 0.0}
    
    grand_mean = sum(sum(g) for g in valid_groups) / total_n
    ss_between = sum(len(g) * ((mean(g) - grand_mean) ** 2) for g in valid_groups)
    ss_within = sum(sum((x - mean(g)) ** 2 for x in g) for g in valid_groups)
    ss_total = ss_between + ss_within
    
    df_between = k - 1
    df_within = total_n - k
    
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within if df_within > 0 else 1.0
    
    f = ms_between / ms_within if ms_within > 0 else 0.0
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
    
    if f <= 0:
        p = 1.0
    else:
        d1, d2 = float(df_between), float(df_within)
        a = 2.0 / (9.0 * d1)
        b = 2.0 / (9.0 * d2)
        z = ((1.0 - b) * (f ** (1.0 / 3.0)) - (1.0 - a)) / math.sqrt(b * (f ** (2.0 / 3.0)) + a)
        p = 1.0 - normal_cdf(z)
        p = max(0.0, min(1.0, p))
        
    return {
        'f': round(f, 3),
        'p': round(p, 4),
        'df_between': df_between,
        'df_within': df_within,
        'eta_sq': round(eta_sq, 3)
    }

def spearman_rank_correlation(x, y):
    """スピアマンの順位相関係数"""
    n = len(x)
    if n < 3:
        return {'rho': 0.0, 'p': 1.0}
    
    def rank_data(arr):
        indexed = sorted(enumerate(arr), key=lambda it: it[1])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n and indexed[j][1] == indexed[i][1]:
                j += 1
            avg_rank = (i + 1 + j) / 2.0
            for k in range(i, j):
                ranks[indexed[k][0]] = avg_rank
            i = j
        return ranks
    
    rx = rank_data(x)
    ry = rank_data(y)
    
    mx, my = mean(rx), mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)) * sum((ry[i] - my) ** 2 for i in range(n)))
    
    rho = num / den if den > 0 else 0.0
    if abs(rho) >= 1.0:
        p = 0.0
    else:
        t = rho * math.sqrt((n - 2) / (1.0 - rho ** 2))
        p = 2.0 * (1.0 - normal_cdf(abs(t)))
        
    return {'rho': round(rho, 3), 'p': round(p, 4)}

def pearson_correlation(x, y):
    """ピアソンの積率相関係数"""
    n = len(x)
    if n < 2:
        return 0.0
    mx, my = mean(x), mean(y)
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (n - 1)
    sx = std_dev(x)
    sy = std_dev(y)
    return round(cov / (sx * sy), 3) if sx > 0 and sy > 0 else 0.0

# ==========================================
# 2. ロジスティック回帰（Newton-Raphson）
# ==========================================

def solve_linear_system(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        max_row = i
        for k in range(i + 1, n):
            if abs(M[k][i]) > abs(M[max_row][i]):
                max_row = k
        M[i], M[max_row] = M[max_row], M[i]
        
        pivot = M[i][i]
        if abs(pivot) < 1e-12:
            return None
            
        for j in range(i, n + 1):
            M[i][j] /= pivot
            
        for k in range(n):
            if k != i:
                factor = M[k][i]
                for j in range(i, n + 1):
                    M[k][j] -= factor * M[i][j]
                    
    return [M[i][n] for i in range(n)]

def invert_matrix(A):
    n = len(A)
    inv = []
    for col in range(n):
        b = [1.0 if i == col else 0.0 for i in range(n)]
        res = solve_linear_system(A, b)
        if res is None:
            return None
        inv.append(res)
    return [[inv[r][c] for r in range(n)] for c in range(n)]

def logistic_regression(X, y, max_iter=25, tol=1e-6):
    n = len(y)
    p = len(X[0])
    beta = [0.0] * p
    
    for it in range(max_iter):
        probs = []
        for i in range(n):
            logit = sum(X[i][j] * beta[j] for j in range(p))
            logit = max(-30.0, min(30.0, logit))
            probs.append(1.0 / (1.0 + math.exp(-logit)))
            
        grad = [0.0] * p
        for j in range(p):
            grad[j] = sum(X[i][j] * (y[i] - probs[i]) for i in range(n))
            
        H = [[0.0] * p for _ in range(p)]
        for j in range(p):
            for k in range(p):
                H[j][k] = - sum(X[i][j] * X[i][k] * probs[i] * (1.0 - probs[i]) for i in range(n))
                
        neg_H = [[-H[j][k] for k in range(p)] for j in range(p)]
        delta = solve_linear_system(neg_H, grad)
        if delta is None:
            break
            
        for j in range(p):
            beta[j] += delta[j]
            
        if max(abs(d) for d in delta) < tol:
            break
            
    inv_neg_H = invert_matrix(neg_H)
    se = [0.0] * p
    if inv_neg_H:
        for j in range(p):
            se[j] = math.sqrt(max(0.0, inv_neg_H[j][j]))
            
    results = []
    for j in range(p):
        b = beta[j]
        s = se[j]
        z = b / s if s > 0 else 0.0
        pval = 2.0 * (1.0 - normal_cdf(abs(z)))
        odds_ratio = math.exp(b) if abs(b) < 20 else math.nan
        ci_lower = math.exp(b - 1.96 * s) if abs(b) < 20 else math.nan
        ci_upper = math.exp(b + 1.96 * s) if abs(b) < 20 else math.nan
        results.append({
            'coef': round(b, 4),
            'se': round(s, 4),
            'z': round(z, 3),
            'p': round(pval, 4),
            'odds_ratio': round(odds_ratio, 3),
            'ci_95': (round(ci_lower, 3), round(ci_upper, 3))
        })
    return results

# ==========================================
# 3. データ読み込みと前処理
# ==========================================

def load_and_preprocess_data():
    files = glob.glob('*全テ*')
    if not files:
        raise FileNotFoundError("データファイルが見つかりません。")
    filename = files[0]
    
    paid_companies = {
        '株式会社リード・イノベーション',
        '株式会社Unith Link',
        '株式会社ベル',
        'NTT 都市開発ホテルマネジメント株式会社　カペラ京都'
    }
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)
        
    processed = []
    for r in raw_rows:
        s_act = r['学生の当日回答'].strip()
        if s_act in ('知りたいを選択せず', '未回答'):
            s_act_clean = 'なし'
            s_score = 0
        elif s_act == '知りたい':
            s_act_clean = '知りたい'
            s_score = 1
        elif s_act == 'めっちゃ知りたい':
            s_act_clean = 'めっちゃ知りたい'
            s_score = 2
        else:
            s_act_clean = 'なし'
            s_score = 0
            
        c_act = r['企業の現在の知りたい'].strip()
        if c_act in ('知りたいなし', '知りたいを選択せず', '未回答'):
            c_act_clean = 'なし'
            c_score = 0
        elif c_act == '知りたい':
            c_act_clean = '知りたい'
            c_score = 1
        elif c_act == 'めっちゃ知りたい':
            c_act_clean = 'めっちゃ知りたい'
            c_score = 2
        else:
            c_act_clean = 'なし'
            c_score = 0
            
        v_fit = float(r['バリューフィット'])
        p_fit_str = r['パーソナリティフィット'].strip()
        p_fit = float(p_fit_str) if p_fit_str != '未算出' else None
        
        is_matched = 1 if r['現在のマッチ状況'].strip() == 'マッチ済み' else 0
        is_paid = 1 if r['企業名'].strip() in paid_companies else 0
        turn_str = r['割当ターン'].strip()
        turn_num = int(turn_str.replace('第', '').replace('ターン', '')) if 'ターン' in turn_str else 0
        
        processed.append({
            'company': r['企業名'].strip(),
            'name': r['氏名'].strip(),
            'university': r['大学'].strip(),
            'turn': turn_num,
            'value_fit': v_fit,
            'personality_fit': p_fit,
            'student_action': s_act_clean,
            'student_score': s_score,
            'company_action': c_act_clean,
            'company_score': c_score,
            'is_matched': is_matched,
            'is_paid': is_paid
        })
        
    return processed

# ==========================================
# 4. サブセット分析（全体、有料、無料用汎用関数）
# ==========================================

def analyze_subset(subset, name="subset"):
    count = len(subset)
    valid_p = [d for d in subset if d['personality_fit'] is not None]
    
    # 企業アクション別
    c_v = {'なし': [], '知りたい': [], 'めっちゃ知りたい': []}
    c_p = {'なし': [], '知りたい': [], 'めっちゃ知りたい': []}
    for d in subset:
        c_v[d['company_action']].append(d['value_fit'])
        if d['personality_fit'] is not None:
            c_p[d['company_action']].append(d['personality_fit'])
            
    stats_c_v = {k: calc_stats(v) for k, v in c_v.items()}
    stats_c_p = {k: calc_stats(v) for k, v in c_p.items()}
    
    anova_c_v = one_way_anova([c_v['なし'], c_v['知りたい'], c_v['めっちゃ知りたい']])
    anova_c_p = one_way_anova([c_p['なし'], c_p['知りたい'], c_p['めっちゃ知りたい']])
    
    t_c_v_very_vs_none = welch_t_test(c_v['めっちゃ知りたい'], c_v['なし'])
    sp_c_v = spearman_rank_correlation([d['company_score'] for d in subset], [d['value_fit'] for d in subset])
    sp_c_p = spearman_rank_correlation([d['company_score'] for d in valid_p], [d['personality_fit'] for d in valid_p])
    
    # 学生アクション別
    s_v = {'なし': [], '知りたい': [], 'めっちゃ知りたい': []}
    s_p = {'なし': [], '知りたい': [], 'めっちゃ知りたい': []}
    for d in subset:
        s_v[d['student_action']].append(d['value_fit'])
        if d['personality_fit'] is not None:
            s_p[d['student_action']].append(d['personality_fit'])
            
    stats_s_v = {k: calc_stats(v) for k, v in s_v.items()}
    stats_s_p = {k: calc_stats(v) for k, v in s_p.items()}
    
    anova_s_v = one_way_anova([s_v['なし'], s_v['知りたい'], s_v['めっちゃ知りたい']])
    anova_s_p = one_way_anova([s_p['なし'], s_p['知りたい'], s_p['めっちゃ知りたい']])
    
    t_s_p_very_vs_none = welch_t_test(s_p['めっちゃ知りたい'], s_p['なし'])
    sp_s_v = spearman_rank_correlation([d['student_score'] for d in subset], [d['value_fit'] for d in subset])
    sp_s_p = spearman_rank_correlation([d['student_score'] for d in valid_p], [d['personality_fit'] for d in valid_p])
    
    # マッチ別
    m_v = {'マッチ済み': [d['value_fit'] for d in subset if d['is_matched'] == 1],
           '未マッチ': [d['value_fit'] for d in subset if d['is_matched'] == 0]}
    m_p = {'マッチ済み': [d['personality_fit'] for d in valid_p if d['is_matched'] == 1],
           '未マッチ': [d['personality_fit'] for d in valid_p if d['is_matched'] == 0]}
           
    stats_m_v = {k: calc_stats(v) for k, v in m_v.items()}
    stats_m_p = {k: calc_stats(v) for k, v in m_p.items()}
    t_m_v = welch_t_test(m_v['マッチ済み'], m_v['未マッチ'])
    t_m_p = welch_t_test(m_p['マッチ済み'], m_p['未マッチ'])
    
    # 3x3マトリクス
    matrix_3x3 = []
    v_tiers = [('低 (<58.0)', lambda v: v < 58), ('中 (58.0〜63.9)', lambda v: 58 <= v < 64), ('高 (>=64.0)', lambda v: v >= 64)]
    p_tiers = [('高 (>=82.0)', lambda p: p >= 82), ('中 (76.0〜81.9)', lambda p: 76 <= p < 82), ('低 (<76.0)', lambda p: p < 76)]
    
    for p_name, p_cond in p_tiers:
        row = []
        for v_name, v_cond in v_tiers:
            cell_items = [d for d in valid_p if v_cond(d['value_fit']) and p_cond(d['personality_fit'])]
            n = len(cell_items)
            matches = sum(d['is_matched'] for d in cell_items)
            match_rate = round(matches / n * 100, 1) if n > 0 else 0.0
            comp_very = sum(1 for d in cell_items if d['company_action'] == 'めっちゃ知りたい')
            comp_very_rate = round(comp_very / n * 100, 1) if n > 0 else 0.0
            stud_know = sum(1 for d in cell_items if d['student_action'] in ('知りたい', 'めっちゃ知りたい'))
            stud_know_rate = round(stud_know / n * 100, 1) if n > 0 else 0.0
            row.append({
                'v_tier': v_name, 'p_tier': p_name,
                'count': n, 'matches': matches, 'match_rate': match_rate,
                'comp_very_rate': comp_very_rate, 'stud_know_rate': stud_know_rate
            })
        matrix_3x3.append(row)
        
    # バリューとパーソナリティの相関
    corr_vp = pearson_correlation([d['value_fit'] for d in valid_p], [d['personality_fit'] for d in valid_p])
    
    return {
        'name': name,
        'count': count,
        'valid_p_count': len(valid_p),
        'match_count': sum(d['is_matched'] for d in subset),
        'match_rate': round(sum(d['is_matched'] for d in subset) / count * 100, 1),
        'value_stats': calc_stats([d['value_fit'] for d in subset]),
        'personality_stats': calc_stats([d['personality_fit'] for d in valid_p]),
        'value_personality_corr': corr_vp,
        'company_analysis': {
            'stats_value': stats_c_v,
            'stats_personality': stats_c_p,
            'anova_value': anova_c_v,
            'anova_personality': anova_c_p,
            't_very_vs_none': t_c_v_very_vs_none,
            'spearman_value': sp_c_v,
            'spearman_personality': sp_c_p
        },
        'student_analysis': {
            'stats_value': stats_s_v,
            'stats_personality': stats_s_p,
            'anova_value': anova_s_v,
            'anova_personality': anova_s_p,
            't_very_vs_none': t_s_p_very_vs_none,
            'spearman_value': sp_s_v,
            'spearman_personality': sp_s_p
        },
        'match_analysis': {
            'stats_value': stats_m_v,
            'stats_personality': stats_m_p,
            'welch_value': t_m_v,
            'welch_personality': t_m_p
        },
        'matrix_3x3': matrix_3x3
    }

# ==========================================
# 5. 全12社別 個別データ分析
# ==========================================

def analyze_companies(data):
    companies = sorted(list(set(d['company'] for d in data)))
    
    paid_companies = {
        '株式会社リード・イノベーション',
        '株式会社Unith Link',
        '株式会社ベル',
        'NTT 都市開発ホテルマネジメント株式会社　カペラ京都'
    }
    
    company_profiles = []
    
    for c in companies:
        c_data = [d for d in data if d['company'] == c]
        n = len(c_data)
        matches = sum(d['is_matched'] for d in c_data)
        match_rate = round(matches / n * 100, 1)
        
        is_paid = 1 if c in paid_companies else 0
        
        # アクション数
        c_very = sum(1 for d in c_data if d['company_action'] == 'めっちゃ知りたい')
        c_know = sum(1 for d in c_data if d['company_action'] == '知りたい')
        c_none = sum(1 for d in c_data if d['company_action'] == 'なし')
        
        s_very = sum(1 for d in c_data if d['student_action'] == 'めっちゃ知りたい')
        s_know = sum(1 for d in c_data if d['student_action'] == '知りたい')
        s_none = sum(1 for d in c_data if d['student_action'] == 'なし')
        
        # フィット度
        vf_all = [d['value_fit'] for d in c_data]
        pf_all = [d['personality_fit'] for d in c_data if d['personality_fit'] is not None]
        
        vf_stats = calc_stats(vf_all)
        pf_stats = calc_stats(pf_all) if pf_all else None
        
        # 企業のバリュー選別感度
        vf_very = [d['value_fit'] for d in c_data if d['company_action'] == 'めっちゃ知りたい']
        vf_know = [d['value_fit'] for d in c_data if d['company_action'] == '知りたい']
        vf_none = [d['value_fit'] for d in c_data if d['company_action'] == 'なし']
        
        m_very = round(mean(vf_very), 2) if vf_very else None
        m_know = round(mean(vf_know), 2) if vf_know else None
        m_none = round(mean(vf_none), 2) if vf_none else None
        diff_very_none = round(m_very - m_none, 2) if (m_very is not None and m_none is not None) else None
        
        # 学生のパーソナリティ感度
        if pf_all:
            pf_know_plus = [d['personality_fit'] for d in c_data if d['student_action'] in ('知りたい', 'めっちゃ知りたい') and d['personality_fit'] is not None]
            pf_none_s = [d['personality_fit'] for d in c_data if d['student_action'] == 'なし' and d['personality_fit'] is not None]
            s_pf_know_mean = round(mean(pf_know_plus), 2) if pf_know_plus else None
            s_pf_none_mean = round(mean(pf_none_s), 2) if pf_none_s else None
            diff_stud_p = round(s_pf_know_mean - s_pf_none_mean, 2) if (s_pf_know_mean is not None and s_pf_none_mean is not None) else None
        else:
            s_pf_know_mean, s_pf_none_mean, diff_stud_p = None, None, None
            
        # プロファイル分類判定
        if match_rate >= 55.0:
            category = "高マッチ・高エンゲージメント型"
        elif diff_very_none is not None and diff_very_none >= 6.0:
            category = "超厳格バリュースクリーニング型"
        elif (s_very + s_know) / n >= 0.65:
            category = "学生人気・集客牽引型"
        elif c_none / n >= 0.50:
            category = "アクション慎重・厳選型"
        else:
            category = "標準バランス型"
            
        company_profiles.append({
            'company': c,
            'is_paid': is_paid,
            'plan_type': '有料出展' if is_paid else '無料出展',
            'count': n,
            'matches': matches,
            'match_rate': match_rate,
            'category': category,
            'company_actions': {
                'very': c_very, 'know': c_know, 'none': c_none,
                'very_rate': round(c_very / n * 100, 1),
                'active_rate': round((c_very + c_know) / n * 100, 1)
            },
            'student_actions': {
                'very': s_very, 'know': s_know, 'none': s_none,
                'very_rate': round(s_very / n * 100, 1),
                'active_rate': round((s_very + s_know) / n * 100, 1)
            },
            'value_stats': vf_stats,
            'personality_stats': pf_stats,
            'value_screening': {
                'mean_very': m_very,
                'mean_know': m_know,
                'mean_none': m_none,
                'diff_very_none': diff_very_none
            },
            'student_personality_reaction': {
                'mean_know_plus': s_pf_know_mean,
                'mean_none': s_pf_none_mean,
                'diff': diff_stud_p
            }
        })
        
    # マッチ率順にソート
    company_profiles.sort(key=lambda x: x['match_rate'], reverse=True)
    return company_profiles

# ==========================================
# 6. メイン実行
# ==========================================

def run_analysis():
    data = load_and_preprocess_data()
    paid_data = [d for d in data if d['is_paid'] == 1]
    free_data = [d for d in data if d['is_paid'] == 0]
    
    print("=" * 60)
    print(f"ASOBIBA FES 2026 拡張データ分析実行")
    print(f"全体: {len(data)}件 | 有料企業: {len(paid_data)}件 | 無料企業: {len(free_data)}件")
    print("=" * 60)
    
    # 1. 全体分析
    overall_res = analyze_subset(data, name="overall")
    
    # 2. 有料企業分析
    paid_res = analyze_subset(paid_data, name="paid")
    
    # 3. 無料企業分析
    free_res = analyze_subset(free_data, name="free")
    
    # 4. 全12社個別分析
    company_profiles = analyze_companies(data)
    
    # 5. ロジスティック回帰（全体）
    valid_p_data = [d for d in data if d['personality_fit'] is not None]
    X_reg = [[1.0, d['value_fit'], d['personality_fit'], float(d['is_paid'])] for d in valid_p_data]
    y_reg = [d['is_matched'] for d in valid_p_data]
    logit_res = logistic_regression(X_reg, y_reg)
    logit_names = ['切片', 'バリューフィット', 'パーソナリティフィット', '有料出展企業フラグ']
    logit_table = [{'variable': name, **res} for name, res in zip(logit_names, logit_res)]
    
    output = {
        'overall': overall_res,
        'paid_analysis': paid_res,
        'free_analysis': free_res,
        'company_profiles': company_profiles,
        'logistic_regression': logit_table
    }
    
    os.makedirs('scripts', exist_ok=True)
    with open('scripts/analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print("[OK] 分析完了！scripts/analysis_results.json を更新しました。")
    return output

if __name__ == '__main__':
    run_analysis()

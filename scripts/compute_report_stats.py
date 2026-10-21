#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/compute_report_stats.py
実データ (313件) から、レポートに必要なすべての統計量を純Pythonで自動計算し、
scripts/report_stats.json に出力する。
"""

import sys, math, json
from collections import defaultdict
sys.path.append('scripts')
from analyze_fit_actions import load_and_preprocess_data, mean

def ok(v):
    return v is not None and not (isinstance(v, float) and math.isnan(v))

def calc_std(lst):
    if len(lst) <= 1: return 0.0
    m = mean(lst)
    return math.sqrt(sum((x - m)**2 for x in lst) / (len(lst) - 1))

def calc_median(lst):
    if not lst: return 0.0
    s = sorted(lst)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    else:
        return (s[n // 2 - 1] + s[n // 2]) / 2.0

def solve_linear(A, b):
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-14:
            raise ValueError("Singular matrix in solve_linear")
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]

def inv_matrix(A):
    n = len(A)
    cols = []
    for j in range(n):
        e = [1.0 if i == j else 0.0 for i in range(n)]
        cols.append(solve_linear(A, e))
    return [[cols[j][i] for j in range(n)] for i in range(n)]

# 2値ロジスティック回帰 (y=1 vs y=0)
def fit_binary_logit(data, x_cols, y_col):
    rows = []
    for r in data:
        y = r[y_col]
        if y not in ['なし', '知りたい', 'めっちゃ知りたい']: continue
        xs = [r[col] for col in x_cols]
        if any(not ok(x) for x in xs): continue
        y_bin = 0.0 if y == 'なし' else 1.0 # 0=なし, 1=知りたい以上
        rows.append(([1.0] + [float(x) for x in xs], y_bin))
        
    N = len(rows)
    K = len(x_cols) + 1
    beta = [0.0] * K
    
    for _ in range(100):
        grad = [0.0] * K
        Info = [[0.0] * K for _ in range(K)]
        for x, y in rows:
            eta = sum(beta[i] * x[i] for i in range(K))
            p = 1.0 / (1.0 + math.exp(-max(min(eta, 30.0), -30.0)))
            err = y - p
            w = p * (1.0 - p)
            for i in range(K):
                grad[i] += err * x[i]
                for j in range(K):
                    Info[i][j] += w * x[i] * x[j]
        try:
            delta = solve_linear(Info, grad)
        except Exception:
            return None
        beta = [b + d for b, d in zip(beta, delta)]
        if max(abs(d) for d in delta) < 1e-9:
            break
            
    try:
        cov = inv_matrix(Info)
    except Exception:
        return None
    se = [math.sqrt(max(0.0, cov[i][i])) for i in range(K)]
    
    res = {'N': N, 'x_cols': x_cols, 'params': {}}
    for i, col_name in enumerate(['const'] + x_cols):
        b_val = beta[i]
        se_val = se[i]
        z_val = b_val / se_val if se_val > 0 else 0.0
        p_val = math.erfc(abs(z_val) / math.sqrt(2))
        scale = 10.0 if col_name != 'const' else 1.0
        or_val = math.exp(scale * b_val)
        ci_low = math.exp(scale * (b_val - 1.96 * se_val))
        ci_high = math.exp(scale * (b_val + 1.96 * se_val))
        res['params'][col_name] = {
            'beta': b_val,
            'se': se_val,
            'z': z_val,
            'p': p_val,
            'or_10': or_val,
            'ci_lower': ci_low,
            'ci_upper': ci_high
        }
    return res

# 多項ロジスティック回帰 (0=なし, 1=知りたい, 2=めっちゃ知りたい)
def fit_mnlogit(data, x_cols, y_col):
    rows = []
    for r in data:
        y = r[y_col]
        if y not in ['なし', '知りたい', 'めっちゃ知りたい']: continue
        xs = [r[col] for col in x_cols]
        if any(not ok(x) for x in xs): continue
        y_idx = 0 if y == 'なし' else (1 if y == '知りたい' else 2)
        rows.append(([1.0] + [float(x) for x in xs], y_idx))
    
    N = len(rows)
    K = len(x_cols) + 1
    P_dim = 2 * K
    beta = [0.0] * P_dim
    
    for it in range(100):
        grad = [0.0] * P_dim
        Info = [[0.0] * P_dim for _ in range(P_dim)]
        
        for x, y in rows:
            eta1 = sum(beta[i] * x[i] for i in range(K))
            eta2 = sum(beta[K + i] * x[i] for i in range(K))
            m = max(0.0, eta1, eta2)
            e0 = math.exp(-m)
            e1 = math.exp(max(min(eta1 - m, 30.0), -30.0))
            e2 = math.exp(max(min(eta2 - m, 30.0), -30.0))
            denom = e0 + e1 + e2
            p1 = e1 / denom
            p2 = e2 / denom
            
            y1 = 1.0 if y == 1 else 0.0
            y2 = 1.0 if y == 2 else 0.0
            
            for i in range(K):
                grad[i] += (y1 - p1) * x[i]
                grad[K + i] += (y2 - p2) * x[i]
                
            for i in range(K):
                for j in range(K):
                    Info[i][j] += p1 * (1.0 - p1) * x[i] * x[j]
                    Info[K + i][K + j] += p2 * (1.0 - p2) * x[i] * x[j]
                    Info[i][K + j] -= p1 * p2 * x[i] * x[j]
                    Info[K + i][j] -= p1 * p2 * x[i] * x[j]
                    
        try:
            delta = solve_linear(Info, grad)
        except Exception:
            return None
            
        beta = [b + d for b, d in zip(beta, delta)]
        if max(abs(d) for d in delta) < 1e-9:
            break
            
    try:
        cov = inv_matrix(Info)
    except Exception:
        return None
    se = [math.sqrt(max(0.0, cov[i][i])) for i in range(P_dim)]
    
    res = {'N': N, 'x_cols': x_cols, '知りたい': {}, 'めっちゃ知りたい': {}}
    for target_idx, target_name in [(1, '知りたい'), (2, 'めっちゃ知りたい')]:
        offset = 0 if target_idx == 1 else K
        for i, col_name in enumerate(['const'] + x_cols):
            b_val = beta[offset + i]
            se_val = se[offset + i]
            z_val = b_val / se_val if se_val > 0 else 0.0
            p_val = math.erfc(abs(z_val) / math.sqrt(2))
            scale = 10.0 if col_name != 'const' else 1.0
            or_val = math.exp(scale * b_val)
            ci_low = math.exp(scale * (b_val - 1.96 * se_val))
            ci_high = math.exp(scale * (b_val + 1.96 * se_val))
            res[target_name][col_name] = {
                'beta': b_val,
                'se': se_val,
                'z': z_val,
                'p': p_val,
                'or_10': or_val,
                'ci_lower': ci_low,
                'ci_upper': ci_high
            }
    return res

# マッチング多変量ロジット (y=is_matched)
def fit_matching_logit(data):
    rows = [r for r in data if ok(r['value_fit']) and ok(r['personality_fit']) and r['is_matched'] is not None]
    N = len(rows)
    K = 4 # const, value_fit, personality_fit, is_paid
    beta = [0.0] * K
    for _ in range(100):
        grad = [0.0] * K
        Info = [[0.0] * K for _ in range(K)]
        for r in rows:
            x = [1.0, float(r['value_fit']), float(r['personality_fit']), float(r['is_paid'])]
            y = float(r['is_matched'])
            eta = sum(beta[i] * x[i] for i in range(K))
            p = 1.0 / (1.0 + math.exp(-max(min(eta, 30.0), -30.0)))
            err = y - p
            w = p * (1.0 - p)
            for i in range(K):
                grad[i] += err * x[i]
                for j in range(K):
                    Info[i][j] += w * x[i] * x[j]
        delta = solve_linear(Info, grad)
        beta = [b + d for b, d in zip(beta, delta)]
        if max(abs(d) for d in delta) < 1e-9:
            break
    cov = inv_matrix(Info)
    se = [math.sqrt(max(0.0, cov[i][i])) for i in range(K)]
    
    names = ['const', 'value_fit', 'personality_fit', 'is_paid']
    res = {'N': N, 'params': {}}
    for i, name in enumerate(names):
        b_val = beta[i]
        se_val = se[i]
        z_val = b_val / se_val if se_val > 0 else 0.0
        p_val = math.erfc(abs(z_val) / math.sqrt(2))
        scale = 10.0 if name in ['value_fit', 'personality_fit'] else 1.0
        or_val = math.exp(scale * b_val)
        ci_low = math.exp(scale * (b_val - 1.96 * se_val))
        ci_high = math.exp(scale * (b_val + 1.96 * se_val))
        res['params'][name] = {
            'beta': b_val,
            'se': se_val,
            'z': z_val,
            'p': p_val,
            'or_10': or_val,
            'ci_lower': ci_low,
            'ci_upper': ci_high
        }
    return res

def summarize_actions(sub_df):
    N_total = len(sub_df)
    res = {}
    for side, act_col in [('company', 'company_action'), ('student', 'student_action')]:
        cats = ['なし', '知りたい', 'めっちゃ知りたい']
        cat_stats = []
        for cat in cats:
            group = [r for r in sub_df if r[act_col] == cat]
            n = len(group)
            pct = (n / N_total * 100.0) if N_total > 0 else 0.0
            v_vals = [r['value_fit'] for r in group if ok(r['value_fit'])]
            p_vals = [r['personality_fit'] for r in group if ok(r['personality_fit'])]
            cat_stats.append({
                'action': cat,
                'count': n,
                'pct': pct,
                'v_mean': mean(v_vals) if v_vals else None,
                'v_std': calc_std(v_vals) if len(v_vals) > 1 else 0.0,
                'p_mean': mean(p_vals) if p_vals else None,
                'p_std': calc_std(p_vals) if len(p_vals) > 1 else 0.0,
                'p_n': len(p_vals)
            })
            
        # 2値 (なし vs 知りたい以上)
        group_bin0 = [r for r in sub_df if r[act_col] == 'なし']
        group_bin1 = [r for r in sub_df if r[act_col] in ['知りたい', 'めっちゃ知りたい']]
        bin_stats = []
        for label, grp in [('なし', group_bin0), ('知りたい以上', group_bin1)]:
            n = len(grp)
            pct = (n / N_total * 100.0) if N_total > 0 else 0.0
            v_vals = [r['value_fit'] for r in grp if ok(r['value_fit'])]
            p_vals = [r['personality_fit'] for r in grp if ok(r['personality_fit'])]
            bin_stats.append({
                'action_bin': label,
                'count': n,
                'pct': pct,
                'v_mean': mean(v_vals) if v_vals else None,
                'v_std': calc_std(v_vals) if len(v_vals) > 1 else 0.0,
                'p_mean': mean(p_vals) if p_vals else None,
                'p_std': calc_std(p_vals) if len(p_vals) > 1 else 0.0,
                'p_n': len(p_vals)
            })
            
        res[side] = {
            'three_cats': cat_stats,
            'binary': bin_stats
        }
    return res

def main():
    df = load_and_preprocess_data()
    print(f"Loaded {len(df)} rows.")
    
    # 1. 基本統計量
    v_all = [r['value_fit'] for r in df if ok(r['value_fit'])]
    p_all = [r['personality_fit'] for r in df if ok(r['personality_fit'])]
    
    kpis = {
        'value_fit': {
            'N': len(v_all),
            'mean': mean(v_all),
            'median': calc_median(v_all),
            'std': calc_std(v_all),
            'min': min(v_all),
            'max': max(v_all)
        },
        'personality_fit': {
            'N': len(p_all),
            'mean': mean(p_all),
            'median': calc_median(p_all),
            'std': calc_std(p_all),
            'min': min(p_all),
            'max': max(p_all)
        },
        'matching': {
            'N_all': len(df),
            'matched_all': sum(r['is_matched'] for r in df),
            'matched_all_pct': (sum(r['is_matched'] for r in df) / len(df) * 100.0),
            'N_pers': len([r for r in df if ok(r['personality_fit'])]),
            'matched_pers': sum(r['is_matched'] for r in df if ok(r['personality_fit'])),
            'matched_pers_pct': (sum(r['is_matched'] for r in df if ok(r['personality_fit'])) / len([r for r in df if ok(r['personality_fit'])]) * 100.0)
        }
    }
    
    # 2. 記述統計 (全体, 有料, 無料)
    overall_actions = summarize_actions(df)
    paid_actions = summarize_actions([r for r in df if r['is_paid'] == 1])
    free_actions = summarize_actions([r for r in df if r['is_paid'] == 0])
    
    # 3. 回帰分析 (全体, 有料, 無料)
    regressions = {}
    for seg_key, sub_data in [('overall', df), ('paid', [r for r in df if r['is_paid'] == 1]), ('free', [r for r in df if r['is_paid'] == 0])]:
        regressions[seg_key] = {
            'company': {
                'binary': {
                    'value_univ': fit_binary_logit(sub_data, ['value_fit'], 'company_action'),
                    'personality_univ': fit_binary_logit(sub_data, ['personality_fit'], 'company_action'),
                    'multivariate': fit_binary_logit(sub_data, ['value_fit', 'personality_fit'], 'company_action')
                },
                'multinomial': {
                    'value_univ': fit_mnlogit(sub_data, ['value_fit'], 'company_action'),
                    'personality_univ': fit_mnlogit(sub_data, ['personality_fit'], 'company_action'),
                    'multivariate': fit_mnlogit(sub_data, ['value_fit', 'personality_fit'], 'company_action')
                }
            },
            'student': {
                'binary': {
                    'personality_univ': fit_binary_logit(sub_data, ['personality_fit'], 'student_action'),
                    'value_univ': fit_binary_logit(sub_data, ['value_fit'], 'student_action'),
                    'multivariate': fit_binary_logit(sub_data, ['personality_fit', 'value_fit'], 'student_action')
                },
                'multinomial': {
                    'personality_univ': fit_mnlogit(sub_data, ['personality_fit'], 'student_action'),
                    'value_univ': fit_mnlogit(sub_data, ['value_fit'], 'student_action'),
                    'multivariate': fit_mnlogit(sub_data, ['personality_fit', 'value_fit'], 'student_action')
                }
            }
        }
        
    # 4. マッチング成立の多変量ロジット (N=286)
    matching_reg = fit_matching_logit(df)
    rows_matched = [r for r in df if ok(r['value_fit']) and ok(r['personality_fit']) and r['is_matched'] == 1]
    rows_unmatched = [r for r in df if ok(r['value_fit']) and ok(r['personality_fit']) and r['is_matched'] == 0]
    matching_comparison = {
        'N_valid': len(rows_matched) + len(rows_unmatched),
        'matched_count': len(rows_matched),
        'unmatched_count': len(rows_unmatched),
        'matched_v_mean': mean([r['value_fit'] for r in rows_matched]),
        'unmatched_v_mean': mean([r['value_fit'] for r in rows_unmatched]),
        'matched_p_mean': mean([r['personality_fit'] for r in rows_matched]),
        'unmatched_p_mean': mean([r['personality_fit'] for r in rows_unmatched]),
        'matched_paid_pct': (mean([r['is_paid'] for r in rows_matched]) * 100.0),
        'unmatched_paid_pct': (mean([r['is_paid'] for r in rows_unmatched]) * 100.0),
        'regression': matching_reg
    }
    
    # 5. 3x3 マトリクス (N=286)
    valid_p_df = [r for r in df if ok(r['value_fit']) and ok(r['personality_fit'])]
    matrix_cells = []
    for p_label, p_check in [('高 (≥82.0)', lambda p: p >= 82.0), ('中 (76.0〜81.9)', lambda p: 76.0 <= p < 82.0), ('低 (<76.0)', lambda p: p < 76.0)]:
        row_cells = []
        for v_label, v_check in [('低 (<58.0)', lambda v: v < 58.0), ('中 (58.0〜63.9)', lambda v: 58.0 <= v < 64.0), ('高 (≥64.0)', lambda v: v >= 64.0)]:
            cell_items = [r for r in valid_p_df if p_check(r['personality_fit']) and v_check(r['value_fit'])]
            n = len(cell_items)
            m_cnt = sum(r['is_matched'] for r in cell_items)
            m_rate = (m_cnt / n * 100.0) if n > 0 else 0.0
            c_high_cnt = sum(1 for r in cell_items if r['company_action'] == 'めっちゃ知りたい')
            c_any_cnt = sum(1 for r in cell_items if r['company_action'] in ['知りたい', 'めっちゃ知りたい'])
            s_high_cnt = sum(1 for r in cell_items if r['student_action'] == 'めっちゃ知りたい')
            s_any_cnt = sum(1 for r in cell_items if r['student_action'] in ['知りたい', 'めっちゃ知りたい'])
            row_cells.append({
                'p_label': p_label,
                'v_label': v_label,
                'count': n,
                'match_count': m_cnt,
                'match_rate': m_rate,
                'company_high_pct': (c_high_cnt / n * 100.0) if n > 0 else 0.0,
                'company_any_pct': (c_any_cnt / n * 100.0) if n > 0 else 0.0,
                'student_high_pct': (s_high_cnt / n * 100.0) if n > 0 else 0.0,
                'student_any_pct': (s_any_cnt / n * 100.0) if n > 0 else 0.0
            })
        matrix_cells.append(row_cells)
        
    # 6. 12社個別カルテ
    companies_summary = []
    comp_names = sorted(list(set(r['company'] for r in df)))
    comp_dict = defaultdict(list)
    for r in df:
        comp_dict[r['company']].append(r)
        
    for cname in comp_names:
        c_rows = comp_dict[cname]
        n = len(c_rows)
        is_paid = c_rows[0]['is_paid']
        m_cnt = sum(r['is_matched'] for r in c_rows)
        m_rate = (m_cnt / n * 100.0) if n > 0 else 0.0
        v_vals = [r['value_fit'] for r in c_rows if ok(r['value_fit'])]
        p_vals = [r['personality_fit'] for r in c_rows if ok(r['personality_fit'])]
        
        # 企業アクション別
        act_breakdown = {}
        for act in ['なし', '知りたい', 'めっちゃ知りたい']:
            grp = [r for r in c_rows if r['company_action'] == act]
            grp_v = [r['value_fit'] for r in grp if ok(r['value_fit'])]
            grp_p = [r['personality_fit'] for r in grp if ok(r['personality_fit'])]
            act_breakdown[act] = {
                'count': len(grp),
                'pct': (len(grp) / n * 100.0) if n > 0 else 0.0,
                'v_mean': mean(grp_v) if grp_v else None,
                'p_mean': mean(grp_p) if grp_p else None
            }
        # 2値
        act_breakdown['知りたい以上'] = {
            'count': act_breakdown['知りたい']['count'] + act_breakdown['めっちゃ知りたい']['count'],
            'pct': act_breakdown['知りたい']['pct'] + act_breakdown['めっちゃ知りたい']['pct']
        }
            
        # 学生アクション別
        st_breakdown = {}
        for act in ['なし', '知りたい', 'めっちゃ知りたい']:
            grp = [r for r in c_rows if r['student_action'] == act]
            grp_v = [r['value_fit'] for r in grp if ok(r['value_fit'])]
            grp_p = [r['personality_fit'] for r in grp if ok(r['personality_fit'])]
            st_breakdown[act] = {
                'count': len(grp),
                'pct': (len(grp) / n * 100.0) if n > 0 else 0.0,
                'v_mean': mean(grp_v) if grp_v else None,
                'p_mean': mean(grp_p) if grp_p else None
            }
        # 2値
        st_breakdown['知りたい以上'] = {
            'count': st_breakdown['知りたい']['count'] + st_breakdown['めっちゃ知りたい']['count'],
            'pct': st_breakdown['知りたい']['pct'] + st_breakdown['めっちゃ知りたい']['pct']
        }
            
        # めっちゃ知りたい群 - なし群 の平均差
        v_high = act_breakdown['めっちゃ知りたい']['v_mean']
        v_none = act_breakdown['なし']['v_mean']
        v_diff = (v_high - v_none) if (v_high is not None and v_none is not None) else None
        
        companies_summary.append({
            'name': cname,
            'is_paid': is_paid,
            'count': n,
            'match_count': m_cnt,
            'match_rate': m_rate,
            'v_mean': mean(v_vals) if v_vals else None,
            'v_std': calc_std(v_vals) if len(v_vals) > 1 else 0.0,
            'p_mean': mean(p_vals) if p_vals else None,
            'p_std': calc_std(p_vals) if len(p_vals) > 1 else 0.0,
            'p_n': len(p_vals),
            'v_diff_high_minus_none': v_diff,
            'company_actions': act_breakdown,
            'student_actions': st_breakdown
        })
        
    companies_summary.sort(key=lambda x: (-x['is_paid'], -x['match_rate']))
    
    out = {
        'kpis': kpis,
        'overall_actions': overall_actions,
        'paid_actions': paid_actions,
        'free_actions': free_actions,
        'regressions': regressions,
        'matching_comparison': matching_comparison,
        'matrix_3x3': matrix_cells,
        'companies': companies_summary
    }
    
    with open('scripts/report_stats.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        
    print("Successfully generated scripts/report_stats.json!")

if __name__ == '__main__':
    main()

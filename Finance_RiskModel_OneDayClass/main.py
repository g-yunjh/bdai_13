"""
Lending Club 스코어카드 검증 실습 (Kaggle Notebook 환경에서 실행)
- 성능: AUC, GINI, K-S  /  안정성: PSI
- 기준 연도 vs 최근 연도의 등급별 건수표로 계산하고, sklearn/scipy 결과와 대조함

데이터: Kaggle "Lending Club" (wordsforthewise/lending-club)
        파일명 accepted_2007_to_2018Q4.csv(.gz)
사용 열: issue_d, grade, loan_status (+ term, 선택)

Output:
[예제표] AUC 0.6816 / GINI 0.3633 / K-S 0.2728
데이터 파일: /kaggle/input/datasets/wordsforthewise/lending-club/accepted_2007_to_2018Q4.csv.gz
전체 행 수: 2260668
loan_status
Fully Paid                                             1076751
Current                                                 878317
Charged Off                                             268559
Late (31-120 days)                                       21467
In Grace Period                                           8436
Late (16-30 days)                                         4349
Does not meet the credit policy. Status:Fully Paid        1988
Does not meet the credit policy. Status:Charged Off        761
Default                                                     40
Name: count, dtype: int64 

종결 대출 수 (36개월 필터 적용 여부: True): 1020768
기준 2013: 100,422건 (부도율 12.3%) / 최근 2015: 283,026건 (부도율 14.9%)

[2013 등급표]
         bad      n   good
grade                    
G         4     15     11
F       163    608    445
E       753   3231   2478
D      2958  14505  11547
C      3777  24693  20916
B      3945  40313  36368
A       778  17057  16279 

[2015 등급표]
          bad      n   good
grade                     
G        113    245    132
F        577   1361    784
E       3101   9443   6342
D       8577  32711  24134
C      15051  77423  62372
B      10911  91725  80814
A       3802  70118  66316 

[기준] AUC 0.6377 | GINI 0.2755 | K-S 0.2164
       sklearn AUC 0.6377 | scipy K-S 0.2164
[최근] AUC 0.6675 | GINI 0.3351 | K-S 0.2616
       sklearn AUC 0.6675 | scipy K-S 0.2616

PSI 0.0569 (안정)
        기준 비중   최근 비중      변화
grade                        
A      0.1699  0.2477  0.0779
B      0.4014  0.3241 -0.0773
C      0.2459  0.2736  0.0277
D      0.1444  0.1156 -0.0289
E      0.0322  0.0334  0.0012
F      0.0061  0.0048 -0.0012
G      0.0001  0.0009  0.0007 

저장: grade_table_2013.csv, grade_table_2015.csv

[세 줄 의견 재료]
(1) 성능: 최근 AUC 0.668, 기준 0.638 대비 +0.030
(2) 안정성: PSI 0.057 (안정)
(3) 결론: 계속 사용 / 조건부 사용 / 재개발 검토 중 하나 + 다음 할 일
"""
import glob
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import roc_auc_score

# ---------------------------------------------------------------
# 0. 설정
# ---------------------------------------------------------------
BASE_YEAR = 2013        # 기준 연도
RECENT_YEAR = 2015      # 최근 연도
ONLY_36M = True         # True면 36개월 대출만 사용 (관찰 기간을 비슷하게 맞추기 위함)

# ---------------------------------------------------------------
# 1. 지표 함수 (엑셀 수식과 1:1 대응)
# ---------------------------------------------------------------
def grade_table(df):
    """등급별 건수표. 위험한 등급(G)부터 정렬."""
    tab = df.groupby('grade')['bad'].agg(bad='sum', n='count')
    tab['good'] = tab['n'] - tab['bad']
    return tab.sort_index(ascending=False)


def perf(tab):
    """AUC, GINI, K-S 반환."""
    # 엑셀 H, I열: 누적 Bad / 누적 Good
    cb = (tab['bad'] / tab['bad'].sum()).cumsum().to_numpy()
    cg = (tab['good'] / tab['good'].sum()).cumsum().to_numpy()

    # 엑셀 J열의 MAX
    ks = (cb - cg).max()

    # 엑셀의 (시작점) 행: 맨 앞에 0 추가
    x = np.r_[0, cg]
    y = np.r_[0, cb]

    # 엑셀 K열의 SUM: 가로 폭 x 평균 높이
    auc = ((x[1:] - x[:-1]) * (y[1:] + y[:-1]) / 2).sum()

    return auc, 2 * auc - 1, ks


def psi(base_n, recent_n):
    """PSI. 두 Series의 인덱스(등급)가 같아야 함."""
    a = base_n / base_n.sum()      # 기준 비중
    b = recent_n / recent_n.sum()  # 최근 비중
    return ((b - a) * np.log(b / a)).sum()


def merge_empty_grades(base_n, recent_n):
    """건수가 0인 등급이 있으면 위험한 쪽 옆 등급과 합침 (예: G를 F에 합침)."""
    base_n, recent_n = base_n.copy(), recent_n.copy()
    grades = list(base_n.index)                   # G, F, E, ... 순서
    merged = []
    i = 0
    while i < len(grades):
        g = grades[i]
        if (base_n[g] == 0 or recent_n[g] == 0) and i + 1 < len(grades):
            nxt = grades[i + 1]
            base_n[nxt] += base_n[g]
            recent_n[nxt] += recent_n[g]
            merged.append(f'{g}->{nxt}')
            base_n, recent_n = base_n.drop(g), recent_n.drop(g)
            grades.pop(i)
        else:
            i += 1
    return base_n, recent_n, merged


def check_with_library(df):
    """직접 구현값 vs roc_auc_score, ks_2samp."""
    # 등급을 숫자로: A=0 ... G=6 (클수록 위험)
    risk = dict(zip('ABCDEFG', range(7)))
    score = df['grade'].map(risk)
    auc_lib = roc_auc_score(df['bad'], score)
    ks_lib = ks_2samp(score[df['bad'] == 1], score[df['bad'] == 0]).statistic
    return auc_lib, ks_lib


# ---------------------------------------------------------------
# 2. 함수 검증: 예제 표(1만 건)로 AUC 0.6816 / GINI 0.3633 / K-S 0.2728 나오는지
# ---------------------------------------------------------------
def self_test():
    ex = pd.DataFrame(
        {'bad':  [38, 115, 275, 430, 590, 360, 95],
         'good': [42, 155, 475, 1070, 2210, 2540, 1605]},
        index=list('GFEDCBA'))
    ex['n'] = ex['bad'] + ex['good']
    auc, gini, ks = perf(ex)
    print(f'[예제표] AUC {auc:.4f} / GINI {gini:.4f} / K-S {ks:.4f}')
    assert round(auc, 4) == 0.6816 and round(gini, 4) == 0.3633 and round(ks, 4) == 0.2728


# ---------------------------------------------------------------
# 3. 데이터 불러오기
# ---------------------------------------------------------------
def find_file():
    patterns = ['/kaggle/input/**/accepted_2007_to_2018Q4*',
                '/kaggle/input/**/accepted_2007_to_2018q4*',
                './**/accepted_2007_to_2018Q4*',
                './**/accepted_2007_to_2018q4*']
    for p in patterns:
        hits = glob.glob(p, recursive=True)
        hits = [h for h in hits if h.endswith(('.csv', '.gz'))]
        if hits:
            return hits[0]
    raise FileNotFoundError('accepted_2007_to_2018Q4.csv 를 찾지 못함. DATA_PATH를 직접 지정할 것.')


def load_data(path=None):
    path = path or find_file()
    print('데이터 파일:', path)
    cols = ['issue_d', 'grade', 'loan_status', 'term']
    df = pd.read_csv(path, usecols=cols, low_memory=False)
    df = df.dropna(subset=['issue_d', 'grade', 'loan_status'])   # 끝에 붙은 메타 행 제거
    df['year'] = pd.to_datetime(df['issue_d'], format='%b-%Y', errors='coerce').dt.year
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)
    return df


def make_bad(df):
    """결과가 확정된 대출만 남기고 bad 열 생성."""
    done = df['loan_status'].isin(['Fully Paid', 'Charged Off', 'Default'])
    df = df[done].copy()
    df['bad'] = (df['loan_status'] != 'Fully Paid').astype(int)
    return df


# ---------------------------------------------------------------
# 4. 실습 1 실행
# ---------------------------------------------------------------
def run(path=None):
    self_test()

    df = load_data(path)
    print('전체 행 수:', len(df))
    print(df['loan_status'].value_counts(), '\n')

    df = make_bad(df)
    if ONLY_36M:
        df = df[df['term'].str.strip() == '36 months']
    print('종결 대출 수 (36개월 필터 적용 여부: %s): %d' % (ONLY_36M, len(df)))

    base = df[df['year'] == BASE_YEAR]
    recent = df[df['year'] == RECENT_YEAR]
    print(f'기준 {BASE_YEAR}: {len(base):,}건 (부도율 {base["bad"].mean():.1%}) / '
          f'최근 {RECENT_YEAR}: {len(recent):,}건 (부도율 {recent["bad"].mean():.1%})\n')

    tab_b, tab_r = grade_table(base), grade_table(recent)
    print(f'[{BASE_YEAR} 등급표]\n', tab_b, '\n')
    print(f'[{RECENT_YEAR} 등급표]\n', tab_r, '\n')

    # 성능 지표
    res = {}
    for name, d, tab in [('기준', base, tab_b), ('최근', recent, tab_r)]:
        auc, gini, ks = perf(tab)
        auc_lib, ks_lib = check_with_library(d)
        res[name] = (auc, gini, ks)
        print(f'[{name}] AUC {auc:.4f} | GINI {gini:.4f} | K-S {ks:.4f}')
        print(f'       sklearn AUC {auc_lib:.4f} | scipy K-S {ks_lib:.4f}')
        assert abs(auc - auc_lib) < 1e-4 and abs(ks - ks_lib) < 1e-4, '직접 구현값과 라이브러리 값이 다름 (등급 순서 확인)'

    # 안정성 지표: 등급이 0건이면 합침
    bn, rn, merged = merge_empty_grades(tab_b['n'], tab_r['n'])
    if merged:
        print('\n건수 0인 등급 병합:', merged)
    p = psi(bn, rn)
    zone = '안정' if p < 0.1 else '주의' if p <= 0.25 else '큰 변화'
    print(f'\nPSI {p:.4f} ({zone})')

    # 등급별 구성 변화 (어느 쪽으로 움직였는지)
    shift = pd.DataFrame({'기준 비중': bn / bn.sum(), '최근 비중': rn / rn.sum()})
    shift['변화'] = shift['최근 비중'] - shift['기준 비중']
    print(shift.round(4).sort_index(), '\n')

    # 엑셀 성능 검증 시트(노란 칸)에 붙여 넣을 파일
    tab_b[['bad', 'good']].to_csv(f'grade_table_{BASE_YEAR}.csv')
    tab_r[['bad', 'good']].to_csv(f'grade_table_{RECENT_YEAR}.csv')
    print('저장: grade_table_%d.csv, grade_table_%d.csv' % (BASE_YEAR, RECENT_YEAR))

    # 세 줄 의견 재료
    d_auc = res['최근'][0] - res['기준'][0]
    print('\n[세 줄 의견 재료]')
    print(f'(1) 성능: 최근 AUC {res["최근"][0]:.3f}, 기준 {res["기준"][0]:.3f} 대비 {d_auc:+.3f}')
    print(f'(2) 안정성: PSI {p:.3f} ({zone})')
    print('(3) 결론: 계속 사용 / 조건부 사용 / 재개발 검토 중 하나 + 다음 할 일')


if __name__ == '__main__':
    run()

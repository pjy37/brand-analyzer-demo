import streamlit as st
import pandas as pd
import time
import random

st.set_page_config(
    page_title="브랜드 검색량 분석기 - AI 데모",
    page_icon="🔍",
    layout="wide",
)

# ============================================================
# 데모 데이터셋
# ============================================================
DEMO_DATASETS = {
    "여드름": {
        "totalKeywords": 1047,
        "excludedWords": '"추천", "크림", "세럼", "치료"',
        "data": [
            {"brand": "메디큐브", "pc": 12400, "mobile": 77000, "keywords": ["메디큐브 여드름", "메디큐브 여드름 패치", "메디큐브 여드름 크림", "메디큐브 좁쌀여드름", "메디큐브 여드름 앰플", "메디큐브 여드름 세럼", "메디큐브 여드름 토너"]},
            {"brand": "아누아", "pc": 8200, "mobile": 54600, "keywords": ["아누아 여드름", "아누아 여드름 토너", "아누아 클렌징 여드름", "아누아 여드름 앰플", "아누아 좁쌀여드름"]},
            {"brand": "코스알엑스", "pc": 5800, "mobile": 38200, "keywords": ["코스알엑스 여드름", "코스알엑스 여드름 패치", "코스알엑스 여드름 크림", "코스알엑스 bha 여드름"]},
            {"brand": "피캄", "pc": 4600, "mobile": 31400, "keywords": ["피캄 여드름", "피캄 여드름 앰플", "피캄 좁쌀여드름", "피캄 여드름 크림"]},
            {"brand": "라로슈포제", "pc": 3900, "mobile": 26100, "keywords": ["라로슈포제 여드름", "라로슈포제 여드름 크림", "라로슈포제 이파클라 여드름"]},
            {"brand": "이니스프리", "pc": 3200, "mobile": 21800, "keywords": ["이니스프리 여드름", "이니스프리 비자 여드름", "이니스프리 여드름 토너"]},
            {"brand": "넘버즈", "pc": 2800, "mobile": 18200, "keywords": ["넘버즈 여드름", "넘버즈 5번 세럼 여드름", "넘버즈 여드름 패드"]},
            {"brand": "토리든", "pc": 2400, "mobile": 15600, "keywords": ["토리든 여드름", "토리든 다이브인 여드름", "토리든 세럼 여드름"]},
            {"brand": "클레어스", "pc": 2100, "mobile": 13900, "keywords": ["클레어스 여드름", "클레어스 비타민 여드름", "클레어스 토너 여드름"]},
            {"brand": "에스트라", "pc": 1900, "mobile": 12100, "keywords": ["에스트라 여드름", "에스트라 아토배리어 여드름"]},
            {"brand": "달바", "pc": 1700, "mobile": 10300, "keywords": ["달바 여드름", "달바 세럼 여드름"]},
            {"brand": "마녀공장", "pc": 1500, "mobile": 9500, "keywords": ["마녀공장 여드름", "마녀공장 갈락토미 여드름"]},
            {"brand": "아크네스", "pc": 1300, "mobile": 8700, "keywords": ["아크네스 여드름", "아크네스 폼클렌저 여드름"]},
            {"brand": "VT", "pc": 1100, "mobile": 7900, "keywords": ["vt 시카 여드름", "vt 여드름 크림"]},
            {"brand": "비오레", "pc": 900, "mobile": 6100, "keywords": ["비오레 여드름", "비오레 클렌저 여드름"]},
            {"brand": "스킨1004", "pc": 800, "mobile": 5200, "keywords": ["스킨1004 여드름", "스킨1004 센텔라 여드름"]},
            {"brand": "센카", "pc": 600, "mobile": 4400, "keywords": ["센카 여드름", "센카 클렌징 여드름"]},
            {"brand": "듀오백", "pc": 400, "mobile": 2900, "keywords": ["듀오백 여드름 패치"]},
        ],
    },
    "탈모": {
        "totalKeywords": 892,
        "excludedWords": '"추천", "샴푸", "치료", "원인"',
        "data": [
            {"brand": "닥터포헤어", "pc": 9800, "mobile": 62000, "keywords": ["닥터포헤어 탈모", "닥터포헤어 탈모 샴푸", "닥터포헤어 탈모 앰플", "닥터포헤어 탈모 토닉", "닥터포헤어 두피 탈모"]},
            {"brand": "TS", "pc": 7400, "mobile": 48600, "keywords": ["ts 탈모 샴푸", "ts 탈모", "ts 탈모 샴푸 후기", "ts 탈모 앰플"]},
            {"brand": "려", "pc": 5600, "mobile": 36800, "keywords": ["려 탈모 샴푸", "려 자양윤모 탈모", "려 탈모", "려 탈모 샴푸 후기"]},
            {"brand": "카다손", "pc": 4200, "mobile": 28400, "keywords": ["카다손 탈모", "카다손 탈모 샴푸", "카다손 두피 탈모"]},
            {"brand": "아모스", "pc": 3500, "mobile": 23100, "keywords": ["아모스 탈모", "아모스 탈모 샴푸", "아모스 녹차실감 탈모"]},
            {"brand": "라보에이치", "pc": 2900, "mobile": 19600, "keywords": ["라보에이치 탈모", "라보에이치 탈모 샴푸", "라보에이치 두피 탈모"]},
            {"brand": "히든래빗", "pc": 2300, "mobile": 15200, "keywords": ["히든래빗 탈모", "히든래빗 탈모 샴푸"]},
            {"brand": "닥터시드", "pc": 1800, "mobile": 11900, "keywords": ["닥터시드 탈모", "닥터시드 탈모 샴푸"]},
            {"brand": "헤드스파7", "pc": 1400, "mobile": 9200, "keywords": ["헤드스파7 탈모", "헤드스파7 탈모 샴푸"]},
            {"brand": "팬틴", "pc": 1100, "mobile": 7400, "keywords": ["팬틴 탈모", "팬틴 탈모 샴푸"]},
            {"brand": "쿤달", "pc": 900, "mobile": 6100, "keywords": ["쿤달 탈모", "쿤달 탈모 샴푸"]},
            {"brand": "케라시스", "pc": 700, "mobile": 4800, "keywords": ["케라시스 탈모", "케라시스 탈모 샴푸"]},
        ],
    },
    "다이어트": {
        "totalKeywords": 1283,
        "excludedWords": '"추천", "방법", "식단", "운동"',
        "data": [
            {"brand": "녹차원", "pc": 8600, "mobile": 55200, "keywords": ["녹차원 다이어트", "녹차원 다이어트 차", "녹차원 다이어트 보이차", "녹차원 다이어트 티"]},
            {"brand": "뉴트리", "pc": 7100, "mobile": 46800, "keywords": ["뉴트리 다이어트", "뉴트리 다이어트 보조제", "뉴트리 다이어트 쉐이크", "뉴트리 다이어트 단백질"]},
            {"brand": "랩노쉬", "pc": 5400, "mobile": 35600, "keywords": ["랩노쉬 다이어트", "랩노쉬 다이어트 쉐이크", "랩노쉬 다이어트 도시락"]},
            {"brand": "허벌라이프", "pc": 4800, "mobile": 31200, "keywords": ["허벌라이프 다이어트", "허벌라이프 다이어트 쉐이크", "허벌라이프 다이어트 후기"]},
            {"brand": "올가니카", "pc": 3600, "mobile": 24100, "keywords": ["올가니카 다이어트", "올가니카 다이어트 유산균"]},
            {"brand": "그리너", "pc": 2900, "mobile": 19200, "keywords": ["그리너 다이어트", "그리너 다이어트 보조제"]},
            {"brand": "칼로바이", "pc": 2400, "mobile": 15800, "keywords": ["칼로바이 다이어트", "칼로바이 다이어트 보조제", "칼로바이 다이어트 후기"]},
            {"brand": "GNM", "pc": 2000, "mobile": 13100, "keywords": ["gnm 다이어트", "gnm 다이어트 유산균"]},
            {"brand": "뉴오리진", "pc": 1600, "mobile": 10500, "keywords": ["뉴오리진 다이어트", "뉴오리진 다이어트 보조제"]},
            {"brand": "종근당", "pc": 1300, "mobile": 8600, "keywords": ["종근당 다이어트", "종근당 다이어트 유산균"]},
            {"brand": "일동후디스", "pc": 1000, "mobile": 6700, "keywords": ["일동후디스 다이어트", "일동후디스 다이어트 쉐이크"]},
            {"brand": "네이처메이드", "pc": 800, "mobile": 5300, "keywords": ["네이처메이드 다이어트", "네이처메이드 다이어트 보조제"]},
            {"brand": "나우푸드", "pc": 600, "mobile": 4100, "keywords": ["나우푸드 다이어트", "나우푸드 다이어트 보조제"]},
        ],
    },
    "선크림": {
        "totalKeywords": 956,
        "excludedWords": '"추천", "발색", "사용법", "성분"',
        "data": [
            {"brand": "라로슈포제", "pc": 11200, "mobile": 71800, "keywords": ["라로슈포제 선크림", "라로슈포제 안뗄리오스 선크림", "라로슈포제 uv 선크림", "라로슈포제 선크림 추천"]},
            {"brand": "아누아", "pc": 7800, "mobile": 51200, "keywords": ["아누아 선크림", "아누아 버치 선크림", "아누아 선크림 추천"]},
            {"brand": "이니스프리", "pc": 6200, "mobile": 40800, "keywords": ["이니스프리 선크림", "이니스프리 데일리 선크림", "이니스프리 톤업 선크림"]},
            {"brand": "닥터지", "pc": 4900, "mobile": 32400, "keywords": ["닥터지 선크림", "닥터지 그린마일드 선크림", "닥터지 선크림 추천"]},
            {"brand": "비오레", "pc": 3800, "mobile": 25100, "keywords": ["비오레 선크림", "비오레 아쿠아리치 선크림", "비오레 선크림 추천"]},
            {"brand": "에스트라", "pc": 3100, "mobile": 20400, "keywords": ["에스트라 선크림", "에스트라 아토배리어 선크림"]},
            {"brand": "아이소이", "pc": 2500, "mobile": 16500, "keywords": ["아이소이 선크림", "아이소이 선크림 추천"]},
            {"brand": "라운드랩", "pc": 2100, "mobile": 13800, "keywords": ["라운드랩 선크림", "라운드랩 자작나무 선크림"]},
            {"brand": "셀퓨전씨", "pc": 1700, "mobile": 11200, "keywords": ["셀퓨전씨 선크림", "셀퓨전씨 톤업 선크림"]},
            {"brand": "미샤", "pc": 1400, "mobile": 9200, "keywords": ["미샤 선크림", "미샤 선크림 추천"]},
            {"brand": "스킨아쿠아", "pc": 1100, "mobile": 7300, "keywords": ["스킨아쿠아 선크림", "스킨아쿠아 톤업 선크림"]},
            {"brand": "듀이트리", "pc": 800, "mobile": 5400, "keywords": ["듀이트리 선크림", "듀이트리 시카 선크림"]},
        ],
    },
    "비타민": {
        "totalKeywords": 1124,
        "excludedWords": '"추천", "효능", "부작용", "복용법"',
        "data": [
            {"brand": "종근당", "pc": 10400, "mobile": 66800, "keywords": ["종근당 비타민", "종근당 비타민c", "종근당 비타민d", "종근당 멀티비타민", "종근당 비타민b"]},
            {"brand": "솔가", "pc": 7600, "mobile": 49800, "keywords": ["솔가 비타민", "솔가 비타민d", "솔가 비타민c", "솔가 멀티비타민"]},
            {"brand": "센트룸", "pc": 6100, "mobile": 40200, "keywords": ["센트룸 비타민", "센트룸 멀티비타민", "센트룸 비타민d"]},
            {"brand": "네이처메이드", "pc": 4700, "mobile": 31000, "keywords": ["네이처메이드 비타민", "네이처메이드 비타민c", "네이처메이드 비타민d"]},
            {"brand": "뉴트리코어", "pc": 3600, "mobile": 23800, "keywords": ["뉴트리코어 비타민", "뉴트리코어 비타민c"]},
            {"brand": "얼라이브", "pc": 2800, "mobile": 18400, "keywords": ["얼라이브 비타민", "얼라이브 멀티비타민"]},
            {"brand": "나우푸드", "pc": 2200, "mobile": 14500, "keywords": ["나우푸드 비타민", "나우푸드 비타민c", "나우푸드 비타민d"]},
            {"brand": "GNM", "pc": 1800, "mobile": 11800, "keywords": ["gnm 비타민", "gnm 비타민c"]},
            {"brand": "고려은단", "pc": 1400, "mobile": 9200, "keywords": ["고려은단 비타민", "고려은단 비타민c"]},
            {"brand": "대웅제약", "pc": 1100, "mobile": 7200, "keywords": ["대웅제약 비타민", "대웅제약 비타민c"]},
            {"brand": "일동제약", "pc": 800, "mobile": 5300, "keywords": ["일동제약 비타민", "일동제약 비타민c"]},
        ],
    },
}

AVAILABLE_KEYWORDS = list(DEMO_DATASETS.keys())


# ============================================================
# 스타일
# ============================================================
st.markdown("""
<style>
    .stApp { background-color: #0a0a0f; }
    .block-container { max-width: 1100px; }

    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #e4e4ef, #00e5a0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #8585a0;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .demo-badge {
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .demo-badge span {
        display: inline-block;
        padding: 4px 14px;
        background: rgba(0,229,160,0.08);
        border: 1px solid rgba(0,229,160,0.3);
        border-radius: 99px;
        font-size: 0.7rem;
        color: #00e5a0;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-family: monospace;
    }
    .demo-badge .sim {
        background: #ff4d6a;
        color: #fff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.6rem;
        font-weight: 700;
        margin-left: 6px;
    }

    .stat-card {
        background: #13131e;
        border: 1px solid #24243a;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    }
    .stat-value {
        font-family: 'Courier New', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #00e5a0;
    }
    .stat-label {
        font-size: 0.75rem;
        color: #8585a0;
        margin-top: 2px;
    }

    .brand-chip {
        display: inline-block;
        padding: 3px 10px;
        background: rgba(0,229,160,0.08);
        border: 1px solid rgba(0,229,160,0.3);
        border-radius: 4px;
        font-size: 0.8rem;
        color: #00e5a0;
        font-weight: 600;
        margin: 2px 3px;
    }

    .ai-bubble {
        background: rgba(124,77,255,0.08);
        border: 1px solid rgba(124,77,255,0.25);
        border-radius: 12px;
        padding: 18px 22px;
        margin: 16px 0;
        line-height: 1.8;
    }
    .ai-label {
        font-family: monospace;
        font-size: 0.7rem;
        color: #7c4dff;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    .step-done {
        background: rgba(0,229,160,0.06);
        border-left: 3px solid #00e5a0;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 0.85rem;
        color: #8585a0;
    }
    .step-done .check { color: #00e5a0; font-weight: 700; font-family: monospace; }

    .compare-box {
        background: rgba(124,77,255,0.04);
        border: 1px solid rgba(124,77,255,0.3);
        border-radius: 12px;
        padding: 20px;
    }

    div[data-testid="stHorizontalBlock"] > div { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 헤더
# ============================================================
st.markdown('<div class="demo-badge"><span>AI-Powered Demo <span class="sim">시뮬레이션</span></span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">브랜드 검색량 분석기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Claude API를 사용하면 이렇게 작동합니다. 키워드를 입력하거나 예시를 클릭하세요.</div>', unsafe_allow_html=True)


# ============================================================
# 입력 영역
# ============================================================
col_input, col_btn = st.columns([4, 1])
with col_input:
    keyword = st.text_input(
        "분석 키워드",
        placeholder="예: 여드름, 탈모, 다이어트...",
        label_visibility="collapsed",
    )
with col_btn:
    run_btn = st.button("▶ 분석 시작", use_container_width=True, type="primary")

# 예시 키워드 칩
st.markdown("**예시 키워드:**")
chip_cols = st.columns(len(AVAILABLE_KEYWORDS))
chip_clicked = None
for i, kw in enumerate(AVAILABLE_KEYWORDS):
    with chip_cols[i]:
        if st.button(kw, key=f"chip_{kw}", use_container_width=True):
            chip_clicked = kw

# 클릭된 칩 또는 입력값 결정
active_keyword = chip_clicked or (keyword.strip() if run_btn and keyword.strip() else None)

if not active_keyword:
    st.info("위에서 키워드를 입력하거나 예시 키워드를 클릭하세요.")
    st.stop()

# ============================================================
# 데이터셋 매칭
# ============================================================
match_key = None
for k in AVAILABLE_KEYWORDS:
    if k == active_keyword:
        match_key = k
        break
if not match_key:
    for k in AVAILABLE_KEYWORDS:
        if active_keyword in k or k in active_keyword:
            match_key = k
            break
if not match_key:
    match_key = random.choice(AVAILABLE_KEYWORDS)

dataset = DEMO_DATASETS[match_key]
data = dataset["data"]
total_kw = dataset["totalKeywords"]
excluded = dataset["excludedWords"]

# ============================================================
# 단계별 시뮬레이션
# ============================================================
st.divider()

steps_placeholder = st.empty()

with steps_placeholder.container():
    # Step 1
    with st.status(f'1️⃣ 네이버 검색광고 API에서 "{active_keyword}" 연관 키워드 조회', expanded=False) as s1:
        time.sleep(0.8)
        st.write("API 호출 완료")
        s1.update(label=f'1️⃣ 네이버 검색광고 API에서 "{active_keyword}" 연관 키워드 조회 — ✅ 완료', state="complete")

    # Step 2
    with st.status(f"2️⃣ 연관 키워드 {total_kw:,}개+ 수신", expanded=False) as s2:
        time.sleep(0.8)
        st.write(f"{total_kw:,}개 키워드 수신 완료")
        s2.update(label=f"2️⃣ 연관 키워드 {total_kw:,}개 수신 — ✅ 완료", state="complete")

    # Step 3 - AI
    with st.status("3️⃣ **Claude AI가 키워드 목록을 분석하여 브랜드명 자동 추출**", expanded=True) as s3:
        time.sleep(1.5)
        st.write(f"{len(data)}개 브랜드를 식별했습니다")
        s3.update(label=f"3️⃣ Claude AI 브랜드 추출 — ✅ {len(data)}개 브랜드", state="complete")

    # Step 4
    with st.status("4️⃣ 브랜드별 검색량 합산 및 순위 계산", expanded=False) as s4:
        time.sleep(0.5)
        st.write("계산 완료")
        s4.update(label="4️⃣ 브랜드별 검색량 합산 및 순위 계산 — ✅ 완료", state="complete")

# ============================================================
# AI 분석 결과 버블
# ============================================================
chips_html = " ".join(f'<span class="brand-chip">{d["brand"]}</span>' for d in data)
st.markdown(f"""
<div class="ai-bubble">
    <div class="ai-label">🤖 Claude AI 분석 결과</div>
    "{active_keyword}" 연관 키워드 {total_kw:,}개를 분석한 결과, <strong style="color:#7c4dff;">{len(data)}개 브랜드</strong>를 식별했습니다:<br><br>
    {chips_html}
    <br><br>
    <span style="font-size:0.75rem;color:#50506a;">✅ {excluded} 등 일반 단어는 자동 제외됨 | 분석 비용: ~$0.02 (약 25원)</span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 통계 카드
# ============================================================
total_brands = len(data)
total_match_kw = sum(len(d["keywords"]) for d in data)
top_total = data[0]["pc"] + data[0]["mobile"]
grand_total = sum(d["pc"] + d["mobile"] for d in data)

c1, c2, c3, c4 = st.columns(4)
for col, val, label in [
    (c1, total_brands, "브랜드 수"),
    (c2, total_match_kw, "매칭 키워드 수"),
    (c3, f"{top_total:,}", "1위 월간 검색량"),
    (c4, f"{grand_total:,}", "총 브랜드 검색량"),
]:
    with col:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{val}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# 바 차트
# ============================================================
st.subheader(f'브랜드별 검색량 TOP {total_brands} — "{active_keyword}"')

df = pd.DataFrame(data)
df["통합"] = df["pc"] + df["mobile"]
df = df.sort_values("통합", ascending=True)

import plotly.express as px

fig = px.bar(
    df,
    y="brand",
    x="통합",
    orientation="h",
    color_discrete_sequence=["#00e5a0"],
    labels={"brand": "브랜드", "통합": "통합 검색량"},
)
fig.update_layout(
    plot_bgcolor="#0a0a0f",
    paper_bgcolor="#0a0a0f",
    font=dict(color="#e4e4ef", size=12),
    xaxis=dict(gridcolor="#24243a", title="통합 검색량 (PC + 모바일)"),
    yaxis=dict(title=""),
    height=max(400, total_brands * 36),
    margin=dict(l=10, r=10, t=10, b=40),
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 상세 테이블
# ============================================================
st.subheader("상세 데이터")

table_df = pd.DataFrame([
    {
        "순위": i + 1,
        "브랜드": d["brand"],
        "매칭 키워드": ", ".join(d["keywords"][:3]) + (f" 외 {len(d['keywords'])-3}개" if len(d["keywords"]) > 3 else ""),
        "PC": d["pc"],
        "모바일": d["mobile"],
        "통합": d["pc"] + d["mobile"],
    }
    for i, d in enumerate(data)
])

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn(width="small"),
        "브랜드": st.column_config.TextColumn(width="medium"),
        "매칭 키워드": st.column_config.TextColumn(width="large"),
        "PC": st.column_config.NumberColumn(format="%d"),
        "모바일": st.column_config.NumberColumn(format="%d"),
        "통합": st.column_config.NumberColumn(format="%d"),
    },
)

# CSV 다운로드
csv_df = pd.DataFrame([
    {
        "순위": i + 1,
        "브랜드": d["brand"],
        "매칭 키워드": "; ".join(d["keywords"]),
        "PC 검색량": d["pc"],
        "모바일 검색량": d["mobile"],
        "통합 검색량": d["pc"] + d["mobile"],
    }
    for i, d in enumerate(data)
])

st.download_button(
    "⬇ CSV 다운로드",
    csv_df.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"brand_analysis_{active_keyword}.csv",
    mime="text/csv",
)

# ============================================================
# 비교 박스
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("무료 vs AI 유료 비교")

col_free, col_ai = st.columns(2)
with col_free:
    st.markdown("""
    **🆓 무료 (현재 버전)**
    1. 키워드 검색
    2. 후보 단어 목록 확인
    3. :red[**브랜드를 직접 체크 ← 수동**]
    4. 결과 확인

    ⏱️ 약 1~2분 소요
    """)
with col_ai:
    st.markdown("""
    **🤖 Claude API (유료 버전)**
    1. 키워드 검색
    2. :green[**AI가 브랜드 자동 추출 ← 원클릭**]
    3. 결과 즉시 표시

    ⏱️ 약 5초 소요 | 💰 ~25원/회
    """)

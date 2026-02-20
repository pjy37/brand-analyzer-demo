import streamlit as st
import pandas as pd
import requests
import hashlib
import hmac
import base64
import time
import json
import re

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="브랜드 검색량 분석기",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 커스텀 CSS ───
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 36px;
        font-weight: 900;
        background: linear-gradient(135deg, #e4e4ef, #00e5a0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-title {
        text-align: center;
        color: #8585a0;
        font-size: 14px;
        margin-bottom: 30px;
    }
    .brand-chip {
        display: inline-block;
        padding: 4px 12px;
        background: #00e5a015;
        border: 1px solid #00e5a050;
        border-radius: 6px;
        font-size: 12px;
        color: #00e5a0;
        font-weight: 600;
        margin: 2px 4px;
    }
    .metric-card {
        background: #13131e;
        border: 1px solid #24243a;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 900;
        color: #00e5a0;
    }
    .metric-label {
        font-size: 12px;
        color: #8585a0;
        margin-top: 4px;
    }
    .step-done {
        padding: 10px 16px;
        background: #00e5a015;
        border-left: 3px solid #00e5a0;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .step-active {
        padding: 10px 16px;
        background: #7c4dff15;
        border-left: 3px solid #7c4dff;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .ai-bubble {
        padding: 16px 20px;
        background: #7c4dff12;
        border: 1px solid #7c4dff40;
        border-radius: 10px;
        font-size: 13px;
        line-height: 1.8;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
# 네이버 검색광고 API 호출
# ═══════════════════════════════════════
def call_naver_api(api_key, secret_key, customer_id, keyword):
    timestamp = str(int(time.time() * 1000))
    method = "GET"
    uri = "/keywordstool"

    message = f"{timestamp}.{method}.{uri}"
    signature = base64.b64encode(
        hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")

    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": customer_id,
        "X-Signature": signature,
    }
    params = {"hintKeywords": keyword, "showDetail": "1"}

    resp = requests.get(
        "https://api.searchad.naver.com/keywordstool",
        headers=headers,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ═══════════════════════════════════════
# Claude API로 브랜드 자동 추출
# ═══════════════════════════════════════
def extract_brands_with_claude(claude_api_key, keyword, keyword_list):
    kw_text = "\n".join(keyword_list[:500])

    prompt = f"""아래는 "{keyword}" 키워드의 네이버 연관 검색어 목록입니다.
이 목록에서 **브랜드명(상표명, 회사명, 제품라인명)**만 추출해주세요.

규칙:
1. 브랜드명/상표명/회사명만 추출하세요
2. 일반 명사(추천, 가격, 크림, 세럼, 후기, 비교, 치료 등)는 절대 포함하지 마세요
3. 제품 카테고리(앰플, 토너, 패치, 클렌저 등)는 포함하지 마세요
4. 유통 채널(올리브영, 쿠팡, 네이버 등)은 포함하지 마세요
5. 성분명(레티놀, 나이아신아마이드, 살리실산 등)은 포함하지 마세요
6. 동일 브랜드의 다른 표기는 하나로 통일하세요 (예: cosrx = 코스알엑스)

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요:
[{{"brand": "브랜드명", "keywords": ["매칭된 키워드1", "매칭된 키워드2"]}}]

연관 검색어 목록:
{kw_text}"""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()

    result_text = resp.json()["content"][0]["text"]
    cleaned = re.sub(r"```json\s*|```\s*", "", result_text).strip()
    brands = json.loads(cleaned)
    return brands


# ═══════════════════════════════════════
# 검색량 파싱
# ═══════════════════════════════════════
def parse_volume(val):
    if not val or val == "< 10":
        return 5
    n = int(re.sub(r"[^0-9]", "", str(val)) or "0")
    return n


# ═══════════════════════════════════════
# 사이드바 설정
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ API 설정")

    st.markdown("**네이버 검색광고 API**")
    naver_api_key = st.text_input("API 키 (License)", type="password", key="nk")
    naver_secret = st.text_input("Secret 키", type="password", key="ns")
    naver_customer = st.text_input("고객 ID", key="nc")

    st.divider()

    st.markdown("**Anthropic Claude API**")
    claude_key = st.text_input("Claude API 키", type="password", key="ck", placeholder="sk-ant-...")

    st.divider()

    st.markdown("**📊 검색량 기준**")
    vol_type = st.radio(
        "표시할 검색량",
        ["통합 (PC+모바일)", "PC만", "모바일만"],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("💰 Claude API 비용: ~25원/회")
    st.caption("v3.0 | [자동화]키워드_경쟁사추출")


# ═══════════════════════════════════════
# 메인 영역
# ═══════════════════════════════════════
st.markdown('<p class="main-title">🔍 브랜드 검색량 분석기</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">키워드를 입력하면 AI가 경쟁 브랜드를 자동 추출하고 검색량 순위를 보여드립니다</p>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns([4, 1])
with col1:
    keyword = st.text_input(
        "분석할 키워드",
        placeholder="예: 여드름, 에어컨, 노트북, 운동화",
        label_visibility="collapsed",
    )
with col2:
    search_clicked = st.button("🔍 분석 시작", use_container_width=True, type="primary")

st.divider()

# ═══════════════════════════════════════
# 분석 실행
# ═══════════════════════════════════════
if search_clicked and keyword:
    if not naver_api_key or not naver_secret or not naver_customer:
        st.error("❌ 사이드바에서 네이버 검색광고 API 키를 입력해주세요.")
        st.stop()
    if not claude_key:
        st.error("❌ 사이드바에서 Claude API 키를 입력해주세요.")
        st.stop()

    kw = keyword.strip()

    # Step 1: 네이버 API
    s1 = st.empty()
    s1.markdown('<div class="step-active">1️⃣ 네이버 검색광고 API에서 연관 키워드 조회 중... ⏳</div>', unsafe_allow_html=True)

    try:
        naver_data = call_naver_api(naver_api_key, naver_secret, naver_customer, kw)
        kw_list = naver_data.get("keywordList", [])
        if not kw_list:
            s1.error("❌ 연관 키워드가 없습니다.")
            st.stop()
        s1.markdown(f'<div class="step-done">1️⃣ 네이버 API 조회 완료 ✅ <b>{len(kw_list)}개 연관 키워드</b></div>', unsafe_allow_html=True)
    except Exception as e:
        s1.error(f"❌ 네이버 API 오류: {e}")
        st.stop()

    # Step 2: Claude AI
    s2 = st.empty()
    s2.markdown('<div class="step-active">2️⃣ 🤖 Claude AI가 브랜드를 추출하는 중... ⏳</div>', unsafe_allow_html=True)

    try:
        kw_names = [item.get("relKeyword", "") for item in kw_list if item.get("relKeyword")]
        brands_raw = extract_brands_with_claude(claude_key, kw, kw_names)
        s2.markdown(f'<div class="step-done">2️⃣ 🤖 Claude AI 완료 ✅ <b>{len(brands_raw)}개 브랜드 추출</b></div>', unsafe_allow_html=True)
    except Exception as e:
        s2.error(f"❌ Claude API 오류: {e}")
        st.stop()

    # Step 3: 검색량 합산
    s3 = st.empty()
    s3.markdown('<div class="step-active">3️⃣ 브랜드별 검색량 합산 중... ⏳</div>', unsafe_allow_html=True)

    brand_results = []
    for brand_info in brands_raw:
        brand_name = brand_info.get("brand", "")
        if not brand_name:
            continue
        bl = brand_name.lower()
        pc_total, mb_total, matched_kws = 0, 0, []

        for item in kw_list:
            rel = (item.get("relKeyword") or "").lower()
            if bl in rel:
                pc_total += parse_volume(item.get("monthlyPcQcCnt"))
                mb_total += parse_volume(item.get("monthlyMobileQcCnt"))
                matched_kws.append(item.get("relKeyword", ""))

        if matched_kws:
            brand_results.append({
                "brand": brand_name, "pc": pc_total, "mobile": mb_total,
                "total": pc_total + mb_total, "keywords": matched_kws,
            })

    brand_results.sort(key=lambda x: x["total"], reverse=True)
    brand_results = brand_results[:20]
    s3.markdown('<div class="step-done">3️⃣ 순위 계산 완료 ✅</div>', unsafe_allow_html=True)

    # AI 결과 버블
    brand_chips = " ".join([f'<span class="brand-chip">{b["brand"]}</span>' for b in brand_results])
    st.markdown(f"""
    <div class="ai-bubble">
        <div style="font-size:11px;color:#7c4dff;letter-spacing:1px;margin-bottom:8px;">🤖 CLAUDE AI 분석 결과</div>
        "{kw}" 연관 키워드 {len(kw_list)}개를 분석 → <b>{len(brand_results)}개 브랜드</b> 식별<br><br>
        {brand_chips}
    </div>
    """, unsafe_allow_html=True)

    if not brand_results:
        st.warning("⚠️ 추출된 브랜드가 없습니다.")
        st.stop()

    st.divider()

    # 데이터 준비
    df = pd.DataFrame(brand_results)
    df["키워드수"] = df["keywords"].apply(len)
    df["주요키워드"] = df["keywords"].apply(lambda x: ", ".join(x[:3]) + (f" 외 {len(x)-3}개" if len(x) > 3 else ""))
    df = df.sort_values("total", ascending=False).reset_index(drop=True)
    df.index = df.index + 1

    vol_col = "pc" if "PC만" in vol_type else ("mobile" if "모바일만" in vol_type else "total")
    vol_label = "PC 검색량" if "PC만" in vol_type else ("모바일 검색량" if "모바일만" in vol_type else "통합 검색량")

    # 주요 지표
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(brand_results)}</div><div class="metric-label">브랜드 수</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{df["키워드수"].sum()}</div><div class="metric-label">매칭 키워드</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{df[vol_col].iloc[0]:,}</div><div class="metric-label">1위 {vol_label}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{df[vol_col].sum():,}</div><div class="metric-label">총 검색량</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 차트
    st.markdown(f"### 📊 브랜드별 {vol_label} TOP {len(brand_results)}")
    chart_df = df[["brand", vol_col]].copy()
    chart_df.columns = ["브랜드", vol_label]
    chart_df = chart_df.set_index("브랜드")
    st.bar_chart(chart_df, color="#00e5a0", horizontal=True, height=max(400, len(brand_results) * 35))

    # 테이블
    st.markdown("### 📋 상세 데이터")
    csv_df = df[["brand", "주요키워드", "pc", "mobile", "total"]].copy()
    csv_df.columns = ["브랜드", "매칭키워드", "PC검색량", "모바일검색량", "통합검색량"]
    csv_data = csv_df.to_csv(index_label="순위", encoding="utf-8-sig")

    dl1, dl2, _ = st.columns([1, 1, 4])
    with dl1:
        st.download_button("⬇️ CSV", csv_data, f"브랜드_{kw}.csv", "text/csv", use_container_width=True)
    with dl2:
        st.download_button("📋 TSV", csv_df.to_csv(index_label="순위", sep="\t"), f"브랜드_{kw}.tsv", "text/plain", use_container_width=True)

    display_df = df[["brand", "주요키워드", "pc", "mobile", "total"]].copy()
    display_df.columns = ["브랜드", "매칭 키워드", "PC 검색량", "모바일 검색량", "통합 검색량"]
    st.dataframe(display_df, use_container_width=True, hide_index=False)

else:
    st.info("👆 키워드를 입력하고 **분석 시작**을 클릭하세요! (사이드바에서 API 키 설정 필요)")
    st.markdown("""
    ### 🎯 이 도구는 이런 분석을 합니다
    > **"여드름"**을 검색하면 → 네이버 연관 키워드에서 "**메디큐브** 여드름 크림", "**아누아** 여드름 토너" 등을 찾아
    > **브랜드별 검색량 순위**를 자동으로 매겨줍니다.
    
    ### 🔧 시작하려면
    1. **사이드바**(왼쪽 ⚙️)에서 네이버 API 키 + Claude API 키 입력
    2. 검색창에 키워드 입력
    3. **분석 시작** 클릭!
    """)

import streamlit as st
import pandas as pd
import requests
import hashlib
import hmac
import base64
import time
import json
import re
from collections import Counter

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
        text-align: center; font-size: 36px; font-weight: 900;
        background: linear-gradient(135deg, #e4e4ef, #00e5a0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0;
    }
    .sub-title { text-align: center; color: #8585a0; font-size: 14px; margin-bottom: 30px; }
    .brand-chip {
        display: inline-block; padding: 4px 12px; background: #00e5a015;
        border: 1px solid #00e5a050; border-radius: 6px; font-size: 12px;
        color: #00e5a0; font-weight: 600; margin: 2px 4px;
    }
    .sub-chip {
        display: inline-block; padding: 3px 10px; background: #7c4dff12;
        border: 1px solid #7c4dff40; border-radius: 6px; font-size: 11px;
        color: #b8a0ff; margin: 2px 4px;
    }
    .metric-card {
        background: #13131e; border: 1px solid #24243a; border-radius: 12px;
        padding: 20px; text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 900; color: #00e5a0; }
    .metric-label { font-size: 12px; color: #8585a0; margin-top: 4px; }
    .step-done {
        padding: 10px 16px; background: #00e5a015; border-left: 3px solid #00e5a0;
        border-radius: 0 8px 8px 0; margin-bottom: 8px; font-size: 13px;
    }
    .step-active {
        padding: 10px 16px; background: #7c4dff15; border-left: 3px solid #7c4dff;
        border-radius: 0 8px 8px 0; margin-bottom: 8px; font-size: 13px;
    }
    .ai-bubble {
        padding: 16px 20px; background: #7c4dff12; border: 1px solid #7c4dff40;
        border-radius: 10px; font-size: 13px; line-height: 1.8; margin: 16px 0;
    }
    .compare-header {
        font-size: 11px; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; padding: 8px 0 4px; margin-bottom: 8px;
    }
    .shopping-chip {
        display: inline-block; padding: 4px 12px; background: #ff6b3515;
        border: 1px solid #ff6b3550; border-radius: 6px; font-size: 12px;
        color: #ff6b35; font-weight: 600; margin: 2px 4px;
    }
    .both-chip {
        display: inline-block; padding: 4px 12px; background: #ffd70015;
        border: 1px solid #ffd70050; border-radius: 6px; font-size: 12px;
        color: #ffd700; font-weight: 600; margin: 2px 4px;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
# 네이버 검색광고 API 호출
# ═══════════════════════════════════════
def call_naver_ad_api(api_key, secret_key, customer_id, keyword):
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
        headers=headers, params=params, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ═══════════════════════════════════════
# 네이버 쇼핑 검색 API 호출
# ═══════════════════════════════════════
def call_naver_shopping_api(client_id, client_secret, keyword, display=100):
    """네이버 쇼핑 검색 API로 상품 목록 조회 → 브랜드 추출"""
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    
    all_items = []
    # 최대 300개까지 수집 (100개씩 3번)
    for start in [1, 101, 201]:
        try:
            params = {
                "query": keyword,
                "display": 100,
                "start": start,
                "sort": "sim",  # 유사도순 (네이버 기본 정렬)
            }
            resp = requests.get(
                "https://openapi.naver.com/v1/search/shop.json",
                headers=headers, params=params, timeout=15,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            all_items.extend(items)
            if len(items) < 100:
                break
            time.sleep(0.2)
        except Exception:
            break
    
    return all_items


def extract_shopping_brands(items):
    """쇼핑 검색 결과에서 브랜드별 상품 수 집계"""
    brand_counter = Counter()
    brand_products = {}
    
    for item in items:
        brand = (item.get("brand") or "").strip()
        if not brand:
            continue
        
        brand_counter[brand] += 1
        
        if brand not in brand_products:
            brand_products[brand] = []
        
        title = re.sub(r"<.*?>", "", item.get("title", ""))  # HTML 태그 제거
        brand_products[brand].append({
            "title": title,
            "price": item.get("lprice", "0"),
            "mall": item.get("mallName", ""),
        })
    
    results = []
    rank = 0
    for brand, count in brand_counter.most_common(30):
        rank += 1
        products = brand_products.get(brand, [])
        sample_titles = [p["title"] for p in products[:3]]
        results.append({
            "brand": brand,
            "product_count": count,
            "rank": rank,
            "sample_products": sample_titles,
        })
    
    return results


# ═══════════════════════════════════════
# Claude API 공통 호출 (재시도 포함)
# ═══════════════════════════════════════
def call_claude(claude_api_key, prompt, max_tokens=4096):
    resp = None
    last_error = None

    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=90,
            )
            resp.raise_for_status()
            break
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
            continue

    if resp is None:
        raise last_error

    result_text = resp.json()["content"][0]["text"]
    cleaned = re.sub(r"```json\s*|```\s*", "", result_text).strip()
    return json.loads(cleaned)


# ═══════════════════════════════════════
# 1차 Claude: 파생 키워드 추천
# ═══════════════════════════════════════
def get_sub_keywords_from_claude(claude_api_key, main_keyword, keyword_list):
    kw_sample = "\n".join(keyword_list[:300])

    prompt = f"""당신은 한국 이커머스/검색 마케팅 전문가입니다.

사용자가 "{main_keyword}" 키워드로 브랜드 검색량을 분석하려 합니다.
아래는 네이버에서 "{main_keyword}"를 검색했을 때 나온 연관 키워드 일부입니다.

현재 문제: 이 키워드만으로는 브랜드가 충분히 발견되지 않습니다.

당신의 임무: 더 많은 브랜드를 발견하기 위해 **추가로 검색해야 할 파생 키워드**를 추천해주세요.

## 추천 기준
- "{main_keyword}" + 제품 카테고리 조합 (예: {main_keyword} 팩, {main_keyword} 클렌저, {main_keyword} 세럼 등)
- "{main_keyword}" + 사용 방법/목적 조합 (예: {main_keyword} 제거, {main_keyword} 관리 등)
- 소비자가 실제로 브랜드를 비교하며 검색할 만한 키워드
- 8~12개 정도 추천

## 제외
- 너무 일반적인 키워드 (예: "{main_keyword} 뜻", "{main_keyword} 원인")

반드시 아래 JSON 형식으로만 응답하세요:
["{main_keyword} 팩", "{main_keyword} 클렌저", ...]

현재 연관 키워드 일부:
{kw_sample}"""

    return call_claude(claude_api_key, prompt, max_tokens=1024)


# ═══════════════════════════════════════
# 2차 Claude: 브랜드 추출
# ═══════════════════════════════════════
def extract_brands_with_claude(claude_api_key, keyword, keyword_list):
    kw_text = "\n".join(keyword_list[:1000])

    prompt = f"""당신은 한국 소비재 시장의 브랜드 전문가입니다.

아래는 네이버에서 "{keyword}" 관련 키워드를 폭넓게 검색하여 수집한 연관 검색어 목록입니다.

당신의 임무: 이 키워드 목록을 분석하여 **소비자가 실제로 검색하는 브랜드/상표/회사명**을 모두 찾아내세요.

## 추출 대상 (포함해야 할 것)
- 화장품/스킨케어 브랜드 (예: 코스알엑스, 이니스프리, 토리든, 넘버즈, 메디큐브, 아누아, 마녀공장, 바닐라코, 한스킨, CNP, 달바, 라곰 등)
- 제약/헬스케어 브랜드 (예: 에스트라, 아크네스, 뉴트로지나 등)
- 가전/전자, 패션, 식품 브랜드
- 기타 모든 상표명, 회사명, 제품라인명, 서브 브랜드명
- 영문/한영 혼용 브랜드 포함

## 제외 대상 (절대 포함하지 말 것)
- 일반 명사: 추천, 가격, 후기, 비교, 순위, 효과, 원인, 치료, 제거, 방법
- 제품 카테고리: 크림, 세럼, 앰플, 토너, 팩, 패치, 클렌저, 오일, 패드, 마스크
- 유통 채널: 올리브영, 쿠팡, 네이버, 다이소, 약국
- 성분명: 레티놀, 나이아신아마이드, 살리실산, BHA, AHA, 비타민C, 티트리
- 피부 상태/증상, 신체 부위

## 중요 규칙
- 동일 브랜드의 다른 표기는 하나로 통일 (예: cosrx → 코스알엑스)
- 누락보다 과포함이 낫습니다
- 붙어있는 브랜드명도 찾기 (예: "이니스프리블랙헤드" → 이니스프리)

반드시 아래 JSON 형식으로만 응답하세요:
[{{"brand": "브랜드명", "keywords": ["매칭 키워드1", "매칭 키워드2"]}}]

연관 검색어 목록 ({len(keyword_list)}개):
{kw_text}"""

    return call_claude(claude_api_key, prompt)


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
    st.markdown("### ⚙️ 설정")

    # Streamlit Secrets에서 기본값 로드
    default_api_key = st.secrets.get("API_KEY", "")
    default_secret = st.secrets.get("SECRET_KEY", "")
    default_customer = st.secrets.get("CUSTOMER_ID", "")
    default_claude = st.secrets.get("CLAUDE_API_KEY", "")
    default_naver_cid = st.secrets.get("NAVER_CLIENT_ID", "")
    default_naver_csec = st.secrets.get("NAVER_CLIENT_SECRET", "")

    st.markdown("**API 연결 상태**")
    if default_api_key and default_secret and default_customer:
        st.success("✅ 네이버 검색광고 API 연결됨")
        naver_api_key = default_api_key
        naver_secret = default_secret
        naver_customer = default_customer
    else:
        st.markdown("**네이버 검색광고 API**")
        naver_api_key = st.text_input("API 키 (License)", type="password", key="nk")
        naver_secret = st.text_input("Secret 키", type="password", key="ns")
        naver_customer = st.text_input("고객 ID", key="nc")

    if default_claude:
        st.success("✅ Claude API 연결됨")
        claude_key = default_claude
    else:
        st.divider()
        st.markdown("**Anthropic Claude API**")
        claude_key = st.text_input("Claude API 키", type="password", key="ck", placeholder="sk-ant-...")

    if default_naver_cid and default_naver_csec:
        st.success("✅ 네이버 쇼핑 API 연결됨")
        naver_cid = default_naver_cid
        naver_csec = default_naver_csec
    else:
        st.divider()
        st.markdown("**네이버 쇼핑 검색 API**")
        naver_cid = st.text_input("Client ID", key="ncid")
        naver_csec = st.text_input("Client Secret", type="password", key="ncsec")

    st.divider()

    st.markdown("**📊 검색량 기준**")
    vol_type = st.radio(
        "표시할 검색량",
        ["통합 (PC+모바일)", "PC만", "모바일만"],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("💰 Claude API 비용: ~$0.02~0.05/회")
    st.caption("v6.0 | 검색량 + 쇼핑 노출 비교")


# ═══════════════════════════════════════
# 메인 영역
# ═══════════════════════════════════════
st.markdown('<p class="main-title">🔍 브랜드 검색량 분석기</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">키워드를 입력하면 AI가 경쟁 브랜드를 자동 추출하고, 네이버 쇼핑 노출과 비교합니다</p>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns([4, 1])
with col1:
    keyword = st.text_input(
        "분석할 키워드",
        placeholder="예: 여드름, 에어컨, 노트북, 블랙헤드",
        label_visibility="collapsed",
    )
with col2:
    search_clicked = st.button("🔍 분석 시작", use_container_width=True, type="primary")

st.divider()

# ═══════════════════════════════════════
# 분석 실행 (5단계)
# ═══════════════════════════════════════
if search_clicked and keyword:
    if not naver_api_key or not naver_secret or not naver_customer:
        st.error("❌ 네이버 검색광고 API 키를 설정해주세요.")
        st.stop()
    if not claude_key:
        st.error("❌ Claude API 키를 설정해주세요.")
        st.stop()

    kw = keyword.strip()
    all_keywords = {}

    # ── Step 1: 1차 네이버 검색광고 API ──
    s1 = st.empty()
    s1.markdown(f'<div class="step-active">1️⃣ 네이버 검색광고 API에서 "{kw}" 연관 키워드 조회 중... ⏳</div>', unsafe_allow_html=True)

    try:
        data = call_naver_ad_api(naver_api_key, naver_secret, naver_customer, kw)
        for item in data.get("keywordList", []):
            rel = item.get("relKeyword", "")
            if rel:
                all_keywords[rel] = item
        if not all_keywords:
            s1.error("❌ 연관 키워드가 없습니다.")
            st.stop()
        s1.markdown(f'<div class="step-done">1️⃣ 1차 검색 완료 ✅ <b>{len(all_keywords)}개 연관 키워드</b></div>', unsafe_allow_html=True)
    except Exception as e:
        s1.error(f"❌ 네이버 검색광고 API 오류: {e}")
        st.stop()

    # ── Step 2: Claude 파생 키워드 추천 + 추가 검색 ──
    s2 = st.empty()
    s2.markdown('<div class="step-active">2️⃣ 🤖 Claude AI가 파생 키워드를 분석 중... ⏳</div>', unsafe_allow_html=True)

    sub_searched = []
    try:
        kw_names_initial = list(all_keywords.keys())
        sub_keywords = get_sub_keywords_from_claude(claude_key, kw, kw_names_initial)

        for i, sub_kw in enumerate(sub_keywords):
            if not isinstance(sub_kw, str):
                continue
            sub_kw = sub_kw.strip()
            if not sub_kw:
                continue
            s2.markdown(f'<div class="step-active">2️⃣ "{sub_kw}" 추가 검색 중... ({i+1}/{len(sub_keywords)}) ⏳</div>', unsafe_allow_html=True)
            try:
                time.sleep(0.3)
                data = call_naver_ad_api(naver_api_key, naver_secret, naver_customer, sub_kw)
                new_count = 0
                for item in data.get("keywordList", []):
                    rel = item.get("relKeyword", "")
                    if rel and rel not in all_keywords:
                        all_keywords[rel] = item
                        new_count += 1
                if new_count > 0:
                    sub_searched.append(f"{sub_kw} (+{new_count})")
            except Exception:
                continue

        s2.markdown(
            f'<div class="step-done">2️⃣ 파생 키워드 {len(sub_keywords)}개 추가 검색 완료 ✅ <b>총 {len(all_keywords)}개 키워드</b></div>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        s2.markdown(f'<div class="step-done">2️⃣ 파생 검색 생략 — 1차 결과로 진행 ✅</div>', unsafe_allow_html=True)

    # ── Step 3: Claude 브랜드 추출 ──
    s3 = st.empty()
    kw_list = list(all_keywords.values())
    kw_names = list(all_keywords.keys())
    s3.markdown(f'<div class="step-active">3️⃣ 🤖 Claude AI가 {len(kw_names)}개 키워드에서 브랜드 추출 중... ⏳</div>', unsafe_allow_html=True)

    try:
        brands_raw = extract_brands_with_claude(claude_key, kw, kw_names)
        s3.markdown(f'<div class="step-done">3️⃣ 브랜드 추출 완료 ✅ <b>{len(brands_raw)}개 브랜드</b></div>', unsafe_allow_html=True)
    except Exception as e:
        s3.error(f"❌ Claude API 오류: {e}")
        st.stop()

    # ── Step 4: 검색량 합산 ──
    s4 = st.empty()
    s4.markdown('<div class="step-active">4️⃣ 브랜드별 검색량 합산 중... ⏳</div>', unsafe_allow_html=True)

    brand_results = []
    for brand_info in brands_raw:
        brand_name = brand_info.get("brand", "")
        if not brand_name:
            continue
        bl = brand_name.lower()
        pc_total, mb_total, matched_kws = 0, 0, []
        matched_kw_details = []  # 키워드별 상세 검색량

        for item in kw_list:
            rel = (item.get("relKeyword") or "").lower()
            if bl in rel:
                pc = parse_volume(item.get("monthlyPcQcCnt"))
                mb = parse_volume(item.get("monthlyMobileQcCnt"))
                pc_total += pc
                mb_total += mb
                matched_kws.append(item.get("relKeyword", ""))
                matched_kw_details.append({
                    "keyword": item.get("relKeyword", ""),
                    "pc": pc,
                    "mobile": mb,
                    "total": pc + mb,
                })

        if matched_kws:
            # 키워드 상세를 검색량 내림차순 정렬
            matched_kw_details.sort(key=lambda x: x["total"], reverse=True)
            brand_results.append({
                "brand": brand_name, "pc": pc_total, "mobile": mb_total,
                "total": pc_total + mb_total, "keywords": matched_kws,
                "keyword_details": matched_kw_details,
            })

    brand_results.sort(key=lambda x: x["total"], reverse=True)
    brand_results = brand_results[:20]
    s4.markdown('<div class="step-done">4️⃣ 검색량 순위 완료 ✅</div>', unsafe_allow_html=True)

    # ── Step 5: 네이버 쇼핑 검색 ──
    s5 = st.empty()
    shopping_brands = []

    if naver_cid and naver_csec:
        s5.markdown(f'<div class="step-active">5️⃣ 네이버 쇼핑에서 "{kw}" 상품 검색 중... ⏳</div>', unsafe_allow_html=True)
        try:
            shop_items = call_naver_shopping_api(naver_cid, naver_csec, kw)
            shopping_brands = extract_shopping_brands(shop_items)
            s5.markdown(f'<div class="step-done">5️⃣ 네이버 쇼핑 검색 완료 ✅ <b>{len(shop_items)}개 상품, {len(shopping_brands)}개 브랜드</b></div>', unsafe_allow_html=True)
        except Exception as e:
            s5.markdown(f'<div class="step-done">5️⃣ 네이버 쇼핑 검색 실패 ({e}) — 검색량 데이터만 표시합니다 ✅</div>', unsafe_allow_html=True)
    else:
        s5.markdown('<div class="step-done">5️⃣ 네이버 쇼핑 API 미설정 — 검색량 데이터만 표시합니다 ✅</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════
    # 결과 표시
    # ═══════════════════════════════════════

    if not brand_results:
        st.warning("⚠️ 추출된 브랜드가 없습니다.")
        st.stop()

    st.divider()

    # ── 데이터 준비 ──
    df = pd.DataFrame(brand_results)
    df["키워드수"] = df["keywords"].apply(len)
    df["주요키워드"] = df["keywords"].apply(lambda x: ", ".join(x[:3]) + (f" 외 {len(x)-3}개" if len(x) > 3 else ""))
    df = df.sort_values("total", ascending=False).reset_index(drop=True)
    df.index = df.index + 1

    vol_col = "pc" if "PC만" in vol_type else ("mobile" if "모바일만" in vol_type else "total")
    vol_label = "PC 검색량" if "PC만" in vol_type else ("모바일 검색량" if "모바일만" in vol_type else "통합 검색량")

    # ══════════════════════════
    # 🆚 비교 섹션 (핵심!)
    # ══════════════════════════
    if shopping_brands:
        st.markdown("## 🆚 검색량 vs 쇼핑 노출 비교")

        search_set = set(b["brand"].lower() for b in brand_results)
        shop_set = set(b["brand"].lower() for b in shopping_brands)

        both = search_set & shop_set
        only_search = search_set - shop_set
        only_shop = shop_set - search_set

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ffd700;">{len(both)}</div><div class="metric-label">🏆 양쪽 모두</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#00e5a0;">{len(only_search)}</div><div class="metric-label">🔍 검색량만</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ff6b35;">{len(only_shop)}</div><div class="metric-label">🛒 쇼핑만</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 양쪽 모두
        if both:
            both_chips = " ".join([f'<span class="both-chip">{b}</span>' for b in sorted(both)])
            st.markdown(f'<div class="compare-header" style="color:#ffd700;">🏆 양쪽 모두 등장 (검색량 높고 + 쇼핑에서도 노출)</div>{both_chips}', unsafe_allow_html=True)

        # 검색량에만 있는 브랜드
        if only_search:
            search_chips = " ".join([f'<span class="brand-chip">{b}</span>' for b in sorted(only_search)])
            st.markdown(f'<div class="compare-header" style="color:#00e5a0;">🔍 검색량에만 등장 (사람들이 검색하지만 쇼핑 상위에는 없음)</div>{search_chips}', unsafe_allow_html=True)

        # 쇼핑에만 있는 브랜드
        if only_shop:
            shop_chips = " ".join([f'<span class="shopping-chip">{b}</span>' for b in sorted(only_shop)])
            st.markdown(f'<div class="compare-header" style="color:#ff6b35;">🛒 쇼핑에만 등장 (검색량 데이터에는 없지만 실제 판매 중)</div>{shop_chips}', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 비교 테이블
        st.markdown("### 📊 브랜드별 상세 비교")

        compare_data = []
        all_brands_set = search_set | shop_set

        search_map = {b["brand"].lower(): b for b in brand_results}
        shop_map = {b["brand"].lower(): b for b in shopping_brands}

        for bl in all_brands_set:
            s_data = search_map.get(bl)
            sh_data = shop_map.get(bl)

            name = s_data["brand"] if s_data else sh_data["brand"]
            search_vol = s_data[vol_col] if s_data else 0
            search_rank = (brand_results.index(s_data) + 1) if s_data and s_data in brand_results else "-"
            shop_count = sh_data["product_count"] if sh_data else 0
            shop_rank = sh_data["rank"] if sh_data else "-"

            where = "🏆 양쪽" if bl in both else ("🔍 검색만" if bl in only_search else "🛒 쇼핑만")

            compare_data.append({
                "브랜드": name,
                "구분": where,
                f"검색량 순위": search_rank,
                f"{vol_label}": search_vol,
                "쇼핑 순위": shop_rank,
                "쇼핑 상품수": shop_count,
            })

        compare_df = pd.DataFrame(compare_data)
        # 양쪽 > 검색만 > 쇼핑만 순, 같은 구분 내에서는 검색량 순
        sort_order = {"🏆 양쪽": 0, "🔍 검색만": 1, "🛒 쇼핑만": 2}
        compare_df["_sort"] = compare_df["구분"].map(sort_order)
        compare_df = compare_df.sort_values(["_sort", vol_label], ascending=[True, False]).drop("_sort", axis=1).reset_index(drop=True)
        compare_df.index = compare_df.index + 1

        st.dataframe(compare_df, use_container_width=True, hide_index=False)

        st.divider()

    # ── 검색량 기준 순위 ──
    st.markdown(f"### 📈 검색량 기준 브랜드 TOP {len(brand_results)}")

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

    chart_df = df[["brand", vol_col]].copy()
    chart_df.columns = ["브랜드", vol_label]
    chart_df = chart_df.set_index("브랜드")
    st.bar_chart(chart_df, color="#00e5a0", horizontal=True, height=max(400, len(brand_results) * 35))

    # ── 브랜드별 키워드 상세 ──
    st.markdown("### 🔎 브랜드별 키워드 상세")
    st.caption("각 브랜드를 펼치면 어떤 키워드로 검색량이 구성되었는지 확인할 수 있습니다.")

    for i, br in enumerate(brand_results):
        details = br.get("keyword_details", [])
        brand_name = br["brand"]
        total_vol = br["total"]
        kw_count = len(details)

        with st.expander(f"**{i+1}위 {brand_name}** — 통합 {total_vol:,} (키워드 {kw_count}개)", expanded=False):
            if details:
                detail_df = pd.DataFrame(details)
                detail_df.index = detail_df.index + 1
                detail_df.columns = ["키워드", "PC 검색량", "모바일 검색량", "통합 검색량"]

                # 비중 컬럼 추가
                if total_vol > 0:
                    detail_df["비중"] = detail_df["통합 검색량"].apply(lambda x: f"{x/total_vol*100:.1f}%")
                else:
                    detail_df["비중"] = "0%"

                st.dataframe(detail_df, use_container_width=True, hide_index=False)
            else:
                st.write("상세 데이터가 없습니다.")

    # ── 쇼핑 노출 기준 순위 ──
    if shopping_brands:
        st.markdown(f"### 🛒 네이버 쇼핑 노출 브랜드 TOP {min(20, len(shopping_brands))}")

        shop_df = pd.DataFrame(shopping_brands[:20])
        shop_df.index = shop_df.index + 1
        shop_df["대표상품"] = shop_df["sample_products"].apply(lambda x: ", ".join(x[:2]))

        shop_chart = shop_df[["brand", "product_count"]].copy()
        shop_chart.columns = ["브랜드", "상품 수"]
        shop_chart = shop_chart.set_index("브랜드")
        st.bar_chart(shop_chart, color="#ff6b35", horizontal=True, height=max(400, len(shop_df) * 35))

    # ── CSV 다운로드 ──
    st.markdown("### 📋 데이터 다운로드")
    csv_df = df[["brand", "주요키워드", "pc", "mobile", "total"]].copy()
    csv_df.columns = ["브랜드", "매칭키워드", "PC검색량", "모바일검색량", "통합검색량"]
    csv_data = csv_df.to_csv(index_label="순위", encoding="utf-8-sig")

    dl1, dl2, _ = st.columns([1, 1, 4])
    with dl1:
        st.download_button("⬇️ 검색량 CSV", csv_data, f"검색량_{kw}.csv", "text/csv", use_container_width=True)
    with dl2:
        if shopping_brands:
            shop_csv_df = pd.DataFrame(shopping_brands[:30])
            shop_csv_df["대표상품"] = shop_csv_df["sample_products"].apply(lambda x: ", ".join(x[:3]))
            shop_csv_data = shop_csv_df[["brand","product_count","rank","대표상품"]].to_csv(index=False, encoding="utf-8-sig")
            st.download_button("⬇️ 쇼핑 CSV", shop_csv_data, f"쇼핑_{kw}.csv", "text/csv", use_container_width=True)

else:
    st.info("👆 키워드를 입력하고 **분석 시작**을 클릭하세요!")
    st.markdown("""
    ### 🎯 작동 방식 (AI 5단계 분석)
    
    | 단계 | 내용 |
    |------|------|
    | 1️⃣ | 네이버 검색광고 API에서 연관 키워드 수집 |
    | 2️⃣ | 🤖 AI가 파생 키워드 추천 → 추가 검색으로 키워드 풀 확장 |
    | 3️⃣ | 🤖 AI가 전체 키워드에서 브랜드 자동 추출 |
    | 4️⃣ | 브랜드별 검색량 합산 → Top 20 순위 |
    | 5️⃣ | **네이버 쇼핑 검색 → 실제 노출 브랜드와 비교** |
    
    > 🆚 **검색량 순위**와 **쇼핑 노출 순위**를 나란히 비교하여
    > "검색은 많이 되지만 쇼핑에서 안 보이는 브랜드" vs "쇼핑에서는 보이지만 검색량이 낮은 브랜드"를 한눈에 파악!
    """)

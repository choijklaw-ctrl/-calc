import streamlit as st
import pandas as pd

# 페이지 기본 설정
st.set_page_config(
    page_title="유류분 및 반환안분액 계산기",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ 유류분 부족액 및 반환의무자별 안분 계산기")
st.caption("상속재산, 증여액(특별수익), 채무 및 상속인별 내역을 입력하여 유류분 부족액과 각 상대방별 반환 청구 금액을 산출합니다.")

st.markdown("---")

# 1. 기초 상속재산 정보 입력
st.header("1. 상속재산 및 채무 입력")
col1, col2, col3 = st.columns(3)

with col1:
    active_estate = st.number_input(
        "사망 당시 적극재산 (원)",
        min_value=0,
        value=200_000_000,
        step=10_000_000,
        format="%d",
        help="피상속인이 사망 당시에 소유하고 있던 예금, 부동산 등 적극재산의 총액입니다."
    )

with col2:
    total_gifts = st.number_input(
        "산정 대상 총 증여액 (원)",
        min_value=0,
        value=1_000_000_000,
        step=10_000_000,
        format="%d",
        help="상속인들의 특별수익 및 유류분 산정 대상이 되는 제3자 증여액의 총합입니다."
    )

with col3:
    debt = st.number_input(
        "상속채무 (원)",
        min_value=0,
        value=50_000_000,
        step=5_000_000,
        format="%d",
        help="피상속인이 남긴 채무의 총액입니다."
    )

# 기초재산 산정
base_estate = active_estate + total_gifts - debt
st.info(f"💡 **유류분 산정 대상 기초재산**: `{base_estate:,.0f} 원` (적극재산 + 증여액 - 채무)")

st.markdown("---")

# 2. 상속인 정보 입력
st.header("2. 상속인 정보 설정")

num_heirs = st.number_input("상속인 수", min_value=1, max_value=10, value=3, step=1)

heirs_data = []

# 기본 테스트 데이터
default_names = ["배우자", "자녀A", "자녀B"]
default_relations = ["배우자", "직계비속", "직계비속"]
default_shares = [1.5, 1.0, 1.0]
default_gifts = [800_000_000, 150_000_000, 50_000_000]
default_nets = [150_000_000, 0, 0]

st.subheader("상속인별 세부 내역 입력")

for i in range(int(num_heirs)):
    st.markdown(f"**상속인 {i+1}**")
    c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 2.5, 2.5])
    
    with c1:
        name = st.text_input(f"성명/칭호 #{i+1}", value=default_names[i] if i < len(default_names) else f"상속인{i+1}", key=f"name_{i}")
    with c2:
        relation = st.selectbox(
            f"관계 #{i+1}",
            ["직계비속", "배우자", "직계존속", "형제자매"],
            index=["직계비속", "배우자", "직계존속", "형제자매"].index(default_relations[i]) if i < len(default_relations) else 0,
            key=f"rel_{i}"
        )
    with c3:
        share = st.number_input(
            f"법정상속지분율 #{i+1}",
            min_value=0.1,
            value=default_shares[i] if i < len(default_shares) else 1.0,
            step=0.5,
            key=f"share_{i}"
        )
    with c4:
        gift = st.number_input(
            f"특별수익(증여/유증) #{i+1}",
            min_value=0,
            value=default_gifts[i] if i < len(default_gifts) else 0,
            step=10_000_000,
            format="%d",
            key=f"gift_{i}"
        )
    with c5:
        net = st.number_input(
            f"순상속분액 #{i+1}",
            min_value=0,
            value=default_nets[i] if i < len(default_nets) else 0,
            step=10_000_000,
            format="%d",
            key=f"net_{i}"
        )
        
    heirs_data.append({
        "id": i,
        "name": name,
        "relation": relation,
        "share": share,
        "gift": gift,
        "net": net
    })

st.markdown("---")

# 3. 유류분 계산 및 안분 산정
st.header("3. 유류분 및 안분 금액 계산")

heir_names = [h["name"] for h in heirs_data]
target_name = st.selectbox("유류분 부족액을 계산할 청구권자를 선택하세요", heir_names, index=2 if len(heir_names) > 2 else 0)

if st.button("🚀 유류분 및 반환 안분액 계산하기", type="primary"):
    if base_estate <= 0:
        st.error("기초재산이 0 이하이므로 산출할 유류분이 없습니다.")
    else:
        total_statutory_shares = sum(h["share"] for h in heirs_data)
        share_ratios = {
            "직계비속": 0.5,
            "배우자": 0.5,
            "직계존속": 1/3,
            "형제자매": 0.0
        }

        # 모든 상속인의 유류분액 및 초과특별수익 산정
        calculated_heirs = []
        for h in heirs_data:
            stat_ratio = h["share"] / total_statutory_shares
            forced_ratio = share_ratios.get(h["relation"], 0.5)
            forced_amount = base_estate * stat_ratio * forced_ratio
            already_rcvd = h["gift"] + h["net"]
            excess_gift = max(0, h["gift"] - forced_amount) # 자신의 유류분액을 초과한 증여액
            
            calculated_heirs.append({
                **h,
                "stat_ratio": stat_ratio,
                "forced_ratio": forced_ratio,
                "forced_amount": forced_amount,
                "already_rcvd": already_rcvd,
                "shortage": max(0, forced_amount - already_rcvd),
                "excess_gift": excess_gift
            })

        # 청구권자 데이터 추출
        target_idx = heir_names.index(target_name)
        target = calculated_heirs[target_idx]
        shortage = target["shortage"]

        # 결과 출력 - 청구권자 기준
        st.subheader(f"📊 [{target['name']}] 님의 유류분 계산 결과")
        
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("총 기초재산", f"{base_estate:,.0f} 원")
        res_col2.metric("산정된 유류분액", f"{target['forced_amount']:,.0f} 원")
        
        if shortage > 0:
            res_col3.metric("⚠️ 최종 유류분 부족액", f"{shortage:,.0f} 원", delta=f"{shortage:,.0f} 원", delta_color="inverse")
            st.error(f"**[{target['name']}]** 님은 유류분 법정 기준 대비 **{shortage:,.0f} 원**이 부족합니다.")
            
            # --- 4. 반환의무자별 안분 계산 ---
            st.markdown("---")
            st.header("4. 반환의무자별 반환액 안분 계산")
            
            # 청구권자 제외한 다른 상속인 중 초과특별수익이 있는 자 추출
            obligors = [h for h in calculated_heirs if h["id"] != target["id"] and h["excess_gift"] > 0]
            total_excess_gift = sum(o["excess_gift"] for o in obligors)

            if total_excess_gift > 0:
                st.write(f"유류분 부족액 **{shortage:,.0f} 원**에 대해, 자신의 유류분액을 초과하여 특별수익을 얻은 상속인들이 초과특별수익 비율에 따라 반환해야 할 금액입니다.")

                apportionment_list = []
                for o in obligors:
                    ratio = o["excess_gift"] / total_excess_gift
                    refund_amount = shortage * ratio
                    apportionment_list.append({
                        "반환의무자": o["name"],
                        "관계": o["relation"],
                        "특별수익(증여/유증)": f"{o['gift']:,.0f} 원",
                        "자신의 유류분액": f"{o['forced_amount']:,.0f} 원",
                        "초과특별수익액": f"{o['excess_gift']:,.0f} 원",
                        "안분 비율": f"{ratio * 100:.2f}%",
                        "최종 반환 청구 금액": f"{refund_amount:,.0f} 원"
                    })

                st.table(pd.DataFrame(apportionment_list))
            else:
                st.warning("청구 상대방(다른 상속인) 중 자신의 유류분액을 초과하여 특별수익을 얻은 자가 없어 상속인 간 안분 청구가 불가능합니다. (제3자 증여가 있는 경우 제3자를 대상으로 청구 고려)")

        else:
            res_col3.metric("최종 유류분 부족액", "0 원")
            st.success(f"**[{target['name']}]** 님은 이미 유류분 상당액 이상({target['already_rcvd']:,.0f} 원)을 취득하였으므로 유류분 부족액이 없으며, 반환 청구 대상이 존재하지 않습니다.")

        # 종합 현황표
        with st.expander("🔍 전체 상속인별 유류분 계산 현황표 보기"):
            summary_df = pd.DataFrame([{
                "성명": h["name"],
                "관계": h["relation"],
                "유류분액": f"{h['forced_amount']:,.0f} 원",
                "기취득액(특별수익+순상속)": f"{h['already_rcvd']:,.0f} 원",
                "부족액": f"{h['shortage']:,.0f} 원",
                "초과특별수익액": f"{h['excess_gift']:,.0f} 원"
            } for h in calculated_heirs])
            st.dataframe(summary_df, use_container_width=True)
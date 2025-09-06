"""
使用 Streamlit 展示分析结果的最小 Dashboard
运行: streamlit run dashboard_app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("选品分析 - 核桃 (MVP)")

uploaded = st.file_uploader("上传分析结果 JSON", type=["json"])

# 省级经纬度映射（用于散点地图热力展示，部分省份示例）
PROVINCE_COORDS = {
    '北京市': (39.9042, 116.4074),
    '天津市': (39.3434, 117.3616),
    '上海市': (31.2304, 121.4737),
    '重庆市': (29.4316, 106.9123),
    '河北省': (38.0428, 114.5149),
    '山西省': (37.8735, 112.5624),
    '辽宁省': (41.8057, 123.4315),
    '吉林省': (43.8888, 125.3221),
    '黑龙江省': (45.7420, 126.6617),
    '江苏省': (32.0603, 118.7969),
    '浙江省': (30.2674, 120.1528),
    '安徽省': (31.8612, 117.2857),
    '福建省': (26.0745, 119.2965),
    '江西省': (28.6741, 115.9100),
    '山东省': (36.6683, 117.0206),
    '河南省': (34.7570, 113.6500),
    '湖北省': (30.5928, 114.3055),
    '湖南省': (28.1127, 112.9834),
    '广东省': (23.1291, 113.2644),
    '海南省': (20.0442, 110.1999),
    '四川省': (30.6595, 104.0657),
    '贵州省': (26.5982, 106.7074),
    '云南省': (25.0406, 102.7091),
    '陕西省': (34.2632, 108.9480),
    '甘肃省': (36.0594, 103.8263),
    '青海省': (36.6200, 101.7779),
    '内蒙古自治区': (40.8170, 111.7652),
    '广西壮族自治区': (22.8156, 108.3275),
    '西藏自治区': (29.6469, 91.1409),
    '宁夏回族自治区': (38.4736, 106.2587),
    '新疆维吾尔自治区': (43.7928, 87.6177),
}

if uploaded is not None:
    df = pd.read_json(uploaded)
    # 确保时间列
    if 'scrape_time' in df.columns:
        df['scrape_time'] = pd.to_datetime(df['scrape_time'])
    else:
        df['scrape_time'] = pd.Timestamp.now()

    st.sidebar.subheader('筛选')
    min_date = df['scrape_time'].min().date()
    max_date = df['scrape_time'].max().date()
    start_date = st.sidebar.date_input('开始日期', min_date)
    end_date = st.sidebar.date_input('结束日期', max_date)

    # 产地筛选
    origins = ['All'] + sorted(df['origin'].fillna('').unique().tolist())
    selected_origins = st.sidebar.multiselect('产地筛选 (可多选)', origins, default=['All'])

    # 过滤时间窗口
    mask = (df['scrape_time'].dt.date >= start_date) & (df['scrape_time'].dt.date <= end_date)
    df_filtered = df.loc[mask].copy()
    if 'All' not in selected_origins:
        df_filtered = df_filtered[df_filtered['origin'].isin(selected_origins)]

    st.subheader("候选商品表")
    st.dataframe(df_filtered[["title", "url", "origin", "score"]])

    st.subheader("描述长度分布")
    fig = px.histogram(df_filtered, x="desc_len", nbins=20)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("关键词命中热力")
    kw_cols = [c for c in df_filtered.columns if c.startswith("kw_")]
    if kw_cols:
        kw_sum = df_filtered[kw_cols].sum().reset_index()
        kw_sum.columns = ["keyword", "count"]
        fig2 = px.bar(kw_sum, x="keyword", y="count")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top 5 候选")
    st.table(df_filtered[["title", "url", "origin", "score"]].head(5))

    # 产地统计与地图
    st.subheader('产地分布（省级）')
    origin_counts = df_filtered['origin'].fillna('未知').value_counts()
    origin_df = origin_counts.reset_index()
    origin_df.columns = ['origin', 'count']

    # 添加经纬度
    lats = []
    lons = []
    for prov in origin_df['origin']:
        coord = PROVINCE_COORDS.get(prov, (None, None))
        lats.append(coord[0])
        lons.append(coord[1])
    origin_df['lat'] = lats
    origin_df['lon'] = lons

    # 地图可视化：使用 scatter_geo 作为省级热力近似
    map_df = origin_df.dropna(subset=['lat', 'lon'])
    if not map_df.empty:
        fig_map = px.scatter_geo(map_df, lat='lat', lon='lon', size='count', color='count', hover_name='origin',
                                 projection='natural earth', scope='asia', title='省级产地热力（散点近似）')
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info('当前数据没有匹配到省级经纬度，无法绘制地图。')

    st.subheader('产地占比')
    fig_pie = px.pie(origin_df, names='origin', values='count')
    st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("请先运行爬虫与分析，上传生成的 analysis_output.json 文件。")

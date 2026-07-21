import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบข้อมูลเกษตรเชียงใหม่จาก API", layout="wide")
st.title("ระบบข้อมูลเกษตรจังหวัดเชียงใหม่ (Live Agri-Data)")
st.caption("ดึงข้อมูลจริงแบบสดจากอินเทอร์เน็ต โฟกัสพื้นที่จังหวัดเชียงใหม่ แล้วแสดงผลโต้ตอบได้")

# พิกัดตั้งต้น: ตัวเมืองเชียงใหม่ (อ.เมืองเชียงใหม่)
LAT_ค่าเริ่มต้น = 18.7883
LON_ค่าเริ่มต้น = 98.9853

# ส่ง User-Agent แบบเบราว์เซอร์ ช่วยให้บาง API ไม่บล็อกว่าเป็นบอท
HEADERS = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0 Safari/537.36"),
           "Accept": "application/json"}

# หมายเหตุ: ชื่อคอลัมน์ห้ามมีจุด "." หรือวงเล็บ เพราะกราฟของ Streamlit (Vega-Lite)
# จะตีความจุดเป็นตัวเข้าถึงฟิลด์ย่อย ทำให้วาดค่าไม่ออก — หน่วยจึงไปไว้ที่ caption/label แทน

@st.cache_data(ttl=1800)
def ดึงอากาศ(lat, lon, days):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
           f"relative_humidity_2m_mean,wind_speed_10m_max,shortwave_radiation_sum"
           f"&timezone=Asia/Bangkok&forecast_days={days}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    w = pd.DataFrame(resp.json()["daily"])
    w.columns = ["วันที่", "สูงสุด", "ต่ำสุด", "ฝน", "ความชื้น", "ลม", "แสง"]
    return w

@st.cache_data(ttl=1800)
def ดึงระดับน้ำ(lat, lon):
    url = (f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}"
           f"&daily=river_discharge&forecast_days=30")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    r = pd.DataFrame(resp.json()["daily"])
    r.columns = ["วันที่", "ปริมาณน้ำ"]
    return r

@st.cache_data(ttl=1800)
def ดึงคุณภาพอากาศ(lat, lon, days):
    # Open-Meteo Air Quality API — ไม่ต้องใช้ API key เหมือน endpoint อื่น ๆ ในแอปนี้
    url = (f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}"
           f"&hourly=pm2_5,pm10,us_aqi&timezone=Asia/Bangkok&forecast_days={days}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    a = pd.DataFrame(resp.json()["hourly"])
    a.columns = ["เวลา", "PM2_5", "PM10", "AQI_US"]
    a["เวลา"] = pd.to_datetime(a["เวลา"])
    return a

def ระดับคุณภาพอากาศ(pm25):
    # เกณฑ์อ้างอิงคร่าว ๆ ตามดัชนีคุณภาพอากาศของไทย (PM2.5 หน่วย มคก./ลบ.ม.)
    if pm25 <= 25:
        return "ดี", "🟢"
    elif pm25 <= 37.5:
        return "ปานกลาง", "🟡"
    elif pm25 <= 75:
        return "เริ่มมีผลต่อสุขภาพ", "🟠"
    else:
        return "มีผลต่อสุขภาพ", "🔴"

# ราคาอ้างอิงพืชเศรษฐกิจสำคัญของเชียงใหม่ (ตัวอย่างประกอบ ไม่ใช่ราคาสดรายวัน)
# ใช้แสดงเมื่อเซิร์ฟเวอร์เข้าแหล่งข้อมูลราคาสดของภาครัฐไม่ได้
ราคาสำรอง = pd.DataFrame({
    "สินค้า": ["ลำไยสด AA", "กระเทียมแห้งคละ", "หอมแดงคละ",
              "ข้าวเหนียว กข6 (เปลือก)", "ลิ้นจี่ฮงฮวย", "กาแฟอาราบิกากะลา"],
    "ราคา": [18.0, 45.0, 25.0, 11.5, 30.0, 120.0],
})

@st.cache_data(ttl=86400)
def _ดึงราคาดิบ():
    # หมายเหตุ: ต้องใส่ resource_id ของชุดข้อมูลราคาสินค้าเกษตร "จังหวัดเชียงใหม่" จาก data.go.th เอง
    # (เดิมโค้ดนี้ผูกกับชุดข้อมูลของบึงกาฬ ซึ่งไม่ใช่ข้อมูลเชียงใหม่ จึงปิดการเรียกไว้ก่อน
    #  เพื่อไม่ให้แสดงข้อมูลผิดจังหวัดโดยไม่ตั้งใจ)
    raise NotImplementedError("ยังไม่ได้ตั้งค่า resource_id ของชุดข้อมูลราคาสินค้าเกษตรเชียงใหม่")

def ดึงราคาเกษตร():
    # st.cache_data ไม่เก็บผลตอน error ดังนั้นถ้าพลาดครั้งนี้ ครั้งหน้าจะลองใหม่เอง
    try:
        return _ดึงราคาดิบ(), True
    except Exception:
        return None, False

แท็บอากาศ, แท็บน้ำ, แท็บราคา, แท็บฝุ่น = st.tabs(
    ["สภาพอากาศ", "ระดับน้ำแม่น้ำ", "ราคาสินค้าเกษตร", "คุณภาพอากาศ (PM2.5)"])

# ---------- แท็บ 1: สภาพอากาศ (Open-Meteo) ----------
with แท็บอากาศ:
    st.subheader("พยากรณ์อากาศรายวันของสวน (จ.เชียงใหม่)")
    c1, c2, c3 = st.columns(3)
    lat = c1.number_input("ละติจูด", value=LAT_ค่าเริ่มต้น)
    lon = c2.number_input("ลองจิจูด", value=LON_ค่าเริ่มต้น)
    วัน = c3.slider("จำนวนวันล่วงหน้า", 3, 16, 15)
    try:
        w = ดึงอากาศ(lat, lon, วัน)
        m1, m2, m3 = st.columns(3)
        m1.metric("อุณหภูมิสูงสุดพรุ่งนี้", f"{w['สูงสุด'].iloc[1]:.0f} °C")
        m2.metric("ฝนรวม (ช่วงที่ดู)", f"{w['ฝน'].sum():.0f} มม.")
        m3.metric("ความชื้นเฉลี่ย", f"{w['ความชื้น'].mean():.0f} %")
        st.write("อุณหภูมิสูงสุด/ต่ำสุด (°C)")
        st.line_chart(w.set_index("วันที่")[["สูงสุด", "ต่ำสุด"]])
        st.write("ปริมาณฝนรายวัน (มม.)")
        st.bar_chart(w.set_index("วันที่")["ฝน"])
        with st.expander("ดูข้อมูลดิบทั้งหมด (หน่วย: °C, มม., %, กม./ชม., MJ/m²)"):
            st.dataframe(w)
    except Exception as e:
        st.error(f"ดึงข้อมูลอากาศไม่สำเร็จ ลองใหม่อีกครั้ง (สาเหตุ: {e})")

# ---------- แท็บ 2: ระดับน้ำแม่น้ำ (flood API) ----------
with แท็บน้ำ:
    st.subheader("ปริมาณการไหลของแม่น้ำปิงและลำน้ำสาขา (เตือนภัยน้ำท่วม จ.เชียงใหม่)")
    c1, c2 = st.columns(2)
    lat2 = c1.number_input("ละติจูด (จุดใกล้แม่น้ำ)", value=LAT_ค่าเริ่มต้น, key="lat_river")
    lon2 = c2.number_input("ลองจิจูด (จุดใกล้แม่น้ำ)", value=LON_ค่าเริ่มต้น, key="lon_river")
    try:
        r = ดึงระดับน้ำ(lat2, lon2)
        st.write("ปริมาณการไหล (ลูกบาศก์เมตร/วินาที)")
        st.line_chart(r.set_index("วันที่")["ปริมาณน้ำ"])
        st.info("ยิ่งค่าสูง = น้ำในแม่น้ำยิ่งมาก/เสี่ยงท่วม (เป็นปริมาณการไหล ไม่ใช่ระดับเป็นเมตร)")
        with st.expander("ดูข้อมูลดิบทั้งหมด"):
            st.dataframe(r)
    except Exception as e:
        st.error(f"ดึงระดับน้ำไม่สำเร็จ ลองใหม่อีกครั้ง (สาเหตุ: {e})")

# ---------- แท็บ 3: ราคาสินค้าเกษตร (เชียงใหม่) ----------
with แท็บราคา:
    st.subheader("ราคาสินค้าเกษตรอ้างอิง จ.เชียงใหม่")
    ราคา, สด = ดึงราคาเกษตร()
    if not สด:
        st.warning("ยังไม่ได้เชื่อมต่อชุดข้อมูลราคาสดของภาครัฐสำหรับจังหวัดเชียงใหม่ "
                   "(ต้องระบุ resource_id ของ data.go.th เอง) — แสดงราคาอ้างอิงแทน")
        st.write("ราคาอ้างอิง (บาท/กก.)")
        st.bar_chart(ราคาสำรอง.set_index("สินค้า")["ราคา"])
        st.dataframe(ราคาสำรอง, hide_index=True)
        st.caption("หมายเหตุ: เป็นตัวเลขอ้างอิงประกอบการสาธิตเท่านั้น ไม่ใช่ราคาตลาดรายวันจริง "
                   "หากมี resource_id ของชุดข้อมูลราคาสินค้าเกษตรเชียงใหม่จาก data.go.th "
                   "สามารถนำไปใส่ในฟังก์ชัน _ดึงราคาดิบ() เพื่อดึงข้อมูลสดได้")
    else:
        ปีล่าสุด = int(ราคา["ปี"].max())
        สินค้าทั้งหมด = sorted(ราคา["สินค้า"].dropna().unique())
        ค่าเริ่ม = [s for s in ["ลำไยสด AA", "กระเทียมแห้งคละ", "หอมแดงคละ"]
                   if s in สินค้าทั้งหมด]
        เลือก = st.multiselect("เลือกสินค้าที่จะดู", สินค้าทั้งหมด, default=ค่าเริ่ม)
        st.caption(f"ข้อมูลล่าสุดปี พ.ศ. {ปีล่าสุด} — สถิติทางการรายเดือน (จ.เชียงใหม่) หน่วย บาท/กก.")
        เดือนเรียง = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                     "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
        if เลือก:
            ปีนี้ = ราคา[(ราคา["ปี"] == ปีล่าสุด) & (ราคา["สินค้า"].isin(เลือก))].copy()
            ปีนี้["เดือน"] = pd.Categorical(ปีนี้["เดือน"], categories=เดือนเรียง, ordered=True)
            ตาราง = ปีนี้.pivot_table(index="เดือน", columns="สินค้า",
                                     values="ราคา", observed=False)
            ตาราง = ตาราง.sort_index()
            ตาราง.index = ตาราง.index.astype(str)   # เลี่ยง categorical index ที่กราฟไม่ยอมวาด
            st.line_chart(ตาราง)
            เดือนล่าสุด = ตาราง.dropna(how="all").index[-1]
            st.write(f"ราคาเดือนล่าสุด ({เดือนล่าสุด} {ปีล่าสุด}) หน่วย บาท/กก.")
            แถวล่าสุด = ตาราง.loc[[เดือนล่าสุด]].T
            แถวล่าสุด.columns = ["ราคา"]
            st.dataframe(แถวล่าสุด)
        else:
            st.warning("เลือกสินค้าอย่างน้อย 1 อย่าง")

# ---------- แท็บ 4: คุณภาพอากาศ / ฝุ่น PM2.5 (Open-Meteo) ----------
with แท็บฝุ่น:
    st.subheader("คุณภาพอากาศและฝุ่น PM2.5 จ.เชียงใหม่")
    st.caption("มีประโยชน์เป็นพิเศษช่วงหน้าแล้ง/ฤดูเผา (ก.พ.–เม.ย.) ที่กระทบต่อสุขภาพและการทำงานกลางแจ้ง")
    c1, c2, c3 = st.columns(3)
    lat3 = c1.number_input("ละติจูด", value=LAT_ค่าเริ่มต้น, key="lat_pm")
    lon3 = c2.number_input("ลองจิจูด", value=LON_ค่าเริ่มต้น, key="lon_pm")
    วันฝุ่น = c3.slider("จำนวนวันล่วงหน้า", 1, 5, 3, key="days_pm")
    try:
        a = ดึงคุณภาพอากาศ(lat3, lon3, วันฝุ่น)
        pm25_ปัจจุบัน = a["PM2_5"].iloc[0]
        ระดับ, สัญลักษณ์ = ระดับคุณภาพอากาศ(pm25_ปัจจุบัน)
        m1, m2, m3 = st.columns(3)
        m1.metric("PM2.5 ปัจจุบัน", f"{pm25_ปัจจุบัน:.0f} มคก./ลบ.ม.")
        m2.metric("PM10 ปัจจุบัน", f"{a['PM10'].iloc[0]:.0f} มคก./ลบ.ม.")
        m3.metric("ระดับคุณภาพอากาศ", f"{สัญลักษณ์} {ระดับ}")
        if pm25_ปัจจุบัน > 37.5:
            st.warning("ค่าฝุ่นเริ่มมีผลต่อสุขภาพ — ควรจำกัดกิจกรรมกลางแจ้งที่ใช้แรงมาก")
        st.write("PM2.5 และ PM10 รายชั่วโมง (มคก./ลบ.ม.)")
        st.line_chart(a.set_index("เวลา")[["PM2_5", "PM10"]])
        st.write("ดัชนีคุณภาพอากาศสหรัฐฯ (US AQI) รายชั่วโมง")
        st.bar_chart(a.set_index("เวลา")["AQI_US"])
        with st.expander("ดูข้อมูลดิบทั้งหมด"):
            st.dataframe(a)
    except Exception as e:
        st.error(f"ดึงข้อมูลคุณภาพอากาศไม่สำเร็จ ลองใหม่อีกครั้ง (สาเหตุ: {e})")
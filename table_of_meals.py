import tkinter as tk
from tkinter import ttk
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import webbrowser

def open_link(url):
    """지정된 URL을 웹 브라우저에서 Open"""
    webbrowser.open_new(url)

# [1] 식단표 페이지 URL
url = "https://www.kopo.ac.kr/seongnam/content.do?menu=4304"

# [2] 요일 변환 (토요일 & 일요일 제외)
weekdays_kor = {
    "Monday": "월요일",
    "Tuesday": "화요일",
    "Wednesday": "수요일",
    "Thursday": "목요일",
    "Friday": "금요일"
}

# [3] 전역 캐시 변수: 프로그램 실행 시 한 번만 데이터를 받아옴
cached_html = None

def cache_meal_data():
    global cached_html
    try:
        response = requests.get(url)
        response.raise_for_status()
        cached_html = response.text
    except Exception as e:
        cached_html = ""
        print("네트워크 오류 발생:", e)

cache_meal_data()

# [4] 특정 날짜의 식단 가져오기 (캐시된 HTML 사용, 주말이면 금요일 식단 표시)
def fetch_meal_data(target_date):
    target_weekday_eng = target_date.strftime("%A")
    # 주말(토,일)이면 금요일 식단으로 변경
    if target_weekday_eng in ["Saturday", "Sunday"]:
        target_date -= timedelta(days=(target_date.weekday() - 4))
        target_weekday_eng = "Friday"
    target_weekday = weekdays_kor[target_weekday_eng]

    meal_data = {"조식": "정보 없음", "중식": "정보 없음", "석식": "정보 없음"}
    
    if cached_html:
        soup = BeautifulSoup(cached_html, "html.parser")
        menu_table = soup.find("table", class_="tbl_table menu")
        if menu_table:
            rows = menu_table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if cols and target_weekday in cols[0].text:
                    def clean_text(text):
                        return ''.join(filter(str.isprintable, text.strip())).replace("\xa0", " ")
                    meal_data["조식"] = clean_text(cols[1].text)
                    meal_data["중식"] = clean_text(cols[2].text)
                    meal_data["석식"] = clean_text(cols[3].text)
                    break
    return target_date, target_weekday, meal_data

# [5] 현재 시간 기준으로 올바른 식단 날짜 가져오기
def get_correct_meal_date():
    now = datetime.now()
    hour = now.hour
    target_date = datetime.today()  # 매번 현재 날짜를 새로 불러옴

    if target_date.strftime("%A") == "Friday" and hour >= 18:
        return target_date  # 금요일 18시 이후에는 금요일 유지

    if hour >= 18:
        target_date += timedelta(days=1)  # 18시 이후면 다음날로 변경

    return fetch_meal_data(target_date)[0]  # 정확한 날짜 반환

# [6] 현재 시간에 따른 식사유형 강조 (오늘 혹은 내일(18시 이후)인 경우)
def get_current_meal(effective_date):
    now = datetime.now()
    today_date = datetime.today().date()
    target_day = effective_date.date()
    
    # 오늘 날짜의 식단인 경우
    if target_day == today_date:
        if now.weekday() >= 5:  # 주말은 강조 없음
            return None
        if now.hour < 9:
            return "조식"
        elif now.hour < 13:
            return "중식"
        elif now.hour < 18:
            return "석식"
        else:
            return None
    # 내일 날짜의 식단이고, 현재 시간이 18시 이상인 경우 (즉, 내일 조식을 강조)
    elif target_day == today_date + timedelta(days=1) and now.hour >= 18:
        if (today_date + timedelta(days=1)).weekday() >= 5:  # 내일이 주말이면 강조 없음
            return None
        return "조식"
    else:
        return None

# [7] Tkinter GUI 생성
root = tk.Tk()
root.title("한국폴리텍 성남 학생식당 식단표")
root.geometry("400x500")
root.resizable(False, False)
root.configure(bg="#f4f4f4")

# [8] 기본 ttk 스타일 적용 (타이틀 등 기본 UI는 그대로 사용)
style = ttk.Style()
style.configure("TLabel", font=("Arial", 12), background="#f4f4f4")
style.configure("TFrame", background="#ffffff", relief="raised", borderwidth=2)
style.configure("Title.TLabel", font=("Arial", 16, "bold"), foreground="#333")
style.configure("TButton", font=("Arial", 12), padding=5)

# [9] 프로그램 시작 시 올바른 식단 불러오기 (캐시된 데이터를 활용)
selected_date = get_correct_meal_date()
selected_date, selected_weekday, selected_meals = fetch_meal_data(selected_date)

# [10] 타이틀 프레임
title_label = ttk.Label(root, style="Title.TLabel")
title_label.pack(pady=10)

# [11] 요일 선택 드롭다운 및 현재 식단 바로가기 버튼
top_frame = ttk.Frame(root)
top_frame.pack(pady=5, fill="x")

weekday_combobox = ttk.Combobox(top_frame, values=list(weekdays_kor.values()), state="readonly", font=("Arial", 12))
weekday_combobox.set(selected_weekday)
weekday_combobox.pack(side="left", padx=5)

def on_weekday_selected(event):
    selected_weekday_val = weekday_combobox.get()
    current_date = datetime.today()
    # 오늘 기준으로 -7일부터 +7일 사이에서 해당 요일을 찾음 (주말은 자동 금요일 처리)
    for i in range(-7, 8):
        test_date = current_date + timedelta(days=i)
        weekday_eng = test_date.strftime("%A")
        if weekdays_kor.get(weekday_eng) == selected_weekday_val:
            update_ui(test_date)
            break

weekday_combobox.bind("<<ComboboxSelected>>", on_weekday_selected)

def go_to_current_meal():
    update_ui(get_correct_meal_date())

current_meal_button = ttk.Button(top_frame, text="현재 식단 바로가기", command=go_to_current_meal)
current_meal_button.pack(side="right", padx=5)

# [12] 어제 & 내일 버튼 프레임
button_frame = ttk.Frame(root)
button_frame.pack(pady=5)

def show_previous_meal():
    previous_day = selected_date - timedelta(days=1)
    while previous_day.strftime("%A") in ["Saturday", "Sunday"]:
        previous_day -= timedelta(days=1)
    update_ui(previous_day)

def show_next_meal():
    next_day = selected_date + timedelta(days=1)
    while next_day.strftime("%A") in ["Saturday", "Sunday"]:
        next_day += timedelta(days=1)
    update_ui(next_day)

prev_button = ttk.Button(button_frame, text="⬅ 어제 식단 보기", command=show_previous_meal)
prev_button.pack(side="left", padx=5)

next_button = ttk.Button(button_frame, text="내일 식단 보기 ➡", command=show_next_meal)
next_button.pack(side="right", padx=5)

# [13] 식단 프레임 생성 (배경색 강조를 위해 tk.Label 사용)
meal_frame = ttk.Frame(root)
meal_frame.pack(pady=10, padx=10, fill="both")

meal_titles = {}
meal_labels = {}

for meal in ["조식", "중식", "석식"]:
    meal_title = tk.Label(meal_frame, text=f"🍽 {meal}", font=("Arial", 14, "bold"), bg="#ffffff", fg="#555", anchor="w")
    meal_title.pack(fill="x", padx=10, pady=2)
    meal_titles[meal] = meal_title  
    
    label = tk.Label(meal_frame, text=selected_meals[meal], font=("Arial", 12), bg="#ffffff", fg="#222", wraplength=350, justify="center")
    label.pack(fill="x", padx=10, pady=5)
    meal_labels[meal] = label  

# [14] UI 업데이트 함수 (캐시된 데이터를 활용, 예외 처리 포함)
def update_ui(target_date):
    global selected_date, selected_weekday, selected_meals
    try:
        selected_date, selected_weekday, selected_meals = fetch_meal_data(target_date)
    except Exception as e:
        title_label.config(text="식단 정보를 불러올 수 없습니다.")
        for meal in ["조식", "중식", "석식"]:
            meal_labels[meal].config(text="정보 없음", bg="#ffffff")
        return
    
    title_label.config(text=f"🍜 {selected_weekday}의 식단")
    weekday_combobox.set(selected_weekday)
    
    # 선택한 날짜가 오늘과 같은 요일이면, 오늘 날짜로 강제하여 현재 시간 강조가 적용되도록 함.
    effective_date = target_date
    if target_date.strftime("%A") == datetime.today().strftime("%A"):
        effective_date = datetime.today()
    
    current_meal = get_current_meal(effective_date)
    for meal in ["조식", "중식", "석식"]:
        highlight = "yellow" if meal == current_meal else "#ffffff"
        meal_titles[meal].config(bg=highlight)
        meal_labels[meal].config(text=selected_meals[meal], bg=highlight)

# [15] 09시, 13시, 18시 정각에 UI 갱신 (단, 캐시된 데이터를 사용)
def check_update_time():
    now = datetime.now()
    update_hours = [9, 13, 18]
    
    if now.hour in update_hours and now.minute == 0:
        update_ui(get_correct_meal_date())
        
    root.after(60000, check_update_time)


# [16] 푸터 생성 (2단 구조)
# 두 줄을 표시하기 위해 높이를 50으로 늘림
footer_frame = tk.Frame(root, bg="#e0e0e0", height=50)
footer_frame.pack_propagate(False)
footer_frame.pack(side="bottom", fill="x")

# --- 첫 번째 줄 ---
line1_frame = tk.Frame(footer_frame, bg="#e0e0e0")
line1_frame.pack(fill="x", padx=10, pady=(5, 0)) # 위쪽 여백만 줌

# 저작권 및 버전 정보
copyright_text = "© 2025 Jeyun. All rights reserved. (v5.0.0)"
copyright_label = tk.Label(line1_frame, text=copyright_text, bg="#e0e0e0", fg="#555")
copyright_label.pack(side="left")

# --- 두 번째 줄 ---
line2_frame = tk.Frame(footer_frame, bg="#e0e0e0")
line2_frame.pack(fill="x", padx=10, pady=(0, 5)) # 아래쪽 여백만 줌

# 개발자 정보 및 GitHub 링크
developer_text = "Developed by Jeyun (https://github.com/JeyunH)"
developer_label = tk.Label(
    line2_frame,
    text=developer_text,
    fg="blue",
    cursor="hand2",
    bg="#e0e0e0"
)
developer_label.pack(side="left")

# 라벨에 GitHub 링크 클릭 이벤트 연결
github_url = "https://github.com/JeyunH"
developer_label.bind("<Button-1>", lambda e: open_link(github_url))


# [17] 초기 UI 업데이트 및 자동 갱신 실행
update_ui(selected_date)
check_update_time()

# [18] Tkinter 실행
root.mainloop()

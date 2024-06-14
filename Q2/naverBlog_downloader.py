from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs, urlencode
import time
import os
import pandas as pd

# 웹 드라이버 설정
path = "chromedriver(123).exe"
service = Service(executable_path=path)

print("="*30,"\n네이버 사이트에서 블로그 정보를 수집하는 크롤러 입니다.\n","="*30)
keyWord = input("크롤링할 검색어는 무엇입니까?: ")
cnt = int(input("크롤링 할 건수는 몇건입니까?(최대 1000건):"))
if cnt > 1000:
    cnt = 1000


include_words = input("결과에서 반드시 포함하는 단어를 입력하세요(ex:일본,바닷가)\n(여러개일 경우 ,로 구분해서 입력하고 없으면 엔터 입력하시오): ")
exclude_words = input("결과에서 제외할 단어를 입력하세요(예:역세권,국내)\n(여러개일 경우 ,로 구분해서 입력하고 없으면 엔터 입력하시오): ")
savePath = input("결과를 저장할 디렉터리 경로를 입력하시오:(ex:C:\\Users\\popoj\\Desktop\\test)")
include_list = include_words.split(",") if include_words else []
exclude_list = exclude_words.split(",") if exclude_words else []

result_keyWord = keyWord

for word in include_list:
    if word:
        result_keyWord += " +" + word

for word in exclude_list:
    if word:
        result_keyWord += " -" + word

# print(f"최종 검색 키워드: {result_keyWord}")
keyWord = result_keyWord

print("검색 옵션을 선택하세요:")
print("1. 모든 시간대 검색")
print("2. 1시간 이내 검색")
print("3. 1일 이내 검색")
print("4. 1주일 이내 검색")
print("5. 1개월 이내 검색")
print("6. 3개월 이내 검색")
print("7. 6개월 이내 검색")
print("8. 1년 이내 검색")
print("9. 직접 입력")

day_input = input("선택: ")

if day_input == "9":
    start_date = input("검색 시작 날짜 (YYYY-MM-DD): ")
    end_date = input("검색 끝나는 날짜 (YYYY-MM-DD): ")

driver = webdriver.Chrome(service=service)
driver.get("https://www.naver.com")
time.sleep(2)

# name이 query인 입력 필드에 텍스트 입력
query_input = driver.find_element(By.NAME, "query")
query_input.send_keys(keyWord)
query_input.send_keys(Keys.RETURN)
time.sleep(2)

blog_link = driver.find_element(By.CSS_SELECTOR, "div.api_flicking_wrap._conveyer_root a[href*='blog']")
blog_link.click()
time.sleep(2)

option_btn = driver.find_element(By.XPATH, '//*[@id="snb"]/div[1]/div/div[2]/a')
option_btn.click() 

current_url = driver.current_url
parsed_url = urlparse(current_url)
query_params = parse_qs(parsed_url.query)

# 날짜 옵션 딕셔너리
days = {
    "1": "all",
    "2": "1h",
    "3": "1d",
    "4": "1w",
    "5": "1m",
    "6": "3m",
    "7": "6m",
    "8": "1y"
}


# URL 쿼리 수정
if day_input in days:
    query_params["nso"] = [f"so:r,p:{days[day_input]}"]
elif day_input == "9":
    
    start_year, start_month, start_day = map(int, start_date.split("-"))
    end_year, end_month, end_day = map(int, end_date.split("-"))
    
    start_query = f"{start_year:04d}{start_month:02d}{start_day:02d}"
    end_query = f"{end_year:04d}{end_month:02d}{end_day:02d}"
    
    query_params["nso"] = [f"so:r,p:from{start_query}to{end_query}"]
else:
    print("잘못된 입력입니다.")
    driver.quit()
    exit()

# 수정된 URL 생성
modified_query = urlencode(query_params, doseq=True)
modified_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{modified_query}"

# 수정된 URL로 이동
driver.get(modified_url)

time.sleep(3)

def scroll_and_expand(driver, cnt):
    while True:
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        # li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.lst_view._fe_view_infinite_scroll_append_target > li.bx")
        li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.lst_view._fe_view_infinite_scroll_append_target > li.bx > div.view_wrap")
        time.sleep(2)
        if len(li_elements) >= cnt:
            break
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            cnt = len(li_elements)
            print("확장 불가")
            break

    return cnt

cnt = scroll_and_expand(driver, cnt)

print(cnt)

html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

ul_tag = soup.find("ul", class_="lst_view _fe_view_infinite_scroll_append_target")

result_list = []
# bx type_join _fe_view_cross_collection_root 
pre_li_tags = ul_tag.find_all("li", class_="bx")
li_tags = [li for li in pre_li_tags if li.find("div", class_="view_wrap")]

for li_tag in li_tags[:cnt]:
    name_tag = li_tag.find("a", class_="name")
    name = name_tag.text.strip() if name_tag else ""

    dsc_link_tag = li_tag.find("a", class_="dsc_link")
    dsc_link = dsc_link_tag.text.strip() if dsc_link_tag else ""

    sub_tag = li_tag.find("span", class_="sub")
    sub = sub_tag.text.strip() if sub_tag else ""

    title_link_tag = li_tag.find("a", class_="title_link")
    title_link = title_link_tag.text.strip() if title_link_tag else ""
    title_link_href = title_link_tag['href'] if title_link_tag else ""

    if name and dsc_link and sub and title_link and title_link_href:
        result_list.append([name, dsc_link, sub, title_link, title_link_href])
    else:
        print("제거된거 있음")
  



# 결과 출력
for i, item in enumerate(result_list):
    print(f"번호: {i+1}")
    print(f"블로그 주소: {item[4]}")
    print(f"제목: {item[3]}")
    print(f"내용: {item[1]}")
    print(f"작성일자: {item[2]}")
    print(f"블로그/인플루언서 닉네임: {item[0]}")

def save_results_to_txt(result_list, directory):
    file_path = os.path.join(directory, "결과.txt")
    
    with open(file_path, "w", encoding="utf-8") as file:
        for i, item in enumerate(result_list):
            file.write(f"번호: {i+1}\n")
            file.write(f"블로그 주소: {item[4]}\n")
            file.write(f"제목: {item[3]}\n")
            file.write(f"내용: {item[1]}\n")
            file.write(f"작성일자: {item[2]}\n")
            file.write(f"블로그/인플루언서 닉네임: {item[0]}\n")
            file.write("\n")
    
    print(f"결과가 {file_path}에 저장되었습니다.")

def save_results_xlsx(result_list, directory):
    data = {
        "제목": [item[3] for item in result_list],
        "블로그 주소": [item[4] for item in result_list],
        "작성일자": [item[2] for item in result_list],
        "블로그/인플루언서 닉네임": [item[0] for item in result_list],
        "내용": [item[1] for item in result_list]
    }
    
    df = pd.DataFrame(data)
    
    xlsx_path = os.path.join(directory, "결과.xlsx")
    df.to_excel(xlsx_path, index_label="번호")
    print(f"결과가 {xlsx_path}에 저장되었습니다.")

save_results_to_txt(result_list, savePath)
save_results_xlsx(result_list, savePath)

driver.quit()
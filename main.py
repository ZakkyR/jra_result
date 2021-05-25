import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime as dt
import urllib.parse

# Constants
JRA_URL = "https://www.jra.go.jp"
URL = 'https://www.jra.go.jp/datafile/seiseki/replay/{0}/g1.html'
ALL_URL = 'https://www.jra.go.jp/datafile/seiseki/replay/{0}/jyusyo.html'
YEARS_LIST = [2021, 2020, 2019]


def main():
    df_race = _get_race(YEARS_LIST)
    df_race.to_csv("race.csv", index=False)
    print(df_race["result"])
    df_detail = _get_race_details(df_race["result"])
    df_detail.to_csv("race_detail.csv", index=False)


def _get_race_details(urls: list):
    colmums = [
        "date",
        "race",
        "race_class",
        "race_name",
        "weather",
        "baba_type",
        "baba_condition",
        "course",
        "course_detail",
        "1st_waku",
        "1st_num",
        "1st_horse",
        "1st_jockey",
        "1st_pop",
        "2nd_waku",
        "2nd_num",
        "2nd_horse",
        "2nd_jockey",
        "2nd_pop",
        "3rd_waku",
        "3rd_num",
        "3rd_horse",
        "3rd_jockey",
        "3rd_pop",
        "1st_pop_place",
        "wakuren-pop",
        "umaren-pop",
        "url"
    ]
    colmums_j = [
        "日付",
        "レース",
        "グレード",
        "レース名",
        "天候",
        "種別",
        "馬場",
        "距離",
        "コース",
        "1位枠",
        "1位順位",
        "1位馬",
        "1位騎手",
        "1位単勝人気",
        "2位枠",
        "2位順位",
        "2位馬",
        "2位騎手",
        "2位単勝人気",
        "3位枠",
        "3位順位",
        "3位馬",
        "3位騎手",
        "3位単勝人気",
        "1番人気順位",
        "枠連人気",
        "馬連人気",
        "結果URL"
    ]

    df_rows = []

    for url in urls:
        html = requests.get(url)
        soup = BeautifulSoup(html.content, "html.parser")

        date_race = soup.find("div", class_="cell date").get_text().replace("\n", "").strip()
        date, race = date_race.split(" ")
        race_name = soup.find("span", class_="race_name").get_text().replace("\n", "").strip()
        race_grade = soup.find("span", class_="race_name").find("img").get_attribute_list('alt')[0]

        print(f"{date_race} {race_name} {race_grade}")

        weather = soup.select("li[class='weather'] span[class='txt']")[0].get_text()
        baba = soup.find("div", class_="cell baba").findAll("li")[1]
        baba_type = baba.find("span", class_="cap").get_text()
        baba_condition = baba.find("span", class_="txt").get_text()

        refund_area = soup.find("div", class_="refund_area mt30")
        wakuren_li = refund_area.find("li", class_="wakuren")
        wakuren_pop_div = wakuren_li.find("div", class_="pop") or wakuren_li.find("span", class_="pop")
        for span in wakuren_pop_div.findAll("span"):
            span.decompose()
        wakuren_pop = wakuren_pop_div.get_text()

        umaren_li = refund_area.find("li", class_="umaren")
        umaren_pop_div = umaren_li.find("div", class_="pop") or umaren_li.find("span", class_="pop")
        for span in umaren_pop_div.findAll("span"):
            span.decompose()
        umaren_pop = umaren_pop_div.get_text()

        # コース
        course_div = soup.find("div", class_="cell course")
        course_detail = course_div.find("span", class_="detail").get_text().replace("（", "").replace("）", "")
        for span in course_div.findAll("span"):
            span.decompose()
        course = course_div.get_text().replace("\n", "").replace(",", "")

        # 結果table取得
        table = soup.find("div", id="race_result").find("table")
        table_rows = table.find("tbody").findAll("tr")

        lst_result = []

        most_pop_place = 0
        for idx, tr in enumerate(table_rows):
            place = tr.find("td", class_="place").get_text()
            waku_img = tr.find("td", class_="waku").find("img").get_attribute_list('src')[0]
            waku = waku_img.split("/")[-1].replace(".png", "")
            num = tr.find("td", class_="num").get_text()
            horse = tr.find("td", class_="horse").get_text().replace(" ", "").replace("\n", "")
            jockey = tr.find("td", class_="jockey").get_text()
            pop = tr.find("td", class_="pop").get_text()

            if idx < 3:
                lst_result.extend([waku, num, horse, jockey, pop])

            if pop == "1":
                most_pop_place = place

        # 行作成
        df_cols = [
            date,
            race,
            race_grade,
            race_name,
            weather,
            baba_type,
            baba_condition,
            course,
            course_detail,
        ]
        df_cols.extend(lst_result)
        df_cols.extend([
            most_pop_place,
            wakuren_pop,
            umaren_pop,
            url,
        ])

        # 行追加
        df_rows.append(df_cols)

    # DataFrame作成
    df = pd.DataFrame(df_rows, columns=colmums_j)

    return df


def _get_race(lst_years: list):
    columns = [
        "date",
        "race",
        "place",
        "age",
        "course",
        "winner",
        "jockey",
        "result",
    ]

    df_rows = []
    for year in lst_years:
        html = requests.get(ALL_URL.format(year))
        soup = BeautifulSoup(html.content, "html.parser")

        table = soup.select("div[class='scr-md'] table")[0]
        rows = table.findAll("tr")

        for idx, tr in enumerate(rows):
            cols = tr.findAll("td")

            if (not cols) or (not tr.find("td", class_="result").get_text()):
                continue

            # dateの編集(span消し)
            for span in tr.find("td", class_="date").findAll("span"):
                span.decompose()

            str_date = f"{year}年{tr.find('td', class_='date').get_text()}"
            date = dt.strptime(str_date, "%Y年%m月%d日")

            url = urllib.parse.urljoin(JRA_URL, tr.find("td", class_="result").find("a").get_attribute_list('href')[0])

            df_cols = [date,
                       tr.find("td", class_="race").get_text(),
                       tr.find("td", class_="place").get_text(),
                       tr.find("td", class_="age").get_text(),
                       tr.find("td", class_="course").get_text(),
                       tr.find("td", class_="winner").get_text(),
                       tr.find("td", class_="jockey").get_text(),
                       url]

            df_rows.append(df_cols)

    df = pd.DataFrame(df_rows, columns=columns)

    return df


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

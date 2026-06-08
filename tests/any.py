# %%
import io
import os
import zipfile

import pandas as pd
from curl_cffi import requests

base_dir = os.getcwd()


def get_domestic_com_future_master_dataframe():
    url = "https://new.real.download.dws.co.kr/common/master/fo_com_code.mst.zip"
    response = requests.get(url, impersonate="chrome")
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        file_list = zip_file.namelist()
        mst_filename = [f for f in file_list if f.endswith(".mst")][0]

        with zip_file.open(mst_filename) as f:
            content = f.read().decode("cp949")

    rows_data = []
    for line in content.splitlines():
        if not line.strip():
            continue

        p1_1 = line[0:1]
        p1_2 = line[1:2]
        p1_3 = line[2:11].strip()
        p1_4 = line[11:23].strip()
        p1_5 = line[23:55].strip()

        part2 = line[55:]
        p2_1 = part2[8:9]
        p2_2 = part2[9:12]
        p2_3 = part2[12:].strip()

        rows_data.append([p1_1, p1_2, p1_3, p1_4, p1_5, p2_1, p2_2, p2_3])

    columns = [
        "상품구분",
        "상품종류",
        "단축코드",
        "표준코드",
        "한글종목명",
        "월물구분코드",
        "기초자산단축코드",
        "기초자산명",
    ]
    df = pd.DataFrame(rows_data, columns=columns)

    return df


# %%
df = get_domestic_com_future_master_dataframe()
df[df["기초자산단축코드"] == "USD"]
# %%
df: pd.DataFrame = df[df["한글종목명"].str.startswith("미국달러 F")]  # type: ignore
df = df.sort_values("한글종목명").reset_index(drop=True)
df.loc[0, "단축코드"]

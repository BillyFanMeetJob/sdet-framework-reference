# toolkit/xpath.py
from selenium.webdriver.common.by import By
from toolkit.types import Locator


def _xpath_literal(text: str) -> str:
    """
    安全地把任意字串變成 XPath 字面值。
    避免文字裡面同時有單引號 / 雙引號時爆掉。

    "O'Reilly" -> "'O'Reilly'"
    'He said "hi"' -> '"He said "hi""'
    同時有 ' 和 " 時，組成 concat()。
    """
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text:
        return f'"{text}"'

    # 同時有 ' 和 " 的情況：用 concat('a',"'",'b')
    parts = text.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"


# === 常用基本模式 ===

def button_by_text(text: str) -> Locator:
    """
    //button[normalize-space()='文字']
    依據顯示文字抓 button。
    """
    literal = _xpath_literal(text)
    xpath = f"//button[normalize-space()={literal}]"
    return (By.XPATH, xpath)


def element_by_text(tag: str, text: str) -> Locator:
    """
    //tag[normalize-space()='文字']
    通用版本，可用於 div/span/a/...。
    """
    literal = _xpath_literal(text)
    xpath = f"//{tag}[normalize-space()={literal}]"
    return (By.XPATH, xpath)


def input_by_label(label_text: str) -> Locator:
    """
    根據 label 文字找到對應的 input（for 屬性對應 id）：
    //input[@id=//label[normalize-space()='帳號']/@for]
    需要前端正確使用 <label for="..."> 搭配 <input id="...">
    """
    literal = _xpath_literal(label_text)
    xpath = f"//input[@id=//label[normalize-space()={literal}]/@for]"
    return (By.XPATH, xpath)


def input_following_label(label_text: str) -> Locator:
    """
    通用 pattern：
    根據 label 文字，找後面對應 input（適用很多非標準 form）：
    //label[normalize-space()='帳號']/following::input[1]
    """
    literal = _xpath_literal(label_text)
    xpath = f"//label[normalize-space()={literal}]/following::input[1]"
    return (By.XPATH, xpath)


def by_data_test(value: str) -> Locator:
    """
    依據 data-test 屬性：
    //*[@data-test='value']
    """
    literal = _xpath_literal(value)
    xpath = f"//*[@data-test={literal}]"
    return (By.XPATH, xpath)


def nth_item_in_list(container_xpath: str, index: int) -> Locator:
    """
    給定一組容器 XPath，取第 N 個（1-based）：
    例如：
    container_xpath = "//div[@class='inventory_item']"
    index = 1 -> //div[@class='inventory_item'][1]
    """
    xpath = f"{container_xpath}[{index}]"
    return (By.XPATH, xpath)


def table_cell_by_header(table_xpath: str|None,header_text: str, row_index: int = 1) -> Locator:
    """
    根據表頭文字 + 資料列索引，取得對應 <td> 的 Locator。

    - header_text: 表頭顯示文字，例如 "文件類型"
    - row_index: 第幾筆資料列（1 = 第一筆資料列，即第二個 tr）
    """
    literal = _xpath_literal(header_text)
    if table_xpath:
        table_locator = (By.XPATH, table_xpath)
    else:
        table_locator = table_by_header(header_text)
    table_xpath = table_locator[1]  # 例如: //table[.//tr[1]/th[normalize-space()='文件類型']]

    xpath = (
        f"{table_xpath}"
        f"//tr[position()>1][{row_index}]"          # 第一筆資料列 = tr[2]，所以 position()>1
        f"/td["
        f"  position() = "
        f"    count("
        f"      ../preceding-sibling::tr[1]"       # 緊鄰在上面的那列（通常是表頭列）
        f"         /th[normalize-space()={literal}]"
        f"         /preceding-sibling::th"
        f"    ) + 1"
        f"]"
    )
    return (By.XPATH, xpath)


def table_input_by_header(table_xpath: str|None, header_text: str, row_index: int = 1) -> Locator:
    """
    根據表頭文字 + 資料列索引，取得該格 <td> 底下的第一個 <input>。
    """
    td_locator = table_cell_by_header( table_xpath,header_text, row_index)
    # 直接在原 td XPath 後面加上 //input
    td_xpath = td_locator[1]
    input_xpath = td_xpath + "//input"
    return (By.XPATH, input_xpath)


def table_by_header(header_text: str) -> Locator:
    """
    根據表頭文字取得對應的 <table>。
    條件：第一列 (tr[1]) 的 th 內含有指定文字。
    """
    literal = _xpath_literal(header_text)
    xpath = (
        f"//table[.//tr[1]/th[normalize-space()={literal}]]"
    )
    return (By.XPATH, xpath)


